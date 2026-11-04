# House Price Prediction — Enterprise Multi-Tier AI Architecture

An enterprise-grade, microservice-based Machine Learning system built with **FastAPI**, **Scikit-Learn**, **React**, and **Docker**.

---

## 1. Enterprise Architecture

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
                    │  • Business Logic & Analytics   │
                    │  • 30-Yr Mortgage Calculations  │
                    │  • Property Tax & Closing Costs │
                    │  • Holds Private ML API Key     │
                    └───────────────┬─────────────────┘
                                    │ Private Network
                                    │ X-API-Key: ml_live_key_...
                                    ▼
                    ┌─────────────────────────────────┐
                    │    ML Inference Microservice    │
                    │     http://127.0.0.1:8001       │
                    │  • Authenticated via API Key    │
                    │  • Scikit-Learn LinearReg Model │
                    │  • Pure AI Model Inference      │
                    └───────────────┬─────────────────┘
                                    │ Loads .pkl
                                    ▼
                    ┌─────────────────────────────────┐
                    │     Trained Model Artifact      │
                    │      house_price_model.pkl      │
                    └─────────────────────────────────┘
```

---

## 2. Directory Structure

```
ai-model/
├── .venv/                         # Dedicated Python virtual environment
├── ml-training/                   # Machine learning model pipeline
│   ├── data/
│   │   └── house_prices.csv       # Training & evaluation dataset
│   ├── notebooks/
│   │   └── train_model.ipynb      # Step-by-step interactive Jupyter notebook
│   ├── models/
│   │   └── house_price_model.pkl  # Serialized Scikit-Learn model artifact
│   ├── train.py                   # Automated CLI training script
│   └── requirements.txt           # ML library dependencies
├── ml-service/                    # Tier 1: Authenticated ML Inference Microservice (Port 8001)
│   ├── main.py                    # Protected /predict endpoint (requires X-API-Key)
│   ├── ml_schemas.py              # Pydantic inference schemas
│   ├── Dockerfile                 # Production Docker image
│   ├── .env                       # ML Service configuration & secret key
│   └── requirements.txt           # Dependencies
├── core-backend/                  # Tier 2: Core Business Logic Backend (Port 8000)
│   ├── main.py                    # Orchestration, mortgage, tax & property tiers
│   ├── core_schemas.py            # Business validation & financial breakdown schemas
│   ├── Dockerfile                 # Production Docker image
│   ├── .env                       # Core backend config & ML service API Key
│   └── requirements.txt           # Dependencies
├── frontend/                      # Tier 3: React + Vite Interactive Dashboard (Port 5173 / 3000)
│   ├── src/
│   │   ├── App.jsx                # Main dashboard with live service badges
│   │   ├── main.jsx               # React entrypoint
│   │   └── index.css              # Modern UI styling & typography
│   ├── Dockerfile                 # Multi-stage production Nginx container
│   ├── nginx.conf                 # Production Nginx reverse-proxy configuration
│   ├── package.json               # Dependencies
│   └── vite.config.js             # Vite configuration
├── docker-compose.yml             # 3-Tier Container Orchestration
├── test_microservices.py          # Integration test verifying API Key security
├── run_all.bat                    # 1-Click launcher for all 3 services
├── run_ml_service.bat             # 1-Click launcher for ML service (Port 8001)
├── run_core_backend.bat           # 1-Click launcher for Core Backend (Port 8000)
├── run_frontend.bat               # 1-Click launcher for Frontend (Port 5173)
├── run_training.bat               # 1-Click launcher for ML training
├── run_jupyter.bat                # 1-Click launcher for JupyterLab
├── .gitignore
└── README.md
```

---

## 3. Microservice Security Specification

The **ML Inference Service** (`port 8001`) is private and protected by an API Key header:

| Header Name | Value | Purpose |
| :--- | :--- | :--- |
| `X-API-Key` | `ml_live_key_9f82d1c87e4a3b10` | Authenticates callers to the raw ML engine |

* **Missing Key**: Returns `401 Unauthorized` (`Missing 'X-API-Key' header`).
* **Invalid Key**: Returns `403 Forbidden` (`Invalid 'X-API-Key'`).
* **Valid Key**: Returns `200 OK` with model prediction.

The **Core Business Backend** holds this secret key server-side. Public clients (such as browsers or mobile devices) never see or expose the ML API key.

---

## 4. How to Run

### Option A — 1-Click Launcher (Windows)
Double-click **`run_all.bat`**. It launches:
1. `ml-service` on `http://127.0.0.1:8001`
2. `core-backend` on `http://127.0.0.1:8000`
3. `frontend` on `http://localhost:5173`

### Option B — Run Integration Tests
Verify API Key enforcement and business logic across both backends:
```bash
python test_microservices.py
```

### Option C — Production Docker Compose
Launch the entire 3-tier containerized stack with one command:
```bash
docker-compose up --build
```
* **Web UI (Nginx)**: `http://localhost:3000`
* **Core Business API**: `http://localhost:8000/docs`
* **ML Inference Service**: `http://localhost:8001/docs`
