# Roadmap: Exactor Accelerator v2.0 (Enfoque en Nichos de Excelencia)

**Version**: 2.0  
**Fecha**: 22 de September de 2026  
**Objective**: Strategic enhancement roadmap to advance domains where Exactor Accelerator is already unbeatable

---

## Executive Summary

Exactor Accelerator v1.0 is **unbeatable** in specific niches:
- Fraud detection (95-100% accuracy, 0.05-0.1ms)
- Medical triage (95-100% accuracy, 0.05-0.1ms)
- Monitoreo de calidad (95-100% accuracy, 0.05-0.1ms)
- Logs de seguridad (95-100% accuracy, 0.05-0.1ms)
- Technical forex (80-100% accuracy, 0.05-0.1ms)

**Estrategia v2.0**: Enfocarse en perfeccionar estos nichos en lugar de intentar ser algo para todos.

**Exactor Accelerator v2.0** will focus on:
1. **Dynamic adaptability** (regime detection, concept drift tracking in key niches)
2. **Functional cold start** (for target niches lacking prior historical data)
3. **Domain-specialized features** (forex, fraud, healthcare, manufacturing, cybersecurity)
4. **Performance extremo** (HFT, monitoreo en tiempo real)
5. **Domain-tailored UX** (dedicated dashboards for each vertical)

**Will NOT focus on**:
- ❌ NLP complejo (donde pierde vs Jev/LLMs)
- ❌ Zero-shot general (donde pierde vs Jev)
- ❌ >10 clases (donde pierde vs ML tradicional)
- ❌ Documentos largos (no es el caso de uso)

---

## Phase 1: Dynamic Adaptability in Target Niches (HIGH Priority)

### 1.1 Domain Regime Detector

**Problema Actual**:
- Exactor Accelerator v1.0 uses static thresholds
- No detecta cambios en el dominio (concept drift)
- Performance degrada cuando el dominio cambia

**Improvement v2.0**:
- Implementar `DomainRegimeDetector` (de exactor-forex-coldstart)
- Automatically detect: STABLE_PATTERN, DRIFTING_PATTERN, HIGH_ENTROPY, CONCEPT_DRIFT
- Dynamically adjust thresholds according to active regime

**Impacto Esperado**:
- Accuracy +15-25% in extreme regimes (forex, fraud)
- Early detection of concept drift in primary niches
- Enhanced production robustness for fraud, healthcare, and manufacturing

**Implementation**:
```python
# exactor_accelerator/regime_detector.py (NUEVO)
class DomainRegimeDetector:
    """Generalized regime detector across arbitrary domains."""
    
    REGIMES = ["STABLE_PATTERN", "DRIFTING_PATTERN", "HIGH_ENTROPY", "CONCEPT_DRIFT"]
    
    @classmethod
    def analyze_regime(cls, features: Dict[str, float], history_df: pd.DataFrame) -> Dict[str, Any]:
        """Detects regime based on stability, entropy, and concept drift."""
        feature_stability = cls._calculate_feature_stability(features, history_df)
        class_entropy = cls._calculate_class_entropy(history_df)
        drift_score = cls._detect_concept_drift(history_df)
        
        regime_probs = {
            "STABLE_PATTERN": feature_stability * 0.4,
            "DRIFTING_PATTERN": drift_score * 0.3,
            "HIGH_ENTROPY": class_entropy * 0.3,
            "CONCEPT_DRIFT": drift_score * 0.3,
        }
        
        return {
            "dominant_regime": max(regime_probs, key=regime_probs.get),
            "regime_distribution": regime_probs,
            "stability_index": feature_stability,
            "entropy_index": class_entropy,
            "drift_score": drift_score,
            "actionability_gate": cls._determine_gate(regime_probs),
        }
```

**Runtime Integration**:
```python
# exactor_accelerator/engine/runtime.py (MODIFICAR)
class HybridRuntime:
    def evaluate(self, state: Dict[str, Any], fast_path: bool = True) -> Dict[str, Any]:
        # Detect regime prior to evaluation
        regime_info = self.regime_detector.analyze_regime(
            features=state,
            history_df=self.ledger.get_recent_history(window=50)
        )
        
        # Adjust threshold according to regime
        if regime_info["dominant_regime"] == "HIGH_ENTROPY":
            effective_threshold = self.fast_path_threshold * 0.7
        elif regime_info["dominant_regime"] == "STABLE_PATTERN":
            effective_threshold = self.fast_path_threshold * 1.2
        else:
            effective_threshold = self.fast_path_threshold
        
        return self._evaluate_with_threshold(state, effective_threshold, fast_path)
```

**Timeline**: 2 semanas  
**Prioridad**: ALTA  
**Dependencias**: Ninguna

---

### 1.2 Motor de Features por Domain

**Problema Actual**:
- Manual feature binarization
- Absence of domain-specialized extractors (forex, fraud, healthcare)
- Friction in adding new specialized verticals

**Improvement v2.0**:
- Implementar `DomainFeatureEngine` (de exactor-forex-coldstart)
- Specialized extractors: forex, fraud, healthcare, manufacturing, cybersecurity
- Declarative feature configuration per domain

**Impacto Esperado**:
- Domain features improve discriminative resolution (+5-10% accuracy in core niches)
- Seamless addition of related structured verticals
- Reusability across structured domains

**Implementation**:
```python
# exactor_accelerator/ingestion/feature_engine.py (NUEVO)
class ConfigurableFeatureEngine:
    """Motor de features configurable para cualquier dominio."""
    
    def __init__(self, domain: str = "general"):
        self.domain = domain
        self.feature_extractors = self._get_domain_features(domain)
    
    def _get_domain_features(self, domain: str) -> List[Callable]:
        if domain == "forex":
            return [self._extract_rsi, self._extract_atr, self._extract_ema_spread, self._extract_macd_hist, self._extract_adx]
        elif domain == "fraud":
            return [self._extract_velocity, self._extract_amount_zscore, self._extract_device_trust_trend, self._extract_ip_reputation, self._extract_geolocation_risk]
        elif domain == "medical":
            return [self._extract_vital_signs_zscore, self._extract_lab_values_trend, self._extract_age_risk_factor, self._extract_comorbidity_score]
        elif domain == "manufacturing":
            return [self._extract_sensor_zscore, self._extract_trend_indicator, self._extract_anomaly_score, self._extract_maintenance_history]
        elif domain == "security":
            return [self._extract_ip_reputation, self._extract_request_velocity, self._extract_payload_anomaly, self._extract_user_behavior_score]
        else:
            return self._get_generic_features()
    
    def extract_all(self, df: pd.DataFrame) -> pd.DataFrame:
        for extractor in self.feature_extractors:
            df = extractor(df)
        return df
```

**Integración en Binarizer**:
```python
# exactor_accelerator/ingestion/binarizer.py (MODIFICAR)
class AdaptiveBinarizer:
    def __init__(self, domain: str = "general"):
        self.feature_engine = ConfigurableFeatureEngine(domain=domain)
    
    def fit(self, df: pd.DataFrame, target_col: str):
        df_enriched = self.feature_engine.extract_all(df)
        return super().fit(df_enriched, target_col)
```

**Timeline**: 2 semanas  
**Prioridad**: ALTA  
**Dependencias**: Ninguna

---

## Fase 2: Cold Start para Nichos (HIGH Priority)

### 2.1 Modo Cold Start por Domain

**Problema Actual**:
- Exactor Accelerator v1.0 requires historical data (≥500 samples)
- Non-functional from day 1 in targeted niches
- Jev puro es mejor para cold start general

**Improvement v2.0**:
- Implement cold-start heuristics específicas por dominio
- Auto-evolución periódica adaptada a cada nicho
- Semillas sintéticas basadas en reglas de negocio de cada dominio

**Impacto Esperado**:
- Functional cold-start from day 1
- Accuracy inicial 70-85%
- Auto-evolución sin reentrenamiento manual

**Implementation**:
```python
# exactor_accelerator/engine/runtime.py (MODIFICAR)
class HybridRuntime:
    def __init__(
        self,
        cold_start: bool = False,
        auto_evolve_every: int = 50,
        fast_path_threshold: float = 0.75,
        min_samples_for_evolution: int = 100,
    ):
        self.cold_start = cold_start
        self.auto_evolve_every = auto_evolve_every
        self.min_samples_for_evolution = min_samples_for_evolution
        
        if cold_start:
            self._initialize_cold_start_seeds()
    
    def _initialize_cold_start_seeds(self, domain: str):
        """Inicializa con reglas heurísticas específicas del dominio cuando no hay datos."""
        if domain == "fraud":
            self.heuristic_rules = {
                "high_amount": lambda x: x.get("amount", 0) > 1000,
                "high_velocity": lambda x: x.get("velocity_1h", 0) > 5,
                "high_risk_country": lambda x: x.get("country_risk") == "HIGH",
                "device_trust_low": lambda x: x.get("device_trust", 1.0) < 0.3,
            }
        elif domain == "medical":
            self.heuristic_rules = {
                "critical_vitals": lambda x: x.get("heart_rate", 0) > 120 or x.get("blood_pressure_systolic", 0) > 160,
                "high_temperature": lambda x: x.get("temperature", 37) > 39,
                "low_oxygen": lambda x: x.get("oxygen_saturation", 100) < 90,
            }
        elif domain == "forex":
            self.heuristic_rules = {
                "high_volatility": lambda x: x.get("atr", 0) > 0.0020,
                "strong_trend": lambda x: abs(x.get("ema_spread", 0)) > 0.0010,
                "overbought_oversold": lambda x: x.get("rsi", 50) > 70 or x.get("rsi", 50) < 30,
            }
        elif domain == "manufacturing":
            self.heuristic_rules = {
                "sensor_anomaly": lambda x: x.get("sensor_zscore", 0) > 3,
                "trend_deviation": lambda x: abs(x.get("trend_indicator", 0)) > 0.5,
                "maintenance_due": lambda x: x.get("hours_since_maintenance", 0) > 1000,
            }
        elif domain == "security":
            self.heuristic_rules = {
                "malicious_ip": lambda x: x.get("ip_reputation") == "MALICIOUS",
                "high_velocity": lambda x: x.get("request_rate", 0) > 100,
                "payload_anomaly": lambda x: x.get("payload_size", 0) > 10000,
            }
    
    def evaluate(self, state: Dict[str, Any], fast_path: bool = True) -> Dict[str, Any]:
        if self.cold_start and len(self.ledger) < self.min_samples_for_evolution:
            return self._evaluate_with_heuristics(state)
        
        result = self._evaluate_normal(state, fast_path)
        
        if len(self.ledger) % self.auto_evolve_every == 0:
            self._trigger_evolution()
        
        return result
```

**Timeline**: 3 semanas  
**Prioridad**: ALTA  
**Dependencias**: Ninguna

---

### 2.2 Primitivas JEV para Nichos Específicos

**Problema Actual**:
- Jev solo se usa para binarización general
- No se aprovecha para casos ambiguos en nichos específicos
- Potencial no utilizado en dominios estructurados

**Improvement v2.0**:
- Implementar `JevPrimitiveExtractor` específico por dominio
- Usar primitivas Jev para ponderar decisiones en casos ambiguos
- Resolver divergencias consultando Jev solo cuando es necesario

**Impacto Esperado**:
- Mejor accuracy en casos ambiguos de nichos actuales (+5-10%)
- Aprovechamiento completo de Jev sin sacrificar velocidad
- Mejor balance velocidad-accuracy en fraude, médico, forex

**Implementation**:
```python
# exactor_accelerator/engine/jev_primitives.py (NUEVO)
class JevPrimitiveExtractor:
    """Extrae primitivas tipadas de JEV para asistir a EXACTOR."""
    
    def extract_relevance_score(self, state: Dict[str, Any], context: str) -> float:
        """Extrae score de relevancia (0-1) usando JEV."""
        res = self.jev_client.score(
            state=state,
            instruction=f"Evalúa la relevancia de este estado para: {context}",
        )
        return res["score"] / 100.0
    
    def extract_binary_evaluation(self, state: Dict[str, Any], condition: str) -> bool:
        """Extrae evaluación binaria usando JEV."""
        res = self.jev_client.decide(
            state=state,
            question=condition,
            threshold=0.70,
        )
        return res["is_true"]
    
    def extract_choice_weights(self, state: Dict[str, Any], choices: List[str]) -> Dict[str, float]:
        """Extrae pesos para choices usando JEV."""
        res = self.jev_client.choose(
            state=state,
            instruction="Selecciona la opción más apropiada",
            choices={c: c for c in choices},
        )
        return res["probabilities"]
```

**Runtime Integration**:
```python
# exactor_accelerator/engine/runtime.py (MODIFICAR)
class HybridRuntime:
    def evaluate(self, state: Dict[str, Any], fast_path: bool = True) -> Dict[str, Any]:
        local_result = self._evaluate_local(state, fast_path)
        
        if local_result["certeza_probabilistica"] < self.fast_path_threshold:
            relevance = self.jev_primitives.extract_relevance_score(
                state, context="clasificación de fraude"
            )
            weighted_decision = self._combine_with_primitives(
                local_result, relevance
            )
            return weighted_decision
        
        return local_result
```

**Timeline**: 2 semanas  
**Prioridad**: MEDIA  
**Dependencias**: Jev API

---

## Fase 3: Performance Extremo para Nichos (HIGH Priority)

### 3.1 Optimización para HFT y Monitoreo en Tiempo Real

**Problema Actual**:
- Latency 0.05-0.1ms ya es excelente
- Pero puede mejorarse aún más para HFT extremo
- Memory usage puede optimizarse para alto volumen

**Improvement v2.0**:
- Compilación JIT de fórmulas específicas por dominio
- Caching de predicciones para nichos con inputs repetitivos
- Batch processing optimizado para monitoreo de sensores

**Impacto Esperado**:
- Latency 0.05-0.1ms → 0.01-0.05ms (2-10x más rápido)
- Memory usage reducido 50%
- Throughput 10,000+ → 50,000+ TPS (crítico para HFT forex)

**Implementation**:
```python
# exactor_accelerator/engine/optimizer.py (NUEVO)
class FormulaOptimizer:
    """Optimizador de fórmulas EXACTOR por dominio."""
    
    def compile_formula(self, formula: str, domain: str) -> Callable:
        """Compila fórmula a código nativo específico del dominio."""
        # Usar numba o Cython para compilación JIT
        from numba import jit
        
        @jit(nopython=True)
        def compiled_formula(features):
            # Compilar fórmula a código nativo optimizado para dominio
            if domain == "forex":
                # Optimizaciones específicas para forex
                pass
            elif domain == "fraud":
                # Optimizaciones específicas para fraude
                pass
            # ... otros dominios
            pass
        
        return compiled_formula
    
    def cache_predictions(self, clf, cache_size: int = 10000, domain: str = "general"):
        """Cache de predicciones para inputs repetitivos específicos del dominio."""
        from functools import lru_cache
        
        @lru_cache(maxsize=cache_size)
        def cached_predict(state_hash):
            return clf._predict_uncached(state_hash)
        
        return cached_predict
```

**Timeline**: 2 semanas  
**Prioridad**: ALTA  
**Dependencias**: numba

---

### 3.2 Batch Processing para Monitoreo de Sensores

**Problema Actual**:
- Monitoreo de calidad requiere procesar 10,000+ sensores simultáneamente
- Procesamiento individual puede ser ineficiente
- Necesario procesamiento por lotes optimizado

**Improvement v2.0**:
- Implementar batch prediction vectorizado
- Paralelización por dominio de sensores
- Streaming processing para tiempo real

**Impacto Esperado**:
- Throughput 10,000+ → 50,000+ TPS para monitoreo
- Latency mantenida en 0.05-0.1ms por sensor
- Escalabilidad horizontal para miles de sensores

**Implementation**:
```python
# exactor_accelerator/engine/batch_processor.py (NUEVO)
class BatchProcessor:
    """Procesador por lotes para monitoreo de sensores."""
    
    def __init__(self, clf, batch_size: int = 1000):
        self.clf = clf
        self.batch_size = batch_size
    
    def predict_batch(self, df: pd.DataFrame) -> pd.Series:
        """Predice en batch para alto throughput."""
        predictions = []
        
        for i in range(0, len(df), self.batch_size):
            batch = df.iloc[i:i + self.batch_size]
            batch_pred = self.clf.predict(batch)
            predictions.extend(batch_pred)
        
        return pd.Series(predictions)
    
    def predict_stream(self, stream: Iterator[Dict[str, Any]]) -> Iterator[str]:
        """Predice en streaming para tiempo real."""
        for state in stream:
            yield self.clf.predict(pd.DataFrame([state]))[0]
```

**Timeline**: 2 semanas  
**Prioridad**: ALTA  
**Dependencias**: Ninguna

---

## Fase 4: UX por Domain (MEDIUM Priority)

### 4.1 Dashboards Específicos por Nicho

**Problema Actual**:
- No hay interfaz visual
- Difícil monitorear performance en producción
- No hay métricas específicas por dominio

**Improvement v2.0**:
- Dashboard web con Streamlit para cada dominio
- Metrics específicas: accuracy, latencia, throughput, falsos negativos
- Alertas configurables por dominio

**Impacto Esperado**:
- Monitoreo en tiempo real de performance
- Detección temprana de degradación
- Mejor experiencia de usuario por dominio

**Implementation**:
```python
# exactor_accelerator/dashboard/fraud_dashboard.py (NUEVO)
import streamlit as st

st.title("Exactor Accelerator - Detección de Fraude")

# Metrics específicas de fraude
col1, col2, col3, col4 = st.columns(4)
col1.metric("Accuracy", "98.5%", "+0.5%")
col2.metric("Latency", "0.08ms", "-0.02ms")
col3.metric("Throughput", "12,500 TPS", "+2,500")
col4.metric("False Negatives", "0", "0")

# Gráficos específicos de fraude
st.line_chart(fraud_history)
st.bar_chart(fraud_by_country)
```

**Timeline**: 3 semanas  
**Prioridad**: MEDIA  
**Dependencias**: streamlit

---

### 4.2 CLI por Domain

**Problema Actual**:
- No hay CLI para entrenamiento y despliegue
- Difícil automatizar workflows
- Barrera de entrada para usuarios no técnicos

**Improvement v2.0**:
- CLI específico por dominio con comandos preconfigurados
- Templates de configuración por dominio
- Integración con CI/CD

**Impacto Esperado**:
- Adopción más fácil
- Menor barrera de entrada
- Automatización de workflows

**Implementation**:
```python
# exactor_accelerator/cli.py (NUEVO)
import click

@click.group()
def cli():
    """Exactor Accelerator CLI - Herramienta de línea de comandos."""
    pass

@cli.command()
@click.option('--domain', required=True, help='Domain: fraud, medical, forex, manufacturing, security')
@click.option('--data', required=True, help='Path to training data')
@click.option('--target', required=True, help='Target column')
@click.option('--output', required=True, help='Output model path')
def train(domain, data, target, output):
    """Entrena modelo Exactor Accelerator para un dominio específico."""
    df = pd.read_csv(data)
    clf = ExactorAcceleratorClassifier(domain=domain)
    clf.fit(df.drop(target, axis=1), df[target])
    clf.save_model(output)
    click.echo(f"Model saved to {output}")

@cli.command()
@click.option('--domain', required=True, help='Domain: fraud, medical, forex, manufacturing, security')
@click.option('--model', required=True, help='Path to model')
@click.option('--input', required=True, help='Input data')
def predict(domain, model, input):
    """Predice usando modelo para un dominio específico."""
    clf = ExactorAcceleratorClassifier(domain=domain)
    clf.load_model(model)
    df = pd.read_csv(input)
    predictions = clf.predict(df)
    click.echo(predictions.to_csv())
```

**Timeline**: 2 semanas  
**Prioridad**: MEDIA  
**Dependencias**: click

---

## Resumen de Roadmap (Enfoque en Nichos)

### Fase 1: Adaptabilidad Dinámica en Nichos (4 semanas)
- 1.1 Detector de Regímenes por Domain (2 semanas, ALTA)
- 1.2 Motor de Features por Domain (2 semanas, ALTA)

### Fase 2: Cold Start para Nichos (5 semanas)
- 2.1 Modo Cold Start por Domain (3 semanas, ALTA)
- 2.2 Primitivas JEV para Nichos Específicos (2 semanas, MEDIA)

### Fase 3: Performance Extremo para Nichos (4 semanas)
- 3.1 Optimización para HFT y Monitoreo en Tiempo Real (2 semanas, ALTA)
- 3.2 Batch Processing para Monitoreo de Sensores (2 semanas, ALTA)

### Fase 4: UX por Domain (5 semanas)
- 4.1 Dashboards Específicos por Nicho (3 semanas, MEDIA)
- 4.2 CLI por Domain (2 semanas, MEDIA)

**Total**: ~18 semanas (4.5 meses)

---

## Priorización Recomendada

### v2.0 MVP (2.5 meses)
- Fase 1: Adaptabilidad Dinámica en Nichos (4 semanas)
- Fase 2: Cold Start para Nichos (5 semanas)

**Impacto**: +15-25% accuracy en extreme regimes, cold start funcional 70-85% accuracy inicial

### v2.1 (1.5 meses)
- Fase 3: Performance Extremo para Nichos (4 semanas)

**Impacto**: Latency 0.05-0.1ms → 0.01-0.05ms, throughput 10,000+ → 50,000+ TPS

### v2.2 (1.5 meses)
- Fase 4: UX por Domain (5 semanas)

**Impacto**: Dashboards específicos, CLI por dominio, mejor adopción

---

## Success Metrics

### v2.0 MVP
- Accuracy extreme regimes: +15-25% (forex, fraude)
- Cold start: N/A → 70-85% accuracy inicial (todos los nichos)
- Adaptabilidad: Detecta concept drift automáticamente en nichos actuales
- Features especializados: +5-10% accuracy en nichos actuales

### v2.1
- Latency: 0.05-0.1ms → 0.01-0.05ms (2-10x más rápido)
- Throughput: 10,000+ → 50,000+ TPS (crítico para HFT forex)
- Memory usage: Reducido 50%
- Batch processing: Escalabilidad horizontal para miles de sensores

### v2.2
- Dashboards: Monitoreo en tiempo real por dominio
- CLI: Automatización de workflows por dominio
- Adopción: Menor barrera de entrada para usuarios no técnicos

---

## Conclusion

**Exactor Accelerator v2.0** perfeccionará los nichos donde ya es insuperable (fraude, médico, manufactura, seguridad, forex) en lugar de intentar ser algo para todos.

**Estrategia**: Enfocarse en adaptabilidad, cold start, performance extremo, y UX específica por dominio.

**Will NOT focus on**: NLP complejo, zero-shot general, >10 clases, documentos largos (donde pierde vs alternativas).

**Prioridad**: Implementar Fase 1 y Fase 2 primero (adaptabilidad + cold start) para máximo impacto en menor tiempo.

**Timeline**: 2.5 meses para MVP v2.0, 4.5 meses para v2.0 completo.

**Resultado**: Exactor Accelerator v2.0 será la solución definitiva para decisiones de alta velocidad en sus nichos de excelencia, con adaptabilidad dinámica, cold start funcional, y performance extremo.

---

**Generado por**: Cascade AI Assistant  
**Proyecto**: exactor-accelerator  
**Version**: 2.0  
**Last updated**: 22 de September de 2026
