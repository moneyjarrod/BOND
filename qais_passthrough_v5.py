"""
QAIS Passthrough v5 - Enhanced Resonance
"Resonate against knowledge, with synonym awareness."

IMPROVEMENTS over v4:
1. Synonym expansion: "meter" ↔ "m", "50m" → "50 meter"
2. Bigram bundling: "50_meter", "boundary_existence" captured
3. Number normalization: "50 meter" and "50m" now match
4. Compound splitting: "heightfield" → "height", "field"

Session 64 | J-Dub & Claude | 2026-01-30
"""

import numpy as np
import hashlib
import re
import os
from typing import List, Dict, Set, Tuple, Optional

N = 4096

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
    'our', 'you', 'your', 'what', 'which', 'who', 'whom', 'about', 'let',
    'tell', 'know', 'think', 'make', 'take', 'see', 'come', 'look', 'use',
    'find', 'give', 'got', 'get', 'put', 'said', 'say', 'like', 'also',
    'well', 'back', 'much', 'way', 'even', 'new', 'want', 'first', 'any',
    'happens', 'does', 'mean', 'work', 'works', 'things', 'thing'
}

# =============================================================================
# SYNONYM MAPS (bidirectional expansion)
# =============================================================================

SYNONYMS = {
    # Units
    'meter': ['m', 'meters', 'metre', 'metres'],
    'm': ['meter', 'meters'],
    'meters': ['m', 'meter'],
    
    # Common abbreviations
    'config': ['configuration', 'configure'],
    'configuration': ['config'],
    'params': ['parameters', 'param'],
    'parameters': ['params', 'param'],
    
    # Domain specific (GSG)
    'fprs': ['boundary', 'existence', '50m'],
    'asdf': ['heightfield', 'sdf', 'terrain', 'csg'],
    'derive': ['compute', 'calculate', 'derived'],
    'store': ['save', 'persist', 'stored'],
}

# Number+unit patterns: "50m" → "50 meter", "100ms" → "100 millisecond"
UNIT_EXPANSIONS = {
    'm': 'meter',
    'ms': 'millisecond', 
    's': 'second',
    'km': 'kilometer',
    'cm': 'centimeter',
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
    """Normalized dot product."""
    return float(np.dot(a, b) / N)


# =============================================================================
# ENHANCED TEXT PROCESSING
# =============================================================================

def normalize_number_units(text: str) -> str:
    """Expand number+unit patterns: '50m' → '50 meter', '100ms' → '100 millisecond'"""
    result = text
    for abbrev, full in UNIT_EXPANSIONS.items():
        # Match number followed by unit abbreviation
        pattern = r'(\d+)' + abbrev + r'\b'
        replacement = r'\1 ' + full
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def split_compounds(word: str) -> List[str]:
    """Split compound words: 'heightfield' → ['height', 'field']"""
    # CamelCase split
    parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', word)
    if len(parts) > 1:
        return [p.lower() for p in parts]
    
    # Common compound patterns (could be expanded)
    compounds = {
        'heightfield': ['height', 'field'],
        'gameplay': ['game', 'play'],
        'runtime': ['run', 'time'],
        'timestamp': ['time', 'stamp'],
    }
    return compounds.get(word.lower(), [])


def expand_synonyms(keywords: List[str]) -> List[str]:
    """Expand keywords with synonyms."""
    expanded = set(keywords)
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in SYNONYMS:
            expanded.update(SYNONYMS[kw_lower])
    return list(expanded)


def text_to_keywords_v5(text: str, expand: bool = True) -> List[str]:
    """
    Enhanced keyword extraction with:
    - Number+unit normalization
    - Compound word splitting
    - Synonym expansion
    """
    # Step 1: Normalize number+units
    text = normalize_number_units(text)
    
    # Step 2: Extract base keywords
    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text.lower())
    keywords = [w for w in words if len(w) > 2 and w not in STOPWORDS]
    
    # Step 3: Split compounds and add parts
    extra = []
    for kw in keywords:
        parts = split_compounds(kw)
        if parts:
            extra.extend(parts)
    keywords.extend(extra)
    
    # Step 4: Expand synonyms
    if expand:
        keywords = expand_synonyms(keywords)
    
    # Step 5: Extract bigrams from original (before expansion)
    base_words = [w for w in words if len(w) > 2 and w not in STOPWORDS]
    for i in range(len(base_words) - 1):
        bigram = f"{base_words[i]}_{base_words[i+1]}"
        keywords.append(bigram)
    
    return list(set(keywords))


def text_to_vector_v5(text: str) -> np.ndarray:
    """Convert text to HD vector with enhanced keyword extraction."""
    keywords = text_to_keywords_v5(text)
    if not keywords:
        return seed_to_vector(text)
    
    bundle = np.zeros(N, dtype=np.float32)
    for kw in keywords:
        bundle += seed_to_vector(kw)
    
    result = np.sign(bundle)
    result[result == 0] = 1
    return result.astype(np.float32)


# =============================================================================
# PASSTHROUGH v5
# =============================================================================

class PassthroughV5:
    """
    Enhanced passthrough with synonym awareness and bigram support.
    """
    
    def __init__(self, field_path: str = None):
        if field_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            field_path = os.path.join(script_dir, "qais_field.npz")
        
        self.field_path = field_path
        self.fact_to_identities: Dict[str, Set[str]] = {}
        self.fact_vectors: Dict[str, np.ndarray] = {}
        self.identity_to_facts: Dict[str, Set[str]] = {}
        self.loaded = False
        
        self._load_field()
    
    def _load_field(self):
        """Load and vectorize facts with v5 processing."""
        if not os.path.exists(self.field_path):
            return
        
        try:
            data = np.load(self.field_path, allow_pickle=True)
            stored = set(data['stored'].tolist())
            
            for key in stored:
                parts = key.split('|', 2)
                if len(parts) == 3:
                    identity, role, fact = parts
                    
                    if fact not in self.fact_to_identities:
                        self.fact_to_identities[fact] = set()
                        # Use v5 vectorization for facts too
                        self.fact_vectors[fact] = text_to_vector_v5(fact)
                    self.fact_to_identities[fact].add(identity)
                    
                    if identity not in self.identity_to_facts:
                        self.identity_to_facts[identity] = set()
                    self.identity_to_facts[identity].add(fact)
            
            self.loaded = True
        except Exception as e:
            pass
    
    def passthrough(self, text: str, candidates: List[str],
                    threshold: float = 0.08,  # Lowered due to better matching
                    top_k: int = 3) -> Dict:
        """
        Enhanced passthrough with synonym-aware resonance.
        """
        text_vec = text_to_vector_v5(text)
        keywords = text_to_keywords_v5(text)
        keywords_lower = set(k.lower() for k in keywords)
        candidate_set = set(candidates)
        
        # Phase 1: Direct keyword match (including synonyms)
        direct_matches = set()
        for candidate in candidates:
            cand_lower = candidate.lower()
            if cand_lower in keywords_lower:
                direct_matches.add(candidate)
            # Check if any synonym matches
            if cand_lower in SYNONYMS:
                for syn in SYNONYMS[cand_lower]:
                    if syn in keywords_lower:
                        direct_matches.add(candidate)
                        break
        
        # Phase 2: Resonate against stored facts
        fact_scores = []
        if self.loaded:
            for fact, fact_vec in self.fact_vectors.items():
                score = resonance(text_vec, fact_vec)
                if score > threshold:
                    fact_scores.append((fact, score, self.fact_to_identities[fact]))
            fact_scores.sort(key=lambda x: -x[1])
        
        # Phase 3: Map to candidates
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
                elif best_score > 0.35:
                    confidence = "HIGH"
                elif best_score > 0.15:
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
        
        conf_order = {"EXACT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        matches.sort(key=lambda x: (conf_order.get(x["confidence"], 4), -x["score"]))
        
        should_load = [m["context"] for m in matches if m["confidence"] in ["EXACT", "HIGH"]]
        
        return {
            "keywords": keywords,
            "matches": matches,
            "should_load": should_load,
            "confidence": matches[0]["confidence"] if matches else "NONE",
            "facts_checked": len(self.fact_vectors)
        }


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("PASSTHROUGH v5 - Enhanced Resonance Test")
    print("=" * 70)
    
    # Test keyword extraction improvements
    print("\n[Keyword Extraction Tests]")
    
    tests = [
        "What happens at the 50m boundary?",
        "50 meter boundary of existence",
        "heightfield terrain carving",
        "derive not store principle",
    ]
    
    for t in tests:
        kw = text_to_keywords_v5(t)
        print(f"\n'{t}'")
        print(f"  → {kw}")
    
    # Test resonance improvements
    print("\n" + "=" * 70)
    print("[Resonance Comparison: v4 vs v5]")
    
    pairs = [
        ("50 meter boundary", "50m boundary of existence"),
        ("heightfield terrain", "height field sdf"),
        ("derive compute anchor", "Everything computed from anchor"),
    ]
    
    for t1, t2 in pairs:
        # v4 style (basic)
        kw1_old = [w for w in re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', t1.lower()) 
                   if len(w) > 2 and w not in STOPWORDS]
        kw2_old = [w for w in re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', t2.lower()) 
                   if len(w) > 2 and w not in STOPWORDS]
        shared_old = set(kw1_old) & set(kw2_old)
        
        # v5 style (enhanced)
        kw1_new = text_to_keywords_v5(t1)
        kw2_new = text_to_keywords_v5(t2)
        shared_new = set(kw1_new) & set(kw2_new)
        
        vec1 = text_to_vector_v5(t1)
        vec2 = text_to_vector_v5(t2)
        score = resonance(vec1, vec2)
        
        print(f"\n'{t1}' ↔ '{t2}'")
        print(f"  v4 shared: {shared_old}")
        print(f"  v5 shared: {shared_new}")
        print(f"  v5 resonance: {score:.4f}")
    
    print("\n" + "=" * 70)
