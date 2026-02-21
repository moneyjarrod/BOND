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

def _log_seed_decision(action, perspective, seed, reason=None, session=None, tracker_stats=None):
    """Append to seed_decisions.jsonl. S100: Automatic logging."""
    from datetime import datetime
    try:
        entry = {"action": action, "perspective": perspective, "seed": seed, "timestamp": datetime.now().isoformat()}
        if reason: entry["reason"] = reason
        if session: entry["session"] = session
        if tracker_stats: entry["tracker_stats"] = tracker_stats
        log_path = os.path.join(BOND_ROOT, 'data', 'seed_decisions.jsonl')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception:
        pass

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

def perspective_crystal_restore(input_str):
    """Restore all crystal momentum from perspective's local crystal field. Input: perspective name"""
    try:
        perspective = input_str.strip()
        crystal_dir = os.path.join(BOND_ROOT, 'data', 'perspectives')
        field_path = os.path.join(crystal_dir, f"{perspective}_crystal.npz")
        if not os.path.exists(field_path):
            return {"perspective": perspective, "sessions": [], "field_count": 0}
        sys.path.insert(0, QAIS_PATH)
        from qais_core import QAISField
        q = QAISField(field_path=field_path)
        sessions = []
        # Crystal stores as Session{N}|momentum|<text>, Session{N}|context|<text>, etc.
        seen = set()
        for key in sorted(q.stored):
            parts = key.split('|', 2)
            if len(parts) < 2:
                continue
            session_id = parts[0]
            if session_id in seen:
                continue
            seen.add(session_id)
            entry = {"session": session_id}
            for role in ['momentum', 'context', 'tags', 'insight']:
                result = q.get(session_id, role)
                if result.get('facts'):
                    entry[role] = result['facts'][0]
            sessions.append(entry)
        return {"perspective": perspective, "sessions": sessions, "field_count": q.count}
    except Exception as e:
        return {"error": str(e)}

def perspective_remove(input_str):
    """Remove seed from perspective's isolated field. Input: perspective|seed_title|seed_content"""
    try:
        parts = input_str.split('|', 2)
        if len(parts) < 3:
            return {"error": "Format: perspective|seed_title|seed_content"}
        perspective, seed_title, seed_content = parts[0].strip(), parts[1].strip(), parts[2].strip()
        q = _get_perspective_field(perspective)
        result = q.remove(perspective, seed_title, seed_content)
        return {"perspective": perspective, "seed": seed_title, "removed": result["status"] == "removed", "field_count": q.count, "detail": result["status"]}
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
        "perspective_remove": perspective_remove,
        "perspective_crystal_restore": perspective_crystal_restore,
    },
    "iss": {
        "analyze": iss_analyze,
        "compare": iss_compare,
        "status": lambda _: iss_status(),
    },
    "eap": {
        "schema": lambda _: eap_schema(),
    },

}

def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: mcp_invoke.py <system> <tool> [input]"}))
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
