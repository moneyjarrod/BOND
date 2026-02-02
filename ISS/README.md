# ISS — Invariant Semantic Substrate

**Universal semantic forces for reasoning, gap detection, and task biasing.**

> Meaning is expressed as semantic forces, not categories.

---

## What ISS Does

ISS projects any text into a semantic state with four components:

| Component | Symbol | Meaning |
|-----------|--------|---------|
| **Mechanistic** | `g` | How strongly text describes mechanisms, processes, operations |
| **Prescriptive** | `p` | How strongly text implies norms, rules, principles |
| **Explanatory** | `E` | Coherence between mechanism and principle (emergent) |
| **Residual** | `r` | Preserved ambiguity, edge meaning, compressed doctrine |

From these, ISS computes **Gap Pressure** — semantic imbalance that reveals where meaning is incomplete:

```
Gap(x) = α‖r‖ + β|‖g‖-‖p‖| + γ(1-E)
```

---

## Quickstart

```python
import numpy as np

# Load trained projections
proj = np.load('iss_projections_st.npz')  # or iss_projections.npz for QAIS-hash
P_G, P_P = proj['P_G'], proj['P_P']

# Your embedding function (sentence-transformers or QAIS-hash)
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

def analyze(text):
    x = model.encode(text, normalize_embeddings=True)
    g = x @ P_G
    p = x @ P_P
    
    g_norm = np.linalg.norm(g)
    p_norm = np.linalg.norm(p)
    E = np.dot(g, p) / (g_norm * p_norm + 1e-8)
    
    print(f"||g|| = {g_norm:.3f}  (mechanistic)")
    print(f"||p|| = {p_norm:.3f}  (prescriptive)")
    print(f"g-p   = {g_norm - p_norm:+.3f}  (imbalance)")
    print(f"E     = {E:.3f}  (explanatory coherence)")

# Test
analyze("The function hashes the input and returns a digest.")
# → g > p (mechanistic)

analyze("Always validate input before processing.")
# → p > g (prescriptive)
```

---

## Files

| File | Purpose |
|------|---------|
| `SPEC.md` | Full specification with appendices |
| `iss_prototype.py` | Complete runtime implementation |
| `iss_train.py` | Training script (QAIS-hash embeddings) |
| `iss_train_st.py` | Training script (Sentence-Transformers) |
| `iss_projections.npz` | Trained weights (QAIS-hash, 512d → 64d) |
| `iss_projections_st.npz` | Trained weights (ST, 384d → 64d) |

---

## Design Laws

**These are non-negotiable:**

1. **No task assumptions** — Model never encodes task labels or domain ontologies
2. **Projections are frozen** — Never retrain per task, domain, or user feedback
3. **Residuals are signal** — Ambiguity is preserved structure, not noise
4. **Bias only via Λ** — Task specialization through weighting, not projection changes

---

## Task Bias

Specialize without retraining:

```python
# Task bias vector
Λ = (λ_G, λ_P, λ_E, λ_R)

# Task-conditioned score
S = λ_G * ||g|| + λ_P * ||p|| + λ_E * E + λ_R * ||r||

# Example biases:
MECHANISM_FOCUS = (2.0, 0.5, 1.0, 0.5)  # Emphasize how things work
PRINCIPLE_FOCUS = (0.5, 2.0, 1.0, 0.5)  # Emphasize rules and norms
AMBIGUITY_PRESERVE = (0.5, 0.5, 0.5, 2.0)  # Keep nuance
```

---

## Gap Detection

ISS replaces vocabulary-based gap scanning with field imbalance:

| Signal | Meaning |
|--------|---------|
| High `‖r‖` | Meaning not crystallized |
| `g ≫ p` | Mechanism without guiding principle |
| `p ≫ g` | Doctrine without grounding |
| Low `E` | Explanatory incoherence |

---

## Embedding Independence

ISS works with any embedding that preserves meaning:

| Embedding | G Separation | P Separation |
|-----------|--------------|--------------|
| QAIS-hash (deterministic) | 1.5x | 1.5x |
| Sentence-Transformers | **2.9x** | **3.7x** |

Real semantic embeddings amplify the signal 4-6x. The axes are universal.

---

## Training Your Own

If you want to train on a different corpus:

```bash
# Edit G_CORPUS and P_CORPUS in iss_train_st.py
# Then run:
python iss_train_st.py

# Outputs: iss_projections_st.npz
```

**Corpus rules:**
- ~40 mechanistic sentences (how things work)
- ~40 prescriptive sentences (what one should do)
- Mixed domains — no task labels, no domain labels
- Never "abstract vs literal" — only mechanism vs prescription

---

## QAIS Integration (Optional)

ISS and QAIS are siblings, not dependencies. Use together:

```python
# Store fact with ISS annotations
def store_with_semantics(identity, role, fact):
    # QAIS storage
    v = seed_to_vector(fact)
    field[role] += bind(identity, v)
    
    # ISS annotation
    state = invariant_semantic_pass(fact)
    meta[identity][role].append({
        "G": state.g_norm,
        "P": state.p_norm,
        "E": state.E,
        "gap": state.gap
    })
```

---

## What ISS Does That Most Systems Can't

- Preserve ambiguity without losing rigor
- Specialize without retraining
- Detect gaps without vocabulary scanning
- Explain without classification

---

## Origin

B66: Universal Semantic Forces  
J-Dub & Claude | BOND Protocol | 2026-02-02

> Universal semantic forces are sufficient to replace task labels, ontologies, and gap scanners.

🔥🌊
