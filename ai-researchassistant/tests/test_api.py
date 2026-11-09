import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.storage.db import init_db

# Ensure database tables exist for tests
init_db()

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "vector_collection" in data


def test_create_and_fetch_memory():
    payload = {
        "category": "IDENTITY",
        "content": "Basant is an AI engineer focused on personalized intelligence systems.",
        "summary": "Core identity and professional focus",
        "verification_status": "VERIFIED_FACT",
        "confidence_score": 1.0,
        "privacy_level": "INTERNAL",
        "tags": ["identity", "ai", "engineer"]
    }
    create_res = client.post("/api/v1/memories/", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["category"] == "IDENTITY"
    assert created_data["verification_status"] == "VERIFIED_FACT"
    mem_id = created_data["id"]

    # Fetch by ID
    get_res = client.get(f"/api/v1/memories/{mem_id}")
    assert get_res.status_code == 200
    assert get_res.json()["content"] == payload["content"]


def test_unsupported_query_returns_clear_admission():
    # When querying something with no matching memory
    query_payload = {
        "query": "What is my favorite Martian recipe from 1820?",
        "categories": ["PREFERENCE"],
        "include_historical": False,
        "max_memories": 5
    }
    query_res = client.post("/api/v1/query/", json=query_payload)
    assert query_res.status_code == 200
    data = query_res.json()
    assert data["grounded"] is True
    # System must admit lack of verified personal information
    assert "do not have verified personal" in data["answer"].lower()
