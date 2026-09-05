"""
src/features/engineering.py
Reproducible, zero-leakage feature engineering pipeline for PaySim fraud detection.

PRE-AUTHORIZATION RISK SIGNALS (Zero Data Leakage)
──────────────────────────────────────────────────
Included features (100% available prior to transaction execution):
  amount                  — transaction value
  log1p_amount            — log(1 + amount) to normalize large skewed tail
  hour_of_day             — step % 24 (temporal hourly pattern)
  day_of_month            — step // 24 (day in monthly cycle)
  type_encoded            — integer encoded transaction category
  is_cash_out             — binary flag for CASH-OUT
  is_transfer             — binary flag for TRANSFER
  orig_balance_before     — oldbalanceOrg (originator available funds)
  dest_balance_before     — oldbalanceDest (destination balance before receipt)
  amount_to_orig_balance  — amount / (orig_balance + 1); indicates full account drain or overdraft
  is_full_drain_attempt   — binary flag: abs(amount - orig_balance_before) < 1.0 (fraudsters drain accounts)
  is_orig_zero_balance    — binary flag: orig_balance_before == 0
  is_dest_zero_balance    — binary flag: dest_balance_before == 0
  dest_is_merchant        — binary flag: destination account is a merchant (starts with 'M')

EXCLUDED FEATURES (Audit & Justification):
─────────────────────────────────────────
1. nameOrig, nameDest:
   - High-cardinality raw strings (>6.35M unique values).
   - Leads to synthetic ID memorization and cannot generalize to new users.
   - We extract only the structural merchant flag: dest_is_merchant = nameDest.startswith('M').

2. newbalanceOrig:
   - Post-settlement account state. At authorization time, transaction is pending.
   - Leakage: In PaySim, fraudulent transactions artificially zero out newbalanceOrig in >99%
     of cases where oldbalanceOrg > 0. Using it would leak the post-drain state.

3. newbalanceDest:
   - Post-settlement recipient state. Not available at decision time.
   - Contains simulation artifacts (stays 0 for many large transfers).

4. isFlaggedFraud:
   - Simulator heuristic flag (>200k in transfer). Only 16 true positives in 6.36M rows.
   - Using simulator internal labels as inputs causes target leakage.
"""

import numpy as np
import pandas as pd

_TYPE_MAP = {
    "CASH_IN": 0,
    "CASH_OUT": 1,
    "DEBIT": 2,
    "PAYMENT": 3,
    "TRANSFER": 4,
}


def _normalize_type(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace("-", "_").str.upper()


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the feature matrix from a raw PaySim DataFrame using strictly
    pre-authorization features.
    """
    out = pd.DataFrame(index=df.index)

    # ── Amount features ──────────────────────────────────────────────
    amount = df["amount"].astype("float32").clip(lower=0)
    out["amount"] = amount
    out["log1p_amount"] = np.log1p(amount).astype("float32")

    # ── Time features ─────────────────────────────────────────────────
    step = df["step"].astype("int32")
    out["hour_of_day"] = (step % 24).astype("int8")
    out["day_of_month"] = (step // 24).astype("int8")

    # ── Transaction type ─────────────────────────────────────────────
    norm_type = _normalize_type(df["type"])
    out["type_encoded"] = norm_type.map(_TYPE_MAP).fillna(-1).astype("int8")
    out["is_cash_out"] = (norm_type == "CASH_OUT").astype("int8")
    out["is_transfer"] = (norm_type == "TRANSFER").astype("int8")

    # ── Pre-transaction balances ─────────────────────────────────────
    orig_before = df["oldbalanceOrg"].astype("float32").clip(lower=0)
    dest_before = df["oldbalanceDest"].astype("float32").clip(lower=0)
    out["orig_balance_before"] = orig_before
    out["dest_balance_before"] = dest_before

    # ── Behavioral & Risk indicators (strictly pre-authorization) ─────
    # Ratio of amount to available balance
    out["amount_to_orig_balance"] = (amount / (orig_before + 1.0)).astype("float32")

    # Full drain attempt: fraudster attempts to withdraw/transfer exact account balance
    out["is_full_drain_attempt"] = (
        (orig_before > 0) & (np.abs(amount - orig_before) < 1.0)
    ).astype("int8")

    # Zero balance flags
    out["is_orig_zero_balance"] = (orig_before == 0).astype("int8")
    out["is_dest_zero_balance"] = (dest_before == 0).astype("int8")

    # Destination type: Merchant ('M...') vs Customer ('C...')
    if "nameDest" in df.columns:
        out["dest_is_merchant"] = df["nameDest"].astype(str).str.startswith("M").astype("int8")
    else:
        out["dest_is_merchant"] = np.zeros(len(df), dtype="int8")

    # ── Target (if present) ──────────────────────────────────────────
    if "isFraud" in df.columns:
        out["isFraud"] = df["isFraud"].astype("int8")

    return out


FEATURE_COLS = [
    "amount",
    "log1p_amount",
    "hour_of_day",
    "day_of_month",
    "type_encoded",
    "is_cash_out",
    "is_transfer",
    "orig_balance_before",
    "dest_balance_before",
    "amount_to_orig_balance",
    "is_full_drain_attempt",
    "is_orig_zero_balance",
    "is_dest_zero_balance",
    "dest_is_merchant",
]

TARGET_COL = "isFraud"
