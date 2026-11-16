from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

# Ingestion Schemas
class DocumentChunk(BaseModel):
    chunk_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IngestTextRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Raw text content to ingest")
    title: Optional[str] = Field(default="untitled", description="Document title or identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional custom metadata")

class IngestResponse(BaseModel):
    status: str
    message: str
    source_name: str
    total_chunks: int
    collection: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Retrieval & Self-Correcting RAG Schemas
class RetrievedChunk(BaseModel):
    id: str
    content: str
    score: float
    source: str = "unknown"
    chunk_index: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RagQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="User question or query")
    top_k: Optional[int] = Field(default=None, ge=1, le=20, description="Number of chunks to retrieve")
    enable_self_correction: bool = Field(default=True, description="Enable grading, query rewrite, and hallucination checks")

class RagQueryResponse(BaseModel):
    original_query: str
    final_query: str
    rewritten_queries: List[str] = Field(default_factory=list)
    retrieved_chunks: List[RetrievedChunk] = Field(default_factory=list)
    relevant_chunks_count: int
    answer: str
    is_grounded: bool
    addresses_query: bool
    iterations: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
