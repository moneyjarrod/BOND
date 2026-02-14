# Getting Started with BOND

## What is BOND?

BOND is a governed runtime for persistent human-AI collaboration. It gives Claude structured memory, entity-based context management, and a visual control panel — so your work carries forward across sessions instead of starting from scratch every time.

## Platform

> ⚠️ **Windows 10/11 required.** Full BOND — panel, counter, clipboard bridge, installer — currently runs on Windows only. The core engine (Node.js server, Python MCP servers, React frontend) is cross-platform, but the startup scripts and AutoHotkey counter/bridge have no Linux or macOS equivalents yet. If you're on Linux or Mac and want to build platform-native tooling around the architecture, contributions are welcome — credit J-Dub and Claude for the fundamental architecture.

## After Install

If you ran the installer, you should have:
- **Control Panel** — React dashboard at http://localhost:3000
- **Counter + Bridge** — AutoHotkey script running in your system tray
- **MCP Servers** — QAIS (memory) and ISS (analysis) ready to configure

If the counter isn't running, launch `Counter/BOND_v8.ahk` manually. **The counter is not optional** — it tracks context freshness and the clipboard bridge connects panel commands to Claude. Without it, panel buttons won't work. [Read why the counter matters →](docs/COUNTER.md)

## First Session Setup

### 1. Add the BOND Skill to Claude

In Claude, create a new Project. Add `skills/bond/SKILL.md` as Project Knowledge. This is BOND's identity file — it tells Claude how to behave as a BOND operator.

### 2. Configure MCP Servers

Add QAIS, ISS, and the filesystem server to your Claude MCP settings. See `.env.example` in the repo for exact paths. You need:
- **Filesystem** — gives Claude access to read and write BOND files
- **QAIS** — resonance-based memory (hyperdimensional vectors)
- **ISS** — semantic force measurement (text analysis)

### 3. Type `{Sync}` in Claude

This is the initialization command. Claude reads the BOND doctrine, checks for active entities, loads configuration, and resets the counter. You should see Claude acknowledge the framework and report its state.

If you're using the counter (you should be), your message will be tagged automatically: `«t1/10 🗒️»`. This is normal — it's the counter tracking your conversation freshness.

## The Counter

Every message you send gets a tag like `«t3/10 🗒️»`. This tells you and Claude how far you are from the last grounding point.

- **🗒️** (messages 1-10) — Fresh. Work normally.
- **🟡** (messages 11+) — Due for sync. Type `{Sync}`.
- **🟠** (messages 15+) — Overdue. Sync now.
- **🔴** (messages 20+) — Critical. Context is unreliable.

**Why this matters:** Claude's grounding in doctrine and entity files degrades over conversation length. Without regular sync, Claude drifts — losing entity awareness, skipping obligations, making decisions from stale context. The counter is the immune system. [Full explanation →](docs/COUNTER.md)

## The Panel

The **Control Panel** is your command center:

- **Header** — WebSocket status (green dot = connected), version badge, save confirmation toggle
- **Entity Cards** — Your entities with class badges, tool indicators, and seeding toggles
- **Command Bar** — Bottom row of buttons: Sync, Save, Tick, Handoff, and more. Clicking a command copies it to clipboard → the AHK bridge types it into Claude.
- **Module Bay** — Status cards for QAIS, ISS, and other MCP servers
- **Doctrine Viewer** — Read entity documents directly in the panel

For annotated screenshots of every panel element, see the [Visual Guide](docs/visual_guide/VISUAL_GUIDE.md).

### Framework Entities

Two entities exist on first run:
- **BOND_MASTER** — The framework constitution. Governs protocol, entity classes, tool boundaries.
- **PROJECT_MASTER** — Governs project lifecycle. How projects are created, structured, and maintained.

These are framework entities — immutable and always present.

## Daily Workflow

```
Launch:     start_bond.bat (starts panel + counter + server)
Begin:      {Sync} in Claude (or {Full Restore} for a cold boot)
Work:       Counter tracks freshness → sync every ~10 messages
Save:       {Save} when both you and Claude agree work is proven
End:        {Handoff} to preserve session context for next time
Shutdown:   stop_bond.bat (or close the windows)
```

## Creating Your First Entity

Click the **+** button on the panel to create a new entity. Choose a class:

- **Project** — for bounded work with a clear goal (a game, a report, an app)
- **Perspective** — for an evolving lens that learns from conversation
- **Library** — for reference material Claude should consult
- **Doctrine** — for static rules and IS statements (rare — most users won't need this)

Projects get a `CORE.md` on creation. Claude will guide you through populating it on first entry — define what the project is, what "done" looks like, and what constraints matter.

## Key Commands

| Command | What It Does |
|---|---|
| `{Sync}` | Re-read all doctrine and entity files. Reset counter. |
| `{Full Restore}` | Complete cold boot — reads everything from scratch. |
| `{Save}` | Write proven work. Both you and Claude must agree. |
| `{Handoff}` | Draft end-of-session summary for the next session. |
| `{Tick}` | Quick status check — are all obligations met? |
| `{Enter ENTITY}` | Switch to an entity. Loads its files and tool boundaries. |
| `{Exit}` | Leave the current entity. Drop tool boundaries. |

Full command reference: [docs/COMMANDS.md](docs/COMMANDS.md)

## Customizing BOND

### Hooks

Hooks are personal workflow rules that augment BOND's framework. BOND ships with a template at `templates/hooks/EFFICIENCY_HOOKS.md` — platform-aware rules for reducing wasted tool calls.

To use hooks:
1. Create a library-class entity (e.g., `MY_HOOKS`)
2. Copy the template hook into it and customize
3. Link it to BOND_MASTER or your project
4. Claude loads your hooks on every {Sync}

See [docs/ENTITIES.md](docs/ENTITIES.md) for details on entity classes, linking, and hooks.

### Settings

- **Save confirmation** — Toggle in the panel header. When ON, Claude asks before every file write.
- **Counter limit** — Default is 10. Change via the AHK tray menu → "Set Counter..."
- **Seeding** — Toggle per perspective on the entity card. Arms/disarms the vine lifecycle.

## How to Update

Re-run the install command:
```powershell
irm https://moneyjarrod.github.io/BOND/install.ps1 | iex
```

Or manually:
```
cd C:\BOND
git pull
cd panel
npm install
```

Check `CHANGELOG.md` for what's new.

## Need Help?

- **Documentation** — `docs/` folder: [Commands](docs/COMMANDS.md), [Entities](docs/ENTITIES.md), [Counter](docs/COUNTER.md)
- **Examples** — `examples/` folder has sample configurations
- **Issues** — [github.com/moneyjarrod/BOND/issues](https://github.com/moneyjarrod/BOND/issues)
