# Platform Specification — Stub-Out Contract

## What This IS

This document defines what any fixture (platform, UI, bridge) needs to connect to BOND's main line. The main line is platform-blind (D6). This spec is the adapter plate.

A builder reads this and knows: water pressure, pipe diameter, valve type. Connect your fixture.

---

## 1. Daemon Endpoint Contract

The daemon (`bond_search.py`) runs on `localhost:{port}` (default 3003). All communication is HTTP. JSON in, JSON out.

### Composite Endpoints (Primary Interface)

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/sync-complete` | GET | Entity state, config, entity files, linked identities, armed seeders, handoff, heatmap, capabilities |
| `/sync-complete` | POST `{"text": "...", "session": "S1"}` | Same as GET + vine resonance scores + tracker updates |
| `/enter-payload?entity=NAME` | GET | Full entity files + linked entity files + config |
| `/obligations` | GET | Derived obligations, warnings, armed seeder count |
| `/vine-data?perspective=NAME` | GET | Seed tracker, seed files, ROOTs, pruned, entity config |

### Search Endpoints

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/search?q=QUERY` | GET | Ranked results with scores, margin, confidence gate |
| `/search?q=QUERY&mode=retrieve` | GET | SLA v2 retrieval mode |
| `/search?q=QUERY&scope=all` | GET | Search all entities (ignores active scope) |
| `/search?q=QUERY&entity=NAME` | GET | Single entity search |

### File Operations

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/manifest` | GET | All files with entity, class, size, modified date |
| `/read?path=REL_PATH` | GET | File content verbatim |
| `/write` | POST `{"path": "...", "content": "..."}` | Write confirmation |
| `/copy?from=REL&to=REL` | GET | Copy confirmation |
| `/export` | GET | Full doctrine assembled into one markdown |

### Heatmap

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/heatmap-touch?concepts=a,b,c` | GET | Touch confirmation with counts |
| `/heatmap-hot` | GET | Top concepts by recency-weighted score |
| `/heatmap-chunk` | GET | Formatted snapshot for session state |
| `/heatmap-clear` | GET | Reset confirmation |

### Resonance

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/resonance-test?perspective=NAME&text=TEXT` | GET | Single perspective score |
| `/resonance-multi?text=TEXT` | GET | All armed perspectives scored |

### Response Shape (Universal)

Every endpoint returns JSON with `Content-Type: application/json; charset=utf-8`. Error responses include `{"error": "description"}`. Success responses vary by endpoint but always include the requested data at top level (no wrapper object).

### Health Detection

There is no `/health` endpoint. The daemon's response IS its health (DAEMON_EVOLUTION_SPEC IS statement). Any successful response = daemon alive. Timeout (recommend 3s) = daemon down.

---

## 2. Entity System Contract

### Entity Structure

Every entity lives in `doctrine/ENTITY_NAME/` and contains:
- `entity.json` — Required. Class, display name, configuration.
- One or more `.md` files — The entity's knowledge.
- `state/` subdirectory — Created on first write. Session-local state.

### entity.json Schema

```json
{
  "class": "doctrine|project|perspective|library",
  "display_name": "Human-Readable Name",
  "public": true,
  "links": ["OTHER_ENTITY"],
  "seeding": false,
  "seed_threshold": 0.04,
  "prune_window": 10
}
```

Required fields: `class`, `display_name`.
Optional fields: `public` (default false), `links` (default []), `seeding` (perspectives only), `seed_threshold`, `prune_window`.

### Four Classes

| Class | Nature | Growth | Key Behavior |
|-------|--------|--------|-------------|
| Doctrine | Static IS | None — immutable | Audit, constitutional authority |
| Project | Bounded workspace | Bounded by CORE | Full operational capability |
| Perspective | Unbounded growth | Unlimited | Vine lifecycle, seed collection |
| Library | Reference shelf | None — read-only | Retrieval and lookup |

### State Pointer

`state/active_entity.json` holds the current entity:
```json
{
  "entity": "ENTITY_NAME",
  "class": "project",
  "path": "doctrine/ENTITY_NAME",
  "entered": "2026-02-19T..."
}
```
Null values = no entity active.

---

## 3. SKILL Contract

SKILL.md is the runtime identity file for the AI channel. Three zones:

| Zone | Content | Survives Compaction |
|------|---------|-------------------|
| Key Signature | Behavioral identity — who Claude IS inside BOND | Always |
| Instrument | One line: "Service daemon obligations" | Always |
| Accidentals | Conditional patterns — dormant until triggered | Usually |

Fixtures do NOT appear in SKILL.md. SKILL describes how to open taps, not how AHK works.

---

## 4. Filesystem Contract

### Directory Layout

```
BOND_ROOT/
  doctrine/           # Entity directories
    BOND_MASTER/      # Framework entity (bootstrapped)
    PROJECT_MASTER/   # Framework entity (bootstrapped)
    {user entities}/  # Created by user
  state/              # Global state
    active_entity.json
    config.json
    heatmap.json
  search_daemon/      # Daemon source
    bond_search.py
  handoffs/           # Session handoff archive
  templates/          # Entity/project starter kits
  SKILL.md            # Runtime identity
  platforms/          # Fixture connections (this level)
```

### Path Resolution

All daemon file operations are relative to `BOND_ROOT`. The daemon enforces path boundaries — no reads/writes outside `BOND_ROOT`.

### State Routing

Session state commands route to entity-local `doctrine/{entity}/state/` when an entity is active, or global `state/` when none is active. `active_entity.json` and `config.json` are always global.

---

## 5. Connecting a New Fixture

1. Start the daemon: `python bond_search.py` (or `--root PATH --port PORT`)
2. Hit `/sync-complete` to get system state
3. Use the `capabilities` field in the response to discover available endpoints
4. Route all state reads through daemon composite endpoints
5. Route file writes through `/write` endpoint
6. Implement your UI/bridge/channel against the contracts above

The daemon doesn't know your fixture exists. That's the point.

---

## Mantra

"Water pressure, pipe diameter, valve type. Connect your fixture."
