# Arquitectura de Memoria Asociativa de Objetos (Exactor Engram Memory)

## 1. Fundamentos Neurobiológicos y Evolución de Exactor Accelerator

En la arquitectura original de **Exactor Accelerator (`exactor-jev`)**, el sistema replica el aprendizaje humano dividiendo el procesamiento cognitivo entre dos sistemas complementarios:
- **Sistema 2 (Razonamiento Lento y Costoso):** Oráculos multimodales y LLMs en la nube que resuelven situaciones no vistas con alta fricción y latencia (1,200–3,500 ms).
- **Sistema 1 (Reflejos Locales Instantáneos):** Autómatas deterministas locales que resuelven en 0.05 ms y a costo marginal cero ($0.00).

**Evolución Arquitectónica:**  
La propuesta de almacenar "recuerdos" complejos amplía el alcance de este motor neuro-simbólico pasándolo de un **clasificador de decisiones lógicas** a un **sistema de recuperación asociativa determinista**. Las fórmulas booleanas minimizadas descubiertas por Exactor dejan de ser meras reglas de corte y se convierten en **claves de direccionamiento asociativo** hacia objetos reales en almacenamiento local (fotos, imágenes, audios o fragmentos de datos).

---

## 2. Los 4 Pilares Adaptados a la Memoria Asociativa

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   ARQUITECTURA DE LOS 4 PILARES                                  │
├─────────────────────────┬──────────────────────────┬────────────────────────┬────────────────────┤
│ PILAR 1: PERCEPCIÓN     │ PILAR 2: FRICCIÓN (S2)   │ PILAR 3: LIBRO MAYOR   │ PILAR 4: FAST-PATH │
├─────────────────────────┼──────────────────────────┼────────────────────────┼────────────────────┤
│ Extracción multimodal   │ Cold-start derivado a la │ Almacenamiento del     │ Exactor simplifica │
│ y binarización en       │ nube (Gemini, OpenAI,    │ payload pesado (foto / │ el hipercubo a     │
│ hipercubo B⁶⁴ con       │ DeepSeek, Local).        │ blob / texto) junto    │ fórmulas engrama:  │
│ estados ternarios       │ Genera etiqueta canónica │ al evento de origen    │ recuperación en    │
│ (1, 0, don't-care).     │ y semántica estructurada.│ en SQLite WAL.         │ 0.05 ms / $0 cost. │
└─────────────────────────┴──────────────────────────┴────────────────────────┴────────────────────┘
```

### Pilar 1: Binarización Multimodal (Percepción en $\mathbb{B}^{64}$)
Para que un objeto ingrese al hipercubo booleano $\mathbb{B}^{64}$:
1. Se extrae un vector de características (proporciones cromáticas HSV, gradientes de borde, simetría, relación de aspecto, compacidad y perfiles radiales de forma) junto con un hash perceptual DCT de 48 bits (o SimHash para texto/binarios).
2. Los valores continuos se proyectan a proposiciones booleanas discretas mediante umbrales calibrados.
3. **Manejo Ternario de Incertidumbre:** Aquellos rasgos continuos cuya distancia al umbral sea inferior al margen de estabilidad se marcan como *don't-care* ($-$). Esto evita que pequeñas perturbaciones de sensor o compresión alteren la recuperación.
4. **Espacio Proposicional ($k=64$):**
   - $b_0$: `es_imagen` (modality guard)
   - $b_1$: `es_texto` (modality guard)
   - $b_2 \dots b_{15}$: 14 rasgos semánticos auditables (color dominante, brillo, saturación, bordes, centrado, etc.)
   - $b_{16} \dots b_{63}$: 48 bits estructurales invariantes por traslación/escala (pHash / SimHash)

### Pilar 2: Resolución del Oráculo Multimodal (Fricción Cognitiva)
Ante un patrón desconocido (**Cold-Start**) o ante una colisión entre múltiples conceptos (**Ambigüedad**):
1. El enrutador desvía el objeto hacia el **Sistema 2** (Google Gemini, endpoint compatible con OpenAI, DeepSeek o el operador humano).
2. El Oráculo interpreta el objeto, devuelve una etiqueta canónica estructurada, descripción ejecutiva y etiquetas semánticas.

### Pilar 3: Almacenamiento del Recuerdo (Libro Mayor WAL SQLite)
A diferencia de un clasificador que solo registra texto plano, el Libro Mayor almacena el **recuerdo completo**:
- **Inline BLOB:** Cargas de hasta 2 MB persisten directamente en SQLite WAL.
- **Punteros Content-Addressed:** Cargas pesadas se resguardan en disco indexadas por SHA-256.
- Vinculación atómica con el evento del Oráculo (tokens consumidos, latencia, modelo) y metadatos de acceso.

### Pilar 4: Direccionamiento por Engrama (Exactor Core & Fast-Path)
El motor minimiza el hipercubo encontrando la expresión canónica irreducible:
$$\text{ENGRAM}(\text{label}) = \bigvee_{c} \Big( \text{MODALIDAD}_c(\mathbf{q}) \wedge \text{GUARDA}_c(\mathbf{q}) \wedge \text{DISCRIMINANTE}_c(\mathbf{q}) \Big)$$
- **Guarda Invariante:** Función umbral booleana sobre los literales comunes de todos los ejemplares consolidados. Resuelve la **detección de novedad en mundo abierto** (rechaza objetos jamás vistos sin forzar clasificaciones erróneas).
- **Discriminante Exactor:** Fórmula mínima producida por el minimizador (Rust HPC o hipercubo local) que separa el concepto de todos los competidores en el espacio proyectado.
- **Evaluación en Hardware:** En consultas subsecuentes, el Fast-Path evalúa la fórmula con operaciones booleanas a nivel de registro de CPU en **0.05 ms (50 microsegundos)**, recuperando el payload directamente desde la memoria viva local con costo marginal cero ($0).

---

## 3. Ventajas Frente a Bases de Datos Vectoriales Tradicionales ($k$-NN)

| Dimensión | Búsquedas Vectoriales Tradicionales (HNSW, Faiss, Pinecone) | Exactor Engram Memory |
| :--- | :--- | :--- |
| **Naturaleza Matemática** | Probabilística aproximada ($k$-NN sobre métricas de distancia en espacio continuo). | **Determinista y Exacta** sobre álgebra booleana irreducible en $\mathbb{B}^k$. |
| **Velocidad de Recuperación** | 1.5 a 15 ms (cálculo de producto punto en coma flotante / GPU). | **0.01 a 0.05 ms** (operaciones bitwise en registros enteros de CPU). |
| **Costo por Consulta Repetida** | Cómputo continuo o costo recurrente por vector consultado. | **$0.00 exacto** (Costo marginal nulo en Fast-Path local). |
| **Explicabilidad y Causalidad** | Caja negra (distancia matemática abstracta sin prueba causal). | **100% Causal y Auditable** (Muestra qué literales e invariantes activaron el recuerdo). |
| **Detección de Novedad** | Difícil: siempre devuelve los vecinos más cercanos aunque sean conceptualmente lejanos. | **Nativa:** La Guarda Invariante rechaza automáticamente patrones fuera del radio de tolerancia. |

---

## 4. Conformidad con el Modelo Comercial y Límites de Licenciamiento

El sistema respeta taxativamente las reglas comerciales de Exactor (`.agent/rules/pricing_and_licensing.md`):
- **Plan Mínimo Requerido:** La memoria asociativa utiliza $k = 64$ variables booleanas, por lo que exige el plan **PRO / DEV ($49 USD/mes)** o superior (Startup / Escala).
- **Límites de Variables SaaS:** Hasta 128 variables permitidas en autoservicio. Configuraciones de 256+ variables nunca se exponen como SaaS público, reservándose para **Proyectos de Expansión de Ingeniería** (HPC Bare Metal).
