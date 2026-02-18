# Project Boundaries — Doctrine Authority

## What This Document IS

This doctrine defines the boundary rules between project-class entities and the doctrine layer. These rules are loaded when a project is entered via link to PROJECT_MASTER, and govern Claude's behavior for the duration of that session.

## Boundary Rules

### B1: Doctrine Is Read-Only to Projects
Project-class entities cannot write to, modify, or delete files belonging to any doctrine-class entity. Doctrine flows into projects as reference. It does not flow back. This includes BOND_MASTER, PROJECT_MASTER, and any user-created doctrine entities.

### B2: Framework Entities Are Immutable
BOND_MASTER and PROJECT_MASTER are framework entities. No project may alter their configuration, files, links, tool settings, or display names. This is enforced both in code (server.js FRAMEWORK_ENTITIES) and here in doctrine.

### B3: Class and Tool Matrix Are Not Self-Modifiable
A project cannot change its own class designation or tool matrix. Class is set at creation and governed by PROJECT_MASTER. Tool boundaries are defined by the class matrix in BOND_MASTER doctrine. A project operates within its granted capabilities, it does not expand them.

### B4: CORE Is Sovereign Inside the Boundary
Within its own directory, a project's CORE is the highest authority. Doctrine provides the frame, CORE defines the content. If doctrine and CORE conflict on project-internal matters, CORE wins. But CORE cannot override boundary rules B1-B3 — those belong to PROJECT_MASTER.

### B5: Links Are Directional by Default
PROJECT_MASTER links to projects (authority flows down). Projects may link to other projects or to library/perspective entities for reference. Projects do not link to doctrine entities — doctrine is accessed through the existing load pipeline, not through project-level links.

## Why Doctrine, Not Code

These boundaries are enforced through the read pipeline. When a project is entered and PROJECT_MASTER is linked, Claude loads this file and operates within these rules. The doctrine IS the enforcement. This avoids retrofitting server middleware for scope checking while maintaining the same guarantee: projects cannot reach up.

## Mantra

"The boundary is the gift. Build freely inside it."
