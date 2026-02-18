# BOND Commands

## Chat Commands

These commands are typed into Claude chat (manually or via panel bridge).

| Command | Purpose | Counter |
|---------|---------|---------|
| `{Full Restore}` | Complete reload — SKILL + OPS + state | Resets to 0 |
| `{Sync}` | Read hierarchy, ground state, write back | Resets to 0 |
| `{Save}` | Write proven work (both operators agree) | No reset |
| `{Crystal}` | Persistent crystallization to QAIS | No reset |
| `{Tick}` | Quick status snapshot | No reset |
| `{Chunk}` | Session snapshot (conversation summary) | No reset |
| `{Relational}` | Architecture re-anchor | No reset |
| `{Drift?}` | Self-check against core principles | No reset |

## Command Bar

The panel's bottom bar has buttons for the most common commands. Click flow:

1. Panel copies `BOND:{command}` to clipboard
2. AHK `OnClipboardChange` fires
3. AHK types command into Claude chat input
4. Clipboard cleared
5. User presses Enter (auto-send is OFF by default)

Requires `BOND_v8.ahk` running.

## Counter

BOND tracks conversation turns to manage context window health.

### Rules (BOND-level, in memory edits)
```
Parse «tN/L» from user message.
N = current turn count, L = limit.
Display: [emoji] N/L

🗒️ ← N ≤ L      (normal)
🟡 ← N > L      (over limit)
🟠 ← N ≥ 15     (warning)
🔴 ← N ≥ 20     (critical)

Reset ONLY on {Sync} or {Full Restore}.
User is source of truth. Never auto-increment.
```

### AHK Counter
- Persists to `%AppData%\BOND\turn_counter.txt`
- Increments on Enter when Claude window is active and BOND is ON
- Injected as `«tN/L emoji»` suffix on user messages
- Auto-starts via Windows Startup folder

## Modes (in-chat)

| Open | Close | Purpose |
|------|-------|---------|
| `<SAC>` | `<SAC/>` | Identity/mantra restore |
| `<BINS>` | `<BINS/>` | Blueprint notation |
| `<DEBUG>` | `<DEBUG/>` | Troubleshooting |

## Entity Commands (Panel)

| Action | Effect |
|--------|--------|
| View | Opens entity files in Viewer tab (read-only) |
| Load | Mounts entity to session (persists in localStorage) |
| Enter | Load + set active + open in Viewer |
| Unload | Removes from session display (does NOT delete files) |

## Tool Toggles (Panel, B69)

Each entity card shows tool toggles based on its class:

| Class | Filesystem | ISS | QAIS | Heatmap | Crystal |
|-------|-----------|-----|------|---------|---------|
| Doctrine | ✅ | ✅ | ❌ | ❌ | ❌ |
| Project | ✅ | ✅ | ✅ | ✅ | ✅ |
| Perspective | ✅ | ❌ | ✅ | ✅ | ✅ |
| Library | ✅ | ❌ | ❌ | ❌ | ❌ |

Toggles only work within class boundaries. Cross-class tools are hard-disabled. Saved to `entity.json` via `PUT /api/doctrine/:entity/tools`.

---
🔥🌊 BOND Commands — S81
