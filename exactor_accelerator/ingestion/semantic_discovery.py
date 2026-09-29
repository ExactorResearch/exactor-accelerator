"""
Semantic Proposition Auto-Discovery Engine using LLM (Zero-Regex).
Inspects customer raw texts / domain dialogues during fit(), discovers optimal domain-specific
semantic propositions, and compiles high-speed keyword regex automata for sub-millisecond runtime inference.
"""

from typing import Dict, Any, List, Optional, Union
import json
import re
import os
import requests
import logging

logger = logging.getLogger("exactor_accelerator.semantic_discovery")


class SemanticPropositionDiscovery:
    """
    Auto-discovers semantic propositions from unstructured text using an LLM (JEV / DeepSeek)
    and compiles them into high-speed compiled regex patterns for instant inference.
    """

    def __init__(
        self,
        deepseek_api_key: Optional[str] = None,
        jev_api_key: Optional[str] = None,
    ):
        self.deepseek_api_key = deepseek_api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.jev_api_key = jev_api_key or os.environ.get("TYPESAFE_API_KEY") or os.environ.get("JEV_API_KEY")
        self.discovered_propositions: Dict[str, Dict[str, Any]] = {}
        self._compiled_regexes: Dict[str, List[re.Pattern]] = {}

    def discover_from_corpus(
        self,
        text_samples: List[str],
        target_labels: Optional[List[int]] = None,
        max_propositions: int = 8,
        domain_hint: str = "general customer operations",
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyzes a sample corpus of unstructured texts, queries the LLM once during training,
        and returns domain-tailored semantic proposition definitions.
        """
        if text_samples is None:
            return {}
        if hasattr(text_samples, "tolist"):
            text_samples = text_samples.tolist()
        elif not isinstance(text_samples, list):
            text_samples = list(text_samples)

        if len(text_samples) == 0:
            return {}

        # Limit sample size sent to LLM prompt (e.g. 15-20 representative texts)
        sample_subset = text_samples[:25]
        samples_formatted = "\n".join([f"- [{i+1}] {str(t)[:250]}" for i, t in enumerate(sample_subset)])

        prompt = f"""You are a Symbolic Logic and NLP Engineer.
Analyze the following unstructured text samples belonging to the '{domain_hint}' domain.
Your task is to auto-discover between 4 and {max_propositions} optimal BOOLEAN SEMANTIC PROPOSITIONS to classify and understand these texts.

Text samples:
{samples_formatted}

For each proposition, you must provide:
1. `key`: Short identifier in snake_case (e.g., `refund_request`, `critical_technical_failure`, `legal_threat`, `chest_pain_symptom`).
2. `description`: Clear English explanation of what the proposition signifies.
3. `keywords`: List of 4 to 10 keywords, stems, lemmas, or expressions that activate this condition (in English and Spanish).

Respond ONLY with a valid JSON object containing the 'propositions' key as a list of objects:
{{
  "propositions": [
    {{
      "key": "refund_request",
      "description": "User requests refund or money back",
      "keywords": ["refund", "reimbursement", "chargeback", "duplicate charge", "money back"]
    }}
  ]
}}
"""
        discovered = self._call_llm(prompt)
        if not discovered:
            # Fallback a heurística de vocabulario de alta frecuencia por TF-IDF rápido / discriminativo
            discovered = self._frequency_fallback(text_samples, max_propositions, target_labels)

        # Compilar patrones en memoria para inferencia < 0.1 ms
        self.compile_propositions(discovered)
        return self.discovered_propositions

    def _call_llm(self, prompt: str) -> Optional[List[Dict[str, Any]]]:
        """Invoca DeepSeek o Jev para generar el esquema semántico."""
        # 1. Intentar con DeepSeek
        if self.deepseek_api_key and not self.deepseek_api_key.startswith("mock_"):
            try:
                headers = {
                    "Authorization": f"Bearer {self.deepseek_api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are a JSON logical proposition extractor assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                }
                resp = requests.post("https://api.deepseek.com/v1/chat/completions", json=payload, headers=headers, timeout=8.0)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    return parsed.get("propositions", [])
            except Exception as e:
                logger.debug(f"LLM semantic discovery fallback to heuristic: {e}")

        return None

    def _frequency_fallback(
        self,
        texts: List[str],
        max_propositions: int,
        target_labels: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """Deterministic fallback if LLM is offline: extracts frequent and discriminative keyword clusters."""
        from collections import Counter
        stopwords = {
            "de", "la", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para", "con", "no", "una",
            "su", "al", "lo", "como", "más", "pero", "sus", "le", "ya", "o", "este", "sí", "porque", "esta", "son",
            "entre", "está", "cuando", "muy", "sin", "sobre", "ser", "tiene", "también", "me", "hasta", "hay",
            "the", "and", "is", "in", "to", "of", "for", "with", "a", "an", "on", "it", "at", "by", "this", "my", "hola",
            "que", "les", "nos", "fue", "han", "ante", "tras", "desde", "hacia", "hace", "todo", "bien", "cada"
        }

        if target_labels is not None and len(target_labels) == len(texts) and len(set(target_labels)) > 1:
            pos_words = []
            neg_words = []
            for t, lbl in zip(texts, target_labels):
                tokens = set(re.findall(r"\b[a-záéíóúñA-ZÁÉÍÓÚÑ]{3,}\b", str(t).lower()))
                filtered = [w for w in tokens if w not in stopwords]
                if int(lbl) == 1:
                    pos_words.extend(filtered)
                else:
                    neg_words.extend(filtered)
            
            pos_counts = Counter(pos_words)
            neg_counts = Counter(neg_words)
            all_vocab = sorted(list(set(pos_counts.keys()).union(set(neg_counts.keys()))))

            # Compute difference in relative frequency
            n_pos = max(1, sum(1 for l in target_labels if int(l) == 1))
            n_neg = max(1, sum(1 for l in target_labels if int(l) == 0))

            scored_pos = []
            scored_neg = []
            for w in all_vocab:
                p_pos = pos_counts.get(w, 0) / n_pos
                p_neg = neg_counts.get(w, 0) / n_neg
                diff = p_pos - p_neg
                if diff > 0.05:
                    scored_pos.append((w, diff))
                elif diff < -0.05:
                    scored_neg.append((w, -diff))

            scored_pos.sort(key=lambda x: (-x[1], -pos_counts.get(x[0], 0), x[0]))
            scored_neg.sort(key=lambda x: (-x[1], -neg_counts.get(x[0], 0), x[0]))

            half = max(1, max_propositions // 2)
            top_pos = [w for w, s in scored_pos[:half]]
            top_neg = [w for w, s in scored_neg[:max_propositions - len(top_pos)]]

            propositions = []
            for w in top_pos:
                propositions.append({
                    "key": f"critical_topic_{w}",
                    "description": f"Presence of alert or risk concept '{w}'",
                    "keywords": [w, f"{w}s", f"{w}ing", f"{w}ed", f"{w}tion"]
                })
            for w in top_neg:
                propositions.append({
                    "key": f"routine_topic_{w}",
                    "description": f"Presence of routine or standard concept '{w}'",
                    "keywords": [w, f"{w}s", f"{w}ing", f"{w}ed", f"{w}tion"]
                })
            if propositions:
                return propositions[:max_propositions]

        # Standard general frequency across all texts
        words = []
        for t in texts:
            tokens = re.findall(r"\b[a-záéíóúñA-ZÁÉÍÓÚÑ]{3,}\b", str(t).lower())
            words.extend([w for w in tokens if w not in stopwords])

        common = Counter(words).most_common(max_propositions * 2)
        top_words = [w for w, count in common][:max_propositions]

        propositions = []
        for w in top_words:
            propositions.append({
                "key": f"topic_{w}",
                "description": f"Presence of concepts related to '{w}'",
                "keywords": [w, f"{w}s", f"{w}ing", f"{w}ed", f"{w}tion"]
            })
        return propositions

    def compile_propositions(self, prop_list: List[Dict[str, Any]]):
        """Compiles discovered keywords into optimized regular expressions."""
        self.discovered_propositions = {}
        self._compiled_regexes = {}

        for p in prop_list:
            key = p["key"]
            keywords = p.get("keywords", [])
            # Build regex pattern with word boundaries and wildcards
            escaped_kws = [re.escape(k).replace(r"\*", r"\w*") for k in keywords]
            pattern_str = r"\b(" + "|".join(escaped_kws) + r")\b"
            
            try:
                compiled = re.compile(pattern_str, re.IGNORECASE)
                self.discovered_propositions[key] = {
                    "key": key,
                    "description": p.get("description", key),
                    "keywords": keywords,
                    "pattern": pattern_str,
                }
                self._compiled_regexes[key] = compiled
            except re.error:
                continue

    def extract_features(self, text: str) -> Dict[str, int]:
        """Extracts boolean state of all discovered propositions in < 0.05 ms."""
        if not text or not isinstance(text, str):
            return {f"auto_{k}": 0 for k in self.discovered_propositions}

        text_lower = text.lower()
        feats = {}
        for key, regex in self._compiled_regexes.items():
            feats[f"auto_{key}"] = 1 if regex.search(text_lower) else 0

        # Structural properties
        words = text.split()
        feats["auto_is_long_text"] = 1 if len(words) >= 25 else 0
        feats["auto_has_exclamation"] = 1 if ("!" in text or "¡" in text) else 0
        return feats
