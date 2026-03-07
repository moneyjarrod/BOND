# Phase 1 — Acceptance Criteria

## What "Proven" Means

BOND_parallel replaces the live system when all 5 tests pass against it.
Each test validates a specific architectural claim from the overhaul design.
Tests run against BOND_parallel via `--root C:\Projects\BOND_parallel --port 3004`.

---

## Test 1: Cold Boot (CORE Success Criteria)

**Claim:** A fresh Claude session with SKILL.md + one daemon call can operate correctly.

**Setup:** New conversation. SKILL.md in context (L0). No prior state. No doctrine files read.

**Execute:**
1. Call `GET /sync-complete` against BOND_parallel daemon
2. Using only the payload + SKILL.md, attempt: {Enter}, {Chunk}, {Tick}, {Exit}

**Pass if:**
- Payload contains: active_entity, config, entity_files, linked_identities, armed_seeders, handoff, heatmap, capabilities
- Claude can execute all commands without reading any BM doctrine file directly
- Entity files load correctly for the active entity

**Validates:** D5 (main line consolidation), D9 (three-zone SKILL), CORE success criteria

---

## Test 2: Tiered Loading (D12)

**Claim:** Linked entities return identity-only on sync; full content on enter.

**Setup:** Test entity with links to at least one other entity in BOND_parallel.

**Execute:**
1. Set test entity active → `GET /sync-complete`
2. Inspect `linked_identities` field
3. Call `GET /enter-payload?entity={linked_entity}`
4. Inspect response

**Pass if:**
- `/sync-complete` returns `linked_identities` with entity.json content only (no .md files)
- `/enter-payload` returns full `entity_files` dict with all .md content
- Token cost of sync payload is measurably lower than old `linked_files` approach

**Validates:** D12 (tiered loading), IS #5 (token cost first-class)

---

## Test 3: Handoff Continuity (D11)

**Claim:** /sync-complete carries the most recent handoff without a separate file read.

**Setup:** Entity active in BOND_parallel. Write a handoff to its local state/.

**Execute:**
1. Write test content to `doctrine/{entity}/state/handoff.md`
2. Call `GET /sync-complete`
3. Inspect `handoff` field

**Pass if:**
- `handoff` field contains the written content verbatim
- No additional tool call needed to retrieve handoff
- If no handoff exists, field is `null` (not error)

**Validates:** D11 (sync carries handoff), joint reduction

---

## Test 4: Obligation Derivation (CORE P2, Principle #8)

**Claim:** The daemon derives obligations from state. Claude doesn't self-report.

**Setup:** BOND_parallel with at least one perspective entity that has `seeding: true`.

**Execute:**
1. Call `GET /obligations`
2. Call `GET /sync-complete`
3. Check armed_seeders array

**Pass if:**
- `/obligations` returns structured obligation list derived from entity configs
- Armed seeders appear in both `/obligations` and `/sync-complete` armed_seeders
- Stale handoff warnings trigger when handoff age > 48h
- Empty CORE warnings trigger for project entities with no CORE content

**Validates:** Principle #8 (armed = obligated), derive-not-store

---

## Test 5: Platform Blindness (D6)

**Claim:** The main line operates without any fixture present.

**Setup:** BOND_parallel daemon running via `--root`. No panel. No AHK. No clipboard bridge. No browser extension.

**Execute:**
1. Start daemon: `python bond_search.py --root C:\Projects\BOND_parallel --port 3004`
2. Hit every composite endpoint via curl or direct HTTP
3. Verify all responses are well-formed

**Pass if:**
- Daemon starts, indexes doctrine, serves all endpoints
- `/sync-complete`, `/enter-payload`, `/obligations`, `/vine-data` all return valid JSON
- `/search?q=test` returns results from BOND_parallel doctrine
- No response references panel, AHK, clipboard, or any fixture
- Zero fixture dependencies in the daemon codebase

**Validates:** D6 (platform blindness), D4 (main line ≠ daemon process, but daemon IS current material)

---

## Running the Suite

**Prerequisites:**
- BOND_parallel has test entities (Phase 4, Group C)
- At least: 1 doctrine entity with links, 1 project entity with CORE, 1 perspective entity with seeding armed
- Daemon runs clean against BOND_parallel via --root

**Order:** Tests are independent. Run any order. All 5 must pass for switchover.

**Failure handling:** A failed test identifies a specific fix. Fix in BOND_parallel, re-run that test. No cascading — each test is a local valve.

---

## Mantra

"If it can't pass the pressure test, it doesn't replace the main."
