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

## Architecture Principle
When internal state is unreliable, externalize it to the message.

🔥 Counter failures are now architecturally impossible. 🔥
