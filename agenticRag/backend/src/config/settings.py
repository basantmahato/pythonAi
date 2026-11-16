from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "Agentic RAG API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Gemini API
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API Key")
    LLM_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "text-embedding-004"
    EMBEDDING_DIMENSION: int = 768

    # Qdrant Vector Store
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION_NAME: str = "agentic_rag_docs"

    # Text Chunking Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Self-Correcting RAG Settings
    DEFAULT_TOP_K: int = 5
    MAX_CORRECTION_RETRIES: int = 2

settings = Settings()
