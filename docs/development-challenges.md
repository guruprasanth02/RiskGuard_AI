# RiskGuard AI — Development Challenges

> Real engineering challenges encountered during implementation. No challenges are invented.

---

## Challenge 1 — Training Memory Exhaustion on 6.36M PaySim Rows

### Problem
First attempt: directly fitting `RandomForestClassifier` (100 estimators) on 6.06 million training rows caused the Python process to consume >12 GB RAM and ran for over 90 minutes without completing on a standard development machine.

### Root Cause
Random Forest builds 100 independent decision trees, each requiring full-dataset traversal for node splitting. At 6M rows × 11 features × 100 trees, the working memory requirement exceeded available resources.

### Solution
Retained **all 5,561 historical fraud cases** in the temporal training window and sampled **150,000 legitimate cases** at random (seeded for reproducibility). This preserved the full fraud distribution (no undersampling of minority class) while reducing the training set from 6M to 155,561 rows — a 40× compression of legitimate examples.

Validation and test sets remained **100% complete** with their natural distributions (209,984 and 90,829 rows, respectively), so evaluation integrity was unaffected.

### Result
Training time reduced from >90 minutes (aborted) to **64 seconds** with equivalent validation PR-AUC (1.0000).

---

## Challenge 2 — SHAP 0.51 Returns 3D ndarray, Not List

### Problem
After upgrading to SHAP 0.51, `shap.TreeExplainer.shap_values()` called on a binary `RandomForestClassifier` returned a **3D numpy array** of shape `(n_samples, n_features, n_classes)` rather than the historical format `[class_0_array, class_1_array]`. The code `if isinstance(sv, list)` never triggered, leaving `sv` as a 3D array. When `sorted(zip(feature_cols, shap_vals))` tried to compare array elements, Python raised:
```
ValueError: The truth value of an array with more than one element is ambiguous.
```

### Root Cause
SHAP's TreeExplainer API changed output format between versions. SHAP 0.51 returns a single 3D array `(1, 14, 2)` for a single-sample, binary classification RF, where the third axis indexes the class.

### Solution
Added explicit dimension inspection before slicing:
```python
if isinstance(sv, np.ndarray) and sv.ndim == 3:
    shap_vals = sv[0, :, 1].tolist()  # class 1 (fraud), first sample
elif isinstance(sv, list) and len(sv) >= 2:
    shap_vals = sv[1][0].tolist()     # legacy format
elif isinstance(sv, np.ndarray) and sv.ndim == 2:
    shap_vals = sv[0].tolist()
```

### Result
SHAP explanations now correctly produce feature-level contributions for each transaction, verified across three distinct test cases.

---

## Challenge 3 — Windows CP1252 Terminal Encoding Failure

### Problem
Training script failed on Windows with `UnicodeEncodeError: 'charmap' codec can't encode character '\u2192'` when the progress logger printed `Loading dataset → engineering features` — the Unicode arrow character is not representable in Windows CP1252 (the default console codepage on the development machine).

### Root Cause
Python on Windows defaults to the system code page (CP1252 / Windows-1252) for stdout/stderr unless explicitly overridden, even when the source file is UTF-8.

### Solution
Replaced all Unicode arrow characters (`→`) with ASCII equivalents (`->`) in log print statements. Also documented the workaround `$env:PYTHONIOENCODING='utf-8'` for users who prefer Unicode output in PowerShell.

### Result
Training script runs cleanly on Windows without encoding errors.

---

## Challenge 4 — data/raw CSV Discovery Path Inconsistency

### Problem
The data loader originally assumed the CSV was at `data/raw/*.csv` relative to the project root. During initial setup the CSV was placed directly at the project root `d:\RiskGuard_AI\PS_20174392719_1491204439457_log.csv`, causing `FileNotFoundError` when running `train.py`.

### Root Cause
Initial setup instructions placed the file at the root; the loader expected it in the `data/raw/` subdirectory per the documented structure.

### Solution
Moved the CSV to `data/raw/` and updated the loader to `glob(DATA_RAW_DIR / "*.csv")` with a clear error message pointing to the correct location. Added `data/README.md` documenting the exact expected path and download URL.

### Result
Loader correctly discovers the dataset with a clear error message if the file is missing.

---

## Challenge 5 — Pydantic v2 Deprecation Warnings in FastAPI

### Problem
After upgrading to Pydantic v2, the existing `api/main.py` used Pydantic v1 syntax:
- `class Config: schema_extra = {...}` (renamed to `model_config = ConfigDict(json_schema_extra=...)`)
- `@validator` (renamed to `@field_validator`)
- `req.dict()` (renamed to `req.model_dump()`)
- `Field(..., example=...)` (moved to `json_schema_extra`)

While the code still ran (Pydantic v2 ships a compatibility shim), it emitted 22 deprecation warnings during every test run.

### Root Cause
Pydantic made breaking API changes between v1 and v2; many FastAPI tutorials and examples still show v1 syntax.

### Solution
Migrated `api/main.py` to full Pydantic v2 syntax:
- `ConfigDict` for model configuration
- `@field_validator` with `@classmethod` decorator
- `model_dump()` for serialization
- `json_schema_extra` for OpenAPI examples

### Result
Test suite reports only 1 deprecation warning (from the test client library itself, not our code).

---

## Challenge 6 — `is_full_drain_attempt` Leakage Concern

### Problem
The `is_full_drain_attempt` flag (`|amount - oldbalanceOrg| < 1.0`) is the top SHAP contributor and fires in 97.63% of fraud transactions vs. 0.0006% of legitimate transactions. During the pre-submission audit, we questioned whether this was a legitimate pre-authorization signal or accidental leakage.

### Root Cause
`oldbalanceOrg` is the sender's balance **before** the transaction — known at authorization time. `amount` is the transaction amount — also known at authorization time. The flag computes a relationship between two pre-authorization fields and captures a deliberate "account drain" pattern observable before the transaction settles.

### Verification
Ablation experiment confirmed:
- **With** `is_full_drain_attempt`: Val PR-AUC = 1.0000, Test PR-AUC = 0.99999
- **Without** `is_full_drain_attempt`: Val PR-AUC = 0.99999, Test PR-AUC = 0.99998

The remaining 13 features preserve near-perfect performance, confirming the result is not artificially dependent on one synthetic feature.

### Resolution
Feature retained. It is a legitimate pre-authorization behavioral signal representing the "exact balance drain" attack vector — a pattern that is observable without any post-settlement information.
