"""
QAIS MCP Server v3 (with Passthrough v5)
Quantum Approximate Identity Substrate
True resonance memory for Claude.

"Don't index. Resonate."

Part of the BOND Protocol
https://github.com/moneyjarrod/BOND

v3 CHANGES:
  - Passthrough now resonates against STORED FACTS, not just context names
  - v5 enhancements: synonym expansion, number+unit normalization, bigrams
  - "50 meter boundary" now finds FPRS via fact "50m boundary of existence"

Session 64 | J-Dub & Claude | 2026-01-30
"""

import json
import hashlib
import sys
import os
import re

try:
    import numpy as np
except ImportError:
    sys.exit(1)

# =============================================================================
# QAIS CORE
# =============================================================================

N = 4096

def seed_to_vector(seed):
    h = hashlib.sha512(seed.encode()).digest()
    rng = np.random.RandomState(list(h[:4]))
    return rng.choice([-1, 1], size=N).astype(np.float32)

def bind(a, b):
    return a * b

def resonance(query, field):
    return float(np.dot(query, field) / N)


# =============================================================================
# ENHANCED TEXT PROCESSING (v5)
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
    'being', 'been', 'much', 'way', 'even', 'new', 'want', 'first', 'any',
    'happens', 'does', 'mean', 'work', 'works', 'things', 'thing'
}

# Synonym expansion map
SYNONYMS = {
    'meter': ['m', 'meters', 'metre'],
    'm': ['meter', 'meters'],
    'meters': ['m', 'meter'],
    'config': ['configuration', 'configure'],
    'configuration': ['config'],
    'params': ['parameters', 'param'],
    'parameters': ['params'],
    'derive': ['compute', 'calculate', 'derived'],
    'compute': ['derive', 'calculate'],
    'store': ['save', 'persist', 'stored'],
    'save': ['store', 'persist'],
}

# Number+unit expansions
UNIT_EXPANSIONS = {
    'm': 'meter',
    'ms': 'millisecond',
    's': 'second',
    'km': 'kilometer',
    'cm': 'centimeter',
}

def normalize_number_units(text):
    """'50m' → '50 meter'"""
    result = text
    for abbrev, full in UNIT_EXPANSIONS.items():
        pattern = r'(\d+)' + abbrev + r'\b'
        replacement = r'\1 ' + full
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result

def expand_synonyms(keywords):
    """Add synonyms to keyword set."""
    expanded = set(keywords)
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in SYNONYMS:
            expanded.update(SYNONYMS[kw_lower])
    return list(expanded)

def text_to_keywords_v5(text):
    """Enhanced keyword extraction."""
    # Normalize number+units
    text = normalize_number_units(text)
    
    # Extract base keywords
    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text.lower())
    keywords = [w for w in words if len(w) > 2 and w not in STOPWORDS]
    
    # Expand synonyms
    keywords = expand_synonyms(keywords)
    
    # Add bigrams
    base_words = [w for w in words if len(w) > 2 and w not in STOPWORDS]
    for i in range(len(base_words) - 1):
        bigram = f"{base_words[i]}_{base_words[i+1]}"
        keywords.append(bigram)
    
    return list(set(keywords))

def text_to_vector_v5(text):
    """Convert text to HD vector with v5 enhancements."""
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
# QAIS FIELD
# =============================================================================

class QAISField:
    def __init__(self, field_path=None):
        if field_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            field_path = os.path.join(script_dir, "qais_field.npz")
        self.field_path = field_path
        self.identity_field = np.zeros(N, dtype=np.float32)
        self.role_fields = {}
        self.stored = set()
        self.count = 0
        
        # Fact registry for passthrough
        self.fact_to_identities = {}
        self.fact_vectors = {}
        self.identity_to_facts = {}
        
        if os.path.exists(self.field_path):
            self._load()
    
    def _load(self):
        try:
            data = np.load(self.field_path, allow_pickle=True)
            self.identity_field = data['identity_field']
            self.role_fields = data['role_fields'].item()
            self.stored = set(data['stored'].tolist())
            self.count = int(data['count'])
            self._build_fact_registry()
        except:
            pass
    
    def _build_fact_registry(self):
        """Build fact->identity mappings with v5 vectorization."""
        self.fact_to_identities = {}
        self.fact_vectors = {}
        self.identity_to_facts = {}
        
        for key in self.stored:
            parts = key.split('|', 2)
            if len(parts) == 3:
                identity, role, fact = parts
                
                if fact not in self.fact_to_identities:
                    self.fact_to_identities[fact] = set()
                    self.fact_vectors[fact] = text_to_vector_v5(fact)
                self.fact_to_identities[fact].add(identity)
                
                if identity not in self.identity_to_facts:
                    self.identity_to_facts[identity] = set()
                self.identity_to_facts[identity].add(fact)
    
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
        
        # Update fact registry
        if fact not in self.fact_to_identities:
            self.fact_to_identities[fact] = set()
            self.fact_vectors[fact] = text_to_vector_v5(fact)
        self.fact_to_identities[fact].add(identity)
        
        if identity not in self.identity_to_facts:
            self.identity_to_facts[identity] = set()
        self.identity_to_facts[identity].add(fact)
        
        self._save()
        return {"status": "stored", "key": key, "count": self.count}
    
    def resonate(self, identity, role, candidates):
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
        vec = seed_to_vector(identity)
        clean = np.sign(self.identity_field)
        score = resonance(vec, clean)
        return {"identity": identity, "score": round(score, 4), "exists": score > 0.025}
    
    def stats(self):
        return {
            "total_bindings": self.count,
            "roles": list(self.role_fields.keys()),
            "role_count": len(self.role_fields),
            "facts_indexed": len(self.fact_vectors),
            "identities_indexed": len(self.identity_to_facts)
        }
    
    def passthrough_v5(self, text, candidates, threshold=0.08, top_k=3):
        """
        v5 Passthrough: Resonate against facts with enhanced text processing.
        """
        text_vec = text_to_vector_v5(text)
        keywords = text_to_keywords_v5(text)
        keywords_lower = set(k.lower() for k in keywords)
        candidate_set = set(candidates)
        
        # Phase 1: Direct keyword match (with synonyms)
        direct_matches = set()
        for candidate in candidates:
            cand_lower = candidate.lower()
            if cand_lower in keywords_lower:
                direct_matches.add(candidate)
            if cand_lower in SYNONYMS:
                for syn in SYNONYMS[cand_lower]:
                    if syn in keywords_lower:
                        direct_matches.add(candidate)
                        break
        
        # Phase 2: Fact resonance
        fact_scores = []
        for fact, fact_vec in self.fact_vectors.items():
            score = resonance(text_vec, fact_vec)
            if score > threshold:
                fact_scores.append((fact, score, self.fact_to_identities[fact]))
        fact_scores.sort(key=lambda x: -x[1])
        
        # Phase 3: Map to candidates
        identity_evidence = {}
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
                elif best_score > 0.30:
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
            "domain_keywords": [],
            "matches": matches,
            "should_load": should_load,
            "confidence": matches[0]["confidence"] if matches else "NONE",
            "facts_checked": len(self.fact_vectors),
            "version": "v5"
        }


# =============================================================================
# MCP PROTOCOL
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
                "identity": {"type": "string", "description": "The entity to query (e.g., 'Chad Money', 'FPRS')"},
                "role": {"type": "string", "description": "The role/attribute to query (e.g., 'prof', 'def', 'bf')"},
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
    },
    {
        "name": "qais_passthrough",
        "description": "Token-saving relevance filter. Given text and candidate contexts, returns which contexts are worth loading. Use BEFORE loading full context to save tokens.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Input text to analyze (user message, code, etc.)"},
                "candidates": {"type": "array", "items": {"type": "string"}, "description": "List of possible contexts to check (e.g., ['SKILL', 'FPRS', 'config'])"},
                "project_keywords": {"type": "array", "items": {"type": "string"}, "description": "Optional: project-specific keywords to boost"}
            },
            "required": ["text", "candidates"]
        }
    }
]


def handle_request(request):
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
                "serverInfo": {"name": "qais-server", "version": "3.0.0"}
            }
        }
    
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    
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
            elif tool_name == "qais_passthrough":
                result = field.passthrough_v5(args["text"], args["candidates"])
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
