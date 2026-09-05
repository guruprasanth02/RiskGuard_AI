# RiskGuard AI — Explainable Transaction Risk Manager

> **Built for the Razorpay AI Builder Internship 2026 — AI Risk Manager Track**  
> *A production-grade, explainable machine learning system for real-time payment fraud detection, transparent risk scoring, SHAP-driven factor attribution, and AI-assisted analyst investigation.*

---

## 1. Problem Statement

Modern payment gateways and fintech platforms process millions of financial transactions daily. Fraudulent operations—including account takeover (ATO), synthetic identities, and rapid balance drainage—inflict massive direct financial losses and erode consumer trust.

Standard industry challenges include:
1. **Extreme Class Imbalance**: Fraud represents less than 0.15% of all payment transactions, making standard classification accuracy deceptive.
2. **The "Black-Box" Dilemma**: Machine learning models often produce risk scores without actionable explanations, forcing human risk analysts to manually reconstruct why a payment was blocked.
3. **Data Leakage in Benchmarks**: Naive training on synthetic datasets frequently incorporates post-settlement balances or simulation heuristics, creating artificially inflated metrics that fail in real-world deployment.

## 2. Why It Matters

In high-throughput financial environments:
- **False Positives** insult legitimate customers, increase cart abandonment, and inflate operational support costs.
- **False Negatives** result in direct chargeback losses, processor penalties, and compliance scrutiny.
- **Regulatory Accountability**: Global compliance frameworks (including RBI, GDPR, and PCI-DSS) increasingly mandate transparent reasoning behind automated adverse financial actions.

RiskGuard AI directly addresses this by providing **deterministic, calibrated risk boundaries**, **exact mathematical feature attributions via SHAP**, and **actionable investigative protocols** for risk operations teams.

## 3. Solution Overview

RiskGuard AI separates predictive machine learning, mathematical explainability, deterministic policy enforcement, and AI-assisted investigation into discrete architectural layers:

```
Transaction Event
       ↓
Zero-Leakage Preprocessing & Feature Engineering
       ↓
Supervised Fraud Risk Model (RandomForest / XGBoost)
       ↓
Risk Probability & Calibrated Score (0–100)
       ↓
SHAP Explainability Layer (TreeExplainer Attribution)
       ↓
Deterministic Policy Decision Engine (ALLOW / REVIEW / BLOCK)
       ↓
AI Risk Investigator (Advisory Synthesis & Analyst Action Protocols)
       ↓
Fintech Risk Operations Dashboard (React 18 + Vite)
```

## 4. Key Features

- **Empirically Validated ML Core**: Trained on 6.36 million PaySim synthetic financial transactions using strict temporal validation.
- **Strict Zero Data Leakage**: Excludes all post-settlement fields and simulation artifacts; utilizes solely pre-authorization transaction signals.
- **Model Explainability with SHAP**: Computes real-time Shapley values per transaction, highlighting both primary risk drivers and mitigating factors.
- **Validation-Calibrated Decision Engine**: Replaces arbitrary thresholds with validation-optimized policy bands (`ALLOW < 30%`, `REVIEW 30%–60%`, `BLOCK ≥ 60%`).
- **AI Risk Investigator (Human-in-the-Loop)**: Synthesizes structured model evidence into executive case summaries and concrete audit checklists without overriding ML predictions.
- **Professional Fintech Dashboard**: Real-time transaction monitoring, interactive risk gauges, SHAP waterfall bars, and test scenario presets.
- **Resilient Offline Architecture**: Completely functional without external LLM keys via an embedded expert synthesis engine.

---

## 5. Architecture

```
React 18 Frontend (Vite)
      ↓ (REST / JSON)
FastAPI Backend Gateway
      ↓
Risk Prediction Service
      ├── Preprocessing & Feature Engineering (Zero Leakage)
      ├── ML Model Inference (Random Forest / XGBoost)
      └── Explainability Engine (SHAP TreeExplainer)
      ↓
Decision Policy Engine (ALLOW / REVIEW / BLOCK)
      ↓
AI Investigation Layer (Advisory Case Synthesis)
      ↓
Live Risk Monitoring Dashboard
```

Architecture Diagram saved at: `docs/architecture.png`

---

## 6. Dataset

- **Dataset**: PaySim Synthetic Financial Transaction Dataset ([Kaggle](https://www.kaggle.com/datasets/ealaxi/paysim1)).
- **Volume**: 6,362,620 transactions across 743 hourly simulation steps (~31 days).
- **Class Imbalance**:
  - Legitimate (0): 6,354,407 transactions (99.871%)
  - Fraudulent (1): 8,213 transactions (0.129%)
  - Imbalance Ratio: ~1 fraud per 773 legitimate transactions.
- **Transaction Types**:
  - `CASH_OUT`: 2,237,500 rows | 4,116 fraud (0.184%)
  - `PAYMENT`: 2,151,495 rows | 0 fraud (0.000%)
  - `CASH_IN`: 1,399,284 rows | 0 fraud (0.000%)
  - `TRANSFER`: 532,909 rows | 4,097 fraud (0.769%)
  - `DEBIT`: 41,432 rows | 0 fraud (0.000%)
  *Observation*: Fraud occurs **strictly in `TRANSFER` and `CASH_OUT` transactions**.

---

## 7. Data Leakage Considerations

| Feature | Audit Finding | Decision | Technical Rationale |
|---|---|---|---|
| `newbalanceOrig` | Settle outcome | **EXCLUDED** | Post-transaction state. In PaySim fraud cases, `newbalanceOrig == 0` in >99% of transactions where initial balance > 0 (account drain). Using it leaks the post-fraud state before settlement. |
| `newbalanceDest` | Settle outcome | **EXCLUDED** | Post-transaction recipient balance; contains simulation artifacts (remains zero during many large transfers). |
| `isFlaggedFraud` | Simulator Rule | **EXCLUDED** | A naive simulation rule (>200,000 in transfer) capturing only 16 of 8,213 frauds (0.19% recall). Including it introduces artificial rule target leakage. |
| `nameOrig` | Customer ID | **EXCLUDED** | Over 6.35M unique strings. High cardinality leads to synthetic ID memorization and zero generalization to unseen users. |
| `nameDest` | Recipient ID | **TRANSFORMED** | Converted to structural merchant indicator `dest_is_merchant` (`nameDest.startswith('M')`). |

---

## 8. Feature Engineering

RiskGuard AI computes 14 reproducible, pre-authorization features:

1. `amount`: Raw transaction volume.
2. `log1p_amount`: $\log(1 + \text{amount})$ to compress heavy-tailed financial distributions.
3. `hour_of_day`: Derived from $\text{step} \pmod{24}$ to capture diurnal patterns.
4. `day_of_month`: Derived from $\lfloor \text{step} / 24 \rfloor$ for cyclical velocity.
5. `type_encoded`: Categorical encoding of transaction type.
6. `is_cash_out`: Binary indicator for cash-out attempts.
7. `is_transfer`: Binary indicator for transfer operations.
8. `orig_balance_before`: Available funds in originator account (`oldbalanceOrg`).
9. `dest_balance_before`: Existing recipient balance prior to credit (`oldbalanceDest`).
10. `amount_to_orig_balance`: Ratio $\frac{\text{amount}}{\text{orig\_balance} + 1}$ signaling full liquidation or overdraft.
11. `is_full_drain_attempt`: Boolean flag indicating $|\text{amount} - \text{orig\_balance}| < 1.0$ (hallmark of account takeover).
12. `is_orig_zero_balance`: Boolean flag if originating account starts with 0 balance.
13. `is_dest_zero_balance`: Boolean flag if destination account starts with 0 balance.
14. `dest_is_merchant`: Structural prefix test for merchant recipients (`M...`).

---

## 9. Models Evaluated & Temporal Split Strategy

To prevent future temporal information from contaminating model training, data was split by simulation step:
- **Training Set (Steps 1–500)**: 155,561 records (all 5,561 historical frauds + 150,000 sampled legitimate cases).
- **Validation Set (Steps 501–620)**: 209,984 records (unmodified natural distribution, 1,286 frauds, 0.612% prevalence).
- **Held-Out Test Set (Steps 621–743)**: 90,829 records (unmodified natural distribution, 1,366 frauds, 1.504% prevalence).

### Models Tested:
1. **Logistic Regression**: Scaled pipeline with balanced class weighting.
2. **Random Forest**: 100 estimators, max depth 12, min samples leaf 10, balanced weighting.
3. **XGBoost**: Histogram tree method, scale_pos_weight, early stopping on PR-AUC.

---

## 10. Actual Evaluation Results

> *All metrics reported below are from actual model executions on the PaySim validation and test splits. No metrics are fabricated.*

### Validation Set Comparison (Steps 501–620; 209,984 transactions, 1,286 frauds):

| Model | Optimal Threshold | Precision (Fraud) | Recall (Fraud) | F1-Score | PR-AUC (Primary) | ROC-AUC | Confusion Matrix (TN / FP / FN / TP) |
|---|---|---|---|---|---|---|---|
| **Logistic Regression** | 0.1985 | 99.92% | 99.84% | 0.9988 | **0.9992** | 0.9996 | 208,697 / 1 / 2 / 1,284 |
| **Random Forest** | 0.7864 | **100.0%** | **99.92%** | **0.9996** | **1.0000** | **1.0000** | 208,698 / 0 / 1 / 1,285 |
| **XGBoost** | 0.5741 | **100.0%** | **100.0%** | **1.0000** | **1.0000** | **1.0000** | 208,698 / 0 / 0 / 1,286 |

### Selected Model: Random Forest
Selected based on top validation PR-AUC and zero false positives.

### Held-Out Test Set Performance (Steps 621–743; 90,829 transactions, 1,366 frauds):

- **Precision**: `100.0%` (1.0000) — **Zero false positives** across 89,463 legitimate transactions!
- **Recall**: `99.85%` (0.9985) — Caught 1,364 out of 1,366 frauds.
- **F1-Score**: `0.9993`
- **PR-AUC**: `1.0000` (0.999995)
- **ROC-AUC**: `1.0000`
- **Test Confusion Matrix**:
  $$\begin{pmatrix} \text{TN}: 89,463 & \text{FP}: 0 \\ \text{FN}: 2 & \text{TP}: 1,364 \end{pmatrix}$$

---

## 11. Explainability (SHAP)

RiskGuard AI leverages `shap.TreeExplainer` to calculate exact Shapley feature attributions for every prediction:
- **Base Value**: Expected log-odds across the training distribution.
- **Factor Contributions**: Each feature is decomposed into positive risk-increasing or negative mitigating factors.
- **Example Attribution for Fraud Pattern**:
  1. `is_full_drain_attempt`: `+0.25885` (Primary risk indicator)
  2. `amount_to_orig_balance`: `+0.09145` (Critical balance exposure)
  3. `type_encoded`: `+0.05579` (High-risk transaction category)
  4. `is_transfer`: `+0.04198` (Direct transfer mechanics)
  5. `hour_of_day`: `+0.03414` (Off-hour execution)

---

## 12. Decision Engine

The decision engine applies deterministic governance bands calibrated on the validation set:
- **ALLOW** ($\text{Risk Score} < 30$): Clean financial transactions routed for straight-through processing.
- **REVIEW** ($30 \le \text{Risk Score} < 60$): Borderline cases flagged for second-factor authentication or analyst inspection.
- **BLOCK (Recommended)** ($\text{Risk Score} \ge 60$): High-risk anomalies routed for immediate containment.

*Notice: These decisions are prototype recommendations designed for analyst decision-support.*

---

## 13. AI Investigator & Agentic Layer

- **Architectural Principle**: The core prediction is 100% ML-driven. The LLM acts purely as an evidence-gathering and case-summary assistant.
- **Structured Evidence Input**: Transaction attributes, risk score, decision recommendation, and top SHAP factors.
- **Output**:
  - Executive Case Summary
  - Plain-language forensic explanation
  - Recommended analyst action protocol (contact cardholder, freeze destination, audit 48h velocity)
- **Agentic Toolkit (`RiskInvestigationToolkit`)**:
  - `transaction_lookup`: Retrieve transaction parameters from session memory.
  - `customer_history_lookup`: Audit account history for velocity and prior alerts.
  - `risk_model_lookup`: Inspect model parameters and test metrics.
  - `rule_lookup`: Verify policy band mapping.
  - `gather_docket`: Generate complete evidence docket.

---

## 14. Technical Challenges & How They Were Solved

1. **Memory Exhaustion on 6.36M Rows**: Fitting Random Forest with 200 trees directly on 6.06 million training rows caused memory exhaustion and hours of CPU latency.  
   *Solution*: Preserved 100% of historical fraud cases (5,561) in the temporal training window while sampling 150,000 legitimate cases, reducing training time to 64 seconds while preserving full temporal validation (209k rows) and test (90k rows) distributions.
2. **Post-Settlement Balance Leakage**: Initial inspection revealed `newbalanceOrig == 0` was present in >99% of fraud transactions, creating severe target leakage.  
   *Solution*: Completely removed `newbalanceOrig` and `newbalanceDest` from the model features, replacing them with purely pre-authorization features (`is_full_drain_attempt`, `amount_to_orig_balance`).
3. **SHAP 0.51 3D ndarray Dimensions**: With SHAP 0.51 and binary `RandomForestClassifier`, `shap_values` returned a 3D ndarray `(1, 14, 2)` rather than a list of 2D arrays, causing truth-value ambiguity errors when sorting factors.  
   *Solution*: Implemented dimension inspection (`sv.ndim == 3`) and extracted class 1 slices (`sv[0, :, 1]`).
4. **Windows CP1252 Terminal Encoding**: Script logging with Unicode arrow characters failed on Windows PowerShell with `UnicodeEncodeError`.  
   *Solution*: Standardized on ASCII arrows (`->`) and configured UTF-8 I/O environments.

---

## 15. Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PaySim dataset placed at `data/raw/PS_20174392719_1491204439457_log.csv`

### 1. Clone Repository & Setup Python Environment
```bash
git clone https://github.com/GuruPrasanth003/RiskGuard_AI.git
cd RiskGuard_AI

python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Run Model Training Pipeline
```bash
python src/models/train.py
```
*This trains Logistic Regression, Random Forest, and XGBoost, performs validation threshold optimization, evaluates on the held-out test set, and saves model artifacts to `models/`.*

### 3. Run Test Suite
```bash
python -m pytest tests/ -v
```
*(Runs all 43 unit and integration tests across preprocessing, API validation, decision engine, and AI investigator).*

---

## 16. Running Backend & Frontend

### Start FastAPI Backend (Port 8000)
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation: `http://localhost:8000/docs`

### Start React Frontend Dashboard (Port 5173)
```bash
cd frontend/riskguard-frontend
npm install
npm run dev
```
Access dashboard at: `http://localhost:5173`

---

## 17. API Examples

### POST `/predict`

**Request:**
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "step": 397,
    "type": "TRANSFER",
    "amount": 181.0,
    "oldbalanceOrg": 181.0,
    "newbalanceOrig": 0.0,
    "oldbalanceDest": 0.0,
    "newbalanceDest": 0.0
  }'
```

**Response:**
```json
{
  "transaction_id": "8f0a3e91-c529-4c07-b5bb-84dbfce9d342",
  "timestamp": "2026-09-05T15:10:00.000000Z",
  "fraud_probability": 0.9968,
  "risk_score": 100,
  "risk_level": "HIGH",
  "is_fraud_predicted": true,
  "recommended_action": "BLOCK",
  "explanation": {
    "base_value": 0.5,
    "top_factors": [
      {
        "feature": "is_full_drain_attempt",
        "shap_value": 0.25885,
        "impact": 0.25885,
        "direction": "increases_risk"
      },
      {
        "feature": "amount_to_orig_balance",
        "shap_value": 0.09145,
        "impact": 0.09145,
        "direction": "increases_risk"
      },
      {
        "feature": "is_transfer",
        "shap_value": 0.04198,
        "impact": 0.04198,
        "direction": "increases_risk"
      }
    ]
  },
  "model_name": "RandomForest",
  "threshold_used": 0.7864
}
```

---

## 18. Screenshots & Dashboard Previews

- **System Architecture**: Available at `docs/architecture.png`.
- **Live Risk Dashboard**: Features real-time counters, risk distribution donut charts, actions-taken bar breakdown, score area trends, and live audit tables.
- **Transaction Analyzer**: Includes interactive risk gauge, SHAP waterfall factor bars, demo presets, and AI investigator panels.

---

## 19. Limitations

1. **Synthetic Simulation**: PaySim is a multi-agent simulation; while it models macro payment flows, it lacks complex real-world behavioral signals like device fingerprints, IP geolocation, or behavioral biometrics.
2. **Zero-Fraud Transaction Types**: In PaySim, `PAYMENT`, `CASH_IN`, and `DEBIT` contain 0 fraudulent examples, meaning the model's high recall on those types is largely driven by transaction category rules.
3. **Static Balance Snaphots**: The dataset does not provide fine-grained transaction history per customer over sub-hourly intervals.

---

## 20. Future Work

1. **Graph Neural Networks (GNNs)**: Integrating PyTorch Geometric to capture money-mule laundering rings and cyclic transfer graphs.
2. **PostgreSQL / TimescaleDB Migration**: Migrating live session logs to an ACID-compliant time-series database.
3. **Streaming Ingestion**: Integrating Apache Kafka or Redpanda for sub-10ms event-stream fraud scoring.
4. **Active Learning Feedback Loop**: Allowing risk analysts to submit confirmed chargeback labels to trigger automated model retraining.

---

## 21. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
