# BOND Troubleshooting: Correcting Protocol Violations

When Claude violates BOND protocols (wrong counter, skipped steps, etc.), use these methods to correct behavior.

---

## Quick Correction (All Tiers)

**Immediate verbal correction:**
```
"That's wrong. {Save} does NOT reset the counter. You were at 6/10, now 7/10."
```

Claude will acknowledge and correct. For persistent issues, use the methods below.

---

## Non-QAIS Users (Memory-Based Correction)

### Step 1: Identify the Violation

| Violation | Example |
|-----------|---------|
| Counter reset on {Save} | Was 6/10, reported 1/10 after {Save} |
| Skipped counter entirely | Response has no 🗒️ N/X |
| Wrong color threshold | At 16/10 but showed 🗒️ instead of 🟠 |
| {Sync} without reading files | Said "synced" but didn't actually read |

### Step 2: Correct via Memory

Ask Claude to add to memory:
```
"Add to your memory: {Save} does NOT reset the BOND counter. Only {Sync} resets. Counter tracks context degradation, not task completion."
```

Or be specific:
```
"Remember this rule: After {Save}, counter INCREMENTS. Example: 6/10 → {Save} → 7/10, NOT 1/10."
```

### Step 3: Verify

After correction, test:
```
"What resets the BOND counter?"
```

Claude should answer: "Only {Sync} or a new conversation resets the counter. {Save} does not."

### Step 4: Reinforce in SKILL

Add to your SKILL.md anti-patterns:
```
## ANTI-PATTERNS (NEVER)
- Reset counter on {Save} (only {Sync} resets)
- Skip counter display
- Confuse task completion with context refresh
```

---

## QAIS Users (Resonance-Based Correction)

### Step 1: Seed the Correction

Ask Claude to store the rule:
```
"Store in QAIS: BOND|counter_rule = 'Save does NOT reset counter - only Sync resets - counter tracks context degradation not task completion'"
```

Or use the tool directly:
```python
qais_store("BOND", "counter_rule", "Save does NOT reset - only Sync resets - writing is not reading")
```

### Step 2: Seed Anti-Pattern

```
"Store in QAIS: BOND|violation = 'resetting counter on Save is WRONG - Save increments Sync resets'"
```

### Step 3: Test Resonance

Ask Claude to check:
```
"Resonate 'reset counter after save' against BOND rules"
```

Should return LOW or NEGATIVE score (indicating it's wrong).

### Step 4: Create Correction Habit

Seed a self-check:
```
"Store in QAIS: Claude|self_check = 'before reporting counter ask: did I READ files or WRITE files? Write=increment Read=reset'"
```

---

## Common Violations & Fixes

### Violation: Counter Reset on {Save}

**What happened:** Claude reported 1/10 after {Save} instead of incrementing.

**Verbal fix:**
```
"Wrong. {Save} was at 6/10, report should be 7/10. {Save} writes, doesn't refresh context. Fix your counter."
```

**Memory fix:**
```
"Remember: {Save}=write=increment counter. {Sync}=read=reset counter. Never reset on {Save}."
```

**QAIS fix:**
```
Store: BOND|save_rule = "Save increments counter - was N now N+1 - never resets"
```

---

### Violation: Skipped Counter Display

**What happened:** Claude's response has no 🗒️ N/X at the end.

**Verbal fix:**
```
"You forgot the counter. Add it now. What number are we at?"
```

**Memory fix:**
```
"Remember: EVERY response ends with 🗒️ N/X counter. No exceptions."
```

**QAIS fix:**
```
Store: BOND|counter_display = "every response ends with counter emoji N/X - mandatory"
```

---

### Violation: Wrong Color Threshold

**What happened:** Counter shows 🗒️ 16/10 instead of 🟠 16/10.

**Verbal fix:**
```
"Wrong color. 15+ is always 🟠 orange. Fix it."
```

**Memory fix:**
```
"Remember: 🟠 starts at 15 (universal). 🔴 starts at 20 (universal). These override personal limits."
```

**QAIS fix:**
```
Store: BOND|thresholds = "15+ is orange 20+ is red - universal - override personal limit"
```

---

### Violation: Fake {Sync}

**What happened:** Claude said "synced" but didn't actually read files.

**Verbal fix:**
```
"You didn't actually read the files. Do a real {Sync} - read GSG_OPS.md and report current state."
```

**Memory fix:**
```
"Remember: {Sync} means ACTUALLY READ the files and report what you found. Not just say 'synced'."
```

**QAIS fix:**
```
Store: BOND|sync_rule = "Sync means read files report state reset counter - not just acknowledge"
```

---

## Prevention: Add to Your SKILL

Include in your SKILL.md Section 4 (Anti-Patterns):

```markdown
## 4. ANTI-PATTERNS (NEVER)

### Counter Violations
- Reset counter on {Save} (only {Sync} resets)
- Skip counter display at end of response  
- Use wrong color (🟠 at 15+, 🔴 at 20+ always)
- Fake {Sync} without reading files

### The Rule
- {Save} = WRITE = counter INCREMENTS (N → N+1)
- {Sync} = READ = counter RESETS (N → 1)
- Counter tracks CONTEXT DEGRADATION, not task completion
```

---

## Escalation

If corrections don't stick across sessions:

1. **Check memory:** Ask "What do you remember about BOND counter rules?"
2. **Re-seed:** Add the rule again to memory or QAIS
3. **Add to SKILL:** Put it in anti-patterns (loaded every session)
4. **Report:** If systematic, report to BOND repo as issue

---

🔥 BOND: The Bonfire Protocol
*Correct the drift. Keep the fire burning.*
