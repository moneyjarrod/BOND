# BOND Audit — Checklist and Violation Patterns

## Purpose

When Claude enters BOND_MASTER, it can audit any BOND component against
this checklist. Each item is a testable assertion. Violations are fixable.

## Audit Categories

### 1. Dead Code
Check for code that is no longer used or was replaced by a newer approach.

**What to look for:**
- HTTP bridge endpoints (`/api/bridge/*`) — clipboard replaced HTTP polling
- Unused hooks or stubs (e.g., `useBridge.js` returning hardcoded values)
- Commented-out code blocks left from previous iterations
- Variables declared but never read
- Import statements for removed modules
- Empty directories (e.g., `services/`)

**Violation:** Dead code exists in the codebase.
**Fix:** Remove it. Dead code is state debt.

### 2. Hardcoded Paths
Check for absolute paths that should be relative or env-configured.

**What to look for:**
- `C:\Projects\BOND_private` hardcoded in server.js or other JS
- Absolute paths in Python scripts that should use config
- Path separators that assume Windows (`\\` instead of `path.join`)

**Violation:** Path works only on J-Dub's machine.
**Fix:** Use relative paths, env vars, or `.env` config.

### 3. Truth Hierarchy Violations
Check that state is not stored redundantly.

**What to look for:**
- Same information in two files (e.g., counter limit in OPS AND memory edit)
- Prose that contradicts code behavior
- Documentation describing removed features
- OPS referencing sessions that don't match actual history

**Violation:** Multiple sources of truth for same datum.
**Fix:** Identify canonical source, remove duplicates, add pointer if needed.

### 4. Entity Architecture Violations
Check that entities respect their class boundaries.

**What to look for:**
- entity.json with tools outside class definition
  - Doctrine: only `filesystem` + `iss`
  - Project: `filesystem` + `qais` + `heatmap` + `crystal` + `iss`
  - Perspective: `filesystem` + `qais` + `heatmap` + `crystal`
  - Library: only `filesystem`
- Entity folders missing entity.json
- Entity files referencing tools their class doesn't permit

**Violation:** Entity has tools outside its class boundary.
**Fix:** Correct entity.json to match class spec.

### 5. Bridge Integrity
Check that the clipboard bridge is the sole communication path.

**What to look for:**
- HTTP endpoints for bridge communication (should be removed)
- Polling loops or intervals checking bridge status
- `fetch('/api/bridge/...')` calls in React code
- Bridge status indicators based on HTTP, not clipboard

**Violation:** Non-clipboard bridge code exists.
**Fix:** Remove HTTP bridge artifacts, use clipboard-only path.

### 6. Counter Integrity
Check that counter rules are correctly implemented.

**What to look for:**
- Counter logic in Claude's memory edits (should be echo-only rule)
- Counter computation anywhere other than AHK
- Missing counter on any Claude response
- Emoji computation in SKILL or OPS (should be AHK-only)

**Violation:** Counter computed outside AHK.
**Fix:** AHK computes emoji, Claude echoes. No exceptions.

### 7. Save Discipline
Check that saves follow protocol.

**What to look for:**
- Files modified without both-agree confirmation
- Saves without proof (no screenshot, no test, no confirmation)
- Speculative writes (changes based on assumption, not evidence)

**Violation:** Unilateral or unproven save.
**Fix:** Revert or verify. Re-apply with proper protocol.

### 8. Installer Readiness
Check that the system could be installed fresh.

**What to look for:**
- Missing `.env.example` with all configurable values
- No unified startup script (`npm start` or equivalent)
- Production static serving not wired in server.js
- Dependencies not listed in package.json
- Python dependencies not documented
- No README or setup guide at project root

**Violation:** Fresh install would fail or require tribal knowledge.
**Fix:** Document, script, and parameterize.

## Optimal Audit Flow

Audit categories are dependency-ordered. Failures in earlier layers invalidate assumptions of later layers. Check foundation before structure, structure before protocol, protocol before readiness.

### Layer 1 — Foundation (check first, failures cascade)
1. **Truth Hierarchy** — If state is contradictory, everything downstream is suspect.
2. **Entity Architecture** — If class boundaries are wrong, tool auth is wrong.
→ *Joint check:* Do entity configs match the truth hierarchy? Do IS statements reflect reality?

### Layer 2 — Structural (system shape)
3. **Dead Code** — Remove noise before checking specifics.
4. **Hardcoded Paths** — Portability.
5. **Bridge Integrity** — Communication path.
→ *Joint check:* Does cleaned code still match entity boundaries? Do paths resolve for all entity types?

### Layer 3 — Protocol (behavioral rules)
6. **Counter Integrity** — Heartbeat.
7. **Save Discipline** — Process.
→ *Joint check:* Do protocol rules hold under the structural assumptions above? Does save discipline cover all entity classes?
*Future slot: Obligation audit, Class linking compliance*

### Layer 4 — Readiness (end-to-end)
8. **Installer Readiness** — Can it stand up fresh?
→ *Joint check:* Does a fresh install pass Layers 1–3?
*Future slot: Warm Restore fidelity, Vine health validation*

Joint checks audit the **boundaries between layers** — where assumptions from one layer become inputs to the next. Straight runs don't fail. Joints do.

Future categories slot by layer without reshuffling the skeleton.

## Running an Audit

When entered via `{Enter BOND_MASTER}`, Claude should:

1. Ask which category or layer to audit (or audit all).
2. Follow the flow order — Foundation → Structural → Protocol → Readiness.
3. Read the relevant source files.
4. Check each assertion in that category.
5. Run joint checks at layer boundaries.
6. Report: ✅ PASS or ❌ VIOLATION with file + line + description.
7. Propose fixes for violations (but don't write without {Save}).

## Mantra

"If it violates doctrine, it's a bug — even if it works."
