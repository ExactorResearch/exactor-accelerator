"""
Memory Ledger Subsystem using SQLite in WAL (Write-Ahead Logging) Mode.
Ensures ultra-fast, concurrent, persistent event logging and incremental memory tracking.
"""

from typing import List, Dict, Any, Optional
import sqlite3
import json
import datetime
import threading
import os


import contextlib

class MemoryLedger:
    """
    Thread-safe SQLite WAL ledger storing live queries, calibrated decisions,
    and rule version history.
    """

    def __init__(self, db_path: str = "memory_ledger.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._mem_conn = None
        if self.db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._mem_conn.row_factory = sqlite3.Row
        self._init_db()

    def __getstate__(self):
        state = self.__dict__.copy()
        state["_lock"] = None
        state["_mem_conn"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._lock = threading.Lock()
        self._mem_conn = None
        if self.db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._mem_conn.row_factory = sqlite3.Row
        self._init_db()

    @contextlib.contextmanager
    def _get_connection(self):
        if self._mem_conn is not None:
            yield self._mem_conn
        else:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            try:
                # Enable WAL mode for high concurrency
                conn.execute("PRAGMA journal_mode = WAL;")
                conn.execute("PRAGMA synchronous = NORMAL;")
                conn.execute("PRAGMA busy_timeout = 5000;")
                yield conn
            finally:
                conn.close()

    def _init_db(self):
        """Initializes database schema if not present."""
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Table for live query interactions
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ledger_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query_id TEXT UNIQUE NOT NULL,
                        timestamp TEXT NOT NULL,
                        raw_state TEXT NOT NULL,
                        minterm_val INTEGER NOT NULL,
                        minterm_binary TEXT NOT NULL,
                        questions_payload TEXT NOT NULL,
                        jev_response TEXT NOT NULL,
                        criterio_logico_prob REAL NOT NULL,
                        chosen_action TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        autonomous_action_executed INTEGER NOT NULL,
                        action_details TEXT,
                        latency_ms REAL NOT NULL,
                        feedback_label INTEGER,
                        rule_version INTEGER NOT NULL DEFAULT 1
                    );
                    """
                )

                # Index for fast sliding window queries
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_ledger_timestamp 
                    ON ledger_entries (id DESC, timestamp DESC);
                    """
                )

                # Table for Exactor rules evolution history
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS rules_history (
                        version INTEGER PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        formula_expr TEXT NOT NULL,
                        terms_json TEXT NOT NULL,
                        hypercube_k INTEGER NOT NULL,
                        sliding_window_size INTEGER NOT NULL,
                        trigger_reason TEXT NOT NULL,
                        stats_json TEXT NOT NULL
                    );
                    """
                )

                conn.commit()

    def record_interaction(
        self,
        query_id: str,
        raw_state: Dict[str, Any],
        minterm_val: int,
        minterm_binary: str,
        questions_payload: Dict[str, Any],
        jev_response: Dict[str, Any],
        criterio_logico_prob: float,
        chosen_action: str,
        confidence: float,
        autonomous_action_executed: bool,
        action_details: str,
        latency_ms: float,
        rule_version: int = 1,
    ) -> int:
        """Appends a new real-time interaction to the SQLite WAL ledger."""
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO ledger_entries (
                        query_id, timestamp, raw_state, minterm_val, minterm_binary,
                        questions_payload, jev_response, criterio_logico_prob,
                        chosen_action, confidence, autonomous_action_executed,
                        action_details, latency_ms, rule_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        query_id,
                        timestamp,
                        json.dumps(raw_state, default=str, ensure_ascii=False),
                        minterm_val,
                        minterm_binary,
                        json.dumps(questions_payload, default=str, ensure_ascii=False),
                        json.dumps(jev_response, default=str, ensure_ascii=False),
                        round(float(criterio_logico_prob), 4),
                        chosen_action,
                        round(float(confidence), 4),
                        1 if autonomous_action_executed else 0,
                        action_details,
                        round(float(latency_ms), 2),
                        rule_version,
                    ),
                )
                conn.commit()
                return cursor.lastrowid

    def save_rules_version(
        self,
        version: int,
        formula_expr: str,
        terms: List[str],
        hypercube_k: int,
        sliding_window_size: int,
        trigger_reason: str,
        stats: Dict[str, Any],
    ):
        """Records an updated Exactor rule version in the ledger."""
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO rules_history (
                        version, timestamp, formula_expr, terms_json, 
                        hypercube_k, sliding_window_size, trigger_reason, stats_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        version,
                        timestamp,
                        formula_expr,
                        json.dumps(terms, ensure_ascii=False),
                        hypercube_k,
                        sliding_window_size,
                        trigger_reason,
                        json.dumps(stats, ensure_ascii=False),
                    ),
                )
                conn.commit()

    def record_feedback(self, query_id: str, label: int):
        """Updates an entry with verified ground truth / human feedback."""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.execute(
                        "UPDATE ledger_entries SET feedback_label = ? WHERE query_id = ?",
                        (int(label), query_id),
                    )
                    conn.commit()
            except sqlite3.OperationalError as e:
                if "no such table" in str(e).lower():
                    self._init_db()
                    try:
                        with self._get_connection() as conn:
                            conn.execute(
                                "UPDATE ledger_entries SET feedback_label = ? WHERE query_id = ?",
                                (int(label), query_id),
                            )
                            conn.commit()
                    except Exception:
                        pass
                else:
                    pass

    def get_recent_entries(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Fetches latest ledger entries for UI and monitoring."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM ledger_entries 
                ORDER BY id DESC LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                try:
                    item["raw_state"] = json.loads(item["raw_state"])
                except Exception:
                    pass
                try:
                    item["jev_response"] = json.loads(item["jev_response"])
                except Exception:
                    pass
                results.append(item)
            return results

    def get_sliding_window_records(self, window_size: int = 50) -> List[Dict[str, Any]]:
        """Retrieves the most recent N interactions for incremental differential learning."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, query_id, minterm_val, criterio_logico_prob, 
                       autonomous_action_executed, feedback_label, raw_state
                FROM ledger_entries
                ORDER BY id DESC LIMIT ?
                """,
                (window_size,),
            )
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                if isinstance(item.get("raw_state"), str):
                    try:
                        item["raw_state"] = json.loads(item["raw_state"])
                    except Exception:
                        pass
                results.append(item)
            return results

    def get_total_count(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ledger_entries")
            return cursor.fetchone()[0]

    def get_latest_rules_version(self) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM rules_history 
                ORDER BY version DESC LIMIT 1
                """
            )
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            try:
                res["terms"] = json.loads(res["terms_json"])
                res["stats"] = json.loads(res["stats_json"])
            except Exception:
                pass
            return res
