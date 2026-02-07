# B65: User Source of Truth

**Session:** 70
**Date:** 2026-02-01

## Problem
Claude's internal counter failed (S70a/b/c) because it lived in vulnerable working memory.

## Insight
**"User = source of truth. Claude just reads the tag."**

## Solution
AHK script appends `«tN/LIMIT emoji»` to messages. Claude reads tag, displays it. Zero internal state.

## Key Properties
- Tag carries N, LIMIT, and emoji
- Even if Claude "forgets" — next message has correct N
- Auto-resets on `{Sync}` or `{Full Restore}`
- Claude echoes the emoji — does NOT compute it independently (S81 refinement)

## Architecture Principle
When internal state is unreliable, externalize it to the message.

## S81 Refinement
Even with correct math rules in memory, Claude drifted on emoji computation.
Semantic pressure ("at the limit feels red") overrides math.
Fix: Remove math from Claude's memory entirely. AHK computes, Claude echoes.

Memory edit (current):
```
BOND Counter: Read user's «tN/L emoji» tag. Echo THEIR emoji exactly.
Do not compute emoji independently. User display is source of truth.
```

🔥 Counter failures are now architecturally impossible. 🔥
