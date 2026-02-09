# QAIS — Quantum Approximate Identity Substrate

*"Don't index. Resonate."*

QAIS is BOND's persistent memory system. It stores identity-role-fact triplets as high-dimensional vectors and retrieves them through resonance rather than keyword matching.

## What It Does

- **Resonance storage**: Store facts about entities as `identity|role|fact` bindings
- **Resonance retrieval**: Query what's stored about an entity by testing candidates against the field
- **Session heat map**: Track which concepts are active during a session
- **Crystal persistence**: Crystallize session momentum for cross-session continuity
- **Conditional routing**: BOND gate evaluates message triggers to adjust tool activation

## MCP Tools

| Tool | Description |
|------|-------------|
| `qais_store` | Store an identity-role-fact binding |
| `qais_resonate` | Test candidates for resonance with stored facts |
| `qais_exists` | Check if an identity exists in the field |
| `qais_get` | Direct retrieval by identity + role |
| `qais_stats` | Field statistics |
| `qais_passthrough` | Token-saving relevance filter |
| `heatmap_touch` | Mark concepts as active |
| `heatmap_hot` | Get hottest concepts by recent activity |
| `heatmap_chunk` | Heat map snapshot for {Chunk} |
| `heatmap_clear` | Reset heat map for new session |
| `crystal` | Persistent session crystallization |
| `bond_gate` | Conditional routing gate |

## Architecture

QAIS uses 4096-dimensional binary vectors (HDC — Hyperdimensional Computing). Each identity and fact gets a deterministic vector from SHA-512 seeding. Storage is superposition-based: multiple bindings coexist in the same vector space. Retrieval uses dot-product resonance.

Data persists to `data/qais_field.npz` with immediate write-through on every store operation.

## Class Boundaries

QAIS tools are available to **project** and **perspective** class entities. Doctrine and library entities cannot access QAIS — this is enforced at runtime by `tool_auth.py`.

## Setup

QAIS runs as an MCP server. Add to your Claude MCP configuration:

```json
{
  "mcpServers": {
    "qais": {
      "command": "python",
      "args": ["BOND_ROOT/QAIS/qais_mcp_server.py"],
      "env": { "BOND_ROOT": "your/bond/path" }
    }
  }
}
```

Requires: Python 3.8+, numpy.
