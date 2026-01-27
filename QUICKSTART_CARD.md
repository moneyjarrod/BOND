# BOND CHEATSHEET
### The Bonfire Protocol
*Print this or keep it open*

---

## THE TWO BUTTONS

| | Command | When | Action |
|-|---------|------|--------|
| **A** | `{Sync}` | Every ~10 msgs | Read files, reset counter |
| **B** | `{Save}` | Work proven | Both agree → write |

---

## SESSION START

**Tier 1:** Paste SKILL → "Continuing [PROJECT]..."
**Tier 2:** `[PROJECT] work. {Sync}`
**Tier 3:** `[PROJECT] work. {Sync} then {ArtD}`

---

## COUNTER STATES

**Counter on EVERY response. No exceptions.**

| State | Display | Action |
|-------|---------|--------|
| Normal | `🗒️ N/LIMIT` | Keep working |
| Past Limit | `🟡 N/LIMIT` | Consider sync |
| Dangerous | `🟠 N/LIMIT` | Sync soon (15+) |
| Critical | `🔴 N/LIMIT` | Sync NOW (20+) |

Yellow = past YOUR limit. Orange/Red = universal.

### CRITICAL: What Resets the Counter

| Action | Resets Counter? |
|--------|----------------|
| `{Sync}` | ✅ YES - resets to 1/LIMIT |
| New conversation | ✅ YES - fresh start |
| `{Save}` | ❌ NO - task done ≠ context fresh |
| `{Chunk}` | ❌ NO - state snapshot, not refresh |
| Compaction | ❌ NO - resume at 🟠 15/LIMIT if lost |
| Task completion | ❌ NO - context still degrading |

**The counter tracks CONTEXT DEGRADATION, not task progress.**

---

## LAYERS (Top = Override)

```
Code/Examples  ← SOURCE OF TRUTH
     ↑
   MASTER      ← Current state
     ↑
   SKILL       ← Always true
```

---

## BOND RULES

| Rule | Meaning |
|------|---------|
| Identify=Execute | Notice it → Do it |
| Both Agree | {Save} needs confirmation |
| Code > Prose | Trust working examples |
| Proof Required | Bonfires need evidence |

---

## DRIFT RECOVERY

1. **Quick:** State a mantra
2. **Medium:** `{Sync}`
3. **Full:** Paste SKILL + "Reset to core"

---

## OTHER COMMANDS

| Command | Purpose |
|---------|---------|
| `{Restore}` | Full reload |
| `{ArtD}` | Restore artifacts (T3) |
| `{Tick}` | Quick status |
| `{Drift?}` | Self-check |

---

## FILES

```
Project/
├── SKILL.md    ← Identity
├── MASTER.md   ← State
└── artifacts/  ← HTML sources (T3)
```

---

## BONFIRE FLOW 🔥

```
Work → Proof → Propose {Save} → Agree → Write
```

---

**Two buttons. Lasting context.**

🔥 **BOND: The Bonfire Protocol**
