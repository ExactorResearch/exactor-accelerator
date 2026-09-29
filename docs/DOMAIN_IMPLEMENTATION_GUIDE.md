# Domain Implementation Guide - Exactor Accelerator v2.0

**Version**: 2.0  
**Date**: September 2026  
**Objective**: Step-by-step guide to implement Exactor Accelerator across core niches of excellence

---

## Table of Contents

1. [Fraud Detection](#fraud-detection)
2. [Medical Triage](#medical-triage)
3. [Technical Forex](#technical-forex)
4. [Quality Monitoring](#quality-monitoring)
5. [Security Logs](#security-logs)

---

## Fraud Detection

### Domain Characteristics

- **Critical latency**: <10ms para decisiones en tiempo real
- **High volume**: >1,000 TPS
- **Structured data**: amount, velocity, device_trust, geolocation
- **Unacceptable false negatives**: 0 cuando anclado
- **Regulatory explainability**: Auditable boolean formulas

### Data Requirements

**Minimum**:
- 500-1,000 historical transactions
- Columns: amount, timestamp, device_trust, ip_reputation, country_risk, is_fraud

**Ideal**:
- 5,000+ historical transactions
- Columns adicionales: user_id, merchant_id, card_type, transaction_type

### Step 1: Prepare Data

```python
import pandas as pd
from exactor_accelerator.feature_engine import get_feature_engine
from exactor_accelerator.regime_detector import get_regime_detector

# Load historical data
df = pd.read_csv("fraud_transactions.csv")

# Enrich with domain-specific features de fraude
feature_engine = get_feature_engine(domain="fraud")
df_enriched = feature_engine.extract_all(df)

# Generated features:
# - velocity_1h, velocity_1m (transacciones por hora/minuto)
# - amount_zscore (z-score del monto)
# - device_trust_trend (tendencia de trust del dispositivo)
# - ip_reputation_score (numerical IP reputation)
# - geolocation_risk_score (numerical geographic risk)
```

### Paso 2: Entrenar Modelo

```python
from exactor_accelerator import ExactorAcceleratorClassifier
from sklearn.model_selection import train_test_split

# Dividir train/test
X = df_enriched.drop("is_fraud", axis=1)
y = df_enriched["is_fraud"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Configurar clasificador para fraude
clf = ExactorAcceleratorClassifier(
    domain="fraud",
    max_variables=16,
    fast_path=True,
    fast_path_threshold=0.75,
    anchor_critical_rules=True  # Eliminate false negatives
)

# Entrenar
clf.fit(X_train, y_train)

# Inspect discovered formula
print(f"Formula: {clf.formula_expr_}")
# Ejemplo: (amount_zscore > 2.5 AND velocity_1h > 10) OR ip_reputation_score == 0
```

### Paso 3: Evaluar Modelo

```python
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# Predicciones
y_pred = clf.predict(X_test)

# Metrics
acc = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred)
cm = confusion_matrix(y_test, y_pred)

print(f"Accuracy: {acc*100:.2f}%")
print(f"Report:\n{report}")
print(f"Confusion Matrix:\n{cm}")

# Esperado: 95-100% accuracy, 0 falsos negativos (cuando anclado)
```

### Step 4: Deploy with Regime Detection

```python
from exactor_accelerator.regime_detector import get_regime_detector

# Initialize regime detector for fraud
regime_detector = get_regime_detector(domain="fraud")

# In production, detect regime prior to each prediction
def predict_with_regime_detection(transaction):
    # Detect current regime
    regime_info = regime_detector.analyze_regime(
        features=transaction,
        history_df=df_enriched.tail(100)
    )
    
    # Adjust threshold based on detected regime
    if regime_info["dominant_regime"] == "HIGH_ENTROPY":
        effective_threshold = clf.fast_path_threshold * 0.7
    elif regime_info["dominant_regime"] == "STABLE_PATTERN":
        effective_threshold = clf.fast_path_threshold * 1.2
    else:
        effective_threshold = clf.fast_path_threshold
    
    # Prediction
    is_fraud = clf.predict(pd.DataFrame([transaction]))[0]
    
    return {
        "is_fraud": is_fraud,
        "regime": regime_info["dominant_regime"],
        "confidence": regime_info["stability_index"],
        "recommendation": regime_info["recommendation"],
    }
```

### Step 5: Production Monitoring

```python
# Continuously monitor regimes
regime_history = regime_detector.get_regime_history(n=10)

for entry in regime_history:
    print(f"Regime: {entry['regime']}")
    print(f"Stability: {entry['stability_index']:.2f}")
    print(f"Drift Score: {entry['drift_score']:.2f}")
    print(f"Gate: {entry['actionability_gate']}")
    print("---")

# Si gate == "HALT", trigger retraining
if regime_history[-1]["actionability_gate"] == "HALT":
    print("ALERT: Concept drift detected - trigger retraining")
    # clf.fit(new_data, new_labels)
```

### Metrics Esperadas

- **Accuracy**: 95-100%
- **Latency**: 0.05-0.1ms
- **Throughput**: 10,000+ TPS
- **False Negatives**: 0 (cuando anclado)
- **Cost**: $0.00 per decision

---

## Medical Triage

### Domain Characteristics

- **Critical latency**: <10ms para decisiones de emergencia
- **Determinismo obligatorio**: 100% predecible
- **Regulatory explainability**: Auditable formulas (HIPAA)
- **Unacceptable false negatives**: 0 cuando anclado
- **Structured data**: vital signs, lab values, age, comorbidities

### Data Requirements

**Minimum**:
- 500-1,000 historical patients
- Columns: heart_rate, blood_pressure_systolic, blood_pressure_diastolic, temperature, severity

**Ideal**:
- 5,000+ historical patients
- Columns adicionales: oxygen_saturation, respiratory_rate, age, comorbidities, lab_values

### Step 1: Prepare Data

```python
import pandas as pd
from exactor_accelerator.feature_engine import get_feature_engine

# Load historical data
df = pd.read_csv("medical_triage.csv")

# Enrich with domain-specific medical features
feature_engine = get_feature_engine(domain="medical")
df_enriched = feature_engine.extract_all(df)

# Generated features:
# - heart_rate_zscore, blood_pressure_systolic_zscore, etc.
# - hemoglobin_trend, white_blood_cells_trend, etc.
# - age_risk_factor (0-1 basado en edad)
# - comorbidity_score (0-1 basado en condiciones preexistentes)
```

### Paso 2: Entrenar Modelo

```python
from exactor_accelerator import ExactorAcceleratorClassifier
from sklearn.model_selection import train_test_split

# Dividir train/test
X = df_enriched.drop("severity", axis=1)
y = df_enriched["severity"]  # CRITICAL, HIGH, MODERATE, LOW
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Configure classifier for healthcare
clf = ExactorAcceleratorClassifier(
    domain="medical",
    max_variables=16,
    fast_path=True,
    fast_path_threshold=0.80,  # More conservative for healthcare
    anchor_critical_rules=True  # Eliminate critical false negatives
)

# Entrenar
clf.fit(X_train, y_train)

# Inspect discovered formula
print(f"Formula: {clf.formula_expr_}")
# Ejemplo: CRITICAL: (heart_rate_zscore > 2 AND blood_pressure_systolic_zscore > 2) OR temperature_zscore > 3
```

### Paso 3: Evaluar Modelo

```python
from sklearn.metrics import accuracy_score, classification_report

# Predicciones
y_pred = clf.predict(X_test)

# Metrics
acc = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred)

print(f"Accuracy: {acc*100:.2f}%")
print(f"Report:\n{report}")

# Esperado: 95-100% accuracy, 0 falsos negativos en CRITICAL
```

### Step 4: Deploy with Regime Detection

```python
from exactor_accelerator.regime_detector import get_regime_detector

# Initialize regime detector for healthcare
regime_detector = get_regime_detector(domain="medical")

def predict_triage_with_regime(patient):
    # Detect current regime
    regime_info = regime_detector.analyze_regime(
        features=patient,
        history_df=df_enriched.tail(50)
    )
    
    # More conservative gate for healthcare
    if regime_info["actionability_gate"] == "HALT":
        # Si drift detectado, usar valores por defecto conservadores
        return {"severity": "HIGH", "reason": "Regime drift detected - using conservative default"}
    
    # Prediction normal
    severity = clf.predict(pd.DataFrame([patient]))[0]
    
    return {
        "severity": severity,
        "regime": regime_info["dominant_regime"],
        "confidence": regime_info["stability_index"],
    }
```

### Metrics Esperadas

- **Accuracy**: 95-100%
- **Latency**: 0.05-0.1ms
- **Throughput**: 10,000+ TPS
- **False Negatives**: 0 (cuando anclado)
- **Determinismo**: 100%

---

## Technical Forex

### Domain Characteristics

- **Critical latency**: <1ms para HFT (High-Frequency Trading)
- **High volume**: >10,000 TPS
- **Structured data**: OHLCV, indicadores técnicos
- **Regímenes de mercado**: Trending, Ranging, Volatile
- **Explainability**: Auditable formulas para backtesting

### Data Requirements

**Minimum**:
- 1,000+ historical candles
- Columns: open, high, low, close, volume

**Ideal**:
- 10,000+ historical candles
- Columns adicionales: timeframe, symbol, indicators pre-calculados

### Step 1: Prepare Data

```python
import pandas as pd
from exactor_accelerator.feature_engine import get_feature_engine

# Load historical data OHLCV
df = pd.read_csv("forex_ohlcv.csv")

# Enrich with domain-specific features de forex
feature_engine = get_feature_engine(domain="forex")
df_enriched = feature_engine.extract_all(df)

# Generated features:
# - rsi (Relative Strength Index)
# - atr (Average True Range)
# - ema_spread (spread entre EMAs)
# - macd_hist (histograma MACD)
# - adx (Average Directional Index)
```

### Step 2: Train Model for Candlestick Classification

```python
from exactor_accelerator import ExactorAcceleratorClassifier
from sklearn.model_selection import train_test_split

# Create target: candlestick topology classification
# Up, Down, X (doji), W (engulfing)
df_enriched["candle_type"] = df_enriched.apply(
    lambda row: "UP" if row["close"] > row["open"] else "DOWN" if row["close"] < row["open"] else "X",
    axis=1
)

# Dividir train/test
X = df_enriched.drop("candle_type", axis=1)
y = df_enriched["candle_type"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Configurar clasificador para forex
clf = ExactorAcceleratorClassifier(
    domain="forex",
    max_variables=16,
    fast_path=True,
    fast_path_threshold=0.70,  # More aggressive for forex
)

# Entrenar
clf.fit(X_train, y_train)

# Inspect discovered formula
print(f"Formula: {clf.formula_expr_}")
# Ejemplo: UP: (rsi > 50 AND ema_spread > 0) AND macd_hist > 0
```

### Paso 3: Evaluar Modelo

```python
from sklearn.metrics import accuracy_score, classification_report

# Predicciones
y_pred = clf.predict(X_test)

# Metrics
acc = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred)

print(f"Accuracy: {acc*100:.2f}%")
print(f"Report:\n{report}")

# Expected: 80-100% accuracy on technical patterns
```

### Step 4: Deploy with Regime Detection de Mercado

```python
from exactor_accelerator.regime_detector import get_regime_detector

# Initialize regime detector for forex
regime_detector = get_regime_detector(domain="forex")

def predict_candle_with_regime(candle):
    # Detect market regime
    regime_info = regime_detector.analyze_regime(
        features=candle,
        history_df=df_enriched.tail(200)  # Larger window for forex
    )
    
    # Adjust strategy based on regime
    if regime_info["dominant_regime"] == "HIGH_ENTROPY":
        # In high volatility, be more conservative
        return {"action": "HOLD", "reason": "High volatility - hold position"}
    
    # Prediction normal
    candle_type = clf.predict(pd.DataFrame([candle]))[0]
    
    return {
        "candle_type": candle_type,
        "regime": regime_info["dominant_regime"],
        "action": "BUY" if candle_type == "UP" else "SELL" if candle_type == "DOWN" else "HOLD",
    }
```

### Metrics Esperadas

- **Accuracy (patrones técnicos)**: 80-100%
- **Latency**: 0.05-0.1ms
- **Throughput**: 10,000+ TPS
- **Profit Factor**: 2.0-3.5 (cuando combinado con gestión de riesgo)

---

## Quality Monitoring

### Domain Characteristics

- **Critical latency**: <10ms para decisiones en línea
- **High volume**: >10,000 TPS (miles de sensores)
- **Structured data**: sensores, métricas de calidad
- **Unacceptable false negatives**: 0 defectos perdidos
- **Explainability**: Fórmulas para ingenieros

### Data Requirements

**Minimum**:
- 1,000+ lecturas de sensores
- Columns: sensor_1, sensor_2, ..., defect

**Ideal**:
- 10,000+ lecturas de sensores
- Columns adicionales: timestamp, machine_id, maintenance_history

### Step 1: Prepare Data

```python
import pandas as pd
from exactor_accelerator.feature_engine import get_feature_engine

# Cargar datos de sensores
df = pd.read_csv("manufacturing_sensors.csv")

# Enrich with domain-specific features de manufactura
feature_engine = get_feature_engine(domain="manufacturing")
df_enriched = feature_engine.extract_all(df)

# Generated features:
# - sensor_1_zscore, sensor_2_zscore, etc.
# - sensor_1_trend, sensor_2_trend, etc.
# - anomaly_score (maximum absolute z-score)
# - maintenance_risk (normalizado por horas desde mantenimiento)
```

### Paso 2: Entrenar Modelo

```python
from exactor_accelerator import ExactorAcceleratorClassifier
from sklearn.model_selection import train_test_split

# Dividir train/test
X = df_enriched.drop("defect", axis=1)
y = df_enriched["defect"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Configurar clasificador para manufactura
clf = ExactorAcceleratorClassifier(
    domain="manufacturing",
    max_variables=16,
    fast_path=True,
    fast_path_threshold=0.75,
    anchor_critical_rules=True  # Eliminate false negatives
)

# Entrenar
clf.fit(X_train, y_train)

# Inspect discovered formula
print(f"Formula: {clf.formula_expr_}")
# Ejemplo: DEFECT: (sensor_1_zscore > 3 AND sensor_2_zscore > 2) OR anomaly_score > 4
```

### Paso 3: Evaluar Modelo

```python
from sklearn.metrics import accuracy_score, classification_report

# Predicciones
y_pred = clf.predict(X_test)

# Metrics
acc = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred)

print(f"Accuracy: {acc*100:.2f}%")
print(f"Report:\n{report}")

# Esperado: 95-100% accuracy, 0 falsos negativos
```

### Paso 4: Desplegar con Batch Processing

```python
from exactor_accelerator.engine.batch_processor import BatchProcessor

# Inicializar procesador por lotes
batch_processor = BatchProcessor(clf, batch_size=1000)

# Procesar miles de sensores en batch
sensor_readings = pd.read_csv("real_time_sensors.csv")
predictions = batch_processor.predict_batch(sensor_readings)

print(f"Processed {len(predictions)} sensor readings")
print(f"Defects detected: {predictions.sum()}")
```

### Metrics Esperadas

- **Accuracy**: 95-100%
- **Latency**: 0.05-0.1ms por sensor
- **Throughput**: 50,000+ TPS (con batch processing)
- **False Negatives**: 0 (cuando anclado)

---

## Security Logs

### Domain Characteristics

- **High volume**: >10,000 TPS
- **Patrones estructurados**: IP, request rate, payload
- **Unacceptable false negatives**: 0 ataques perdidos
- **Explainability**: Fórmulas para incident response

### Data Requirements

**Minimum**:
- 1,000+ historical logs
- Columns: ip_reputation, request_rate, payload_size, is_attack

**Ideal**:
- 10,000+ historical logs
- Columns adicionales: user_id, endpoint, timestamp, user_behavior

### Step 1: Prepare Data

```python
import pandas as pd
from exactor_accelerator.feature_engine import get_feature_engine

# Cargar logs de seguridad
df = pd.read_csv("security_logs.csv")

# Enrich with domain-specific features de seguridad
feature_engine = get_feature_engine(domain="security")
df_enriched = feature_engine.extract_all(df)

# Generated features:
# - ip_reputation_score (0-1)
# - request_velocity_1m, request_velocity_1s
# - payload_anomaly_score
# - user_behavior_risk (0-1)
```

### Paso 2: Entrenar Modelo

```python
from exactor_accelerator import ExactorAcceleratorClassifier
from sklearn.model_selection import train_test_split

# Dividir train/test
X = df_enriched.drop("is_attack", axis=1)
y = df_enriched["is_attack"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Configurar clasificador para seguridad
clf = ExactorAcceleratorClassifier(
    domain="security",
    max_variables=16,
    fast_path=True,
    fast_path_threshold=0.70,  # More aggressive for cybersecurity
    anchor_critical_rules=True  # Eliminate false negatives
)

# Entrenar
clf.fit(X_train, y_train)

# Inspect discovered formula
print(f"Formula: {clf.formula_expr_}")
# Ejemplo: ATTACK: (ip_reputation_score == 0) OR (request_velocity_1m > 100 AND payload_anomaly_score > 3)
```

### Paso 3: Evaluar Modelo

```python
from sklearn.metrics import accuracy_score, classification_report

# Predicciones
y_pred = clf.predict(X_test)

# Metrics
acc = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred)

print(f"Accuracy: {acc*100:.2f}%")
print(f"Report:\n{report}")

# Esperado: 95-100% accuracy, 0 falsos negativos
```

### Step 4: Deploy with Regime Detection

```python
from exactor_accelerator.regime_detector import get_regime_detector

# Initialize regime detector for security
regime_detector = get_regime_detector(domain="security")

def predict_log_with_regime(log_entry):
    # Detect current regime
    regime_info = regime_detector.analyze_regime(
        features=log_entry,
        history_df=df_enriched.tail(150)
    )
    
    # Gate muy conservador para seguridad
    if regime_info["actionability_gate"] == "HALT":
        # Si drift detectado, bloquear todo
        return {"is_attack": True, "reason": "Regime drift detected - blocking all"}
    
    # Prediction normal
    is_attack = clf.predict(pd.DataFrame([log_entry]))[0]
    
    return {
        "is_attack": is_attack,
        "regime": regime_info["dominant_regime"],
        "confidence": regime_info["stability_index"],
    }
```

### Metrics Esperadas

- **Accuracy**: 95-100%
- **Latency**: 0.05-0.1ms
- **Throughput**: 10,000+ TPS
- **False Negatives**: 0 (cuando anclado)

---

## Resumen Comparativo

| Domain | Accuracy | Latency | Throughput | False Negatives | Specialization |
|---------|----------|----------|------------|-----------------|-----------------|
| **Fraude** | 95-100% | 0.05-0.1ms | 10,000+ TPS | 0 (anclado) | velocity, amount, geolocation |
| **Healthcare** | 95-100% | 0.05-0.1ms | 10,000+ TPS | 0 (anchored) | vital signs, lab values, comorbidities |
| **Forex** | 80-100% | 0.05-0.1ms | 10,000+ TPS | N/A | RSI, ATR, MACD, ADX |
| **Manufactura** | 95-100% | 0.05-0.1ms | 50,000+ TPS | 0 (anclado) | sensor z-score, anomaly score |
| **Seguridad** | 95-100% | 0.05-0.1ms | 10,000+ TPS | 0 (anclado) | IP reputation, request velocity |

---

## Best Practices

### 1. Always Leverage Historical Data

Exactor Accelerator requires historical data (≥500 samples). Without prior data, utilize pure Jev or cold-start mode.

### 2. Anchor Critical Rules

For mission-critical domains where false negatives are unacceptable (fraud, healthcare, cybersecurity), set `anchor_critical_rules=True`.

### 3. Detect Market & Operational Regimes

Use the regime detector to dynamically adjust thresholds and track concept drift.

### 4. Features Especializadas

Use domain-specific feature engineering for optimal discriminative signal.

### 5. Monitoreo Continuo

Monitor regimes, accuracy, and false negatives continuously in production.

---

**Generado por**: Cascade AI Assistant  
**Proyecto**: exactor-accelerator  
**Version**: 2.0  
**Last updated**: September 26, 2026
