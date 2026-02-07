# BOND Turn Counter

**User-side turn tracking for reliable Claude conversations.**

## The Problem

Claude's internal counter can fail due to:
- Tool chain context displacement
- Compaction/memory issues  
- Pattern interference at limit boundaries

## The Solution

**You become the source of truth.**

This AutoHotkey script appends `«tN/LIMIT emoji»` to your messages. Claude just reads the tag — no internal counting needed.

## Installation

### Step 1: Install AutoHotkey v2

Download from: **https://www.autohotkey.com/** (must be v2, not v1)

### Step 2: Run the Script

Double-click `BOND_counter_v6.ahk`. Look for tray icon.

### Step 3: (Optional) Auto-Start

Press `Win+R`, type `shell:startup`, create shortcut to the script.

## Hotkeys

| Hotkey | Action |
|--------|--------|
| **Enter** | Tag + send (when BOND ON) |
| **Ctrl+Shift+B** | Toggle ON/OFF |
| **Ctrl+Shift+R** | Reset to 0 |
| **Ctrl+Shift+T** | Show status |

## Tag Format

`«t5/10 🗒️»` — Turn 5, limit 10, normal

## Color Scheme (computed by AHK, echoed by Claude)

| Emoji | Meaning |
|-------|---------|
| 🗒️ | N ≤ LIMIT |
| 🟡 | N > LIMIT |
| 🟠 | N ≥ 15 |
| 🔴 | N ≥ 20 |

Claude does not compute these — Claude echoes the emoji from the user's tag.

## Auto-Reset

Type `{Sync}` or `{Full Restore}` — script detects and resets to 0.

## Compatibility

- ✅ Claude Desktop (Windows)
- ✅ claude.ai in Chrome/Edge/Firefox
- ❌ Mac (AHK is Windows-only)
- ❌ Mobile

## Configuration

Edit line 31 to change limit: `global LIMIT := 10`

---

*Session 70 — J-Dub & Claude*
