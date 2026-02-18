# Seed Collection — Doctrine Authority

## What This Document IS

This doctrine defines how perspective entities collect seeds through passive resonance during normal BOND sessions. Seeds are the raw material from which perspectives grow.

## Mechanism

### Armed Perspectives
A perspective entity can be "armed" for seed collection by setting `seeding: true` in its `entity.json`. This can be toggled via the Panel UI (SEED ON/OFF button on perspective cards) or via the API.

### Passive Collection (Sync Step 5)
During every {Sync}, the BOND protocol checks for armed perspectives. If any exist:
1. Conversation text is checked against each armed perspective's isolated QAIS field via `perspective_check`
2. Seeds that resonate above threshold are surfaced as candidates
3. Claude presents candidates to the user for approve/reject decision
4. Approved seeds are stored via `perspective_store` into the perspective's isolated field

### Tool Authorization Bypass
When armed seeders exist, QAIS tools (`qais_passthrough`, `perspective_store`, `perspective_check`) are allowed through any entity class — not just QAIS-enabled classes. The active entity does NOT absorb QAIS capability; the tools serve the perspectives directly.

### Decision Logging
Every approve/reject decision is logged to `data/seed_decisions.jsonl` for future genetic optimization. Each entry records: perspective, seed title, decision, timestamp, active entity context.

## Principles

- **Organic over forced**: Seeds accumulate naturally during work sessions. Never manufacture seed opportunities.
- **User sovereignty**: Every seed requires explicit user approval. No automatic storage.
- **Isolation**: Each perspective has its own `.npz` field. Seeds don't cross-contaminate between perspectives.
- **Non-invasive**: Seed collection adds ~30 seconds to Sync. It does not interrupt workflow.

## Phase 2: Genetic Optimization

After 50+ labeled decisions accumulate, the decision log enables genetic optimization of the QAIS resonance algorithm. The genome evolves to better predict which seeds the user will approve, improving signal-to-noise ratio over time.

## Mantra

"Seeds grow where attention falls."
