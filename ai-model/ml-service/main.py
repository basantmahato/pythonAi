import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import joblib
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader

from ml_schemas import HealthResponse, PredictionRequest, PredictionResponse

# Configuration & Security
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = BASE_DIR.parent / "ml-training" / "models" / "house_price_model.pkl"
MODEL_PATH = Path(os.getenv("MODEL_PATH", str(DEFAULT_MODEL_PATH)))

# Secret API Key required to query this ML service
API_KEY_NAME = "X-API-Key"
VALID_API_KEY = os.getenv("ML_SERVICE_API_KEY", "ml_live_key_9f82d1c87e4a3b10")

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Global model state
model = None


def load_model_from_disk(path: Path):
    """Load joblib trained model from disk if file exists."""
    if not path.is_file():
        return None
    try:
        loaded = joblib.load(path)
        print(f"[ML Service] Model loaded successfully from: {path}")
        return loaded
    except Exception as exc:
        print(f"[ML Service] Error loading model from {path}: {exc}")
        return None


def get_model():
    """Lazy model getter."""
    global model
    if model is None:
        model = load_model_from_disk(MODEL_PATH)
    return model


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)):
    """
    Authenticate callers using standard API Key header (X-API-Key).
    Protects the raw ML inference microservice from unauthorized access.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing 'X-API-Key' header. Access to ML Inference Microservice requires an API Key.",
        )
    if api_key != VALID_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid 'X-API-Key'. You are not authorized to invoke this ML model.",
        )
    return api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI startup lifespan: pre-load model into RAM."""
    global model
    model = get_model()
    yield


app = FastAPI(
    title="ML Model Inference Microservice",
    description="Internal microservice serving Scikit-Learn House Price model. Authenticated via X-API-Key.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", summary="ML Service Info")
def root_info():
    return {
        "service": "ML Model Inference Microservice",
        "port": 8001,
        "auth_required": True,
        "auth_header": "X-API-Key",
        "docs_url": "/docs",
        "health_check": "/health",
        "predict_endpoint": "/predict (requires X-API-Key)",
    }


@app.get("/health", response_model=HealthResponse, summary="Service Health Check")
def health_check():
    """Public health verification endpoint."""
    current_model = get_model()
    is_loaded = current_model is not None
    return HealthResponse(
        service="ML Model Inference Service",
        status="healthy" if is_loaded else "degraded",
        model_loaded=is_loaded,
        model_path=str(MODEL_PATH),
        port=8001,
    )


@app.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute ML Prediction (Protected)",
)
def predict_house_price(
    request: PredictionRequest,
    _auth_key: str = Depends(verify_api_key),
):
    """
    Authenticated ML inference endpoint.
    Requires header: `X-API-Key: ml_live_key_9f82d1c87e4a3b10`
    """
    current_model = get_model()
    if current_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model artifact '{MODEL_PATH.name}' is not loaded. Train the model first.",
        )

    try:
        # Prepare 2D input matching trained feature names
        input_features = pd.DataFrame([[request.area]], columns=["area"])

        # Run inference
        predicted_raw = float(current_model.predict(input_features)[0])
        predicted_price = max(0.0, round(predicted_raw, 2))

        slope = float(current_model.coef_[0])
        intercept = float(current_model.intercept_)

        return PredictionResponse(
            area=request.area,
            predicted_price=predicted_price,
            formatted_price=f"${predicted_price:,.2f}",
            currency="USD",
            model_version="1.0.0",
            intercept=round(intercept, 2),
            slope_per_sqft=round(slope, 2),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference computation error: {str(exc)}",
        )
