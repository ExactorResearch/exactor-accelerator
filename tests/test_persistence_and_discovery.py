"""
Test Suite for Model Serialization (.ea / .ej), Persistence, and Semantic Auto-Discovery.
"""

import unittest
import os
import pandas as pd
import numpy as np

from exactor_accelerator import (
    ExactorAcceleratorClassifier,
    save_model,
    load_model,
    SemanticPropositionDiscovery,
)
from exactor_accelerator.sdk import ExactorAccelerator


class TestPersistenceAndSemanticDiscovery(unittest.TestCase):

    def setUp(self):
        self.tmp_model_path = "test_model_artifact.ea"
        self.df = pd.DataFrame([
            {"amount": 1200, "tenure": 2, "text": "Terrible service, I demand an immediate refund!", "fraud": 1},
            {"amount": 2500, "tenure": 1, "text": "My account was hacked and password changed!", "fraud": 1},
            {"amount": 35,   "tenure": 24, "text": "Thank you very much for your great assistance.", "fraud": 0},
            {"amount": 80,   "tenure": 12, "text": "Inquiry regarding invoice due date.", "fraud": 0},
        ] * 10)

    def tearDown(self):
        if os.path.exists(self.tmp_model_path):
            os.remove(self.tmp_model_path)
        if os.path.exists("test_model_artifact.ej"):
            os.remove("test_model_artifact.ej")

    def test_01_save_and_load_exactor_accelerator_sdk(self):
        """Tests compact serialization and reloading of ExactorAccelerator SDK."""
        engine = ExactorAccelerator(use_cloud_exactor=False)
        engine.fit(self.df, target_col="fraud", max_variables=8)

        # Save model
        path = save_model(engine, self.tmp_model_path, metadata={"author": "TestDev", "version": "1.0.0"})
        self.assertTrue(os.path.exists(path))
        print(f"\n[OK] ExactorAccelerator model saved at: {path} ({os.path.getsize(path)} bytes)")

        # Load model into clean memory
        loaded_engine = load_model(path)
        self.assertIsNotNone(loaded_engine.runtime.current_rule)

        # Evaluate prediction with original and reloaded model
        test_event = {"amount": 1200, "tenure": 2, "text": "Terrible service, I demand an immediate refund!"}
        orig_res = engine.evaluate(test_event, fast_path=True)
        loaded_res = loaded_engine.evaluate(test_event, fast_path=True)

        self.assertEqual(orig_res["decision"], loaded_res["decision"])
        self.assertEqual(orig_res["exact_boolean_evaluation"], loaded_res["exact_boolean_evaluation"])
        print(f"[OK] Reloaded model inference successful ({loaded_res['decision']}, {loaded_res['latency_ms']} ms).")

    def test_02_save_and_load_sklearn_classifier(self):
        """Tests serialization and reloading of ExactorAcceleratorClassifier."""
        clf = ExactorAcceleratorClassifier(max_variables=8, fast_path=True)
        X = self.df[["amount", "tenure", "text"]]
        y = self.df["fraud"].values
        clf.fit(X, y)

        path = save_model(clf, self.tmp_model_path)
        loaded_clf = load_model(path)

        preds = loaded_clf.predict(X.iloc[:2])
        self.assertEqual(len(preds), 2)
        print(f"[OK] Reloaded Sklearn Classifier predicting: {preds}")

    def test_03_semantic_proposition_discovery(self):
        """Tests semantic auto-discovery engine (Zero-Regex)."""
        discovery = SemanticPropositionDiscovery()
        texts = [
            "Urgent cancellation due to duplicate charge and unauthorized card use!",
            "Balance refund requested due to server error on page.",
            "Thank you so much for the quick and helpful response.",
            "Inquiry regarding payment plans and installment options.",
        ]

        propositions = discovery.discover_from_corpus(texts, max_propositions=4, domain_hint="fintech operations")
        self.assertGreaterEqual(len(propositions), 1)
        print(f"[OK] Auto-Discovered Semantic Propositions: {list(propositions.keys())}")

        # Extract features
        sample_feats = discovery.extract_features("I demand cancellation of my plan right now")
        self.assertIsInstance(sample_feats, dict)
        print(f"[OK] Extracted features: {sample_feats}")


if __name__ == "__main__":
    unittest.main()
