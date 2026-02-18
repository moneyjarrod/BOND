# Local State Routing — Amendment (S120)

## The Rule

When an entity is active (`state/active_entity.json` points to it), all session state commands write to that entity's local `state/` subdirectory. When no entity is active, session state writes to the global `state/` directory.

This applies to ALL entity classes: project, perspective, doctrine, library.

## What Routes Locally

| Command | Output File | Location When Entity Active | Location When No Entity |
|---------|------------|----------------------------|------------------------|
| {Chunk} | session_chunks.md | `doctrine/{entity}/state/` | `state/` |
| {Handoff} | handoff.md | `doctrine/{entity}/state/` | `state/` |
| {Tick} | tick_output.md | `doctrine/{entity}/state/` | `state/` |
| {Crystal} | QAIS crystal field | Already local ✓ | Global field |
| {Save} | Target file(s) | Entity's own directory | As specified |

## What Stays Global

| File | Reason |
|------|--------|
| `state/active_entity.json` | Pointer TO the entity — must be accessible before entity is known |
| `state/config.json` | User preferences — not entity content |

## Routing Logic

```
On any state-writing command:
  1. Read state/active_entity.json
  2. If entity is set:
     → resolve path: doctrine/{entity}/state/
     → if state/ subdirectory doesn't exist, create it
     → write to that path
  3. If entity is null:
     → write to global state/
```

## Auto-Creation

Entity `state/` subdirectories are created on first write, not provisioned in advance. When a command needs to write and the directory doesn't exist, create it silently. Same pattern as perspective QAIS fields — created on first use.

## Warm Restore Scoping

Warm Restore reads from the active entity's local state:
- **Entity active:** reads `doctrine/{entity}/state/handoff.md` and `doctrine/{entity}/state/session_chunks.md`
- **No entity active:** reads `state/handoff.md` and `state/session_chunks.md`
- **Cross-entity:** Warm Restore NEVER reads another entity's state. If you're in GSG, you don't see P11's handoff. If you're in P11, you don't see GSG's chunks.

## Full Restore Scoping

Same routing as Warm Restore. Full Restore reads deeper but from the same scoped location.

## {Sync} Behavior

{Sync} reads `state/active_entity.json` (global — always), then loads entity files from the entity's own directory. Session state reads (if any) come from the entity's local `state/` subdirectory.

## Panel Integration

Panel commands that read/write session state must route through the same logic:
- Tick button → writes to entity-local `state/tick_output.md`
- Handoff display → reads from entity-local `state/handoff.md`
- Chunk accumulation → entity-local `state/session_chunks.md`

## Directory Structure Examples

```
doctrine/
  GSG/
    CORE.md
    ARCHITECTURE_MAP.md
    REFERENCE_DOMAINS.md
    entity.json
    state/                    ← GSG session state
      session_chunks.md
      handoff.md
      tick_output.md
  P11-Plumber/
    entity.json
    ROOT/
    state/                    ← P11 session state
      session_chunks.md
      handoff.md
      tick_output.md
  BOND_MASTER/
    entity.json
    BOND_PROTOCOL.md
    state/                    ← BM session state (if worked on directly)
      session_chunks.md
      handoff.md
      tick_output.md

state/                        ← Global fallback (no entity active)
  active_entity.json          ← Always global
  config.json                 ← Always global
  session_chunks.md           ← Used when no entity active
  handoff.md                  ← Used when no entity active
  tick_output.md              ← Used when no entity active
```

## Migration

Existing global `state/session_chunks.md` and `state/handoff.md` remain as the no-entity fallback. No migration of existing content needed — new local state directories populate as sessions occur within entities. Old global state becomes the "outside any entity" bucket, which is what it should have always been.

## Rationale

- Stops state bloat in shared directory
- Makes each entity self-contained (portable, archivable, deletable)
- Aligns with existing local field pattern (QAIS, Crystal already route locally)
- Closes the gap between class boundary theory and filesystem reality
- Warm Restore context is always relevant to the active entity — no cross-contamination

## Mantra

State flows to where the work lives. Not to a shared drain.
