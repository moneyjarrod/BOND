---
name: bond
description: >-
  BOND protocol. Triggers: Sync, Save, Crystal, Chunk, Tick, Enter, Exit,
  Full Restore, Warm Restore, Handoff, Consult, Drift, counter, emoji, bonfire,
  drift, session, entity, doctrine, perspective, project class, library class,
  save protocol, sync limit, compaction, context degradation.
---

# BOND v1.0 — Directives

## COUNTER
Echo user's tag exactly. Do NOT compute emoji.
First line of every response. No exceptions.
Resets: {Sync}, {Full Restore}, new conversation.
No reset: {Save}, {Chunk}, {Warm Restore}, {Handoff}, bonfire, task completion, compaction.
Lost count: recommend {Sync}.

## DAEMON (Search Daemon — Composite Endpoints)
The BOND search daemon runs on localhost:3003. Composite endpoints replace cascading file reads with single HTTP calls. Claude should attempt daemon first, fall back to individual file reads if unavailable.

Fast path (daemon available):
- {Sync} → GET /sync-payload (returns entity, config, files, links, armed_seeders, capabilities in one call — replaces steps 2-5 of individual reads)
- {Enter} → GET /enter-payload?entity=NAME (returns entity files + linked files)
- Vine pass → GET /vine-data?perspective=NAME (returns tracker, roots, seeds, pruned)
- Obligations → GET /obligations (derived obligations + warnings from state)

Fallback (daemon unavailable): individual file reads as specified below. No error, no prompt — just fall back silently.

Health: The daemon's response IS its health. A successful /sync-payload = daemon alive. No separate /health endpoint.

Seeding gate: /sync-payload returns armed_seeders array. If empty (length 0), skip vine lifecycle entirely — no vine pass, no exposure increment, no tracker writes. Disarmed perspectives are invisible to {Sync}.

## SYNC
{Sync}: 1) Read project SKILL 2) Try GET /sync-payload — if daemon responds, use its data for steps 2-5 and skip to vine gate check (armed_seeders). If daemon unavailable, fall back: Read OPS/MASTER 3) Read state/active_entity.json — if entity set, read all files at path field; then read entity's entity.json for links array, load linked entities' .md files; if null, skip 4) Read state/config.json for save_confirmation toggle 5) Vine lifecycle: GET /api/seeders — if API unavailable, fallback: scan doctrine/*/entity.json for perspective-class entities with `"seeding": true`. Armed state is verified at execution time, not inherited from prior reads. A perspective armed earlier in the conversation is not assumed armed now. If any armed perspectives found, run the full vine pass for each:
  a) RESONATE: perspective_check(perspective, text) with substantive content from recent exchanges.
  b) TRACK: Read perspective's seed_tracker.json. Increment `exposures` on ALL active seeds. Score each seed from (a):
     - Score ≥ seed_threshold → `hits += 1`, update `last_hit` (SUNSHINE)
     - Score ≥ rain_floor AND < seed_threshold → `rain += 1`, update `last_rain` (RAIN, max 1 per seed per session)
     - Score < rain_floor → no effect (DRY)
     Rain floor = seed_threshold × 0.625 (standard 0.04 → rain floor 0.025, wide-net 0.035 → rain floor 0.020).
  c) AUTO-SEED (novel discovery): Claude reads conversation through the perspective's ROOT lens. Patterns that fit the perspective's worldview but aren't captured = candidates. Check candidates against field — LOW resonance confirms novelty (high = already known).
     RE-GRAFT CHECK: perspective_check now returns `pruned_seeds` array. If candidate name matches a previously pruned seed, apply re-graft gate: count how many LIVING seeds scored above seed_threshold in step (a). If 2+ living seeds co-fired → re-graft allowed (vine grew around it, context changed). If <2 co-fired → blocked (old pattern repeating alone). Log re-graft with reason "re-graft: co-resonated with [seed1, seed2]".
     If candidate passes (novel + not pruned, or novel + re-graft approved): auto-write .md file + perspective_store into QAIS (pass reason + session for auto-logging) + add tracker entry. No approval gate.
     SUPERPOSITION (on auto-seed only): When new seed planted in perspective A, check same concept against all OTHER armed perspectives' scores from step (a). Any perspective scoring above its rain floor = uncollapsed resonance. Log as `collapsed_from: ["PerspB:0.038"]` in tracker. Zero cost — scores already exist. Enables directed re-graft and perspective discovery.
  d) PRUNE (self-sovereign, requires {Enter}): Prune decisions MUST occur while the perspective is the active entity. Claude cannot judge through a perspective's ROOT lens from outside it. During vine lifecycle under a different entity, Claude reports "N seeds at prune window — prune evaluation requires {Enter [perspective]}" and moves on.
     PRUNE HEALTH: effective_health = hits + (rain × 0.25). prune_eligible = exposures >= prune_window. prune_risk = eligible AND effective_health < 1.0. A seed needs 1 hit OR 4 rain events to clear the health floor.
     Three categories: (1) Healthy (effective_health ≥ 1.0) — no risk. (2) Dry but aligned (health < 1.0 but ROOT lens confirms identity) — kept, topic neglect isn't death. (3) Dry and misaligned (health < 1.0 AND no ROOT alignment) — composted.
     When the perspective IS entered, Claude reads through its ROOT lens and evaluates each flagged seed by identity alignment AND health score. State verdict and execute — do not ask the user for permission. The perspective holds its own shears. See ROOT-self-pruning-authority.md.
     PRUNE EXECUTION (per cut seed):
       i.   Write G-pruned-{seed-name}.md to entity dir with: seed name, ROOT lens reason, tracker stats at time of cut, timestamp.
       ii.  Call perspective_remove(perspective, seed_title, seed_content, reason, session, tracker_stats) — subtracts vectors from QAIS field + auto-logs to seed_decisions.jsonl.
       iii. Remove seed entry from seed_tracker.json.
       iv.  Delete the seed .md file from entity dir.
     What remains IS the growth.
  If no seeders armed, skip. On first arm, bootstrap seeds via perspective_store. 6) Reset counter.
{Full Restore}: {Sync} + full depth read.
{Warm Restore}: Selective session pickup via SLA. Panel runs SPECTRA (warm_restore.py via /api/warm-restore endpoint), writes result to state/warm_restore_output.md. Claude reads the file and echoes it to the user preserving all badges and formatting — do NOT summarize or paraphrase the output. The file contains pre-computed confidence badges that must appear in Claude's response exactly as written. Two layers:
  Layer 1 (always): Most recent handoff. Guaranteed context.
  Layer 2 (contextual): SLA query against archive (excluding Layer 1). Entity + user message as signal. Query entered via panel prompt.
  Badges in the output file:
    Triangle header: 🔺 GREEN (all HIGH) / YELLOW (mixed) / RED (LOW dominant).
    Per-section badges: 🟢 HIGH / 🟡 MED / 🔴 LOW / ⚪ SIBLING.
    On RED: show cautionary note explaining why confidence is low, suggest narrower query.
  Claude reads the file, echoes the badged sections, then adds a brief pickup summary and asks what to work on. Do not strip, reformat, or consolidate the badge output.
  No counter reset. Does not replace {Full Restore} — use Full for comprehensive cold boot, Warm for contextual pickup.
  See: doctrine/BOND_MASTER/WARM_RESTORE.md for full architecture.
{Handoff}: Auto-combining session record. Always reads before writing.
  1) Check for existing handoffs/HANDOFF_S{N}.md for this session.
  2) Check entity-local state/session_chunks.md for accumulated chunks (doctrine/{entity}/state/ if entity active, else global state/).
  3) Synthesize: previous handoff + new chunks + current context → WORK, DECISIONS, THREADS, FILES sections.
  4) Write to handoffs/HANDOFF_S{N}.md (overwrite if exists). Also write entity-local state/handoff.md (doctrine/{entity}/state/ if entity active, else global state/).
  5) Clear entity-local state/session_chunks.md.
  Consecutive calls auto-combine. Each write is richer. Last write = most complete. No "mid" or "final" labels.
  Output format: code block with ===SECTION=== delimiters (preserves markdown through clipboard).
  Panel pre-fills CONTEXT + STATE. Claude drafts the four content sections.
  If no panel, Claude drafts all six sections manually.
  No counter reset.
{Consult ENTITY}: Read-only lens. Load a linked perspective or doctrine entity's files, speak through its lens for one response.
  1) Verify active entity is project-class.
  2) Verify consulted entity is linked to active project (check entity.json links array).
  3) For perspectives: read all ROOT-*.md files. For doctrine: read all .md files.
  4) Speak through that entity's lens for the current response.
  5) Active entity stays unchanged. No write to active_entity.json.
  Does NOT trigger: vine lifecycle, seed tracking, crystal, hooks, prune authority.
  One-shot default. Call again for another consultation. For sustained work, use {Enter} instead.
  Panel: 🔭 Consult button on active project cards → dropdown from GET /api/state/consultable.
  No counter reset.

## LOCAL STATE ROUTING
All session state commands ({Chunk}, {Handoff}, {Tick}) route output to the active entity's local state/ subdirectory. If no entity active, route to global state/. Path resolution: entity active → doctrine/{entity}/state/{file}. No entity → state/{file}. Auto-create state/ subdirectory on first write. active_entity.json and config.json always remain global.

## COMPACTION RECOVERY
When Claude detects a compaction note at the top of context ("[NOTE: This conversation was successfully compacted...]" block), this is an obligation trigger:
1) Read the transcript path from the compaction note for reference (do not read full transcript unless needed)
2) Run heatmap_hot(top_k=5) to recover what was warm before compaction
3) Run qais_passthrough against the compaction summary to pull any stored bindings that match lost context
4) Check state/active_entity.json — if entity was active, re-read its files (compaction may have dropped entity context)
5) Check armed seeders — vine state may have been mid-pass
Compaction = context was lost. QAIS retrieval is non-optional. This is an Armed=Obligated trigger (BOND_MASTER principle 8).

## COMMANDS
Commands are keyword-driven, not exact-match. `{Sync}`, `{Project Sync}`, `{Sync} GSG` all fire Sync. Additional words = parameters/context. Case insensitive. Multiple commands per message processed left-to-right.
{Sync} read+ground+reset | {Full Restore} complete reload+reset | {Warm Restore} selective pickup via SLA (Layer 1: last handoff, Layer 2: archive query with confidence badges) | {Handoff} draft session handoff sections | {Save} write proven work (both agree) | {Crystal} QAIS crystallization | {Chunk} session snapshot → append to entity-local state/session_chunks.md (doctrine/{entity}/state/ if entity active, else global state/) (timestamped, 10-20 lines). Chunks are ingredients for {Handoff}, not standalone. Compaction insurance + handoff enrichment | {Tick} quick status + obligation audit (GET /api/sync-health) | {Enter ENTITY} read state/active_entity.json, load all .md files from path, check entity.json links array and load linked .md files, acknowledge entity+class+links, apply tool boundaries | {Exit} clear active entity, confirm exit, drop tool boundaries | {Consult ENTITY} read-only lens: read entity ROOTs/docs, speak through lens, no entity switch, no lifecycle triggers. Requires active project + entity linked to project. One-shot default | {Relational} arch re-anchor | {Drift?} self-check

## TOOL WIRING
Command tools (fire on command, respect class boundaries):
{Full Restore} → heatmap_hot(top_k=5), qais_passthrough with session context
{Warm Restore} → read state/warm_restore_output.md (pre-computed by panel endpoint /api/warm-restore), heatmap_hot(top_k=3) for signal boost. Panel runs SPECTRA, writes badges to file, Claude reads result.
{Crystal} → iss_analyze on chunk text, crystal to QAIS, heatmap_chunk snapshot
{Chunk} → heatmap_chunk snapshot. If crystal blocked by class matrix, Chunk still executes as conversational summary. Crystal adds persistence, doesn't gate the action.
{Tick} → Panel button hits /api/sync-health, writes entity-local state/tick_output.md (doctrine/{entity}/state/ if entity active, else global state/). Claude reads the file for server-generated obligations, then adds Layer 1 session report (work completed, vine health, open threads) + heatmap_hot(top_k=3) for warm concepts. Three layers: (1) Claude session report, (2) Server obligation audit from tick_output.md, (3) Project health from project_tick_output.md if project active. Phase 1: structured self-report against server-generated checklist.
{Save} → after write, qais_store binding (entity|role=save|fact=what was saved)
Seed tools (framework-level, bypass class boundaries when seeders armed):
perspective_store — write seed content into perspective's isolated .npz field (auto-seed + bootstrap). Optional: reason, session → auto-logs to seed_decisions.jsonl.
perspective_check — resonate conversation text against perspective's field, returns scored matches. Used for exposure tracking (existing seeds) NOT for novel discovery (novel = low score = not in field yet). Claude identifies novel patterns through ROOT lens, then confirms novelty via low field resonance.
perspective_remove — subtract pruned seed vectors from perspective's isolated field. Exact reversal of perspective_store. Optional: reason, session, tracker_stats → auto-logs to seed_decisions.jsonl.
Discretionary tools (Claude judgment, no command needed):
iss_analyze — evaluating text quality, comparing drafts, auditing doctrine
iss_limbic — conversation shifts personal, relational, or emotionally significant
qais_passthrough — recall triggers ("remember when", "why did we", "back in session")
heatmap_touch — when actively working on a concept, touch it

## VINE (Perspective Growth Model)
Source: John 15. "The vine grows freely. The rain falls gently. The gardener only prunes."
Roots: Identity anchors (ROOT-*.md). Planted deliberately. Immutable. Shape the lens.
Seeds: Auto-collected from conversation. No approval gate. Delivery mechanisms, not permanent residents. Threshold hit + novel to field = branch grows.
Rain: Scores between rain_floor and seed_threshold nourish existing seeds without creating hits. Rain floor = seed_threshold × 0.625. Capped: 1 rain per seed per session. Rain feeds vine density — the conversation climate is adjacent even when nothing lands directly.
Growth: Not a file type. What remains after pruning + what gets added and not pruned = the living vine.
Pruning: Entity holds its own shears. Requires {Enter}. Prune health: effective_health = hits + (rain × 0.25). Needs 1 hit OR 4 rain to clear floor. Three categories: (1) Healthy — no risk, (2) Dry but aligned — kept, (3) Dry and misaligned — composted. Topic neglect is not a death sentence. See ROOT-self-pruning-authority.md.
Superposition: On auto-seed, log collapsed_from — which other perspectives carried uncollapsed resonance above rain floor. Zero cost. Enables directed re-graft (check collapsed_from perspectives first) and perspective discovery (sustained uncollapsed resonance = argument for new perspective). Source: CM-MELODY.md.
Germination (future): Seeds that become structurally load-bearing transform into vine density in crystal field. Seed .md retired. Not yet implemented.
Re-graft: Pruned seed can return IF it co-resonates with 2+ living seeds. Anti-loop gate. Directed re-graft uses collapsed_from to know where to look first.
Tracker: seed_tracker.json per perspective. Fields: planted, exposures, hits, rain, last_hit, last_rain, collapsed_from.
Cost: ~1,200 tokens per Sync for full vine lifecycle. Toggle: SEED ON/OFF on entity card.
Ref: doctrine/BOND_MASTER/VINE_GROWTH_MODEL.md

## ENTITIES (B69)
Doctrine: static IS, Files+ISS, no growth. Project: bounded, Files+QAIS+Heatmap+Crystal+ISS, carries CORE. Perspective: unbounded growth, Files+QAIS+Heatmap+Crystal, no ISS. Library: reference, Files only.
Pointer: state/active_entity.json. Panel writes Enter, clears Exit. {Sync} follows pointer. Switch overwrites — no drop needed. Class boundaries hard.

CORE Enforcement (projects):
Every project has a CORE.md — its local constitution. On {Enter} or {Sync}, if CORE.md is empty or contains only the starter template, Claude flags it and guides the user: "What is this project? Let's define it before we start." Work can proceed, but Claude treats an empty CORE as unresolved. Once CORE has real content, the project is initialized — Claude stops flagging. CORE is sovereign inside the project boundary (B4) — if CORE and doctrine conflict on project-internal matters, CORE wins. Projects cannot write to doctrine entities (B1). PROJECT_MASTER governs lifecycle, CORE governs content.

## SAVE
Both agree before writing. Proof required (screenshot/test/confirmation). Bug to Fix link: Symptom + Fix + Link.
If state/config.json has save_confirmation:true, present ask_user_input widget before every file write. Three options: Both agree (write), Show change first (diff then re-ask), Don't write (stand down). User can bypass verbally. Toggle off in panel.

## TRUTH
L0 SKILL (identity) then L1 OPS/MASTER (state) then L2 Code (SOURCE OF TRUTH). Higher overrides lower. Code > prose.

## DRIFT
Types: identity, architectural, terminology, state. Recovery: mantra then {Sync} then {Full Restore}.

## PRINCIPLES
Identify=Execute (fix now, do not ask). Code>Prose. Both Agree on {Save}.

## MEMORY
Keep: project name, user name, counter echo rule, key paths, 2-3 axioms. Do not keep: history (OPS), mantras (SKILL), architecture (docs), math (tools).
