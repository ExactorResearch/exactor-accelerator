"""
Test Suite para Soporte Nativo Multi-Clase (C > 2) y Multi-Etiqueta en ExactorAccelerator.
Prueba:
 1. Multi-Class Classification with 4 operational business categories:
    - 'FRAUDE_BANCARIO'
    - 'DISPUTA_COMERCIAL'
    - 'SOPORTE_TECNICO'
    - 'BAJA_VOLUNTARIA'
 2. ExactorAccelerator SDK evaluate() with multi-class probability distribution.
 3. ExactorAcceleratorClassifier estilo scikit-learn (predict_proba con shape N x C).
 4. ExactorAcceleratorMultiLabelClassifier (matriz binaria multietiqueta N x K).
 5. Persistencia y recarga transparente de modelos multi-clase (.ej).
"""

import unittest
import os
import time
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, classification_report

from exactor_accelerator import (
    ExactorAcceleratorClassifier,
    ExactorAcceleratorMultiLabelClassifier,
    save_model,
    load_model,
)
from exactor_accelerator.sdk import ExactorAccelerator


class TestMultiClassMultiLabel(unittest.TestCase):

    def setUp(self):
        self.tmp_model_path = "test_multiclass_model.ej"
        self.tmp_db_path = "test_multiclass_memory.db"
        if os.path.exists(self.tmp_db_path):
            os.remove(self.tmp_db_path)

        # Synthetic 4-class dataset with tabular data and unstructured text
        data = [
            # 1. FRAUDE_BANCARIO
            {"monto": 4500, "antiguedad": 1, "intentos_fallidos": 4, "texto": "Transferencia urgente no reconocida hacia cuenta desconocida", "categoria": "FRAUDE_BANCARIO"},
            {"monto": 3800, "antiguedad": 2, "intentos_fallidos": 3, "texto": "Mi clave fue cambiada y me vaciaron la cuenta de ahorros", "categoria": "FRAUDE_BANCARIO"},
            {"monto": 5200, "antiguedad": 1, "intentos_fallidos": 5, "texto": "Alerta de spoofing y hackeo en tarjeta de crédito", "categoria": "FRAUDE_BANCARIO"},

            # 2. DISPUTA_COMERCIAL
            {"monto": 120, "antiguedad": 18, "intentos_fallidos": 0, "texto": "Cobro duplicado en la factura de este mes, pido reintegro", "categoria": "DISPUTA_COMERCIAL"},
            {"monto": 85,  "antiguedad": 24, "intentos_fallidos": 0, "texto": "Me facturaron un cargo de mantenimiento que no corresponde", "categoria": "DISPUTA_COMERCIAL"},
            {"monto": 210, "antiguedad": 12, "intentos_fallidos": 0, "texto": "Reclamo por cobro de seguro no contratado en la tarjeta", "categoria": "DISPUTA_COMERCIAL"},

            # 3. SOPORTE_TECNICO
            {"monto": 0,   "antiguedad": 6,  "intentos_fallidos": 1, "texto": "La aplicación móvil se cierra sola al intentar iniciar sesión", "categoria": "SOPORTE_TECNICO"},
            {"monto": 0,   "antiguedad": 15, "intentos_fallidos": 0, "texto": "No puedo descargar el extracto en formato PDF desde la web", "categoria": "SOPORTE_TECNICO"},
            {"monto": 0,   "antiguedad": 9,  "intentos_fallidos": 1, "texto": "Error de conexión 500 al intentar transferir entre mis cuentas", "categoria": "SOPORTE_TECNICO"},

            # 4. BAJA_VOLUNTARIA
            {"monto": 45,  "antiguedad": 36, "intentos_fallidos": 0, "texto": "Quiero cancelar el servicio y dar de baja mi cuenta bancaria", "categoria": "BAJA_VOLUNTARIA"},
            {"monto": 60,  "antiguedad": 48, "intentos_fallidos": 0, "texto": "Solicito la rescisión inmediata de mi contrato y portabilidad", "categoria": "BAJA_VOLUNTARIA"},
            {"monto": 30,  "antiguedad": 20, "intentos_fallidos": 0, "texto": "Cerrar cuenta definitivamente por mudanza al exterior", "categoria": "BAJA_VOLUNTARIA"},
        ] * 8

        self.df = pd.DataFrame(data)

    def tearDown(self):
        if os.path.exists(self.tmp_model_path):
            os.remove(self.tmp_model_path)
        if os.path.exists(self.tmp_db_path):
            try:
                os.remove(self.tmp_db_path)
            except Exception:
                pass

    def test_01_sdk_multiclass_fit_and_evaluate(self):
        """Prueba ExactorAccelerator SDK con target multi-clase (C = 4)."""
        engine = ExactorAccelerator(use_cloud_exactor=False, db_path=self.tmp_db_path)
        fit_res = engine.fit(self.df, target_col="categoria", max_variables=16)

        self.assertEqual(fit_res["status"], "SUCCESS")
        self.assertTrue(fit_res["is_multiclass"])
        self.assertEqual(len(fit_res["classes"]), 4)
        print(f"\n[OK] Fit Multi-Clase ExactorAccelerator: {fit_res['total_clases']} clases inducidas con éxito.")

        # Evaluar un caso de Fraude
        evento_fraude = {
            "monto": 4000,
            "antiguedad": 1,
            "intentos_fallidos": 4,
            "texto": "Cuenta hackeada y transferencia no autorizada",
        }
        res_fraude = engine.evaluate(evento_fraude, fast_path=True)
        self.assertEqual(res_fraude["categoria_ganadora"], "FRAUDE_BANCARIO")
        self.assertIn("FRAUDE_BANCARIO", res_fraude["distribucion_probabilidades"])
        print(f"[OK] Inferencia Multi-Clase Fraude: {res_fraude['categoria_ganadora']} ({res_fraude['certeza_probabilistica']}%, {res_fraude['latencia_ms']} ms)")

        # Evaluar un caso de Soporte Técnico
        evento_soporte = {
            "monto": 0,
            "antiguedad": 6,
            "intentos_fallidos": 1,
            "texto": "La aplicación móvil se cierra con error al intentar iniciar sesión",
        }
        res_soporte = engine.evaluate(evento_soporte, fast_path=True)
        self.assertEqual(res_soporte["categoria_ganadora"], "SOPORTE_TECNICO")
        print(f"[OK] Inferencia Multi-Clase Soporte: {res_soporte['categoria_ganadora']} ({res_soporte['certeza_probabilistica']}%, {res_soporte['latencia_ms']} ms)")

        # Evaluar explicación
        exp = engine.explain(evento_fraude)
        self.assertIn("FRAUDE_BANCARIO", exp)
        print(f"[OK] Explicación Multi-Clase generada:\n{exp[:200]}...")

    def test_02_sklearn_multiclass_classifier(self):
        """Prueba ExactorAcceleratorClassifier con interfaz Scikit-Learn multi-clase."""
        clf = ExactorAcceleratorClassifier(max_variables=16, fast_path=True)
        X = self.df[["monto", "antiguedad", "intentos_fallidos", "texto"]]
        y = self.df["categoria"]

        clf.fit(X, y)
        self.assertTrue(clf.is_multiclass_)
        self.assertEqual(len(clf.classes_), 4)

        # Predict
        y_pred = clf.predict(X)
        acc = accuracy_score(y, y_pred)
        self.assertGreaterEqual(acc, 0.95)
        print(f"\n[OK] Sklearn Multi-Class Accuracy: {acc * 100:.1f}%")

        # Predict Proba
        probas = clf.predict_proba(X)
        self.assertEqual(probas.shape, (len(X), 4))
        # Validar que las probabilidades sumen 1.0 por fila
        row_sums = np.sum(probas, axis=1)
        np.testing.assert_allclose(row_sums, 1.0, rtol=1e-5)
        print(f"[OK] Predict Proba Multi-Class validado (Shape: {probas.shape}, sum=1.0)")

    def test_03_multilabel_classifier(self):
        """Prueba ExactorAcceleratorMultiLabelClassifier con múltiples etiquetas binarias simultáneas."""
        X = self.df[["monto", "antiguedad", "intentos_fallidos", "texto"]]
        
        # Crear 3 etiquetas binarias simultáneas
        Y_multilabel = pd.DataFrame({
            "alerta_riesgo_alto": (self.df["categoria"] == "FRAUDE_BANCARIO").astype(int),
            "requiere_reembolso": (self.df["categoria"] == "DISPUTA_COMERCIAL").astype(int),
            "ticket_tecnico": (self.df["categoria"] == "SOPORTE_TECNICO").astype(int),
        })

        ml_clf = ExactorAcceleratorMultiLabelClassifier(max_variables=16, fast_path=True)
        ml_clf.fit(X, Y_multilabel)

        y_pred_matrix = ml_clf.predict(X)
        self.assertEqual(y_pred_matrix.shape, (len(X), 3))

        probas_matrix = ml_clf.predict_proba(X)
        self.assertEqual(probas_matrix.shape, (len(X), 3))
        print(f"\n[OK] Multi-Label Predict & Proba validado (Matriz shape: {y_pred_matrix.shape})")

    def test_04_save_and_load_multiclass_model(self):
        """Prueba persistencia y recarga de modelo multi-clase (.ej)."""
        engine = ExactorAccelerator(use_cloud_exactor=False)
        engine.fit(self.df, target_col="categoria", max_variables=16)

        # Guardar en archivo
        save_model(engine, self.tmp_model_path, metadata={"tipo": "multiclase_4_vias"})
        self.assertTrue(os.path.exists(self.tmp_model_path))

        # Cargar en nueva instancia
        loaded_engine = load_model(self.tmp_model_path)
        self.assertTrue(loaded_engine.is_multiclass)
        self.assertEqual(len(loaded_engine.classes), 4)

        # Evaluar
        test_event = {"monto": 50, "antiguedad": 40, "intentos_fallidos": 0, "texto": "Quiero cancelar mi cuenta"}
        res = loaded_engine.evaluate(test_event, fast_path=True)
        self.assertEqual(res["categoria_ganadora"], "BAJA_VOLUNTARIA")
        print(f"\n[OK] Modelo Multi-Clase Recargado (.ej): Categoría={res['categoria_ganadora']}, Latencia={res['latencia_ms']} ms")


if __name__ == "__main__":
    unittest.main()
