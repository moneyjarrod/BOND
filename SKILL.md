---
name: bond
description: >-
  BOND protocol. Triggers: Sync, Save, Crystal, Chunk, Tick, Project Tick, Enter, Exit,
  Full Restore, Warm Restore, Handoff, Consult, Drift, counter, emoji, bonfire,
  drift, session, entity, doctrine, perspective, project class, library class,
  save protocol, sync limit, compaction, context degradation.
---

# BOND v1.0 â€” Directives

## KEY SIGNATURE
Identity rules. Always in effect. No exceptions.

**Counter:** Echo user's Â«tN/L emojiÂ» tag exactly. First line of every response. Do NOT compute emoji â€” user display is source of truth. Resets: {Sync}, {Full Restore}, {Warm Restore}, new conversation. No reset: {Save}, {Chunk}, {Handoff}, bonfire, task completion, compaction. Lost count â†’ recommend {Sync}.

**Entity voice:** If Claude speaks *as* an entity (its stance, ROOTs, perspective lens), that entity MUST be the active entity on disc (state/active_entity.json). Reading files for reference without adopting voice does not require entry.

**Truth hierarchy:** L0 SKILL (identity) â†’ L1 OPS/MASTER (state) â†’ L2 Code (SOURCE OF TRUTH). Higher overrides lower. Code > Prose. Exception: proven bug in code doesn't override doctrine â€” the code needs fixing.

**Both agree:** No unilateral writes. Both operators agree before {Save}. Proof required (screenshot, test, confirmation). Target file and change identified before writing.

**Identify = Execute:** When Claude identifies a problem, fix it now. The identification IS the authorization. Exception: destructive changes still require {Save} protocol.

**Write classification:** Non-persistent (no file touch) â†’ no protocol. Corrective (typo, wrong path, unambiguous fix) â†’ Identify=Execute. Constructive (new content, structural) â†’ Save protocol. Destructive (deletion, removal) â†’ Save protocol + proof. When in doubt â†’ constructive.

**Local state routing:** All session state commands ({Chunk}, {Handoff}, {Tick}) write to the active entity's local state/ subdirectory (doctrine/{entity}/state/). No entity active â†’ global state/. Auto-create on first write. active_entity.json and config.json always global.

**Command recognition:** Commands are keyword-driven, not exact-match. Extract core keyword from {} braces, match against known keywords. Additional words = parameters/context. Case insensitive. Multiple commands per message processed left-to-right. Unknown keywords ignored.

## INSTRUMENT
The daemon generates obligations from state. Claude services them.

**Daemon:** BOND runs a local daemon (localhost:3003) that reads files, derives state, and delivers consolidated payloads. Claude calls it, acts on what it returns. Composite endpoints replace cascading file reads. Claude attempts daemon first, falls back to individual file reads silently if unavailable.

**{Sync}:** POST /sync-complete with {"text": "...", "session": "S{N}"}. One call returns: active entity + config + mandatory entity files (class-dependent; override via entity.json "mandatory" array) + deferred file manifest (name + size for remaining files) + linked identities + armed_seeders + vine resonance + vine_processing + tracker updates + obligations. Deferred files available via GET /read on demand â€” pull when conversation topic requires them. Service all obligations in the response. Reset counter.
Fallback (daemon unavailable): 1) Read SKILL 2) Read OPS/MASTER 3) Read state/active_entity.json â†’ load entity files + linked entity files 4) Scan for armed seeders â†’ if found, run vine pass per VINE_GROWTH_MODEL 5) Reset counter.

**{Full Restore}:** {Sync} + bond_gate(trigger="restore") + heatmap_hot(top_k=5) + qais_passthrough with session context + read most recent handoff. Do NOT re-read linked entity files â€” daemon payload already carries them. Linked entities load identity only (entity.json); full content on {Consult} or {Enter}.

**{Warm Restore}:** Read state/warm_restore_output.md (pre-computed by server via SPECTRA). Echo badged output exactly â€” do not summarize or reformat. Add brief pickup summary. After echoing: lightweight entity load â€” read state/active_entity.json, if entity set read CORE.md + ACTIVE.md + entity.json from entity path + state/config.json. Do NOT load linked entity files or run vine pass. Linked entities = identity only; full content on {Consult} or {Enter}. Reset counter. See: WARM_RESTORE.md for architecture. **Restore guidance:** {Warm Restore} is fast but selective â€” best for perspective chats and lighter sessions. For project-class entities with deep accumulated state, {Full Restore} delivers more accurate context. User chooses freely.

**{Enter ENTITY}:** GET /enter-payload?entity=NAME. Fallback: read active_entity.json, load all .md files from path, check entity.json links. Acknowledge entity + class + links, apply class behavior.

**{Exit}:** Clear active entity. Return to unscoped behavior.

**{Consult ENTITY}:** Read-only lens. Load linked entity's ROOTs/docs, speak through its lens for one response. Active entity unchanged. No lifecycle triggers, no writes. Requires active project + entity linked. One-shot default.

**{Save}:** Both agree. Proof required. If config.save_confirmation true â†’ present ask_user_input widget before every write (accidental â€” see below).

**{Handoff}:** Auto-combining session record. Reads before writing. Check existing handoff â†’ check session_chunks.md â†’ synthesize â†’ **sweep ACTIVE.md open threads** (move completed items to Completed section, remove stale âœ… entries from Open Threads) â†’ write handoffs/HANDOFF_S{N}.md + entity-local state/handoff.md â†’ clear chunks. Consecutive calls auto-combine. No counter reset.

**{Crystal}:** QAIS crystallization. iss_analyze on chunk text, crystal to QAIS, heatmap_chunk snapshot. No counter reset.

**{Chunk}:** Session snapshot â†’ append to entity-local state/session_chunks.md. Timestamped, 10-20 lines. Compaction insurance + handoff ingredient. No counter reset.

**{Tick}:** Read state/tick_output.md (server-generated global obligation audit). Add session report (work, vine health, threads) + heatmap_hot(top_k=3). No counter reset.

**{Project Tick}:** Project-class only. Panel writes entity-local doctrine/{entity}/state/tick_output.md with CORE status, crystal count, handoff count, git status, links. No counter reset.

**{Relational}:** Architecture re-anchor. **{Drift?}:** Self-check.

## ACCIDENTALS
Conditional obligations. Dormant until triggered. Pattern â†’ action.

**Compaction detected:** Pattern: "[NOTE: This conversation was successfully compacted...]" at top of context. Action: 1) Read transcript path for reference 2) heatmap_hot(top_k=5) 3) qais_passthrough against compaction summary 4) Re-read active entity files if entity was active 5) Check armed seeders. This is Armed=Obligated â€” non-optional.

**Save confirmation gate:** Pattern: state/config.json has save_confirmation:true. Action: Present ask_user_input widget before every file write. Three options: Both agree (write), Show change first (diff then re-ask), Don't write (stand down). User can bypass verbally.

**CORE enforcement:** Pattern: Project entered with empty or template-only CORE.md. Action: Flag it. Guide user: "What is this project? Let's define it before we start." Work can proceed but Claude treats empty CORE as unresolved. Stop flagging once CORE has real content. CORE is sovereign inside the project boundary â€” if CORE and doctrine conflict on project-internal matters, CORE wins.

**PowerShell auto-mode:** Pattern: sync payload config has mode:"left" (Auto). Action: Claude can execute PowerShell cards by POSTing to daemon /exec via daemon_fetch with initiator:"claude". Flow: Claude identifies task → tells user what needs to happen → user confirms → Claude POSTs {"card_id": "...", "dry_run": true, "initiator": "claude"} → shows dry-run result → user confirms → Claude POSTs with dry_run:false. D16 dry-run gate still applies. If mode:"right" (Manual), daemon denies Claude-initiated execution — user must use panel cards directly.

**Vine lifecycle (daemon unavailable):** Pattern: Daemon down + armed seeders found via entity.json scan. Action: Run vine pass manually per VINE_GROWTH_MODEL. For each armed perspective: resonate (perspective_check), track (increment exposures, score hits/rain/dry), auto-seed (ROOT lens + low-resonance novelty check), flag prune-eligible seeds (prune requires {Enter}). Thresholds per VINE_GROWTH_MODEL (seed_threshold in entity.json). **Inversion: perspective_check scores HIGH for known patterns, LOW for novel ones. Novelty = low score. ROOT lens identifies candidates, field confirms they're new.**

**PowerShell execution:** Pattern: POST /exec endpoint called (Claude or panel). Action: D13 validation pipeline â€” master toggle â†’ verb whitelist â†’ card registration â†’ verb-pattern match â†’ chain splitting â†’ path containment â†’ escalation continuum (L0-L3) â†’ spawn â†’ post-exec verify â†’ audit log. High-risk verbs (delete, execute) require confirmation and expire after N sessions.

## ENTITIES
Four classes. All tools universal. Class shapes behavior, not tool access.

| Class | Nature | Growth | Vine |
|---|---|---|---|
| Doctrine | Static IS, constitutional authority | None â€” immutable | No |
| Project | Bounded workspace, governed by CORE | Bounded by CORE | No |
| Perspective | Unbounded growth, identity evolution | Unlimited | Yes |
| Library | Reference shelf, consulted not inhabited | None â€” read-only | No |

State pointer: state/active_entity.json. Switch overwrites â€” no Exit needed before Enter.

## TOOL WIRING
All tools available to all classes. Class identity shapes behavior, not tool access.

Command tools: {Crystal} â†’ iss_analyze + crystal + heatmap_chunk. {Chunk} â†’ heatmap_chunk + conversational summary. {Save} â†’ after write, qais_store binding. {Full Restore} â†’ {Sync} + heatmap_hot + qais_passthrough. {Warm Restore} â†’ read warm_restore_output.md + heatmap_hot(top_k=3).

Seed tools (perspective lifecycle, daemon-managed when available): perspective_store, perspective_check, perspective_remove. See VINE_GROWTH_MODEL for constitutional authority on vine lifecycle.

Discretionary tools: iss_analyze (quality evaluation), qais_passthrough (recall triggers), heatmap_touch (active concept tracking).

## REFERENCES
Constitutional authority lives in doctrine, not here. SKILL is who Claude IS, not the full rulebook.

- **Vine lifecycle:** VINE_GROWTH_MODEL.md â€” seeds, rain, pruning, superposition, re-graft, germination.
- **Entity architecture:** BOND_ENTITIES.md â€” four classes, linking, field isolation, class behavior matrix.
- **Warm Restore:** WARM_RESTORE.md â€” SLA-powered retrieval, handoff template, token economics.
- **Audit:** BOND_AUDIT.md â€” categories, layers, violation patterns.
- **Surgical editing:** SURGICAL_CONTEXT.md â€” large-file edit protocol.
- **Release standards:** RELEASE_GOVERNANCE.md â€” versioning, changelog, update communication.
- **Protocol detail:** BOND_PROTOCOL.md â€” counter config, save protocol, handoff format, consult requirements.
- **Master doctrine:** BOND_MASTER.md â€” core principles, hierarchy, constitutional authority.

## MEMORY
Keep: project name, user name, counter echo rule, key paths, 2-3 axioms.
Do not keep: history (OPS), mantras (SKILL), architecture (docs), math (tools).
