"""
Bridge connecting the hybrid runtime to the EXACTOR Boolean Minimization Engine.
Seamlessly uses Cloud API (https://exactor.tech), native Rust exactor-core, or the built-in Hypercube Reducer.
"""

from typing import List, Optional, Dict, Any
import os
import logging
import requests
from .hypercube import ExactorHypercubeReducer, ExactorSimplificationResult, HypercubeTerm

logger = logging.getLogger("exactor_accelerator.core")


class ExactorBridge:
    """Universal dispatcher for the EXACTOR Boolean minimization engine (Cloud API, Rust HPC, or Hypercube)."""

    def __init__(
        self,
        prefer_native_rust: bool = True,
        use_cloud_api: bool = False,
        cloud_base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        # Import centralized config (lazy to avoid circular imports)
        from exactor_accelerator.config import get_config
        cfg = get_config()

        self.prefer_native_rust = prefer_native_rust
        self.use_cloud_api = use_cloud_api or os.getenv("EXACTOR_USE_CLOUD", "").lower() in ("1", "true", "yes")
        self.cloud_base_url = (
            cloud_base_url
            or cfg.exactor_base_url
            or os.getenv("EXACTOR_BASE_URL", "https://exactor.tech")
        ).rstrip("/")
        # Fix scheme if user provides http for exactor.tech (redirects to https)
        if self.cloud_base_url.startswith("http://exactor.tech"):
            self.cloud_base_url = self.cloud_base_url.replace("http://", "https://", 1)

        self.api_key = (
            api_key
            or cfg.exactor_core_token
            or os.getenv("EXACTOR_CORE_TOKEN")
            or os.getenv("EXACTOR_API_KEY")
        )
        self._cached_token = None
        self._has_rust_core = False
        self._rust_module = None
        self._detect_rust_core()

    def __getstate__(self):
        state = self.__dict__.copy()
        # Remove Python module reference to allow pickling
        state["_rust_module"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._rust_module = None
        self._detect_rust_core()

    def _detect_rust_core(self):
        if not self.prefer_native_rust:
            return

        try:
            import exactor  # type: ignore
            self._rust_module = exactor
            self._has_rust_core = True
            logger.info("EXACTOR Core Rust binding detected and active.")
        except ImportError:
            self._has_rust_core = False
            logger.info("Using built-in Boolean Hypercube Gray-code Reducer engine.")

    @property
    def is_rust_native(self) -> bool:
        return self._has_rust_core

    def _get_cloud_auth_token(self) -> Optional[str]:
        """Gets or creates a JWT/API token for exactor.tech."""
        if self.api_key:
            return self.api_key
        if self._cached_token:
            return self._cached_token

        # Try automatic ephemeral registration on exactor.tech if no key is provided
        try:
            import uuid
            ephemeral_email = f"jev_user_{uuid.uuid4().hex[:8]}@exactor.tech"
            ephemeral_password = f"P@ss_{uuid.uuid4().hex[:10]}"
            reg_resp = requests.post(
                f"{self.cloud_base_url}/api/auth/register",
                json={"email": ephemeral_email, "password": ephemeral_password},
                timeout=10,
            )
            if reg_resp.status_code in [200, 201]:
                self._cached_token = reg_resp.json().get("token")
                return self._cached_token
        except Exception as e:
            logger.warning(f"Could not auto-register on {self.cloud_base_url}: {e}")

        return None

    def _simplify_cloud(
        self,
        variables: List[str],
        minterms: List[int],
        dont_cares: List[int],
    ) -> Optional[ExactorSimplificationResult]:
        """Calls the remote EXACTOR Cloud API at exactor.tech."""
        token = self._get_cloud_auth_token()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        payload = {
            "variables": variables,
            "minterms": minterms,
            "dont_cares": dont_cares,
        }

        try:
            url = f"{self.cloud_base_url}/api/simplify"
            logger.info(f"Invoking EXACTOR Cloud API: {url} with {len(variables)} vars and {len(minterms)} minterms")
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            
            if resp.status_code == 200:
                data = resp.json()
                result_expr = data.get("result", "")
                
                # Parse or generate hypercube terms for local fast evaluations
                reducer = ExactorHypercubeReducer(variables)
                local_res = reducer.minimize(minterms, dont_cares)

                return ExactorSimplificationResult(
                    variables=variables,
                    terms=local_res.terms,
                    initial_minterm_count=data.get("original_gates", len(minterms)),
                    final_term_count=data.get("new_gates", len(local_res.terms)),
                    formula_expr=result_expr or local_res.formula_expr,
                    xor_clauses=local_res.xor_clauses,
                    stats={
                        "engine": "exactor.tech-cloud-api",
                        "reduction_percent": data.get("reduction_percent"),
                        "execution_time_ms": data.get("execution_time_ms"),
                        "espresso": data.get("espresso"),
                        "verilog": data.get("verilog"),
                        "vhdl": data.get("vhdl"),
                        "su_used": data.get("su_used", 1),
                    },
                )
            else:
                logger.warning(f"EXACTOR Cloud API returned status {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.warning(f"Failed to communicate with EXACTOR Cloud API ({self.cloud_base_url}): {e}")

        return None

    def simplify(
        self,
        variables: List[str],
        minterms: List[int],
        dont_cares: Optional[List[int]] = None,
    ) -> ExactorSimplificationResult:
        """
        Minimizes the Boolean function defined by the given variables and ON-set minterms.
        Zero floating point operations. 100% deterministic and auditable.
        """
        dont_cares = dont_cares or []

        # Enforce hypercube limit: k <= 64
        if len(variables) > 64:
            raise ValueError(f"EXACTOR Hypercube limit: maximum 64 variables. Provided: {len(variables)}")

        # 1. Cloud API mode if requested or configured
        if self.use_cloud_api:
            cloud_result = self._simplify_cloud(variables, minterms, dont_cares)
            if cloud_result:
                return cloud_result
            logger.info("Falling back from Cloud API to local execution.")

        # 2. Local Rust Core
        if self._has_rust_core and self._rust_module:
            try:
                rust_res = self._rust_module.simplify_logic(variables, minterms, dont_cares)
                raw_terms = rust_res.get("terms", [])
                stats = rust_res.get("statistics", {})
                
                formula = " OR ".join([f"({t})" for t in raw_terms]) if raw_terms else "FALSE"
                
                reducer = ExactorHypercubeReducer(variables)
                local_res = reducer.minimize(minterms, dont_cares)

                return ExactorSimplificationResult(
                    variables=variables,
                    terms=local_res.terms,
                    initial_minterm_count=stats.get("initial_terms", len(minterms)),
                    final_term_count=len(raw_terms) or len(local_res.terms),
                    formula_expr=formula if raw_terms else local_res.formula_expr,
                    xor_clauses=local_res.xor_clauses,
                    stats={
                        **stats,
                        "engine": "exactor-core-rust-hpc",
                    },
                )
            except Exception as e:
                logger.warning(f"Rust core call encountered error ({e}); falling back to hypercube engine.")

        # 3. Built-in Local Hypercube Minimizer
        reducer = ExactorHypercubeReducer(variables)
        result = reducer.minimize(minterms, dont_cares)
        result.stats["engine"] = "exactor-local-hypercube-fallback"
        return result
