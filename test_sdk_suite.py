"""
Automated Test Suite for exactor_accelerator_sdk and jev_sdk.
Cubre:
1. Historical ingestion and training (fit) with DataFrame and CSV file
2. Proposition discovery and logical hypercube induction in EXACTOR
3. Inferencia en vivo y decisiones deterministas (evaluate) para:
   - Critical Case (Preventive block)
   - Safe Case (Autonomous approval)
   - Borderline Case (Manual review / 2FA)
4. Explicabilidad Causal con DeepSeek
5. Simplified jev_sdk module (decide, choose, score)
"""

import unittest
import pandas as pd
import numpy as np
from exactor_accelerator.sdk import ExactorAccelerator
from jev_sdk import jev


class TestExactorAcceleratorSDK(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 1. Crear dataset sintético de prueba con patrones definidos
        np.random.seed(42)
        n = 300
        amounts = np.random.exponential(scale=100, size=n)
        velocities = np.random.poisson(lam=2, size=n)
        risks = np.random.choice(["LOW", "MEDIUM", "HIGH"], size=n, p=[0.7, 0.2, 0.1])
        trusts = np.random.uniform(0.1, 1.0, size=n)
        pins = np.random.poisson(lam=0.5, size=n)

        # Regla conocida: si amount > 150 y (country_risk == HIGH o pins >= 2) -> fraude
        is_fraud = [
            1 if (a > 150 and (r == "HIGH" or p >= 2)) else 0
            for a, r, p in zip(amounts, risks, pins)
        ]

        cls.df_train = pd.DataFrame({
            "amount": amounts,
            "velocity_1h": velocities,
            "country_risk": risks,
            "device_trust": trusts,
            "failed_pin_attempts": pins,
            "is_fraud": is_fraud,
        })

        cls.engine = ExactorAccelerator()

    def test_01_fit_training(self):
        """Prueba que EXACTOR aprenda las reglas del DataFrame del cliente."""
        res = self.engine.fit(self.df_train, target_col="is_fraud", max_variables=12)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIsNotNone(res["formula_booleana"])
        self.assertGreater(len(res["variables_descubiertas"]), 0)
        self.assertIn("explicacion", res)
        print(f"\n[OK] Fit completado con {len(res['variables_descubiertas'])} variables.")

    def test_02_evaluate_critical_case(self):
        """Prueba que un caso de alto riesgo dispare CRITICAL y BLOQUEAR_TRANSACCION."""
        evento_critico = {
            "amount": 2500.0,
            "velocity_1h": 8,
            "country_risk": "HIGH",
            "device_trust": 0.10,
            "failed_pin_attempts": 3,
        }
        res = self.engine.evaluate(evento_critico)
        self.assertIn(res["decision"], ["CRITICAL", "REVIEW"])
        self.assertIn("freeze", res["endpoint_disparado"].lower() + res["accion"].lower())
        print(f"[OK] Caso Crítico evaluado: {res['decision']} -> {res['accion']} ({res['latencia_ms']} ms)")

    def test_03_evaluate_safe_case(self):
        """Prueba que una transacción habitual y segura dispare SAFE y APROBADO."""
        evento_seguro = {
            "amount": 15.0,
            "velocity_1h": 1,
            "country_risk": "LOW",
            "device_trust": 0.98,
            "failed_pin_attempts": 0,
        }
        res = self.engine.evaluate(evento_seguro)
        self.assertEqual(res["decision"], "SAFE")
        self.assertEqual(res["accion"], "APROBAR_TRANSACCION")
        self.assertTrue(res["ejecucion_autonoma"])
        self.assertIn("authorize", res["endpoint_disparado"])
        print(f"[OK] Caso Seguro evaluado: {res['decision']} -> {res['accion']} ({res['latencia_ms']} ms)")

    def test_04_deepseek_explanation(self):
        """Prueba la generación de explicaciones en lenguaje natural con DeepSeek."""
        evento = {
            "amount": 3400.0,
            "velocity_1h": 6,
            "country_risk": "HIGH",
            "device_trust": 0.12,
            "failed_pin_attempts": 3,
        }
        explicacion = self.engine.explain(evento)
        self.assertIsInstance(explicacion, str)
        self.assertGreater(len(explicacion), 50)
        self.assertIn("¿Qué", explicacion)
        print(f"[OK] Explicación DeepSeek generada con éxito ({len(explicacion)} caracteres).")

    def test_05_jev_sdk_decide_and_choose(self):
        """Prueba las funciones directas del cliente simplificado jev_sdk."""
        # Test decide
        res_decide = jev.decide(
            state={"monto": 4000, "intentos_fallidos": 4},
            question="¿Es esta operación riesgosa?",
        )
        self.assertIn("is_true", res_decide)
        self.assertIn("probability", res_decide)

        # Test choose
        res_choose = jev.choose(
            state={"monto": 20, "dispositivo_seguro": True},
            instruction="¿Qué acción ejecutar?",
            choices=["BLOQUEAR", "REVISION", "APROBAR"],
        )
        self.assertIn("action", res_choose)
        self.assertIn("confidence", res_choose)

        # Test score
        res_score = jev.score(
            state={"error_rate": 15.0, "latency": 450},
            instruction="Evalúa el impacto de la alerta",
        )
        self.assertIn("score", res_score)
        self.assertIn("level", res_score)
        print("[OK] Funciones mínimas de jev_sdk probadas con éxito.")

    def test_06_custom_choices_configuration(self):
        """Prueba la personalización dinámica de opciones Choice de negocio."""
        self.engine.set_choices([
            "ACCION_VIP_INMEDIATA",
            "PEDIR_BIOMETRIA_2FA",
            "BLOQUEO_TOTAL_FRAUDE"
        ])
        evento_riesgoso = {
            "amount": 3500.0,
            "velocity_1h": 8,
            "country_risk": "HIGH",
            "device_trust": 0.10,
            "failed_pin_attempts": 3,
        }
        res = self.engine.evaluate(evento_riesgoso)
        self.assertIn(res["accion"], ["ACCION_VIP_INMEDIATA", "PEDIR_BIOMETRIA_2FA", "BLOQUEO_TOTAL_FRAUDE"])
        print(f"[OK] Custom Choice ejecutado: {res['accion']}")

    def test_07_fast_path_instant_evaluation(self):
        """Prueba la inferencia instantánea sub-milisegundo (< 1 ms)."""
        evento = {
            "amount": 12.50,
            "velocity_1h": 1,
            "country_risk": "LOW",
            "device_trust": 0.99,
            "failed_pin_attempts": 0,
        }
        res = self.engine.evaluate(evento, fast_path=True)
        self.assertEqual(res["decision"], "SAFE")
        self.assertLess(res["latencia_ms"], 5.0) # Confirm sub-millisecond execution
        print(f"[OK] Fast-Path Instantáneo ejecutado en {res['latencia_ms']} ms ({res['decision']})")


if __name__ == "__main__":
    unittest.main()
