import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir / "ml-service"))
sys.path.insert(0, str(root_dir / "core-backend"))

from fastapi.testclient import TestClient

# Import ML service
import importlib.util
spec_ml = importlib.util.spec_from_file_location("ml_main", str(root_dir / "ml-service" / "main.py"))
ml_module = importlib.util.module_from_spec(spec_ml)
spec_ml.loader.exec_module(ml_module)
ml_app = ml_module.app

VALID_KEY = "ml_live_key_9f82d1c87e4a3b10"


def run_tests():
    print("=" * 65)
    print("MICROSERVICES & API-KEY COMMUNICATION TEST SUITE")
    print("=" * 65)

    ml_client = TestClient(ml_app)

    # 1. Test ML Service without API Key -> Expect 401
    print("\n[TEST 1] Calling ML Service /predict with NO API Key...")
    res_no_key = ml_client.post("/predict", json={"area": 1850.0})
    print(f"Status: {res_no_key.status_code} (Expected 401)")
    print(f"Detail: {res_no_key.json()['detail']}")
    assert res_no_key.status_code == 401

    # 2. Test ML Service with Invalid API Key -> Expect 403
    print("\n[TEST 2] Calling ML Service /predict with WRONG API Key...")
    res_wrong_key = ml_client.post(
        "/predict",
        json={"area": 1850.0},
        headers={"X-API-Key": "fake_unauthorized_key"}
    )
    print(f"Status: {res_wrong_key.status_code} (Expected 403)")
    print(f"Detail: {res_wrong_key.json()['detail']}")
    assert res_wrong_key.status_code == 403

    # 3. Test ML Service with Valid API Key -> Expect 200
    print("\n[TEST 3] Calling ML Service /predict with VALID API Key...")
    res_valid = ml_client.post(
        "/predict",
        json={"area": 1850.0},
        headers={"X-API-Key": VALID_KEY}
    )
    print(f"Status: {res_valid.status_code} (Expected 200)")
    data = res_valid.json()
    print(f"Predicted Price: {data['formatted_price']}")
    print(f"Model Parameters: Slope = ${data['slope_per_sqft']}/sqft, Intercept = ${data['intercept']}")
    assert res_valid.status_code == 200
    assert "predicted_price" in data
    assert data["area"] == 1850.0

    # 4. Test Core Business Logic Calculations
    print("\n[TEST 4] Testing Core Business Logic calculations...")
    spec_core = importlib.util.spec_from_file_location("core_main", str(root_dir / "core-backend" / "main.py"))
    core_module = importlib.util.module_from_spec(spec_core)
    spec_core.loader.exec_module(core_module)

    mortgage = core_module.calculate_mortgage(principal=300000.0, annual_rate_percent=6.5, years=30)
    tier = core_module.determine_market_tier(379000.0)
    print(f"Calculated 30-Yr Mortgage ($300k principal @ 6.5%): ${mortgage:,.2f}/month")
    print(f"Assigned Market Tier: {tier}")
    assert mortgage == 1896.20
    assert tier == "Mid-Tier Suburban"

    print("\n" + "=" * 65)
    print("ALL MICROSERVICES & API-KEY TESTS PASSED SUCCESSFULLY! [OK]")
    print("=" * 65)


if __name__ == "__main__":
    run_tests()
