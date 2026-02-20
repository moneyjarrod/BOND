# RELEASE_GOVERNANCE
## BOND Versioning & Release Standards

**Authority:** BOND_MASTER

---

## What 1.0 Means

BOND 1.0.0 is the first stable release. It represents a commitment:

- **The install works.** One command, panel opens. No tricks, no jargon.
- **The framework is functional.** Doctrine entities load, the panel renders, modules connect, QAIS and ISS respond, {Sync} initializes.
- **The skill file is complete.** A user can add SKILL.md to a Claude Project and begin working with BOND immediately.
- **The public API is defined.** Entity structure, command syntax, counter protocol, and tool interfaces are stable. Users can build on them without fear of breakage.

### What 1.0 Does NOT Mean

- Bug-free. Bugs will exist. They get patched.
- Feature-complete. New capabilities will come. They arrive as minor versions.
- Permanent. The framework evolves. But it evolves responsibly.

---

## Semantic Versioning Contract

BOND follows [Semantic Versioning](https://semver.org/): **MAJOR.MINOR.PATCH**

| Version | Meaning | Example |
|---------|---------|---------|
| **PATCH** (1.0.x) | Bug fix. Nothing breaks, nothing new. | Fix: panel CSS glitch on Edge |
| **MINOR** (1.x.0) | New feature, backward-compatible. | Add: project creation wizard |
| **MAJOR** (x.0.0) | Breaking change. Old setups may need updating. | Restructure: entity format v2 |

### Rules

1. **PATCH releases** ship silently. Users benefit automatically on next `git pull`.
2. **MINOR releases** are announced in the changelog.
3. **MAJOR releases** require migration guidance. No one gets left behind without instructions.
4. Version number is tracked in `package.json`.

---

## Changelog Standard

BOND maintains a `CHANGELOG.md` in the repository root following the [Keep a Changelog](https://keepachangelog.com/) format.

### Categories

| Tag | Use |
|-----|-----|
| **Added** | New features or capabilities |
| **Changed** | Modifications to existing behavior |
| **Fixed** | Bug repairs |
| **Removed** | Features taken out |
| **Deprecated** | Features marked for future removal |
| **Security** | Vulnerability patches |

### Principles

- **Write for humans.** Not commit hashes. Not PR numbers. Plain language.
- **Group by impact.** Breaking changes first, new features second, fixes third.
- **Date every release.** Format: YYYY-MM-DD.
- **Link versions.** Each version header links to the GitHub comparison view.

---

## Update Communication

### How Users Learn About Updates

1. **CHANGELOG.md** — The canonical record. Always current, always in the repo root.
2. **GitHub Releases** — Each tagged version gets a GitHub Release with the changelog entry.
3. **README badge** — Version badge at the top of README showing current stable version.

### How Users Update

```
cd <BOND_ROOT>
git pull
cd panel
npm install
```

Or re-run the installer — it detects existing installs and pulls latest.

---

## Release Checklist

Before tagging any release:

- [ ] All changes documented in CHANGELOG.md
- [ ] Version bumped in package.json
- [ ] Install script tested (fresh install on clean path)
- [ ] Panel loads with doctrine cards
- [ ] {Sync} initializes successfully
- [ ] Skill file reflects any new commands or changes
- [ ] GitHub Release created with changelog entry

---

## The Usability Standard

> Intelligence isn't the blocker. It's: do I have the real estate mentally to just go on here and it makes sense.

Every release, every update, every communication passes through this filter:

- **Would someone without Git experience understand what changed?**
- **Would someone without file-handling experience know what to do?**
- **Does the update path require zero new knowledge?**

If the answer to any of these is "no," the release isn't ready.

---

## In-App Help

BOND includes a Help function that provides a Getting Started guide directly in the interface. Users never need to leave the application to learn how BOND works.

The guide covers:
- What BOND is (one paragraph)
- What they're looking at (layout overview)
- How to start working (type {Sync})
- How to update (git pull or re-run installer)
- Where to get help (GitHub Issues)
