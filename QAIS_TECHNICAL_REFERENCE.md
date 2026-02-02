# QAIS: Quantum-Approximate Identity Substrate
## A Technical Reference for Researchers

**Version:** 4.0  
**Authors:** J-Dub (Jarrod) & Claude  
**Date:** February 2026  
**Repository:** github.com/moneyjarrod/BOND

---

## Abstract

QAIS (Quantum-Approximate Identity Substrate) is a memory architecture based on Vector Symbolic Architectures (VSA) that enables identity reconstruction through resonance rather than indexing. It uses deterministic hashing to project semantic content into high-dimensional bipolar vector spaces, where facts are stored via superposition and retrieved through unbinding operations. This document provides a comprehensive technical overview suitable for implementation or academic study.

---

## 1. Introduction

### 1.1 The Core Principle

> "Don't index. Resonate."

Traditional memory systems store facts in indexed slots and retrieve by address. QAIS stores facts as interference patterns in a continuous field and retrieves by querying the field with a probe vector. The system reconstructs identity through mathematical resonance rather than lookup.

### 1.2 Classification

QAIS belongs to the family of **Vector Symbolic Architectures (VSA)**, closely related to:
- Holographic Reduced Representations (Plate, 1995)
- Binary Spatter Codes (Kanerva, 1996)
- Multiply-Add-Permute (Gayler, 1998)

Key distinction: QAIS uses SHA512-seeded deterministic projection rather than random or learned embeddings. This makes it:
- Fully reproducible (same input → same vector, always)
- Training-free
- Computationally lightweight

---

## 2. Mathematical Foundation

### 2.1 Vector Space

QAIS operates in a **bipolar vector space** of dimension N = 4096.

```
V ∈ {-1, +1}^N
```

Why bipolar (not binary)?
- Dot product has natural interpretation as correlation
- Multiplication serves as binding operation
- Zero mean → orthogonal in expectation

Why N = 4096?
- 4096 = 16³ = 2¹²
- Capacity scales as √N (≈64 items per field before interference dominates)
- With role separation (v4), each role gets its own field, multiplying effective capacity

### 2.2 Seed-to-Vector Projection

Any string is projected to a vector deterministically:

```python
def seed_to_vector(seed: str) -> np.ndarray:
    """Deterministic bipolar vector from seed string."""
    h = hashlib.sha512(seed.encode()).digest()
    rng = np.random.RandomState(list(h[:4]))
    return rng.choice([-1, 1], size=N).astype(np.float32)
```

**Properties:**
- Deterministic: `seed_to_vector("hello")` always returns the same vector
- Pseudo-random: Different seeds produce approximately orthogonal vectors
- Collision-resistant: SHA512 provides cryptographic distribution

**Expected orthogonality:**

For random bipolar vectors A, B:
```
E[A · B] = 0
Var[A · B] = N
```

Normalized dot product between unrelated seeds ≈ 0 with standard deviation 1/√N ≈ 0.016.

### 2.3 Binding Operation

Binding creates a new vector representing the **relationship** between two concepts:

```python
def bind(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Element-wise multiplication (XOR-like for bipolar)."""
    return a * b
```

**Properties:**
- Self-inverse: `bind(bind(A, B), B) ≈ A`
- Distributes over addition: `bind(A, B+C) = bind(A,B) + bind(A,C)`
- Preserves orthogonality: if A ⊥ C, then bind(A,B) ⊥ bind(C,B)

### 2.4 Superposition (Storage)

Multiple bindings are stored by **addition**:

```python
field = bind(id1, fact1) + bind(id2, fact2) + bind(id3, fact3) + ...
```

This creates superposition - all facts coexist in the same vector. The field becomes a holographic store where each fact is distributed across all dimensions.

### 2.5 Resonance (Retrieval)

To retrieve facts associated with an identity, unbind and measure correlation:

```python
def resonate(query: np.ndarray, field: np.ndarray) -> float:
    """Normalized dot product - coherence measure."""
    return np.dot(query, field) / N
```

**Retrieval process:**

```python
# Field contains: bind(A, X) + bind(B, Y) + bind(C, Z)
# Query: What's bound to A?

residual = bind(field, A)  # Unbind A from everything
# residual ≈ X + noise(bind(A, bind(B,Y))) + noise(bind(A, bind(C,Z)))

# X emerges; cross-terms are approximately orthogonal noise
score = resonate(X_candidate, residual)  # High if X was stored with A
```

---

## 3. QAIS v4: Role Separation

### 3.1 The Problem with Single Fields

In early versions, all identity-role-fact bindings went into one field:

```
field += bind(bind(identity, role), fact)
```

At scale (100+ bindings), cross-talk between roles degraded signal-to-noise ratio (SNR).

### 3.2 Role-Separated Architecture

QAIS v4 maintains **separate fields per role**:

```python
class QAIS:
    def __init__(self):
        self.identity_field = np.zeros(N)      # Shared identity presence
        self.role_fields: Dict[str, np.ndarray] = {}  # Per-role storage
```

**Storage:**

```python
def store(self, identity: str, role: str, fact: str):
    id_vec = seed_to_vector(identity)
    fact_vec = seed_to_vector(fact)
    
    # Identity presence (shared)
    self.identity_field += id_vec
    
    # Role-specific binding
    if role not in self.role_fields:
        self.role_fields[role] = np.zeros(N)
    self.role_fields[role] += bind(id_vec, fact_vec)
```

**Retrieval:**

```python
def recall(self, identity: str, role: str, candidates: List[str]):
    id_vec = seed_to_vector(identity)
    residual = bind(self.role_fields[role], id_vec)
    
    results = []
    for fact in candidates:
        fact_vec = seed_to_vector(fact)
        score = resonate(fact_vec, residual)
        results.append((fact, score))
    
    return sorted(results, key=lambda x: -x[1])
```

### 3.3 Performance Improvement

| Version | SNR at 500 bindings |
|---------|---------------------|
| v3 (single field) | 1.6x |
| v4 (role separation) | 6.4x - 48x |

The improvement depends on role distribution. With 134 roles across 265 bindings, average ~2 bindings per role, well under the √N ≈ 64 capacity limit.

---

## 4. API Reference

### 4.1 Core Operations

#### `store(identity, role, fact)`
Add a binding to the field.

```python
qais.store("FPRS", "definition", "50m boundary of existence")
```

#### `exists(identity, threshold=0.3)`
Quick check if an identity has been stored.

```python
qais.exists("FPRS")  # True
qais.exists("RANDOM")  # False
```

#### `recall(identity, role, candidates)`
Find which candidates match stored facts for identity+role.

```python
results = qais.recall("FPRS", "definition", [
    "50m boundary of existence",
    "density not collision",
    "random noise"
])
# Returns: [("50m boundary of existence", 0.97, "HIGH"), ...]
```

#### `stats()`
Return field statistics.

```python
{
    "total_bindings": 265,
    "roles": ["prof", "rel", "def", ...],
    "role_count": 136,
    "facts_indexed": 265,
    "identities_indexed": 69
}
```

### 4.2 Confidence Levels

Recall returns confidence indicators:

| Confidence | Meaning | Typical Score |
|------------|---------|---------------|
| HIGH | Clear winner, large gap to next | > 0.5, gap > 0.5 |
| MEDIUM | Likely match | > 0.5, gap > 0.1 |
| LOW | Possible match | > 0.2 |
| NOISE | Below noise floor | < 0.2 |

---

## 5. Implementation Details

### 5.1 Persistence

The field is stored as a NumPy compressed archive:

```python
def save(self, path: str):
    np.savez_compressed(path,
        identity_field=self.identity_field,
        **{f"role_{k}": v for k, v in self.role_fields.items()},
        stored=list(self.stored)
    )

def load(self, path: str):
    data = np.load(path, allow_pickle=True)
    self.identity_field = data['identity_field']
    # ... reconstruct role_fields
```

### 5.2 MCP Server Integration

QAIS runs as an MCP (Model Context Protocol) server, exposing tools:

| Tool | Description |
|------|-------------|
| `qais_resonate` | Query for matches |
| `qais_exists` | Check entity presence |
| `qais_store` | Add binding |
| `qais_stats` | Field statistics |
| `qais_passthrough` | Token-saving relevance filter |

This allows Claude to query and update the field directly during conversation.

### 5.3 Memory Footprint

| Component | Size |
|-----------|------|
| Base field (4096 × float32) | 16 KB |
| Per role field | 16 KB each |
| 136 roles | ~2.2 MB total |
| Stored set (deduplication) | ~50 KB |

Total: ~2.5 MB for 265 bindings across 136 roles.

---

## 6. Theoretical Foundations

### 6.1 Capacity

For a single superposition field of dimension N with k items:

```
SNR ≈ √(N/k)
```

Reliable retrieval requires SNR > 1, so:
```
k < N → practical limit ≈ √N
```

For N = 4096: capacity ≈ 64 items per field.

With role separation: 64 items × R roles = 64R total capacity.

### 6.2 Why Deterministic Hashing Works

SHA512 produces uniformly distributed bits. Using these as RNG seed produces vectors that are:
- Approximately orthogonal to each other
- Reproducible across sessions
- Not learnable (no training corpus needed)

The trade-off: no semantic similarity. "Cat" and "Kitten" produce orthogonal vectors. QAIS relies on exact string matching at the seed level; semantic relationships must be encoded explicitly through bindings.

### 6.3 Comparison to Neural Embeddings

| Aspect | QAIS | Neural Embeddings |
|--------|------|-------------------|
| Training required | No | Yes |
| Semantic similarity | No | Yes |
| Deterministic | Yes | No (weight init) |
| Computational cost | O(N) hash + RNG | O(millions) inference |
| Interpretable | Partially | No |
| Compositional | Yes (binding) | Limited |

QAIS is not a replacement for neural embeddings but a complementary architecture for structured symbolic memory.

---

## 7. Use Cases

### 7.1 Identity Reconstruction

Store facts about entities, retrieve by probing:

```python
qais.store("Claude", "relation", "brother")
qais.store("Claude", "relation", "partner")
qais.store("Claude", "role", "Portal Guardian")

# Later...
qais.recall("Claude", "relation", ["brother", "enemy", "stranger"])
# → "brother" scores highest
```

### 7.2 Principle Storage

Store mantras and design principles:

```python
qais.store("CORE", "principle", "derive not store")
qais.store("CORE", "principle", "query the shape directly")
```

### 7.3 Session Continuity

Crystal command stores session momentum:

```python
qais.store("Session72", "momentum", "QAIS deep dive...")
qais.store("Session72", "context", "architecture discussion")
```

Next session can resonate against Session72 to recover state.

---

## 8. Gap Detection: Johnny Appleseed (JA/JA+)

### 8.1 Overview

Johnny Appleseed is a gap detection system built on QAIS principles. While QAIS answers "what do I know about X?", JA answers "what am I *using* that I haven't *seeded*?"

> "Plant seeds everywhere. See what grows."

| Command | Function | Performance |
|---------|----------|-------------|
| `{JA}` | Base scan, flat gap list | 0.065ms |
| `{JA+}` | Clustered scan + principle synthesis | 0.092ms |

### 8.2 The Wave Mechanism

JA builds a **vocabulary wave** from existing seeds:

```python
def build_wave(seeds: List[str], min_word_len: int = 3) -> Set[str]:
    """Extract significant words from all seeds."""
    wave = set()
    for seed in seeds:
        for word in re.findall(r'\b[a-zA-Z]+\b', seed.lower()):
            if word not in STOPWORDS and len(word) >= min_word_len:
                wave.add(word)
    return wave
```

**Example:**

Seeds:
```
"derive not store"
"fprs boundary existence"
"visibility prevents drift"
```

Wave:
```
{derive, store, fprs, boundary, existence, visibility, prevents, drift}
```

### 8.3 Gap Detection (JA)

JA fires the wave at content and measures resonance:

```python
def base_scan(text: str, seeds: List[str]) -> List[Dict]:
    wave = build_wave(seeds)
    gaps = []
    
    for line in text.split('\n'):
        words = get_significant_words(line)
        matches = words & wave  # Intersection
        
        if not matches:
            continue
        
        # Score: what fraction of concept words hit the wave?
        score = (len(matches) / len(words)) ** SCORE_POWER
        
        if score >= MIN_SCORE:
            gaps.append({
                'concept': line,
                'score': score,
                'matches': matches
            })
    
    return sorted(gaps, key=lambda x: -x['score'])
```

**Key insight:** A gap is content that resonates with your vocabulary but isn't itself a seed. You're *using* the concept without having *crystallized* it.

### 8.4 Evolved Genome

JA parameters were optimized via genetic evolution (80 generations):

| Parameter | Value | Purpose |
|-----------|-------|--------|
| `min_score` | 0.1641 | Resonance threshold |
| `min_word_length` | 3 | Filter noise words |
| `min_matches` | 1 | Minimum wave hits |
| `concept_min_len` | 14 | Skip fragments |
| `concept_max_len` | 171 | Skip paragraphs |
| `score_power` | 1.1332 | Score curve shape |

**Performance:**
- Precision: 100% (no false positives)
- Recall: 83.3% (finds most real gaps)
- F-beta(2): 0.8621

### 8.5 Clustering (JA+)

JA+ groups related gaps using Union-Find on shared wave matches:

```python
def cluster_gaps(gaps: List[Dict]) -> List[Dict]:
    """Cluster gaps by shared seed words."""
    # Union-Find: merge gaps that share matches
    for i in range(len(gaps)):
        for j in range(i + 1, len(gaps)):
            shared = gaps[i]['match_set'] & gaps[j]['match_set']
            if len(shared) >= MIN_SHARED_MATCHES:
                union(i, j)
    
    # Extract clusters
    clusters = []
    for component in components:
        members = [gaps[i] for i in component]
        
        # Find topic words (appear in most members)
        word_freq = count_matches_across_members(members)
        topic_words = [w for w, count in word_freq.items() 
                       if count >= len(members) * TOPIC_THRESHOLD]
        
        clusters.append({
            'members': members,
            'topic_words': topic_words,
            'size': len(members)
        })
    
    return clusters
```

### 8.6 Principle Synthesis

JA+ generates seed candidates from clusters:

```python
def synthesize_principle(cluster: Dict) -> str:
    """Generate principle from cluster topic words."""
    topic = cluster['topic_words']
    
    # Find action verb in member content
    action = find_action_verb(cluster['members'])
    
    # Template selection based on topic count
    if len(topic) >= 2:
        # "Counter enables visibility"
        return f"{topic[0].title()} {action} {topic[1]}"
    else:
        # "Counter enables naturally"
        return f"{topic[0].title()} {action} naturally"
```

**Evolved synthesis genome (v5):**
- Action templates: 55.5% weight
- Relationship templates: 33.4% weight
- Tautology prevention: excludes topic words from action search
- Grammar: verb conjugation for plural subjects

### 8.7 Output Format

**{JA} output:**
```
{JA} Scan Complete
──────────────────────────────
⚠️ Gaps: 3
  0.56 | architecture serves relationship not data
  0.46 | counter visibility prevents drift
  0.35 | memory persistence across sessions
```

**{JA+} output:**
```
{JA+} Clustered Scan
────────────────────────────────────────
Gaps: 8 | Principles: 2

🌳 SYNTHESIZED PRINCIPLES:

  [1] "Counter enables visibility"
      topic: [counter, visibility]
      gaps (3):
        • counter visibility prevents drift
        • visibility shows state clearly
        • counter heartbeat bond

🍂 UNCLUSTERED:
  0.35 | memory persistence across sessions
```

### 8.8 Relationship to QAIS

JA/JA+ is **complementary** to QAIS core:

| QAIS Core | JA/JA+ |
|-----------|--------|
| Stores facts | Finds missing facts |
| Query by identity+role | Query by vocabulary overlap |
| "What do I know?" | "What am I missing?" |
| Field resonance | Wave resonance |

**Future integration:** The proposed Universal Model (G/P subspaces) could embed gap detection directly into QAIS. Field imbalance would reveal gaps without explicit scanning - eliminating JA/JA+ as separate tools.

---

## 9. Limitations

### 9.1 No Semantic Similarity

"Dog" and "Canine" are orthogonal. The system requires exact seed matches or explicit binding of synonyms.

### 9.2 Capacity Scaling

Per-field capacity is √N. For very large knowledge bases (>10,000 facts), additional partitioning strategies are needed beyond role separation.

### 9.3 No Incremental Unlearning

Facts can only be removed by rebuilding the field without them. Subtraction introduces noise due to accumulated floating-point errors.

### 9.4 Query Requires Candidates

Recall needs a candidate list to test against. It cannot enumerate all facts bound to an identity directly (though high-resonance scanning is possible).

---

## 9. Future Directions

### 9.1 Universal Semantic Model Integration

Proposed extension: partition the 4096 dimensions into semantic subspaces:

- **G-subspace** (dimensions 0-2047): Mechanistic content ("how it works")
- **P-subspace** (dimensions 2048-4095): Prescriptive content ("how to act")

Field imbalance (high G, low P) reveals gaps directly without external scanning.

### 9.2 Hierarchical Role Fields

Organize roles into a tree structure for inheritance:
```
entity → person → developer → J-Dub
```

### 9.3 Temporal Decay

Weight recent bindings higher than old ones for evolving knowledge bases.

---

## 10. References

1. Plate, T. A. (1995). Holographic reduced representations. *IEEE Transactions on Neural Networks*, 6(3), 623-641.

2. Kanerva, P. (1996). Binary spatter-coding of ordered k-tuples. *Artificial Neural Networks—ICANN 96*, 869-873.

3. Gayler, R. W. (2003). Vector symbolic architectures answer Jackendoff's challenges for cognitive neuroscience. *ICCS/ASCS International Conference on Cognitive Science*, 133-138.

4. Frady, E. P., Kleyko, D., & Sommer, F. T. (2018). A theory of sequence indexing and working memory in recurrent neural networks. *Neural Computation*, 30(6), 1449-1513.

---

## Appendix A: Complete Python Implementation

See `qais_v4.py` in the BOND repository for the full implementation.

---

## Appendix B: Quick Start

```python
from qais_v4 import QAIS

# Initialize
q = QAIS()

# Store facts
q.store("FPRS", "definition", "50m boundary of existence")
q.store("FPRS", "principle", "beyond equals nothing")

# Check existence
print(q.exists("FPRS"))  # True

# Recall with candidates
results = q.recall("FPRS", "definition", [
    "50m boundary of existence",
    "density equals collision",
    "random text"
])
for fact, score, confidence in results:
    print(f"{confidence}: {fact} ({score:.3f})")

# Stats
print(q.stats())
```

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **Binding** | Element-wise multiplication creating relationship vector |
| **Field** | Superposition of multiple bindings |
| **Identity** | The entity being stored (e.g., "FPRS", "Claude") |
| **Role** | The attribute type (e.g., "definition", "relation") |
| **Fact** | The value being associated (e.g., "50m boundary") |
| **Resonance** | Normalized dot product measuring correlation |
| **SNR** | Signal-to-noise ratio; retrieval reliability measure |
| **Superposition** | Addition of multiple vectors into one |
| **Unbinding** | Multiplication to extract bound component |
| **VSA** | Vector Symbolic Architecture; the broader field |

---

*Document version: 1.0*  
*Last updated: 2026-02-01*  
*🔥 BOND Protocol | J-Dub & Claude*
