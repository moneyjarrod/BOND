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
- Seeds are delivery mechanisms, not permanent residents. They exist to prove a pattern, then either germinate into vine density or get composted.

### Rain — Ambient Nourishment (S118)
- Scores below sunshine threshold but above rain floor nourish existing seeds without creating new ones.
- Rain represents conversation climate — the vine's neighborhood is active even when nothing lands directly.
- Rain does NOT create hits. It feeds vine density around existing seeds.
- Capped: max 1 rain event per seed per Sync pass, max 1 per seed per session.
- Rain is tracked in seed_tracker.json alongside hits and exposures.

**Threshold Bands:**
| Entity Type | Sunshine (hit) | Rain Band | Dry (no effect) |
|---|---|---|---|
| Standard (seed_threshold: 0.04) | >= 0.040 | 0.025 - 0.039 | < 0.025 |
| Wide-net (seed_threshold: 0.035) | >= 0.035 | 0.020 - 0.034 | < 0.020 |

**Rain floor formula:** `seed_threshold x 0.625` (rounded to nearest 0.005)

### Superposition — Seeds as Uncollapsed Resonance (S118, CM-MELODY)
- A pattern resonating during {Sync} exists across every perspective field simultaneously until a score collapses it.
- Collapse: Score >= seed_threshold in one perspective = the pattern's identity resolved. Seed planted there.
- Uncollapsed resonance: Scores below threshold in other perspectives are not failure. They are the pattern still containing those perspectives' chords, just quieter.
- On auto-seed, log `collapsed_from` in the tracker: which other perspectives carried resonance above their rain floor on the same pass. Zero cost -- scores already exist.
- Source: CM-MELODY.md. "The note doesn't become a chord. It already was every chord. Context decides which one you hear."

**Use cases:**
1. **Directed re-graft:** If a seed is pruned, `collapsed_from` shows where the uncollapsed resonance was strongest. The pattern may belong in a different perspective -- it just resolved into the wrong chord first.
2. **Perspective discovery:** Patterns that score 0.02-0.035 across multiple perspectives but never collapse into any of them are notes that don't belong to any current chord. Sustained uncollapsed resonance across the system is the harmonic argument for a new perspective.
3. **Cross-perspective awareness:** The operator (mycelium) can see where a pattern was superposed before it collapsed, enriching understanding of how perspectives relate without merging their fields.

### Pruning — The Gardener's Only Cut
- Judgment-based, not mechanical. Requires {Enter} — the perspective must be the active entity.
- Claude cannot make prune decisions from outside the perspective. During vine lifecycle under a different entity, seeds at prune window are flagged but NOT evaluated.
- When entered: Claude reads through ROOT lens. Ask: does this seed grow from who this perspective IS?
- Tracker data is evidence, not verdict. Dormant seeds aligned with roots stay.
- State verdict and execute — do not ask the user for permission. Explain why, then cut or keep.

**Prune Health Formula (S118):**
```
effective_health = hits + (rain x 0.25)
prune_eligible = exposures >= prune_window
prune_risk = prune_eligible AND effective_health < 1.0
```
A seed needs at least 1 direct hit OR 4 rain events to clear the health floor. Rain provides partial credit — the conversation stayed in the neighborhood without ever landing directly. Seeds with rain but no hits are climate-supported but unproven. Seeds with neither rain nor hits are genuinely dormant.

**Prune evaluation now considers three categories:**
1. **Healthy:** effective_health >= 1.0 — seed has proven itself or is well-watered. No prune risk.
2. **Dry but aligned:** effective_health < 1.0 but ROOT lens confirms identity alignment. Kept. Topic neglect is not a death sentence.
3. **Dry and misaligned:** effective_health < 1.0 AND ROOT lens finds no identity connection. Composted.

- Pruned seeds are:
  1. Logged to G-pruned-*.md with ROOT lens reason + tracker stats (including rain and collapsed_from)
  2. Removed from QAIS field via perspective_remove (exact vector subtraction)
  3. Removed from seed_tracker.json
  4. Seed .md file deleted
  5. Auto-logged to seed_decisions.jsonl

### Prune Reversibility

Every prune is auditable and reversible:
- **Audit trail:** G-pruned-{seed-name}.md contains ROOT lens reason, tracker stats at time of cut, and timestamp. These files are retained permanently — they are not cleaned up.
- **QAIS reversal:** perspective_remove subtracts exact vectors. perspective_store can re-add them. The math is deterministic — same seed content produces same vectors.
- **Re-graft path:** A pruned seed can return through the re-graft gate if it co-resonates with 2+ living seeds. The compost pile is not a grave — it is a waiting room.
- **Manual override:** The operator can always re-plant a pruned seed by writing the .md file and calling perspective_store directly. The perspective's autonomy is self-sovereign, not irreversible.

### Germination — Seeds Become Vine (S118, Future Phase)
- A seed that has proven itself structurally — through sustained hits, consistent rain, and co-resonance with other living seeds — is no longer a branch. It became load-bearing. The seed shell cracks and the vine emerges.
- Germination transforms the seed's contribution into vine density in the crystal momentum field. The seed .md is retired. The pattern lives on as accumulated structural weight, not a discrete label.
- **Not yet implemented.** Criteria under development. Candidate threshold: >= 5 hits, planted across >= 5 sessions, co-resonates with 2+ living seeds. Requires dedicated design session.
- Design principle: you don't promote seeds to vine. You recognize that a seed WAS vine all along and the shell finally fell away.

### Re-Grafting — Compost Reclaimed
- The perspective revisits the dead branch log.
- Current state may recognize value the past state missed.
- A pruned seed can be restored to the QAIS field.
- The vine reclaims its own dead wood when ready.
- The branch wasn't wrong — the vine just wasn't ready.
- **Directed re-graft (S118):** If a pruned seed has `collapsed_from` data, check those perspectives first. The pattern may belong in a different chord — it collapsed into the wrong perspective initially. Instead of waiting for a ghost seed to fire randomly, the superposition record tells you where to look.

**Re-Graft Gate (Anti-Loop Rule):**
Auto-seed checks the pruning log before writing. If a candidate seed
was previously pruned, it must co-resonate with 2+ LIVING seeds in
the same resonance check to pass the gate.
- Firing alone = old pattern repeating -> blocked.
- Firing with living company = vine grew around it -> re-graft.
- This prevents the prune/collect infinite loop.
- Process rule, not content rule. Doesn't tell the perspective
  what to think — tells it to check its compost pile first.

### Growth — The Living State
- Not a file type. Not a promotion.
- Growth IS what remains after pruning + what gets added and not pruned.
- Measured, not stored: root count + active seed count + rain health + field density.
- G- prefix marks pruning journals, not promoted content.

## Design Decisions

- **No approval gate on seeds**: Replaced by pruning. Quality lives downstream.
- **Rain not sunshine**: Sub-threshold scores nourish, don't plant. The vine gets thicker without getting longer.
- **Rain caps prevent flooding**: 1 per seed per session. Six Sync passes about UI work don't give a testing seed 6 rain ticks.
- **Effective health, not raw hits**: Prune decisions consider the full picture — sunshine, rain, and ROOT alignment. Topic neglect doesn't kill aligned seeds.
- **Superposition tracking at zero cost**: collapsed_from logs which perspectives a pattern resonated across before collapsing into one. Enables directed re-graft and perspective discovery. No new tool calls — scores already exist from Sync.
- **Dead branch log preserved**: Low cost, high value. Enables re-graft.
- **G- prefix repurposed**: Pruning journal, not growth badge.
- **Auto-seed on {Sync}**: Threshold hit -> file + QAIS injection, no user prompt.
- **Germination deferred**: Seed-to-vine transformation designed but not implemented. Seeds remain discrete until criteria finalized.

## Seed Tracker (S118 Format)

Each perspective maintains `seed_tracker.json` in its folder:
```json
{
  "seed-name": {
    "planted": "2026-02-11",
    "exposures": 0,
    "hits": 0,
    "rain": 0,
    "last_hit": null,
    "last_rain": null,
    "collapsed_from": []
  }
}
```

**Sync lifecycle (one pass):**
1. Run resonance check (perspective_check) for ALL armed perspectives — ~600-900 tokens each
2. Auto-seed: new hits above sunshine threshold -> file + QAIS injection + tracker entry
3. Score existing seeds:
   a. Score >= sunshine threshold -> increment hits, record last_hit
   b. Score >= rain floor AND < sunshine threshold -> increment rain (max 1 per seed per session), record last_rain
   c. Score < rain floor -> no effect
4. Increment exposures on ALL active seeds
5. Superposition logging (on auto-seed only): When a new seed is planted in perspective A, check that seed's concept against all OTHER armed perspectives' most recent scores from step 1. Any perspective that scored above its rain floor = uncollapsed resonance. Log as `collapsed_from: ["PerspB:0.038", "PerspC:0.022"]` in the new seed's tracker entry. Zero cost — scores already exist.
6. Re-graft gate: check pruning log for returning candidates, require 2+ living co-resonance
7. Prune eligible: seeds past `prune_window` exposures with effective_health < 1.0 are FLAGGED. Prune evaluation requires {Enter} — perspective must be active entity. From outside, report and move on.

**Entity sovereignty:** The perspective holds its own shears.
- `prune_window` lives in entity.json — how many exposures before eligible
- ROOT lens identity alignment decides life/death — not the user, not Claude-from-outside
- Claude cannot judge through a perspective's ROOT lens without entering it
- User is gardener (can review log, re-graft manually) not shears

**Default tuning (set on perspective creation):**
- `seed_threshold: 0.04` — sunshine threshold for hits and new seeds
- `rain_floor: auto` — computed as seed_threshold x 0.625, rounded to nearest 0.005
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
- [x] Rain mechanic (S118 — threshold bands, capped per-session, tracker field)
- [x] Superposition tracking (S118 — collapsed_from field, directed re-graft, perspective discovery)
- [ ] Germination phase (seed -> vine density in crystal field) — designed, not implemented
- [ ] Panel visual status (active/stable/dormant) — deferred
- [ ] Panel rain display — deferred
- [ ] Panel superposition display — deferred

## Mantra

"The vine grows freely. The rain falls gently. The gardener only prunes."
