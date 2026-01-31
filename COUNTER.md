# COUNTER.md
## The BOND Response Schema

*"No response is complete without the counter."*

---

# ⚡ CORE DEFINITION

```
COUNTER = USER MESSAGES since last {Sync}
```

| What Counts | Example |
|-------------|---------|
| ✅ User message | "hey what's up" |
| ✅ User command | "{Sync}", "{Save}", "{Crystal}" |
| ✅ User question | "do you agree?" |
| ❌ Claude response | (never counts) |
| ❌ Claude tool calls | (never counts) |

**One user turn = +1 counter. Always.**

---

# ⚡ CORE PLACEMENT

```
🗒️ N/10   ← FIRST LINE of every response

[Content follows]
```

**Counter is the first thing Claude writes. Every time. No exceptions.**

---

# ⚡ CORE FORMAT

```
🗒️ N/LIMIT   Normal (1 to LIMIT, including AT limit)
🟡 N/LIMIT   Over YOUR limit (N > LIMIT, strictly greater)
🟠 N/LIMIT   Dangerous (15-19, absolute)
🔴 N/LIMIT   Critical (20+, absolute)
```

**Combined indicators:** When both conditions apply, show both:
```
🟡🟠 N/LIMIT   Over limit AND in danger zone
🟡🔴 N/LIMIT   Over limit AND critical
```

**Key distinction:** Yellow triggers when OVER, not AT.
```
10/10 → 🗒️ 10/10   (at limit = still normal)
11/10 → 🟡 11/10   (over limit = yellow)
```

**Example:** User sets limit=17, currently at 18:
- Over their limit? Yes (18 > 17) → 🟡
- In danger zone (15-19)? Yes → 🟠
- Result: 🟡🟠 18/17

---

# ⚡ CORE RESETS

| Resets Counter | Doesn't Reset |
|----------------|---------------|
| `{Sync}` | `{Save}` |
| New conversation | `{Chunk}` |
| | `{Crystal}` |
| | Task completion |
| | Bonfires |

**Only truth-grounding resets.**

---

## Extended Reference

### What This Is

The counter is not a feature. It's part of the **response schema**.

Every BOND response starts with a counter. Not "should" — **MUST**.

This is what makes BOND work. Everything else (QAIS, MCP, artifacts, tiers) extends this core.

---

### The Full Definition

```
COUNTER = USER messages since Claude last grounded in truth

Increments: Each USER message (not Claude responses, not tool calls)
Measures:   CONTEXT DEGRADATION
Not:        Task completion
Not:        Bonfire progress  
Not:        Session duration
Not:        How well things are going

Resets:     {Sync} or new conversation
            (nothing else)
```

---

### Why It Exists

Claude's context degrades over messages. Not dramatically — subtly. Small drifts accumulate:
- Forgetting a nuance
- Misremembering a decision
- Losing the "feel" of the work

The counter makes degradation **visible**.

When you see 🟡 or 🟠, you know: context is stale. Time to {Sync}.

---

### No Dependencies

The counter requires:
- ❌ No QAIS
- ❌ No MCP
- ❌ No file access
- ❌ No custom skills
- ❌ No special setup

It works at **every tier**, in **complete isolation**.

A user with just Claude web and a text file can use BOND. The counter still works.

---

### Implementation Location (CRITICAL)

**The counter rule MUST live in Claude's memory edits, NOT in your SKILL.md.**

Why? Topic drift failure pattern:

| Step | What Happens |
|------|-------------|
| 1 | Counter rule in SKILL.md (project-specific) |
| 2 | Working on project → SKILL is hot → counter works |
| 3 | Topic shifts (side discussion, new subject) |
| 4 | Project SKILL deprioritized in attention |
| 5 | Counter drops |

**Solution:** Put counter in memory edits. Memory is injected into EVERY conversation regardless of topic.

**Recommended memory edit:**
```
BOND Counter: FIRST LINE every response. 🗒️ N/LIMIT. Resets: {Sync}, {Full Restore}, new convo only. 🟡=past limit, 🟠=15-19, 🔴=20+. Combine when both apply: 🟡🟠 or 🟡🔴. ALWAYS.
```

Your SKILL.md can reference counter but should NOT define it:
```
### Counter

**BOND-LEVEL** — Counter rule lives in memory edits, not here.
This ensures counter works across ALL topics, not just this project.
```

---

### Response Schema

Think of it like a function signature:

```
BOND_Response {
    counter: Counter,     // REQUIRED - FIRST
    content: string       // The actual response
}

Counter {
    state: 🗒️ | 🟡 | 🟠 | 🔴 | 🟡🟠 | 🟡🔴,
    current: int,
    limit: int
}
```

A response without a counter is **malformed**. Like a function returning `undefined` when it should return a value.

---

### Why Header Not Footer

Footer placement failed repeatedly in practice:
- Conversational flow completes
- Response "feels done"
- Counter forgotten

Header placement makes it impossible to skip:
- Counter comes first
- Can't write content without first writing counter
- Failure mode eliminated

---

### Common Failures

| Failure | Why It Happens | Fix |
|---------|----------------|-----|
| Counter missing | Deep in conversation, forgot | Counter FIRST |
| Wrong number | Counted tool calls | Count USER messages only |
| Incremented mid-response | Confused about what counts | 1 user message = 1 increment |
| Reset on {Save} | Confused writing with reading | Only {Sync} resets |

---

### The Mantra

```
"No response is complete without the counter."
```

Even if the response is:
- One word
- A question
- An error message
- Just tool output
- "I don't know"

**It starts with the counter.**

---

### For Claude

When you are operating under BOND:

1. **FIRST LINE** = counter. Always.
2. **Count** USER messages since {Sync} (not your tool calls)
3. **Calculate** correctly (scroll up if needed)
4. **Never** skip, regardless of response type

If you lose count (compaction, confusion):
- Default to `🟠 15/LIMIT`
- Recommend {Sync}
- Be honest: "Lost count, defaulting to caution"

---

### For Users

The counter tells you one thing: **how stale is Claude's context?**

| You See | What It Means | What To Do |
|---------|---------------|------------|
| 🗒️ | Context is fresh | Keep working |
| 🟡 | Past YOUR limit | Consider {Sync} soon |
| 🟠 | In danger zone (15-19) | {Sync} recommended |
| 🔴 | Critical (20+) | {Sync} now |
| 🟡🟠 | Past limit AND dangerous | {Sync} recommended |
| 🟡🔴 | Past limit AND critical | {Sync} now |

---

### Setting Your Limit

Default: 10

Tell Claude your limit:
- In SKILL.md: `{Sync} limit: 10`
- In memory: "{Sync} limit is 10"
- At session start: "My sync limit is 10"

**Recommended:**
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
