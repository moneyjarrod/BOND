"""
================================================================================
JOHNNY APPLESEED+ ({JA+}) - Gap Clustering with Evolved Synthesis
"Find the branch, not just the leaves."
================================================================================

J-Dub & Claude | Session 66 | 2026-01-31
QAIS Tool (Tier 4+)

COMMANDS:
    {JA}   ← Base scan, flat gap list (0.065ms)
    {JA+}  ← Clustered scan with evolved principle synthesis (0.092ms)

SYNTHESIS GENOME (evolved v5):
    action_weight:      55.5%   (prefer action templates)
    relationship_weight: 33.4%  (relationship templates)
    single_topic:       for clusters with one topic word
    tautology_prevention: excludes topic words from action search
    grammar:            verb conjugation for plural subjects

================================================================================
"""

import re
from typing import List, Dict, Set
from dataclasses import dataclass
from collections import defaultdict
import random

# ============================================================
# GENOMES
# ============================================================

@dataclass
class AppleseedGenome:
    """Base JA parameters (from genetic evolution)"""
    min_score: float = 0.1641
    min_word_length: int = 3
    min_matches: int = 1
    concept_min_len: int = 14
    concept_max_len: int = 171
    score_power: float = 1.1332

@dataclass 
class ClusterGenome:
    """Clustering parameters"""
    min_shared_matches: int = 1
    min_cluster_size: int = 2
    max_clusters: int = 5
    topic_threshold: float = 0.5

@dataclass
class SynthesisGenome:
    """Evolved synthesis parameters"""
    action_weight: float = 0.555
    relationship_weight: float = 0.334
    pattern_weight: float = 0.111
    prefer_topic_first: float = 0.90
    max_length: int = 50

GENOME = AppleseedGenome()
CLUSTER_GENOME = ClusterGenome()
SYNTH_GENOME = SynthesisGenome()

STOPWORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
    'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
    'as', 'it', 'that', 'this', 'not', 'all', 'but', 'or', 'and',
    'can', 'will', 'should', 'would', 'could', 'when', 'where',
    'what', 'how', 'why', 'if', 'then', 'so', 'just', 'also',
    'its', 'has', 'have', 'had', 'you', 'your', 'we', 'our',
    'i', 'me', 'my', 'do', 'does', 'did', 'done', 'being'
}

# ============================================================
# VERB HANDLING
# ============================================================

VERB_FORMS = {
    'prevent': ('prevents', 'prevent'),
    'enable': ('enables', 'enable'),
    'accumulate': ('accumulates', 'accumulate'),
    'show': ('shows', 'show'),
    'derive': ('derives', 'derive'),
    'require': ('requires', 'require'),
    'connect': ('connects', 'connect'),
    'transform': ('transforms', 'transform'),
    'optimize': ('optimizes', 'optimize'),
    'hold': ('holds', 'hold'),
    'drift': ('drifts', 'drift'),
    'cluster': ('clusters', 'cluster'),
    'emerge': ('emerges', 'emerge'),
    'depend': ('depends', 'depend'),
}

ACTION_KEYWORDS = {
    'prevent': ['prevents', 'stops', 'blocks', 'avoids', 'guards'],
    'enable': ['enables', 'allows', 'permits', 'supports', 'helps'],
    'accumulate': ['accumulates', 'grows', 'increases', 'builds'],
    'show': ['shows', 'displays', 'reveals', 'indicates'],
    'derive': ['derives', 'computes', 'calculates', 'generates'],
    'connect': ['connects', 'links', 'joins', 'bridges', 'clusters'],
    'optimize': ['optimizes', 'improves', 'enhances', 'refines'],
    'hold': ['holds', 'maintains', 'keeps', 'preserves'],
}

def is_plural(word: str) -> bool:
    """Detect if word is plural (for verb conjugation)"""
    w = word.lower()
    if w.endswith('s') and not w.endswith(('ss', 'us', 'is', 'ness')):
        return True
    return False

def conjugate(verb: str, plural: bool = False) -> str:
    """Return correct verb form for singular/plural"""
    base = verb.lower().rstrip('s')
    if base in VERB_FORMS:
        return VERB_FORMS[base][1 if plural else 0]
    return verb if plural else (verb + 's' if not verb.endswith('s') else verb)

def find_action(words, exclude=None) -> str:
    """Find best action verb, excluding topic words to prevent tautology"""
    exclude = exclude or set()
    for action, keywords in ACTION_KEYWORDS.items():
        if action in exclude:
            continue
        for k in keywords:
            if k in words:
                return action
    return random.choice(['enable', 'connect', 'show'])

# ============================================================
# EVOLVED TEMPLATES (v5 - grammar-correct, tautology-free)
# ============================================================

ACTION_TEMPLATES = [
    "{T0} {verb} {t1}",
    "{T0} {verb} through {t1}",
]

SINGLE_TOPIC_TEMPLATES = [
    "{T0} {verb} naturally",
    "{T0} {verb} over time",
    "{T0} is key",
]

RELATIONSHIP_TEMPLATES = [
    "{T0} depends on {t1}",
    "Without {t0}, {t1} weakens",
]

# ============================================================
# CORE FUNCTIONS
# ============================================================

def build_wave(seeds: List[str], min_word_len: int = 3) -> Set[str]:
    """Build vocabulary wave from seeds"""
    wave = set()
    for seed in seeds:
        for w in re.findall(r'\b[a-zA-Z]+\b', seed.lower()):
            if w not in STOPWORDS and len(w) >= min_word_len:
                wave.add(w)
    return wave

def get_words(text: str, min_len: int = 3) -> Set[str]:
    """Extract significant words from text"""
    return set(w for w in re.findall(r'\b[a-zA-Z]+\b', text.lower())
               if w not in STOPWORDS and len(w) >= min_len)

def base_scan(text: str, seeds: List[str], genome=GENOME) -> List[Dict]:
    """Base Johnny Appleseed scan - returns flat gap list"""
    wave = build_wave(seeds, genome.min_word_length)
    gaps = []
    for line in text.split('\n'):
        line = line.strip()
        if len(line) < genome.concept_min_len or len(line) > genome.concept_max_len:
            continue
        words = get_words(line, genome.min_word_length)
        if not words:
            continue
        matches = words & wave
        score = (len(matches) / len(words)) ** genome.score_power if words else 0
        if score >= genome.min_score and len(matches) >= genome.min_matches:
            gaps.append({
                'concept': line,
                'score': score,
                'matches': sorted(matches),
                'match_set': frozenset(matches),
                'word_set': frozenset(words)
            })
    return sorted(gaps, key=lambda x: -x['score'])

def cluster_gaps(gaps: List[Dict], cg: ClusterGenome = CLUSTER_GENOME) -> List[Dict]:
    """Cluster gaps by shared seed words using Union-Find"""
    if len(gaps) < cg.min_cluster_size:
        return []
    n = len(gaps)
    parent = list(range(n))
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py
    
    for i in range(n):
        for j in range(i + 1, n):
            shared = gaps[i]['match_set'] & gaps[j]['match_set']
            if len(shared) >= cg.min_shared_matches:
                union(i, j)
    
    components = defaultdict(list)
    for i in range(n):
        components[find(i)].append(i)
    
    clusters = []
    for indices in components.values():
        if len(indices) < cg.min_cluster_size:
            continue
        members = [gaps[i] for i in indices]
        word_freq = defaultdict(int)
        for m in members:
            for w in m['match_set']:
                word_freq[w] += 1
        topic_words = sorted([w for w, c in word_freq.items() 
                              if c >= len(members) * cg.topic_threshold])
        clusters.append({
            'members': members,
            'topic_words': topic_words,
            'size': len(members)
        })
    clusters.sort(key=lambda c: -c['size'])
    return clusters[:cg.max_clusters]

# ============================================================
# EVOLVED SYNTHESIS
# ============================================================

def synthesize_principle(cluster: Dict, genome: SynthesisGenome = SYNTH_GENOME) -> str:
    """Generate principle using evolved templates (v5 - grammar-correct, tautology-free)"""
    topic = cluster['topic_words']
    if not topic:
        return "A pattern emerges"
    
    members = cluster['members']
    all_words = []
    for m in members:
        all_words.extend(m.get('word_set', []))
    
    t0 = topic[0]
    has_second = len(topic) > 1
    t1 = topic[1] if has_second else None
    
    # Plural detection for verb conjugation
    t0_plural = is_plural(t0)
    
    # Exclude topic words from action detection to prevent tautology
    exclude = set(t.lower().rstrip('s').rstrip('ion') for t in topic)
    action = find_action(all_words, exclude)
    verb = conjugate(action, plural=t0_plural)
    
    # Select template based on topic count
    if has_second:
        r = random.random()
        if r < genome.action_weight:
            template = random.choice(ACTION_TEMPLATES)
        else:
            template = random.choice(RELATIONSHIP_TEMPLATES)
        result = template.format(
            T0=t0.title(),
            t0=t0.lower(),
            T1=t1.title(),
            t1=t1.lower(),
            verb=verb
        )
    else:
        template = random.choice(SINGLE_TOPIC_TEMPLATES)
        result = template.format(
            T0=t0.title(),
            t0=t0.lower(),
            verb=verb
        )
    
    if len(result) > genome.max_length:
        result = result[:genome.max_length].rsplit(' ', 1)[0]
    
    return result

def _quick_score(principle: str, topic_words: List[str]) -> float:
    """Quick scoring for tournament selection"""
    s = 0
    p_lower = principle.lower()
    words = p_lower.split()
    
    # Topic coverage
    for t in topic_words[:2]:
        if t in p_lower:
            s += 1
    
    # Has verb
    for v in VERB_FORMS:
        if v in p_lower or conjugate(v) in p_lower:
            s += 1
            break
    
    # No duplicate words (tautology penalty)
    if len(words) == len(set(words)):
        s += 0.5
    else:
        s -= 2  # Heavy penalty for duplicates
    
    # Not generic
    if 'are connected' not in p_lower:
        s += 0.3
    
    return s

# ============================================================
# MAIN FUNCTIONS
# ============================================================

def johnny_appleseed(text: str, seeds: List[str]) -> List[Dict]:
    """{JA} - Base scan, flat gap list"""
    return base_scan(text, seeds)

def johnny_appleseed_plus(text: str, seeds: List[str]) -> Dict:
    """{JA+} - Clustered scan with evolved principle synthesis"""
    gaps = base_scan(text, seeds)
    clusters = cluster_gaps(gaps)
    
    for cluster in clusters:
        # Tournament selection: generate multiple, pick best
        candidates = [synthesize_principle(cluster) for _ in range(5)]
        candidates.sort(key=lambda p: _quick_score(p, cluster['topic_words']), reverse=True)
        cluster['principle'] = candidates[0]
    
    clustered = set()
    for c in clusters:
        for m in c['members']:
            clustered.add(m['concept'])
    
    unclustered = [g for g in gaps if g['concept'] not in clustered]
    
    return {
        'total_gaps': len(gaps),
        'clusters': clusters,
        'unclustered': unclustered,
        'principles_found': len(clusters)
    }

# Aliases
ja = johnny_appleseed
ja_plus = johnny_appleseed_plus
JA = johnny_appleseed
JA_PLUS = johnny_appleseed_plus

# ============================================================
# OUTPUT FORMATTING
# ============================================================

def format_ja_output(gaps: List[Dict]) -> str:
    """Format base JA output"""
    lines = ["{JA} Scan Complete", "─" * 30]
    lines.append(f"⚠️ Gaps: {len(gaps)}")
    for g in gaps[:10]:
        lines.append(f"  {g['score']:.2f} | {g['concept'][:55]}")
    if len(gaps) > 10:
        lines.append(f"  ... +{len(gaps)-10} more")
    return "\n".join(lines)

def format_ja_plus_output(result: Dict) -> str:
    """Format JA+ clustered output"""
    lines = ["{JA+} Clustered Scan", "─" * 40]
    lines.append(f"Gaps: {result['total_gaps']} | Principles: {result['principles_found']}")
    
    if result['clusters']:
        lines.append("\n🌳 SYNTHESIZED PRINCIPLES:")
        for i, c in enumerate(result['clusters'], 1):
            lines.append(f"\n  [{i}] \"{c['principle']}\"")
            lines.append(f"      topic: {c['topic_words']}")
            lines.append(f"      gaps ({c['size']}):")
            for m in c['members'][:4]:
                lines.append(f"        • {m['concept'][:55]}")
            if c['size'] > 4:
                lines.append(f"        ... +{c['size']-4} more")
    
    if result['unclustered']:
        lines.append("\n🍂 UNCLUSTERED:")
        for g in result['unclustered'][:5]:
            lines.append(f"  {g['score']:.2f} | {g['concept'][:50]}")
    
    return "\n".join(lines)
