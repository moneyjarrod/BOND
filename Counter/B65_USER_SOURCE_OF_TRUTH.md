# B65: User Source of Truth

**Session:** 70
**Date:** 2026-02-01

## Problem Solved
Claude's internal counter failed in multiple ways:
- S70a: MCP fragmentation corrupted response structure
- S70b: Limit boundary pattern ("10 = complete") overrode explicit rule
- S70c: Tool chain displaced working memory, causing multi-emission

All failures shared root cause: Counter lived in Claude's working memory, which is vulnerable to displacement and pattern interference.

## Insight
**"User = source of truth. Claude just reads the tag."**

## Solution
Move counter tracking to user side via AutoHotkey:

```
OLD ARCHITECTURE:
  User sends message
  Claude increments N internally
  Claude displays N/LIMIT
  (vulnerable to displacement)

NEW ARCHITECTURE:
  User types message
  AHK appends «tN»
  User sends «t5»
  Claude reads tag → N=5
  Claude displays 5/LIMIT
  (bulletproof)
```

## Key Properties
- Claude has ZERO internal state to track
- Tag in message is the count
- Even if Claude "forgets" — next message has the correct N
- AHK handles {Sync}/{Full Restore} detection and reset

## Implementation
- `BOND_counter_v5.ahk` — AutoHotkey script
- Memory edit #6 updated: "Read N from user's «tN» tag. User=source of truth."
- Braces required for reset: `{Sync}` not `Sync`

## Architecture Principle
When Claude's internal state is unreliable, externalize it.
The user's message is always present. Make the message carry the state.

## Related
- B61: Counter Architecture (memory-level survives topic drift)
- B64: Field Attention (attempted, same vulnerability)
- S70a/b/c: Counter failure modes documented

🔥 Counter failures are now architecturally impossible. 🔥
