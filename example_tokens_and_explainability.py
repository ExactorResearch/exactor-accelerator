"""
COMPLETE EXAMPLE: CONFIGURATION OF TOKENS AND CAUSAL AUDIT EXPLAINABILITY (DEEPSEEK)

This script demonstrates:
1. Explicit configuration of tokens (EXACTOR Core, TypeSafe JEV, DeepSeek).
2. Training on EXACTOR engine (Phase A).
3. Contextual decision-making with JEV (Phase B).
4. Generating 3 levels of Causal Explainability:
   - Level 1: Exact Boolean Formula and Minterm (Strict mathematical audit).
   - Level 2: Proposition Breakdown and RLCD Certainty (Technical traceability).
   - Level 3: Natural Language Explanation with DeepSeek (For customer / regulator / legal).
"""

import time
import pandas as pd
from exactor_accelerator import ExactorAcceleratorClassifier
from exactor_accelerator.sdk import ExactorAccelerator


def main():
    print("=" * 85)
    print("EXACTOR ACCELERATOR: COMPLETE EXAMPLE WITH ALL TOKENS AND CAUSAL EXPLAINABILITY")
    print("=" * 85)

    # =========================================================================
    # 1. DEFINITION OF TOKENS AND CREDENTIALS
    # =========================================================================
    EXACTOR_TOKEN    = "exactor_token_live_production_998877"
    JEV_TOKEN        = "mock_jev_api_key_demo_001122"
    DEEPSEEK_API_KEY = "sk-deepseek-audit-causal-ai-live-key"

    print("\n[STEP 1] Configuring credentials for all 3 engines:")
    print(f" -> EXACTOR Cloud API:  https://exactor.tech (Token: {EXACTOR_TOKEN[:15]}...)")
    print(f" -> TypeSafe JEV API:   https://api.typesafe.ai/v1 (Token: {JEV_TOKEN[:20]}...)")
    print(f" -> DeepSeek Explainer: https://api.deepseek.com/v1 (Key: {DEEPSEEK_API_KEY[:15]}...)")

    # =========================================================================
    # 2. INITIALIZING THE ENGINE WITH TOKENS
    # =========================================================================
    engine = ExactorAccelerator(
        exactor_token=EXACTOR_TOKEN,
        use_cloud_exactor=False,               # True to connect to exactor.tech or False for local engine
        exactor_base_url="https://exactor.tech",
        jev_token=JEV_TOKEN,
        deepseek_api_key=DEEPSEEK_API_KEY,
        default_threshold=0.80,
        db_path="memory_ledger.db"
    )

    # Business action catalog (Choice)
    engine.set_choices({
        "TOTAL_BLOCK_FRAUD": "Flagrant violation of financial security rules",
        "REQUEST_BIOMETRIC_2FA": "Borderline transaction or contextual uncertainty",
        "DIRECT_APPROVAL": "Standard habitual transaction without risk signs",
    })

    # =========================================================================
    # 3. TRAINING / LOGICAL EXTRACTION (PHASE A)
    # =========================================================================
    print("\n[STEP 2] Training logic engine on historical transactions:")
    
    historical_data = pd.DataFrame([
        {"amount": 3200, "pin_attempts": 3, "country": "HIGH", "is_new_device": 1, "is_fraud": 1},
        {"amount": 4500, "pin_attempts": 2, "country": "HIGH", "is_new_device": 1, "is_fraud": 1},
        {"amount": 120,  "pin_attempts": 0, "country": "LOW",  "is_new_device": 0, "is_fraud": 0},
        {"amount": 45,   "pin_attempts": 0, "country": "LOW",  "is_new_device": 0, "is_fraud": 0},
        {"amount": 950,  "pin_attempts": 1, "country": "MED",  "is_new_device": 0, "is_fraud": 0},
    ] * 10)

    discovery_result = engine.fit(
        data=historical_data,
        target_col="is_fraud",
        max_variables=8
    )

    print(f" -> Rule Status: {discovery_result['status']}")
    print(f" -> Extracted Boolean Formula:\n    {discovery_result['boolean_formula']}")
    print(f" -> Semantic Description:\n    {discovery_result['explanation']}")

    # =========================================================================
    # 4. REAL-TIME INFERENCE AND 3-LEVEL CAUSAL EXPLAINABILITY (PHASE B)
    # =========================================================================
    print("\n[STEP 3] Evaluating incoming live event:")

    live_transaction = {
        "amount": 3800.0,
        "pin_attempts": 3,
        "country": "HIGH",
        "is_new_device": 1,
    }

    t0 = time.perf_counter()
    eval_res = engine.evaluate(live_transaction, fast_path=False)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    print(f"\n >>> DECISION EXECUTED IN {elapsed_ms:.1f} ms:")
    print(f"   * Status:           {eval_res['decision']}")
    print(f"   * Action:           {eval_res['action']}")
    print(f"   * Certainty:        {eval_res['probabilistic_certainty']}%")
    print(f"   * Endpoint:         {eval_res['triggered_endpoint']}")

    # LEVEL 1 & 2 AUDIT
    print("\n --- LEVEL 1 & 2: MATHEMATICAL & BOOLEAN AUDIT (EXACTOR) ---")
    print(f"   * Hypercube Evaluation:  {eval_res['exact_boolean_evaluation']} (1 = MATCH, 0 = REJECT)")
    print(f"   * Active Boolean Rule:   {eval_res['active_formula']}")

    # LEVEL 3 AUDIT (DEEPSEEK NATURAL LANGUAGE)
    print("\n --- LEVEL 3: REGULATORY EXPLAINABILITY (DEEPSEEK) ---")
    audit_explanation = engine.explain(live_transaction)
    print(f"Explanation generated by {audit_explanation['model']} in {audit_explanation['latency_ms']} ms:\n")
    print(audit_explanation["explanation"])

    print("\n" + "=" * 85)
    print("END-TO-END PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 85)


if __name__ == "__main__":
    main()
