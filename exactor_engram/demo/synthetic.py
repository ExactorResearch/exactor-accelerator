"""
Synthetic demo corpus: "photos" of the same objects under different conditions
(position, scale, rotation, lighting, sensor noise, background tint) plus families of
text / data fragments with paraphrases. Deterministic given a seed.
"""

from __future__ import annotations

import io
import math
import random
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PALETTE: Dict[str, Tuple[int, int, int]] = {
    "rojo": (226, 52, 64),
    "amarillo": (246, 196, 40),
    "verde": (46, 184, 92),
    "azul": (48, 102, 230),
    "magenta": (206, 60, 190),
    "cian": (40, 200, 214),
}
SHAPES = ["círculo", "cuadrado", "triángulo", "estrella"]

DEMO_CONCEPTS: List[Tuple[str, str]] = [
    ("círculo", "rojo"), ("cuadrado", "azul"), ("triángulo", "verde"), ("estrella", "amarillo"),
    ("círculo", "magenta"), ("cuadrado", "cian"), ("triángulo", "rojo"), ("estrella", "azul"),
]


def _polygon(shape: str, cx: float, cy: float, r: float, rot: float) -> List[Tuple[float, float]]:
    if shape == "cuadrado":
        n, radii = 4, [r * 1.0]
        base = math.pi / 4
    elif shape == "triángulo":
        n, radii = 3, [r * 1.1]
        base = -math.pi / 2
    else:  # estrella
        n, radii = 10, [r * 1.15, r * 0.48]
        base = -math.pi / 2
    pts = []
    for i in range(n):
        a = base + rot + 2 * math.pi * i / n
        rr = radii[i % len(radii)]
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def render_object(shape: str, color: str, seed: Optional[int] = None, size: int = 320) -> bytes:
    rnd = random.Random(seed)
    bg_v = rnd.randint(228, 250)
    tint = [bg_v + rnd.randint(-8, 4) for _ in range(3)]
    img = Image.new("RGB", (size, size), tuple(int(max(0, min(255, t))) for t in tint))
    d = ImageDraw.Draw(img)
    r = size * rnd.uniform(0.22, 0.32)
    cx = size / 2 + rnd.uniform(-0.12, 0.12) * size
    cy = size / 2 + rnd.uniform(-0.12, 0.12) * size
    rot = math.radians(rnd.uniform(-14, 14))
    light = rnd.uniform(0.86, 1.10)
    base = PALETTE[color]
    fill = tuple(int(max(0, min(255, c * light + rnd.randint(-10, 10)))) for c in base)
    if shape == "círculo":
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)
    else:
        d.polygon(_polygon(shape, cx, cy, r, rot), fill=fill)
    img = img.filter(ImageFilter.GaussianBlur(rnd.uniform(0.0, 1.1)))
    arr = np.asarray(img).astype(np.int16)
    noise = np.random.default_rng(seed).normal(0, rnd.uniform(2, 7), arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()


TEXT_FAMILIES: Dict[str, List[str]] = {
    "factura pago": [
        "Factura N° {n} emitida el {d}. Total a pagar: $ {a} USD. Vence en 30 días. Medio de pago: transferencia bancaria a la cuenta corporativa.",
        "Adjuntamos la factura {n} con fecha {d}. El importe total es $ {a} USD y el pago debe realizarse por transferencia bancaria antes del vencimiento.",
        "Recordatorio: la factura {n} del {d} por $ {a} USD sigue pendiente de pago. Puede abonarla por transferencia bancaria.",
    ],
    "incidente servidor": [
        "ALERTA: el servidor api-{n} supera 95% de CPU desde las 03:{m}. Latencia p99 de 2.4 s y errores 502 en el balanceador.",
        "Incidente crítico en api-{n}: uso de CPU al 97%, latencia p99 elevada y respuestas 502 desde el balanceador de carga.",
        "El nodo api-{n} reporta saturación de CPU y picos de latencia; el balanceador devuelve errores 502 a los clientes.",
    ],
    "receta cocina": [
        "Receta de pan casero: mezclar 500 g de harina, 10 g de levadura, agua tibia y sal. Amasar 10 minutos y hornear a 220 grados.",
        "Para el pan casero se necesita harina, levadura, agua tibia y sal; amasar bien, dejar levar y hornear a 220 grados unos 35 minutos.",
        "Pan casero fácil: harina, levadura y agua tibia con una pizca de sal. Amasar, levar una hora y hornear a 220 grados.",
    ],
}


def render_text(concept: str, seed: Optional[int] = None) -> str:
    rnd = random.Random(seed)
    tpl = rnd.choice(TEXT_FAMILIES[concept])
    return tpl.format(
        n=rnd.randint(1000, 9999), d=f"{rnd.randint(1, 28)}/{rnd.randint(1, 12)}/2026",
        a=f"{rnd.randint(100, 9000)}.{rnd.randint(0, 99):02d}", m=f"{rnd.randint(0, 59):02d}",
    )
