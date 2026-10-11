"""
Bridge to the EXACTOR Boolean Minimization Engine (adapted from exactor-jev).

Dispatch order: EXACTOR Cloud API (opt-in) -> native Rust `exactor` binding -> built-in
hypercube reducer. Always returns an ExactorSimplificationResult whose `terms` can be
evaluated locally in the Fast-Path.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

import requests

from .hypercube import ExactorHypercubeReducer, ExactorSimplificationResult

logger = logging.getLogger("exactor_engram.core")


class ExactorBridge:
    def __init__(self, prefer_native_rust: bool = True, use_cloud_api: Optional[bool] = None):
        self.prefer_native_rust = prefer_native_rust
        self.use_cloud_api = (
            use_cloud_api
            if use_cloud_api is not None
            else os.getenv("EXACTOR_USE_CLOUD", "").lower() in ("1", "true", "yes")
        )
        self.cloud_base_url = os.getenv("EXACTOR_BASE_URL", "https://exactor.tech").rstrip("/")
        self.api_key = os.getenv("EXACTOR_CORE_TOKEN") or os.getenv("EXACTOR_API_KEY")
        self._rust_module = None
        if prefer_native_rust:
            try:
                import exactor  # type: ignore

                self._rust_module = exactor
                logger.info("EXACTOR Core Rust binding detected.")
            except ImportError:
                logger.info("Rust binding not found; using built-in hypercube reducer.")

    @property
    def engine_name(self) -> str:
        if self.use_cloud_api:
            return "exactor.tech-cloud-api"
        if self._rust_module is not None:
            return "exactor-core-rust-hpc"
        return "exactor-local-hypercube"

    def _simplify_cloud(
        self, variables: List[str], minterms: List[int], dont_cares: List[int]
    ) -> Optional[ExactorSimplificationResult]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            resp = requests.post(
                f"{self.cloud_base_url}/api/simplify",
                headers=headers,
                json={"variables": variables, "minterms": minterms, "dont_cares": dont_cares},
                timeout=20,
            )
            if resp.status_code == 200:
                data = resp.json()
                local = ExactorHypercubeReducer(variables).minimize(minterms, dont_cares)
                local.formula_expr = data.get("result") or local.formula_expr
                local.stats.update({"engine": "exactor.tech-cloud-api", "su_used": data.get("su_used", 1)})
                return local
            logger.warning("EXACTOR Cloud API status %s", resp.status_code)
        except Exception as exc:  # pragma: no cover - network
            logger.warning("EXACTOR Cloud API unavailable: %s", exc)
        return None

    def simplify(
        self, variables: List[str], minterms: List[int], dont_cares: Optional[List[int]] = None
    ) -> ExactorSimplificationResult:
        """Exact boolean minimization. Zero floating point. Deterministic and auditable."""
        dont_cares = dont_cares or []
        if len(variables) > 64:
            raise ValueError(f"Límite del hipercubo: 64 variables (recibidas {len(variables)}).")

        if self.use_cloud_api:
            res = self._simplify_cloud(variables, minterms, dont_cares)
            if res is not None:
                return res

        if self._rust_module is not None:
            try:
                rust_res = self._rust_module.simplify_logic(variables, minterms, dont_cares)
                local = ExactorHypercubeReducer(variables).minimize(minterms, dont_cares)
                raw_terms = rust_res.get("terms", [])
                if raw_terms:
                    local.formula_expr = " OR ".join(f"({t})" for t in raw_terms)
                local.stats.update({**rust_res.get("statistics", {}), "engine": "exactor-core-rust-hpc"})
                return local
            except Exception as exc:  # pragma: no cover
                logger.warning("Rust core error (%s); falling back.", exc)

        result = ExactorHypercubeReducer(variables).minimize(minterms, dont_cares)
        result.stats["engine"] = "exactor-local-hypercube"
        return result
