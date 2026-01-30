"""
QAIS Passthrough v4
"Resonate against knowledge, not names."

Token-saving relevance filter using hyperdimensional computing.
Determines WHAT context to load BEFORE committing tokens to retrieval.

v4 CHANGES:
  - Now resonates against STORED FACTS, not just context names
  - "50 meter boundary" -> finds FPRS via stored fact "50m boundary of existence"
  - Requires qais_field.npz to be present for fact resonance
  - Falls back to keyword matching if no field found

Part of BOND Protocol | github.com/moneyjarrod/BOND
Session 64 | J-Dub & Claude | 2026-01-30

Usage:
    from qais_passthrough import passthrough, PassthroughV4
    
    # Quick usage (auto-loads field)
    result = passthrough(
        "What happens at the 50 meter boundary?",
        ["FPRS", "ASDF", "mining"]
    )
    print(result["should_load"])  # ["FPRS"] - found via fact resonance!
    
    # Or with explicit field path
    proc = PassthroughV4("path/to/qais_field.npz")
    result = proc.passthrough(text, candidates)
"""

import numpy as np
import hashlib
import re
import os
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass

N = 4096  # Hyperdimensional vector size

# =============================================================================
# STOPWORDS
# =============================================================================

STOPWORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'to', 'of',
    'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
    'during', 'before', 'after', 'above', 'below', 'between', 'under',
    'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where',
    'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some',
    'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
    'very', 'just', 'and', 'but', 'if', 'or', 'because', 'until', 'while',
    'this', 'that', 'these', 'those', 'it', 'its', 'i', 'me', 'my', 'we',
    'our', 'you', 'your', 'he', 'him', 'his', 'she', 'her', 'they', 'them',
    'their', 'what', 'which', 'who', 'whom', 'about', 'let', 'tell', 'know',
    'think', 'make', 'take', 'see', 'come', 'look', 'use', 'find', 'give',
    'got', 'get', 'put', 'said', 'say', 'like', 'also', 'well', 'back',
    'being', 'been', 'much', 'way', 'even', 'new', 'want', 'first', 'any'
}

# =============================================================================
# CORE VECTOR OPERATIONS
# =============================================================================

def seed_to_vector(seed: str) -> np.ndarray:
    """Deterministic bipolar vector from any string."""
    h = hashlib.sha512(seed.encode()).digest()
    rng = np.random.RandomState(list(h[:4]))
    return rng.choice([-1, 1], size=N).astype(np.float32)


def resonance(a: np.ndarray, b: np.ndarray) -> float:
    """Normalized dot product - coherence measure."""
    return float(np.dot(a, b) / N)


def text_to_keywords(text: str) -> List[str]:
    """Extract meaningful keywords from text."""
    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text.lower())
    return list(set(w for w in words if len(w) > 2 and w not in STOPWORDS))


def text_to_vector(text: str) -> np.ndarray:
    """Convert text to HD vector by bundling keywords."""
    keywords = text_to_keywords(text)
    if not keywords:
        return seed_to_vector(text)
    
    bundle = np.zeros(N, dtype=np.float32)
    for kw in keywords:
        bundle += seed_to_vector(kw)
    
    result = np.sign(bundle)
    result[result == 0] = 1
    return result.astype(np.float32)


# =============================================================================
# PASSTHROUGH v4 - FACT RESONANCE
# =============================================================================

class PassthroughV4:
    """
    Token-saving filter that resonates against STORED FACTS.
    
    The insight: User text should match against knowledge, not just names.
    "50 meter boundary" finds FPRS via stored fact "50m boundary of existence".
    
    Usage:
        proc = PassthroughV4("path/to/qais_field.npz")
        result = proc.passthrough(user_input, ["FPRS", "ASDF", "mining"])
        # result["should_load"] contains relevant contexts
    """
    
    def __init__(self, field_path: str = None):
        """
        Initialize with QAIS field path.
        
        Args:
            field_path: Path to qais_field.npz. If None, searches:
                        1. Same directory as this script
                        2. Current working directory
        """
        if field_path is None:
            # Try script directory first
            script_dir = os.path.dirname(os.path.abspath(__file__))
            field_path = os.path.join(script_dir, "qais_field.npz")
            if not os.path.exists(field_path):
                # Try current directory
                field_path = "qais_field.npz"
        
        self.field_path = field_path
        self.fact_to_identities: Dict[str, Set[str]] = {}
        self.fact_vectors: Dict[str, np.ndarray] = {}
        self.identity_to_facts: Dict[str, Set[str]] = {}
        self.loaded = False
        
        self._load_field()
    
    def _load_field(self):
        """Load fact registry from QAIS field."""
        if not os.path.exists(self.field_path):
            return
        
        try:
            data = np.load(self.field_path, allow_pickle=True)
            stored = set(data['stored'].tolist())
            
            for key in stored:
                parts = key.split('|', 2)
                if len(parts) == 3:
                    identity, role, fact = parts
                    
                    # fact -> identities
                    if fact not in self.fact_to_identities:
                        self.fact_to_identities[fact] = set()
                        self.fact_vectors[fact] = text_to_vector(fact)
                    self.fact_to_identities[fact].add(identity)
                    
                    # identity -> facts
                    if identity not in self.identity_to_facts:
                        self.identity_to_facts[identity] = set()
                    self.identity_to_facts[identity].add(fact)
            
            self.loaded = True
        except Exception as e:
            pass
    
    def passthrough(self, text: str, candidates: List[str],
                    threshold: float = 0.12,
                    top_k: int = 3) -> Dict:
        """
        Main passthrough function with fact resonance.
        
        Args:
            text: User input to analyze
            candidates: Contexts to check (e.g., ["FPRS", "ASDF", "mining"])
            threshold: Minimum fact resonance score (default 0.12)
            top_k: Max evidence facts per match (default 3)
        
        Returns:
            Dict with:
            - keywords: extracted keywords
            - matches: contexts with confidence and evidence
            - should_load: HIGH/EXACT confidence contexts
            - confidence: overall confidence level
            - facts_checked: number of facts in registry
        """
        text_vec = text_to_vector(text)
        keywords = text_to_keywords(text)
        keywords_lower = set(keywords)
        candidate_set = set(candidates)
        
        # Phase 1: Direct keyword match (fastest)
        direct_matches = set()
        for candidate in candidates:
            if candidate.lower() in keywords_lower:
                direct_matches.add(candidate)
        
        # Phase 2: Resonate against stored facts (if field loaded)
        fact_scores = []
        if self.loaded:
            for fact, fact_vec in self.fact_vectors.items():
                score = resonance(text_vec, fact_vec)
                if score > threshold:
                    fact_scores.append((fact, score, self.fact_to_identities[fact]))
            fact_scores.sort(key=lambda x: -x[1])
        
        # Phase 3: Map resonating facts to candidate identities
        identity_evidence: Dict[str, List[Tuple[str, float]]] = {}
        
        for fact, score, identities in fact_scores:
            for identity in identities:
                if identity in candidate_set:
                    if identity not in identity_evidence:
                        identity_evidence[identity] = []
                    if len(identity_evidence[identity]) < top_k:
                        identity_evidence[identity].append((fact, score))
        
        # Phase 4: Build results
        matches = []
        for candidate in candidates:
            direct = candidate in direct_matches
            evidence = identity_evidence.get(candidate, [])
            
            if direct or evidence:
                best_score = evidence[0][1] if evidence else 0.0
                
                if direct:
                    confidence = "EXACT"
                elif best_score > 0.4:
                    confidence = "HIGH"
                elif best_score > 0.2:
                    confidence = "MEDIUM"
                else:
                    confidence = "LOW"
                
                matches.append({
                    "context": candidate,
                    "score": round(best_score, 4),
                    "confidence": confidence,
                    "direct": direct,
                    "evidence": [(f, round(s, 4)) for f, s in evidence[:top_k]]
                })
        
        # Sort: EXACT first, then by score
        conf_order = {"EXACT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        matches.sort(key=lambda x: (conf_order.get(x["confidence"], 4), -x["score"]))
        
        should_load = [m["context"] for m in matches if m["confidence"] in ["EXACT", "HIGH"]]
        
        return {
            "keywords": keywords,
            "domain_keywords": [],  # Backward compat
            "matches": matches,
            "should_load": should_load,
            "confidence": matches[0]["confidence"] if matches else "NONE",
            "facts_checked": len(self.fact_vectors)
        }


# =============================================================================
# CONVENIENCE API
# =============================================================================

_PROCESSOR: Optional[PassthroughV4] = None

def get_processor() -> PassthroughV4:
    """Get or create the global processor."""
    global _PROCESSOR
    if _PROCESSOR is None:
        _PROCESSOR = PassthroughV4()
    return _PROCESSOR


def passthrough(text: str, candidates: List[str],
                threshold: float = 0.12) -> Dict:
    """
    Quick passthrough query with fact resonance.
    
    Args:
        text: Input text to analyze
        candidates: Contexts to check for relevance
        threshold: Minimum resonance score
    
    Returns:
        Dict with matches and load recommendations
    """
    return get_processor().passthrough(text, candidates, threshold=threshold)


def quick_check(text: str, context: str) -> Tuple[bool, str]:
    """Quick check if a context should be loaded."""
    result = get_processor().passthrough(text, [context])
    if result["matches"]:
        m = result["matches"][0]
        return (m["confidence"] in ["EXACT", "HIGH"], m["confidence"])
    return (False, "NONE")


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("QAIS Passthrough v4 - Fact Resonance")
    print("=" * 70)
    
    proc = get_processor()
    print(f"Field loaded: {proc.loaded}")
    print(f"Facts indexed: {len(proc.fact_vectors)}")
    print(f"Identities indexed: {len(proc.identity_to_facts)}")
    
    if proc.loaded:
        # Test the original failing case
        print("\n[Test: '50 meter boundary' -> should find FPRS]")
        result = passthrough(
            "What happens beyond the 50 meter boundary?",
            ["FPRS", "ASDF", "mining", "QAIS"]
        )
        print(f"Keywords: {result['keywords']}")
        print(f"Should load: {result['should_load']}")
        for m in result['matches']:
            print(f"  {m['context']}: {m['confidence']} ({m['score']})")
            if m['evidence']:
                print(f"    Evidence: {m['evidence'][:2]}")
    else:
        print("\nNo QAIS field found - run with qais_field.npz present")
    
    print("\n" + "=" * 70)
