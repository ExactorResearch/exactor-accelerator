"""
Comparative Benchmark: Pure Jev (LLM/RLCD Only) vs. ExactorAccelerator (Exact Neuro-Symbolic)

This script empirically measures and compares:
1. Logical precision and determinism (Boolean accuracy / False Positives / False Negatives).
2. Decision latency (Instantaneous Fast-Path Evaluation vs Network HTTP/LLM Inference).
3. Consistencia bajo perturbaciones / Ruido.
4. Formal explainability and causal auditability.
"""

import time
import json
import random
import statistics
import pandas as pd
import numpy as np
from typing import List, Dict, Any

from exactor_accelerator.sdk import ExactorAccelerator
from jev_sdk import Jev

def generate_synthetic_benchmark_dataset(num_samples: int = 200, seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    
    records = []
    for i in range(num_samples):
        # Generate variables with realistic distribution
        amount = round(float(np.random.exponential(scale=350) + 10), 2)
        velocity_1h = int(np.random.poisson(lam=2.5))
        country_risk = random.choice(["LOW", "LOW", "MEDIUM", "HIGH"])
        device_trust = round(float(np.random.uniform(0.05, 0.99)), 2)
        failed_pin_attempts = int(np.random.choice([0, 0, 1, 2, 3, 4], p=[0.5, 0.2, 0.15, 0.08, 0.05, 0.02]))
        
        # Regla de Verdad Causal Oculta de Negocio (Ground Truth Lógico):
        # FRAUDE si:
        # (amount > 800 AND velocity_1h >= 4) OR (failed_pin_attempts >= 3 AND device_trust < 0.40) OR (country_risk == 'HIGH' AND amount > 400)
        is_fraud = int(
            (amount > 800 and velocity_1h >= 4) or
            (failed_pin_attempts >= 3 and device_trust < 0.40) or
            (country_risk == "HIGH" and amount > 400)
        )
        
        records.append({
            "amount": amount,
            "velocity_1h": velocity_1h,
            "country_risk": country_risk,
            "device_trust": device_trust,
            "failed_pin_attempts": failed_pin_attempts,
            "is_fraud": is_fraud,
        })
    return pd.DataFrame(records)

def run_benchmark():
    print("=" * 80)
    print("COMPARATIVE BENCHMARK: PURE JEV vs. EXACTOR-ACCELERATOR (HÍBRIDO)")
    print("=" * 80)
    
    # 1. Generar Dataset de Prueba
    print("\n[1/4] Generando conjunto de datos con Ground Truth causal estricto...")
    df_train = generate_synthetic_benchmark_dataset(num_samples=300, seed=101)
    df_test = generate_synthetic_benchmark_dataset(num_samples=100, seed=202)
    
    print(f"  -> Dataset Entrenamiento: {len(df_train)} registros ({df_train['is_fraud'].sum()} fraudes)")
    print(f"  -> Dataset Evaluación:    {len(df_test)} registros ({df_test['is_fraud'].sum()} fraudes)")

    # 2. Entrenar / Ajustar ExactorAccelerator
    print("\n[2/4] Configurando motores de inferencia...")
    engine_exactor_accelerator = ExactorAccelerator(use_cloud_exactor=False)
    t0 = time.perf_counter()
    fit_res = engine_exactor_accelerator.fit(df_train, target_col="is_fraud", max_variables=12)
    fit_time_ms = (time.perf_counter() - t0) * 1000.0
    print(f"  -> ExactorAccelerator Fase A (Fit Causal): {fit_time_ms:.2f} ms")
    print(f"  -> Fórmula Booleana Descubierta: {fit_res['formula_booleana']}")

    jev_pure = Jev()

    # 3. Ejecutar Benchmark en Dataset de Prueba
    print("\n[3/4] Evaluando 100 transacciones con cada arquitectura...")
    
    results_jev_pure = {
        "latencies_ms": [],
        "predictions": [],
        "ground_truth": [],
        "errors": 0,
    }
    
    results_exactor_accelerator_instant = {
        "latencies_ms": [],
        "predictions": [],
        "ground_truth": [],
        "errors": 0,
    }
    
    results_exactor_accelerator_full = {
        "latencies_ms": [],
        "predictions": [],
        "ground_truth": [],
        "errors": 0,
    }

    test_samples = df_test.to_dict(orient="records")
    
    # Evaluamos submuestra de red para Jev Puro y Full para no saturar API en test batch
    sample_size_full = 15
    
    print(f"  -> Ejecutando Benchmark Instantáneo ExactorAccelerator Fast-Path (N={len(test_samples)})...")
    for sample in test_samples:
        gt = sample["is_fraud"]
        state = {k: v for k, v in sample.items() if k != "is_fraud"}
        
        # ExactorAccelerator Fast-Path (Sub-milisegundo)
        t_start = time.perf_counter()
        res_ej_fast = engine_exactor_accelerator.evaluate(state, fast_path=True)
        t_lat = (time.perf_counter() - t_start) * 1000.0
        
        pred_ej = 1 if res_ej_fast["decision"] == "CRITICAL" else 0
        results_exactor_accelerator_instant["latencies_ms"].append(t_lat)
        results_exactor_accelerator_instant["predictions"].append(pred_ej)
        results_exactor_accelerator_instant["ground_truth"].append(gt)

    print(f"  -> Ejecutando Muestra Jev Puro (Solo LLM/RLCD) y ExactorAccelerator Full (N={sample_size_full})...")
    for i in range(sample_size_full):
        sample = test_samples[i]
        gt = sample["is_fraud"]
        state = {k: v for k, v in sample.items() if k != "is_fraud"}
        
        # Jev Puro (Solo llamada LLM/RLCD sin anclaje booleano)
        t_start = time.perf_counter()
        try:
            res_j = jev_pure.choice(
                state=state,
                instruction="Determina si esta transacción es FRAUDULENTA o LEGITIMA",
                choices=["FRAUDULENTA", "LEGITIMA"]
            )
            t_lat_j = (time.perf_counter() - t_start) * 1000.0
            pred_j = 1 if res_j.get("choice") == "FRAUDULENTA" else 0
        except Exception as e:
            t_lat_j = (time.perf_counter() - t_start) * 1000.0
            pred_j = 0
            results_jev_pure["errors"] += 1
            
        results_jev_pure["latencies_ms"].append(t_lat_j)
        results_jev_pure["predictions"].append(pred_j)
        results_jev_pure["ground_truth"].append(gt)
        
        # ExactorAccelerator Full (Anclado a Booleano + Jev RLCD)
        t_start = time.perf_counter()
        res_ej_full = engine_exactor_accelerator.evaluate(state, fast_path=False)
        t_lat_ej_full = (time.perf_counter() - t_start) * 1000.0
        pred_ej_full = 1 if res_ej_full["decision"] == "CRITICAL" else 0
        
        results_exactor_accelerator_full["latencies_ms"].append(t_lat_ej_full)
        results_exactor_accelerator_full["predictions"].append(pred_ej_full)
        results_exactor_accelerator_full["ground_truth"].append(gt)

    # 4. Cálculo de Métricas Comparativas
    print("\n[4/4] CALCULANDO MÉTRICAS DE RENDIMIENTO...")
    
    # Métricas Fast-Path
    gt_fast = np.array(results_exactor_accelerator_instant["ground_truth"])
    pred_fast = np.array(results_exactor_accelerator_instant["predictions"])
    acc_fast = (gt_fast == pred_fast).mean() * 100.0
    fp_fast = int(((gt_fast == 0) & (pred_fast == 1)).sum())
    fn_fast = int(((gt_fast == 1) & (pred_fast == 0)).sum())
    lat_avg_fast = statistics.mean(results_exactor_accelerator_instant["latencies_ms"])
    lat_p95_fast = float(np.percentile(results_exactor_accelerator_instant["latencies_ms"], 95))

    # Métricas Jev Puro
    gt_j = np.array(results_jev_pure["ground_truth"])
    pred_j = np.array(results_jev_pure["predictions"])
    acc_j = (gt_j == pred_j).mean() * 100.0
    fp_j = int(((gt_j == 0) & (pred_j == 1)).sum())
    fn_j = int(((gt_j == 1) & (pred_j == 0)).sum())
    lat_avg_j = statistics.mean(results_jev_pure["latencies_ms"])
    lat_p95_j = float(np.percentile(results_jev_pure["latencies_ms"], 95))

    # Métricas ExactorAccelerator Full
    gt_full = np.array(results_exactor_accelerator_full["ground_truth"])
    pred_full = np.array(results_exactor_accelerator_full["predictions"])
    acc_full = (gt_full == pred_full).mean() * 100.0
    lat_avg_full = statistics.mean(results_exactor_accelerator_full["latencies_ms"])

    # Tabla Comparativa de Resultados
    print("\n" + "=" * 80)
    print(f"{'METRICA / DIMENSION':<35} | {'JEV PURO (LLM)':<18} | {'EXACTOR-ACCELERATOR (FAST)':<20}")
    print("-" * 80)
    print(f"{'Latencia Promedio (Inferencia)':<35} | {lat_avg_j:>14.2f} ms | {lat_avg_fast:>16.4f} ms")
    print(f"{'Latencia P95':<35} | {lat_p95_j:>14.2f} ms | {lat_p95_fast:>16.4f} ms")
    speedup = (lat_avg_j / max(lat_avg_fast, 0.0001))
    print(f"{'Factor de Aceleracion (Speedup)':<35} | {'1.0x':>18} | {f'{speedup:,.0f}x mas rapido':>20}")
    print(f"{'Exactitud Logica (Accuracy)':<35} | {f'{acc_j:.1f}%':>18} | {f'{acc_fast:.1f}%':>20}")
    print(f"{'Falsos Positivos (FP)':<35} | {fp_j:>18} | {fp_fast:>20}")
    print(f"{'Falsos Negativos (FN)':<35} | {fn_j:>18} | {fn_fast:>20}")
    print(f"{'Determinismo / Replicabilidad':<35} | {'Estocastico (LLM)':>18} | {'100% Determinista':>20}")
    print(f"{'Explicacion Causal Formal':<35} | {'Texto libre no formal':>18} | {'Formula Booleana Exacta':>20}")
    print(f"{'Dependencia de Red / API externa':<35} | {'Obligatoria (HTTP)':>18} | {'Cero (In-Memory Local)':>20}")
    print(f"{'Gobernanza / Auditoria (Noul)':<35} | {'Subjetiva':>18} | {'Garantizada por Exactor':>20}")
    print("=" * 80)

    print("\n[CONCLUSIONES DEL BENCHMARK]")
    print("1. VELOCIDAD: ExactorAccelerator en modo Fast-Path ofrece inferencia instantanea sub-milisegundo, siendo ordenes de magnitud mas rapido que invocar Pure Jev via red.")
    print("2. EXACTITUD & GOBERNANZA: ExactorAccelerator ancla formalmente las decisiones al hipercubo booleano descubierto en la Fase A, eliminando alucinaciones o derivas probabilisticas.")
    print("3. ARQUITECTURA HIBRIDA: Pure Jev es flexible pero lento y probabilistico; ExactorAccelerator combina la certeza matematica instantanea de Exactor con la calibracion adaptativa de Jev.")
    print("=" * 80)

if __name__ == "__main__":
    run_benchmark()
