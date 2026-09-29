import unittest
import os
import tempfile
from exactor_accelerator.engine.runtime import HybridRuntime
from exactor_accelerator.ingestion.loader import DataLoader


class TestLiveMemoryAndRuntime(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_memory.db")
        self.runtime = HybridRuntime(db_path=self.db_path, default_threshold=0.80)

    def tearDown(self):
        import gc
        gc.collect()
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    def test_full_phase_a_and_phase_b_flow(self):
        # 1. Phase A Onboarding
        df = DataLoader.generate_fintech_fraud_sample(n_records=120, seed=77)
        onboard_res = self.runtime.phase_a_onboard(df, target_col="is_fraud", max_variables=8)

        self.assertEqual(onboard_res["status"], "SUCCESS")
        self.assertGreater(onboard_res["rule_version"], 1)
        self.assertIsNotNone(self.runtime.current_rule)

        # 2. Phase B Live Query (High Fraud probability event)
        fraud_event = {
            "amount": 3800.0,
            "velocity_1h": 7,
            "country_risk": "HIGH",
            "device_trust": 0.10,
            "failed_pin_attempts": 3,
            "is_new_device": 1,
        }

        query_res = self.runtime.phase_b_query(fraud_event, confidence_threshold=0.80)
        self.assertIsInstance(query_res.query_id, str)
        self.assertGreaterEqual(query_res.criterio_logico_prob, 0.0)
        self.assertLessEqual(query_res.criterio_logico_prob, 1.0)
        self.assertIn(query_res.chosen_action, ["EJECUCION_AUTONOMA", "REVISION_HUMANA", "DESCARTAR", "BLOQUEAR_TRANSACCION", "APROBAR_TRANSACCION", "AUTONOMOUS_EXECUTION", "HUMAN_REVIEW", "DISMISS", "BLOCK_TRANSACTION", "APPROVE_TRANSACTION"])

        # Check ledger recording in SQLite WAL
        entries = self.runtime.ledger.get_recent_entries(limit=10)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["query_id"], query_res.query_id)

        # 3. Simulate 10 live queries
        for i in range(10):
            sample_evt = {
                "amount": 100.0 * (i + 1),
                "velocity_1h": i % 4,
                "country_risk": "MEDIUM" if i % 2 == 0 else "LOW",
                "device_trust": 0.8,
                "failed_pin_attempts": 0,
                "is_new_device": 0,
            }
            self.runtime.phase_b_query(sample_evt)

        all_entries = self.runtime.ledger.get_recent_entries(limit=50)
        self.assertEqual(len(all_entries), 11)

        # 4. Differential hot update
        update_res = self.runtime.trigger_differential_update(window_size=10)
        self.assertIn(update_res["status"], ["UPDATED", "NO_RECORDS"])
        if update_res["status"] == "UPDATED":
            self.assertGreater(update_res["rule_version"], onboard_res["rule_version"])


if __name__ == "__main__":
    unittest.main()
