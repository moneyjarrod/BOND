"""
ISS MCP Server — Invariant Semantic Substrate
Exposes ISS analysis to Claude via MCP protocol.

Author: J-Dub & Claude
Date: 2026-02-02
"""

import json
import sys
import numpy as np
import os
import hashlib

# =============================================================================
# ISS CORE
# =============================================================================

# Use QAIS-hash for instant startup
EMBED_DIM = 512
PROJ_FILE = "iss_projections.npz"

def embed_text(text: str) -> np.ndarray:
    h = hashlib.sha512(text.encode()).hexdigest()
    seed = int(h[:16], 16) % (2**32)
    rng = np.random.default_rng(seed)
    vec = rng.choice([-1.0, 1.0], size=EMBED_DIM)
    return vec / np.linalg.norm(vec)

# Load projections
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
proj_path = os.path.join(SCRIPT_DIR, PROJ_FILE)
if os.path.exists(proj_path):
    proj = np.load(proj_path)
    P_G = proj['P_G']
    P_P = proj['P_P']
else:
    np.random.seed(42)
    P_G = np.random.randn(EMBED_DIM, 64) * 0.1
    np.random.seed(43)
    P_P = np.random.randn(EMBED_DIM, 64) * 0.1

def analyze(text: str, alpha: float = 1.0, beta: float = 1.0, gamma: float = 1.0) -> dict:
    x = embed_text(text)
    g = x @ P_G
    p = x @ P_P
    
    g_norm = float(np.linalg.norm(g))
    p_norm = float(np.linalg.norm(p))
    
    if g_norm > 1e-8 and p_norm > 1e-8:
        E = float(np.dot(g, p) / (g_norm * p_norm))
    else:
        E = 0.0
    
    g_reconstructed = g @ np.linalg.pinv(P_G)
    p_reconstructed = p @ np.linalg.pinv(P_P)
    r = x - 0.5 * (g_reconstructed + p_reconstructed)
    r_norm = float(np.linalg.norm(r))
    
    gap = alpha * r_norm + beta * abs(g_norm - p_norm) + gamma * (1.0 - E)
    
    signals = []
    imbalance = g_norm - p_norm
    if imbalance > 0.1:
        signals.append("G>P (mechanistic)")
    elif imbalance < -0.1:
        signals.append("P>G (prescriptive)")
    else:
        signals.append("balanced")
    
    if E > 0.5:
        signals.append("high coherence")
    elif E < 0.2:
        signals.append("low coherence")
    
    if r_norm > 0.8:
        signals.append("high residual")
    
    return {
        "g_norm": round(g_norm, 4),
        "p_norm": round(p_norm, 4),
        "imbalance": round(imbalance, 4),
        "E": round(E, 4),
        "r_norm": round(r_norm, 4),
        "gap": round(gap, 4),
        "diagnosis": "; ".join(signals),
        "embedding": "qais-hash"
    }

def compare(texts: list) -> list:
    return [{"text": t[:50] + "..." if len(t) > 50 else t, **analyze(t)} for t in texts]

# =============================================================================
# TOOLS
# =============================================================================

TOOLS = [
    {
        "name": "iss_analyze",
        "description": "Analyze text for semantic forces (G=mechanistic, P=prescriptive, E=coherence, r=residual, gap=imbalance)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to analyze"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "iss_compare",
        "description": "Compare multiple texts for semantic force differences",
        "inputSchema": {
            "type": "object",
            "properties": {
                "texts": {"type": "array", "items": {"type": "string"}, "description": "List of texts to compare"}
            },
            "required": ["texts"]
        }
    },
    {
        "name": "iss_status",
        "description": "Get ISS status and configuration",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]

# =============================================================================
# MCP HANDLER (simple line-based, matching QAIS)
# =============================================================================

def handle_request(request):
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {})
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "iss-server", "version": "1.0.0"}
            }
        }
    
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    
    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        
        try:
            if tool_name == "iss_analyze":
                result = analyze(args.get("text", ""))
            elif tool_name == "iss_compare":
                result = compare(args.get("texts", []))
            elif tool_name == "iss_status":
                result = {
                    "status": "active",
                    "embedding": "qais-hash",
                    "embed_dim": EMBED_DIM,
                    "proj_file": PROJ_FILE,
                    "proj_dim": 64
                }
            else:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}}
            
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
            }
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(e)}}
    
    if method == "notifications/initialized":
        return None
    
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}


def main():
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
