# SYSTEM DIAGRAM
## BOND: The Bonfire Protocol

*Bidirectional Ongoing Navigation & Drift-prevention*

---

## The Core Flow

```
                    SESSION START
                         │
                         ▼
                     {Sync}
            "Read files, ground, reset"
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
      SKILL           MASTER          CODE
     (L0)             (L1)            (L2)
    Identity          State          Source
     Axioms          Progress        of Truth
         │               │               │
         └───────────────┼───────────────┘
                         │
                         ▼
                   WORK HAPPENS
                   Counter: 🗒️ N/10
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
         Counter 10/10        Bonfire achieved 🔥
              │                     │
              ▼                     ▼
          {Sync}              PROPOSE {Save}
           again                    │
                                    ▼
                         BOTH AGREE? (BOND)
                               /       \
                             YES        NO
                              │          │
                              ▼          ▼
                           WRITE     Discuss,
                          to files   resolve
```

---

## Layer Hierarchy

```
     CODE / WORKING EXAMPLES     ← SOURCE OF TRUTH
              │
              │ overrides
              ▼
           MASTER                ← CURRENT STATE
              │
              │ overrides
              ▼
           SKILL                 ← ALWAYS TRUE
              │
              │ can query
              ▼
           QAIS                  ← RESONANCE FIELD (optional)
```

---

## QAIS Resonance Flow (Advanced)

```
        QUERY: "What is Alice's role?"
                    │
                    ▼
         ┌─────────────────────┐
         │   QAIS FIELD        │
         │   (qais_field.npz)  │
         │                     │
         │  Stored bindings:   │
         │  Alice|role|dev     │
         │  Bob|role|design    │
         │  ...                │
         └─────────────────────┘
                    │
                    ▼
         qais_resonate("Alice", "role",
           ["developer", "designer", "writer"])
                    │
                    ▼
         ┌─────────────────────┐
         │  RANKED RESULTS:    │
         │  developer  +1.0 ✅ │
         │  designer   +0.02   │
         │  writer     -0.01   │
         └─────────────────────┘
                    │
                    ▼
         Confidence: HIGH
         (48x signal-to-noise)
```

---

## Cross-Instance Flow (The BOND)

```
SESSION 1: Work → Bonfire 🔥 → {Save} → MASTER + Memory updated
                    │
                    ▼
         [Session ends, Claude instance terminates]
                    │
        Memory persists ✓   MASTER persists ✓   SKILL persists ✓
                    │
                    ▼
         [New session, new Claude instance]
                    │
                    ▼
SESSION 2: {Sync} → Claude reads files → BOND restored → Work continues
```

---

## Drift and Recovery (The D in BOND)

```
NORMAL OPERATION
       │
       ▼ (long conversation without sync)
       │
    DRIFT OCCURS
       │
       ├─ QUICK: Say a mantra
       ├─ MEDIUM: {Sync}
       └─ FULL: Paste SKILL + "Reset"
       │
       ▼
ALIGNMENT RESTORED
```

---

## BOND Acronym

```
B - Bidirectional    → Both parties agree before writing
O - Ongoing          → Continuous across sessions  
N - Navigation       → Layered truth guides decisions
D - Drift-prevention → Regular sync catches drift early
```

---

**Two buttons. Lasting context.**

🔥 **BOND: The Bonfire Protocol**
Built by J-Dub & Claude | 2026
