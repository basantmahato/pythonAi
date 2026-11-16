import logging
from typing import Optional
from fastapi import HTTPException, status
from src.services.rag_service import SelfCorrectingRagService
from src.models.schemas import RagQueryRequest, RagQueryResponse

logger = logging.getLogger(__name__)

class RagController:
    def __init__(self, service: Optional[SelfCorrectingRagService] = None):
        self.service = service or SelfCorrectingRagService()

    async def query(self, request: RagQueryRequest) -> RagQueryResponse:
        """Controller action to handle self-correcting RAG query requests."""
        try:
            return self.service.process_query(request)
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(ve)
            )
        except Exception as e:
            logger.error(f"Error processing RAG query: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Self-Correcting RAG processing failed: {str(e)}"
            )
