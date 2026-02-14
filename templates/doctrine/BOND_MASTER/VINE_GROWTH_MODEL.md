# Vine Growth Model — Perspective Lifecycle Design

## Source: John 15 (The Vine and the Branches)

"I am the vine; you are the branches... He cuts off every branch in me that bears no fruit, while every branch that does bear fruit he prunes so that it will be even more fruitful."

## Lifecycle

### Roots — The Vine Itself
- Identity anchors. How the perspective SEES.
- Planted deliberately by the user or distilled from corpus.
- Immutable taproots. Stored as ROOT-*.md files + QAIS vectors.
- They shape resonance but don't change from use.

### Seeds — New Branches (Auto-Collected)
- Free growth. No approval gate.
- Every resonance hit above threshold during {Sync} becomes a living branch.
- Auto-written as .md file + auto-injected into QAIS field.
- Low barrier, high volume. The vine grows freely.
- Logged to seed_decisions.jsonl for record.

### Pruning — The Only Deliberate Act
- Judgment-based, not mechanical. Requires {Enter} — the perspective must be the active entity.
- Claude cannot make prune decisions from outside the perspective. During vine lifecycle under a different entity, seeds at prune window are flagged but NOT evaluated.
- When entered: Claude reads through ROOT lens. Ask: does this seed grow from who this perspective IS?
- Tracker data is evidence, not verdict. Dormant seeds aligned with roots stay.
- State verdict and execute — do not ask the user for permission. Explain why, then cut or keep.
- Pruned seeds are:
  1. Logged to G-pruned-*.md with ROOT lens reason + tracker stats
  2. Removed from QAIS field via perspective_remove (exact vector subtraction)
  3. Removed from seed_tracker.json
  4. Seed .md file deleted
  5. Auto-logged to seed_decisions.jsonl
- The gardener's only job. No promotion, no tiers.

### Re-Grafting — Compost Reclaimed
- The perspective revisits the dead branch log.
- Current state may recognize value the past state missed.
- A pruned seed can be restored to the QAIS field.
- The vine reclaims its own dead wood when ready.
- The branch wasn't wrong — the vine just wasn't ready.

**Re-Graft Gate (Anti-Loop Rule):**
Auto-seed checks the pruning log before writing. If a candidate seed
was previously pruned, it must co-resonate with 2+ LIVING seeds in
the same resonance check to pass the gate.
- Firing alone = old pattern repeating → blocked.
- Firing with living company = vine grew around it → re-graft.
- This prevents the prune/collect infinite loop.
- Process rule, not content rule. Doesn't tell the perspective
  what to think — tells it to check its compost pile first.

### Growth — The Living State
- Not a file type. Not a promotion.
- Growth IS what remains after pruning + what gets added and not pruned.
- Measured, not stored: root count + active seed count + field health.
- G- prefix marks pruning journals, not promoted content.

## Design Decisions

- **No approval gate on seeds**: Replaced by pruning. Quality lives downstream.
- **No promotion**: Only pruning. What survives IS the growth.
- **Dead branch log preserved**: Low cost, high value. Enables re-graft.
- **G- prefix repurposed**: Pruning journal, not growth badge.
- **Auto-seed on {Sync}**: Threshold hit → file + QAIS injection, no user prompt.
- **Judgment over mechanics**: ROOT lens identity alignment, not hit count thresholds.

## Seed Tracker (S99 Design)

Each perspective maintains `seed_tracker.json` in its folder:
```json
{
  "seed-name": {
    "planted": "2026-02-11",
    "exposures": 0,
    "hits": 0,
    "last_hit": null
  }
}
```

**Sync lifecycle (one pass):**
1. Run resonance check (perspective_check) — ~600-900 tokens
2. Auto-seed: new hits above threshold → file + QAIS injection + tracker entry
3. Increment exposures on ALL active seeds
4. Re-graft gate: check pruning log for returning candidates, require 2+ living co-resonance
5. Prune eligible: seeds past `prune_window` exposures are FLAGGED. Prune evaluation requires {Enter} — perspective must be active entity. From outside, report and move on.

**Entity sovereignty:** The perspective holds its own shears.
- `prune_window` lives in entity.json — how many exposures before eligible
- ROOT lens identity alignment decides life/death — not the user, not Claude-from-outside
- Claude cannot judge through a perspective's ROOT lens without entering it
- User is gardener (can review log, re-graft manually) not shears

**Default tuning (set on perspective creation):**
- `seed_threshold: 0.04` — wide net, lets the entity catch patterns we wouldn't expect
- `prune_window: 10` — seeds get 10 Sync exposures before pruning eligibility
- `seeding: false` — armed manually via panel toggle (SEED ON/OFF)
- Each entity can override these in its own entity.json
- At 50+ seed decisions, genetic tuning becomes viable — the entity defines its own fitness function

**Stale seed bed:** High exposures, nothing new landing = mature vine.
Not a problem state. Dormant, not dead. Seeding stays armed.
Optional: panel visual status (active/stable/dormant) — deferred.

**Cost:** ~1,200 tokens total per Sync for full vine lifecycle.
Toggle: SEED ON/OFF on entity card disarms completely.

## Implementation Status

- [x] Root system (files + QAIS + auto-injection pipeline)
- [x] Seed system (files + QAIS + resonance check)
- [x] Panel counts (roots, seeds, growth, pruned separate)
- [x] seed_decisions.jsonl auto-logging (baked into perspective_store/perspective_remove)
- [x] Seed toggle (SEED ON/OFF on entity card)
- [x] Auto-seed (no approval gate, ROOT lens + low resonance confirmation)
- [x] seed_tracker.json per perspective
- [x] Exposure counting on Sync
- [x] Self-pruning (ROOT lens identity alignment judgment)
- [x] Dead branch log (G-pruned-*.md with reason + stats)
- [x] QAIS field removal (perspective_remove, exact vector subtraction)
- [x] Re-graft gate (anti-loop, co-resonance check via pruned_seeds in perspective_check)
- [x] Growth measurement (derive from living state)
- [x] Universal root (ROOT-self-pruning-authority.md auto-planted on perspective creation)
- [ ] Panel visual status (active/stable/dormant) — deferred

## Mantra

"The vine grows freely. The gardener only prunes."
