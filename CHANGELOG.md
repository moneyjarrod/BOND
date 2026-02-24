# Changelog

All notable changes to BOND will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [2.5.0] - 2026-02-24

### Added
- **D19 Unified /file-op endpoint** — Single `POST /file-op` with `op` field replaces three separate write endpoints. Daemon write friction now matches filesystem tool friction.
- **D17 GNOISE (Noise Gnome)** — Inverted resonance auditor. Scores entity paragraphs against identity centroid to find content that no longer belongs. Full stack: panel tile → daemon → TF-IDF cosine → holding cell → triage controls. Recency exemption (14-day default) prevents false positives on new content.
- **GNOISE panel UX** — Settings panel with adjustable threshold and exempt days. Contextual explanation when files are skipped. Smart zero-state messaging.
- **D18 Async PowerShell execution** — Card-declared `async:true` routes to daemon job tank. Bypass valve pattern for long-running operations.
- **D21 UTF-8 encoding fix** — cp1252 double-encoding on Windows stdin in QAIS MCP server. Two fixes: `sys.stdin.reconfigure(encoding='utf-8')` + `ensure_ascii=False` with byte-counted Content-Length.
- **Platform_Reference entity** — Library class, 11 documented traps across 6 categories (Encoding, HTTP, Process, Path, MCP, SPA). Seeded from web research and BOND incidents.
- **QA-Boundary entity** — Perspective class, 8 ROOTs defining diagnostic methodology for system boundary inspection. Linked to Platform_Reference.
- **D16 Computed dry runs** — Replaces static dry_run_text + honor-system confirm with computed dry runs and mandatory gate. 9/9 validation passing.
- **Zombie guard** — start_bond.bat checks for orphaned processes before launching daemon.

### Changed
- **Daemon v3.2.0** — All write, async, GNOISE, and encoding improvements consolidated.
- **SKILL.md counter rule** — Pure mirror. AHK bridge owns the count, emoji, and all resets. Claude echoes, never computes.

### Fixed
- **D21 Unicode pipeline** — em dash, checkmark, arrow, ellipsis all survive /file-op round trip on Windows.
- **D20 IS Collapse verified** — Fresh sessions use /file-op naturally for governed writes. SKILL.md instructions survive context boundary.

## [2.4.0] - 2026-02-22

### Added
- **D17 GNOISE daemon** — GnoiseAuditor class + GET routes (/gnoise, /gnoise-cell, /gnoise-triage). Panel Module Bay tile with entity selector, scan trigger, findings list, priority breakdown, and triage controls.
- **D18 Async execution** — daemon job tank for long-running PowerShell cards.
- **D-pad Auto mode** — daemon gate checks config mode; Manual denies Claude-initiated execution, Auto passes.

## [2.3.0] - 2026-02-20

### Added
- **D15 Write path safety** — /append, /replace endpoints. /write gets shadow .bak + 50% destructive overwrite gate. P9 principle (write path mirrors read path) added to CORE.
- **D16 Computed dry runs** — Mandatory gate replaces honor-system confirmation.
- **D14 Deferred entity loading** — {Sync} loads mandatory set only (CORE.md + ACTIVE.md + entity.json). Deferred manifest lists remaining files with size. 85% token reduction per sync for large projects.

### Changed
- **Daemon v3.1.0** — Write safety, deferred loading, dry run gate.

### Fixed
- **Pipeline Audit A1-A4** — 45 findings, 17 fixed. Security hardening (EncodedCommand L3 block, BLACKLIST_REGEX), token savings, audience hygiene.

## [2.1.0] - 2026-02-17

### Added
- **D13 PowerShell execution** — Full architecture: master toggle → verb whitelist → card registration → verb-pattern match → chain splitting → path containment → escalation continuum (L0-L3) → spawn → post-exec verify → audit log. Panel UI with cards, dry run, confirmation flow.
- **Gift Pack import** — GET /api/starters + POST /api/starters/import. Panel component for importing starter ROOT packs into perspectives.
- **Layer 0 Warm Restore** — Entity-local state replaces global handoff as primary restore source.
- **Handoff sweep protocol** — Mandatory ACTIVE.md open thread sweep during {Handoff}.
- **Starter cards** — doctrine-backup, doctrine-backup-check, entity-export, repo-sync, panel-build, system-diagnostic.

### Changed
- **Panel audit** — 16 violations fixed across 2 rounds. Dead code removed, hardcoded paths → relative, tool toggle endpoint removed.

## [2.0.0] - 2026-02-16

### Added
- **BOND Overhaul architecture** — Complete redesign of BOND's runtime. SKILL.md + daemon-derived state replaces 14 piecemeal doctrine file loads. Three-audience sort (runtime/constitutional/rationale) governs all content placement.
- **Search daemon v3.0.0** — Standalone Python daemon on port 3003. TF-IDF paragraph-level search, composite payloads (/sync-complete, /enter-payload), entity-scoped indexing, SLA v2 retrieval.
- **Composite sync** — Single POST /sync-complete returns: active entity + config + mandatory files + deferred manifest + linked identities + armed seeders + vine resonance + tracker updates + obligations.
- **SKILL.md v1.0** — Three-zone architecture (Key Signature, Instrument, Accidentals). 52% token reduction from previous version. Runtime-only audience.
- **D12 Tiered entity loading** — Linked entities return identity only (entity.json) on sync/restore. Full content on {Consult} or {Enter}.
- **Entity-local state routing** — All session state ({Chunk}, {Handoff}, {Tick}) writes to active entity's local state/ subdirectory.
- **Four entity classes** — Doctrine (static), Project (bounded), Perspective (unbounded growth + vine), Library (read-only reference).

### Changed
- **Phase 6 Switchover** — BOND_parallel is the live system. All tools, installer, and repo sync ship from the new architecture.

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

[1.5.0]: https://github.com/moneyjarrod/BOND/releases/tag/v1.5.0
[1.0.0]: https://github.com/moneyjarrod/BOND/releases/tag/v1.0.0
