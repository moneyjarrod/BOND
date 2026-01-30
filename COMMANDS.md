# BOND Commands Reference

## ⚡ THE CORE: Counter

Before anything else, understand this:

```
COUNTER = USER MESSAGES since last {Sync}
```

| What Counts | Example |
|-------------|--------|
| ✅ User message | "hey what's up" |
| ✅ User command | "{Sync}", "{Save}" |
| ❌ Claude response | (never) |
| ❌ Claude tool calls | (never) |

**Placement:** FIRST LINE of every response. Not footer — header.

```
🗒️ 5/10   ← FIRST

[Then content]
```

---

## Core Commands

| Command | When | What It Does |
|---------|------|--------------|
| `{Sync}` | Every ~10 messages | Claude reads your files, re-grounds in truth |
| `{Save}` | After proven work | Both agree → Claude writes to proper files |

---

## {Sync} Protocol

**Trigger:** User says `{Sync}`

**Action:**
1. Read SKILL.md (identity/truth)
2. Read MASTER.md or OPS file (current state)
3. Optionally read code files if task requires
4. Confirm grounding: "I'm here, [name]. 🔥🌊" or similar
5. Reset counter to 1

**Dependencies:** 
- Tier 1: User pastes content
- Tier 2+: MCP filesystem access

**Output:**
```
🗒️ 1/10

[Confirmation of what was read]
[Brief status if relevant]
```

---

## {Save} Protocol

**Trigger:** User says `{Save}` OR Claude proposes save

**Action:**
1. State what will be written and where
2. Wait for explicit agreement from user
3. Only after "yes/confirmed/do it": write to files
4. Report what was written
5. Increment counter (does NOT reset)

**Dependencies:**
- Tier 2+: MCP filesystem write access
- Tier 1: Claude provides content, user saves manually

**Output:**
```
🗒️ N/10   ← NOT reset

Proposing to save:
- [file]: [what changes]

Confirm?

[after confirmation]

Saved:
- [file]: [done]
```

**Critical:** {Save} does NOT reset the counter. Writing ≠ reading.

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

**The Problem:** Claude drops the counter during conversational flow.

**The Rule:** Every response STARTS with counter. NO EXCEPTIONS.

### Enforcement Checklist

Before completing any response, Claude verifies:

```
☐ Counter is FIRST LINE of response
☐ Counter number is CORRECT (count USER messages)
☐ Counter appears BEFORE all prose/results
```

### Common Failure Modes

| Failure | Fix |
|---------|-----|
| Conversational reply, forgot counter | Counter FIRST, always |
| Counted tool calls | Only count USER messages |
| Counter at end (footer) | Move to FIRST LINE |
| Guessed wrong number | Count user turns since {Sync} |

### The Mantra

```
"No response is complete without the counter."
```

Even if the response is:
- A single sentence
- Just tool output
- An error message
- A question

**It starts with the counter.**

### Example: Any Response

```
🗒️ 5/10   ← ALWAYS FIRST

[tool call 1]
[result]
[tool call 2]
[result]
[prose explanation]
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

---

## {Tick} Protocol

**Trigger:** User says `{Tick}`

**Purpose:** Quick status check without reading files. Lighter than {Sync}.

**Action:**
1. Report current understanding of session state
2. List what's been accomplished this session
3. Note any open threads or pending items
4. Do NOT read files (that's {Sync})
5. Increment counter (does NOT reset)

**Dependencies:** None — works at all tiers

**Output:**
```
🗒️ N/10   ← NOT reset

{Tick} — Session [N] Status

Done:
- [item]
- [item]

Open:
- [item]

Next: [what's queued]
```

**When to use:** 
- Quick check before stepping away
- Verify Claude's understanding without full sync
- Lighter weight than {Sync}

**When NOT to use:**
- Context feels stale (use {Sync})
- Need to ground in files (use {Sync})
- Counter is yellow/orange/red (use {Sync})

---

## {Chunk} Protocol

**Trigger:** User says `{Chunk}`

**Purpose:** Create a crystallization summary for handoff — to another session, another Claude instance, or future self.

**Action:**
1. Summarize what was worked on this session
2. List key decisions and insights
3. Note current state of work
4. Identify open threads and next steps
5. Format for easy paste into new session
6. Do NOT reset counter

**Dependencies:** None — works at all tiers

**Output:**
```
🗒️ N/10   ← NOT reset

## {Chunk} — Session [N] Crystallization

### Completed
- [major item]
- [major item]

### Key Decisions
- [decision]: [why]

### Current State
[where things stand]

### Open Threads
- [thread]: [status]

### Next Session
[what to pick up]
```

**When to use:**
- End of session (planned handoff)
- Context window getting full
- Before expected compaction
- Switching to different work stream

**Key insight:** {Chunk} gives compaction good material to summarize. If you crystallize clearly, the compressed version retains more meaning.

---

## {ArtD} Protocol

**Trigger:** User says `{ArtD}`

**Purpose:** Restore persistent artifacts to the sidebar. Artifacts live in project folder (survive sessions) but must be copied to outputs (ephemeral) each session.

**Action:**
1. Read `ARTIFACT_REGISTRY.md` from project folder
2. For each artifact in registry:
   - Copy from source path to `/mnt/user-data/outputs/`
3. Present files to sidebar
4. Report what was restored
5. Increment counter (does NOT reset)

**Dependencies:** 
- Tier 3 (requires MCP filesystem)
- `ARTIFACT_REGISTRY.md` must exist
- `artifacts/` folder with source files

**File Structure:**
```
YourProject/
├── ARTIFACT_REGISTRY.md    ← Lists what to restore
└── artifacts/
    ├── dashboard.html      ← Persistent source
    └── other.html
```

**Registry Format:**
```markdown
## Artifact Registry

| Name | Source Path | Type | Description |
|------|-------------|------|-------------|
| Dashboard | `artifacts/dashboard.html` | HTML | Status dashboard |
```

**Output:**
```
🗒️ N/10   ← NOT reset

{ArtD} — Artifacts restored

- dashboard.html ✅

[files appear in sidebar]
```

**When to use:**
- Session start (after {Sync})
- After compaction
- When artifacts disappeared from sidebar

**Why artifacts disappear:** The outputs folder (`/mnt/user-data/outputs/`) is ephemeral — it wipes between sessions. Your source files in `artifacts/` persist. {ArtD} bridges the gap.

---

## Command Summary

| Command | Reads Files | Writes Files | Resets Counter | Tier |
|---------|-------------|--------------|----------------|------|
| `{Sync}` | ✅ Yes | ❌ No | ✅ Yes | All |
| `{Save}` | ❌ No | ✅ Yes | ❌ No | 2+ |
| `{Tick}` | ❌ No | ❌ No | ❌ No | All |
| `{Chunk}` | ❌ No | ❌ No | ❌ No | All |
| `{Crystal}` | ❌ No | ✅ QAIS | ❌ No | QAIS |
| `{ArtD}` | ✅ Registry | ✅ Copies | ❌ No | 3 |

---

## {Crystal} Protocol

**Trigger:** User says `{Crystal}`

**Purpose:** Persistent crystallization. Like {Chunk} but stores to QAIS field. "Chunk hopes. Crystal ensures."

**Action:**
1. Generate crystallization summary (same as {Chunk})
2. Call `crystal` MCP tool with the chunk text
3. Tool extracts key concepts from text
4. Tool touches heatmap with extracted concepts
5. Tool generates momentum seed from completed/state/next
6. Tool stores to QAIS:
   - `Session[N]|momentum` — flow state
   - `Session[N]|context` — what was worked on
   - `Session[N]|insight` — key insight (if found)
   - `Session[N]|tags` — top concepts
7. Return summary of what was persisted
8. Do NOT reset counter

**Dependencies:**
- QAIS MCP server (v3.2+)
- `crystal` tool available

**Output:**
```
🗒️ N/10   ← NOT reset

## {Crystal} — Session [N] Crystallization

### Completed
- [item]
- [item]

### Key Insight
[insight]

### Current State
[state]

### Next
[next task]

---

**Persisted to QAIS:**
- Session[N]|momentum ✅
- Session[N]|context ✅
- Session[N]|tags ✅

**Heatmap touched:** [N] concepts
```

**When to use:**
- End of session (want state to survive)
- Before expected compaction
- When insights are worth preserving
- Major milestone completed

**Comparison:**

| | {Chunk} | {Crystal} |
|---|---------|-----------|
| Tier | All | QAIS |
| Output | Text | Text + QAIS seeds |
| Persists | Conversation only | QAIS field |
| Survives compaction | Maybe | Yes (field persists) |
| Survives session end | No | Yes |

**Key insight:** Chunk hopes compaction is kind. Crystal ensures persistence.

---

🔥 BOND: The Bonfire Protocol
