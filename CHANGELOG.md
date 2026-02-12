# Changelog

All notable changes to BOND will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.4.0] - 2026-02-12

### Added
- **Doctrine files synced** — BOND_ENTITIES.md, BOND_AUDIT.md, BOND_PROTOCOL.md now present in GitHub repo (were described in 1.3.0 CHANGELOG but files not yet copied).
- **Server CLASS_LINK_MATRIX** — `/api/state/link` enforcement and `/api/state/linkable` endpoint now in GitHub server.js.
- **Banner server-side filtering** — DoctrineBanner.jsx and ProjectMasterBanner.jsx updated with server-side linkable fetch.

## [1.3.0] - 2026-02-12

### Added
- **Class Linking Matrix** — Entity links now filtered by class compatibility. Doctrine↔perspective links forbidden (incompatible tool boundaries). Enforced at three levels: UI dropdown, server 403, protocol refusal.
- **Linkable API** — `GET /api/state/linkable` returns only class-compatible, unlinkable entities for the active entity. Panel fetches server-side instead of client-side filtering.
- **Optimal Audit Flow** — BOND_AUDIT.md now defines dependency-ordered layers (Foundation → Structural → Protocol → Readiness) with joint checks at layer boundaries.
- **Hook Recognition** — BOND_PROTOCOL.md documents library-class positional hooks (BUILD_HOOKS, AUDIT_HOOKS, WORKFLOW_HOOKS) that fire at declared workflow positions.
- **Cross-Class Consultation** — BOND_ENTITIES.md documents operator-bridge pattern for carrying information between incompatible entity classes.
- **New doctrine templates** — BOND_ENTITIES.md, BOND_AUDIT.md, BOND_PROTOCOL.md added to templates/doctrine/BOND_MASTER/.

### Changed
- **Banner link pickers** — DoctrineBanner.jsx and ProjectMasterBanner.jsx now fetch linkable entities from server on entity activation instead of client-side filtering.

## [1.2.0] - 2026-02-12

### Added
- **Sync Obligations API** — `GET /api/sync-obligations` and `GET /api/sync-health` endpoints. Server derives obligations from state: active entity files, linked entity files, armed perspectives, save confirmation config. Phase 1 structured audit for {Tick} command.

### Changed
- **Server rewrite** — Clean single-file server.js (v1.4.0-s113). Removed duplicate code blocks, streamlined formatting.

## [1.1.2] - 2026-02-12

### Fixed
- **Seed watcher gap** — Sync protocol now includes seed check step. Scans doctrine/ for armed perspectives, runs qais_passthrough against conversation context. Previously the SEED ON toggle was cosmetic — the protocol never checked it.

## [1.1.1] - 2026-02-12

### Fixed
- **Link dropdown clipping** — link picker now opens downward instead of upward, fixing entities being hidden above the viewport edge.

## [1.1.0] - 2026-02-12

### Added
- **Update Informer** — panel header shows current version badge. Server checks GitHub for newer releases on startup and hourly. When an update is available, badge turns gold and links to the repo.

## [1.0.1] - 2026-02-12

### Added
- **Entity Voice Rule** — if Claude speaks *as* an entity, that entity must be active on disc. Panel always reflects who is talking. No ghost entries.

## [1.0.0] - 2026-02-12

### Added
- **One-command installer** — paste a single line into PowerShell, BOND installs and opens
- **Control Panel** — React dashboard with entity cards, module bay, doctrine viewer, search
- **BOND_MASTER** — constitutional doctrine entity with seed collection, vine growth, warm restore
- **PROJECT_MASTER** — project lifecycle governance with boundary enforcement
- **QAIS Memory** — resonance-based storage with heat map, crystal persistence, perspective fields
- **ISS Analysis** — semantic force measurement (G/P/E/r/gap) with limbic perception
- **SLA Retrieval** — Spectral Lexical Addressing for deterministic text retrieval
- **AHK Counter Bridge** — session counter + clipboard relay between panel and Claude
- **BOND Skill** — protocol skill file for Claude Projects
- **Install page** — hosted at moneyjarrod.github.io/BOND with copy-paste install command
- **Start/stop scripts** — `start_bond.bat` and `stop_bond.bat` for daily use
- **Entity system** — four-class hierarchy (doctrine, project, library, perspective)
- **MCP integration** — QAIS and ISS as MCP servers with tool authorization
- **WebSocket live updates** — real-time panel state via WebSocket connection
- **Module bay** — visual status cards for QAIS, ISS, EAP, and Limbic modules
- **Doctrine viewer** — read doctrine files directly in the panel
- **Search panel** — SLA-powered document search within the panel
- **Example templates** — writer MASTER and SKILL examples for reference
- **Documentation** — commands, entities, counter, and search reference guides

[1.0.0]: https://github.com/moneyjarrod/BOND/releases/tag/v1.0.0
