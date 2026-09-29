"""
Hybrid Runtime Orchestrator: EXACTOR + Jev.
Coordinates Phase A (Initial Onboarding & Discovery), Phase B (Continuous Operation),
Autonomous Action Execution, and Differential Hot Updates over SQLite WAL Ledger.
"""

from typing import Dict, Any, Optional, List, Tuple, Union
import uuid
import time
import pandas as pd
import numpy as np
import logging

from ..ingestion.binarizer import AdaptiveBinarizer, BinarizationResult, Proposition
from ..core.hypercube import ExactorSimplificationResult
from ..core.exactor_bridge import ExactorBridge
from ..adapter.translator import ExactorToJevTranslator
from ..adapter.jev_schema import JevPayload
from ..ledger.sqlite_wal import MemoryLedger
from .jev_client import JevClient
from .deepseek_client import DeepSeekExplainer

logger = logging.getLogger("exactor_accelerator.runtime")


class QueryResult:
    """Encapsulates the real-time inference result of Phase B."""

    def __init__(
        self,
        query_id: str,
        raw_state: Dict[str, Any],
        minterm_val: int,
        minterm_binary: str,
        exact_boolean_evaluation: int,
        jev_response: Dict[str, Any],
        criterio_logico_prob: float,
        chosen_action: str,
        confidence: float,
        autonomous_action_executed: bool,
        action_details: str,
        latency_ms: float,
        rule_version: int,
        propositions_evaluated: Optional[Dict[str, int]] = None,
        deepseek_explanation: Optional[Dict[str, Any]] = None,
        decision_status: str = "SAFE",
        decision_category: str = "SAFE",
        friendly_label: str = "APROBADO",
        action_endpoint: str = "POST api.gateway/v1/authorize",
        route: str = "JEV_ORACLE",
        ahorro_tokens_pct: float = 0.0,
        formula_expr: Optional[str] = None,
    ):
        self.query_id = query_id
        self.raw_state = raw_state
        self.minterm_val = minterm_val
        self.minterm_binary = minterm_binary
        self.exact_boolean_evaluation = exact_boolean_evaluation
        self.jev_response = jev_response
        self.criterio_logico_prob = criterio_logico_prob
        self.chosen_action = chosen_action
        self.confidence = confidence
        self.autonomous_action_executed = autonomous_action_executed
        self.action_details = action_details
        self.latency_ms = latency_ms
        self.rule_version = rule_version
        self.propositions_evaluated = propositions_evaluated or {}
        self.deepseek_explanation = deepseek_explanation or {}
        self.decision_status = decision_status
        self.decision_category = decision_category
        self.friendly_label = friendly_label
        self.action_endpoint = action_endpoint
        self.route = route
        self.ahorro_tokens_pct = ahorro_tokens_pct
        self.formula_expr = formula_expr

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "raw_state": self.raw_state,
            "minterm_val": self.minterm_val,
            "minterm_binary": self.minterm_binary,
            "exact_boolean_evaluation": self.exact_boolean_evaluation,
            "criterio_logico_prob": self.criterio_logico_prob,
            "chosen_action": self.chosen_action,
            "confidence": self.confidence,
            "autonomous_action_executed": self.autonomous_action_executed,
            "action_details": self.action_details,
            "latency_ms": self.latency_ms,
            "rule_version": self.rule_version,
            "jev_response": self.jev_response,
            "propositions_evaluated": self.propositions_evaluated,
            "deepseek_explanation": self.deepseek_explanation,
            "decision_status": self.decision_status,
            "decision_category": self.decision_category,
            "friendly_label": self.friendly_label,
            "action_endpoint": self.action_endpoint,
            "route": self.route,
            "ahorro_tokens_pct": self.ahorro_tokens_pct,
            "formula_expr": self.formula_expr,
        }


class HybridRuntime:
    """
    Main controller for the EXACTOR + Jev Hybrid Architecture.
    Supports Cold Start (online self-distillation from user interactions without prior training data).
    """

    def __init__(
        self,
        db_path: str = "memory_ledger.db",
        default_threshold: float = 0.80,
        api_key: Optional[str] = None,
        jev_api_key: Optional[str] = None,
        use_cloud_exactor: bool = False,
        exactor_api_key: Optional[str] = None,
        exactor_base_url: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
        cold_start: bool = False,
        auto_evolve_every: int = 25,
        fast_path_threshold: float = 0.80,
        seed_features: Optional[List[str]] = None,
    ):
        self.db_path = db_path
        self.default_threshold = default_threshold
        self.cold_start = cold_start
        self.auto_evolve_every = auto_evolve_every
        self.fast_path_threshold = fast_path_threshold
        self.seed_features = seed_features or []

        self.binarizer = AdaptiveBinarizer(max_variables=12)
        self.bridge = ExactorBridge(
            prefer_native_rust=True,
            use_cloud_api=use_cloud_exactor,
            cloud_base_url=exactor_base_url,
            api_key=exactor_api_key,
        )
        self.translator = ExactorToJevTranslator()
        self.ledger = MemoryLedger(db_path=db_path)
        self.jev_client = JevClient(api_key=jev_api_key or api_key)
        self.deepseek_explainer = DeepSeekExplainer(api_key=deepseek_api_key)

        self.current_rule: Optional[ExactorSimplificationResult] = None
        self.current_rule_version: int = 1
        self.propositions_map: Dict[str, Proposition] = {}
        self.custom_action_choices: Optional[Dict[str, Optional[str]]] = None
        self.is_initialized: bool = True if cold_start else False

        # Live online learning & token savings telemetry
        self.total_queries: int = 0
        self.local_queries: int = 0
        self.jev_queries: int = 0
        self._cold_start_jev_calls: int = 0

    def set_choices(self, choices: Union[Dict[str, Optional[str]], List[str], List[Dict[str, str]]]):
        """
        Configures user-defined Choice actions for JEV business execution.
        Accepts:
          - Dict: {"TOTAL_BLOCK": "Description", "REQUIRE_2FA": "Description", ...}
          - List of str: ["BLOQUEO_TOTAL", "PEDIR_2FA", "APROBAR"]
          - List of Dicts: [{"name": "BLOQUEAR", "description": "..."}, ...]
        """
        if isinstance(choices, dict):
            self.custom_action_choices = choices
        elif isinstance(choices, list):
            parsed = {}
            for item in choices:
                if isinstance(item, str):
                    parsed[item] = f"Operational business action: {item}"
                elif isinstance(item, dict):
                    name = item.get("name") or item.get("choice") or item.get("id") or str(item)
                    desc = item.get("description") or item.get("desc") or f"Business action: {name}"
                    parsed[name] = desc
            self.custom_action_choices = parsed
        logger.info(f"Custom JEV Choices updated: {list(self.custom_action_choices.keys()) if self.custom_action_choices else 'None'}")

    def update_credentials(
        self,
        exactor_api_key: Optional[str] = None,
        exactor_base_url: Optional[str] = None,
        use_cloud_exactor: Optional[bool] = None,
        jev_api_key: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
    ):
        """Updates live API keys and endpoints for EXACTOR, Jev, and DeepSeek."""
        if exactor_api_key is not None:
            self.bridge.api_key = exactor_api_key
            self.bridge._cached_token = None
        if exactor_base_url is not None:
            self.bridge.cloud_base_url = exactor_base_url.rstrip("/")
            if self.bridge.cloud_base_url.startswith("http://exactor.tech"):
                self.bridge.cloud_base_url = self.bridge.cloud_base_url.replace("http://", "https://", 1)
        if use_cloud_exactor is not None:
            self.bridge.use_cloud_api = use_cloud_exactor
        if jev_api_key is not None:
            self.jev_client.api_key = jev_api_key
            self.jev_client.use_mock_simulator = not bool(jev_api_key) or jev_api_key.startswith("mock_")
        if deepseek_api_key is not None:
            self.deepseek_explainer.api_key = deepseek_api_key

    # -------------------------------------------------------------------------
    # FASE A: PUESTA EN MARCHA (Ingesta Inicial de Entrenamiento)
    # -------------------------------------------------------------------------

    def phase_a_onboard(
        self,
        df: pd.DataFrame,
        target_col: str,
        max_variables: int = 12,
        trigger_reason: str = "INITIAL_ONBOARDING",
    ) -> Dict[str, Any]:
        """
        Executes Phase A onboarding:
        1. Adaptive Binarization onto B^k
        2. Exactor Logic Discovery (AND, OR, XOR, NOT)
        3. Jev Schema Calibration
        4. Version Registration in SQLite WAL Ledger
        """
        logger.info(f"Phase A Onboarding starting with {len(df)} records. Target: {target_col}")

        # 1. Binarize
        self.binarizer = AdaptiveBinarizer(max_variables=max_variables)
        self.binarizer.fit(df, target_col=target_col)
        bin_res = self.binarizer.transform(df)

        self.propositions_map = {p.name: p for p in self.binarizer.propositions}
        self.translator.target_label = target_col

        # 2. Exactor Core Logic Discovery
        exactor_res = self.bridge.simplify(
            variables=bin_res.variables,
            minterms=bin_res.minterms_on,
            dont_cares=[],
        )
        self.current_rule = exactor_res
        self.current_rule_version += 1

        # 3. Calibrate Jev Schema
        questions_schema = self.translator.create_questions_schema(
            result=exactor_res,
            propositions_map=self.propositions_map,
            custom_action_choices=self.custom_action_choices,
        )

        # 4. Save to Ledger
        self.ledger.save_rules_version(
            version=self.current_rule_version,
            formula_expr=exactor_res.formula_expr,
            terms=[t.to_string(exactor_res.variables) for t in exactor_res.terms],
            hypercube_k=len(exactor_res.variables),
            sliding_window_size=len(df),
            trigger_reason=trigger_reason,
            stats=exactor_res.stats,
        )

        self.is_initialized = True

        return {
            "status": "SUCCESS",
            "rule_version": self.current_rule_version,
            "hypercube_dimension_k": len(exactor_res.variables),
            "variables": exactor_res.variables,
            "formula_expr": exactor_res.formula_expr,
            "xor_clauses": exactor_res.xor_clauses,
            "terms_count": exactor_res.final_term_count,
            "initial_minterms": exactor_res.initial_minterm_count,
            "stats": exactor_res.stats,
            "jev_questions_count": len(questions_schema),
            "explanation": self.translator.generate_human_explanation(exactor_res, self.propositions_map),
        }

    # -------------------------------------------------------------------------
    # FASE B: OPERACION CONTINUA Y MEMORIA VIVA (Sin Reentrenamiento)
    # -------------------------------------------------------------------------

    def _calculate_savings_pct(self) -> float:
        if self.total_queries == 0:
            return 0.0
        return round((self.local_queries / self.total_queries) * 100.0, 1)

    def _heuristic_cold_start_prob(self, raw_state: Dict[str, Any]) -> float:
        """Calibrated probabilistic heuristic for offline Jev simulation during Cold Start."""
        for k in ["prob", "probability", "probabilidad", "score", "risk", "riesgo"]:
            if k in raw_state and isinstance(raw_state[k], (int, float)):
                val = float(raw_state[k])
                return max(0.01, min(0.99, val if val <= 1.0 else val / 100.0))

        alert_terms = ["fraud", "fraude", "hack", "hackeo", "hackeada", "theft", "robo", "urgent", "urgente", "suspicious", "sospechoso", "irregular", "alert", "alerta"]
        text_str = ""
        for v in raw_state.values():
            if isinstance(v, str):
                text_str += " " + v.lower()
        if any(t in text_str for t in alert_terms):
            return 0.95

        for k, v in raw_state.items():
            k_low = k.lower()
            if any(term in k_low for term in ["attempt", "intento", "failed_pin"]) and isinstance(v, (int, float)) and v >= 3:
                return 0.92
            if any(term in k_low for term in ["amount", "monto"]) and isinstance(v, (int, float)) and v >= 3000:
                return 0.90
            if "rsi" in k_low and isinstance(v, (int, float)) and (v >= 70 or v <= 30):
                return 0.88

        return 0.08

    def _categorize_decision(
        self,
        criterio_prob: float,
        threshold: float,
        chosen_action: str,
        exact_bool_val: int = 0,
    ) -> Tuple[str, str, str, str, bool, str]:
        act_upper = chosen_action.upper()
        is_explicit_review = (
            "REVISION" in act_upper
            or "HUMAN" in act_upper
            or "ESCALA" in act_upper
            or "OBSERVACION" in act_upper
            or "GUARDIA" in act_upper
        )

        if exact_bool_val == 1:
            decision_status = "CRITICAL"
            decision_category = "CRITICAL"
            friendly_label = "PREVENTIVE BLOCK"
            action_endpoint = "POST api.gateway/v1/freeze"
            autonomous_executed = True
            action_details = (
                f"Autonomous action [{chosen_action}] executed: Risk rule matched with certainty ({criterio_prob:.1%}). "
                f"Operation preventively blocked to protect the platform."
            )
        elif criterio_prob >= threshold and not is_explicit_review:
            decision_status = "CRITICAL"
            decision_category = "CRITICAL"
            friendly_label = "PREVENTIVE BLOCK"
            action_endpoint = "POST api.gateway/v1/freeze"
            autonomous_executed = True
            action_details = (
                f"Autonomous action [{chosen_action}] executed: Risk rule matched with certainty ({criterio_prob:.1%}). "
                f"Operation preventively blocked to protect the platform."
            )
        elif is_explicit_review or (criterio_prob > (1.0 - threshold) and criterio_prob < threshold):
            decision_status = "REVIEW"
            decision_category = "REVIEW"
            friendly_label = "MANUAL REVIEW"
            action_endpoint = "POST api.gateway/v1/escalate"
            autonomous_executed = False
            action_details = (
                f"Preventive escalation for [{chosen_action}]: Borderline parameters with uncertainty ({criterio_prob:.1%}). "
                f"Sent to human review / 2FA queue."
            )
        else:
            decision_status = "SAFE"
            decision_category = "SAFE"
            friendly_label = "APPROVED"
            action_endpoint = "POST api.gateway/v1/authorize"
            autonomous_executed = True
            action_details = (
                f"Autonomous action [{chosen_action}] executed: Legitimate transaction with confidence ({(1.0 - criterio_prob):.1%}). "
                f"Direct pass authorized without friction."
            )

        return decision_status, decision_category, friendly_label, action_endpoint, autonomous_executed, action_details

    # -------------------------------------------------------------------------
    # FASE B: OPERACION CONTINUA Y MEMORIA VIVA (Sin Reentrenamiento)
    # -------------------------------------------------------------------------

    def phase_b_query(
        self,
        raw_state: Dict[str, Any],
        confidence_threshold: Optional[float] = None,
        query_id: Optional[str] = None,
        fast_path: bool = False,
    ) -> QueryResult:
        """
        Executes Phase B real-time inference with Dual Routing:
        - Route 1 (FAST_PATH_LOCAL): If a confident boolean rule covers the state (< 0.1 ms, 0 API tokens).
        - Route 2 (JEV_ORACLE): Cold-start discovery or boundary uncertainty, consulting JEV and logging to WAL.
        """
        if not self.is_initialized and not self.cold_start:
            raise RuntimeError("El sistema no ha completado la Fase A de puesta en marcha.")

        start_t = time.perf_counter()
        q_id = query_id or f"qry-{uuid.uuid4().hex[:10]}"
        threshold = confidence_threshold if confidence_threshold is not None else self.default_threshold
        self.total_queries += 1

        # -------------------------------------------------------------
        # CASE 1: INITIAL COLD START (No compiled rule yet)
        # -------------------------------------------------------------
        if self.current_rule is None:
            self.jev_queries += 1
            self._cold_start_jev_calls += 1
            route = "JEV_ORACLE"

            exact_bool_val = 0
            minterm_val = 0
            minterm_binary = "0"
            prop_dict: Dict[str, int] = {}

            if fast_path:
                criterio_prob = self._heuristic_cold_start_prob(raw_state)
                if self.custom_action_choices:
                    c_keys = list(self.custom_action_choices.keys())
                    chosen_action = c_keys[0] if criterio_prob >= threshold else c_keys[-1]
                else:
                    chosen_action = "BLOQUEAR_TRANSACCION" if criterio_prob >= threshold else "APROBAR_TRANSACCION"
                confidence = criterio_prob if criterio_prob >= threshold else (1.0 - criterio_prob)
                jev_resp = {
                    "id": f"jev-cold-{uuid.uuid4().hex[:8]}",
                    "fast_path": True,
                    "nouls": {"criterio_logico": {"noul": criterio_prob}},
                    "choices": {"accion_recomendada": {"choice": chosen_action, "confidence": confidence}},
                }
            else:
                if self.custom_action_choices:
                    criteria_dict = {
                        k: (v if v else f"Clase o accion {k}")
                        for k, v in self.custom_action_choices.items()
                    }
                else:
                    criteria_dict = {
                        "BLOQUEAR_TRANSACCION": "Transaccion con alto riesgo o anomalia",
                        "REVISION_MANUAL": "Transaccion con incertidumbre",
                        "APROBAR_TRANSACCION": "Transaccion legitima sin indicios de riesgo",
                    }
                default_questions = {
                    "criterio_logico": {
                        "type": "noul",
                        "instructions": "Determine if the event presents a risk condition, alert, or positive target.",
                        "criteria": {
                            "description": "Determine if the event presents a risk condition, alert, or positive target."
                        },
                    },
                    "accion_recomendada": {
                        "type": "choice",
                        "criteria": criteria_dict,
                    }
                }
                jev_resp = self.jev_client.evaluate(
                    state={"evento": raw_state},
                    questions=default_questions,
                    ground_truth_eval=None,
                )
                criterio_noul = jev_resp.get("nouls", {}).get("criterio_logico", {})
                criterio_prob = float(criterio_noul.get("noul", 0.50))
                action_choice = jev_resp.get("choices", {}).get("accion_recomendada", {})
                chosen_action = action_choice.get("choice", "REVISION_HUMANA")
                confidence = float(action_choice.get("confidence", criterio_prob))

            decision_status, decision_category, friendly_label, action_endpoint, autonomous_executed, action_details = (
                self._categorize_decision(criterio_prob, threshold, chosen_action, exact_bool_val=0)
            )

            decision_elapsed_ms = (time.perf_counter() - start_t) * 1000.0

            # Guardar en SQLite WAL Ledger
            self.ledger.record_interaction(
                query_id=q_id,
                raw_state=raw_state,
                minterm_val=minterm_val,
                minterm_binary=minterm_binary,
                questions_payload=raw_state,
                jev_response=jev_resp,
                criterio_logico_prob=criterio_prob,
                chosen_action=chosen_action,
                confidence=confidence,
                autonomous_action_executed=autonomous_executed,
                action_details=action_details,
                latency_ms=decision_elapsed_ms,
                rule_version=self.current_rule_version,
            )

            # Automated boolean deduction upon reaching interaction threshold
            if self.cold_start and self._cold_start_jev_calls >= self.auto_evolve_every:
                self.auto_evolve_from_ledger()

            return QueryResult(
                query_id=q_id,
                raw_state=raw_state,
                minterm_val=minterm_val,
                minterm_binary=minterm_binary,
                exact_boolean_evaluation=exact_bool_val,
                jev_response=jev_resp,
                criterio_logico_prob=criterio_prob,
                chosen_action=chosen_action,
                confidence=confidence,
                autonomous_action_executed=autonomous_executed,
                action_details=action_details,
                latency_ms=decision_elapsed_ms,
                rule_version=self.current_rule_version,
                propositions_evaluated=prop_dict,
                decision_status=decision_status,
                decision_category=decision_category,
                friendly_label=friendly_label,
                action_endpoint=action_endpoint,
                route=route,
                ahorro_tokens_pct=self._calculate_savings_pct(),
                formula_expr=self.current_rule.formula_expr if self.current_rule else None,
            )

        # -------------------------------------------------------------
        # CASE 2: ACTIVE RULE (Evaluation with Dual Routing)
        # -------------------------------------------------------------
        # Proyectar al hipercubo booleano
        minterm_val, prop_dict = self.binarizer.transform_single(raw_state)
        k = len(self.binarizer.variables)
        minterm_binary = format(minterm_val, f"0{k}b")

        # Evaluar regla booleana en microsegundos
        exact_bool_val = self.current_rule.evaluate_dict(prop_dict)

        # Routing criterion: explicit fast_path or boolean conviction
        use_local_fast_path = fast_path or (exact_bool_val == 1) or (
            self.cold_start and exact_bool_val == 0
        )

        if use_local_fast_path:
            self.local_queries += 1
            route = "FAST_PATH_LOCAL"

            criterio_prob = 0.96 if exact_bool_val == 1 else 0.04
            default_action = "BLOQUEAR_TRANSACCION" if exact_bool_val == 1 else "APROBAR_TRANSACCION"
            if self.custom_action_choices:
                choices_keys = list(self.custom_action_choices.keys())
                chosen_action = choices_keys[0] if exact_bool_val == 1 else choices_keys[-1]
            else:
                chosen_action = default_action
            confidence = criterio_prob if exact_bool_val == 1 else (1.0 - criterio_prob)
            jev_resp = {
                "id": f"jev-fast-{uuid.uuid4().hex[:8]}",
                "fast_path": True,
                "nouls": {"criterio_logico": {"noul": criterio_prob}},
                "choices": {"accion_recomendada": {"choice": chosen_action, "confidence": confidence}},
            }
        else:
            self.jev_queries += 1
            self._cold_start_jev_calls += 1
            route = "JEV_ORACLE"

            jev_payload = self.translator.build_payload(
                raw_event_state=raw_state,
                result=self.current_rule,
                propositions_map=self.propositions_map,
                custom_action_choices=self.custom_action_choices,
                include_all_questions=True,
            )
            jev_resp = self.jev_client.evaluate(
                state={"evento": raw_state},
                questions=jev_payload.to_dict()["questions"],
                ground_truth_eval=exact_bool_val,
            )
            criterio_noul = jev_resp.get("nouls", {}).get("criterio_logico", {})
            criterio_prob = float(criterio_noul.get("noul", 0.50))
            action_choice = jev_resp.get("choices", {}).get("accion_recomendada", {})
            chosen_action = action_choice.get("choice", "REVISION_HUMANA")
            confidence = float(action_choice.get("confidence", criterio_prob))

            # Periodic auto-evolve after accumulating new JEV queries
            if self.cold_start and self._cold_start_jev_calls % self.auto_evolve_every == 0:
                self.trigger_differential_update()

        decision_status, decision_category, friendly_label, action_endpoint, autonomous_executed, action_details = (
            self._categorize_decision(criterio_prob, threshold, chosen_action, exact_bool_val)
        )

        decision_elapsed_ms = (time.perf_counter() - start_t) * 1000.0

        # Registrar en Ledger
        self.ledger.record_interaction(
            query_id=q_id,
            raw_state=raw_state,
            minterm_val=minterm_val,
            minterm_binary=minterm_binary,
            questions_payload=raw_state,
            jev_response=jev_resp,
            criterio_logico_prob=criterio_prob,
            chosen_action=chosen_action,
            confidence=confidence,
            autonomous_action_executed=autonomous_executed,
            action_details=action_details,
            latency_ms=decision_elapsed_ms,
            rule_version=self.current_rule_version,
        )

        return QueryResult(
            query_id=q_id,
            raw_state=raw_state,
            minterm_val=minterm_val,
            minterm_binary=minterm_binary,
            exact_boolean_evaluation=exact_bool_val,
            jev_response=jev_resp,
            criterio_logico_prob=criterio_prob,
            chosen_action=chosen_action,
            confidence=confidence,
            autonomous_action_executed=autonomous_executed,
            action_details=action_details,
            latency_ms=decision_elapsed_ms,
            rule_version=self.current_rule_version,
            propositions_evaluated=prop_dict,
            decision_status=decision_status,
            decision_category=decision_category,
            friendly_label=friendly_label,
            action_endpoint=action_endpoint,
            route=route,
            ahorro_tokens_pct=self._calculate_savings_pct(),
            formula_expr=self.current_rule.formula_expr if self.current_rule else None,
        )

    def auto_evolve_from_ledger(self, window_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Automatically deduces or updates the boolean formula from interactions
        acumuladas en el MemoryLedger.
        """
        w = window_size or max(self.auto_evolve_every * 2, 50)
        recent_records = self.ledger.get_sliding_window_records(window_size=w)
        if not recent_records:
            return {"status": "NO_RECORDS", "message": "Not enough records in the ledger."}

        records_data = []
        labels = []
        for r in recent_records:
            raw = r.get("raw_state", {})
            if not isinstance(raw, dict):
                continue
            prob = float(r.get("criterio_logico_prob", 0.50))
            feedback = r.get("feedback_label")
            is_pos = 1 if (feedback == 1 or (feedback is None and prob >= self.fast_path_threshold)) else 0
            records_data.append(raw)
            labels.append(is_pos)

        if not records_data:
            return {"status": "NO_VALID_DATA"}

        import pandas as pd
        df = pd.DataFrame(records_data)
        df["__target__"] = labels

        # Fit binarizer if not yet fitted
        if not self.binarizer.is_fitted:
            self.binarizer.fit(df, target_col="__target__")
            self.propositions_map = {p.name: p for p in self.binarizer.propositions}

        b_res = self.binarizer.transform(df)
        minterms_on = b_res.minterms_on
        if not minterms_on:
            minterms_on = [0]

        new_rule = self.bridge.simplify(
            variables=self.binarizer.variables,
            minterms=minterms_on,
            dont_cares=[],
        )

        old_formula = self.current_rule.formula_expr if self.current_rule else None
        self.current_rule = new_rule
        self.current_rule_version += 1
        self.is_initialized = True

        self.ledger.save_rules_version(
            version=self.current_rule_version,
            formula_expr=new_rule.formula_expr,
            terms=[t.to_string(new_rule.variables) for t in new_rule.terms],
            hypercube_k=len(new_rule.variables),
            sliding_window_size=len(records_data),
            trigger_reason="COLD_START_AUTO_EVOLVE",
            stats=new_rule.stats,
        )

        return {
            "status": "EVOLVED",
            "rule_version": self.current_rule_version,
            "old_formula": old_formula,
            "new_formula": new_rule.formula_expr,
            "terms_count": new_rule.final_term_count,
            "variables": self.binarizer.variables,
            "ahorro_tokens_pct": self._calculate_savings_pct(),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Returns live telemetry of the engine, token savings, and active rule."""
        savings = self._calculate_savings_pct()
        formula = self.current_rule.formula_expr if self.current_rule else None
        return {
            "cold_start": self.cold_start,
            "is_initialized": self.is_initialized,
            "total_queries": self.total_queries,
            "local_queries": self.local_queries,
            "jev_queries": self.jev_queries,
            "token_savings_pct": savings,
            "ahorro_tokens_pct": savings,
            "rule_version": self.current_rule_version,
            "active_formula": formula,
            "formula_activa": formula,
            "active_propositions": len(self.binarizer.variables),
            "proposiciones_activas": len(self.binarizer.variables),
            "variables": self.binarizer.variables,
        }

    # -------------------------------------------------------------------------
    # ACTUALIZACION DIFERENCIAL (Exactor Incremental en Caliente)
    # -------------------------------------------------------------------------

    def trigger_differential_update(self, window_size: int = 30) -> Dict[str, Any]:
        """
        Incremental Differential Update:
        Inspects the sliding window of recent ledger interactions to hot-adjust
        Exactor logical rules and re-calibrate the Jev Schema without offline retraining.
        """
        if not self.is_initialized or self.current_rule is None:
            raise RuntimeError("The system is not initialized.")

        recent_records = self.ledger.get_sliding_window_records(window_size=window_size)
        if not recent_records:
            return {"status": "NO_RECORDS", "message": "Not enough records in the ledger."}

        # Aggregate minterms from recent window where outcome was positive or verified
        current_on_minterms = set()
        for term in self.current_rule.terms:
            current_on_minterms.update(term.covered_minterms)

        window_positive_minterms = set()
        for r in recent_records:
            # Verified label takes precedence, otherwise calibrated prob >= 0.70
            label = r.get("feedback_label")
            prob = r.get("criterio_logico_prob", 0.0)
            m_val = r.get("minterm_val")
            if m_val is not None:
                if label == 1 or (label is None and prob >= 0.70):
                    window_positive_minterms.add(m_val)

        # Differential merge
        new_minterms = sorted(list(current_on_minterms.union(window_positive_minterms)))

        # Re-minimize with Exactor in hot memory
        new_result = self.bridge.simplify(
            variables=self.binarizer.variables,
            minterms=new_minterms,
            dont_cares=[],
        )

        old_formula = self.current_rule.formula_expr
        self.current_rule = new_result
        self.current_rule_version += 1

        # Save to rules ledger
        self.ledger.save_rules_version(
            version=self.current_rule_version,
            formula_expr=new_result.formula_expr,
            terms=[t.to_string(new_result.variables) for t in new_result.terms],
            hypercube_k=len(new_result.variables),
            sliding_window_size=len(recent_records),
            trigger_reason="DIFFERENTIAL_HOT_UPDATE",
            stats=new_result.stats,
        )

        return {
            "status": "UPDATED",
            "rule_version": self.current_rule_version,
            "window_size": len(recent_records),
            "old_formula": old_formula,
            "new_formula": new_result.formula_expr,
            "new_terms_count": new_result.final_term_count,
            "stats": new_result.stats,
            "explanation": self.translator.generate_human_explanation(new_result, self.propositions_map),
        }
