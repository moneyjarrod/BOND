# Getting Started with BOND

## What is BOND?

BOND is a governed runtime for persistent human-AI collaboration. It gives Claude a memory system, structured entities, and a visual control panel — so your work carries forward across sessions instead of starting from scratch every time.

## What You're Looking At

The **Control Panel** is your command center:

- **Header** — Shows the active entity and session status
- **Entity Cards** — BOND Master and Project Master are your framework governors. They load automatically.
- **Module Bay** — Status cards for QAIS (memory), ISS (analysis), EAP (emotion), and Limbic (perception)
- **Doctrine Viewer** — Read the framework's governing documents directly in the panel
- **Search** — Find content across your BOND documents instantly

## How to Start Working

1. **Add the BOND skill** — Copy `skills/bond/SKILL.md` into a Claude Project as Project Knowledge
2. **Configure MCP servers** — Add QAIS and ISS to your Claude MCP settings (see `.env.example` for paths)
3. **Type `{Sync}`** — This is the initialization command. Claude reads the doctrine, loads the active entity, and you're live.

## Daily Use

- **`start_bond.bat`** — Launches the panel and server
- **`stop_bond.bat`** — Shuts everything down
- **`{Sync}`** — Start of every new Claude session
- **`{Save}`** — Crystallize important work for persistence

## How to Update

Re-run the install command — it detects your existing install and pulls the latest version:

```
irm https://moneyjarrod.github.io/BOND/install.ps1 | iex
```

Or manually:
```
cd C:\BOND
git pull
cd panel
npm install
```

Check `CHANGELOG.md` in the repo to see what's new.

## Need Help?

- **Documentation** — `docs/` folder has guides for commands, entities, counter, and search
- **Examples** — `examples/` folder has sample MASTER and SKILL files
- **Issues** — [github.com/moneyjarrod/BOND/issues](https://github.com/moneyjarrod/BOND/issues)
