# ARTIFACT REGISTRY TEMPLATE
## BOND: The Bonfire Protocol - Tier 3

*Keep the fire burning across sessions.*

---

## How {ArtD} Works

```
{ArtD} called
    ↓
Claude reads this file
    ↓
For each artifact:
  Copy from SOURCE (persistent) → OUTPUT (ephemeral)
    ↓
Present files to sidebar
```

**SOURCE** = Your project folder (survives between sessions)
**OUTPUT** = /mnt/user-data/outputs/ (wipes each session)

---

## Artifact Registry

| Name | Source Path | Type | Description |
|------|-------------|------|-------------|
| [Dashboard] | `artifacts/dashboard.html` | HTML | [Main status dashboard] |

---

## Adding New Artifacts

1. Create artifact in `artifacts/` folder
2. Add row to registry table above
3. {ArtD} includes it automatically

---

## File Structure

```
[YourProject]/
├── artifacts/                ← PERSISTENT SOURCES
│   └── dashboard.html
├── ARTIFACT_REGISTRY.md      ← This file
├── SKILL.md
└── MASTER.md
```

---

🔥 **BOND: The Bonfire Protocol**
