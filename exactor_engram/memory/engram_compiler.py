"""
Pillar 4 - Engram Compiler: boolean formulas as associative addresses.

For every concept consolidated by the Oracle, the compiler builds an *engram*:

    ENGRAM(label) = OR_c [ MODALITY_c(q) AND GUARD_c(q) AND DISCRIMINANT_c(q) ]

    GUARD_c         Threshold boolean function over the *invariant literals* of cluster c
                    (bits on which every exemplar is stable and agrees). It answers
                    "is this a known thing?" - open-world novelty detection, so an object
                    never seen before is routed to the Oracle instead of being force-matched.
                    It accepts at most `tolerance` violated literals (Hamming radius) - still
                    a pure, deterministic boolean function (a threshold gate).

    DISCRIMINANT_c  Minimal sum-of-products produced by the EXACTOR minimizer that separates
                    cluster c from every exemplar of every *other* concept. The support is
                    chosen by greedy hitting-set over the invariant literals and then exactly
                    minimized with unobserved cells as don't-cares (maximal generalization
                    inside the guard).

Evaluation is a handful of integer AND/XOR/popcount operations per cluster -> micro-seconds.
"""

from __future__ import annotations

import itertools
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..core import ExactorBridge
from ..core.hypercube import HypercubeTerm
from ..perception import K, MODALITY_MASK, proposition_names

FULL = (1 << K) - 1
SEMANTIC_BITS = (1 << 16) - 1 & ~MODALITY_MASK  # bits 2..15


@dataclass
class Exemplar:
    mem_id: str
    sha256: str
    modality: str
    label: str
    value: int
    care: int


@dataclass
class EngramCluster:
    cid: str
    label: str
    modality: str
    member_ids: List[str]
    modality_value: int
    inv_value: int
    inv_care: int
    tolerance: int
    disc_terms: List[Tuple[int, int]] = field(default_factory=list)  # (care, value) over B^64
    disc_formula: str = "TRUE"
    disc_support: List[int] = field(default_factory=list)
    disc_stats: Dict[str, Any] = field(default_factory=dict)
    conflicts: List[str] = field(default_factory=list)

    @property
    def literals(self) -> int:
        return self.inv_care.bit_count()

    # ---------------------------------------------------------------- fast-path primitives
    def guard(self, qv: int, qc: int) -> Tuple[bool, int, int]:
        ic = self.inv_care
        mism = ((qv ^ self.inv_value) & ic & qc).bit_count()
        unknown = (ic & ~qc).bit_count()
        return (mism + unknown // 2) <= self.tolerance, mism, unknown

    def discriminant(self, qv: int, qc: int) -> int:
        """Index of the satisfied term or -1. Unstable query bits are treated as compatible."""
        if not self.disc_terms:
            return 0
        for i, (c, v) in enumerate(self.disc_terms):
            if (qv ^ v) & c & qc == 0:
                return i
        return -1

    # ---------------------------------------------------------------- explainability
    def explain(self, qv: int, qc: int, max_items: int = 14) -> Dict[str, Any]:
        names = proposition_names(self.modality)
        ok, mism, unknown = self.guard(qv, qc)
        matched, violated, unk = [], [], []
        for i in range(K):
            if not (self.inv_care >> i) & 1:
                continue
            lit = names[i] if (self.inv_value >> i) & 1 else f"NOT {names[i]}"
            if not (qc >> i) & 1:
                unk.append(lit)
            elif ((qv ^ self.inv_value) >> i) & 1:
                violated.append(lit)
            else:
                matched.append(lit)
        ti = self.discriminant(qv, qc)
        return {
            "cluster": self.cid,
            "guard": {
                "passed": ok, "literals": self.literals, "matched": len(matched), "violated": violated,
                "unknown": len(unk), "tolerance": self.tolerance,
                "matched_sample": [m for m in matched if not m.startswith(("phash", "simhash", "NOT phash", "NOT simhash"))][:max_items]
                or matched[:max_items],
            },
            "discriminant": {
                "formula": self.disc_formula,
                "support": [names[b] for b in self.disc_support],
                "satisfied_term": self._term_str(ti) if ti >= 0 else None,
            },
        }

    def _term_str(self, idx: int) -> str:
        if not self.disc_terms:
            return "TRUE"
        names = proposition_names(self.modality)
        c, v = self.disc_terms[idx]
        lits = [names[i] if (v >> i) & 1 else f"NOT {names[i]}" for i in range(K) if (c >> i) & 1]
        return " AND ".join(lits) or "TRUE"

    def to_dict(self) -> Dict[str, Any]:
        names = proposition_names(self.modality)
        inv_sem = [
            (names[i] if (self.inv_value >> i) & 1 else f"NOT {names[i]}")
            for i in range(2, 16) if (self.inv_care >> i) & 1
        ]
        return {
            "cluster": self.cid,
            "label": self.label,
            "modality": self.modality,
            "members": len(self.member_ids),
            "member_ids": self.member_ids,
            "invariant_literals": self.literals,
            "invariant_semantic": inv_sem,
            "invariant_ternary": "".join(
                "-" if not (self.inv_care >> i) & 1 else str((self.inv_value >> i) & 1) for i in range(K)
            ),
            "tolerance": self.tolerance,
            "guard_formula": f"MATCH_{self.literals}(invariantes) con <= {self.tolerance} violaciones",
            "discriminant_formula": self.disc_formula,
            "discriminant_support": [names[b] for b in self.disc_support],
            "discriminant_stats": self.disc_stats,
            "conflicts": self.conflicts,
        }


@dataclass
class EngramSet:
    version: int
    clusters: List[EngramCluster]
    compile_ms: float
    engine: str
    by_modality: Dict[str, List[EngramCluster]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.by_modality = {}
        for c in self.clusters:
            self.by_modality.setdefault(c.modality, []).append(c)

    @property
    def concepts(self) -> List[str]:
        return sorted({c.label for c in self.clusters})

    def evaluate(self, qv: int, qc: int, modality: str) -> Tuple[List[EngramCluster], List[EngramCluster]]:
        """Returns (full matches, guard-only matches). Pure integer logic."""
        mod_bits = qv & MODALITY_MASK
        hits, near = [], []
        for cl in self.by_modality.get(modality, ()):
            if cl.modality_value != mod_bits:
                continue
            ok, _, _ = cl.guard(qv, qc)
            if not ok:
                continue
            if cl.discriminant(qv, qc) >= 0:
                hits.append(cl)
            else:
                near.append(cl)
        return hits, near

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "compile_ms": self.compile_ms,
            "engine": self.engine,
            "concepts": self.concepts,
            "clusters": [c.to_dict() for c in self.clusters],
        }


class EngramCompiler:
    def __init__(
        self,
        bridge: Optional[ExactorBridge] = None,
        tolerance_ratio: float = 0.14,
        min_tolerance: int = 3,
        min_literals: int = 12,
        max_disc_bits: int = 10,
    ):
        self.bridge = bridge or ExactorBridge()
        self.tolerance_ratio = tolerance_ratio
        self.min_tolerance = min_tolerance
        self.min_literals = min_literals
        self.max_disc_bits = max_disc_bits

    # ------------------------------------------------------------------ consensus
    @staticmethod
    def _consensus(members: List[Exemplar]) -> Tuple[int, int]:
        care = FULL
        v0 = members[0].value
        for m in members:
            care &= m.care & ~(m.value ^ v0)
        care &= ~MODALITY_MASK & FULL
        return v0 & care, care

    def _tolerance(self, literals: int) -> int:
        return max(self.min_tolerance, int(round(self.tolerance_ratio * literals)))

    def _cluster_label(self, members: List[Exemplar]) -> List[List[Exemplar]]:
        """Deterministic agglomerative clustering: merge while invariants keep >= min_literals."""
        groups: List[List[Exemplar]] = [[m] for m in members]
        cons = [self._consensus(g) for g in groups]
        while len(groups) > 1:
            best: Optional[Tuple[int, int, int]] = None
            for i, j in itertools.combinations(range(len(groups)), 2):
                vi, ci = cons[i]
                vj, cj = cons[j]
                lits = (ci & cj & ~(vi ^ vj)).bit_count()
                if lits >= self.min_literals and (best is None or lits > best[0]):
                    best = (lits, i, j)
            if best is None:
                break
            _, i, j = best
            groups[i] = groups[i] + groups[j]
            cons[i] = self._consensus(groups[i])
            del groups[j], cons[j]
        return groups

    # ------------------------------------------------------------------ discriminant
    def _discriminant(self, cl: EngramCluster, off: List[Exemplar]) -> None:
        names = proposition_names(cl.modality)
        iv, ic = cl.inv_value, cl.inv_care
        diffs = [(o, ic & o.care & (o.value ^ iv)) for o in off]
        conflicts = [o for o, d in diffs if d == 0]
        pending = [(o, d) for o, d in diffs if d != 0]
        support: List[int] = []
        while pending and len(support) < self.max_disc_bits:
            counts: Dict[int, int] = {}
            for _, d in pending:
                x = d
                while x:
                    low = x & -x
                    b = low.bit_length() - 1
                    counts[b] = counts.get(b, 0) + 1
                    x ^= low
            # most separating bit; prefer named semantic traits, then lower index (deterministic)
            b = max(counts, key=lambda k: (counts[k], 1 if (SEMANTIC_BITS >> k) & 1 else 0, -k))
            support.append(b)
            pending = [(o, d) for o, d in pending if not (d >> b) & 1]
        conflicts += [o for o, _ in pending]
        cl.conflicts = sorted({f"{o.label} ({o.mem_id})" for o in conflicts})
        separable = [o for o, d in diffs if d != 0 and o not in conflicts]

        if not support:
            cl.disc_terms, cl.disc_formula, cl.disc_support = [], "TRUE", []
            cl.disc_stats = {"engine": "trivial", "reason": "sin competidores en la modalidad"}
            return

        support.sort()
        s = len(support)
        var_names = [names[b] for b in support]

        def project(value: int) -> int:
            m = 0
            for j, b in enumerate(support):
                if (value >> b) & 1:
                    m |= 1 << (s - 1 - j)
            return m

        on = project(iv)
        off_cells = set()
        for o in separable:
            fixed = [(j, (o.value >> b) & 1) for j, b in enumerate(support) if (o.care >> b) & 1]
            free = [j for j, b in enumerate(support) if not (o.care >> b) & 1]
            base = 0
            for j, bit in fixed:
                if bit:
                    base |= 1 << (s - 1 - j)
            for combo in range(1 << len(free)):
                cell = base
                for t, j in enumerate(free):
                    if (combo >> t) & 1:
                        cell |= 1 << (s - 1 - j)
                off_cells.add(cell)
        off_cells.discard(on)
        dont_cares = [m for m in range(1 << s) if m != on and m not in off_cells]
        res = self.bridge.simplify(var_names, [on], dont_cares)

        terms: List[Tuple[int, int]] = []
        for t in res.terms:
            c = v = 0
            for j, st in enumerate(t.states):
                if st == HypercubeTerm.STATE_DC:
                    continue
                c |= 1 << support[j]
                if st == HypercubeTerm.STATE_1:
                    v |= 1 << support[j]
            terms.append((c, v))
        cl.disc_terms = terms
        cl.disc_support = sorted({b for c, _ in terms for b in range(K) if (c >> b) & 1})
        cl.disc_formula = res.formula_expr if terms else "FALSE"
        cl.disc_stats = {
            "engine": res.stats.get("engine", self.bridge.engine_name),
            "projected_vars": s,
            "off_cells": len(off_cells),
            "dont_cares": len(dont_cares),
            "terms": len(terms),
            "literals": sum(c.bit_count() for c, _ in terms),
            "minimize_ms": res.stats.get("execution_time_ms"),
            "competitors": len(off),
        }

    # ------------------------------------------------------------------ compile
    def compile(self, exemplars: List[Exemplar], version: int) -> EngramSet:
        t0 = time.perf_counter()
        by_key: Dict[Tuple[str, str], List[Exemplar]] = {}
        for e in exemplars:
            by_key.setdefault((e.label, e.modality), []).append(e)

        clusters: List[EngramCluster] = []
        for (label, modality), members in sorted(by_key.items()):
            for idx, group in enumerate(self._cluster_label(members)):
                iv, ic = self._consensus(group)
                lits = ic.bit_count()
                clusters.append(
                    EngramCluster(
                        cid=f"{label}#{modality[:3]}{idx}",
                        label=label,
                        modality=modality,
                        member_ids=[g.mem_id for g in group],
                        modality_value=group[0].value & MODALITY_MASK,
                        inv_value=iv,
                        inv_care=ic,
                        tolerance=self._tolerance(lits),
                    )
                )
        for cl in clusters:
            off = [e for e in exemplars if e.modality == cl.modality and e.label != cl.label]
            self._discriminant(cl, off)
        ms = round((time.perf_counter() - t0) * 1000, 3)
        return EngramSet(version=version, clusters=clusters, compile_ms=ms, engine=self.bridge.engine_name)
