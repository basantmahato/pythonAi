import logging
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from src.services.ingestion_service import IngestionService
from src.models.schemas import IngestResponse, IngestTextRequest

logger = logging.getLogger(__name__)

class IngestionController:
    def __init__(self, service: Optional[IngestionService] = None):
        self.service = service or IngestionService()

    async def ingest_file(self, file: UploadFile) -> IngestResponse:
        """Controller action to handle uploaded file ingestion."""
        try:
            content = await file.read()
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Uploaded file '{file.filename}' is empty."
                )

            return self.service.ingest_file(
                file_bytes=content,
                filename=file.filename,
                extra_metadata={"content_type": file.content_type}
            )
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error handling file upload in controller: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to ingest file: {str(e)}"
            )

    async def ingest_text(self, request: IngestTextRequest) -> IngestResponse:
        """Controller action to handle direct text ingestion."""
        try:
            return self.service.ingest_raw_text(
                text=request.text,
                source_name=request.title or "raw_text",
                extra_metadata=request.metadata
            )
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
        except Exception as e:
            logger.error(f"Error handling text ingestion in controller: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to ingest text: {str(e)}"
            )
