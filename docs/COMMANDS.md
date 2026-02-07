# BOND Commands Reference

## Core Commands

| Command | Action | Counter |
|---------|--------|---------|
| `{Sync}` | Read SKILL → OPS → active entity. Ground in truth. | **Resets** |
| `{Full Restore}` | Complete reload. SKILL + OPS + entity + full depth. | **Resets** |
| `{Save}` | Write proven work. Both must agree. | No reset |
| `{Crystal}` | QAIS crystallization — store session concepts. | No reset |
| `{Chunk}` | Session snapshot — handoff file + crystal. | No reset |
| `{Tick}` | Quick status check. Where are we? | No reset |

## Entity Commands

| Command | Action |
|---------|--------|
| `{Enter ENTITY}` | Load entity files, apply class tool boundaries. |
| `{Exit}` | Clear active entity, drop tool boundaries. |

## Recovery Commands

| Command | Action |
|---------|--------|
| `{Drift?}` | Self-check. Am I drifting from truth? |
| `{Relational}` | Re-anchor relational architecture. |

## Command Flow

```
Session Start → {Full Restore} or {Sync}
Work naturally → counter tracks context age
Every ~10 messages → {Sync} to refresh
Before big changes → {Save} with proof
Session end → {Chunk} to preserve
```

## Bridge Protocol

Commands flow through clipboard: Panel button click → copies `BOND:{command}` → AHK OnClipboardChange → pastes into Claude.

The Command Bar at the bottom of the Control Panel provides one-click access to all core commands.
