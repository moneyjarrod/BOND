# Panel Handoff Generator — Implementation Spec
## Written: 2026-02-10 | Session 94

---

## Overview

Add a "Generate Handoff" button to the BOND panel CommandBar that produces
a standardized handoff file via hybrid approach: panel pre-fills what it
knows from state, Claude drafts the rest via bridge command, user reviews
and approves before writing to disc.

## Trigger

New button in CommandBar: **"Generate Handoff"** (or 📋 icon + label).
Standalone — not tied to {Sync} or {Save}. User clicks once at session end.

## Flow

```
1. User clicks "Generate Handoff"
2. Panel reads state → pre-fills CONTEXT + STATE sections
3. Panel sends bridge command to Claude → "{Handoff}"
4. Claude drafts WORK, DECISIONS, THREADS, FILES from conversation context
5. Claude returns structured response (JSON or delimited sections)
6. Panel displays all 6 sections in editable text areas
7. User reviews, edits any section as needed
8. User clicks "Write Handoff"
9. Panel writes handoffs/HANDOFF_S{N}.md in standardized template
10. Panel confirms: "Handoff S{N} written to disc"
```

## Session Number Derivation

Panel scans `handoffs/` directory for existing `HANDOFF_S*.md` files.
Extracts highest session number via regex `S(\d+)`.
New handoff = max + 1. If no handoffs exist, start at S1.

```javascript
// pseudocode
const files = fs.readdirSync(handoffsDir).filter(f => /HANDOFF_S\d+\.md/.test(f));
const nums = files.map(f => parseInt(f.match(/S(\d+)/)[1]));
const nextSession = nums.length > 0 ? Math.max(...nums) + 1 : 1;
```

## Pre-fill (Panel Side)

### CONTEXT section
Read from `state/active_entity.json`:
```
Session {N}. Entity: {entity} ({class}). Counter: {current counter}.
Links: {links array from entity.json, or "none"}.
```

### STATE section
Read from `state/active_entity.json` + `state/config.json`:
```
Entity: {entity} ({class})
Counter: {current counter value}
Config: save_confirmation {ON|OFF}
```

## Claude-Drafted Sections (Bridge Side)

Panel sends `{Handoff}` through bridge. Claude receives it and drafts:

### WORK
What was built, created, changed, or proved this session.
Subsections with ### headers for distinct work items.

### DECISIONS
What was agreed between both operators. Design choices, architectural calls.

### THREADS
What's pending, parked, or needs pickup next session.

### FILES
```
path/to/file   — NEW | UPDATED | DELETED: brief description
```

### Claude Response Format

Claude should return sections in a parseable format. Recommended:
```
===WORK===
(content)
===DECISIONS===
(content)
===THREADS===
(content)
===FILES===
(content)
```

Panel splits on `==={SECTION}===` delimiters to populate text areas.

## Standardized Template (Output Format)

```markdown
# HANDOFF S{N} — {ENTITY_NAME}
## Written: {YYYY-MM-DD}
## Session: {N}

---

## CONTEXT
{pre-filled by panel}

## WORK
{drafted by Claude, reviewed by user}

## DECISIONS
{drafted by Claude, reviewed by user}

## STATE
{pre-filled by panel}

## THREADS
{drafted by Claude, reviewed by user}

## FILES
{drafted by Claude, reviewed by user}
```

## UI Layout

When "Generate Handoff" is clicked, panel shows a modal or dedicated view:

```
┌─────────────────────────────────────────┐
│  GENERATE HANDOFF — S{N}                │
├─────────────────────────────────────────┤
│  CONTEXT  [pre-filled, editable]        │
│  ┌─────────────────────────────────┐    │
│  │ Session 94. Entity: BOND_MASTER │    │
│  └─────────────────────────────────┘    │
│                                         │
│  WORK  [Claude-drafted, editable]       │
│  ┌─────────────────────────────────┐    │
│  │ ### Warm Restore SKILL wiring   │    │
│  │ Added {Warm Restore} to...      │    │
│  └─────────────────────────────────┘    │
│                                         │
│  DECISIONS  [Claude-drafted, editable]  │
│  ┌─────────────────────────────────┐    │
│  │ On-demand handoff generation... │    │
│  └─────────────────────────────────┘    │
│                                         │
│  STATE  [pre-filled, editable]          │
│  ┌─────────────────────────────────┐    │
│  │ Entity: BOND_MASTER (doctrine)  │    │
│  └─────────────────────────────────┘    │
│                                         │
│  THREADS  [Claude-drafted, editable]    │
│  ┌─────────────────────────────────┐    │
│  │ GSG entity wiring...            │    │
│  └─────────────────────────────────┘    │
│                                         │
│  FILES  [Claude-drafted, editable]      │
│  ┌─────────────────────────────────┐    │
│  │ SKILL.md  — UPDATED             │    │
│  └─────────────────────────────────┘    │
│                                         │
│  [ Write Handoff ]    [ Cancel ]        │
└─────────────────────────────────────────┘
```

## File Locations

- **Output directory:** `handoffs/` (relative to BOND_ROOT)
- **State reads:** `state/active_entity.json`, `state/config.json`
- **Entity reads:** `doctrine/{entity}/entity.json` (for links)

## Dependencies

- Existing panel infrastructure (CommandBar, server.js, bridge)
- `handoffs/` directory must exist (create if missing)
- Bridge must support `{Handoff}` command routing to Claude

## Edge Cases

- No active entity: CONTEXT says "No entity active", still generates
- Bridge offline: Panel shows pre-filled sections only, text areas blank with note "Bridge unavailable — fill manually"
- Duplicate session number: Scan should always catch highest, but guard with overwrite confirmation
- Empty Claude sections: Allow write with empty sections (user may fill manually)

## Not In Scope

- Auto-triggering on {Save} or {Sync}
- Version history or handoff diffing
- Handoff templates per entity class
