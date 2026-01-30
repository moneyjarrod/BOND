"""
Session Heat Map
Tracks concept activity for smarter crystallization.

"What did we actually touch, not what do I think we touched."

Part of BOND Protocol | Session 64
"""

import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class ConceptTouch:
    """Single touch record for a concept."""
    count: int = 0
    first_touch: float = 0.0
    last_touch: float = 0.0
    contexts: List[str] = field(default_factory=list)  # Why it was touched

class SessionHeatMap:
    """
    Tracks concept activity during a session.
    Resets each session (not persistent like QAIS).
    
    Usage:
        heatmap = SessionHeatMap()
        heatmap.touch("mining", "discussed depth merging")
        heatmap.touch("FPRS", "boundary question")
        heatmap.touch("mining", "wrote test code")
        
        hot = heatmap.get_hot(top_k=5)
        # [("mining", 2, "recently active"), ("FPRS", 1, "touched once")]
    """
    
    def __init__(self):
        self.concepts: Dict[str, ConceptTouch] = defaultdict(ConceptTouch)
        self.session_start = time.time()
    
    def touch(self, concept: str, context: str = "") -> Dict:
        """
        Mark a concept as touched.
        
        Args:
            concept: The concept name (e.g., "mining", "FPRS")
            context: Optional context for why (e.g., "discussed depth merging")
        
        Returns:
            Current stats for this concept
        """
        concept = concept.lower()
        now = time.time()
        
        entry = self.concepts[concept]
        if entry.count == 0:
            entry.first_touch = now
        entry.count += 1
        entry.last_touch = now
        if context:
            entry.contexts.append(context)
        
        return {
            "concept": concept,
            "count": entry.count,
            "age_seconds": round(now - entry.first_touch, 1)
        }
    
    def touch_multiple(self, concepts: List[str], context: str = "") -> Dict:
        """Touch multiple concepts at once."""
        results = []
        for c in concepts:
            results.append(self.touch(c, context))
        return {"touched": len(results), "concepts": results}
    
    def get_hot(self, top_k: int = 10, min_count: int = 1) -> List[Dict]:
        """
        Get hottest concepts by activity.
        
        Scoring: count * recency_weight
        - Recent touches weighted higher
        - Multiple touches weighted higher
        
        Returns:
            List of hot concepts with stats
        """
        now = time.time()
        scored = []
        
        for concept, entry in self.concepts.items():
            if entry.count < min_count:
                continue
            
            # Recency: touches in last 5 min worth 2x, last 15 min worth 1.5x
            age_minutes = (now - entry.last_touch) / 60
            if age_minutes < 5:
                recency = 2.0
            elif age_minutes < 15:
                recency = 1.5
            elif age_minutes < 30:
                recency = 1.0
            else:
                recency = 0.5
            
            score = entry.count * recency
            
            scored.append({
                "concept": concept,
                "count": entry.count,
                "score": round(score, 2),
                "last_touch_mins": round(age_minutes, 1),
                "contexts": entry.contexts[-3:]  # Last 3 contexts
            })
        
        # Sort by score descending
        scored.sort(key=lambda x: -x["score"])
        return scored[:top_k]
    
    def get_cold(self, top_k: int = 5) -> List[Dict]:
        """
        Get concepts touched early but not recently.
        Might be forgotten but still relevant.
        """
        now = time.time()
        candidates = []
        
        for concept, entry in self.concepts.items():
            age_minutes = (now - entry.last_touch) / 60
            if age_minutes > 15:  # Not touched in 15+ minutes
                candidates.append({
                    "concept": concept,
                    "count": entry.count,
                    "last_touch_mins": round(age_minutes, 1),
                    "contexts": entry.contexts[-2:]
                })
        
        # Sort by last touch (oldest first)
        candidates.sort(key=lambda x: -x["last_touch_mins"])
        return candidates[:top_k]
    
    def get_stats(self) -> Dict:
        """Session heat map statistics."""
        now = time.time()
        session_minutes = (now - self.session_start) / 60
        
        total_touches = sum(e.count for e in self.concepts.values())
        
        return {
            "session_minutes": round(session_minutes, 1),
            "unique_concepts": len(self.concepts),
            "total_touches": total_touches,
            "hot_concepts": [c["concept"] for c in self.get_hot(5)]
        }
    
    def clear(self) -> Dict:
        """Reset heat map for new session."""
        count = len(self.concepts)
        self.concepts.clear()
        self.session_start = time.time()
        return {"cleared": count, "status": "reset"}
    
    def for_chunk(self) -> Dict:
        """
        Get heat map summary formatted for {Chunk} output.
        
        Returns structured data for crystallization.
        """
        hot = self.get_hot(10)
        cold = self.get_cold(5)
        stats = self.get_stats()
        
        return {
            "session_minutes": stats["session_minutes"],
            "total_concepts": stats["unique_concepts"],
            "hot": [
                {"concept": h["concept"], "count": h["count"], "why": h["contexts"]}
                for h in hot
            ],
            "cold_but_touched": [c["concept"] for c in cold],
            "summary": f"{stats['unique_concepts']} concepts, {stats['total_touches']} touches, hot: {', '.join(c['concept'] for c in hot[:5])}"
        }


# =============================================================================
# CONVENIENCE API
# =============================================================================

_HEATMAP: Optional[SessionHeatMap] = None

def get_heatmap() -> SessionHeatMap:
    """Get or create the global heat map."""
    global _HEATMAP
    if _HEATMAP is None:
        _HEATMAP = SessionHeatMap()
    return _HEATMAP

def touch(concept: str, context: str = "") -> Dict:
    """Touch a concept."""
    return get_heatmap().touch(concept, context)

def touch_multiple(concepts: List[str], context: str = "") -> Dict:
    """Touch multiple concepts."""
    return get_heatmap().touch_multiple(concepts, context)

def hot(top_k: int = 10) -> List[Dict]:
    """Get hot concepts."""
    return get_heatmap().get_hot(top_k)

def cold(top_k: int = 5) -> List[Dict]:
    """Get cold concepts."""
    return get_heatmap().get_cold(top_k)

def stats() -> Dict:
    """Get stats."""
    return get_heatmap().get_stats()

def for_chunk() -> Dict:
    """Get chunk-formatted summary."""
    return get_heatmap().for_chunk()

def clear() -> Dict:
    """Reset for new session."""
    return get_heatmap().clear()


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    import time as t
    
    print("=" * 60)
    print("Session Heat Map Test")
    print("=" * 60)
    
    hm = SessionHeatMap()
    
    # Simulate session activity
    hm.touch("mining", "discussed depth merging")
    hm.touch("FPRS", "boundary question")
    hm.touch("mining", "wrote test code")
    hm.touch("ASDF", "terrain formula")
    hm.touch("mining", "optimization")
    hm.touch("passthrough", "v5 upgrade")
    hm.touch("passthrough", "fact resonance")
    
    print("\n[Hot Concepts]")
    for h in hm.get_hot(5):
        print(f"  {h['concept']}: {h['count']}x, score={h['score']}, contexts={h['contexts']}")
    
    print("\n[Stats]")
    print(f"  {hm.get_stats()}")
    
    print("\n[For Chunk]")
    chunk = hm.for_chunk()
    print(f"  Summary: {chunk['summary']}")
    
    print("\n" + "=" * 60)
