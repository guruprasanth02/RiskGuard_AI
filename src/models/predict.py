"""
src/models/predict.py
Loads the trained model and returns structured predictions with risk scores.
"""
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"

_model = None
_meta = None


def _load_artifacts():
    global _model, _meta
    if _model is None:
        model_path = MODELS_DIR / "best_model.joblib"
        meta_path = MODELS_DIR / "model_meta.json"
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model not found at {model_path}. "
                "Run `python src/models/train.py` first."
            )
        _model = joblib.load(model_path)
        with open(meta_path) as f:
            _meta = json.load(f)
    return _model, _meta


def predict_single(transaction: dict[str, Any]) -> dict[str, Any]:
    """
    Run fraud prediction on a single transaction dict.

    Expected keys (matching PaySim schema):
        step, type, amount, oldbalanceOrg, newbalanceOrig,
        oldbalanceDest, newbalanceDest

    Returns
    -------
    dict with: fraud_probability, risk_score (0-100), risk_level, threshold_used
    """
    model, meta = _load_artifacts()
    feature_cols = meta["feature_cols"]
    threshold = meta["threshold"]

    # Build a one-row raw dataframe
    row = pd.DataFrame([transaction])
    # Engine features expect the raw PaySim columns
    # We re-import here to avoid circular imports at module level
    import sys
    sys.path.insert(0, str(ROOT))
    from src.features.engineering import engineer_features

    feat = engineer_features(row)

    # Handle missing feature cols
    for c in feature_cols:
        if c not in feat.columns:
            feat[c] = 0.0

    X = feat[feature_cols]
    proba = float(model.predict_proba(X)[0, 1])
    risk_score = int(round(proba * 100))
    is_fraud = proba >= threshold

    if proba < 0.3:
        risk_level = "LOW"
    elif proba < 0.6:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    return {
        "fraud_probability": round(proba, 4),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "is_fraud_predicted": bool(is_fraud),
        "threshold_used": round(threshold, 4),
        "model_name": meta["model_name"],
    }


def predict_batch(transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run prediction on a list of transaction dicts."""
    return [predict_single(t) for t in transactions]
