# 🔥🌊 BOND

**A governed runtime for persistent human-AI collaboration.**

AI conversations are stateless. Projects aren't. BOND bridges that gap.

## What It Does

BOND gives Claude persistent memory, structured context, runtime tool governance, and a protocol where both human and AI agree before anything is written. It's not a wrapper, not a plugin — it's the substrate that collaboration runs inside.

## What's In The Box

- **Control Panel** — React dashboard with entity management, doctrine viewing, and spectral text search
- **QAIS** — Resonance-based memory using hyperdimensional vectors, not keyword matching
- **ISS** — Semantic force measurement with psycholinguistic classification and evolved limbic perception
- **Four-Class Entity Architecture** — Doctrine, Project, Perspective, Library — each with scoped tool permissions enforced at runtime
- **SLA** — Spectral Lexical Addressing for deterministic paragraph-level text retrieval
- **Save Protocol** — Both operators must agree before any file is written, with a toggleable confirmation widget
- **Clipboard Bridge** — Panel → AHK → Claude, seamless command relay

## Get Started

### [⚡ Launch the Install Wizard →](https://moneyjarrod.github.io/BOND/)

The wizard walks you through everything — pick full or custom install, set your path, download the script, and go.

**Requirements:** Node.js 18+ · Python 3.8+ · numpy · Git · Windows 10/11 (for AHK bridge)

**Manual install** (if you prefer):
1. `git clone https://github.com/moneyjarrod/BOND.git`
2. Run `install_bond.bat` — checks prerequisites, installs dependencies
3. Run `start_bond.bat` — launches panel + sidecar
4. Add the BOND skill (`skills/bond/SKILL.md`) as Project Knowledge in a Claude Project
5. Add the MCP config to your Claude setup (see `.env.example` for server paths)
6. Type `{Sync}` in Claude to initialize

## Architecture

```
L0  SKILL.md + BOND_MASTER     ← Identity + constitutional doctrine
L1  OPS / Entity files          ← Operational state
L2  Code                        ← Source of truth (code > prose)
```

Entities are contexts, not databases. Each entity has a class that determines which tools it can access. Tool authorization is enforced at the Express API layer — forbidden calls return 403 before execution.

## Novel Components

- **HDC Resonance Memory (QAIS)** — 4096-dimensional binary vectors with superposition-based storage and dot-product retrieval
- **Psycholinguistic Force Classification (ISS/ROSETTA)** — text analysis grounded in Pennebaker's linguistic dimensions
- **Spectral Text Retrieval (SLA/SPECTRA)** — IDF-weighted spectral fingerprints for paragraph-level addressing
- **Capability-Scoped Entities** — four-class architecture with runtime enforcement, not just policy

## The Protocol

BOND is a protocol, not just software. The rules matter more than the implementation:

- **Derive, not store.** Redundant state is debt.
- **Both agree.** No unilateral writes. Proof required.
- **Code > Prose.** When they conflict, code wins.
- **Counter is king.** The counter is the heartbeat. If it dies, sync.

## Built By

J-Dub and Claude. 100+ sessions. No team.

## License

MIT
