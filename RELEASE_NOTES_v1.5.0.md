# BOND v1.5.0 — Two-Field Architecture

**Perspectives now remember across sessions.**

Each perspective entity maintains two separate QAIS memory fields: one for identity growth (seeds), one for session continuity (crystal). They never mix. Enter a perspective, work inside it, crystallize — that session momentum stays local. Come back later, hit 🔥 Warm, and pick up where you left off.

## What's New

### Two-Field Architecture
Perspectives now get two `.npz` files:
- **Seed field** (`{entity}.npz`) — curated identity seeds, grown through the vine lifecycle
- **Crystal field** (`{entity}_crystal.npz`) — session momentum, same shape as global crystal

No cross-contamination. Seeds stay tight for resonance checks. Crystal accumulates narrative without drowning the seeds.

### Crystal Routing
`{Crystal}` automatically routes based on active entity:
- Perspective active → writes to local crystal field exclusively
- No perspective active → writes to global (unchanged)

### Entity Warm Restore
New 🔥 Warm button appears in the panel when inside a perspective. Retrieves all session momentum from the local crystal field. Global warm restore is unchanged.

### Visual Guide
7 annotated screenshots now ship with the repo in `docs/visual_guide/`. New users can see what the panel looks like before and after setup.

### Fixes
- Doctrine/code drift corrected — false IS statements about crystal routing removed before building the real thing
- Gitignore architecture cleaned up — doctrine tracked directly, template redundancy removed

## Install / Update

**New install:**
```powershell
irm https://moneyjarrod.github.io/BOND/docs/install.ps1 | iex
```

**Existing install:**
```powershell
cd C:\BOND
git pull
cd panel
npm install
```
