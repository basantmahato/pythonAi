import pytest
import shutil
from pathlib import Path
from uuid import uuid4
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.storage.vector_store import QdrantVectorStore


@pytest.fixture
def test_vector_store(tmp_path):
    # Create isolated Qdrant vector store in temp directory
    test_client = QdrantClient(path=str(tmp_path / "qdrant_test"))
    store = QdrantVectorStore(
        client=test_client,
        collection_name="test_memories",
        vector_dim=4
    )
    return store


def test_upsert_and_search_with_filter(test_vector_store):
    store = test_vector_store
    m_id1 = uuid4()
    m_id2 = uuid4()

    # Memory 1: Active Goal
    store.upsert_memory(
        memory_id=m_id1,
        vector=[1.0, 0.0, 0.0, 0.0],
        payload={
            "memory_id": str(m_id1),
            "category": "GOAL_CAREER",
            "is_current": True,
            "verification_status": "VERIFIED_FACT",
            "content_preview": "Ship personal AI project"
        }
    )

    # Memory 2: Historical / Inactive
    store.upsert_memory(
        memory_id=m_id2,
        vector=[0.9, 0.1, 0.0, 0.0],
        payload={
            "memory_id": str(m_id2),
            "category": "GOAL_CAREER",
            "is_current": False,
            "verification_status": "HISTORICAL",
            "content_preview": "Old completed milestone"
        }
    )

    # Search current only
    results = store.search_memories(
        query_vector=[1.0, 0.0, 0.0, 0.0],
        limit=5,
        is_current_only=True
    )

    assert len(results) == 1
    assert results[0]["memory_id"] == str(m_id1)


def test_payload_update(test_vector_store):
    store = test_vector_store
    m_id = uuid4()

    store.upsert_memory(
        memory_id=m_id,
        vector=[0.0, 1.0, 0.0, 0.0],
        payload={
            "memory_id": str(m_id),
            "category": "PROJECT",
            "is_current": True
        }
    )

    # Invalidate
    store.update_payload(m_id, {"is_current": False})

    active = store.search_memories(
        query_vector=[0.0, 1.0, 0.0, 0.0],
        is_current_only=True
    )
    assert len(active) == 0
