import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from src.config.settings import settings

logger = logging.getLogger(__name__)

class QdrantRepository:
    def __init__(self, client: Optional[QdrantClient] = None):
        self.client = client or QdrantClient(url=settings.QDRANT_URL)
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.vector_size = settings.EMBEDDING_DIMENSION

    def ensure_collection(self) -> None:
        """Create the Qdrant collection if it does not already exist."""
        try:
            collections = self.client.get_collections().collections
            existing_names = [col.name for col in collections]

            if self.collection_name not in existing_names:
                logger.info(f"Creating Qdrant collection '{self.collection_name}' with vector size {self.vector_size}...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.vector_size,
                        distance=qmodels.Distance.COSINE
                    )
                )
                logger.info(f"Collection '{self.collection_name}' created successfully.")
            else:
                logger.info(f"Qdrant collection '{self.collection_name}' already exists.")
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection exists: {e}")
            raise

    def upsert_points(
        self,
        ids: List[str],
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]]
    ) -> bool:
        """Upsert points (chunks + vectors + payloads) into Qdrant."""
        try:
            points = [
                qmodels.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
                for point_id, vector, payload in zip(ids, vectors, payloads)
            ]

            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Upserted {len(points)} points into '{self.collection_name}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert points into Qdrant: {e}")
            raise

    def search_points(
        self,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search for most similar vectors in Qdrant collection."""
        try:
            # Compatible with both modern query_points and search methods in qdrant-client
            if hasattr(self.client, "query_points"):
                results = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    limit=limit,
                    score_threshold=score_threshold
                ).points
            else:
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=limit,
                    score_threshold=score_threshold
                )

            scored_points = []
            for point in results:
                scored_points.append({
                    "id": str(point.id),
                    "score": float(point.score),
                    "payload": point.payload or {}
                })

            logger.info(f"Retrieved {len(scored_points)} points from '{self.collection_name}'.")
            return scored_points
        except Exception as e:
            logger.error(f"Search failed in Qdrant: {e}")
            raise
