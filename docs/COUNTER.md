# BOND Counter Specification

## Purpose

Context degrades over conversation length. The counter makes this visible.

## Format

```
«tN/L emoji»
```

- **N** = current count (user messages since last reset)
- **L** = sync limit (default 10)
- **emoji** = user's chosen status indicator

## Rules

1. **First line, every response.** No exceptions.
2. **Echo the user's tag exactly.** Do not compute emoji independently.
3. **User display is source of truth.** If user says `«t5/10 🗒️»`, that's the count.

## What Counts

| Event | Counts? |
|-------|---------|
| User message | ✅ Yes |
| User command ({Sync}, {Save}, etc.) | ✅ Yes |
| Claude's response | ❌ No |
| Claude's tool calls | ❌ No |
| Context compaction | ❌ No |

## Resets

| Event | Resets counter? |
|-------|----------------|
| `{Sync}` | ✅ Yes |
| `{Full Restore}` | ✅ Yes |
| New conversation | ✅ Yes |
| `{Save}` | ❌ No |
| `{Chunk}` | ❌ No |
| `{Warm Restore}` | ❌ No |
| `{Handoff}` | ❌ No |
| Task completion | ❌ No |
| Compaction | ❌ No |

## Status Indicators

Users choose their own emoji. Common patterns:

| Emoji | Meaning |
|-------|---------|
| 🗒️ | Normal operation |
| 🟡 | Past sync limit |
| 🟠 | Context degrading |
| 🔴 | Critical — sync immediately |

## Recovery

If count is lost (compaction, confusion), recommend `{Sync}` to reset cleanly.

## AHK Bridge Integration

The optional AHK Bridge script (`BOND_v8.ahk`) provides a hotkey-driven counter that automatically tags messages on Enter and relays panel commands via clipboard. See the `Counter/` directory for setup.
