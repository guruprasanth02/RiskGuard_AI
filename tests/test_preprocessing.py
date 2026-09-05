"""
tests/test_preprocessing.py
Tests for feature engineering and data preprocessing pipeline.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.features.engineering import engineer_features, FEATURE_COLS, TARGET_COL
from src.evaluation.decision_engine import get_decision


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_row(**kwargs) -> pd.DataFrame:
    """Create a minimal raw PaySim row for testing."""
    defaults = {
        "step": 1,
        "type": "TRANSFER",
        "amount": 500.0,
        "nameOrig": "C123",
        "oldbalanceOrg": 500.0,
        "newbalanceOrig": 0.0,
        "nameDest": "C456",
        "oldbalanceDest": 0.0,
        "newbalanceDest": 500.0,
        "isFraud": 1,
        "isFlaggedFraud": 0,
    }
    defaults.update(kwargs)
    return pd.DataFrame([defaults])


# ─────────────────────────────────────────────────────────────────────────────
# Feature Engineering Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestFeatureEngineering:
    def test_output_columns_present(self):
        df = make_row()
        result = engineer_features(df)
        for col in FEATURE_COLS:
            assert col in result.columns, f"Missing feature column: {col}"

    def test_target_present(self):
        df = make_row(isFraud=1)
        result = engineer_features(df)
        assert TARGET_COL in result.columns

    def test_log1p_amount_positive(self):
        df = make_row(amount=1000.0)
        result = engineer_features(df)
        assert result["log1p_amount"].iloc[0] > 0

    def test_hour_of_day_range(self):
        for step in [1, 23, 24, 25, 100, 744]:
            df = make_row(step=step)
            result = engineer_features(df)
            hour = result["hour_of_day"].iloc[0]
            assert 0 <= hour <= 23, f"hour_of_day={hour} out of range for step={step}"

    def test_is_transfer_flag(self):
        df_tf = make_row(type="TRANSFER")
        df_co = make_row(type="CASH-OUT")
        df_pay = make_row(type="PAYMENT")

        assert engineer_features(df_tf)["is_transfer"].iloc[0] == 1
        assert engineer_features(df_co)["is_transfer"].iloc[0] == 0
        assert engineer_features(df_pay)["is_transfer"].iloc[0] == 0

    def test_is_cash_out_flag(self):
        df_co = make_row(type="CASH-OUT")
        df_tf = make_row(type="TRANSFER")
        assert engineer_features(df_co)["is_cash_out"].iloc[0] == 1
        assert engineer_features(df_tf)["is_cash_out"].iloc[0] == 0

    def test_amount_to_orig_balance_zero_balance(self):
        """Test ratio when originator balance is 0 (should not divide by zero)."""
        df = make_row(amount=100.0, oldbalanceOrg=0.0)
        result = engineer_features(df)
        ratio = result["amount_to_orig_balance"].iloc[0]
        assert np.isfinite(ratio)

    def test_no_raw_identifiers_in_output(self):
        """nameOrig and nameDest must NOT appear in engineered features."""
        df = make_row()
        result = engineer_features(df)
        assert "nameOrig" not in result.columns
        assert "nameDest" not in result.columns

    def test_no_leaky_columns_in_output(self):
        """isFlaggedFraud must NOT appear as an input feature."""
        df = make_row()
        result = engineer_features(df)
        assert "isFlaggedFraud" not in [c for c in result.columns if c != TARGET_COL]

    def test_multiple_rows(self):
        """Engineer features handles DataFrames with multiple rows."""
        rows = pd.concat([make_row(step=i, amount=float(i * 100)) for i in range(1, 6)])
        result = engineer_features(rows)
        assert len(result) == 5
        for col in FEATURE_COLS:
            assert col in result.columns


# ─────────────────────────────────────────────────────────────────────────────
# Decision Engine Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDecisionEngine:
    def test_low_probability(self):
        d = get_decision(0.05)
        assert d["risk_level"] == "LOW"
        assert d["recommended_action"] == "ALLOW"

    def test_medium_probability(self):
        d = get_decision(0.45)
        assert d["risk_level"] == "MEDIUM"
        assert d["recommended_action"] == "REVIEW"

    def test_high_probability(self):
        d = get_decision(0.85)
        assert d["risk_level"] == "HIGH"
        assert d["recommended_action"] == "BLOCK"

    def test_boundary_low_medium(self):
        d = get_decision(0.30)
        assert d["risk_level"] == "MEDIUM"

    def test_boundary_medium_high(self):
        d = get_decision(0.60)
        assert d["risk_level"] == "HIGH"

    def test_risk_score_range(self):
        for prob in [0.0, 0.1, 0.5, 0.99, 1.0]:
            d = get_decision(prob)
            assert 0 <= d["risk_score"] <= 100

    def test_probability_one(self):
        d = get_decision(1.0)
        assert d["risk_level"] == "HIGH"
        assert d["recommended_action"] == "BLOCK"
        assert d["risk_score"] == 100
