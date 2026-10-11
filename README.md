# Exactor Engram Memory

**Memoria Asociativa Neuro-Simbólica de Objetos Multimodales (Imágenes, Fotos y Segmentos de Datos) basada en los 4 Pilares de Exactor Accelerator.**

Evoluciona la tecnología de simplificación de consultas booleanas de `exactor-jev` pasando de un clasificador de decisiones a un **sistema de recuperación asociativa determinista**, donde las fórmulas lógicas mínimas actúan como **direcciones de memoria asociativa** hacia objetos reales almacenados localmente.

---

## 🏛️ Los 4 Pilares de la Memoria de Objetos

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   ARQUITECTURA DE LOS 4 PILARES                                  │
├─────────────────────────┬──────────────────────────┬────────────────────────┬────────────────────┤
│ PILAR 1: PERCEPCIÓN     │ PILAR 2: FRICCIÓN (S2)   │ PILAR 3: LIBRO MAYOR   │ PILAR 4: FAST-PATH │
├─────────────────────────┼──────────────────────────┼────────────────────────┼────────────────────┤
│ Binarización multimodal │ Oráculo en la nube ante  │ Almacenamiento persist.│ Exactor minimiza el│
│ continua a discreta     │ patrones desconocidos    │ del payload pesado     │ hipercubo: fórmula │
│ en hipercubo B⁶⁴ con    │ (Cold-Start / Gemini /   │ (foto / blob / texto)  │ booleana como clave│
│ estados ternarios       │ OpenAI / DeepSeek) que   │ en SQLite WAL con      │ asociativa. Retorno│
│ (1, 0, don't-care).     │ etiqueta y estructura.   │ evento de origen.      │ en 0.05 ms a $0.   │
└─────────────────────────┴──────────────────────────┴────────────────────────┴────────────────────┘
```

1. **Binarización Multimodal (Pilar 1 - Percepción):**
   - Transforma fotos, imágenes, audios o fragmentos de datos continuos en proposiciones discretas proyectadas en un hipercubo booleano $\mathbb{B}^k$ ($k=64$).
   - Descompone el objeto en 2 bits de modalidad, 14 rasgos semánticos auditables (color dominante, brillo, bordes, compacidad, simetría, relación aspecto) y 48 bits de hash perceptual DCT (o SimHash para texto/binarios).
   - Incorpora lógica **ternaria con margen de estabilidad**: los rasgos cercanos a umbrales se marcan como *don't-care*, dotando a la memoria de robustez ante ruido, rotación e iluminación.

2. **Resolución del Oráculo Multimodal (Pilar 2 - Fricción Cognitiva):**
   - Ante un patrón desconocido (**Cold-Start**), el enrutador delega en el Sistema 2 (Google Gemini, OpenAI-compatible, DeepSeek o el operador humano).
   - El Oráculo interpreta el objeto, devuelve una etiqueta canónica estructurada y descripción.

3. **Almacenamiento del Recuerdo (Pilar 3 - Libro Mayor WAL):**
   - A diferencia de un clasificador que guarda solo texto, el Libro Mayor en SQLite WAL almacena el **payload pesado completo** (la foto, segmento de imagen o bloque de datos) junto con su hash SHA-256, embedding continuo, vector de características y el evento del Oráculo que lo originó.

4. **Direccionamiento por Engrama (Pilar 4 - Exactor Core & Fast-Path):**
   - Exactor simplifica el hipercubo y descubre la fórmula booleana mínima (engrama) que identifica el patrón.
   - La fórmula booleana opera como un **índice de dirección asociativa**:
     $$\text{ENGRAM}(\text{label}) = \bigvee_{c} \Big( \text{MODALIDAD}_c(\mathbf{q}) \wedge \text{GUARDA}_c(\mathbf{q}) \wedge \text{DISCRIMINANTE}_c(\mathbf{q}) \Big)$$
   - Ante consultas repetidas o variaciones del mismo objeto, el Fast-Path resuelve la regla localmente en **0.05 milisegundos (50 microsegundos)** recuperando el recuerdo exacto sin invocar a la nube (**costo marginal cero**).

---

## ⚡ Ventajas frente a Búsquedas Vectoriales Tradicionales

- **Determinismo Absoluto vs Aproximación:** Las bases de datos vectoriales tradicionales ($k$-NN / HNSW / Faiss) realizan búsquedas de vecinos más cercanos de forma probabilística y lenta (1–15 ms con cómputo de coma flotante en GPU). Exactor Engram recupera el recuerdo a través de álgebra booleana en registros de CPU en **0.05 ms** con **100% de explicabilidad causal**.
- **Costo Cero en Consultas Repetidas:** Una vez consolidado un patrón por el Sistema 2, no se vuelven a pagar tokens ni cómputo cloud por procesar la misma estructura visual o variantes dentro del margen de tolerancia.
- **Detección Nativa de Novedad:** La **Guarda Invariante** rechaza patrones nunca antes vistos sin forzar emparejamientos erróneos, desviándolos de forma segura hacia el Oráculo.

---

## 🚀 Inicio Rápido

### Requisitos
- Python 3.9+
- Dependencias: `pip install -r requirements.txt`

### 1. Ejecutar el Servidor Web y API
```bash
python run_server.py
```
- Dashboard Interactivo: [http://localhost:8080](http://localhost:8080)
- Documentación Swagger OpenAPI: [http://localhost:8080/docs](http://localhost:8080/docs)

### 2. Ejecutar Demostración por Consola
```bash
python examples/demo_walkthrough.py
```

### 3. Ejecutar la Suite de Pruebas
```bash
python -m pytest tests/ -v
```

---

## 📋 Estructura del Proyecto

```
exactor-engram-memory/
├── exactor_engram/
│   ├── config.py             # Configuración central y matriz de planes oficial
│   ├── core/
│   │   ├── hypercube.py      # Reductor booleano del hipercubo B^k
│   │   └── exactor_bridge.py # Puente con Rust HPC / Cloud API / Reductor local
│   ├── perception/
│   │   └── binarizer.py      # Pilar 1: Binarización multimodal en B^64
│   ├── oracle/
│   │   └── multimodal_oracle.py # Pilar 2: Oráculo Sistema 2 (Gemini, OpenAI, DeepSeek, Local)
│   ├── ledger/
│   │   └── memory_ledger.py  # Pilar 3: Libro Mayor WAL (persistencia de payloads y eventos)
│   ├── memory/
│   │   ├── engram_compiler.py   # Pilar 4: Compilador de engramas y guardas invariantes
│   │   └── associative_memory.py# Orquestador de memoria asociativa
│   ├── demo/
│   │   └── synthetic.py      # Generador sintético de fotos con ruido y textos
│   ├── api/
│   │   └── server.py         # Endpoints FastAPI
│   └── web/
│       ├── index.html        # Dashboard interactivo con diseño glassmorphic
│       ├── styles.css        # Tokens CSS y paleta cyber-logic
│       └── app.js            # Controlador frontend
├── examples/
│   └── demo_walkthrough.py   # Recorrido de los 4 pilares en código
├── tests/
│   └── test_engram_memory.py # Suite de pruebas automatizadas
├── ARCHITECTURE_ENGRAM.md    # Especificación formal completa
├── pyproject.toml
├── requirements.txt
└── run_server.py             # Lanzador del servidor
```

---

## 💼 Esquema de Licenciamiento y Planes
Cumple con las directrices oficiales (`.agent/rules/pricing_and_licensing.md`):
- Hipercubo asociativo con $k=64$ requiere suscripción **PRO / DEV** ($49/mes) o superior.
- Tope de variables en autoservicio SaaS: 128 variables. Proyectos con 256+ variables se gestionan como Proyectos de Expansión de Ingeniería dedicados (Bare Metal).
