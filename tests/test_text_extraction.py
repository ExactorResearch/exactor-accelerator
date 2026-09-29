import unittest
import pandas as pd
from exactor_accelerator.ingestion.text_extractor import TextFeatureExtractor
from exactor_accelerator.ingestion.binarizer import AdaptiveBinarizer


class TestUnstructuredTextExtraction(unittest.TestCase):
    def test_text_feature_extractor(self):
        angry_msg = (
            "I was charged twice for the subscription this month on my credit card and "
            "nobody answers my emails. This is a scam, cancel my account and refund "
            "my money immediately or I will take legal action with consumer protection."
        )
        feats = TextFeatureExtractor.extract_from_text(angry_msg)
        self.assertEqual(feats["text_has_cancellation_intent"], 1)
        self.assertEqual(feats["text_has_billing_payment_issue"], 1)
        self.assertEqual(feats["text_has_urgency_critical"], 1)
        self.assertEqual(feats["text_has_frustration_anger"], 1)
        self.assertEqual(feats["text_is_long"], 1)

        friendly_msg = (
            "Hello, good morning. Could you tell me what payment methods are available "
            "and what your telephone support hours are? Thank you very much for your help."
        )
        feats2 = TextFeatureExtractor.extract_from_text(friendly_msg)
        self.assertEqual(feats2["text_has_cancellation_intent"], 0)
        self.assertEqual(feats2["text_has_gratitude_positive"], 1)
        self.assertEqual(feats2["text_has_frustration_anger"], 0)

    def test_binarizer_on_text_dataframe(self):
        df = pd.DataFrame([
            {"user_message": "I want to cancel the service right now, this is a scam!", "target": 1},
            {"user_message": "Error 500 on server, the website is constantly down and crashing.", "target": 1},
            {"user_message": "Thank you so much for the assistance, excellent support.", "target": 0},
            {"user_message": "Hello, what contact channels are available?", "target": 0},
        ])

        binarizer = AdaptiveBinarizer(max_variables=8)
        binarizer.fit(df, target_col="target")
        res = binarizer.transform(df)

        self.assertGreater(len(res.variables), 0)
        self.assertEqual(res.bit_matrix.shape[0], 4)

        # Verify single state transformation from free-form text
        minterm, prop_map = binarizer.transform_single({
            "user_message": "Urgent, the application crashes and returns an error immediately!"
        })
        self.assertIsInstance(minterm, int)
        self.assertIsInstance(prop_map, dict)


if __name__ == "__main__":
    unittest.main()
