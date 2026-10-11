"""
FastAPI Server & REST API for Exactor Engram Associative Memory.
Exposes endpoints for multimodal object perception, System 1 Fast-Path recall,
System 2 Oracle cognitive friction resolution, memory inspection, and benchmarks.
"""

from __future__ import annotations

import io
import json
import logging
import os
import random
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..config import get_config
from ..demo import DEMO_CONCEPTS, render_object, render_text
from ..memory import EngramMemory

logger = logging.getLogger("exactor_engram.api")

app = FastAPI(
    title="Exactor Engram Memory API",
    description="Deterministic Associative Memory for Multimodal Objects (Images, Photos, and Data Segments)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global singleton memory instance
_memory: Optional[EngramMemory] = None


def get_memory_instance() -> EngramMemory:
    global _memory
    if _memory is None:
        _memory = EngramMemory(get_config())
    return _memory


# -----------------------------------------------------------------------------
# Request Models
# -----------------------------------------------------------------------------


class TextRecallRequest(BaseModel):
    text: str
    filename: Optional[str] = "fragmento.txt"
    allow_oracle: bool = True
    label_hint: Optional[str] = None
    simulate_latency: bool = True


class TeachRequest(BaseModel):
    text: Optional[str] = None
    label: str
    filename: Optional[str] = "objeto"


# -----------------------------------------------------------------------------
# System & Status
# -----------------------------------------------------------------------------


@app.get("/api/system/status")
def system_status():
    mem = get_memory_instance()
    return mem.stats()


@app.post("/api/system/reset")
def system_reset():
    mem = get_memory_instance()
    mem.reset()
    return {"status": "ok", "message": "Memoria viva y libro mayor reiniciados exitosamente."}


# -----------------------------------------------------------------------------
# Perception (Pilar 1)
# -----------------------------------------------------------------------------


@app.post("/api/perceive/text")
def perceive_text_api(req: TextRecallRequest):
    mem = get_memory_instance()
    obj = mem.perceive(text=req.text, filename=req.filename or "fragmento.txt")
    return {
        "sha256": obj.sha256,
        "modality": obj.modality,
        "code": obj.code.to_dict(),
        "features": obj.features,
        "preview": obj.text_preview,
    }


@app.post("/api/perceive/file")
async def perceive_file_api(file: UploadFile = File(...)):
    mem = get_memory_instance()
    data = await file.read()
    obj = mem.perceive(data=data, filename=file.filename or "archivo", mime=file.content_type or "")
    return {
        "sha256": obj.sha256,
        "modality": obj.modality,
        "filename": obj.filename,
        "code": obj.code.to_dict(),
        "features": obj.features,
    }


# -----------------------------------------------------------------------------
# Recall & Association (Pilares 1, 2, 3, 4)
# -----------------------------------------------------------------------------


@app.post("/api/recall/text")
def recall_text_api(req: TextRecallRequest):
    mem = get_memory_instance()
    res = mem.recall(
        text=req.text,
        filename=req.filename or "fragmento.txt",
        allow_oracle=req.allow_oracle,
        label_hint=req.label_hint,
        simulate_latency=req.simulate_latency,
    )
    return res


@app.post("/api/recall/file")
async def recall_file_api(
    file: UploadFile = File(...),
    allow_oracle: bool = Form(True),
    label_hint: Optional[str] = Form(None),
    simulate_latency: bool = Form(True),
):
    mem = get_memory_instance()
    data = await file.read()
    res = mem.recall(
        data=data,
        filename=file.filename or "archivo",
        mime=file.content_type or "",
        allow_oracle=allow_oracle,
        label_hint=label_hint,
        simulate_latency=simulate_latency,
    )
    return res


@app.post("/api/teach")
async def teach_api(
    label: str = Form(...),
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    mem = get_memory_instance()
    if file is not None:
        data = await file.read()
        res = mem.teach(label=label, data=data, filename=file.filename or "objeto", mime=file.content_type or "")
    elif text:
        res = mem.teach(label=label, text=text, filename="fragmento.txt")
    else:
        raise HTTPException(status_code=400, detail="Se requiere un archivo o texto para enseñar.")
    return res


# -----------------------------------------------------------------------------
# Memories & Blobs (Pilar 3)
# -----------------------------------------------------------------------------


@app.get("/api/memories")
def list_memories(label: Optional[str] = Query(None), limit: int = Query(100)):
    mem = get_memory_instance()
    return mem.ledger.list_memories(label=label, limit=limit)


@app.get("/api/memories/{mem_id}")
def get_memory_detail(mem_id: str):
    mem = get_memory_instance()
    item = mem.ledger.get_memory(mem_id, with_payload=False)
    if not item:
        raise HTTPException(status_code=404, detail="Memoria no encontrada")
    return item


@app.get("/api/memories/{mem_id}/thumbnail")
def get_memory_thumbnail(mem_id: str):
    mem = get_memory_instance()
    thumb = mem.ledger.get_thumbnail(mem_id)
    if not thumb:
        raise HTTPException(status_code=404, detail="Miniatura no encontrada")
    return Response(content=thumb, media_type="image/png")


@app.get("/api/memories/{mem_id}/payload")
def get_memory_payload(mem_id: str):
    mem = get_memory_instance()
    item = mem.ledger.get_memory(mem_id, with_payload=True)
    if not item or "payload" not in item:
        raise HTTPException(status_code=404, detail="Payload de memoria no encontrado")
    return Response(content=item["payload"], media_type=item.get("mime", "application/octet-stream"))


# -----------------------------------------------------------------------------
# Engrams & Hypercube Minimization (Pilar 4)
# -----------------------------------------------------------------------------


@app.get("/api/engrams")
def get_engrams():
    mem = get_memory_instance()
    return mem.engrams.to_dict()


@app.post("/api/engrams/consolidate")
def consolidate_engrams():
    mem = get_memory_instance()
    return mem.consolidate(trigger="api-manual")


@app.get("/api/engrams/history")
def engram_history(limit: int = Query(20)):
    mem = get_memory_instance()
    return mem.ledger.engram_history(limit=limit)


# -----------------------------------------------------------------------------
# Ledger & Events
# -----------------------------------------------------------------------------


@app.get("/api/ledger/recalls")
def recent_recalls(limit: int = Query(50)):
    mem = get_memory_instance()
    return mem.ledger.recent_recalls(limit=limit)


# -----------------------------------------------------------------------------
# Benchmarks & Demos
# -----------------------------------------------------------------------------


@app.get("/api/benchmark")
def run_benchmark(iterations: int = Query(1000)):
    mem = get_memory_instance()
    return mem.benchmark(iterations=iterations)


@app.post("/api/demo/seed")
def seed_demo(
    concepts: int = Query(6, ge=1, le=8),
    exemplars_per_concept: int = Query(2, ge=1, le=5),
):
    mem = get_memory_instance()
    created = []

    # Seed images
    selected_concepts = DEMO_CONCEPTS[:concepts]
    for shape, color in selected_concepts:
        label = f"{shape} {color}"
        for i in range(exemplars_per_concept):
            img_bytes = render_object(shape, color, seed=100 + i * 37 + hash(label) % 1000)
            res = mem.teach(
                label=label,
                data=img_bytes,
                filename=f"{shape}_{color}_{i}.png",
                mime="image/png",
                simulate_latency=False,
            )
            created.append({"type": "image", "label": label, "memory_id": res.get("memory", {}).get("id")})

    # Seed text families
    for concept_name in ["factura pago", "incidente servidor", "receta cocina"][: max(1, concepts // 2)]:
        for i in range(exemplars_per_concept):
            sample_txt = render_text(concept_name, seed=200 + i * 43)
            res = mem.teach(
                label=concept_name,
                text=sample_txt,
                filename=f"{concept_name.replace(' ', '_')}_{i}.txt",
                simulate_latency=False,
            )
            created.append({"type": "text", "label": concept_name, "memory_id": res.get("memory", {}).get("id")})

    return {
        "status": "seeded",
        "total_created": len(created),
        "concepts_seeded": len(selected_concepts) + min(concepts // 2, 3),
        "stats": mem.stats(),
    }


@app.get("/api/demo/samples")
def get_sample_queries():
    """Generates a fresh set of query samples for testing in the UI."""
    samples = []
    # Images with novel random variation (new orientation/tint)
    for shape, color in DEMO_CONCEPTS[:4]:
        raw_png = render_object(shape, color, seed=random.randint(10000, 99999))
        import base64

        b64 = base64.b64encode(raw_png).decode("ascii")
        samples.append({
            "name": f"{shape.capitalize()} {color} (variación)",
            "type": "image",
            "label_expected": f"{shape} {color}",
            "mime": "image/png",
            "data_url": f"data:image/png;base64,{b64}",
        })

    # Unknown novel image (cold start trigger)
    unknown_png = render_object("estrella", "cian", seed=999999)
    import base64

    samples.append({
        "name": "Estrella cian (NOVEDAD / Cold Start)",
        "type": "image",
        "label_expected": "estrella cian",
        "mime": "image/png",
        "data_url": f"data:image/png;base64,{base64.b64encode(unknown_png).decode('ascii')}",
    })

    # Text samples
    samples.append({
        "name": "Factura nueva con otro importe",
        "type": "text",
        "label_expected": "factura pago",
        "text": render_text("factura pago", seed=8888),
    })
    samples.append({
        "name": "Incidente CPU en nodo nuevo",
        "type": "text",
        "label_expected": "incidente servidor",
        "text": render_text("incidente servidor", seed=7777),
    })

    return samples


# -----------------------------------------------------------------------------
# Static Web Frontend
# -----------------------------------------------------------------------------

web_dir = os.path.join(os.path.dirname(__file__), "..", "web")
if os.path.isdir(web_dir):
    app.mount("/static", StaticFiles(directory=web_dir), name="static")


@app.get("/", response_class=HTMLResponse)
def index_page():
    index_path = os.path.join(web_dir, "index.html")
    if os.path.isfile(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Exactor Engram Memory API</h1><p>Web frontend en construcción.</p>"
