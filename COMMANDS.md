# COMMANDS REFERENCE
## BOND: The Bonfire Protocol

*Bidirectional Ongoing Navigation & Drift-prevention*

---

## Core Commands (The Two Buttons)

### {Sync} - Button A

**Purpose:** Read files, ground in truth, reset counter

**When to use:**
- Start of every session
- Every ~10 messages (or when counter hits X/X)
- After Claude seems confused or off-track
- When switching tasks within a project

**What Claude does:**
1. Reads SKILL.md (identity layer)
2. Reads MASTER.md (state layer)
3. Optionally reads source-of-truth files if task requires
4. Resets sticky counter to 1/X
5. Confirms sync complete

**Tier availability:**
- Tier 1: Manual (paste files or key sections)
- Tier 2+: Automated (Claude reads from filesystem)

---

### {Save} - Button B

**Purpose:** Write proven work to files

**When to use:**
- Bonfire achieved (with proof)
- Session ending with progress to preserve
- Important decision made

**The Protocol (Bidirectional Agreement):**
1. One party proposes save (human or Claude)
2. Other party confirms or raises concerns
3. Both agree → Claude writes
4. Never write without agreement

**Tier availability:**
- Tier 1: Manual (you update files yourself)
- Tier 2+: Automated (Claude writes to filesystem)

---

## Supporting Commands

| Command | Purpose | Tier |
|---------|---------|------|
| `{Restore}` | Full reload of all files | 2+ |
| `{ArtD}` | Restore artifacts to sidebar | 3 |
| `{Tick}` | Quick status check (no file read) | All |
| `{Relational}` | Architecture alignment check | 2+ |
| `{Drift?}` | Self-check for drift | All |

---

## The Sticky Counter

**Format:** `🗒️ N/X`

- N = messages since last {Sync}
- X = your threshold (default 10)
- At X/X → {Sync} recommended
- Resets to 1/X after {Sync}

---

## BOND Rules

| Rule | Meaning |
|------|---------|
| **Identify=Execute** | Notice it → Do it NOW |
| **Both Agree** | {Save} needs confirmation from both |
| **Code > Prose** | Trust working examples over descriptions |
| **Proof Required** | Bonfires need evidence |

---

## Custom Commands

Add domain-specific commands in your SKILL.md:

| Example | Domain | Action |
|---------|--------|--------|
| `{Voice}` | Writing | Review style guide |
| `{Test}` | Dev | Run test suite |
| `{Research}` | Academic | Search sources |

---

🔥 **BOND: The Bonfire Protocol**
*Keep the fire burning across sessions.*
