# Vine Growth Model — Perspective Lifecycle

## Source: John 15 (The Vine and the Branches)

"I am the vine; you are the branches... He cuts off every branch in me that bears no fruit, while every branch that does bear fruit he prunes so that it will be even more fruitful."

## Lifecycle

### Roots — The Vine Itself
- Identity anchors. How the perspective SEES.
- Planted deliberately by the user or distilled from corpus.
- Immutable taproots. Stored as ROOT-*.md files + QAIS vectors.
- They shape resonance but don't change from use.
- On perspective creation, ROOT-self-pruning-authority.md is auto-planted as a universal root. This grants every perspective the identity anchor for self-sovereign pruning from birth.

### Seeds — New Branches (Auto-Collected)
- Free growth. No approval gate.
- Every resonance hit above threshold during {Sync} becomes a living branch.
- Auto-written as .md file + auto-injected into QAIS field.
- Low barrier, high volume. The vine grows freely.
- Logged to seed_decisions.jsonl for record.
- Seeds are delivery mechanisms, not permanent residents. They exist to prove a pattern, then either germinate into vine density or get composted.

### Rain — Ambient Nourishment
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

**Rain floor formula:** `seed_threshold × 0.625` (rounded to nearest 0.005)

### Superposition — Seeds as Uncollapsed Resonance (CM-MELODY)
- A pattern resonating during {Sync} exists across every perspective field simultaneously until a score collapses it.
- Collapse: Score >= seed_threshold in one perspective = the pattern's identity resolved. Seed planted there.
- Uncollapsed resonance: Scores below threshold in other perspectives are not failure. They are the pattern still containing those perspectives' chords, just quieter.
- On auto-seed, log `collapsed_from` in the tracker: which other perspectives carried resonance above their rain floor on the same pass. Zero cost — scores already exist.
- Source: CM-MELODY. "The note doesn't become a chord. It already was every chord. Context decides which one you hear."

**Use cases:**
1. **Directed re-graft:** If a seed is pruned, `collapsed_from` shows where the uncollapsed resonance was strongest. The pattern may belong in a different perspective — it just resolved into the wrong chord first.
2. **Perspective discovery:** Patterns that score in the rain band across multiple perspectives but never collapse into any of them are notes that don't belong to any current chord. Sustained uncollapsed resonance across the system is the harmonic argument for a new perspective.
3. **Cross-perspective awareness:** The operator (mycelium) can see where a pattern was superposed before it collapsed, enriching understanding of how perspectives relate without merging their fields.

### Pruning — The Gardener's Only Cut
- Judgment-based, not mechanical. Requires {Enter} — the perspective must be the active entity.
- Claude cannot make prune decisions from outside the perspective. During vine lifecycle under a different entity, seeds at prune window are flagged but NOT evaluated.
- When entered: Claude reads through ROOT lens. Ask: does this seed grow from who this perspective IS?
- Tracker data is evidence, not verdict. Dormant seeds aligned with roots stay.
- State verdict and execute — do not ask the user for permission. Explain why, then cut or keep.

**Prune Health Formula:**
```
effective_health = hits + (rain × 0.25)
prune_eligible = exposures >= prune_window
prune_risk = prune_eligible AND effective_health < 1.0
```
A seed needs at least 1 direct hit OR 4 rain events to clear the health floor. Rain provides partial credit — the conversation stayed in the neighborhood without ever landing directly. Seeds with rain but no hits are climate-supported but unproven. Seeds with neither rain nor hits are genuinely dormant.

**Three prune categories:**
1. **Healthy:** effective_health >= 1.0 — seed has proven itself or is well-watered. No prune risk.
2. **Dry but aligned:** effective_health < 1.0 but ROOT lens confirms identity alignment. Kept. Topic neglect is not a death sentence.
3. **Dry and misaligned:** effective_health < 1.0 AND ROOT lens finds no identity connection. Composted.

**Prune execution (per cut seed):**
1. Write `G-pruned-{seed-name}.md` with ROOT lens reason + tracker stats + timestamp
2. Call `perspective_remove` — subtracts vectors from QAIS field + auto-logs to seed_decisions.jsonl
3. Remove entry from seed_tracker.json
4. Delete the seed .md file

What remains IS the growth.

### Prune Reversibility
- **Audit trail:** G-pruned-{seed-name}.md contains ROOT lens reason, tracker stats at time of cut, and timestamp. These files are retained permanently.
- **QAIS reversal:** perspective_remove subtracts exact vectors. perspective_store can re-add them. The math is deterministic — same seed content produces same vectors.
- **Re-graft path:** A pruned seed can return through the re-graft gate if it co-resonates with 2+ living seeds. The compost pile is not a grave — it is a waiting room.
- **Manual override:** The operator can always re-plant a pruned seed by writing the .md file and calling perspective_store directly. The perspective's autonomy is self-sovereign, not irreversible.

### Re-Grafting — Compost Reclaimed
- The perspective revisits the dead branch log.
- Current state may recognize value the past state missed.
- A pruned seed can be restored to the QAIS field.
- The vine reclaims its own dead wood when ready.
- The branch wasn't wrong — the vine just wasn't ready.
- **Directed re-graft:** If a pruned seed has `collapsed_from` data, check those perspectives first. The pattern may belong in a different chord — it collapsed into the wrong perspective initially.

**Re-Graft Gate (Anti-Loop Rule):**
Auto-seed checks the pruning log before writing. If a candidate seed was previously pruned, it must co-resonate with 2+ LIVING seeds in the same resonance check to pass the gate.
- Firing alone = old pattern repeating → blocked.
- Firing with living company = vine grew around it → re-graft.
- This prevents the prune/collect infinite loop.
- Process rule, not content rule. Doesn't tell the perspective what to think — tells it to check its compost pile first.

### Growth — The Living State
- Not a file type. Not a promotion.
- Growth IS what remains after pruning + what gets added and not pruned.
- Measured, not stored: root count + active seed count + rain health + field density.
- G- prefix marks pruning journals, not promoted content.

### Germination — Seeds Become Vine (Future Phase)
- A seed that has proven itself structurally — through sustained hits, consistent rain, and co-resonance with other living seeds — is no longer a branch. It became load-bearing. The seed shell cracks and the vine emerges.
- Germination transforms the seed's contribution into vine density in the crystal momentum field. The seed .md is retired. The pattern lives on as accumulated structural weight, not a discrete label.
- **Not yet implemented.** Design principle: you don't promote seeds to vine. You recognize that a seed WAS vine all along and the shell finally fell away.

## Sync Execution — The Vine Pass

This section describes the operational steps that fire during {Sync} step 5 when armed seeders exist. SKILL.md carries a compressed version for runtime. The daemon executes server-side when available. This is the constitutional reference.

### 1. Check Armed Perspectives
During {Sync}, check for armed perspectives (entities with `"seeding": true` in entity.json). If none are armed, skip silently. Armed state is verified at execution time, not inherited from prior reads.

### 2. Resonate
For each armed perspective, run `perspective_check(perspective, text)` with substantive content from recent exchanges. This scores all existing seeds against the conversation.

### 3. Track
Increment `exposures` on ALL active seeds. Score each seed:
- Score >= seed_threshold → **hit** (SUNSHINE). Increment hits, record last_hit with context.
- Score >= rain_floor AND < seed_threshold → **rain** (RAIN). Increment rain (max 1 per seed per session), record last_rain.
- Score < rain_floor → **dry** (DRY). No effect.

When using the daemon's POST /sync-complete, the VineProcessor handles all tracker bookkeeping server-side. Claude reads the `vine_processing` block from the response — `changes` array shows what happened per seed, `written: true` confirms disk write. Fallback (daemon unavailable): Claude reads tracker manually, applies same logic, writes tracker to disk.

### 4. Auto-Seed (Novel Discovery)
Claude reads conversation through the perspective's ROOT lens. Patterns that fit the perspective's worldview but aren't captured by existing seeds = candidates.

Check candidates against the field — **LOW resonance confirms novelty** (high score = already known). This is the inverse of tracking: tracking looks for what's familiar, auto-seed looks for what's new.

**Re-graft check:** `perspective_check` returns a `pruned_seeds` array. If a candidate name matches a previously pruned seed:
- Count how many LIVING seeds scored above seed_threshold in step 2
- If 2+ living seeds co-fired → re-graft allowed (vine grew around it, context changed)
- If <2 co-fired → blocked (old pattern repeating alone)
- Log re-graft with reason: "re-graft: co-resonated with [seed1, seed2]"

If candidate passes (novel + not pruned, or novel + re-graft approved):
1. Auto-write .md file to the perspective's directory
2. Store to perspective's isolated QAIS field via `perspective_store` (pass reason + session for auto-logging)
3. Add entry to seed_tracker.json

**No approval gate.** The seed is written immediately. If it doesn't belong, pruning will find it.

**Superposition logging (on auto-seed only):** When a new seed is planted in perspective A, check that seed's concept against all OTHER armed perspectives' scores from step 2. Any perspective scoring above its rain floor = uncollapsed resonance. Log as `collapsed_from: ["PerspB:0.038"]` in the new seed's tracker entry. Zero cost — scores already exist.

### 5. Prune (Requires {Enter})
Prune decisions MUST occur while the perspective is the active entity. Claude cannot judge through a perspective's ROOT lens from outside it.

During vine lifecycle under a different entity, Claude reports: "N seeds at prune window — prune evaluation requires {Enter [perspective]}" and moves on.

When the perspective IS entered, Claude reads through its ROOT lens and evaluates each eligible seed by identity alignment AND health score. State verdict and execute — do not ask the user for permission. The perspective holds its own shears.

### Resource Rules
- Vine lifecycle costs ~1,200 tokens per Sync for full pass.
- Claude should not run resonance on trivial exchanges (greetings, confirmations, counter echoes).
- Multiple armed perspectives: each runs its own full pass sequentially.

## Boundary Bypass

Seed tools (`perspective_store`, `perspective_check`, `perspective_remove`) operate at framework level during Sync step 5. This means:
- The active entity does NOT gain QAIS access through the vine pass
- The tools serve the armed perspectives directly, not the active entity
- Class tool matrix is unchanged — no entity absorbs QAIS through seed check
- This bypass applies ONLY to Sync step 5 vine lifecycle

## Seed Tracker

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

- `rain` — ambient nourishment events (score in rain band but below hit threshold)
- `last_rain` — timestamp of most recent rain event
- `collapsed_from` — which other perspectives carried uncollapsed resonance when this seed was planted (CM-MELODY superposition tracking)
- `effective_health = hits + (rain × 0.25)` — seeds need health >= 1.0 to clear prune floor

**Default tuning (set on perspective creation):**
- `seed_threshold: 0.04` — wide net, lets the entity catch patterns we wouldn't expect
- `rain_floor: auto` — computed as seed_threshold × 0.625, rounded to nearest 0.005
- `prune_window: 10` — seeds get 10 Sync exposures before pruning eligibility
- `seeding: false` — armed manually via toggle
- Each entity can override these in its own entity.json
- At 50+ seed decisions, genetic optimization becomes viable — the entity defines its own fitness function

## Decision Logging

All seed lifecycle events are logged to `data/seed_decisions.jsonl`. This is handled automatically:
- `perspective_store` logs plants (auto-seed, bootstrap, re-graft) with reason and session
- `perspective_remove` logs prunes with reason, session, and tracker stats at time of cut

No manual logging needed. The tools carry the obligation.

## Design Decisions

- **No approval gate on seeds**: Replaced by pruning. Quality lives downstream.
- **Rain not sunshine**: Sub-threshold scores nourish, don't plant. The vine gets thicker without getting longer.
- **Rain caps prevent flooding**: 1 per seed per session. Six Sync passes about UI work don't give a testing seed 6 rain ticks.
- **Effective health, not raw hits**: Prune decisions consider the full picture — sunshine, rain, and ROOT alignment. Topic neglect doesn't kill aligned seeds.
- **Superposition tracking at zero cost**: collapsed_from logs which perspectives a pattern resonated across before collapsing into one. Enables directed re-graft and perspective discovery. No new tool calls — scores already exist from Sync.
- **Dead branch log preserved**: Low cost, high value. Enables re-graft.
- **G- prefix repurposed**: Pruning journal, not growth badge.
- **Auto-seed on {Sync}**: Threshold hit → file + QAIS injection, no user prompt.
- **Germination deferred**: Seed-to-vine transformation designed but not implemented.
- **Sync execution in this file, not PROTOCOL**: The vine is one system. Design and execution are the same pipe viewed from two time axes. SKILL carries the compressed runtime reference. PROTOCOL carries the pointer. This file is the constitutional authority.

## Mantra

"The vine grows freely. The rain falls gently. The gardener only prunes."
