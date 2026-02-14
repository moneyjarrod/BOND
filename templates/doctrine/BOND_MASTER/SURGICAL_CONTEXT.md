# Surgical Context Management

## What Surgical Context Management IS

Surgical Context Management is a protocol for editing large files without exhausting the context window. It prevents the pattern where loading a full file + reasoning + editing burns half the window before work begins, triggering compaction mid-surgery.

## The Pattern

1. **Skeleton scan** — Read structure only (function names, line ranges), not full bodies.
2. **Composition check** — Are source and target the same material?
   - Same formatting → proceed to surgery.
   - Different formatting, no personal data → full overwrite from source of truth.
   - Different formatting, has personal data → transform first, then surgery.
3. **Plan** — Identify exact blocks needing surgery and execution order.
4. **Execute in blocks** — Load only lines needed per edit, make change, move on.
5. **Verify** — Spot-check results without re-reading the entire file.

## Why the Composition Check Exists

Step 2 was added after S114 proved the cost of skipping it. The surgical pattern worked perfectly on a single file (private server.js — 17 writeFile swaps completed in sequence). It failed when applied across two copies of the same file with different formatting (private vs public repo). Three turns burned on edit-string mismatches before a full overwrite resolved it in one.

The root cause: tool was chosen before material was checked. Plumber's ROOT-know-pipe-composition — cold water pipe and hot water pipe carry the same flow but need different handling based on material.

## Decision Rules

- **Single file, known format:** Surgery. Load blocks, edit, verify.
- **Source → target sync, no personal data:** Overwrite. Read source once, write target once.
- **Source → target sync, has personal data:** Transform. Strip personal items from source copy, then write.
- **File too large for single write_file:** Surgery is mandatory. Plan blocks to stay within output limits.

## What This Replaces

Before this pattern, the default was: read whole file → hold in context → edit → write back. That approach scales to ~200 lines before context pressure becomes a risk. Beyond that, surgical management is preferred.
