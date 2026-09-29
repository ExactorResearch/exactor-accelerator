import unittest
from exactor_accelerator.core.hypercube import ExactorHypercubeReducer
from exactor_accelerator.adapter.translator import ExactorToJevTranslator
from exactor_accelerator.adapter.jev_schema import JevPayload


class TestJevAdapter(unittest.TestCase):

    def test_translation_to_jev_payload(self):
        variables = ["amount_high", "velocity_high", "country_risky"]
        minterms = [6, 7]  # 110 and 111 => amount_high & velocity_high & (-)

        reducer = ExactorHypercubeReducer(variables)
        result = reducer.minimize(minterms)

        translator = ExactorToJevTranslator()
        state_data = {"amount": 2500, "velocity": 4, "country": "HIGH"}

        payload = translator.build_payload(state_data, result, include_all_questions=True)
        p_dict = payload.to_dict()

        # Validate TypeSafe AI Jev structure requirements
        self.assertEqual(p_dict["model"], "jev-latest")
        self.assertIn("state", p_dict)
        self.assertIn("questions", p_dict)
        self.assertIn("criterio_logico", p_dict["questions"])

        criterio = p_dict["questions"]["criterio_logico"]
        self.assertEqual(criterio["type"], "noul")
        self.assertTrue(criterio["instructions"].startswith("Is the boolean condition"))

        self.assertIn("accion_recomendada", p_dict["questions"])
        self.assertEqual(p_dict["questions"]["accion_recomendada"]["type"], "choice")


if __name__ == "__main__":
    unittest.main()
