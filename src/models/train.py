"""
src/models/train.py
Trains Logistic Regression, Random Forest, and XGBoost on the PaySim dataset.
Uses a strict temporal split:
  - Training window:   step <= 500
  - Validation window: 500 < step <= 620
  - Test window:       step > 620

Reports Precision, Recall, F1, PR-AUC, ROC-AUC, and confusion matrix.
Saves model artifacts and metadata in models/.
"""

import json
import os
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.data.loader import load_raw
from src.features.engineering import engineer_features, FEATURE_COLS, TARGET_COL

PROCESSED_DIR = ROOT / "data" / "processed"
MODELS_DIR = ROOT / "models"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_END_STEP = 500
VAL_END_STEP = 620


def temporal_split(df_feat: pd.DataFrame, raw_steps: pd.Series):
    """
    Split feature DataFrame according to temporal steps.
    To allow fast, high-quality convergence on imbalanced data without memory exhaustion,
    train set retains ALL frauds in the training window + 150,000 sampled legitimate cases.
    Validation and Test sets remain 100% complete with their natural distributions.
    """
    train_mask = raw_steps <= TRAIN_END_STEP
    val_mask = (raw_steps > TRAIN_END_STEP) & (raw_steps <= VAL_END_STEP)
    test_mask = raw_steps > VAL_END_STEP

    train_df = df_feat[train_mask]
    val_df = df_feat[val_mask]
    test_df = df_feat[test_mask]

    # Subsample legitimate in train to preserve all frauds while ensuring efficient CPU training
    train_fraud = train_df[train_df[TARGET_COL] == 1]
    train_legit = train_df[train_df[TARGET_COL] == 0]
    sample_legit = train_legit.sample(n=min(150000, len(train_legit)), random_state=42)
    train_sampled = pd.concat([train_fraud, sample_legit]).sample(frac=1.0, random_state=42)

    X_train = train_sampled[FEATURE_COLS]
    y_train = train_sampled[TARGET_COL]

    X_val = val_df[FEATURE_COLS]
    y_val = val_df[TARGET_COL]

    X_test = test_df[FEATURE_COLS]
    y_test = test_df[TARGET_COL]

    print("\n--- TEMPORAL SPLIT DETAILS ---")
    print(f"  Train Window (steps 1-{TRAIN_END_STEP})    : {len(X_train):>8,} rows | fraud={y_train.sum():,} ({y_train.mean()*100:.3f}%)")
    print(f"  Val Window   (steps {TRAIN_END_STEP+1}-{VAL_END_STEP})  : {len(X_val):>8,} rows | fraud={y_val.sum():,} ({y_val.mean()*100:.3f}%)")
    print(f"  Test Window  (steps {VAL_END_STEP+1}-743)  : {len(X_test):>8,} rows | fraud={y_test.sum():,} ({y_test.mean()*100:.3f}%)")

    return X_train, y_train, X_val, y_val, X_test, y_test


def evaluate(name: str, model, X, y, threshold: float = 0.5) -> dict:
    """Compute and print classification metrics."""
    proba = model.predict_proba(X)[:, 1]
    preds = (proba >= threshold).astype(int)

    pr_auc = float(average_precision_score(y, proba))
    roc_auc = float(roc_auc_score(y, proba))
    cm = confusion_matrix(y, preds)
    report = classification_report(y, preds, target_names=["Legit", "Fraud"], output_dict=True, zero_division=0)

    print(f"\n============================================================")
    print(f"  {name}  (threshold={threshold:.4f})")
    print(f"============================================================")
    print(classification_report(y, preds, target_names=["Legit", "Fraud"], zero_division=0))
    print(f"  PR-AUC (Primary Metric) : {pr_auc:.4f}")
    print(f"  ROC-AUC                : {roc_auc:.4f}")
    print(f"  Confusion Matrix:\n{cm}")

    return {
        "name": name,
        "threshold": float(threshold),
        "precision_fraud": float(report["Fraud"]["precision"]),
        "recall_fraud": float(report["Fraud"]["recall"]),
        "f1_fraud": float(report["Fraud"]["f1-score"]),
        "pr_auc": pr_auc,
        "roc_auc": roc_auc,
        "confusion_matrix": cm.tolist(),
    }


def find_best_threshold(model, X_val, y_val, beta: float = 1.0) -> float:
    """Find the threshold that maximizes F-beta score on validation data."""
    proba = model.predict_proba(X_val)[:, 1]
    precisions, recalls, thresholds = precision_recall_curve(y_val, proba)
    beta2 = beta ** 2
    with np.errstate(invalid="ignore", divide="ignore"):
        fbeta = (1 + beta2) * (precisions * recalls) / (beta2 * precisions + recalls + 1e-9)
    best_idx = int(np.argmax(fbeta[:-1]))
    best_thresh = float(thresholds[best_idx])
    print(f"  Optimal validation threshold (F{beta}): {best_thresh:.4f} -> Precision={precisions[best_idx]:.4f}, Recall={recalls[best_idx]:.4f}")
    return best_thresh


def train():
    start_time = time.time()
    print("[1/5] Loading raw PaySim dataset...")
    raw = load_raw()
    raw_steps = raw["step"].copy()

    print("\n[2/5] Engineering zero-leakage pre-authorization features...")
    feat_df = engineer_features(raw)
    del raw  # free memory

    # Save small processed sample for inspection / demo
    sample_path = PROCESSED_DIR / "sample_processed.csv"
    feat_df.head(1000).to_csv(sample_path, index=False)
    print(f"  Saved 1,000 row processed sample -> {sample_path}")

    # Split
    X_train, y_train, X_val, y_val, X_test, y_test = temporal_split(feat_df, raw_steps)

    # ─────────────────────────────────────────────────────────────────────────
    # MODEL 1: Logistic Regression
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[3/5] (1/3) Training Logistic Regression...")
    t0 = time.time()
    lr_pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=42,
        ))
    ])
    lr_pipe.fit(X_train, y_train)
    print(f"  Trained in {time.time() - t0:.2f}s")
    lr_thresh = find_best_threshold(lr_pipe, X_val, y_val, beta=1.0)
    lr_val = evaluate("Logistic Regression (Validation Set)", lr_pipe, X_val, y_val, lr_thresh)

    # ─────────────────────────────────────────────────────────────────────────
    # MODEL 2: Random Forest
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[3/5] (2/3) Training Random Forest...")
    t0 = time.time()
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_leaf=10,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    rf_model.fit(X_train, y_train)
    print(f"  Trained in {time.time() - t0:.2f}s")
    rf_thresh = find_best_threshold(rf_model, X_val, y_val, beta=1.0)
    rf_val = evaluate("Random Forest (Validation Set)", rf_model, X_val, y_val, rf_thresh)

    # ─────────────────────────────────────────────────────────────────────────
    # MODEL 3: XGBoost
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[3/5] (3/3) Training XGBoost...")
    t0 = time.time()
    fraud_weight = (len(y_train) - y_train.sum()) / y_train.sum()
    xgb_model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=fraud_weight,
        eval_metric="aucpr",
        early_stopping_rounds=25,
        random_state=42,
        n_jobs=-1,
        tree_method="hist",
    )
    xgb_model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )
    print(f"  Trained in {time.time() - t0:.2f}s")
    xgb_thresh = find_best_threshold(xgb_model, X_val, y_val, beta=1.0)
    xgb_val = evaluate("XGBoost (Validation Set)", xgb_model, X_val, y_val, xgb_thresh)

    # ─────────────────────────────────────────────────────────────────────────
    # MODEL SELECTION (Based on Validation PR-AUC)
    # ─────────────────────────────────────────────────────────────────────────
    candidates = [
        ("LogisticRegression", lr_pipe, lr_thresh, lr_val),
        ("RandomForest", rf_model, rf_thresh, rf_val),
        ("XGBoost", xgb_model, xgb_thresh, xgb_val),
    ]

    best_name, best_model, best_thresh, best_val = max(candidates, key=lambda c: c[3]["pr_auc"])

    print("\n" + "=" * 60)
    print(f"  SELECTION WINNER: {best_name} (Val PR-AUC = {best_val['pr_auc']:.4f})")
    print("=" * 60)

    # ── Final Test Set Evaluation ────────────────────────────────────────────
    print("\n[4/5] Evaluating selected model on Held-out Temporal Test Set...")
    test_metrics = evaluate(f"{best_name} (Held-out Test Set)", best_model, X_test, y_test, best_thresh)

    # ── Save Artifacts ───────────────────────────────────────────────────────
    print("\n[5/5] Saving model artifacts...")
    joblib.dump(best_model, MODELS_DIR / "best_model.joblib")
    joblib.dump(lr_pipe, MODELS_DIR / "logistic_regression.joblib")
    joblib.dump(rf_model, MODELS_DIR / "random_forest.joblib")
    joblib.dump(xgb_model, MODELS_DIR / "xgboost.joblib")

    meta = {
        "model_name": best_name,
        "threshold": best_thresh,
        "feature_cols": FEATURE_COLS,
        "train_end_step": TRAIN_END_STEP,
        "val_end_step": VAL_END_STEP,
        "val_metrics": best_val,
        "test_metrics": test_metrics,
        "all_val_metrics": {c[0]: c[3] for c in candidates},
        "training_duration_seconds": round(time.time() - start_time, 2),
    }

    with open(MODELS_DIR / "model_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"  Artifacts successfully saved to {MODELS_DIR}")
    print(f"  Total time: {time.time() - start_time:.1f}s")
    return meta


if __name__ == "__main__":
    train()
