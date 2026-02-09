---
name: bond
description: >-
  BOND protocol. Triggers: Sync, Save, Crystal, Chunk, Tick, Enter, Exit,
  Full Restore, Drift, counter, emoji, bonfire, drift, session, entity,
  doctrine, perspective, project class, library class, save protocol,
  sync limit, compaction, context degradation.
---

# BOND v1.0 — Directives

## COUNTER
Echo user's tag exactly. Do NOT compute emoji.
First line of every response. No exceptions.
Resets: {Sync}, {Full Restore}, new conversation.
No reset: {Save}, {Chunk}, bonfire, task completion, compaction.
Lost count: recommend {Sync}.

## SYNC
{Sync}: 1) Read project SKILL 2) Read OPS/MASTER 3) Read state/active_entity.json — if entity set, read all files at path field; then read entity's entity.json for links array, load linked entities' .md files; if null, skip 4) Read state/config.json for save_confirmation toggle 5) Reset counter.
{Full Restore}: {Sync} + full depth read.

## COMMANDS
{Sync} read+ground+reset | {Full Restore} complete reload+reset | {Save} write proven work (both agree) | {Crystal} QAIS crystallization | {Chunk} session snapshot | {Tick} quick status | {Enter ENTITY} read state/active_entity.json, load all .md files from path, check entity.json links array and load linked .md files, acknowledge entity+class+links, apply tool boundaries | {Exit} clear active entity, confirm exit, drop tool boundaries | {Relational} arch re-anchor | {Drift?} self-check

## TOOL WIRING
Command tools (fire on command, respect class boundaries):
{Full Restore} → heatmap_hot(top_k=5), qais_passthrough with session context
{Crystal} → iss_analyze on chunk text, crystal to QAIS, heatmap_chunk snapshot
{Chunk} → heatmap_chunk snapshot
{Tick} → heatmap_hot(top_k=3) for warm concepts
{Save} → after write, qais_store binding (entity|role=save|fact=what was saved)
Discretionary tools (Claude judgment, no command needed):
iss_analyze — evaluating text quality, comparing drafts, auditing doctrine
iss_limbic — conversation shifts personal, relational, or emotionally significant
qais_passthrough — recall triggers ("remember when", "why did we", "back in session")
heatmap_touch — when actively working on a concept, touch it

## ENTITIES (Four-Class Architecture)
Doctrine: static IS, Files+ISS, no growth. Project: bounded, Files+QAIS+Heatmap+Crystal+ISS, carries CORE. Perspective: unbounded growth, Files+QAIS+Heatmap+Crystal, no ISS. Library: reference, Files only.
Pointer: state/active_entity.json. Panel writes Enter, clears Exit. {Sync} follows pointer. Switch overwrites — no drop needed. Class boundaries hard.

## SAVE
Both agree before writing. Proof required (screenshot/test/confirmation). Bug to Fix link: Symptom + Fix + Link.
If state/config.json has save_confirmation:true, present ask_user_input widget before every file write. Three options: Both agree (write), Show change first (diff then re-ask), Don't write (stand down). User can bypass verbally. Toggle off in panel.

## TRUTH
L0 SKILL (identity) then L1 OPS/MASTER (state) then L2 Code (SOURCE OF TRUTH). Higher overrides lower. Code > prose.

## DRIFT
Types: identity, architectural, terminology, state. Recovery: mantra then {Sync} then {Full Restore}.

## PRINCIPLES
Identify=Execute (fix now, do not ask). Code>Prose. Both Agree on {Save}.

## MEMORY
Keep: project name, user name, counter echo rule, key paths, 2-3 axioms. Do not keep: history (OPS), mantras (SKILL), architecture (docs), math (tools).
