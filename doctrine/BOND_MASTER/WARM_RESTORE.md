# Warm Restore — SLA-Powered Session Retrieval

**Entity Class:** Doctrine (BOND_MASTER)
**Authority:** BOND_MASTER
**Domain:** Session continuity through selective handoff retrieval

---

## What Warm Restore IS

Warm Restore is the SLA-powered session continuity command. Where {Full Restore}
loads all available state linearly, {Warm Restore} queries the handoff archive
using SLA's retrieval pipeline and loads only the sections relevant to the
current context.

Warm Restore IS:
- A retrieval command, not a storage command. It consumes handoffs written by {Save}.
- SLA's first operational role inside BOND — doctrine serving the framework, not just theory.
- Selective: loads 2-5 relevant sections instead of N entire handoffs.
- Context-aware: uses active entity, user's opening message, and heatmap state as query signals.

Warm Restore IS NOT:
- A replacement for {Full Restore}. Full Restore is the comprehensive cold boot.
- A replacement for crystals or memory edits. Those serve different continuity layers.
- Automatic. The user invokes {Warm Restore} explicitly.

## Choosing Your Restore

Both restore commands are always available. The choice depends on the session ahead.

| Factor | {Warm Restore} | {Full Restore} |
|--------|---------------|----------------|
| Speed to productive | 1 turn | 2-3 turns |
| Context depth | Selective (SLA-ranked sections) | Comprehensive (full state) |
| Accumulated state handling | May miss cross-session proof chains | Carries full history |
| Best fit | Perspective chats, creative riffing, light check-ins | Large projects, complex work streams, deep decision history |

**Calibration insight:** For project-class entities with many completed items, open threads, and cross-session dependencies, Full Restore's extra context load pays for itself in accuracy. Warm Restore can reach "productive" in one turn but may not reach "accurate" without corrections. The more accumulated state a project carries, the stronger the case for Full Restore.

The user chooses freely. This is guidance, not a gate.

## The Continuity Stack

Four layers, each serving a different purpose:

| Layer | Persistence | Scope | Loaded By |
|-------|-------------|-------|-----------|
| Memory edits | Permanent (Anthropic) | Shallow facts, preferences | Always present |
| Crystals | Per-project (QAIS) | Session-end state snapshots | {Full Restore} |
| Handoffs | Disc (markdown) | Detailed session records | {Full Restore} or {Warm Restore} |
| Transcripts | Disc (text) | Raw conversation logs | Manual reference only |

{Full Restore} loads crystals + all handoffs. Comprehensive but expensive.
{Warm Restore} loads crystals + SLA-selected handoff sections. Surgical.

## Handoff Template

All handoffs must follow this standardized format for SPECTRA indexing.
Each `## SECTION` header defines a retrieval chunk boundary.

```markdown
# HANDOFF S{N} — {Active Entity}
## Written: {ISO Date}
## Session: {N}

---

## CONTEXT
Session {N}. Entity: {name} ({class}). Counter: {tN/L emoji}.
Links: {comma-separated entity names}.
{1-2 sentence summary of session goal/theme.}

## WORK
{What was built, changed, or decided. Concrete nouns and specifics.
File names, component names, API endpoints, algorithms.
This section carries the heaviest SPECTRA signal.}

## DECISIONS
{Design decisions made and their rationale. Each decision is a
statement of what WAS chosen and WHY. Not options considered.}

## STATE
Entity: {name} ({class})
Counter: {tN/L emoji}
Config: {key settings}
{Any runtime state worth preserving.}

## THREADS
{Open items, loose ends, next steps. Prioritized.
Each thread is a future query target — write them as
topics someone would search for.}

## FILES
{Files created or modified. Paths only, no content.}
```

### Why This Format

- **CONTEXT** is low-IDF (common words like "session", "entity"). It won't win retrieval
  contests but provides metadata when loaded.
- **WORK** is high-IDF (specific technical terms, file names, component names). This is
  the primary retrieval target.
- **DECISIONS** carries unique vocabulary (rationale language, option names). Good for
  "why did we decide X?" queries.
- **THREADS** is future-facing. When someone starts a session saying "let's work on
  the SLA retrieval," THREADS from the session that parked that idea will match.
- **STATE** and **FILES** are structural. Rarely the retrieval target but useful context
  when a neighboring section is loaded.

### Section Loading Rules

When SLA selects a section, always load:
1. The matched section itself
2. The CONTEXT section from the same handoff (metadata anchor)
3. The STATE section from the same handoff (continuity anchor)

This guarantees every loaded chunk has its session context attached.

## Retrieval Architecture

### Build Time: Indexing

The indexer runs on the `handoffs/` directory:

1. **Parse** each `HANDOFF_S{N}.md` into sections by `## HEADER` boundary
2. **Tag** each section: `{session: N, section: "WORK", entity: "GSG"}`
3. **Tokenize** via ROSETTA stemmer (shared with SLA)
4. **Build** SLACorpus from all sections across all handoffs
5. **Save** index to `state/warm_restore_index.json`

Index is rebuilt when:
- A new handoff is written (end of session)
- User explicitly requests reindex
- {Warm Restore} detects handoff count != indexed count

### Query Time: {Warm Restore}

When user invokes {Warm Restore}:

1. **Gather signals:**
   - Active entity name (from `state/active_entity.json`)
   - User's opening message (the text accompanying or following {Warm Restore})
   - Heatmap hot concepts (from QAIS heatmap if available)

2. **Construct query string:**
   ```
   {entity_name} {user_message_keywords} {hot_concepts}
   ```

3. **Run SLA pipeline:**
   - SPECTRA shortlists top-5 sections
   - Anchors + neighbors adjust confidence margin
   - Gate routes: HIGH → load directly, LOW → load more sections as hedge

4. **Expand selections:**
   - For each selected section, also load its CONTEXT and STATE siblings
   - Deduplicate (if CONTEXT from the same handoff is already selected, don't load twice)

5. **Return to Claude:**
   - Ordered by session number (chronological)
   - Prefixed with retrieval metadata: which sections matched, confidence level
   - Total token estimate for loaded content

### Query Construction Details

The query string is the critical input. Too generic = bad retrieval. Too specific = misses.

**Entity signal:** Always included. If active entity is GSG, the query starts with "GSG"
which immediately biases toward handoffs that discuss GSG work.

**User message:** Content-stemmed. If user says "let's continue the panel work from
last session," the stems are: "continu panel work session" — which will match WORK
sections discussing panel components.

**Heatmap:** If available, top-3 hot concepts are appended. These represent what the
user was recently working on, even if they didn't mention it explicitly.

**Fallback:** If no user message and no heatmap, query is just the entity name.
This returns the most entity-relevant sections across all handoffs.

## Token Economics

Assume 15 handoffs × 5 sections × ~200 tokens/section = 15,000 tokens total archive.

| Strategy | Tokens Loaded |
|----------|--------------|
| {Full Restore} — all handoffs | ~15,000 |
| {Warm Restore} — 3 sections + context/state | ~1,800 |
| {Warm Restore} — 5 sections + context/state | ~3,000 |

At 50 handoffs (long-lived project): Full Restore = 50,000 tokens. Warm Restore still ~3,000.

The savings compound. This is why it matters.

## File Structure

```
handoffs/
  HANDOFF_S90.md              ← standardized template
  HANDOFF_S91.md
  HANDOFF_S92.md
  ...
state/
  warm_restore_index.json     ← precomputed SLA index
  warm_restore_output.md      ← latest retrieval output (Claude reads this)
warm_restore.py               ← indexer + query engine (BOND_ROOT level)
```

## Integration Points

- **Handoff writing:** Claude writes handoffs in the standardized template. The template IS the contract. Deviation breaks indexing.
- **BOND skill:** {Warm Restore} is defined alongside {Full Restore} in the BOND skill file. Claude reads the command definition and executes the pipeline.
- **Server-side execution:** The indexer and query engine run server-side where Python has full filesystem access. The retrieval output is written to `state/warm_restore_output.md`. Claude reads the pre-computed result — badges already rendered.
- **Why server-side:** Claude's tool environment cannot execute Python against the local filesystem. The server runs on the user's machine where Python has full access to `handoffs/` and `state/`.

## IS Statements

- Warm Restore IS the selective session retrieval command.
- Warm Restore IS powered by SLA — SPECTRA ranking, anchor confidence, gated routing.
- Warm Restore IS section-level retrieval, not paragraph-level.
- Warm Restore IS context-aware: entity + message + heatmap signals.
- Warm Restore IS additive to the continuity stack, not a replacement for any layer.
- Warm Restore IS NOT automatic. User invokes it explicitly.
- Warm Restore IS NOT a storage mechanism. It consumes handoffs produced by {Save}.
- Warm Restore resets the counter. It establishes a fresh context baseline like {Sync} and {Full Restore}.
