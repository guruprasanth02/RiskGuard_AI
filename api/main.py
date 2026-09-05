"""
api/main.py
FastAPI application for RiskGuard AI.
"""
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator

# ── project path ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.models.predict import predict_single
from src.explainability.shap_explainer import explain_transaction
from src.evaluation.decision_engine import get_decision
from src.investigation.investigator import run_ai_investigation

# In-memory transaction log for live dashboard visualization
_transaction_log: list[dict] = []

app = FastAPI(
    title="RiskGuard AI",
    description="Explainable Transaction Risk Manager — PaySim Prototype for Razorpay AI Builder Internship",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_TYPES = {"CASH-IN", "CASH-OUT", "DEBIT", "PAYMENT", "TRANSFER", "CASH_IN", "CASH_OUT"}


class TransactionRequest(BaseModel):
    """Input transaction for risk prediction."""
    transaction_id: Optional[str] = Field(
        default=None,
        description="Optional client-supplied transaction ID",
    )
    step: int = Field(..., ge=1, le=744, description="PaySim time step (1-744, 1 step = 1 hour)")
    type: str = Field(..., description="Transaction type")
    amount: float = Field(..., gt=0, description="Transaction amount (must be > 0)")
    oldbalanceOrg: float = Field(..., ge=0, description="Originator balance before transaction")
    newbalanceOrig: float = Field(..., ge=0, description="Originator balance after transaction")
    oldbalanceDest: float = Field(..., ge=0, description="Destination balance before transaction")
    newbalanceDest: float = Field(..., ge=0, description="Destination balance after transaction")
    nameOrig: Optional[str] = Field(default=None, description="Optional originator account ID")
    nameDest: Optional[str] = Field(default=None, description="Optional destination account ID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "step": 1,
                "type": "TRANSFER",
                "amount": 181.0,
                "oldbalanceOrg": 181.0,
                "newbalanceOrig": 0.0,
                "oldbalanceDest": 0.0,
                "newbalanceDest": 0.0,
            }
        }
    )

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        norm = v.upper().replace("-", "_")
        valid_norms = {t.replace("-", "_") for t in VALID_TYPES}
        if norm not in valid_norms:
            raise ValueError(f"type must be one of {sorted(VALID_TYPES)}")
        return v.upper()


class PredictionResponse(BaseModel):
    transaction_id: str
    timestamp: str
    fraud_probability: float
    risk_score: int
    risk_level: str
    is_fraud_predicted: bool
    recommended_action: str
    explanation: dict
    model_name: str
    threshold_used: float


class InvestigationRequest(BaseModel):
    transaction_id: str
    transaction: dict
    risk_score: int
    risk_level: str
    recommended_action: str
    top_factors: list[dict]


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health():
    """Basic health check and model availability status."""
    models_dir = ROOT / "models"
    model_ready = (models_dir / "best_model.joblib").exists()
    return {
        "status": "ok",
        "model_ready": model_ready,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
def predict(req: TransactionRequest):
    """
    Predict fraud risk for a single transaction.
    Returns risk score, risk level, recommended action, and SHAP explanation.
    """
    txn_dict = req.model_dump()
    txn_id = txn_dict.pop("transaction_id") or str(uuid.uuid4())

    try:
        pred = predict_single(txn_dict)
        decision = get_decision(pred["fraud_probability"])

        try:
            explanation = explain_transaction(txn_dict)
        except Exception as e:
            explanation = {"error": str(e), "top_factors": [], "base_value": None}

        result = {
            "transaction_id": txn_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fraud_probability": pred["fraud_probability"],
            "risk_score": decision["risk_score"],
            "risk_level": decision["risk_level"],
            "is_fraud_predicted": pred["is_fraud_predicted"],
            "recommended_action": decision["recommended_action"],
            "explanation": explanation,
            "model_name": pred["model_name"],
            "threshold_used": pred["threshold_used"],
        }

        _transaction_log.append({
            "transaction_id": txn_id,
            "timestamp": result["timestamp"],
            "type": req.type,
            "amount": req.amount,
            "risk_score": result["risk_score"],
            "risk_level": result["risk_level"],
            "recommended_action": result["recommended_action"],
            "fraud_probability": result["fraud_probability"],
            "explanation": explanation,
        })
        if len(_transaction_log) > 1000:
            _transaction_log.pop(0)

        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {e}")


@app.post("/investigate", tags=["Investigation"])
def investigate(req: InvestigationRequest):
    """
    AI Risk Investigator assistant.
    Receives ONLY structured evidence from the ML + XAI layer and provides:
    - Executive investigation summary
    - Natural language explanation of risk drivers
    - Concrete recommended next steps for human risk analysts
    """
    report = run_ai_investigation(
        transaction_id=req.transaction_id,
        transaction=req.transaction,
        risk_score=req.risk_score,
        risk_level=req.risk_level,
        recommended_action=req.recommended_action,
        top_factors=req.top_factors,
    )
    return report


@app.get("/transactions", tags=["Dashboard"])
def get_transactions(limit: int = 100):
    """Return recent transactions analyzed during this session."""
    return {
        "total": len(_transaction_log),
        "transactions": list(reversed(_transaction_log))[:limit],
    }


@app.get("/stats", tags=["Dashboard"])
def get_stats():
    """Aggregate statistics for the risk monitoring dashboard."""
    if not _transaction_log:
        return {
            "total_analyzed": 0,
            "high_risk": 0,
            "medium_risk": 0,
            "low_risk": 0,
            "blocked": 0,
            "reviewed": 0,
            "allowed": 0,
        }

    levels = [t["risk_level"] for t in _transaction_log]
    actions = [t["recommended_action"] for t in _transaction_log]

    return {
        "total_analyzed": len(_transaction_log),
        "high_risk": levels.count("HIGH"),
        "medium_risk": levels.count("MEDIUM"),
        "low_risk": levels.count("LOW"),
        "blocked": actions.count("BLOCK"),
        "reviewed": actions.count("REVIEW"),
        "allowed": actions.count("ALLOW"),
    }


@app.get("/model/info", tags=["Model"])
def model_info():
    """Return model metadata, hyperparameters, and held-out test evaluation metrics."""
    meta_path = ROOT / "models" / "model_meta.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Model not trained yet.")
    with open(meta_path) as f:
        return json.load(f)


DEMO_TRANSACTIONS = [
    {
        "label": "Normal Routine Payment — LOW RISK",
        "description": "Routine merchant payment with sufficient balance. Model-verified ALLOW (Risk Score ~1/100).",
        "transaction": {
            "step": 1,
            "type": "PAYMENT",
            "amount": 9.99,
            "oldbalanceOrg": 1000.0,
            "newbalanceOrig": 990.01,
            "oldbalanceDest": 0.0,
            "newbalanceDest": 9.99,
            "nameOrig": "C1231006815",
            "nameDest": "M1979574682",
        },
    },
    {
        "label": "Large Partial Transfer — MEDIUM RISK",
        "description": "50% balance drain to non-merchant over a single step. Model-verified REVIEW band (~44/100).",
        "transaction": {
            "step": 200,
            "type": "TRANSFER",
            "amount": 2500000.0,
            "oldbalanceOrg": 5000000.0,
            "newbalanceOrig": 2500000.0,
            "oldbalanceDest": 0.0,
            "newbalanceDest": 2500000.0,
            "nameOrig": "C5432167890",
            "nameDest": "C9876543210",
        },
    },
    {
        "label": "Full Balance Drain — HIGH RISK",
        "description": "100% account balance drained via TRANSFER to a zero-balance destination. Model-verified BLOCK (~99/100).",
        "transaction": {
            "step": 397,
            "type": "TRANSFER",
            "amount": 181.0,
            "oldbalanceOrg": 181.0,
            "newbalanceOrig": 0.0,
            "oldbalanceDest": 0.0,
            "newbalanceDest": 0.0,
            "nameOrig": "C1231006815",
            "nameDest": "C1979574682",
        },
    },
]


@app.get("/demo/transactions", tags=["Demo"])
def demo_transactions():
    """Returns representative synthetic PaySim test transactions for demonstration."""
    return {
        "disclaimer": "These are synthetic PaySim test transactions for demonstration only. Not real Razorpay transactions.",
        "transactions": DEMO_TRANSACTIONS,
    }
