# Daemon Evolution — Design Spec (S120)

## Current State
Search daemon (`bond_search.py`) runs on localhost:3003. Hot water (search/SLA) and cold water (file ops). User starts manually via terminal. Claude accesses via browser channel (javascript_tool → localhost:3003).

## Design: Data Assembly Layer + Panel Manager

### IS Statement
**The daemon's response IS its health. A separate health check is redundant state.**

Derived from CM layered narrowing + P11 joint analysis (S120). Health is not polled — it falls out of real work requests. One initial request on panel load collapses health + data. All subsequent requests self-report.

### Architecture

```
Panel loads → /sync-payload (one call)
  ├── Success → green dot, data cached, daemon online
  └── Timeout (3s) → red dot, offer restart button
  
Any subsequent panel→daemon call:
  ├── Success → green dot maintained
  └── Failure → red dot, offer restart

Restart button → fires launcher script → retries /sync-payload
```

### Composite Endpoints (Payload Consolidation)

| Endpoint | Replaces | Returns |
|---|---|---|
| `/sync-payload` | 10-15 individual file reads | active entity, config, all entity files, linked entity files, armed seeders list, available daemon capabilities |
| `/enter-payload?entity=X` | 5-10 file reads on {Enter} | all files for entity + linked entities + entity.json |
| `/vine-data?perspective=X` | 3+ reads per vine pass | seed_tracker, seed .md files, ROOT file list |
| `/obligations` | manual state scanning | armed states, pending threads, stale handoffs, health signals |

Each endpoint returns a capability manifest alongside data — Claude learns what's available from the response itself, no hooks or memory edits needed.

### Panel Manager UI

- **Status indicator**: green/red dot in panel header. Derived from last daemon call, not polled.
- **Restart button**: visible when status is red. Fires `start_daemon.bat` / `start_daemon.sh`.
- **Auto-start option**: checkbox in settings. If enabled, panel spawns daemon on launch via launcher script.
- **No terminal exposure**: user never sees Python commands.

### Launcher Script (Transition Fitting)

P11's joint-failure mitigation. Panel doesn't spawn Python directly — it calls a script.

**`start_daemon.bat` (Windows):**
```bat
@echo off
cd /d "%~dp0"
start /b python search_daemon/bond_search.py
```

**`start_daemon.sh` (Unix):**
```bash
#!/bin/bash
cd "$(dirname "$0")"
python3 search_daemon/bond_search.py &
```

Why a script, not direct spawn:
- Decouples Node from Python version/path issues
- User can run manually if panel coupling fails
- One visible, debuggable, replaceable file
- Joint is one fitting, not embedded coupling

### Panel → Daemon Communication

- Panel hits daemon endpoints via `fetch()` from React frontend
- Same channel Claude uses (localhost:3003)
- Sacred flow direction: Panel → daemon only. Daemon never pushes to panel.
- Timeout: 3 seconds. Failure = status red.

### Claude Integration

On {Sync}, Claude's first action is `/sync-payload` via browser channel. The response contains:
1. All state data Claude currently gathers via 10-15 file reads
2. Capability manifest listing available endpoints
3. Armed seeder list for vine lifecycle

If daemon is down, Claude falls back to individual file reads via filesystem MCP. Graceful degradation.

### Failure Modes

| Failure | Detection | Recovery |
|---|---|---|
| Daemon not running | `/sync-payload` timeout on panel load | Red dot + restart button |
| Daemon crashes mid-session | Next panel→daemon call fails | Red dot + restart button |
| Port conflict | Daemon returns connection refused | Red dot + log: "Port 3003 in use" |
| Python not on PATH | Launcher script fails | Panel shows "Could not start daemon" + manual instructions |
| Zombie process on restart | Port check before spawn | Launcher checks port, kills existing if needed |

### Build Sequence

1. **Composite endpoints** in bond_search.py (`/sync-payload`, `/enter-payload`, `/vine-data`, `/obligations`)
2. **Launcher scripts** (bat + sh)
3. **Panel status indicator** (green/red dot derived from fetch results)
4. **Panel restart button** (fires launcher, retries sync-payload)
5. **Auto-start option** (settings checkbox, panel calls launcher on mount)
6. **Claude integration** (SKILL/hooks updated to prefer composite endpoints)

### Doctrine Alignment

- **Derive, not store** — health derived from work calls, not stored/polled
- **Both agree** — design spec requires Save before implementation
- **Code > Prose** — endpoints are the enforcement, this doc is documentation
- **Armed = Obligated** — if auto-start is enabled, panel MUST attempt daemon launch
- **Principle 9** — new endpoints require doctrine review (trigger: new server endpoint)
- **CM layered narrowing** — each call narrows scope, no layer overrides higher
- **P11 joints-fail** — launcher script is transition fitting, one joint not embedded coupling
- **P11 build-for-access** — manual fallback path always available

### Open Questions
1. Should `/sync-payload` include handoff summary or just entity state?
2. PID tracking: launcher writes PID to `state/daemon.pid` for clean restart?
3. Log tail in panel? Or keep manager minimal?
4. Should daemon serve panel static files too? (Probably not — separate concerns)
