from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Enum as SQLEnum,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, ARRAY
from sqlalchemy.orm import declarative_base, relationship

from app.models.schemas import (
    MemoryCategory,
    VerificationStatus,
    PrivacyLevel,
    SourceType,
    MemoryRelationType,
    GoalTimeframe,
    GoalStatus,
    ProjectStatus,
)

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class SourceModel(Base):
    __tablename__ = "sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_type = Column(SQLEnum(SourceType), nullable=False)
    title = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=True)
    content_hash = Column(String(64), unique=True, nullable=False, index=True)
    raw_content = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    memories = relationship("MemoryModel", back_populates="source", cascade="all, delete-orphan")


class MemoryModel(Base):
    __tablename__ = "memories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    category = Column(SQLEnum(MemoryCategory), nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(String(512), nullable=True)

    # Epistemic & Trust
    verification_status = Column(
        SQLEnum(VerificationStatus),
        nullable=False,
        default=VerificationStatus.USER_STATED,
        index=True
    )
    confidence_score = Column(Float, default=1.0, nullable=False)
    privacy_level = Column(
        SQLEnum(PrivacyLevel),
        nullable=False,
        default=PrivacyLevel.INTERNAL
    )

    # Temporal
    valid_from = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    valid_until = Column(DateTime(timezone=True), nullable=True)
    is_current = Column(Boolean, default=True, nullable=False, index=True)

    # Dynamic payload & tags
    structured_payload = Column(JSON, default=dict)
    tags = Column(JSON, default=list)  # stored as JSON list for SQLite/Postgres portability

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    source = relationship("SourceModel", back_populates="memories")
    goals = relationship("GoalMilestoneModel", back_populates="memory", cascade="all, delete-orphan")
    projects = relationship("ProjectModel", back_populates="memory", cascade="all, delete-orphan")


class MemoryRelationModel(Base):
    __tablename__ = "memory_relations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_memory_id = Column(String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    target_memory_id = Column(String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(SQLEnum(MemoryRelationType), nullable=False)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class MemoryAuditLogModel(Base):
    __tablename__ = "memory_audit_log"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    memory_id = Column(String(36), nullable=False, index=True)
    action = Column(String(20), nullable=False)  # INSERT, UPDATE, SUPERSEDE, DELETE, VERIFY
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)
    actor = Column(String(50), default="SYSTEM")
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class GoalMilestoneModel(Base):
    __tablename__ = "goals_and_milestones"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    memory_id = Column(String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    timeframe = Column(SQLEnum(GoalTimeframe), default=GoalTimeframe.SHORT_TERM)
    status = Column(SQLEnum(GoalStatus), default=GoalStatus.ACTIVE)
    target_date = Column(DateTime(timezone=True), nullable=True)
    progress_percent = Column(Integer, default=0)
    kpis = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    memory = relationship("MemoryModel", back_populates="goals")


class ProjectModel(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    memory_id = Column(String(36), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.IN_PROGRESS)
    tech_stack = Column(JSON, default=list)
    repo_url = Column(Text, nullable=True)
    outcomes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    memory = relationship("MemoryModel", back_populates="projects")
