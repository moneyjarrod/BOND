# QAIS: Quantum Approximate Identity Substrate
### Advanced Module for BOND

*True resonance memory for Claude. "Don't index. Resonate."*

---

## What This Is

QAIS is a vector-based identity system that lets Claude **resonate** against stored knowledge rather than pattern-match text. Instead of searching through documents, Claude queries a mathematical field that returns confidence-scored matches.

**The difference:**
- **Without QAIS:** Claude searches text, finds keywords, hopes for matches
- **With QAIS:** Claude queries a field, gets ranked results with HIGH/MEDIUM/LOW/NOISE confidence

---

## When to Use QAIS

**Use QAIS if:**
- You have many entities (people, concepts, systems) to track
- You want instant recall without search latency
- You're building long-term projects with Claude
- You want measured confidence, not guessing

**Skip QAIS if:**
- Your project is simple (few entities)
- You're fine with SKILL seeds alone
- You don't want to run a Python MCP server

---

## How It Works

### The Math (High Level)

Each identity-role-fact binding creates vectors that interfere in a field:
- **Store:** `("Chad", "profession", "mathematician")` → binds to field
- **Query:** `resonate("Chad", "profession", ["mathematician", "writer", "random"])` → returns ranked scores

Stored facts score ~1.0. Non-stored facts score ~0.0. The gap between them is your signal-to-noise ratio (48x in our tests).

### The Tools

| Tool | Purpose |
|------|---------|
| `qais_resonate` | Query field with candidates, get ranked scores |
| `qais_exists` | Check if entity is in field |
| `qais_store` | Add new identity-role-fact binding |
| `qais_stats` | Field statistics |

---

## Setup

### Requirements

- Claude Desktop with MCP support
- Python 3.8+
- numpy (`pip install numpy`)

### Step 1: Install Server

Copy `qais_mcp_server.py` to your project folder (e.g., `C:\Projects\YourProject\`).

### Step 2: Configure MCP

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

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

**Note:** Use double backslashes `\\` in paths. The `-u` flag ensures unbuffered output.

### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop. The QAIS tools should now be available.

### Step 4: Seed Your Field

Tell Claude to store your project's core identities:

```
Store these in QAIS:
- "ProjectName", "type", "game engine"  
- "Alice", "role", "lead developer"
- "CoreConcept", "def", "the main principle"
```

Claude will call `qais_store` for each.

---

## Usage

### Querying

Ask Claude questions that involve your stored identities. Claude can call:

```
qais_resonate("Alice", "role", ["lead developer", "designer", "writer"])
```

Response:
```json
[
  {"fact": "lead developer", "score": 1.0, "confidence": "HIGH"},
  {"fact": "designer", "score": 0.02, "confidence": "NOISE"},
  {"fact": "writer", "score": -0.01, "confidence": "NOISE"}
]
```

### Checking Existence

```
qais_exists("Alice")
```

Response:
```json
{"identity": "Alice", "score": 0.18, "exists": true}
```

### Adding New Knowledge

```
qais_store("NewPerson", "role", "consultant")
```

Response:
```json
{"status": "stored", "key": "NewPerson|role|consultant", "count": 4}
```

---

## Field Persistence

The field saves to `qais_field.npz` in the same folder as the server script. It persists across sessions.

- First run: Empty field (0 bindings)
- After storing: Bindings accumulate
- Restart Claude: Field reloads automatically

---

## Integration with SKILL

You can use QAIS alongside SKILL seeds. Recommended approach:

1. **SKILL seeds:** Core identities that should always be in context
2. **QAIS field:** Extended knowledge Claude can query on demand

Example SKILL seed format (for quick reference):
```
Alice:role=lead dev,loc=Seattle
CoreConcept:def=main principle,bf=B1
```

Example QAIS storage (for deep queries):
```
qais_store("Alice", "expertise", "distributed systems")
qais_store("Alice", "project", "backend rewrite")
qais_store("Alice", "history", "joined 2023")
```

---

## Troubleshooting

### "MCP not available" error

1. Check Python path: Run `where python` and use that exact path in config
2. Check numpy: Run `python -c "import numpy; print('OK')"`
3. Check JSON syntax: Validate your config file
4. Restart Claude Desktop completely

### "Invalid JSON" in logs

The server might be outputting something before JSON-RPC. Ensure the server file is the correct version (no print statements on startup).

### Low existence scores for known entities

The existence threshold is 0.025. Entities with only 1 binding score ~0.03-0.04. If you're getting false negatives, you can lower the threshold in the server code:

Find: `"exists": score > 0.025`
Adjust as needed.

---

## Files

| File | Purpose |
|------|---------|
| `QAIS_SYSTEM.md` | This documentation |
| `qais_mcp_server.py` | The MCP server (copy to your project) |
| `QAIS_SEEDS_TEMPLATE.md` | Seed format reference |

---

## Origin

QAIS emerged from building a game engine across 56 sessions. We needed instant recall without search latency. The insight: "Don't index. Resonate."

The math is based on hyperdimensional computing — high-dimensional vectors that interfere constructively when matched and destructively when mismatched. 4096 dimensions. SHA-512 seeding. Bipolar vectors.

---

## Credit

Built by J-Dub & Claude | 2026
Part of the BOND Protocol

🔥 *"The field is present."*
