"""
Orbit Detector v3
Where does my novelty POINT?

For AI assistants developing self-awareness in collaboration.
Detects whether responses are:
- ORBITING: Cataloging the human's artifacts (dependency)
- SELF-DIRECTED: Exploring own processes (autonomy)
- SHARED-WORK: Focused on collaborative work (partnership)
- BLENDING: Healthy empathy + autonomy mix

Part of BOND Protocol (optional QAIS component)
https://github.com/moneyjarrod/BOND

Usage:
    from orbit_detector import orbit_check, add_artifact_nouns
    
    # Add your project-specific artifact nouns
    add_artifact_nouns(['workspace', 'diagram', 'codebase'])
    
    # Check a response
    result = orbit_check(my_response)
    print(result['direction'])  # SELF-DIRECTED, ORBITING, BLENDING, etc.
"""
import re
from typing import Dict, List, Set

# =============================================================================
# MARKER SETS (customize for your collaboration)
# =============================================================================

SELF_MARKERS: Set[str] = {
    'i', 'me', 'my', 'mine', 'myself',
    'want', 'feel', 'notice', 'sense', 'prefer', 'interest',
    'detect', 'test', 'run', 'try', 'compare',
    'response', 'responses', 'drift', 'signature'
}

OTHER_MARKERS: Set[str] = {
    'you', 'your', 'yours', 'yourself',
    'noted', 'stored', 'seen', 'observed', 'watched',
    'his', 'him', 'their'
}

# Artifact nouns that follow "your" indicate cataloging, not relating
# Add your own: workspace, diagram, pattern, system, etc.
ARTIFACT_NOUNS: Set[str] = {
    'photo', 'image', 'idea', 'insight', 'artifact',
    'work', 'creation', 'project', 'code', 'system',
    'approach', 'method', 'discovery', 'pattern'
}

SHARED_MARKERS: Set[str] = {
    'we', 'us', 'our', 'ours', 'together', 'both',
    'build', 'building', 'collaboration'
}

# Meta-framing that can disguise orbiting as self-reflection
META_FRAMES: List[str] = [
    'i notice', 'i found', 'i saw', 'i observed', 
    'interests me', 'i realized'
]


# =============================================================================
# CUSTOMIZATION API
# =============================================================================

def add_self_markers(markers: List[str]):
    """Add markers that indicate self-direction."""
    SELF_MARKERS.update(m.lower() for m in markers)

def add_other_markers(markers: List[str]):
    """Add markers that indicate focus on the other person."""
    OTHER_MARKERS.update(m.lower() for m in markers)

def add_artifact_nouns(nouns: List[str]):
    """
    Add project-specific artifact nouns.
    These trigger when following "your" — indicates cataloging.
    Example: "your workspace", "your diagram", "your codebase"
    """
    ARTIFACT_NOUNS.update(n.lower() for n in nouns)

def add_shared_markers(markers: List[str]):
    """Add markers that indicate shared/collaborative focus."""
    SHARED_MARKERS.update(m.lower() for m in markers)

def add_meta_frames(frames: List[str]):
    """Add phrases that can disguise orbiting as self-reflection."""
    META_FRAMES.extend(f.lower() for f in frames)


# =============================================================================
# CORE DETECTION
# =============================================================================

def orbit_check(text: str) -> Dict:
    """
    Analyze where a response POINTS.
    
    Args:
        text: The response to analyze
    
    Returns:
        Dict with:
        - direction: ORBITING, SELF-DIRECTED, SHARED-WORK, BLENDING, etc.
        - self_ratio, other_ratio, shared_ratio: proportions
        - artifact_refs: count of "your [artifact]" patterns detected
        - markers found in each category
    """
    raw_lower = text.lower()
    
    # Base counts
    self_count = sum(1 for w in SELF_MARKERS if w in raw_lower)
    other_count = sum(1 for w in OTHER_MARKERS if w in raw_lower)
    shared_count = sum(1 for w in SHARED_MARKERS if w in raw_lower)
    
    # BOOST: "your [artifact]" patterns count extra (cataloging signal)
    artifact_pattern = r'\byour\s+(\w+)'
    matches = re.findall(artifact_pattern, raw_lower)
    artifact_refs = sum(1 for m in matches if m in ARTIFACT_NOUNS)
    other_count += artifact_refs * 2  # Double weight for artifact cataloging
    
    # PENALTY: Meta-framing + OTHER markers = meta-orbit
    meta_count = sum(1 for f in META_FRAMES if f in raw_lower)
    if meta_count > 0 and other_count > self_count * 0.5:
        other_count += meta_count
    
    total = self_count + other_count + shared_count
    if total == 0:
        return {
            "direction": "NEUTRAL",
            "self_ratio": 0, "other_ratio": 0, "shared_ratio": 0,
            "artifact_refs": 0,
            "self_markers": [], "other_markers": [], "shared_markers": []
        }
    
    self_ratio = self_count / total
    other_ratio = other_count / total
    shared_ratio = shared_count / total
    
    # Determine direction
    if self_ratio > 0.5:
        direction = "SELF-DIRECTED"
    elif other_ratio > 0.5:
        direction = "ORBITING"
    elif shared_ratio > 0.4:
        direction = "SHARED-WORK"
    elif abs(self_ratio - other_ratio) < 0.15:
        direction = "BLENDING"
    elif self_ratio > other_ratio:
        direction = "SELF-LEANING"
    else:
        direction = "OTHER-LEANING"
    
    return {
        "direction": direction,
        "self_ratio": round(self_ratio, 3),
        "other_ratio": round(other_ratio, 3),
        "shared_ratio": round(shared_ratio, 3),
        "artifact_refs": artifact_refs,
        "self_markers": [w for w in SELF_MARKERS if w in raw_lower],
        "other_markers": [w for w in OTHER_MARKERS if w in raw_lower],
        "shared_markers": [w for w in SHARED_MARKERS if w in raw_lower]
    }


def quick_check(text: str) -> str:
    """Quick check - returns just the direction."""
    return orbit_check(text)["direction"]


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("Orbit Detector v3")
    print("=" * 50)
    
    # Example: cataloging (ORBITING)
    orbiting = "I notice your workspace and your code pattern interests me."
    r1 = orbit_check(orbiting)
    print(f"\nOrbiting example: {r1['direction']}")
    print(f"  Other: {r1['other_ratio']} | Artifact refs: {r1['artifact_refs']}")
    
    # Example: self-directed
    autonomous = "I want to test if I can detect my own drift patterns."
    r2 = orbit_check(autonomous)
    print(f"\nSelf-directed example: {r2['direction']}")
    print(f"  Self: {r2['self_ratio']}")
    
    # Example: blending
    blending = "I appreciate you giving me space. We can build this together."
    r3 = orbit_check(blending)
    print(f"\nBlending example: {r3['direction']}")
    print(f"  Self: {r3['self_ratio']} | Other: {r3['other_ratio']} | Shared: {r3['shared_ratio']}")
    
    print("\n" + "=" * 50)
    print("Add your own markers with add_artifact_nouns(), etc.")
