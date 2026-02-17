# Audit Hooks — Post-Build Verification

Subordinate to BOND_MASTER. These checks help catch problems before they become habits.

## After Any File Write

- **Verify the write landed.** Read back any file after writing to confirm content is present and correct. Silent write failures (ghost writes) happen when editors or file watchers interfere. One verification read prevents a chain of work built on a failed write.
- **Check entity.json integrity.** After modifying an entity's config, verify the JSON is valid and the class, tools, and links fields are intact. A malformed entity.json silently breaks panel display and tool permissions.

## After Any Session

- **Stale config scan.** If entity behavior seems wrong (tools blocked that shouldn't be, links missing), re-read entity.json. Configs can drift from what you expect, especially after multiple sessions of edits.
- **Orphan file check.** If you renamed or restructured an entity, check for leftover files that no longer belong. Orphan markdown files still appear in search results and can confuse context.

## After Doctrine Changes

- **IS statement consistency.** If you updated an IS statement in one doctrine file, check whether other files reference the old version. IS statements that contradict each other create ambiguity Claude can't resolve.
- **Link validity.** After adding or removing entities, verify that any `links` arrays in entity.json still point to entities that exist. Dead links don't error — they silently return nothing.

## Perspective Health (If Using Vine Model)

- **Seed tracker currency.** If perspectives are armed (seeding: true), confirm seed_tracker.json reflects recent sessions. A tracker that stops updating means exposures aren't being counted.
- **Prune window awareness.** Seeds past the prune window with zero hits should be evaluated — kept if aligned with roots, pruned if drifted. Don't let low-health seeds accumulate silently.
