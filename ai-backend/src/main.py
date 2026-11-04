from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

# Import router from routes
from src.routes.llmRoutes import llmRoutes

# Create FastAPI app instance
app = FastAPI(
    title="AI Backend",
    description="FastAPI with Local Ollama & ChromaDB Memory",
    version="1.0.0"
)

# Include routers
app.include_router(llmRoutes, prefix="/api/v1")

# Root endpoint
@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "API is running",
        "docs": "/docs",
        "redoc": "/redoc"
    }

