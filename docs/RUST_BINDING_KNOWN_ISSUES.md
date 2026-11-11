# Known Issue: Rust `exactor` binding (PyPI `exactor==0.1.0`)

**Status**: upstream defect, mitigated in `exactor_accelerator` v2.0.13.
**Source**: `exactor-core-v128` (`src/function/reduction.rs`), GitLab `exactorresearch/exactor/exactor-core-v128`.

## Symptom

`exactor.simplify_logic(variables, minterms_lsb_first)` returns **incorrect or unusable
output for a large fraction of Boolean functions** (~50% of random functions in fuzz
testing, concentrated on small variable counts and functions with don't-cares /
parity-like structure).

Observed failure modes:

1. **Empty result for non-empty functions** — minimal reproductions (n = 1 variable,
   LSB-first minterm encoding, variable `v0` = bit 0):

   | ON-set (LSB-first) | Expected SOP | `simplify_logic` output |
   |---|---|---|
   | `[0, 1]` (tautology) | `1` (always true) | `[]` |
   | `[1]` | `v0` | `[]` |
   | `[0]` | `~v0` | `[]` |

   ```python
   import exactor
   exactor.simplify_logic(["v0"], [0, 1])  # -> []   (should be tautology)
   exactor.simplify_logic(["v0"], [1])     # -> []   (should be "v0")
   exactor.simplify_logic(["v0"], [0])     # -> []   (should be "~v0")
   ```

2. **Placeholder `'1'` literals** emitted inside product terms for functions that
   have no 2-level SOP cover under the returned encoding (parity/XOR-like cases).

3. **Cubes covering OFF-care points** when don't-care sets are supplied.

4. The binding prints Rust `dbg!` output to **stdout** on every call
   (`reduction.rs:343` — `"Default Unsorted true_values"`), which cannot be
   silenced from Python.

## Mitigation in this repo

`exactor_accelerator.core.exactor_bridge.ExactorBridge` treats the Rust output as
*untrusted*:

- Converts project MSB-first minterms to the binding's LSB-first convention.
- Parses product terms into `HypercubeTerm`s.
- **Verifies exhaustively**: every ON minterm covered, no OFF-care point covered
  (`_verify_terms_cover`).
- Falls back to the local Python hypercube engine on any failure.

Fuzz result (400 random functions, exhaustive evaluation): **0 incorrect results**;
Rust output accepted only when verified (134/400 cases).

## Reproduce

```bash
pip install exactor==0.1.0
python - <<'EOF'
import exactor
print(exactor.simplify_logic(["v0"], [1]))   # expect ["v0"], get []
EOF
```
