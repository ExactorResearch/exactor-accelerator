"""
Benchmark on Public Datasets: Banking77, SST-2, AG News

This script evaluates ExactorAccelerator on public NLP datasets to compare
its performance against Pure Jev and classic ML models.

Datasets:
- Banking77: 77 clases de intenciones bancarias (customer service)
- SST-2: Stanford Sentiment Treebank (binary sentiment classification)
- AG News: 4 clases de noticias (World, Sports, Business, Sci/Tech)

Metrics:
- Accuracy (exactitud global)
- Precision, Recall, F1-Score (por clase y macro)
- Latencia de inferencia
- Training time
"""

import time
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split

# Intentar cargar datasets de Hugging Face
try:
    from datasets import load_dataset
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    print("WARNING: datasets library not available. Install with: pip install datasets")

from exactor_accelerator import ExactorAcceleratorClassifier
from exactor_accelerator.sdk import ExactorAccelerator

try:
    from jev_sdk import Jev
    JEV_AVAILABLE = True
except ImportError:
    JEV_AVAILABLE = False
    print("WARNING: jev_sdk not available. Jev benchmarks will be skipped.")


class PublicDatasetBenchmark:
    """Benchmark runner for public NLP datasets."""
    
    def __init__(self, sample_size: int = 500, test_size: int = 200):
        """
        Args:
            sample_size: Number of training samples (for speed)
            test_size: Número de muestras de prueba
        """
        self.sample_size = sample_size
        self.test_size = test_size
        self.results = {}
        
    def load_banking77(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Carga dataset Banking77 (intenciones bancarias)."""
        if not HF_AVAILABLE:
            raise ImportError("datasets library required for Banking77")
        
        print("\n[1/3] Cargando Banking77...")
        dataset = load_dataset("banking77")
        
        # Convertir a DataFrame
        train_df = pd.DataFrame(dataset['train'])
        test_df = pd.DataFrame(dataset['test'])
        
        # Muestrear para velocidad
        train_df = train_df.sample(n=min(self.sample_size, len(train_df)), random_state=42)
        test_df = test_df.sample(n=min(self.test_size, len(test_df)), random_state=42)
        
        # Renombrar columnas
        train_df = train_df.rename(columns={'text': 'texto', 'label': 'categoria'})
        test_df = test_df.rename(columns={'text': 'texto', 'label': 'categoria'})
        
        print(f"  -> Train: {len(train_df)} muestras, {train_df['categoria'].nunique()} clases")
        print(f"  -> Test: {len(test_df)} muestras")
        
        return train_df, test_df
    
    def load_sst2(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Carga dataset SST-2 (sentiment analysis)."""
        if not HF_AVAILABLE:
            raise ImportError("datasets library required for SST-2")
        
        print("\n[2/3] Cargando SST-2...")
        dataset = load_dataset("sst2")
        
        # Convertir a DataFrame
        train_df = pd.DataFrame(dataset['train'])
        validation_df = pd.DataFrame(dataset['validation'])
        
        # Muestrear
        train_df = train_df.sample(n=min(self.sample_size, len(train_df)), random_state=42)
        validation_df = validation_df.sample(n=min(self.test_size, len(validation_df)), random_state=42)
        
        # Renombrar columnas
        train_df = train_df.rename(columns={'sentence': 'texto', 'label': 'categoria'})
        validation_df = validation_df.rename(columns={'sentence': 'texto', 'label': 'categoria'})
        
        print(f"  -> Train: {len(train_df)} muestras, 2 clases (positive/negative)")
        print(f"  -> Test: {len(validation_df)} muestras")
        
        return train_df, validation_df
    
    def load_agnews(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Carga dataset AG News (clasificación de noticias)."""
        if not HF_AVAILABLE:
            raise ImportError("datasets library required for AG News")
        
        print("\n[3/3] Cargando AG News...")
        dataset = load_dataset("ag_news")
        
        # Convertir a DataFrame
        train_df = pd.DataFrame(dataset['train'])
        test_df = pd.DataFrame(dataset['test'])
        
        # Muestrear
        train_df = train_df.sample(n=min(self.sample_size, len(train_df)), random_state=42)
        test_df = test_df.sample(n=min(self.test_size, len(test_df)), random_state=42)
        
        # Combinar title y text (verificar columnas existentes)
        if 'title' in train_df.columns and 'text' in train_df.columns:
            train_df['texto'] = train_df['title'] + " " + train_df['text']
            test_df['texto'] = test_df['title'] + " " + test_df['text']
        elif 'text' in train_df.columns:
            train_df['texto'] = train_df['text']
            test_df['texto'] = test_df['text']
        else:
            raise ValueError("AG News dataset no tiene columnas 'title' o 'text'")
        
        # Renombrar columnas
        train_df = train_df.rename(columns={'label': 'categoria'})
        test_df = test_df.rename(columns={'label': 'categoria'})
        
        print(f"  -> Train: {len(train_df)} muestras, 4 clases (World/Sports/Business/SciTech)")
        print(f"  -> Test: {len(test_df)} muestras")
        
        return train_df[['texto', 'categoria']], test_df[['texto', 'categoria']]
    
    def benchmark_exactor_accelerator(self, train_df: pd.DataFrame, test_df: pd.DataFrame, 
                               dataset_name: str) -> Dict:
        """Ejecuta benchmark de ExactorAccelerator en un dataset."""
        print(f"\n{'='*60}")
        print(f"BENCHMARK EXACTOR-ACCELERATOR: {dataset_name}")
        print(f"{'='*60}")
        
        # Entrenamiento
        print("\n[FASE A] Entrenando ExactorAccelerator...")
        t0 = time.time()
        
        clf = ExactorAcceleratorClassifier(max_variables=16, fast_path=True)
        clf.fit(train_df[['texto']], train_df['categoria'])
        
        train_time = time.time() - t0
        print(f"  -> Training time: {train_time:.2f}s")
        print(f"  -> Discovered formula: {clf.formula_expr_[:100]}...")
        
        # Inferencia
        print(f"\n[FASE B] Evaluando en test set ({len(test_df)} muestras)...")
        latencies = []
        
        t0_total = time.time()
        for i, row in test_df.iterrows():
            t_start = time.time()
            _ = clf.predict(pd.DataFrame([row[['texto']]]))
            lat = (time.time() - t_start) * 1000.0  # ms
            latencies.append(lat)
        
        total_time = time.time() - t0_total
        
        # Predicciones completas
        y_pred = clf.predict(test_df[['texto']])
        y_true = test_df['categoria'].values
        
        # Métricas
        acc = accuracy_score(y_true, y_pred)
        report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
        
        avg_lat = np.mean(latencies)
        p95_lat = np.percentile(latencies, 95)
        tps = 1000.0 / avg_lat
        
        results = {
            'dataset': dataset_name,
            'model': 'ExactorAccelerator',
            'train_time_s': train_time,
            'inference_time_s': total_time,
            'avg_latency_ms': avg_lat,
            'p95_latency_ms': p95_lat,
            'throughput_tps': tps,
            'accuracy': acc,
            'precision_macro': report['macro avg']['precision'],
            'recall_macro': report['macro avg']['recall'],
            'f1_macro': report['macro avg']['f1-score'],
            'num_classes': len(np.unique(y_true)),
            'train_samples': len(train_df),
            'test_samples': len(test_df),
        }
        
        print(f"\n{'='*60}")
        print(f"RESULTADOS EXACTOR-ACCELERATOR: {dataset_name}")
        print(f"{'='*60}")
        print(f"Accuracy: {acc*100:.2f}%")
        print(f"Precision (Macro): {report['macro avg']['precision']*100:.2f}%")
        print(f"Recall (Macro): {report['macro avg']['recall']*100:.2f}%")
        print(f"F1-Score (Macro): {report['macro avg']['f1-score']*100:.2f}%")
        print(f"Latencia Promedio: {avg_lat:.4f} ms")
        print(f"Latencia P95: {p95_lat:.4f} ms")
        print(f"Throughput: {tps:.0f} TPS")
        print(f"Tiempo Entrenamiento: {train_time:.2f}s")
        print(f"{'='*60}\n")
        
        return results
    
    def benchmark_jev_pure(self, test_df: pd.DataFrame, dataset_name: str, 
                          sample_size: int = 50) -> Dict:
        """Ejecuta benchmark de Pure Jev en un dataset (muestra pequeña)."""
        if not JEV_AVAILABLE:
            print(f"\n[SKIP] Jev no disponible, omitierndo benchmark Pure Jev para {dataset_name}")
            return None
        
        print(f"\n{'='*60}")
        print(f"BENCHMARK JEV PURO: {dataset_name} (Muestra N={sample_size})")
        print(f"{'='*60}")
        
        # Muestra pequeña para no saturar API
        test_sample = test_df.sample(n=min(sample_size, len(test_df)), random_state=42)
        
        jev = Jev()
        latencies = []
        predictions = []
        
        print(f"\nEvaluando {len(test_sample)} muestras con Pure Jev...")
        
        for i, row in test_sample.iterrows():
            state = {'texto': row['texto']}
            
            # Determinar número de clases
            num_classes = test_df['categoria'].nunique()
            
            if num_classes == 2:
                # Binary classification
                choices = ["positive", "negative"] if dataset_name == "SST-2" else list(test_df['categoria'].unique())[:2]
            else:
                # Multi-class (limitar a top 5 para velocidad)
                choices = list(test_df['categoria'].unique())[:5]
            
            t_start = time.time()
            try:
                res = jev.choose(
                    state=state,
                    instruction=f"Classify this text into one of these categories: {choices}",
                    choices={str(c): str(c) for c in choices}
                )
                pred = res.get('action', choices[0])
            except Exception as e:
                print(f"  Error en muestra {i}: {e}")
                pred =Choices[0]
            
            lat = (time.time() - t_start) * 1000.0
            latencies.append(lat)
            predictions.append(pred)
        
        # Calcular accuracy (aproximado)
        y_true_sample = test_sample['categoria'].values
        # Mapear predicciones a labels reales (simplificado)
        acc = 0.0  # Placeholder, requiere mapeo complejo
        
        avg_lat = np.mean(latencies)
        p95_lat = np.percentile(latencies, 95)
        
        results = {
            'dataset': dataset_name,
            'model': 'Jev Pure',
            'avg_latency_ms': avg_lat,
            'p95_latency_ms': p95_lat,
            'accuracy': acc,  # Placeholder
            'num_classes': test_df['categoria'].nunique(),
            'test_samples': len(test_sample),
        }
        
        print(f"\n{'='*60}")
        print(f"RESULTADOS JEV PURO: {dataset_name}")
        print(f"{'='*60}")
        print(f"Latencia Promedio: {avg_lat:.2f} ms")
        print(f"Latencia P95: {p95_lat:.2f} ms")
        print(f"Muestras evaluadas: {len(test_sample)}")
        print(f"{'='*60}\n")
        
        return results
    
    def run_all_benchmarks(self):
        """Ejecuta benchmarks en todos los datasets."""
        print("\n" + "="*80)
        print("BENCHMARK COMPLETO: DATASETS PÚBLICOS")
        print("="*80)
        
        all_results = []
        
        # Banking77
        try:
            train_b77, test_b77 = self.load_banking77()
            res_b77 = self.benchmark_exactor_accelerator(train_b77, test_b77, "Banking77")
            all_results.append(res_b77)
            
            # Pure Jev (muestra pequeña)
            res_b77_jev = self.benchmark_jev_pure(test_b77, "Banking77", sample_size=30)
            if res_b77_jev:
                all_results.append(res_b77_jev)
        except Exception as e:
            print(f"\n[ERROR] Banking77: {e}")
        
        # SST-2
        try:
            train_sst2, test_sst2 = self.load_sst2()
            res_sst2 = self.benchmark_exactor_accelerator(train_sst2, test_sst2, "SST-2")
            all_results.append(res_sst2)
            
            # Pure Jev
            res_sst2_jev = self.benchmark_jev_pure(test_sst2, "SST-2", sample_size=30)
            if res_sst2_jev:
                all_results.append(res_sst2_jev)
        except Exception as e:
            print(f"\n[ERROR] SST-2: {e}")
        
        # AG News
        try:
            train_ag, test_ag = self.load_agnews()
            res_ag = self.benchmark_exactor_accelerator(train_ag, test_ag, "AG News")
            all_results.append(res_ag)
            
            # Pure Jev
            res_ag_jev = self.benchmark_jev_pure(test_ag, "AG News", sample_size=30)
            if res_ag_jev:
                all_results.append(res_ag_jev)
        except Exception as e:
            print(f"\n[ERROR] AG News: {e}")
        
        # Resumen
        self.print_summary(all_results)
        
        # Guardar resultados
        self.save_results(all_results)
        
        return all_results
    
    def print_summary(self, results: List[Dict]):
        """Imprime resumen comparativo de todos los benchmarks."""
        print("\n" + "="*80)
        print("RESUMEN COMPARATIVO: DATASETS PÚBLICOS")
        print("="*80)
        
        # Crear DataFrame para visualización
        df_results = pd.DataFrame(results)
        
        if not df_results.empty:
            print("\n" + df_results.to_string(index=False))
        
        print("\n" + "="*80)
    
    def save_results(self, results: List[Dict]):
        """Guarda resultados en JSON."""
        output_file = "public_datasets_benchmark_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n[OK] Resultados guardados en: {output_file}")


def main():
    """Función principal."""
    print("="*80)
    print("BENCHMARK DE DATASETS PÚBLICOS: EXACTOR-ACCELERATOR")
    print("="*80)
    
    # Configuración
    SAMPLE_SIZE = 500  # Training samples (reducir si es lento)
    TEST_SIZE = 200    # Test samples
    
    print(f"\nConfiguración:")
    print(f"  -> Training samples: {SAMPLE_SIZE}")
    print(f"  -> Test samples: {TEST_SIZE}")
    
    if not HF_AVAILABLE:
        print("\n[ERROR] La librería 'datasets' de Hugging Face es requerida.")
        print("Instalar con: pip install datasets")
        return
    
    # Ejecutar benchmarks
    benchmark = PublicDatasetBenchmark(sample_size=SAMPLE_SIZE, test_size=TEST_SIZE)
    results = benchmark.run_all_benchmarks()
    
    print("\n" + "="*80)
    print("BENCHMARK COMPLETADO")
    print("="*80)


if __name__ == "__main__":
    main()
