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
| `{Tick}` | Quick status check. Where are we? | No reset |

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

## Command Flow

```
Session Start → {Full Restore} or {Sync}
                (or {Warm Restore} for targeted pickup)
Work naturally → counter tracks context age
Every ~10 messages → {Sync} to refresh
Before big changes → {Save} with proof
Session end → {Handoff} to preserve
```

## Warm Restore vs Full Restore

- **{Full Restore}** — Cold boot. Reads everything from scratch. Use when starting fresh or deeply lost.
- **{Warm Restore}** — Contextual pickup. Panel runs SPECTRA ranking against handoff archive, returns the most relevant sections with confidence badges. Use when resuming specific work.

Warm Restore has two layers:
- Layer 1: Most recent handoff (always included)
- Layer 2: SLA query against archive with confidence scoring (🟢 HIGH / 🟡 MED / 🔴 LOW)

## Bridge Protocol

Commands flow through clipboard: Panel button click → copies `BOND:{command}` → AHK OnClipboardChange → types into Claude.

The Command Bar at the bottom of the Control Panel provides one-click access to all core commands.
