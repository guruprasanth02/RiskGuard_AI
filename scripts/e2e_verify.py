"""
scripts/e2e_verify.py
Runs an end-to-end verification of all FastAPI endpoints, ML prediction,
SHAP explanation, AI investigation, and session logging.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def run_e2e():
    print("--- 1. Health Check ---")
    h = client.get("/health")
    assert h.status_code == 200
    print("Health:", h.json())

    print("\n--- 2. Demo Transactions ---")
    d = client.get("/demo/transactions")
    assert d.status_code == 200
    demos = d.json()["transactions"]
    print(f"Found {len(demos)} demo transactions")

    print("\n--- 3. Predict on Demo Transactions ---")
    for demo in demos:
        print(f"\nEvaluating: {demo['label']}")
        payload = demo["transaction"]
        resp = client.post("/predict", json=payload)
        assert resp.status_code == 200, resp.text
        res = resp.json()
        print(f"  Score: {res['risk_score']}/100 | Level: {res['risk_level']} | Action: {res['recommended_action']}")
        print(f"  Top factor: {res['explanation']['top_factors'][0]['feature']} ({res['explanation']['top_factors'][0]['direction']})")

        print("  Running AI Investigation...")
        inv_payload = {
            "transaction_id": res["transaction_id"],
            "transaction": payload,
            "risk_score": res["risk_score"],
            "risk_level": res["risk_level"],
            "recommended_action": res["recommended_action"],
            "top_factors": res["explanation"]["top_factors"],
        }
        inv_resp = client.post("/investigate", json=inv_payload)
        assert inv_resp.status_code == 200
        inv_data = inv_resp.json()
        print(f"  AI Summary: {inv_data['executive_summary'][:80]}...")
        print(f"  Next Steps count: {len(inv_data['recommended_next_steps'])}")

    print("\n--- 4. Dashboard Stats ---")
    s = client.get("/stats")
    assert s.status_code == 200
    print("Stats:", s.json())

    print("\n--- 5. Transaction Log ---")
    txns = client.get("/transactions?limit=10")
    assert txns.status_code == 200
    print(f"Total logged transactions: {txns.json()['total']}")

    print("\n--- 6. Model Metadata ---")
    m = client.get("/model/info")
    assert m.status_code == 200
    meta = m.json()
    print(f"Model: {meta['model_name']} | Val PR-AUC: {meta['val_metrics']['pr_auc']:.4f} | Test F1: {meta['test_metrics']['f1_fraud']:.4f}")

    print("\n==========================================")
    print("ALL END-TO-END CHECKS PASSED PERFECTLY!")
    print("==========================================")

if __name__ == "__main__":
    run_e2e()
