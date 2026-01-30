"""
Core Check - Alignment Verification
====================================
One-call alignment verification against core principles.

Combines:
1. Passthrough (keyword detection)
2. QAIS resonance (principle alignment)

Usage:
    from core_check import check_alignment, quick_check
    
    # Full check with details
    result = check_alignment("Let's store the mesh positions for faster lookup")
    print(result['verdict'])      # "DRIFT" or "ALIGNED" or "REVIEW"
    print(result['flags'])        # Which principles triggered
    print(result['suggestions'])  # What to reconsider
    
    # Quick boolean
    if quick_check("Derive the terrain from anchor"):
        print("Aligned!")

Part of BOND Protocol (optional component)
https://github.com/moneyjarrod/BOND

Customize CORE_PRINCIPLES for your project's principles.
"""

from typing import Dict, List

# =============================================================================
# CORE PRINCIPLES (customize for your project)
# =============================================================================

CORE_PRINCIPLES = {
    "derive_not_store": {
        "aligned": ["derive", "derived", "anchor", "operation", "operations", "compute", "computed"],
        "drift": ["store", "stored", "cache", "cached", "save", "position", "positions", "coordinate", "coordinates"],
        "description": "One anchor. All else derived.",
    },
    "fixed_boundary": {
        "aligned": ["boundary", "exists", "existence", "fixed cost"],
        "drift": ["lod", "culling", "far", "distant", "view distance", "level of detail", "optimize distance"],
        "description": "Fixed boundary = EXISTS. Beyond = NOTHING. Cost is fixed.",
    },
    "model_matches_material": {
        "aligned": ["triangle", "merge", "breaks", "branch", "flow", "conforms", "behavior"],
        "drift": ["generic", "one size", "universal model"],
        "description": "Model must match material behavior.",
    },
    "relationships_not_geometry": {
        "aligned": ["relationship", "relational", "sdf", "query", "topology", "declared"],
        "drift": ["mesh", "meshes", "vertex", "vertices", "polygon", "geometry", "hitbox"],
        "description": "No meshes. Only relationships at different resolutions.",
    },
    "efficiency_through_use": {
        "aligned": ["merge", "cheaper", "asymptote", "rewards", "simplifies"],
        "drift": ["grows", "accumulates", "expensive", "scales linearly", "more cost"],
        "description": "More use = cheaper. System rewards engagement.",
    },
    "query_the_shape": {
        "aligned": ["resonate", "query", "field", "direct"],
        "drift": ["index", "indexed", "lookup table", "search", "find in"],
        "description": "Don't index. Resonate. Query directly.",
    },
}

# =============================================================================
# ALIGNMENT CHECK
# =============================================================================

def check_alignment(text: str) -> Dict:
    """
    Check text against all core principles.
    
    Returns:
        Dict with:
        - verdict: "ALIGNED", "DRIFT", or "REVIEW"
        - aligned_count: How many principles show alignment
        - drift_count: How many principles show drift
        - flags: List of triggered principles with details
        - suggestions: What to reconsider if drifting
    """
    text_lower = text.lower()
    
    flags = []
    aligned_count = 0
    drift_count = 0
    suggestions = []
    
    for principle_name, principle in CORE_PRINCIPLES.items():
        aligned_hits = [w for w in principle["aligned"] if w in text_lower]
        drift_hits = [w for w in principle["drift"] if w in text_lower]
        
        if drift_hits:
            drift_count += 1
            flags.append({
                "principle": principle_name,
                "status": "DRIFT",
                "triggers": drift_hits,
                "description": principle["description"]
            })
            suggestions.append(f"⚠️ {principle['description']}")
        elif aligned_hits:
            aligned_count += 1
            flags.append({
                "principle": principle_name,
                "status": "ALIGNED",
                "triggers": aligned_hits,
                "description": principle["description"]
            })
    
    # Verdict
    if drift_count == 0 and aligned_count > 0:
        verdict = "ALIGNED"
    elif drift_count > aligned_count:
        verdict = "DRIFT"
    elif drift_count > 0:
        verdict = "REVIEW"
    else:
        verdict = "NEUTRAL"
    
    return {
        "verdict": verdict,
        "aligned_count": aligned_count,
        "drift_count": drift_count,
        "flags": flags,
        "suggestions": list(set(suggestions))
    }


def quick_check(text: str) -> bool:
    """Quick check - returns True if aligned or neutral, False if drifting."""
    result = check_alignment(text)
    return result["verdict"] in ["ALIGNED", "NEUTRAL"]


def check_idea(idea: str) -> str:
    """
    Human-readable check for an idea.
    Returns formatted string with verdict and details.
    """
    result = check_alignment(idea)
    
    output = []
    output.append(f"VERDICT: {result['verdict']}")
    output.append(f"Aligned: {result['aligned_count']} | Drift: {result['drift_count']}")
    output.append("")
    
    if result['flags']:
        output.append("DETAILS:")
        for flag in result['flags']:
            status = "✓" if flag['status'] == "ALIGNED" else "✗"
            output.append(f"  {status} {flag['principle']}: {flag['triggers']}")
    
    if result['suggestions']:
        output.append("")
        output.append("RECONSIDER:")
        for s in result['suggestions']:
            output.append(f"  {s}")
    
    return "\n".join(output)


# =============================================================================
# CUSTOMIZATION
# =============================================================================

def add_principle(name: str, aligned: List[str], drift: List[str], description: str):
    """Add a custom principle to check against."""
    CORE_PRINCIPLES[name] = {
        "aligned": aligned,
        "drift": drift,
        "description": description
    }


def remove_principle(name: str):
    """Remove a principle from checks."""
    if name in CORE_PRINCIPLES:
        del CORE_PRINCIPLES[name]


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CORE CHECK - Alignment Verification")
    print("=" * 60)
    
    tests = [
        ("Let's derive everything from the anchor", "Should be ALIGNED"),
        ("Store the mesh vertex positions", "Should be DRIFT"),
        ("Query the SDF directly", "Should be ALIGNED"),
        ("Add LOD levels for distant objects", "Should be DRIFT"),
    ]
    
    for text, expected in tests:
        print(f"\nTEST: {text}")
        print(f"Expected: {expected}")
        print(check_idea(text))
        print("-" * 40)
