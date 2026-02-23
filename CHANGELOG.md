# Changelog

All notable changes to BOND will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [2.4.0] - 2026-02-23

### Added
- **D17 GNOISE** — Inverted resonance auditor. Daemon scans entities for content that no longer belongs, routes findings to a holding cell for triage. Three endpoints: `/gnoise`, `/gnoise-cell`, `/gnoise-triage`. Panel Module Bay tile with entity dropdown, scan, and triage UI.
- **D18 Async Execution** — Bypass valve for long-running PowerShell cards. Cards declare `async: true`, daemon spawns background thread, panel polls for result. No more timeouts on repo-sync or heavy operations.
- **Auto-mode wiring** — When PowerShell mode is set to Auto (←), Claude can execute cards via the daemon with `initiator: "claude"`. D16 dry-run gate still enforced. Manual mode (→) denies Claude-initiated execution at the daemon layer.
- **SKILL.md PowerShell auto-mode instruction** — Protocol now documents the auto-mode flow: Claude identifies task → user confirms → Claude fires dry run → user confirms → Claude fires live.

### Fixed
- **SPA catch-all hang** — Unmatched `/api/` paths now return 404 JSON instead of hanging indefinitely.
- **Zombie process guard** — `start_bond.bat` now kills existing processes on port 3000 before launching, matching `start_daemon.bat` pattern. Prevents silent EADDRINUSE crashes on restart.
- **GnoiseModule dropdown** — Triple data-shape mismatch fixed (API response wrapping, field names, .type vs .class).

## [2.3.0] - 2026-02-21

### Added
- **D16 Computed Dry Runs** — Static `dry_run_text` replaced with `dry_run_command` (read-verb validated) + `requires_dry_run` (enforced gate). Daemon session tracking gates both panel and auto paths identically. Execute and delete verbs always require dry run.
- **CONSULTATION.md** — Six-perspective consultation bench mapped to all open threads.
- **DECIDED splits** — DECIDED_CONSTITUTIONAL.md (active decisions) separated from DECIDED_ARCHIVE.md (historical rationale moved to handoffs/).

### Changed
- **ACTIVE.md trim** — 26 completed items archived to CHANGELOG.md. Mandatory-set payload cut from ~4.5KB to ~1.5KB. Compounds D14 savings every sync.
- **Entity reclassifications** — Bridge_Doctrine, ROSETTA, SPECTRA, SLA reclassified from doctrine to library class.

## [2.2.0] - 2026-02-20

### Added
- **D14 Deferred Entity File Loading** — `{Sync}` now loads mandatory file set only (CORE.md + ACTIVE.md + entity.json for projects). Remaining files listed in deferred manifest with size. 85% payload reduction for large entities.
- **D15 Write Path Safety** — New daemon endpoints: `POST /append` (positional insert), `POST /replace` (exact-match edit). `POST /write` gets shadow `.bak` backup and 50% destructive overwrite gate. Implements CORE principle P9: write path mirrors read path.

### Changed
- **Daemon v3.1.0** — Write safety endpoints, deferred loading logic, mandatory file resolution by entity class.

## [2.1.0] - 2026-02-18

### Added
- **D13 PowerShell Execution** — Governed shell execution with 12-step validation pipeline. Verb classification (read/copy/move/create/delete/execute), whitelist toggles, operation cards, Level 3 blacklist, chain splitting, path containment, audit logging. Panel UI with master toggle, mode selector, verb switches, card list.
- **Gift Pack Import** — `GET /api/starters` + `POST /api/starters/import` endpoints. Panel UI for importing starter ROOT files into perspectives. 409 conflict detection for existing files.
- **Layer 0 Warm Restore** — Entity-local state replaces global handoff as primary restore source. Global becomes fallback. `warm_restore.py` rewritten.
- **Starter PowerShell cards** — doctrine-backup (copy), doctrine-backup-check (read), entity-export (execute), panel-build (execute), system-diagnostic (read), repo-sync (execute).
- **Parameterized cards** — Cards can declare `source: "argument"` params with validation. Panel renders inline input prompts.

### Fixed
- **Panel audit (2 rounds)** — 16 violations fixed: dead code removed (empty services/, unused components, vestigial module defs), hardcoded `localhost:3000` → relative paths across all fetch calls, tool toggle endpoint removed (tools universal per doctrine).
- **D-pad Auto mode gate** — Daemon validation step 4 checks config mode. Manual denies `initiator: "claude"` at L2.

### Security
- **Pipeline Audit A1-A4** — 45 findings, 17 fixed. EncodedCommand L3 block, BLACKLIST_REGEX patterns (.NET types, UNC paths, env vars), unrecognized command classification gate, argument-source param validation.

## [2.0.0] - 2026-02-17

### Changed
- **Phase 6 Switchover** — BOND_parallel is now the live system. All development, installer builds, and repo syncs ship from it. The original BOND directory is archived.
- **Daemon v3.0.0** — Composite payloads (`/sync-complete`, `/enter-payload`, `/vine-data`, `/obligations`), D11 sync carries handoff, D12 tiered linking (identity only for linked entities), `--root` flag for portable paths.
- **SKILL.md rewrite** — Three-zone architecture (Key Signature, Instrument, Accidentals). 52% token reduction. Runtime audience only.
- **IS Reduction** — 15 doctrine files consolidated to 8 framework entities via audience sort.

### Added
- **Daemon Heat Map** — Session concept tracking with disk persistence. Bypasses class matrix. Endpoints: `/heatmap-touch`, `/heatmap-hot`, `/heatmap-chunk`, `/heatmap-clear`.
- **QAIS Resonance (daemon-local)** — Vine scoring moved from MCP round-trips to daemon. `/resonance-test`, `/resonance-multi` endpoints. Daemon reads perspective `.npz` fields directly.
- **Vine Processor** — Daemon handles tracker bookkeeping (exposures, hits, rain, dry) and disk writes during `{Sync}`. Claude handles judgment only.
- **Acceptance suite** — 22/22 tests covering entity lifecycle, linking, handoff, sync, restore.

## [1.5.0] - 2026-02-14

### Added
- **Two-field architecture** — Each perspective now maintains two separate QAIS fields: seed field (`.npz`) for vine lifecycle resonance, crystal field (`_crystal.npz`) for narrative continuity. No cross-contamination between identity growth and session memory.
- **Crystal routing** — When a perspective is the active entity, `{Crystal}` writes exclusively to the perspective's local crystal field instead of global. No perspective active → global as before.
- **Entity Warm Restore** — New `perspective_crystal_restore` MCP tool retrieves all session momentum from a perspective's local crystal field. Panel shows 🔥 Warm button in the entity bar when inside a perspective.
- **Visual Guide screenshots** — 7 annotated PNG images added to `docs/visual_guide/images/`. Fresh panel overview, header, tabs, entity card, command bar, populated panel, and entity grid.
- **Project Full Restore** — `/api/project-restore/:entity` endpoint. Assembles CORE, local crystal, SLA archive, and git status into a single recovery document scoped to the active project.
- **Project Handoff** — `/api/project-handoff/next/:entity` and `/api/project-handoff/write/:entity` endpoints. Scoped handoffs stored inside `doctrine/{PROJECT}/handoffs/`.
- **Project Tick** — `/api/project-tick/:entity` endpoint. Quick project health pulse: crystal count, handoff count, doctrine files, git status, CORE initialization.
- **EntityBar two-row layout** — Redesigned EntityBar.jsx to accommodate 8 buttons (4 project-specific + 4 standard BOND tools) in a clean two-row layout.
- **Tick role expansion** — Tick now serves dual purpose: quick status check AND system integrity auditor.

### Changed
- **Perspective doctrine updated** — BOND_ENTITIES.md now documents the two-field architecture with explicit routing rules.

### Fixed
- **Doctrine/code drift** — S115 wrote doctrine claiming crystal routed to local fields before implementation existed. Corrected to match actual architecture before building the proven mechanism.
- **Gitignore architecture** — `doctrine/` now tracked directly in git (BOND_MASTER/ and PROJECT_MASTER/ whitelisted). Removed stale `templates/doctrine/` redundancy and server bootstrap copy code.
- **Crystal section bug** — Fixed missing function reference, wrong file path, and wrong data access pattern in crystal section code.
- **Path traversal guards** — All four new project endpoints sanitize `../` and absolute paths. Security standard for all new endpoints going forward.
- **EntityBar cross-repo match** — EntityBar.jsx exact-matched between public and private repos.
- **Stale template code in private server.js** — Removed 1,135 bytes of dead `templates/doctrine/` bootstrap code that had been cleaned from public but lingered in private. Repos now match.
- **Installer: Node version check** — `install.ps1` now validates Node.js 18+ instead of just checking existence. Users with Node 16 get a clear error and download link instead of cryptic npm failures.
- **Installer: Counter auto-launch** — `install.ps1` now attempts to start `BOND_v8.ahk` automatically on install (matching `start_bond.bat` behavior). Adapts output: if AHK present, counter launches and "Next steps" skips manual launch; if AHK missing, yellow warning with install link.

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

[2.4.0]: https://github.com/moneyjarrod/BOND/releases/tag/v2.4.0
[2.3.0]: https://github.com/moneyjarrod/BOND/releases/tag/v2.3.0
[2.2.0]: https://github.com/moneyjarrod/BOND/releases/tag/v2.2.0
[2.1.0]: https://github.com/moneyjarrod/BOND/releases/tag/v2.1.0
[2.0.0]: https://github.com/moneyjarrod/BOND/releases/tag/v2.0.0
[1.5.0]: https://github.com/moneyjarrod/BOND/releases/tag/v1.5.0
[1.0.0]: https://github.com/moneyjarrod/BOND/releases/tag/v1.0.0
