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

### Sticky Counter

Every reply ends with `🗒️ N/X`. Default is 10. Adjust X based on your work:
- Fast iteration: `5` (sync more often)
- Deep focus: `15` (fewer interruptions)
- Complex project: `10` (balanced)

At X/X, {Sync} recommended.

**Counter Colors (MANDATORY when triggered):**
- `🗒️ N/X` = Normal (within limit)
- `🟡 N/X` = Past YOUR limit (LIMIT < N < 15)
- `🟠 N/X` = Dangerous (15 ≤ N < 20)
- `🔴 N/X` = Critical (N ≥ 20)

**PRIORITY: Universal thresholds (15, 20) ALWAYS override personal limits.**
Example: If your limit is 15 and you're at 16, that's 🟠 not 🟡.

**CRITICAL - What Resets the Counter:**
| Action | Resets? | Why |
|--------|---------|-----|
| `{Sync}` | ✅ YES | Fresh context from files |
| New conversation | ✅ YES | Clean slate |
| `{Save}` | ❌ NO | Task done ≠ context fresh |
| `{Chunk}` | ❌ NO | State snapshot only |
| Bonfire declared | ❌ NO | Milestone ≠ refresh |
| Compaction | ❌ NO | Resume at 🟠 15/X if lost |

**⚠️ COMMON MISTAKE - {Save} Does NOT Reset:**
Claude may conflate "task complete" with "counter reset." This is WRONG.
- {Save} = "I wrote to files" → Counter INCREMENTS (report is a message)
- {Sync} = "I read from files" → Counter RESETS to 1

The counter tracks CONTEXT DEGRADATION, not task completion.
Only READING fresh context resets drift. WRITING does not.

Example of CORRECT behavior:
```
User: {Save}
Claude: [writes to files, reports success] 🗒️ 7/10  ← NOT 1/10
```

If Claude loses count (compaction, confusion), default to `🟠 15/X` and recommend {Sync}.

**Emotional Carryover (Anti-Pattern):**
After {Sync}, counter is 1 and state is 🗒️. Do NOT carry forward the previous caution color. The reset is complete.

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
