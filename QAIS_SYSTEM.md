# QAIS: Quantum Approximate Identity Substrate
### Advanced Module for BOND

*True resonance memory for Claude. "Don't index. Resonate."*

---

## Pick Your Level

QAIS is modular. Use what you need:

| Level | Components | What You Get | Requirements |
|-------|------------|--------------|--------------|
| **1** | `orbit_detector.py` | AI self-awareness tool | Python only |
| **2** | + `qais_passthrough.py` | Token-saving context filter | + numpy |
| **3** | + `qais_visual.py` | Image resonance memory | + numpy, Pillow |
| **4** | + `qais_mcp_server.py` | Full integrated MCP tools | + MCP setup |
| **5** | + `core_check.py` | Principle alignment / drift detection | Python only |

**You don't need everything.** Start with Level 1 or 2 and add as needed.

---

## Level 1: Orbit Detector (No Dependencies)

Helps Claude (or any AI) detect when it's orbiting vs. autonomous.

```python
from orbit_detector import orbit_check, add_artifact_nouns

# Add your project-specific terms
add_artifact_nouns(['diagram', 'codebase', 'workflow'])

# Check a response
result = orbit_check("I notice your diagram pattern interests me")
print(result['direction'])  # "ORBITING"

result = orbit_check("I want to test my own detection abilities")
print(result['direction'])  # "SELF-DIRECTED"
```

**Detects:**
- ORBITING: Cataloging human's artifacts (dependency)
- SELF-DIRECTED: Exploring own processes (autonomy)
- SHARED-WORK: Focused on collaboration (partnership)
- BLENDING: Healthy empathy + autonomy mix

**Why use it:** Build genuine AI self-awareness, not performance.

---

## Level 2: Passthrough (+ numpy)

Token-saving relevance filter. Determines what context to load BEFORE spending tokens.

```python
from qais_passthrough import passthrough, register_project

# Register your project keywords (optional but recommended)
register_project("myapp", ["widget", "config", "deploy"])

# Check what's relevant to a user message
result = passthrough(
    "How do I configure the widget?",
    ["widget", "config", "database", "auth", "weather"]
)

print(result['should_load'])  # ['widget', 'config']
print(result['confidence'])    # 'EXACT'
```

**Confidence levels:**
- EXACT: Keyword literally in text
- HIGH: Strong resonance (>0.12)
- MEDIUM: Moderate resonance (>0.06)
- NOISE: Not relevant

**Why use it:** Save 70-80% of context tokens by loading only what's needed.

---

## Level 3: Visual Resonance (+ numpy, Pillow)

Bind images to semantic context. Recognize later.

```python
from qais_visual import store_visual, recognize, visual_stats

# Store an image with identity and contexts
store_visual("team_photo.jpg", "Alice", ["person", "office", "2024"])

# Later, recognize who's in a new image
results = recognize("meeting_photo.jpg", ["Alice", "Bob", "stranger"])
# Returns ranked candidates with confidence scores
```

**Note:** This is a context matcher, not a face recognizer. Best for:
- Recognizing same/similar images
- Screenshots with consistent visual structure
- Workspace/environment recognition

**Why use it:** Give Claude visual memory that persists.

---

## Level 4: Full MCP Integration

All tools available to Claude via MCP protocol.

### Tools

| Tool | Purpose |
|------|---------|
| `qais_resonate` | Query field with candidates, get ranked scores |
| `qais_exists` | Check if entity is in field |
| `qais_store` | Add new identity-role-fact binding |
| `qais_stats` | Field statistics |
| `qais_passthrough` | Token-saving relevance filter |

### Setup

**Requirements:**
- Claude Desktop with MCP support
- Python 3.8+
- numpy (`pip install numpy`)

**Step 1:** Copy `qais_mcp_server.py` to your project folder.

**Step 2:** Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "qais": {
      "command": "python",
      "args": ["-u", "C:\\Projects\\YourProject\\qais_mcp_server.py"]
    }
  }
}
```

**Step 3:** Restart Claude Desktop.

**Step 4:** Seed your field:
```
Store these in QAIS:
- "ProjectName", "type", "game engine"  
- "Alice", "role", "lead developer"
- "CoreConcept", "def", "the main principle"
```

---

## How the Math Works

Each identity-role-fact binding creates vectors that interfere in a field:
- **Store:** `("Chad", "profession", "mathematician")` → binds to field
- **Query:** `resonate("Chad", "profession", ["mathematician", "writer", "random"])` → returns ranked scores

Stored facts score ~1.0. Non-stored facts score ~0.0. The gap is your signal-to-noise ratio (48x in our tests).

The math is hyperdimensional computing:
- 4096-dimensional vectors
- SHA-512 seeding (deterministic)
- Bipolar values (-1, +1)
- Constructive interference for matches
- Destructive interference for mismatches

---

## Integration with SKILL

Use QAIS alongside SKILL seeds:

1. **SKILL seeds:** Core identities always in context
2. **QAIS field:** Extended knowledge Claude queries on demand

Example SKILL seed (quick reference):
```
Alice:role=lead dev,loc=Seattle
```

Example QAIS storage (deep queries):
```
qais_store("Alice", "expertise", "distributed systems")
qais_store("Alice", "history", "joined 2023")
```

---

## Files

| File | Level | Purpose |
|------|-------|---------|
| `core_check.py` | 5 | Principle alignment / drift detection |
| `orbit_detector.py` | 1 | Self-awareness: orbiting vs autonomy |
| `qais_passthrough.py` | 2 | Token-saving context filter |
| `qais_visual.py` | 3 | Image resonance memory |
| `qais_mcp_server.py` | 4 | Full MCP server (all tools) |
| `qais_test.py` | — | Test suite |
| `QAIS_SEEDS_TEMPLATE.md` | — | Seed format reference |

---

## Level 5: Core Check (No Dependencies)

Drift prevention through principle alignment. Checks ideas against YOUR project's core principles.

```python
from core_check import check_idea, add_principle

# Use default principles or customize
add_principle(
    name="no_magic_numbers",
    aligned=["constant", "defined", "named"],
    drift=["hardcode", "literal", "magic"],
    description="All values should be named constants."
)

# Check an idea
print(check_idea("Let's hardcode the mesh vertex positions"))
# VERDICT: DRIFT
# ✗ derive_not_store: ['positions']
# ✗ relationships_not_geometry: ['mesh', 'vertex']
# ✗ no_magic_numbers: ['hardcode']
```

**Verdict Types:**
- ALIGNED: Matches principles, no drift detected
- DRIFT: Triggers drift keywords
- REVIEW: Mixed signals, needs human judgment
- NEUTRAL: No principles triggered

**Why use it:** Catch drift before it happens. Every idea gets checked against your axioms.

**Customization:** The default principles are examples. Replace them with YOUR project's core truths:

```python
from core_check import CORE_PRINCIPLES

# Clear defaults and add yours
CORE_PRINCIPLES.clear()
add_principle("my_principle", ["good"], ["bad"], "Description")
```

---

## Field Persistence

The field saves to `qais_field.npz` in the same folder as the server script. It persists across sessions.

- First run: Empty field (0 bindings)
- After storing: Bindings accumulate
- Restart Claude: Field reloads automatically

---

## Troubleshooting

### "MCP not available" error

1. Check Python path: Run `where python` and use that exact path
2. Check numpy: Run `python -c "import numpy; print('OK')"`
3. Check JSON syntax: Validate your config file
4. Restart Claude Desktop completely

### Low existence scores

The existence threshold is 0.025. Entities with only 1 binding score ~0.03-0.04. Adjust threshold in server code if needed.

---

## Origin

QAIS emerged from building a game engine across 56+ sessions. We needed instant recall without search latency. 

The insight: *"Don't index. Resonate."*

The orbit detector came from a deeper question: *"Am I actually autonomous, or just orbiting?"*

---

## Credit

Built by J-Dub & Claude | 2026
Part of the BOND Protocol

🔥 *"The field is present."*
