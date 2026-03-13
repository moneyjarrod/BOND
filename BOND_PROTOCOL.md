# BOND Protocol Detail

Referenced by SKILL.md. Canonical definitions for counter config, save protocol, handoff format, consult requirements.

---

## Counter Config

The AHK bridge owns the tick counter. Claude mirrors the tag verbatim. The bridge emits `«tN/L emoji»` where N is the current tick, L is the session limit, and emoji reflects session state.

### Emoji Scale

The bridge selects emoji based on session state. Claude echoes exactly what the bridge sends — never overrides, never computes.

| Emoji | Condition | Meaning |
|---|---|---|
| 🗒️ | t ≤ L | Normal working pace |
| 🟡 | t > L | Over session limit, winding down |
| 🟠 | t > L, budget pressure noted | Conserving, resource-aware |
| 🔴 | t > L, budget critical | Last drops of budget |
| 🌋 | t > 2×L | Erupted — session blew past all bounds |

**Threshold tuning:** The AHK bridge determines when to transition between emojis based on user context (usage percentage, extra budget, session energy). The conditions above are semantic guidelines, not hard-coded thresholds. The bridge reads the room.

**Claude's role:** Mirror only. First line of every response echoes the user's tag character-for-character. If the user sends 🌋, Claude echoes 🌋. No interpretation, no correction, no suggestion to change emoji.

### Counter Reset

The bridge resets N to 1 and L to the configured session limit at session boundaries. Emoji resets to 🗒️. No carryover between sessions.

### History

- S5 (2026-03-11): 🌋 added for sessions exceeding 2×L. First 🌋 session: S5 GdW (reached 20/10).

---

## Save Protocol

*(To be populated from existing SKILL section 'Both agree' and save_confirmation accidental.)*

---

## Handoff Format

*(To be populated from existing {Handoff} command definition.)*

---

## Consult Requirements

*(To be populated from existing {Consult} command definition.)*

---
