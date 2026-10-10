"""
Unit and Integration Tests for Certainty Islands Engine in Exactor-Jev.
"""

import unittest
import math
import numpy as np
import pandas as pd

from exactor_accelerator import (
    CertaintyIslandsEngine,
    CertaintyIslandDefinition,
    IslandCategory,
    IslandEvaluationResult,
    get_certainty_islands_engine,
)


class TestCertaintyIslands(unittest.TestCase):
    """Test suite for domain-agnostic Certainty Islands."""

    def test_general_engine_evaluation(self):
        engine = get_certainty_islands_engine(domain="general")
        
        # Valid state with low entropy & high conviction
        sample_valid = {
            "entropy": 0.12,
            "entropy_threshold": 0.50,
            "probabilistic_certainty": 88.5,
            "latency_ms": 0.04
        }
        res = engine.evaluate(sample_valid)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.action_decision, "FASTPATH_EXECUTE")
        self.assertIn("ISLAND-STATE-CONSISTENCY", res.active_islands)
        self.assertIn("ISLAND-LOW-ENTROPY", res.active_islands)
        self.assertIn("ISLAND-HIGH-CONVICTION", res.active_islands)
        self.assertIn(r"\mathbf{CertaintyProof}", res.formal_proof_latex)

    def test_mandatory_guardrail_failure(self):
        engine = get_certainty_islands_engine(domain="general")
        
        # Sample with NaN (violates state consistency)
        sample_invalid = {
            "entropy": 0.10,
            "probabilistic_certainty": 95.0,
            "corrupted_feature": float("nan")
        }
        res = engine.evaluate(sample_invalid)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.action_decision, "VETO_REJECT")
        self.assertIn("ISLAND-STATE-CONSISTENCY", res.rejected_islands)

    def test_financial_domain_presets(self):
        engine = get_certainty_islands_engine(domain="financial")
        
        # Safe transaction
        tx_safe = {
            "amount": 250.0,
            "available_balance": 1000.0,
            "speed_kmh": 45.0,
            "is_sanctioned": False,
            "certainty": 92.0
        }
        res_safe = engine.evaluate(tx_safe)
        self.assertTrue(res_safe.is_valid)
        self.assertEqual(res_safe.action_decision, "FASTPATH_EXECUTE")
        self.assertIn("ISLAND-FIN-SOLVENCY-INTEGRITY", res_safe.active_islands)
        self.assertIn("ISLAND-FIN-SANCTIONS-CLEARANCE", res_safe.active_islands)

        # Sanctioned entity transaction
        tx_sanctioned = {
            "amount": 100.0,
            "available_balance": 5000.0,
            "speed_kmh": 0.0,
            "is_sanctioned": True
        }
        res_sanctioned = engine.evaluate(tx_sanctioned)
        self.assertFalse(res_sanctioned.is_valid)
        self.assertEqual(res_sanctioned.action_decision, "VETO_REJECT")

    def test_medical_domain_presets(self):
        engine = get_certainty_islands_engine(domain="medical")
        
        # Normal clinical sample
        patient_normal = {
            "heart_rate": 72,
            "spo2": 98,
            "has_contraindication": False,
            "certainty": 88.0
        }
        res = engine.evaluate(patient_normal)
        self.assertTrue(res.is_valid)
        self.assertIn("ISLAND-MED-PHYSIOLOGY-GUARD", res.active_islands)

        # Lethal / invalid sensor value
        patient_abnormal = {
            "heart_rate": 500,  # Physically impossible
            "spo2": 98,
            "has_contraindication": False
        }
        res_abn = engine.evaluate(patient_abnormal)
        self.assertFalse(res_abn.is_valid)
        self.assertEqual(res_abn.action_decision, "VETO_REJECT")

    def test_custom_dynamic_island(self):
        engine = get_certainty_islands_engine(domain="general")
        
        # Register custom IoT temperature sentry
        engine.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-IOT-THERMAL-EQUILIBRIUM",
            name="Turbine Thermal Equilibrium Invariant",
            category=IslandCategory.CUSTOM,
            description="Turbine temperature must remain within safe operational bounds.",
            formal_invariant=r"\mathcal{I}_{\text{Thermal}} \equiv T_{\text{turbine}} \in [45^{\circ}\text{C}, 120^{\circ}\text{C}]",
            predicate=lambda d: 45.0 <= d.get("temp_c", 0.0) <= 120.0,
            is_mandatory_guardrail=True,
            min_confidence=0.98
        ))

        # Test within bounds
        sample_ok = {"temp_c": 78.5, "probabilistic_certainty": 82.0}
        res_ok = engine.evaluate(sample_ok)
        self.assertTrue(res_ok.is_valid)
        self.assertIn("ISLAND-IOT-THERMAL-EQUILIBRIUM", res_ok.active_islands)

        # Test overheating
        sample_overheat = {"temp_c": 145.0, "probabilistic_certainty": 90.0}
        res_overheat = engine.evaluate(sample_overheat)
        self.assertFalse(res_overheat.is_valid)
        self.assertEqual(res_overheat.action_decision, "VETO_REJECT")

    def test_batch_dataframe_evaluation(self):
        engine = get_certainty_islands_engine(domain="financial")
        df = pd.DataFrame([
            {"amount": 50.0, "available_balance": 500.0, "speed_kmh": 20.0, "is_sanctioned": False, "certainty": 85.0},
            {"amount": 900.0, "available_balance": 100.0, "speed_kmh": 10.0, "is_sanctioned": False, "certainty": 80.0}, # Overdraft
            {"amount": 10.0, "available_balance": 1000.0, "speed_kmh": 1200.0, "is_sanctioned": False, "certainty": 90.0}, # Geo-jump
        ])
        results = engine.batch_evaluate(df)
        self.assertEqual(len(results), 3)
        self.assertTrue(results[0].is_valid)
        self.assertFalse(results[1].is_valid) # Solvency failed
        self.assertIn("ISLAND-FIN-VELOCITY-SENTRY", results[2].rejected_islands) # Velocity failed


if __name__ == "__main__":
    unittest.main()
