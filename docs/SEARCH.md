# SLA — Doctrine Search

The panel includes a built-in search engine powered by SLA (Spectral Linguistic Anchorage). When you enter an entity, its doctrine files — plus any linked entities — are automatically indexed for instant search.

## How It Works

1. **Enter an entity** — click Enter on any entity card
2. **Index builds automatically** — all `.md` files from the active entity and its linked entities are parsed and indexed client-side
3. **Search** — type a query in the search panel and hit Enter
4. **Results** — ranked paragraphs with confidence badges

## Confidence Badges

| Badge | Margin | Meaning |
|-------|--------|---------|
| 🟢 HIGH | > 50% | Strong match — #1 is clearly the best result |
| 🟡 MED | 15-50% | Likely match — #1 leads but not by much |
| 🔴 LOW | < 15% | Multiple candidates — system can't discriminate |

🔴 LOW doesn't mean failure. It means "here are your options" — useful for cross-referencing where a concept appears across doctrine.

## Escalation

Every search result includes a "Send to Claude →" (or "Escalate to Claude →" for LOW confidence) button. This copies a compact shortlist (~200 tokens) to your clipboard. Paste it into Claude for LLM-assisted discrimination.

The AHK bridge recognizes escalation clipboard content and leaves it for manual paste rather than auto-typing.

## Architecture

Search runs entirely client-side. Zero API calls, zero tokens for the search itself:

- **Splitting** — Markdown files are split into paragraphs using headers, double-newlines, and IS statements as boundaries
- **Indexing** — SPECTRA IDF fingerprints + contrastive anchors computed at build time
- **Ranking** — SPECTRA determines ranking (immutable). Anchors and neighbors adjust confidence margin only
- **Gate** — Confidence margin routes to direct return or LLM escalation

## Token Economics

| Approach | Cost per query |
|----------|---------------|
| Ship full doctrine to LLM | ~31,000 tokens |
| SLA (HIGH/MED confidence) | **0 tokens** |
| SLA (LOW → escalate) | **~200 tokens** |

## Technical Details

See [`SLA/`](../SLA/) for the full doctrine, reference implementations (Python + JavaScript), and validation results.
