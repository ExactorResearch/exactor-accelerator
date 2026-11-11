# Exactor Accelerator

**Compile your recurring AI decisions into deterministic local Boolean reflexes — and keep a cloud LLM only for the cases that are actually ambiguous.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](#license)
[![PyPI Version](https://img.shields.io/pypi/v/exactor-accelerator.svg)](https://pypi.org/project/exactor-accelerator/)
[![Python Version](https://img.shields.io/pypi/pyversions/exactor-accelerator.svg)](https://pypi.org/project/exactor-accelerator/)
[![Tests](https://img.shields.io/badge/tests-59%20passed%2C%201%20skipped-brightgreen.svg)](#development)

Exactor Accelerator is a **neuro-symbolic decision engine** for Python. It learns the *shape* of your past decisions as exact Boolean formulas (hypercube minimization), evaluates them locally at microsecond latency with zero API cost, and escalates only genuinely ambiguous events to a cloud oracle such as [TypeSafe AI Jev](https://api.typesafe.ai) or any OpenAI-compatible LLM.

> **The idea in one sentence:** most production AI decisions are repetitive. Learn them once as exact rules, run them forever on CPU — and spend oracle tokens only on what the rules cannot decide.

---

## Why

Cloud LLMs and decision APIs are good at open-ended reasoning and bad at high-volume repetition:

| Pain | Consequence |
|---|---|
| Per-token / per-call pricing | Cost grows linearly with traffic |
| Network roundtrips | 0.5–1.5 s latency breaks edge/payment SLAs |
| Probabilistic outputs | Hard to audit under GDPR Art. 22, HIPAA, SOX |

Exactor Accelerator inverts the economics: **decisions that repeat become free, deterministic, and auditable; the expensive oracle is reserved for novelty.**

---

## Architecture

```
Event ──► Adaptive Binarization (features → Boolean propositions on B^k, k ≤ 64)
            │
            ├─ Fast-path hit ──► Local Boolean formula ──► Decision + causal proof   (~µs, $0)
            │
            └─ Ambiguous ──────► Oracle (Jev / LLM) ──► Decision
                                     │
                                     ▼
                              SQLite WAL ledger ──► future rule consolidation
```

- **Phase A (fit):** ingests labeled examples, discovers Boolean propositions, minimizes the decision function into DNF terms (Quine–McCluskey / Espresso-style reduction with don't-care handling).
- **Phase B (evaluate):** hot-path formula evaluation; optionally escalates low-certainty cases to the oracle.
- **Certainty Islands:** declarative guard rules (`@certainty_guard`) that veto unsafe decisions before any model runs.
- **Engines:** optional EXACTOR Cloud minimization, optional native Rust `exactor` binding (verified before use), always-available local Python hypercube engine.

---

## Honest performance numbers

Measured, reproducible results — see [`docs/BENCHMARK_RESULTS.md`](docs/BENCHMARK_RESULTS.md) for methodology and raw JSON.

### Structured/tabular decisions (the design target)

Synthetic fraud dataset with a known Boolean ground truth (300 train / 100 test):

| Metric | Jev (pure oracle) | Exactor fast-path |
|---|---|---|
| Accuracy | 56.7% | **78.0%** |
| Mean latency | 1256 ms | **13.1 ms (~96× faster)** |
| Network required | Always | Never |

*Note: 78% reflects the learned formula's approximation of the hidden rule — accuracy depends on how well binarization captures the decision boundary. With propositions that match the true rule structure, the engine can represent the exact function.*

### Unstructured NLP (honest limitation)

Public datasets, 500 train / 200 test samples, Jev evaluated on a 30-sample subset:

| Dataset | Exactor accuracy | Jev accuracy | Exactor latency | Jev latency |
|---|---|---|---|---|
| SST-2 (sentiment) | 54.0% | **96.7%** | 5.9 ms | 1179 ms |
| AG News (4 classes) | 22.0% | 20.0% | 13.5 ms | 1179 ms |
| Banking77 (70 classes) | 8.5% | 0.0%* | 109 ms | 1140 ms |

\* Jev was only offered 5 of 70 classes (cost-limited benchmark) — not a fair comparison.

**Takeaway:** on raw text classification, a cloud LLM oracle wins on accuracy while Exactor wins on speed/cost. Exactor Accelerator is designed for **structured or semi-structured decisions** (fraud rules, triage policies, WAF matrices, SLA routing) — not as a general NLP classifier.

---

## Quickstart

```bash
pip install exactor-accelerator
```

```python
import pandas as pd
from exactor_accelerator import ExactorAcceleratorClassifier

# Structured events: numeric/categorical features + a target label
df = pd.DataFrame({
    "amount":      [45.0, 120.5, 950.0, 15.0, 2100.0],
    "velocity_1h": [1, 2, 8, 1, 15],
    "device_trust":[0.95, 0.88, 0.20, 0.99, 0.10],
})
y = pd.Series([0, 0, 1, 0, 1])

clf = ExactorAcceleratorClassifier(domain="fraud", fast_path=True)
clf.fit(df, y)

# Local inference — no network call
pred = clf.predict(df.iloc[[2]])
print(clf.formula_expr_)   # the exact Boolean rule that fired
```

### Programmatic API

```python
from exactor_accelerator import ExactorAccelerator

engine = ExactorAccelerator()
engine.fit(train_df, target_col="is_fraud")

res = engine.evaluate({"amount": 1850.0, "velocity_1h": 14, ...})
res["decision"]     # e.g. "CRITICAL"
res["formula_activa"]  # exact Boolean proof
res["route"]        # FAST_PATH_LOCAL or oracle escalation
```

### Scikit-learn compatible

`ExactorAcceleratorClassifier` and `ExactorAcceleratorMultiLabelClassifier` implement `fit` / `predict` / `predict_proba` / `score`, so they drop into existing pipelines.

### Optional: FastAPI server

```bash
pip install "exactor-accelerator[server]"
exactor-accelerator serve   # Swagger UI at /docs
```

---

## Configuration

All credentials are **explicit opt-in** — nothing phones home without them:

| Variable | Purpose | Required? |
|---|---|---|
| `EXACTOR_CORE_TOKEN` | Cloud Boolean minimization (exactor.tech) | Optional — local engine works without it |
| `JEV_API_KEY` (or `TYPESAFE_API_KEY`) | TypeSafe Jev oracle for ambiguous cases | Optional |
| `DEEPSEEK_API_KEY` (+ `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`) | Natural-language audit explanations | Optional — auto-disabled on 401/402/403 |

Copy `.env.example` to `.env` and fill in what you need. Without any keys the engine runs **100% locally**.

---

## Examples & demos

| Project | What it shows |
|---|---|
| **[SATGuardian](https://exactorresearch.github.io/satguardian/)** | **Production WAF** (Rust): security rules as 128-bit Boolean cubes, ~0.5 ms p50, auditable proof per block. Measured 82.0% vs 80.7% recall vs Aegis+OWASP CRS on the CRS v4.30 suite, with 92.9% union coverage. Cloud review is opt-in and returns proposals only. |
| **[exactor-minesweeper](https://github.com/ExactorResearch/exactor-minesweeper)** | System 1 vs System 2 in real time: deterministic tiles resolved locally at CPU speed, ambiguous 50/50 states escalated to the cloud oracle. [Live demo](https://minesweeper.exactor.ai) |
| **[exactor-sudoku-arena](https://github.com/ExactorResearch/exactor-sudoku-arena)** | Constraint satisfaction (NP-complete): deductive Boolean solving with zero constraint violations vs probabilistic LLM guessing. [Live demo](https://sudoku.exactor.ai) |

SATGuardian demonstrates the intended deployment regime: **structured, high-volume decisions with hard audit requirements** — exactly where the Boolean fast-path beats per-request LLM calls on both latency and cost. The arenas isolate the same property interactively: recurring structure resolved locally, oracle reserved for genuine ambiguity.

---

## When to use it — and when not to

**Good fit:**
- High-volume structured decisions with recurring patterns (fraud, triage, routing, SLA checks)
- You need an auditable, deterministic rule behind each decision
- You want oracle escalation only for edge cases

**Not a fit:**
- Open-domain text classification where a general LLM is more accurate (see benchmarks above)
- Tasks with no learnable structure or extremely high label cardinality
- Sub-10 µs hard real-time requirements (Python overhead applies; the formula itself is fast)

---

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v          # 60 tests
python benchmark_comparison.py       # structured-data benchmark
python benchmark_public_datasets.py  # NLP benchmark (needs JEV_API_KEY)
```

## License

MIT — see [LICENSE](LICENSE).
