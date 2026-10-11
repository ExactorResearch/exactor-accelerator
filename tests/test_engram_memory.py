"""
Comprehensive Test Suite for Exactor Engram Associative Memory.
Validates all 4 Pillars of the neuro-symbolic associative architecture:
  1. Multimodal Perception & Projection onto B^64
  2. Multimodal Oracle (System 2 Cognitive Friction Resolution)
  3. Living Memory Ledger (SQLite WAL Payload & Event Persistence)
  4. Engram Compilation & Ultra-low Latency Fast-Path Recall
"""

import os
import shutil
import tempfile
import pytest

from exactor_engram.config import EngramConfig, PLANS
from exactor_engram.perception import MultimodalBinarizer, K, proposition_names
from exactor_engram.demo import render_object, render_text
from exactor_engram.oracle import LocalOracle, OracleRouter, OracleVerdict
from exactor_engram.ledger import MemoryLedger
from exactor_engram.memory import EngramMemory, EngramCompiler, Exemplar


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp(prefix="engram_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def test_config(tmp_dir):
    cfg = EngramConfig(
        db_path=os.path.join(tmp_dir, "test_ledger.db"),
        blob_dir=os.path.join(tmp_dir, "blobs"),
        inline_blob_max_bytes=1024 * 1024,
        plan="PRO",
        stability_margin=0.15,
        guard_tolerance_ratio=0.18,
        guard_min_tolerance=2,
        guard_min_literals=8,
        discriminant_max_bits=8,
    )
    return cfg


# -----------------------------------------------------------------------------
# Pilar 1: Multimodal Perception & Binarization
# -----------------------------------------------------------------------------

def test_pilar1_image_perception():
    binarizer = MultimodalBinarizer(stability_margin=0.15)
    img_bytes = render_object("círculo", "rojo", seed=42)
    obj = binarizer.perceive(data=img_bytes, filename="circulo_rojo.png", mime="image/png")

    assert obj.modality == "image"
    assert obj.sha256 is not None
    assert obj.code.care.bit_count() >= 20  # Has sufficient stable bits
    assert obj.code.bit(0) == 1  # b0: es_imagen is 1
    assert obj.code.bit(1) == 0  # b1: es_texto is 0

    # Named propositions match K=64
    props = proposition_names("image")
    assert len(props) == K
    assert "rojo_dominante" in props
    assert "es_imagen" in props


def test_pilar1_text_perception():
    binarizer = MultimodalBinarizer(stability_margin=0.15)
    txt = render_text("factura pago", seed=101)
    obj = binarizer.perceive(text=txt, filename="factura.txt")

    assert obj.modality == "text"
    assert obj.code.bit(0) == 0  # es_imagen is 0
    assert obj.code.bit(1) == 1  # es_texto is 1
    assert "factura" in txt.lower() or "$" in txt


# -----------------------------------------------------------------------------
# Pilar 2: Multimodal Oracle (System 2)
# -----------------------------------------------------------------------------

def test_pilar2_oracle_resolution(test_config):
    router = OracleRouter(test_config)
    binarizer = MultimodalBinarizer(stability_margin=0.15)
    img_bytes = render_object("estrella", "azul", seed=88)
    obj = binarizer.perceive(data=img_bytes, filename="estrella.png")

    verdict = router.consult(obj, simulate_latency=False)
    assert isinstance(verdict, OracleVerdict)
    assert verdict.label is not None
    assert len(verdict.label) > 0
    assert verdict.tokens_in > 0


# -----------------------------------------------------------------------------
# Pilar 3: Living Memory Ledger (SQLite WAL Persistence)
# -----------------------------------------------------------------------------

def test_pilar3_ledger_payload_persistence(test_config):
    ledger = MemoryLedger(
        db_path=test_config.db_path,
        blob_dir=test_config.blob_dir,
        inline_max=1000,  # low threshold to test file storage
    )

    binarizer = MultimodalBinarizer(stability_margin=0.15)
    img_bytes = render_object("cuadrado", "verde", seed=77)
    obj = binarizer.perceive(data=img_bytes, filename="cuadrado.png")

    mem_id = ledger.store_memory(
        sha256=obj.sha256,
        modality=obj.modality,
        mime=obj.mime,
        filename=obj.filename,
        payload=obj.payload,
        thumbnail=obj.thumbnail,
        text_preview=obj.text_preview,
        code_value=obj.code.value,
        code_care=obj.code.care,
        features=obj.features,
        embedding=obj.embedding,
        label="cuadrado verde",
        description="Figura cuadrada verde",
        tags=["cuadrado", "verde"],
        origin_event_id=None,
    )

    retrieved = ledger.get_memory(mem_id, with_payload=True)
    assert retrieved is not None
    assert retrieved["label"] == "cuadrado verde"
    assert retrieved["storage"] == "file"  # file pointer
    assert retrieved["payload"] == img_bytes  # read from blob path


# -----------------------------------------------------------------------------
# Pilar 4: Engram Compiler & Ultra-Low Latency Fast-Path Recall
# -----------------------------------------------------------------------------

def test_pilar4_cold_start_then_fast_path(test_config):
    memory = EngramMemory(test_config)

    # 1. Cold-start query: "círculo rojo"
    img1 = render_object("círculo", "rojo", seed=10)
    res1 = memory.recall(data=img1, filename="c1.png", mime="image/png", simulate_latency=False)

    assert res1["path"] in ("COLD_START", "ENSENANZA")
    assert res1["system"] == "SISTEMA_2"
    assert res1["label"] is not None
    orig_label = res1["label"]

    # 2. Repeated query with identical object: must be IDENTICO / Fast-Path
    res2 = memory.recall(data=img1, filename="c1.png", mime="image/png", simulate_latency=False)
    assert res2["path"] == "IDENTICO"
    assert res2["system"] == "SISTEMA_1"
    assert res2["label"] == orig_label
    assert res2["savings"]["tokens_saved"] > 0
    assert res2["timing"]["fastpath_us"] > 0

    # 3. Varied exemplar of the same object (different noise / angle / lighting):
    # Evaluates via the compiled Boolean Engram Fast-Path!
    img1_variation = render_object("círculo", "rojo", seed=11)
    res3 = memory.recall(data=img1_variation, filename="c1_var.png", mime="image/png", simulate_latency=False)

    # Either it resolves as FAST_PATH or safely consults the oracle and extends the engram cluster
    assert res3["label"] == orig_label
    assert res3["memory"] is not None


def test_pilar4_engram_benchmark(test_config):
    memory = EngramMemory(test_config)

    # Seed 3 concepts
    for shape, color in [("círculo", "rojo"), ("cuadrado", "azul"), ("triángulo", "verde")]:
        img = render_object(shape, color, seed=99)
        memory.teach(label=f"{shape} {color}", data=img, filename=f"{shape}.png", simulate_latency=False)

    bench = memory.benchmark(iterations=100)
    assert "engram_fastpath_us" in bench
    assert "vector_knn_us" in bench
    assert bench["engram_fastpath_us"] < bench["vector_knn_us"]  # Faster than python k-NN
    assert bench["engram_self_recall_accuracy"] >= 0.90


# -----------------------------------------------------------------------------
# Plan Limits & Licensing Validation
# -----------------------------------------------------------------------------

def test_plan_limits_validation():
    # Attempting to run with k=64 under GRATIS plan (max 12 vars) must be blocked
    gratis_cfg = EngramConfig(plan="GRATIS")
    with pytest.raises(ValueError, match="requiere al menos PRO / DEV"):
        gratis_cfg.validate()

    # PRO plan allows up to 64 variables
    pro_cfg = EngramConfig(plan="PRO")
    pro_cfg.validate()  # Passes without error
    assert pro_cfg.plan_limits.max_variables == 64
