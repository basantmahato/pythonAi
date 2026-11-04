from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Input payload for ML model inference."""
    area: float = Field(
        ...,
        gt=0,
        le=50000,
        description="Property area in square feet",
        json_schema_extra={"example": 1850.0}
    )


class PredictionResponse(BaseModel):
    """Raw model output from Scikit-Learn Linear Regression."""
    area: float = Field(..., description="Evaluated area in square feet")
    predicted_price: float = Field(..., description="Estimated raw price in USD")
    formatted_price: str = Field(..., description="Formatted price string")
    currency: str = Field(default="USD", description="Currency unit")
    model_version: str = Field(default="1.0.0", description="Trained model version")
    intercept: float = Field(..., description="Learned bias / baseline price")
    slope_per_sqft: float = Field(..., description="Learned weight / dollar rate per sqft")


class HealthResponse(BaseModel):
    """Service status and model readiness."""
    service: str = Field(default="ML Model Inference Service")
    status: str = Field(..., description="Operational status")
    model_loaded: bool = Field(..., description="Whether model .pkl is ready in memory")
    model_path: str = Field(..., description="Disk location of loaded model")
    port: int = Field(default=8001)

