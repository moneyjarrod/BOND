"""
QAIS Passthrough Processor v3
"Resonate first, load later."

Token-saving relevance filter using hyperdimensional computing.
Determines WHAT context to load BEFORE committing tokens to retrieval.

Modular domain system:
- CODE_KEYWORDS: Programming concepts (always active)
- DOC_KEYWORDS: Documentation/prose  
- USER domains: Project-specific terms (register your own)

Part of BOND Protocol | github.com/moneyjarrod/BOND
Created: Session 63 | J-Dub & Claude | 2026-01-30

Usage:
    from qais_passthrough import passthrough, register_project
    
    # Register your project's keywords
    register_project("myproject", ["widget", "gadget", "flux"])
    
    # Query incoming text
    result = passthrough(user_message, ["widget", "gadget", "other"])
    
    # Only load what matches
    if result["should_load"]:
        for context in result["should_load"]:
            load_context(context)  # Your retrieval function
"""

import numpy as np
import hashlib
import re
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass

N = 4096  # Hyperdimensional vector size

# =============================================================================
# STOPWORDS (filtered out of keyword extraction)
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
# BUILT-IN DOMAIN KEYWORD SETS
# =============================================================================

# Always active for code detection
CODE_KEYWORDS = {
    # Structure
    'function', 'class', 'method', 'module', 'package', 'library',
    'variable', 'constant', 'parameter', 'argument', 'return', 'import',
    'export', 'interface', 'type', 'enum', 'struct', 'trait', 'impl',
    # Flow control
    'loop', 'condition', 'branch', 'recursion', 'iteration', 'switch',
    'async', 'await', 'callback', 'promise', 'thread', 'concurrent',
    'yield', 'generator', 'iterator', 'break', 'continue',
    # Operations
    'parse', 'serialize', 'validate', 'transform', 'convert', 'compile',
    'fetch', 'request', 'response', 'query', 'filter', 'map', 'reduce',
    'sort', 'search', 'match', 'replace', 'split', 'join', 'merge',
    # State & debugging
    'error', 'exception', 'debug', 'test', 'fix', 'bug', 'issue',
    'config', 'settings', 'environment', 'initialize', 'setup', 'init',
    'log', 'trace', 'warn', 'assert', 'expect', 'mock', 'stub',
    # Data structures
    'array', 'list', 'dict', 'dictionary', 'map', 'set', 'queue', 'stack',
    'tree', 'graph', 'node', 'edge', 'hash', 'table', 'buffer', 'cache',
    'string', 'integer', 'float', 'boolean', 'null', 'none', 'undefined',
    # Patterns
    'api', 'endpoint', 'route', 'handler', 'middleware', 'controller',
    'model', 'view', 'service', 'repository', 'factory', 'singleton',
    'observer', 'listener', 'event', 'dispatch', 'emit', 'subscribe',
    # Memory & performance
    'memory', 'allocate', 'free', 'garbage', 'reference', 'pointer',
    'optimize', 'performance', 'benchmark', 'profile', 'complexity',
    # Version control
    'commit', 'branch', 'merge', 'rebase', 'pull', 'push', 'clone',
    'diff', 'patch', 'conflict', 'resolve', 'stash', 'checkout'
}

# For documentation/prose content
DOC_KEYWORDS = {
    'section', 'chapter', 'heading', 'paragraph', 'summary', 'overview',
    'introduction', 'conclusion', 'appendix', 'reference', 'index',
    'version', 'changelog', 'release', 'update', 'deprecated', 'legacy',
    'breaking', 'migration', 'upgrade', 'compatibility',
    'install', 'setup', 'configure', 'usage', 'example', 'tutorial',
    'guide', 'quickstart', 'getting', 'started', 'requirements',
    'workflow', 'pipeline', 'process', 'step', 'phase', 'stage',
    'input', 'output', 'result', 'outcome', 'goal', 'objective'
}

# BOND protocol keywords (for BOND users)
BOND_KEYWORDS = {
    'skill', 'drift', 'anchor', 'tokens', 'bonfire', 'qais', 'bond',
    'resonance', 'field', 'optimization', 'layer', 'sync', 'save',
    'portal', 'buffer', 'archive', 'ops', 'master', 'relational',
    'passthrough', 'visual', 'identity', 'binding', 'seed', 'vector',
    'counter', 'session', 'context', 'restore', 'compact'
}


# =============================================================================
# DOMAIN REGISTRY
# =============================================================================

@dataclass
class Domain:
    """A domain is a named set of weighted keywords."""
    name: str
    keywords: Set[str]
    weight: float = 3.0
    active: bool = True


class DomainRegistry:
    """
    Manages domain keyword sets.
    Users can add project-specific domains.
    """
    
    def __init__(self):
        self.domains: Dict[str, Domain] = {}
        # Register built-in domains
        self.register("code", CODE_KEYWORDS, weight=3.0, active=True)
        self.register("docs", DOC_KEYWORDS, weight=2.0, active=True)
    
    def register(self, name: str, keywords: Set[str], weight: float = 3.0, active: bool = True):
        """Register a new domain."""
        self.domains[name] = Domain(name, {k.lower() for k in keywords}, weight, active)
    
    def activate(self, name: str):
        """Activate a domain."""
        if name in self.domains:
            self.domains[name].active = True
    
    def deactivate(self, name: str):
        """Deactivate a domain."""
        if name in self.domains:
            self.domains[name].active = False
    
    def add_keywords(self, domain_name: str, keywords: List[str]):
        """Add keywords to an existing domain."""
        if domain_name in self.domains:
            self.domains[domain_name].keywords.update(k.lower() for k in keywords)
    
    def get_weight(self, keyword: str) -> float:
        """Get weight for a keyword based on active domains."""
        keyword = keyword.lower()
        max_weight = 1.0
        for domain in self.domains.values():
            if domain.active and keyword in domain.keywords:
                max_weight = max(max_weight, domain.weight)
        return max_weight
    
    def get_all_active_keywords(self) -> Set[str]:
        """Get all keywords from active domains."""
        result = set()
        for domain in self.domains.values():
            if domain.active:
                result.update(domain.keywords)
        return result
    
    def list_domains(self) -> List[Dict]:
        """List all domains with stats."""
        return [
            {"name": d.name, "keywords": len(d.keywords), "weight": d.weight, "active": d.active}
            for d in self.domains.values()
        ]


# Global registry instance
_REGISTRY = DomainRegistry()

def get_registry() -> DomainRegistry:
    """Get the global domain registry."""
    return _REGISTRY


# =============================================================================
# VECTOR OPERATIONS (Hyperdimensional Computing)
# =============================================================================

def seed_to_vector(seed: str) -> np.ndarray:
    """Convert text seed to N-dimensional bipolar HD vector."""
    h = hashlib.sha512(seed.encode()).digest()
    rng = np.random.RandomState(list(h[:4]))
    return rng.choice([-1, 1], size=N).astype(np.float32)


def resonance(a: np.ndarray, b: np.ndarray) -> float:
    """Compute resonance (normalized dot product) between two vectors."""
    return float(np.dot(a, b) / N)


# =============================================================================
# TEXT PROCESSING
# =============================================================================

def text_to_keywords(text: str) -> List[str]:
    """Extract meaningful keywords from text."""
    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text.lower())
    return list(set(w for w in words if len(w) > 2 and w not in STOPWORDS))


def text_to_vector_weighted(text: str, registry: DomainRegistry = None) -> Tuple[np.ndarray, List[str], List[str]]:
    """
    Convert text to HD vector with domain-based weighting.
    Domain keywords get higher weight in the bundle.
    
    Returns: (vector, all_keywords, domain_keywords_found)
    """
    if registry is None:
        registry = get_registry()
    
    keywords = text_to_keywords(text)
    if not keywords:
        return seed_to_vector(text), [], []
    
    domain_keywords = registry.get_all_active_keywords()
    domain_found = [k for k in keywords if k in domain_keywords]
    
    # Bundle keywords with weighting
    bundle = np.zeros(N, dtype=np.float32)
    for kw in keywords:
        weight = registry.get_weight(kw)
        bundle += weight * seed_to_vector(kw)
    
    # Normalize to bipolar
    result = np.sign(bundle)
    result[result == 0] = 1
    return result.astype(np.float32), keywords, domain_found


# =============================================================================
# PASSTHROUGH PROCESSOR
# =============================================================================

class PassthroughProcessor:
    """
    Resonance-based relevance filter.
    
    "Resonate first, load later" - determines what context to load
    BEFORE committing tokens to full retrieval.
    
    Usage:
        proc = PassthroughProcessor()
        proc.register_domain("myproject", ["widget", "gadget"])
        result = proc.passthrough(user_input, ["widget", "other"])
        # result["should_load"] contains contexts worth loading
    """
    
    def __init__(self, registry: DomainRegistry = None):
        self.registry = registry or get_registry()
        self.known_contexts: Set[str] = set()
    
    def add_context(self, context: str):
        """Add a known context to check against."""
        self.known_contexts.add(context)
    
    def add_contexts(self, contexts: List[str]):
        """Add multiple contexts."""
        self.known_contexts.update(contexts)
    
    def register_domain(self, name: str, keywords: List[str], weight: float = 3.0):
        """Register a project-specific domain."""
        self.registry.register(name, set(keywords), weight=weight, active=True)
    
    def passthrough(self, text: str, candidates: Optional[List[str]] = None) -> Dict:
        """
        Main passthrough function.
        
        Args:
            text: Input text to analyze
            candidates: Contexts to check (uses known_contexts if None)
        
        Returns:
            Dict with:
            - keywords: all extracted keywords
            - domain_keywords: keywords matching active domains
            - matches: contexts with confidence levels
            - should_load: HIGH/EXACT confidence contexts
            - confidence: overall confidence level
        """
        text_vec, keywords, domain_found = text_to_vector_weighted(text, self.registry)
        keywords_lower = set(keywords)
        
        check_contexts = list(candidates) if candidates else list(self.known_contexts)
        
        result = {
            "keywords": keywords,
            "domain_keywords": domain_found,
            "matches": [],
            "should_load": [],
            "confidence": "NONE"
        }
        
        for context in check_contexts:
            ctx_lower = context.lower()
            
            # Check direct keyword match
            direct_match = ctx_lower in keywords_lower
            
            # Compute resonance
            score = resonance(text_vec, seed_to_vector(context))
            
            # Determine confidence
            if direct_match:
                confidence = "EXACT"
            elif score > 0.12:
                confidence = "HIGH"
            elif score > 0.06:
                confidence = "MEDIUM"
            elif score > 0.02:
                confidence = "LOW"
            else:
                confidence = "NOISE"
            
            if confidence != "NOISE":
                result["matches"].append({
                    "context": context,
                    "score": round(score, 4),
                    "confidence": confidence,
                    "direct": direct_match
                })
        
        # Sort: EXACT first, then by score
        conf_order = {"EXACT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        result["matches"].sort(key=lambda x: (conf_order.get(x["confidence"], 4), -x["score"]))
        
        # Load recommendations (EXACT and HIGH only)
        for m in result["matches"]:
            if m["confidence"] in ["EXACT", "HIGH"]:
                result["should_load"].append(m["context"])
        
        if result["matches"]:
            result["confidence"] = result["matches"][0]["confidence"]
        
        return result
    
    def quick_check(self, text: str, context: str) -> Tuple[bool, str]:
        """
        Quick yes/no for a specific context.
        
        Returns: (should_load, confidence_level)
        """
        text_vec, keywords, _ = text_to_vector_weighted(text, self.registry)
        
        if context.lower() in set(keywords):
            return (True, "EXACT")
        
        score = resonance(text_vec, seed_to_vector(context))
        
        if score > 0.12:
            return (True, "HIGH")
        elif score > 0.06:
            return (True, "MEDIUM")
        else:
            return (False, "LOW" if score > 0.02 else "NOISE")


# =============================================================================
# CONVENIENCE API
# =============================================================================

_PROCESSOR: Optional[PassthroughProcessor] = None

def get_processor() -> PassthroughProcessor:
    """Get or create the global processor."""
    global _PROCESSOR
    if _PROCESSOR is None:
        _PROCESSOR = PassthroughProcessor()
    return _PROCESSOR


def passthrough(text: str, candidates: List[str] = None) -> Dict:
    """
    Quick passthrough query.
    
    Args:
        text: Input text to analyze
        candidates: Contexts to check for relevance
    
    Returns:
        Dict with matches and load recommendations
    """
    return get_processor().passthrough(text, candidates)


def register_project(name: str, keywords: List[str], weight: float = 3.0):
    """
    Register a project-specific domain.
    
    Args:
        name: Domain name (e.g., "myproject")
        keywords: List of project-specific keywords
        weight: Weight multiplier (default 3.0)
    """
    get_processor().register_domain(name, keywords, weight)


def add_contexts(contexts: List[str]):
    """Add known contexts to the global processor."""
    get_processor().add_contexts(contexts)


def register_bond():
    """Register BOND protocol domain (for BOND users)."""
    register_project("bond", list(BOND_KEYWORDS), weight=3.0)


def quick_check(text: str, context: str) -> Tuple[bool, str]:
    """Quick check if a context should be loaded."""
    return get_processor().quick_check(text, context)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("QAIS Passthrough v3 - Token-Saving Relevance Filter")
    print("=" * 60)
    
    # Example: Generic code
    print("\n[Test 1: Generic code]")
    result = passthrough(
        "def fetch_user_data(): return api.request('/users')",
        ["api", "fetch", "user", "pizza", "weather"]
    )
    print(f"Should load: {result['should_load']}")
    print(f"Confidence: {result['confidence']}")
    
    # Example: With project domain
    print("\n[Test 2: With project domain]")
    register_project("myapp", ["widget", "gadget", "flux"])
    result2 = passthrough(
        "The widget component needs flux state management",
        ["widget", "flux", "gadget", "pizza"]
    )
    print(f"Should load: {result2['should_load']}")
    print(f"Domain keywords: {result2['domain_keywords']}")
    
    # List domains
    print("\n[Registered domains]")
    for d in get_registry().list_domains():
        print(f"  {d['name']}: {d['keywords']} keywords, weight={d['weight']}")
    
    print("\n" + "=" * 60)
    print("✓ Ready for use. See docstring for integration examples.")
    print("=" * 60)
