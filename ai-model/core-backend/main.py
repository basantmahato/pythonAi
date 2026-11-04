import os
from datetime import datetime
from typing import List, Optional

import httpx
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from core_schemas import FinancialBreakdown, HealthStatus, ValuationRequest, ValuationResponse

# Microservice Configuration
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://127.0.0.1:8001").rstrip("/")
ML_SERVICE_API_KEY = os.getenv("ML_SERVICE_API_KEY", "ml_live_key_9f82d1c87e4a3b10")

app = FastAPI(
    title="Core Business Backend API",
    description="Business logic layer orchestrating ML inference via authenticated API Key and computing financial analytics.",
    version="1.0.0",
)

# Enable CORS for React frontend (port 5173, 3000, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory history cache of recent inquiries
inquiry_history: List[dict] = []


def calculate_mortgage(
    principal: float, annual_rate_percent: float, years: int = 30
) -> float:
    """Calculate monthly mortgage payment using standard amortization formula."""
    if principal <= 0:
        return 0.0
    monthly_rate = (annual_rate_percent / 100.0) / 12.0
    num_payments = years * 12
    if monthly_rate == 0:
        return principal / num_payments

    monthly_payment = principal * (
        (monthly_rate * (1 + monthly_rate) ** num_payments)
        / ((1 + monthly_rate) ** num_payments - 1)
    )
    return round(monthly_payment, 2)


def determine_market_tier(price: float) -> str:
    """Classify property into a market segment."""
    if price < 200000:
        return "Affordable Starter"
    elif price < 450000:
        return "Mid-Tier Suburban"
    elif price < 700000:
        return "Prime Executive"
    else:
        return "Luxury Estate"


@app.get("/", summary="Core Backend Overview")
def root():
    return {
        "service": "Core Business Backend",
        "port": 8000,
        "ml_service_target": ML_SERVICE_URL,
        "docs_url": "/docs",
        "health_endpoint": "/health",
        "valuation_endpoint": "/api/v1/properties/valuation",
    }


@app.get("/health", response_model=HealthStatus, summary="System Health & ML Connectivity")
async def health_check():
    """Verify core backend health AND ping the ML microservice with the API Key."""
    ml_connected = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.get(f"{ML_SERVICE_URL}/health")
            if res.status_code == 200:
                data = res.json()
                ml_connected = data.get("model_loaded", False)
    except Exception:
        ml_connected = False

    return HealthStatus(
        service="Core Business Backend",
        status="healthy" if ml_connected else "degraded",
        port=8000,
        ml_service_connected=ml_connected,
        ml_service_url=ML_SERVICE_URL,
        auth_mode="API Key (X-API-Key)",
    )


@app.post(
    "/api/v1/properties/valuation",
    response_model=ValuationResponse,
    status_code=status.HTTP_200_OK,
    summary="Property Valuation & Financial Analysis",
)
async def generate_property_valuation(request: ValuationRequest):
    """
    1. Forwards area to ML Inference Service over HTTP with 'X-API-Key'.
    2. Receives raw machine learning price prediction.
    3. Executes business logic: mortgage calculations, taxes, closing costs, tier classification.
    4. Returns rich payload to the React frontend.
    """
    headers = {
        "X-API-Key": ML_SERVICE_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"area": request.area}

    # Step 1: Query ML Microservice with Secret API Key
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{ML_SERVICE_URL}/predict",
                json=payload,
                headers=headers,
            )

        if response.status_code == 401 or response.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="ML Service authentication failed: API Key was rejected or missing.",
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"ML Service returned error: {response.text}",
            )

        ml_data = response.json()
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Could not reach ML Inference Service at {ML_SERVICE_URL}. "
                "Ensure 'ml-service' is running on port 8001."
            ),
        )

    # Step 2: Extract ML Output
    predicted_price = float(ml_data["predicted_price"])
    price_per_sqft = round(predicted_price / request.area, 2)

    # Step 3: Core Business Financial Calculations
    down_payment_pct = request.down_payment_percent or 20.0
    interest_rate = request.interest_rate_percent or 6.5

    down_payment = round(predicted_price * (down_payment_pct / 100.0), 2)
    loan_amount = round(predicted_price - down_payment, 2)

    monthly_mortgage = calculate_mortgage(loan_amount, interest_rate, years=30)
    monthly_property_tax = round((predicted_price * 0.012) / 12.0, 2)  # ~1.2% tax
    monthly_insurance = round(max(50.0, predicted_price * 0.0035 / 12.0), 2)  # ~0.35%
    total_monthly = round(
        monthly_mortgage + monthly_property_tax + monthly_insurance, 2
    )
    closing_costs = round(predicted_price * 0.03, 2)  # ~3% closing fees

    market_tier = determine_market_tier(predicted_price)
    # Investment score based on price/sqft value (benchmark ~$200/sqft = 9.0)
    investment_score = round(min(10.0, max(1.0, 10.0 - (price_per_sqft - 180) / 30)), 1)

    financials = FinancialBreakdown(
        down_payment=down_payment,
        loan_amount=loan_amount,
        monthly_mortgage_principal_interest=monthly_mortgage,
        monthly_property_tax=monthly_property_tax,
        monthly_insurance=monthly_insurance,
        total_estimated_monthly=total_monthly,
        estimated_closing_costs=closing_costs,
    )

    result = ValuationResponse(
        area=request.area,
        predicted_price=predicted_price,
        formatted_price=f"${predicted_price:,.2f}",
        currency="USD",
        price_per_sqft=price_per_sqft,
        market_tier=market_tier,
        investment_score=investment_score,
        financials=financials,
        model_metadata={
            "intercept": ml_data.get("intercept"),
            "slope_per_sqft": ml_data.get("slope_per_sqft"),
            "model_version": ml_data.get("model_version"),
            "inference_source": "Scikit-Learn Microservice (Port 8001)",
        },
    )

    # Record to inquiry history
    inquiry_history.insert(
        0,
        {
            "timestamp": datetime.utcnow().isoformat(),
            "area": request.area,
            "predicted_price": predicted_price,
            "tier": market_tier,
        },
    )
    if len(inquiry_history) > 20:
        inquiry_history.pop()

    return result


@app.get("/api/v1/properties/history", summary="Recent Valuation Inquiries")
def get_valuation_history():
    """Retrieve recent property inquiries logged by the business backend."""
    return {"inquiries": inquiry_history}
