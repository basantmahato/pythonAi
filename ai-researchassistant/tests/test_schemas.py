import pytest
from uuid import uuid4
from app.models.schemas import (
    MemoryCategory,
    MemoryCreate,
    VerificationStatus,
    PrivacyLevel,
)


def test_memory_category_validation():
    # Valid categories
    valid = MemoryCreate(
        category=MemoryCategory.IDENTITY,
        content="Basant is an AI engineer focused on personalized intelligence.",
        verification_status=VerificationStatus.VERIFIED_FACT
    )
    assert valid.category == MemoryCategory.IDENTITY
    assert valid.verification_status == VerificationStatus.VERIFIED_FACT


def test_ai_inferred_confidence_cap():
    # Rule: AI_INFERRED facts cannot start with confidence > 0.85
    mem = MemoryCreate(
        category=MemoryCategory.GOAL_CAREER,
        content="May be interested in autonomous agentic workflows.",
        verification_status=VerificationStatus.AI_INFERRED,
        confidence_score=0.99
    )
    assert mem.confidence_score <= 0.85


def test_verified_fact_full_confidence():
    # Verified facts can have 1.0 confidence
    mem = MemoryCreate(
        category=MemoryCategory.IDENTITY,
        content="Primary email: basant@example.com",
        verification_status=VerificationStatus.VERIFIED_FACT,
        confidence_score=1.0
    )
    assert mem.confidence_score == 1.0
