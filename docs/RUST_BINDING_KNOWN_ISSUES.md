# Rust `exactor` binding: status and mitigation

**Status**: **fixed in `exactor` v0.1.1** (binding-level repair, 2025).
**Source**: `exactor-core-v128` (`src/function/reduction.rs`), GitLab
`exactorresearch/exactor/exactor-core-v128`.

## History

`exactor` v0.1.0 returned **incorrect or unusable output for a large fraction
of Boolean functions** (~50% of random functions in fuzz testing). Observed
failure modes in v0.1.0:

1. **Empty results for non-empty functions** — minimal reproductions
   (n = 1 variable, LSB-first minterm encoding, variable `v0` = bit 0):

   | ON-set (LSB-first) | Expected SOP | v0.1.0 output |
   |---|---|---|
   | `[0, 1]` (tautology) | `1` (always true) | `[]` |
   | `[1]` | `v0` | `[]` |
   | `[0]` | `~v0` | `[]` |

2. **Placeholder `'1'` literals** emitted inside product terms for functions
   that have no 2-level SOP cover under the returned encoding (parity/XOR-like
   cases).

3. **Cubes covering OFF-care points** when don't-care sets are supplied.

4. Rust `dbg!` output printed to **stdout** on every call
   (`reduction.rs:343`), which cannot be silenced from Python.

The exotic `ExactorAlgorithm`/`reducir()` engine remains under suspicion; the
committed `HashMap`→`BTreeMap` change in `exactor-core-v128` improved
determinism but did **not** fix correctness.

## Fix shipped in `exactor` v0.1.1

The Python binding (`exactor-py/src/lib.rs`) now guarantees correctness by
construction:

- **Quine-McCluskey path**: for `num_vars <= 16` and
  `minterms + dont_cares <= 20_000`, `simplify_logic` minimizes with a
  verified Quine-McCluskey implementation (prime implicants of ON ∪ DC,
  essential + greedy cover). Output is a correct SOP by construction.
- **Verified exotic path**: for larger inputs the proprietary
  `ExactorAlgorithm` still runs, but its terms are converted to cubes and
  checked **exhaustively** (every ON minterm covered, no cube covers an
  OFF point, coverage budget-capped). If verification fails, the binding
  raises `ValueError` instead of returning a wrong cover.
- Callers such as `exactor_accelerator` catch that error and fall back to
  their local engine — honest failure, never a silently wrong answer.

### Verification results (v0.1.1)

- Rust unit tests: tautology, positive/negative literal, XOR, AND gate,
  deterministic fuzz (n=3–5, 60 functions each) — **5/5 pass**.
- Python fuzz: **0 failures / 1800 random functions** (n=1–6, with and
  without don't-cares), exhaustive evaluation of all `2^n` points.
- Through `ExactorBridge` (MSB↔LSB conversion + bridge verification):
  **900/900 random functions accepted from the Rust engine** (previously
  ~33%); the remainder of cases still fall back safely.

## Mitigation retained in `exactor_accelerator`

`exactor_accelerator.core.exactor_bridge.ExactorBridge` still treats Rust
output as *untrusted* and re-verifies every cover exhaustively before use.
This is intentional defense-in-depth: the binding is correct today, but the
bridge must stay safe if an older `exactor` wheel is installed.

## Reproduce

```bash
pip install "exactor>=0.1.1"
python - <<'EOF'
import exactor
print(exactor.simplify_logic(["v0"], [0, 1]))  # -> ['1']  (tautology)
print(exactor.simplify_logic(["v0"], [1]))     # -> ['v0']
print(exactor.simplify_logic(["v0"], [0]))     # -> ['~v0']
EOF
```

For `exactor==0.1.0` the same calls return `[]` — the defect this release
repairs.
