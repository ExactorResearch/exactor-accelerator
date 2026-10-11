"""
End-to-End Walkthrough Demonstration of Exactor Engram Associative Memory.
Shows how the 4 Pillars operate together in code:
  1. Multimodal Perception (Projection to B^64)
  2. Cognitive Friction Resolution (Oracle System 2)
  3. Memory Ledger Persistence (Payload & Events in SQLite WAL)
  4. Engram Addressing & Fast-Path Microsecond Recall (System 1)
"""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exactor_engram.config import EngramConfig
from exactor_engram.memory import EngramMemory
from exactor_engram.demo import render_object, render_text


def main():
    print("=" * 80)
    print("  EXACTOR ENGRAM MEMORY - RECORRIDO DE LOS 4 PILARES")
    print("=" * 80)

    cfg = EngramConfig(
        db_path=":memory:",  # In-memory for pristine demonstration run
        plan="PRO",
        stability_margin=0.15,
    )
    memory = EngramMemory(cfg)

    # -------------------------------------------------------------------------
    # PASO 1: Cold-Start (Objeto Desconocido -> Oráculo Sistema 2)
    # -------------------------------------------------------------------------
    print("\n[PASO 1] Presentando un objeto desconocido por primera vez (Cold-Start)...")
    circulo_rojo_img1 = render_object("círculo", "rojo", seed=42)

    res1 = memory.recall(
        data=circulo_rojo_img1,
        filename="foto_circulo_1.png",
        mime="image/png",
        simulate_latency=False,
    )

    print(f"  • Ruta resuelta:        {res1['path']} ({res1['system']})")
    print(f"  • Etiqueta del Oráculo: {res1['label']}")
    print(f"  • Memoria Almacenada:   ID {res1['memory']['id']} ({res1['memory']['size_bytes']} bytes en SQLite WAL)")
    print(f"  • Versión de Engrama:   v{res1['engram_version']}")
    print(f"  • Tiempo Total:         {res1['timing']['total_ms']:.2f} ms (Invocó Sistema 2)")

    # -------------------------------------------------------------------------
    # PASO 2: Consulta Repetida Idéntica (Fast-Path -> Costo Marginal Cero)
    # -------------------------------------------------------------------------
    print("\n[PASO 2] Re-consultando el objeto idéntico en producción...")
    res2 = memory.recall(
        data=circulo_rojo_img1,
        filename="foto_circulo_1.png",
        mime="image/png",
        simulate_latency=False,
    )

    print(f"  - Ruta resuelta:        {res2['path']} ({res2['system']})")
    print(f"  - Memoria Recuperada:   {res2['memory']['label']} (ID: {res2['memory']['id']})")
    print(f"  - Tiempo Fast-Path:     {res2['timing']['fastpath_us']:.2f} us ({(res2['timing']['fastpath_us']/1000):.4f} ms)")
    print(f"  - Ahorro de Tokens:     {res2['savings']['tokens_saved']} tokens")
    print(f"  - Costo Marginal:       ${res2['savings']['cost_saved_usd']:.4f} USD ($0.00 pagados a la nube)")

    # -------------------------------------------------------------------------
    # PASO 3: Nueva Foto con Ruido / Rotación / Variación del Mismo Objeto
    # -------------------------------------------------------------------------
    print("\n[PASO 3] Consultando una nueva foto del mismo objeto (con ruido, rotacion y diferente iluminacion)...")
    circulo_rojo_img2 = render_object("círculo", "rojo", seed=43)

    res3 = memory.recall(
        data=circulo_rojo_img2,
        filename="foto_circulo_2_ruido.png",
        mime="image/png",
        simulate_latency=False,
    )

    print(f"  - Ruta resuelta:        {res3['path']} ({res3['system']})")
    print(f"  - Memoria Asociada:     {res3['memory']['label']} (ID: {res3['memory']['id']})")
    print(f"  - Tiempo de Decision:   {res3['timing']['fastpath_us']:.2f} us")
    if res3["proof"]:
        g = res3["proof"][0]["guard"]
        print(f"  - Guarda Invariante:    {g['matched']} / {g['literals']} literales satisfechos (Tolerancia: <= {g['tolerance']})")

    # -------------------------------------------------------------------------
    # PASO 4: Enseñar una Familia Textual (Segmentos de Datos)
    # -------------------------------------------------------------------------
    print("\n[PASO 4] Incorporando un segmento de datos / texto no estructurado...")
    txt_factura = render_text("factura pago", seed=100)
    res4 = memory.teach(
        label="factura pago",
        text=txt_factura,
        filename="factura_1.txt",
        simulate_latency=False,
    )
    print(f"  - Concepto Ensenado:    {res4['label']} (v{res4['engram_version']})")

    # -------------------------------------------------------------------------
    # PASO 5: Benchmark contra Búsqueda Vectorial (k-NN)
    # -------------------------------------------------------------------------
    print("\n[PASO 5] Ejecutando Benchmark en vivo (Engramas Booleanos vs k-NN Coseno)...")
    bench = memory.benchmark(iterations=500)
    print(f"  - Latencia Fast-Path Engrama: {bench['engram_fastpath_us']:.2f} us")
    print(f"  - Latencia Busqueda k-NN:     {bench['vector_knn_us']:.2f} us")
    print(f"  - Factor de Aceleracion:      {bench['speedup']}x mas rapido")
    print(f"  - Precision Causal:           {bench['engram_self_recall_accuracy']*100:.1f}%")

    print("\n" + "=" * 80)
    print("  DEMOSTRACION COMPLETADA CON EXITO")
    print("=" * 80)


if __name__ == "__main__":
    main()
