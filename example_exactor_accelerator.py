"""
Example usage of Exactor Accelerator SDK:
Complete Workflow:
1. engine.fit(...)      -> EXACTOR learns logical rules from historical data
2. engine.evaluate(...) -> Evaluates events in real-time combining EXACTOR + JEV
3. engine.explain(...)  -> Generates natural language audit trail with DeepSeek
"""

from exactor_accelerator.sdk import ExactorAccelerator

# 1. Instantiate engine
engine = ExactorAccelerator()

print("==================================================================")
print("STEP 1: TRAINING / RULE DISCOVERY (EXACTOR PHASE A)")
print("==================================================================")

# Train with a historical CSV file (or DataFrame) specifying the target column
# (e.g. fraudulent transactions or customer churn)
csv_history = "exactor_accelerator/data/sample_fraud_transactions.csv"

rules = engine.fit(
    data=csv_history,
    target_col="is_fraud",
    max_variables=16
)

print(f"Discovery Status: {rules['status']}")
print(f"Extracted Boolean Formula: {rules['boolean_formula']}")
print(f"Causal Rule Explanation:\n{rules['explanation']}\n")


print("==================================================================")
print("STEP 2: REAL-TIME PRODUCTION EVALUATION (EXACTOR + JEV)")
print("==================================================================")

# Case A: Suspicious Transaction
suspicious_event = {
    "amount": 3400.0,
    "velocity_1h": 6,
    "country_risk": "HIGH",
    "device_trust": 0.12,
    "failed_pin_attempts": 3,
    "is_new_device": 1
}

res_a = engine.evaluate(suspicious_event)
print(f"--> Transaction of $3,400 USD:")
print(f"    Ruling:              {res_a['decision']} ({res_a['label']})")
print(f"    Executed Action:     {res_a['action']}")
print(f"    Calibrated Certainty:{res_a['probabilistic_certainty']}%")
print(f"    Autonomous Action:   {res_a['autonomous_execution']}")
print(f"    Triggered Endpoint:  {res_a['triggered_endpoint']}")
print(f"    Total Latency:       {res_a['latency_ms']} ms\n")

# Case B: Standard Legitimate Transaction
safe_event = {
    "amount": 25.50,
    "velocity_1h": 1,
    "country_risk": "LOW",
    "device_trust": 0.95,
    "failed_pin_attempts": 0,
    "is_new_device": 0
}

res_b = engine.evaluate(safe_event)
print(f"--> Transaction of $25.50 USD:")
print(f"    Ruling:              {res_b['decision']} ({res_b['label']})")
print(f"    Executed Action:     {res_b['action']}")
print(f"    Calibrated Certainty:{res_b['probabilistic_certainty']}%")
print(f"    Autonomous Action:   {res_b['autonomous_execution']}")
print(f"    Triggered Endpoint:  {res_b['triggered_endpoint']}")
print(f"    Total Latency:       {res_b['latency_ms']} ms\n")


print("==================================================================")
print("STEP 3: NATURAL LANGUAGE AUDIT EXPLANATION (DEEPSEEK)")
print("==================================================================")

# Request natural language audit explanation
audit = engine.explain(suspicious_event)
print("Explanation for Suspicious Transaction:")
print(audit["explanation"])
print(f"(Explanation Latency: {audit['latency_ms']} ms)")
