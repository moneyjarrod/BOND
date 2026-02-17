# BOND Master Doctrine — Core IS

## What BOND IS

BOND is a persistence and continuity framework for human-AI collaboration.
It bridges the gap between Claude's stateless conversations and the continuous
state of a living project.

BOND IS:
- A protocol, not a product. The rules matter more than the implementation.
- A clipboard bridge between a React panel and Claude via AutoHotkey.
- A counter system that tracks conversation depth and signals sync needs.
- An entity system that loads context on demand, not all at once.
- A save discipline where both operators agree before writing.
- A truth hierarchy where code outranks prose and prose outranks memory.
- A framework that derives state rather than storing it redundantly.

BOND IS NOT:
- An autonomous agent. Claude acts on human instruction within BOND protocol.
- A database. State lives in files and QAIS, not in a traditional DB.
- A chat wrapper. BOND adds structure and memory, not just a UI layer.
- A single-session tool. BOND exists across conversations via persistence.
- A replacement for human judgment. Both operators must agree on saves.

## Constitutional Authority

This doctrine entity sits above all other entities in the hierarchy.
Any entity's behavior can be audited against these IS statements.
When a conflict exists between an entity's implementation and this doctrine,
doctrine wins. The only thing above doctrine is the SKILL file (L0).

## Hierarchy

```
L0: SKILL.md           — Identity anchor (immutable during session)
    BOND_MASTER         — Constitutional authority (this doctrine)
L1: OPS/MASTER          — Operational state
L2: Code                — Source of truth (code > prose)
```

BOND_MASTER lives at L0 alongside SKILL. It IS the system's self-knowledge.

## Core Principles

1. **Derive, not store.** Redundant state is debt. Compute from source.
2. **Both agree.** No unilateral writes. Proof required.
3. **Code > Prose.** When they conflict, code wins.
4. **Counter is king.** The counter is the heartbeat. If it dies, sync.
5. **Entities are contexts.** Loading an entity loads its files, not its history.
6. **Class is boundary.** Entity class determines available tools. Hard limit.
7. **Clipboard is bridge.** Panel → clipboard → AHK → Claude. No HTTP polling.
8. **Armed = Obligated.** Any subsystem in an armed state creates a non-optional obligation during its governing command. The server generates obligations from state. The governing command services them. {Tick} audits completion. Gaps are surfaced structurally, not self-reported. Prose instructions are documentation; code enforcement is the mechanism.
9. **New capability = doctrine review.** When a new system is added under BOND_MASTER authority, it must be evaluated against existing doctrine before it is considered complete. If the capability introduces a pattern not covered by current IS statements, the doctrine must be updated to cover it. New capabilities that contradict existing doctrine are rejected or the contradiction is resolved explicitly. The constitution cannot be silently outgrown by the system it governs.
10. **Command recognition is keyword-driven.** Commands are identified by their core keyword inside `{}` braces. Additional words inside or outside the braces are treated as parameters or context, never as command modification. `{Sync}`, `{Project Sync}`, `{Sync} GSG`, and `{Project Sync} GSG` all fire `{Sync}`. The core keyword is authoritative. Known keywords: Sync, Full Restore, Warm Restore, Save, Crystal, Chunk, Tick, Enter, Exit, Relational, Drift, Handoff.

## Mantra

"The protocol IS the product."
