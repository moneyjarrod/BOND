# BOND Turn Counter

**User-side turn tracking for reliable Claude conversations.**

## The Problem

Claude's internal conversation counter drifts due to context displacement, compaction, and pattern interference. Auto-increment rules create conflicting instructions between memory edits, OPS files, and SKILL docs.

## The Solution

**You are the source of truth. Claude never counts.**

The AutoHotkey script:
1. Appends `«tN/L»` to your messages automatically (N=count, L=limit)
2. Claude parses your tag — no internal tracking needed
3. Auto-resets when you type `{Sync}` or `{Full Restore}`
4. Emoji computed client-side and included in tag

Result: Counter failures become impossible. Claude just reads what you send.

---

## Tag Format

```
«tN/L emoji»

N = your turn count (you increment, not Claude)
L = your session limit
emoji = computed by AHK script

Examples:
  «t1/10 🗒️»    → first turn, limit 10, normal
  «t5/10 🗒️»    → fifth turn, normal
  «t12/10 🟡»   → over limit
  «t15/10 🟡🟠» → over limit + getting long
```

---

## Installation

### Step 1: Install AutoHotkey v2

Download from: **https://www.autohotkey.com/**

- Click "Download v2.0" (must be v2, not v1)
- Run installer, accept defaults

### Step 2: Get the Script

Save `BOND_counter_v6.ahk` to a permanent location:
- `C:\Users\YourName\Documents\BOND\BOND_counter_v6.ahk`
- Or anywhere you prefer

### Step 3: Run

Double-click `BOND_counter_v6.ahk`

Look for tray icon (bottom-right, may need to click `^` to expand).

### Step 4: (Optional) Auto-Start with Windows

1. Press `Win+R`, type `shell:startup`, press Enter
2. Create shortcut to `BOND_counter_v6.ahk` in this folder
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
| **XButton2** | Insert 🧠 limbic trigger |

### Workflow

1. Open Claude (Desktop or browser)
2. Type your message
3. Press **Enter**
4. Script adds `«t1/10 🗒️»` and sends
5. Continue — each Enter increments: `«t2/10 🗒️»`, `«t3/10 🗒️»`, etc.

### Auto-Reset

Type `{Sync}` or `{Full Restore}` in your message:
- Script detects it as you type
- Shows "Reset flagged" tooltip
- Next Enter sends as `«t1/L»`

### Toggle OFF

Press **Ctrl+Shift+B** to toggle OFF.
- BOND OFF = Enter works normally (no tagging)
- BOND ON = Enter tags + sends

---

## How Claude Uses It

Claude's memory should include this rule:

```
BOND Counter: Read user's «tN/L emoji» tag. Echo THEIR emoji exactly.
Do not compute emoji independently. User display is source of truth.
```

Claude reads your tag and echoes your emoji as-is:
- `«t5/10 🗒️»` → 🗒️ 5/10
- `«t12/10 🟡»` → 🟡 12/10

No internal tracking. No emoji computation. AHK computes the correct emoji
client-side. Claude just reads and echoes. (Changed S81 — Claude repeatedly
drifted when given math rules to evaluate.)

---

## Tray Menu

Right-click the tray icon:
- **● BOND ON / ○ BOND OFF** — Click to toggle
- **N = X** — Current count
- **Reset to 0** — Manual reset
- **Exit** — Close script

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

## Version History

- **v6** — Tag format `«tN/L emoji»`, client-side emoji, XButton2 limbic trigger
- **v5** — Auto-reset on {Sync}/{Full Restore}, hotstring detection
- **v4** — Clipboard-based detection (deprecated)
- **v3** — Toggle ON/OFF
- **v2** — Enter key tagging
- **v1** — Ctrl+Enter tagging

---

## License

MIT — Part of the BOND project

---

*"User = source of truth. Claude just reads the tag. Never auto-increment."*
