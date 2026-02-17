# BOND Protocol — Counter, Bridge, Commands

## Counter

The counter tracks conversation depth. It IS the sync timer.

### Rules
- User provides the counter tag: `«tN/L emoji»`
- Claude echoes the user's tag exactly as first line of every response.
- Claude does NOT compute the emoji. User display is source of truth.
- Resets on: {Sync}, {Full Restore}, new conversation.
- Does NOT reset on: {Save}, {Chunk}, bonfire, task completion, compaction.
- Lost count → recommend {Sync}.

### Emoji Thresholds (computed by AHK, not Claude)
- 🗒️ = N ≤ LIMIT (normal)
- 🟡 = N > LIMIT (sync recommended)
- 🟠 = N ≥ 15 (sync urged)
- 🔴 = N ≥ 20 (sync critical)

### Config
- `counter_limit` lives in project OPS CONFIG section.
- Default: 10.
- QAIS backup: `CONFIG|counter_limit|10`.

## Bridge Architecture

### Flow
```
Panel Button → clipboard write → AHK monitor → keystroke injection → Claude
Claude response → user reads → panel state updated via API
```

### Implementation
- Panel writes `BOND:command:args` to clipboard.
- AHK monitors clipboard, parses BOND: prefix.
- AHK types the command into the active Claude window.
- No HTTP polling. No websockets. Clipboard is the bridge.

### Why Clipboard
- HTTP polling caused 500ms lag spikes.
- Clipboard is event-driven, zero polling overhead.
- AHK already runs for counter — no new dependency.

## Entity Voice Rule

If Claude speaks *as* an entity — using its stance, ROOTs, or perspective lens — that entity MUST be the active entity on disc (`state/active_entity.json`). No ghost entries. No invisible consultations.

Protocol:
1. {Enter ENTITY} — write to active_entity.json, panel reflects it
2. Speak as that entity
3. {Exit} or {Enter OTHER} when done — panel updates accordingly

Reading an entity's files for reference (without adopting its voice) does NOT require entry. The rule triggers when Claude adopts the entity's stance and speaks from it.

The panel should always reflect who is actually talking.

## Hook Recognition

If a library-class entity with positional hooks (BUILD_HOOKS, AUDIT_HOOKS, WORKFLOW_HOOKS) is linked to the active entity, Claude reads the hook files at workflow entry and honors positional triggers:

- **Pre-Build** hooks fire before any file creation or modification.
- **Post-Build** hooks fire after changes are written, before the session moves on.
- **Post-Push** hooks fire after GitHub push prep is complete.
- **Audit layer hooks** attach to their declared layer in the Optimal Audit Flow skeleton.
- **Workflow hooks** apply continuously across all work.

Hooks are subordinate to BOND_MASTER doctrine. They augment, never override.

## Commands

| Command | Action | Resets Counter |
|---------|--------|---------------|
| {Sync} | Read hierarchy by task, write state | Yes |
| {Full Restore} | Complete reload + full depth read | Yes |
| {Save} | Write proven work (both agree) | No |
| {Crystal} | QAIS crystallization | No |
| {Chunk} | Session snapshot → appends to state/session_chunks.md | No |
| {Tick} | Quick status | No |
| {Enter ENTITY} | Load entity files, apply class boundaries | No |
| {Exit} | Clear active entity, drop boundaries | No |
| {Relational} | Architecture re-anchor | No |
| {Drift?} | Self-check | No |

## Command Recognition

Commands are parsed by **core keyword**, not exact string match. When Claude encounters `{}` braces in user input:

1. Extract all words inside the braces.
2. Match against known command keywords: Sync, Full Restore, Warm Restore, Save, Crystal, Chunk, Tick, Enter, Exit, Relational, Drift, Handoff.
3. If a known keyword is found, fire that command.
4. All other words (inside or outside braces) are treated as **parameters** — entity names, project context, descriptors.
5. Multiple commands in one message are processed left-to-right.

**Examples:**
- `{Sync}` → fires Sync
- `{Sync} GSG` → fires Sync, "GSG" is context
- `{Project Sync} GSG` → fires Sync, "Project" and "GSG" are context
- `{Project Chunk} GSG{Project Sync} GSG` → fires Chunk then Sync
- `{Enter BOND_MASTER}` → fires Enter, "BOND_MASTER" is the entity parameter

**Case insensitive.** `{sync}`, `{SYNC}`, `{Sync}` all match.

**Unknown keywords are ignored.** `{Thoughts on dinner}` does not fire any command.

## Sync Protocol

{Sync} reads in order:
1. Project SKILL.md
2. OPS/MASTER state file
3. state/active_entity.json — if entity set, read all files at path; if null, skip
4. Seed check — Scan doctrine/ for perspective entities with `"seeding": true` in entity.json. For each armed perspective, collect seed file titles and run `qais_passthrough` against recent conversation context. Report any hits. If no armed seeders, skip silently.
5. Reset counter

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

## Chunk Persistence

{Chunk} writes a timestamped snapshot to `state/session_chunks.md` (append-only). Each entry is a concise summary (10-20 lines) of work completed, decisions made, and open threads at that point in the session.

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
2. Check `state/session_chunks.md` for accumulated chunks.
3. Synthesize: previous handoff content + new chunks + current context → structured sections (WORK, DECISIONS, THREADS, FILES).
4. Write to `handoffs/HANDOFF_S{N}.md` (overwrite if exists).
5. Clear `state/session_chunks.md`.

Consecutive {Handoff} calls in the same session automatically combine. Each write is richer than the last. The final write is always the most complete — no "mid" or "final" labels needed.

```
{Chunk} t3  → session_chunks.md
{Chunk} t7  → session_chunks.md
{Handoff} t10 → reads chunks → writes HANDOFF_S119.md → clears chunks
{Chunk} t14 → session_chunks.md
{Handoff} t20 → reads HANDOFF_S119.md + chunks → overwrites HANDOFF_S119.md → clears chunks
```

{Warm Restore} Layer 1 picks up the one file. Everything synthesized. Nothing lost.
