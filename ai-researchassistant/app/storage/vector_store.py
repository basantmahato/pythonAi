import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    def __init__(
        self,
        client: Optional[QdrantClient] = None,
        collection_name: Optional[str] = None,
        vector_dim: Optional[int] = None
    ):
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        self.vector_dim = vector_dim or settings.EMBEDDING_DIMENSION
        self.client = client if client is not None else self._init_client()
        self._ensure_collection()

    def _init_client(self) -> QdrantClient:
        if settings.USE_LOCAL_QDRANT:
            logger.info(f"Using local Qdrant disk storage at {settings.QDRANT_LOCAL_PATH}")
            self._clean_stale_lock(settings.QDRANT_LOCAL_PATH)
            return QdrantClient(path=settings.QDRANT_LOCAL_PATH)

        try:
            logger.info(f"Attempting connection to Qdrant at {settings.QDRANT_URL}")
            client = QdrantClient(url=settings.QDRANT_URL, timeout=3.0)
            client.get_collections()
            logger.info("Successfully connected to Qdrant server.")
            return client
        except Exception as e:
            logger.warning(
                f"Could not connect to Qdrant at {settings.QDRANT_URL}: {e}. "
                f"Falling back to embedded local storage at {settings.QDRANT_LOCAL_PATH}"
            )
            self._clean_stale_lock(settings.QDRANT_LOCAL_PATH)
            return QdrantClient(path=settings.QDRANT_LOCAL_PATH)

    def _clean_stale_lock(self, dir_path: str):
        try:
            lock_file = Path(dir_path) / ".lock"
            if lock_file.exists():
                lock_file.unlink(missing_ok=True)
        except Exception:
            pass

    def _ensure_collection(self):
        """Ensure collection exists and payload indexes are configured."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating Qdrant collection '{self.collection_name}' ({self.vector_dim}d, Cosine)...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.vector_dim,
                        distance=qmodels.Distance.COSINE
                    ),
                    hnsw_config=qmodels.HnswConfigDiff(
                        m=16,
                        ef_construct=128
                    )
                )

                # Create Payload Indexes for fast pre-filtering
                for field_name, schema_type in [
                    ("category", qmodels.PayloadSchemaType.KEYWORD),
                    ("verification_status", qmodels.PayloadSchemaType.KEYWORD),
                    ("is_current", qmodels.PayloadSchemaType.BOOL),
                    ("privacy_level", qmodels.PayloadSchemaType.KEYWORD),
                    ("valid_from", qmodels.PayloadSchemaType.INTEGER),
                ]:
                    try:
                        self.client.create_payload_index(
                            collection_name=self.collection_name,
                            field_name=field_name,
                            field_schema=schema_type
                        )
                    except Exception as idx_err:
                        logger.debug(f"Payload index creation info for {field_name}: {idx_err}")

                logger.info(f"Collection '{self.collection_name}' initialized with indexes.")
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection: {e}")

    def upsert_memory(
        self,
        memory_id: UUID,
        vector: List[float],
        payload: Dict[str, Any]
    ) -> bool:
        """Upsert a memory vector and associated metadata payload."""
        try:
            point = qmodels.PointStruct(
                id=str(memory_id),
                vector=vector,
                payload=payload
            )
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert memory point {memory_id}: {e}")
            raise e

    def search_memories(
        self,
        query_vector: List[float],
        limit: int = 10,
        categories: Optional[List[str]] = None,
        is_current_only: bool = True,
        verification_statuses: Optional[List[str]] = None,
        score_threshold: float = 0.50
    ) -> List[Dict[str, Any]]:
        """Perform semantic search with metadata filters."""
        must_conditions = []

        if is_current_only:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="is_current",
                    match=qmodels.MatchValue(value=True)
                )
            )

        if categories:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="category",
                    match=qmodels.MatchAny(any=categories)
                )
            )

        if verification_statuses:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="verification_status",
                    match=qmodels.MatchAny(any=verification_statuses)
                )
            )

        query_filter = None
        if must_conditions:
            query_filter = qmodels.Filter(must=must_conditions)

        try:
            if hasattr(self.client, "query_points"):
                results = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=query_filter,
                    limit=limit,
                    score_threshold=score_threshold,
                    with_payload=True
                ).points
            else:
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=limit,
                    score_threshold=score_threshold,
                    with_payload=True
                )

            formatted = []
            for hit in results:
                formatted.append({
                    "memory_id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload
                })
            return formatted
        except Exception as e:
            logger.error(f"Error executing vector search: {e}")
            return []

    def update_payload(self, memory_id: UUID, payload_patch: Dict[str, Any]) -> bool:
        """Update payload attributes (e.g. is_current, verification_status) without re-embedding."""
        try:
            self.client.set_payload(
                collection_name=self.collection_name,
                payload=payload_patch,
                points=[str(memory_id)]
            )
            return True
        except Exception as e:
            logger.error(f"Error updating payload for {memory_id}: {e}")
            return False

    def delete_memory(self, memory_id: UUID) -> bool:
        """Delete a vector point."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=qmodels.PointIdsList(points=[str(memory_id)])
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting vector point {memory_id}: {e}")
            return False


# Singleton instance
vector_store = QdrantVectorStore()
