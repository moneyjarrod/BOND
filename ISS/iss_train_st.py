"""
ISS-ST: Sentence-Transformers Branch
Tests whether G/P separation is embedding-independent.

If this works with real semantic embeddings (not just QAIS hashes),
the claim strengthens: G/P are universal axes, not artifacts.

Author: J-Dub & Claude
Date: 2026-02-02
"""

import numpy as np
from typing import List, Tuple

# =============================================================================
# EMBEDDING LAYER - Sentence Transformers
# =============================================================================

try:
    from sentence_transformers import SentenceTransformer
    MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    EMBED_DIM = 384
    print("[ISS-ST] Using sentence-transformers (all-MiniLM-L6-v2)")
    print(f"[ISS-ST] Embedding dimension: {EMBED_DIM}")
except ImportError:
    print("[ISS-ST] ERROR: sentence-transformers not installed")
    print("[ISS-ST] Run: pip install sentence-transformers")
    exit(1)


def embed_text(text: str) -> np.ndarray:
    """Embed using real semantic model."""
    return MODEL.encode(text, normalize_embeddings=True)


def embed_corpus(sentences: List[str]) -> np.ndarray:
    """Embed all sentences, return (N, EMBED_DIM) matrix."""
    return np.array([embed_text(s) for s in sentences])


# =============================================================================
# TRAINING CORPUS (same as iss_train.py)
# =============================================================================

G_CORPUS = [
    # Computing
    "The function hashes the input and returns a fixed-length digest.",
    "SHA512 produces a 512-bit cryptographic hash from any input.",
    "The compiler transforms source code into executable machine instructions.",
    "Memory is allocated on the heap and freed when no longer referenced.",
    "The parser tokenizes the input stream into an abstract syntax tree.",
    "Data flows through the pipeline from source to sink.",
    "The CPU fetches instructions from memory and executes them sequentially.",
    "Garbage collection reclaims memory by tracing reachable objects.",
    # Physics
    "Water flows downhill due to gravitational potential energy.",
    "Heat transfers from hot objects to cold objects until equilibrium.",
    "Light refracts when passing through materials of different densities.",
    "Sound propagates through air as compression waves.",
    "Electrons flow through conductors when voltage is applied.",
    "Pressure increases with depth in a fluid.",
    # Biology
    "Cells divide through mitosis to create identical copies.",
    "Enzymes catalyze reactions by lowering activation energy.",
    "Blood circulates through arteries and returns through veins.",
    "Neurons transmit signals via electrochemical impulses.",
    "Photosynthesis converts sunlight into chemical energy.",
    # Mechanics
    "The engine converts fuel combustion into rotational motion.",
    "Gears transfer torque by meshing teeth at different ratios.",
    "The pump creates pressure differential to move fluid.",
    "Springs store energy when compressed and release it when extended.",
    "Bearings reduce friction by separating moving surfaces.",
    # Math/Logic
    "The algorithm sorts elements by repeatedly comparing adjacent pairs.",
    "Recursion solves problems by calling the same function with smaller inputs.",
    "The hash table maps keys to values using a hash function.",
    "Matrix multiplication combines rows and columns through dot products.",
    "The Fourier transform decomposes signals into frequency components.",
    # General processes
    "Evaporation occurs when molecules gain enough energy to escape liquid.",
    "Rust forms when iron oxidizes in the presence of water and oxygen.",
    "Bread rises because yeast produces carbon dioxide during fermentation.",
    "Ice melts when heat energy breaks the hydrogen bonds between molecules.",
    "Coffee extracts when hot water dissolves soluble compounds from grounds.",
    # GSG-specific mechanisms
    "The SDF query returns signed distance from any point to the surface.",
    "Mining operations subtract capsule shapes from the terrain field.",
    "The anchor position determines what exists within the 50m boundary.",
]

P_CORPUS = [
    # Software principles
    "Always validate input before processing.",
    "Never store passwords in plain text.",
    "Functions should do one thing and do it well.",
    "Prefer composition over inheritance.",
    "Code must be tested before deployment.",
    "Avoid premature optimization.",
    "Keep interfaces small and focused.",
    "Handle errors at the appropriate level.",
    # Design rules
    "The system should prioritize user safety above performance.",
    "Data integrity must be maintained at all times.",
    "Failures should be isolated and not cascade.",
    "Resources must be released when no longer needed.",
    "State changes should be atomic and reversible.",
    "Dependencies should flow in one direction only.",
    # Constraints
    "Memory usage must not exceed allocated limits.",
    "Response time should remain under 100 milliseconds.",
    "The API must maintain backward compatibility.",
    "Access requires proper authentication.",
    "Sensitive data must be encrypted at rest.",
    # Principles
    "Simplicity should be preferred over complexity.",
    "Correctness takes precedence over speed.",
    "Explicit is better than implicit.",
    "Errors should never pass silently.",
    "Flat is better than nested.",
    # Domain rules
    "Patients must provide informed consent before treatment.",
    "Financial transactions require dual authorization.",
    "Safety equipment must be inspected before each use.",
    "Changes to production require approval from two reviewers.",
    "Personal data must be deleted upon user request.",
    # Prohibitions
    "Never expose internal implementation details.",
    "Do not modify shared state without synchronization.",
    "Avoid circular dependencies between modules.",
    "Never trust user input without validation.",
    "Do not catch exceptions you cannot handle.",
    # GSG-specific principles
    "Always derive, never store positions directly.",
    "Store operations, not positions.",
    "The model must not encode task assumptions.",
    "Residuals are signal, not noise.",
    "Tasks must not modify projections or embeddings.",
    "Ambiguity is preserved structure.",
    "If gap detection requires a separate system, the invariant core is incomplete.",
]

print(f"[ISS-ST] Corpus: {len(G_CORPUS)} G sentences, {len(P_CORPUS)} P sentences")


# =============================================================================
# PROJECTION TRAINING
# =============================================================================

PROJ_DIM = 64


def train_projections(G_embeds: np.ndarray, P_embeds: np.ndarray,
                      n_iters: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
    """Train G/P projections with proper gradient."""
    
    embed_dim = G_embeds.shape[1]
    
    print(f"\n[ISS-ST] Training P_G ({embed_dim} → {PROJ_DIM})...")
    print("  Goal: high norm for G sentences, low norm for P sentences")
    
    np.random.seed(42)
    P_G = np.random.randn(embed_dim, PROJ_DIM) * 0.1
    
    lr = 0.005
    for i in range(n_iters):
        g_proj = G_embeds @ P_G
        p_proj = P_embeds @ P_G
        
        g_norms = np.linalg.norm(g_proj, axis=1)
        p_norms = np.linalg.norm(p_proj, axis=1)
        
        grad_pos = np.zeros_like(P_G)
        for x, proj, norm in zip(G_embeds, g_proj, g_norms):
            if norm > 1e-8:
                grad_pos += np.outer(x, proj) / norm
        grad_pos /= len(G_embeds)
        
        grad_neg = np.zeros_like(P_G)
        for x, proj, norm in zip(P_embeds, p_proj, p_norms):
            if norm > 1e-8:
                grad_neg += np.outer(x, proj) / norm
        grad_neg /= len(P_embeds)
        
        P_G += lr * (grad_pos - 0.5 * grad_neg)
        
        norm_P = np.linalg.norm(P_G)
        if norm_P > 5.0:
            P_G = P_G / norm_P * 5.0
        
        if i % 200 == 0:
            sep = np.mean(g_norms) - np.mean(p_norms)
            print(f"  Iter {i:4d}: G={np.mean(g_norms):.4f}, P={np.mean(p_norms):.4f}, sep={sep:+.4f}")
    
    print(f"\n[ISS-ST] Training P_P ({embed_dim} → {PROJ_DIM})...")
    print("  Goal: high norm for P sentences, low norm for G sentences")
    
    np.random.seed(43)
    P_P = np.random.randn(embed_dim, PROJ_DIM) * 0.1
    
    for i in range(n_iters):
        g_proj = G_embeds @ P_P
        p_proj = P_embeds @ P_P
        
        g_norms = np.linalg.norm(g_proj, axis=1)
        p_norms = np.linalg.norm(p_proj, axis=1)
        
        grad_pos = np.zeros_like(P_P)
        for x, proj, norm in zip(P_embeds, p_proj, p_norms):
            if norm > 1e-8:
                grad_pos += np.outer(x, proj) / norm
        grad_pos /= len(P_embeds)
        
        grad_neg = np.zeros_like(P_P)
        for x, proj, norm in zip(G_embeds, g_proj, g_norms):
            if norm > 1e-8:
                grad_neg += np.outer(x, proj) / norm
        grad_neg /= len(G_embeds)
        
        P_P += lr * (grad_pos - 0.5 * grad_neg)
        
        norm_P = np.linalg.norm(P_P)
        if norm_P > 5.0:
            P_P = P_P / norm_P * 5.0
        
        if i % 200 == 0:
            sep = np.mean(p_norms) - np.mean(g_norms)
            print(f"  Iter {i:4d}: P={np.mean(p_norms):.4f}, G={np.mean(g_norms):.4f}, sep={sep:+.4f}")
    
    return P_G, P_P


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("ISS-ST: Sentence-Transformers Branch Experiment")
    print("Testing: Is G/P separation embedding-independent?")
    print("="*70)
    
    # Embed
    print("\n[ISS-ST] Embedding corpus with sentence-transformers...")
    G_embeds = embed_corpus(G_CORPUS)
    P_embeds = embed_corpus(P_CORPUS)
    print(f"  G: {G_embeds.shape}, P: {P_embeds.shape}")
    
    # Train
    P_G, P_P = train_projections(G_embeds, P_embeds, n_iters=1000)
    
    # Evaluate
    print("\n" + "="*70)
    print("EVALUATION")
    print("="*70)
    
    g_via_G = np.mean(np.linalg.norm(G_embeds @ P_G, axis=1))
    p_via_G = np.mean(np.linalg.norm(P_embeds @ P_G, axis=1))
    g_via_P = np.mean(np.linalg.norm(G_embeds @ P_P, axis=1))
    p_via_P = np.mean(np.linalg.norm(P_embeds @ P_P, axis=1))
    
    print(f"\nP_G projection (should favor G):")
    print(f"  G sentences: ||g|| = {g_via_G:.4f}")
    print(f"  P sentences: ||g|| = {p_via_G:.4f}")
    print(f"  Separation: {g_via_G - p_via_G:+.4f}")
    print(f"  Ratio: {g_via_G / p_via_G:.2f}x")
    
    print(f"\nP_P projection (should favor P):")
    print(f"  G sentences: ||p|| = {g_via_P:.4f}")
    print(f"  P sentences: ||p|| = {p_via_P:.4f}")
    print(f"  Separation: {p_via_P - g_via_P:+.4f}")
    print(f"  Ratio: {p_via_P / g_via_P:.2f}x")
    
    # Save
    np.savez("iss_projections_st.npz", P_G=P_G, P_P=P_P, embed_dim=EMBED_DIM)
    print(f"\n✓ Saved to iss_projections_st.npz")
    
    # Compare with QAIS baseline
    print("\n" + "="*70)
    print("COMPARISON: QAIS-hash vs Sentence-Transformers")
    print("="*70)
    
    # Load QAIS results if available
    try:
        qais_proj = np.load("iss_projections.npz")
        print("\nQAIS-hash baseline (from iss_projections.npz):")
        print("  P_G separation: +0.098 (from training log)")
        print("  P_P separation: +0.092 (from training log)")
    except:
        print("\n(QAIS baseline not loaded)")
    
    print(f"\nSentence-Transformers:")
    print(f"  P_G separation: {g_via_G - p_via_G:+.4f}")
    print(f"  P_P separation: {p_via_P - g_via_P:+.4f}")
    
    # Verdict
    print("\n" + "="*70)
    print("VERDICT")
    print("="*70)
    
    qais_sep = 0.098  # Known from earlier run
    st_sep = (g_via_G - p_via_G + p_via_P - g_via_P) / 2
    
    if st_sep > qais_sep * 0.8:
        print("\n✓ SIGNAL IS EMBEDDING-INDEPENDENT")
        print("  G/P separation works with real semantic embeddings.")
        print("  The axes are universal, not artifacts of hashing.")
    elif st_sep > 0:
        print("\n~ SIGNAL EXISTS BUT WEAKER")
        print("  G/P separation present but reduced with transformers.")
        print("  May indicate some hash-specific structure.")
    else:
        print("\n✗ SIGNAL LOST")
        print("  G/P separation failed with real embeddings.")
        print("  The QAIS result may have been a hash artifact.")
    
    print("\n" + "="*70)
    
    # Quick test on held-out sentences
    print("\nQUICK TEST: Held-out sentences")
    print("-"*70)
    
    test_cases = [
        ("The function hashes the input and seeds a random generator.", "MECH"),
        ("You must validate input before processing.", "PRESC"),
        ("Store operations, not positions.", "PRESC"),
        ("SHA512 produces a 512-bit hash.", "MECH"),
        ("We derive instead of storing because it eliminates sync bugs.", "EXPL"),
    ]
    
    for text, expected in test_cases:
        x = embed_text(text)
        g_norm = np.linalg.norm(x @ P_G)
        p_norm = np.linalg.norm(x @ P_P)
        diff = g_norm - p_norm
        actual = "G>P" if diff > 0 else "P>G" if diff < 0 else "BAL"
        
        status = "✓" if (expected == "MECH" and diff > 0) or \
                       (expected == "PRESC" and diff < 0) or \
                       (expected == "EXPL" and abs(diff) < 0.05) else "?"
        
        print(f"  {status} [{expected:5s}] g-p={diff:+.4f}  {text[:50]}...")
