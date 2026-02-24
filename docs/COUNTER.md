# Why the Counter Matters

## The Problem BOND Solves Every 10 Messages

Claude doesn't have persistent memory. Every message you send exists inside a context window — a fixed-size buffer that holds the entire conversation. As the conversation grows, the oldest context gets pushed toward the edges. Claude doesn't "forget" in a human sense — it gradually loses *grounding*. The doctrine it read at the start of the session becomes distant. Entity files blur. Truth hierarchy fades.

This is not a bug. It's how large language models work. BOND doesn't fix the architecture — it works *with* it.

## What the Counter Is

Every message in BOND is tagged with a counter: `«t1/10 🗒️»` through `«t10/10 🟡»`. This is the heartbeat of the system. It tells both you and Claude how far you are from the last grounding point.

The counter isn't a timer. It's a **context freshness gauge**. At `t1/10`, Claude just synced — doctrine is loaded, entity files are read, truth hierarchy is active, obligations are checked. By `t10/10`, all of that is 10 exchanges old. It's still in the window, but it's no longer front-of-mind.

## What Happens Without Sync

Here's what degrades as you pass the sync window without refreshing:

**Messages 1-10 (green zone):** Claude is grounded. Entity context is fresh. Tool boundaries are respected. Obligations are tracked. Decisions align with doctrine.

**Messages 11-15 (yellow zone):** Grounding starts to soften. Claude may still function well, but it's working from memory of the doctrine rather than direct reference. Subtle drift begins — terminology loosens, entity awareness thins.

**Messages 16+ (red zone):** Real degradation. Claude may:
- Forget which entity is active and apply wrong tool boundaries
- Skip obligations that were clear at sync time
- Make decisions that contradict doctrine it read 20 messages ago
- Lose track of linked entities and their files
- Drift from the truth hierarchy (treating prose as authoritative over code)
- Miss vine lifecycle obligations for armed perspectives

None of this is Claude being careless. The grounding context has simply moved far enough back in the window that it no longer dominates Claude's attention. This is predictable, measurable, and preventable.

## Why 10 Is the Number

10 is not arbitrary. It's the empirically observed sweet spot where:

- Context from the last sync is still strongly influential
- Enough work has been done to justify the cost of re-reading files
- Drift hasn't accumulated enough to cause real errors

You can sync more often (every 5-7 messages during complex work). You can push past 10 occasionally for simple exchanges. But 10 is the default because it reliably prevents the degradation described above.

## What {Sync} Actually Does

When you type `{Sync}`, Claude re-reads the entire grounding stack:

1. **SKILL.md** — The protocol identity. Who BOND is and how it behaves.
2. **OPS/MASTER** — Operational state and session context.
3. **Active entity files** — Every `.md` file in the current entity directory.
4. **Linked entity files** — Files from any entities linked to the active one.
5. **Config** — Settings like save confirmation toggle.
6. **Vine lifecycle** — For any armed perspectives, runs the full seed check cycle.
7. **Counter reset** — AHK bridge resets to `t1/10` automatically when it detects {Sync}.

This puts doctrine back at the *front* of Claude's attention. It's not restarting the conversation — it's refreshing the foundation that everything else is built on.

## What You Need to Do

**Watch the counter.** It's in every message. When it hits yellow (`🟡`), it's time to sync.

**Type `{Sync}` regularly.** It takes Claude a few seconds to re-read everything. That's a small cost compared to the drift that accumulates without it.

**Don't ignore the emoji.** The progression from 🗒️ (fresh) to 🟡 (due) to 🔴 (overdue) is a visual warning system. Treat yellow as "sync soon" and red as "sync now."

**After long exchanges without sync,** expect Claude to be less precise about entity context, doctrine details, and obligations. If something feels off, sync first, then reassess.

## The Analogy

Think of it like instrument calibration. A perfectly calibrated gauge reads true at the start of the day. As temperature shifts, vibration accumulates, and drift sets in, the readings become less reliable. You don't throw out the gauge — you recalibrate. `{Sync}` is recalibration. The counter tells you when you're due.

## Quick Reference

| Counter | Status | Action |
|---------|--------|--------|
| `t1-7/10 🗒️` | Fresh | Work normally |
| `t8-9/10 🗒️` | Aging | Consider syncing if doing complex work |
| `t10/10 🟡` | Due | Sync before next major task |
| `t11+/10 🟡` | Overdue | Sync immediately |
| `🔴` | Critical | Stop and sync — context is unreliable |

## Summary

The counter is not a suggestion. It's the mechanism that keeps BOND reliable. Without regular sync, Claude drifts from the doctrine, entities, and truth hierarchy that make BOND work. The protocol is only as strong as the last time it was read.

**Sync early. Sync often. Trust the counter.**
