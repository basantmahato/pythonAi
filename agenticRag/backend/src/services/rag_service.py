import logging
from typing import List, Optional
from src.config.settings import settings
from src.models.schemas import RagQueryRequest, RagQueryResponse, RetrievedChunk
from src.repository.qdrant_repository import QdrantRepository
from src.services.embedder import GeminiEmbedder
from src.services.llm_service import GeminiLLMService

logger = logging.getLogger(__name__)

class SelfCorrectingRagService:
    def __init__(
        self,
        repository: Optional[QdrantRepository] = None,
        embedder: Optional[GeminiEmbedder] = None,
        llm: Optional[GeminiLLMService] = None,
        max_retries: int = settings.MAX_CORRECTION_RETRIES
    ):
        self.repository = repository or QdrantRepository()
        self.embedder = embedder or GeminiEmbedder()
        self.llm = llm or GeminiLLMService()
        self.max_retries = max_retries

    def _retrieve(self, query: str, top_k: int) -> List[RetrievedChunk]:
        """Generate embedding for query and retrieve top-k chunks from Qdrant."""
        query_embeddings = self.embedder.generate_embeddings([query])
        if not query_embeddings:
            return []

        query_vector = query_embeddings[0]
        results = self.repository.search_points(query_vector=query_vector, limit=top_k)

        chunks: List[RetrievedChunk] = []
        for r in results:
            payload = r.get("payload", {})
            chunks.append(
                RetrievedChunk(
                    id=r.get("id"),
                    content=payload.get("content", ""),
                    score=r.get("score", 0.0),
                    source=payload.get("source", "unknown"),
                    chunk_index=payload.get("chunk_index"),
                    metadata=payload
                )
            )
        return chunks

    def process_query(self, request: RagQueryRequest) -> RagQueryResponse:
        original_query = request.query
        current_query = original_query
        top_k = request.top_k or settings.DEFAULT_TOP_K

        rewritten_queries: List[str] = []
        retrieved_chunks: List[RetrievedChunk] = []
        relevant_chunks: List[RetrievedChunk] = []
        iterations = 1

        logger.info(f"Initiating Self-Correcting RAG for: '{original_query}'")

        if not request.enable_self_correction:
            # Standard single-pass RAG without grading or self-correction
            retrieved_chunks = self._retrieve(current_query, top_k)
            context = [c.content for c in retrieved_chunks]
            answer = self.llm.generate_answer(original_query, context) if context else "No documents found."
            return RagQueryResponse(
                original_query=original_query,
                final_query=current_query,
                rewritten_queries=[],
                retrieved_chunks=retrieved_chunks,
                relevant_chunks_count=len(retrieved_chunks),
                answer=answer,
                is_grounded=True,
                addresses_query=True,
                iterations=1
            )

        # Self-Correction Retrieval & Grading Loop
        for attempt in range(self.max_retries + 1):
            logger.info(f"Retrieval Attempt {attempt + 1} with query: '{current_query}'")
            retrieved_chunks = self._retrieve(current_query, top_k)

            # Document Grading Step: filter for relevant chunks
            relevant_chunks = []
            for chunk in retrieved_chunks:
                grade = self.llm.grade_document_relevance(original_query, chunk.content)
                if grade.get("is_relevant", False):
                    relevant_chunks.append(chunk)

            logger.info(
                f"Attempt {attempt + 1}: Found {len(relevant_chunks)}/{len(retrieved_chunks)} relevant chunks."
            )

            # If we found relevant documents, break out of retry loop
            if relevant_chunks:
                break

            # If no relevant documents found and retries remaining, rewrite query
            if attempt < self.max_retries:
                logger.info("No relevant chunks found. Triggering Query Rewriter...")
                attempted = [original_query] + rewritten_queries
                rewritten = self.llm.rewrite_query(original_query, attempted)
                rewritten_queries.append(rewritten)
                current_query = rewritten
                iterations += 1

        # Check if we still have no relevant documents
        if not relevant_chunks:
            return RagQueryResponse(
                original_query=original_query,
                final_query=current_query,
                rewritten_queries=rewritten_queries,
                retrieved_chunks=retrieved_chunks,
                relevant_chunks_count=0,
                answer="I searched the indexed documents, but could not find information relevant to your question.",
                is_grounded=True,
                addresses_query=False,
                iterations=iterations
            )

        # Synthesize Answer from verified relevant chunks
        context_texts = [c.content for c in relevant_chunks]
        answer = self.llm.generate_answer(original_query, context_texts)

        # Self-Reflection Step 1: Hallucination Check
        grounded_check = self.llm.check_hallucination(context_texts, answer)
        is_grounded = grounded_check.get("is_grounded", True)

        # Self-Reflection Step 2: Answer Quality Check
        quality_check = self.llm.check_answer_quality(original_query, answer)
        addresses_query = quality_check.get("addresses_query", True)

        # Correction if hallucination detected: regenerate with strict fallback
        if not is_grounded:
            logger.warning("Potential hallucination detected during reflection. Regenerating with strict constraint...")
            answer = self.llm.generate_answer(
                f"STRICT CONSTRAINT: Base your response exclusively on explicit facts from the context. Do not infer. Query: {original_query}",
                context_texts
            )
            is_grounded = True

        return RagQueryResponse(
            original_query=original_query,
            final_query=current_query,
            rewritten_queries=rewritten_queries,
            retrieved_chunks=relevant_chunks,
            relevant_chunks_count=len(relevant_chunks),
            answer=answer,
            is_grounded=is_grounded,
            addresses_query=addresses_query,
            iterations=iterations
        )
