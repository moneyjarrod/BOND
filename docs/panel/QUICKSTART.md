# BOND Control Panel — Quick Start

## Prerequisites

- **Node.js** 18+ (`node --version`)
- **Python** 3.10+ (`python --version`)
- **numpy** (`pip install numpy`)
- **AutoHotkey v2** (optional, for counter + command bridge)

## Install

```
cd C:\Projects\BOND_private\panel
npm install
```

## Launch

Double-click `start_bond.bat` in BOND_private root. This starts:

1. **Express sidecar** on `http://localhost:3000` — serves doctrine API + MCP proxy
2. **Vite dev server** on `http://localhost:5173` — serves the React panel
3. Opens browser automatically

Or start manually:
```
cd panel
node server.js          # Terminal 1: sidecar
npx vite                # Terminal 2: panel
```

## Optional: AHK Bridge

Double-click `bridge\BOND_v8.ahk` for:
- Counter tag injection (`«tN/L emoji»` on Enter when Claude is active)
- Clipboard bridge (panel commands → Claude chat input)

Auto-start: `BOND_v8.bat` is in your Windows Startup folder.

## First Look

Navigate to `http://localhost:5173`. You'll see:

| Tab | What's There |
|-----|-------------|
| Doctrine | Doctrine-class entities (static IS knowledge) |
| Projects | Project-class entities (bounded workspaces with CORE files) |
| Perspectives | Perspective-class entities (unbounded growth) |
| Library | Library-class entities (reference shelves) |
| Systems | Module bay — QAIS, ISS, EAP, Limbic cards with live stats |
| Viewer | Doctrine file reader for any entity |

## Systems Tab

Click any module card to expand it. You'll see:
- Live stats (QAIS bindings, ISS version, etc.)
- Raw JSON toggle
- Tool buttons (Analyze, Resonate, Exists, etc.)

Tool invocation requires the sidecar + Python path to be correct. See MODULES.md.

## Entity Actions

On any entity card:
- **View** — peek at files in the Viewer tab
- **Load** — mount to session (persists in localStorage)
- **Enter** — load + set as active entity + open in Viewer

## Command Bar

Bottom bar sends commands to Claude via clipboard bridge:
`{Restore}` `{Sync}` `{Save}` `{Crystal}` `{Tick}` `{Chunk}`

Requires BOND_v8.ahk running. Flow: Panel copies `BOND:{command}` → AHK fires on clipboard change → types in Claude.

## Stopping

Close the terminal windows, or run `stop_bond.bat`.

---
🔥🌊 BOND Control Panel v1.0 — S81
