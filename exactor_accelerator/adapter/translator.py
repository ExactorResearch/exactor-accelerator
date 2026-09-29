"""
Dynamic Adapter: EXACTOR -> Jev.
Translates Boolean formulas and hypercube terms from Exactor into typed questions
for TypeSafe AI Jev (Noul, Choice, Score).
"""

from typing import Dict, Any, List, Optional
from ..core.hypercube import ExactorSimplificationResult
from ..ingestion.binarizer import Proposition
from .jev_schema import NoulQuestion, ChoiceQuestion, ScoreQuestion, JevPayload


class ExactorToJevTranslator:
    """
    Translates minimized Boolean logic formulas into calibrated question schemas for Jev.
    """

    def __init__(self, target_label: str = "critical_event"):
        self.target_label = target_label

    def generate_human_explanation(
        self,
        result: ExactorSimplificationResult,
        propositions_map: Optional[Dict[str, Proposition]] = None,
    ) -> str:
        """Converts mathematical Boolean terms into natural semantic explanation."""
        if not result.terms:
            return "No historical activation conditions were detected."

        clauses = []
        for term in result.terms:
            literals = []
            for i, s in enumerate(term.states):
                if s == 2:
                    continue
                v_name = result.variables[i]
                prop = propositions_map.get(v_name) if propositions_map else None
                desc = prop.description if prop else v_name
                if s == 1:
                    literals.append(f"[{desc}]")
                elif s == 0:
                    literals.append(f"[NOT {desc}]")

            clause_str = " AND ".join(literals) if literals else "ALWAYS_ACTIVE"
            clauses.append(clause_str)

        if len(clauses) == 1:
            return f"Satisfied when: {clauses[0]}"
        return "Satisfied when at least one of the following combinations is true: " + " OR ".join(
            [f"({c})" for c in clauses]
        )

    def create_questions_schema(
        self,
        result: ExactorSimplificationResult,
        propositions_map: Optional[Dict[str, Proposition]] = None,
        custom_action_choices: Optional[Dict[str, Optional[str]]] = None,
    ) -> Dict[str, Any]:
        """
        Builds the complete typed questions schema according to TypeSafe AI specifications.
        """
        explanation = self.generate_human_explanation(result, propositions_map)
        formula_snippet = result.formula_expr[:180] + ("..." if len(result.formula_expr) > 180 else "")

        # 1. Primary Noul question: Exact boolean condition derived from Exactor
        noul_instructions = (
            f"Is the boolean condition derived from historical analysis satisfied? "
            f"Logical formula: {formula_snippet}. Criterion: {explanation}"
        )
        criterio_logico = NoulQuestion(instructions=noul_instructions)

        # 2. Autonomous Business Action: Choice question
        if not custom_action_choices:
            tl = self.target_label.lower()
            if "fraud" in tl:
                custom_action_choices = {
                    "BLOCK_TRANSACTION": "If fraud or anomaly risk is high and matches risk conditions",
                    "MANUAL_REVIEW": "If there is moderate suspicion or borderline parameters requiring review",
                    "APPROVE_TRANSACTION": "If transaction is legitimate, habitual, and low risk",
                }
            elif "mitigation" in tl or "sre" in tl:
                custom_action_choices = {
                    "TRIGGER_MITIGATION": "If incidents and error metrics exceed SLA thresholds",
                    "ESCALATE_ON_CALL": "If there is partial service degradation",
                    "DISMISS_ALERT": "If metrics are within normal operating parameters",
                }
            elif "churn" in tl:
                custom_action_choices = {
                    "IMMEDIATE_RETENTION_OFFER": "If the customer has high risk of imminent cancellation",
                    "CONTACT_EXECUTIVE_CSM": "If there is moderate dissatisfaction risk",
                    "MAINTAIN_CURRENT_PLAN": "If the customer is retained and satisfied",
                }
            elif "block" in tl or "soc" in tl or "ip" in tl:
                custom_action_choices = {
                    "BLOCK_IP_FIREWALL": "If a clear cyberattack or brute force pattern is detected",
                    "ISOLATE_HOST_QUARANTINE": "If suspicious traffic anomalies are detected",
                    "ALLOW_TRAFFIC": "If traffic is verified and legitimate",
                }
            elif "icu" in tl or "triage" in tl:
                custom_action_choices = {
                    "TRANSFER_TO_ICU_URGENT": "If vital signs indicate imminent life risk",
                    "CONTINUOUS_OBSERVATION": "If the patient requires intermediate monitoring",
                    "DISCHARGE_GENERAL_WARD": "If patient parameters are stable",
                }
            elif "escalate" in tl or "sup" in tl:
                custom_action_choices = {
                    "ESCALATE_TO_SUPERVISOR": "If the user is dissatisfied or reports critical issues",
                    "TRANSFER_TO_SENIOR_AGENT": "If the inquiry is complex",
                    "RESOLVE_WITH_BOT": "If it is a standard informational inquiry",
                }
            else:
                custom_action_choices = {
                    "APPROVE_OPERATION": "The event satisfies normal parameters and presents no risk",
                    "MANUAL_REVIEW": "There is uncertainty or boundary values in event parameters",
                    "BLOCK_RISK": "The event satisfies logical risk or anomaly conditions",
                }

        business_action = ChoiceQuestion(
            instructions=(
                f"What business action should be executed for this event considering logical rule '{formula_snippet}'?"
            ),
            criteria=custom_action_choices,
        )

        # 3. Calibrated Risk/Severity Score question
        score_question = ScoreQuestion(
            instructions=f"Evaluate on a continuous scale the impact/criticality level of the event according to the logical rule.",
            criteria={
                "low": "Standard event without critical rule activation", "bajo": "Standard event without critical rule activation",
                "medium": "Parameters close to logical activation boundaries", "medio": "Parameters close to logical activation boundaries",
                "critical": "Full compliance with boolean rule and high severity", "critico": "Full compliance with boolean rule and high severity",
            },
        )

        return {
            "criterio_logico": criterio_logico,
            "accion_recomendada": business_action,
            "calibracion_criticidad": score_question,
        }

    def build_payload(
        self,
        raw_event_state: Dict[str, Any],
        result: ExactorSimplificationResult,
        propositions_map: Optional[Dict[str, Proposition]] = None,
        custom_action_choices: Optional[Dict[str, Optional[str]]] = None,
        include_all_questions: bool = True,
    ) -> JevPayload:
        """
        Builds the exact JSON payload expected by the TypeSafe AI Jev API.
        """
        if include_all_questions:
            questions = self.create_questions_schema(
                result=result,
                propositions_map=propositions_map,
                custom_action_choices=custom_action_choices,
            )
        else:
            explanation = self.generate_human_explanation(result, propositions_map)
            questions = {
                "criterio_logico": NoulQuestion(
                    instructions=f"Is the boolean condition derived from historical analysis satisfied? {explanation}"
                )
            }

        return JevPayload(
            model="jev-latest",
            state={"evento": raw_event_state},
            questions=questions,
        )
