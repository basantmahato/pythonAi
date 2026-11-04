from fastapi import APIRouter
from src.controller.llmController import (
    generate_text,
    clear_memory_handler,
    memory_stats_handler,
    PromptRequest,
    PromptResponse
)

llmRoutes = APIRouter(prefix="/llm", tags=["LLM with Vector Memory"])
router = llmRoutes

@llmRoutes.get("/status")
async def get_status():
    """Health check for the LLM service."""
    return {"status": "LLM route active"}

@llmRoutes.post("/generate", response_model=PromptResponse)
async def generate(request: PromptRequest):
    """
    Main AI endpoint with built-in Vector Memory:
    1. Automatically searches ChromaDB for relevant past context.
    2. Augments the prompt so Ollama answers accurately.
    3. Automatically saves the new conversation back into ChromaDB.
    """
    return await generate_text(request)

@llmRoutes.get("/memory")
async def get_memory_stats():
    """View the total count of conversation memories stored in ChromaDB."""
    return await memory_stats_handler()

@llmRoutes.delete("/memory")
async def clear_memory():
    """Reset and clear all saved memories in ChromaDB."""
    return await clear_memory_handler()
