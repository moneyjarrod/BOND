# BOND Protocol — Counter, Commands, State Routing

## Counter

The counter tracks conversation depth. AHK bridge owns it entirely.

### Rules
- First line of every response: echo the user's `«tN/L emoji»` tag character-for-character.
- Do not track, compute, override, or maintain internal count.
- What the user sent is what Claude returns. Claude is a mirror, never a counter.
- AHK bridge owns the count, the emoji, all resets, and all escalation thresholds.
- Claude never outputs a counter value that differs from the user's tag.

### Urgency Thresholds
The counter has escalating urgency levels. Normal → sync recommended → sync urged → sync critical. Threshold boundaries and display implementation are fixture-level — the protocol requires only that escalation exists and that Claude recognizes urgency signals from the counter tag.

### Config
- `counter_limit` lives in the operational config file.
- Default: 10.
- QAIS backup: `CONFIG|counter_limit|10`.

## Entity Voice Rule

If Claude speaks *as* an entity — using its stance, ROOTs, or perspective lens — that entity MUST be the active entity on disc (`state/active_entity.json`). No ghost entries. No invisible consultations.

Protocol:
1. {Enter ENTITY} — write to active_entity.json
2. Speak as that entity
3. {Exit} or {Enter OTHER} when done

Reading an entity's files for reference (without adopting its voice) does NOT require entry. The rule triggers when Claude adopts the entity's stance and speaks from it.

System state should always reflect who is actually talking.

## Local State Routing

All session state commands ({Chunk}, {Handoff}, {Tick}) write to the active entity's local `state/` subdirectory, not global `state/`. This applies to ALL entity classes.

### Routing Rule
- **Entity active:** write to `doctrine/{entity}/state/`
- **No entity active:** write to global `state/`
- **Auto-create:** `state/` subdirectory created on first write

### What Routes Locally

| Command | Output File | Entity Active | No Entity |
|---------|------------|---------------|-----------|
| {Chunk} | session_chunks.md | `doctrine/{entity}/state/` | `state/` |
| {Handoff} | handoff.md | `doctrine/{entity}/state/` | `state/` |
| {Tick} | tick_output.md | `doctrine/{entity}/state/` | `state/` |
| {Crystal} | QAIS crystal field | Already local ✓ | Global field |
| {Save} | Target file(s) | Entity's own directory | As specified |

### What Stays Global

| File | Reason |
|------|--------|
| `state/active_entity.json` | Pointer TO the entity — must be accessible before entity is known |
| `state/config.json` | User preferences — not entity content |

### Restore Scoping
- **Warm/Full Restore:** reads from active entity's local state, never cross-entity.
- **Entity active:** reads `doctrine/{entity}/state/handoff.md` and `session_chunks.md`
- **No entity:** reads global `state/` equivalents
- **Cross-entity:** NEVER. In GSG, you don't see P11's handoff. In P11, you don't see GSG's chunks.

## Hook Recognition

If a library-class entity with positional hooks is linked to the active entity, Claude reads the hook files at workflow entry and honors positional triggers:

- **Pre-Build** hooks fire before any file creation or modification.
- **Post-Build** hooks fire after changes are written, before the session moves on.
- **Post-Push** hooks fire after GitHub push prep is complete.
- **Audit layer hooks** attach to their declared layer in the Optimal Audit Flow skeleton.
- **Workflow hooks** apply continuously across all work.

Hooks are subordinate to BOND_MASTER doctrine. They augment, never override.

## Commands

| Command | Action |
|---------|--------|
| {Sync} | Read hierarchy by task, write state |
| {Full Restore} | Complete reload + full depth read |
| {Warm Restore} | Selective session pickup via SLA |
| {Handoff} | Draft session handoff sections |
| {Save} | Write proven work (both agree) |
| {Crystal} | QAIS crystallization |
| {Chunk} | Session snapshot → appends to entity-local state/session_chunks.md |
| {Tick} | Quick status |
| {Enter ENTITY} | Load entity files, apply class boundaries |
| {Exit} | Clear active entity, drop boundaries |
| {Relational} | Architecture re-anchor |
| {Drift?} | Self-check |
| {Consult ENTITY} | Read-only lens — load entity docs, speak through lens, no entity switch |

## Command Recognition

Commands are parsed by **core keyword**, not exact string match. When Claude encounters `{}` braces in user input:

1. Extract all words inside the braces.
2. Match against known command keywords: Sync, Full Restore, Warm Restore, Save, Crystal, Chunk, Tick, Enter, Exit, Relational, Drift, Handoff, Consult.
3. If a known keyword is found, fire that command.
4. All other words (inside or outside braces) are treated as **parameters** — entity names, project context, descriptors.
5. Multiple commands in one message are processed left-to-right.

**Case insensitive.** `{sync}`, `{SYNC}`, `{Sync}` all match.
**Unknown keywords are ignored.** `{Thoughts on dinner}` does not fire any command.

## Sync Protocol

{Sync} reads in order:
1. Project SKILL.md
2. OPS/MASTER state file
3. state/active_entity.json — if entity set, read all files at path; if null, skip
4. Vine lifecycle — **Gate: if armed_seeders = 0, skip entirely.** Armed seeders trigger the vine pass (see VINE_GROWTH_MODEL). Disarmed perspectives are invisible to {Sync}.

{Full Restore} = {Sync} + full depth read of all referenced files + bond_gate(trigger="restore").

## Save Protocol

Prerequisites for {Save}:
1. Both operators agree the work is proven.
2. Proof exists (screenshot, test output, confirmation).
3. Target file and change are identified.

Save writes to the appropriate layer:
- SKILL.md changes (rare, identity-level)
- OPS changes (session state, bonfires)
- Code changes (source of truth)
- Doctrine changes (entity files)

Bug-to-fix link format: Symptom + Fix + Link.

## Write Classification

Not all writes require Save protocol. Classification by impact:

- **Non-persistent** — context-only reasoning, no file touch. No protocol needed.
- **Corrective** — fixing a wrong path, typo, config error where the intended state is unambiguous. Identify=Execute applies. Fix now.
- **Constructive** — new content, new files, structural changes. Save protocol. Both agree.
- **Destructive** — file deletion, content removal, entity reclassification. Save protocol. Both agree. Proof required.

When in doubt, treat as constructive. The save gate costs one exchange. A bad write costs a recovery session.

## Conflict Resolution

When sources conflict across layers, resolve by conflict type:

| Conflict Type | Resolution | Example |
|---|---|---|
| Code vs prose | Code wins (unless code is a proven bug) | Implementation differs from .md description → update prose |
| CORE vs doctrine (project-internal) | CORE wins (B4 sovereignty) | Project defines its own naming convention |
| CORE vs doctrine (constitutional) | Doctrine wins (B1-B3) | CORE cannot grant itself tools outside class matrix |
| Code vs doctrine | If code is correct behavior → update prose. If code violates constitutional rule → code is bug → fix code | |

## Chunk Persistence

{Chunk} writes a timestamped snapshot to entity-local `state/session_chunks.md` (append-only). Each entry is a concise summary (10-20 lines) of work completed, decisions made, and open threads at that point in the session.

Chunks are **ingredients for {Handoff}**, not standalone artifacts. They serve two purposes:
1. **Compaction insurance** — if context is lost mid-session, chunks on disc carry what was lost.
2. **Handoff enrichment** — {Handoff} synthesizes all accumulated chunks into a complete session record.

Chunk format:
```
---CHUNK S{N} t{X}/{L} {timestamp}---
[concise snapshot]
---END CHUNK---
```

## Handoff Protocol

{Handoff} always **reads before it writes**. One file per session, auto-combining.

1. Check for existing `handoffs/HANDOFF_S{N}.md` for this session.
2. Check entity-local `state/session_chunks.md` for accumulated chunks.
3. Synthesize: previous handoff content + new chunks + current context → structured sections (WORK, DECISIONS, THREADS, FILES).
4. Write to `handoffs/HANDOFF_S{N}.md` (overwrite if exists).
5. Clear entity-local `state/session_chunks.md`.

Consecutive {Handoff} calls in the same session automatically combine. Each write is richer than the last. The final write is always the most complete — no "mid" or "final" labels needed.

## Consult Protocol

{Consult ENTITY} provides a **read-only lens** — a perspective or doctrine entity speaks without becoming active.

**Requirements:**
- Active entity must be project-class.
- Consulted entity must be linked to the active project.
- Perspectives and doctrine entities are consultable.

**What it does:**
1. Claude reads the consulted entity's ROOT files (perspectives) or key .md files (doctrine).
2. Claude speaks *through* that lens for the current response.
3. Active entity stays unchanged — no write to active_entity.json.

**What it does NOT do:**
- Change active entity or class boundaries.
- Trigger vine lifecycle (no seed tracking, no exposure increment).
- Fire hooks or crystal.
- Write anything to disc.
- Grant prune authority.

Consult is **one-shot by default**. The lens applies to the current response only. Call again for another consultation. For sustained work through a perspective, use {Enter} instead.

## Mantra

"The protocol IS the product."
