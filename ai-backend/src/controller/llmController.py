from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from src.services.llmService import LLMService
from src.services.vectorService import VectorService

llm_service = LLMService()
vector_service = VectorService()

class PromptRequest(BaseModel):
    prompt: str = Field(..., description="Your message or question")
    model: Optional[str] = Field(default=None, description="Optional model override (default: llama3.2:3b)")
    enable_memory: bool = Field(default=True, description="Automatically retrieve and store conversation memory")

class PromptResponse(BaseModel):
    response: str
    model: str
    memory_recalled: List[str] = Field(default_factory=list, description="Relevant memories recalled from Vector DB")
    total_memories_stored: int

async def generate_text(request: PromptRequest) -> PromptResponse:
    selected_model = request.model or llm_service.default_model
    recalled_memories: List[str] = []

    # 1. Pre-retrieval: Check Vector DB for relevant context if memory is enabled
    if request.enable_memory:
        recalled_memories = vector_service.search_relevant(query=request.prompt, top_k=2)

    # 2. Augment prompt with recalled memories if available
    if recalled_memories:
        memory_block = "\n".join(f"- {mem}" for mem in recalled_memories)
        full_prompt = (
            f"You are a helpful assistant with memory of past interactions.\n"
            f"Relevant previous context:\n{memory_block}\n\n"
            f"User says: {request.prompt}\n"
            f"Respond accurately taking the above context into account:"
        )
    else:
        full_prompt = request.prompt

    # 3. Generate response from local Ollama model
    result = await llm_service.generate_response(full_prompt, model=selected_model)

    # 4. Post-response: Store this interaction in Vector DB for future recall
    if request.enable_memory:
        interaction = f"User said: {request.prompt} | AI answered: {result}"
        vector_service.add_memory(
            text=interaction,
            metadata={
                "prompt": request.prompt,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    return PromptResponse(
        response=result,
        model=selected_model,
        memory_recalled=recalled_memories,
        total_memories_stored=vector_service.count_memories()
    )

async def clear_memory_handler() -> Dict[str, Any]:
    vector_service.clear_all()
    return {"message": "All vector conversation memory cleared successfully."}

async def memory_stats_handler() -> Dict[str, Any]:
    return {
        "collection": "conversation_memory",
        "total_memories": vector_service.count_memories()
    }
