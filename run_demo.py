"""
EXACTOR + Jev: Comprehensive Demonstration of Live Memory and Initial Ingestion.
Executes full lifecycle: Phase A -> Phase B -> SQLite WAL -> Differential Update.
"""

import os
import sys
import time
import json
import pandas as pd

# Set up project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from exactor_accelerator.engine.runtime import HybridRuntime
from exactor_accelerator.ingestion.loader import DataLoader


if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def print_banner():
    print("=" * 80)
    print("       EXACTOR  [ SMLE Boolean Minimization Engine (Rust) ]")
    print("                              [ X ]")
    print("       JEV      [ TypeSafe AI - System One Decision Models ]")
    print("=" * 80)
    print(" Arquitectura Hibrida: Memoria Viva, Ingesta Inicial y Decisiones Tipadas")
    print(" Paradigma de Aprendizaje Incremental Continuo (Sin Reentrenamiento Estatico)")
    print("=" * 80 + "\n")


def run_demo():
    print_banner()

    db_test_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_memory_ledger.db")
    if os.path.exists(db_test_path):
        try:
            os.remove(db_test_path)
        except Exception:
            pass

    runtime = HybridRuntime(db_path=db_test_path, default_threshold=0.80)

    # -------------------------------------------------------------------------
    # FASE A: PUESTA EN MARCHA (Ingesta Inicial de Entrenamiento)
    # -------------------------------------------------------------------------
    print(">>> [FASE A] PUESTA EN MARCHA (Ingesta Inicial)")
    print("1. Loading historical financial transactions dataset (Fintech Fraud)...")
    df = DataLoader.generate_fintech_fraud_sample(n_records=300, seed=42)
    print(f"   ✓ Registros cargados: {len(df)} filas, {len(df.columns)} columnas.")
    print(f"   ✓ Vista previa:\n{df.head(3).to_string(index=False)}\n")

    print("2. Executing Adaptive Binarization into Boolean Hypercube B^k...")
    print("3. Distilling pure logical rules with EXACTOR Core Engine (Rust)...")
    onboard_res = runtime.phase_a_onboard(df, target_col="is_fraud", max_variables=10)

    print(f"   ✓ Hypercube Dimension B^k: k = {onboard_res['hypercube_dimension_k']} variables.")
    print(f"   ✓ Minitérminos ON-set observados: {onboard_res['initial_minterms']}")
    print(f"   ✓ Términos simplificados finales: {onboard_res['terms_count']}")
    print(f"   ✓ Compresión lógica: {((1 - onboard_res['terms_count']/onboard_res['initial_minterms'])*100):.1f}%")
    print(f"   ✓ Motor activo: {onboard_res['stats'].get('engine')}")
    print(f"\n   [FÓRMULA EXACTOR CANÓNICA]:")
    print(f"   >> {onboard_res['formula_expr']}")
    print(f"\n   [INTERPRETACIÓN SEMÁNTICA]:")
    print(f"   >> {onboard_res['explanation']}\n")

    # -------------------------------------------------------------------------
    # CALIBRACIÓN DEL ESQUEMA JEV (TypeSafe AI)
    # -------------------------------------------------------------------------
    print(">>> [CALIBRACIÓN DEL ESQUEMA JEV (TypeSafe AI)]")
    questions = runtime.translator.create_questions_schema(runtime.current_rule, runtime.propositions_map)
    print("   Preguntas tipadas generadas para el modelo Jev:")
    for q_name, q_obj in questions.items():
        q_type = getattr(q_obj, "type", "desconocido")
        q_inst = getattr(q_obj, "instructions", "")[:90] + "..."
        print(f"   - Pregunta '{q_name}' [Tipo: {q_type.upper()}]: {q_inst}")

    print("\n   Payload representativo enviado a TypeSafe API:")
    sample_payload = runtime.translator.build_payload(
        {"amount": 2900.0, "velocity_1h": 5, "country_risk": "HIGH"},
        runtime.current_rule,
        runtime.propositions_map,
    )
    print(json.dumps(sample_payload.to_dict(), indent=2, ensure_ascii=False)[:350] + "\n   ...\n")

    # -------------------------------------------------------------------------
    # FASE B: OPERACIÓN CONTINUA Y MEMORIA VIVA (Sin Reentrenamiento)
    # -------------------------------------------------------------------------
    print(">>> [FASE B] OPERACIÓN EN TIEMPO REAL (Evaluación Jev & Disparo Autónomo)")
    print("   El sistema recibe eventos en producción, evalúa en milisegundos y actualiza el Ledger WAL.\n")

    test_events = [
        {
            "desc": "Evento 1: Transacción crítica (Alto monto, velocidad inusual, país de alto riesgo)",
            "state": {"amount": 3400.0, "velocity_1h": 6, "country_risk": "HIGH", "device_trust": 0.12, "failed_pin_attempts": 3, "is_new_device": 1},
        },
        {
            "desc": "Evento 2: Transacción legítima cotidiana (Bajo monto, dispositivo confiable)",
            "state": {"amount": 25.50, "velocity_1h": 1, "country_risk": "LOW", "device_trust": 0.96, "failed_pin_attempts": 0, "is_new_device": 0},
        },
        {
            "desc": "Evento 3: Caso límite de incertidumbre (Monto mediano, dispositivo nuevo)",
            "state": {"amount": 750.0, "velocity_1h": 2, "country_risk": "MEDIUM", "device_trust": 0.55, "failed_pin_attempts": 1, "is_new_device": 1},
        },
        {
            "desc": "Evento 4: Anomalía combinada (Alta velocidad y fallos de PIN)",
            "state": {"amount": 1850.0, "velocity_1h": 5, "country_risk": "MEDIUM", "device_trust": 0.28, "failed_pin_attempts": 2, "is_new_device": 0},
        },
    ]

    for idx, t_evt in enumerate(test_events, start=1):
        print(f"--- [{t_evt['desc']}] ---")
        q_res = runtime.phase_b_query(t_evt["state"], confidence_threshold=0.80)
        noul_p = q_res.criterio_logico_prob
        action = q_res.chosen_action
        conf = q_res.confidence
        auton = "⚡ SÍ (AUTÓNOMA)" if q_res.autonomous_action_executed else "🛡️ NO (ESCALADA A HUMANO)"

        print(f"   Minitérmino Hypercubo: {q_res.minterm_val} (binario: b'{q_res.minterm_binary}')")
        print(f"   Evaluación Exacta Exactor: {q_res.exact_boolean_evaluation}")
        print(f"   Probabilidad Calibrada Noul (RLCD): {noul_p:.2%}")
        print(f"   Decisión Seleccionada (Choice): [{action}] (Confianza: {conf:.2%})")
        print(f"   Ejecución Autónoma de Acción de Negocio: {auton}")
        print(f"   Detalle: {q_res.action_details}")
        print(f"   Latencia total: {q_res.latency_ms:.1f} ms\n")

    # -------------------------------------------------------------------------
    # MEMORIA VIVA: CONSULTA DEL LEDGER SQLite WAL
    # -------------------------------------------------------------------------
    print(">>> [LEDGER DE MEMORIA VIVA (SQLite WAL)]")
    entries = runtime.ledger.get_recent_entries(limit=5)
    print(f"   ✓ Interacciones registradas en el Ledger WAL: {runtime.ledger.get_total_count()}")
    print("   Últimas transacciones auditadas:")
    for e in entries[:3]:
        print(f"   - ID: {e['query_id']} | Hora: {e['timestamp'].split('T')[1][:8]} | Prob Noul: {e['criterio_logico_prob']} | Acción: {e['chosen_action']} | Ejecutada: {bool(e['autonomous_action_executed'])}")

    # -------------------------------------------------------------------------
    # ACTUALIZACIÓN DIFERENCIAL (Exactor Incremental en Caliente)
    # -------------------------------------------------------------------------
    print("\n>>> [ACTUALIZACIÓN DIFERENCIAL INCREMENTAL]")
    print("   Procesando ventana deslizante reciente para ajustar las reglas en caliente sin reentrenamiento estático...")
    update_res = runtime.trigger_differential_update(window_size=10)
    print(f"   ✓ Estado de actualización: {update_res['status']}")
    print(f"   ✓ Regla evolucionada a versión: v{update_res['rule_version']}")
    print(f"   ✓ Ventana deslizante procesada: {update_res['window_size']} interacciones")
    print(f"   ✓ Nueva Fórmula: {update_res['new_formula']}")

    print("\n" + "=" * 80)
    print("   ¡DEMOSTRACIÓN COMPLETADA EXITOSAMENTE!")
    print("   El sistema opera bajo Memoria Viva: ingesta inicial + evolución continua en tiempo real.")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
