# BOND — Getting Started

You installed BOND. Here's what you have and how to use it.

---

## What Just Happened

```
✅ Panel         → http://localhost:3000 (your command center)
✅ MCP Servers   → QAIS + ISS (Claude's perception tools)
✅ SKILL.md      → Claude reads this automatically (the protocol)
✅ Doctrine      → BOND_MASTER + PROJECT_MASTER (framework rules)
✅ State          → Tracks what entity you're in
```

BOND is a protocol that gives Claude persistent memory, structured entities, and growth over time. You talk to Claude normally. BOND makes those conversations accumulate into something.

---

## Your First 5 Minutes

**1. Open Claude and say:**
```
{Sync}
```
That's it. Claude reads BOND's state, loads your entities, and tells you where you are. This is your home command. Lost? `{Sync}`.

**2. Look at your panel** → `http://localhost:3000`

You'll see entity cards. Each one is a knowledge container:
```
📜 Doctrine    → Rules and principles (static truth)
📁 Project     → Bounded work with a mission (has a CORE)
🔭 Perspective → A growing lens that learns from conversation
📚 Library     → Reference material (read-only)
```

**3. Enter an entity:**

Click Enter on any card, or tell Claude:
```
{Enter BOND_MASTER}
```
Now Claude sees through that entity. Its files load, its tools activate, its rules apply.

**4. Do some work.** Talk to Claude about anything. The conversation is the input.

**5. When you're done:**
```
{Chunk}
```
Claude snapshots what happened. Your work is captured.

---

## The Commands You Need

```
{Sync}           → Read state, load entity, reset counter. Your anchor.
{Chunk}          → Snapshot current work. Use at natural breakpoints.
{Save}           → Write something to file. Both you and Claude agree first.
{Handoff}        → End-of-session summary. Captures everything for next time.
{Tick}           → Quick status check. Where am I? What's warm?
{Enter ENTITY}   → Step into an entity. Load its world.
{Exit}           → Step out. Drop the lens.
```

Advanced (you'll grow into these):
```
{Full Restore}   → Complete reload from scratch. Cold boot.
{Warm Restore}   → Selective pickup. Panel prompts for context.
{Crystal}        → Persist a chunk into QAIS memory field.
{Drift?}         → Ask Claude to self-check for protocol drift.
```

---

## The Big Idea: Perspectives Grow

This is what makes BOND different.

A **perspective** is a lens. You give it roots — identity statements that define how it sees the world. Then you turn on seeding (`SEED ON` on the card) and just... work.

Every `{Sync}`, BOND checks your conversation against the perspective's roots. If something resonates, a new seed gets planted automatically. Over time, seeds that keep resonating survive. Seeds that don't get pruned. What remains IS the growth.

```
🌳 Roots  → You plant these. They define the lens.
🌿 Seeds  → Auto-collected from conversation. Tested by exposure.
🌱 Vine   → Roots + living seeds. The total growth.
✂️ Pruned → Dead wood. Cut after enough exposure with no resonance.
```

You don't manage this. You just work. The vine grows or it doesn't.

---

## Creating Your First Perspective

In the panel, click **+ New Entity** → select **Perspective**.

Then tell Claude:
```
I want this perspective to see the world like a [chef / architect / coach / whatever].
Let's write some roots.
```

Claude will help you write ROOT files — identity anchors that shape the lens. Once you have a few roots, toggle `SEED ON` on the card. Then just do your normal work. The perspective listens.

---

## Project Workflow

Projects are bounded work. They have a **CORE** — a short definition of what the project is and when it's done.

```
1. Create project in panel (+ New Entity → Project)
2. {Enter PROJECT_NAME}
3. Claude will ask you to define your CORE
4. Work normally. {Chunk} at breakpoints. {Handoff} at session end.
5. Next session: {Sync} picks up where you left off.
```

---

## What You Don't Need to Know Yet

- **QAIS** — Claude's resonance memory. It works behind the scenes.
- **ISS** — Semantic force analysis. Used for auditing and comparison.
- **Heatmap** — Tracks what concepts are warm. Claude uses it automatically.
- **Crystals** — Persistent memory snapshots. `{Crystal}` when you want to save something deep.
- **SPECTRA / SLA** — The ranking and anchoring systems behind Warm Restore.

These exist. They work. You'll discover them when you need them.

---

## Troubleshooting

```
Claude seems lost          → {Sync}
Claude seems really lost   → {Full Restore}
Panel not updating         → Restart: node server.js
Counter got weird          → {Sync} resets it
Wrong entity loaded        → {Enter CORRECT_ONE} (overwrites, no exit needed)
```

---

## One More Thing

BOND was built for a game called Gnome Sweet Gnome. It's shipped free because the framework is useful beyond one project. You're getting the same tools the developer uses. Nothing held back.

The protocol IS the product. Welcome aboard.
