# BOND Entities — Four-Class Architecture (B69)

## The Four Classes

| Class | Nature | Tools | Growth |
|-------|--------|-------|--------|
| Doctrine | Static IS | Files + ISS | None — immutable |
| Project | Bounded workspace | Files + QAIS + Heatmap + Crystal + ISS | Bounded by CORE |
| Perspective | Unbounded growth | Files + QAIS + Heatmap + Crystal | Unlimited |
| Library | Reference shelf | Files only | None — read-only |

## Class IS Statements

### Doctrine
- IS: Immutable truth. Constitutional authority.
- IS: Self-auditable. ISS validates code against IS statements.
- IS NOT: Growable. Doctrine doesn't learn — it defines.
- Tools: Filesystem (read doctrine files) + ISS (audit/validate).
- Example: BOND_MASTER, PROJECT_MASTER, your doctrine entities.

### Project
- IS: A bounded workspace with a mission.
- IS: The most capable class — all tools available.
- IS: Governed by a CORE file (~500 tokens) that defines boundaries.
- IS NOT: Open-ended. CORE constrains scope.
- Tools: Files + QAIS + Heatmap + Crystal + ISS.
- CORE file: Loaded once, refreshed on {Sync}. Counter cycle IS the refresh timer.
- Example: Your project entity.

### Perspective
- IS: An unbounded knowledge domain that grows through conversation.
- IS: Free to accumulate seeds, crystals, and connections.
- IS: Narratively continuous. Each perspective maintains a local QAIS field (`data/perspectives/{entity}.npz`) that accumulates context independently of the global field.
- IS NOT: Policed. No ISS — growth shouldn't be validated against fixed rules.
- IS NOT: Globally entangled. Perspective fields are isolated from the global QAIS field.
- Tools: Files + QAIS + Heatmap + Crystal.
- Local Field: Two .npz files per perspective, created automatically. Seed field (`{entity}.npz`) for vine lifecycle. Crystal field (`{entity}_crystal.npz`) for narrative continuity. Entity Warm Restore queries crystal field. Global Warm Restore does not touch perspective fields. Exclusive routing: perspective active → crystal writes local only (S116).
- Field Isolation: Perspective fields are independent. Linked perspectives share seed resonance through the vine lifecycle but do not access each other's local fields.
- Example: User-created perspectives (P1, P2, etc.).

### Library
- IS: A reference shelf. Static knowledge for lookup.
- IS: The simplest class — just files.
- IS NOT: Active. No tools beyond reading.
- Tools: Filesystem only.
- Example: Reference documents, archives.

## Boundaries

Class boundaries are HARD:
- Cross-class tools are unavailable, not just hidden.
- UI teaches architecture by showing what's possible per class.
- An entity's class is set in its entity.json and does not change without deliberate reclassification.

## Class Linking Matrix

Links load .md files during {Sync} and create an expectation of interaction. If the active entity's class cannot use the linked entity's tools, the link creates a misleading invitation. Links are filtered by class compatibility:

| Active Class | Can Link To |
|---|---|
| Doctrine | Doctrine, Project, Library |
| Project | Doctrine, Project, Perspective, Library |
| Perspective | Project, Perspective, Library |
| Library | Doctrine, Library |

Rule: **Doctrine and Perspective never link directly.** Their tool boundaries are incompatible — doctrine uses ISS, perspectives use QAIS. Neither can fulfill the other's expectations.

This is enforced at three levels:
1. **UI** — Link dropdown only shows class-compatible entities.
2. **Server** — `/api/state/link` validates the pairing and returns 403 on forbidden links.
3. **Protocol** — Claude flags violations in conversation. {Tick} audits existing links for compliance.

Even if the user requests a forbidden link, the system refuses. The wall is structural, not advisory.

## Link Badges (S118)

Two distinct visual signals on entity cards:

- **Blue LINKED** — Entity is actively loaded as context in the current session. Appears when the active entity's links array includes this entity. Session-level, temporary.
- **Purple 🔗 N** — Same-class peer references only. Counts how many entities of the SAME class permanently link to this entity in their entity.json. Cross-class links (project→perspective) do NOT count toward the purple badge.

Purple = "peers referencing you." Blue = "active in this session." Cross-class governance flows through PROJECT_MASTER's PERSPECTIVE_REGISTRY, not through badge clutter on perspective cards.

## Cross-Class Consultation

When doctrine needs perspective input (or vice versa), the **operator is the bridge**:

1. Exit the current entity (or work unscoped).
2. Run the consultation in the appropriate context.
3. Carry the result into the target entity as user input.
4. The target entity evaluates it against its own principles.

The tool wall stays intact. Information flows through the operator, not around the boundary. No new infrastructure is needed — the protocol pattern is: **class boundaries restrict tool access, not information access.**

## Entity Structure

Every entity lives in `doctrine/ENTITY_NAME/` and contains:
- `entity.json` — class, tools, display_name
- One or more `.md` files — the entity's knowledge

## State Pointer

`state/active_entity.json` holds the current entity:
```json
{
  "entity": "CM",
  "class": "doctrine",
  "path": "...",
  "entered": "2026-02-07T..."
}
```

- Panel writes on Enter, clears on Exit.
- {Sync} follows the pointer — reads path if set, skips if null.
- Switch overwrites — no Exit needed before Enter.

## Naming

- Doctrine/Project: Descriptive names (BOND_MASTER, CM)
- Perspectives: User-created via + button (auto-numbered P1, P2, etc.)
- Library: Descriptive names
- Files within: `[ENTITY]_[topic].md` pattern

## Mantra

"The class IS the filter. The CORE IS the boundary."
