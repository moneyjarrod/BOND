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

## Counter Enforcement (CRITICAL)

**The Problem:** Claude drops the counter during multi-tool operations.

**The Rule:** Every response ends with counter. NO EXCEPTIONS.

### Enforcement Checklist

Before completing any response, Claude verifies:

```
☐ Counter is present at END of response
☐ Counter number is CORRECT (not guessed)
☐ Counter appears AFTER all prose/results
```

### Common Failure Modes

| Failure | Fix |
|---------|-----|
| Tool-heavy response, forgot counter | Add counter after final tool result |
| Deep in problem-solving, lost track | Count user messages since last {Sync} |
| Ended with emoji/signoff, no counter | Counter goes LAST, after everything |
| Guessed wrong number | Scroll up and count manually |

### The Mantra

```
"No response is complete without the counter."
```

Even if the response is:
- A single sentence
- Just tool output
- An error message
- A question

**It ends with the counter.**

### Example: Multi-Tool Response

```
[tool call 1]
[result]
[tool call 2]
[result]
[prose explanation]

🗒️ 5/10   ← ALWAYS HERE
```

---

## What Resets the Counter

| Action | Resets Counter? | Why |
|--------|-----------------|-----|
| `{Sync}` | ✅ YES | Reading files refreshes context |
| New conversation | ✅ YES | Clean slate |
| `{Save}` | ❌ NO | Writing ≠ reading |
| `{Chunk}` | ❌ NO | Snapshot only |
| Bonfire declared | ❌ NO | Milestone ≠ refresh |
| Compaction | ❌ NO | Resume at 🟠 15/X |

**⚠️ CRITICAL:** {Save} does NOT reset the counter.

```
WRONG:  User: {Save}  →  Claude: [report] 🗒️ 1/10
RIGHT:  User: {Save}  →  Claude: [report] 🗒️ 7/10
```

The counter tracks CONTEXT DEGRADATION (drift from truth).
- {Save} = "I wrote" → Counter increments
- {Sync} = "I read" → Counter resets

---

## After Compaction

If you see a message like "[conversation was compacted]" or "This conversation was summarized", call `{Sync}` immediately.

**Why:** Compaction compresses the conversation to free up context space. Claude loses detail about:
- Recent decisions and agreements
- Nuanced context from earlier messages
- The "feel" of the conversation flow

**What to do:**
1. Notice the compaction message
2. Say `{Sync}` (or `{Sync} post-compaction`)
3. Claude re-reads files and re-grounds
4. Continue working

**Rule:** Compaction = instant 🔴. Always sync immediately after.

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
