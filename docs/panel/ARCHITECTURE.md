# BOND Architecture

## System Overview

BOND is a local control panel + bridge system for managing Claude conversations with persistent state, perception tools, and structured knowledge.

```
┌─────────────────────────────────────────────────┐
│                  BOND Panel                      │
│         Vite/React on localhost:5173             │
│                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Entity   │ │ Module   │ │ Command Bar      │ │
│  │ Cards    │ │ Bay      │ │ (clipboard→AHK)  │ │
│  └────┬─────┘ └────┬─────┘ └────────┬─────────┘ │
│       │             │                │            │
└───────┼─────────────┼────────────────┼────────────┘
        │             │                │
        ▼             ▼                ▼
┌───────────────────────────────────────────────────┐
│           Express Sidecar (localhost:3000)         │
│                                                    │
│  /api/doctrine/*     Filesystem API                │
│  /api/modules        Module config loader          │
│  /api/mcp/*/stats    Status proxy → mcp_stats.py   │
│  /api/mcp/*/invoke   Tool proxy → mcp_invoke.py    │
│  /api/bridge/*       Command queue (legacy HTTP)    │
└───────────────────────────────────────────────────┘
        │                              │
        ▼                              ▼
┌──────────────┐              ┌──────────────────┐
│ Python Tools │              │  BOND_v8.ahk     │
│              │              │                  │
│ qais_v4.py   │              │ Clipboard bridge │
│ iss_proto.py │              │ Counter inject   │
│ limbic genome│              │ Auto-start       │
└──────────────┘              └──────────────────┘
        │                              │
        ▼                              ▼
┌──────────────┐              ┌──────────────────┐
│ Data Files   │              │  Claude Chat     │
│              │              │                  │
│ qais_field.npz│             │ Commands typed   │
│ iss_proj.npz │              │ Counter tagged   │
│ genome.json  │              │                  │
└──────────────┘              └──────────────────┘
```

## Four-Class Entity Architecture (B69)

All BOND entities belong to exactly one class. Class determines tool access.

| Class | Purpose | Tools | Mutability |
|-------|---------|-------|------------|
| **Doctrine** | Static IS knowledge | Filesystem + ISS | Immutable |
| **Project** | Bounded workspace | All tools + CORE enforcement | CORE immutable, rest mutable |
| **Perspective** | Unbounded growth | Filesystem + QAIS + Heatmap + Crystal | Fully mutable |
| **Library** | Reference shelf | Filesystem only | Read-only |

Each entity folder contains an `entity.json`:
```json
{
  "class": "project",
  "core": "CORE.md",
  "tools": {}
}
```

Tool overrides in `tools` can only enable what the class allows. Cross-class tools are hard-disabled.

## Bridge Architecture

The bridge evolved from HTTP polling (v7) to clipboard events (v8).

### v8 Flow (Current)
```
Panel button click
  → copies "BOND:{command}" to clipboard
  → AHK OnClipboardChange fires
  → AHK checks if Claude window active
  → AHK types command via SendText
  → clipboard cleared
```

Zero polling. Event-driven. No lag.

### Counter Flow
```
User presses Enter in Claude
  → AHK checks: Claude active? BOND ON?
  → If yes: increment N, read L from turn_counter.txt
  → Inject «tN/L emoji» at cursor position
  → Persist N to %AppData%\BOND\turn_counter.txt
```

## MCP Tool Pipeline

Panel talks to Python tools through two scripts proxied by the Express sidecar:

### Status (read-only, polled)
```
useModules.js → GET /api/mcp/:system/stats → server.js → mcp_stats.py → JSON
```

### Invocation (on-demand)
```
ModuleRenderer → POST /api/mcp/:system/invoke → server.js → mcp_invoke.py → JSON
```

Both scripts import from actual Python codebases:
- QAIS: `C:\Projects\GnomeSweetGnome\Python\qais_v4.py`
- ISS: `C:\Projects\GnomeSweetGnome\ISS\iss_prototype.py`
- Limbic: reads `ISS\limbic_genome_10d.json`
- EAP: returns schema (Claude-native, not invocable externally)

## File Layout

```
BOND_private/
├── bridge/
│   └── BOND_v8.ahk              ← Clipboard bridge + counter
├── panel/
│   ├── src/
│   │   ├── App.jsx              ← Shell + routing (Systems → ModuleBay)
│   │   ├── components/
│   │   │   ├── CommandBar.jsx   ← Clipboard command dispatch
│   │   │   ├── CreateEntity.jsx ← New entity modal
│   │   │   ├── DoctrineViewer.jsx
│   │   │   ├── EntityCards.jsx  ← Class-filtered entity display
│   │   │   ├── Header.jsx      ← Status bar (Sys, Q, ISS, bridge)
│   │   │   ├── ModuleBay.jsx   ← Module grid + expand
│   │   │   ├── ModuleRenderer.jsx ← Detail + tool invocation
│   │   │   └── SystemStatus.jsx ← Legacy (fallback)
│   │   ├── hooks/
│   │   │   ├── useBridge.js    ← Bridge status (static connected)
│   │   │   ├── useDoctrine.js  ← Entity listing from sidecar
│   │   │   ├── useMCP.js       ← Direct MCP tool invocation
│   │   │   └── useModules.js   ← Module discovery + toggle + polling
│   │   └── styles/
│   │       └── bond.css        ← Dark theme, coal-mine aesthetic
│   ├── modules/
│   │   ├── qais.json, iss.json, eap.json, limbic.json
│   ├── mcp_stats.py            ← Status reader
│   ├── mcp_invoke.py           ← Tool dispatcher
│   └── server.js               ← Express sidecar (:3000)
├── doctrine/
│   ├── CM/                     ← Calendar Master (doctrine class)
│   ├── P11-Plumber/            ← Plumber (perspective class)
│   └── _library/               ← Library class
├── data/
│   └── qais_field.npz          ← QAIS persistent field
├── handoffs/                   ← Session handoff files
├── docs/
│   └── panel/                  ← These docs
├── start_bond.bat              ← Launch everything
└── stop_bond.bat               ← Kill servers
```

## Design Principles

1. **Panel is a controller, not just display.** Buttons do things.
2. **Folder contents ARE the manifest.** No separate registry. Mount = load folder.
3. **Class IS the filter.** Tool access determined by entity class, not config.
4. **Doctrine flows one way.** Disc → QAIS. Never back.
5. **Zero token cost.** Panel runs locally, outside Claude's context.
6. **Clipboard > polling.** Event-driven bridge, no lag.

## Build History

| Session | What | Status |
|---------|------|--------|
| S1 | Foundation (Vite, shell, CSS, sidecar) | ✅ |
| S2 | Entity system (cards, viewer, classification) | ✅ |
| S3 | Module system (ModuleBay, ModuleRenderer) | ✅ |
| S4 | MCP integration (invoke pipeline, useMCP) | ✅ |
| S5 | Bridge (clipboard v8, counter) | ✅ |
| S6 | Docs + spec update | ✅ |

---
🔥🌊 BOND Architecture — S81
