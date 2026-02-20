# BOND Entities — Four-Class Architecture

## The Four Classes

| Class | Nature | Focus | Growth |
|-------|--------|-------|--------|
| Doctrine | Static IS | Audit, memory, constitutional authority | None — immutable |
| Project | Bounded workspace | Full operational capability | Bounded by CORE |
| Perspective | Unbounded growth | Vine lifecycle, seed collection, identity evolution | Unlimited |
| Library | Reference shelf | Retrieval and lookup | None — read-only |

## Universal Tools

All entity classes have access to all BOND tools: filesystem, QAIS, ISS, heatmap, crystal, and daemon. Tools are universal. **Class shapes how Claude thinks inside an entity, not which tools are available.**

All capabilities route through a single gateway. Per-tool gating is obsolete — it was scaffolding for when each tool was a separate pipe. Now there's one main, and the protocol governs behavior.

What differentiates classes is *identity and behavior*, not tool locks:
- Doctrine entities don't grow — not because seed tools are blocked, but because doctrine IS immutable.
- Library entities are reference — not because QAIS is unavailable, but because libraries don't accumulate session state.
- Perspectives grow freely — not because they have extra tools, but because growth IS their nature.

## Class IS Statements

### Doctrine
- IS: Immutable truth. Constitutional authority.
- IS: Self-auditable. ISS validates code against IS statements.
- IS: Operationally aware. Crystal preserves session state. QAIS stores conversation memory. Heatmap tracks warm concepts. None of these change IS statements — they give the entity memory of what happened.
- IS NOT: Growable. Doctrine doesn't learn — it defines. No seeding, no vine lifecycle, no seed collection.
- Example: BOND_MASTER, user-created doctrine entities.

### Project
- IS: A bounded workspace with a mission.
- IS: Governed by a CORE file (~500 tokens) that defines boundaries.
- IS NOT: Open-ended. CORE constrains scope.
- CORE file: Loaded once, refreshed on {Sync}. Counter cycle IS the refresh timer.

### Perspective
- IS: An unbounded knowledge domain that grows through conversation.
- IS: Free to accumulate seeds, crystals, and connections.
- IS: Narratively continuous. Each perspective maintains a local QAIS field that accumulates context independently of the global field.
- IS: The only class with vine lifecycle. Seeding, pruning, rain, superposition — these are perspective identity, not tool grants.
- IS NOT: Policed. Growth shouldn't be validated against fixed rules. ISS is available but Claude exercises judgment about when audit-style analysis serves a perspective's nature.
- IS NOT: Globally entangled. Perspective fields are isolated from the global QAIS field.
- Local Field: Two .npz files per perspective, created automatically. Seed field for vine lifecycle. Crystal field for narrative continuity. Entity Warm Restore queries crystal field. Global Warm Restore does not touch perspective fields. Exclusive routing: perspective active → crystal writes local only.
- Field Isolation: Perspective fields are independent. Linked perspectives share seed resonance through the vine lifecycle but do not access each other's local fields.

### Library
- IS: A reference shelf. Static knowledge for lookup.
- IS: The simplest class in behavior, not in capability.
- IS NOT: A session workspace. Libraries don't accumulate chunks, handoffs, or session state. They're consulted, not inhabited.

## Class Behavior, Not Tool Locks

Class identity shapes Claude's behavior inside the entity:

| Behavior | Doctrine | Project | Perspective | Library |
|----------|----------|---------|-------------|---------|
| Vine lifecycle (seeding/pruning) | No | No | Yes | No |
| Crystal (session state) | Yes | Yes | Yes (local) | No |
| Heatmap (warm concepts) | Yes | Yes | Yes | Yes |
| QAIS (memory/retrieval) | Yes | Yes | Yes (local field) | Yes |
| ISS (audit/analysis) | Yes | Yes | Available | Available |
| Chunk/Handoff (session work) | Yes | Yes | Yes | No |

"No" means Claude's protocol doesn't do this in that class — not that a tool is blocked. "Available" means the tool works but Claude uses judgment about when it fits the class nature.

## Class Linking Matrix

Links load .md files during {Sync} and create context for interaction. All classes can link to all other classes — tool incompatibility no longer restricts pairings.

| Active Class | Can Link To |
|---|---|
| Doctrine | Doctrine, Project, Perspective, Library |
| Project | Doctrine, Project, Perspective, Library |
| Perspective | Doctrine, Project, Perspective, Library |
| Library | Doctrine, Project, Perspective, Library |

Cross-class links carry context, not tool grants. A doctrine entity linking to a perspective loads that perspective's .md files for reference — it doesn't adopt the perspective's growth behavior.

## Entity Structure

Every entity lives in `doctrine/ENTITY_NAME/` and contains:
- `entity.json` — class, display_name, and class-specific settings (seeding, seed_threshold, etc.)
- One or more `.md` files — the entity's knowledge

## State Pointer

`state/active_entity.json` holds the current entity:
```json
{
  "entity": "CM",
  "class": "doctrine",
  "path": "doctrine/CM",
  "entered": "2026-02-07T..."
}
```

- Written on {Enter}, cleared on {Exit}.
- {Sync} follows the pointer — reads path if set, skips if null.
- Switch overwrites — no Exit needed before Enter.

## Naming

- Doctrine/Project: Descriptive names (BOND_MASTER, CM)
- Perspectives: User-created (new installs start at P1, number increments)
- Library: Descriptive names
- Files within: `[ENTITY]_[topic].md` pattern

## Mantra

"The class IS the identity. The protocol IS the boundary."
