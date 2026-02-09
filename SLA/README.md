# SLA — Spectral Linguistic Anchorage

**Retrieval orchestration layer for BOND.**

SLA composes ROSETTA (force classification), SPECTRA (spectral fingerprinting), and CM (layered lookup) into a unified pipeline for locating specific passages within large text bodies.

## How It Works

1. **Build time** — Tokenize corpus, compute IDF fingerprints, extract contrastive anchors, map neighborhoods. All precomputed, stored once.
2. **Query time** — SPECTRA ranks candidates (immutable). Anchors and neighbors adjust the confidence margin only — lower layers narrow within higher layers, never override.
3. **Confidence gate** — Margin between #1 and #2 determines routing: HIGH (>50%) returns directly, MED (15-50%) flags for review, LOW (<15%) escalates shortlist to LLM (~200 tokens).

## Key Principle

SPECTRA's ranking is immutable. Anchors can make the system less confident about SPECTRA's pick, but they cannot change it. This aligns with Calendar Master's foundational rule: lower layers narrow within higher layers, never override.

## Files

| File | Description |
|------|-------------|
| `SLA.md` | Full doctrine — theory, architecture, validation results |
| `sla.py` | Python reference implementation v2 |
| `sla.js` | JavaScript reference implementation v2 (browser/Node) |

## Token Economics

| Approach | Cost per query |
|----------|---------------|
| Ship full corpus to LLM | N × ~40 tokens |
| SLA (HIGH confidence) | **0 tokens** |
| SLA (MED confidence) | **0 tokens** (flagged) |
| SLA (LOW confidence) | **~200 tokens** (5 candidates to LLM) |

## Validation

20/20 accuracy on a 39-verse Bible corpus with deliberate cross-cluster vocabulary overlap. See `SLA.md` for full results.

## Usage (JavaScript)

```javascript
const { SLACorpus } = require('./sla.js');

const corpus = new SLACorpus(paragraphs, { labels });
const { results, margin, confidence } = corpus.query('search terms');

console.log(confidence.level); // 'HIGH', 'MED', or 'LOW'
console.log(results[0].label); // best match
```

## Usage (Python)

```python
from sla import SLACorpus

corpus = SLACorpus(paragraphs, labels=labels)
results, margin = corpus.query('search terms')
print(corpus.confidence_label(margin))
```
