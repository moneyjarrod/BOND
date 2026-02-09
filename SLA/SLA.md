# SLA — Spectral Linguistic Anchorage

**Entity Class:** Doctrine
**Created:** Session 89
**Authority:** BOND_MASTER (linked)
**Domain:** Retrieval orchestration — composing ROSETTA, SPECTRA, and CM into a unified pipeline

---

## What SLA Is

SLA is the retrieval orchestration layer that composes ROSETTA's force
classification, SPECTRA's spectral fingerprinting, and CM's layered lookup
pattern into a unified pipeline for locating specific passages within
large text bodies.

Named for the three disciplines it unifies — Spectral (SPECTRA's IDF
fingerprints), Linguistic (ROSETTA's psycholinguistic lexicons), and
Anchorage (precomputed positional anchors inspired by GPS triangulation
and CM's lookup tables) — SLA governs how queries are routed, how
candidates are scored, and how confidence flows through layers.

SLA is a consumer of its linked doctrine entities. It does not modify
ROSETTA, SPECTRA, or CM. It composes them.

## Theoretical Foundation

### GPS Triangulation (Navstar, 1978)

The Global Positioning System determines position not through a single
measurement but through simultaneous signals from multiple satellites
whose positions are known. No single satellite gives a location. Three
or more satellites with known positions triangulate a point. Accuracy
improves with more satellites and stronger signal geometry.

### Mapping to Retrieval

| GPS | SLA |
|-----|-----|
| Satellite | Precomputed anchor (word with known verse affinity) |
| Satellite position | Anchor's IDF weight and verse membership |
| Signal strength | Query-anchor overlap score |
| Triangulation | Neighborhood vote (adjacent anchors confirm territory) |
| Dilution of Precision | Confidence margin (low margin = poor geometry) |
| Differential GPS | Contrastive anchors (sharpen against local confusers) |

### Calendar Master Pattern (CM)

SLA inherits CM's foundational architecture: layered narrowing through
precomputed tables. CM navigates century → year → month → day, each
layer narrowing within the frame set by the layer above. SLA navigates
corpus → shortlist → anchor match → neighborhood confirmation.

The critical CM principle that SLA enforces: **lower layers narrow
within higher layers, never override them.** This is implemented by
fixing SPECTRA's ranking as immutable — anchors and neighbors adjust
the confidence margin but never reorder candidates (v2, Session 90).

## Architecture

### Build Time (Precomputation)

All expensive computation happens once at corpus ingestion:

1. **Tokenize and index** — ROSETTA stemmer + stop word removal
2. **IDF computation** — SPECTRA spectral fingerprints per paragraph
3. **Contrastive anchor extraction** — for each paragraph:
   a. Find K nearest confusers by SPECTRA cosine similarity
   b. Score each word: `contrastive = IDF × (1 - presence_in_confusers)`
   c. Store top-K words as the paragraph's anchor fingerprint
4. **Neighborhood map** — store adjacency relationships (sequential
   position within the source document)

Build-time output is static. Same corpus always produces same anchors,
same neighborhoods, same IDF tables. Store to disk, load at runtime.

### Query Time (Pipeline)

```
Query arrives
    ↓
Mode Router: Exact / Keyword / Explore
    ↓
[Exact]    → n-gram hash lookup → match or fail
[Keyword]  → SPECTRA shortlist → Anchor refinement → Neighborhood vote → Gate
[Explore]  → Full pipeline → Gate → LLM fallback if LOW confidence
```

### Mode Routing

**Exact Mode** — query contains a verbatim text fragment.
- Detection: high n-gram overlap with a single paragraph
- Method: substring or n-gram hash matching
- Confidence: binary (match or no match)
- Cost: near zero (hash lookup)
- Sits above SPECTRA in the stack — if it fires, skip everything else

**Keyword Mode** — query carries descriptive vocabulary.
- Detection: multiple content words, no verbatim substring match
- Method: full SLA pipeline (see below)
- Confidence: margin-gated (HIGH / MED / LOW)
- Cost: milliseconds (dictionary math, no API calls)

**Explore Mode** — query is broad or ambiguous.
- Detection: low-IDF query words, or user-selected mode
- Method: full SLA pipeline + LLM escalation when gate reads LOW
- Confidence: variable, LLM-assisted for hard cases
- Cost: 0 tokens if gate reads HIGH, ~200 tokens if LLM fallback

## The Pipeline (Keyword / Explore)

### Layer 1: SPECTRA Shortlist

Score all paragraphs by IDF-weighted overlap with query terms.
Return top-N candidates (default N=5). This reduces the corpus
by 99%+ in a single pass.

    score(para, query) = Σ idf(w) for w in (para ∩ query) / |query|

This is pure SPECTRA — no modification to the base algorithm.

### Layers 2+3: Confidence Adjustment (v2, Session 90)

Anchors and neighbors do NOT change the ranking. They adjust the
confidence margin between #1 and #2.

**Anchor differential:** Count anchor hits on #1 vs #2.

    anchor_adj = anchor_weight × (top_hits - runner_hits)

If #1 has more anchor hits than #2, margin goes up (more confident).
If #2 has more anchor hits than #1, margin goes down (less confident).
Neither changes who #1 is.

**Neighborhood differential:** Compare neighbor resonance.

    nbr_resonance(idx) = avg(IDF overlap with neighbors) / query_size
    nbr_diff = (top_nbr - runner_nbr) / max(top_nbr, runner_nbr)
    nbr_adj = nbr_weight × nbr_diff

If #1's neighborhood resonates more than #2's, margin goes up.

**Final margin:**

    raw_margin = SPECTRA margin between #1 and #2
    margin = clamp(raw_margin + anchor_adj + nbr_adj, 0.1%, 100%)

Tested parameters (S90):
- anchor_weight = 15 (pp per anchor hit differential)
- nbr_weight = 10 (pp scaling for neighborhood differential)

**Why not multiplicative (S89 → S90 correction):** Session 89
used multiplicative composition where anchor/neighbor bonuses
scaled the combined score. This violated the CM principle because
different multipliers for different candidates COULD flip the
ranking. A single anchor hit (1/5 = 0.2 ratio) gave a 30% bonus,
enough to override a 3.4% SPECTRA lead. Session 90 fixed this by
separating ranking (SPECTRA, immutable) from confidence (anchors +
neighbors, margin adjustment only).

### Layer 4: Confidence Gate

Route based on the adjusted margin:

| Margin | Confidence | Action |
|--------|------------|--------|
| > 50%  | HIGH       | Return #1 directly. Zero tokens. |
| 15-50% | MED        | Return #1 with flag. Soft verify. |
| < 15%  | LOW        | Escalate shortlist to LLM (~200 tokens). |

The gate makes the system's uncertainty visible. High confidence
means the math is decisive. Low confidence means the query lacks
enough distinctive vocabulary to discriminate — the system knows
what it doesn't know.

## Contrastive Anchors

Standard anchors select globally rare words (highest IDF). This
works well for diverse corpora. For dense corpora where neighboring
paragraphs share vocabulary, contrastive anchors provide sharper
discrimination.

### Algorithm

For each paragraph p:
1. Find K nearest confusers by SPECTRA cosine similarity
2. For each word w in p:
   - presence = fraction of confusers containing w
   - contrastive_score = IDF(w) × (1.0 - presence)
3. Select top-K words by contrastive score as anchors

### Properties

- **Scale-dependent:** On small corpora (< 100 paragraphs), global
  IDF ≈ contrastive scoring. On large corpora (1000+), they diverge
  and contrastive provides meaningful lift.
- **Never worse:** Contrastive scores converge to global IDF when
  confusers don't share vocabulary. No downside risk.
- **Build-time only:** Confuser identification and scoring happen
  once at ingestion. Runtime cost is identical to global anchors.

**Doctrine default:** Use contrastive anchors for all build-time
anchor computation regardless of corpus size.

## Validation Results

### Test Corpus: 39 Bible Verses (Session 89)

5 clusters across 1 Kings, Romans, Genesis, 2 Samuel, and Psalms.
Deliberate cross-cluster vocabulary overlap ("servant," "lord,"
"king," "woman" shared across clusters A, C, D).

| System | Accuracy | HIGH | MED | LOW |
|--------|----------|------|-----|-----|
| SPECTRA alone | 20/20 | — | — | — |
| GPS v1 (additive, S89) | 19/20 | 16 | 3 | 1 |
| GPS v2 (multiplicative, S89) | 19/20 | 17 | 2 | 1 |
| SLA v2 (layered narrowing, S90) | 20/20 | 18 | 0 | 2 |

Key findings:
- v1 additive: anchor hits on lower-ranked candidate leapfrogged higher
- v2 multiplicative: different multipliers still allowed rank flipping
  (a single anchor hit giving 30% boost overrode a 3.4% SPECTRA lead)
- v2 layered narrowing (S90): SPECTRA ranking locked as immutable,
  anchors/neighbors adjust margin only → 20/20 correct, honest confidence
- Token economics: ~200 tokens total vs 31,200 for shipping full corpus

### Hard Ceiling Query

"servant said master lord king woman" → 1 Kings 1:2

All query words are high-df (appear in many verses). Runner-up
(2 Sam 13:17) has an anchor hit on "woman" that #1 lacks. In v1/v2
multiplicative, this flipped the ranking. In v2 layered narrowing,
SPECTRA's ranking is immutable: 1 Kings 1:2 stays #1, but the
anchor differential reduces the margin from 3.4% to 0.1% → LOW
confidence → LLM escalation. The system preserves the correct
answer while honestly reporting that it's not sure.

## Token Economics

For a corpus of N paragraphs with average query load:

| Approach | Cost per query |
|----------|---------------|
| Ship full corpus to LLM | N × ~40 tokens |
| Embedding + vector DB | API call + storage |
| SLA (HIGH confidence) | 0 tokens |
| SLA (MED confidence) | 0 tokens (flagged) |
| SLA (LOW confidence) | ~200 tokens (5 candidates to LLM) |

Expected distribution at scale: ~80% HIGH, ~15% MED, ~5% LOW.
Average cost approaches near-zero per query.

## Known Limitations

- **Word-level ceiling:** Inherited from SPECTRA. Cannot disambiguate
  when query vocabulary genuinely spans multiple paragraphs. This is
  a property of word-level matching, not a bug.
- **No semantic understanding:** "Curiosity" won't match a paragraph
  about "inquisitiveness." The stemmer helps with inflections but
  true synonyms require the LLM fallback.
- **Sequential adjacency assumption:** Neighborhood voting assumes
  nearby paragraphs are related. Works for narrative text (chapters,
  articles). May not apply to randomly ordered collections.
- **Exact mode not yet implemented:** Mode routing is designed but
  only Keyword/Explore modes are validated. Exact mode (n-gram hash)
  is specified but untested.

## IS Statements

- SLA IS the retrieval orchestration doctrine.
- SLA IS a consumer of ROSETTA, SPECTRA, and CM — it composes them without modifying them.
- SLA IS layered: SPECTRA ranks (immutable), anchors and neighbors adjust confidence only. Lower layers narrow within higher layers, never override.
- SLA IS mode-aware: Exact, Keyword, and Explore route to different pipeline depths.
- SLA IS confidence-gated: margin between candidates determines routing.
- SLA IS precomputed where possible: anchors, neighborhoods, and IDF tables are build-time.
- SLA IS contrastive by default: anchor selection accounts for local confusers.
- SLA IS honest: the system reports what it knows and what it doesn't know.
- SLA IS NOT a replacement for any linked doctrine entity.
- SLA IS NOT a semantic search engine — it extends word-level retrieval with structural intelligence.

## Linked Entities

- **BOND_MASTER** — constitutional authority
- **ROSETTA** — force classification (Layer 1 of compound anchor, stemmer + lexicons)
- **SPECTRA** — spectral fingerprinting (IDF retrieval, shortlist generation)
- **CM** — layered lookup pattern (narrowing architecture, multiplicative principle)
