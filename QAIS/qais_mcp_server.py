"""
QAIS MCP Server v3.4
Quantum Approximate Identity Substrate
True resonance memory for Claude.

"Don't index. Resonate."

Part of the BOND Protocol
https://github.com/moneyjarrod/BOND

Tools:
  - qais_resonate: Query for resonance matches
  - qais_exists: Check if entity exists in field
  - qais_store: Store identity-role-fact binding
  - qais_stats: Get field statistics
  - qais_get: Direct retrieval (anchor→content)
  - qais_passthrough: Token-saving relevance filter
  - heatmap_touch/hot/chunk/clear: Session heat map
  - bond_gate: Conditional routing gate
  - crystal: Persistent crystallization
  - perspective_store: Store seed into perspective's isolated field
  - perspective_check: Check text against perspective's seeds
"""

import json
import hashlib
import sys
import os
import re
import time
from collections import defaultdict
from datetime import datetime
from BOND_gate import get_gate
from tool_auth import validate_tool_call, get_active_entity

try:
    import numpy as np
except ImportError:
    sys.exit(1)

N = 4096

def seed_to_vector(seed):
    h = hashlib.sha512(seed.encode()).digest()
    rng = np.random.RandomState(list(h[:4]))
    return rng.choice([-1, 1], size=N).astype(np.float32)

def bind(a, b):
    return a * b

def resonance(query, field):
    return float(np.dot(query, field) / N)


# ═════════════════════════════════════════════════════
# Session Heat Map
# ═════════════════════════════════════════════════════

class SessionHeatMap:
    def __init__(self):
        self.concepts = defaultdict(lambda: {"count": 0, "first": 0, "last": 0, "contexts": []})
        self.session_start = time.time()

    def touch(self, concepts, context=""):
        now = time.time()
        results = []
        for concept in concepts:
            concept = concept.lower()
            entry = self.concepts[concept]
            if entry["count"] == 0:
                entry["first"] = now
            entry["count"] += 1
            entry["last"] = now
            if context:
                entry["contexts"].append(context)
            results.append({"concept": concept, "count": entry["count"]})
        return {"touched": len(results), "concepts": results}

    def hot(self, top_k=10):
        now = time.time()
        scored = []
        for concept, entry in self.concepts.items():
            age_minutes = (now - entry["last"]) / 60
            if age_minutes < 5: recency = 2.0
            elif age_minutes < 15: recency = 1.5
            elif age_minutes < 30: recency = 1.0
            else: recency = 0.5
            score = entry["count"] * recency
            scored.append({"concept": concept, "count": entry["count"], "score": round(score, 2),
                          "last_touch_mins": round(age_minutes, 1), "contexts": entry["contexts"][-3:]})
        scored.sort(key=lambda x: -x["score"])
        return scored[:top_k]

    def for_chunk(self):
        hot = self.hot(10)
        now = time.time()
        session_mins = (now - self.session_start) / 60
        cold = [c for c, e in self.concepts.items() if (now - e["last"]) / 60 > 15]
        hot_names = [h["concept"] for h in hot[:5]]
        return {"session_minutes": round(session_mins, 1), "total_concepts": len(self.concepts),
                "total_touches": sum(e["count"] for e in self.concepts.values()),
                "hot": [{"concept": h["concept"], "count": h["count"], "why": h["contexts"]} for h in hot],
                "cold": cold[:5],
                "summary": f"{len(self.concepts)} concepts, hot: {', '.join(hot_names)}"}

    def clear(self):
        count = len(self.concepts)
        self.concepts.clear()
        self.session_start = time.time()
        return {"cleared": count, "status": "reset"}

HEATMAP = SessionHeatMap()


# ═════════════════════════════════════════════════════
# Crystal — Persistent Crystallization
# ═════════════════════════════════════════════════════

SIGNAL_WORDS = {'breakthrough', 'insight', 'fixed', 'solved', 'proven', 'works', 'principle',
    'architecture', 'pattern', 'protocol', 'rule', 'bonfire', 'milestone', 'complete', 'done',
    'verified', 'created', 'implemented', 'integrated', 'unified', 'merged'}

STOPWORDS = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
    'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
    'shall', 'can', 'need', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
    'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'under', 'again',
    'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each',
    'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
    'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or', 'because', 'until', 'while',
    'this', 'that', 'these', 'those', 'it', 'its', 'i', 'me', 'my', 'we', 'our', 'you', 'your',
    'he', 'him', 'his', 'she', 'her', 'they', 'them', 'their', 'what', 'which', 'who', 'whom',
    'about', 'let', 'tell', 'know', 'think', 'make', 'take', 'see', 'come', 'look', 'use', 'find',
    'give', 'got', 'get', 'put', 'said', 'say', 'like', 'also', 'well', 'back', 'being', 'been',
    'much', 'way', 'even', 'new', 'want', 'first', 'any', 'happens', 'does', 'mean', 'work',
    'works', 'things', 'thing', 'session', 'chunk', 'crystallization'}

def extract_concepts(text, max_concepts=10):
    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text)
    freq = {}
    for word in words:
        w = word.lower()
        if len(w) > 2 and w not in STOPWORDS:
            freq[w] = freq.get(w, 0) + 1
    scored = []
    for word, count in freq.items():
        score = count
        if word in SIGNAL_WORDS: score += 5
        if word.upper() in text or word.capitalize() in text: score += 2
        scored.append((word, score))
    scored.sort(key=lambda x: -x[1])
    return [c[0] for c in scored[:max_concepts]]

def extract_sections(text):
    sections = {}
    header_matches = re.findall(r'###\s*(\w+[\w\s]*)\n(.*?)(?=###|\Z)', text, re.DOTALL | re.IGNORECASE)
    for header, content in header_matches:
        sections[header.lower().strip()] = content.strip()[:500]
    bold_matches = re.findall(r'\*\*(\w+[\w\s]*):\*\*\s*(.*?)(?=\*\*|\n\n|\Z)', text, re.DOTALL)
    for header, content in bold_matches:
        sections[header.lower().strip()] = content.strip()[:500]
    return sections

def parse_bullet_items(text):
    items = re.findall(r'[-*]\s*(.+?)(?:\n|$)', text)
    return [item.strip() for item in items if item.strip()]

class Crystal:
    def __init__(self, field, heatmap):
        self.field = field
        self.heatmap = heatmap

    def crystallize(self, chunk_text, session_num, project="BOND", context=None):
        timestamp = datetime.now().isoformat()
        result = {"session": session_num, "project": project, "timestamp": timestamp,
                  "concepts": [], "momentum": None, "stored": [], "heatmap_touched": 0}
        concepts = extract_concepts(chunk_text)
        result["concepts"] = concepts
        if concepts:
            touch_result = self.heatmap.touch(concepts, f"Session {session_num} crystal")
            result["heatmap_touched"] = touch_result["touched"]
        sections = extract_sections(chunk_text)
        completed = []
        for key in ['completed', 'done', 'finished']:
            if key in sections:
                completed = parse_bullet_items(sections[key])
                break
        state = "in progress"
        for key in ['state', 'current', 'status']:
            if key in sections:
                state = sections[key][:100]
                break
        next_task = "continue"
        for key in ['next', 'open', 'todo']:
            if key in sections:
                next_text = sections[key]
                items = parse_bullet_items(next_text)
                next_task = items[0] if items else next_text[:100]
                break
        completed_str = ", ".join(completed[:3]) if completed else "work"
        momentum = f"S{session_num} {completed_str}, {state[:50]}, next: {next_task[:50]}"
        result["momentum"] = momentum
        session_id = f"Session{session_num}"
        store_result = self.field.store(session_id, "momentum", momentum)
        if store_result["status"] == "stored":
            result["stored"].append(f"{session_id}|momentum")
        if context:
            store_result = self.field.store(session_id, "context", context[:200])
            if store_result["status"] == "stored":
                result["stored"].append(f"{session_id}|context")
        for key in ['insight', 'key insight', 'key']:
            if key in sections:
                insight = sections[key][:200]
                store_result = self.field.store(session_id, "insight", insight)
                if store_result["status"] == "stored":
                    result["stored"].append(f"{session_id}|insight")
                break
        if concepts:
            tags = ", ".join(concepts[:5])
            store_result = self.field.store(session_id, "tags", tags)
            if store_result["status"] == "stored":
                result["stored"].append(f"{session_id}|tags")
        return result

CRYSTAL = None
def get_crystal():
    global CRYSTAL
    if CRYSTAL is None:
        CRYSTAL = Crystal(get_field(), HEATMAP)
    return CRYSTAL


# ═════════════════════════════════════════════════════
# QAIS Field — Resonance Storage
# ═════════════════════════════════════════════════════

SYNONYMS = {'meter': ['m', 'meters', 'metre'], 'm': ['meter', 'meters'], 'meters': ['m', 'meter'],
    'config': ['configuration', 'configure'], 'configuration': ['config'],
    'params': ['parameters', 'param'], 'parameters': ['params'],
    'derive': ['compute', 'calculate', 'derived'], 'compute': ['derive', 'calculate'],
    'store': ['save', 'persist', 'stored'], 'save': ['store', 'persist']}
UNIT_EXPANSIONS = {'m': 'meter', 'ms': 'millisecond', 's': 'second', 'km': 'kilometer', 'cm': 'centimeter'}

def normalize_number_units(text):
    result = text
    for abbrev, full in UNIT_EXPANSIONS.items():
        pattern = r'(\d+)' + abbrev + r'\b'
        replacement = r'\1 ' + full
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result

def expand_synonyms(keywords):
    expanded = set(keywords)
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in SYNONYMS:
            expanded.update(SYNONYMS[kw_lower])
    return list(expanded)

def text_to_keywords_v5(text):
    text = normalize_number_units(text)
    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text.lower())
    keywords = [w for w in words if len(w) > 2 and w not in STOPWORDS]
    keywords = expand_synonyms(keywords)
    base_words = [w for w in words if len(w) > 2 and w not in STOPWORDS]
    for i in range(len(base_words) - 1):
        bigram = f"{base_words[i]}_{base_words[i+1]}"
        keywords.append(bigram)
    return list(set(keywords))

def text_to_vector_v5(text):
    keywords = text_to_keywords_v5(text)
    if not keywords:
        return seed_to_vector(text)
    bundle = np.zeros(N, dtype=np.float32)
    for kw in keywords:
        bundle += seed_to_vector(kw)
    result = np.sign(bundle)
    result[result == 0] = 1
    return result.astype(np.float32)

class QAISField:
    def __init__(self, field_path=None):
        if field_path is None:
            # Default: data/ directory relative to BOND_ROOT
            bond_root = os.environ.get('BOND_ROOT',
                os.path.join(os.path.dirname(__file__), '..'))
            data_dir = os.path.join(bond_root, 'data')
            os.makedirs(data_dir, exist_ok=True)
            field_path = os.path.join(data_dir, 'qais_field.npz')
        self.field_path = field_path
        self.identity_field = np.zeros(N, dtype=np.float32)
        self.role_fields = {}
        self.stored = set()
        self.count = 0
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
        except: pass

    def _build_fact_registry(self):
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
            np.savez(self.field_path, identity_field=self.identity_field,
                     role_fields=self.role_fields,
                     stored=np.array(list(self.stored)), count=self.count)
        except: pass

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
        return {"total_bindings": self.count, "roles": list(self.role_fields.keys()),
                "role_count": len(self.role_fields), "facts_indexed": len(self.fact_vectors),
                "identities_indexed": len(self.identity_to_facts)}

    def get(self, identity, role):
        """Direct retrieval for three-block architecture."""
        for key in self.stored:
            parts = key.split('|', 2)
            if len(parts) == 3:
                stored_id, stored_role, fact = parts
                if stored_id == identity and stored_role == role:
                    return {"identity": identity, "role": role, "fact": fact, "found": True}
        return {"identity": identity, "role": role, "fact": None, "found": False}

    def remove(self, identity, role, fact):
        """Remove a binding by subtracting its vectors from the field.
        Deterministic vectors allow exact reversal of store()."""
        key = f"{identity}|{role}|{fact}"
        if key not in self.stored:
            return {"status": "not_found", "key": key}
        self.stored.discard(key)
        id_vec = seed_to_vector(identity)
        fact_vec = seed_to_vector(fact)
        self.identity_field -= id_vec
        if role in self.role_fields:
            self.role_fields[role] -= bind(id_vec, fact_vec)
        self.count -= 1
        # Update registries
        if fact in self.fact_to_identities:
            self.fact_to_identities[fact].discard(identity)
            if not self.fact_to_identities[fact]:
                del self.fact_to_identities[fact]
                self.fact_vectors.pop(fact, None)
        if identity in self.identity_to_facts:
            self.identity_to_facts[identity].discard(fact)
            if not self.identity_to_facts[identity]:
                del self.identity_to_facts[identity]
        self._save()
        return {"status": "removed", "key": key, "count": self.count}

    def passthrough_v5(self, text, candidates, threshold=0.08, top_k=3):
        text_vec = text_to_vector_v5(text)
        keywords = text_to_keywords_v5(text)
        keywords_lower = set(k.lower() for k in keywords)
        candidate_set = set(candidates)
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
        fact_scores = []
        for fact, fact_vec in self.fact_vectors.items():
            score = resonance(text_vec, fact_vec)
            if score > threshold:
                fact_scores.append((fact, score, self.fact_to_identities[fact]))
        fact_scores.sort(key=lambda x: -x[1])
        identity_evidence = {}
        for fact, score, identities in fact_scores:
            for identity in identities:
                if identity in candidate_set:
                    if identity not in identity_evidence:
                        identity_evidence[identity] = []
                    if len(identity_evidence[identity]) < top_k:
                        identity_evidence[identity].append((fact, score))
        matches = []
        for candidate in candidates:
            direct = candidate in direct_matches
            evidence = identity_evidence.get(candidate, [])
            if direct or evidence:
                best_score = evidence[0][1] if evidence else 0.0
                if direct: confidence = "EXACT"
                elif best_score > 0.30: confidence = "HIGH"
                elif best_score > 0.15: confidence = "MEDIUM"
                else: confidence = "LOW"
                matches.append({"context": candidate, "score": round(best_score, 4),
                               "confidence": confidence, "direct": direct,
                               "evidence": [(f, round(s, 4)) for f, s in evidence[:top_k]]})
        conf_order = {"EXACT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        matches.sort(key=lambda x: (conf_order.get(x["confidence"], 4), -x["score"]))
        should_load = [m["context"] for m in matches if m["confidence"] in ["EXACT", "HIGH"]]
        return {"keywords": keywords, "matches": matches, "should_load": should_load,
                "confidence": matches[0]["confidence"] if matches else "NONE",
                "facts_checked": len(self.fact_vectors), "version": "v5"}

FIELD = None
def get_field():
    global FIELD
    if FIELD is None:
        FIELD = QAISField()
    return FIELD


# ═════════════════════════════════════════════════════
# Perspective Isolated Fields (S98)
# ═════════════════════════════════════════════════════
# Each perspective gets its own tiny .npz field.
# Seed content resonates in isolation — no global field noise.

PERSPECTIVE_FIELDS = {}
PERSPECTIVE_DATA_DIR = os.path.join(
    os.environ.get('BOND_ROOT', os.path.join(os.path.dirname(__file__), '..')),
    'data', 'perspectives'
)
os.makedirs(PERSPECTIVE_DATA_DIR, exist_ok=True)

def get_perspective_field(perspective):
    """Get or create an isolated QAISField for a perspective's seeds."""
    if perspective not in PERSPECTIVE_FIELDS:
        field_path = os.path.join(PERSPECTIVE_DATA_DIR, f"{perspective}.npz")
        PERSPECTIVE_FIELDS[perspective] = QAISField(field_path)
    return PERSPECTIVE_FIELDS[perspective]

# Crystal continuity fields — separate from seed fields (S116)
# Same QAISField, different file. Seeds stay tight, crystal stays narrative.
PERSPECTIVE_CRYSTAL_FIELDS = {}

def get_perspective_crystal_field(perspective):
    """Get or create an isolated QAISField for a perspective's crystal momentum."""
    if perspective not in PERSPECTIVE_CRYSTAL_FIELDS:
        field_path = os.path.join(PERSPECTIVE_DATA_DIR, f"{perspective}_crystal.npz")
        PERSPECTIVE_CRYSTAL_FIELDS[perspective] = QAISField(field_path)
    return PERSPECTIVE_CRYSTAL_FIELDS[perspective]


# ═════════════════════════════════════════════════════
# MCP Tool Definitions
# ═════════════════════════════════════════════════════

TOOLS = [
    {"name": "qais_resonate", "description": "Query the QAIS field for resonance matches.",
     "inputSchema": {"type": "object", "properties": {
         "identity": {"type": "string", "description": "The entity to query"},
         "role": {"type": "string", "description": "The role/attribute to query"},
         "candidates": {"type": "array", "items": {"type": "string"}, "description": "List of possible facts to test"}
     }, "required": ["identity", "role", "candidates"]}},
    {"name": "qais_exists", "description": "Check if an entity exists in the QAIS field.",
     "inputSchema": {"type": "object", "properties": {
         "identity": {"type": "string", "description": "The entity to check"}
     }, "required": ["identity"]}},
    {"name": "qais_store", "description": "Store a new identity-role-fact binding in the QAIS field.",
     "inputSchema": {"type": "object", "properties": {
         "identity": {"type": "string", "description": "The entity"},
         "role": {"type": "string", "description": "The role/attribute"},
         "fact": {"type": "string", "description": "The fact to store"}
     }, "required": ["identity", "role", "fact"]}},
    {"name": "qais_stats", "description": "Get QAIS field statistics.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "qais_get", "description": "Direct retrieval for three-block architecture.",
     "inputSchema": {"type": "object", "properties": {
         "identity": {"type": "string", "description": "The anchor/entity to retrieve"},
         "role": {"type": "string", "description": "The role (e.g., 'bridge', 'content', 'block_b')"}
     }, "required": ["identity", "role"]}},
    {"name": "qais_passthrough", "description": "Token-saving relevance filter.",
     "inputSchema": {"type": "object", "properties": {
         "text": {"type": "string", "description": "Input text to analyze"},
         "candidates": {"type": "array", "items": {"type": "string"}, "description": "Contexts to check"}
     }, "required": ["text", "candidates"]}},
    {"name": "heatmap_touch", "description": "Mark concept(s) as actively being worked on.",
     "inputSchema": {"type": "object", "properties": {
         "concepts": {"type": "array", "items": {"type": "string"}, "description": "Concepts being touched"},
         "context": {"type": "string", "description": "Optional: why"}
     }, "required": ["concepts"]}},
    {"name": "heatmap_hot", "description": "Get hottest concepts by recent activity.",
     "inputSchema": {"type": "object", "properties": {
         "top_k": {"type": "integer", "description": "How many to return (default 10)"}}}},
    {"name": "heatmap_chunk", "description": "Get heat map summary formatted for {Chunk}.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "heatmap_clear", "description": "Reset heat map for new session.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "bond_gate", "description": "Conditional routing gate.",
     "inputSchema": {"type": "object", "properties": {
         "trigger": {"type": "string", "description": "Trigger type: 'restore' | 'crystal' | 'message'"},
         "context": {"type": "string", "description": "Optional context"},
         "message": {"type": "string", "description": "For 'message' trigger"}
     }, "required": ["trigger"]}},
    {"name": "crystal", "description": "Persistent crystallization.",
     "inputSchema": {"type": "object", "properties": {
         "chunk_text": {"type": "string", "description": "The crystallization text"},
         "session_num": {"type": "integer", "description": "Session number"},
         "project": {"type": "string", "description": "Project name (default: BOND)"},
         "context": {"type": "string", "description": "Optional context"}
     }, "required": ["chunk_text", "session_num"]}},
    {"name": "perspective_store", "description": "Store a seed into a perspective's isolated QAIS field. Each perspective has its own .npz field for tight resonance.",
     "inputSchema": {"type": "object", "properties": {
         "perspective": {"type": "string", "description": "Perspective entity name (e.g. P11-Plumber)"},
         "seed_title": {"type": "string", "description": "Seed name/title"},
         "seed_content": {"type": "string", "description": "Seed content text"}
     }, "required": ["perspective", "seed_title", "seed_content"]}},
    {"name": "perspective_check", "description": "Check conversation text against a perspective's isolated field for seed resonance. Returns scored matches. Used by Sync step 5 seed collection.",
     "inputSchema": {"type": "object", "properties": {
         "perspective": {"type": "string", "description": "Perspective entity name (e.g. P11-Plumber)"},
         "text": {"type": "string", "description": "Conversation text to check for resonance"}
     }, "required": ["perspective", "text"]}},
    {"name": "perspective_remove", "description": "Remove a pruned seed from a perspective's isolated QAIS field. Subtracts vectors for exact reversal. Used by Sync step 5d pruning execution.",
     "inputSchema": {"type": "object", "properties": {
         "perspective": {"type": "string", "description": "Perspective entity name (e.g. P11-Plumber)"},
         "seed_title": {"type": "string", "description": "Seed name/title to remove"},
         "seed_content": {"type": "string", "description": "Seed content text (must match what was stored)"}
     }, "required": ["perspective", "seed_title", "seed_content"]}},
]


# ═════════════════════════════════════════════════════
# MCP Handler
# ═════════════════════════════════════════════════════

def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
            "serverInfo": {"name": "qais-server", "version": "3.4.0"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        # ─── Runtime capability enforcement (S90) ───
        allowed, error = validate_tool_call(tool_name)
        if not allowed:
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": json.dumps(error, indent=2)}]}}
        try:
            if tool_name == "qais_resonate":
                result = get_field().resonate(args["identity"], args["role"], args["candidates"])
            elif tool_name == "qais_exists":
                result = get_field().exists(args["identity"])
            elif tool_name == "qais_store":
                result = get_field().store(args["identity"], args["role"], args["fact"])
            elif tool_name == "qais_stats":
                result = get_field().stats()
            elif tool_name == "qais_get":
                result = get_field().get(args["identity"], args["role"])
            elif tool_name == "qais_passthrough":
                result = get_field().passthrough_v5(args["text"], args["candidates"])
            elif tool_name == "heatmap_touch":
                result = HEATMAP.touch(args["concepts"], args.get("context", ""))
            elif tool_name == "heatmap_hot":
                result = HEATMAP.hot(args.get("top_k", 10))
            elif tool_name == "heatmap_chunk":
                result = HEATMAP.for_chunk()
            elif tool_name == "heatmap_clear":
                result = HEATMAP.clear()
            elif tool_name == "bond_gate":
                result = get_gate().evaluate(args["trigger"], args.get("context", ""), args.get("message", ""))
            elif tool_name == "crystal":
                # Two-field architecture (S116): perspective active → local crystal field
                # Seeds in {entity}.npz, crystal momentum in {entity}_crystal.npz
                entity, entity_class = get_active_entity()
                if entity and entity_class == 'perspective':
                    pcf = get_perspective_crystal_field(entity)
                    local_crystal = Crystal(pcf, HEATMAP)
                    result = local_crystal.crystallize(args["chunk_text"], args["session_num"],
                        args.get("project", "BOND"), args.get("context"))
                    result["routed_to"] = entity
                    result["field"] = "local"
                else:
                    result = get_crystal().crystallize(args["chunk_text"], args["session_num"],
                        args.get("project", "BOND"), args.get("context"))
                    result["field"] = "global"
            elif tool_name == "perspective_store":
                pf = get_perspective_field(args["perspective"])
                store_result = pf.store(args["seed_title"], "seed", args["seed_content"])
                result = {"perspective": args["perspective"], "seed": args["seed_title"],
                         "stored": store_result["status"] in ("stored", "exists"), "field_count": pf.count}
            elif tool_name == "perspective_remove":
                pf = get_perspective_field(args["perspective"])
                # Remove seed: identity=title, role=seed, fact=content (mirrors perspective_store)
                remove_result = pf.remove(args["seed_title"], "seed", args["seed_content"])
                result = {"perspective": args["perspective"], "seed": args["seed_title"],
                         "removed": remove_result["status"] == "removed", "field_count": pf.count,
                         "detail": remove_result["status"]}
            elif tool_name == "perspective_check":
                pf = get_perspective_field(args["perspective"])
                if pf.count == 0:
                    result = {"perspective": args["perspective"], "matches": [],
                             "note": "Field empty — no seeds stored yet. Use perspective_store to bootstrap."}
                else:
                    text_vec = text_to_vector_v5(args["text"])
                    matches = []
                    seen = set()
                    for key in pf.stored:
                        parts = key.split('|', 2)
                        if len(parts) == 3:
                            title, role, content = parts
                            if title in seen:
                                continue
                            seen.add(title)
                            seed_vec = text_to_vector_v5(content)
                            score = float(np.dot(text_vec, seed_vec) / N)
                            matches.append({"seed": title, "content_preview": content[:80], "score": round(score, 4)})
                    matches.sort(key=lambda x: -x["score"])
                    result = {"perspective": args["perspective"], "matches": matches, "field_count": pf.count}
            else:
                return {"jsonrpc": "2.0", "id": req_id, "error": {
                    "code": -32601, "message": f"Unknown tool: {tool_name}"}}
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(e)}}
    if method == "notifications/initialized":
        return None
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}

def main():
    get_field()
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            if response is not None:
                print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {
                "code": -32700, "message": "Parse error"}}), flush=True)
        except Exception as e:
            print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {
                "code": -32603, "message": str(e)}}), flush=True)

if __name__ == "__main__":
    main()
