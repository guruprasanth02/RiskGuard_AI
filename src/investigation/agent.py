"""
src/investigation/agent.py
Agentic Investigation & Evidence Gathering Layer.

GOAL:
Provide autonomous investigation workflows using structured tools to assist human risk analysts.
Tools are strictly read-only for evidence gathering.
The agent CANNOT autonomously execute real financial actions (e.g. fund transfers, account bans).
"""

import json
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[2]


class RiskInvestigationToolkit:
    """Read-only investigative tools for risk analysts and AI agents."""

    @staticmethod
    def transaction_lookup(transaction_id: str, transaction_log: list[dict]) -> dict[str, Any]:
        """Lookup transaction parameters and risk evaluation history by ID."""
        for txn in transaction_log:
            if txn.get("transaction_id") == transaction_id:
                return {"status": "found", "transaction": txn}
        return {"status": "not_found", "message": f"Transaction {transaction_id} not found in active session log"}

    @staticmethod
    def customer_history_lookup(customer_id: str, transaction_log: list[dict]) -> dict[str, Any]:
        """Lookup previous activity for a given customer or account identifier."""
        matched = [
            t for t in transaction_log
            if t.get("nameOrig") == customer_id or t.get("nameDest") == customer_id
        ]
        return {
            "customer_id": customer_id,
            "total_transactions_observed": len(matched),
            "high_risk_count": sum(1 for t in matched if t.get("risk_level") == "HIGH"),
            "recent_records": matched[:5],
        }

    @staticmethod
    def risk_model_lookup() -> dict[str, Any]:
        """Retrieve model metadata, current threshold, and test set performance."""
        meta_file = ROOT / "models" / "model_meta.json"
        if not meta_file.exists():
            return {"status": "error", "message": "Model metadata not found"}
        with open(meta_file) as f:
            meta = json.load(f)
        return {
            "model_name": meta.get("model_name"),
            "threshold": meta.get("threshold"),
            "test_pr_auc": meta.get("test_metrics", {}).get("pr_auc"),
            "test_f1": meta.get("test_metrics", {}).get("f1_fraud"),
            "feature_count": len(meta.get("feature_cols", [])),
        }

    @staticmethod
    def rule_lookup(risk_score: int) -> dict[str, Any]:
        """Evaluate deterministic risk policy bands against a given score."""
        prob = risk_score / 100.0
        if prob < 0.30:
            return {"policy_band": "LOW", "recommended_action": "ALLOW", "policy_code": "POL-001"}
        elif prob < 0.60:
            return {"policy_band": "MEDIUM", "recommended_action": "REVIEW", "policy_code": "POL-002"}
        else:
            return {"policy_band": "HIGH", "recommended_action": "BLOCK", "policy_code": "POL-003"}


class RiskAgent:
    """
    Evidence Gathering Agent for Risk Analysts.
    Executes a structured workflow to compile an Investigation Docket.
    """

    def __init__(self, transaction_log: Optional[list[dict]] = None):
        self.toolkit = RiskInvestigationToolkit()
        self.transaction_log = transaction_log or []

    def gather_docket(self, transaction: dict[str, Any], risk_score: int, top_factors: list[dict[str, Any]]) -> dict[str, Any]:
        """Assemble an evidence docket by coordinating investigative tools."""
        txn_id = transaction.get("transaction_id", "adhoc_eval")

        # 1. Model policy lookup
        model_info = self.toolkit.risk_model_lookup()
        policy = self.toolkit.rule_lookup(risk_score)

        # 2. Originator customer lookup
        orig_id = transaction.get("nameOrig")
        cust_profile = self.toolkit.customer_history_lookup(orig_id, self.transaction_log) if orig_id else {"status": "unspecified"}

        # 3. Compile evidence docket
        docket = {
            "docket_id": f"DOC-{txn_id[:8].upper()}",
            "transaction_snapshot": transaction,
            "governance_policy": policy,
            "ml_model_context": model_info,
            "customer_profile": cust_profile,
            "top_shap_factors": top_factors[:5],
            "agent_verdict": {
                "risk_score": risk_score,
                "recommended_action": policy["recommended_action"],
                "requires_analyst_signoff": policy["recommended_action"] != "ALLOW",
            }
        }
        return docket
