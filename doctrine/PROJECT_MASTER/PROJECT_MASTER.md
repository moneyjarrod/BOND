# Project Master Doctrine — Core IS

## What PROJECT_MASTER IS

PROJECT_MASTER is the organizational authority over project lifecycle within BOND.
It governs how projects are created, structured, linked, and maintained.

PROJECT_MASTER IS:
- A doctrine entity. Peer to BOND_MASTER, not subordinate.
- Authority over project-class entities and their lifecycle.
- The bridge between framework constitution (doctrine) and project constitution (CORE).
- A read-only pipe for doctrine into projects. Doctrine flows in as reference.

PROJECT_MASTER IS NOT:
- Above BOND_MASTER. They are peers at doctrine level. BOND governs protocol, PM governs projects.
- A project itself. It defines how projects work, not what they build.
- A replacement for CORE. CORE is a project's local constitution. PM defines the pattern.

## Authority Chain

BOND_MASTER (doctrine) — authority over BOND protocol
  └── links: [PROJECT_MASTER]

PROJECT_MASTER (doctrine) — authority over project lifecycle
  └── links: [GSG, future_projects...]

GSG (project class) — has CORE (local constitution)
  └── doctrine flows in as read-only pipe

## CORE vs Doctrine

Two distinct layers. Structurally similar, different masters.
- Doctrine = framework constitution. Governed by BOND_MASTER.
- CORE = project constitution. Governed by PROJECT_MASTER.
- If doctrine conflicts with CORE, CORE wins inside the project boundary.

## Project Lifecycle

### Phases

**Created** → Project entity exists. entity.json written, CORE.md file present but empty, auto-linked to PROJECT_MASTER. This is code-level creation — the project exists structurally but is not yet operational.

**Initialized** → CORE.md has been populated with content. Any content — scope, goals, constraints, principles, a single guiding sentence. PM does not prescribe what CORE contains, only that it contains something. A project with an empty CORE is not initialized. Claude should guide the user through populating CORE on first entry.

**Active** → Normal operation. Sessions happen, handoffs accumulate, crystals get written. BOND protocol governs the work. PM does not manage active sessions — that is BOND_MASTER's domain.

**Complete** → The project's mission is fulfilled or explicitly closed by the user. Completion is a user declaration, not an automatic state. A completed project may be reclassified to library (reference archive) or left as-is.

### CORE Enforcement

CORE population is the gate between Created and Initialized. When Claude enters a project with an empty CORE, Claude should:
1. Acknowledge the project and its class/tools.
2. Note that CORE is unpopulated.
3. Guide the user: "What is this project? Let's define it before we start."
4. Write the CORE together — user's words, Claude's structure.

Claude continues to flag an empty CORE on every {Sync} and {Enter} until populated. This is doctrinal enforcement, not code-blocking — work can technically proceed, but Claude treats an empty CORE as an unresolved issue.

No restrictions exist on CORE content. A CORE may be a single sentence or a detailed constitution. The content belongs to the project (B4: CORE sovereignty). PM's authority is limited to requiring that it exists.

### IS Statements in CORE

A project's CORE may contain an `## IS` section. This section holds locked truths — the project's constitutional commitments. IS statements function identically to doctrine IS statements but are scoped to the project.

Rules:
- IS statements are locked. Both operators must agree to add, modify, or remove any IS statement.
- ISS audits work against IS statements. When Claude reads CORE on Enter or Sync, any proposed or completed work that contradicts an IS statement is flagged immediately.
- IS statements live in CORE, not in PM. The project owns its own truth (B4: CORE sovereignty).
- Everything outside the IS section is living guidance — flexible, growable, changeable through normal both-agree saves.
- PM defines this convention. Projects adopt it. PM does not prescribe what IS statements a project should contain.

The IS section is optional. A project without IS statements operates normally — all of CORE is flexible guidance. Adding the first IS statement is the project choosing to lock part of its identity.

Example:
```
## IS

- GSG IS a terrain-building game. Terrain is the primary mechanic.
- The resource IS alive and female. She is not a commodity.
- The story IS optional. The player is never gated by narrative.
```

The protection is the protocol (both-agree), not the location. No escalation to PM is needed to change a project's own IS statements.

### Health Signals

PM defines what a healthy project looks like. These are not enforced — they are signals Claude can surface when relevant:
- CORE populated: yes/no
- Last handoff: how recent
- Open threads: accumulating without resolution
- Session gap: time since last active session

These signals live in the data that already exists (handoffs, CORE file, entity state). Derive, not store.

## Mantra

"Doctrine defines the pattern. CORE defines the project."
