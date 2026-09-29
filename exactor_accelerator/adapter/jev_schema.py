"""
TypeSafe AI Jev Schema Primitives & Payload Models.
Defines Noul, Choice, Score question types and the System One payload structure.
"""

from typing import Dict, Any, Optional, Union, List
import json


class NoulQuestion:
    """
    Noul question primitive (Bernoulli binary decision).
    Returns a calibrated probability (0 to 1) representing the likelihood of truth.
    """

    def __init__(self, instructions: str):
        self.type = "noul"
        self.instructions = instructions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "instructions": self.instructions,
        }


class ChoiceQuestion:
    """
    Choice question primitive for categorical decision-making.
    Returns probabilities across each predefined option and the chosen category.
    """

    def __init__(self, instructions: str, criteria: Dict[str, Optional[str]]):
        self.type = "choice"
        self.instructions = instructions
        self.criteria = criteria

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "instructions": self.instructions,
            "criteria": self.criteria,
        }


class ScoreQuestion:
    """
    Score question primitive for continuous calibrated assessment on a spectrum.
    TypeSafe API requires criteria to be an ordered list of score levels.
    """

    def __init__(self, instructions: str, criteria: Optional[Union[List[str], Dict[str, Optional[str]]]] = None):
        self.type = "score"
        self.instructions = instructions
        if isinstance(criteria, dict):
            self.criteria = [f"{k}: {v}" if v else k for k, v in criteria.items()]
        elif isinstance(criteria, list):
            self.criteria = criteria
        else:
            self.criteria = [
                "Low: Low or negligible impact/risk",
                "Medium: Moderate impact requiring precaution",
                "Critical: Severe or critical, mandatory activation",
            ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "instructions": self.instructions,
            "criteria": self.criteria,
        }


class JevPayload:
    """
    Official payload structure for TypeSafe AI Jev System One model.
    """

    def __init__(
        self,
        state: Dict[str, Any],
        questions: Dict[str, Union[NoulQuestion, ChoiceQuestion, ScoreQuestion, Dict[str, Any]]],
        model: str = "jev-latest",
    ):
        self.model = model
        self.state = state
        self.questions = questions

    def to_dict(self) -> Dict[str, Any]:
        serialized_questions = {}
        for q_name, q_obj in self.questions.items():
            if hasattr(q_obj, "to_dict"):
                serialized_questions[q_name] = q_obj.to_dict()
            elif isinstance(q_obj, dict):
                serialized_questions[q_name] = q_obj
            else:
                serialized_questions[q_name] = {"type": "noul", "instructions": str(q_obj)}

        return {
            "model": self.model,
            "state": self.state,
            "questions": serialized_questions,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
