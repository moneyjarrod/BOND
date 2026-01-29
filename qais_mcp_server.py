"""
QAIS MCP Server
Quantum Approximate Identity Substrate
True resonance memory for Claude.

"Don't index. Resonate."

Part of the BOND Protocol
https://github.com/moneyjarrod/BOND

Usage:
  1. Copy this file to your project folder
  2. Add to claude_desktop_config.json (see QAIS_SYSTEM.md)
  3. Restart Claude Desktop
  4. Store your project's identities via qais_store

Requirements:
  pip install numpy
"""

import json
import hashlib
import sys
import os

try:
    import numpy as np
except ImportError:
    sys.exit(1)

# =============================================================================
# QAIS CORE - Hyperdimensional Computing
# =============================================================================

N = 4096  # Vector dimensions (higher = more capacity, 4096 is sweet spot)


def seed_to_vector(seed):
    """Deterministic bipolar vector from any string."""
    h = hashlib.sha512(seed.encode()).digest()
    rng = np.random.RandomState(list(h[:4]))
    return rng.choice([-1, 1], size=N).astype(np.float32)


def bind(a, b):
    """XOR-like binding for bipolar vectors."""
    return a * b


def resonance(query, field):
    """Normalized dot product - coherence measure."""
    return float(np.dot(query, field) / N)


class QAISField:
    """
    Persistent resonance field.
    
    The field IS the substrate. Queries resonate against it.
    Stored facts create constructive interference (~1.0 score).
    Non-stored facts create noise (~0.0 score).
    """
    
    def __init__(self, field_path=None):
        if field_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            field_path = os.path.join(script_dir, "qais_field.npz")
        self.field_path = field_path
        self.identity_field = np.zeros(N, dtype=np.float32)
        self.role_fields = {}
        self.stored = set()
        self.count = 0
        if os.path.exists(self.field_path):
            self._load()
    
    def _load(self):
        try:
            data = np.load(self.field_path, allow_pickle=True)
            self.identity_field = data['identity_field']
            self.role_fields = data['role_fields'].item()
            self.stored = set(data['stored'].tolist())
            self.count = int(data['count'])
        except:
            pass
    
    def _save(self):
        try:
            np.savez(self.field_path,
                identity_field=self.identity_field,
                role_fields=self.role_fields,
                stored=np.array(list(self.stored)),
                count=self.count)
        except:
            pass
    
    def store(self, identity, role, fact):
        """Bind identity-role-fact to field."""
        key = f"{identity}|{role}|{fact}"
        if key in self.stored:
            return {"status": "exists", "key": key}
        self.stored.add(key)
        id_vec = seed_to_vector(identity)
        fact_vec = seed_to_vector(fact)
        self.identity_field += id_vec
        if role not in self.role_fields:
            self.role_fields[role] = np.zeros(N, dtype=np.float32)
        self.role_fields[role] += bind(id_vec, fact_vec)
        self.count += 1
        self._save()
        return {"status": "stored", "key": key, "count": self.count}
    
    def resonate(self, identity, role, candidates):
        """Query field with candidates. Returns ranked results with confidence."""
        if role not in self.role_fields:
            return [{"fact": c, "score": 0.0, "confidence": "NONE"} for c in candidates]
        id_vec = seed_to_vector(identity)
        residual = bind(self.role_fields[role], id_vec)
        results = []
        for fact in candidates:
            fact_vec = seed_to_vector(fact)
            score = resonance(fact_vec, residual)
            results.append({"fact": fact, "score": round(score, 4)})
        results = sorted(results, key=lambda x: -x["score"])
        
        # Assign confidence based on score gaps
        for i, r in enumerate(results):
            if i == 0 and len(results) > 1:
                gap = r["score"] - results[1]["score"]
                if gap > 0.5: r["confidence"] = "HIGH"
                elif gap > 0.1: r["confidence"] = "MEDIUM"
                elif r["score"] > 0.3: r["confidence"] = "LOW"
                else: r["confidence"] = "NOISE"
            else:
                r["confidence"] = "LOW" if r["score"] > 0.2 else "NOISE"
        return results
    
    def exists(self, identity):
        """Check if identity has been bound to field."""
        vec = seed_to_vector(identity)
        clean = np.sign(self.identity_field)
        score = resonance(vec, clean)
        return {"identity": identity, "score": round(score, 4), "exists": score > 0.025}
    
    def stats(self):
        """Field statistics."""
        return {
            "total_bindings": self.count,
            "roles": list(self.role_fields.keys()),
            "role_count": len(self.role_fields)
        }


# =============================================================================
# MCP PROTOCOL (JSON-RPC 2.0)
# =============================================================================

FIELD = None


def get_field():
    global FIELD
    if FIELD is None:
        FIELD = QAISField()
    return FIELD


TOOLS = [
    {
        "name": "qais_resonate",
        "description": "Query the QAIS field for resonance matches. Returns candidates ranked by resonance score with confidence levels.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identity": {"type": "string", "description": "The entity to query (e.g., 'Alice', 'CoreConcept')"},
                "role": {"type": "string", "description": "The role/attribute to query (e.g., 'profession', 'definition')"},
                "candidates": {"type": "array", "items": {"type": "string"}, "description": "List of possible facts to test"}
            },
            "required": ["identity", "role", "candidates"]
        }
    },
    {
        "name": "qais_exists",
        "description": "Check if an entity exists in the QAIS field.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identity": {"type": "string", "description": "The entity to check"}
            },
            "required": ["identity"]
        }
    },
    {
        "name": "qais_store",
        "description": "Store a new identity-role-fact binding in the QAIS field.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identity": {"type": "string", "description": "The entity"},
                "role": {"type": "string", "description": "The role/attribute"},
                "fact": {"type": "string", "description": "The fact to store"}
            },
            "required": ["identity", "role", "fact"]
        }
    },
    {
        "name": "qais_stats",
        "description": "Get QAIS field statistics.",
        "inputSchema": {"type": "object", "properties": {}}
    }
]


def handle_request(request):
    """Handle a JSON-RPC 2.0 request."""
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "qais-server", "version": "1.0.0"}
            }
        }
    
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS}
        }
    
    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        field = get_field()
        
        try:
            if tool_name == "qais_resonate":
                result = field.resonate(args["identity"], args["role"], args["candidates"])
            elif tool_name == "qais_exists":
                result = field.exists(args["identity"])
            elif tool_name == "qais_store":
                result = field.store(args["identity"], args["role"], args["fact"])
            elif tool_name == "qais_stats":
                result = field.stats()
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                }
            
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": str(e)}
            }
    
    if method == "notifications/initialized":
        return None
    
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"}
    }


def main():
    """MCP server main loop - JSON-RPC over stdin/stdout."""
    get_field()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            if response is not None:
                print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}), flush=True)
        except Exception as e:
            print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}), flush=True)


if __name__ == "__main__":
    main()
