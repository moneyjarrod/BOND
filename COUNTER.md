# COUNTER.md
## The BOND Response Schema

---

# ⚡ CORE DEFINITION

```
User provides «tN/L» in every message
N = user's count, L = user's limit
Claude READS, never auto-increments
User = source of truth
```

| Source | Rule |
|--------|------|
| User provides «tN/L» | Claude parses N and L |
| User omits tag | Claude asks for it |
| User resets via {Sync} or {Full Restore} | N resets to 1 |

---

# ⚡ PREREQUISITE: Echo-Only Rule

**The principle (non-negotiable):** Claude echoes the emoji from the user's tag.
Claude does NOT compute the emoji independently.

This was learned over 80+ sessions of drift. Even with correct math rules
in memory, Claude's semantic processing overrides math ("at the limit *feels*
red"). The fix: AHK computes, Claude echoes.

Get this rule into Claude's persistent context. Recommended: memory edit.
```
BOND Counter: Read user's «tN/L emoji» tag. Echo THEIR emoji exactly.
Do not compute emoji independently. User display is source of truth.
```

Alternatives (if memory slots are full): SKILL.md section, Project instructions,
or any method that keeps the rule in Claude's context across topic drift.
See SETUP_GUIDE.md for reliability comparison.

---

# ⚡ CORE PLACEMENT

```
Response[0] := [emoji] N/L
```

---

# ⚡ CORE FORMAT

```
User tag: «tN/L emoji»
Claude: echo THEIR emoji exactly + N/L

Do NOT compute emoji independently.
The AHK script computes the correct emoji client-side.
Claude's only job: read the tag, echo the emoji.
```

**AHK-side math (for reference — Claude does NOT evaluate this):**
```
🗒️ ← (N ≤ L)
🟡 ← (N > L)
🟠 ← (N ≥ 15)
🔴 ← (N ≥ 20)

Stacking:
🟡🟠 ← (N > L) ∧ (N ≥ 15)
🟡🔴 ← (N > L) ∧ (N ≥ 20)
```

**Why echo-only?** Claude repeatedly drifted on emoji computation even with
correct math rules in memory. Semantic pressure ("at the limit feels red")
overrides math. Single-source fix: AHK computes, Claude echoes. (B65+S81)

---

# ⚡ CORE RESETS

```
N := 1 on:
  - {Sync}
  - {Full Restore}
  - new conversation

N unchanged on:
  - {Save}
  - {Chunk}
  - {Crystal}
  - task completion
  - bonfire declaration
```

---

## Extended Reference

### Response Schema

```
BOND_Response {
    line[0]: Counter,    // REQUIRED — first line of every response
    line[1..n]: Content
}

Counter {
    emoji: 🗒️ | 🟡 | 🟠 | 🔴 | 🟡🟠 | 🟡🔴,
    N: int,    // from user's «tN/L» tag
    L: int     // from user's «tN/L» tag
}
```

---

### User Tag Format

```
«tN/L»

Examples:
  «t1/10»   → first turn, limit 10
  «t5/10»   → fifth turn, limit 10
  «t12/10»  → twelfth turn, over limit
  «t3/20»   → third turn, limit 20
```

The user increments N themselves each message. Claude never modifies N.
Claude reads both values and displays the appropriate emoji + N/L.

---

### Implementation Location

Counter rule → memory edits (survives topic drift)

Memory edit format (copy this):
```
BOND Counter: Read user's «tN/L emoji» tag. Echo THEIR emoji exactly.
Do not compute emoji independently. User display is source of truth.
```

**Why this changed (S81):** The previous memory edit included math rules
(🗒️←N≤L, etc). Claude repeatedly drifted on computation despite correct rules.
Removing math from Claude's memory and letting AHK be the single emoji source
eliminates the drift entirely.

---

### Missing Tag Protocol

```
IF user omits «tN/L»:
  Ask user to include their count
  Do NOT guess or auto-assign
```

---

### Validator

`bond_counter_validator.py` — AHK-side reference implementation

This validator contains the math for computing emojis. It is used by AHK
and for testing — NOT by Claude. Claude echoes the user's emoji.

```python
from bond_counter_validator import get_counter_display
display = get_counter_display(n=10, limit=10)  # "🗒️ 10/10"
display = get_counter_display(n=11, limit=10)  # "🟡 11/10"
```

---

🔥 BOND: The Bonfire Protocol
