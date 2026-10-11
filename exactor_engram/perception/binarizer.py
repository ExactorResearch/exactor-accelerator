"""
Pillar 1 - Multimodal Perception: projection of objects onto the boolean hypercube B^64.

Every object (photo, image segment, text fragment, data segment) is abstracted into a
*ternary* code over k = 64 atomic propositions:

    bit = 1   -> trait present        (stable)
    bit = 0   -> trait absent         (stable)
    bit = -   -> don't-care           (the continuous value lies too close to its threshold)

Layout (shared by all modalities):
    b0        es_imagen            (modality, always stable)
    b1        es_texto             (modality, always stable)
    b2..b15   14 named semantic traits (modality specific)
    b16..b63  48 structural bits   (perceptual DCT hash for images / SimHash for text & bytes)

The code is stored as two 64-bit integers: `value` (bit values) and `care` (stable mask).
Bit i of the integer corresponds to proposition i.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

K = 64
N_SEMANTIC = 14
N_STRUCT = 48
STRUCT_OFFSET = 16
MODALITY_MASK = 0b11  # bits 0 and 1

IMAGE_TRAITS = [
    "rojo_dominante", "amarillo_dominante", "verde_dominante", "cian_dominante",
    "azul_dominante", "magenta_dominante", "alto_brillo", "alta_saturacion",
    "alto_contraste", "bordes_densos", "objeto_centrado", "simetria_horizontal",
    "forma_compacta", "fondo_claro",
]
TEXT_TRAITS = [
    "texto_largo", "densidad_numerica", "mayusculas_frecuentes", "contiene_url",
    "contiene_email", "contiene_codigo", "es_pregunta", "es_estructurado",
    "lista_enumerada", "idioma_es", "idioma_en", "contiene_fecha",
    "contiene_moneda", "alta_diversidad_lexica",
]
BINARY_TRAITS = [f"byte_rasgo_{i:02d}" for i in range(N_SEMANTIC)]


def proposition_names(modality: str) -> List[str]:
    if modality == "image":
        sem, prefix = IMAGE_TRAITS, "phash"
    elif modality == "text":
        sem, prefix = TEXT_TRAITS, "simhash"
    else:
        sem, prefix = BINARY_TRAITS, "bytehash"
    return ["es_imagen", "es_texto"] + list(sem) + [f"{prefix}_{i:02d}" for i in range(N_STRUCT)]


@dataclass
class TernaryCode:
    value: int
    care: int
    modality: str
    margins: List[float] = field(default_factory=list)  # 64 stability margins (inf for crisp bits)

    @property
    def stable_bits(self) -> int:
        return self.care.bit_count()

    def bit(self, i: int) -> Optional[int]:
        if not (self.care >> i) & 1:
            return None
        return (self.value >> i) & 1

    def to_string(self) -> str:
        """MSB-last textual rendering b0..b63 using 1/0/-."""
        return "".join(
            "-" if not (self.care >> i) & 1 else str((self.value >> i) & 1) for i in range(K)
        )

    def to_dict(self) -> Dict[str, Any]:
        names = proposition_names(self.modality)
        return {
            "modality": self.modality,
            "value_hex": f"{self.value:016x}",
            "care_hex": f"{self.care:016x}",
            "ternary": self.to_string(),
            "stable_bits": self.stable_bits,
            "bits": [
                {
                    "i": i,
                    "name": names[i],
                    "state": None if not (self.care >> i) & 1 else (self.value >> i) & 1,
                    "margin": (None if math.isinf(self.margins[i]) else round(self.margins[i], 3))
                    if self.margins
                    else None,
                }
                for i in range(K)
            ],
        }


@dataclass
class PerceivedObject:
    sha256: str
    modality: str  # image | text | binary
    mime: str
    filename: str
    payload: bytes
    code: TernaryCode
    features: Dict[str, Any]
    embedding: List[float]  # continuous vector (baseline for vector-search comparison)
    thumbnail: Optional[bytes] = None  # PNG for images
    text_preview: Optional[str] = None


# ----------------------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------------------


def _trait(value: float, threshold: float, scale: float) -> Tuple[int, float]:
    """Returns (bit, margin) for a continuous trait against a discrete threshold."""
    bit = 1 if value > threshold else 0
    margin = abs(value - threshold) / max(scale, 1e-9)
    return bit, margin


def _crisp(flag: bool) -> Tuple[int, float]:
    return (1 if flag else 0), math.inf


def _assemble(
    modality: str, sem: List[Tuple[int, float]], struct: List[Tuple[int, float]], stability: float
) -> TernaryCode:
    bits: List[Tuple[int, float]] = [
        _crisp(modality == "image"),
        _crisp(modality == "text"),
    ] + sem + struct
    assert len(bits) == K
    value = care = 0
    margins: List[float] = []
    for i, (b, m) in enumerate(bits):
        margins.append(m)
        if b:
            value |= 1 << i
        if m >= stability:
            care |= 1 << i
    value &= care | MODALITY_MASK  # keep values only for stable bits
    return TernaryCode(value=value & care, care=care, modality=modality, margins=margins)


def _dct_matrix(n: int) -> np.ndarray:
    k = np.arange(n)[:, None]
    i = np.arange(n)[None, :]
    m = np.cos(np.pi * (2 * i + 1) * k / (2 * n))
    m[0, :] *= 1 / math.sqrt(2)
    return m * math.sqrt(2 / n)


_DCT32 = _dct_matrix(32)
_ZIGZAG_8 = sorted(((r, c) for r in range(8) for c in range(8)), key=lambda rc: (rc[0] + rc[1], rc[0]))[1:]


# ----------------------------------------------------------------------------------------
# image perception
# ----------------------------------------------------------------------------------------


def _foreground_mask(rgb: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    border = np.concatenate([rgb[0, :], rgb[-1, :], rgb[:, 0], rgb[:, -1]], axis=0).astype(np.float32)
    bg = np.median(border, axis=0)
    dist = np.sqrt(((rgb.astype(np.float32) - bg) ** 2).sum(axis=2))
    mask = dist > 48.0
    frac = mask.mean()
    if frac < 0.01 or frac > 0.97:  # natural photo without clear background -> whole frame
        mask = np.ones(mask.shape, dtype=bool)
    return mask, bg


def shape_descriptor(mask: np.ndarray) -> Dict[str, float]:
    """Rotation-invariant radial profile of a foreground mask (used by the local oracle)."""
    ys, xs = np.nonzero(mask)
    if len(xs) < 20 or mask.all():
        return {"lobes": 0, "radial_cv": 1.0, "fill_circle": 0.0}
    cy, cx = ys.mean(), xs.mean()
    # boundary pixels
    m = mask.astype(np.int8)
    inner = m[1:-1, 1:-1] & m[:-2, 1:-1] & m[2:, 1:-1] & m[1:-1, :-2] & m[1:-1, 2:]
    boundary = m.copy()
    boundary[1:-1, 1:-1] = m[1:-1, 1:-1] - inner
    by, bx = np.nonzero(boundary)
    ang = np.arctan2(by - cy, bx - cx)
    rad = np.hypot(by - cy, bx - cx)
    nbins = 90
    idx = ((ang + np.pi) / (2 * np.pi) * nbins).astype(int) % nbins
    prof = np.zeros(nbins)
    np.maximum.at(prof, idx, rad)
    # fill empty bins by circular interpolation
    if (prof == 0).any():
        good = np.nonzero(prof)[0]
        prof = np.interp(np.arange(nbins), good, prof[good], period=nbins)
    kernel = np.array([1, 2, 3, 2, 1], dtype=float) / 9.0
    sm = np.convolve(np.concatenate([prof[-2:], prof, prof[:2]]), kernel, mode="valid")
    cv = float(sm.std() / max(sm.mean(), 1e-6))
    thr = sm.mean() + 0.25 * sm.std()
    peaks = 0
    for i in range(nbins):
        if sm[i] > thr and sm[i] >= sm[i - 1] and sm[i] > sm[(i + 1) % nbins]:
            peaks += 1
    area = float(mask.sum())
    fill_circle = area / (math.pi * float(rad.max()) ** 2 + 1e-6)
    return {"lobes": int(peaks), "radial_cv": round(cv, 4), "fill_circle": round(fill_circle, 4)}


def perceive_image(data: bytes, filename: str, mime: str, stability: float) -> PerceivedObject:
    from PIL import Image, ImageOps

    img = Image.open(io.BytesIO(data))
    img = ImageOps.exif_transpose(img).convert("RGB")
    thumb = img.copy()
    thumb.thumbnail((256, 256))
    tbuf = io.BytesIO()
    thumb.save(tbuf, format="PNG")

    small = img.resize((128, 128), Image.BILINEAR)
    rgb = np.asarray(small)
    hsv = np.asarray(small.convert("HSV")).astype(np.float32)
    H, S, V = hsv[..., 0], hsv[..., 1] / 255.0, hsv[..., 2] / 255.0
    gray = np.asarray(small.convert("L")).astype(np.float32) / 255.0

    mask, bg = _foreground_mask(rgb)
    fg = mask
    chroma = fg & (S > 0.25) & (V > 0.2)
    n_chroma = max(int(chroma.sum()), 1)
    h = H[chroma]
    bins = {
        "rojo": ((h < 11) | (h >= 235)).sum(),
        "amarillo": ((h >= 11) & (h < 50)).sum(),
        "verde": ((h >= 50) & (h < 115)).sum(),
        "cian": ((h >= 115) & (h < 145)).sum(),
        "azul": ((h >= 145) & (h < 190)).sum(),
        "magenta": ((h >= 190) & (h < 235)).sum(),
    }
    chroma_frac = chroma.sum() / max(int(fg.sum()), 1)
    shares = {k: (v / n_chroma) * min(1.0, chroma_frac * 2.0) for k, v in bins.items()}

    gy, gx = np.gradient(gray)
    grad = np.hypot(gx, gy)
    edge_frac = float((grad > 0.12).mean())

    ys, xs = np.nonzero(fg)
    cy, cx = (ys.mean() / 127.0, xs.mean() / 127.0) if len(xs) else (0.5, 0.5)
    center_dist = math.hypot(cy - 0.5, cx - 0.5)
    sym = 1.0 - float(np.abs(fg.astype(np.float32) - fg[:, ::-1].astype(np.float32)).mean()) * (
        1.0 / max(fg.mean(), 1e-3)
    ) * 0.5
    if len(xs):
        bbox_area = (ys.max() - ys.min() + 1) * (xs.max() - xs.min() + 1)
        fill_ratio = float(fg.sum()) / bbox_area
    else:
        fill_ratio = 1.0
    bg_lum = float((0.299 * bg[0] + 0.587 * bg[1] + 0.114 * bg[2]) / 255.0)
    shape = shape_descriptor(fg)

    feats = {
        **{f"share_{k}": round(float(v), 4) for k, v in shares.items()},
        "brightness": round(float(V.mean()), 4),
        "saturation": round(float(S[fg].mean()) if fg.any() else 0.0, 4),
        "contrast": round(float(gray.std()), 4),
        "edge_density": round(edge_frac, 4),
        "center_dist": round(center_dist, 4),
        "symmetry_h": round(sym, 4),
        "fill_ratio": round(fill_ratio, 4),
        "background_luma": round(bg_lum, 4),
        "foreground_frac": round(float(fg.mean()), 4),
        **shape,
        "width": img.width,
        "height": img.height,
    }

    sem = [
        _trait(shares["rojo"], 0.30, 0.30),
        _trait(shares["amarillo"], 0.30, 0.30),
        _trait(shares["verde"], 0.30, 0.30),
        _trait(shares["cian"], 0.30, 0.30),
        _trait(shares["azul"], 0.30, 0.30),
        _trait(shares["magenta"], 0.30, 0.30),
        _trait(float(V.mean()), 0.55, 0.25),
        _trait(feats["saturation"], 0.45, 0.30),
        _trait(feats["contrast"], 0.22, 0.12),
        _trait(edge_frac, 0.06, 0.05),
        _trait(-center_dist, -0.12, 0.10),
        _trait(sym, 0.85, 0.10),
        _trait(fill_ratio, 0.70, 0.25),
        _trait(bg_lum, 0.60, 0.25),
    ]

    # Perceptual DCT hash on the foreground crop (translation & scale invariant).
    full_gray = img.convert("L")
    if len(xs) and not mask.all():
        sx, sy = img.width / 128.0, img.height / 128.0
        pad = 2
        box = (
            max(0, int((xs.min() - pad) * sx)), max(0, int((ys.min() - pad) * sy)),
            min(img.width, int((xs.max() + pad + 1) * sx)), min(img.height, int((ys.max() + pad + 1) * sy)),
        )
        full_gray = full_gray.crop(box)
    g32 = np.asarray(full_gray.resize((32, 32), Image.BILINEAR)).astype(np.float64)
    dct = _DCT32 @ g32 @ _DCT32.T
    coefs = np.array([dct[r, c] for r, c in _ZIGZAG_8[:N_STRUCT]])
    med = float(np.median(coefs))
    sd = float(coefs.std()) or 1.0
    struct = [(1 if c > med else 0, abs(c - med) / sd) for c in coefs]

    code = _assemble("image", sem, struct, stability)
    embedding = [float(v) for v in list(shares.values())] + [
        feats["brightness"], feats["saturation"], feats["contrast"], edge_frac, center_dist,
        sym, fill_ratio, bg_lum,
    ] + list((coefs - med) / sd)

    return PerceivedObject(
        sha256=hashlib.sha256(data).hexdigest(),
        modality="image",
        mime=mime or "image/png",
        filename=filename,
        payload=data,
        code=code,
        features=feats,
        embedding=embedding,
        thumbnail=tbuf.getvalue(),
    )


# ----------------------------------------------------------------------------------------
# text / data-segment perception
# ----------------------------------------------------------------------------------------

_ES_STOP = {"el", "la", "de", "que", "y", "en", "los", "las", "un", "una", "por", "con", "para", "del", "se", "es", "al", "lo", "como", "más", "pero", "sus", "su", "fue", "este", "esta"}
_EN_STOP = {"the", "of", "and", "to", "in", "is", "that", "for", "it", "with", "as", "was", "on", "be", "at", "by", "this", "are", "from", "or", "an", "have", "not", "but", "you", "your"}
_WORD = re.compile(r"[a-záéíóúñü0-9]+", re.IGNORECASE)


def _hash64(token: str) -> int:
    return int.from_bytes(hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest(), "big")


def _simhash(features: Counter) -> Tuple[List[Tuple[int, float]], np.ndarray]:
    acc = np.zeros(N_STRUCT)
    sq = 0.0
    for tok, w in features.items():
        h = _hash64(tok)
        for b in range(N_STRUCT):
            acc[b] += w if (h >> b) & 1 else -w
        sq += w * w
    norm = math.sqrt(sq) or 1.0
    return [(1 if a > 0 else 0, abs(a) / norm) for a in acc], acc / norm


def perceive_text(text: str, data: bytes, filename: str, mime: str, stability: float) -> PerceivedObject:
    raw = text
    low = raw.lower()
    words = _WORD.findall(low)
    n_words = max(len(words), 1)
    chars = max(len(raw), 1)
    digits = sum(ch.isdigit() for ch in raw) / chars
    letters = [ch for ch in raw if ch.isalpha()]
    upper = sum(ch.isupper() for ch in letters) / max(len(letters), 1)
    es = sum(w in _ES_STOP for w in words) / n_words
    en = sum(w in _EN_STOP for w in words) / n_words
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    enumerated = sum(bool(re.match(r"^([-*•]|\d+[.)])\s", ln)) for ln in lines) / max(len(lines), 1)
    structured = False
    stripped = raw.strip()
    if stripped[:1] in "{[":
        try:
            json.loads(stripped)
            structured = True
        except Exception:
            pass
    if not structured and len(lines) >= 2 and all(ln.count(",") >= 2 for ln in lines[:5]):
        structured = True

    feats = {
        "n_words": len(words),
        "digit_ratio": round(digits, 4),
        "upper_ratio": round(upper, 4),
        "es_ratio": round(es, 4),
        "en_ratio": round(en, 4),
        "lexical_diversity": round(len(set(words)) / n_words, 4),
        "enumerated_ratio": round(enumerated, 4),
    }
    sem = [
        _trait(len(words), 60, 40),
        _trait(digits, 0.08, 0.06),
        _trait(upper, 0.20, 0.12),
        _crisp(bool(re.search(r"https?://|www\.", low))),
        _crisp(bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", low))),
        _crisp(bool(re.search(r"[{};]|def |function |=>|</", raw))),
        _crisp("?" in raw),
        _crisp(structured),
        _trait(enumerated, 0.3, 0.2),
        _trait(es - en, 0.0, 0.04),
        _trait(en - es, 0.0, 0.04),
        _crisp(bool(re.search(r"\b\d{1,4}[-/]\d{1,2}[-/]\d{1,4}\b", raw))),
        _crisp(bool(re.search(r"[$€£]|\busd\b|\beur\b|\bars\b", low))),
        _trait(feats["lexical_diversity"], 0.70, 0.15),
    ]
    content = [w for w in words if w not in _ES_STOP and w not in _EN_STOP]
    grams: Counter = Counter()
    for w in content:
        grams[w] += 1.0
    for a, b in zip(content, content[1:]):
        grams[f"{a}_{b}"] += 0.5
    if not grams:
        grams[low or "<vacio>"] = 1.0
    struct, acc = _simhash(grams)
    code = _assemble("text", sem, struct, stability)
    embedding = [float(len(words)) / 100.0, digits, upper, es, en, feats["lexical_diversity"], enumerated] + list(acc)
    return PerceivedObject(
        sha256=hashlib.sha256(data).hexdigest(),
        modality="text",
        mime=mime or "text/plain",
        filename=filename,
        payload=data,
        code=code,
        features={**feats, "keywords": [w for w, _ in Counter(content).most_common(6)]},
        embedding=embedding,
        text_preview=raw[:600],
    )


def perceive_bytes(data: bytes, filename: str, mime: str, stability: float) -> PerceivedObject:
    grams: Counter = Counter()
    view = data[:65536]
    for i in range(0, max(len(view) - 3, 1), 2):
        grams[view[i : i + 4].hex()] += 1.0
    struct, acc = _simhash(grams)
    hist = np.bincount(np.frombuffer(view or b"\0", dtype=np.uint8), minlength=256) / max(len(view), 1)
    entropy = float(-(hist[hist > 0] * np.log2(hist[hist > 0])).sum())
    sem = [_trait(float(hist[i * 18 : (i + 1) * 18].sum()), 1 / 14, 0.05) for i in range(N_SEMANTIC)]
    code = _assemble("binary", sem, struct, stability)
    return PerceivedObject(
        sha256=hashlib.sha256(data).hexdigest(),
        modality="binary",
        mime=mime or "application/octet-stream",
        filename=filename,
        payload=data,
        code=code,
        features={"size": len(data), "entropy": round(entropy, 4)},
        embedding=list(hist[::8]) + list(acc),
    )


class MultimodalBinarizer:
    """Dispatches raw objects to the proper perceptual projector."""

    def __init__(self, stability_margin: float = 0.18):
        self.stability = stability_margin

    def perceive(
        self,
        data: Optional[bytes] = None,
        filename: str = "objeto",
        mime: str = "",
        text: Optional[str] = None,
    ) -> PerceivedObject:
        if text is not None:
            payload = text.encode("utf-8")
            return perceive_text(text, payload, filename or "fragmento.txt", "text/plain", self.stability)
        if data is None:
            raise ValueError("Se requiere `data` o `text`.")
        mime = (mime or "").lower()
        if mime.startswith("image/") or self._looks_like_image(data):
            return perceive_image(data, filename, mime, self.stability)
        try:
            decoded = data.decode("utf-8")
            if decoded.strip():
                return perceive_text(decoded, data, filename, mime or "text/plain", self.stability)
        except UnicodeDecodeError:
            pass
        return perceive_bytes(data, filename, mime, self.stability)

    @staticmethod
    def _looks_like_image(data: bytes) -> bool:
        sigs = (b"\x89PNG", b"\xff\xd8\xff", b"GIF8", b"BM", b"RIFF")
        return any(data.startswith(s) for s in sigs)
