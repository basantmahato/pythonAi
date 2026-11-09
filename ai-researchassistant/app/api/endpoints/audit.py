from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.models.database import MemoryAuditLogModel
from app.models.schemas import AuditLogResponse
from app.storage.db import get_db

router = APIRouter(prefix="/audit", tags=["Audit Log"])


@router.get("/logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    memory_id: Optional[UUID] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """Retrieve audit trail of changes, status elevations, and deletions."""
    query = db.query(MemoryAuditLogModel)

    if memory_id:
        query = query.filter(MemoryAuditLogModel.memory_id == str(memory_id))

    records = query.order_by(MemoryAuditLogModel.created_at.desc()).offset(offset).limit(limit).all()

    return [
        AuditLogResponse(
            id=UUID(r.id),
            memory_id=UUID(r.memory_id),
            action=r.action,
            previous_state=r.previous_state,
            new_state=r.new_state,
            actor=r.actor,
            reason=r.reason,
            timestamp=r.created_at
        )
        for r in records
    ]
