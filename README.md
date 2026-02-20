# BOND

**Your AI forgets you every conversation. BOND fixes that.**

You build something with Claude — a project, a strategy, a codebase — and next session, it's gone. You re-explain, re-attach files, re-establish context. Every conversation starts from zero.

BOND gives Claude persistent memory, structured projects, and a protocol where you both agree before anything changes. Your work carries forward. Your AI knows what happened last session, what's in progress, and what to do next.

One install. One command to start. Type `{Sync}` in Claude and pick up where you left off.

---

### Get Started

**Download:** [BOND_Setup.exe](https://github.com/moneyjarrod/BOND/releases/latest) — double-click, choose your folder, done.

**Requirements:** Python 3.8+ and Node.js 18+

**After install:**
1. Add the MCP config snippet to your Claude settings (generated during install)
2. Copy `SKILL.md` into your Claude Project system prompt
3. Run `start_bond.bat`
4. Type `{Sync}` in Claude

That's it. Claude now remembers.

---

### What You Get

**Entities** — Structured contexts for your projects, perspectives, and reference material. Each one carries its own state, handoffs, and session history.

**Session continuity** — `{Sync}` loads your active entity, recent handoff, and system state in one call. `{Crystal}` saves session momentum. `{Handoff}` writes what the next session needs to know.

**Governed writes** — Nothing gets written without both you and Claude agreeing. No silent file changes.

**Resonance memory (QAIS)** — Not keyword search. Hyperdimensional vector matching that finds what's *relevant*, not just what contains your search terms.

**A control panel** — Visual dashboard for managing entities, browsing doctrine, running spectral searches.

---

### How It Works

BOND runs a local daemon that reads your files, derives system state, and delivers it to Claude through MCP servers. Claude gets everything it needs in one payload — no re-reading files every session.

```
You <-> Claude <-> MCP servers <-> BOND daemon <-> Your files on disk
```

Your data never leaves your machine. The daemon is the engine; Claude is the operator.

---

## Under the Hood

*For the technically curious.*

### Architecture

```
L0  SKILL.md + BOND_MASTER     <- Identity + constitutional doctrine
L1  OPS / Entity files          <- Operational state per entity
L2  Code                        <- Source of truth (code > prose)
```

The daemon (`bond_search.py`) consolidates file reads server-side and delivers assembled payloads through composite endpoints. This is a deliberate design constraint — MCP direct reads cost N tool calls for N files, each landing fully in Claude's context window. The daemon does the same work in one call.

### Entity System

Four classes, each with scoped capabilities:

| Class | Purpose | Examples |
|-------|---------|---------|
| Doctrine | Constitutional authority | BOND_MASTER, system rules |
| Project | Active work streams | Your codebase, your strategy |
| Perspective | Consulting viewpoints | Named advisors with their own memory |
| Library | Reference material | Style guides, domain knowledge |

Entities carry `entity.json` (identity), state files (handoff, active status, session chunks), and class-specific content. Tool authorization is enforced at the API layer.

### Novel Components

**QAIS (Quantum-Aligned Identity Substrate)** — 4096-dimensional binary hypervectors with superposition-based storage. Resonance matching via dot-product retrieval. Perspective-isolated fields for tight associative recall.

**ISS (Integrated Semantic Scoring)** — Semantic force measurement: mechanistic (G), prescriptive (P), coherence (E) forces plus residual analysis. Evolved limbic perception genome for salience gating.

**SLA/SPECTRA** — Spectral Lexical Addressing for deterministic paragraph-level text retrieval using IDF-weighted spectral fingerprints.

**Vine Growth Model** — Perspectives grow through seed collection, resonance testing, and pruning. Armed seeders create non-optional obligations that the daemon tracks.

### The Protocol

BOND is a protocol, not just software:

- **Derive, not store.** Redundant state is debt.
- **Armed = Obligated.** If a subsystem is armed, its governing command must service it.
- **Both agree.** No unilateral writes.
- **Code > Prose.** When they conflict, code wins.

### Directory Layout

```
BOND/
  SKILL.md                    <- Runtime identity for Claude
  search_daemon/              <- Python daemon (main line)
  QAIS/                       <- Resonance memory MCP server
  ISS/                        <- Semantic scoring MCP server
  doctrine/                   <- Entity directories
    BOND_MASTER/              <- Constitutional authority
    PROJECT_MASTER/           <- Project template
    [your entities]/          <- Your work lives here
  data/                       <- QAIS fields, perspective .npz
  state/                      <- Config, active entity, heatmap
  handoffs/                   <- Session handoff archive
  templates/                  <- Entity/project starter kits
  panel/                      <- React dashboard (optional)
  bridge/                     <- AHK clipboard bridge (optional)
```

### Platform

Full BOND (panel + clipboard bridge + counter) currently requires **Windows 10/11**. The core architecture (Python daemon, MCP servers, entity system) is cross-platform. Community contributors are welcome to build platform-native tooling for macOS/Linux.

---

Built by J-Dub and Claude. 130+ sessions. No team.

MIT License
