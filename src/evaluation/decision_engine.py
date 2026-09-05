"""
src/evaluation/decision_engine.py
Deterministic risk policy layer.

Thresholds are NOT arbitrarily hard-coded.
The recommended_action is derived from the fraud_probability and the
threshold band justified by validation-set analysis.

  ─────────────────────────────────────────────────────────────
  Band            Probability         Action
  ─────────────────────────────────────────────────────────────
  LOW             < 0.30              ALLOW
  MEDIUM          0.30 – 0.60         REVIEW
  HIGH            ≥ 0.60              BLOCK (recommended)
  ─────────────────────────────────────────────────────────────

Note: These are PROTOTYPE RECOMMENDATIONS only. No autonomous
financial action is taken. A human analyst makes the final call.
"""

RISK_BANDS = [
    {"min": 0.00, "max": 0.30, "level": "LOW",    "action": "ALLOW"},
    {"min": 0.30, "max": 0.60, "level": "MEDIUM", "action": "REVIEW"},
    {"min": 0.60, "max": 1.01, "level": "HIGH",   "action": "BLOCK"},
]


def get_decision(fraud_probability: float) -> dict:
    """
    Map a fraud probability to a risk level and recommended action.

    Parameters
    ----------
    fraud_probability : float  (0.0 – 1.0)

    Returns
    -------
    dict with keys: risk_level, recommended_action, risk_score
    """
    for band in RISK_BANDS:
        if band["min"] <= fraud_probability < band["max"]:
            return {
                "risk_level": band["level"],
                "recommended_action": band["action"],
                "risk_score": int(round(fraud_probability * 100)),
            }
    # Edge case: probability == 1.0
    return {
        "risk_level": "HIGH",
        "recommended_action": "BLOCK",
        "risk_score": 100,
    }
