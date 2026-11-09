import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.database import SourceModel, MemoryModel, MemoryAuditLogModel
from app.models.schemas import (
    MemoryResponse,
    SourceResponse,
    SourceType,
    VerificationStatus,
)
from app.storage.db import get_db
from app.storage.vector_store import vector_store
from app.services.embedding import embedding_service
from app.services.extractor import memory_extractor
from app.services.conflict import conflict_detector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


class TextInput(BaseModel):
    title: str = "Direct Note"
    content: str
    source_type: SourceType = SourceType.MANUAL_ENTRY
    default_verification_status: VerificationStatus = VerificationStatus.USER_STATED


class IngestionSummary(BaseModel):
    source_id: UUID
    title: str
    memories_extracted: int
    conflicts_or_updates: int
    memories: List[MemoryResponse]


@router.post("/text", response_model=IngestionSummary)
def ingest_text(data: TextInput, db: Session = Depends(get_db)):
    """Ingest free-form personal notes or statements, extract atomic memories, and index them."""
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty.")

    content_hash = memory_extractor.compute_hash(data.content)

    # 1. Register Source
    existing_source = db.query(SourceModel).filter(SourceModel.content_hash == content_hash).first()
    if existing_source:
        source_id = existing_source.id
    else:
        source = SourceModel(
            source_type=data.source_type,
            title=data.title,
            content_hash=content_hash,
            raw_content=data.content
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        source_id = source.id

    # 2. Extract atomic memories
    extracted = memory_extractor.extract_memories(
        raw_text=data.content,
        source_id=UUID(source_id),
        default_status=data.default_verification_status
    )

    created_memories: List[MemoryResponse] = []
    conflict_count = 0

    # 3. Process each memory: conflict check & dual-write
    for item in extracted:
        vec = embedding_service.embed_text(item.content)
        conflict_res = conflict_detector.check_conflict(item, vector=vec)

        if conflict_res.action_suggested == "IGNORE":
            # Redundant exact duplicate
            conflict_count += 1
            continue

        if conflict_res.action_suggested == "SUPERSEDE" and conflict_res.existing_memory_id:
            # Supersede old memory
            old_rec = db.query(MemoryModel).filter(MemoryModel.id == str(conflict_res.existing_memory_id)).first()
            if old_rec:
                old_rec.is_current = False
                vector_store.update_payload(conflict_res.existing_memory_id, {"is_current": False})
                conflict_count += 1

        db_mem = MemoryModel(
            source_id=source_id,
            category=item.category,
            content=item.content,
            summary=item.summary,
            verification_status=item.verification_status,
            confidence_score=item.confidence_score,
            privacy_level=item.privacy_level,
            is_current=item.is_current,
            structured_payload=item.structured_payload,
            tags=item.tags
        )
        db.add(db_mem)
        db.commit()
        db.refresh(db_mem)

        payload = {
            "memory_id": db_mem.id,
            "category": db_mem.category.value,
            "verification_status": db_mem.verification_status.value,
            "privacy_level": db_mem.privacy_level.value,
            "is_current": db_mem.is_current,
            "confidence_score": db_mem.confidence_score,
            "tags": db_mem.tags,
            "content_preview": db_mem.content[:200]
        }
        vector_store.upsert_memory(memory_id=UUID(db_mem.id), vector=vec, payload=payload)

        # Audit
        audit = MemoryAuditLogModel(
            memory_id=db_mem.id,
            action="INSERT",
            new_state=payload,
            reason=f"Ingestion from source {source_id}"
        )
        db.add(audit)
        db.commit()

        created_memories.append(
            MemoryResponse(
                id=UUID(db_mem.id),
                source_id=UUID(db_mem.source_id),
                category=db_mem.category,
                content=db_mem.content,
                summary=db_mem.summary,
                verification_status=db_mem.verification_status,
                confidence_score=db_mem.confidence_score,
                privacy_level=db_mem.privacy_level,
                valid_from=db_mem.valid_from,
                valid_until=db_mem.valid_until,
                is_current=db_mem.is_current,
                structured_payload=db_mem.structured_payload,
                tags=db_mem.tags,
                created_at=db_mem.created_at,
                updated_at=db_mem.updated_at
            )
        )

    return IngestionSummary(
        source_id=UUID(source_id),
        title=data.title,
        memories_extracted=len(created_memories),
        conflicts_or_updates=conflict_count,
        memories=created_memories
    )


@router.post("/file", response_model=IngestionSummary)
async def ingest_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload and ingest a Markdown, text, or JSON file."""
    content_bytes = await file.read()
    raw_text = content_bytes.decode("utf-8", errors="replace")
    doc_title = title or file.filename or "Uploaded File"

    file_type = SourceType.FILE_MD if file.filename and file.filename.endswith(".md") else SourceType.MANUAL_ENTRY

    return ingest_text(
        TextInput(
            title=doc_title,
            content=raw_text,
            source_type=file_type,
            default_verification_status=VerificationStatus.VERIFIED_FACT
        ),
        db=db
    )
