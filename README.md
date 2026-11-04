# Python AI & Machine Learning Engineering Workspace

Welcome to the **Python AI & Machine Learning Workspace**. This repository contains production-ready AI/ML systems, microservices, and experimentation pipelines.

---

## 📂 Workspace Projects

```
pythonAi/
│
├── ai-model/                     # Project 01: House Price Prediction (Classical ML System)
│   ├── ml-training/              # Dataset, EDA, training pipeline & .pkl artifacts
│   ├── ml-service/               # Tier 1: Private ML Inference Microservice (Port 8001)
│   ├── core-backend/             # Tier 2: Core Business Logic & Orchestrator (Port 8000)
│   ├── frontend/                 # Tier 3: React + Vite Interactive Valuation Dashboard
│   ├── docker-compose.yml        # Full-stack container orchestration
│   ├── test_microservices.py     # Automated API Key & integration test suite
│   ├── run_all.bat               # 1-Click launcher for all 3 tiers
│   └── README.md                 # Detailed project documentation
│
├── ai-backend/                   # LLM & Vector Retrieval Service (ChromaDB + FastAPI)
│   ├── src/                      # Controllers, routes & vector services
│   └── data/                     # Vector embeddings database
│
├── .gitignore                    # Comprehensive Python, Node.js, & secrets ignore rules
└── README.md                     # Workspace index (this file)
```

---

## 🚀 Project 01: House Price Prediction (Classical ML)

An enterprise multi-tier architecture demonstrating how to train a machine learning model from scratch and deploy it as a production microservice.

### System Architecture

```
                    ┌─────────────────────────────────┐
                    │     React Frontend (Vite)       │
                    │      http://localhost:5173      │
                    │   Interactive Valuation UI      │
                    └───────────────┬─────────────────┘
                                    │ HTTP / JSON
                                    ▼
                    ┌─────────────────────────────────┐
                    │      Core Business Backend      │
                    │     http://127.0.0.1:8000       │
                    │  • Orchestration & Analytics    │
                    │  • 30-Yr Mortgage Calculations  │
                    │  • Property Tax & Closing Costs │
                    │  • Holds Private ML API Key     │
                    └───────────────┬─────────────────┘
                                    │ Private Network Link
                                    │ Header: X-API-Key: ml_live_key_...
                                    ▼
                    ┌─────────────────────────────────┐
                    │    ML Inference Microservice    │
                    │     http://127.0.0.1:8001       │
                    │  • Protected by X-API-Key Guard │
                    │  • Scikit-Learn LinearReg Model │
                    │  • Pure Sub-Millisecond AI      │
                    └───────────────┬─────────────────┘
                                    │ Loads .pkl
                                    ▼
                    ┌─────────────────────────────────┐
                    │     Trained Model Artifact      │
                    │      house_price_model.pkl      │
                    └─────────────────────────────────┘
```

---

## ⚡ Quick Start (`ai-model`)

### 1. 1-Click Launch (Windows)
Double-click [`ai-model/run_all.bat`](file:///c:/Users/basant/Documents/Basant/pythonAi/ai-model/run_all.bat). It automatically opens all 3 services in separate windows:
* **Web Dashboard**: [http://localhost:5173](http://localhost:5173)
* **Core Business API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ML Service API Docs**: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs) *(Requires `X-API-Key`)*

### 2. Manual Terminal Start
```bash
# Terminal 1 — Start ML Inference Microservice (Port 8001)
cd ai-model/ml-service
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8001

# Terminal 2 — Start Core Business Backend (Port 8000)
cd ai-model/core-backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Terminal 3 — Start React Frontend (Port 5173)
cd ai-model/frontend
npm run dev
```

### 3. Run Automated Tests
```bash
cd ai-model
python test_microservices.py
```

---

## 🛠️ Technology Stack

| Domain | Technology | Purpose |
| :--- | :--- | :--- |
| **Machine Learning** | **Scikit-Learn**, **NumPy**, **Pandas** | Model training, evaluation ($R^2 = 0.998$), data cleaning |
| **Model Persistence** | **Joblib** | Serializes trained model into reusable `.pkl` artifact |
| **Inference Microservice** | **FastAPI**, **Uvicorn**, **Pydantic** | Authenticated sub-millisecond model inference (`X-API-Key`) |
| **Business Backend** | **FastAPI**, **HTTPX** | Microservice orchestration, financial analytics & mortgage logic |
| **Frontend UI** | **React**, **Vite**, **Lucide Icons** | Real-time interactive valuation calculator with health badges |
| **DevOps / Containers** | **Docker**, **Docker Compose**, **Nginx** | Production containerization & reverse proxy |

---

## 🗺️ Learning Roadmap & Upcoming Projects

1. **Project 01 (Completed)**: House Price Prediction — Classical Regression & Multi-Tier Microservices
2. **Project 02**: Customer Churn Predictor — Binary Classification with **XGBoost**
3. **Project 03**: Credit Card Fraud Detection — Imbalanced Data & Real-Time Scoring
4. **Project 04**: Customer Segmentation — Unsupervised **K-Means Clustering** & PCA
5. **Project 05**: Document RAG Assistant — Vector Databases (**ChromaDB**) & Generative AI

