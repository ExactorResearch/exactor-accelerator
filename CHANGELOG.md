# Changelog

All notable changes to Exactor Accelerator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.11] - 2026-09-29

### Architecture & Runtime Requirements
- **Modular Tiered Architecture**: Documented minimal operational requirements across `README.md` and `docs/WHY_EXACTOR_ACCELERATOR.md`. Clarified that the Python core runs 100% offline at 0.05 ms, Jev (TypeSafe AI) acts as the Day 1 Zero-Data Cold-Start Oracle, EXACTOR Core API provides Rust HPC cluster scaling up to 64 variables and millions of minterms, and LLM explainers are 100% optional with swappable OpenAI/Ollama/vLLM endpoints.
- **Dual Prediction Output**: Highlighted that every inference delivers both the forecast (`predict(X)`) and the exact active Boolean rule that triggered it (`explain(X)`), establishing unambiguous causal provenance.
- **Hypercube Unit Test Suite**: Added a comprehensive 11-test suite in `tests/test_exactor_hypercube.py` verifying tabular grouping, Hamming distance merging, Don't Care expansion, standard logic gates (AND, OR, XOR), and 4-variable Multiplexer reduction.

### Documentation & Developer Experience
- **Human Reflex Metaphor (System 1 vs System 2)**: Overhauled `README.md`, `COMMUNITY_RELEASE_EXPERIMENT.md`, and architectural documents with the human reflex metaphor—positioning Jev as the analytical brain (System 2) and Exactor as the local automatic muscle memory (System 1).
- **Interactive Continuous Lifecycle**: Documented the 4-step decision lifecycle with an ASCII architecture diagram depicting instant Fast-Path execution, WAL ledger persistence, and hot in-memory logic compilation.
- **Clear Business Benefits**: Highlighted tangible metrics including 100% token savings on routine events, 0.05 ms latency, mathematical regulatory auditability, and offline edge resilience.

## [2.0.10] - 2026-09-29

### Documentation & Global Localization
- **Complete English Localization**: Translated all documentation, conceptual guides, tutorials, and architectural docs into high-precision technical English.
- **Value Proposition & Key Gains**: Added clear strategic gain metrics in documentation (sub-millisecond edge latency, $0.00 marginal inference cost, 100% regulatory auditability, zero-data cold start, and zero false negatives via rule anchoring).

## [2.0.9] - 2026-09-29

### Documentation & Positioning
- **Strategic Alliance Narrative**: Positioned Exactor Accelerator as an infrastructure partner that complements TypeSafe AI (Jev) agility by bringing its declarative cognitive power to edge micro-latency (`0.05 ms`), eliminating cloud network latency overhead and optimizing token budgets.
- **Production Benchmarks Reframing**: Updated comparative tables and value proposition across `README.md`, `COMMUNITY_RELEASE_EXPERIMENT.md`, and architectural documents to emphasize hybrid synergy, zero-data cold-start auto-distillation, and deterministic regulatory auditability.

## [2.0.8] - 2026-09-29

### Security & Sanitization
- **Repository Security Hardening**: Removed hardcoded tokens and credentials from codebase; fully transitioned to environment-based secret resolution (`DEEPSEEK_API_KEY`, `JEV_API_KEY`, `EXACTOR_CORE_TOKEN`).
- **Intellectual Property Shielding**: Sanitized local fallback minimization engine terminology (`ExactorHypercubeReducer`) to standard Quine-McCluskey tabular combination and greedy set cover.
- **Git Hygiene**: Added `cl.txt` and temporary artifacts to `.gitignore` and untracked sensitive local credential caches.

## [2.0.7] - 2026-09-28

### Added
- **Domain Feature Engine**: Added `exactor_accelerator.feature_engine` with specialized engines (`FraudFeatureEngine`, `MedicalFeatureEngine`, `ForexFeatureEngine`, `ManufacturingFeatureEngine`, `SecurityFeatureEngine`, `DomainFeatureEngine`) and `get_feature_engine()` factory function.
- **Top-level Exports**: Exported `get_feature_engine`, `DomainFeatureEngine`, `get_regime_detector`, and `DomainRegimeDetector` in `exactor_accelerator.__init__`.
- **Test Coverage**: Added comprehensive test suite `tests/test_feature_engine.py` covering feature calculations, edge cases, missing columns, and immutability across all domains.

## [2.0.6] - 2026-09-28

### Changed
- **Packaging Maintenance**: Clean distribution release artifact build ensuring complete Python 3.8+ universal wheel compatibility.
- **Dependency Optimization**: Validated lower-bound dependency constraints for legacy runtime stability.

## [2.0.5] - 2026-09-28

### Changed
- **Python Compatibility Lowered**: Lowered `requires-python` from `>=3.9` to `>=3.8` to enable installations on Python 3.8 environments.
- **Classification & Targets**: Added Python 3.8 trove classifier and updated tool configurations (`black`, `ruff`, `mypy`).

## [2.0.4] - 2026-09-28

### Changed
- **Release Maintenance**: Clean release build with updated package metadata for PyPI and local distribution.
- **Packaging Integrity**: Verified wheel and source distribution packaging reproducibility under Python 3.9 through 3.14.

## [2.0.3] - 2026-09-28

### Changed
- **Name Standardization**: Completely removed any legacy `exactor-jev` occurrences in favor of `exactor-accelerator` and `Exactor Accelerator`.
- **Internationalization**: Full English translation of all documentation, docstrings, examples, test suites, and web UI dashboard.
- **Scikit-Learn Interface**: Standardized `ExactorAcceleratorClassifier` and `ExactorAcceleratorMultiLabelClassifier` naming and pipeline export.
- **SDK Compatibility**: Added canonical English keys (`exact_boolean_evaluation`, `autonomous_action_executed`) with backward-compatible aliases.

### Fixed
- Fixed email domain and package metadata URLs across documentation and pyproject configuration.
- Fixed boolean evaluation key access in persistence and regression test suites.

## [2.0.1] - 2026-09-28

### Fixed
- Fixed metadata compliance for PyPI legacy upload
- Sanitized ASCII characters in package description
- Standardized PEP 621 license table specification

## [2.0.0] - 2026-09-28

### ⚠ BREAKING CHANGES
- **Standardized package name**: `exactor-accelerator`
- **Import path standardized**: `import exactor_accelerator`
- **Standardized class names**:
  - `ExactorAcceleratorClassifier`
  - `ExactorAcceleratorMultiLabelClassifier`
  - `ExactorAccelerator`
- `setup.py` removed; `pyproject.toml` is the single source of truth
- Minimum Python version raised to 3.9

### Added
- `exactor_accelerator.configure()` — top-level function to set API tokens programmatically
- `exactor_accelerator.config` module — centralized configuration with env var, `.env` file, and programmatic support
- `EXACTOR_CORE_TOKEN` environment variable support
- `.env.example` template with all configurable tokens
- `py.typed` marker for PEP 561 type checking support
- GitHub Actions CI/CD pipeline (lint, test, build, publish)
- Server dependencies split into `[server]` optional extra
- DomainRegimeDetector for adaptive threshold adjustment
- DomainFeatureEngine for domain-specific feature extraction
- BatchProcessor for high-throughput processing
- Domain-specific detectors: Fraud, Medical, Forex, Manufacturing, Security
- Examples for all 5 domains

### Changed
- `fastapi` and `uvicorn` moved to optional `[server]` dependency group
- Updated roadmap v2.0 to focus on niches of excellence
- SDK module located at `exactor_accelerator/sdk.py`

### Fixed
- Improved cold start handling
- Better regime detection for high-entropy scenarios

## [1.0.0] - 2026-09-26

### Added
- Initial release of Exactor Accelerator
- Hybrid neuro-symbolic architecture (EXACTOR + Jev)
- Scikit-learn compatible interface
- Multi-class and multi-label support
- Fast-path for <1ms decisions
- Live memory and incremental learning
- Comprehensive documentation
- Benchmark suite with public datasets
