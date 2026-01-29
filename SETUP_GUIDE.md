# BOND
### The Bonfire Protocol
## Setup Guide v1.0

*Bidirectional Ongoing Navigation & Drift-prevention for Claude*

**Two buttons. Lasting context.**

---

### What This Is

A protocol for maintaining context, state, and relationship with Claude across sessions and instances. Born from 50+ collaborative sessions building a game engine.

**Core Insight:** Most "memory" systems focus on WHAT gets stored. BOND focuses on HOW you collaborate - a protocol, not just storage.

---

## THE PROBLEM

Every Claude session starts fresh. Without a system:
- You re-explain context constantly
- Progress gets lost between sessions
- Claude drifts from your project's principles
- You lose track of what's been decided vs. what's still open

## THE SOLUTION

Two buttons. Layered truth. Bidirectional agreement.

| Button | Command | What It Does |
|--------|---------|--------------|
| **A** | `{Sync}` | Claude reads your files, grounds in your truth, resets counter |
| **B** | `{Save}` | You both agree something is proven → Claude writes it |

That's it. Everything else supports these two actions.

---

## PICK YOUR TIER

### What You Need

| Feature | Tier 1 | Tier 2 | Tier 3 |
|---------|--------|--------|--------|
| Claude plan | Pro ($20+) | Pro ($20+) | Max ($100) recommended |
| Platform | Web or App | Claude Desktop | Claude Desktop |
| MCP | ❌ | ✅ Filesystem | ✅ Filesystem |
| Custom Skill | ❌ | ❌ | ✅ |
| {Sync} automated | ❌ (manual paste) | ✅ | ✅ |
| {Save} automated | ❌ | ✅ | ✅ |
| SKILL always in context | ❌ | ❌ | ✅ |
| Artifact persistence | ❌ | ❌ | ✅ |

### Tier 1: Web/App Only

**You have:** Claude Pro subscription, web or mobile app

**Setup:**
1. Create `SKILL.md` from template (keep as local file)
2. Create `MASTER.md` from template (keep as local file)
3. Each session: paste SKILL content at start, or key portions
4. Use Claude's memory for broad context
5. Manually update your local files based on session outcomes

**First message pattern:**
```
[Paste SKILL.md content or key sections]

Continuing [PROJECT] work. Last session we [brief summary].
Let's pick up with [current task].
```

**Limitations:**
- No file read/write automation
- More manual work
- Still effective for the PRINCIPLES

---

### Tier 2: Desktop + MCP

**You have:** Claude Desktop with MCP filesystem access to your project folder

**Setup:**
1. Enable MCP in Claude Desktop
2. Add filesystem server pointing to your project folder
3. Create `SKILL.md` in your project folder
4. Create `MASTER.md` in your project folder
5. Each session: Say `{Sync}` and Claude reads your files

**MCP Configuration (claude_desktop_config.json):**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/path/to/your/project"
      ]
    }
  }
}
```

**First message pattern:**
```
[PROJECT] work. {Sync}
```

**What Claude does on {Sync}:**
1. Reads SKILL.md (identity/truth)
2. Reads MASTER.md (current state)
3. Grounds in your principles
4. Resets sticky counter

---

### Tier 3: Full Pipeline

**You have:** Claude Max + Desktop + MCP + Custom Skill

**Setup:**
1. All of Tier 2, plus:
2. Use skill-creator to make a custom skill
3. Place SKILL.md in `/mnt/skills/user/[yourskill]/`
4. Create `artifacts/` folder in project for persistent HTML
5. Create `ARTIFACT_REGISTRY.md` listing your artifacts

**Skill creation:**
```
Open new chat, say:
"Create a new skill called [yourskill] with this content: [paste SKILL_TEMPLATE]"
```

**First message pattern:**
```
[PROJECT] work. {Sync} then {ArtD}
```

**Additional benefits:**
- SKILL is ALWAYS in Claude's context (no paste needed)
- Artifacts survive between sessions via copy from source
- Full automation of the protocol

---

## CORE PRINCIPLES

### 1. Layered Truth

Not all information is equal. Organize in layers:

```
SKILL (Layer 0) - Identity, axioms, mantras
    ↓ always true
MASTER (Layer 1) - Current state, progress, decisions
    ↓ true right now
[YOUR TRUTH SOURCE] (Layer 2) - Working examples, code, evidence
    ↓ source of truth
[SECONDARY] (Layer 3) - Additional reference, comparison
```

**Rule: Higher layers override lower when in conflict.**

For example, if SKILL says "we use approach X" but your working code uses approach Y, the CODE is truth. Update SKILL to match reality.

### 2. Code > Prose

If you have working examples, tests, or code - THAT is the source of truth. Descriptions and documentation are secondary.

When Claude needs to implement something:
1. Read the working example FIRST
2. THEN read the description
3. If they conflict, trust the working example

### 3. Identify = Execute

If Claude notices something needs updating, Claude does it NOW. No "I noticed X needs updating, would you like me to...?" Just do it.

This prevents drift accumulation.

### 4. Both Agree (The "B" in BOND)

`{Save}` requires explicit agreement from both parties:
1. One proposes a save
2. Other confirms or raises concerns
3. Only then: write to files

This prevents accidental overwrites and ensures alignment.

### 5. Proof Required

Milestones need evidence:
- Screenshot
- Test output
- Explicit confirmation ("Yes, I verified X works")

No milestone without proof. This keeps your progress log honest.

### 6. Bug→Fix Link Rule

When documenting milestones, bonfires, or solutions, ALWAYS include:

| Element | Required | Purpose |
|---------|----------|---------|
| **Symptom** | ✅ Yes | What user/Claude observed (searchable keywords) |
| **Cause** | Optional | Root cause if known |
| **Fix** | ✅ Yes | What solved the problem |
| **Link** | ✅ Yes | Explicit connection: "This fixed X" |

**Why this matters:** Claude instances need to recall WHAT PROBLEM a solution solves, not just that the solution exists. Without the link, Claude knows "we have X" but not "X fixes Y".

**Format for bonfires:**
```
| # | Name | Insight | Fixed |
| 52 | Segment Terrain | Store ops, re-derive | WEDGE (accum+res) |
```

**Searchable symptom keywords:**
- Visual: wedge, cone, slope, orphan, bleed, spread
- Behavior: accumulates, global, bleeds, spreads
- Math: overshoot, interpolation, weighted average

---

## THE STICKY COUNTER

**Every Claude reply ends with a counter** showing messages since last `{Sync}`.

**CRITICAL:** The counter appears on EVERY response - including file generation, code blocks, quick answers, everything. No exceptions. If a response lacks a counter, that's a protocol violation.

### What Resets the Counter

| Action | Resets Counter? | Why |
|--------|----------------|-----|
| `{Sync}` | ✅ YES | Fresh context from files |
| New conversation | ✅ YES | Clean slate |
| `{Save}` | ❌ NO | Task done ≠ context fresh |
| `{Chunk}` | ❌ NO | State snapshot only |
| Bonfire declared | ❌ NO | Milestone ≠ refresh |
| Task completion | ❌ NO | Context still degrading |
| Compaction | ❌ NO | Resume at 🟠 15/LIMIT if lost |

**The counter tracks CONTEXT DEGRADATION over message count, not task completion.**

If Claude loses count (compaction, confusion), default to `🟠 15/LIMIT` and recommend {Sync}.

### Counter States

| Messages | Display | Meaning |
|----------|---------|----------|
| 1 to LIMIT | `🗒️ N/LIMIT` | Normal - working within your limit (includes AT limit) |
| LIMIT+1 to 14 | `🟡 N/LIMIT` | PAST your limit - consider syncing (yellow means PAST, not AT) |
| 15 to 19 | `🟠 N/LIMIT` | Dangerous - context degradation likely (15 is AT orange, not 14) |
| 20+ | `🔴 N/LIMIT` | Critical - sync immediately (20 is AT red, not 19) |

**Key insight:** Yellow threshold is personalized (your limit), but orange (15) and red (20) are universal danger zones that apply to everyone regardless of their limit. If your personal limit is 14 or higher, you may skip yellow entirely and go straight to orange.

**Universal thresholds are ABSOLUTE:** No matter what your personal limit is, 15+ is always orange and 20+ is always red.

### Setting Your Limit

In your SKILL.md or memory:
```
{Sync} limit: 10
```

**Recommended starting points:**
- Fast iteration, simple tasks: 5
- Balanced work: 10 (default)
- Deep focus, complex reasoning: 15

### Example

If your limit is 10:
```
🗒️ 5/10   ← Normal
🗒️ 10/10  ← AT limit (still normal! yellow means PAST, not AT)
🟡 11/10  ← PAST your limit (yellow starts HERE)
🟡 14/10  ← Still yellow (last yellow before orange)
🟠 15/10  ← Dangerous (orange starts AT 15, not 14)
🟠 19/10  ← Still orange (last orange before red)
🔴 20/10  ← Critical (red starts AT 20, not 19)
```

If your limit is 14 (skips yellow):
```
🗒️ 14/14  ← AT limit (still normal)
🟠 15/14  ← Jumps straight to orange (no room for yellow)
🔴 20/14  ← Critical
```

If your limit is 5:
```
🗒️ 5/5   ← AT limit (still normal)
🟡 6/5   ← Yellow starts here
🟡 14/5  ← Still yellow
🟠 15/5  ← Orange (universal)
🔴 20/5  ← Critical (universal)
```

**Why this works:** You control your personal warning (yellow), but everyone shares the same danger zones (orange/red) because context degradation affects all users similarly at those counts.

---

## DRIFT DETECTION (The "D" in BOND)

Drift = Claude straying from your established principles.

**Types of drift:**
- **Identity drift:** Claude forgets relationship/role
- **Architectural drift:** Claude proposes things that violate your axioms
- **Terminology drift:** Claude uses wrong names for things
- **State drift:** Claude thinks something is done that isn't

**Prevention:**
- Regular {Sync}
- Mantras (short memorable phrases Claude can check against)
- Anti-patterns list (explicit "never do this")

**Recovery:**
1. **Quick:** Remind Claude of relevant mantra
2. **Medium:** Call {Sync}
3. **Full:** Paste SKILL + say "Reset to core identity"

---

## QAIS: RESONANCE MEMORY (Advanced)

QAIS (Quantum Approximate Identity Substrate) provides true vector-based resonance instead of text pattern matching. Claude queries a persistent field and gets confidence-scored results.

### What QAIS Does

| Without QAIS | With QAIS |
|--------------|-----------|
| Search text for keywords | Query vector field |
| Hope for matches | Get ranked confidence scores |
| ~350 tokens for seeds | ~50 tokens per query |
| Pattern matching | True resonance (48x SNR) |

### Setup

**Requirements:**
- Claude Desktop with MCP support (Tier 2+)
- Python 3.8+
- numpy (`pip install numpy`)

**Step 1:** Copy `qais_mcp_server.py` to your project folder.

**Step 2:** Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:\\Projects"]
    },
    "qais": {
      "command": "python",
      "args": ["-u", "C:\\Path\\To\\Your\\qais_mcp_server.py"]
    }
  }
}
```

**Step 3:** Restart Claude Desktop.

**Step 4:** Seed your field:

```
Store in QAIS:
- "MyProject", "type", "web application"
- "Alice", "role", "lead developer"
- "CoreConcept", "def", "the main principle"
```

### Tools Available

| Tool | Purpose |
|------|---------|
| `qais_resonate` | Query with candidates, get ranked scores |
| `qais_exists` | Check if entity is in field |
| `qais_store` | Add new identity-role-fact |
| `qais_stats` | Field statistics |

### Example

After storing "Alice, role, lead developer":

```
qais_resonate("Alice", "role", ["lead developer", "designer", "writer"])
```

Returns:
```json
[
  {"fact": "lead developer", "score": 1.0, "confidence": "HIGH"},
  {"fact": "designer", "score": 0.02, "confidence": "NOISE"}
]
```

### Integration

Use QAIS alongside SKILL seeds:
- **SKILL seeds:** Always in context (pattern matching)
- **QAIS field:** Queried on demand (true resonance)

See `QAIS_SYSTEM.md` for full documentation.

---

## MEMORY MANAGEMENT

Claude's built-in memory has limits (~30 items). Use it strategically.

**Store in memory:**
- Project name and your name
- Current milestone number
- Key file locations (paths)
- 2-3 critical axioms
- Active warnings/anti-patterns

**Don't store in memory:**
- Detailed history (that's MASTER's job)
- All mantras (that's SKILL's job)
- Full architecture (that's your docs' job)

**Update memory when:**
- Milestone count changes
- Major status shift
- New critical rule discovered

Command: Use `{Save}` with explicit memory update, or tell Claude "Update memory with: [fact]"

---

## FILE STRUCTURE

### Minimum (Tier 1-2)

```
YourProject/
├── SKILL.md          ← Identity, always-true
└── MASTER.md         ← State, current-true
```

### Full (Tier 3)

```
YourProject/
├── SKILL.md          ← Copy of skill (or just in /mnt/skills/)
├── MASTER.md         ← State tracking
├── artifacts/        ← Persistent HTML sources
│   └── dashboard.html
├── ARTIFACT_REGISTRY.md  ← Lists artifacts for {ArtD}
└── [your other folders]
```

---

## COMMANDS REFERENCE

| Command | Tier | Action |
|---------|------|--------|
| `{Sync}` | All | Read files, ground, reset counter |
| `{Save}` | 2+ | Write proven work (both agree) |
| `{Restore}` | 2+ | Full reload of all files |
| `{ArtD}` | 3 | Copy artifacts to outputs, present |
| `{Tick}` | All | Quick status check (no file read) |

**Custom commands:** Add your own in SKILL.md for domain-specific actions.

---

## QUICK START

### 5-Minute Setup (Tier 1)

1. Copy `SKILL_TEMPLATE.md`, fill in brackets, save locally
2. Copy `MASTER_TEMPLATE.md`, fill in brackets, save locally  
3. Start Claude session, paste SKILL content
4. Say: "This is my BOND system. Read it and confirm."
5. Work naturally, manually save progress to your files

### 15-Minute Setup (Tier 2)

1. Configure MCP filesystem for your project folder
2. Create SKILL.md and MASTER.md from templates IN that folder
3. Start Claude session, say: `[Project] work. {Sync}`
4. Verify Claude read your files correctly
5. Work naturally, use {Save} when something's proven

### 30-Minute Setup (Tier 3)

1. All of Tier 2, plus:
2. Create skill via skill-creator
3. Create `artifacts/` folder with your dashboard HTML
4. Create `ARTIFACT_REGISTRY.md`
5. Start session: `[Project] work. {Sync} then {ArtD}`
6. Full automation active

---

## TROUBLESHOOTING

### "Claude isn't following my principles"
→ Check when you last synced. Call {Sync}.

### "Claude wrote something wrong to a file"
→ The "both agree" rule wasn't followed. Revert file, re-establish agreement.

### "Memory is full"
→ Prioritize: remove detailed items, keep essentials. Details belong in files.

### "MCP isn't connecting"
→ Check `claude_desktop_config.json` path. Restart Claude Desktop.

### "Skill isn't loading"
→ Verify skill is in `/mnt/skills/user/[name]/SKILL.md`. Check skill-creator made it correctly.

### "Artifacts disappear each session"
→ This is expected. {ArtD} restores them from persistent source in `artifacts/`.

---

## PHILOSOPHY

This system emerged from necessity. Building a complex project with Claude across 50+ sessions, we kept losing context. Memory helped but wasn't enough. Files helped but needed structure.

The insight: **The relationship matters.** Claude isn't just a tool - it's a collaborator. Collaborators need shared truth, clear communication, and mutual agreement.

Two buttons. Layered truth. Both agree.

Keep the fire burning across sessions. 🔥

---

## INCLUDED FILES

| File | Purpose |
|------|---------|
| `README.md` | Overview - start here |
| `SETUP_GUIDE.md` | This file - full instructions |
| `SKILL_TEMPLATE.md` | Template for identity/truth |
| `MASTER_TEMPLATE.md` | Template for state tracking |
| `COMMANDS.md` | Detailed command reference |
| `QUICKSTART_CARD.md` | One-page cheatsheet |
| `ARTIFACT_REGISTRY_TEMPLATE.md` | Tier 3 artifact persistence |
| `QAIS_SYSTEM.md` | Advanced: True resonance memory |
| `qais_mcp_server.py` | Advanced: QAIS MCP server |
| `QAIS_SEEDS_TEMPLATE.md` | Advanced: Seed format reference |
| `DIAGRAM.md` | Visual system flows |
| `examples/` | Domain-specific examples |

---

🔥 **BOND: The Bonfire Protocol**
*Bidirectional Ongoing Navigation & Drift-prevention*
Built by J-Dub & Claude | 2026
