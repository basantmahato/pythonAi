import logging
from typing import Dict, Any, Optional
from src.services.loader import DocumentLoader
from src.services.chunker import RecursiveChunker
from src.services.embedder import GeminiEmbedder
from src.repository.qdrant_repository import QdrantRepository
from src.models.schemas import IngestResponse

logger = logging.getLogger(__name__)

class IngestionService:
    def __init__(
        self,
        loader: Optional[DocumentLoader] = None,
        chunker: Optional[RecursiveChunker] = None,
        embedder: Optional[GeminiEmbedder] = None,
        repository: Optional[QdrantRepository] = None
    ):
        self.loader = loader or DocumentLoader()
        self.chunker = chunker or RecursiveChunker()
        self.embedder = embedder or GeminiEmbedder()
        self.repository = repository or QdrantRepository()

    def ingest_raw_text(
        self,
        text: str,
        source_name: str = "raw_text",
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> IngestResponse:
        """Process and ingest raw text into Qdrant."""
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty.")

        logger.info(f"Starting ingestion pipeline for text source: {source_name}")

        # 1. Chunk document
        chunks = self.chunker.chunk_document(
            text=text,
            source_name=source_name,
            base_metadata=extra_metadata
        )

        if not chunks:
            raise ValueError(f"No chunks could be extracted from '{source_name}'.")

        # 2. Generate embeddings
        texts_to_embed = [chunk.content for chunk in chunks]
        embeddings = self.embedder.generate_embeddings(texts_to_embed)

        if len(embeddings) != len(chunks):
            raise RuntimeError(
                f"Mismatch: generated {len(embeddings)} embeddings for {len(chunks)} chunks."
            )

        # 3. Prepare points for Qdrant
        ids = [chunk.chunk_id for chunk in chunks]
        payloads = [
            {"content": chunk.content, **chunk.metadata}
            for chunk in chunks
        ]

        # 4. Upsert into Qdrant
        self.repository.upsert_points(ids=ids, vectors=embeddings, payloads=payloads)

        return IngestResponse(
            status="success",
            message=f"Successfully processed and stored {len(chunks)} chunks in Qdrant.",
            source_name=source_name,
            total_chunks=len(chunks),
            collection=self.repository.collection_name
        )

    def ingest_file(
        self,
        file_bytes: bytes,
        filename: str,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> IngestResponse:
        """Extract text from file bytes and run ingestion pipeline."""
        logger.info(f"Extracting content from uploaded file: {filename}")
        extracted_text = self.loader.load_from_bytes(file_bytes=file_bytes, filename=filename)

        if not extracted_text or not extracted_text.strip():
            raise ValueError(f"Extracted content from '{filename}' is empty.")

        metadata = extra_metadata or {}
        metadata["filename"] = filename

        return self.ingest_raw_text(
            text=extracted_text,
            source_name=filename,
            extra_metadata=metadata
        )
