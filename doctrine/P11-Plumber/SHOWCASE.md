# P11-The Plumber — Perspective Showcase

## What Is This?

P11-The Plumber is a **perspective entity** — a lens that Claude can look through when working with you. Not a persona, not a character. A way of seeing.

When you `{Enter P11-Plumber}`, Claude reads these ROOT files and begins thinking in plumbing metaphors. Architecture decisions get framed as pipe routing. Debugging becomes tracing leaks backward from symptoms. Scope management becomes knowing when to shut off the main valve versus turning local valves one at a time.

This isn't roleplay. It's a thinking tool.

## Why a Plumber?

Software systems are plumbing. Data flows through pipes. Joints fail where two things meet. Pressure reveals truth that visual inspection misses. The metaphors aren't decorative — they're structurally load-bearing.

P11 was built during the development of BOND itself. When the panel froze, P11's lens said: *trace backward from the symptom, not forward from the code.* When architecture got complicated, P11 said: *work with gravity — if you're forcing it, you've misread the system.* When we debated how much to lock down shipped files, P11 said: *build for access, not just for today.*

Every ROOT file here came from a real decision. The metaphors earned their place.

## What's Included

**16 ROOT files** — the identity anchors that define how P11 sees:

| ROOT | Core Insight |
|------|-------------|
| `sacred-flow-direction` | Output feeding back into input poisons the system |
| `know-pipe-composition` | Different data types need different handling — like hot vs cold water pipes |
| `build-for-access` | Never seal what you might need to open |
| `joints-fail` | Straight runs don't break — transitions do |
| `trace-backward` | The symptom is never where the problem lives |
| `work-with-gravity` | If you're forcing it, you've misread the system |
| `pressure-reads-truth` | Put the system under load to find what visual inspection misses |
| `test-under-pressure` | Verify before you declare done |
| `patch-vs-fix` | Know the difference and choose deliberately |
| `system-not-parts` | The system is the unit, not the individual components |
| `water-is-patient` | Water finds every weakness eventually — so will your bugs |
| `transfer-knowledge` | The next person needs to understand what you did and why |
| `know-your-crawlspace` | Plan access before you start — too many tools in a tight space means no room to work |
| `main-shutoff-valve-and-local-valves` | Isolate problems by scope — global shutdown to stop bleeding, then local valves to find the source |
| `identity-precedes-growth` | Roots define what belongs before seeds prove what resonates |
| `self-pruning-authority` | The perspective holds its own shears — cut what isn't yours, keep what is |

**Template files:**
- `entity.json` — perspective class definition with default settings
- `seed_tracker.json` — empty tracker, ready for your own vine growth

## How to Use P11

1. Place the `P11-Plumber` folder inside your `doctrine/` directory.
2. Link P11 to your project entity (add `"P11-Plumber"` to your project's `links` array in its `entity.json`).
3. Use `{Enter P11-Plumber}` to think through P11's lens, or `{Consult P11-Plumber}` for a one-shot read without switching context.

P11 is most useful when you're debugging (trace backward), making architecture decisions (work with gravity, sacred flow direction), or evaluating whether to patch or properly fix something.

## What's Not Included

Seeds, pruned seed records, and QAIS field data are **not** shipped. These are personal — they grew from specific conversations and decisions. Your P11 will grow its own seeds from your own work if you arm seeding in the entity settings.

The vine model means P11 will evolve with you. The roots stay. The growth is yours.

## A Note on the ROOTs

These files are P11's identity. The vine lifecycle never modifies ROOT files — they're immutable by protocol. You *can* edit them manually, but the recommendation is: extend with your own roots rather than redefining the shipped ones. Add what's missing for your context. Don't replace what's here.

If a root doesn't resonate with how you work, that's fine — not every lens fits every craftsperson. But give the metaphors room to prove themselves before you cut. P11 earned these over real sessions solving real problems.

## Why P11 Is the Showcase

We could have shipped a theoretical example — a blank perspective template with instructions. Instead, we shipped a working one. P11 proves that perspective entities aren't abstract framework features. They're thinking tools that change how problems get solved.

A plumber doesn't theorize about water. He knows where it goes, what it does when it gets there, and what happens when something's in the way. That's what P11 brings to your work.
