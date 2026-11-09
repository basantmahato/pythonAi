import logging
from typing import List, Union
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.dimension = settings.EMBEDDING_DIMENSION
        self._model = None

    @property
    def model(self):
        if self._model is None:
            logger.info(f"Loading SentenceTransformer embedding model: {self.model_name}...")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully.")
        return self._model

    def embed_text(self, text: str) -> List[float]:
        """Generate normalized embedding for a single text."""
        cleaned = text.strip().replace("\n", " ")
        if not cleaned:
            return [0.0] * self.dimension
        
        vec = self.model.encode(cleaned, normalize_embeddings=True)
        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate normalized embeddings for a batch of texts."""
        cleaned = [t.strip().replace("\n", " ") for t in texts]
        if not cleaned:
            return []
        
        vecs = self.model.encode(cleaned, batch_size=32, normalize_embeddings=True)
        return vecs.tolist()


# Global singleton
embedding_service = EmbeddingService()
