# 🧪 Open Experiment: Exactor Accelerator (JEV + Boolean Logic in Rust)

> **Release document for developer communities (Reddit, Hacker News, Dev.to, Discord, and technical networks).**  
> You can copy and paste the content below directly to share the project and invite community collaboration.

---

## 📢 Launch & Collaboration Announcement

**Title:**  
**Open Experiment: Can JEV decisions be accelerated to $< 1\text{ ms}$ using boolean logic in Rust? Sharing code for testing and feedback**

### Post Body

Hi everyone,

I wanted to share an experiment I've been working on over the past few weeks that may be useful for engineers working on AI-driven decision-making in production.

### 1. The Context: The "Human Reflex" Metaphor (System 1 vs System 2)

When you learn to drive, you initially think through every single motion (**System 2**: conscious, analytical, slow). After a few months, your nervous system internalizes the patterns into automatic muscle memory (**System 1**: sub-second reflex).

In modern software architectures, **JEV (TypeSafe AI)** represents that brilliant analytical brain: its reasoning is formidable, delivering zero-data clarity and semantic comprehension right out of the box. However, deploying cloud AI models for every single high-frequency request (payment gateways, real-time security alerts, sub-second routing) forces systems to pay a heavy tax: **500–1,200 ms network transit latency** and compounding token costs on routine queries.

### 2. The Hypothesis: Transforming Cognitive Reasoning into Local Muscle Memory

Instead of forcing a compromise, what if we pair Jev's analytical brain with an automatic edge reflex?

In this architecture, **Jev acts as the strategic intelligence**, calibrating ambiguous or shifting cases in the cloud. **Exactor acts as the local muscle memory compiler in Rust**: it records Jev's decisions in a lightweight SQLite WAL ledger, distills the underlying logical invariants, and executes subsequent routine queries locally at hardware speed (**~0.05 ms**) with **$0.00 marginal cost**.

The result of this experiment is **Exactor Accelerator**, and early benchmarks have shown promising results:

- ⚡ **Local CPU Inference:** Evaluation of routine events executes in **~0.05 to 0.5 milliseconds** with zero network calls and zero real-time token consumption.
- 🎯 **Prediction + Instant Rule-Grounded Explanation:** Every forecast is coupled with the exact Boolean rule that triggered it (`clf.explain()`), proving why the decision occurred based strictly on the active premise (zero black-box approximations, zero hallucination).
- 🧬 **Zero-Regex:** The engine auto-discovers language patterns during training, eliminating the need to maintain fragile manual regular expressions.
- 🔀 **Multi-Class & Multi-Label Support:** Extended via parallel hypercubes (*One-vs-Rest*) to route across business categories simultaneously (e.g., *Fraud, Disputes, Support, Churn*).
- 🔍 **Formal Causal Auditability (GDPR/HIPAA Ready):** Generates verifiable audit certificates and natural language justifications grounded strictly in the mathematical conditions that activated.
- 🐍 **Scikit-Learn Interface:** Standard scikit-learn workflow (`fit`, `predict`, `predict_proba`).
- 📦 **Compact Model Artifacts:** Saved as `.ea` / `.ej` files (~1.9 KB) ready for standalone deployment with FastAPI and Docker.

---

### 🎁 Free EXACTOR Community Token (50,000 Queries until Jan 1, 2027)

To allow anyone to test the **EXACTOR Core API** without needing to register or add payment methods, a community token with **50,000 queries** is available:

```bash
# Linux / macOS:
export EXACTOR_CORE_TOKEN="YOUR_EXACTOR_TOKEN_HERE"

# Windows (PowerShell):
$env:EXACTOR_CORE_TOKEN="YOUR_EXACTOR_TOKEN_HERE"
```

*(You can also pass it directly in code via `exactor_accelerator.configure(exactor_core_token="...")` or `use_cloud_exactor=True`)*.

---

### 💻 Quick Start in 2 Minutes

Install the package directly via `pip` or clone the repository:

```bash
pip install exactor-accelerator
```

Or clone the repository and run the test suite:

```bash
git clone https://github.com/ExactorResearch/exactor-accelerator.git
cd exactor-accelerator
python test_multiclass_multilabel.py
```

#### Minimal Usage Example:

```python
import pandas as pd
from exactor_accelerator import ExactorAcceleratorClassifier

# Sample dataset with unstructured text and numerical variables
df = pd.DataFrame([
    {"amount": 4500, "tenure": 1, "text": "Unrecognized urgent wire transfer", "category": "FRAUD"},
    {"amount": 120,  "tenure": 18, "text": "Duplicate charge on credit card", "category": "DISPUTE"},
    {"amount": 0,    "tenure": 6,  "text": "Mobile application crashes on startup", "category": "SUPPORT"},
    {"amount": 45,   "tenure": 36, "text": "I want to cancel my subscription", "category": "CHURN"},
] * 5)

# 1. Train the multi-class classifier
clf = ExactorAcceleratorClassifier(max_variables=16, fast_path=True)
clf.fit(df[["amount", "tenure", "text"]], df["category"])

# 2. Sub-millisecond local inference (< 1 ms)
new_event = pd.DataFrame([{"amount": 5000, "tenure": 1, "text": "Account hacked emergency help"}])
prediction = clf.predict(new_event)[0]
probas = clf.predict_proba(new_event)[0]

print(f"Predicted Category: {prediction}")
print(f"Class Probabilities: {probas}")

# 3. Formal explainability for clients / auditors
# (Generates the exact justification based on activated boolean rules)
explanation = clf.explain(new_event.iloc[0].to_dict())
print("\n--- Formal Explanation Certificate ---")
print(explanation)
```

---

### 🤝 Feedback and Collaboration

As an open community project, we would love your critical feedback and contributions:

1. **Testing on real or noisy datasets:** If you have challenging test cases (typos, industry jargon, class imbalance), let us know how the system behaves.
2. **Architecture feedback:** Ideas for optimizing logical representations, probability calibration, or interfaces.
3. **Collaborations & PRs:** Contributions in Rust algorithm optimization, WebAssembly (WASM) export, or documentation improvements are welcome!

🔗 **Repository:** `https://github.com/ExactorResearch/exactor-accelerator`  
*(If you find this approach interesting, a GitHub star ⭐ or opening an issue with ideas helps a lot)*

Looking forward to your thoughts and discussion!
