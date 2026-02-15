"""
BOND MCP Stats — Reads QAIS/ISS/Gate state and outputs JSON for panel sidecar.
Called by: node server.js via child_process.execFile
Output: JSON to stdout
"""
import json
import sys
import os

# Paths resolve from BOND_ROOT environment variable
BOND_ROOT = os.environ.get('BOND_ROOT', os.path.join(os.path.dirname(__file__), '..'))

def qais_stats():
    """Read QAIS field file and return stats."""
    field_path = os.environ.get('QAIS_FIELD_PATH', os.path.join(BOND_ROOT, 'data', 'qais_field.npz'))
    try:
        import numpy as np
        if not os.path.exists(field_path):
            return {"status": "offline", "error": "No field file"}
        data = np.load(field_path, allow_pickle=True)
        stored = set(data['stored'].tolist())
        count = int(data['count'])
        role_fields = data['role_fields'].item()
        
        # Count unique identities and facts
        identities = set()
        facts = set()
        for key in stored:
            parts = key.split('|', 2)
            if len(parts) == 3:
                identities.add(parts[0])
                facts.add(parts[2])
        
        return {
            "status": "active",
            "total_bindings": count,
            "total_identities": len(identities),
            "total_roles": len(role_fields),
            "roles": list(role_fields.keys()),
            "facts_indexed": len(facts)
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def iss_stats():
    """ISS status from known config."""
    return {
        "status": "active",
        "version": "2.0",
        "dimensions": "G, P, E, r, gap"
    }

def eap_stats():
    """EAP status — 10D schema."""
    return {
        "status": "active",
        "dimensions": 10,
        "schema": "valence, arousal, confidence, urgency, connection, curiosity, frustration, fatigue, wonder, trust"
    }

def limbic_stats():
    """Limbic evolver status."""
    return {
        "status": "active",
        "fitness": 0.017,
        "genome": "v2.0 evolved"
    }

def perspective_crystal_stats(perspective_name):
    """Read crystal count from perspective's local crystal field."""
    field_path = os.path.join(BOND_ROOT, 'data', 'perspectives', f"{perspective_name}_crystal.npz")
    try:
        import numpy as np
        if not os.path.exists(field_path):
            return {"status": "empty", "count": 0, "perspective": perspective_name}
        data = np.load(field_path, allow_pickle=True)
        count = int(data['count'])
        return {"status": "active", "count": count, "perspective": perspective_name}
    except Exception as e:
        return {"status": "error", "count": 0, "error": str(e)}

def main():
    system = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    handlers = {
        "qais": qais_stats,
        "iss": iss_stats,
        "eap": eap_stats,
        "limbic": limbic_stats,
    }
    
    if system == "perspective_crystal":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        print(json.dumps(perspective_crystal_stats(name)))
    elif system == "all":
        results = {name: fn() for name, fn in handlers.items()}
        print(json.dumps(results))
    elif system in handlers:
        print(json.dumps(handlers[system]()))
    else:
        print(json.dumps({"error": f"Unknown system: {system}"}))

if __name__ == "__main__":
    main()
