# BOND Audit — Checklist and Violation Patterns

## Purpose

When Claude enters BOND_MASTER, it can audit any BOND component against
this checklist. Each item is a testable assertion. Violations are fixable.

## Audit Categories

### 1. Dead Code
Check for code that is no longer used or was replaced by a newer approach.

**What to look for:**
- Unused hooks or stubs (e.g., hooks returning hardcoded values)
- Commented-out code blocks left from previous iterations
- Variables declared but never read
- Import statements for removed modules
- Empty directories

**Violation:** Dead code exists in the codebase.
**Fix:** Remove it. Dead code is state debt.

### 2. Hardcoded Paths
Check for absolute paths that should be relative or env-configured.

**What to look for:**
- Absolute paths hardcoded in server or client code
- Path separators that assume a specific OS
- Paths that work only on one machine

**Violation:** Path works only on one machine.
**Fix:** Use relative paths, env vars, or config files.

### 3. Truth Hierarchy Violations
Check that state is not stored redundantly.

**What to look for:**
- Same information in two files
- Prose that contradicts code behavior
- Documentation describing removed features
- OPS referencing sessions that don't match actual history

**Violation:** Multiple sources of truth for same datum.
**Fix:** Identify canonical source, remove duplicates, add pointer if needed.

### 4. Entity Architecture Violations
Check that entities respect their class boundaries.

**What to look for:**
- entity.json with settings outside class definition
- Entity folders missing entity.json
- Entity files referencing behavior their class doesn't permit

**Violation:** Entity violates class boundary.
**Fix:** Correct entity.json and behavior to match class spec.

### 5. Communication Path Integrity
Check that the bridge between user interface and Claude is the sole communication path.

**What to look for:**
- Multiple communication channels active simultaneously
- Redundant or deprecated bridge mechanisms still present in code
- Status indicators based on deprecated methods

**Violation:** Non-canonical communication path exists.
**Fix:** Remove deprecated paths, ensure single bridge.

### 6. Counter Protocol Integrity
Check that counter rules are correctly implemented.

**What to look for:**
- Counter computation in the wrong layer (counter state is authoritative, Claude echoes)
- Missing counter on any Claude response
- Incorrect reset behavior (resets on wrong commands, fails to reset on correct ones)

**Violation:** Counter protocol violated.
**Fix:** Ensure counter state flows one direction: authoritative source → Claude echo.

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
- Missing config example with all configurable values
- No unified startup script
- Dependencies not listed in manifest
- No README or setup guide at project root

**Violation:** Fresh install would fail or require tribal knowledge.
**Fix:** Document, script, and parameterize.

## Optimal Audit Flow

Audit categories are dependency-ordered. Failures in earlier layers invalidate assumptions of later layers. Check foundation before structure, structure before protocol, protocol before readiness.

### Layer 1 — Foundation (check first, failures cascade)
1. **Truth Hierarchy** — If state is contradictory, everything downstream is suspect.
2. **Entity Architecture** — If class boundaries are wrong, behavior governance is wrong.
→ *Joint check:* Do entity configs match the truth hierarchy? Do IS statements reflect reality?

### Layer 2 — Structural (system shape)
3. **Dead Code** — Remove noise before checking specifics.
4. **Hardcoded Paths** — Portability.
5. **Communication Path Integrity** — Bridge is sole path.
→ *Joint check:* Does cleaned code still match entity boundaries? Do paths resolve for all entity types?

### Layer 3 — Protocol (behavioral rules)
6. **Counter Protocol Integrity** — Heartbeat.
7. **Save Discipline** — Process.
→ *Joint check:* Do protocol rules hold under the structural assumptions above? Does save discipline cover all entity classes?

### Layer 4 — Readiness (end-to-end)
8. **Installer Readiness** — Can it stand up fresh?
→ *Joint check:* Does a fresh install pass Layers 1–3?

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
