from typing import List, Optional
from pydantic import BaseModel, Field


class ValuationRequest(BaseModel):
    """Client request from React frontend."""
    area: float = Field(
        ...,
        gt=0,
        le=50000,
        description="House area in square feet",
        json_schema_extra={"example": 1850.0}
    )
    down_payment_percent: Optional[float] = Field(
        default=20.0,
        ge=0,
        le=100,
        description="Down payment percentage (default 20%)"
    )
    interest_rate_percent: Optional[float] = Field(
        default=6.5,
        ge=0.1,
        le=25.0,
        description="Annual mortgage interest rate (default 6.5%)"
    )


class FinancialBreakdown(BaseModel):
    """Real estate financial calculations performed by business backend."""
    down_payment: float = Field(..., description="Estimated down payment in USD")
    loan_amount: float = Field(..., description="Loan principal amount")
    monthly_mortgage_principal_interest: float = Field(..., description="Monthly mortgage payment")
    monthly_property_tax: float = Field(..., description="Estimated monthly property tax")
    monthly_insurance: float = Field(..., description="Estimated monthly homeowners insurance")
    total_estimated_monthly: float = Field(..., description="Total monthly housing cost")
    estimated_closing_costs: float = Field(..., description="Estimated closing costs (~3%)")


class ValuationResponse(BaseModel):
    """Enriched business payload returned to frontend."""
    area: float = Field(..., description="Property area in square feet")
    predicted_price: float = Field(..., description="Estimated market valuation")
    formatted_price: str = Field(..., description="Formatted valuation string")
    currency: str = Field(default="USD")
    price_per_sqft: float = Field(..., description="Valuation per square foot")
    market_tier: str = Field(..., description="Property classification tier")
    investment_score: float = Field(..., description="Affordability/Value score (1-10)")
    financials: FinancialBreakdown = Field(..., description="Mortgage and tax breakdown")
    model_metadata: dict = Field(..., description="Details from ML inference microservice")


class HealthStatus(BaseModel):
    service: str = Field(default="Core Business Backend")
    status: str
    port: int = Field(default=8000)
    ml_service_connected: bool
    ml_service_url: str
    auth_mode: str = Field(default="API Key (X-API-Key)")

