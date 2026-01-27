# BOND Commands Reference

## Core Commands

| Command | When | What It Does |
|---------|------|--------------|
| `{Sync}` | Every ~10 messages | Claude reads your files, re-grounds in truth |
| `{Save}` | After proven work | Both agree → Claude writes to proper files |

---

## Sync Counter System

Claude tracks messages since last `{Sync}` with a visual counter at the end of each response.

### Counter States

| State | Symbol | Meaning |
|-------|--------|---------|
| **Normal** | `🗒️ N/LIMIT` | Under your limit |
| **Past Limit** | `🟡 N/LIMIT` | Over your limit but < 15 |
| **Dangerous** | `🟠 N/LIMIT` | 15+ messages without sync |
| **Critical** | `🔴 N/LIMIT` | 20+ messages without sync |

### How It Works

- Counter shows `N/LIMIT` where N = messages since sync, LIMIT = your configured limit
- Counter **continues past limit** (11/10, 12/10...) rather than resetting
- **Yellow threshold** varies by user's limit (personal warning)
- **Orange threshold** (15) is universal (dangerous for any user)
- **Red threshold** (20) is universal (critical for any user)

### Example

If your limit is 10:
🗒️ 5/10   ← Normal, 5 messages in
🗒️ 10/10  ← At limit
🟡 12/10  ← Past YOUR limit, sync recommended
🟠 15/10  ← Dangerous - context degradation likely
🔴 22/10  ← Critical - sync immediately

If someone else's limit is 5:
🗒️ 3/5    ← Normal
🟡 7/5    ← Past THEIR limit
🟠 15/5   ← Same dangerous threshold
🔴 20/5   ← Same critical threshold

### Setting Your Limit

In your SKILL.md or memory, specify:
{Sync} limit: 10

---

## Supporting Commands

| Command | Purpose |
|---------|---------|
| `{Tick}` | Quick session snapshot (no file writes) |
| `{Chunk}` | Handoff compression for context limits |
| `{Relational}` | Architecture alignment check |
| `{ArtD}` | Restore artifacts to sidebar |

---

🔥 BOND: The Bonfire Protocol