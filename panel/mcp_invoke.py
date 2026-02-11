"""
BOND MCP Invoke — Runs QAIS/ISS/Limbic tools from panel.
Called by: node server.js via child_process.execFile
Args: system tool [input]
Output: JSON to stdout
"""
import json
import sys
import os
import numpy as np

# Paths resolve from BOND_ROOT environment variable
BOND_ROOT = os.environ.get('BOND_ROOT', os.path.join(os.path.dirname(__file__), '..'))
QAIS_FIELD_PATH = os.environ.get('QAIS_FIELD_PATH', os.path.join(BOND_ROOT, 'data', 'qais_field.npz'))
ISS_PATH = os.environ.get('ISS_PATH', os.path.join(BOND_ROOT, 'ISS'))
QAIS_PATH = os.environ.get('QAIS_PATH', os.path.join(BOND_ROOT, 'QAIS'))

# ─── QAIS Tools ────────────────────────────────────────────

def _get_qais():
    """Load QAISField from qais_core."""
    sys.path.insert(0, QAIS_PATH)
    from qais_core import QAISField
    return QAISField(field_path=QAIS_FIELD_PATH)

def qais_stats():
    """Full QAIS field stats."""
    try:
        q = _get_qais()
        result = q.stats()
        result["status"] = "active"
        return result
    except Exception as e:
        return {"error": str(e)}

def qais_exists(input_str):
    """Check if identity exists in QAIS field."""
    try:
        q = _get_qais()
        identity = input_str.strip()
        result = q.exists(identity)
        bindings = [k for k in q.stored if k.startswith(f"{identity}|")]
        result["binding_count"] = len(bindings)
        result["bindings"] = bindings[:20]
        return result
    except Exception as e:
        return {"error": str(e)}

def qais_resonate(input_str):
    """Resonate against QAIS field. Input: identity|role|candidate1,candidate2,..."""
    try:
        q = _get_qais()
        parts = input_str.split('|', 2)
        if len(parts) < 3:
            return {"error": "Format: identity|role|candidate1,candidate2,..."}
        identity, role, candidates_str = parts
        candidates = [c.strip() for c in candidates_str.split(',')]
        results = q.resonate(identity.strip(), role.strip(), candidates)
        return {"identity": identity, "role": role, "results": results}
    except Exception as e:
        return {"error": str(e)}

# ─── ISS Tools ─────────────────────────────────────────────

def iss_analyze(input_str):
    """Analyze text with ISS semantic forces."""
    sys.path.insert(0, ISS_PATH)
    try:
        from iss_core import analyze
        result = analyze(input_str.strip())
        return {
            "text": input_str.strip()[:100],
            "G": result['G'],
            "P": result['P'],
            "E": result['E'],
            "r": result['r'],
            "gap": result['gap'],
            "diagnosis": result.get('diagnosis', ''),
        }
    except Exception as e:
        return {"error": str(e)}

def iss_compare(input_str):
    """Compare multiple texts. Input: one text per line."""
    sys.path.insert(0, ISS_PATH)
    try:
        from iss_core import analyze
        texts = [t.strip() for t in input_str.strip().split('\n') if t.strip()]
        if len(texts) < 2:
            return {"error": "Need 2+ texts (one per line)"}
        
        results = []
        for text in texts:
            r = analyze(text)
            results.append({
                "text": text[:80],
                "G": r['G'],
                "P": r['P'],
                "E": r['E'],
                "gap": r['gap'],
                "diagnosis": r.get('diagnosis', ''),
            })
        return {"comparisons": results}
    except Exception as e:
        return {"error": str(e)}

def iss_status():
    """ISS system status."""
    return {
        "status": "active",
        "version": "2.0",
        "forces": "G (mechanistic), P (prescriptive), E (coherence), r (residual)",
        "gap_formula": "α‖r‖ + β|‖g‖-‖p‖| + γ(1-E)",
        "training": "38 G + 41 P sentences, frozen",
    }

# ─── EAP Tools ─────────────────────────────────────────────

def eap_schema():
    """Return EAP 10D schema."""
    return {
        "dimensions": 10,
        "schema": [
            "valence (-1 to 1)",
            "arousal (0 to 1)",
            "confidence (0 to 1)",
            "urgency (0 to 1)",
            "connection (0 to 1)",
            "curiosity (0 to 1)",
            "frustration (0 to 1)",
            "fatigue (0 to 1)",
            "wonder (0 to 1)",
            "trust (0 to 1)",
        ],
        "note": "Claude provides EAP from native read. Not invocable externally.",
    }

# ─── Limbic Tools ──────────────────────────────────────────

def limbic_status():
    """Limbic system status."""
    genome_path = os.path.join(ISS_PATH, "limbic_genome_10d.json")
    try:
        with open(genome_path) as f:
            genome = json.load(f)
        return {
            "status": "active",
            "fitness": genome.get("fitness", "unknown"),
            "genome_version": "v2.0 evolved",
            "inputs": "ISS(G,P,E,r,gap) + EAP(10D) + QAIS(familiarity)",
            "outputs": "S(salience), V(valence), T(threat), G(gate)",
        }
    except Exception as e:
        return {"error": str(e)}

def limbic_scan(input_str):
    """Run ISS on text, return forces (limbic proper needs EAP from Claude)."""
    result = iss_analyze(input_str)
    if "error" in result:
        return result
    result["note"] = "Full limbic requires Claude's EAP read. Showing ISS forces only."
    return result

# ─── Dispatch ──────────────────────────────────────────────

def qais_store(input_str):
    """Store identity|role|fact binding in QAIS field."""
    try:
        q = _get_qais()
        parts = input_str.split('|', 2)
        if len(parts) < 3:
            return {"error": "Format: identity|role|fact"}
        identity, role, fact = parts[0].strip(), parts[1].strip(), parts[2].strip()
        result = q.store(identity, role, fact)
        return result
    except Exception as e:
        return {"error": str(e)}

def qais_get(input_str):
    """Get fact for identity|role from QAIS field."""
    try:
        q = _get_qais()
        parts = input_str.split('|', 1)
        if len(parts) < 2:
            return {"error": "Format: identity|role"}
        identity, role = parts[0].strip(), parts[1].strip()
        return q.get(identity, role)
    except Exception as e:
        return {"error": str(e)}

# ─── Perspective Tools ─────────────────────────────────────

def _get_perspective_field(perspective):
    """Load isolated QAISField for a perspective entity."""
    perspectives_dir = os.path.join(BOND_ROOT, 'data', 'perspectives')
    os.makedirs(perspectives_dir, exist_ok=True)
    field_path = os.path.join(perspectives_dir, f"{perspective}.npz")
    sys.path.insert(0, QAIS_PATH)
    from qais_core import QAISField
    return QAISField(field_path=field_path)

def perspective_store(input_str):
    """Store seed into perspective's isolated field. Input: perspective|seed_title|seed_content"""
    try:
        parts = input_str.split('|', 2)
        if len(parts) < 3:
            return {"error": "Format: perspective|seed_title|seed_content"}
        perspective, seed_title, seed_content = parts[0].strip(), parts[1].strip(), parts[2].strip()
        q = _get_perspective_field(perspective)
        result = q.store(perspective, seed_title, seed_content)
        return {"perspective": perspective, "seed": seed_title, "stored": True, "field_count": q.count}
    except Exception as e:
        return {"error": str(e)}

TOOLS = {
    "qais": {
        "stats": lambda _: qais_stats(),
        "exists": qais_exists,
        "resonate": qais_resonate,
        "store": qais_store,
        "get": qais_get,
        "perspective_store": perspective_store,
    },
    "iss": {
        "analyze": iss_analyze,
        "compare": iss_compare,
        "status": lambda _: iss_status(),
    },
    "eap": {
        "schema": lambda _: eap_schema(),
    },
    "limbic": {
        "status": lambda _: limbic_status(),
        "scan": limbic_scan,
    },
}

def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: mcp_invoke.py <s> <tool> [input]"}))
        return

    system = sys.argv[1]
    tool = sys.argv[2]
    input_str = sys.argv[3] if len(sys.argv) > 3 else ""

    if system not in TOOLS:
        print(json.dumps({"error": f"Unknown system: {system}"}))
        return
    if tool not in TOOLS[system]:
        print(json.dumps({"error": f"Unknown tool: {system}/{tool}", "available": list(TOOLS[system].keys())}))
        return

    result = TOOLS[system][tool](input_str)
    print(json.dumps(result))

if __name__ == "__main__":
    main()
