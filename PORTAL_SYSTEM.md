# BOND: Portal System Module

> Optional extension for managing multiple work streams.  
> "Only the active portal exists."

## When to Use This

| Situation | Recommended |
|-----------|-------------|
| Single project | ❌ Basic BOND is fine |
| Multiple related projects | ⚠️ Consider it |
| Context switching between domains | ✅ Use Portals |

## Concept

Portals let you switch between work streams without losing position. Like FPRS in game dev: only the active portal is "computed" - the rest exist as shelved state, ready to resume.

## Commands

| Command | Action |
|---------|--------|
| `{Portal}` | Show active + list all portals |
| `{Portal X}` | Switch to portal X (auto-shelve current) |
| `{Portal park}` | Shelve current, neutral state (no active portal) |
| `{Portal link X/file}` | Cross-reference without switching |

## On Switch

When Claude executes `{Portal X}`:

1. **Auto-shelve current** - Save position + pending items
2. **Load target** - Read X's OPS.md
3. **Report resume point** - Tell you where you left off

No context bleed. Each portal is its own world.

## Auto-Detection (Optional)

If enabled, Claude monitors for domain shifts:

> "This feels like [X] - switch portal?"

User confirms or declines. **No silent switches.** You stay in control.

To enable: Add to your SKILL.md:
```
**Auto-detect:** If conversation shifts domain for 2+ exchanges, 
Claude prompts: "This feels like [X] - switch portal?" 
User confirms or declines. No silent switches.
```

## Setup

### Directory Structure

```
Project/
├── Portals/
│   ├── ProjectA/
│   │   └── OPS.md
│   ├── ProjectB/
│   │   └── OPS.md
│   └── Research/
│       └── OPS.md
└── SKILL.md (shared identity)
```

### Portal OPS.md Template

Each portal has its own OPS.md following the standard format:

```markdown
# PORTAL_NAME OPS.md

## ANCHOR
SKILL.md v1.0

## BONFIRES
(portal-specific milestones)

## PENDING
(portal-specific work in progress)

## CURRENT STATE
Position: Where you left off
```

## Cross-Reference Without Switching

Sometimes you need info from another portal without fully switching:

```
{Portal link Research/findings}
```

Claude fetches the specific file, uses the info, but stays in current portal.

## Philosophy

This mirrors how humans context-switch:

| Human | Portal System |
|-------|---------------|
| "Let me check my notes on X" | `{Portal link X/file}` |
| "Switching to project B now" | `{Portal B}` |
| "Taking a break from all of it" | `{Portal park}` |
| "Wait, where was I?" | `{Portal}` (status) |

The key insight: **You can only truly focus on one thing.** Pretending otherwise leads to drift. Portals make the switch explicit and clean.

## Example Portals

| Portal | Domain |
|--------|--------|
| `GSG` | Game development |
| `BOND` | Protocol documentation |
| `Math` | Number theory research |
| `Health` | Personal research |
| `Work` | Day job projects |

Your portals match your work streams. Name them what makes sense to you.

---

*Portal System Module v1.0 — J-Dub & Claude, 2026-01-28*
