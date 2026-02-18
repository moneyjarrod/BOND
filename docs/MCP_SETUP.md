# MCP Server Setup

BOND uses three MCP servers that Claude needs configured before `{Sync}` will work. This guide gives you the exact JSON to paste into your Claude configuration.

## Where to Add This

**Claude Desktop (Windows):**
Open `%APPDATA%\Claude\claude_desktop_config.json` in any text editor. If the file doesn't exist, create it.

**Claude Code / Other MCP Clients:**
Add these server definitions to your MCP client's configuration. The transport is `stdio` for all three.

## Configuration

Paste this into your `claude_desktop_config.json`. If you installed BOND to a different path than `C:\BOND`, replace all instances of `C:\\BOND` with your actual path.

```json
{
  "mcpServers": {
    "qais": {
      "command": "python",
      "args": ["C:\\BOND\\QAIS\\qais_mcp_server.py"],
      "env": {
        "BOND_ROOT": "C:\\BOND"
      }
    },
    "iss": {
      "command": "python",
      "args": ["C:\\BOND\\ISS\\iss_mcp_server.py"],
      "env": {
        "BOND_ROOT": "C:\\BOND"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "C:\\BOND"
      ]
    }
  }
}
```

> **Note:** If you already have other MCP servers configured, merge the three entries above into your existing `mcpServers` object — don't replace the whole file.

## What Each Server Does

**QAIS** (Quantum Approximate Identity Substrate) — Resonance-based memory. Stores identity-role-fact bindings as hyperdimensional vectors. Provides tools like `qais_store`, `qais_resonate`, `qais_passthrough`, `heatmap_*`, `crystal`, `daemon_fetch` (bridge to search daemon), and the perspective seed tools (`perspective_store`, `perspective_check`, `perspective_remove`). Data persists in `C:\BOND\data\`.

**ISS** (Invariant Semantic Substrate) — Text analysis. Classifies semantic forces in text (mechanistic, prescriptive, coherence) and provides limbic perception (salience, threat, gate). Tools: `iss_analyze`, `iss_compare`, `iss_limbic`, `iss_status`.

**Filesystem** — Gives Claude read/write access to BOND's doctrine files, entity configs, state files, and handoffs. Without this, Claude can't load entities or write saves. The path argument (`C:\BOND`) restricts access to only the BOND directory.

## Verifying It Works

After saving the config and restarting Claude:

1. Open a Claude conversation in your BOND project
2. Type `{Sync}`
3. Claude should report reading BOND_MASTER, checking entities, and resetting the counter

If Claude says it can't find tools like `qais_store` or `iss_analyze`, the MCP servers aren't connected. Check:
- Is Python on your PATH? (run `python --version` in a terminal)
- Is Node.js on your PATH? (run `node --version`)
- Is numpy installed? (run `pip install numpy` if not)
- Are the paths in the config correct for your install location?

You can also check the **Systems** tab in the BOND panel — it shows whether QAIS and ISS are responding.

## Environment Variable

Both QAIS and ISS use the `BOND_ROOT` environment variable to find the `data/`, `state/`, and `doctrine/` directories. If `BOND_ROOT` is not set, they default to the parent directory of their own script location — which works correctly when installed to `C:\BOND`. You only need to set `BOND_ROOT` explicitly if you moved the servers to a non-standard location.
