# BOND: Tiered Memory Module

> Optional extension for complex, long-running projects.  
> "Store operations, not positions. Re-derive on query."

## When to Use This

| Project Type | Recommended |
|--------------|-------------|
| Weekend hack | ❌ Basic BOND is fine |
| Multi-week project | ⚠️ Consider it |
| Multi-month, 50+ milestones | ✅ Use Tiered Memory |

## Architecture

```
L0: IDENTITY (always in context)
    └── Core truth, mantras, who you are together
    └── ~1-2K tokens, never fetched (already there)

L1: OPERATIONS (quick sync)
    └── What happened, what's proven, current status
    └── ~2-5K tokens, read on {Sync}
    └── Contains DEPTH LINKS to L2

L2: DEPTH (fetch on demand)
    └── .why    → Principles, architecture docs
    └── .how    → Working code, implementations
    └── .trouble → Known fixes, debugging guides
    └── Fetched only when Claude needs more
```

## The OPS Format

Each entry is an **operation**, not a state snapshot:

```markdown
## BONFIRES

B12: Feature Name - one line summary [tag1,tag2]
  .mantra: The insight in quotable form.
  .fixed: What problem this solved
  .why: path/to/principles.md#section
  .how: path/to/implementation.py
  .trouble: Quick fix or path to troubleshooting

## SESSIONS

S25: What happened this session [date] <B12,B11>
  .file: new_file_created.md
  .insight: Key realization

## DRIFTS

~25a: What went wrong [drift,tag] <S25>
  .correction: How it was fixed
  .lesson: What to remember
```

### Format Elements

| Element | Purpose |
|---------|---------|
| `B##:` | Bonfire (proven milestone, immutable) |
| `S##:` | Session (work log) |
| `~##:` | Drift (mistake + correction) |
| `[tags]` | Searchable categories |
| `<refs>` | Links to related ops |
| `.key: value` | Structured metadata |
| `.why:` | Depth link to principles |
| `.how:` | Depth link to code |
| `.trouble:` | Depth link to fixes |

## Auto-Fetch Triggers

Claude decides when to go deeper based on task + confidence:

| Signal | Fetch |
|--------|-------|
| Writing code | `.how` (implementation) |
| Debugging | `.how` + `.trouble` |
| Designing new system | `.why` + check drifts |
| Explaining concepts | `.why` |
| Low confidence | `.proof` or `.why` |
| Status check | Nothing (L1 enough) |

### How It Works

Claude doesn't need explicit commands. The triggers are **intent-based**:

```
User: "Let's implement the mining system"
       ↓
Claude: (implementing → need code)
       ↓
Fetches: .how: Python/mining_system.py
       ↓
Proceeds with accurate implementation
```

```
User: "Something's weird with the terrain"
       ↓
Claude: (debugging → need code + fixes)
       ↓
Fetches: .how + .trouble
       ↓
Checks known issues first
```

## Token Economics

| Approach | Per Sync | Notes |
|----------|----------|-------|
| Full state doc | ~10K tokens | Everything every time |
| OPS only | ~2K tokens | 80% reduction |
| OPS + depth fetch | ~4K tokens | Only when needed |

**The win:** More context for actual work, less for re-loading state.

## Migration Path

### From Basic BOND

1. Keep your identity anchor (becomes L0)
2. Convert session log to operations format (becomes L1)
3. Move detailed docs to reference files (becomes L2)
4. Add depth links (`.why`, `.how`, `.trouble`)

### Quick Start Template

```markdown
# PROJECT_OPS.md

## ANCHOR
IDENTITY.md v1.0

## BONFIRES

B1: First milestone [tag]
  .mantra: Key insight
  .how: path/to/code.py

## SESSIONS

S1: Initial session [date]

## DRIFTS

(none yet)

## CURRENT STATE

Bonfire: 1
Session: 1
```

## Example: GSG Project

This module was developed for Gnome Sweet Gnome, a game project with:
- 54 bonfires (proven milestones)
- 62 sessions
- 3 documented drifts
- Complex terrain/mining systems

**Results:**
- State file reduced from 39KB to 8KB
- Sync tokens reduced by 80%
- Same information, derived instead of stored
- Depth available when needed

## Philosophy

This mirrors how human memory works:

| Human | Tiered Memory |
|-------|---------------|
| Tip of tongue | L1 (know the name/summary) |
| Know where to look | Depth links |
| Deep recall | L2 fetch |

And it follows the same principle the project itself uses:

> "Store operations, not positions. Re-derive on query."

The documentation now follows the same architecture as the code.

---

*Tiered Memory Module v1.0 — J-Dub & Claude, 2026-01-28*
