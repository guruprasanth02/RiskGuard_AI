"""
src/explainability/shap_explainer.py
Computes SHAP explanations for individual predictions.
"""
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"

_explainer = None
_model = None
_meta = None


def _load():
    global _explainer, _model, _meta
    if _explainer is not None:
        return _explainer, _model, _meta

    model_path = MODELS_DIR / "best_model.joblib"
    meta_path = MODELS_DIR / "model_meta.json"

    if not model_path.exists():
        raise FileNotFoundError("Model not trained yet. Run src/models/train.py first.")

    _model = joblib.load(model_path)
    with open(meta_path) as f:
        _meta = json.load(f)

    model_name = _meta.get("model_name", "")
    if "XGBoost" in model_name or "RandomForest" in model_name:
        _explainer = shap.TreeExplainer(_model)
    else:
        try:
            clf = _model.named_steps["clf"]
            scaler = _model.named_steps["scaler"]
            _explainer = ("linear", clf, scaler)
        except Exception:
            _explainer = shap.Explainer(_model)

    return _explainer, _model, _meta


def explain_transaction(transaction: dict[str, Any]) -> dict[str, Any]:
    """
    Return SHAP-based explanation for a single transaction.

    Returns
    -------
    dict with keys:
        base_value       — model's expected value (fraud class)
        shap_values      — dictionary of feature -> SHAP contribution
        top_factors      — list of dicts {feature, shap_value, impact, direction}
    """
    import sys
    sys.path.insert(0, str(ROOT))
    from src.features.engineering import engineer_features

    explainer, model, meta = _load()
    feature_cols = meta["feature_cols"]

    row = pd.DataFrame([transaction])
    feat = engineer_features(row)
    for c in feature_cols:
        if c not in feat.columns:
            feat[c] = 0.0
    X = feat[feature_cols]

    # ── Compute SHAP values ───────────────────────────────────────────────────
    if isinstance(explainer, tuple) and explainer[0] == "linear":
        _, clf, scaler = explainer
        X_scaled = scaler.transform(X)
        shap_vals = (clf.coef_[0] * X_scaled[0]).tolist()
        base_val = float(clf.intercept_[0])
    else:
        sv = explainer.shap_values(X)
        # sv can be:
        # 1. 3D ndarray: shape (n_samples, n_features, n_classes) -> sv[0, :, 1]
        # 2. list of 2D arrays: [class0_arr, class1_arr] -> sv[1][0]
        # 3. 2D ndarray: shape (n_samples, n_features) -> sv[0]
        if isinstance(sv, np.ndarray) and sv.ndim == 3:
            shap_vals = sv[0, :, 1].tolist()
        elif isinstance(sv, list) and len(sv) >= 2:
            shap_vals = sv[1][0].tolist()
        elif isinstance(sv, np.ndarray) and sv.ndim == 2:
            shap_vals = sv[0].tolist()
        else:
            shap_vals = np.array(sv).flatten().tolist()

        ev = explainer.expected_value
        if isinstance(ev, (list, np.ndarray)):
            base_val = float(ev[1] if len(ev) > 1 else ev[0])
        else:
            base_val = float(ev)

    # ── Sort factors by absolute impact ───────────────────────────────────────
    feature_importance = sorted(
        zip(feature_cols, shap_vals),
        key=lambda x: abs(float(x[1])),
        reverse=True,
    )

    top_factors = []
    for feat_name, sv_item in feature_importance[:8]:
        val = float(sv_item)
        top_factors.append({
            "feature": feat_name,
            "shap_value": round(val, 5),
            "impact": round(abs(val), 5),
            "direction": "increases_risk" if val > 0 else "decreases_risk",
        })

    return {
        "base_value": round(base_val, 5),
        "shap_values": {f: round(float(v), 5) for f, v in zip(feature_cols, shap_vals)},
        "top_factors": top_factors,
    }
