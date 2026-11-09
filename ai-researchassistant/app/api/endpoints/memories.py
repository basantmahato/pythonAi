import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.database import MemoryModel, MemoryAuditLogModel
from app.models.schemas import (
    MemoryCategory,
    MemoryCreate,
    MemoryFilter,
    MemoryResponse,
    MemoryUpdate,
    VerificationStatus,
)
from app.storage.db import get_db
from app.storage.vector_store import vector_store
from app.services.embedding import embedding_service
from app.storage.cache import cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memories", tags=["Memories"])


@router.post("/", response_model=MemoryResponse, status_code=201)
def create_memory(memory_in: MemoryCreate, db: Session = Depends(get_db)):
    """Create a new personal memory directly with dual-persistence in PostgreSQL and Qdrant."""
    db_memory = MemoryModel(
        source_id=str(memory_in.source_id) if memory_in.source_id else None,
        category=memory_in.category,
        content=memory_in.content,
        summary=memory_in.summary or memory_in.content[:50] + "...",
        verification_status=memory_in.verification_status,
        confidence_score=memory_in.confidence_score,
        privacy_level=memory_in.privacy_level,
        is_current=memory_in.is_current,
        structured_payload=memory_in.structured_payload,
        tags=memory_in.tags,
    )
    db.add(db_memory)
    db.commit()
    db.refresh(db_memory)

    # 1. Generate dense vector embedding
    vector = embedding_service.embed_text(db_memory.content)

    # 2. Persist in Qdrant with payload filters
    payload = {
        "memory_id": db_memory.id,
        "category": db_memory.category.value,
        "verification_status": db_memory.verification_status.value,
        "privacy_level": db_memory.privacy_level.value,
        "is_current": db_memory.is_current,
        "confidence_score": db_memory.confidence_score,
        "valid_from": int(db_memory.valid_from.timestamp()) if db_memory.valid_from else 0,
        "tags": db_memory.tags,
        "content_preview": db_memory.content[:200]
    }
    vector_store.upsert_memory(memory_id=UUID(db_memory.id), vector=vector, payload=payload)

    # 3. Log Audit
    audit_entry = MemoryAuditLogModel(
        memory_id=db_memory.id,
        action="INSERT",
        new_state=payload,
        reason="Manual creation via API"
    )
    db.add(audit_entry)
    db.commit()

    # Invalidate cache
    cache.clear_pattern("profile_*")

    return MemoryResponse(
        id=UUID(db_memory.id),
        source_id=UUID(db_memory.source_id) if db_memory.source_id else None,
        category=db_memory.category,
        content=db_memory.content,
        summary=db_memory.summary,
        verification_status=db_memory.verification_status,
        confidence_score=db_memory.confidence_score,
        privacy_level=db_memory.privacy_level,
        valid_from=db_memory.valid_from,
        valid_until=db_memory.valid_until,
        is_current=db_memory.is_current,
        structured_payload=db_memory.structured_payload,
        tags=db_memory.tags,
        created_at=db_memory.created_at,
        updated_at=db_memory.updated_at
    )


@router.get("/", response_model=List[MemoryResponse])
def list_memories(
    category: Optional[MemoryCategory] = None,
    verification_status: Optional[VerificationStatus] = None,
    is_current: Optional[bool] = True,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """List and filter personal memories with pagination."""
    query = db.query(MemoryModel)

    if category:
        query = query.filter(MemoryModel.category == category)
    if verification_status:
        query = query.filter(MemoryModel.verification_status == verification_status)
    if is_current is not None:
        query = query.filter(MemoryModel.is_current == is_current)

    records = query.order_by(MemoryModel.created_at.desc()).offset(offset).limit(limit).all()

    return [
        MemoryResponse(
            id=UUID(r.id),
            source_id=UUID(r.source_id) if r.source_id else None,
            category=r.category,
            content=r.content,
            summary=r.summary,
            verification_status=r.verification_status,
            confidence_score=r.confidence_score,
            privacy_level=r.privacy_level,
            valid_from=r.valid_from,
            valid_until=r.valid_until,
            is_current=r.is_current,
            structured_payload=r.structured_payload,
            tags=r.tags,
            created_at=r.created_at,
            updated_at=r.updated_at
        )
        for r in records
    ]


@router.get("/{memory_id}", response_model=MemoryResponse)
def get_memory(memory_id: UUID, db: Session = Depends(get_db)):
    """Retrieve a single memory by ID."""
    rec = db.query(MemoryModel).filter(MemoryModel.id == str(memory_id)).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Memory not found")

    return MemoryResponse(
        id=UUID(rec.id),
        source_id=UUID(rec.source_id) if rec.source_id else None,
        category=rec.category,
        content=rec.content,
        summary=rec.summary,
        verification_status=rec.verification_status,
        confidence_score=rec.confidence_score,
        privacy_level=rec.privacy_level,
        valid_from=rec.valid_from,
        valid_until=rec.valid_until,
        is_current=rec.is_current,
        structured_payload=rec.structured_payload,
        tags=rec.tags,
        created_at=rec.created_at,
        updated_at=rec.updated_at
    )


@router.put("/{memory_id}", response_model=MemoryResponse)
def update_memory(
    memory_id: UUID,
    update_data: MemoryUpdate,
    db: Session = Depends(get_db)
):
    """Update memory contents, status, or tags with automatic audit logging."""
    rec = db.query(MemoryModel).filter(MemoryModel.id == str(memory_id)).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Memory not found")

    prev_state = {
        "content": rec.content,
        "verification_status": rec.verification_status.value,
        "is_current": rec.is_current,
        "confidence_score": rec.confidence_score
    }

    re_embed = False
    if update_data.content is not None and update_data.content != rec.content:
        rec.content = update_data.content
        re_embed = True
    if update_data.summary is not None:
        rec.summary = update_data.summary
    if update_data.verification_status is not None:
        rec.verification_status = update_data.verification_status
    if update_data.confidence_score is not None:
        rec.confidence_score = update_data.confidence_score
    if update_data.privacy_level is not None:
        rec.privacy_level = update_data.privacy_level
    if update_data.is_current is not None:
        rec.is_current = update_data.is_current
    if update_data.structured_payload is not None:
        rec.structured_payload = update_data.structured_payload
    if update_data.tags is not None:
        rec.tags = update_data.tags

    rec.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(rec)

    # Sync to Qdrant
    if re_embed:
        new_vec = embedding_service.embed_text(rec.content)
        payload = {
            "memory_id": rec.id,
            "category": rec.category.value,
            "verification_status": rec.verification_status.value,
            "privacy_level": rec.privacy_level.value,
            "is_current": rec.is_current,
            "confidence_score": rec.confidence_score,
            "tags": rec.tags,
            "content_preview": rec.content[:200]
        }
        vector_store.upsert_memory(memory_id=memory_id, vector=new_vec, payload=payload)
    else:
        # Patch payload only
        vector_store.update_payload(
            memory_id=memory_id,
            payload_patch={
                "verification_status": rec.verification_status.value,
                "is_current": rec.is_current,
                "confidence_score": rec.confidence_score,
                "tags": rec.tags
            }
        )

    # Audit Log
    audit = MemoryAuditLogModel(
        memory_id=str(memory_id),
        action="UPDATE",
        previous_state=prev_state,
        new_state={
            "content": rec.content,
            "verification_status": rec.verification_status.value,
            "is_current": rec.is_current,
            "confidence_score": rec.confidence_score
        },
        reason=update_data.update_reason or "Direct user edit"
    )
    db.add(audit)
    db.commit()

    return MemoryResponse(
        id=UUID(rec.id),
        source_id=UUID(rec.source_id) if rec.source_id else None,
        category=rec.category,
        content=rec.content,
        summary=rec.summary,
        verification_status=rec.verification_status,
        confidence_score=rec.confidence_score,
        privacy_level=rec.privacy_level,
        valid_from=rec.valid_from,
        valid_until=rec.valid_until,
        is_current=rec.is_current,
        structured_payload=rec.structured_payload,
        tags=rec.tags,
        created_at=rec.created_at,
        updated_at=rec.updated_at
    )


@router.delete("/{memory_id}", status_code=204)
def delete_memory(memory_id: UUID, db: Session = Depends(get_db)):
    """Soft-delete memory (marks is_current=False and invalidates from vector search)."""
    rec = db.query(MemoryModel).filter(MemoryModel.id == str(memory_id)).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Memory not found")

    rec.is_current = False
    rec.valid_until = datetime.now(timezone.utc)
    db.commit()

    # Update Qdrant payload to exclude from active search
    vector_store.update_payload(memory_id=memory_id, payload_patch={"is_current": False})

    # Audit Log
    audit = MemoryAuditLogModel(
        memory_id=str(memory_id),
        action="DELETE",
        previous_state={"is_current": True},
        new_state={"is_current": False},
        reason="User requested deletion"
    )
    db.add(audit)
    db.commit()
    return None
