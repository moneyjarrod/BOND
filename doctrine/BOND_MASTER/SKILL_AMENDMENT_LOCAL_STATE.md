# SKILL.md Amendment — Local State Routing

## Changes Required

The SKILL.md at `/mnt/skills/user/bond/SKILL.md` needs the following updates.
Full spec: `doctrine/BOND_MASTER/LOCAL_STATE_ROUTING.md`

---

### 1. Add routing rule (new section, after line ~91 or in a logical position)

ADD:
```
## LOCAL STATE ROUTING
All session state commands ({Chunk}, {Handoff}, {Tick}) route output to the active entity's local state/ subdirectory. If no entity active, route to global state/. Path resolution: entity active → doctrine/{entity}/state/{file}. No entity → state/{file}. Auto-create state/ subdirectory on first write. active_entity.json and config.json always remain global.
```

---

### 2. Line 51 — Warm Restore chunk check

CURRENT:
```
  2) Check state/session_chunks.md for accumulated chunks.
```

REPLACE WITH:
```
  2) Check entity-local state/session_chunks.md for accumulated chunks (doctrine/{entity}/state/ if entity active, else global state/).
```

---

### 3. Line 54 — Warm Restore chunk clear

CURRENT:
```
  5) Clear state/session_chunks.md.
```

REPLACE WITH:
```
  5) Clear entity-local state/session_chunks.md.
```

---

### 4. Line 82 — Command summary (Chunk reference)

CURRENT (partial):
```
{Chunk} session snapshot -> append to state/session_chunks.md
```

REPLACE WITH:
```
{Chunk} session snapshot -> append to entity-local state/session_chunks.md (doctrine/{entity}/state/ if entity active, else global state/)
```

---

### 5. Line 90 — Tick reference

CURRENT:
```
{Tick} -> Panel button hits /api/sync-health, writes state/tick_output.md.
```

REPLACE WITH:
```
{Tick} -> Panel button hits /api/sync-health, writes entity-local state/tick_output.md (doctrine/{entity}/state/ if entity active, else global state/).
```

---

### 6. Add to Handoff section (wherever {Handoff} write behavior is defined)

ADD or REPLACE any global path reference:
```
{Handoff} writes to entity-local state/handoff.md (doctrine/{entity}/state/ if entity active, else global state/).
```

---

## Panel Impact

Panel code that reads/writes these paths needs the same routing logic:
- Read active_entity.json (always global)
- If entity set → resolve doctrine/{entity}/state/ for all session state reads/writes
- If null → use global state/

## Summary

5-6 line changes in SKILL.md. One new LOCAL_STATE_ROUTING.md already written to BOND_MASTER. No migration needed — existing global state becomes the no-entity fallback.
