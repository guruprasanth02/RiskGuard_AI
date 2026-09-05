"""
src/investigation/investigator.py
AI Risk Investigator layer.

CRITICAL ARCHITECTURAL CONSTRAINTS:
1. Core fraud prediction is strictly ML-based (RandomForest / XGBoost).
2. The LLM receives ONLY structured evidence:
   - transaction details
   - model risk score
   - top SHAP factors
   - triggered policy rules
3. The LLM produces:
   - executive investigation summary
   - natural language explanation
   - recommended next investigative steps for human analysts
4. The LLM CANNOT and MUST NOT override the ML risk score or autonomous decision.
5. If no LLM API key is present, a deterministic rule-grounded expert engine
   synthesizes the evidence without failing.
"""

import os
import json
from typing import Any, Optional


def _deterministic_synthesis(
    transaction_id: str,
    transaction: dict[str, Any],
    risk_score: int,
    risk_level: str,
    recommended_action: str,
    top_factors: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Deterministic evidence synthesis when external LLM API key is unavailable.
    Provides natural language explanations grounded directly in SHAP impacts.
    """
    amount = float(transaction.get("amount", 0))
    txn_type = str(transaction.get("type", "UNKNOWN")).upper()
    orig_bal = float(transaction.get("oldbalanceOrg", 0))

    # Extract primary risk and mitigating factors
    risk_drivers = [f for f in top_factors if f.get("direction") == "increases_risk"]
    mitigating_factors = [f for f in top_factors if f.get("direction") == "decreases_risk"]

    driver_names = [f["feature"] for f in risk_drivers[:3]]
    driver_str = ", ".join(driver_names) if driver_names else "baseline model prior"

    # Narrative generation
    if risk_level == "HIGH":
        summary = (
            f"HIGH RISK ALERT: Transaction {transaction_id[:12]} exhibited strong fraudulent signatures "
            f"with a Risk Score of {risk_score}/100. Primary risk drivers include: {driver_str}."
        )
        if "is_full_drain_attempt" in driver_names:
            narrative = (
                f"The transaction attempted to transfer/withdraw ₹{amount:,.2f} of ₹{orig_bal:,.2f} "
                f"available funds (100% account drainage) via {txn_type}. This matches the signature "
                f"account-takeover / rapid cashout pattern observed in synthetic PaySim fraudulent activities."
            )
        else:
            narrative = (
                f"The transaction amount of ₹{amount:,.2f} is significantly elevated relative to normal "
                f"behavior for {txn_type}. SHAP attribution indicates substantial risk elevation driven by {driver_str}."
            )
        next_steps = [
            "Contact account holder via verified out-of-band communication (SMS/voice) to verify transaction authorization.",
            "Temporarily place a security hold on destination account pending origin verification.",
            "Review sender's transaction history over the preceding 48 hours for velocity spikes or credential updates.",
            "If unauthorized, initiate immediate recall procedure and lock originating credentials.",
        ]

    elif risk_level == "MEDIUM":
        summary = (
            f"MANUAL REVIEW RECOMMENDED: Transaction {transaction_id[:12]} assigned Risk Score {risk_score}/100. "
            f"Key contributing factors: {driver_str}."
        )
        narrative = (
            f"While the transaction exhibits elevated characteristics (amount ₹{amount:,.2f} via {txn_type}), "
            f"it does not meet definitive block criteria. Mitigating signals (such as {mitigating_factors[0]['feature'] if mitigating_factors else 'pre-existing balance'}) "
            f"partially offset the risk score."
        )
        next_steps = [
            "Perform secondary authentication check (step-up 2FA/OTP).",
            "Verify whether destination account has a prior successful transaction history with this originator.",
            "Escalate to L2 Risk Analyst if transfer exceeds single-day customer limits.",
        ]

    else:
        summary = (
            f"TRANSACTION CLEARED: Low risk profile identified with Risk Score {risk_score}/100. "
            f"Recommended policy action is {recommended_action}."
        )
        narrative = (
            f"Transaction ₹{amount:,.2f} ({txn_type}) aligns with typical legitimate payment behavior. "
            f"No account-drain anomalies or uncharacteristic velocity signals were detected."
        )
        next_steps = [
            "No manual analyst action required. Permit transaction to settle normally.",
            "Continue standard passive background monitoring.",
        ]

    return {
        "investigation_id": f"inv_{transaction_id[:8]}",
        "llm_provider": "deterministic_expert_synthesizer",
        "executive_summary": summary,
        "natural_language_explanation": narrative,
        "primary_risk_drivers": driver_names,
        "recommended_next_steps": next_steps,
        "analyst_disclaimer": "AI investigation assistant provides advisory summaries grounded in ML/XAI evidence. The final decision remains with the authorized risk officer.",
    }


def run_ai_investigation(
    transaction_id: str,
    transaction: dict[str, Any],
    risk_score: int,
    risk_level: str,
    recommended_action: str,
    top_factors: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Executes AI Risk Investigation.
    Checks for external LLM API keys (e.g. GEMINI_API_KEY, OPENAI_API_KEY);
    if present and accessible, queries the LLM using strictly structured evidence.
    Otherwise gracefully falls back to the deterministic expert synthesis engine.
    """
    # Check for optional API keys
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if openai_key:
        try:
            import httpx
            prompt = f"""You are an AI Financial Risk Investigator assisting a human risk analyst.
You receive ONLY structured evidence from an ML fraud model and SHAP explainability layer.
DO NOT override the risk score or action.

Structured Evidence:
- Transaction ID: {transaction_id}
- Transaction Details: {json.dumps(transaction)}
- ML Risk Score: {risk_score}/100
- Risk Level: {risk_level}
- Recommended Action: {recommended_action}
- Top SHAP Factors: {json.dumps(top_factors)}

Generate a JSON response with:
1. "executive_summary": string
2. "natural_language_explanation": string
3. "primary_risk_drivers": list of strings
4. "recommended_next_steps": list of strings (concrete investigative steps)
"""
            resp = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                },
                timeout=5.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                content = json.loads(data["choices"][0]["message"]["content"])
                content["investigation_id"] = f"inv_{transaction_id[:8]}"
                content["llm_provider"] = "openai-gpt-4o-mini"
                content["analyst_disclaimer"] = "AI investigation advisory summary grounded in ML/XAI evidence."
                return content
        except Exception:
            pass  # fallback

    # Reliable, zero-dependency deterministic synthesis fallback
    return _deterministic_synthesis(
        transaction_id=transaction_id,
        transaction=transaction,
        risk_score=risk_score,
        risk_level=risk_level,
        recommended_action=recommended_action,
        top_factors=top_factors,
    )
