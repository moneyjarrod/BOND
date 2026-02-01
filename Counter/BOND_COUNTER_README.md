# BOND Turn Counter

**User-side turn tracking for reliable Claude conversations.**

## The Problem

Claude's internal conversation counter can fail due to:
- Tool chain context displacement
- Compaction/memory issues  
- Pattern interference at limit boundaries

These failures cause desyncs between Claude's count and actual turn number.

## The Solution

**You become the source of truth.**

This AutoHotkey script:
1. Appends `«tN»` to your messages automatically
2. Claude reads your tag — no internal counting needed
3. Auto-resets when you type `{Sync}` or `{Full Restore}`

Result: Counter failures become impossible.

---

## Installation

### Step 1: Install AutoHotkey v2

Download from: **https://www.autohotkey.com/**

- Click "Download v2.0" (must be v2, not v1)
- Run installer, accept defaults

### Step 2: Get the Script

Save `BOND_counter_v5.ahk` to a permanent location:
- `C:\Users\YourName\Documents\BOND\BOND_counter_v5.ahk`
- Or anywhere you prefer

### Step 3: Run

Double-click `BOND_counter_v5.ahk`

Look for tray icon (bottom-right, may need to click `^` to expand).

### Step 4: (Optional) Auto-Start with Windows

1. Press `Win+R`, type `shell:startup`, press Enter
2. Create shortcut to `BOND_counter_v5.ahk` in this folder
3. Script runs automatically on login

---

## Usage

### Hotkeys

| Hotkey | Action |
|--------|--------|
| **Enter** | Tag message + send (when BOND ON) |
| **Ctrl+Shift+B** | Toggle BOND ON/OFF |
| **Ctrl+Shift+R** | Manual reset to 0 |
| **Ctrl+Shift+T** | Show current N |

### Workflow

1. Open Claude (Desktop or browser)
2. Type your message
3. Press **Enter**
4. Script adds `«t1»` and sends
5. Continue — each Enter increments: `«t2»`, `«t3»`, etc.

### Auto-Reset

Type `{Sync}` or `{Full Restore}` in your message:
- Script detects it as you type
- Shows "Reset flagged" tooltip
- Next Enter sends as `«t1»`

### Toggle OFF

Need normal Enter behavior? Press **Ctrl+Shift+B** to toggle OFF.
- BOND OFF = Enter works normally (no tagging)
- BOND ON = Enter tags + sends

---

## How Claude Uses It

Claude's memory includes this rule:

```
BOND Counter: Read N from user's «tN» tag.
Display: [emoji] N/LIMIT.
Reset ONLY on literal {Sync}|{Full Restore} (braces required).
User = source of truth.
```

Claude extracts N from your tag and displays accordingly:
- `«t5»` → 🗒️ 5/10
- `«t12»` → 🟡 12/10

No internal tracking. Your tag IS the count.

---

## Tray Menu

Right-click the tray icon:
- **● BOND ON / ○ BOND OFF** — Click to toggle
- **N = X** — Current count
- **Reset to 0** — Manual reset
- **Exit** — Close script

---

## Data Storage

Counter saved to: `%APPDATA%\BOND\turn_counter.txt`

Survives:
- Script restart
- System reboot
- Session changes

---

## Compatibility

| Platform | Works? |
|----------|--------|
| Claude Desktop (Windows) | ✅ |
| Claude.ai in Chrome/Edge/Firefox | ✅ |
| Claude Desktop (Mac) | ❌ (AHK is Windows-only) |
| Claude mobile app | ❌ |

For Mac users: Keyboard Maestro or Hammerspoon could replicate this functionality.

---

## Troubleshooting

**Script not running?**
- Check system tray (may be hidden under `^`)
- Ensure AutoHotkey v2 is installed (not v1)

**Enter not tagging?**
- Check tray shows "BOND ON"
- Ensure Claude window is focused
- Press Ctrl+Shift+B to verify toggle state

**Wrong N value?**
- Press Ctrl+Shift+R to reset
- Or type `{Sync}` to auto-reset on send

**Hotkeys conflicting?**
- Edit the script to change hotkey assignments
- Look for `^+b`, `^+r`, `^+t` lines

---

## Version History

- **v5** — Auto-reset on {Sync}/{Full Restore}, hotstring detection
- **v4** — Clipboard-based detection (deprecated)
- **v3** — Toggle ON/OFF
- **v2** — Enter key tagging
- **v1** — Ctrl+Enter tagging

---

## License

MIT — Part of the BOND project

---

## Credits

Created by J-Dub & Claude, Session 70.

*"User = source of truth. Claude just reads the tag."*
