"""
Unstructured Text & Conversation Feature Extractor.
Extracts semantic, intentional, and emotional Boolean propositions from raw text,
chat transcripts, and customer support dialogue sessions.
"""

from typing import Dict, Any, List, Union
import re


class TextFeatureExtractor:
    """
    Analyzes raw unstructured text / conversations and extracts discrete Boolean
    propositions for projection onto the Boolean Hypercube B^k.
    """

    # Semantic keyword patterns (Bilingual: Spanish / English with stem matching)
    PATTERNS = {
        "cancellation_intent": [
            r"\b(cancel\w*|dar\s+de\s+baja|baja|anul\w*|reembols\w*|devoluci[oó]n|devuelv\w*|desuscrib\w*|unsubscribe|refund)\b"
        ],
        "billing_payment_issue": [
            r"\b(cobr\w*|tarjeta\w*|factur\w*|precio\w*|pag\w*|duplicad\w*|dinero|d[eé]bito\w*|billing|charge\w*|invoice\w*|payment\w*|credit\s*card)\b"
        ],
        "urgency_critical": [
            r"\b(urgent\w*|ya\s+mismo|inmediat\w*|asap|cuanto\s+antes|r[aá]pid\w*|emergenc\w*|cr[ií]tic\w*|critical|immediately)\b"
        ],
        "frustration_anger": [
            r"\b(p[eé]sim\w*|horrible\w*|inaceptable\w*|verg[uü]enza|abus\w*|demand\w*|abogad\w*|estafa\w*|enojad\w*|furios\w*|harto\w*|scam\w*|terrible|awful|lawyer|furious|angry)\b"
        ],
        "technical_bug": [
            r"\b(error\w*|fall\w*|no\s+funciona|se\s+cae|ca[ií]d[oa]|bloquead\w*|pantalla\s+negra|bug\w*|crash\w*|down|failed|broken|not\s+working|glitch\w*)\b"
        ],
        "repeated_contact": [
            r"\b(otra\s+vez|de\s+nuevo|segunda\s+vez|tercera\s+vez|nadie\s+(\w+\s+)?respond\w*|sigo\s+esperando|again|second\s+time|nobody\s+answers|still\s+waiting)\b"
        ],
        "gratitude_positive": [
            r"\b(gracias|excelente\w*|perfect\w*|solucionad\w*|amable\w*|agradec\w*|thank\w*|thanks|great|resolved|solved)\b"
        ],
        "legal_threat": [
            r"\b(demand\w*|abogad\w*|juicio|denuncia\w*|defensa\s+del\s+consumidor|sue|legal\s+action|lawsuit|consumer\s+protection)\b"
        ],
        "security_account": [
            r"\b(contrase[ñn]a\w*|password\w*|hack\w*|bloquead\w*|phishing|seguridad|rob\w*|unauthorized)\b"
        ],
        "request_supervisor": [
            r"\b(supervisor\w*|gerente\w*|humano|persona\s+real|representante|hablar\s+con\s+alguien|manager|human\s+agent)\b"
        ],
        "sla_breach": [
            r"\b(semana\w*|d[ií]as\s+esperando|meses|demora|atras\w*|tardanza|hours\s+waiting|days\s+waiting)\b"
        ],
    }

    @classmethod
    def extract_from_text(cls, text: str) -> Dict[str, int]:
        """
        Extracts a dictionary of Boolean propositions (0 or 1) from raw text.
        """
        if not text or not isinstance(text, str):
            return {f"text_has_{k}": 0 for k in cls.PATTERNS} | {
                "text_is_long": 0,
                "text_has_exclamation": 0,
                "text_has_all_caps": 0,
            }

        text_clean = text.strip()
        text_lower = text_clean.lower()
        features: Dict[str, int] = {}

        # 1. Keyword / Intent regex matching
        for feature_name, regex_list in cls.PATTERNS.items():
            matched = 0
            for pattern in regex_list:
                if re.search(pattern, text_lower):
                    matched = 1
                    break
            features[f"text_has_{feature_name}"] = matched

        # 2. Structural & intensity signals
        word_count = len(text_clean.split())
        features["text_is_long"] = 1 if word_count >= 25 else 0
        features["text_has_exclamation"] = 1 if ("!" in text_clean or "¡" in text_clean) else 0

        # Check for shout / caps intensity (at least 2 uppercase words of length > 2)
        words = text_clean.split()
        caps_words = [w for w in words if len(w) > 2 and w.isupper()]
        features["text_has_all_caps"] = 1 if len(caps_words) >= 2 else 0

        return features

    @classmethod
    def extract_from_conversation(cls, dialogue: Union[List[Dict[str, Any]], str]) -> Dict[str, int]:
        """
        Processes multi-turn dialogue transcripts or raw chat strings.
        """
        if isinstance(dialogue, list):
            # Concatenate user messages
            user_texts = []
            turn_count = len(dialogue)
            for turn in dialogue:
                if isinstance(turn, dict):
                    content = turn.get("message") or turn.get("text") or turn.get("content", "")
                    user_texts.append(str(content))
                else:
                    user_texts.append(str(turn))
            full_text = " ".join(user_texts)
            base_features = cls.extract_from_text(full_text)
            base_features["conv_has_many_turns"] = 1 if turn_count >= 4 else 0
            return base_features
        else:
            return cls.extract_from_text(str(dialogue))
