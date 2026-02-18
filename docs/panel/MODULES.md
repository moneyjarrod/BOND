# BOND Modules

## Overview

Modules are self-describing JSON configs that connect the panel to BOND's perception systems. Each module lives in `panel/modules/` as a `.json` file.

The panel auto-discovers modules on startup and polls their status at configurable intervals.

## Current Modules

| Module | File | Server | Tools |
|--------|------|--------|-------|
| QAIS 🔮 | qais.json | qais_v4.py | stats, exists, resonate |
| ISS 📐 | iss.json | iss_prototype.py | analyze, compare, status |
| EAP 🎭 | eap.json | (Claude-native) | schema |
| Limbic 🧠 | limbic.json | limbic_genome_10d.json | status, scan |

## Module JSON Spec

```json
{
  "id": "qais",
  "name": "QAIS",
  "icon": "🔮",
  "description": "Quantum-Approximate Identity Substrate",
  "status_endpoint": "/api/mcp/qais/stats",
  "display_fields": [
    { "key": "total_bindings", "label": "Bindings", "icon": "🔗" },
    { "key": "total_identities", "label": "Identities", "icon": "👤" }
  ],
  "refresh_interval": 30
}
```

### Fields

| Field | Type | Purpose |
|-------|------|---------|
| `id` | string | Unique module identifier, matches system name in MCP proxy |
| `name` | string | Display name on card |
| `icon` | string | Emoji shown on card and in header |
| `description` | string | Shown in expanded detail view |
| `status_endpoint` | string | Sidecar route polled for live stats |
| `display_fields` | array | What stats to show — each has `key`, `label`, `icon` |
| `refresh_interval` | number | Seconds between status polls (default 30) |

## Data Flow

```
Module card polls:
  useModules.js → GET /api/mcp/:system/stats → server.js → mcp_stats.py → Python → JSON

Tool invocation:
  ModuleRenderer → POST /api/mcp/:system/invoke → server.js → mcp_invoke.py → Python → JSON
```

### mcp_stats.py

Reads live state for status cards. QAIS reads `qais_field.npz` directly. ISS/EAP/Limbic return config values.

Location: `panel/mcp_stats.py`

### mcp_invoke.py

Dispatches tool calls. Imports actual Python modules and runs them.

Location: `panel/mcp_invoke.py`

Supported tools:
- `qais/stats` — full field statistics
- `qais/exists` — check identity presence, returns bindings list
- `qais/resonate` — input: `identity|role|candidate1,candidate2,...`
- `iss/analyze` — returns G, P, E, r, gap for input text
- `iss/compare` — multiple texts (one per line), returns force comparison
- `iss/status` — version + force definitions
- `eap/schema` — 10D dimension listing
- `limbic/status` — genome fitness + version
- `limbic/scan` — ISS forces for text (full limbic needs Claude's EAP)

## UI Components

### ModuleBay.jsx
Grid of compact module cards. Shows active/waiting/off counts. Click card to expand.

### ModuleRenderer.jsx
Expanded detail panel. Shows:
- Stats grid with large amber values
- Raw JSON collapsible
- Tool buttons with input fields and JSON output

### SystemStatus.jsx
Original flat card list (kept as fallback, replaced by ModuleBay on Systems tab).

## Creating a Custom Module

1. Create `panel/modules/mymodule.json` with the spec above
2. Add a handler in `mcp_stats.py` for status polling
3. Add tool handlers in `mcp_invoke.py` if tools are needed
4. Restart the sidecar (`node server.js`)

The panel will auto-discover the new module on next refresh.

## Toggle Behavior

Toggles persist in `localStorage` under `bond_modules_enabled`. Default is ON for all modules. Disabled modules skip status polling entirely.

---
🔥🌊 BOND Modules — S81
