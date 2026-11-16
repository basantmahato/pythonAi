# Python AI & Machine Learning Engineering Workspace

Welcome to the **Python AI & Machine Learning Workspace** — a collection of production-ready AI/ML systems, agentic pipelines, RAG architectures, and microservice backends.

---

## 📂 Workspace Structure

```
pythonAi/
│
├── ai-model/                     # Project 01 — House Price Prediction (Classical ML System)
│   ├── ml-training/              # Dataset, EDA, training pipeline & .pkl artifacts
│   ├── ml-service/               # Tier 1: Private ML Inference Microservice (Port 8001)
│   ├── core-backend/             # Tier 2: Core Business Logic & Orchestrator (Port 8000)
│   ├── frontend/                 # Tier 3: React + Vite Interactive Valuation Dashboard
│   ├── docker-compose.yml        # Full-stack container orchestration
│   ├── run_all.bat               # 1-Click launcher for all 3 tiers (Windows)
│   └── README.md                 # Detailed project documentation
│
├── ai-backend/                   # Project 02 — LLM Chat Backend (Ollama + ChromaDB)
│   ├── src/                      # Controllers, routes & vector services
│   └── data/                     # ChromaDB vector embeddings store
│
├── agenticRag/                   # Project 03 — Agentic RAG System (Gemini + Qdrant)
│   └── backend/
│       ├── src/
│       │   ├── config/           # App settings & environment loader
│       │   ├── controller/       # Ingestion & RAG controllers
│       │   ├── models/           # Pydantic schemas
│       │   ├── repository/       # Qdrant vector store repository
│       │   └── services/         # Chunker, Embedder, LLM, Loader, RAG services
│       ├── main.py               # FastAPI app entrypoint
│       ├── docker-compose.yml    # Qdrant container orchestration
│       └── .env                  # API keys & configuration
│
├── ai-researchassistant/         # Project 04 — Personal Intelligence System (PIS)
│   ├── app/                      # FastAPI app (api, core, models, services, storage)
│   ├── frontend/                 # Vanilla JS + HTML UI
│   ├── tests/                    # API, schema & vector store tests
│   ├── cli.py                    # Interactive CLI interface
│   ├── demo_live_run.py          # Live demo runner
│   ├── docker-compose.yml        # PostgreSQL + Qdrant services
│   └── README.md                 # Detailed project documentation
│
├── .gitignore                    # Python, Node.js & secrets ignore rules
└── README.md                     # Workspace index (this file)
```

---

## 🏗️ Projects Overview

### Project 01 — House Price Prediction (Classical ML)

An enterprise multi-tier architecture demonstrating end-to-end ML — from training a Scikit-Learn model to deploying it as a secured production microservice behind an API key guard.

**Architecture:**
```
  React Frontend (Vite)       http://localhost:5173
         │ HTTP / JSON
         ▼
  Core Business Backend       http://127.0.0.1:8000
  • Orchestration & Analytics
  • 30-Yr Mortgage Calculations
  • Property Tax & Closing Costs
  • Holds Private ML API Key
         │ X-API-Key (private network)
         ▼
  ML Inference Microservice   http://127.0.0.1:8001
  • Protected by X-API-Key Guard
  • Scikit-Learn LinearRegression Model
  • Sub-millisecond inference
         │ Loads .pkl
         ▼
  Trained Model Artifact      house_price_model.pkl
```

**Quick Start:**
```bash
# 1-Click (Windows) — opens all 3 tiers in separate terminals
ai-model/run_all.bat

# Manual
cd ai-model/ml-service && python -m uvicorn main:app --host 127.0.0.1 --port 8001
cd ai-model/core-backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000
cd ai-model/frontend && npm run dev
```

---

### Project 02 — LLM Chat Backend (Ollama + ChromaDB)

A FastAPI backend wiring a **local Ollama LLM** to a **ChromaDB** vector memory store, exposing a clean REST API for chat and semantic retrieval.

**Stack:** FastAPI · Uvicorn · Ollama · ChromaDB · Pydantic · python-dotenv

**Quick Start:**
```bash
cd ai-backend
# Start Ollama (separately) then:
python -m uvicorn src.main:app --reload
# API Docs → http://localhost:8000/docs
```

---

### Project 03 — Agentic RAG System (Gemini + Qdrant)

A **self-correcting, agentic Retrieval-Augmented Generation** pipeline powered by the **Gemini API** and **Qdrant** vector database. Features an intelligent correction loop that grades retrieved documents, rewrites queries when retrieval quality is poor, and performs hallucination checks before returning answers.

**Pipeline Flow:**
```
User Query
    │
    ▼
[Embedder]  →  text-embedding-004 (768-dim)
    │
    ▼
[Qdrant Search]  →  Top-K semantic retrieval
    │
    ▼
[Document Grader]  →  LLM relevance scoring
    │                  ↑ No relevant chunks?
    ▼                  │
[Query Rewriter]  ─────┘ (up to MAX_CORRECTION_RETRIES)
    │
    ▼
[Answer Generator]  →  Gemini 2.5 Flash
    │
    ▼
[Hallucination Check]  →  Grounded vs. fabricated
    │
    ▼
[Answer Quality Check]  →  Addresses original query?
    │
    ▼
Final Response (with chunk citations & metadata)
```

**Services:**
| Service | Description |
|---|---|
| `chunker.py` | Splits documents into overlapping semantic chunks |
| `embedder.py` | Generates 768-dim embeddings via Gemini `text-embedding-004` |
| `ingestion_service.py` | Loads, chunks & indexes documents into Qdrant |
| `rag_service.py` | Self-correcting RAG loop with grading & hallucination checks |
| `llm_service.py` | Gemini LLM calls: answer generation, grading, rewriting |

**Quick Start:**
```bash
cd agenticRag/backend

# 1. Copy & fill in your Gemini API key
cp .env .env.local   # edit GEMINI_API_KEY

# 2. Start Qdrant vector store
docker compose up -d

# 3. Start the API
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 4. Open API docs
# http://localhost:8000/docs
```

**Key config (`.env`):**
```env
GEMINI_API_KEY="your_key_here"
LLM_MODEL="gemini-2.5-flash"
EMBEDDING_MODEL="text-embedding-004"
QDRANT_COLLECTION_NAME="agentic_rag_docs"
MAX_CORRECTION_RETRIES=2
```

---

### Project 04 — Personal Intelligence System (PIS)

A personalized RAG-based intelligence system acting as an **external memory, learning assistant, knowledge manager, and career intelligence layer**. Features a strict epistemic model that separates verified facts from AI inferences and prevents hallucination through multi-stage hybrid retrieval.

**Architecture:**
- **Dual-Store**: PostgreSQL (relational/audit) + Qdrant (semantic vector search)
- **Fallback**: Automatic SQLite + local Qdrant disk when Docker is unavailable
- **LLM**: Local Ollama (`llama3.2:3b`) by default; pluggable OpenAI / Claude

**7-Category Memory Taxonomy:**
| Category | Description |
|---|---|
| `IDENTITY` | Core profile facts & immutable background |
| `SEMANTIC_KNOWLEDGE` | Concepts, frameworks & domain knowledge |
| `EPISODIC` | Past events, milestones & decisions |
| `PROCEDURAL` | Work conventions, coding standards & methods |
| `GOAL_CAREER` | Short- & long-term career aspirations & OKRs |
| `PROJECT` | System architectures, repos & technical deliverables |
| `PREFERENCE` | Tools, tone, learning styles & habits |

**Quick Start:**
```bash
cd ai-researchassistant

# 1. Configure environment
cp .env.example .env

# 2. Start supporting services
docker compose up -d

# 3. Start API
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Ingest personal knowledge
curl -X POST http://localhost:8000/api/v1/ingest/text \
  -H "Content-Type: application/json" \
  -d '{"title": "My Bio", "content": "...", "default_verification_status": "VERIFIED_FACT"}'

# 5. Query
curl -X POST http://localhost:8000/api/v1/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What are my primary career goals?"}'
```

**Interfaces:** REST API (`/docs`) · Swagger UI · ReDoc · CLI (`cli.py`) · Frontend UI

---

## 🛠️ Full Technology Stack

| Domain | Technology | Used In |
| :--- | :--- | :--- |
| **ML / Training** | Scikit-Learn, NumPy, Pandas, Joblib | ai-model |
| **LLM (Cloud)** | Gemini 2.5 Flash, `text-embedding-004` | agenticRag |
| **LLM (Local)** | Ollama (`llama3.2:3b`) | ai-backend, ai-researchassistant |
| **Vector DB** | Qdrant | agenticRag, ai-researchassistant |
| **Vector DB** | ChromaDB | ai-backend |
| **Relational DB** | PostgreSQL / SQLite (fallback) | ai-researchassistant |
| **API Framework** | FastAPI, Uvicorn, Pydantic | All projects |
| **Frontend** | React, Vite, Lucide Icons | ai-model |
| **Frontend** | Vanilla JS, HTML, CSS | ai-researchassistant |
| **DevOps** | Docker, Docker Compose, Nginx | ai-model, agenticRag, ai-researchassistant |
| **Testing** | Pytest | ai-researchassistant, ai-model |

---

## 📡 Port Map

| Project | Service | Port |
|---|---|---|
| ai-model | React Frontend | `5173` |
| ai-model | Core Business Backend | `8000` |
| ai-model | ML Inference Service | `8001` |
| ai-backend | LLM Chat API | `8000` |
| agenticRag | Agentic RAG API | `8000` |
| agenticRag | Qdrant | `6333` |
| ai-researchassistant | PIS API | `8000` |
| ai-researchassistant | Qdrant | `6333` |
| ai-researchassistant | PostgreSQL | `5432` |

> [!NOTE]
> Run each project in its own virtual environment to avoid dependency conflicts. Projects using port `8000` cannot run simultaneously without port remapping.
