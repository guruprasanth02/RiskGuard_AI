"""
scripts/verify_shap_cases.py
Verifies SHAP explanations and decisions across 3 distinct test scenarios.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.predict import predict_single
from src.explainability.shap_explainer import explain_transaction
from src.evaluation.decision_engine import get_decision

test_cases = [
    {
        "name": "Normal Small Payment",
        "txn": {
            "step": 10, "type": "PAYMENT", "amount": 25.50,
            "oldbalanceOrg": 1500.0, "newbalanceOrig": 1474.50,
            "oldbalanceDest": 0.0, "newbalanceDest": 25.50,
            "nameDest": "M123456"
        }
    },
    {
        "name": "Suspicious Medium Transfer",
        "txn": {
            "step": 200, "type": "TRANSFER", "amount": 40000.0,
            "oldbalanceOrg": 90000.0, "newbalanceOrig": 50000.0,
            "oldbalanceDest": 0.0, "newbalanceDest": 40000.0,
            "nameDest": "C999999"
        }
    },
    {
        "name": "High-Risk Account Drain",
        "txn": {
            "step": 400, "type": "CASH-OUT", "amount": 150000.0,
            "oldbalanceOrg": 150000.0, "newbalanceOrig": 0.0,
            "oldbalanceDest": 0.0, "newbalanceDest": 150000.0,
            "nameDest": "C111111"
        }
    }
]

for tc in test_cases:
    print("========================================")
    print("Case:", tc["name"])
    p = predict_single(tc["txn"])
    d = get_decision(p["fraud_probability"])
    e = explain_transaction(tc["txn"])
    print(f"Probability: {p['fraud_probability']*100:.2f}% | Score: {d['risk_score']} | Action: {d['recommended_action']}")
    print("Top 3 factors:")
    for f in e["top_factors"][:3]:
        print(f"  {f['feature']}: {f['shap_value']:+.5f} ({f['direction']})")
