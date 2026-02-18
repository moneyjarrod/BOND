# BOND_BONDFIRES — Closed Chapters

Each Bondfire is a solved problem. The insight is permanent.
New work must align with existing Bondfires.

---

| # | Name | Insight | Fixed | Session |
|---|------|---------|-------|---------|
| 1 | ROSETTA | Dictionary word-counting beats hash embeddings for force classification. LIWC psycholinguistic framework → deterministic word-to-force mapping. 1 force class became 4, 88% retrieval became 100%. | ISS discrimination gap — all blocks classified 'r', zero discrimination | S85-86 |

---

## Bondfire Details

### BF1 — ROSETTA (S85-86)

**Problem:** ISS hash-based embeddings produced identical force profiles
for all text blocks. Every block classified as 'r' (residual). Layer 1
of the compound anchor contributed zero discrimination. Continuous ISS
vectors tested — cosine similarity 0.93-0.99 between siblings. The r
dimension drowns G/P/E in both categorical and continuous space.

**Insight:** Pennebaker's LIWC framework (1993-2022) demonstrated that
dictionary-based word counting reliably reveals psychological dimensions
of text. Adapted to ISS: map words to G (mechanistic), P (prescriptive),
E (coherence), r (residual) force dimensions. Deterministic. No neural
network. Same text always produces same profile.

**Solution:** ROSETTA doctrine entity. Four word lists (~100 words each)
derived from LIWC category taxonomy. force_profile() counts hits per
dimension, returns 4D ratio vector + dominant class. Light stemmer
normalizes word forms. Stronger family disambiguation for broad queries.

**Result:** 4 distinct force classes where ISS produced 1. Compound
anchor retrieval: 23/26 (88%) → 26/26 (100%).

**Closed:** The discrimination gap is solved. ROSETTA is doctrine —
static truth, immutable word lists. ISS hash embeddings are bypassed
for force classification. The compound anchor's Layer 1 is alive.
