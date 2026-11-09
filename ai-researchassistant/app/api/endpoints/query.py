import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.schemas import GroundedQueryRequest, GroundedQueryResponse
from app.storage.db import get_db
from app.services.retriever import hybrid_retriever
from app.services.grounding import grounding_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["Grounded Query"])


@router.post("/", response_model=GroundedQueryResponse)
def query_personal_intelligence(
    request: GroundedQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Execute a grounded, context-aware query against personal memories.
    Returns synthesized response with explicit memory citations and hallucination guards.
    """
    # 1. Hybrid semantic retrieval
    citations = hybrid_retriever.retrieve(
        query=request.query,
        db=db,
        categories=request.categories,
        include_historical=request.include_historical,
        limit=request.max_memories
    )

    # 2. Grounded synthesis and citation verification
    response = grounding_service.answer_query(
        query=request.query,
        citations=citations
    )

    return response
