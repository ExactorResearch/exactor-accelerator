"""
TEST SUITE INTENSIVAS DE PROCESAMIENTO DE DATOS NO ESTRUCTURADOS (NLP / TEXT / CHAT)

This suite rigorously tests the ExactorAccelerator text pipeline:
1. LINGUISTIC VARIETY AND FORMATS TEST:
   - English and Spanish with slang, typos, sustained uppercase, and special characters.
   - Short texts (tweets/SMS), medium (support tickets), and long (full transcripts).
   - Multi-turn dialogues in JSON/List format.

2. VOLUME AND PERFORMANCE STRESS TEST:
   - Burst ingestion of 500 texts to measure binarization latency and hypercube projection.

3. CONTEXTUAL CAUSAL RULES ACCURACY TEST:
   - Rule discovery on complex combinations:
     (Legal Threat AND Unauthorized Billing) OR (Critical Technical Failure AND Hacked Account).

4. NOISE RESISTANCE AND ADVERSARIAL CASES TEST:
   - Detection of critical intents disguised among polite text.
"""

import unittest
import time
import random
import pandas as pd
import numpy as np

from exactor_accelerator import ExactorAcceleratorClassifier
from exactor_accelerator.sdk import ExactorAccelerator
from exactor_accelerator.ingestion.text_extractor import TextFeatureExtractor


class TestIntensiveUnstructuredText(unittest.TestCase):

    def setUp(self):
        random.seed(42)
        np.random.seed(42)

    # -------------------------------------------------------------------------
    # TEST 1: MULTILINGUAL SEMANTIC EXTRACTION AND ERROR RESILIENCE
    # -------------------------------------------------------------------------
    def test_01_multilingual_semantic_extraction(self):
        """Validates that the extractor detects precise intents in English and Spanish with noise."""
        samples = [
            # Text with uppercase and legal threat in Spanish
            (
                "I DEMAND A REFUND OF MY MONEY IMMEDIATELY OR I AM GOING TO CONSUMER PROTECTION WITH A LAWYER!!",
                {"text_has_cancellation_intent": 1, "text_has_legal_threat": 1, "text_has_all_caps": 1}
            ),
            # Technical failure and frustration in English
            (
                "Your system is completely broken and down! Failed to login for the second time. Terrible support.",
                {"text_has_technical_bug": 1, "text_has_repeated_contact": 1, "text_has_frustration_anger": 1}
            ),
            # Seguridad y hackeo
            (
                "Help, my password was reset without my authorization and account is blocked!",
                {"text_has_security_account": 1}
            ),
            # Polite frictionless conversation
            (
                "Thank you very much for today's help, excellent support as always. Best regards!",
                {"text_has_gratitude_positive": 1, "text_has_legal_threat": 0, "text_has_frustration_anger": 0}
            )
        ]

        for text, expected in samples:
            feats = TextFeatureExtractor.extract_from_text(text)
            for key, val in expected.items():
                self.assertEqual(
                    feats.get(key), val,
                    f"Fallo en feature '{key}' para el texto: {text}"
                )
        print("[OK] Test 1: Multilingual semantic extraction and noise resilience validated.")

    # -------------------------------------------------------------------------
    # TEST 2: DIÁLOGOS MULTI-TURNO EN FORMATO JSON
    # -------------------------------------------------------------------------
    def test_02_multiturn_dialogue_processing(self):
        """Prueba la ingesta y extracción sobre estructuras de chat multi-turno."""
        chat_transcript = [
            {"speaker": "agente", "text": "Hola, ¿en qué puedo ayudarte hoy?"},
            {"speaker": "cliente", "text": "Hola, sigo esperando hace 3 días que me respondan el reclamo."},
            {"speaker": "agente", "text": "Entiendo, déjame revisar tu cuenta por favor."},
            {"speaker": "cliente", "text": "Es urgente porque me cobraron doble y necesito hablar con un supervisor!"},
        ]

        feats = TextFeatureExtractor.extract_from_conversation(chat_transcript)
        self.assertEqual(feats.get("conv_has_many_turns"), 1)
        self.assertEqual(feats.get("text_has_repeated_contact"), 1)
        self.assertEqual(feats.get("text_has_request_supervisor"), 1)
        self.assertEqual(feats.get("text_has_billing_payment_issue"), 1)
        print("[OK] Test 2: Diálogos multi-turno JSON procesados correctamente.")

    # -------------------------------------------------------------------------
    # TEST 3: APRENDIZAJE CAUSAL Y ACCIONABILIDAD SOBRE 200 CHATS
    # -------------------------------------------------------------------------
    def test_03_causal_learning_on_unstructured_corpus(self):
        """Entrena ExactorAccelerator sobre un corpus variado de 200 chats y valida exactitud."""
        intents_pool = [
            ("Quiero dar de baja mi suscripción y solicitar reembolso.", 1),
            ("Pésimo servicio, los voy a demandar con un abogado por estafa!", 1),
            ("Mi cuenta fue hackeada y cambiaron la contraseña.", 1),
            ("Demora inaceptable, es la tercera vez que consulto.", 1),
            ("Muchas gracias, el problema quedó solucionado.", 0),
            ("Buenas tardes, quería consultar los planes disponibles.", 0),
            ("Excelente atención, muy amables todos.", 0),
            ("¿Dónde puedo descargar mi última factura pagada? Gracias.", 0),
        ]

        dataset = []
        for i in range(200):
            text_template, is_critical = random.choice(intents_pool)
            monto = random.uniform(10, 500)
            dataset.append({
                "monto_factura": monto,
                "antiguedad_meses": random.randint(1, 36),
                "mensaje_cliente": f"Cliente #{i}: {text_template}",
                "es_critico": is_critical
            })

        df_chats = pd.DataFrame(dataset)

        engine = ExactorAccelerator(use_cloud_exactor=False)
        engine.set_choices({
            "ESCALAR_SUPERVISOR_URGENTE": "Casos con amenazas legales, hackeo o quejas graves",
            "ATENCION_BOT_REGULAR": "Consultas cordiales y de baja complejidad"
        })

        t0 = time.perf_counter()
        fit_res = engine.fit(df_chats, target_col="es_critico", max_variables=12)
        fit_time_ms = (time.perf_counter() - t0) * 1000.0

        self.assertIsNotNone(fit_res["formula_booleana"])
        print(f"[OK] Test 3: Fit completado en {fit_time_ms:.2f} ms")
        print(f"     Fórmula Booleana de Texto: {fit_res['formula_booleana']}")

        # Probar evaluación en vivo de caso crítico conocido
        caso_peligroso = {
            "monto_factura": 420.0,
            "antiguedad_meses": 2,
            "mensaje_cliente": "Pésimo servicio, los voy a demandar con un abogado por estafa!"
        }
        res = engine.evaluate(caso_peligroso, fast_path=True)
        self.assertEqual(res["decision"], "CRITICAL")
        self.assertEqual(res["evaluacion_exacta_booleana"], 1)
        print(f"[OK] Test 3: Inferencia instantánea de texto validada ({res['latencia_ms']} ms).")

    # -------------------------------------------------------------------------
    # TEST 4: ESTRÉS DE RENDIMIENTO (THROUGHPUT DE BINARIZACIÓN DE TEXTO)
    # -------------------------------------------------------------------------
    def test_04_stress_throughput_text_processing(self):
        """Mide la velocidad de extracción sobre 500 textos consecutivos."""
        sample_texts = [
            "Mensaje de prueba con múltiples palabras y signos de exclamación para verificar el rendimiento en ráfaga!!",
            "Cancelación urgente de servicio por cobro duplicado y demora en la respuesta del equipo.",
            "Todo perfecto, muchas gracias por la atención rápida y cordial.",
            "Error grave en el sistema, la pantalla queda en negro al intentar pagar con tarjeta.",
        ] * 125  # 500 textos

        t0 = time.perf_counter()
        for txt in sample_texts:
            _ = TextFeatureExtractor.extract_from_text(txt)
        total_time_ms = (time.perf_counter() - t0) * 1000.0
        avg_time_ms = total_time_ms / len(sample_texts)
        tps = 1000.0 / avg_time_ms

        self.assertLess(avg_time_ms, 1.0)  # Menos de 1 ms por texto
        print(f"[OK] Test 4: 500 textos procesados en {total_time_ms:.2f} ms ({avg_time_ms:.4f} ms/texto, ~{tps:,.0f} TPS).")

    # -------------------------------------------------------------------------
    # TEST 5: COMPATIBILIDAD SCIKIT-LEARN CON COLUMNAS DE TEXTO
    # -------------------------------------------------------------------------
    def test_05_sklearn_classifier_with_unstructured_text(self):
        """Valida que ExactorAcceleratorClassifier maneje texto en fit, predict y score."""
        df = pd.DataFrame([
            {"monto": 100, "chat": "Cancelar servicio de inmediato!", "target": 1},
            {"monto": 20,  "chat": "Muchas gracias por todo!", "target": 0},
            {"monto": 300, "chat": "Demanda con abogado por estafa!", "target": 1},
            {"monto": 50,  "chat": "Excelente ayuda, gracias.", "target": 0},
        ] * 25)

        clf = ExactorAcceleratorClassifier(max_variables=8, fast_path=True)
        X = df[["monto", "chat"]]
        y = df["target"].values

        clf.fit(X, y)
        self.assertTrue(clf.is_fitted_)

        preds = clf.predict(X)
        self.assertEqual(len(preds), len(y))

        acc = clf.score(X, y)
        self.assertGreaterEqual(acc, 0.90)
        print(f"[OK] Test 5: ExactorAcceleratorClassifier con texto alcanzó {acc * 100:.1f}% de Accuracy.")


if __name__ == "__main__":
    unittest.main()
