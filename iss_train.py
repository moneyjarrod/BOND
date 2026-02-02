"""
ISS Phase 2: Training Corpus + Projection Learning
Trains P_G and P_P to separate mechanistic from prescriptive sentences.

Author: J-Dub & Claude
Date: 2026-02-01
"""

import numpy as np
import hashlib
from typing import List, Tuple

# =============================================================================
# TRAINING CORPUS
# Mixed domains, no task assumptions, no abstract/literal labels
# Only: "Does it explain HOW something works?" vs "Does it prescribe WHAT one should do?"
# =============================================================================

# MECHANISTIC: Describes how something works, processes, operations
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
    "Flags merge when their depth values exceed the merge threshold.",
]

# PRESCRIPTIVE: States what one should/must do, rules, principles, constraints
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

print(f"Training corpus: {len(G_CORPUS)} G sentences, {len(P_CORPUS)} P sentences")

# =============================================================================
# EMBEDDING (same as prototype)
# =============================================================================

EMBED_DIM = 512

def embed_text(text: str) -> np.ndarray:
    """QAIS-style deterministic embedding."""
    h = hashlib.sha512(text.encode()).hexdigest()
    seed = int(h[:16], 16) % (2**32)
    rng = np.random.default_rng(seed)
    vec = rng.choice([-1.0, 1.0], size=EMBED_DIM)
    return vec / np.linalg.norm(vec)


def embed_corpus(sentences: List[str]) -> np.ndarray:
    """Embed all sentences, return (N, EMBED_DIM) matrix."""
    return np.array([embed_text(s) for s in sentences])


# =============================================================================
# PROJECTION TRAINING
# Goal: P_G maximizes G-sentence norms, minimizes P-sentence norms (and vice versa)
# =============================================================================

PROJ_DIM = 64

def train_projection(positive: np.ndarray, negative: np.ndarray, 
                     n_iters: int = 1000, lr: float = 0.01) -> np.ndarray:
    """
    Train a projection matrix that:
    - Maximizes norm of projected positive samples
    - Minimizes norm of projected negative samples
    
    Uses simple gradient descent on contrastive objective.
    """
    np.random.seed(42)
    P = np.random.randn(EMBED_DIM, PROJ_DIM) * 0.1
    
    n_pos = positive.shape[0]
    n_neg = negative.shape[0]
    
    for i in range(n_iters):
        # Forward pass
        pos_proj = positive @ P  # (n_pos, PROJ_DIM)
        neg_proj = negative @ P  # (n_neg, PROJ_DIM)
        
        pos_norms = np.linalg.norm(pos_proj, axis=1)  # (n_pos,)
        neg_norms = np.linalg.norm(neg_proj, axis=1)  # (n_neg,)
        
        # Loss: minimize negative of (mean_pos_norm - mean_neg_norm)
        # We want pos_norms high, neg_norms low
        margin = 0.5
        loss = -np.mean(pos_norms) + np.mean(neg_norms) + margin * np.mean(neg_norms**2)
        
        # Gradient (simplified, using finite differences for stability)
        grad = np.zeros_like(P)
        eps = 1e-5
        
        for j in range(PROJ_DIM):
            for k in range(0, EMBED_DIM, 8):  # Sparse gradient for speed
                P[k, j] += eps
                pos_proj_p = positive @ P
                neg_proj_p = negative @ P
                loss_p = -np.mean(np.linalg.norm(pos_proj_p, axis=1)) + \
                         np.mean(np.linalg.norm(neg_proj_p, axis=1))
                P[k, j] -= eps
                grad[k, j] = (loss_p - loss) / eps
        
        # Update
        P -= lr * grad
        
        # Normalize columns periodically to prevent explosion
        if i % 100 == 0:
            col_norms = np.linalg.norm(P, axis=0, keepdims=True)
            P = P / (col_norms + 1e-8) * 0.1
            
            if i % 200 == 0:
                print(f"  Iter {i:4d}: loss={loss:.4f}, "
                      f"pos_norm={np.mean(pos_norms):.4f}, "
                      f"neg_norm={np.mean(neg_norms):.4f}")
    
    return P


def train_projections_fast(G_embeds: np.ndarray, P_embeds: np.ndarray,
                           n_iters: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
    """
    Train projections to separate G from P sentences.
    Uses contrastive gradient without aggressive normalization.
    """
    print("\nTraining P_G (mechanistic projection)...")
    print("  Goal: high norm for G sentences, low norm for P sentences")
    
    np.random.seed(42)
    P_G = np.random.randn(EMBED_DIM, PROJ_DIM) * 0.1
    
    lr = 0.005
    for i in range(n_iters):
        g_proj = G_embeds @ P_G
        p_proj = P_embeds @ P_G
        
        g_norms = np.linalg.norm(g_proj, axis=1)
        p_norms = np.linalg.norm(p_proj, axis=1)
        
        # Gradient: maximize G norms, minimize P norms
        # For ||Ax||, gradient w.r.t. A is x * (Ax)^T / ||Ax||
        grad_pos = np.zeros_like(P_G)
        for j, (x, proj, norm) in enumerate(zip(G_embeds, g_proj, g_norms)):
            if norm > 1e-8:
                grad_pos += np.outer(x, proj) / norm
        grad_pos /= len(G_embeds)
        
        grad_neg = np.zeros_like(P_G)
        for j, (x, proj, norm) in enumerate(zip(P_embeds, p_proj, p_norms)):
            if norm > 1e-8:
                grad_neg += np.outer(x, proj) / norm
        grad_neg /= len(P_embeds)
        
        P_G += lr * (grad_pos - 0.5 * grad_neg)
        
        # Light regularization only - prevent explosion, not crush
        norm_P = np.linalg.norm(P_G)
        if norm_P > 5.0:
            P_G = P_G / norm_P * 5.0
        
        if i % 200 == 0:
            sep = np.mean(g_norms) - np.mean(p_norms)
            print(f"  Iter {i:4d}: G_norm={np.mean(g_norms):.4f}, "
                  f"P_norm={np.mean(p_norms):.4f}, sep={sep:+.4f}")
    
    print("\nTraining P_P (prescriptive projection)...")
    print("  Goal: high norm for P sentences, low norm for G sentences")
    
    np.random.seed(43)
    P_P = np.random.randn(EMBED_DIM, PROJ_DIM) * 0.1
    
    for i in range(n_iters):
        g_proj = G_embeds @ P_P
        p_proj = P_embeds @ P_P
        
        g_norms = np.linalg.norm(g_proj, axis=1)
        p_norms = np.linalg.norm(p_proj, axis=1)
        
        grad_pos = np.zeros_like(P_P)
        for j, (x, proj, norm) in enumerate(zip(P_embeds, p_proj, p_norms)):
            if norm > 1e-8:
                grad_pos += np.outer(x, proj) / norm
        grad_pos /= len(P_embeds)
        
        grad_neg = np.zeros_like(P_P)
        for j, (x, proj, norm) in enumerate(zip(G_embeds, g_proj, g_norms)):
            if norm > 1e-8:
                grad_neg += np.outer(x, proj) / norm
        grad_neg /= len(G_embeds)
        
        P_P += lr * (grad_pos - 0.5 * grad_neg)
        
        norm_P = np.linalg.norm(P_P)
        if norm_P > 5.0:
            P_P = P_P / norm_P * 5.0
        
        if i % 200 == 0:
            sep = np.mean(p_norms) - np.mean(g_norms)
            print(f"  Iter {i:4d}: P_norm={np.mean(p_norms):.4f}, "
                  f"G_norm={np.mean(g_norms):.4f}, sep={sep:+.4f}")
    
    return P_G, P_P


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("="*60)
    print("ISS Phase 2: Training Semantic Projections")
    print("="*60)
    
    # Embed corpus
    print("\nEmbedding corpus...")
    G_embeds = embed_corpus(G_CORPUS)
    P_embeds = embed_corpus(P_CORPUS)
    print(f"  G: {G_embeds.shape}, P: {P_embeds.shape}")
    
    # Train projections
    P_G, P_P = train_projections_fast(G_embeds, P_embeds, n_iters=500)
    
    # Evaluate separation
    print("\n" + "="*60)
    print("EVALUATION")
    print("="*60)
    
    g_via_G = np.mean(np.linalg.norm(G_embeds @ P_G, axis=1))
    p_via_G = np.mean(np.linalg.norm(P_embeds @ P_G, axis=1))
    g_via_P = np.mean(np.linalg.norm(G_embeds @ P_P, axis=1))
    p_via_P = np.mean(np.linalg.norm(P_embeds @ P_P, axis=1))
    
    print(f"\nP_G projection (should favor G sentences):")
    print(f"  G sentences: ||g|| = {g_via_G:.4f}")
    print(f"  P sentences: ||g|| = {p_via_G:.4f}")
    print(f"  Separation: {g_via_G - p_via_G:+.4f}")
    
    print(f"\nP_P projection (should favor P sentences):")
    print(f"  G sentences: ||p|| = {g_via_P:.4f}")
    print(f"  P sentences: ||p|| = {p_via_P:.4f}")
    print(f"  Separation: {p_via_P - g_via_P:+.4f}")
    
    # Save trained projections
    np.savez("iss_projections.npz", P_G=P_G, P_P=P_P)
    print("\n✓ Saved trained projections to iss_projections.npz")
    
    # Print for embedding in prototype
    print("\n" + "="*60)
    print("COPY TO iss_prototype.py (replace random init):")
    print("="*60)
    print(f"# Trained projections - DO NOT MODIFY")
    print(f"# G corpus: {len(G_CORPUS)} sentences, P corpus: {len(P_CORPUS)} sentences")
    print(f"P_G = np.load('iss_projections.npz')['P_G']")
    print(f"P_P = np.load('iss_projections.npz')['P_P']")
