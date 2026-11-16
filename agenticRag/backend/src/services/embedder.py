import logging
from typing import List, Optional
from google import genai
from src.config.settings import settings

logger = logging.getLogger(__name__)

class GeminiEmbedder:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.EMBEDDING_MODEL

        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger.warning("GEMINI_API_KEY is not configured in .env. API calls will fail until set.")

        self.client = genai.Client(api_key=self.api_key)

    def generate_embeddings(self, texts: List[str], batch_size: int = 50) -> List[List[float]]:
        """Generate vector embeddings for a list of strings using Google Gemini API."""
        if not texts:
            return []

        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise ValueError(
                "GEMINI_API_KEY is missing or invalid. Please set your Gemini API key in backend/.env"
            )

        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = self.client.models.embed_content(
                    model=self.model,
                    contents=batch
                )
                if hasattr(response, "embeddings") and response.embeddings:
                    for item in response.embeddings:
                        all_embeddings.append(item.values)
                else:
                    raise ValueError("Gemini API returned an unexpected empty embedding response.")
            except Exception as e:
                logger.error(f"Failed to generate embeddings with Gemini model '{self.model}': {e}")
                raise

        logger.info(f"Successfully generated {len(all_embeddings)} embeddings.")
        return all_embeddings
