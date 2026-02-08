"""
ISS — Invariant Semantic Substrate
Prototype Implementation

Tests the G/P/E/r/Gap framework on sample text.
Uses sentence-transformers if available, else QAIS-style deterministic vectors.

Author: J-Dub & Claude
Date: 2026-02-01
"""

import numpy as np
from typing import NamedTuple, List, Tuple
import hashlib

# =============================================================================
# EMBEDDING LAYER
# =============================================================================

try:
    from sentence_transformers import SentenceTransformer
    EMBED_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    EMBED_DIM = 384
    USE_TRANSFORMER = True
    print("[ISS] Using sentence-transformers (all-MiniLM-L6-v2)")
except ImportError:
    EMBED_MODEL = None
    EMBED_DIM = 512
    USE_TRANSFORMER = False
    print("[ISS] Fallback: QAIS-style deterministic vectors")


def embed_text(text: str) -> np.ndarray:
    """Embed text to vector space."""
    if USE_TRANSFORMER:
        return EMBED_MODEL.encode(text, normalize_embeddings=True)
    else:
        # QAIS-style: SHA512 -> seed -> bipolar vector
        h = hashlib.sha512(text.encode()).hexdigest()
        seed = int(h[:16], 16) % (2**32)
        rng = np.random.default_rng(seed)
        vec = rng.choice([-1.0, 1.0], size=EMBED_DIM)
        return vec / np.linalg.norm(vec)


# =============================================================================
# TRAINED PROJECTION MATRICES (Phase 2 complete)
# DO NOT MODIFY - trained on 38 G + 41 P sentences
# =============================================================================

PROJ_DIM = 64  # Projection space dimension

import os
_proj_path = os.path.join(os.path.dirname(__file__), 'iss_projections.npz')
if os.path.exists(_proj_path):
    _proj = np.load(_proj_path)
    P_G = _proj['P_G']  # Mechanistic projection
    P_P = _proj['P_P']  # Prescriptive projection
    print("[ISS] Loaded trained projections from iss_projections.npz")
else:
    # Fallback to random if file missing
    print("[ISS] WARNING: iss_projections.npz not found, using random projections")
    np.random.seed(42)
    P_G = np.random.randn(EMBED_DIM, PROJ_DIM) * 0.1
    np.random.seed(43)
    P_P = np.random.randn(EMBED_DIM, PROJ_DIM) * 0.1


# =============================================================================
# PHASE 1 HEURISTICS: DELETED (Phase 2 training complete)
# =============================================================================


# =============================================================================
# ISS CORE
# =============================================================================

class SemanticState(NamedTuple):
    """Canonical semantic state (g, p, E, r)"""
    g: np.ndarray       # Mechanistic projection
    p: np.ndarray       # Prescriptive projection
    E: float            # Emergent explanatory elevation
    r: np.ndarray       # Residual
    g_norm: float       # ||g||
    p_norm: float       # ||p||
    r_norm: float       # ||r||
    gap: float          # Gap pressure


def invariant_semantic_pass(text: str, 
                            alpha: float = 1.0,
                            beta: float = 1.0,
                            gamma: float = 1.0) -> SemanticState:
    """
    Core ISS computation.
    
    Args:
        text: Input text
        alpha: Weight for residual in gap
        beta: Weight for G-P imbalance in gap
        gamma: Weight for (1-E) in gap
    
    Returns:
        SemanticState with all projections
    """
    # 1. Embed
    x = embed_text(text)
    
    # 2. Project to G and P (using trained projections)
    g = x @ P_G
    p = x @ P_P
    
    # 3. Compute E (cosine similarity)
    g_norm = np.linalg.norm(g)
    p_norm = np.linalg.norm(p)
    
    if g_norm > 1e-8 and p_norm > 1e-8:
        E = np.dot(g, p) / (g_norm * p_norm)
    else:
        E = 0.0
    
    # 4. Compute residual (what's left after projections)
    # Using pseudoinverse for reconstruction
    # g is (k,), pinv(P_G) is (k, d), so g @ pinv = (d,)
    g_reconstructed = g @ np.linalg.pinv(P_G)
    p_reconstructed = p @ np.linalg.pinv(P_P)
    r = x - 0.5 * (g_reconstructed + p_reconstructed)
    r_norm = np.linalg.norm(r)
    
    # 5. Gap pressure
    gap = (alpha * r_norm + 
           beta * abs(g_norm - p_norm) + 
           gamma * (1.0 - E))
    
    return SemanticState(
        g=g, p=p, E=E, r=r,
        g_norm=g_norm, p_norm=p_norm, r_norm=r_norm,
        gap=gap
    )


def apply_task_bias(state: SemanticState, 
                    lambda_G: float = 1.0,
                    lambda_P: float = 1.0,
                    lambda_E: float = 1.0,
                    lambda_R: float = 1.0) -> float:
    """
    Task-conditioned score.
    
    Λ_T = (λG, λP, λE, λR)
    S_T(x) = λG||g|| + λP||p|| + λE*E + λR||r||
    """
    return (lambda_G * state.g_norm +
            lambda_P * state.p_norm +
            lambda_E * state.E +
            lambda_R * state.r_norm)


# =============================================================================
# DIAGNOSTICS
# =============================================================================

def diagnose(state: SemanticState) -> str:
    """Interpret gap signals."""
    signals = []
    
    if state.r_norm > 0.8:
        signals.append("HIGH_RESIDUAL: Meaning not fully crystallized")
    
    imbalance = state.g_norm - state.p_norm
    if imbalance > 0.3:
        signals.append("G>>P: Mechanism without guiding principle")
    elif imbalance < -0.3:
        signals.append("P>>G: Doctrine without grounding")
    
    if state.E < 0.3:
        signals.append("LOW_E: Explanatory strain/incoherence")
    elif state.E > 0.7:
        signals.append("HIGH_E: Coherent explanation")
    
    if state.gap > 2.0:
        signals.append("HIGH_GAP: Significant semantic imbalance")
    
    return "; ".join(signals) if signals else "BALANCED"


def analyze_text(text: str, label: str = "") -> None:
    """Analyze text and print results."""
    state = invariant_semantic_pass(text)
    
    print(f"\n{'='*60}")
    if label:
        print(f"[{label}]")
    print(f"Text: {text[:80]}{'...' if len(text) > 80 else ''}")
    print(f"-"*60)
    print(f"  ||g|| = {state.g_norm:.4f}  (mechanistic)")
    print(f"  ||p|| = {state.p_norm:.4f}  (prescriptive)")
    print(f"  g-p   = {state.g_norm - state.p_norm:+.4f}  (imbalance)")
    print(f"  E     = {state.E:.4f}  (explanatory coherence)")
    print(f"  ||r|| = {state.r_norm:.4f}  (residual)")
    print(f"  Gap   = {state.gap:.4f}")
    print(f"  Diagnosis: {diagnose(state)}")


# =============================================================================
# TEST SUITE
# =============================================================================

def run_tests():
    """Test ISS on various sentence types."""
    
    print("\n" + "="*60)
    print("ISS — Invariant Semantic Substrate Prototype")
    print("="*60)
    
    # Mechanistic sentences (should have higher G)
    mechanistic = [
        "The function hashes the input and seeds a random generator.",
        "Water flows downhill due to gravitational potential.",
        "The compiler transforms source code into machine instructions.",
    ]
    
    # Prescriptive sentences (should have higher P)
    prescriptive = [
        "Always derive, never store positions directly.",
        "You must validate input before processing.",
        "The system should prioritize user safety above performance.",
    ]
    
    # Explanatory sentences (should have high E - balanced G and P)
    explanatory = [
        "We derive instead of storing because it eliminates sync bugs.",
        "The rule enforces validation to prevent injection attacks.",
        "FPRS exists within 50m because beyond that nothing is computed.",
    ]
    
    # Ambiguous/compressed (should have high residual)
    ambiguous = [
        "The math IS the merge.",
        "Chainmail is modelable water.",
        "Don't index. Resonate.",
    ]
    
    # Gap cases (should show imbalance)
    gap_cases = [
        ("Store operations, not positions.", "P>>G expected"),
        ("SHA512 produces a 512-bit hash.", "G>>P expected"),
        ("Things happen for reasons.", "High residual expected"),
    ]
    
    print("\n--- MECHANISTIC SENTENCES ---")
    for s in mechanistic:
        analyze_text(s, "MECH")
    
    print("\n--- PRESCRIPTIVE SENTENCES ---")
    for s in prescriptive:
        analyze_text(s, "PRESC")
    
    print("\n--- EXPLANATORY SENTENCES ---")
    for s in explanatory:
        analyze_text(s, "EXPL")
    
    print("\n--- AMBIGUOUS/COMPRESSED ---")
    for s in ambiguous:
        analyze_text(s, "AMBIG")
    
    print("\n--- GAP CASES ---")
    for s, expected in gap_cases:
        analyze_text(s, f"GAP ({expected})")
    
    # Task bias demonstration
    print("\n" + "="*60)
    print("TASK BIAS DEMONSTRATION")
    print("="*60)
    
    test_text = "We derive instead of storing because it eliminates sync bugs."
    state = invariant_semantic_pass(test_text)
    
    print(f"\nText: {test_text}")
    print(f"\nBase state: ||g||={state.g_norm:.3f}, ||p||={state.p_norm:.3f}, E={state.E:.3f}")
    
    # Different task biases
    biases = [
        ("Neutral", (1.0, 1.0, 1.0, 1.0)),
        ("Mechanism-heavy", (2.0, 0.5, 1.0, 0.5)),
        ("Principle-heavy", (0.5, 2.0, 1.0, 0.5)),
        ("Explanation-seeking", (1.0, 1.0, 3.0, 0.5)),
        ("Ambiguity-preserving", (0.5, 0.5, 0.5, 2.0)),
    ]
    
    for name, (lg, lp, le, lr) in biases:
        score = apply_task_bias(state, lg, lp, le, lr)
        print(f"  {name:25s} Λ=({lg},{lp},{le},{lr}) → Score={score:.4f}")


if __name__ == "__main__":
    run_tests()
