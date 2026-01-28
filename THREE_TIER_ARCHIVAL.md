# BOND: Three-Tier Archival Module

> Optional extension for long-running projects that accumulate milestones.  
> "Graduate the old, preserve the history, keep the present lean."

## When to Use This

| Project State | Recommended |
|---------------|-------------|
| < 10 milestones | ❌ Basic OPS is fine |
| 10-30 milestones | ⚠️ Consider it |
| 30+ milestones, growing | ✅ Use Three-Tier |

## The Problem

Projects grow. Milestones accumulate. Your OPS.md gets bloated. Sync takes longer. Context fills with old history instead of current work.

## The Solution

Three tiers with automatic graduation:

```
L1: OPS.md      → Current + recent (always loaded)
        ↓ graduates to
L2: BUFFER.md   → Graduated items (on-demand)
        ↓ graduates to  
L3: ARCHIVE.md  → Closed eras (deep history)
```

## Tier Details

| Tier | File | Contains | When Loaded |
|------|------|----------|-------------|
| L1 | OPS.md | Current + recent milestones | Always ({Sync}) |
| L2 | BUFFER.md | Graduated milestones | On-demand |
| L3 | ARCHIVE.md | Closed eras, summarized | Deep history lookup |

## Auto-Graduation Rules

Claude checks these on `{Sync}` and graduates automatically:

| Trigger | Action |
|---------|--------|
| OPS has > 10 recent milestones | Graduate oldest to BUFFER |
| BUFFER has > 20 milestones | Graduate oldest era to ARCHIVE |
| Resolved pending > 2 sessions old | Graduate to BUFFER |

### What "Graduate" Means

- Move the entry from one tier to the next
- Preserve all metadata (`.how`, `.why`, `.trouble` links still work)
- In ARCHIVE, eras get summarized (individual milestones → era summary)

## Commands

| Command | Action |
|---------|--------|
| `{Archive}` | Manual graduation trigger |
| `{Era}` | Close current era, summarize, move to archive |

## File Structure

```
Project/
├── OPS.md          (L1 - current work)
├── BUFFER.md       (L2 - graduated milestones)
├── ARCHIVE.md      (L3 - closed eras)
└── SKILL.md        (identity - unchanged)
```

## BUFFER.md Format

```markdown
# PROJECT_BUFFER.md
# Graduated milestones (L2)

## ERA: Foundation (M1-M15)
Graduated: 2026-01-28

M1: First milestone [tag]
  .mantra: Key insight
  .how: path/to/code.py

M2: Second milestone [tag]
  .fixed: What it solved
  ...

## ERA: Growth (M16-M30)
Graduated: 2026-02-15
...
```

## ARCHIVE.md Format

```markdown
# PROJECT_ARCHIVE.md
# Closed eras (L3)

## ERA: Foundation (M1-M15)
Closed: 2026-02-01
Summary: Built core systems, established patterns.
Key milestones: M5 (breakthrough), M12 (architecture)
Full details: See BUFFER backup or git history

## ERA: Growth (M16-M30)
Closed: 2026-03-01
Summary: Scaled to production, fixed edge cases.
...
```

## Token Economics

| Milestone Count | Without Archival | With Archival |
|-----------------|------------------|---------------|
| 10 | ~2K tokens | ~2K tokens |
| 30 | ~6K tokens | ~2K tokens |
| 50 | ~10K tokens | ~2K tokens |
| 100 | ~20K tokens | ~2K tokens |

**The win:** OPS.md stays ~2K tokens forever. Old work graduates but remains accessible.

## Retrieval

When Claude needs graduated info:

```
"Let me check BUFFER for milestone 25..."
```

Or for deep history:

```
"Looking in ARCHIVE for the Foundation era..."
```

Depth links (`.how`, `.why`) still work - they point to actual files, not the tier documents.

## Philosophy

This mirrors how institutions manage knowledge:

| Institution | Three-Tier |
|-------------|------------|
| Working memory | OPS.md |
| Filing cabinet | BUFFER.md |
| Archives | ARCHIVE.md |

The key insight: **Not everything needs to be top-of-mind.** Graduated doesn't mean forgotten - it means properly filed.

## Migration Path

1. Start with basic OPS.md
2. When you hit ~10 milestones, create empty BUFFER.md
3. Graduate oldest milestones manually or let auto-rules handle it
4. When BUFFER hits ~20, create ARCHIVE.md
5. Close an era, summarize, archive

---

*Three-Tier Archival Module v1.0 — J-Dub & Claude, 2026-01-28*
