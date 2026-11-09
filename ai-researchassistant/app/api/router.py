from fastapi import APIRouter

from app.api.endpoints.memories import router as memories_router
from app.api.endpoints.ingestion import router as ingestion_router
from app.api.endpoints.query import router as query_router
from app.api.endpoints.audit import router as audit_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(memories_router)
api_router.include_router(ingestion_router)
api_router.include_router(query_router)
api_router.include_router(audit_router)
