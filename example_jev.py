"""
Example usage of JevClient for TypeSafe AI decisions.
Demonstrates 3 primitives:
1. client.decide(...) -> Boolean condition and calibrated probability
2. client.choose(...) -> Multi-alternative action selection
3. client.score(...)  -> Impact and severity assessment
"""

from exactor_accelerator.engine.jev_client import JevClient

client = JevClient()

print("==================================================")
print("1. EXAMPLE: client.evaluate with Noul (Probability / Condition)")
print("==================================================")
suspicious_transaction = {
    "amount": 3800.0,
    "failed_attempts": 3,
    "country_risk": "HIGH",
    "is_new_device": 1,
}

res_decision = client.evaluate(
    state=suspicious_transaction,
    questions={
        "is_fraud": {
            "type": "noul",
            "instructions": "Does this transaction present an imminent risk of banking fraud?",
        }
    },
)

noul_res = res_decision["nouls"]["is_fraud"]
print(f"Calculated Probability: {noul_res['noul'] * 100:.1f}%")
print(f"Uncertainty:            {noul_res['uncertainty']:.4f}")
print(f"Latency:                {res_decision['latency_ms']} ms\n")


print("==================================================")
print("2. EXAMPLE: Choice (Select Business Action)")
print("==================================================")
safe_transaction = {
    "amount": 18.50,
    "failed_attempts": 0,
    "country_risk": "LOW",
    "is_new_device": 0,
}

res_action = client.evaluate(
    state=safe_transaction,
    questions={
        "action": {
            "type": "choice",
            "instructions": "What security action should be executed?",
            "criteria": {
                "BLOCK_ACCOUNT": "If there are clear attack patterns",
                "REQUEST_2FA": "If there is minor authentication doubt",
                "DIRECT_APPROVAL": "If it is a standard and secure transaction",
            },
        }
    },
)

choice_res = res_action["choices"]["action"]
print(f"Recommended Action:     {choice_res['choice']}")
print(f"Action Confidence:      {choice_res['confidence'] * 100:.1f}%")
print(f"Probability Distribution:{choice_res['probabilities']}\n")


print("==================================================")
print("3. EXAMPLE: Score (Severity Level / Continuous Spectrum)")
print("==================================================")
cloud_incident = {
    "p99_latency_ms": 420.0,
    "http_error_rate": 14.5,
    "cpu_pct": 94.0,
}

res_score = client.evaluate(
    state=cloud_incident,
    questions={
        "severity": {
            "type": "score",
            "instructions": "Assess service degradation impact level on infrastructure",
            "criteria": {
                "low": "Negligible or normal operational variance",
                "medium": "Moderate degradation requiring precaution",
                "critical": "Severe impact, mandatory automated mitigation",
            },
        }
    },
)

score_res = res_score["scores"]["severity"]
print(f"Numeric Score (0-100):  {score_res['score']}")
print(f"Distribution:           {score_res['distribution']}")
print(f"Total Latency:          {res_score['latency_ms']} ms")
print("==================================================")
