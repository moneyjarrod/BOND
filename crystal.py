"""
Crystal: Persistent Crystallization for BOND
"Chunk hopes. Crystal ensures."

Takes session state, extracts key concepts, stores to QAIS field.
Returns what was persisted for confirmation.

Session 64 | J-Dub & Claude | 2026-01-30
"""

import re
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# =============================================================================
# CONCEPT EXTRACTION
# =============================================================================

# High-value terms that indicate important concepts
SIGNAL_WORDS = {
    'breakthrough', 'insight', 'fixed', 'solved', 'proven', 'works',
    'principle', 'architecture', 'pattern', 'protocol', 'rule',
    'bonfire', 'milestone', 'complete', 'done', 'verified'
}

# Skip these common words
STOPWORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'to', 'of',
    'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
    'this', 'that', 'these', 'those', 'it', 'its', 'and', 'but', 'or',
    'if', 'then', 'else', 'when', 'where', 'why', 'how', 'what', 'which',
    'who', 'whom', 'all', 'each', 'every', 'some', 'any', 'no', 'not',
    'just', 'only', 'also', 'very', 'too', 'more', 'most', 'less', 'least'
}


def extract_concepts(text: str, max_concepts: int = 10) -> List[Tuple[str, int]]:
    """
    Extract key concepts from text with importance scoring.
    Returns list of (concept, score) tuples, sorted by score descending.
    """
    # Find all words and phrases
    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text)
    
    # Count frequencies, skip stopwords
    freq = {}
    for word in words:
        w = word.lower()
        if len(w) > 2 and w not in STOPWORDS:
            freq[w] = freq.get(w, 0) + 1
    
    # Score: frequency + signal word bonus
    scored = []
    for word, count in freq.items():
        score = count
        if word in SIGNAL_WORDS:
            score += 5  # Boost important terms
        # Boost capitalized terms (likely proper nouns/acronyms)
        if any(w.isupper() or w[0].isupper() for w in [word]):
            score += 2
        scored.append((word, score))
    
    # Sort by score, take top N
    scored.sort(key=lambda x: -x[1])
    return scored[:max_concepts]


def extract_sections(text: str) -> Dict[str, str]:
    """
    Extract labeled sections from crystallization text.
    Looks for patterns like "### Completed", "**State:**", etc.
    """
    sections = {}
    
    # Pattern: ### Header or **Header:** or Header:
    patterns = [
        (r'###\s*(\w+)', r'###\s*\w+\s*\n(.*?)(?=###|\Z)'),
        (r'\*\*(\w+):\*\*', r'\*\*\w+:\*\*\s*(.*?)(?=\*\*|\Z)'),
    ]
    
    for header_pat, content_pat in patterns:
        headers = re.findall(header_pat, text, re.IGNORECASE)
        contents = re.findall(content_pat, text, re.DOTALL | re.IGNORECASE)
        for h, c in zip(headers, contents):
            sections[h.lower()] = c.strip()[:500]  # Cap length
    
    return sections


# =============================================================================
# MOMENTUM SEED GENERATION
# =============================================================================

def generate_momentum(
    session_num: int,
    completed: List[str],
    state: str,
    next_task: str,
    flow: str = "good"
) -> str:
    """
    Generate momentum seed in standard format.
    
    Format: "S[N] complete, [state], next is [task], flow is [quality]"
    """
    completed_str = ", ".join(completed[:3])  # Cap at 3 items
    return f"S{session_num} {completed_str}, {state}, next is {next_task}, flow is {flow}"


# =============================================================================
# CRYSTAL PROCESSOR
# =============================================================================

class Crystal:
    """
    Processes crystallization and prepares QAIS storage operations.
    
    Does NOT directly call QAIS (that's Claude's job via MCP).
    Instead, returns structured data for Claude to store.
    """
    
    def __init__(self, session_num: int, project: str = "BOND"):
        self.session_num = session_num
        self.project = project
        self.timestamp = datetime.now().isoformat()
    
    def process(self, chunk_text: str, context: Optional[str] = None) -> Dict:
        """
        Process crystallization text and return storage operations.
        
        Args:
            chunk_text: The {Chunk} style crystallization text
            context: Optional additional context (e.g., "QAIS v3.1 work")
        
        Returns:
            Dict with:
            - concepts: List of extracted concepts for heatmap
            - momentum: Formatted momentum seed
            - insights: List of (identity, role, fact) tuples to store
            - summary: Human-readable summary
        """
        result = {
            'session': self.session_num,
            'project': self.project,
            'timestamp': self.timestamp,
            'concepts': [],
            'momentum': None,
            'insights': [],
            'summary': ''
        }
        
        # Extract concepts
        concepts = extract_concepts(chunk_text)
        result['concepts'] = [c[0] for c in concepts]
        
        # Extract sections
        sections = extract_sections(chunk_text)
        
        # Build momentum seed
        completed = []
        if 'completed' in sections:
            # Parse bullet points
            completed = re.findall(r'[-*]\s*(.+?)(?:\n|$)', sections['completed'])
        elif 'done' in sections:
            completed = re.findall(r'[-*]\s*(.+?)(?:\n|$)', sections['done'])
        
        state = sections.get('state', sections.get('current', 'in progress'))
        next_task = sections.get('next', sections.get('open', 'continue'))
        
        # Clean up extracted text
        if isinstance(state, str) and len(state) > 50:
            state = state[:50] + "..."
        if isinstance(next_task, str) and len(next_task) > 50:
            next_task = next_task[:50] + "..."
        
        result['momentum'] = generate_momentum(
            self.session_num,
            completed[:3] if completed else ['work'],
            str(state)[:50],
            str(next_task)[:50]
        )
        
        # Generate insights to store
        # Session momentum
        result['insights'].append((
            f"Session{self.session_num}",
            "momentum",
            result['momentum']
        ))
        
        # Top concepts with context
        if context:
            result['insights'].append((
                f"Session{self.session_num}",
                "context", 
                context[:200]
            ))
        
        # If we found key insights in the text
        if 'insight' in sections or 'key' in sections:
            insight_text = sections.get('insight', sections.get('key', ''))
            if insight_text:
                result['insights'].append((
                    f"Session{self.session_num}",
                    "insight",
                    insight_text[:200]
                ))
        
        # Build summary
        result['summary'] = self._build_summary(result)
        
        return result
    
    def _build_summary(self, result: Dict) -> str:
        """Build human-readable summary of what will be stored."""
        lines = [
            f"## {{Crystal}} — Session {self.session_num}",
            f"**Timestamp:** {self.timestamp}",
            "",
            "### Concepts (for heatmap)",
            ", ".join(result['concepts'][:10]),
            "",
            "### Momentum Seed",
            f"`{result['momentum']}`",
            "",
            "### QAIS Storage Operations",
        ]
        
        for identity, role, fact in result['insights']:
            lines.append(f"- `{identity}|{role}`: {fact[:60]}...")
        
        return "\n".join(lines)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def crystallize(
    chunk_text: str,
    session_num: int,
    project: str = "BOND",
    context: Optional[str] = None
) -> Dict:
    """
    One-shot crystallization processing.
    
    Example:
        result = crystallize(chunk_output, session_num=64, project="GSG")
        # Claude then stores result['insights'] to QAIS
        # Claude then touches result['concepts'] to heatmap
    """
    crystal = Crystal(session_num, project)
    return crystal.process(chunk_text, context)


def format_for_claude(result: Dict) -> str:
    """
    Format crystal result as instructions for Claude.
    Returns text Claude can use to execute QAIS operations.
    """
    lines = [result['summary'], "", "### Execute:", ""]
    
    # Heatmap touch
    concepts_str = json.dumps(result['concepts'][:10])
    lines.append(f"heatmap_touch({concepts_str}, \"Session {result['session']} crystal\")")
    lines.append("")
    
    # QAIS stores
    for identity, role, fact in result['insights']:
        lines.append(f"qais_store(\"{identity}\", \"{role}\", \"{fact}\")")
    
    return "\n".join(lines)


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    # Test with sample chunk
    sample_chunk = """
    ## {Chunk} — Session 64 Crystallization
    
    ### Completed
    - COUNTER.md created (response schema spec)
    - COMMANDS.md full protocol definitions
    - {ArtD} recovered and documented
    
    ### Key Insight
    Counter is CORE BOND - everything else extends it.
    
    ### Current State
    BOND package clean, ready for use
    
    ### Next
    Test {Crystal} command
    """
    
    result = crystallize(sample_chunk, session_num=64, project="GSG", context="BOND cleanup session")
    print(format_for_claude(result))
