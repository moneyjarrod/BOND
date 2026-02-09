"""
QAIS Core — Standalone QAISField for panel mcp_invoke.py.
Extracted from qais_mcp_server.py. No MCP deps, no tool_auth.
"""

import numpy as np
import hashlib
import os
import re

N = 4096

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
    'give', 'got', 'get', 'put', 'said', 'say', 'like', 'also', 'well', 'back', 'much', 'way',
    'even', 'new', 'want', 'first', 'any', 'happens', 'mean', 'work', 'works', 'things', 'thing',
    'session', 'chunk', 'crystallization'}

SYNONYMS = {'config': ['configuration', 'configure'], 'configuration': ['config'],
    'params': ['parameters', 'param'], 'parameters': ['params'],
    'derive': ['compute', 'calculate', 'derived'], 'compute': ['derive', 'calculate'],
    'store': ['save', 'persist', 'stored'], 'save': ['store', 'persist']}


def seed_to_vector(seed):
    h = hashlib.sha512(seed.encode()).digest()
    rng = np.random.RandomState(list(h[:4]))
    return rng.choice([-1, 1], size=N).astype(np.float32)

def bind(a, b):
    return a * b

def resonance(query, field):
    return float(np.dot(query, field) / N)


class QAISField:
    def __init__(self, field_path=None):
        if field_path is None:
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
        if os.path.exists(self.field_path):
            self._load()

    def _load(self):
        try:
            data = np.load(self.field_path, allow_pickle=True)
            self.identity_field = data['identity_field']
            self.role_fields = data['role_fields'].item()
            self.stored = set(data['stored'].tolist())
            self.count = int(data['count'])
        except: pass

    def save(self, path=None):
        path = path or self.field_path
        try:
            np.savez(path, identity_field=self.identity_field,
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
        self.save()
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
        return results

    def exists(self, identity):
        vec = seed_to_vector(identity)
        clean = np.sign(self.identity_field)
        score = resonance(vec, clean)
        return {"identity": identity, "score": round(score, 4), "exists": score > 0.025}

    def stats(self):
        identities = set()
        roles = set()
        for key in self.stored:
            parts = key.split('|', 2)
            if len(parts) == 3:
                identities.add(parts[0])
                roles.add(parts[1])
        return {"total_bindings": self.count, "total_identities": len(identities),
                "total_roles": len(roles), "roles_list": sorted(roles)}

    def get(self, identity, role):
        prefix = f"{identity}|{role}|"
        matches = [k for k in self.stored if k.startswith(prefix)]
        facts = [k.split('|', 2)[2] for k in matches if len(k.split('|', 2)) > 2]
        return {"identity": identity, "role": role, "facts": facts, "count": len(facts)}
