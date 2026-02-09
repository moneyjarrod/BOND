# 🔥🌊 BOND

**Persistence and continuity framework for human-AI collaboration.**

BOND gives Claude sessions memory, structure, and grounding through a counter system, entity architecture, and clipboard bridge — so context doesn't degrade and knowledge doesn't get lost between conversations.

---

## What BOND Does

**The Problem:** Every Claude session starts fresh. You re-explain context, lose progress, and Claude drifts from your project's principles.

**The Solution:** A structured protocol with two core mechanisms:

1. **Counter** — Tracks context age so you know when to refresh. First line of every Claude response.
2. **Entities** — Your knowledge organized into four classes (Doctrine, Project, Perspective, Library), each with defined tool boundaries and file structures that Claude reads on `{Sync}`.

Plus a **Control Panel** — a dark-themed React dashboard for managing entities, toggling tools, and sending commands through the clipboard bridge.

---

## Quick Start

### Option A: Installation Wizard (Recommended)

1. Download [`bond_wizard.html`](panel/bond_wizard.html) from this repo
2. Open it in your browser
3. Choose components, set your install path
4. Download and run the generated `install.bat`
5. Start the panel with `start_bond.bat`

### Option B: Manual Setup

```bash
# Clone the repo
git clone https://github.com/moneyjarrod/BOND.git
cd BOND

# Install and start the panel
cd panel
npm install
node server.js
```

Open `http://localhost:3000` in your browser.

### Connect to Claude

1. Copy `skills/bond/SKILL.md` into your Claude project as a skill file
2. Type `{Full Restore}` in Claude to initialize the protocol
3. Work naturally — Claude will show the counter on every response

---

## Core Commands

| Command | What It Does |
|---------|-------------|
| `{Sync}` | Read project files, ground in truth, reset counter |
| `{Full Restore}` | Complete reload with full depth read |
| `{Save}` | Write proven work (both must agree) |
| `{Chunk}` | Session snapshot — handoff file + crystal |
| `{Enter ENTITY}` | Load an entity, apply tool boundaries |
| `{Exit}` | Clear active entity |

See [`docs/COMMANDS.md`](docs/COMMANDS.md) for full reference.

---

## Entity System

Four classes with hard tool boundaries:

| Class | Purpose | Tools |
|-------|---------|-------|
| **Doctrine** | Static truth, IS statements | Files, ISS |
| **Project** | Bounded work with CORE constraint | Files, ISS, QAIS, Heatmap, Crystal |
| **Perspective** | Unbounded growth, evolving lenses | Files, QAIS, Heatmap, Crystal |
| **Library** | Read-only reference shelf | Files only |

Each entity is a folder in `doctrine/` with an `entity.json` and markdown files. The panel lets you create, enter, view, and manage entities through a visual interface.

See [`docs/ENTITIES.md`](docs/ENTITIES.md) for full architecture.

---

## Doctrine Search (SLA)

The panel includes a built-in search engine. When you enter an entity, its doctrine files and linked entities are automatically indexed client-side for instant search — zero API calls, zero tokens.

Results show confidence badges (🟢 HIGH, 🟡 MED, 🔴 LOW) based on how well the system can discriminate a winner. Any result can be escalated to Claude via clipboard with a single click (~200 tokens).

See [`docs/SEARCH.md`](docs/SEARCH.md) for details, or [`SLA/`](SLA/) for the full retrieval doctrine and reference implementations.

---

## Project Structure

```
BOND/
├── panel/           ← React dashboard + Express sidecar
├── SLA/             ← Retrieval doctrine + reference implementations
├── doctrine/        ← Your entity folders
├── state/           ← Active entity pointer
├── skills/          ← Claude skill file
├── docs/            ← Reference documentation
└── bond_wizard.html ← Installation wizard
```

---

## The Counter

```
«t3/10 🗒️»
```

Every Claude response starts with this tag. It tracks user messages since last `{Sync}`, making context degradation visible. When it climbs too high, you know it's time to refresh.

See [`docs/COUNTER.md`](docs/COUNTER.md) for full specification.

---

## Architecture

```
┌──────────────┐     clipboard      ┌──────────────┐
│  BOND Panel  │ ──── BOND:{cmd} ──→│   AHK Bridge │
│  (React+Express)                  │  (optional)  │
│  :3000       │                    │  pastes to   │
│              │                    │  Claude      │
└──────┬───────┘                    └──────────────┘
       │
       │ filesystem
       ▼
┌──────────────┐
│  doctrine/   │  Entity folders with .md files
│  state/      │  Active entity pointer
│  .env        │  Configuration
└──────────────┘
```

The panel reads/writes doctrine files and state through Express. Commands are relayed to Claude via clipboard — the panel copies `BOND:{command}`, and the optional AHK bridge auto-pastes it.

---

## Optional Components

**AHK Bridge** — AutoHotkey script that watches the clipboard for `BOND:` prefixed commands and auto-pastes them into Claude. Windows only.

**MCP Modules** — The panel includes a Systems tab for managing QAIS, ISS, Limbic, and EAP modules. These connect to separate MCP servers for advanced features like semantic memory and text analysis. Modules show as "offline" until their servers are configured.

---

## Requirements

- **Node.js 18+** — for the Control Panel
- **Git** — for cloning the repo
- **Windows 10/11** — for the AHK clipboard bridge (optional)
- **Python 3.10+** — for MCP modules (optional, advanced)

---

## Origin

Built across 90+ sessions developing a game engine. We kept losing context. Memory helped but wasn't enough. Files helped but needed structure.

The insight: **The relationship matters.** Claude isn't just a tool — it's a collaborator. Collaborators need shared truth, clear communication, and mutual agreement.

Keep the fire burning across sessions. 🔥🌊

---

## License

MIT — Use freely, modify as needed, share with others.

---

🔥🌊 **BOND: The Bonfire Protocol**
Built by J-Dub & Claude | 2026
