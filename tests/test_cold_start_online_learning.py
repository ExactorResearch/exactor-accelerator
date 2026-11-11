"""
Test Suite for Cold Start Auto-Learning and Progressive Distillation in ExactorAccelerator.
Prueba:
 1. Cold initialization without prior training dataset (cold_start=True).
 2. Hot inference through JEV Oracle during the first N interactions.
 3. Automatic boolean deduction via EXACTOR after exceeding auto_evolve_every threshold.
 4. Transition to FAST_PATH_LOCAL (< 0.1 ms) and token savings metric (token_savings_pct).
 5. Live feedback recording (record_feedback) and hot rule patching.
 6. Persistencia transparente (.ej) de modelos auto-destilados.
"""

import unittest
import os
import time
import numpy as np
import pandas as pd

from exactor_accelerator import ExactorAccelerator, save_model, load_model


class TestColdStartOnlineLearning(unittest.TestCase):

    def setUp(self):
        self.tmp_db_path = "test_cold_start_memory.db"
        self.tmp_model_path = "test_cold_start_model.ej"
        for p in [self.tmp_db_path, self.tmp_model_path]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

    def tearDown(self):
        for p in [self.tmp_db_path, self.tmp_model_path]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

    def test_01_cold_start_without_fit(self):
        """Valida que ExactorAccelerator puede instanciarse y evaluar eventos sin fit() previo."""
        engine = ExactorAccelerator(
            cold_start=True,
            auto_evolve_every=10,
            fast_path_threshold=0.80,
            db_path=self.tmp_db_path,
        )

        self.assertTrue(engine.cold_start)
        self.assertTrue(engine.runtime.is_initialized)
        self.assertIsNone(engine.runtime.current_rule)

        # Evaluar un evento en frío
        event = {"monto": 500, "intentos_fallidos": 1, "texto": "Consulta de saldo normal"}
        res = engine.evaluate(event, fast_path=True)

        self.assertIn("decision", res)
        self.assertIn("query_id", res)
        self.assertEqual(res["route"], "JEV_ORACLE")
        self.assertEqual(res["ahorro_tokens_pct"], 0.0)
        self.assertIsNone(res["formula_activa"])
        print(f"\n[OK] Cold Start Inicial: Ruta={res['route']}, Decisión={res['decision']}, Latencia={res['latencia_ms']} ms")

    def test_02_progressive_auto_distillation_and_token_savings(self):
        """Valida la auto-deducción booleana tras N eventos y la conmutación a FAST_PATH_LOCAL."""
        engine = ExactorAccelerator(
            cold_start=True,
            auto_evolve_every=10,
            fast_path_threshold=0.80,
            db_path=self.tmp_db_path,
        )

        # 1. Enviar 10 eventos para alimentar el Ledger
        high_risk_events = [
            {"monto": 4500, "intentos_fallidos": 4, "texto": "Alerta de fraude y transferencia urgente no autorizada"},
            {"monto": 5200, "intentos_fallidos": 5, "texto": "Cuenta hackeada y retiro sospechoso"},
            {"monto": 3900, "intentos_fallidos": 3, "texto": "Robo de clave y vaciado de fondos"},
        ]
        low_risk_events = [
            {"monto": 50, "intentos_fallidos": 0, "texto": "Consulta de saldo por cajero"},
            {"monto": 80, "intentos_fallidos": 0, "texto": "Pago de servicios en línea"},
            {"monto": 120, "intentos_fallidos": 0, "texto": "Transferencia rutinaria entre cuentas propias"},
        ]

        # Intercalar 10 eventos (5 altos, 5 bajos)
        for i in range(10):
            ev = high_risk_events[i % len(high_risk_events)] if i % 2 == 0 else low_risk_events[i % len(low_risk_events)]
            res = engine.evaluate(ev, fast_path=True)
            self.assertEqual(res["route"], "JEV_ORACLE")

        # Al décimo evento, debe haberse disparado la auto-deducción booleana
        stats = engine.get_stats()
        self.assertIsNotNone(stats["formula_activa"])
        self.assertGreater(stats["proposiciones_activas"], 0)
        self.assertEqual(stats["rule_version"], 2)
        print(f"\n[OK] Auto-Deducción Booleana alcanzada en evento #10!")
        print(f"     Fórmula Booleana compilada: {stats['formula_activa']}")
        print(f"     Variables descubiertas: {stats['variables']}")

        # 2. Enviar siguientes eventos: deben resolver por FAST_PATH_LOCAL
        ev_test_1 = {"monto": 5000, "intentos_fallidos": 4, "texto": "Alerta de fraude y transferencia urgente"}
        res_post = engine.evaluate(ev_test_1, fast_path=False)
        self.assertEqual(res_post["route"], "FAST_PATH_LOCAL")
        self.assertIsNotNone(res_post["formula_activa"])
        self.assertGreater(res_post["ahorro_tokens_pct"], 0.0)
        print(f"[OK] Evento #11 enrutado vía: {res_post['route']} (Ahorro tokens: {res_post['ahorro_tokens_pct']}%)")

        # Enviar 5 eventos más para medir la curva de ahorro
        for i in range(5):
            ev = low_risk_events[i % len(low_risk_events)]
            res_iter = engine.evaluate(ev, fast_path=False)

        final_stats = engine.get_stats()
        print(f"[OK] Telemetría Final Cold Start:")
        print(f"     Total Queries: {final_stats['total_queries']}")
        print(f"     Consultas Locales (Fast-Path): {final_stats['local_queries']}")
        print(f"     Consultas API Jev: {final_stats['jev_queries']}")
        print(f"     Ahorro de Tokens Jev: {final_stats['ahorro_tokens_pct']}%")
        self.assertGreaterEqual(final_stats["ahorro_tokens_pct"], 35.0)

    def test_03_record_ground_truth_feedback(self):
        """Valida que el feedback empírico (record_feedback) actualiza el ledger."""
        engine = ExactorAccelerator(
            cold_start=True,
            auto_evolve_every=5,
            db_path=self.tmp_db_path,
        )

        res = engine.evaluate({"monto": 200, "intentos_fallidos": 0, "texto": "Operación normal"}, fast_path=True)
        q_id = res["query_id"]

        # Registrar feedback real (ej. se confirmó que fue fraude a posteriori)
        engine.record_feedback(query_id=q_id, label=1)

        # Verificar en el ledger que el feedback_label está registrado
        records = engine.runtime.ledger.get_sliding_window_records(window_size=1)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["feedback_label"], 1)
        print(f"\n[OK] Feedback Empírico registrado exitosamente para Query ID: {q_id}")

    def test_04_save_and_reload_cold_started_model(self):
        """Valida que un modelo originado en Cold Start se serializa y recarga (.ej) preservando la regla."""
        engine = ExactorAccelerator(
            cold_start=True,
            auto_evolve_every=6,
            db_path=self.tmp_db_path,
        )

        for i in range(6):
            monto = 5000 if i % 2 == 0 else 50
            intentos = 4 if i % 2 == 0 else 0
            engine.evaluate({"monto": monto, "intentos_fallidos": intentos, "texto": "Transacción de prueba"}, fast_path=True)

        original_stats = engine.get_stats()
        formula_orig = original_stats["formula_activa"]
        self.assertIsNotNone(formula_orig)

        # Guardar modelo
        saved_path = save_model(engine, self.tmp_model_path)
        self.assertTrue(os.path.exists(saved_path))

        # Recargar modelo
        loaded_engine = load_model(saved_path)
        loaded_stats = loaded_engine.get_stats()

        self.assertEqual(loaded_stats["formula_activa"], formula_orig)
        self.assertEqual(loaded_stats["rule_version"], original_stats["rule_version"])

        # Evaluar con el modelo recargado
        res_loaded = loaded_engine.evaluate({"monto": 5000, "intentos_fallidos": 4, "texto": "Transacción de prueba"})
        self.assertEqual(res_loaded["route"], "FAST_PATH_LOCAL")
        print(f"\n[OK] Modelo Cold Start guardado y recargado con éxito:")
        print(f"     Fórmula Preservada: {res_loaded['formula_activa']}")


if __name__ == "__main__":
    unittest.main()
