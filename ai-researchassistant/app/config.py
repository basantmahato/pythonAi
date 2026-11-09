from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    APP_NAME: str = "Personal Intelligence System"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"

    # Storage Settings
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/personal_intelligence"
    SQLITE_FALLBACK_URL: str = f"sqlite:///{Path(__file__).resolve().parent.parent / 'data' / 'personal_intelligence.db'}"
    USE_SQLITE_FALLBACK: bool = False

    # Qdrant Vector Store
    QDRANT_URL: Optional[str] = "http://localhost:6333"
    QDRANT_LOCAL_PATH: str = str(Path(__file__).resolve().parent.parent / "data" / "qdrant_storage")
    QDRANT_COLLECTION: str = "personal_memories_v1"
    USE_LOCAL_QDRANT: bool = False

    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"

    # Embedding Model
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-base-en-v1.5"
    EMBEDDING_DIMENSION: int = 768

    # LLM Provider Configuration
    DEFAULT_LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # Ingestion Parameters
    MAX_CHUNK_SIZE_TOKENS: int = 400
    CHUNK_OVERLAP_TOKENS: int = 50
    CONFLICT_SIMILARITY_THRESHOLD: float = 0.88
    MIN_CONFIDENCE_THRESHOLD: float = 0.70

    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"


settings = Settings()

# Ensure data directory exists
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
