# Rust `exactor` binding: status and mitigation

**Status**: **RESOLVED** — `exactor-core-v128` itself was repaired (commit
`dfc6be4`): its `reducir()` pipeline is now a faithful port of the
fuzz-verified v1 algorithm running on scalable `BitVec` keys (>64 variables
supported). `exactor-py` v0.2.0+ depends on the fixed `exactor-core-v128`.
**Source**: `exactor-core-v128` (GitLab `exactorresearch/exactor/exactor-core-v128`),
binding crate `exactor-py`.

## Root cause (confirmed)

The bug was **not** in the minimization algorithm itself — it was in the
`exactor-core-v128` BitVec port:

- `exactor-core` **v1** stores minterms as `u64` in **MSB-first** order
  (variable `i` = bit `num_vars-1-i`) and its `reducir()` engine is correct.
- `exactor-core-v128` introduced `Utility::u64_to_bitvec`, which stores bit
  `i` at vector index `i` (**LSB-first**), inverting the convention the
  reduction pipeline was designed around. Combined with changes in
  `src/function/reduction.rs`, this produced invalid covers: empty results
  for tautologies, `'1'` placeholder literals, and cubes covering OFF-care
  points (~50% of random functions failed exhaustive verification).

A `HashMap`→`BTreeMap` change in v128 improved determinism but did not fix
correctness.

## Fix shipped upstream in `exactor-core-v128` + `exactor-py` v0.2.0

The core defect was repaired in `exactor-core-v128` (not worked around):

- `src/function/reduction.rs` — replaced with a faithful port of the
  proven `exactor-core` v1 `reducir()` algorithm, keeping
  `BTreeMap<BitVec>` keys so arbitrary variable width is preserved.
- `src/algorithm.rs` — reversed `etiquetas` (the engine reads bit `j`
  LSB-first while `Term`/SOP is MSB-first), decode **all** `Verdad` values
  per result function, expand XOR labels into SOP cubes, and re-add
  uncovered minterms as full cubes (same safe repair as v1).
- `src/utility.rs` — `modify_gray_code_with_indices` no longer returns a
  zero `BitVec` when the differing positions cover every bit (a guard that
  was only valid for fixed `u64` width and broke legitimate merges).
- `src/export.rs` (`to_blif`) — emit one term node per `Verdad` value.
- `src/validation.rs` — MSB-first variable mapping (`variables[i]` =
  bitvec index `n-1-i`).

`exactor-py` now depends on **`exactor-core-v128`** again (the fixed
scalable engine), wrapping u64 minterms with `Utility::u64_to_bitvec`:

- Public contract: `variables[0]` is the **most significant bit** of the u64
  minterm (standard SOP/minterm-index notation — same convention used by
  `exactor_accelerator` internally).
- The engine output is still **verified exhaustively** before being
  returned (every ON minterm covered, no cube covers an OFF point).
- If verification fails or the engine errors, a correct-by-construction
  **Quine-McCluskey** fallback handles practical sizes (n ≤ 16,
  ≤ 20k points); otherwise `ValueError` is raised — never a wrong answer.

### Verification results

- `exactor-core-v128` regression suite (`tests/known_defects.rs`): **6/6**,
  including 600-function exhaustive fuzz — **0 invalid covers**.
- `validation_suite`: **6/6**, including the 64-variable checkerboard
  (scaling beyond u64 preserved via BitVec keys).
- `exactor-py` Rust tests: **6/6** on the v128 backend.
- Bridge fuzz (`ExactorBridge`): **900/900** random functions served by the
  Rust engine and accepted after exhaustive verification.
- Earlier evidence: `exactor-core` v1 engine fuzz — **0 failures / 1200
  random
  functions** (n=1–6, with/without don't-cares), exhaustive `2^n` evaluation.
- Binding unit tests: single minterm, XOR (2 cubes), tautology, random
  covers, QM cases — **6/6 pass**.
- Through `ExactorBridge` (MSB-first, no conversion): **900/900 random
  functions served by the Rust engine** (`engine=exactor-core-rust-hpc`),
  all passing the bridge's own cover verification.

## Mitigation retained in `exactor_accelerator`

`ExactorBridge` still re-verifies every Rust cover exhaustively before use —
defense-in-depth in case an older `exactor` wheel is installed. With
`exactor>=0.2.0` the conversion helper was removed (conventions now match).

## Reproduce

```bash
pip install "exactor>=0.2.0"
python - <<'EOF'
import exactor
# n=3, MSB-first: minterm 1 = 0b001 -> ~v0 & ~v1 & v2
print(exactor.simplify_logic(["v0","v1","v2"], [1])["terms"])
# -> ['~v0 & ~v1 & v2']
print(exactor.simplify_logic(["v0","v1","v2"], [1, 2])["terms"])
# -> ['~v0 & v1 & ~v2', '~v0 & ~v1 & v2']  (XOR, two cubes)
print(exactor.simplify_logic(["v0"], [0, 1])["terms"])
# -> ['1']  (tautology)
EOF
```

With `exactor==0.1.0` (v128-based) the same calls returned `[]` or invalid
covers.
