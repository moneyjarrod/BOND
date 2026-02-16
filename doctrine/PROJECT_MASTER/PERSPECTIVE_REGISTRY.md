# Perspective Registry — Cross-Class Bridge

## What This Document IS

This registry is PROJECT_MASTER's curated list of perspectives available to the project ecosystem. Projects load this file through their link to PM, then use it to decide which perspectives to link for cross-class context injection.

PM holds the menu. Projects order from it. The class matrix enforces what's allowed — this registry curates what's recommended.

## How It Works

1. Project enters → loads PM files (including this registry)
2. User or Claude identifies need for a perspective lens
3. Project links to perspective directly (project→perspective, allowed by class matrix)
4. Perspective context loads alongside project context
5. On exit, link persists in project's entity.json for future sessions

PM does not enforce these links. The class matrix already prevents invalid connections. This registry is governance documentation — advisory, not blocking.

## Registry

Add perspectives here as your system grows.

| Perspective | Lens | When to Link |
|---|---|---|
| *(empty — add perspectives as your system grows)* | | |

### Example Entry

| Perspective | Lens | When to Link |
|---|---|---|
| P11-Plumber | Systems thinking, flow architecture, pipe composition | Architecture decisions, debugging flow, system design |
| P12-Sacred | Relationship, covenant, friendship dynamics | Identity work, partnership decisions, values alignment |

## Badge Behavior

When a project links to a perspective:
- **Blue LINKED** badge appears on perspective card during active session
- **Purple 🔗 N** badge only counts same-class links (perspective→perspective peer references)
- Cross-class project→perspective links do NOT show purple — they're governance, not peer relationship

## Mantra

"PM holds the menu. Projects order from it."
