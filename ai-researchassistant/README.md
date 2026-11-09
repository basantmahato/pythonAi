# Personal Intelligence System (PIS)

A personalized RAG-based intelligence system that acts as an external memory, learning assistant, knowledge manager, and career intelligence system.

## Features

- **Dual-Store Architecture**: PostgreSQL for authoritative relational storage and audit trail; Qdrant for dense semantic vector search.
- **7-Category Memory Taxonomy**:
  1. `IDENTITY`: Core profile facts and immutable background.
  2. `SEMANTIC_KNOWLEDGE`: Concepts, frameworks, and domain knowledge.
  3. `EPISODIC`: Discrete past events, milestones, and decisions.
  4. `PROCEDURAL`: Work conventions, coding standards, and methods.
  5. `GOAL_CAREER`: Short- and long-term career aspirations and OKRs.
  6. `PROJECT`: System architectures, repositories, and technical deliverables.
  7. `PREFERENCE`: Tools, tone, learning styles, and habits.
- **Strict Epistemic Invariants**: Verified facts, user-stated notes, historical conditions, and AI-inferred deductions are strictly separated. Inferences are capped and never silently converted to verified truth.
- **Hallucination Prevention**: Multi-stage hybrid retrieval with temporal resolution, explicit citation generation (`[Memory: <id>]`), and mandatory admission when information is missing.
- **Model Agnostic**: Defaults to local **Ollama** (`llama3.2:3b`), with pluggable support for OpenAI or Claude.

## Quick Start

### 1. Environment Configuration
Copy `.env.example` to `.env` and verify settings:
```bash
cp .env.example .env
```

### 2. Launch Supporting Services (Docker)
```bash
docker compose up -d
```
*(Note: If Docker is not running, the system automatically falls back to embedded SQLite and local Qdrant disk storage).*

### 3. Start API Server
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Interactive API Docs
Open your browser to:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Ingesting Your Personal Knowledge

### Ingesting Personal Notes / Bio
```bash
curl -X POST http://localhost:8000/api/v1/ingest/text \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Bio & Career Goals 2026",
    "content": "My name is Basant. I am building a personal learning AI assistant. My primary career goal is to master agentic workflows and deploy production-grade RAG architectures.",
    "default_verification_status": "VERIFIED_FACT"
  }'
```

### Asking Grounded Questions
```bash
curl -X POST http://localhost:8000/api/v1/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are my primary career goals and what project am I building?"
  }'
```
