"""
DeepSeek Explainer Engine for EXACTOR x JEV.
Generates rich natural language audit explanations grounding why a decision
was executed based on EXACTOR's active boolean propositions and JEV's RLCD certainty.
"""

import os
import time
import logging
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger("exactor_accelerator.deepseek")


class DeepSeekExplainer:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 15,
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = (base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")).rstrip("/")
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.timeout = timeout

    def generate_explanation(
        self,
        event_state: Dict[str, Any],
        active_propositions: Dict[str, int],
        exact_eval: int,
        criterio_prob: float,
        chosen_action: str,
        autonomous_executed: bool,
        rule_formula: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calls DeepSeek LLM to generate an executive audit explanation.
        """
        start_t = time.perf_counter()
        
        # Filter only active (1) propositions
        active_list = [p for p, v in active_propositions.items() if v == 1]

        # Categorize clearly for DeepSeek prompt
        act_upper = chosen_action.upper()
        is_critical = exact_eval == 1 or "BLOQUE" in act_upper or "FREEZE" in act_upper or "MITIGAC" in act_upper or "UCI" in act_upper or criterio_prob >= 0.70
        is_review = "REVISION" in act_upper or "HUMAN" in act_upper or "ESCALA" in act_upper or (criterio_prob > 0.30 and criterio_prob < 0.70 and not is_critical)
        
        if is_critical:
            veredicto_claro = "PREVENTIVE BLOCK OR CONTAINMENT (High Risk Operation)"
            sentido_decision = "The operation was NOT approved and was blocked or mitigated preventively to safeguard security."
        elif is_review:
            veredicto_claro = "MANUAL REVIEW OR 2FA (Borderline or uncertain case)"
            sentido_decision = "The operation is paused pending identity confirmation (2FA) or analyst review."
        else:
            veredicto_claro = "APPROVED OPERATION (Legitimate and secure transaction)"
            sentido_decision = "The operation was FULLY APPROVED and authorized immediately without friction."

        prompt = f"""Explain in simple, everyday English why this decision was made regarding the following operation:

OPERATION DATA:
{event_state}

SYSTEM RULING:
- Definitive Verdict: {veredicto_claro}
- Executed Action: {chosen_action}
- Decision Meaning: {sentido_decision}
- Certainty / Safety Level: {criterio_prob * 100:.1f}%
- Activated Risk Alerts or Conditions: {active_list if active_list else "None (all parameters are normal and legitimate)"}

MANDATORY GUIDELINES:
- You MUST strictly respect the definitive verdict ({veredicto_claro}). If approved, explain that it was approved; if blocked or placed on review, explain accordingly.
- DO NOT use technical jargon (e.g., hypercube, boolean, vector, B^32, minterm, RLCD, disjunction, clause).
- Write with a clear, professional, and reassuring tone.
- Organize your response into these 3 sections:

1. **What was decided?** (1 sentence confirming if the operation was approved, blocked, or placed under review).
2. **Why?** (2 or 3 brief bullets analyzing real parameters: amount, failed PIN attempts, device trust, velocity, or IP reputation).
3. **What does this mean for you?** (1 sentence stating clear next steps)."""

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a friendly and professional customer support assistant. Your task is to explain business or financial decisions in 100% everyday, clear language understandable to anyone without technical background.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 400,
            }

            resp = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                elapsed_ms = round((time.perf_counter() - start_t) * 1000.0, 2)
                return {
                    "success": True,
                    "model": self.model,
                    "explanation": content,
                    "latency_ms": elapsed_ms,
                    "active_propositions": active_list,
                }
            else:
                logger.warning(f"DeepSeek API error {resp.status_code}: {resp.text}")
                return self._fallback_explanation(event_state, active_list, chosen_action, exact_eval, criterio_prob, start_t)

        except Exception as e:
            logger.error(f"Error calling DeepSeek API: {e}")
            return self._fallback_explanation(event_state, active_list, chosen_action, exact_eval, criterio_prob, start_t)

    def _fallback_explanation(
        self,
        event_state: Dict[str, Any],
        active_list: list,
        chosen_action: str,
        exact_eval: int,
        criterio_prob: float,
        start_t: float,
    ) -> Dict[str, Any]:
        """Human-friendly plain language fallback."""
        elapsed_ms = round((time.perf_counter() - start_t) * 1000.0, 2)
        if exact_eval == 1 or len(active_list) > 0:
            text = (
                f"**1. What decision was made and why?**\n"
                f"Action **{chosen_action}** was applied to protect your operation, as the system detected patterns that deviate from standard behavior.\n\n"
                f"**2. What factors led to this decision?**\n"
                f"• Unusual values were identified in transaction parameters.\n"
                f"• The risk alert level exceeds safety margins set for automated pass-through.\n\n"
                f"**3. What does this mean for the user or business?**\n"
                f"The operation is held preventively to avoid loss or unauthorized access."
            )
        else:
            text = (
                f"**1. What decision was made and why?**\n"
                f"The operation was successfully **{chosen_action}** because all entered data is consistent, legitimate, and secure.\n\n"
                f"**2. What factors led to this decision?**\n"
                f"• Transaction amount and frequency correspond to normal and standard usage.\n"
                f"• No security alerts, failed attempts, or network anomalies were detected.\n\n"
                f"**3. What does this mean for the user or business?**\n"
                f"The transaction is completed immediately without delay or customer friction."
            )
        return {
            "success": False,
            "model": "local-human-fallback",
            "explanation": text,
            "latency_ms": elapsed_ms,
            "active_propositions": active_list,
        }
