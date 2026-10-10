"""
Example: Certainty Islands (Islas de Certeza) in Exactor-Jev Enterprise.

Demonstrates how to use the domain-agnostic Certainty Islands framework
to enforce formal mathematical invariants, eliminate hallucinations/noise,
and route edge decisions (Fast-Path vs Oracle Escalation vs Safety Veto).
"""

from __future__ import annotations

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd
from exactor_accelerator import (
    CertaintyIslandsEngine,
    CertaintyIslandDefinition,
    IslandCategory,
    get_certainty_islands_engine,
)


def run_financial_fraud_demo():
    print("=" * 80)
    print("  🏦 1. FINANCIAL / FRAUD DETECTION CERTAINTY ISLANDS DEMO")
    print("=" * 80)

    # Instantiate financial domain engine
    engine = get_certainty_islands_engine(domain="financial", default_threshold=0.75)

    # Inspect active islands
    print("\n[+] Registered Islands in Financial Domain:")
    for isl in engine.list_islands():
        print(f"  • [{isl['island_id']}] {isl['name']} ({isl['category']})")
        print(f"    Invariant: {isl['formal_invariant']}")

    # Test cases
    transactions = [
        {
            "tx_id": "TX-101",
            "amount": 120.0,
            "available_balance": 1500.0,
            "speed_kmh": 40.0,
            "is_sanctioned": False,
            "certainty": 94.0,
            "description": "Normal local grocery purchase"
        },
        {
            "tx_id": "TX-102",
            "amount": 2500.0,
            "available_balance": 500.0,
            "speed_kmh": 20.0,
            "is_sanctioned": False,
            "certainty": 85.0,
            "description": "Overdraft attempt (exceeds balance)"
        },
        {
            "tx_id": "TX-103",
            "amount": 350.0,
            "available_balance": 10000.0,
            "speed_kmh": 1850.0,  # Impossible physical flight speed
            "is_sanctioned": False,
            "certainty": 90.0,
            "description": "Geo-velocity jump anomaly"
        }
    ]

    print("\n[+] Evaluating Financial Transactions against Certainty Invariants:")
    for tx in transactions:
        res = engine.evaluate(tx)
        print(f"\n▶ Transaction {tx['tx_id']}: '{tx['description']}'")
        print(f"   • Valid Decision : {res.is_valid}")
        print(f"   • Action Routing : ⚡ {res.action_decision}")
        print(f"   • Confidence     : {res.confidence_score * 100:.1f}%")
        print(f"   • Active Islands : {res.active_islands}")
        print(f"   • LaTeX Proof    : {res.formal_proof_latex}")


def run_custom_iot_demo():
    print("\n" + "=" * 80)
    print("  🏭 2. INDUSTRIAL IoT & CRITICAL SYSTEMS CUSTOM ISLANDS DEMO")
    print("=" * 80)

    engine = get_certainty_islands_engine(domain="general")

    # Register custom Invariant: Turbine Pressure & Temperature Envelope
    engine.register_island(CertaintyIslandDefinition(
        island_id="ISLAND-TURBINE-SAFE-ENVELOPE",
        name="Nuclear/Gas Turbine Pressure-Temp Safe Envelope",
        category=IslandCategory.CUSTOM,
        description="Enforces that turbine pressure and core temperature satisfy ideal gas thermodynamics.",
        formal_invariant=r"\mathcal{I}_{\text{Turbine}} \equiv (P \le 18.5\,\text{bar}) \land (T \le 650^{\circ}\text{C}) \land (\frac{P}{T} \le 0.035)",
        predicate=lambda d: (
            d.get("pressure_bar", 0.0) <= 18.5 and
            d.get("temp_c", 0.0) <= 650.0 and
            (d.get("pressure_bar", 0.0) / max(d.get("temp_c", 1.0), 1.0)) <= 0.035
        ),
        is_mandatory_guardrail=True,
        min_confidence=0.99
    ))

    # Test sensor readings
    readings = pd.DataFrame([
        {"sensor_id": "T-1", "pressure_bar": 12.0, "temp_c": 420.0, "probabilistic_certainty": 92.0, "entropy": 0.05},
        {"sensor_id": "T-2", "pressure_bar": 22.4, "temp_c": 710.0, "probabilistic_certainty": 95.0, "entropy": 0.08}, # Critical rupture risk
    ])

    results = engine.batch_evaluate(readings)
    for idx, row in readings.iterrows():
        r = results[idx]
        print(f"\n▶ Turbine Sensor {row['sensor_id']} (P={row['pressure_bar']} bar, T={row['temp_c']} C):")
        print(f"   • Invariant Valid : {r.is_valid}")
        print(f"   • Routing Action  : {r.action_decision}")
        print(f"   • Active Islands  : {r.active_islands}")
        print(f"   • LaTeX Deduction : {r.formal_proof_latex}")


if __name__ == "__main__":
    run_financial_fraud_demo()
    run_custom_iot_demo()
