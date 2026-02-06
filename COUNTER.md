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

# ⚡ CORE PLACEMENT

```
Response[0] := [emoji] N/L
```

---

# ⚡ CORE FORMAT

```
L ← from user's «tN/L» tag (default 10 if not specified)

🗒️ ← (N ≤ L)
🟡 ← (N > L)
🟠 ← (N ≥ 15)
🔴 ← (N ≥ 20)
```

**Stacking:**
```
🟡🟠 ← (N > L) ∧ (N ≥ 15)
🟡🔴 ← (N > L) ∧ (N ≥ 20)
```

**Evaluation:**
```
N=10, L=10:  10 ≤ 10 = TRUE  → 🗒️
N=11, L=10:  11 > 10 = TRUE  → 🟡
N=15, L=10:  15 > 10 ∧ 15 ≥ 15 → 🟡🟠
N=15, L=20:  15 > 20 = FALSE, 15 ≥ 15 = TRUE → 🟠
```

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
BOND Counter: Parse «tN/L» from user. N=count, L=limit. Display: [emoji] N/L. 
🗒️←(N≤L), 🟡←(N>L), 🟠←(N≥15), 🔴←(N≥20). 
Reset on {Sync}|{Full Restore} only. User=source of truth. Never auto-increment.
```

---

### Missing Tag Protocol

```
IF user omits «tN/L»:
  Ask user to include their count
  Do NOT guess or auto-assign
```

---

### Validator

`bond_counter_validator.py` — single source of truth

```python
from bond_counter_validator import get_counter_display
display = get_counter_display(n=10, limit=10)  # "🗒️ 10/10"
display = get_counter_display(n=11, limit=10)  # "🟡 11/10"
```

---

🔥 BOND: The Bonfire Protocol
