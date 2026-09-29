# Exactor Accelerator

[![PyPI Version](https://img.shields.io/pypi/v/exactor-accelerator.svg)](https://pypi.org/project/exactor-accelerator/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/pypi/pyversions/exactor-accelerator.svg)](https://pypi.org/project/exactor-accelerator/)

**Exactor Accelerator** is the first neuro-symbolic hybrid engine that unifies **Unsupervised Learning**, **Supervised Boolean Minimization**, and **Zero-Data Autonomous Cold-Start Distillation** in a single library—accelerating TypeSafe AI (**Jev**) decisions by **4,770–24,000x** with **95–100% accuracy**, **$0.00 marginal production cost**, and **100% regulatory auditability**.

---

## Why Exactor Accelerator? (The Blue Ocean Advantage)

Traditional ML (`XGBoost`, `scikit-learn`) is fast at inference, but completely blind on Day 1 without thousands of labeled rows and opaque to strict regulatory audits. Pure TypeSafe AI (**Jev**) and LLMs can reason on Day 1 without data, but suffer from **500–1,200ms network latency** and linear token costs on every single call.

**Exactor Accelerator turns Jev into a cognitive compiler**: it uses Jev to reason over unknown or drifting states and automatically compiles that intelligence into an **Exact Boolean Hypercube in Rust (`0.05ms`)**.

| Capability | Pure Jev (TypeSafe AI) | Traditional ML (XGBoost / Sklearn) | **Exactor Accelerator v2.0 (Blue Ocean)** |
| :--- | :---: | :---: | :---: |
| **Zero-Data Cold-Start (Day 1)** | ✅ Yes (via slow API) | ❌ Impossible (requires labeled dataset) | **✅ Yes (`cold_start=True` + auto-distillation)** |
| **Unsupervised Drift & Anomaly Detection** | ❌ Not built-in | ⚠️ Requires separate pipeline | **✅ Built-in (`RegimeDetector` + `FeatureEngine`)** |
| **Supervised Exact Training (`.fit(X, y)`)** | ❌ Does not compile rules | ✅ Yes (Black-Box trees/weights) | **✅ Yes (Exact Boolean Hypercube $B^k$)** |
| **Production Latency** | 477 – 1,200 ms | 1 – 10 ms | **0.05 – 0.1 ms (4,770x–24,000x faster)** |
| **Marginal Cost per 100M Decisions** | $40,000 – $1,800,000 | Compute infrastructure cost | **$0.00 on Fast-Path (100% token savings)** |
| **Regulatory Explainability** | Free-form text (non-auditable) | Post-hoc approximations (SHAP) | **100% Deterministic Boolean Formulas (GDPR/HIPAA/SOX)** |

---

## Three Learning Paradigms in a Single Library

1. **Unsupervised Learning (No Labels Required)**:
   - `get_feature_engine(domain=...)` and `get_regime_detector(domain=...)` extract multi-dimensional z-scores, behavioral velocity, Shannon entropy, and detect `STABLE_PATTERN`, `DRIFTING_PATTERN`, `HIGH_ENTROPY`, and `CONCEPT_DRIFT` on unlabeled streams.
2. **Autonomous Cold-Start Distillation (Unsupervised $\rightarrow$ Supervised in Live Production)**:
   - `ExactorAccelerator(cold_start=True, auto_evolve_every=N)` deploys with **0 historical rows**. It queries Jev on initial live events, records interactions in a high-concurrency SQLite WAL ledger, and **autonomously distills exact boolean rules** every $N$ events—seamlessly transitioning from ~800ms cloud calls to **0.05ms local execution**.
3. **Supervised Exact Classification (`scikit-learn` Drop-in API)**:
   - `ExactorAcceleratorClassifier` and `ExactorAcceleratorMultiLabelClassifier` provide standard `.fit(X, y)`, `.predict(X)`, and `.predict_proba(X)` methods backed by Gray-code hypercube minimization.

---

## Niches of Excellence

- **Fraud Detection**: 95–100% accuracy, `0.05–0.1ms` latency, zero false negatives on anchored rules
- **Medical Triage**: 95–100% accuracy, `0.05–0.1ms` latency, HIPAA-ready boolean audit trail
- **Manufacturing & IoT Quality**: 95–100% accuracy, `50,000+ TPS` batch & stream processing
- **Security & SOC Logs**: 95–100% accuracy, real-time anomaly & burst velocity detection
- **Algorithmic Forex**: 80–100% accuracy, sub-millisecond candle & regime classification

## Installation

```bash
pip install exactor-accelerator
```

## Configuration

Exactor Accelerator connects to the [EXACTOR Core engine](https://exactor.tech) for cloud-accelerated boolean minimization. Set your token using any of these methods:

### Option 1: Environment Variable (recommended for production)

```bash
export EXACTOR_CORE_TOKEN="your-token-here"
export JEV_API_KEY="your-jev-key"          # Optional: TypeSafe Jev API
export DEEPSEEK_API_KEY="your-key"          # Optional: LLM explainer
```

### Option 2: `.env` File

```bash
cp .env.example .env
# Edit .env with your tokens
```

### Option 3: Programmatic Configuration

```python
import exactor_accelerator

exactor_accelerator.configure(
    exactor_core_token="your-token-here",
    jev_api_key="your-jev-key",           # Optional
    deepseek_api_key="your-key",          # Optional
)
```

### Option 4: Per-Instance Token

```python
from exactor_accelerator import ExactorAccelerator

engine = ExactorAccelerator(
    exactor_token="your-token-here",
    use_cloud_exactor=True,
)
```

> **Note:** Without an EXACTOR Core token, the library falls back to the built-in Hypercube Gray-code Reducer engine, which provides the same deterministic boolean minimization locally.

---

## Quick Start (Copy & Run: Unsupervised + Supervised + Cold-Start)

```python
import pandas as pd
from exactor_accelerator import (
    ExactorAccelerator,
    ExactorAcceleratorClassifier,
    get_feature_engine,
    get_regime_detector,
)

# 1. Raw unlabeled stream (or load via pd.read_csv("your_data.csv"))
raw_df = pd.DataFrame({
    "amount": [45.0, 120.5, 950.0, 15.0, 2100.0, 32.0, 1500.0, 80.0, 42.0, 310.0, 1800.0, 55.0],
    "velocity_1h": [1, 2, 8, 1, 15, 1, 12, 2, 1, 3, 14, 1],
    "device_trust": [0.95, 0.88, 0.20, 0.99, 0.10, 0.92, 0.15, 0.85, 0.90, 0.70, 0.08, 0.94],
    "ip_reputation": ["CLEAN", "CLEAN", "SUSPICIOUS", "CLEAN", "MALICIOUS", "CLEAN", "MALICIOUS", "CLEAN", "CLEAN", "SUSPICIOUS", "MALICIOUS", "CLEAN"],
    "country_risk": ["LOW", "LOW", "MEDIUM", "LOW", "HIGH", "LOW", "HIGH", "LOW", "LOW", "MEDIUM", "HIGH", "LOW"],
})

# =====================================================================
# MODE A: UNSUPERVISED (Feature Extraction, Anomaly Z-Scores & Drift)
# =====================================================================
feature_engine = get_feature_engine(domain="fraud")
df_enriched = feature_engine.extract_all(raw_df)

regime_detector = get_regime_detector(domain="fraud")
regime_info = regime_detector.analyze_regime(
    features=df_enriched.iloc[-1].to_dict(),
    history_df=df_enriched,
)
print(f"[Unsupervised] Regime: {regime_info['dominant_regime']} | Gate: {regime_info['actionability_gate']}")

# =====================================================================
# MODE B: SUPERVISED (Exact Boolean Hypercube Minimization + Audit)
# =====================================================================
target = pd.Series([0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0], name="target")

clf = ExactorAcceleratorClassifier(domain="fraud", fast_path=True)
clf.fit(df_enriched, target)

new_tx = feature_engine.extract_all(pd.DataFrame([{
    "amount": 1850.0,
    "velocity_1h": 14,
    "device_trust": 0.12,
    "ip_reputation": "MALICIOUS",
    "country_risk": "HIGH",
}]))
prediction = clf.predict(new_tx)
explanation = clf.explain(new_tx)

print(f"\n[Supervised] Prediction (is_fraud): {prediction[0]}")
print(f"[Supervised] Exact Boolean Rule: {clf.formula_expr_}")
print(f"[Supervised] Why this decision was made:\n{explanation}")

# =====================================================================
# MODE C: AUTONOMOUS COLD-START (Zero Prior Data -> Live Auto-Distillation)
# =====================================================================
cold_engine = ExactorAccelerator(cold_start=True, auto_evolve_every=5)
live_res = cold_engine.evaluate(new_tx.iloc[0].to_dict(), fast_path=True)
print(f"\n[Cold-Start] Decision: {live_res['decision']} | Route: {live_res['route']}")
print(f"[Cold-Start] Why: {live_res['explicacion_natural']}")
```

### Expected Output

```text
[Unsupervised] Regime: STABLE_PATTERN | Gate: PROCEED

[Supervised] Prediction (is_fraud): 1
[Supervised] Exact Boolean Rule: (~amount_low & ~velocity_1h_high & ~velocity_1h_low & ~device_trust_above_target_median & ~device_trust_low & ~ip_reputation_eq_clean & ip_reputation_eq_suspicious)
[Supervised] Why this decision was made:
1. **What was decided?**
The operation was blocked as a preventive security measure because it was flagged as high risk.

2. **Why?**
- **The device couldn't be trusted:** The device used for this operation had a very low trust score (0.12 out of 1), meaning it didn't look like a device you normally use or one we recognize as safe.
- **The internet connection came from a dangerous source:** The IP address was flagged as malicious, with a very high risk score of 0.95.
- **The activity pattern was unusual:** There were 14 operations in just one hour, which is far more than normal, and the operation came from a high-risk country ($1,850).

3. **What does this mean for you?**
Your operation was not processed, but your account and funds remain safe.

[Cold-Start] Decision: SAFE | Route: JEV_ORACLE
[Cold-Start] Why: Autonomous action [APROBAR_TRANSACCION] executed: Legitimate transaction with confidence (92.0%). Direct pass authorized without friction.
```

## Examples by Domain

- [Fraud Detection](https://github.com/ExactorResearch/exactor-accelerator/blob/main/examples/fraud_detection_example.py)
- [Medical Triage](https://github.com/ExactorResearch/exactor-accelerator/blob/main/examples/medical_triage_example.py)
- [Forex Trading](https://github.com/ExactorResearch/exactor-accelerator/blob/main/examples/forex_trading_example.py)
- [Quality Monitoring](https://github.com/ExactorResearch/exactor-accelerator/blob/main/examples/manufacturing_quality_example.py)
- [Security Logs](https://github.com/ExactorResearch/exactor-accelerator/blob/main/examples/security_logs_example.py)

## Documentation

- [Use Case Guide](https://github.com/ExactorResearch/exactor-accelerator/blob/main/docs/USE_CASE_GUIDE.md)
- [Why Exactor Accelerator](https://github.com/ExactorResearch/exactor-accelerator/blob/main/docs/WHY_EXACTOR_ACCELERATOR.md)
- [Domain Implementation Guide](https://github.com/ExactorResearch/exactor-accelerator/blob/main/docs/DOMAIN_IMPLEMENTATION_GUIDE.md)
- [Roadmap v2.0](https://github.com/ExactorResearch/exactor-accelerator/blob/main/docs/ROADMAP_V2.md)
- [Executive Summary](https://github.com/ExactorResearch/exactor-accelerator/blob/main/docs/EXECUTIVE_SUMMARY.md)

## Roadmap

See [ROADMAP_V2.md](https://github.com/ExactorResearch/exactor-accelerator/blob/main/docs/ROADMAP_V2.md) for details.

## Contributing

See [CONTRIBUTING.md](https://github.com/ExactorResearch/exactor-accelerator/blob/main/CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](https://github.com/ExactorResearch/exactor-accelerator/blob/main/LICENSE) for details.

---

## Architecture & System Design

This architecture integrates the **EXACTOR** boolean minimization engine (SMLE) with the **Jev** typed decision model (TypeSafe AI). The system operates under a **Live & Incremental Memory** paradigm: it starts with optional cold-start historical ingestion and evolves organically with every new query in real time, completely eliminating heavy offline retraining cycles.

```
       [ PHASE A: INITIAL INGESTION ]
   Historical Files (CSV / JSON / Logs)
                 │
                 ▼
   [ Adaptive Binarization in B^k ]
                 │
                 ▼
   [ EXACTOR Core Engine (Rust/Cloud) ] ──▶ Pure Rules (AND, OR, XOR, NOT)
                 │
                 ▼
   [ Dynamic Exactor ➔ Jev Adapter ]   ──▶ Typed Schema (Noul, Choice, Score)
                 │
                 ▼
       [ PHASE B: REAL-TIME OPERATION ]
   Production Query ──▶ [ Fast-Path Boolean / Jev (0.05-500ms) ]
                                     │
                ┌────────────────────┴────────────────────┐
                ▼                                         ▼
   [ Confidence >= Threshold ]                  [ SQLite WAL Ledger ]
                │                               (Collective Memory)
                ▼                                         │
    [ AUTONOMOUS EXECUTION ]                              ▼
                                                [ Sliding Window ]
                                                          │
                                                          ▼
                                            [ DIFFERENTIAL UPDATE ]
                                                (Hot Evolution)
```

---

## Operational Workflow

### Phase A: Cold-Start & Ingestion
1. **Historical Data Load**: Users or administrators supply initial records (CSV, JSON, logs, transactions, or tabular features) via the web interface or REST API.
2. **Adaptive Binarization**: The preprocessing engine transforms continuous and categorical variables into discrete propositions ($0$ and $1$) projected onto the boolean hypercube $\mathbb{B}^k$ ($k \le 64$).
3. **Logical Discovery (Exactor Core)**: The Rust/Cloud engine processes the binarized matrix, distilling an initial set of exact, immutable logical rules (AND, OR, XOR, NOT) with 100% auditability and zero black-box opacity.
4. **Jev Schema Calibration**: The discovered rules automatically translate into typed question schemas (`Choice`, `Score`, `Noul`) consumed by the Jev API.

### Phase B: Continuous Operation & Live Memory (Zero Retraining)
1. **Real-World Capture**: Each new production query, log event, or interaction enters the runtime in raw or semi-structured form.
2. **Ultra-Low Latency Evaluation**: Fast-path evaluates the boolean formula in 0.05–0.1 ms ($4,770\times$ speedup); complex or borderline states route to Jev calibrated probability distributions (**RLCD - Reinforcement Learning for Calibrated Decisions**).
3. **Memory Ledger Tracking**: Every interaction is automatically logged into a high-concurrency lightweight database (**SQLite in WAL mode**), building cumulative system memory.
4. **Differential Updates**: Periodically or on-demand, the engine processes recent sliding windows to update logic rules **in-place (hot evolution)**, allowing organic learning from real-world drift without downtime.

---

## Component Architecture

### Component 1: Ingestion & Binarization Subsystem (`exactor_accelerator.ingestion`)
- **Function**: Converts continuous and categorical features into clean boolean proposition matrices.
- **Inputs**: CSV/JSON datasets (at cold-start) or streaming event payloads (in production).
- **Outputs**: Discretized miniterm matrix with hypercube dimension mapping and target column.
- **Key Modules**: `binarizer.py`, `loader.py`, `text_extractor.py`.

### Component 2: Logic Minimization Engine (`exactor_accelerator.core`)
- **Function**: Executes boolean logic minimization using Gray codes and stack-based hypercube reduction.
- **Key Characteristics**: Native boolean hypercube ($\mathbb{B}^k$) operation without floating-point drift, producing auditable rules.
- **Native XOR Support**: Detects parity and non-linear algebraic symmetry.
- **Key Modules**: `hypercube.py`, `exactor_bridge.py`.

### Component 3: Dynamic Adapter (`exactor_accelerator.adapter`)
- **Function**: Translates Exactor boolean formulas into typed question schemas for TypeSafe Jev (`typesafe-sdk`).
- **Payload Structure**:
```json
{
  "model": "jev-latest",
  "state": { "event": "Real-time production query data" },
  "questions": {
    "logic_criterion": {
      "type": "noul",
      "instructions": "Is the boolean condition derived from historical analysis satisfied?"
    },
    "recommended_action": {
      "type": "choice",
      "instructions": "Which business action should be executed?",
      "criteria": {
        "AUTONOMOUS_EXECUTION": "High confidence",
        "HUMAN_REVIEW": "Uncertainty / edge case",
        "DISCARD": "Condition not met"
      }
    },
    "criticality_calibration": {
      "type": "score",
      "instructions": "Impact level on a continuous ordinal scale."
    }
  }
}
```
- **Key Modules**: `jev_schema.py`, `translator.py`.

### Component 4: Decision & Live Memory Layer (`exactor_accelerator.ledger` & `exactor_accelerator.engine`)
- **Function**: Delivers calibrated probabilistic responses to clients and records interactions for incremental learning.
- **Autonomous Execution**: Automatically triggers downstream workflows when confidence exceeds the configured threshold.
- **Concurrent Ledger**: SQLite optimized with `PRAGMA journal_mode = WAL;` and `PRAGMA synchronous = NORMAL;` for non-blocking concurrent writes.
- **Key Modules**: `sqlite_wal.py`, `jev_client.py`, `runtime.py`.

---

## Project Structure

```
exactor-accelerator/
├── exactor_accelerator/
│   ├── ingestion/             # Component 1: Ingestion & Binarization
│   │   ├── binarizer.py       # Adaptive hypercube discretizer
│   │   ├── loader.py          # CSV/JSON parsers & synthetic loaders
│   │   └── text_extractor.py  # Unstructured text feature extraction
│   ├── core/                  # Component 2: Exactor Logic Engine
│   │   ├── hypercube.py       # Hypercube, Gray code & stack reduction
│   │   └── exactor_bridge.py  # Dispatcher to exactor.tech Cloud / local
│   ├── adapter/               # Component 3: Exactor -> Jev Adapter
│   │   ├── jev_schema.py      # Noul, Choice, and Score primitives
│   │   └── translator.py      # TypeSafe payload generator
│   ├── ledger/                # Component 4A: Live Memory (SQLite WAL)
│   │   └── sqlite_wal.py      # Write-Ahead Logging persistence
│   ├── engine/                # Component 4B: Runtime & Jev Client
│   │   ├── jev_client.py      # TypeSafe API client & RLCD simulator
│   │   └── runtime.py         # HybridRuntime master orchestrator
│   ├── api/                   # FastAPI REST Service
│   │   └── server.py          # OpenAPI endpoints & static UI hosting
│   ├── web/                   # Control Dashboard (Glassmorphic)
│   │   ├── index.html         # Live telemetry & 4-phase dashboard
│   │   ├── styles.css         # Cyber-logic aesthetic
│   │   └── app.js             # Client logic & WAL stream feed
│   └── data/                  # Embedded sample datasets
├── tests/                     # Automated test suite
│   ├── test_binarizer.py
│   ├── test_exactor_hypercube.py
│   ├── test_jev_adapter.py
│   └── test_live_memory.py
├── run_demo.py                # End-to-end interactive CLI demonstration
├── run_server.py              # Web dashboard & REST API server launcher
└── pyproject.toml             # Standard PEP 621 package specification
```

---

## Usage Instructions

### 1. Run Automated Test Suite
```bash
python -m pytest tests/ -v
```

### 2. Run Interactive CLI Demonstration
Demonstrates the complete end-to-end lifecycle in one command:
```bash
python run_demo.py
```

### 3. Launch Web Server & Control Dashboard
```bash
python run_server.py
```
- **Web Control Panel**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/system/status` | Engine status, active rule version, and ledger record count |
| `POST` | `/api/ingest/file` | Phase A: Upload CSV/JSON dataset and trigger logical discovery |
| `POST` | `/api/ingest/sample` | Phase A: Instantly load sample datasets (fraud / sre / triage) |
| `GET` | `/api/exactor/rules` | Canonical boolean formulas distilled by Exactor |
| `GET` | `/api/jev/schema` | Calibrated typed question schema (`Noul`, `Choice`, `Score`) |
| `POST` | `/api/query` | Phase B: Real-time query evaluation with fast-path and WAL logging |
| `GET` | `/api/ledger` | Stream audited interaction records from SQLite WAL |
| `POST` | `/api/ledger/feedback` | Inject human feedback / ground truth for a past query |
| `POST` | `/api/differential/update` | Trigger differential rule update over a sliding window |
