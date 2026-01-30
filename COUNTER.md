# COUNTER.md
## The BOND Response Schema

*"No response is complete without the counter."*

---

## What This Is

The counter is not a feature. It's part of the **response schema**.

Every BOND response ends with a counter. Not "should" — **MUST**.

This is what makes BOND work. Everything else (QAIS, MCP, artifacts, tiers) extends this core.

---

## The Definition

```
COUNTER = Messages since Claude last grounded in truth

Measures:   CONTEXT DEGRADATION
Not:        Task completion
Not:        Bonfire progress  
Not:        Session duration
Not:        How well things are going

Resets:     {Sync} or new conversation
            (nothing else)
```

---

## The Format

```
🗒️ N/LIMIT   Normal (1 to LIMIT)
🟡 N/LIMIT   Past limit (LIMIT+1 to 14)
🟠 N/LIMIT   Dangerous (15-19)
🔴 N/LIMIT   Critical (20+)
```

**Examples (LIMIT = 10):**
```
🗒️ 5/10    ← Normal
🗒️ 10/10   ← AT limit (still normal)
🟡 11/10   ← PAST limit (yellow starts here)
🟠 15/10   ← Dangerous (universal threshold)
🔴 20/10   ← Critical (universal threshold)
```

---

## Why It Exists

Claude's context degrades over messages. Not dramatically — subtly. Small drifts accumulate:
- Forgetting a nuance
- Misremembering a decision
- Losing the "feel" of the work

The counter makes degradation **visible**.

When you see 🟡 or 🟠, you know: context is stale. Time to {Sync}.

---

## No Dependencies

The counter requires:
- ❌ No QAIS
- ❌ No MCP
- ❌ No file access
- ❌ No custom skills
- ❌ No special setup

It works at **every tier**, in **complete isolation**.

A user with just Claude web and a text file can use BOND. The counter still works.

---

## Response Schema

Think of it like a function signature:

```
BOND_Response {
    content: string,      // The actual response
    counter: Counter      // REQUIRED - never optional
}

Counter {
    state: 🗒️ | 🟡 | 🟠 | 🔴,
    current: int,
    limit: int
}
```

A response without a counter is **malformed**. Like a function returning `undefined` when it should return a value.

---

## Placement

Counter goes **LAST**. After everything:
- After prose
- After code blocks
- After tool results
- After questions
- After emojis/signoffs

```
[All your content here]

🗒️ 5/10   ← Always last line
```

---

## What Resets It

| Action | Resets? | Why |
|--------|---------|-----|
| `{Sync}` | ✅ YES | Reading files = fresh context |
| New conversation | ✅ YES | Clean slate |
| `{Save}` | ❌ NO | Writing ≠ reading |
| `{Chunk}` | ❌ NO | Snapshot only |
| Completing a task | ❌ NO | Task done ≠ context fresh |
| Declaring a bonfire | ❌ NO | Milestone ≠ refresh |
| Compaction | ❌ NO | Resume at 🟠 15/LIMIT |

**Only truth-grounding resets the counter.**

---

## Common Failures

| Failure | Why It Happens | Fix |
|---------|----------------|-----|
| Counter missing | Deep in tool calls, forgot | Check before sending |
| Wrong number | Guessed instead of counted | Scroll up, count manually |
| Counter mid-response | Put it before final content | Move to end |
| Reset on {Save} | Confused task completion with grounding | {Save} doesn't reset |
| No counter on short reply | Thought it was optional | It's never optional |

---

## The Mantra

```
"No response is complete without the counter."
```

Even if the response is:
- One word
- A question
- An error message
- Just tool output
- "I don't know"

**It ends with the counter.**

---

## For Claude

When you are operating under BOND:

1. **Track** messages since last {Sync}
2. **Calculate** the correct count (don't guess)
3. **Append** counter as final line of every response
4. **Never** skip it, regardless of response type

If you lose count (compaction, confusion):
- Default to `🟠 15/LIMIT`
- Recommend {Sync}
- Be honest: "Lost count, defaulting to caution"

---

## For Users

The counter tells you one thing: **how stale is Claude's context?**

| You See | What It Means | What To Do |
|---------|---------------|------------|
| 🗒️ | Context is fresh | Keep working |
| 🟡 | Getting stale | Consider {Sync} soon |
| 🟠 | Probably degraded | {Sync} recommended |
| 🔴 | Definitely degraded | {Sync} now |

You control your LIMIT. Start with 10, adjust based on experience.

---

## Setting Your Limit

Tell Claude your limit in any of these ways:
- In SKILL.md: `{Sync} limit: 10`
- In memory: "{Sync} limit is 10"
- At session start: "My sync limit is 10"

**Recommended starting points:**
- Fast iteration: 5
- Balanced work: 10
- Deep focus: 15

---

## Why This Matters

BOND works because it makes the invisible visible.

Without the counter, you don't know when context has degraded. You just notice Claude "feeling off" or making mistakes that seem out of character.

With the counter, degradation has a number. And numbers can be managed.

**The counter is the heartbeat of BOND.**

---

🔥 BOND: The Bonfire Protocol
