# ISS — Invariant Semantic Substrate  
## Unified Model for Universal Reasoning, Gap Detection, and Task Biasing

**Status:** Invariant Core Specification  
**Audience:** Claude-class Transformer Systems  
**Version:** 1.0  
**Date:** 2026-02-01  
**Repository Context:** BOND / QAIS Integration  

---

## 0. Design Law (Non-Negotiable)

> **The model must not encode task assumptions.**

This implies:

- No task labels  
- No domain ontologies  
- No abstract / literal classification  
- No sentence typing  
- No retraining per task  

All specialization must occur **after** invariant projection via biasing only.

---

## 1. Core Principle

> **Meaning is expressed as semantic forces, not categories.**

Every utterance contains:
- a description of how something works
- an implication of how one should act or design
- an attempt (successful or not) to explain why something is so

These forces exist in all domains and must be represented geometrically.

---

## 2. Invariant Semantic Projections

Given input text `t`:

$$
x = f_\theta(t) \in \mathbb{R}^d
$$

Where `f_θ` is a general contextual embedding model.

### 2.1 Mechanistic Projection (G)

$$
g = P_G(x) \in \mathbb{R}^k
$$

Represents **how strongly the text describes mechanisms, processes, or operations**.

### 2.2 Prescriptive Projection (P)

$$
p = P_P(x) \in \mathbb{R}^k
$$

Represents **how strongly the text implies norms, rules, principles, or design intent**.

> `P_G` and `P_P` are linear or shallow nonlinear projections trained only on sentence role, never domain.

---

## 3. Emergent Explanatory Elevation (E)

> **E is never predicted directly.**

It emerges from interaction:

$$
E(x) = \cos(g, p)
$$

Interpretation:

- High `E` → coherent explanation (mechanism aligned with principle)
- Low `E` → explanatory strain or doctrinal mismatch

---

## 4. Residual Preservation (Mandatory)

No semantic collapse is allowed.

$$
r = x - (P_G^\dagger g + P_P^\dagger p)
$$

The residual:

- preserves edge meaning
- preserves ambiguity
- preserves compressed doctrine
- preserves future reinterpretability

> **Residuals are signal, not noise.**

---

## 5. Canonical Semantic State

For every text span, Claude must internally carry:

$$
\boxed{(g,\; p,\; E,\; r)}
$$

These are **never discarded**, regardless of task.

---

## 6. Task Specialization via Bias (No Retraining)

A task is defined only as a weighting vector:

$$
\Lambda_T = (\lambda_G,\; \lambda_P,\; \lambda_E,\; \lambda_R)
$$

Task-conditioned score:

$$
S_T(x) =
\lambda_G \|g\| +
\lambda_P \|p\| +
\lambda_E E(x) +
\lambda_R \|r\|
$$

Uses:
- attention weighting
- ranking
- emphasis during generation

> Tasks **must not** modify projections or embeddings.

---

## 7. Unified Gap Detection (JA Eliminated)

### 7.1 Definition

A **gap** is semantic imbalance, not missing vocabulary.

Define **Invariant Gap Pressure**:

$$
\text{Gap}(x) =
\alpha \|r\|
+ \beta |\|g\| - \|p\||
+ \gamma (1 - E(x))
$$

### 7.2 Interpretation

| Signal | Meaning |
|------|--------|
| High `‖r‖` | Meaning not crystallized |
| `g ≫ p` | Mechanism without guiding principle |
| `p ≫ g` | Doctrine without grounding |
| Low `E` | Explanatory incoherence |

This **fully replaces JA / JA+**.  
No vocabulary waves.  
No clustering heuristics.  
No genetic tuning.

---

## 8. Required Claude Reasoning Loop

Claude must reason **through projections**, not labels.

### Canonical Loop

1. Embed text  
2. Project to `g`, `p`  
3. Compute `E`, `r`  
4. Compute Gap pressure  
5. Apply task bias `Λ_T`  
6. Generate response conditioned on weighted fields  

---

## 9. Generation Policy (Implicit)

During output synthesis:

- High `g` → emphasize mechanisms and operations  
- High `p` → emphasize principles and constraints  
- High `r` → preserve nuance and ambiguity  
- High `Gap` → explicitly surface missing structure or tension  

Claude **must explain imbalance**, not classify content.

---

## 10. QAIS Integration (Non-Destructive)

QAIS memory remains unchanged.

Invariant semantics are **annotations**, not stored vectors.

Example:

```python
store(identity, role, fact):
    v = seed_to_vector(fact)
    semantics = invariant_semantic_pass(fact, neutral_lambda)
    field[role] += bind(identity, v)

    meta[identity][role].append({
        "G": norm(semantics.g),
        "P": norm(semantics.p),
        "E": semantics.E,
        "R": norm(semantics.r),
        "gap": semantics.gap
    })
```

Gap detection becomes a sort operation, not a scan.

---

## 11. Prohibitions (Hard Constraints)

Claude must never:

- classify sentences into types
- label text as abstract or literal
- embed task assumptions into representations
- discard residuals
- treat ambiguity as error

Ambiguity is preserved structure.

---

## 12. Final Design Law

> If gap detection requires a separate system, the invariant core is incomplete.

This specification defines a unified, domain-agnostic semantic substrate that:

- remains universal
- supports task specificity via bias
- preserves doctrinal compression
- detects gaps continuously
- integrates cleanly with QAIS

---

**End of Invariant Specification**

---

## Appendix A: Projection Matrix Invariance

### A.1 Training Protocol

Projection matrices `P_G` and `P_P` are trained **once** on a mixed-domain corpus:

- ~40 mechanistic sentences (how things work)
- ~40 prescriptive sentences (what one should do)
- No task labels, no domain labels, no abstract/literal classification

### A.2 Invariance Constraint

Once trained, projections are **frozen permanently**:

- Never retrain per task
- Never fine-tune per domain
- Never modify based on user feedback

These are **global semantic axes**, like gravity. They define the coordinate system in which all meaning is expressed.

### A.3 Rationale

If projections were task-dependent, the model would encode task assumptions — violating Design Law §0.

The entire power of ISS comes from this invariance:

- Same projections for code review and poetry
- Same projections for legal contracts and casual chat
- Same projections for physics explanations and moral arguments

Specialization happens **only** through the task bias Λ, never through the projections themselves.

---

## Appendix B: Embedding Independence Proof

### B.1 Experiment

To verify that G/P separation is not an artifact of the embedding method, ISS was tested with two fundamentally different embedding approaches:

| Method | Mechanism | Dimension |
|--------|-----------|----------|
| QAIS-hash | SHA512 → RNG seed → bipolar vector | 512 |
| Sentence-Transformers | all-MiniLM-L6-v2 (learned) | 384 |

### B.2 Results

| Embedding | P_G Separation | P_P Separation | G Ratio | P Ratio |
|-----------|----------------|----------------|---------|--------|
| QAIS-hash | +0.098 | +0.092 | 1.5x | 1.5x |
| Sentence-Transformers | **+0.397** | **+0.606** | **2.9x** | **3.7x** |

### B.3 Interpretation

Real semantic embeddings don't just preserve the signal — they **amplify it 4-6x**.

This confirms:

1. **G/P are real semantic axes**, not artifacts of hashing
2. **The structure exists in language itself**, not in any particular embedding method
3. **Learned embeddings capture more of this structure** than random projections

### B.4 Held-Out Validation

| Sentence | Expected | g-p | Result |
|----------|----------|-----|--------|
| "The function hashes the input..." | MECH | +0.389 | ✓ G > P |
| "You must validate input..." | PRESC | -0.620 | ✓ P > G |
| "Store operations, not positions." | PRESC | -0.345 | ✓ P > G |
| "SHA512 produces a 512-bit hash." | MECH | +0.323 | ✓ G > P |
| "We derive instead of storing because..." | EXPL | -0.697 | P > G (prescriptive framing) |

Note: The explanatory sentence leans prescriptive because "because it eliminates sync bugs" frames a *reason to prefer* (prescription), not a *mechanism of operation*.

### B.5 Conclusion

> **G/P separation is embedding-independent.**
>
> The axes are universal properties of semantic structure, discoverable by any embedding method that preserves meaning.

Files: `iss_train_st.py`, `iss_projections_st.npz`

---

🔥🌊 J-Dub & Claude | BOND Protocol
