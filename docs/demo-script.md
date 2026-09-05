# RiskGuard AI — 5-Minute Technical Demo Script

> **Track**: Razorpay AI Builder Internship 2026 — AI Risk Manager Track  
> **Topic**: Explainable Transaction Risk Manager  
> **Target Audience**: Technical Evaluation Panel & Risk Engineering Leads

---

## Pitch Structure & Timing Overview

| Timecode | Section | Key Message |
|---|---|---|
| **0:00 – 0:30** | The Problem | Severe class imbalance, high cost of false positives, and the "black-box" auditability dilemma in payments. |
| **0:30 – 1:00** | The Solution | ML-first risk classification + SHAP factor attribution + deterministic policy + AI case investigation. |
| **1:00 – 3:00** | Live Product Demo | Live transaction audit through the React dashboard (Normal payment -> Suspicious -> High-Risk drain -> AI Brief). |
| **3:00 – 3:45** | System Architecture | Strict separation of concerns: Zero-leakage preprocessor, TreeExplainer, policy engine, read-only agent. |
| **3:45 – 4:20** | ML Evaluation & Audit | Temporal split (steps 1–500 train, 501–620 val, 621–743 test), PR-AUC optimization, ablation analysis. |
| **4:20 – 4:45** | What Broke & Real Fixes | 6.36M row memory pressure, SHAP 0.51 3D ndarray bug, CP1252 Windows encoding, balance leakage audit. |
| **4:45 – 5:00** | Impact, Limitations & Roadmap | Honest assessment of PaySim synthetic simulation, GNN roadmap, and concluding statement. |

---

## Detailed Speaking Script

### 0:00 – 0:30: The Problem
> *"Good morning panel. Modern payment gateways like Razorpay process millions of transactions per day. Fraud detection in financial infrastructure faces three core challenges:*  
> *First, **extreme class imbalance**—fraud represents less than 0.15% of transactions, meaning standard accuracy is a completely deceptive metric.*  
> *Second, **the false-positive penalty**—blocking a legitimate merchant or cardholder causes immediate checkout abandonment, brand erosion, and support costs.*  
> *Third, **the black-box problem**—regulators and human risk operations cannot act on a raw, unexplained 0.92 probability score. Analysts need to know exactly why a transaction was flagged and what to do next."*

### 0:30 – 1:00: The Solution
> *"To solve this, I built **RiskGuard AI**—an explainable transaction risk management platform.*  
> *The core design philosophy is strictly **ML-first**: an ensemble tree model estimates calibrated fraud risk; a deterministic policy engine maps probabilities into operational bands (ALLOW, REVIEW, BLOCK); a real-time SHAP layer calculates exact feature attributions; and finally, an AI Risk Investigator synthesizes this structured evidence into plain-language case briefs and audit checklists for human risk officers.*  
> *Critically: the LLM never generates or overrides the risk score—it serves purely as an advisory synthesis layer."*

### 1:00 – 3:00: Live Product Demo
*(Switch screen to React Dashboard at `http://localhost:5173`)*

1. **Dashboard Overview (1:00 – 1:30)**:
   > *"Here is the RiskGuard live operations console. On the top cards, we track real-time session throughput: total analyzed transactions, risk severity breakdowns, and policy actions taken. The charts show our risk distribution and score velocity across time steps."*

2. **Scenario 1: Routine Clean Payment (1:30 – 1:50)**:
   > *"Let's navigate to the Transaction Analyzer. I'll load a standard ₹9.99 merchant payment. When I click 'Evaluate Risk Score', the payload hits our FastAPI backend. The model assigns a Risk Score of **1/100 (ALLOW)**. In the SHAP waterfall below, the green bars indicate mitigating factors: the destination is an established merchant, the amount is modest, and there is no balance drain attempt."*

3. **Scenario 2: High-Risk Account Drain (1:50 – 2:25)**:
   > *"Now, let's load a characteristic PaySim attack: a ₹181.00 transfer where the originator's initial balance was exactly ₹181.00. Clicking evaluate immediately yields a Risk Score of **100/100 (BLOCK)**. Notice the SHAP factor breakdown: `is_full_drain_attempt` contributes **+0.2588** to risk, followed by `amount_to_orig_balance` and transaction type `TRANSFER`.*  
   > *Now watch what happens when I click **'Run Investigation'**: our AI Investigator parses the structured ML and SHAP evidence, producing an Executive Summary, forensic narrative, and a 4-point verification checklist—including placing a hold on the destination wallet and reviewing 48-hour login velocity."*

4. **Scenario 3: Borderline Review Case (2:25 – 3:00)**:
   > *"Finally, loading a large partial transfer of ₹2,500,000 against a ₹5,000,000 balance lands in our **REVIEW** band (Score 44/100). Rather than a hard block, the policy engine routes this case for step-up two-factor authentication or Level-2 analyst inspection."*

### 3:00 – 3:45: Architecture & Dataflow
*(Display `docs/architecture.png`)*
> *"Architecturally, RiskGuard AI enforces strict separation of concerns:*
> - *The frontend communicates with a FastAPI gateway enforcing Pydantic v2 validation.*
> - *The preprocessor computes 14 zero-leakage, pre-authorization features.*
> - *The model layer produces calibrated probabilities evaluated against validation thresholds.*
> - *SHAP TreeExplainer computes exact additive contributions.*
> - *The deterministic decision engine applies validation-calibrated business rules.*
> - *The AI Investigator operates as an advisory layer with a full offline deterministic fallback if no external API key is present.*
> - *Our agent toolkit (`RiskAgent`) is strictly read-only for evidence gathering—it cannot execute transfers or modify transactions."*

### 3:45 – 4:20: ML Evaluation & Technical Audit
> *"Let's discuss the ML evaluation with complete transparency:*  
> *We utilized the 6.36-million row PaySim synthetic dataset with a **strict temporal split**:*
> - *Training on historical steps 1 through 500,*
> - *Validation on steps 501 through 620,*
> - *Held-out test evaluation on steps 621 through 743.*
>
> *We evaluated Logistic Regression, Random Forest, and XGBoost using **PR-AUC (Precision-Recall Area Under Curve)** as our primary metric.*  
> *On the held-out test set of 90,829 transactions, Random Forest caught 1,364 out of 1,366 frauds (99.85% recall) with zero false positives across 89,463 legitimate transactions.*  
> *In our pre-submission audit, we investigated whether this near-perfect metric was driven by leakage. Our ablation study proved that even without the account drain feature, the model achieves 0.99997 Test PR-AUC. However, as an engineer, I must highlight that this high separability is an artifact of the synthetic PaySim simulator where fraud agents execute predictable balance liquidations. In real-world payment data, PR-AUC typically ranges between 0.70 and 0.85."*

### 4:20 – 4:45: What Broke During Development
> *"During implementation, we encountered and solved four real technical bottlenecks:*  
> *1. **Memory exhaustion on 6M rows**: Fitting deep decision trees crashed memory. We preserved 100% of historical frauds while representative-sampling legitimate training cases, reducing training time from over 90 minutes to 64 seconds without altering the full validation or test splits.*  
> *2. **Post-settlement balance leakage**: PaySim's `newbalanceOrig == 0` leaked fraud in 99% of cases. We purged post-transaction fields and restricted inputs purely to pre-authorization signals.*  
> *3. **SHAP 0.51 3D array bug**: For binary Random Forest classifiers, SHAP 0.51 returns a 3D ndarray `(1, 14, 2)`. Slicing required explicit dimension inspection to prevent truth-value comparison errors.*  
> *4. **Windows CP1252 character map error**: Standardized console logging to UTF-8 and ASCII arrows to guarantee cross-platform portability."*

### 4:45 – 5:00: Impact, Limitations & Roadmap
> *"To conclude: RiskGuard AI is an honest, mathematically explainable prototype designed for high-stakes payment risk review.*  
> *With more time, our next production steps include migrating session memory to PostgreSQL, integrating Graph Neural Networks (GNNs) to detect mule account rings, and streaming event scoring via Apache Kafka.*  
> *Thank you, and I welcome your technical questions."*
