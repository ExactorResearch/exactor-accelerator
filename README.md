# Exactor Accelerator: The Muscular Memory Layer for AI

[![License: MIT/Apache-2.0](https://img.shields.io/badge/License-MIT%2FApache--2.0-blue.svg)](#license)
[![Rust: 2024 Edition](https://img.shields.io/badge/Rust-2024%20Edition-orange.svg)](https://www.rust-lang.org/)
[![Inference Latency](https://img.shields.io/badge/Fast--Path-0.05ms-brightgreen.svg)](#performance-benchmarks)
[![Oracle Compatibility](https://img.shields.io/badge/Oracle-Jev%20%7C%20LLMs-purple.svg)](#architecture--how-it-works)
[![Explainability](https://img.shields.io/badge/Compliance-Glass%20Box%20(Boolean)-blue.svg)](#glass-box-explainability--regulatory-compliance)
[![PyPI Version](https://img.shields.io/pypi/v/exactor-accelerator.svg)](https://pypi.org/project/exactor-accelerator/)
[![Python Version](https://img.shields.io/pypi/pyversions/exactor-accelerator.svg)](https://pypi.org/project/exactor-accelerator/)

**Exactor Accelerator** compiles complex, slow, and expensive cloud AI reasoning into deterministic, sub-millisecond local boolean reflexes. 

By mirroring the biological transition between **System 2** (deliberative cognitive reasoning) and **System 1** (automated muscular memory), Exactor enables enterprise applications to resolve **99.9% of recurring decisions locally at hardware speed (0.05 ms) with zero marginal API cost**, delegating only true anomalies to cloud oracles.

> **Master Tagline:** *Exactor Accelerator: The muscle memory of your Artificial Intelligence.*  
> **Operational:** *0.05ms predictions. Zero marginal cost. Absolute transparency.*  
> **Contrast:** *Don't rent probabilities. Own your certainties.*  
> **Compliance:** *The only AI that delivers the decision and the causal proof simultaneously.*  
> **Data Science:** *Day 1 Data Science: Start with zero historical data, evolve in real time.*

---

## Interactive Live Demos

Explore Exactor Accelerator running in production environments. Each demo isolates a fundamental property of neuro-symbolic decision execution:

| Demo | Focus Area | Live Interactive App | Directory |
| :--- | :--- | :--- | :--- |
| **`exactor-waf-guardian`** | **Enterprise Cyber Defense**<br>Inspects HTTP payloads, mitigates SQLi/XSS/bot vectors in 0.05 ms, and emits causal boolean proof certificates per blocked request. | [Launch WAF Guardian](https://waf.exactor.ai) | [`../exactor-waf-guardian`](../exactor-waf-guardian) |
| **`exactor-sudoku-arena`** | **Deterministic Constraint Satisfaction (CSP)**<br>Demonstrates zero-hallucination logical deduction vs. probabilistic LLM token guessing on NP-complete grids. | [Launch Sudoku Arena](https://sudoku.exactor.ai) | [`../exactor-sudoku-arena`](../exactor-sudoku-arena) |
| **`exactor-minesweeper`** | **System 1 vs. System 2 in Real Time**<br>Clears 95%+ of deterministic tiles locally at CPU speed; escalates ambiguous 50/50 board states to the cloud oracle and compiles the resolution. | [Launch Minesweeper](https://minesweeper.exactor.ai) | [`../exactor-minesweeper`](../exactor-minesweeper) |

---

## The Problem: The Inefficiency of Cloud Inference

Current decision systems built on LLMs or cloud-hosted decision models face three operational bottlenecks:

1. **Linear Token Costs (The CFO):** Evaluating millions of real-time events (payment authorizations, web requests, log streams) creates a directly linear API cost curve. Scaling AI in production becomes financially unsustainable.
2. **Network & Compute Latency (The CTO / Ops):** Cloud roundtrips of 500 ms to 1,200 ms breach latency Service Level Agreements (SLAs) in edge computing, payment fraud mitigation, and high-throughput routing.
3. **Black-Box Opacity (The Chief Compliance Officer / CCO):** Probabilistic models and deep neural nets output confidence scores, not causal justifications, conflicting with regulatory compliance frameworks (**EU AI Act, GDPR Article 22, HIPAA, SOX, PCI-DSS**).

---

## 👔 Key Messaging by Buyer Persona

### For the Chief Technology Officer (CTO / CIO)
* **The Hook:** *"Stop sacrificing speed for intelligence."*
* **The Argument:** Exactor Accelerator gives you the reasoning depth of an advanced foundational model paired with the latency of a local script (0.05 ms). It maintains high availability offline if internet connectivity drops, installs via a simple `pip install` or `cargo add`, and provides native Scikit-Learn API compatibility (`.fit()`, `.predict()`).

### For the Chief Compliance / Legal Officer (CCO)
* **The Hook:** *"Mathematical audits, not probabilistic approximations."*
* **The Argument:** If a regulator audits your company tomorrow, conventional AI tools will deliver a statistical guess (like SHAP) of why a decision was made. Exactor delivers an absolute causal certificate. No black boxes, no hidden biases: compliance by design.

### For the Chief Financial Officer (CFO)
* **The Hook:** *"Decouple your business growth from your AI bill."*
* **The Argument:** We transform your variable operational expenditure (per-token/API billing) into a proprietary capital logic asset running at zero marginal cost. Fund AI to discover what is new, not to repeat what your systems already know.

---

## Architecture & How It Works

Exactor couples flexible cloud cognition with strict local boolean synthesis across four distinct architectural pillars:

```text
[ Incoming Telemetry / Event Stream ]
                 │
                 ▼
     [ Step 1: Perception Layer ]
   (Adaptive Binarization to Hypercube B^k)
                 │
        ┌────────┴────────┐
        ▼                 ▼
 [ Known Engram ]   [ Ambiguous / High Entropy ]
 (Fast-Path Hit)    (Cognitive Friction)
        │                 │
        │ 0.05 ms         ▼
        │          [ Step 2: Cloud Oracle ]
        │          (Jev / LLM Deliberation)
        │                 │
        │                 ▼
        │          [ Step 3: SQLite WAL Ledger ]
        │          (Concurrent Event Logging)
        │                 │
        │                 ▼
        │          [ Step 4: Exactor Core (Rust) ]
        │          (Hot Boolean Minimization)
        │                 │
        └────────┬────────┘
                 ▼
    [ Dual Deterministic Output ]
    1. Exact Decision (0.05 ms)
    2. Causal Boolean Formula
```

### 1. Perception Layer (Adaptive Binarization)
Continuous and categorical features are mapped onto discrete propositions over a boolean hypercube $\mathbb{B}^k$ (supporting up to 64 dimensions).

### 2. Cognitive Friction & Oracle Routing (System 2)
When an input vector falls outside established boolean boundaries (Cold-Start or elevated entropy), the router dispatches the case to an external cognitive oracle (such as **TypeSafe Jev** or a foundation LLM) for deliberation.

### 3. Living Memory Ledger (WAL)
Every resolved friction is stored concurrently in a high-throughput SQLite Write-Ahead Logging (`PRAGMA journal_mode=WAL;`) ledger without blocking the primary operational path.

### 4. Engram Consolidation & Fast-Path (System 1)
The **Exactor Core** engine (written in Rust) continuously minimizes truth tables using Quine-McCluskey and Espresso-style boolean reduction, pruning redundant variables (*Don't Care* states). Subsequent matching vectors execute directly in hot memory in **0.05 ms**.

### 5. Autonomous Epistemic Vigilance
The engine monitors real-time transaction entropy (Shannon entropy and multi-dimensional Z-scores). If production data exhibits *concept drift*, the local fast-path reflex is temporarily disengaged for that specific subspace, routing traffic back to the oracle until new invariants are synthesized.

---

## Performance Benchmarks

### High-Volume Evaluation Streams (1,000,000 Decisions)

| Metric | Traditional Cloud LLM | Cloud Decision API (Jev) | Exactor Accelerator (Fast-Path) |
| :--- | :--- | :--- | :--- |
| **p50 Latency** | 620 ms | 48 ms | **0.05 ms** (1,000x - 12,000x faster) |
| **p99 Latency** | 1,450 ms | 115 ms | **0.08 ms** |
| **Cost per 1M Events** | ~$2,000 – $15,000 | ~$100 – $400 | **~$0.10 – $0.40** (99.9% local resolution) |
| **Offline Resilience** | Zero (Fails on network drop) | Zero (Fails on network drop) | **100% Autonomous Local Uptime** |
| **Decision Explainability** | Opaque / Post-hoc SHAP | Probabilistic Score | **Exact Boolean Proof Certificate** |

### Side-by-Side Production Comparison

| Capability | Pure Cloud LLM | Traditional ML (XGBoost) | Exactor Accelerator Hybrid |
|---|---|---|---|
| **Zero-Data Cold-Start (Day 1)** | ✅ Yes (Cloud evaluation) | ❌ Impossible (Requires labeled data) | **✅ Yes (Immediate symbiosis)** |
| **Execution Latency** | 477 – 1,200 ms | 1 – 10 ms | **0.05 – 0.1 ms (Edge hardware speed)** |
| **Cost per 100M Decisions** | Linear token invoicing | Infrastructure compute cost | **$0.00 on Fast-Path (Radical savings)** |
| **Regulatory Explainability** | Free-form un-auditable text | Post-hoc approximations (SHAP) | **100% Exact Boolean Formulas (GDPR/HIPAA/SOX)** |
| **Offline High Availability** | ❌ Requires persistent connection | ✅ Yes | **✅ Yes (In-Memory Local)** |

---

## Quickstart

### Prerequisites
* Rust 1.80+ (`cargo`)
* Python 3.10+ (for Python library and bindings)

---

### Rust Engine Integration

Add Exactor Core to your `Cargo.toml`:

```toml
[dependencies]
exactor-core = { git = "https://github.com/ExactorResearch/exactor-accelerator" }
```

#### Basic Usage in Rust

```rust
use exactor_core::{Engine, FeatureVector, OracleClient};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize the engine with local storage and oracle fallback
    let mut engine = Engine::builder()
        .storage_path("./data/exactor_ledger.db")
        .oracle(OracleClient::new_jev(std::env::var("JEV_API_KEY")?))
        .build()?;

    // Feature vector representing incoming request
    let features = FeatureVector::from_slice(&[
        ("ip_reputation_low", true),
        ("payload_entropy_high", true),
        ("rate_limit_exceeded", false),
    ]);

    // Fast-path evaluation (0.05 ms) or oracle fallback
    let decision = engine.evaluate(&features)?;

    println!("Action: {:?}", decision.action);
    println!("Causal Proof: {}", decision.causal_proof);
    // Output: Causal Proof: (ip_reputation_low AND payload_entropy_high) -> BLOCK

    Ok(())
}
```

---

### Python Integration (Scikit-Learn Compatible)

#### Installation
```bash
pip install exactor-accelerator
```

#### Configuration
Set your tokens using environment variables, `.env` file, or programmatically:

```bash
export EXACTOR_CORE_TOKEN="your-token-here"
export JEV_API_KEY="your-jev-key"          # Optional: TypeSafe Jev API
export DEEPSEEK_API_KEY="your-key"          # Optional: LLM explainer
```

#### Scikit-Learn Compatible Python Workflow

```python
from exactor_accelerator import ExactorAcceleratorClassifier

# Initialize model with cloud oracle backend
clf = ExactorAcceleratorClassifier(
    oracle="jev",
    domain="fraud",
    fast_path=True,
)

# Start without pre-existing historical datasets
# Exactor learns on the fly and consolidates local rules
clf.fit(X_train, y_train)

# Real-time inference
prediction = clf.predict(X_live)
proof = clf.explain(X_live)

print(f"Decision: {prediction[0]} | Proof: {proof}")
```

#### Comprehensive Multi-Mode Quickstart (Unsupervised + Supervised + Cold-Start)

```python
import pandas as pd
from exactor_accelerator import (
    ExactorAccelerator,
    ExactorAcceleratorClassifier,
    get_feature_engine,
    get_regime_detector,
)

# 1. Raw stream data
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

---

## 🏝️ Topological Certainty Islands (Zero-Cost Guardrails & Formal Deductions)

> **"The Islands are the Theorems; the Domain is the Book or Chapter where they reside."**

A **Certainty Island** is a topological manifold where Shannon entropy collapses to zero ($H(X) \to 0$). When incoming data falls within a Certainty Island, the decision is **100% deterministic, executed in $<10\,\mu\text{s}$, cost-free ($0.00$), and mathematically proven**.

```python
from exactor_accelerator import certainty_guard

@certainty_guard(domain="financial", auto_veto=True, on_veto_raise=False)
def process_payment(amount: float, balance: float, **kwargs):
    # Only executes if all topological invariants pass (Solvency, Velocity, Sanctions)
    return ml_model.predict([amount, balance])

# Overdraft attempt ($5,000 > $200) is vetoed in 0.01 ms with zero ML inference cost:
result = process_payment(amount=5000.0, balance=200.0) # Returns None
```

👉 **Complete Guide:** [docs/CERTAINTY_ISLANDS_GUIDE.md](docs/CERTAINTY_ISLANDS_GUIDE.md)

---

## Glass Box Explainability & Regulatory Compliance

Unlike deep networks that rely on post-hoc heuristics (such as LIME or SHAP), Exactor provides **axiomatic transparency**:

$$\text{Decision}(X) = \bigvee_{i} \left( \bigwedge_{j} L_{i,j} \right) \oplus \bigoplus_{r} X_r$$

* **Zero Hallucinations:** Every output is bound to an evaluated canonical boolean formula.
* **Audit-Ready Evidence:** Each transaction record includes the exact logical formula invoked, satisfying traceability mandates under the **EU AI Act (High-Risk Classification Systems)**, **GDPR Article 22**, **HIPAA**, and **SOX**.

---

## ⚡ High-Impact Niches of Excellence

* **Real-Time Fraud Prevention**: Sub-millisecond local decisions complemented by Jev's adaptive cloud intelligence for complex edge cases (10,000+ TPS).
* **Emergency Medical Triage**: Immutable, deterministic audit trails certified and ready for HIPAA compliance.
* **Cybersecurity & SOC Automation**: Process 50,000+ events per second detecting anomalies and burst velocities at line rate.
* **Algorithmic Trading & HFT**: Microsecond execution for high-frequency signal validation with strict zero false negative risk controls.
* **Total Regulatory Compliance**: Every decision is explained by an exact mathematical formula (`IF ... AND ... OR ... NOT`), eliminating legal liability in automated decisions.

---

## Project Structure

```text
exactor-accelerator/
├── crates/                    # Rust Core Engine (2024 Edition)
│   ├── exactor-core/          # Hypercube minimization & SQLite WAL ledger
│   ├── exactor-oracle/        # Integrations with Jev, OpenAI, and Claude
│   └── exactor-python/        # PyO3 bindings for Scikit-Learn compatibility
├── exactor_accelerator/       # Python Package & Subsystems
│   ├── ingestion/             # Adaptive Binarizer to Hypercube B^k
│   ├── core/                  # Gray code & stack reduction engine
│   ├── adapter/               # Jev typed schema generator (Noul, Choice, Score)
│   ├── ledger/                # SQLite WAL high-concurrency memory ledger
│   ├── engine/                # Master HybridRuntime orchestrator
│   ├── api/                   # FastAPI REST Service & OpenAPI docs
│   └── web/                   # Cyber-Logic Glassmorphic telemetry dashboard
├── demos/                     # Production Interactive Demonstrations
│   ├── waf-guardian/          # Enterprise cyber defense & HTTP inspect demo
│   ├── sudoku-arena/          # Exact constraint satisfaction engine demo
│   └── minesweeper/           # System 1 reflex vs. System 2 deliberation demo
├── tests/                     # Automated unit and integration test suite
├── run_demo.py                # End-to-end interactive CLI demonstration
├── run_server.py              # Web dashboard & REST API server launcher
└── Cargo.toml                 # Multi-crate workspace specification
```

---

## Running the Demos Locally

### 1. Run Interactive CLI Demonstration
```bash
python run_demo.py
```

### 2. Launch Web Server & Control Dashboard
```bash
python run_server.py
```
* **Web Control Panel**: [http://localhost:8000](http://localhost:8000)
* **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Run Production Interactive App Demos
```bash
# WAF Guardian Simulation (Cyber Defense)
cargo run --release --bin exactor-waf-demo

# Sudoku Arena (Constraint Satisfaction)
cargo run --release --bin exactor-sudoku-demo

# Minesweeper (System 1 vs. System 2 in Real Time)
cargo run --release --bin exactor-minesweeper-demo
```

### 4. Run Automated Test Suite
```bash
python -m pytest tests/ -v
```

---

## REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/system/status` | Engine status, active rule version, and ledger record count |
| `POST` | `/api/ingest/file` | Upload CSV/JSON dataset and trigger logical discovery |
| `POST` | `/api/ingest/sample` | Instantly load sample datasets (fraud / sre / triage) |
| `GET` | `/api/exactor/rules` | Canonical boolean formulas distilled by Exactor |
| `GET` | `/api/jev/schema` | Calibrated typed question schema (`Noul`, `Choice`, `Score`) |
| `POST` | `/api/query` | Real-time query evaluation with fast-path and WAL logging |
| `GET` | `/api/ledger` | Stream audited interaction records from SQLite WAL |
| `POST` | `/api/ledger/feedback` | Inject human feedback / ground truth for a past query |
| `POST` | `/api/differential/update` | Trigger differential rule update over a sliding window |

---

## 📚 Documentation & Strategic Resources

* 💼 **[Commercial Narrative & Positioning Guide](docs/COMMERCIAL_POSITIONING_GUIDE.md)**: Executive B2B playbook for marketing, sales, and buyer personas (CFO, CTO, CCO).
* 📋 **[Executive Summary](docs/EXECUTIVE_SUMMARY.md)**: High-level overview of technical architecture and business ROI.
* 🔍 **[Why Exactor Accelerator](docs/WHY_EXACTOR_ACCELERATOR.md)**: In-depth technical rationale, production benchmarks, and architectural advantages.
* 🛠️ **[Domain Implementation Guide](docs/DOMAIN_IMPLEMENTATION_GUIDE.md)**: Production implementation guide across target niches (Fraud, Medical Triage, Forex, SOC Security).
* 🔬 **[Comparative Benchmark Report](docs/COMPARATIVE_BENCHMARK_REPORT.md)**: Empirical measurements of latency, throughput, and boolean determinism.

---

## License

Dual-licensed under either of:

* Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE))
* MIT license ([LICENSE](LICENSE))

at your option.

---

## 🏁 Call to Action

> **"Experience certainty on your own infrastructure. Start today with zero historical data and watch your system develop its own reflexes in real time."**
