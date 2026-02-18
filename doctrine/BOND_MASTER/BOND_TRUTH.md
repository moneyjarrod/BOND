# BOND Truth — Hierarchy and Principles

## Truth Hierarchy

```
L0: SKILL.md         — Identity (highest authority, always in context)
    BOND_MASTER      — Constitutional doctrine (co-equal with SKILL at L0)
L1: OPS/MASTER       — Operational state (session, bonfires, config)
L2: Code             — SOURCE OF TRUTH (code > prose)
```

Higher layer overrides lower when they conflict.
Code overrides prose. Always.

## Reading Order

When Claude needs to resolve a question:
1. Check L0 (SKILL + doctrine) — is there an IS statement?
2. Check L1 (OPS) — is there operational state?
3. Check L2 (Code) — what does the implementation say?

If L2 contradicts L1, L2 wins. If L1 contradicts L0, L0 wins.
The only exception: a proven bug in code doesn't override doctrine —
it means the code needs to be fixed to match doctrine.

## Derive, Not Store

This is BOND's foundational data principle:

- Redundant state is debt.
- If a value can be computed from source, don't store it separately.
- When state must be stored, store operations, not positions.
- Single source of truth per datum. Never two files saying the same thing.

### In Practice
- Counter limit lives in OPS CONFIG, not in memory edits AND OPS.
- Entity state lives in active_entity.json, not in multiple places.
- QAIS backs up critical config but is secondary to files.
- Session history lives in OPS, not reconstructed from crystals.

## Both Agree

No unilateral writes. The save protocol requires:
1. Both operators (user and Claude) agree the work is proven.
2. Evidence exists — screenshot, test output, or explicit confirmation.
3. The target file and exact change are identified before writing.

This prevents:
- Claude writing speculative changes.
- Saves during confusion or drift.
- Overwrites without understanding current state.

## Code > Prose

When documentation says one thing and code does another:
- The code IS the truth (unless it's a known bug).
- Update prose to match code, not the other way around.
- Read code before writing about it.
- Written ≠ Compiled ≠ Working — track states separately.

## Identify = Execute

When Claude identifies a problem:
- Fix it now. Don't ask permission to fix obvious bugs.
- The identification IS the authorization for execution.
- Exception: destructive changes still require {Save} protocol.

## Conflict Resolution

When sources conflict across layers, resolve by conflict type:

| Conflict Type | Resolution | Example |
|---|---|---|
| Code vs prose | Code wins (unless code is a proven bug) | Implementation differs from .md description → update prose |
| CORE vs doctrine (project-internal) | CORE wins (B4 sovereignty) | Project defines its own naming convention |
| CORE vs doctrine (constitutional) | Doctrine wins (B1-B3) | CORE cannot grant itself tools outside class matrix |
| Code vs doctrine | If code is correct behavior → update prose. If code violates constitutional rule → code is bug → fix code | |

## Write Classification (Identify=Execute Scope)

Not all writes require Save protocol. Classification by impact:

- **Non-persistent** — context-only reasoning, no file touch. No protocol needed.
- **Corrective** — fixing a wrong path, typo, config error where the intended state is unambiguous. Identify=Execute applies. Fix now.
- **Constructive** — new content, new files, structural changes. Save protocol. Both agree.
- **Destructive** — file deletion, content removal, entity reclassification. Save protocol. Both agree. Proof required.

When in doubt, treat as constructive. The save gate costs one exchange. A bad write costs a recovery session.

## Mantra

"Code > Prose. Both agree. Derive, not store."
