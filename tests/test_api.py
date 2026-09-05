"""
tests/test_api.py
Integration tests for the FastAPI prediction endpoint.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Try to import test client — skip all API tests if FastAPI not installed
try:
    from fastapi.testclient import TestClient
    from api.main import app

    client = TestClient(app)
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

MODEL_TRAINED = (ROOT / "models" / "best_model.joblib").exists()


VALID_TXN = {
    "step": 1,
    "type": "TRANSFER",
    "amount": 181.0,
    "oldbalanceOrg": 181.0,
    "newbalanceOrig": 0.0,
    "oldbalanceDest": 0.0,
    "newbalanceDest": 0.0,
}


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
class TestHealthEndpoint:
    def test_health_returns_200(self):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_has_status(self):
        resp = client.get("/health")
        data = resp.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_has_model_ready_field(self):
        resp = client.get("/health")
        data = resp.json()
        assert "model_ready" in data


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
@pytest.mark.skipif(not MODEL_TRAINED, reason="Model not trained yet")
class TestPredictEndpoint:
    def test_valid_transaction_returns_200(self):
        resp = client.post("/predict", json=VALID_TXN)
        assert resp.status_code == 200

    def test_response_has_required_fields(self):
        resp = client.post("/predict", json=VALID_TXN)
        data = resp.json()
        required = [
            "transaction_id", "timestamp", "fraud_probability",
            "risk_score", "risk_level", "recommended_action",
            "explanation", "model_name", "threshold_used",
        ]
        for field in required:
            assert field in data, f"Missing field: {field}"

    def test_risk_score_in_range(self):
        resp = client.post("/predict", json=VALID_TXN)
        data = resp.json()
        assert 0 <= data["risk_score"] <= 100

    def test_risk_level_valid(self):
        resp = client.post("/predict", json=VALID_TXN)
        data = resp.json()
        assert data["risk_level"] in {"LOW", "MEDIUM", "HIGH"}

    def test_recommended_action_valid(self):
        resp = client.post("/predict", json=VALID_TXN)
        data = resp.json()
        assert data["recommended_action"] in {"ALLOW", "REVIEW", "BLOCK"}

    def test_fraud_probability_in_range(self):
        resp = client.post("/predict", json=VALID_TXN)
        data = resp.json()
        assert 0.0 <= data["fraud_probability"] <= 1.0

    def test_explanation_has_top_factors(self):
        resp = client.post("/predict", json=VALID_TXN)
        data = resp.json()
        expl = data["explanation"]
        assert "top_factors" in expl

    def test_custom_transaction_id(self):
        txn = {**VALID_TXN, "transaction_id": "my_custom_id"}
        resp = client.post("/predict", json=txn)
        data = resp.json()
        assert data["transaction_id"] == "my_custom_id"


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
class TestInvalidInput:
    def test_negative_amount_rejected(self):
        bad = {**VALID_TXN, "amount": -100.0}
        resp = client.post("/predict", json=bad)
        assert resp.status_code == 422

    def test_zero_amount_rejected(self):
        bad = {**VALID_TXN, "amount": 0.0}
        resp = client.post("/predict", json=bad)
        assert resp.status_code == 422

    def test_invalid_type_rejected(self):
        bad = {**VALID_TXN, "type": "INVALID_TYPE"}
        resp = client.post("/predict", json=bad)
        assert resp.status_code == 422

    def test_missing_amount_rejected(self):
        bad = {k: v for k, v in VALID_TXN.items() if k != "amount"}
        resp = client.post("/predict", json=bad)
        assert resp.status_code == 422

    def test_step_out_of_range_rejected(self):
        bad = {**VALID_TXN, "step": 0}
        resp = client.post("/predict", json=bad)
        assert resp.status_code == 422


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
class TestDashboardEndpoints:
    def test_stats_returns_200(self):
        resp = client.get("/stats")
        assert resp.status_code == 200

    def test_transactions_returns_200(self):
        resp = client.get("/transactions")
        assert resp.status_code == 200

    def test_demo_transactions_returns_200(self):
        resp = client.get("/demo/transactions")
        assert resp.status_code == 200

    def test_demo_has_disclaimer(self):
        resp = client.get("/demo/transactions")
        data = resp.json()
        assert "disclaimer" in data
