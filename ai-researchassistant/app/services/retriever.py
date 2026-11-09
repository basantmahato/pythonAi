import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.database import MemoryModel
from app.models.schemas import (
    MemoryCategory,
    MemoryCitation,
    VerificationStatus,
)
from app.storage.vector_store import vector_store
from app.services.embedding import embedding_service

logger = logging.getLogger(__name__)


class HybridRetriever:
    def __init__(self):
        pass

    def retrieve(
        self,
        query: str,
        db: Session,
        categories: Optional[List[MemoryCategory]] = None,
        include_historical: bool = False,
        limit: int = 8,
        min_relevance: float = 0.40
    ) -> List[MemoryCitation]:
        """Execute multi-stage hybrid retrieval combining Qdrant dense vector search with SQL metadata."""
        # 1. Generate query embedding
        query_vec = embedding_service.embed_text(query)

        # 2. Vector search in Qdrant with payload filtering
        cat_filter = [c.value for c in categories] if categories else None
        
        # When include_historical is False, strictly retrieve active memories
        vector_results = vector_store.search_memories(
            query_vector=query_vec,
            limit=limit * 2,
            categories=cat_filter,
            is_current_only=not include_historical,
            score_threshold=min_relevance
        )

        if not vector_results:
            logger.info("No vector matches found above threshold.")
            return []

        # 3. Fetch authoritative relational rows from PostgreSQL for verification
        memory_ids = [res["memory_id"] for res in vector_results]
        db_records = (
            db.query(MemoryModel)
            .filter(MemoryModel.id.in_(memory_ids))
            .all()
        )
        record_map = {rec.id: rec for rec in db_records}

        # 4. Construct grounded citations with exact provenance
        citations: List[MemoryCitation] = []
        for res in vector_results:
            m_id = res["memory_id"]
            rec = record_map.get(m_id)
            if not rec:
                continue

            # Check temporal validity
            if not include_historical and not rec.is_current:
                continue

            citation = MemoryCitation(
                memory_id=UUID(rec.id),
                category=rec.category,
                verification_status=rec.verification_status,
                content_snippet=rec.content,
                relevance_score=round(res["score"], 4)
            )
            citations.append(citation)

            if len(citations) >= limit:
                break

        return citations


hybrid_retriever = HybridRetriever()
