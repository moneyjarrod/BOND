# BOND Commands Reference

## Core Commands

| Command | Action | Counter |
|---------|--------|---------|
| `{Sync}` | Read SKILL → OPS → active entity → seed check → ground in truth. | **Resets** |
| `{Full Restore}` | Complete reload. SKILL + OPS + entity + full depth. | **Resets** |
| `{Warm Restore}` | Selective pickup via SLA. Panel runs SPECTRA, Claude reads result. | No reset |
| `{Handoff}` | Draft end-of-session summary (WORK, DECISIONS, THREADS, FILES). | No reset |
| `{Save}` | Write proven work. Both must agree. | No reset |
| `{Crystal}` | QAIS crystallization — store session concepts. | No reset |
| `{Chunk}` | Session snapshot. | No reset |
| `{Tick}` | Obligation audit. Server generates obligations from state, Claude verifies each was serviced. Gaps surface structurally. | No reset |

## Entity Commands

| Command | Action |
|---------|--------|
| `{Enter ENTITY}` | Load entity files, apply class tool boundaries, load linked entities. |
| `{Exit}` | Clear active entity, drop tool boundaries. |

## Recovery Commands

| Command | Action |
|---------|--------|
| `{Drift?}` | Self-check. Am I drifting from truth? |
| `{Relational}` | Re-anchor relational architecture. |

## Sync Procedure

`{Sync}` reads in order:
1. Project SKILL.md
2. OPS/MASTER state file
3. `state/active_entity.json` — if entity set, read all files at path; if null, skip
4. **Seed check** — Scan `doctrine/` for perspective entities with `"seeding": true` in `entity.json`. For each armed perspective, collect seed file titles and run `qais_passthrough` against recent conversation context. Report any hits. If no armed seeders, skip silently.
5. Reset counter

`{Full Restore}` = `{Sync}` + full depth read of all referenced files.

## Tick Procedure

`{Tick}` reads `/api/sync-obligations` or `/api/sync-health` from the panel server. The server derives obligations from current state:

- **Active entity** — all .md files must be loaded
- **Linked entities** — linked entity files must be loaded
- **Armed perspectives** — vine lifecycle (perspective_check, tracker update, prune evaluation, auto-seed scan) must run
- **Config flags** — save_confirmation ON means ask_user_input widget required before writes

Claude checks each obligation against what was actually done during the session and reports status. Gaps are surfaced as structural misses, not self-reported.

## Command Flow

```
Session Start → {Full Restore} or {Sync}
                (or {Warm Restore} for targeted pickup)
Work naturally → counter tracks context age
Every ~10 messages → {Sync} to refresh (this is critical — see below)
Before big changes → {Save} with proof
Session end → {Handoff} to preserve
```

> **⚠️ Why every 10 messages?** Claude's grounding in doctrine, entity files, and truth hierarchy actively degrades over conversation length. Without sync, Claude drifts — losing entity awareness, skipping obligations, and making decisions from stale context. The counter isn't a suggestion, it's the immune system. **[Full explanation →](COUNTER.md)**

## Warm Restore vs Full Restore

- **{Full Restore}** — Cold boot. Reads everything from scratch. Use when starting fresh or deeply lost.
- **{Warm Restore}** — Contextual pickup. Panel runs SPECTRA ranking against handoff archive, returns the most relevant sections with confidence badges. Use when resuming specific work.

Warm Restore has two layers:
- Layer 1: Most recent handoff (always included)
- Layer 2: SLA query against archive with confidence scoring (🟢 HIGH / 🟡 MED / 🔴 LOW)

## Bridge Protocol

Commands flow through clipboard: Panel button click → copies `BOND:{command}` → AHK OnClipboardChange → types into Claude.

The Command Bar at the bottom of the Control Panel provides one-click access to all core commands.
