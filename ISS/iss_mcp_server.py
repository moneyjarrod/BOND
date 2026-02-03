"""
ISS MCP Server v2.0 — Invariant Semantic Substrate + Limbic (10D EAP)
Exposes ISS analysis and limbic perception to Claude via MCP protocol.

Tools: iss_analyze, iss_compare, iss_limbic, iss_status

Limbic v2.0: 10D EAP input, evolved genome (S75, fitness 0.017)
  Pipeline: Claude native read → EAP (10 floats) → ISS forces → Genome → S/T/G
  Constraints: C1-C4 compliant (no word lists, no new axes, no vocab logic)

Author: J-Dub & Claude
Date: 2026-02-02 (v1.0), 2026-02-03 (v2.0)
Session: S75
"""

import json
import sys
import numpy as np
import os
import hashlib

# =============================================================================
# ISS CORE
# =============================================================================

EMBED_DIM = 512
PROJ_FILE = "iss_projections.npz"

def embed_text(text: str) -> np.ndarray:
    h = hashlib.sha512(text.encode()).hexdigest()
    seed = int(h[:16], 16) % (2**32)
    rng = np.random.default_rng(seed)
    vec = rng.choice([-1.0, 1.0], size=EMBED_DIM)
    return vec / np.linalg.norm(vec)

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
# LIMBIC v2.0 — Evolved 10D EAP Genome (S75, fitness 0.017)
# =============================================================================
# EAP schema: [valence, arousal, confidence, urgency, connection,
#              curiosity, frustration, fatigue, wonder, trust]
#
# Input vector (16): ISS(5) + EAP(10) + QAIS(1)
# Derived (5): |valence|, max(0,-val), |g-p|, (1-E), (1-qais)
# Output: S(salience), T(threat), G(gate), V(valence passthrough)

EAP_NAMES = ["valence", "arousal", "confidence", "urgency", "connection",
             "curiosity", "frustration", "fatigue", "wonder", "trust"]

# --- Evolved weights (hardcoded from limbic_genome_10d.json) ---

# S (Salience) raw weights: [g_norm, p_norm, E, r_norm, gap,
#   valence, arousal, confidence, urgency, connection,
#   curiosity, frustration, fatigue, wonder, trust, qais_score]
S_RAW = np.array([
    0.3557, 0.5550, -0.0634, 0.3239, 0.4997,
    0.1450, 0.5622, -0.4786, -0.4183, 0.6361,
    -0.1271, 0.2949, 0.3145, 0.2332, -0.4887, -0.1811
])
S_DERIVED = np.array([0.3309, -0.2142, 0.0663, -0.4381, -0.8057])
S_BIAS = 0.0742

# T (Threat) raw weights
T_RAW = np.array([
    0.0318, 0.9895, -0.1544, -0.8483, -0.0094,
    0.4800, -0.8201, -0.8575, 0.1807, -0.1981,
    0.0053, -0.0314, -0.2000, -0.1210, -0.5289, 0.0183
])
T_DERIVED = np.array([0.2263, 0.8268, 0.2601, 0.4073, 0.4335])
T_BIAS = 0.6439

# Gate thresholds
G_S_THRESH = 0.4787
G_T_THRESH = 0.3892


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, float(x)))


def limbic(text: str, eap: list = None, qais_score: float = 0.3, context: str = "") -> dict:
    """
    Full limbic scan: ISS perception + EAP emotion + QAIS memory → S/T/G.

    Args:
        text: Raw text to analyze
        eap: 10 floats from Claude's native emotional read
             [valence, arousal, confidence, urgency, connection,
              curiosity, frustration, fatigue, wonder, trust]
             If None, defaults to neutral (all 0.0 except trust=0.5)
        qais_score: QAIS familiarity score (0=novel, 1=very familiar)
        context: Optional hint for interpretation
    """
    # 1. ISS analysis
    iss = analyze(text)
    g_norm = iss["g_norm"]
    p_norm = iss["p_norm"]
    E = iss["E"]
    r_norm = iss["r_norm"]
    gap = iss["gap"]

    # 2. EAP — default to neutral if not provided
    if eap is None or len(eap) != 10:
        eap = [0.0, 0.0, 0.5, 0.0, 0.3, 0.0, 0.0, 0.0, 0.0, 0.5]

    # Ensure floats
    eap = [float(v) for v in eap]

    # 3. Build 16D raw input
    raw = np.array([
        g_norm, p_norm, E, r_norm, gap,
        *eap,
        float(qais_score)
    ])

    # 4. Build 5D derived features
    derived = np.array([
        abs(eap[0]),                       # |valence|
        max(0.0, -eap[0]),                # max(0, -valence)
        abs(g_norm - p_norm),              # |g - p|
        1.0 - E,                           # (1 - E)
        1.0 - float(qais_score)           # (1 - qais_score)
    ])

    # 5. Compute S, T, G
    S = clamp(float(np.dot(S_RAW, raw)) + float(np.dot(S_DERIVED, derived)) + S_BIAS)
    T = clamp(float(np.dot(T_RAW, raw)) + float(np.dot(T_DERIVED, derived)) + T_BIAS)
    G = (S > G_S_THRESH) or (T > G_T_THRESH)
    V = eap[0]  # valence passthrough

    # 6. Build signal description
    signals = []

    # Salience signals
    if S > 0.8:
        signals.append("HIGH salience")
    elif S > 0.5:
        signals.append("moderate salience")

    # Threat signals
    if T > 0.7:
        signals.append("HIGH threat")
    elif T > 0.4:
        signals.append("moderate threat")

    # EAP-specific flags (Rav4 auto-trigger conditions)
    if eap[6] > 0.6:  # frustration
        signals.append("frustration elevated")
    if eap[7] > 0.7:  # fatigue
        signals.append("fatigue warning")
    if eap[9] < 0.3:  # trust dropping
        signals.append("trust low")
    if eap[8] > 0.7:  # wonder spiking
        signals.append("wonder spike")

    # Valence
    if V > 0.5:
        signals.append("positive")
    elif V < -0.3:
        signals.append("negative")

    # 7. Action recommendation
    if not G:
        action = "pass"
    elif T > 0.6:
        action = "intervene — threat detected"
    elif S > 0.7 and T < 0.2:
        action = "celebrate — significant positive moment"
    elif S > 0.5:
        action = "attend — something matters here"
    else:
        action = "note — gate triggered, review context"

    return {
        "S": round(S, 4),
        "V": round(V, 4),
        "T": round(T, 4),
        "G": G,
        "gap": round(gap, 4),
        "signal": "; ".join(signals) if signals else "quiet",
        "action": action,
        "iss": {
            "g_norm": round(g_norm, 4),
            "p_norm": round(p_norm, 4),
            "E": round(E, 4),
            "r_norm": round(r_norm, 4),
            "diagnosis": iss["diagnosis"]
        },
        "eap": {name: round(v, 2) for name, v in zip(EAP_NAMES, eap)},
        "qais_score": round(float(qais_score), 4),
        "genome": "v2.0-10D-S75"
    }


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
        "name": "iss_limbic",
        "description": "Limbic scan: ISS perception + EAP emotion (10D) + QAIS familiarity → S(salience), V(valence), T(threat), G(gate). Uses evolved genome (v2.0, fitness 0.017). Claude provides EAP from native read.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Raw text to analyze (user message or situation)"
                },
                "eap": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "10 floats: [valence, arousal, confidence, urgency, connection, curiosity, frustration, fatigue, wonder, trust]. Range: -1 to 1 for valence, 0 to 1 for others."
                },
                "qais_score": {
                    "type": "number",
                    "description": "QAIS familiarity (0=novel, 1=familiar). Default 0.3"
                },
                "context": {
                    "type": "string",
                    "description": "Optional hint (e.g. 'GSG mining', 'self-exploration')"
                }
            },
            "required": ["text"]
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
# MCP HANDLER
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
                "serverInfo": {"name": "iss-server", "version": "2.0.0"}
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
            elif tool_name == "iss_limbic":
                result = limbic(
                    text=args.get("text", ""),
                    eap=args.get("eap", None),
                    qais_score=args.get("qais_score", 0.3),
                    context=args.get("context", "")
                )
            elif tool_name == "iss_status":
                result = {
                    "status": "active",
                    "version": "2.0.0",
                    "embedding": "qais-hash",
                    "embed_dim": EMBED_DIM,
                    "proj_file": PROJ_FILE,
                    "proj_dim": 64,
                    "limbic": "active",
                    "limbic_genome": "v2.0-10D-S75",
                    "limbic_fitness": 0.017355,
                    "eap_schema": EAP_NAMES,
                    "eap_dims": 10,
                    "gate_thresholds": {
                        "S": G_S_THRESH,
                        "T": G_T_THRESH
                    }
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
