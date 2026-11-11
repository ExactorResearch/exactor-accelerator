# Benchmark Results — Reproducible Measurements

**Version**: exactor-accelerator 2.0.13
**Date**: measured on this repository's benchmark scripts (see *Reproduction* below)
**Status**: authoritative, reproducible numbers. Supersedes marketing figures in earlier drafts of `COMPARATIVE_BENCHMARK_REPORT.md`.

---

## 1. Structured/tabular data — the design target

**Script**: `benchmark_comparison.py`
**Scenario**: synthetic fraud detection. Hidden ground-truth rule:

```
FRAUD = (amount > 800 AND velocity_1h >= 4)
     OR (failed_pin_attempts >= 3 AND device_trust < 0.40)
     OR (country_risk == 'HIGH' AND amount > 400)
```

Train: 300 samples (38 fraud). Test: 100 samples (13 fraud).
Exactor `fit()` time: ~99 ms. Jev pure oracle: live `api.typesafe.ai` calls, N=30.

| Metric | Jev Pure | ExactorAccelerator (fast-path) |
|---|---|---|
| Accuracy | 56.7% | **78.0%** |
| False Positives | 13 | 17 |
| False Negatives | 0 | 5 |
| Mean latency | 1256.27 ms | **13.15 ms (~96× faster)** |
| p95 latency | 1551.46 ms | 18.60 ms |
| Network dependency | Always | Never |

**Interpretation**

- Exactor wins both axes on this workload: ~96× faster **and** +21 points of accuracy.
- 78% is *not* 100%: the learned DNF approximates the hidden rule because automatic binarization does not align its thresholds (`amount_high`, `velocity_1h_high`, …) with the true boundaries. When propositions match the real decision structure (e.g., hand-crafted features like `amount_gt_800`), the hypercube engine can represent the exact function.
- Jev pure (no Boolean anchoring) effectively guesses fraud rules from prose — expected to be weak on tabular data.

---

## 2. Public NLP datasets — honest limitation

**Script**: `benchmark_public_datasets.py`
**Setup**: 500 train / 200 test samples per dataset; Jev evaluated on a 30-sample subset (API cost). Exactor accuracy measured on the full 200-sample test set.

| Dataset | Classes | Exactor acc | Jev acc | Exactor latency | Jev latency | Jev choices offered |
|---|---|---|---|---|---|---|
| SST-2 (sentiment) | 2 | 54.0% | **96.7%** | 5.9 ms | 1179 ms | 2/2 |
| AG News | 4 | 22.0% | 20.0% | 13.5 ms | 1179 ms | 4/4 |
| Banking77 | 70 | 8.5% | 0.0%* | 109 ms | 1140 ms | **5/70** |

\* Banking77 is **not** a fair Jev comparison: only the 5 most frequent classes were offered as choices (cost limit). Treat that cell as "unmeasured", not as Jev failing.

**Interpretation**

- On unstructured text, the Boolean fast-path loses accuracy to a general LLM oracle — the binarizer cannot capture enough semantics. **Exactor Accelerator is not a general NLP classifier.**
- Where Exactor still wins on NLP: latency (5.9–109 ms vs ~1.2 s) and cost (zero vs per-call API).
- AG News at ~20–22% for both ≈ chance level (25% baseline) — neither approach handles it well at this sample size.

**When to use which**

| Workload | Recommended approach |
|---|---|
| Structured/tabular decisions, recurring patterns, audit requirements | **Exactor fast-path** (optionally with oracle escalation) |
| Unstructured text understanding, novel domains, low volume | **Jev / general LLM** |
| Mixed: mostly-structured stream with rare ambiguous cases | **Exactor hybrid** — fast-path resolves the bulk, oracle handles the tail |

---

## 3. Engine correctness verification

The Boolean minimization layer was fuzz-tested exhaustively (all $2^k$ cube points evaluated):

- Local Python hypercube engine: **0 failures / 400 random functions**.
- Rust `exactor` binding (PyPI `exactor==0.1.0`): produces invalid covers in ~50% of random cases (including don't-care and parity-like functions). The bridge **verifies every Rust output exhaustively** (all ON minterms covered, no OFF-care minterm covered) and falls back to the local engine on failure: **0 failures / 400**, with Rust accepted in 134 cases where verified correct.

> The Rust binding defect should be reported upstream. Until fixed, users get correct results via automatic fallback — at the cost of the Rust path being used only ~1/3 of the time on random functions. Minimal reproductions and details: [`RUST_BINDING_KNOWN_ISSUES.md`](RUST_BINDING_KNOWN_ISSUES.md).

**Related production deployment**: [SATGuardian](https://exactorresearch.github.io/satguardian/) (Rust WAF) applies the same Boolean-cube decision approach to security rules — ~0.5 ms p50 per request, auditable proof per block, measured 82.0% recall vs 80.7% for Aegis+OWASP CRS on the CRS v4.30 suite.

---

## 4. Reproduction

```bash
pip install -e ".[dev]"

# Structured benchmark (needs JEV_API_KEY for the Jev column)
python benchmark_comparison.py

# Public NLP datasets (needs JEV_API_KEY; downloads via HuggingFace)
python benchmark_public_datasets.py

# Unit tests
pytest tests/ -v    # 60 tests
```

Environment: `.env` (gitignored) with `JEV_API_KEY`. All cloud calls require explicit credentials — no implicit registration or network traffic otherwise.
