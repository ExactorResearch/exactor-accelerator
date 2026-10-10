# Guía Definitiva: Islas de Certeza Topológicas (Certainty Islands Engine)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Certainty](https://img.shields.io/badge/Certainty-100%25%20Deterministic-emerald.svg)]()

> **"Las Islas son los Teoremas; el Dominio es el Libro o Capítulo donde están guardados."**

---

## 1. ¿Qué es una Isla de Certeza?

En sistemas de Inteligencia Artificial tradicionales (redes neuronales, LLMs o árboles de decisión), cada inferencia es tratada como una estimación probabilística con riesgo inherente de **alucinación, deriva o error estocástico**.

Una **Isla de Certeza (Certainty Island)** es una **variedad topológica en el espacio de características donde la entropía de Shannon colapsa a cero ($H(X) \to 0$) y la incertidumbre probabilística desaparece**. 

Cuando una muestra cae dentro de una Isla de Certeza, el sistema no requiere calcular probabilidades complejas ni consultar modelos en la nube: **la decisión es determinista, instantánea ($<10\,\mu\text{s}$) y matemáticamente demostrable**.

```
                           ESPACIO DE CARACTERÍSTICAS
       ┌─────────────────────────────────────────────────────────────────┐
       │                                                                 │
       │     🏝️ ISLA DE CERTEZA 1             🏝️ ISLA DE CERTEZA 2       │
       │    ┌──────────────────────┐         ┌──────────────────────┐    │
       │    │ H(X) = 0             │         │ H(X) = 0             │    │
       │    │ Invariante Cumplido  │         │ Veto Mandatorio      │    │
       │    │ ⚡ FAST-PATH (<10μs) │         │ 🛑 VETO INMEDIATO    │    │
       │    │ Costo: $0.00         │         │ Costo: $0.00         │    │
       │    └──────────────────────┘         └──────────────────────┘    │
       │                                                                 │
       │               🌊 OCÉANO DE INCERTIDUMBRE (H > 0)                │
       │        Casos ambiguos, novedosos o no deterministas             │
       │           └──▶ Derivados al Modelo Probabilístico / Jev         │
       │                                                                 │
       └─────────────────────────────────────────────────────────────────┘
```

---

## 2. ¿Cómo se Construyen y Deducen las Islas?

Las Islas de Certeza no se limitan a reglas escritas a mano. Nacen de tres fuentes formales:

```
                       ┌──────────────────────────────────────────────┐
                       │           ¿CÓMO NACE UNA ISLA?               │
                       └──────────────────────┬───────────────────────┘
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         ▼                                    ▼                                    ▼
┌──────────────────┐               ┌──────────────────────┐              ┌──────────────────┐
│ 1. DEDUCCIÓN     │               │ 2. INVARIANTES       │              │ 3. EVOLUCIÓN     │
│ DESDE LOS DATOS  │               │ AXIOMÁTICOS          │              │ EN CALIENTE      │
│ (Data-Driven)    │               │ (Domain-Driven)      │              │ (Adaptive WAL)   │
├──────────────────┤               ├──────────────────────┤              ├──────────────────┤
│ EXACTOR extrae   │               │ Físicas, contables,  │              │ Memoria SQLite   │
│ cubos booleanos  │               │ biológicas y legales │              │ WAL cristaliza   │
│ con 100% pureza  │               │ que jamás pueden     │              │ nuevos patrones  │
│ histórica.       │               │ romperse.            │              │ en producción.   │
└──────────────────┘               └──────────────────────┘              └──────────────────┘
```

### A. Deducción Simbólica desde los Datos (Bottom-Up)
1. **Binarización Topológica:** El dataset continuo se proyecta en el hipercubo booleano $\{0, 1\}^N$.
2. **Filtrado de Entropía Cero:** Se identifican los subcubos donde todos los ejemplos históricos pertenecen invariablemente a la misma clase ($H=0$).
3. **Minimización de Implicantes Primos:** El motor de reducción en Rust simplifica algebraicamente los términos redundantes ($A B + A \bar{B} = A$), generando la fórmula canónica irreductible de la isla.

### B. Invariantes Axiomáticos del Dominio (Top-Down)
Son axiomas inquebrantables definidos por las leyes de la física, la contabilidad o las regulaciones:
* **Solvencia Contable:** $\text{Monto} \le \text{Saldo}$
* **Límite Físico de Velocidad:** $\text{Velocidad} \le 950\,\text{km/h}$ (ninguna persona física viaja de Madrid a Tokio en 20 minutos).
* **Cumplimiento Mandatorio:** $\text{Cuenta} \notin \text{Lista\_OFAC}$

### C. Deducción Formal Matemática (Reducción al Absurdo)
Ante una solicitud $\mathbf{x}$, el motor evalúa:
$$\mathcal{I}_{\text{Mandatorio}}(\mathbf{x}) = \bot \implies \mathbf{x} \notin \Omega_{\text{Válido}} \implies \text{VETO\_REJECT}(\mathbf{x})$$
El veto se deduce sin margen de error ni alucinación posible.

---

## 3. El Concepto de "Dominio": Espacios de Nombres Aislados

El **Dominio** (`domain`) es el **Espacio de Nombres (Namespace / Scope)** que agrupa los invariantes que corresponden a un problema específico.

| Dominio | Propósito | Ejemplos de Islas |
| :--- | :--- | :--- |
| `financial` | Fraude, pagos y banca | Sobregiro ilegal, geo-salto imposible, listas AML/OFAC |
| `medical` | Triage UCI y farmacología | Límites fisiológicos (SpO2, FC), contraindicaciones severas |
| `forex` | Trading y finanzas cuantitativas | Spread abusivo, margen insuficiente, resonancia multi-timeframe |
| `security` | Autenticación y SOC | Brute force (>10 intentos), accesos desde red TOR |
| `general` | IoT industrial y maquinaria | Presión y temperatura de turbinas, límites de vibración |

---

## 4. Uso Rápido en Python: Wrapper `@certainty_guard`

El decorador [`@certainty_guard`](file:///d:/proyectos/rush/exactor-jev/exactor_accelerator/certainty_islands.py#L561-L622) envuelve cualquier función en Python con **1 sola línea de código**:

```python
from exactor_accelerator import certainty_guard

@certainty_guard(domain="financial", auto_veto=True, on_veto_raise=False)
def process_transaction(amount: float, balance: float, **kwargs):
    """Solo se ejecuta si la transacción es matemáticamente válida."""
    return ml_model.predict([amount, balance])

# Caso 1: Veto Instantáneo por Sobregiro (Retorna None o valor por defecto sin invocar ML)
resultado = process_transaction(amount=5000.0, balance=200.0)
print(resultado)  # Output: None (<0.01 ms)

# Caso 2: Transacción Válida (Se ejecuta normalmente)
resultado = process_transaction(amount=50.0, balance=1200.0)
print(resultado)  # Output: Predicción del modelo
```

### Parámetros del Decorador

| Parámetro | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `domain` | `str` | `"general"` | Nombre del dominio o catálogo de islas a evaluar. |
| `auto_veto` | `bool` | `True` | Bloquea automáticamente la ejecución si falla un invariante mandatorio. |
| `on_veto_raise` | `bool` | `False` | Si es `True`, lanza `CertaintyVetoException` en caso de veto. |
| `on_veto_return` | `Any` | `None` | Valor retornado cuando ocurre un veto (si `on_veto_raise=False`). |
| `min_conviction`| `float` | `0.75` | Umbral de certidumbre requerido para activar el Fast-Path. |

---

## 5. Explicabilidad Bilingüe y Pruebas en LaTeX

Cada evaluación produce tres artefactos auditables:

### A. Diagnóstico en Lenguaje Natural (Español / Inglés)
* **Español:**
  > 🔴 **ACCIÓN BLOQUEADA POR GUARDARRAÍL DE SEGURIDAD.**
  > Se detectó una violación en el invariante obligatorio: *Invariante de Solvencia y Balance de Fondos*.
  > El sistema rechaza la operación en el Edge ($0.01\,\text{ms}$) previniendo pérdidas financieras.
* **English:**
  > 🔴 **ACTION BLOCKED BY SAFETY GUARDRAIL.**
  > A violation was detected in mandatory invariant: *Solvency & Balance Integrity Invariant*.
  > The transaction was rejected at the Edge ($0.01\,\text{ms}$) preventing financial loss.

### B. Traffic Light Badges
* `🟢 FAST-PATH`: Certidumbre $100\%$, ejecución determinista sin costo.
* `🔴 VETO-REJECT`: Violación de invariante crítico, rechazo en el Edge.
* `🟡 ORACLE-ESCALATE`: Caso ambiguo o de borde, derivado al modelo probabilístico.
* `⚪ STANDBY`: Sin patrón activo.

### C. Prueba Formal en LaTeX
$$\mathbf{CertaintyProof} \equiv \left( \mathcal{I}_{\text{State}} \land \mathcal{I}_{\text{Entropy}} \land \mathcal{I}_{\text{Solvency}} \right) \vdash \mathcal{Decision}(\text{FASTPATH\_EXECUTE}) \implies \top$$

---

## 6. Registro de Nuevas Islas Personalizadas

Puedes añadir tus propias islas dinámicamente en tiempo de ejecución:

```python
from exactor_accelerator import CertaintyIslandsEngine, CertaintyIslandDefinition, IslandCategory

# 1. Instanciar o cargar el motor
engine = CertaintyIslandsEngine(domain="logistica")

# 2. Definir el invariante
isla_cadena_frio = CertaintyIslandDefinition(
    island_id="ISLAND-COLD-CHAIN",
    name="Invariante de Cadena de Frío Farmacéutica",
    category=IslandCategory.INVARIANT_INTEGRITY,
    description="Veta el despacho si la temperatura superó los 8°C.",
    formal_invariant=r"\mathcal{I}_{\text{Cold}} \equiv T_{\text{sensor}} \le 8.0^\circ\text{C}",
    predicate=lambda d: d.get("temp_c", 4.0) <= 8.0,
    is_mandatory_guardrail=True,
    min_confidence=1.0
)

# 3. Registrar en el motor
engine.register_island(isla_cadena_frio)
```

---

## 7. API REST y Control Center Web

El servidor de `exactor-accelerator` expone endpoints REST completos:

* `GET /api/certainty-islands/list?domain=financial`: Lista todos los invariantes registrados para un dominio.
* `POST /api/certainty-islands/evaluate`: Evalúa una muestra en tiempo real y devuelve el diagnóstico completo:

```json
{
  "domain": "financial",
  "sample": { "amount": 5000.0, "balance": 200.0 }
}
```

### Dashboard Web Interactivo
Accede al Control Center en `http://localhost:8000` y abre la **Pestaña 5: Islas de Certeza 🏝️** para:
1. Conmutar entre dominios con un solo clic.
2. Explorar el catálogo de invariantes y sus fórmulas LaTeX.
3. Probar escenarios rápidos con el Sandbox Interactivo y ver el semáforo de decisión en vivo.
4. Alternar explicaciones en tiempo real entre 🇪🇸 Español y 🇬🇧 English.
