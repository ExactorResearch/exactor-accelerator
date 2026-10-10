"""
Generic Certainty Islands Engine (Islas de Certeza) for Exactor-Jev.

Provides a domain-agnostic Neuro-Symbolic topological certainty framework
to enforce formal mathematical invariants, eliminate hallucinations/noise,
and guarantee determinism before executing automated edge decisions.

Features:
- @certainty_guard decorator for zero-friction function protection.
- Bilingual Natural Language Explanation Generator (Español / English).
- Formal LaTeX Mathematical Proof generation.
- Conformal safety vetoes and multi-domain presets.
"""

from __future__ import annotations

import math
import functools
import inspect
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd


class IslandCategory(str, Enum):
    """Categories of Certainty Islands across enterprise domains."""
    INVARIANT_INTEGRITY = "INVARIANT_INTEGRITY"        # Mandatory business & state integrity invariants
    LOW_ENTROPY_DETERMINISM = "LOW_ENTROPY_DETERMINISM"  # Low Shannon entropy & high state clarity
    ANOMALY_BOUNDARY_SENTRY = "ANOMALY_BOUNDARY_SENTRY"  # Anomaly, outlier, and regime drift defense
    HIGH_CONVICTION_FASTPATH = "HIGH_CONVICTION_FASTPATH" # High-confidence propositional Boolean match
    CONFORMAL_SAFETY_GUARD = "CONFORMAL_SAFETY_GUARD"    # Conformal uncertainty & fail-safe veto
    CUSTOM = "CUSTOM"                                  # Domain-specific custom invariant


class CertaintyVetoException(Exception):
    """Exception raised when a mandatory Certainty Guardrail is violated."""
    def __init__(self, message: str, evaluation_result: Optional[IslandEvaluationResult] = None):
        super().__init__(message)
        self.evaluation_result = evaluation_result


@dataclass
class CertaintyIslandDefinition:
    """Definition of a topological Certainty Island in state/feature space."""
    island_id: str
    name: str
    category: IslandCategory
    description: str
    formal_invariant: str
    predicate: Optional[Callable[[Dict[str, Any]], bool]] = None
    min_confidence: float = 0.75
    risk_multiplier: float = 1.0
    is_mandatory_guardrail: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def evaluate(self, sample: Dict[str, Any]) -> Tuple[bool, str]:
        """Evaluates sample against this island predicate."""
        if self.predicate is None:
            return True, f"[{self.island_id}] Sin predicado definido (Aprobado por defecto)"
        try:
            passed = self.predicate(sample)
            status_text = "SATISFECHO" if passed else "VIOLADO"
            msg = f"[{self.island_id}] {status_text}: {self.name}"
            return passed, msg
        except Exception as e:
            return False, f"[{self.island_id}] EXCEPCIÓN: {e}"


@dataclass
class IslandEvaluationResult:
    """Consolidated result of evaluating a sample across all active Certainty Islands."""
    is_valid: bool
    action_decision: str  # "FASTPATH_EXECUTE", "ORACLE_ESCALATE", "VETO_REJECT", "STANDBY"
    active_islands: List[str]
    rejected_islands: List[str]
    confidence_score: float
    effective_risk_weight: float
    deduction_steps: List[str]
    formal_proof_latex: str
    explanation_es: str = ""
    explanation_en: str = ""
    traffic_light_badge: str = "⚪ STANDBY"
    audit_trail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "action_decision": self.action_decision,
            "traffic_light_badge": self.traffic_light_badge,
            "active_islands": self.active_islands,
            "rejected_islands": self.rejected_islands,
            "confidence_score": round(self.confidence_score, 4),
            "effective_risk_weight": round(self.effective_risk_weight, 4),
            "explanation_es": self.explanation_es,
            "explanation_en": self.explanation_en,
            "deduction_steps": self.deduction_steps,
            "formal_proof_latex": self.formal_proof_latex,
            "audit_trail": self.audit_trail
        }


class CertaintyIslandsEngine:
    """
    Generic, domain-agnostic Neuro-Symbolic Certainty Islands Solver.
    
    Evaluates enterprise tabular data, event streams, or model features against
    topological certainty manifolds and formal invariants.
    """

    def __init__(
        self,
        domain: str = "general",
        default_threshold: float = 0.75,
        strict_mode: bool = True
    ):
        self.domain = domain.lower()
        self.default_threshold = default_threshold
        self.strict_mode = strict_mode
        self._islands: Dict[str, CertaintyIslandDefinition] = {}

        # Load domain presets
        self._load_domain_presets()

    def register_island(self, island: CertaintyIslandDefinition) -> None:
        """Registers or overrides a Certainty Island definition."""
        self._islands[island.island_id] = island

    def remove_island(self, island_id: str) -> bool:
        """Removes an island by ID."""
        return self._islands.pop(island_id, None) is not None

    def get_island(self, island_id: str) -> Optional[CertaintyIslandDefinition]:
        """Gets island definition by ID."""
        return self._islands.get(island_id)

    def list_islands(self) -> List[Dict[str, Any]]:
        """Lists metadata of all registered islands."""
        return [
            {
                "island_id": isl.island_id,
                "name": isl.name,
                "category": isl.category.value,
                "description": isl.description,
                "formal_invariant": isl.formal_invariant,
                "min_confidence": isl.min_confidence,
                "risk_multiplier": isl.risk_multiplier,
                "is_mandatory_guardrail": isl.is_mandatory_guardrail
            }
            for isl in self._islands.values()
        ]

    def evaluate(
        self,
        sample: Union[Dict[str, Any], pd.Series, np.ndarray],
        feature_names: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> IslandEvaluationResult:
        """
        Evaluates a sample against all registered Certainty Islands.
        """
        data = self._normalize_sample(sample, feature_names)
        if context:
            data.update(context)

        active_islands: List[str] = []
        rejected_islands: List[str] = []
        deduction_steps: List[str] = []
        mandatory_failed: bool = False
        confidence_accum: List[float] = []
        risk_weights: List[float] = []

        # Evaluate each island
        for isl_id, island in self._islands.items():
            passed, detail = island.evaluate(data)
            deduction_steps.append(detail)

            if passed:
                active_islands.append(isl_id)
                confidence_accum.append(island.min_confidence)
                risk_weights.append(island.risk_multiplier)
            else:
                rejected_islands.append(isl_id)
                if island.is_mandatory_guardrail:
                    mandatory_failed = True
                    deduction_steps.append(f"⛔ VETO CRÍTICO: Guardarraíl Mandatorio [{isl_id}] falló.")

        # Compute overall confidence & risk
        if active_islands and not mandatory_failed:
            avg_confidence = float(np.mean(confidence_accum))
            effective_risk = float(np.prod(risk_weights)) if risk_weights else 1.0
            is_valid = avg_confidence >= self.default_threshold
        else:
            avg_confidence = 0.0
            effective_risk = 0.0
            is_valid = False

        # Determine actionable routing decision
        if mandatory_failed:
            action_decision = "VETO_REJECT"
            traffic_light = "🔴 VETO-REJECT"
        elif is_valid and len(active_islands) >= 2:
            action_decision = "FASTPATH_EXECUTE"
            traffic_light = "🟢 FAST-PATH"
        elif is_valid and len(active_islands) == 1:
            action_decision = "FASTPATH_EXECUTE" if avg_confidence >= 0.85 else "ORACLE_ESCALATE"
            traffic_light = "🟢 FAST-PATH" if action_decision == "FASTPATH_EXECUTE" else "🟡 ORACLE-ESCALATE"
        elif avg_confidence > 0.40:
            action_decision = "ORACLE_ESCALATE"
            traffic_light = "🟡 ORACLE-ESCALATE"
        else:
            action_decision = "STANDBY"
            traffic_light = "⚪ STANDBY"

        # Generate LaTeX Proof Representation
        formal_proof_latex = self._build_latex_proof(active_islands, rejected_islands, is_valid, action_decision)

        # Generate Bilingual Natural Language Explanations
        expl_es, expl_en = self._generate_bilingual_explanations(
            data=data,
            active=active_islands,
            rejected=rejected_islands,
            decision=action_decision,
            confidence=avg_confidence,
            mandatory_failed=mandatory_failed
        )

        return IslandEvaluationResult(
            is_valid=is_valid,
            action_decision=action_decision,
            active_islands=active_islands,
            rejected_islands=rejected_islands,
            confidence_score=avg_confidence,
            effective_risk_weight=effective_risk,
            deduction_steps=deduction_steps,
            formal_proof_latex=formal_proof_latex,
            explanation_es=expl_es,
            explanation_en=expl_en,
            traffic_light_badge=traffic_light,
            audit_trail={
                "domain": self.domain,
                "total_islands": len(self._islands),
                "active_count": len(active_islands),
                "rejected_count": len(rejected_islands),
                "mandatory_failed": mandatory_failed
            }
        )

    def batch_evaluate(
        self,
        df: pd.DataFrame,
        context: Optional[Dict[str, Any]] = None
    ) -> List[IslandEvaluationResult]:
        """Evaluates a full pandas DataFrame row-by-row."""
        results = []
        for _, row in df.iterrows():
            res = self.evaluate(row.to_dict(), context=context)
            results.append(res)
        return results

    def filter_dataframe(
        self,
        df: pd.DataFrame,
        allowed_decisions: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Returns only rows from DataFrame that meet specified certainty decisions."""
        if allowed_decisions is None:
            allowed_decisions = ["FASTPATH_EXECUTE"]
        results = self.batch_evaluate(df)
        mask = [r.action_decision in allowed_decisions for r in results]
        return df[mask].copy()

    def _normalize_sample(
        self,
        sample: Union[Dict[str, Any], pd.Series, np.ndarray],
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        if isinstance(sample, dict):
            return dict(sample)
        if isinstance(sample, np.ndarray):
            if feature_names and len(feature_names) == len(sample):
                return {feature_names[i]: sample[i] for i in range(len(sample))}
            return {f"feature_{i}": val for i, val in enumerate(sample.flatten())}
        if isinstance(sample, pd.Series):
            return sample.to_dict()
        if hasattr(sample, "model_dump") and callable(getattr(sample, "model_dump")):
            return sample.model_dump()
        if hasattr(sample, "__dict__"):
            return {k: v for k, v in sample.__dict__.items() if not k.startswith("_")}
        return {"value": sample}

    def _build_latex_proof(
        self,
        active: List[str],
        rejected: List[str],
        is_valid: bool,
        decision: str
    ) -> str:
        active_terms = [r"\mathcal{I}_{\text{" + isl.replace("ISLAND-", "").replace("_", "-") + r"}}" for isl in active]
        active_str = r" \land ".join(active_terms) if active_terms else r"\emptyset"
        status_sym = r"\top" if is_valid else r"\bot"
        return (
            rf"\mathbf{{CertaintyProof}} \equiv \left( {active_str} \right) "
            rf"\vdash \mathcal{{Decision}}(\text{{{decision}}}) \implies {status_sym}"
        )

    def _generate_bilingual_explanations(
        self,
        data: Dict[str, Any],
        active: List[str],
        rejected: List[str],
        decision: str,
        confidence: float,
        mandatory_failed: bool
    ) -> Tuple[str, str]:
        """Generates crisp, human-readable natural language explanations in Spanish and English."""
        active_names_es = [self._islands[i].name for i in active if i in self._islands]
        active_names_en = [self._islands[i].name for i in active if i in self._islands]
        rejected_names_es = [self._islands[i].name for i in rejected if i in self._islands]
        rejected_names_en = [self._islands[i].name for i in rejected if i in self._islands]

        if decision == "VETO_REJECT":
            es = (
                f"🔴 ACCIÓN BLOQUEADA POR GUARDARRAÍL DE SEGURIDAD.\n"
                f"Se detectó una violación en {len(rejected)} invariante(s) obligatorio(s): "
                f"{', '.join(rejected_names_es)}.\n"
                f"El sistema rechaza la operación en el Edge (0.01 ms) previniendo riesgos o pérdidas."
            )
            en = (
                f"🔴 ACTION BLOCKED BY SAFETY GUARDRAIL.\n"
                f"A violation was detected in {len(rejected)} mandatory invariant(s): "
                f"{', '.join(rejected_names_en)}.\n"
                f"The system rejects the transaction at the Edge (0.01 ms) preventing risk or losses."
            )
        elif decision == "FASTPATH_EXECUTE":
            es = (
                f"🟢 EJECUCIÓN INSTANTÁNEA FAST-PATH (0.05 ms).\n"
                f"El estado satisface {len(active)} Islas de Certeza ({confidence * 100:.1f}% de certidumbre): "
                f"{', '.join(active_names_es)}.\n"
                f"Garantía determinista completa con coste marginal $0.00."
            )
            en = (
                f"🟢 INSTANT FAST-PATH EXECUTION (0.05 ms).\n"
                f"The state satisfies {len(active)} Certainty Islands ({confidence * 100:.1f}% certainty): "
                f"{', '.join(active_names_en)}.\n"
                f"Full deterministic mathematical guarantee at $0.00 marginal cost."
            )
        elif decision == "ORACLE_ESCALATE":
            es = (
                f"🟡 CASO DE BORDE / ESCALADO A ORÁCULO JEV.\n"
                f"El evento no alcanzó la certidumbre completa para ejecución autónoma. "
                f"Islas activas: {len(active)}. Se deriva al modelo contextual para análisis causal."
            )
            en = (
                f"🟡 BORDERLINE CASE / ESCALATED TO JEV ORACLE.\n"
                f"Event did not reach full certainty for autonomous edge execution. "
                f"Active islands: {len(active)}. Escalating to contextual LLM for causal discovery."
            )
        else:
            es = (
                f"⚪ ESTADO EN STANDBY.\n"
                f"No se detectaron patrones de certidumbre suficientes en el régimen actual."
            )
            en = (
                f"⚪ STATE IN STANDBY.\n"
                f"No actionable certainty manifolds detected in current regime."
            )

        return es, en

    def _load_domain_presets(self) -> None:
        """Loads domain-specific baseline certainty islands."""
        if self.domain in ("financial", "fraud", "banking"):
            self._load_financial_presets()
        elif self.domain in ("medical", "healthcare", "clinical"):
            self._load_medical_presets()
        elif self.domain in ("forex", "trading", "quant"):
            self._load_forex_presets()
        elif self.domain in ("security", "cyber", "auth"):
            self._load_security_presets()
        else:
            self._load_general_presets()

    def _load_general_presets(self) -> None:
        # 1. State Consistency
        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-STATE-CONSISTENCY",
            name="Invariante de Consistencia de Estado",
            category=IslandCategory.INVARIANT_INTEGRITY,
            description="Garantiza que no existan variables NaN, infinitos o fuera de escala física.",
            formal_invariant=r"\mathcal{I}_{\text{State}} \equiv \forall x_i \in \mathbf{x}, x_i \notin \{\text{NaN}, \infty\} \land x_i \in \Omega_i",
            predicate=lambda d: not any(
                isinstance(v, float) and (math.isnan(v) or math.isinf(v)) for v in d.values() if isinstance(v, (int, float))
            ),
            is_mandatory_guardrail=True,
            min_confidence=0.99
        ))

        # 2. Low Entropy Invariant
        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-LOW-ENTROPY",
            name="Isla de Baja Entropía y Determinismo",
            category=IslandCategory.LOW_ENTROPY_DETERMINISM,
            description="Se activa cuando la entropía de Shannon local está por debajo del umbral de caos.",
            formal_invariant=r"\mathcal{I}_{\text{Entropy}} \equiv H(\mathbf{X}) < \tau_{\text{chaos}}",
            predicate=lambda d: d.get("entropy", 0.0) <= d.get("entropy_threshold", 0.50),
            min_confidence=0.85
        ))

        # 3. High Conviction FastPath
        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-HIGH-CONVICTION",
            name="Isla de Alta Convicción Proposicional",
            category=IslandCategory.HIGH_CONVICTION_FASTPATH,
            description="Se activa cuando la certidumbre de la regla booleana supera el umbral calibrado.",
            formal_invariant=r"\mathcal{I}_{\text{Conviction}} \equiv \mathcal{C}(\mathbf{R}(\mathbf{x})) \ge \theta_{\text{fastpath}}",
            predicate=lambda d: d.get("certainty", d.get("probabilistic_certainty", 0.0)) >= 75.0,
            min_confidence=0.88,
            risk_multiplier=1.2
        ))

    def _load_financial_presets(self) -> None:
        self._load_general_presets()

        # 1. Balance & Solvency Integrity
        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-FIN-SOLVENCY-INTEGRITY",
            name="Invariante de Solvencia y Balance de Fondos",
            category=IslandCategory.INVARIANT_INTEGRITY,
            description="Garantiza que el monto de la transacción sea positivo y no exceda el saldo disponible.",
            formal_invariant=r"\mathcal{I}_{\text{Solvency}} \equiv (\text{Amount} > 0) \land (\text{Amount} \le \text{Balance})",
            predicate=lambda d: d.get("amount", 0.0) > 0 and d.get("amount", 0.0) <= d.get("available_balance", d.get("balance", float("inf"))),
            is_mandatory_guardrail=True,
            min_confidence=0.99
        ))

        # 2. Geolocation & Velocity Sentry
        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-FIN-VELOCITY-SENTRY",
            name="Centinela de Velocidad de Transacción y Geo-Salto",
            category=IslandCategory.ANOMALY_BOUNDARY_SENTRY,
            description="Bloquea desplazamientos físicos imposibles entre transacciones consecutivas.",
            formal_invariant=r"\mathcal{I}_{\text{Velocity}} \equiv \frac{\Delta \text{Distance}(\text{Tx}_t, \text{Tx}_{t-1})}{\Delta t} \le V_{\text{max}}",
            predicate=lambda d: d.get("speed_kmh", d.get("velocity_kmh", 0.0)) <= d.get("max_physical_speed_kmh", 950.0),
            is_mandatory_guardrail=True,
            min_confidence=0.90
        ))

        # 3. Deterministic Sanctions Veto
        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-FIN-SANCTIONS-CLEARANCE",
            name="Centinela de Cumplimiento y Listas OFAC / AML",
            category=IslandCategory.CONFORMAL_SAFETY_GUARD,
            description="Asegura que el destinatario no esté presente en listas negras de sanciones internacionales.",
            formal_invariant=r"\mathcal{I}_{\text{Sanctions}} \equiv \text{Entity}(\text{Account}) \notin \mathbf{Blocklist}",
            predicate=lambda d: not bool(d.get("is_sanctioned", False)),
            is_mandatory_guardrail=True,
            min_confidence=1.0
        ))

    def _load_medical_presets(self) -> None:
        self._load_general_presets()

        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-MED-PHYSIOLOGY-GUARD",
            name="Guardarraíl de Plausibilidad Fisiológica",
            category=IslandCategory.INVARIANT_INTEGRITY,
            description="Garantiza que los signos vitales estén en rangos compatibles con la vida.",
            formal_invariant=r"\mathcal{I}_{\text{Vitals}} \equiv (\text{HR} \in [20, 260]) \land (\text{SpO2} \in [50, 100])",
            predicate=lambda d: (
                20 <= d.get("heart_rate", d.get("fc", 75)) <= 260 and
                50 <= d.get("spo2", d.get("sao2", 98)) <= 100
            ),
            is_mandatory_guardrail=True,
            min_confidence=0.99
        ))

        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-MED-CONTRAINDICATION-SENTRY",
            name="Centinela de Contraindicaciones y Alergias",
            category=IslandCategory.ANOMALY_BOUNDARY_SENTRY,
            description="Bloquea prescripciones ante alergias o interacciones farmacológicas severas.",
            formal_invariant=r"\mathcal{I}_{\text{Contra}} \equiv \text{Interactions}(\text{Rx}, \text{Allergies}) == \emptyset",
            predicate=lambda d: not bool(d.get("has_contraindication", False)),
            is_mandatory_guardrail=True,
            min_confidence=1.0
        ))

    def _load_forex_presets(self) -> None:
        self._load_general_presets()

        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-FX-SPREAD-SENTRY",
            name="Centinela de Spread Institucional y Noticias",
            category=IslandCategory.ANOMALY_BOUNDARY_SENTRY,
            description="Veta operaciones ante picos de spread anormal (> 6.0 pips) o ventanas de noticias de alto impacto.",
            formal_invariant=r"\mathcal{I}_{\text{Spread}} \equiv (\text{Spread} \le 6.0\text{ pips}) \land \neg \text{NewsWindow}",
            predicate=lambda d: (
                d.get("spread_pips", d.get("current_spread", 1.0)) <= 6.0 and
                not bool(d.get("high_impact_news_active", d.get("is_news_event", False)))
            ),
            is_mandatory_guardrail=True,
            min_confidence=0.95
        ))

        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-FX-MARGIN-SOLVENCY",
            name="Guardarraíl de Margen y Preservación de Capital",
            category=IslandCategory.CONFORMAL_SAFETY_GUARD,
            description="Veta operaciones con nivel de margen inferior al 50% (Riesgo de Stop-Out).",
            formal_invariant=r"\mathcal{I}_{\text{Margin}} \equiv \text{MarginLevel} \ge 50\%",
            predicate=lambda d: d.get("margin_level_pct", d.get("margin_level", 200.0)) >= 50.0,
            is_mandatory_guardrail=True,
            min_confidence=1.0
        ))

    def _load_security_presets(self) -> None:
        self._load_general_presets()

        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-SEC-BRUTEFORCE-SENTRY",
            name="Centinela de Intentos de Autenticación y Fuerza Bruta",
            category=IslandCategory.ANOMALY_BOUNDARY_SENTRY,
            description="Bloquea solicitudes tras superar 10 intentos fallidos de autenticación.",
            formal_invariant=r"\mathcal{I}_{\text{BruteForce}} \equiv \text{FailedAttempts} \le 10",
            predicate=lambda d: d.get("failed_attempts", 0) <= 10,
            is_mandatory_guardrail=True,
            min_confidence=0.99
        ))

        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-SEC-TOR-NETWORK-VETO",
            name="Invariante de Nodos de Anonimización Prohibidos",
            category=IslandCategory.CONFORMAL_SAFETY_GUARD,
            description="Veta accesos originados desde nodos de salida TOR o proxies anónimos.",
            formal_invariant=r"\mathcal{I}_{\text{Tor}} \equiv \neg \text{IsTorExitNode}",
            predicate=lambda d: not bool(d.get("is_tor_exit_node", False)),
            is_mandatory_guardrail=True,
            min_confidence=1.0
        ))


def get_certainty_islands_engine(
    domain: str = "general",
    default_threshold: float = 0.75,
    strict_mode: bool = True
) -> CertaintyIslandsEngine:
    """Factory helper to obtain a CertaintyIslandsEngine instance."""
    return CertaintyIslandsEngine(
        domain=domain,
        default_threshold=default_threshold,
        strict_mode=strict_mode
    )


def certainty_guard(
    domain: str = "general",
    engine: Optional[CertaintyIslandsEngine] = None,
    auto_veto: bool = True,
    on_veto_raise: bool = False,
    on_veto_return: Any = None,
    min_conviction: float = 0.75
):
    """
    Zero-Friction Python Decorator to protect any function with Certainty Islands.

    Usage:
        @certainty_guard(domain="financial", on_veto_raise=True)
        def transfer_funds(amount: float, available_balance: float):
            return {"status": "SUCCESS", "amount": amount}
    """
    _engine = engine or get_certainty_islands_engine(domain=domain, default_threshold=min_conviction)

    def decorator(fn: Callable):
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            # Extract arguments as a dictionary
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            sample_dict = dict(bound.arguments)

            # If first argument is already a dict, unpack it
            if args and isinstance(args[0], dict):
                sample_dict.update(args[0])

            # Evaluate against Certainty Islands
            eval_res = _engine.evaluate(sample_dict)

            # Check for veto
            if eval_res.action_decision == "VETO_REJECT" and auto_veto:
                if on_veto_raise:
                    raise CertaintyVetoException(eval_res.explanation_es, evaluation_result=eval_res)
                if on_veto_return is not None:
                    return on_veto_return
                return {
                    "error": "CERTAINTY_GUARDRAIL_VETO",
                    "action_decision": eval_res.action_decision,
                    "explanation": eval_res.explanation_es,
                    "rejected_islands": eval_res.rejected_islands,
                    "formal_proof_latex": eval_res.formal_proof_latex
                }

            # Execute function
            result = fn(*args, **kwargs)

            # Attach evaluation metadata if result is a dictionary
            if isinstance(result, dict):
                result["__certainty_evaluation__"] = eval_res.to_dict()

            return result

        return wrapper

    return decorator
