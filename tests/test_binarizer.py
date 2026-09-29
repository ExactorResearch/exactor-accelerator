import unittest
import pandas as pd
import numpy as np
from exactor_accelerator.ingestion.binarizer import AdaptiveBinarizer, Proposition
from exactor_accelerator.ingestion.loader import DataLoader


class TestAdaptiveBinarizer(unittest.TestCase):

    def test_binarization_hypercube_dimension(self):
        df = DataLoader.generate_fintech_fraud_sample(n_records=100, seed=42)
        binarizer = AdaptiveBinarizer(max_variables=8)
        binarizer.fit(df, target_col="is_fraud")

        self.assertTrue(binarizer.is_fitted)
        self.assertLessEqual(len(binarizer.variables), 8)
        self.assertGreaterEqual(len(binarizer.variables), 4)

        result = binarizer.transform(df)
        self.assertEqual(result.get_hypercube_dimension(), len(binarizer.variables))
        self.assertEqual(len(result.bit_matrix), 100)
        self.assertTrue(all(0 <= m < (1 << len(binarizer.variables)) for m in result.minterms_on))

    def test_single_record_transform(self):
        df = DataLoader.generate_fintech_fraud_sample(n_records=50, seed=12)
        binarizer = AdaptiveBinarizer(max_variables=6)
        binarizer.fit(df, target_col="is_fraud")

        record = {
            "amount": 3500.0,
            "velocity_1h": 6,
            "country_risk": "HIGH",
            "device_trust": 0.15,
            "failed_pin_attempts": 3,
            "is_new_device": 1,
        }

        minterm_val, prop_dict = binarizer.transform_single(record)
        self.assertIsInstance(minterm_val, int)
        self.assertGreaterEqual(minterm_val, 0)
        self.assertEqual(len(prop_dict), len(binarizer.variables))
        for v in binarizer.variables:
            self.assertIn(prop_dict[v], (0, 1))


if __name__ == "__main__":
    unittest.main()
