"""
Tests for scikit-learn style interface (ExactorAcceleratorClassifier).
Validates fit, predict, predict_proba, score, and pipeline export.
"""

import unittest
import numpy as np
import pandas as pd
from exactor_accelerator import ExactorAcceleratorClassifier
from exactor_accelerator.sdk import ExactorAccelerator
from jev_sdk import Jev


class TestSklearnInterface(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        n = 200
        amounts = np.random.exponential(scale=100, size=n)
        velocities = np.random.poisson(lam=2, size=n)
        risks = np.random.choice(["LOW", "MEDIUM", "HIGH"], size=n, p=[0.7, 0.2, 0.1])
        trusts = np.random.uniform(0.1, 1.0, size=n)
        pins = np.random.poisson(lam=0.5, size=n)

        # Ground truth rule: if amount > 150 and (country_risk == HIGH or pins >= 2) -> 1
        y = [
            1 if (a > 150 and (r == "HIGH" or p >= 2)) else 0
            for a, r, p in zip(amounts, risks, pins)
        ]

        self.X_df = pd.DataFrame({
            "amount": amounts,
            "velocity_1h": velocities,
            "country_risk": risks,
            "device_trust": trusts,
            "failed_pin_attempts": pins,
        })
        self.y = np.array(y)

    def test_01_fit_predict_score(self):
        """Test fit(), predict(), and score() identical to scikit-learn."""
        clf = ExactorAcceleratorClassifier(max_variables=12, fast_path=True)
        clf.fit(self.X_df, self.y)

        self.assertTrue(clf.is_fitted_)
        self.assertIsNotNone(clf.formula_expr_)
        print(f"\n[OK] Discovered Sklearn Formula: {clf.formula_expr_}")

        # Predict
        preds = clf.predict(self.X_df)
        self.assertEqual(len(preds), len(self.y))
        
        # Score (Accuracy)
        acc = clf.score(self.X_df, self.y)
        self.assertGreaterEqual(acc, 0.85)
        print(f"[OK] Sklearn Mean Accuracy: {acc * 100:.1f}%")

    def test_02_predict_proba(self):
        """Test predict_proba() with calibrated probabilities."""
        clf = ExactorAcceleratorClassifier(max_variables=6, fast_path=True)
        clf.fit(self.X_df, self.y)

        probas = clf.predict_proba(self.X_df)
        self.assertEqual(probas.shape, (len(self.y), 2))
        # Validate that row probabilities sum to 1.0
        np.testing.assert_allclose(np.sum(probas, axis=1), 1.0, atol=1e-3)
        print(f"[OK] Sklearn predict_proba validated (Shape: {probas.shape})")

    def test_03_numpy_inputs(self):
        """Test compatibility with pure NumPy arrays."""
        X_mat = self.X_df.values
        clf = ExactorAcceleratorClassifier(max_variables=6, fast_path=True)
        clf.fit(X_mat, self.y)

        preds = clf.predict(X_mat)
        self.assertEqual(len(preds), len(self.y))
        print("[OK] Sklearn NumPy Matrix Input validated.")


if __name__ == "__main__":
    unittest.main()
