from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator, ConfigDict


class MemoryCategory(str, Enum):
    IDENTITY = "IDENTITY"
    SEMANTIC_KNOWLEDGE = "SEMANTIC_KNOWLEDGE"
    EPISODIC = "EPISODIC"
    PROCEDURAL = "PROCEDURAL"
    GOAL_CAREER = "GOAL_CAREER"
    PROJECT = "PROJECT"
    PREFERENCE = "PREFERENCE"


class VerificationStatus(str, Enum):
    VERIFIED_FACT = "VERIFIED_FACT"        # Confirmed truth, user-approved
    USER_STATED = "USER_STATED"            # Stated by user in conversation
    HISTORICAL = "HISTORICAL"              # Superseded or past state
    AI_INFERRED = "AI_INFERRED"            # Extracted by model from context


class PrivacyLevel(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class SourceType(str, Enum):
    FILE_MD = "FILE_MD"
    FILE_PDF = "FILE_PDF"
    FILE_JSON = "FILE_JSON"
    CONVERSATION = "CONVERSATION"
    MANUAL_ENTRY = "MANUAL_ENTRY"


class MemoryRelationType(str, Enum):
    SUPERSEDES = "SUPERSEDES"
    SUPPORTS = "SUPPORTS"
    DEPENDS_ON = "DEPENDS_ON"
    CONTRADICTS = "CONTRADICTS"
    DERIVED_FROM = "DERIVED_FROM"


# --- Source Schemas ---

class SourceBase(BaseModel):
    source_type: SourceType
    title: str
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SourceCreate(SourceBase):
    raw_content: Optional[str] = None


class SourceResponse(SourceBase):
    id: UUID
    content_hash: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Memory Schemas ---

class MemoryBase(BaseModel):
    category: MemoryCategory
    content: str
    summary: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.USER_STATED
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    privacy_level: PrivacyLevel = PrivacyLevel.INTERNAL
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_current: bool = True
    structured_payload: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    @field_validator("confidence_score")
    @classmethod
    def validate_inferred_confidence(cls, v: float, info) -> float:
        # If AI_INFERRED, enforce reasonable confidence cap
        status = info.data.get("verification_status")
        if status == VerificationStatus.AI_INFERRED and v > 0.85:
            # Inferred facts start capped until user verification
            return 0.85
        return v


class MemoryCreate(MemoryBase):
    source_id: Optional[UUID] = None


class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    summary: Optional[str] = None
    verification_status: Optional[VerificationStatus] = None
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    privacy_level: Optional[PrivacyLevel] = None
    valid_until: Optional[datetime] = None
    is_current: Optional[bool] = None
    structured_payload: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    update_reason: Optional[str] = None


class MemoryResponse(MemoryBase):
    id: UUID
    source_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemoryFilter(BaseModel):
    categories: Optional[List[MemoryCategory]] = None
    verification_statuses: Optional[List[VerificationStatus]] = None
    is_current: Optional[bool] = True
    max_privacy_level: PrivacyLevel = PrivacyLevel.INTERNAL
    tags: Optional[List[str]] = None
    search_query: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# --- Relation Schemas ---

class MemoryRelationCreate(BaseModel):
    source_memory_id: UUID
    target_memory_id: UUID
    relation_type: MemoryRelationType
    confidence: float = 1.0


class MemoryRelationResponse(BaseModel):
    id: UUID
    source_memory_id: UUID
    target_memory_id: UUID
    relation_type: MemoryRelationType
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Audit Log Schemas ---

class AuditLogResponse(BaseModel):
    id: UUID
    memory_id: UUID
    action: str
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    actor: str = "SYSTEM"
    reason: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Goals & Milestones Schemas ---

class GoalTimeframe(str, Enum):
    SHORT_TERM = "SHORT_TERM"
    MEDIUM_TERM = "MEDIUM_TERM"
    LONG_TERM = "LONG_TERM"


class GoalStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"
    PAUSED = "PAUSED"


class GoalMilestoneCreate(BaseModel):
    title: str
    description: Optional[str] = None
    timeframe: GoalTimeframe = GoalTimeframe.SHORT_TERM
    status: GoalStatus = GoalStatus.ACTIVE
    target_date: Optional[datetime] = None
    progress_percent: int = Field(default=0, ge=0, le=100)
    kpis: List[Dict[str, Any]] = Field(default_factory=list)


class GoalMilestoneResponse(GoalMilestoneCreate):
    id: UUID
    memory_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Project Registry Schemas ---

class ProjectStatus(str, Enum):
    IDEA = "IDEA"
    IN_PROGRESS = "IN_PROGRESS"
    SHIPPED = "SHIPPED"
    MAINTENANCE = "MAINTENANCE"


class ProjectRecordCreate(BaseModel):
    name: str
    status: ProjectStatus = ProjectStatus.IN_PROGRESS
    tech_stack: List[str] = Field(default_factory=list)
    repo_url: Optional[str] = None
    outcomes: Optional[str] = None


class ProjectRecordResponse(ProjectRecordCreate):
    id: UUID
    memory_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Grounded Query & Anti-Hallucination Schemas ---

class MemoryCitation(BaseModel):
    memory_id: UUID
    category: MemoryCategory
    verification_status: VerificationStatus
    content_snippet: str
    relevance_score: float


class GroundedQueryRequest(BaseModel):
    query: str
    categories: Optional[List[MemoryCategory]] = None
    include_historical: bool = False
    max_memories: int = Field(default=8, ge=1, le=25)


class GroundedQueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[MemoryCitation]
    inferred_recommendations: List[str] = Field(default_factory=list)
    conflicts_detected: List[str] = Field(default_factory=list)
    grounded: bool
    model_used: str


# --- Conflict Detection Schemas ---

class ConflictDetectionResult(BaseModel):
    has_conflict: bool
    existing_memory_id: Optional[UUID] = None
    conflicting_statement: Optional[str] = None
    similarity_score: float = 0.0
    action_suggested: str = "PROCEED"  # "PROCEED", "SUPERSEDE", "FLAG_FOR_REVIEW"
