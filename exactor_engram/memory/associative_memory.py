"""
Associative Engram Memory - orchestrates the 4 pillars.

    recall(object)
      1. Perception      -> ternary code in B^64                         (Pillar 1)
      2. Fast-Path       -> evaluate engrams with integer logic (us)     (Pillar 4, System 1)
           exactly one concept satisfied  -> return the stored memory (zero marginal cost)
      3. Cognitive friction (cold start / ambiguity) -> Oracle            (Pillar 2, System 2)
      4. Persist payload + originating event in the WAL ledger           (Pillar 3)
      5. Re-consolidate engrams (exact minimization)                     (Pillar 4)
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

import numpy as np

from ..config import EngramConfig, get_config
from ..core import ExactorBridge
from ..ledger import MemoryLedger
from ..oracle import OracleRouter
from ..perception import MultimodalBinarizer, PerceivedObject
from .engram_compiler import EngramCluster, EngramCompiler, EngramSet, Exemplar


class EngramMemory:
    def __init__(self, cfg: Optional[EngramConfig] = None):
        self.cfg = cfg or get_config()
        self.cfg.validate()
        self.ledger = MemoryLedger(self.cfg.db_path, self.cfg.blob_dir, self.cfg.inline_blob_max_bytes)
        self.binarizer = MultimodalBinarizer(self.cfg.stability_margin)
        self.oracle = OracleRouter(self.cfg)
        self.bridge = ExactorBridge()
        self.compiler = EngramCompiler(
            self.bridge,
            tolerance_ratio=self.cfg.guard_tolerance_ratio,
            min_tolerance=self.cfg.guard_min_tolerance,
            min_literals=self.cfg.guard_min_literals,
            max_disc_bits=self.cfg.discriminant_max_bits,
        )
        self._lock = threading.RLock()
        self._index: List[Dict[str, Any]] = []
        self._sha: Dict[str, str] = {}
        self.engrams = EngramSet(version=0, clusters=[], compile_ms=0.0, engine=self.bridge.engine_name)
        self._reload_index()
        version = self.ledger.latest_engram_version()
        if self._index:
            self._compile(version or 1, "arranque", persist=version == 0)

    # ------------------------------------------------------------------ index / compile
    def _reload_index(self) -> None:
        self._index = self.ledger.load_index()
        self._sha = {r["sha256"]: r["id"] for r in self._index}

    def _exemplars(self) -> List[Exemplar]:
        return [
            Exemplar(r["id"], r["sha256"], r["modality"], r["label"], r["value"], r["care"]) for r in self._index
        ]

    def _compile(self, version: int, trigger: str, persist: bool = True) -> EngramSet:
        es = self.compiler.compile(self._exemplars(), version)
        self.engrams = es
        if persist:
            self.ledger.save_engram_version(
                version, trigger, len(es.concepts), len(es.clusters), es.compile_ms, es.engine,
                [c.to_dict() for c in es.clusters],
            )
        return es

    def consolidate(self, trigger: str = "manual") -> Dict[str, Any]:
        with self._lock:
            self._reload_index()
            es = self._compile(self.engrams.version + 1, trigger)
        return {"version": es.version, "compile_ms": es.compile_ms, "concepts": len(es.concepts), "clusters": len(es.clusters)}

    # ------------------------------------------------------------------ helpers
    def _memory_card(self, mem_id: str) -> Optional[Dict[str, Any]]:
        m = self.ledger.get_memory(mem_id)
        if not m:
            return None
        return {
            "id": m["id"],
            "label": m["label"],
            "description": m.get("description"),
            "modality": m["modality"],
            "mime": m["mime"],
            "filename": m.get("filename"),
            "size_bytes": m["size_bytes"],
            "storage": m["storage"],
            "text_preview": m.get("text_preview"),
            "tags": m.get("tags", []),
            "recall_count": m.get("recall_count", 0),
            "thumbnail_url": f"/api/memories/{m['id']}/thumbnail" if m["modality"] == "image" else None,
            "payload_url": f"/api/memories/{m['id']}/payload",
        }

    def _rank_label_members(self, label: str, qv: int, qc: int, modality: str) -> List[str]:
        same, cross = [], []
        for r in self._index:
            if r["label"] != label:
                continue
            if r["modality"] == modality:
                d = ((qv ^ r["value"]) & qc & r["care"]).bit_count() * 2 + (r["care"] ^ qc).bit_count()
                same.append((d, r["id"]))
            else:
                cross.append(r["id"])
        same.sort()
        return [i for _, i in same] + cross

    def _savings_reference(self) -> Dict[str, float]:
        t = self.ledger.totals()
        if t["oracle_calls"]:
            calls = t["oracle_calls"]
            return {"tokens": int(t["oracle_tokens"] / calls) or self.cfg.oracle_ref_tokens,
                    "cost": (t["oracle_cost_usd"] / calls) or self.cfg.oracle_ref_cost_usd}
        return {"tokens": self.cfg.oracle_ref_tokens, "cost": self.cfg.oracle_ref_cost_usd}

    # ------------------------------------------------------------------ public API
    def perceive(self, data: Optional[bytes] = None, text: Optional[str] = None, filename: str = "objeto",
                 mime: str = "") -> PerceivedObject:
        return self.binarizer.perceive(data=data, text=text, filename=filename, mime=mime)

    def fast_path(self, obj: PerceivedObject) -> Dict[str, Any]:
        """System 1 only: evaluate the compiled engrams. Never calls the Oracle."""
        qv, qc = obj.code.value, obj.code.care
        t0 = time.perf_counter_ns()
        dup = self._sha.get(obj.sha256)
        hits, near = self.engrams.evaluate(qv, qc, obj.modality)
        labels = sorted({h.label for h in hits})
        ranked = self._rank_label_members(labels[0], qv, qc, obj.modality) if len(labels) == 1 else []
        us = (time.perf_counter_ns() - t0) / 1000.0
        return {"dup": dup, "hits": hits, "near": near, "labels": labels, "ranked": ranked, "fastpath_us": us}

    def recall(
        self,
        data: Optional[bytes] = None,
        text: Optional[str] = None,
        filename: str = "objeto",
        mime: str = "",
        allow_oracle: bool = True,
        label_hint: Optional[str] = None,
        simulate_latency: bool = True,
    ) -> Dict[str, Any]:
        t_start = time.perf_counter()
        obj = self.perceive(data=data, text=text, filename=filename, mime=mime)
        perception_ms = (time.perf_counter() - t_start) * 1000.0
        qv, qc = obj.code.value, obj.code.care

        with self._lock:
            fp = self.fast_path(obj)
            version = self.engrams.version

        base = {
            "query": {"sha256": obj.sha256, "modality": obj.modality, "filename": obj.filename,
                      "features": obj.features, "code": obj.code.to_dict()},
            "engram_version": version,
        }

        def proof_for(clusters: List[EngramCluster]) -> List[Dict[str, Any]]:
            return [{"label": c.label, **c.explain(qv, qc)} for c in clusters]

        # ------------------------------------------------ System 1: exact duplicate / fast path
        if not label_hint and (fp["dup"] or len(fp["labels"]) == 1):
            ref = self._savings_reference()
            if fp["dup"]:
                path, mem_id = "IDENTICO", fp["dup"]
                label = next((r["label"] for r in self._index if r["id"] == mem_id), None)
                associated_ids = self._rank_label_members(label, qv, qc, obj.modality) if label else [mem_id]
            else:
                path, label = "FAST_PATH", fp["labels"][0]
                associated_ids = fp["ranked"]
                mem_id = associated_ids[0]
            self.ledger.touch_recall(mem_id)
            total_ms = (time.perf_counter() - t_start) * 1000.0
            proof = proof_for([h for h in fp["hits"] if h.label == label])
            self.ledger.record_recall(
                query_sha256=obj.sha256, modality=obj.modality, path=path, label=label, memory_id=mem_id,
                engram_version=version, fastpath_us=fp["fastpath_us"], total_ms=total_ms,
                tokens_saved=ref["tokens"], cost_saved_usd=ref["cost"], proof=proof,
            )
            return {
                **base,
                "path": path, "system": "SISTEMA_1", "label": label,
                "memory": self._memory_card(mem_id),
                "associated": [c for c in (self._memory_card(i) for i in associated_ids[1:9]) if c],
                "proof": proof,
                "rejected_concepts": len(self.engrams.concepts) - 1,
                "oracle": None,
                "timing": {"perception_ms": round(perception_ms, 3), "fastpath_us": round(fp["fastpath_us"], 2),
                           "oracle_ms": 0.0, "total_ms": round(total_ms, 3)},
                "savings": {"tokens_saved": ref["tokens"], "cost_saved_usd": round(ref["cost"], 6)},
            }

        # ------------------------------------------------ cognitive friction
        if label_hint:
            reason = "ENSENANZA"
        elif len(fp["labels"]) > 1:
            reason = "AMBIGUO"
        else:
            reason = "COLD_START"
        candidates = proof_for(fp["hits"] or fp["near"])

        if not allow_oracle:
            total_ms = (time.perf_counter() - t_start) * 1000.0
            self.ledger.record_recall(
                query_sha256=obj.sha256, modality=obj.modality, path="NOVEDAD", engram_version=version,
                fastpath_us=fp["fastpath_us"], total_ms=total_ms, proof=candidates,
            )
            return {
                **base, "path": "NOVEDAD", "system": "SISTEMA_1", "label": None, "memory": None,
                "associated": [], "proof": candidates, "reason": reason, "oracle": None,
                "timing": {"perception_ms": round(perception_ms, 3), "fastpath_us": round(fp["fastpath_us"], 2),
                           "oracle_ms": 0.0, "total_ms": round(total_ms, 3)},
                "savings": {"tokens_saved": 0, "cost_saved_usd": 0.0},
            }

        # ------------------------------------------------ System 2: Oracle
        t_or = time.perf_counter()
        verdict = self.oracle.consult(obj, label_hint=label_hint, simulate_latency=simulate_latency)
        oracle_ms = (time.perf_counter() - t_or) * 1000.0
        vd = verdict.to_dict()
        event_id = self.ledger.record_oracle_event(reason, vd)

        with self._lock:
            mem_id = self._sha.get(obj.sha256)
            if mem_id is None:
                mem_id = self.ledger.store_memory(
                    sha256=obj.sha256, modality=obj.modality, mime=obj.mime, filename=obj.filename,
                    payload=obj.payload, thumbnail=obj.thumbnail, text_preview=obj.text_preview,
                    code_value=qv, code_care=qc, features=obj.features, embedding=obj.embedding,
                    label=verdict.label, description=verdict.description, tags=verdict.tags,
                    origin_event_id=event_id,
                )
            self._reload_index()
            es = self._compile(self.engrams.version + 1, f"{reason}:{verdict.label}")
            fp2 = self.fast_path(obj)  # verify the new engram now addresses the memory

        total_ms = (time.perf_counter() - t_start) * 1000.0
        self.ledger.record_recall(
            query_sha256=obj.sha256, modality=obj.modality, path=reason if reason != "ENSENANZA" else "ENSENANZA",
            label=verdict.label, memory_id=mem_id, engram_version=es.version, fastpath_us=fp["fastpath_us"],
            total_ms=total_ms, oracle_event_id=event_id, proof=candidates,
        )
        new_clusters = [c for c in es.clusters if c.label == verdict.label]
        associated = [i for i in self._rank_label_members(verdict.label, qv, qc, obj.modality) if i != mem_id]
        return {
            **base,
            "path": reason, "system": "SISTEMA_2", "label": verdict.label,
            "engram_version": es.version,
            "memory": self._memory_card(mem_id),
            "associated": [c for c in (self._memory_card(i) for i in associated[:8]) if c],
            "proof": candidates,
            "oracle": vd,
            "consolidation": {
                "version": es.version, "compile_ms": es.compile_ms, "engine": es.engine,
                "engram": [c.to_dict() for c in new_clusters],
                "self_addressable": fp2["labels"] == [verdict.label],
            },
            "timing": {"perception_ms": round(perception_ms, 3), "fastpath_us": round(fp["fastpath_us"], 2),
                       "oracle_ms": round(oracle_ms, 2), "total_ms": round(total_ms, 3)},
            "savings": {"tokens_saved": 0, "cost_saved_usd": 0.0},
        }

    def teach(self, label: str, **kw: Any) -> Dict[str, Any]:
        return self.recall(label_hint=label, **kw)

    # ------------------------------------------------------------------ telemetry
    def stats(self) -> Dict[str, Any]:
        t = self.ledger.totals()
        hit_rate = (t["fast_hits"] / t["recalls"]) if t["recalls"] else 0.0
        lim = self.cfg.plan_limits
        return {
            **t,
            "hit_rate": round(hit_rate, 4),
            "engram_version": self.engrams.version,
            "clusters": len(self.engrams.clusters),
            "engine": self.engrams.engine,
            "oracle": self.oracle.describe(),
            "hypercube_k": 64,
            "plan": {"name": lim.name, "max_variables": lim.max_variables, "max_minterms": lim.max_minterms,
                     "su_included_month": lim.su_included_month},
        }

    def benchmark(self, iterations: int = 2000) -> Dict[str, Any]:
        """Fast-Path engram addressing vs. brute-force cosine k-NN over continuous embeddings."""
        if not self._index:
            return {"error": "La memoria está vacía. Siembra la demo primero."}
        rows = self._index
        rng = np.random.default_rng(7)
        picks = [rows[i] for i in rng.integers(0, len(rows), size=min(iterations, 500))]
        # engram path
        t0 = time.perf_counter_ns()
        n = 0
        agree = 0
        for _ in range(max(1, iterations // len(picks))):
            for r in picks:
                hits, _ = self.engrams.evaluate(r["value"], r["care"], r["modality"])
                labels = {h.label for h in hits}
                agree += labels == {r["label"]}
                n += 1
        engram_us = (time.perf_counter_ns() - t0) / 1000.0 / n
        # vector k-NN baseline (per modality matrices, cosine, leave-one-in)
        mats: Dict[str, Any] = {}
        for mod in {r["modality"] for r in rows}:
            sub = [r for r in rows if r["modality"] == mod]
            dim = max(len(r["embedding"]) for r in sub)
            M = np.array([r["embedding"] + [0.0] * (dim - len(r["embedding"])) for r in sub], dtype=np.float64)
            M /= np.linalg.norm(M, axis=1, keepdims=True) + 1e-12
            mats[mod] = (M, [r["label"] for r in sub], dim)
        t0 = time.perf_counter_ns()
        m = 0
        for _ in range(max(1, iterations // len(picks))):
            for r in picks:
                M, labels, dim = mats[r["modality"]]
                q = np.array(r["embedding"] + [0.0] * (dim - len(r["embedding"])))
                q /= np.linalg.norm(q) + 1e-12
                _ = labels[int(np.argmax(M @ q))]
                m += 1
        knn_us = (time.perf_counter_ns() - t0) / 1000.0 / m
        return {
            "memories": len(rows),
            "queries": n,
            "engram_fastpath_us": round(engram_us, 3),
            "vector_knn_us": round(knn_us, 3),
            "speedup": round(knn_us / engram_us, 2) if engram_us else None,
            "engram_self_recall_accuracy": round(agree / n, 4),
            "note": "k-NN en numpy (fuerza bruta, coseno). Mediciones locales en este equipo.",
        }

    def reset(self) -> None:
        with self._lock:
            self.ledger.reset()
            self._reload_index()
            self.engrams = EngramSet(version=0, clusters=[], compile_ms=0.0, engine=self.bridge.engine_name)
