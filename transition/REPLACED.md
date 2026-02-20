# REPLACED.md — Provenance Record

## What This IS

This document records what was replaced during the BOND overhaul switchover, what replaced it, and why. The next builder who asks "why is it this way?" finds the answer here without archaeology.

Old files are archived in `transition/old_pipe/` for reference. They are not active. They are not loaded. They are provenance.

---

## Doctrine Files

### Removed (absorbed or dead)

| Old File | Disposition | Absorbed By | Reason |
|----------|------------|-------------|--------|
| BOND_TRUTH.md | Absorbed | BOND_MASTER.md + BOND_PROTOCOL.md | 4 of 7 sections redundant with MASTER. 3 unique statements (Identify=Execute, Write Classification, Conflict Resolution) redistributed. D7. |
| LOCAL_STATE_ROUTING.md | Absorbed | BOND_PROTOCOL.md | Single-concept content. Routing rule, tables, restore scoping became a PROTOCOL section. D7. |
| SEED_COLLECTION.md | Absorbed | VINE_GROWTH_MODEL.md | Heavy overlap. Operational steps became a section in VINE_GROWTH. D8. |
| SKILL_AMENDMENT_LOCAL_STATE.md | Deleted | — | Work ticket. Changes already applied. Dead pipe. D8. |
| DAEMON_EVOLUTION_SPEC.md | Moved to fittings | — | Design spec, not doctrine. Main-line concept captured in CORE P2/D5. Fixture-level reference only. D8. |

### Survived (with surgery)

| File | Changes | Decision |
|------|---------|----------|
| BOND_MASTER.md | Stripped 2 fixture statements (clipboard def, clipboard-is-bridge). Stripped material names per D4. | D7 |
| BOND_PROTOCOL.md | Stripped Bridge Architecture section, emoji thresholds, panel refs. Absorbed TRUTH unique statements + LSR routing. | D7 |
| BOND_ENTITIES.md | Stripped badge rendering, panel-write ref, material name, personal ref. | D7 |
| VINE_GROWTH_MODEL.md | Absorbed SEED_COLLECTION. Stripped 1 panel ref. | D8 |
| WARM_RESTORE.md | Stripped 2 fixture refs from Integration Points. | D8 |
| BOND_AUDIT.md | Rewritten fixture-specific categories to main-line terms. Stripped personal known violations. | D8 |
| SURGICAL_CONTEXT.md | No changes. Cleanest file — zero violations, zero redundancy. | D8 |
| RELEASE_GOVERNANCE.md | No changes. Product governance, audience 3 (builder). | D8 |

### Personal (never shipped)

| File | Reason |
|------|--------|
| PARITY_REGISTRY.md | J-Dub's working registry. Format templated for public. |
| BOND_BONDFIRES.md | Session history. Format templated for public. |

---

## SKILL.md

| Aspect | Old | New | Decision |
|--------|-----|-----|----------|
| Architecture | Single zone, ~500 lines | Three zones (key signature, instrument, accidentals), ~80-100 lines | D9 |
| Token cost | ~2,000 tokens | ~400 tokens (52% reduction) | D9 |
| Fixture content | Bridge architecture, emoji thresholds, panel integration, daemon URLs | Removed entirely | D9 + D6 |
| Vine lifecycle | Full implementation steps | "Service daemon obligations" (one line) | D9 |

---

## Daemon (bond_search.py)

| Aspect | Old | New | Decision |
|--------|-----|-----|----------|
| Linked entity loading | `linked_files` — full .md content for all linked entities | `linked_identities` — entity.json only. Full via /enter-payload. | D12 |
| Handoff in sync | Not included | `handoff` field reads entity-local state/handoff.md | D11 |
| Root override | Not supported | `--root` CLI flag for parallel/test instances | S128 Group A |
| Version | 2.3.0 | 3.0.0 (breaking: key rename) | S128 |

---

## Directory Structure

| Old | New | Why |
|-----|-----|-----|
| Flat root (doctrine, panel, state mixed) | Manifold: doctrine + daemon + state at root, platforms/ for fixtures | D10 |
| Panel at root level | `platforms/panel/` | D10 — fixture isolation |
| No platform spec | `platforms/_platform_spec.md` | D10 — stub-out contract |
| No transition record | `transition/REPLACED.md` (this file) + `transition/old_pipe/` | D10 — provenance |

---

## The Rule

Every entry in this file maps to a locked decision (D1-D12). If it doesn't have a decision reference, it wasn't authorized. The overhaul is a controlled replacement, not a drift.

---

## Mantra

"Show the next builder where the shutoffs are."
