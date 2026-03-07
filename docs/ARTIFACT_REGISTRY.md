# ARTIFACT REGISTRY
## BOND Protocol — Persistent Artifacts

*{ArtD} reads this file, copies SOURCE → OUTPUT, presents to sidebar.*

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

**SOURCE** = `C:\Projects\BOND_github\artifacts\` (survives between sessions)
**OUTPUT** = `/mnt/user-data/outputs/` (wipes each session)

---

## Artifact Registry

| Name | Source Path | Type | Description |
|------|-------------|------|-------------|
| Möbius Variations | `artifacts/S76_mobius_pull_acceleration_variations.md` | MD | Self-collision vs multi-pass smearing design doc |
| Flash Reflection | `artifacts/S76_t2_flash_reflection.md` | MD | S76 flash observation (E=+0.043) reflection |

---

## Adding New Artifacts

1. Create artifact in `artifacts/` folder
2. Add row to registry table above
3. {ArtD} includes it automatically

---

🔥🌊 BOND Protocol | J-Dub & Claude