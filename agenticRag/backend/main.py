import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.repository.qdrant_repository import QdrantRepository
from src.routes.ingestion_routes import router as ingestion_router
from src.routes.rag_routes import router as rag_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure Qdrant collection is ready
    logger.info("Initializing Agentic RAG services...")
    try:
        repo = QdrantRepository()
        repo.ensure_collection()
        logger.info("Qdrant vector collection verified and ready.")
    except Exception as e:
        logger.warning(
            f"Could not connect to Qdrant at {settings.QDRANT_URL}: {e}. "
            "Ensure Docker container is running (`docker compose up -d`)."
        )
    yield
    # Shutdown logic (if any)
    logger.info("Shutting down Agentic RAG services...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(ingestion_router)
app.include_router(rag_router)

@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "qdrant_collection": settings.QDRANT_COLLECTION_NAME,
        "embedding_model": settings.EMBEDDING_MODEL
    }
