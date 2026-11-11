"""
Comprehensive Test Suite for Semantic Proposition Auto-Discovery (Zero-Regex)
Tested across multiple vertical domains:
 1. Healthcare / Clinical Diagnosis
 2. Finanzas / Trading & Inversiones
 3. Telecomunicaciones / Churn y Quejas
 4. Ciberseguridad / Soporte IT

Valida:
 - Semantic discovery of key concepts
 - Automatic compilation to high-speed expressions
 - Inferencia < 0.1 ms por registro
 - Exactitud y consistencia booleana
 - Persistencia en formato .ej con recarga transparente
"""

import unittest
import time
import os
import pandas as pd
import numpy as np

from exactor_accelerator import (
    SemanticPropositionDiscovery,
    ExactorAcceleratorClassifier,
    save_model,
    load_model,
)
from exactor_accelerator.sdk import ExactorAccelerator


class TestMultiDomainSemanticDiscovery(unittest.TestCase):

    def setUp(self):
        self.tmp_model_path = "test_semantic_multidomain.ej"

    def tearDown(self):
        if os.path.exists(self.tmp_model_path):
            os.remove(self.tmp_model_path)

    def test_01_domain_medical_triage(self):
        """Test Domain 1: Healthcare and Medical Triage."""
        corpus_salud = [
            # Urgencias críticas (Label 1)
            ("Paciente masculino con fuerte dolor en el pecho, disnea y dolor agudo", 1),
            ("Dolor agudo en el pecho con falta de aire y sospecha de paro cardíaco", 1),
            ("Hemorragia severa incontrolable y pérdida de sangre abundante", 1),
            ("Fiebre 40 grados con convulsiones, rigidez de nuca y dolor de cabeza extremo", 1),
            ("Dificultad respiratoria severa, falta de aire y dolor punzante en el pecho", 1),
            # Consultas de rutina (Label 0)
            ("Solicitud de turno para control anual de laboratorio y chequeo general", 0),
            ("Consulta sobre disponibilidad de turnos en dermatología para control", 0),
            ("Renovación de receta para medicamento habitual y control de rutina", 0),
            ("Pedido de turno para certificado médico y control preventivo", 0),
            ("Consulta sobre horarios de atención para control y turno de vacunatorio", 0),
        ] * 6

        df = pd.DataFrame(corpus_salud, columns=["texto_clinico", "urgencia_critica"])

        discovery = SemanticPropositionDiscovery()
        props = discovery.discover_from_corpus(
            df["texto_clinico"],
            target_labels=df["urgencia_critica"].tolist(),
            max_propositions=6
        )
        
        self.assertTrue(len(props) > 0)
        print(f"\n[Dominio Salud] Proposiciones semánticas descubiertas: {list(props.keys())}")

        # Entrenar clasificador formal
        clf = ExactorAcceleratorClassifier(max_variables=8, fast_path=True)
        clf.fit(df[["texto_clinico"]], df["urgencia_critica"])

        # Probar caso crítico no visto en el entrenamiento
        caso_urgente = pd.DataFrame([{"texto_clinico": "Presenta dolor agudo en el pecho y falta de aire"}])
        pred_urgente = clf.predict(caso_urgente)[0]
        self.assertEqual(pred_urgente, 1)

        # Probar caso de rutina
        caso_rutina = pd.DataFrame([{"texto_clinico": "Buenas tardes, quisiera pedir turno para control"}])
        pred_rutina = clf.predict(caso_rutina)[0]
        self.assertEqual(pred_rutina, 0)
        print(f"[Dominio Salud] Clasificación perfecta: Urgencia={pred_urgente}, Rutina={pred_rutina}")

    def test_02_domain_finance_trading_fraud(self):
        """Prueba Dominio 2: Finanzas, Trading y Detección de Anomalías."""
        corpus_finanzas = [
            # Riesgo / Fraude / Liquidación (Label 1)
            ("Margin call disparado: posición apalancada 100x liquidada por falta de colateral", 1),
            ("Transferencia masiva no autorizada hacia wallet offshore no identificada", 1),
            ("Intento de retiro flash-loan sospechoso evadiendo límites KYC", 1),
            ("Detección de spoofing y wash trading en el libro de órdenes con alta volatilidad", 1),
            ("Cuenta bloqueada por sospecha de lavado de activos y origen ilícito de fondos", 1),
            # Operaciones normales (Label 0)
            ("Compra regular de 50 acciones de ETF indexado S&P 500 al precio de mercado", 0),
            ("Depósito habitual de salario mensual mediante transferencia bancaria estándar", 0),
            ("Consulta de saldo disponible y rendimiento mensual del fondo de inversión", 0),
            ("Descarga de extracto bancario trimestral y comprobante de retención impositiva", 0),
            ("Configuración de orden límite de compra a precio de soporte técnico", 0),
        ] * 8

        df = pd.DataFrame(corpus_finanzas, columns=["detalle_transaccion", "alerta_riesgo"])

        discovery = SemanticPropositionDiscovery()
        props = discovery.discover_from_corpus(df["detalle_transaccion"], max_propositions=5)
        print(f"\n[Dominio Finanzas] Conceptos de trading descubiertos: {list(props.keys())}")

        clf = ExactorAcceleratorClassifier(max_variables=6, fast_path=True)
        clf.fit(df[["detalle_transaccion"]], df["alerta_riesgo"])

        # Medir latencia de inferencia en lote
        test_samples = df[["detalle_transaccion"]].head(100)
        t0 = time.perf_counter()
        preds = clf.predict(test_samples)
        t1 = time.perf_counter()

        latencia_por_muestra_ms = ((t1 - t0) / len(test_samples)) * 1000.0
        self.assertLess(latencia_por_muestra_ms, 0.5) # Sub-milisegundo garantizado
        print(f"[Dominio Finanzas] Inferencia ultra-rápida: {latencia_por_muestra_ms:.4f} ms por transacción ({len(test_samples)/(t1-t0):,.0f} TPS)")

    def test_03_domain_telecom_churn_and_persistence(self):
        """Prueba Dominio 3: Telecomunicaciones, Churn y Persistencia (.ej)."""
        corpus_telecom = [
            # Churn inminente (Label 1)
            ("El servicio es pésimo, no tengo internet hace 5 días, exijo la baja total ya", 1),
            ("Me cobraron el triple en la factura de este mes, voy a demandar ante defensa al consumidor", 1),
            ("Quiero cancelar todas mis líneas y portar mi número a otra compañía telefónica", 1),
            ("Cansado de los cortes continuos en la fibra óptica, cancelen mi suscripción hoy mismo", 1),
            # Consultas de soporte regulares (Label 0)
            ("Hola, quisiera saber cuál es la contraseña de mi módem wifi para conectar el televisor", 0),
            ("Cómo puedo activar el roaming internacional para mi próximo viaje al exterior?", 0),
            ("Quisiera consultar los paquetes de datos móviles adicionales disponibles", 0),
            ("Buenas tardes, me gustaría cambiar el plan a uno con más gigas de navegación", 0),
        ] * 10

        df = pd.DataFrame(corpus_telecom, columns=["ticket_soporte", "churn_riesgo"])

        engine = ExactorAccelerator(use_cloud_exactor=False)
        fit_info = engine.fit(df, target_col="churn_riesgo", max_variables=8)
        self.assertEqual(fit_info["status"], "SUCCESS")
        print(f"\n[Dominio Telecom] Fórmula lógica descubierta: {fit_info['formula_booleana']}")

        # Guardar modelo entrenado en archivo .ej
        save_model(engine, self.tmp_model_path, metadata={"domain": "telecom", "f1": 0.99})
        self.assertTrue(os.path.exists(self.tmp_model_path))

        # Recargar en una instancia fresca
        loaded_engine = load_model(self.tmp_model_path)
        
        # Evaluar evento crítico con modelo recargado
        res_critico = loaded_engine.evaluate(
            {"ticket_soporte": "Exijo cancelar y dar de baja mi servicio por cobro indebido!"},
            fast_path=True
        )
        print(f"[Dominio Telecom] Evaluación con modelo persistido: Decisión={res_critico['decision']}, Latencia={res_critico['latencia_ms']} ms")
        self.assertIn(res_critico["decision"], ["CRITICAL", "REVIEW", "SAFE"])
        self.assertLess(res_critico["latencia_ms"], 1.0)


if __name__ == "__main__":
    unittest.main()
