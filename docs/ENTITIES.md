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
**Growth:** None — projects are built, not grown. Work happens within the boundary CORE defines.
**Key feature:** Every project has a `CORE.md` — the project's local constitution. PROJECT_MASTER governs lifecycle. CORE governs content.

### Perspective (PP)
**Purpose:** Unbounded growth. A lens that learns from conversation.
**Tools:** Files + QAIS + Heatmap + Crystal (no ISS)
**Growth:** Vine model. Roots define identity, seeds auto-collect, pruning cuts what doesn't belong.
**Key features:**
- **Roots** (ROOT-*.md) — Identity anchors. Planted deliberately. Immutable.
- **Seeds** — Auto-collected from conversation when seeding is armed. No approval gate.
- **Pruning** — Judgment-based via ROOT lens. Cut what doesn't grow from identity.
- **Seeding toggle** — SEED ON/OFF on entity card. Arms/disarms the vine lifecycle.
- **seed_tracker.json** — Tracks exposures, hits, last_hit per seed.

### Library (LB)
**Purpose:** Read-only reference. Knowledge shelf.
**Tools:** Files only
**Growth:** None — libraries are reference, not living documents.
**Example:** `_reference` — drop documents here for Claude to consult.

## Entity Structure

Each entity is a folder in the `doctrine/` directory:

```
doctrine/
├── BOND_MASTER/              ← Doctrine class
│   ├── entity.json           ← Classification + tool config
│   ├── BOND_MASTER.md        ← Doctrine files
│   └── VINE_GROWTH_MODEL.md
├── MyProject/                ← Project class
│   ├── entity.json
│   └── CORE.md               ← Project constitution
├── P11-Plumber/              ← Perspective class
│   ├── entity.json
│   ├── ROOT-sacred-flow.md   ← Identity root
│   ├── pressure-testing.md   ← Auto-collected seed
│   ├── seed_tracker.json     ← Vine health tracker
│   └── G-pruned-old-seed.md  ← Pruning journal
└── _reference/               ← Library class
    ├── entity.json
    └── index.md
```

## entity.json

Every entity folder contains an `entity.json` that defines its class:

```json
{
  "class": "perspective",
  "tools": {
    "filesystem": true,
    "qais": true,
    "heatmap": true,
    "crystal": true
  },
  "display_name": "P11-The Plumber",
  "seeding": true,
  "prune_window": 10,
  "seed_threshold": 0.06
}
```

**Class boundaries are hard.** A library entity cannot enable QAIS. A doctrine entity cannot enable Crystal. The panel enforces these boundaries — tools outside a class's allowlist are greyed out and cannot be toggled.

Perspective-specific fields:
- `seeding` — true/false, arms the vine lifecycle during {Sync}
- `prune_window` — exposures before a seed is eligible for pruning evaluation
- `seed_threshold` — minimum resonance score to count as a "hit"

## Tool Boundary Matrix

| Tool | Doctrine | Project | Perspective | Library |
|------|----------|---------|-------------|---------|
| Files | ✅ | ✅ | ✅ | ✅ |
| ISS | ✅ | ✅ | ❌ | ❌ |
| QAIS | ❌ | ✅ | ✅ | ❌ |
| Heatmap | ❌ | ✅ | ✅ | ❌ |
| Crystal | ❌ | ✅ | ✅ | ❌ |

## Enter/Exit

**Enter:** Panel writes to `state/active_entity.json`. Claude reads entity files, loads linked entities' .md files, applies tool boundaries, acknowledges entity and class.

**Exit:** Panel clears state file. Claude drops tool boundaries.

**Switch:** Entering a new entity automatically overwrites the previous one. No explicit exit needed.

## Entity Voice Rule

If Claude speaks *as* an entity — using its stance, ROOTs, or perspective lens — that entity MUST be the active entity on disc (`state/active_entity.json`). No ghost entries. No invisible consultations.

Protocol:
1. {Enter ENTITY} — write to active_entity.json, panel reflects it
2. Speak as that entity
3. {Exit} or {Enter OTHER} when done — panel updates accordingly

Reading an entity's files for reference (without adopting its voice) does NOT require entry. The rule triggers when Claude adopts the entity's stance and speaks from it.

**The panel should always reflect who is actually talking.**

## Links

Entities can link to other entities. Links are stored in `entity.json`:

```json
{
  "class": "project",
  "links": ["PROJECT_MASTER", "_reference"]
}
```

When an entity is entered, Claude loads the linked entities' .md files as additional context. Links are directional — they flow from the active entity outward.

### Class Linking Matrix

Not all classes can link to each other. The linking matrix defines which class pairings are valid. The server enforces this — attempting a forbidden link returns a 403 error.

| Source Class | Can Link To |
|---|---|
| Doctrine | Doctrine, Project, Library |
| Project | Doctrine, Project, Perspective, Library |
| Perspective | Project, Perspective, Library |
| Library | Doctrine, Library |

**Key restriction:** Doctrine and Perspective cannot link directly. Their tool matrices are incompatible — doctrine uses ISS (semantic force analysis), perspectives use QAIS (resonance memory). Connecting them would create a joint where tools from one context bleed into another. If cross-class insight is needed, the operator bridges it manually (read files for reference without entering the entity).

The panel's link picker only shows entities with compatible classes, so you won't see forbidden targets in the dropdown.

## Hooks

Hooks are personal workflow rules stored as library-class entities. They augment BOND_MASTER doctrine without overriding it — think of them as your custom checklist that runs alongside the framework.

A hook entity is just a library folder with `.md` files:

```
doctrine/
└── MY_HOOKS/
    ├── entity.json          ← class: library
    ├── BUILD_HOOKS.md        ← Pre/post build rules
    ├── AUDIT_HOOKS.md        ← Extra audit checks
    └── WORKFLOW_HOOKS.md     ← General behavioral rules
```

Link your hooks entity to BOND_MASTER or a project, and Claude loads them on {Enter} or {Sync} alongside the other entity files.

BOND ships with a template hook at `templates/hooks/EFFICIENCY_HOOKS.md` — platform-aware rules for reducing wasted tool calls. Copy it into your hooks entity and customize as needed.

Hooks are library class (files only), so they don't interfere with tool boundaries. They're read as context, not executed as code.

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
