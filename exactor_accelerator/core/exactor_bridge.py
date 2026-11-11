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
        if self.use_cloud_api and not self.api_key:
            logger.warning(
                "EXACTOR cloud API is enabled but no credentials were provided "
                "(set EXACTOR_CORE_TOKEN or pass api_key). Cloud calls will be "
                "skipped and local engines used instead."
            )
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
        """Returns the configured EXACTOR Cloud credential, if any.

        No implicit account registration is performed: cloud access requires an
        explicit EXACTOR_CORE_TOKEN / api_key so that no data leaves the host
        without the operator's consent.
        """
        return self.api_key

    def _simplify_cloud(
        self,
        variables: List[str],
        minterms: List[int],
        dont_cares: List[int],
    ) -> Optional[ExactorSimplificationResult]:
        """Calls the remote EXACTOR Cloud API at exactor.tech."""
        token = self._get_cloud_auth_token()
        if not token:
            logger.warning(
                "Skipping EXACTOR Cloud API call: no EXACTOR_CORE_TOKEN/api_key "
                "configured. Falling back to local engines."
            )
            return None
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

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

                # The cloud response does not expose an evaluatable term
                # representation, so the local hypercube result is used for the
                # auditable terms/formula while cloud metrics are kept in stats.
                reducer = ExactorHypercubeReducer(variables)
                local_res = reducer.minimize(minterms, dont_cares)

                return ExactorSimplificationResult(
                    variables=variables,
                    terms=local_res.terms,
                    initial_minterm_count=len(minterms),
                    final_term_count=len(local_res.terms),
                    formula_expr=local_res.formula_expr,
                    xor_clauses=local_res.xor_clauses,
                    stats={
                        "engine": "exactor.tech-cloud-api",
                        "cloud_original_gates": data.get("original_gates"),
                        "cloud_new_gates": data.get("new_gates"),
                        "cloud_reduction_percent": data.get("reduction_percent"),
                        "cloud_execution_time_ms": data.get("execution_time_ms"),
                        "su_used": data.get("su_used", 1),
                    },
                )
            else:
                logger.warning(f"EXACTOR Cloud API returned status {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.warning(f"Failed to communicate with EXACTOR Cloud API ({self.cloud_base_url}): {e}")

        return None

    @staticmethod
    def _msb_to_lsb_minterm(minterm: int, num_vars: int) -> int:
        """
        Converts a minterm index from the local MSB-first convention
        (variable i occupies bit position num_vars-1-i) to the LSB-first
        convention used by the Rust exactor-core binding (variable i
        occupies bit position i).
        """
        converted = 0
        for i in range(num_vars):
            if (minterm >> (num_vars - 1 - i)) & 1:
                converted |= 1 << i
        return converted

    @staticmethod
    def _parse_product_terms(raw_terms: List[str], variables: List[str]) -> Optional[List[HypercubeTerm]]:
        """
        Converts espresso-style product term strings (e.g. "~a & b", "1")
        returned by the Rust core into HypercubeTerm objects so the result
        stays internally consistent and locally evaluatable.
        Returns None if any term cannot be parsed safely.
        """
        num_vars = len(variables)
        var_index = {name: i for i, name in enumerate(variables)}
        terms: List[HypercubeTerm] = []

        for raw in raw_terms:
            text = str(raw).strip()
            if not text or text in ("0", "FALSE", "false"):
                return None
            if text in ("1", "TRUE", "true"):
                terms.append(HypercubeTerm([HypercubeTerm.STATE_DC] * num_vars, num_vars))
                continue

            states = [HypercubeTerm.STATE_DC] * num_vars
            for literal in text.split("&"):
                lit = literal.strip()
                if not lit:
                    return None
                negated = lit.startswith("~") or lit.startswith("!")
                name = lit[1:].strip() if negated else lit
                idx = var_index.get(name)
                if idx is None:
                    return None
                states[idx] = HypercubeTerm.STATE_0 if negated else HypercubeTerm.STATE_1
            terms.append(HypercubeTerm(states, num_vars))

        return terms

    @staticmethod
    def _verify_terms_cover(
        terms: List[HypercubeTerm],
        on_set: set,
        care_set: set,
        num_vars: int,
        point_budget: int = 300_000,
    ) -> bool:
        """
        Exact verification that a set of parsed product terms reproduces the
        target function: every ON minterm must be covered and no term may cover
        an OFF-care point. Returns False when verification would be too
        expensive (caller must then fall back to the local engine).
        """
        budget = point_budget

        # 1. Every ON minterm must be matched by at least one term.
        for m in on_set:
            if budget <= 0:
                return False
            budget -= len(terms)
            if not any(t.matches(m) for t in terms):
                return False

        # 2. No term may cover a point outside ON-set U DC-set. Each term is a
        # subcube; enumerate its covered minterms (2^dc_count) and check
        # membership in the care set.
        for t in terms:
            dc_positions = [i for i, s in enumerate(t.states) if s == HypercubeTerm.STATE_DC]
            span = 1 << len(dc_positions)
            if span > budget:
                return False
            budget -= span

            base = 0
            for i, s in enumerate(t.states):
                if s == HypercubeTerm.STATE_1:
                    base |= 1 << (num_vars - 1 - i)
            for combo in range(span):
                m = base
                for j, pos in enumerate(dc_positions):
                    if (combo >> j) & 1:
                        m |= 1 << (num_vars - 1 - pos)
                if m not in care_set:
                    return False

        return True

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

        if not minterms:
            reducer = ExactorHypercubeReducer(variables)
            return reducer.minimize(minterms, dont_cares)

        # 1. Cloud API mode if requested or configured
        if self.use_cloud_api:
            cloud_result = self._simplify_cloud(variables, minterms, dont_cares)
            if cloud_result:
                return cloud_result
            logger.info("Falling back from Cloud API to local execution.")

        # 2. Local Rust Core
        if self._has_rust_core and self._rust_module:
            try:
                num_vars = len(variables)
                rust_minterms = [self._msb_to_lsb_minterm(m, num_vars) for m in minterms]
                rust_dont_cares = [self._msb_to_lsb_minterm(d, num_vars) for d in dont_cares]
                rust_res = self._rust_module.simplify_logic(variables, rust_minterms, rust_dont_cares)
                raw_terms = rust_res.get("terms", [])
                stats = rust_res.get("statistics", {})

                parsed_terms = self._parse_product_terms(raw_terms, variables)
                care_set = set(minterms) | set(dont_cares)
                if parsed_terms is None or not self._verify_terms_cover(
                    parsed_terms, set(minterms), care_set, num_vars
                ):
                    logger.warning(
                        "EXACTOR Rust core output failed verification "
                        "(unsupported term format or incorrect cover); "
                        "falling back to the local hypercube engine."
                    )
                else:
                    formula = " OR ".join([f"({t})" for t in raw_terms]) if raw_terms else "FALSE"
                    return ExactorSimplificationResult(
                        variables=variables,
                        terms=parsed_terms,
                        initial_minterm_count=stats.get("initial_terms", len(minterms)),
                        final_term_count=len(parsed_terms),
                        formula_expr=formula,
                        xor_clauses=[],
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
