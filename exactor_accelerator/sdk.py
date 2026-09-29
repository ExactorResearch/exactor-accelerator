"""
exactor_accelerator.sdk: Unified Neuro-Symbolic SDK (EXACTOR Core + TypeSafe JEV)

Provides a complete interface in 2 steps:
1. `engine.fit(df, target_col)`: EXACTOR discovers exact boolean rules (in milliseconds via Rust/C)
   and automatically calibrates the question schema for JEV.
   Supports Binary (C=2) and Multi-Class (C>2) datasets with parallel One-vs-Rest.
2. `engine.evaluate(event_state)`: Evaluates any live event with:
   - Exact formal deduction (zero hallucinations)
   - Calibrated probability and certainty (JEV RLCD)
   - Suggested autonomous business action
"""

from typing import Dict, Any, Optional, List, Union
import numpy as np
import pandas as pd
from exactor_accelerator.engine.runtime import HybridRuntime


class ExactorAccelerator:
    """
    High-level Neuro-Symbolic client: EXACTOR (HPC / Cloud API) + TypeSafe JEV.
    """

    def __init__(
        self,
        # Tokens
        exactor_token: Optional[str] = None,
        jev_token: Optional[str] = None,
        exactor_api_key: Optional[str] = None,
        jev_api_key: Optional[str] = None,
        api_key: Optional[str] = None,  # Jev legacy alias
        deepseek_api_key: Optional[str] = None,
        # Exactor Cloud config
        use_cloud_exactor: bool = False,
        exactor_base_url: Optional[str] = "https://exactor.tech",
        # Engine parameters
        db_path: str = "memory_ledger.db",
        default_threshold: float = 0.80,
        # Cold Start & Online Learning parameters
        cold_start: bool = False,
        auto_evolve_every: int = 25,
        fast_path_threshold: float = 0.80,
        seed_features: Optional[List[str]] = None,
    ):
        self.resolved_exactor_key = exactor_token or exactor_api_key
        self.resolved_jev_key = jev_token or jev_api_key or api_key
        self.deepseek_api_key = deepseek_api_key
        self.use_cloud_exactor = use_cloud_exactor or bool(self.resolved_exactor_key)
        self.exactor_base_url = exactor_base_url
        self.db_path = db_path
        self.default_threshold = default_threshold
        self.cold_start = cold_start
        self.auto_evolve_every = auto_evolve_every
        self.fast_path_threshold = fast_path_threshold
        self.seed_features = seed_features or []
        self.custom_choices: Optional[Any] = None

        self.runtime = self._create_runtime()
        self.is_multiclass: bool = False
        self.classes: List[Any] = []
        self.class_runtimes: Dict[Any, HybridRuntime] = {}
        self.class_formulas: Dict[Any, str] = {}

    def _create_runtime(self) -> HybridRuntime:
        rt = HybridRuntime(
            db_path=self.db_path,
            default_threshold=self.default_threshold,
            jev_api_key=self.resolved_jev_key,
            use_cloud_exactor=self.use_cloud_exactor,
            exactor_api_key=self.resolved_exactor_key,
            exactor_base_url=self.exactor_base_url,
            deepseek_api_key=self.deepseek_api_key,
            cold_start=self.cold_start,
            auto_evolve_every=self.auto_evolve_every,
            fast_path_threshold=self.fast_path_threshold,
            seed_features=self.seed_features,
        )
        if self.custom_choices:
            rt.set_choices(self.custom_choices)
        return rt

    def set_tokens(
        self,
        exactor_token: Optional[str] = None,
        jev_token: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
        use_cloud_exactor: Optional[bool] = None,
        exactor_base_url: Optional[str] = None,
    ):
        """Dynamically update EXACTOR, Jev, or DeepSeek tokens at runtime."""
        self.runtime.update_credentials(
            exactor_api_key=exactor_token,
            exactor_base_url=exactor_base_url,
            use_cloud_exactor=use_cloud_exactor,
            jev_api_key=jev_token,
            deepseek_api_key=deepseek_api_key,
        )
        for rt in self.class_runtimes.values():
            rt.update_credentials(
                exactor_api_key=exactor_token,
                exactor_base_url=exactor_base_url,
                use_cloud_exactor=use_cloud_exactor,
                jev_api_key=jev_token,
                deepseek_api_key=deepseek_api_key,
            )

    def set_choices(self, choices: Union[Dict[str, Optional[str]], List[str], List[Dict[str, str]]]):
        """
        Customize the catalog of business choices that Jev will select from.
        """
        self.custom_choices = choices
        self.runtime.set_choices(choices)
        for rt in self.class_runtimes.values():
            rt.set_choices(choices)

    # -------------------------------------------------------------------------
    # 1. TRAIN / DISCOVER HISTORICAL RULES (EXACTOR PHASE A)
    # -------------------------------------------------------------------------
    def fit(
        self,
        data: Union[pd.DataFrame, str, List[Dict[str, Any]]],
        target_col: str,
        max_variables: int = 16,
    ) -> Dict[str, Any]:
        """
        Train the logic engine on a historical dataset.
        Supports Binary and Multi-Class (C > 2) classification.
        """
        if isinstance(data, str):
            if data.endswith(".csv"):
                df = pd.read_csv(data)
            elif data.endswith(".json"):
                df = pd.read_json(data)
            else:
                raise ValueError("Unsupported file format. Use .csv or .json")
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise TypeError("`data` must be a DataFrame, file path, or list of dicts.")

        unique_targets = df[target_col].dropna().unique()
        n_classes = len(unique_targets)

        if n_classes <= 2:
            self.is_multiclass = False
            self.classes = sorted(list(unique_targets))
            result = self.runtime.phase_a_onboard(
                df=df,
                target_col=target_col,
                max_variables=max_variables,
                trigger_reason="SDK_FIT_METHOD",
            )
            return {
                "status": result.get("status"),
                "is_multiclass": False,
                "classes": self.classes,
                "boolean_formula": result.get("formula_expr"),
                "explanation": result.get("explanation"),
                "discovered_variables": result.get("variables"),
                "rule_clauses": result.get("xor_clauses"),
                "calibrated_jev_questions": result.get("jev_questions_count"),
            }
        else:
            # Multi-Class Induction
            self.is_multiclass = True
            self.classes = sorted(list(unique_targets))
            self.class_runtimes = {}
            self.class_formulas = {}
            variables_all = set()

            for c in self.classes:
                c_rt = self._create_runtime()
                target_bin_col = f"__target_class_{str(c).replace(' ', '_')}__"
                df_train = df.drop(columns=[target_col]).copy()
                df_train[target_bin_col] = (df[target_col] == c).astype(int)

                res_c = c_rt.phase_a_onboard(
                    df=df_train,
                    target_col=target_bin_col,
                    max_variables=max_variables,
                    trigger_reason=f"SDK_FIT_MULTICLASS_{c}",
                )
                self.class_runtimes[c] = c_rt
                self.class_formulas[c] = res_c.get("formula_expr")
                for v in res_c.get("variables", []):
                    variables_all.add(v)

            return {
                "status": "SUCCESS",
                "is_multiclass": True,
                "classes": self.classes,
                "formulas_per_class": self.class_formulas,
                "discovered_variables": sorted(list(variables_all)),
                "total_classes": len(self.classes),
            }

    # -------------------------------------------------------------------------
    # 2. LIVE EVALUATION (EXACTOR + JEV PHASE B)
    # -------------------------------------------------------------------------
    def evaluate(
        self,
        event: Dict[str, Any],
        confidence_threshold: Optional[float] = None,
        fast_path: bool = False,
    ) -> Dict[str, Any]:
        """
        Evaluate an event in real-time in sub-second latency using EXACTOR + JEV.
        """
        if not self.is_multiclass:
            if not self.runtime.is_initialized and not self.cold_start:
                raise RuntimeError("You must call engine.fit(data, target_col) before evaluating events.")

            query_res = self.runtime.phase_b_query(
                raw_state=event,
                confidence_threshold=confidence_threshold,
                fast_path=fast_path,
            )
            data = query_res.to_dict()

            return {
                "decision": data["decision_status"],
                "action": data["chosen_action"],
                "label": data["friendly_label"],
                "autonomous_execution": data["autonomous_action_executed"],
                "probabilistic_certainty": round(data["criterio_logico_prob"] * 100, 1),
                "exact_boolean_evaluation": data["exact_boolean_evaluation"],
                "triggered_endpoint": data["action_endpoint"],
                "action_details": data["action_details"],
                "explanation": data["action_details"],
                "latency_ms": round(data["latency_ms"], 2),
                "query_id": data["query_id"],
                "route": data.get("route", "FAST_PATH_LOCAL" if fast_path else "JEV_ORACLE"),
                "token_savings_pct": data.get("ahorro_tokens_pct", 0.0),
                "active_formula": data.get("formula_expr"),
                # Spanish compatibility aliases
                "accion": data["chosen_action"],
                "etiqueta": data["friendly_label"],
                "certeza_probabilistica": round(data["criterio_logico_prob"] * 100, 1),
                "evaluacion_exacta_booleana": data["exact_boolean_evaluation"],
                "ejecucion_autonoma": data["autonomous_action_executed"],
                "endpoint_disparado": data["action_endpoint"],
                "detalles_accion": data["action_details"],
                "explicacion_natural": data["action_details"],
                "latencia_ms": round(data["latency_ms"], 2),
            }
        else:
            # Multi-Class Evaluation
            import time
            t0 = time.perf_counter()
            class_scores = {}
            class_results = {}
            exact_matches = []

            for c, rt in self.class_runtimes.items():
                q_res = rt.phase_b_query(
                    raw_state=event,
                    confidence_threshold=confidence_threshold,
                    fast_path=fast_path,
                )
                class_results[c] = q_res
                score = float(q_res.criterio_logico_prob)
                if q_res.exact_boolean_evaluation == 1 or q_res.decision_status == "CRITICAL":
                    score += 1.0
                    exact_matches.append(c)
                class_scores[c] = max(0.01, score)

            # Softmax normalisation
            c_keys = list(class_scores.keys())
            raw_vals = np.array([class_scores[k] for k in c_keys])
            exp_vals = np.exp(raw_vals - np.max(raw_vals))
            probas = exp_vals / np.sum(exp_vals)
            proba_dict = {k: round(float(p) * 100, 1) for k, p in zip(c_keys, probas)}

            best_idx = int(np.argmax(probas))
            winning_class = c_keys[best_idx]
            winning_res = class_results[winning_class]
            latency_ms = (time.perf_counter() - t0) * 1000.0

            return {
                "winning_class": winning_class,
                "probability_distribution": proba_dict,
                "boolean_match_classes": exact_matches,
                "decision": winning_res.decision_status,
                "action": winning_res.chosen_action,
                "label": str(winning_class),
                "probabilistic_certainty": proba_dict[winning_class],
                "exact_boolean_evaluation": winning_res.exact_boolean_evaluation,
                "latency_ms": round(latency_ms, 2),
                "query_id": winning_res.query_id,
            }

    # -------------------------------------------------------------------------
    # 3. AUDITABLE NATURAL LANGUAGE EXPLANATION (DEEPSEEK)
    # -------------------------------------------------------------------------
    def explain(self, event: Dict[str, Any]) -> str:
        """
        Generate a plain-language explanation for clients or auditors.
        """
        if not self.is_multiclass:
            eval_res = self.runtime.phase_b_query(raw_state=event)
            exp = self.runtime.deepseek_explainer.generate_explanation(
                event_state=event,
                active_propositions=eval_res.propositions_evaluated,
                exact_eval=eval_res.exact_boolean_evaluation,
                criterio_prob=eval_res.criterio_logico_prob,
                chosen_action=eval_res.chosen_action,
                autonomous_executed=eval_res.autonomous_action_executed,
                rule_formula=self.runtime.current_rule.formula_expr if self.runtime.current_rule else None,
            )
            return exp.get("explanation", "")
        else:
            eval_dict = self.evaluate(event, fast_path=True)
            winning_c = eval_dict["winning_class"]
            winning_rt = self.class_runtimes[winning_c]
            eval_res = winning_rt.phase_b_query(raw_state=event, fast_path=True)
            
            exp = winning_rt.deepseek_explainer.generate_explanation(
                event_state=event,
                active_propositions=eval_res.propositions_evaluated,
                exact_eval=eval_res.exact_boolean_evaluation,
                criterio_prob=eval_res.criterio_logico_prob,
                chosen_action=eval_res.chosen_action,
                autonomous_executed=eval_res.autonomous_action_executed,
                rule_formula=self.class_formulas.get(winning_c, ""),
            )
            base_exp = exp.get("explanation", "")
            return f"**[Classified Category: {winning_c} ({eval_dict['probabilistic_certainty']}%)**\n{base_exp}"

    # -------------------------------------------------------------------------
    # 4. ONLINE SELF-LEARNING, FEEDBACK & TELEMETRY (COLD START)
    # -------------------------------------------------------------------------
    def record_feedback(self, query_id: str, label: int):
        """
        Record ground-truth feedback for a query (1 = positive/success, 0 = negative/false positive).
        Enables calibration and repair of the boolean rule against real outcomes.
        """
        self.runtime.ledger.record_feedback(query_id=query_id, label=label)

    def auto_evolve(self, window_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Force deduction or update of the boolean rule from interactions
        accumulated in the MemoryLedger.
        """
        return self.runtime.auto_evolve_from_ledger(window_size=window_size)

    def get_stats(self) -> Dict[str, Any]:
        """
        Return real-time model statistics: total queries, local queries,
        Jev token savings (%), rule version, and active variables.
        """
        return self.runtime.get_stats()
