"""
QAIS MCP Server v2
Quantum Approximate Identity Substrate
True resonance memory for Claude.

"Don't index. Resonate."

Part of the BOND Protocol
https://github.com/moneyjarrod/BOND

Tools:
  - qais_resonate: Query field for matches
  - qais_store: Store identity-role-fact bindings
  - qais_exists: Check if entity exists
  - qais_stats: Field statistics
  - qais_passthrough: Token-saving relevance filter (NEW)

Usage:
  1. Copy this file to your project folder
  2. Add to claude_desktop_config.json (see QAIS_SYSTEM.md)
  3. Restart Claude Desktop
  4. Store your project's identities via qais_store

Requirements:
  pip install numpy
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
# QAIS CORE - Hyperdimensional Computing
# =============================================================================

N = 4096  # Vector dimensions

def seed_to_vector(seed):
    """Deterministic bipolar vector from any string."""
    h = hashlib.sha512(seed.encode()).digest()
    rng = np.random.RandomState(list(h[:4]))
    return rng.choice([-1, 1], size=N).astype(np.float32)

def bind(a, b):
    """XOR-like binding for bipolar vectors."""
    return a * b

def resonance(query, field):
    """Normalized dot product - coherence measure."""
    return float(np.dot(query, field) / N)


# =============================================================================
# PASSTHROUGH - Token-Saving Relevance Filter
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

CODE_KEYWORDS = {
    'function', 'class', 'method', 'module', 'package', 'library',
    'variable', 'constant', 'parameter', 'argument', 'return', 'import',
    'export', 'interface', 'type', 'enum', 'struct', 'trait', 'impl',
    'loop', 'condition', 'branch', 'recursion', 'iteration', 'switch',
    'async', 'await', 'callback', 'promise', 'thread', 'concurrent',
    'parse', 'serialize', 'validate', 'transform', 'convert', 'compile',
    'fetch', 'request', 'response', 'query', 'filter', 'map', 'reduce',
    'error', 'exception', 'debug', 'test', 'fix', 'bug', 'issue',
    'config', 'settings', 'environment', 'initialize', 'setup', 'init',
    'array', 'list', 'dict', 'dictionary', 'set', 'queue', 'stack',
    'tree', 'graph', 'node', 'edge', 'hash', 'table', 'buffer', 'cache',
    'api', 'endpoint', 'route', 'handler', 'middleware', 'controller',
    'model', 'view', 'service', 'repository', 'factory', 'singleton',
    'commit', 'branch', 'merge', 'rebase', 'pull', 'push', 'clone'
}

# User can register project-specific keywords
PROJECT_KEYWORDS = set()

def register_keywords(keywords):
    """Register project-specific keywords for weighting."""
    PROJECT_KEYWORDS.update(k.lower() for k in keywords)

def text_to_keywords(text):
    """Extract meaningful keywords from text."""
    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text.lower())
    return list(set(w for w in words if len(w) > 2 and w not in STOPWORDS))

def text_to_vector_weighted(text):
    """Convert text to HD vector with domain weighting."""
    keywords = text_to_keywords(text)
    if not keywords:
        return seed_to_vector(text), [], []
    
    all_domain = CODE_KEYWORDS | PROJECT_KEYWORDS
    domain_found = [k for k in keywords if k in all_domain]
    
    bundle = np.zeros(N, dtype=np.float32)
    for kw in keywords:
        weight = 3.0 if kw in all_domain else 1.0
        bundle += weight * seed_to_vector(kw)
    
    result = np.sign(bundle)
    result[result == 0] = 1
    return result.astype(np.float32), keywords, domain_found

def passthrough(text, candidates):
    """
    Token-saving relevance filter.
    Returns which candidates are worth loading based on text resonance.
    
    Confidence levels:
    - EXACT: Direct keyword match in text
    - HIGH: Strong resonance (>0.12)
    - MEDIUM: Moderate resonance (>0.06)
    - LOW: Weak resonance (>0.02)
    - NOISE: Not relevant
    """
    text_vec, keywords, domain_found = text_to_vector_weighted(text)
    keywords_lower = set(keywords)
    
    result = {
        "keywords": keywords,
        "domain_keywords": domain_found,
        "matches": [],
        "should_load": [],
        "confidence": "NONE"
    }
    
    for candidate in candidates:
        ctx_lower = candidate.lower()
        direct_match = ctx_lower in keywords_lower
        score = resonance(text_vec, seed_to_vector(candidate))
        
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
                "context": candidate,
                "score": round(score, 4),
                "confidence": confidence,
                "direct": direct_match
            })
    
    conf_order = {"EXACT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    result["matches"].sort(key=lambda x: (conf_order.get(x["confidence"], 4), -x["score"]))
    
    for m in result["matches"]:
        if m["confidence"] in ["EXACT", "HIGH"]:
            result["should_load"].append(m["context"])
    
    if result["matches"]:
        result["confidence"] = result["matches"][0]["confidence"]
    
    return result


# =============================================================================
# QAIS FIELD
# =============================================================================

class QAISField:
    """Persistent resonance field."""
    
    def __init__(self, field_path=None):
        if field_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            field_path = os.path.join(script_dir, "qais_field.npz")
        self.field_path = field_path
        self.identity_field = np.zeros(N, dtype=np.float32)
        self.role_fields = {}
        self.stored = set()
        self.count = 0
        if os.path.exists(self.field_path):
            self._load()
    
    def _load(self):
        try:
            data = np.load(self.field_path, allow_pickle=True)
            self.identity_field = data['identity_field']
            self.role_fields = data['role_fields'].item()
            self.stored = set(data['stored'].tolist())
            self.count = int(data['count'])
        except:
            pass
    
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
            "role_count": len(self.role_fields)
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
                "identity": {"type": "string", "description": "The entity to query"},
                "role": {"type": "string", "description": "The role/attribute to query"},
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
                "project_keywords": {"type": "array", "items": {"type": "string"}, "description": "Optional: project-specific keywords to boost (e.g., ['bonfire', 'fprs'])"}
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
                "serverInfo": {"name": "qais-server", "version": "2.0.0"}
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
                # Register project keywords if provided
                if "project_keywords" in args:
                    register_keywords(args["project_keywords"])
                result = passthrough(args["text"], args["candidates"])
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
