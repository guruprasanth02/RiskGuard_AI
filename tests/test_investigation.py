"""
tests/test_investigation.py
Tests for AI Investigator and Agentic Evidence Gathering layer.
"""
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.investigation.investigator import run_ai_investigation
from src.investigation.agent import RiskAgent, RiskInvestigationToolkit


SAMPLE_TXN = {
    "step": 1,
    "type": "TRANSFER",
    "amount": 181.0,
    "oldbalanceOrg": 181.0,
    "newbalanceOrig": 0.0,
    "oldbalanceDest": 0.0,
    "newbalanceDest": 0.0,
    "nameOrig": "C123456",
    "nameDest": "C654321",
}

SAMPLE_FACTORS = [
    {"feature": "is_full_drain_attempt", "shap_value": 0.25, "impact": 0.25, "direction": "increases_risk"},
    {"feature": "amount_to_orig_balance", "shap_value": 0.09, "impact": 0.09, "direction": "increases_risk"},
    {"feature": "is_cash_out", "shap_value": -0.02, "impact": 0.02, "direction": "decreases_risk"},
]


class TestAIInvestigator:
    def test_high_risk_investigation_output(self):
        report = run_ai_investigation(
            transaction_id="txn_test_high_001",
            transaction=SAMPLE_TXN,
            risk_score=95,
            risk_level="HIGH",
            recommended_action="BLOCK",
            top_factors=SAMPLE_FACTORS,
        )
        assert "executive_summary" in report
        assert "natural_language_explanation" in report
        assert "recommended_next_steps" in report
        assert len(report["recommended_next_steps"]) > 0
        assert "is_full_drain_attempt" in report["primary_risk_drivers"]

    def test_low_risk_investigation_output(self):
        report = run_ai_investigation(
            transaction_id="txn_test_low_001",
            transaction={**SAMPLE_TXN, "type": "PAYMENT", "amount": 10.0, "oldbalanceOrg": 500.0},
            risk_score=5,
            risk_level="LOW",
            recommended_action="ALLOW",
            top_factors=[],
        )
        assert "TRANSACTION CLEARED" in report["executive_summary"]
        assert report["analyst_disclaimer"] is not None

    def test_does_not_override_risk_score(self):
        report = run_ai_investigation(
            transaction_id="txn_test_medium_001",
            transaction=SAMPLE_TXN,
            risk_score=45,
            risk_level="MEDIUM",
            recommended_action="REVIEW",
            top_factors=SAMPLE_FACTORS,
        )
        # Verify explanation acknowledges the medium review action
        assert "REVIEW" in report["executive_summary"]


class TestAgenticLayer:
    def test_toolkit_rule_lookup(self):
        toolkit = RiskInvestigationToolkit()
        low = toolkit.rule_lookup(15)
        assert low["recommended_action"] == "ALLOW"
        med = toolkit.rule_lookup(45)
        assert med["recommended_action"] == "REVIEW"
        high = toolkit.rule_lookup(85)
        assert high["recommended_action"] == "BLOCK"

    def test_toolkit_risk_model_lookup(self):
        toolkit = RiskInvestigationToolkit()
        info = toolkit.risk_model_lookup()
        assert info.get("model_name") in ["RandomForest", "XGBoost", "LogisticRegression"]
        assert "threshold" in info

    def test_agent_gather_docket(self):
        agent = RiskAgent(transaction_log=[{"transaction_id": "txn_001", "nameOrig": "C123456"}])
        docket = agent.gather_docket(SAMPLE_TXN, risk_score=95, top_factors=SAMPLE_FACTORS)
        assert "docket_id" in docket
        assert "governance_policy" in docket
        assert "top_shap_factors" in docket
        assert docket["agent_verdict"]["requires_analyst_signoff"] is True
