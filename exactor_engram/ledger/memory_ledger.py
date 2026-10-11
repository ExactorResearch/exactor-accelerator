"""
Pillar 3 - Living Memory Ledger (SQLite WAL).

Unlike the decision ledger of exactor-jev (labels only), this ledger stores the *memory
itself*: the heavy payload (photo, image segment, text/data fragment) inline as a BLOB or,
above `inline_blob_max_bytes`, as a content-addressed file pointer - always together with
the oracle event that originated it and its ternary hypercube code.
"""

from __future__ import annotations

import contextlib
import datetime
import json
import os
import sqlite3
import threading
import uuid
from typing import Any, Dict, Iterator, List, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    sha256 TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    modality TEXT NOT NULL,
    mime TEXT NOT NULL,
    filename TEXT,
    size_bytes INTEGER NOT NULL,
    storage TEXT NOT NULL,              -- inline | file
    payload BLOB,
    blob_path TEXT,
    thumbnail BLOB,
    text_preview TEXT,
    code_value TEXT NOT NULL,           -- 64-bit hex
    code_care TEXT NOT NULL,            -- 64-bit hex (stable-bit mask)
    features_json TEXT NOT NULL,
    embedding_json TEXT NOT NULL,
    label TEXT NOT NULL,
    description TEXT,
    tags_json TEXT,
    origin_event_id INTEGER,
    recall_count INTEGER NOT NULL DEFAULT 0,
    last_recalled_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_memories_label ON memories(label);

CREATE TABLE IF NOT EXISTS oracle_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    memory_id TEXT,
    reason TEXT NOT NULL,               -- COLD_START | AMBIGUO | ENSENANZA
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    simulated INTEGER NOT NULL,
    verdict_json TEXT NOT NULL,
    tokens_in INTEGER NOT NULL,
    tokens_out INTEGER NOT NULL,
    cost_usd REAL NOT NULL,
    latency_ms REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS recall_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    query_sha256 TEXT NOT NULL,
    modality TEXT NOT NULL,
    path TEXT NOT NULL,                 -- IDENTICO | FAST_PATH | COLD_START | AMBIGUO | NOVEDAD
    label TEXT,
    memory_id TEXT,
    engram_version INTEGER,
    fastpath_us REAL NOT NULL,
    total_ms REAL NOT NULL,
    oracle_event_id INTEGER,
    tokens_saved INTEGER NOT NULL DEFAULT 0,
    cost_saved_usd REAL NOT NULL DEFAULT 0,
    proof_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_recall_id ON recall_events(id DESC);

CREATE TABLE IF NOT EXISTS engram_versions (
    version INTEGER PRIMARY KEY,
    ts TEXT NOT NULL,
    trigger TEXT NOT NULL,
    n_concepts INTEGER NOT NULL,
    n_clusters INTEGER NOT NULL,
    compile_ms REAL NOT NULL,
    engine TEXT NOT NULL,
    snapshot_json TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class MemoryLedger:
    def __init__(self, db_path: str = "engram_memory.db", blob_dir: str = "engram_blobs", inline_max: int = 2 << 20):
        self.db_path = db_path
        self.blob_dir = blob_dir
        self.inline_max = inline_max
        self._lock = threading.Lock()
        self._mem_conn: Optional[sqlite3.Connection] = None
        if db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._mem_conn.row_factory = sqlite3.Row
        else:
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        with self._conn() as c:
            c.executescript(SCHEMA)
            c.commit()

    @contextlib.contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        if self._mem_conn is not None:
            yield self._mem_conn
            return
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA busy_timeout = 5000;")
            yield conn
        finally:
            conn.close()

    # ------------------------------------------------------------------ memories
    def store_memory(
        self,
        *,
        sha256: str,
        modality: str,
        mime: str,
        filename: str,
        payload: bytes,
        thumbnail: Optional[bytes],
        text_preview: Optional[str],
        code_value: int,
        code_care: int,
        features: Dict[str, Any],
        embedding: List[float],
        label: str,
        description: str,
        tags: List[str],
        origin_event_id: Optional[int],
    ) -> str:
        mem_id = uuid.uuid4().hex[:12]
        storage, inline, path = "inline", payload, None
        if len(payload) > self.inline_max:
            storage, inline = "file", None
            sub = os.path.join(self.blob_dir, sha256[:2])
            os.makedirs(sub, exist_ok=True)
            path = os.path.join(sub, sha256)
            if not os.path.exists(path):
                with open(path, "wb") as fh:
                    fh.write(payload)
        with self._lock, self._conn() as c:
            c.execute(
                """INSERT INTO memories (id, sha256, created_at, modality, mime, filename, size_bytes, storage,
                       payload, blob_path, thumbnail, text_preview, code_value, code_care, features_json,
                       embedding_json, label, description, tags_json, origin_event_id)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    mem_id, sha256, _now(), modality, mime, filename, len(payload), storage, inline, path,
                    thumbnail, text_preview, f"{code_value:016x}", f"{code_care:016x}",
                    json.dumps(features, ensure_ascii=False, default=str),
                    json.dumps([round(float(x), 5) for x in embedding]), label, description,
                    json.dumps(tags, ensure_ascii=False), origin_event_id,
                ),
            )
            if origin_event_id:
                c.execute("UPDATE oracle_events SET memory_id = ? WHERE id = ?", (mem_id, origin_event_id))
            c.commit()
        return mem_id

    def find_by_sha(self, sha256: str) -> Optional[Dict[str, Any]]:
        with self._conn() as c:
            r = c.execute(
                "SELECT id, label, modality FROM memories WHERE sha256 = ?", (sha256,)
            ).fetchone()
            return dict(r) if r else None

    def load_index(self) -> List[Dict[str, Any]]:
        """Light-weight rows (no payloads) used to compile engrams."""
        with self._conn() as c:
            rows = c.execute(
                "SELECT id, sha256, modality, label, code_value, code_care, embedding_json FROM memories ORDER BY created_at"
            ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["value"] = int(d.pop("code_value"), 16)
            d["care"] = int(d.pop("code_care"), 16)
            d["embedding"] = json.loads(d.pop("embedding_json"))
            out.append(d)
        return out

    def get_memory(self, mem_id: str, with_payload: bool = False) -> Optional[Dict[str, Any]]:
        cols = "*" if with_payload else (
            "id, sha256, created_at, modality, mime, filename, size_bytes, storage, blob_path, text_preview, "
            "code_value, code_care, features_json, label, description, tags_json, origin_event_id, recall_count, last_recalled_at"
        )
        with self._conn() as c:
            r = c.execute(f"SELECT {cols} FROM memories WHERE id = ?", (mem_id,)).fetchone()
        if not r:
            return None
        d = dict(r)
        d.pop("thumbnail", None)
        d["features"] = json.loads(d.pop("features_json"))
        d["tags"] = json.loads(d.pop("tags_json") or "[]")
        d.pop("embedding_json", None)
        if with_payload and d.get("storage") == "file" and d.get("blob_path"):
            with open(d["blob_path"], "rb") as fh:
                d["payload"] = fh.read()
        return d

    def get_thumbnail(self, mem_id: str) -> Optional[bytes]:
        with self._conn() as c:
            r = c.execute("SELECT thumbnail FROM memories WHERE id = ?", (mem_id,)).fetchone()
        return r[0] if r else None

    def list_memories(self, label: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
        q = (
            "SELECT id, created_at, modality, mime, filename, size_bytes, storage, text_preview, label, "
            "description, recall_count, code_care FROM memories"
        )
        args: tuple = ()
        if label:
            q += " WHERE label = ?"
            args = (label,)
        q += " ORDER BY created_at DESC LIMIT ?"
        with self._conn() as c:
            rows = c.execute(q, args + (limit,)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["stable_bits"] = int(d.pop("code_care"), 16).bit_count()
            out.append(d)
        return out

    def touch_recall(self, mem_id: str) -> None:
        with self._lock, self._conn() as c:
            c.execute(
                "UPDATE memories SET recall_count = recall_count + 1, last_recalled_at = ? WHERE id = ?",
                (_now(), mem_id),
            )
            c.commit()

    # ------------------------------------------------------------------ events
    def record_oracle_event(self, reason: str, verdict: Dict[str, Any]) -> int:
        with self._lock, self._conn() as c:
            cur = c.execute(
                """INSERT INTO oracle_events (ts, reason, provider, model, simulated, verdict_json,
                       tokens_in, tokens_out, cost_usd, latency_ms) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    _now(), reason, verdict["provider"], verdict["model"], int(bool(verdict["simulated"])),
                    json.dumps(verdict, ensure_ascii=False, default=str), int(verdict["tokens_in"]),
                    int(verdict["tokens_out"]), float(verdict["cost_usd"]), float(verdict["latency_ms"]),
                ),
            )
            c.commit()
            return int(cur.lastrowid)

    def record_recall(self, **kw: Any) -> int:
        with self._lock, self._conn() as c:
            cur = c.execute(
                """INSERT INTO recall_events (ts, query_sha256, modality, path, label, memory_id, engram_version,
                       fastpath_us, total_ms, oracle_event_id, tokens_saved, cost_saved_usd, proof_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    _now(), kw["query_sha256"], kw["modality"], kw["path"], kw.get("label"), kw.get("memory_id"),
                    kw.get("engram_version"), float(kw["fastpath_us"]), float(kw["total_ms"]),
                    kw.get("oracle_event_id"), int(kw.get("tokens_saved", 0)), float(kw.get("cost_saved_usd", 0.0)),
                    json.dumps(kw.get("proof"), ensure_ascii=False, default=str),
                ),
            )
            c.commit()
            return int(cur.lastrowid)

    def recent_recalls(self, limit: int = 40) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                """SELECT id, ts, modality, path, label, memory_id, engram_version, fastpath_us, total_ms,
                          tokens_saved, cost_saved_usd FROM recall_events ORDER BY id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def save_engram_version(self, version: int, trigger: str, n_concepts: int, n_clusters: int,
                            compile_ms: float, engine: str, snapshot: Any) -> None:
        with self._lock, self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO engram_versions VALUES (?,?,?,?,?,?,?,?)",
                (version, _now(), trigger, n_concepts, n_clusters, compile_ms, engine,
                 json.dumps(snapshot, ensure_ascii=False, default=str)),
            )
            c.commit()

    def latest_engram_version(self) -> int:
        with self._conn() as c:
            r = c.execute("SELECT MAX(version) FROM engram_versions").fetchone()
        return int(r[0] or 0)

    def engram_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT version, ts, trigger, n_concepts, n_clusters, compile_ms, engine FROM engram_versions ORDER BY version DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def totals(self) -> Dict[str, Any]:
        with self._conn() as c:
            mem = c.execute("SELECT COUNT(*), COALESCE(SUM(size_bytes),0), COUNT(DISTINCT label) FROM memories").fetchone()
            orc = c.execute("SELECT COUNT(*), COALESCE(SUM(tokens_in+tokens_out),0), COALESCE(SUM(cost_usd),0), COALESCE(AVG(latency_ms),0) FROM oracle_events").fetchone()
            rec = c.execute(
                """SELECT COUNT(*),
                          COALESCE(SUM(CASE WHEN path IN ('FAST_PATH','IDENTICO') THEN 1 ELSE 0 END),0),
                          COALESCE(SUM(tokens_saved),0), COALESCE(SUM(cost_saved_usd),0),
                          COALESCE(AVG(CASE WHEN path IN ('FAST_PATH','IDENTICO') THEN fastpath_us END),0)
                   FROM recall_events"""
            ).fetchone()
        return {
            "memories": mem[0], "payload_bytes": mem[1], "concepts": mem[2],
            "oracle_calls": orc[0], "oracle_tokens": orc[1], "oracle_cost_usd": round(orc[2], 6),
            "oracle_avg_latency_ms": round(orc[3], 2),
            "recalls": rec[0], "fast_hits": rec[1], "tokens_saved": rec[2],
            "cost_saved_usd": round(rec[3], 6), "fastpath_avg_us": round(rec[4], 2),
        }

    def reset(self) -> None:
        with self._lock, self._conn() as c:
            for t in ("memories", "oracle_events", "recall_events", "engram_versions"):
                c.execute(f"DELETE FROM {t}")
            c.commit()
