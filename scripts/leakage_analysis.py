import pandas as pd
import numpy as np

print("Loading dataset for leakage analysis...")
df = pd.read_csv('data/raw/PS_20174392719_1491204439457_log.csv')
print(f"Loaded {len(df):,} rows.")

fraud = df[df['isFraud'] == 1]
legit = df[df['isFraud'] == 0]

print("--- BALANCE LEAKAGE INVESTIGATION ---")
# Check how often fraudulent transactions zero out the account
drained = ((fraud['oldbalanceOrg'] > 0) & (fraud['newbalanceOrig'] == 0)).mean()
print(f"Fraud where oldbalanceOrg > 0 and newbalanceOrig == 0: {drained*100:.2f}%")

amt_equals_bal = (fraud['amount'] == fraud['oldbalanceOrg']).mean()
print(f"Fraud where amount == oldbalanceOrg: {amt_equals_bal*100:.2f}%")

# Check destination balance anomaly in PaySim:
# In PaySim, many fraud transactions have oldbalanceDest == 0 and newbalanceDest == 0!
dest_both_zero_fraud = ((fraud['oldbalanceDest'] == 0) & (fraud['newbalanceDest'] == 0)).mean()
dest_both_zero_legit = ((legit['oldbalanceDest'] == 0) & (legit['newbalanceDest'] == 0)).mean()
print(f"Fraud where oldbalanceDest == 0 AND newbalanceDest == 0: {dest_both_zero_fraud*100:.2f}%")
print(f"Legit where oldbalanceDest == 0 AND newbalanceDest == 0: {dest_both_zero_legit*100:.2f}%")

print("\n--- IDENTIFIERS (nameOrig, nameDest) INVESTIGATION ---")
orig_counts = df['nameOrig'].value_counts()
print(f"Total unique nameOrig: {df['nameOrig'].nunique():,}")
print(f"Repeat originators: {(orig_counts > 1).sum():,}")
print(f"Max transactions per originator: {orig_counts.max()}")

dest_counts = df['nameDest'].value_counts()
print(f"Total unique nameDest: {df['nameDest'].nunique():,}")
print(f"Repeat destinations: {(dest_counts > 1).sum():,}")
print(f"Max transactions per destination: {dest_counts.max()}")

# Fraud destination reuse
fraud_dest_unique = fraud['nameDest'].nunique()
print(f"Fraud transactions: {len(fraud):,}")
print(f"Unique destinations in fraud: {fraud_dest_unique:,} ({fraud_dest_unique/len(fraud)*100:.2f}% unique)")
dest_in_both = set(fraud['nameDest']).intersection(set(legit['nameDest']))
print(f"Destinations appearing in BOTH fraud and legit: {len(dest_in_both):,}")
