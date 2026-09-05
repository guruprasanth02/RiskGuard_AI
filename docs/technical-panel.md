# RiskGuard AI — Technical Panel Preparation Guide

> Concise, honest answers for Razorpay AI Builder Internship 2026 technical review panel.
> All answers are grounded in the actual implementation.

---

## 1. Why did you choose the AI Risk Manager track?

Payment fraud causes direct financial losses and erodes consumer trust. AI-based risk management is one of the clearest, most measurable engineering problems in fintech — the inputs, outputs, and ground truth are well-defined. I chose this track because it demands a rigorous ML-first approach with real evaluation metrics, not just UI over an LLM.

---

## 2. Why PaySim?

PaySim is the most commonly cited public synthetic financial transaction dataset with realistic fraud patterns. It is available without licensing restrictions, does not contain real customer PII, and models multi-agent banking behavior including account takeover and balance-drain attacks. It was the highest-quality publicly available option.

---

## 3. Why is PaySim not equivalent to real Razorpay data?

PaySim is a multi-agent simulation built from anonymized West African mobile-money patterns. It lacks:
- Device fingerprints, browser canvas, and behavioral biometrics
- UPI-specific transaction types (UPI P2P, mandate, split)
- IP geolocation and velocity-based signals
- Real merchant category codes (MCC)
- Chargebacks, dispute resolution records, and account linkage graphs

Real Razorpay data would also have far richer contextual signals, more diverse fraud patterns (card-not-present, refund abuse, ATO via OTP relay), and non-stationary fraud evolution.

---

## 4. Why not the famous Kaggle credit card fraud dataset?

The ULB credit card fraud dataset has two problems for this use case:
1. **Features are PCA-anonymized** (V1–V28) with no interpretable semantics — SHAP explanations would produce meaningless output.
2. **Class distribution is fixed** with no temporal structure, so temporal split validation is not possible.

PaySim provides interpretable field names (amount, type, balance) that produce meaningful SHAP attributions, and it has a step-based temporal dimension that enables realistic deployment-style evaluation.

---

## 5. Why temporal split?

Because models are trained on historical data and deployed against future data. If we randomly split, future transactions appear in training — the model can memorize temporal patterns or overfit to fraud clusters that don't generalize. Temporal split simulates the actual deployment scenario:

- Train: Steps 1–500 (historical)
- Validate: Steps 501–620 (recent, unseen at train time)
- Test: Steps 621–743 (future, strictly held-out)

---

## 6. Why not random split?

Random split leaks future transactions into training. In PaySim, transaction amounts and fraud rates vary by step. Randomly assigning step 700 fraud into training and step 200 to test would let the model see "future fraud patterns" during training, inflating metrics unrealistically.

---

## 7. What is class imbalance?

In our dataset: 8,213 fraudulent transactions in 6,362,620 total (0.129%). For every 1 fraud, there are ~773 legitimate transactions. If a naive classifier always predicts "legitimate," it achieves 99.87% accuracy — meaningless for fraud detection.

---

## 8. Why is accuracy misleading?

With 0.129% fraud rate, a model that always says "not fraud" achieves 99.87% accuracy. We need to know: of all flagged transactions, how many are actually fraud (precision)? And: of all actual frauds, how many did we catch (recall)?

---

## 9. What is precision?

$$\text{Precision} = \frac{TP}{TP + FP}$$

The fraction of flagged transactions that are genuinely fraudulent. High precision = fewer false positives = fewer legitimate customers blocked.

---

## 10. What is recall?

$$\text{Recall} = \frac{TP}{TP + FN}$$

The fraction of actual frauds that were flagged. High recall = fewer missed frauds = less financial loss.

---

## 11. Why PR-AUC?

PR-AUC (Precision-Recall Area Under Curve) summarizes the trade-off between precision and recall across all classification thresholds. For severely imbalanced datasets, PR-AUC is much more informative than ROC-AUC because ROC-AUC can remain high even when a classifier performs poorly on the minority class. PR-AUC is 0.5 for a random classifier on balanced data, but degrades sharply on imbalanced data, making it a strict operational metric.

---

## 12. Why Random Forest?

Random Forest achieved the highest validation PR-AUC (1.0000) with zero false positives and one false negative on the 209,984-transaction validation set. It was more stable than XGBoost at the 0.7864 threshold and fully interpretable via SHAP TreeExplainer. It also generalizes well without extensive hyperparameter tuning.

---

## 13. Why XGBoost?

XGBoost was included as an alternative because it handles class imbalance natively via `scale_pos_weight`, supports early stopping on PR-AUC, and is typically the strongest gradient-boosted tree implementation. On validation it achieved PR-AUC 1.0000 with zero false positives and zero false negatives — perfect. Both tied. Random Forest was selected due to tie-breaking simplicity and better threshold interpretability.

---

## 14. Why not deep learning?

Deep learning (MLPs, transformers) is not justified for this problem:
1. Tabular structured data with 14 features does not benefit from learned representations.
2. Deep models are less interpretable — SHAP attributions for MLPs are approximations only.
3. Training time and infrastructure requirements are higher.
4. Tree ensembles consistently outperform deep learning on structured tabular fraud data in literature.

---

## 15. What is SHAP?

SHAP (SHapley Additive exPlanations) is a method grounded in cooperative game theory that assigns each feature a contribution to a specific prediction. The SHAP value for feature $f$ is:

$$\phi_f = \sum_{S \subseteq F \setminus \{f\}} \frac{|S|!(|F|-|S|-1)!}{|F|!} [v(S \cup \{f\}) - v(S)]$$

Unlike feature importance (which is global), SHAP values are **per-prediction** — each flagged transaction gets its own breakdown.

---

## 16. How does SHAP explain a prediction?

For our Random Forest:
1. `shap.TreeExplainer` computes exact (not approximated) Shapley values by traversing the tree ensemble.
2. `base_value` ≈ 0.5 (expected model output over training distribution).
3. Each feature's SHAP value shows how much it pushed the probability up or down from that baseline.
4. Example: `is_full_drain_attempt: +0.259` means this feature alone moved the risk score up by ~26 percentage points.

---

## 17. What is data leakage?

Data leakage occurs when information that would not be available at prediction time influences the model during training, causing artificially inflated evaluation metrics that collapse in deployment.

Examples in our context:
- Using `newbalanceOrig` (post-settlement state) to predict fraud at authorization time
- Using `isFlaggedFraud` (the simulator's own rule-based label)
- Using test set statistics to select a threshold

---

## 18. Which PaySim fields create leakage concerns?

| Field | Concern |
|-------|---------|
| `newbalanceOrig` | Post-transaction account state — not available at authorization time |
| `newbalanceDest` | Post-transaction recipient balance — not available at authorization time |
| `isFlaggedFraud` | Simulator rule — directly derived from the simulation's own labeling logic |
| `nameOrig` / `nameDest` | Raw account IDs — lead to memorization of synthetic IDs, not generalizable |

---

## 19. How did you prevent leakage?

1. **Feature exclusions**: Dropped all post-transaction fields and simulation labels.
2. **Temporal split**: Training window strictly precedes validation and test windows.
3. **Threshold selection on validation only**: The 0.7864 threshold was selected using validation F1 maximization; test data was never touched until final evaluation.
4. **No scaler fitting on combined data**: Logistic Regression uses a pipeline where the scaler is fit only on training data.
5. **`is_full_drain_attempt` is a pre-authorization signal**: It compares `amount` (known at authorization) to `oldbalanceOrg` (known at authorization). Neither requires post-settlement information.

---

## 20. How did you choose the threshold?

Using `precision_recall_curve` on the **validation set only** (steps 501–620). We optimized F1-score across all candidate thresholds and selected the one that maximized it. The test set was never used for this step.

```python
precisions, recalls, thresholds = precision_recall_curve(y_val, proba_val)
fbeta = 2 * (precisions * recalls) / (precisions + recalls + 1e-9)
best_thresh = thresholds[np.argmax(fbeta[:-1])]
```

Selected threshold: **0.7864** for Random Forest.

---

## 21. Why is the LLM not responsible for fraud prediction?

LLMs generate plausible text — they do not guarantee calibrated probability estimates over structured financial attributes. An LLM asked "is this transaction fraudulent?" would produce inconsistent, non-reproducible, and non-auditable answers. Regulatory frameworks (RBI, PCI-DSS) require deterministic, explainable risk decisions. The ML model provides exact probabilities; the LLM synthesizes structured ML evidence into human-readable investigation summaries.

---

## 22. What does the AI Investigator do?

The AI Investigator receives **structured evidence only**:
- Transaction attributes
- ML risk score
- Policy decision (ALLOW/REVIEW/BLOCK)
- Top SHAP factor attributions

It generates:
- Executive case summary
- Plain-language forensic explanation
- Recommended analyst action protocol (specific verification steps)

It cannot generate or modify the risk score.

---

## 23. What does the agent do?

`RiskAgent` in `src/investigation/agent.py` provides an **evidence-gathering workflow** for risk analysts. Available read-only tools:
- `transaction_lookup`: Retrieve previously analyzed transactions from the in-memory session log
- `customer_history_lookup`: Summarize account history (count, high-risk frequency)
- `risk_model_lookup`: Return current model metadata and test metrics
- `rule_lookup`: Map a risk score to the policy band
- `gather_docket`: Compile a structured evidence docket for analyst handoff

---

## 24. How do you prevent the agent from taking unsafe actions?

The `RiskAgent` has no write tools, no payment system API access, and no ability to execute financial transactions. All methods return read-only data structures. The tool list is explicitly bounded to the five functions listed above. There is no mechanism to call external payment APIs, modify database records, or block real accounts.

---

## 25. What happens if the LLM is unavailable?

`run_ai_investigation()` first checks `os.getenv("OPENAI_API_KEY")`. If unavailable (or API call fails), it silently falls back to `_deterministic_synthesis()` — a rule-based synthesis engine that generates natural-language case summaries directly from the SHAP factors, risk level, and transaction attributes without any network call. The full application remains functional.

---

## 26. What happens if the model is wrong?

Two residual errors in our test set:
- **False Negatives (2)**: Two frauds were assigned probabilities below the 0.7864 threshold. These would be missed by the automated system and pass through as ALLOW.
- **False Positives (0)**: None on the 89,463-transaction test set.

In production mitigation: human analyst review, fraud velocity monitoring, chargeback integrations as a feedback loop, and threshold adjustment based on operational cost ratios.

---

## 27. How would you reduce false positives?

1. Lower the HIGH threshold from 60% to 75% (increasing precision at the cost of recall in the HIGH band).
2. Add a "soft block" escalation requiring additional authentication rather than hard reject.
3. Add cardholder friction (step-up OTP) at the REVIEW band to reduce unnecessary declines.

---

## 28. How would you deploy this at scale?

1. Serve the model via FastAPI behind a load balancer (AWS ALB / GCP Load Balancer).
2. Use model serialization with joblib; cache in memory at startup.
3. Compute SHAP at request time (TreeExplainer is fast for RF/XGBoost: <50ms).
4. Store transactions in PostgreSQL / TimescaleDB.
5. Run Kafka/Redpanda for event streaming.
6. Use Prometheus + Grafana for live inference metrics.
7. Deploy model versions with blue/green rollout.

---

## 29. How would you handle concept drift?

1. Monitor KL-divergence between training feature distributions and live inference feature distributions.
2. Track daily precision/recall on confirmed fraud labels from chargeback feeds.
3. Retrain weekly with a rolling 90-day training window.
4. Use champion/challenger A/B testing during retraining.
5. Alert on threshold drift (when optimal validation threshold diverges from deployed threshold by >0.05).

---

## 30. How would this work with real Razorpay data?

1. Map Razorpay payment events to equivalent features (amount, instrument type, source/destination account type, timestamp step, balance context).
2. Add Razorpay-specific signals: UPI VPA type, device fingerprint hash, BIN country, card network.
3. Re-train and re-evaluate on actual labeled chargeback/dispute data.
4. Adjust risk bands based on actual operational cost ratios (false positive cost vs. fraud loss).
5. Integrate investigation summaries into Razorpay's existing risk analyst tooling.

---

## 31. What are the biggest limitations?

1. Synthetic dataset — PaySim fraud patterns are simpler and more deterministic than real-world fraud.
2. Fraud concentrated in only two transaction types (`TRANSFER`, `CASH_OUT`).
3. No behavioral biometrics or device signals.
4. In-memory session storage (no persistence between restarts).
5. SHAP computation time grows with forest size — at scale would require background pre-computation.

---

## 32. What would you improve with more time?

1. Graph Neural Network layer to detect money mule rings via transaction graph topology.
2. Real-time streaming ingestion via Kafka.
3. PostgreSQL/TimescaleDB for persistent transaction audit log.
4. Automated model retraining pipeline with drift detection.
5. Privacy-preserving feature engineering (hashed account IDs for velocity features).
6. Richer explainability UI with full SHAP waterfall plots and counterfactual analysis.
