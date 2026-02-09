"""
ISS Core — Standalone analysis functions.
Used by: mcp_invoke.py (panel) and iss_mcp_server.py (MCP)
No MCP dependencies, no tool_auth — pure math.
"""

import numpy as np
import hashlib
import os

EMBED_DIM = 512
PROJ_FILE = "iss_projections.npz"

BOND_ROOT = os.environ.get('BOND_ROOT', os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BOND_ROOT, 'data')
proj_path = os.path.join(DATA_DIR, PROJ_FILE)

if os.path.exists(proj_path):
    _proj = np.load(proj_path)
    P_G = _proj['P_G']
    P_P = _proj['P_P']
else:
    np.random.seed(42)
    P_G = np.random.randn(EMBED_DIM, 64) * 0.1
    np.random.seed(43)
    P_P = np.random.randn(EMBED_DIM, 64) * 0.1


def embed_text(text: str) -> np.ndarray:
    h = hashlib.sha512(text.encode()).hexdigest()
    seed = int(h[:16], 16) % (2**32)
    rng = np.random.default_rng(seed)
    vec = rng.choice([-1.0, 1.0], size=EMBED_DIM)
    return vec / np.linalg.norm(vec)


def analyze(text: str, alpha=1.0, beta=1.0, gamma=1.0) -> dict:
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
        "G": round(g_norm, 4),
        "P": round(p_norm, 4),
        "E": round(E, 4),
        "r": round(r_norm, 4),
        "gap": round(gap, 4),
        "imbalance": round(imbalance, 4),
        "diagnosis": "; ".join(signals),
    }


def compare(texts: list) -> list:
    return [
        {"text": t[:50] + "..." if len(t) > 50 else t, **analyze(t)}
        for t in texts
    ]
