from fastapi import APIRouter, UploadFile, File, Depends
from src.controller.ingestion_controller import IngestionController
from src.models.schemas import IngestResponse, IngestTextRequest

router = APIRouter(prefix="/api/v1/ingest", tags=["Ingestion Pipeline"])

def get_ingestion_controller() -> IngestionController:
    return IngestionController()

@router.post(
    "/file",
    response_model=IngestResponse,
    summary="Upload & Ingest Document",
    description="Extracts text from an uploaded document (PDF, TXT, Markdown), splits into chunks, embeds with Gemini, and stores in Qdrant."
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to ingest (PDF, TXT, MD)"),
    controller: IngestionController = Depends(get_ingestion_controller)
) -> IngestResponse:
    return await controller.ingest_file(file=file)

@router.post(
    "/text",
    response_model=IngestResponse,
    summary="Ingest Raw Text",
    description="Accepts raw text with optional metadata, chunks it, generates vector embeddings, and stores in Qdrant."
)
async def ingest_raw_text(
    request: IngestTextRequest,
    controller: IngestionController = Depends(get_ingestion_controller)
) -> IngestResponse:
    return await controller.ingest_text(request=request)
