# BOND Entity System

## Four-Class Architecture

BOND organizes knowledge into four entity classes, each with distinct rules and tool boundaries.

### Doctrine (DC)
**Purpose:** Static truth. IS statements. Immutable method.
**Tools:** Files + ISS
**Growth:** None — doctrine doesn't grow, it IS.
**Example:** BOND_MASTER (the framework's own constitutional authority)

### Project (PC)
**Purpose:** Bounded workspace with a CORE immutable boundary.
**Tools:** Files + ISS + QAIS + Heatmap + Crystal
**Growth:** Growth files track evolution within the CORE boundary.
**Key feature:** Every project has a `CORE.md` — the immutable constraint. Work happens within the boundary CORE defines.

### Perspective (PP)
**Purpose:** Unbounded growth. Seeds that evolve through resonance.
**Tools:** Files + QAIS + Heatmap + Crystal (no ISS)
**Growth:** Seeds grow into fuller documents over time. No fixed boundary.
**Slots:** P01 through P10 are base slots. P10 = Wildcard. Create more as needed.

### Library (LB)
**Purpose:** Read-only reference. Knowledge shelf.
**Tools:** Files only
**Growth:** None — libraries are reference, not living documents.
**Example:** `_reference` — drop documents here for Claude to consult.

## Entity Structure

Each entity is a folder in the `doctrine/` directory:

```
doctrine/
├── BOND_MASTER/          ← Doctrine class
│   ├── entity.json       ← Classification + tool config
│   ├── BOND_MASTER.md    ← Doctrine files
│   └── BOND_PROTOCOL.md
├── MyProject/            ← Project class
│   ├── entity.json
│   ├── CORE.md           ← Immutable boundary
│   └── G-sprint-1.md     ← Growth file
├── P01-Thinking/         ← Perspective class
│   ├── entity.json
│   └── seed.md           ← Seed that grows
└── _reference/           ← Library class
    ├── entity.json
    └── index.md
```

## entity.json

Every entity folder contains an `entity.json` that defines its class:

```json
{
  "class": "project",
  "core": "CORE.md",
  "tools": {
    "filesystem": true,
    "iss": true,
    "qais": true,
    "heatmap": true,
    "crystal": true
  }
}
```

**Class boundaries are hard.** A library entity cannot enable QAIS. A doctrine entity cannot enable Crystal. The panel enforces these boundaries — tools outside a class's allowlist are greyed out and cannot be toggled.

## Tool Boundary Matrix

| Tool | Doctrine | Project | Perspective | Library |
|------|----------|---------|-------------|---------|
| Files | ✅ | ✅ | ✅ | ✅ |
| ISS | ✅ | ✅ | ❌ | ❌ |
| QAIS | ❌ | ✅ | ✅ | ❌ |
| Heatmap | ❌ | ✅ | ✅ | ❌ |
| Crystal | ❌ | ✅ | ✅ | ❌ |

## Enter/Exit

**Enter:** Panel writes to `state/active_entity.json`. Claude reads entity files, applies tool boundaries, acknowledges entity and class.

**Exit:** Panel clears state file. Claude drops tool boundaries.

**Switch:** Entering a new entity automatically overwrites the previous one. No explicit exit needed.

## State Pointer

The active entity is tracked in `state/active_entity.json`:

```json
{
  "entity": "MyProject",
  "class": "project",
  "path": "C:\\BOND\\doctrine\\MyProject",
  "entered": "2026-02-07T10:30:00.000Z"
}
```

When null, no entity is active and {Sync} skips entity loading.
