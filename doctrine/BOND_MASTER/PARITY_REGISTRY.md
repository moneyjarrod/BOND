# Parity Registry — Framework vs Personal Classification

## Purpose

Every doctrine file under BOND_MASTER is classified as FRAMEWORK or PERSONAL.
FRAMEWORK files must exist in the public repo with matching content (minus personal references).
PERSONAL files stay in the private repo only.

When a new .md file is created in BOND_MASTER, it MUST be classified here before the session ends.
Unclassified files are a parity violation.

## Classification Rules

- **FRAMEWORK**: Defines how BOND works for any user. Protocol, principles, architecture, governance.
- **PERSONAL**: References J-Dub-specific entities, sessions, configurations, or history.
- **When unclear**: If removing all personal references leaves a useful document, it's FRAMEWORK. If removing personal references leaves nothing, it's PERSONAL.

## Registry

### BOND_MASTER Doctrine Files

| File | Class | Public Location | Notes |
|------|-------|-----------------|-------|
| BOND_MASTER.md | FRAMEWORK | doctrine/BOND_MASTER/ | Constitutional authority. Private has `GSG_OPS.md` reference → public uses `OPS/MASTER`. |
| BOND_PROTOCOL.md | FRAMEWORK | doctrine/BOND_MASTER/ | Counter, bridge, commands. Minor sanitization (session refs removed). |
| BOND_ENTITIES.md | FRAMEWORK | doctrine/BOND_MASTER/ | Four-class architecture. Path examples sanitized. |
| BOND_AUDIT.md | FRAMEWORK | doctrine/BOND_MASTER/ | Audit categories and flow. Known violations section stripped for public. |
| BOND_TRUTH.md | FRAMEWORK | doctrine/BOND_MASTER/ | Truth hierarchy and principles. `inherited from GSG` → generic, `J-Dub` → `user`. |
| SEED_COLLECTION.md | FRAMEWORK | doctrine/BOND_MASTER/ + templates/ | Vine lifecycle protocol. Identical in all three locations. |
| VINE_GROWTH_MODEL.md | FRAMEWORK | doctrine/BOND_MASTER/ + templates/ | Perspective lifecycle design. |
| WARM_RESTORE.md | FRAMEWORK | doctrine/BOND_MASTER/ + templates/ | SLA-powered session retrieval. |
| RELEASE_GOVERNANCE.md | FRAMEWORK | doctrine/BOND_MASTER/ | Versioning, changelog, release standards. |
| SURGICAL_CONTEXT.md | FRAMEWORK | doctrine/BOND_MASTER/ | Large-file edit methodology. |
| BOND_BONDFIRES.md | PERSONAL | — | Contains J-Dub session-specific solved problems. Template could be FRAMEWORK (future). |
| PARITY_REGISTRY.md | PERSONAL | — | This file. References private repo structure and personal entity names. |
| entity.json | FRAMEWORK | doctrine/BOND_MASTER/ | Links array differs: private has PERSONAL_HOOKS+CM, public has PROJECT_MASTER. |

### Other Doctrine Entities

| Entity | Class | Notes |
|--------|-------|-------|
| PROJECT_MASTER/ | FRAMEWORK | Generic project governance. Exists in both repos. |
| CM/ | PERSONAL | Calendar Master — J-Dub's doctrine entity. |
| Bridge_Doctrine/ | PERSONAL | Bridge-specific doctrine. |
| GSG/ | PERSONAL | Game project. |
| SACRED/ | PERSONAL | Sacred investigation files. |
| ROSETTA/ | PERSONAL | Force classification dictionary. Could become FRAMEWORK if generalized. |
| SPECTRA/ | PERSONAL | Spectral analysis entity. Could become FRAMEWORK if generalized. |
| SLA/ | FRAMEWORK | Search engine. Exists in both repos. |
| P11-Plumber/ | PERSONAL | J-Dub's perspective entity. |
| P12-Sacred/ | PERSONAL | J-Dub's friendship perspective. |
| PERSONAL_HOOKS/ | PERSONAL | J-Dub's workflow hooks. |
| _library/ | PERSONAL | J-Dub's reference shelf. |

### Root-Level Files

| File | Class | Notes |
|------|-------|-------|
| SKILL.md | FRAMEWORK | Identity file. Must be identical in both repos. |
| GETTING_STARTED.md | FRAMEWORK | User onboarding. Public only (not needed in private). |
| install_bond.bat | FRAMEWORK | Installer. |
| start_bond.bat | FRAMEWORK | Startup script. |
| stop_bond.bat | FRAMEWORK | Shutdown script. |
| fix_pm_template.js | FRAMEWORK | Template fix utility. |
| warm_restore.py | FRAMEWORK | Warm restore engine. |

### Templates

| File | Class | Notes |
|------|-------|-------|
| templates/doctrine/BOND_MASTER/* | FRAMEWORK | Starter copies of framework doctrine. Must match active doctrine. |
| templates/doctrine/PROJECT_MASTER/* | FRAMEWORK | Project governance templates. |
| templates/hooks/EFFICIENCY_HOOKS.md | FRAMEWORK | Platform-aware efficiency rules. |
| templates/hooks/PLATFORM_BASH_GUARD.md | FRAMEWORK | Windows bash guard. |

### Public-Only Files

| File | Notes |
|------|-------|
| README.md | Public repo landing page. |
| LICENSE | Open source license. |
| CHANGELOG.md | Release history. |
| docs/ENTITIES.md | User-facing entity documentation. |
| docs/COMMANDS.md | Command reference. |
| docs/COUNTER.md | Counter explanation. |
| docs/SEARCH.md | SLA search documentation. |
| docs/install.ps1 | PowerShell installer. |
| docs/index.html | GitHub Pages. |
| examples/ | Sample configurations. |
| skills/bond/SKILL.md | Skill file copy for Claude Projects. |
| ISS/README.md, SPEC.md, etc. | ISS documentation and training scripts. |
| QAIS/README.md | QAIS documentation. |
| SLA/README.md | SLA documentation. |

## Sanitization Patterns

When pushing FRAMEWORK files to public:
- `GSG_OPS.md` → `OPS/MASTER`
- `J-Dub` → `user` (in operational context; credit lines keep J-Dub)
- `C:\Projects\BOND_private` → `C:\BOND` or relative paths
- Session-specific references (S85, S99, etc.) → removed or generalized
- Personal entity names in examples → generic names

## Obligation

When creating a new .md file in any doctrine entity:
1. Classify it here as FRAMEWORK or PERSONAL.
2. If FRAMEWORK, write it to public repo before session ends.
3. If FRAMEWORK and it references a concept other doctrine files describe, run a sibling check.

Unclassified files at {Handoff} are flagged as parity violations.

## Mantra

"If it defines how BOND works, everyone gets it."
