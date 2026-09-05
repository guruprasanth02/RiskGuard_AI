"""
src/data/loader.py
Loads the raw PaySim CSV with memory-efficient dtypes.
"""
import os
import pandas as pd
from pathlib import Path

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
PROCESSED_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

# Explicit dtypes to reduce memory usage on the ~470 MB CSV
DTYPE_MAP = {
    "step": "int32",
    "type": "category",
    "amount": "float32",
    "nameOrig": "object",
    "oldbalanceOrg": "float32",
    "newbalanceOrig": "float32",
    "nameDest": "object",
    "oldbalanceDest": "float32",
    "newbalanceDest": "float32",
    "isFraud": "int8",
    "isFlaggedFraud": "int8",
}


def find_raw_csv() -> Path:
    """Locate the PaySim CSV in data/raw/, regardless of exact filename."""
    candidates = list(RAW_DATA_DIR.glob("*.csv"))
    if not candidates:
        raise FileNotFoundError(
            f"No CSV found in {RAW_DATA_DIR}. "
            "Please download the PaySim dataset from Kaggle and place it there."
        )
    if len(candidates) > 1:
        print(f"[WARNING] Multiple CSVs found in {RAW_DATA_DIR}, using: {candidates[0].name}")
    return candidates[0]


def load_raw(nrows: int | None = None) -> pd.DataFrame:
    """
    Load the raw PaySim CSV.

    Parameters
    ----------
    nrows : int or None
        If set, load only the first N rows (useful for quick exploration).

    Returns
    -------
    pd.DataFrame
    """
    csv_path = find_raw_csv()
    print(f"[Loader] Loading: {csv_path.name}  (nrows={nrows or 'all'})")
    df = pd.read_csv(csv_path, dtype=DTYPE_MAP, nrows=nrows)
    print(f"[Loader] Shape: {df.shape}")
    return df
