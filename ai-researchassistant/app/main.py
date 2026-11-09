import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from rich.console import Console

from app.config import settings
from app.storage.db import init_db
from app.storage.vector_store import vector_store
from app.api.router import api_router

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger("pis")
console = Console()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME}...")
    try:
        init_db()
        logger.info("Relational database ready.")
    except Exception as e:
        logger.error(f"Error initializing relational database: {e}")

    # Vector store verification
    try:
        cols = vector_store.client.get_collections()
        logger.info(f"Vector Store initialized. Available collections: {[c.name for c in cols.collections]}")
    except Exception as e:
        logger.error(f"Error connecting to vector store: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Personal Intelligence System...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Personal RAG-based Cognitive Memory and Career Intelligence System",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register main API router
app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health_check():
    """System health check and component status."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "llm_provider": settings.DEFAULT_LLM_PROVIDER,
        "vector_collection": settings.QDRANT_COLLECTION,
        "embedding_model": settings.EMBEDDING_MODEL_NAME
    }


# Mount Frontend Static SPA (must be mounted after all API and health routes)
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
