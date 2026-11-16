from fastapi import APIRouter, Depends
from src.controller.rag_controller import RagController
from src.models.schemas import RagQueryRequest, RagQueryResponse

router = APIRouter(prefix="/api/v1/rag", tags=["Self-Correcting RAG"])

def get_rag_controller() -> RagController:
    return RagController()

@router.post(
    "/query",
    response_model=RagQueryResponse,
    summary="Execute Self-Correcting RAG Query",
    description="Embeds query, retrieves relevant chunks from Qdrant, grades chunk relevance with Gemini, rewrites query if needed, generates response, and runs hallucination reflection."
)
async def query_rag(
    request: RagQueryRequest,
    controller: RagController = Depends(get_rag_controller)
) -> RagQueryResponse:
    return await controller.query(request)
