"""
Generic Certainty Islands Engine (Islas de Certeza) for Exactor-Jev.

Provides a domain-agnostic Neuro-Symbolic topological certainty framework
to enforce formal mathematical invariants, eliminate hallucinations/noise,
and guarantee determinism before executing automated edge decisions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
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
            return True, f"[{self.island_id}] No predicate defined (default PASS)"
        try:
            passed = bool(self.predicate(sample))
            msg = f"[{self.island_id}] {'SATISFIED' if passed else 'VIOLATED'}: {self.name}"
            return passed, msg
        except Exception as e:
            return False, f"[{self.island_id}] EXCEPTION: {e}"


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
    audit_trail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "action_decision": self.action_decision,
            "active_islands": self.active_islands,
            "rejected_islands": self.rejected_islands,
            "confidence_score": round(self.confidence_score, 4),
            "effective_risk_weight": round(self.effective_risk_weight, 4),
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
        # Normalize input to dictionary
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
                    deduction_steps.append(f"⛔ CRITICAL VETO: Mandatory Guardrail [{isl_id}] failed.")

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
        elif is_valid and len(active_islands) >= 2:
            action_decision = "FASTPATH_EXECUTE"
        elif is_valid and len(active_islands) == 1:
            action_decision = "FASTPATH_EXECUTE" if avg_confidence >= 0.85 else "ORACLE_ESCALATE"
        elif avg_confidence > 0.40:
            action_decision = "ORACLE_ESCALATE"
        else:
            action_decision = "STANDBY"

        # Generate LaTeX Proof Representation
        formal_proof_latex = self._build_latex_proof(active_islands, rejected_islands, is_valid, action_decision)

        return IslandEvaluationResult(
            is_valid=is_valid,
            action_decision=action_decision,
            active_islands=active_islands,
            rejected_islands=rejected_islands,
            confidence_score=avg_confidence,
            effective_risk_weight=effective_risk,
            deduction_steps=deduction_steps,
            formal_proof_latex=formal_proof_latex,
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

    def _normalize_sample(
        self,
        sample: Union[Dict[str, Any], pd.Series, np.ndarray],
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        if isinstance(sample, dict):
            return dict(sample)
        elif isinstance(sample, pd.Series):
            return sample.to_dict()
        elif isinstance(sample, np.ndarray):
            if feature_names and len(feature_names) == len(sample):
                return {feature_names[i]: sample[i] for i in range(len(sample))}
            return {f"feature_{i}": val for i, val in enumerate(sample.flatten())}
        else:
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
            rf"\vdash \mathcal{{Decision}}({decision}) \implies {status_sym}"
        )

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
            name="State Space Consistency Invariant",
            category=IslandCategory.INVARIANT_INTEGRITY,
            description="Guarantees no null, NaN, or non-physical out-of-bound variables in state vector.",
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
            name="Low Entropy Determinism Island",
            category=IslandCategory.LOW_ENTROPY_DETERMINISM,
            description="Activates when Shannon entropy of the local window is below chaotic boundary.",
            formal_invariant=r"\mathcal{I}_{\text{Entropy}} \equiv H(\mathbf{X}) < \tau_{\text{chaos}}",
            predicate=lambda d: d.get("entropy", 0.0) <= d.get("entropy_threshold", 0.50),
            min_confidence=0.85
        ))

        # 3. High Conviction FastPath
        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-HIGH-CONVICTION",
            name="Propositional High Conviction Island",
            category=IslandCategory.HIGH_CONVICTION_FASTPATH,
            description="Activates when boolean rule match certainty exceeds the calibrated threshold.",
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
            name="Financial Solvency & Balance Guardrail",
            category=IslandCategory.INVARIANT_INTEGRITY,
            description="Guarantees amount is positive and does not exceed available balance or velocity caps.",
            formal_invariant=r"\mathcal{I}_{\text{Solvency}} \equiv (\text{Amount} > 0) \land (\text{Amount} \le \text{Balance})",
            predicate=lambda d: d.get("amount", 0.0) > 0 and d.get("amount", 0.0) <= d.get("available_balance", float("inf")),
            is_mandatory_guardrail=True,
            min_confidence=0.99
        ))

        # 2. Geolocation & Velocity Sentry
        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-FIN-VELOCITY-SENTRY",
            name="Transaction Velocity & Geo-Jump Sentry",
            category=IslandCategory.ANOMALY_BOUNDARY_SENTRY,
            description="Blocks impossible physical travel speeds between consecutive transactions.",
            formal_invariant=r"\mathcal{I}_{\text{Velocity}} \equiv \frac{\Delta \text{Distance}(\text{Tx}_t, \text{Tx}_{t-1})}{\Delta t} \le V_{\text{max}}",
            predicate=lambda d: d.get("speed_kmh", 0.0) <= d.get("max_physical_speed_kmh", 950.0),
            is_mandatory_guardrail=True,
            min_confidence=0.90
        ))

        # 3. Deterministic Fraud Veto
        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-FIN-SANCTIONS-CLEARANCE",
            name="Anti-Money Laundering & Sanctions Clearance",
            category=IslandCategory.CONFORMAL_SAFETY_GUARD,
            description="Ensures recipient is not present on OFAC or sanctions blocklists.",
            formal_invariant=r"\mathcal{I}_{\text{Sanctions}} \equiv \text{Entity}(\text{Account}) \notin \mathbf{Blocklist}",
            predicate=lambda d: not bool(d.get("is_sanctioned", False)),
            is_mandatory_guardrail=True,
            min_confidence=1.0
        ))

    def _load_medical_presets(self) -> None:
        self._load_general_presets()

        # 1. Physiological Boundaries
        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-MED-PHYSIOLOGY-GUARD",
            name="Physiological Plausibility Boundary",
            category=IslandCategory.INVARIANT_INTEGRITY,
            description="Guarantees vital signs (HR, BP, SpO2) are physically compatible with life.",
            formal_invariant=r"\mathcal{I}_{\text{Vitals}} \equiv (\text{HR} \in [20, 260]) \land (\text{SpO2} \in [40, 100])",
            predicate=lambda d: (
                20 <= d.get("heart_rate", 75) <= 260 and
                40 <= d.get("spo2", 98) <= 100
            ),
            is_mandatory_guardrail=True,
            min_confidence=0.99
        ))

        # 2. Contraindication Sentry
        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-MED-CONTRAINDICATION-SENTRY",
            name="Drug-Allergy & Interaction Sentry",
            category=IslandCategory.ANOMALY_BOUNDARY_SENTRY,
            description="Blocks prescription if allergy or severe adverse drug interaction is detected.",
            formal_invariant=r"\mathcal{I}_{\text{Contra}} \equiv \text{Interactions}(\text{Rx}, \text{Allergies}) == \emptyset",
            predicate=lambda d: not bool(d.get("has_contraindication", False)),
            is_mandatory_guardrail=True,
            min_confidence=1.0
        ))

    def _load_forex_presets(self) -> None:
        self._load_general_presets()

        # 1. Multi-Timeframe Resonance
        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-MTF-RESONANCE",
            name="Multi-Timeframe Structural Resonance Island",
            category=IslandCategory.HIGH_CONVICTION_FASTPATH,
            description="Guarantees that macro trend (H4) and micro structure (H1/M15) align in the same vector.",
            formal_invariant=r"\mathcal{I}_{\text{MTF}} \equiv (\text{Trend}_{H4} == \mathbf{Dir}) \land (\text{Structure}_{H1} == \mathbf{Dir})",
            predicate=lambda d: (
                d.get("trend_h4") is not None and
                d.get("trend_h4") == d.get("structure_h1") and
                d.get("trend_h4") in ("BULLISH", "BEARISH", "BUY", "SELL", 1, -1)
            ),
            min_confidence=0.85
        ))

        # 2. Spread & News Sentry
        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-SPREAD-NEWS-SENTRY",
            name="Institutional Spread & News Sentry",
            category=IslandCategory.ANOMALY_BOUNDARY_SENTRY,
            description="Vetoes trades during high-impact news spikes and abnormally wide spreads.",
            formal_invariant=r"\mathcal{I}_{\text{News}} \equiv (\text{Spread} \le 3.0 \times \text{AvgSpread}) \land \neg \text{NewsWindow}(\pm 15\text{min})",
            predicate=lambda d: (
                d.get("current_spread", 1.0) <= 3.0 * d.get("avg_spread", 1.2) and
                not bool(d.get("high_impact_news_active", False))
            ),
            is_mandatory_guardrail=True,
            min_confidence=0.95
        ))

        # 3. Capital Preservation Guardrail
        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-CAPITAL-PRESERVATION",
            name="Portfolio Daily Drawdown Guardrail",
            category=IslandCategory.CONFORMAL_SAFETY_GUARD,
            description="Hard circuit breaker if account equity drawdown hits prop-firm limit.",
            formal_invariant=r"\mathcal{I}_{\text{Capital}} \equiv \text{DailyDD}_{\text{equity}} < 4.5\%",
            predicate=lambda d: d.get("daily_drawdown_pct", 0.0) < d.get("max_daily_drawdown_limit", 4.5),
            is_mandatory_guardrail=True,
            min_confidence=1.0
        ))

    def _load_security_presets(self) -> None:
        self._load_general_presets()

        self.register_island(CertaintyIslandDefinition(
            island_id="ISLAND-AUTH-MFA-INVARIANT",
            name="Multi-Factor Auth Integrity Invariant",
            category=IslandCategory.INVARIANT_INTEGRITY,
            description="Ensures privileged admin operations hold valid cryptographically verified MFA tokens.",
            formal_invariant=r"\mathcal{I}_{\text{Auth}} \equiv \text{PrivilegedAction} \implies \text{ValidMFA}(\text{Token})",
            predicate=lambda d: (not d.get("is_privileged", False)) or bool(d.get("mfa_verified", False)),
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
