"""
Exactor Accelerator v2.0 - Unified Demonstration
Demonstrates Unsupervised Learning, Supervised Boolean Minimization,
Zero-Data Autonomous Cold-Start Distillation, and Causal Explainability.
"""

import pandas as pd
from exactor_accelerator import (
    ExactorAccelerator,
    ExactorAcceleratorClassifier,
    get_feature_engine,
    get_regime_detector,
)

# 1. Raw unlabeled stream (or load via pd.read_csv("your_data.csv"))
raw_df = pd.DataFrame({
    "amount": [45.0, 120.5, 950.0, 15.0, 2100.0, 32.0, 1500.0, 80.0, 42.0, 310.0, 1800.0, 55.0],
    "velocity_1h": [1, 2, 8, 1, 15, 1, 12, 2, 1, 3, 14, 1],
    "device_trust": [0.95, 0.88, 0.20, 0.99, 0.10, 0.92, 0.15, 0.85, 0.90, 0.70, 0.08, 0.94],
    "ip_reputation": ["CLEAN", "CLEAN", "SUSPICIOUS", "CLEAN", "MALICIOUS", "CLEAN", "MALICIOUS", "CLEAN", "CLEAN", "SUSPICIOUS", "MALICIOUS", "CLEAN"],
    "country_risk": ["LOW", "LOW", "MEDIUM", "LOW", "HIGH", "LOW", "HIGH", "LOW", "LOW", "MEDIUM", "HIGH", "LOW"],
})

# =====================================================================
# MODE A: UNSUPERVISED (Feature Extraction, Anomaly Z-Scores & Drift)
# =====================================================================
feature_engine = get_feature_engine(domain="fraud")
df_enriched = feature_engine.extract_all(raw_df)

regime_detector = get_regime_detector(domain="fraud")
regime_info = regime_detector.analyze_regime(
    features=df_enriched.iloc[-1].to_dict(),
    history_df=df_enriched,
)
print(f"[Unsupervised] Regime: {regime_info['dominant_regime']} | Gate: {regime_info['actionability_gate']}")

# =====================================================================
# MODE B: SUPERVISED (Exact Boolean Hypercube Minimization + Audit)
# =====================================================================
target = pd.Series([0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0], name="target")

clf = ExactorAcceleratorClassifier(domain="fraud", fast_path=True)
clf.fit(df_enriched, target)

new_tx = feature_engine.extract_all(pd.DataFrame([{
    "amount": 1850.0,
    "velocity_1h": 14,
    "device_trust": 0.12,
    "ip_reputation": "MALICIOUS",
    "country_risk": "HIGH",
}]))
prediction = clf.predict(new_tx)
explanation = clf.explain(new_tx)

print(f"\n[Supervised] Prediction (is_fraud): {prediction[0]}")
print(f"[Supervised] Exact Boolean Rule: {clf.formula_expr_}")
print(f"[Supervised] Why this decision was made:\n{explanation}")

# =====================================================================
# MODE C: AUTONOMOUS COLD-START (Zero Prior Data -> Live Auto-Distillation)
# =====================================================================
cold_engine = ExactorAccelerator(cold_start=True, auto_evolve_every=5)
live_res = cold_engine.evaluate(new_tx.iloc[0].to_dict(), fast_path=True)
print(f"\n[Cold-Start] Decision: {live_res['decision']} | Route: {live_res['route']}")
print(f"[Cold-Start] Why: {live_res['explicacion_natural']}")
