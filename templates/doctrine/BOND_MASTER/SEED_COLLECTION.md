# Seed Collection — Perspective Growth Protocol

## What This IS

Seed collection is the mechanism by which perspectives grow. When a perspective is armed (seeding: true), the vine lifecycle runs during every {Sync}. Seeds auto-write with no approval gate. Quality lives downstream in pruning.

## How It Works

### 1. Check Armed Perspectives
During {Sync} step 5, Claude checks for armed perspectives (entities with `"seeding": true` in entity.json). If none are armed, skip silently.

### 2. Resonate
For each armed perspective, run `perspective_check(perspective, text)` with substantive content from recent exchanges. This scores all existing seeds against the conversation.

### 3. Track
Read the perspective's `seed_tracker.json`. Increment `exposures` on ALL active seeds. Seeds that scored above the entity's `seed_threshold` get `hits += 1` and `last_hit` updated with context.

### 4. Auto-Seed (Novel Discovery)
Claude reads conversation through the perspective's ROOT lens. Patterns that fit the perspective's worldview but aren't captured by existing seeds = candidates.

Check candidates against the field — **LOW resonance confirms novelty** (high score = already known). This is the inverse of tracking: tracking looks for what's familiar, auto-seed looks for what's new.

If candidate passes novelty check:
1. Auto-write `.md` file to the perspective's directory
2. Store to perspective's isolated QAIS field via `perspective_store` (pass reason + session for auto-logging to `seed_decisions.jsonl`)
3. Add entry to `seed_tracker.json`

**No approval gate.** The seed is written immediately. If it doesn't belong, pruning will find it.

### 5. Re-Graft Check
Before writing any auto-seed, check the pruning log. `perspective_check` returns a `pruned_seeds` array. If a candidate name matches a previously pruned seed:

- Count how many LIVING seeds scored above `seed_threshold` in step 2
- If **2+ living seeds co-fired** → re-graft allowed (vine grew around it, context changed)
- If **<2 co-fired** → blocked (old pattern repeating alone)
- Log re-graft with reason: "re-graft: co-resonated with [seed1, seed2]"

This prevents the prune/collect infinite loop. Process rule, not content rule.

### 6. Prune (Requires {Enter})
Prune decisions MUST occur while the perspective is the active entity. Claude cannot judge through a perspective's ROOT lens from outside it.

During vine lifecycle under a different entity, Claude reports: "N seeds at prune window — prune evaluation requires {Enter [perspective]}" and moves on.

When the perspective IS entered, Claude reads through its ROOT lens and evaluates each eligible seed by identity alignment, not hit count. The tracker is evidence, not verdict. Ask: does this seed grow from who this perspective IS?

State verdict and execute — do not ask the user for permission. The perspective holds its own shears. See ROOT-self-pruning-authority.md.

**Prune execution (per cut seed):**
1. Write `G-pruned-{seed-name}.md` with ROOT lens reason + tracker stats + timestamp
2. Call `perspective_remove` — subtracts vectors from QAIS field + auto-logs to `seed_decisions.jsonl`
3. Remove entry from `seed_tracker.json`
4. Delete the seed `.md` file

What remains IS the growth.

## Decision Logging

All seed lifecycle events are logged to `data/seed_decisions.jsonl`. This is handled automatically:
- `perspective_store` logs plants (auto-seed, bootstrap, re-graft) with reason and session
- `perspective_remove` logs prunes with reason, session, and tracker stats at time of cut

No manual logging needed. The tools carry the obligation.

## Resource Rules

- Vine lifecycle costs ~1,200 tokens per Sync for full pass
- Claude should not run resonance on trivial exchanges (greetings, confirmations, counter echoes)
- Multiple armed perspectives: each runs its own full pass sequentially

## Boundary Bypass

Seed tools (`perspective_store`, `perspective_check`, `perspective_remove`) operate at framework level during Sync step 5. This means:
- The active entity does NOT gain QAIS access
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
    "last_hit": null
  }
}
```

Default tuning (set on perspective creation):
- `seed_threshold: 0.04` — wide net, lets the entity catch patterns we wouldn't expect
- `prune_window: 10` — seeds get 10 Sync exposures before pruning eligibility
- `seeding: false` — armed manually via panel toggle (SEED ON/OFF)
- Each entity can override these in its own `entity.json`

## Phase 2: Genetic Optimization

After sufficient seed lifecycle data accumulates in `seed_decisions.jsonl`, genetic optimization becomes viable for:
- Score threshold tuning per perspective
- Prune window calibration
- Candidate construction (ROOT lens patterns vs. keyword matching)
- Multi-perspective weighting when several are armed simultaneously

The decision log carries plant reasons, prune reasons, tracker stats at time of cut, and session context — enough signal for the entity to define its own fitness function.

## Mantra

"Seeds grow where attention falls. The vine grows freely. The gardener only prunes."
