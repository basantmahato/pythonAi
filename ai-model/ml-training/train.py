"""
House Price Prediction - Model Training Pipeline
=================================================
Covers Phase 2 through Phase 5:
- Data ingestion & inspection
- Preprocessing (missing values)
- Train/test split
- Linear Regression model training
- Evaluation (MAE, MSE, RMSE, R²)
- Model serialization with Joblib
"""

import os
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


def main():
    print("=" * 60)
    print("HOUSE PRICE PREDICTION - TRAINING WORKFLOW")
    print("=" * 60)

    # 1. Resolve paths
    base_dir = Path(__file__).resolve().parent
    data_path = base_dir / "data" / "house_prices.csv"
    model_dir = base_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "house_price_model.pkl"

    print(f"\n[Phase 1] Loading data from: {data_path}")
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found at {data_path}")

    # 2. Phase 2: Load and Prepare Data
    df = pd.read_csv(data_path)
    print(f"Dataset shape: {df.shape[0]} rows, {df.shape[1]} columns")
    print("\nDataset Preview:")
    print(df.head(5))

    # Check missing values
    missing = df.isnull().sum()
    print("\nMissing values per column:")
    print(missing)

    # Handle missing values: Fill numeric NaNs with median values
    for col in df.columns:
        if df[col].isnull().sum() > 0:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            print(f"Filled {col} missing values with median: {median_val}")

    # Feature and Target Selection
    # Primary feature: house area (sqft)
    # Target: house price (USD)
    X = df[["area"]]
    y = df["price"]

    # Split dataset: 80% Train, 20% Test (random_state for reproducibility)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"\nTraining set size: {len(X_train)} samples")
    print(f"Testing set size:  {len(X_test)} samples")

    # 3. Phase 3: Build & Train Model
    print("\n[Phase 3] Initializing Linear Regression...")
    model = LinearRegression()
    model.fit(X_train, y_train)

    slope = float(model.coef_[0])
    intercept = float(model.intercept_)
    print("\n--- Model Parameters ---")
    print(f"Coefficient (Slope / Price per sqft) : ${slope:,.2f}")
    print(f"Intercept (Baseline Base Price)      : ${intercept:,.2f}")
    print(f"Linear Equation: Price = ({slope:.2f} * Area) + {intercept:.2f}")

    # 4. Phase 4: Model Evaluation
    print("\n[Phase 4] Evaluating model performance on Test set...")
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    print(f"Mean Absolute Error (MAE) : ${mae:,.2f}")
    print(f"Mean Squared Error (MSE)  : {mse:,.2f}")
    print(f"Root Mean Squared (RMSE)  : ${rmse:,.2f}")
    print(f"R-squared Score (R²)      : {r2:.4f} ({r2 * 100:.2f}% variance explained)")

    # Sample Predictions Comparison
    comparison = pd.DataFrame(
        {
            "Area (sqft)": X_test["area"].values[:5],
            "Actual Price ($)": y_test.values[:5],
            "Predicted Price ($)": np.round(y_pred[:5], 2),
            "Difference ($)": np.round(np.abs(y_test.values[:5] - y_pred[:5]), 2),
        }
    )
    print("\nSample Test Predictions:")
    print(comparison.to_string(index=False))

    # 5. Phase 5: Model Persistence
    print(f"\n[Phase 5] Saving model with Joblib to: {model_path}")
    joblib.dump(model, model_path)
    print("Model saved successfully!")

    # Verify reloading
    loaded_model = joblib.load(model_path)
    sample_df = pd.DataFrame([[1800.0]], columns=["area"])
    sample_pred = loaded_model.predict(sample_df)[0]
    print(f"\nIndependent Verification Test:")
    print(f"Predicted price for 1,800 sqft house: ${sample_pred:,.2f}")
    print("\nPipeline completed successfully!")


if __name__ == "__main__":
    main()
