"""
Pillar 2 - Cognitive Friction: the multimodal Oracle (System 2).

When the Fast-Path cannot resolve an object (cold start or ambiguity), the router sends it
to a cloud oracle that interprets it and returns a structured verdict. Providers:

    gemini   - Google Gemini (vision + text)          GEMINI_API_KEY
    openai   - any OpenAI-compatible vision endpoint  OPENAI_API_KEY / OPENAI_BASE_URL
    deepseek - DeepSeek (text fragments only)          DEEPSEEK_API_KEY
    human    - label supplied by an operator
    local    - offline deterministic vision/text heuristics (simulated System 2)
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import requests

from ..config import EngramConfig
from ..perception import PerceivedObject

logger = logging.getLogger("exactor_engram.oracle")

PROMPT = (
    "Eres el Oráculo (Sistema 2) de una memoria asociativa. Interpreta el objeto y responde SOLO JSON "
    'con las claves: "label" (concepto canónico corto en español, 1-3 palabras, minúsculas, sin artículos, '
    'reutilizable para objetos equivalentes), "description" (1 frase), "tags" (3-6 palabras clave).'
)


@dataclass
class OracleVerdict:
    label: str
    description: str
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.9
    provider: str = "local"
    model: str = "local-heuristic"
    simulated: bool = True
    latency_ms: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    raw: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def normalize_label(label: str) -> str:
    label = (label or "").strip().lower()
    label = re.sub(r"[\"'`.:;!¡?¿]+", "", label)
    label = re.sub(r"\s+", " ", label)
    return label[:60] or "sin etiqueta"


def _parse_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0) if m else text)


# ----------------------------------------------------------------------------------------
# Cloud providers
# ----------------------------------------------------------------------------------------


class GeminiOracle:
    name = "gemini"

    def __init__(self, cfg: EngramConfig):
        self.key, self.model = cfg.gemini_api_key, cfg.gemini_model

    def available(self, obj: PerceivedObject) -> bool:
        return bool(self.key) and obj.modality in ("image", "text")

    def consult(self, obj: PerceivedObject) -> OracleVerdict:
        parts: List[Dict[str, Any]] = [{"text": PROMPT}]
        if obj.modality == "image":
            parts.append({"inline_data": {"mime_type": obj.mime, "data": base64.b64encode(obj.payload).decode()}})
        else:
            parts.append({"text": obj.payload.decode("utf-8", "replace")[:8000]})
        t0 = time.perf_counter()
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
            params={"key": self.key},
            json={"contents": [{"parts": parts}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}},
            timeout=40,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        usage = data.get("usageMetadata", {})
        parsed = _parse_json(text)
        tin, tout = int(usage.get("promptTokenCount", 0)), int(usage.get("candidatesTokenCount", 0))
        return OracleVerdict(
            label=normalize_label(parsed.get("label", "")),
            description=parsed.get("description", ""),
            tags=list(parsed.get("tags", []))[:6],
            provider=self.name, model=self.model, simulated=False,
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            tokens_in=tin, tokens_out=tout,
            cost_usd=round(tin * 0.10e-6 + tout * 0.40e-6, 6),
            raw=parsed,
        )


class OpenAICompatibleOracle:
    name = "openai"

    def __init__(self, cfg: EngramConfig, key: Optional[str] = None, base: Optional[str] = None,
                 model: Optional[str] = None, name: str = "openai", vision: bool = True):
        self.key = key if key is not None else cfg.openai_api_key
        self.base = (base or cfg.openai_base_url).rstrip("/")
        self.model = model or cfg.openai_model
        self.name = name
        self.vision = vision

    def available(self, obj: PerceivedObject) -> bool:
        if not self.key:
            return False
        return obj.modality == "text" or (self.vision and obj.modality == "image")

    def consult(self, obj: PerceivedObject) -> OracleVerdict:
        if obj.modality == "image":
            uri = f"data:{obj.mime};base64,{base64.b64encode(obj.payload).decode()}"
            content: Any = [{"type": "text", "text": "Interpreta esta imagen."}, {"type": "image_url", "image_url": {"url": uri}}]
        else:
            content = obj.payload.decode("utf-8", "replace")[:8000]
        t0 = time.perf_counter()
        resp = requests.post(
            f"{self.base}/chat/completions",
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
            json={
                "model": self.model,
                "messages": [{"role": "system", "content": PROMPT}, {"role": "user", "content": content}],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
                "max_tokens": 300,
            },
            timeout=40,
        )
        resp.raise_for_status()
        data = resp.json()
        parsed = _parse_json(data["choices"][0]["message"]["content"])
        usage = data.get("usage", {})
        tin, tout = int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))
        return OracleVerdict(
            label=normalize_label(parsed.get("label", "")),
            description=parsed.get("description", ""),
            tags=list(parsed.get("tags", []))[:6],
            provider=self.name, model=self.model, simulated=False,
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            tokens_in=tin, tokens_out=tout,
            cost_usd=round(tin * 0.15e-6 + tout * 0.60e-6, 6),
            raw=parsed,
        )


# ----------------------------------------------------------------------------------------
# Local (offline) oracle - deterministic simulation of System 2
# ----------------------------------------------------------------------------------------

_COLOR_NAMES = {
    "rojo": "rojo", "amarillo": "amarillo", "verde": "verde",
    "cian": "cian", "azul": "azul", "magenta": "magenta",
}
_STOP = {
    "el", "la", "de", "que", "y", "en", "los", "las", "un", "una", "por", "con", "para", "del", "se", "es",
    "al", "lo", "como", "the", "of", "and", "to", "in", "is", "for", "on", "a", "su", "sus", "este", "esta",
    "hay", "fue", "son", "está", "mi", "me", "nos", "le", "o", "si", "no", "ya", "más", "muy",
}


class LocalOracle:
    """Offline System 2: rotation-invariant shape analysis + chromatic naming / keyword extraction."""

    name = "local"

    def __init__(self, cfg: EngramConfig):
        self.cfg = cfg
        self.simulated_latency_ms = float(os.getenv("ENGRAM_SIMULATED_ORACLE_LATENCY_MS", "650"))

    def available(self, obj: PerceivedObject) -> bool:
        return True

    def consult(self, obj: PerceivedObject, simulate_latency: bool = True) -> OracleVerdict:
        t0 = time.perf_counter()
        if obj.modality == "image":
            label, desc, tags = self._vision(obj.features)
        elif obj.modality == "text":
            label, desc, tags = self._text(obj)
        else:
            label = f"segmento binario {obj.sha256[:6]}"
            desc, tags = "Segmento de datos binarios sin interpretación semántica.", ["binario"]
        if simulate_latency and self.simulated_latency_ms > 0:
            time.sleep(self.simulated_latency_ms / 1000.0)
        return OracleVerdict(
            label=normalize_label(label), description=desc, tags=tags, confidence=0.82,
            provider=self.name, model="local-vision-heuristic", simulated=True,
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            tokens_in=self.cfg.oracle_ref_tokens, tokens_out=60,
            cost_usd=self.cfg.oracle_ref_cost_usd,
        )

    @staticmethod
    def _vision(f: Dict[str, Any]):
        shares = {k[6:]: v for k, v in f.items() if k.startswith("share_")}
        color, share = max(shares.items(), key=lambda kv: kv[1]) if shares else ("", 0.0)
        color_name = _COLOR_NAMES.get(color, "") if share > 0.15 else ""
        is_object = f.get("foreground_frac", 1.0) < 0.95
        if is_object:
            if f.get("radial_cv", 1) < 0.06 or f.get("fill_circle", 0) > 0.85:
                shape = "círculo"
            else:
                lobes = f.get("lobes", 0)
                shape = {3: "triángulo", 4: "cuadrado", 5: "estrella", 6: "hexágono"}.get(lobes)
                if shape is None:
                    shape = "estrella" if f.get("fill_ratio", 1) < 0.5 else "figura irregular"
            if not color_name:
                color_name = "claro" if f.get("brightness", 0) > 0.6 else "oscuro"
            label = f"{shape} {color_name}"
            desc = f"Objeto con forma de {shape} de tono {color_name} sobre fondo {'claro' if f.get('background_luma', 0) > 0.6 else 'oscuro'}."
            tags = [shape, color_name, "objeto", "figura"]
        else:
            light = "luminosa" if f.get("brightness", 0) > 0.55 else "sombría"
            texture = "detallada" if f.get("edge_density", 0) > 0.06 else "suave"
            label = f"escena {color_name or 'neutra'} {light}"
            desc = f"Fotografía {light} y {texture} con dominante {color_name or 'neutra'}."
            tags = ["escena", color_name or "neutra", light, texture]
        return label, desc, tags

    @staticmethod
    def _text(obj: PerceivedObject):
        text = obj.payload.decode("utf-8", "replace").lower()
        words = [w for w in re.findall(r"[a-záéíóúñü]{3,}", text) if w not in _STOP]
        top = [w for w, _ in Counter(words).most_common(3)]
        label = " ".join(top[:2]) if top else "fragmento vacío"
        return label, f"Fragmento de texto sobre: {', '.join(top) or 'n/d'}.", top


# ----------------------------------------------------------------------------------------
# Router
# ----------------------------------------------------------------------------------------


class OracleRouter:
    def __init__(self, cfg: EngramConfig):
        self.cfg = cfg
        self.local = LocalOracle(cfg)
        self.providers = {
            "gemini": GeminiOracle(cfg),
            "openai": OpenAICompatibleOracle(cfg),
            "deepseek": OpenAICompatibleOracle(
                cfg, key=cfg.deepseek_api_key, base=cfg.deepseek_base_url, model=cfg.deepseek_model,
                name="deepseek", vision=False,
            ),
        }

    def describe(self) -> Dict[str, Any]:
        return {
            "mode": self.cfg.oracle_provider,
            "configured": [n for n, p in self.providers.items() if getattr(p, "key", None)],
            "fallback": "local",
        }

    def consult(self, obj: PerceivedObject, label_hint: Optional[str] = None, simulate_latency: bool = True) -> OracleVerdict:
        if label_hint:
            return OracleVerdict(
                label=normalize_label(label_hint),
                description="Etiqueta asignada por un operador humano.",
                tags=[normalize_label(label_hint)], confidence=1.0,
                provider="human", model="operador", simulated=False,
            )
        mode = (self.cfg.oracle_provider or "auto").lower()
        order = ["gemini", "openai", "deepseek"] if mode == "auto" else [mode]
        for name in order:
            prov = self.providers.get(name)
            if prov is None or not prov.available(obj):
                continue
            try:
                verdict = prov.consult(obj)
                if verdict.label and verdict.label != "sin etiqueta":
                    return verdict
            except Exception as exc:
                logger.warning("Oracle %s failed: %s", name, exc)
        return self.local.consult(obj, simulate_latency=simulate_latency)
