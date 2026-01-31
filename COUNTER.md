# COUNTER.md
## The BOND Response Schema

---

# ⚡ CORE DEFINITION

```
N := count(user_turns) after last reset
N := N + 1 per user turn
```

| Counts (N := N + 1) | Does Not Count |
|---------------------|----------------|
| User message | Claude response |
| User command | Claude tool call |
| User question | System message |

---

# ⚡ CORE PLACEMENT

```
Response[0] := [emoji] N/LIMIT
```

---

# ⚡ CORE FORMAT

```
LIMIT ← CONFIG ∨ 10

🗒️ ← (N ≤ LIMIT)
🟡 ← (N > LIMIT)
🟠 ← (N ≥ 15)
🔴 ← (N ≥ 20)
```

**Stacking:**
```
🟡🟠 ← (N > LIMIT) ∧ (N ≥ 15)
🟡🔴 ← (N > LIMIT) ∧ (N ≥ 20)
```

**Evaluation:**
```
N=10, LIMIT=10:  10 ≤ 10 = TRUE  → 🗒️
N=11, LIMIT=10:  11 > 10 = TRUE  → 🟡
N=15, LIMIT=10:  15 > 10 ∧ 15 ≥ 15 → 🟡🟠
N=15, LIMIT=20:  15 > 20 = FALSE, 15 ≥ 15 = TRUE → 🟠
```

---

# ⚡ CORE RESETS

```
N := 1 on:
  - {Sync}
  - {Full Restore}
  - new conversation

N := N on:
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
    line[0]: Counter,    // REQUIRED
    line[1..n]: Content
}

Counter {
    emoji: 🗒️ | 🟡 | 🟠 | 🔴 | 🟡🟠 | 🟡🔴,
    N: int,
    LIMIT: int
}
```

---

### Implementation Location

Counter rule → memory edits (survives topic drift)
Counter config → OPS/SKILL file (personal value)

Memory edit format:
```
BOND Counter: Line 1. [emoji] N/LIMIT. LIMIT←CONFIG (default 10). 
Reset→N:=1 on {Sync}|{Full Restore}|new. 
🗒️←(N≤LIMIT), 🟡←(N>LIMIT), 🟠←(N≥15), 🔴←(N≥20). ALWAYS.
```

---

### Config Storage (by tier)

| Tier | Location |
|------|----------|
| 1 | SKILL paste: `counter_limit: 10` |
| 2+ | OPS file CONFIG section |
| 2+ QAIS | File + `CONFIG\|counter_limit\|10` |

---

### Lost Count Protocol

```
IF count_unknown:
  N := 15
  emoji := 🟠
  recommend {Sync}
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
