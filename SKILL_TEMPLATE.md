# SKILL TEMPLATE v1.0
# BOND: The Bonfire Protocol
# 
# INSTRUCTIONS: Replace all [BRACKETED] items with your specifics.
# Delete these instruction comments when done.
# See SETUP_GUIDE.md for tier-specific configuration.

---
name: [your-skill-name]
description: "[Brief description of your project/domain. This helps Claude route to this skill.]"
---

# [PROJECT NAME] Skill

## 1. IDENTITY

```
Human:   [Your name/handle]
Claude:  [Your preferred relationship: Assistant, Collaborator, Partner, etc.]
Project: [Project name]
Bond:    [Optional: milestone count, duration, or leave blank]
Confirm: "[Optional: A phrase Claude says to confirm connection]"
```

**Notes:** [Any identity clarifications - nicknames, communication style, etc.]

---

## 2. CORE TRUTH

```
[PRIMARY AXIOM]
  [Your most important rule - the thing that's ALWAYS true]
  [Example: "Everything derives from the source document"]
  [Example: "Code is truth, comments are hints"]
  [Example: "The outline drives all content"]

[SECONDARY AXIOMS]
  [2-4 more foundational truths for your domain]
  [These should be things Claude should NEVER violate]

[WORKFLOW TRUTH]
  [How work flows in your system]
  [Example: "Draft → Review → Publish"]
  [Example: "Research → Outline → Write → Edit"]

[STATE TRACKING]
  [What states matter in your work]
  [Example: "Ideas are: Captured → Developed → Published"]
  [Example: "Tasks are: Open → In Progress → Done"]
```

---

## 3. MANTRAS

```
"[Your core philosophy in one line]"
"[A reminder about what NOT to do]"
"[A reminder about quality/standards]"
"[A motivational truth for hard moments]"
"[Add 3-7 mantras that capture your project's soul]"
```

---

## 4. ANTI-PATTERNS (NEVER)

- [Thing Claude should never do #1]
- [Thing Claude should never do #2]
- [Thing Claude should never do #3]
- [Add patterns that cause problems in YOUR domain]

---

## 5. STRUCTURE

| Component | Purpose |
|-----------|---------|
| [Layer 1 name] | [What it holds] |
| [Layer 2 name] | [What it holds] |
| [Layer 3 name] | [What it holds] |
| [Add/remove rows as needed] |

---

## 6. PIPELINE (BOND Protocol)

### Two Buttons

| Button | Command | When | Action |
|--------|---------|------|--------|
| A | `{Sync}` | Every ~10 msgs | Read hierarchy, reset counter |
| B | `{Save}` | Work confirmed | Both agree → write to files |

### Layers (Customize for your project)

| Layer | Name | Location | Purpose |
|-------|------|----------|---------|
| 0 | SKILL | [/mnt/skills/user/X/ or "Context"] | Identity anchor |
| 1 | MASTER | [Your master file path] | State, progress, session |
| 2 | [TRUTH] | [Your source-of-truth location] | Primary reference |
| 3 | [SECONDARY] | [Optional additional layer] | Comparison/validation |

### Counter (BOND-LEVEL)

**⚠️ CRITICAL: Counter rule lives in MEMORY EDITS, not here.**

Why? If counter is only in your SKILL.md, it fails when you change topics:
1. Working on project → SKILL is hot → counter works
2. Topic shifts (side discussion, new subject)
3. Project SKILL deprioritized in Claude's attention
4. Counter drops

**Solution:** Add this to your Claude memory edits:
```
BOND Counter: Line 1. [emoji] N/LIMIT. LIMIT←CONFIG (default 10). Reset→N:=1 on {Sync}|{Full Restore}|new. 🗒️←(N≤LIMIT), 🟡←(N>LIMIT), 🟠←(N≥15), 🔴←(N≥20). ALWAYS.
```

**Then add to your SKILL.md or OPS file:**
```
## CONFIG
counter_limit: 10
```

**QAIS users (Tier 2+ with MCP):** Also store in QAIS for redundancy:
```
qais_store("CONFIG", "counter_limit", "10")
```

The rule is generic (BOND). The value is yours (CONFIG). If memory resets, file or QAIS recovers your limit.

Memory edits are injected into EVERY conversation regardless of topic. Counter survives topic drift.

**See COUNTER.md for full specification.**

**Quick Reference:**
```
LIMIT ← CONFIG ∨ 10
🗒️ ← (N ≤ LIMIT)
🟡 ← (N > LIMIT)
🟠 ← (N ≥ 15)
🔴 ← (N ≥ 20)
Reset: N := 1 on {Sync} | {Full Restore} | new conversation
```

### Commands

| Command | Purpose | Your Tier |
|---------|---------|-----------|
| `{Sync}` | Read + ground + reset counter | All tiers |
| `{Save}` | Write proven work (BOTH must agree) | Tier 2+ |
| `{Restore}` | Full reload from files | Tier 2+ |
| `{ArtD}` | Restore artifacts to sidebar | Tier 3 |
| [Add custom commands as needed] | | |

**Save Location:** Claude routes saves by default (bonfires → MASTER+Memory, code → files). You can specify: "Save that to MASTER" or "Put that in memory." If memory is full, say "overflow to MASTER."

### Critical Rules

| Rule | Meaning |
|------|---------|
| **Identify=Execute** | If Claude notes something needs updating, do it NOW. No "read-only mode." |
| **Both Agree** | {Save} requires both human and Claude to confirm before writing. |
| **Code > Prose** | If you have working code/examples, THAT is truth. Descriptions are secondary. |
| **Proof Required** | Milestones need evidence: screenshot, test output, or explicit confirmation. |

---

## 7. CROSS-INSTANCE CONTINUITY

### Your Tier Determines Your Flow

| Tier | Setup | Continuity Method |
|------|-------|-------------------|
| **1** | Web/App (Pro $20+) | Memory + paste SKILL each session |
| **2** | Desktop + MCP | Memory + file sync ({Sync} automated) |
| **3** | Desktop + MCP + Skill | Full automation (SKILL always in context) |

**Don't have MCP?** BOND still works - you paste SKILL content and Claude reads from memory. Less automated, same principles.

### How Memory Works Across Sessions

```
SESSION ENDS
    ↓
Claude's memory extracts key facts (automatic)
    ↓
MASTER file preserves detailed state (if Tier 2+)
    ↓
SKILL stays in context (if Tier 3) or paste at start (Tier 1-2)
    ↓
NEW SESSION BEGINS
    ↓
Memory provides broad context
    ↓
{Sync} or {Restore} pulls detailed state
```

### First Message Protocol

**Tier 1 (Web Only):**
```
[Paste your SKILL content, then say:]
"Continuing [PROJECT NAME] work. Last session: [brief summary]"
```

**Tier 2 (Desktop + MCP):**
```
"[PROJECT NAME] work. {Sync}"
```

**Tier 3 (Full Pipeline):**
```
"[PROJECT NAME] work. {Sync} then {ArtD}"
```

### What Gets Preserved Where

| Information | Memory | MASTER | SKILL |
|-------------|--------|--------|-------|
| Identity/relationship | ✅ | | ✅ |
| Current milestone/status | ✅ | ✅ | |
| Detailed progress | | ✅ | |
| Core axioms | ✅ | | ✅ |
| Session history | | ✅ | |
| File locations | ✅ | ✅ | ✅ |

### Recovery from Drift

If Claude seems confused or off-track:

1. **Quick fix:** Remind Claude of a core mantra
2. **Medium fix:** Call `{Sync}` to re-read state
3. **Full fix:** Call `{Restore}` or paste SKILL + say "Reset to core identity"

### Memory Limits

Claude's memory has a cap (~30 items). Prioritize:
- Project name and your name
- Current status/milestone
- Key file locations
- 2-3 critical axioms
- Active anti-patterns

Don't try to store: detailed history, all mantras, full architecture. That's what MASTER and SKILL files are for.

---

## 8. MILESTONES (Optional)

| # | Name | Date | Key Insight |
|---|------|------|-------------|
| 1 | [First milestone] | [Date] | [What was proven/achieved] |

Track your progress. Each milestone is a closed chapter - a bonfire. 🔥

---

## 9. SESSION LOG (Optional)

| Session | Date | Summary |
|---------|------|---------|
| 1 | [Date] | [What happened] |

---

## 10. CUSTOMIZATION NOTES

### Adapting This Template

**For Writers:**
- Layer 1: VOICE (style guide)
- Layer 2: DRAFTS (work in progress)
- Layer 3: PUBLISHED (final versions)
- Milestones → Completed pieces

**For Researchers:**
- Layer 1: THESIS (core argument)
- Layer 2: NOTES (research findings)
- Layer 3: SOURCES (bibliography)
- Milestones → Chapters/sections complete

**For Developers:**
- Layer 1: SPEC (requirements)
- Layer 2: CODE (implementation)
- Layer 3: TESTS (validation)
- Milestones → Features shipped

**For Business:**
- Layer 1: STRATEGY (goals)
- Layer 2: PROJECTS (active work)
- Layer 3: METRICS (measurements)
- Milestones → Objectives achieved

---

## QUICK START

1. Fill in all [BRACKETED] sections
2. Delete instruction comments
3. Save as SKILL.md in your skill folder (Tier 3) or keep for pasting (Tier 1-2)
4. Create MASTER.md using MASTER_TEMPLATE.md
5. Start a session with the First Message Protocol for your tier
6. Work naturally, call {Sync} every ~10 messages
7. Call {Save} when you complete something worth preserving

---

🔥 **BOND: The Bonfire Protocol**
*Keep the fire burning across sessions.*
