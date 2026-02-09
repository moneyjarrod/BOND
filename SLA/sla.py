"""
SLA — Spectral Linguistic Anchorage
Reference Implementation v2 (Session 89→90)

v2 DIFFERENTIAL: SPECTRA ranking is IMMUTABLE.
Anchors and neighbors adjust confidence margin only,
never reorder candidates. CM principle enforced.

Usage:
    corpus = SLACorpus(paragraphs)     # build time
    results, margin = corpus.query(text) # query time
"""

import re, math
import numpy as np
from collections import defaultdict, Counter


# ═══════════════════════════════════════════════════════════
# ROSETTA — Stemmer + Stop Words (from doctrine)
# ═══════════════════════════════════════════════════════════

SUFFIXES = ['ation','tion','sion','ness','ment','able','ible','ful','ous','ing','ed','ly','s']
STEM_EXCEPTIONS = {
    'this','his','its','was','has','does','is','as','us','yes','thus','plus','minus','status','focus',
    'process','express','access','address','unless','less','loss','boss','miss','pass','class',
    'across','always','perhaps','besides','sometimes','series','species','indices','becomes','parties',
    'used','based','need','seed','speed','feed','shared','said','paid','red','bed','led','bounded',
    'being','thing','nothing','something','everything','string','bring','during','morning','feeling','meaning',
    'binding','mapping','working','building','only','early','likely','family','really','finally',
    'apply','supply','reply','rely','silently','other','another','either','neither','whether',
    'never','ever','over','under','after','rather','layer','player','server','container','counter',
    'sidecar','however','together','whatever','trigger','buffer','cluster','register',
    'between','even','means','sometimes','collaborative','speculative','performing','observations',
}
STOP_WORDS = {
    'the','be','to','of','and','in','that','have','it','for','on','with','he','as','you','do','at',
    'this','but','his','by','from','they','we','say','her','she','or','an','will','my','one','all',
    'would','there','their','what','so','up','out','if','about','who','get','which','go','me','when',
    'make','can','like','no','just','him','know','take','how','could','them','see','than','been','had',
    'its','was','has','does','are','were','did','am','is','not','don','also','ll','re','ve','won',
    'didn','isn','aren','doesn','some','any','much','more','most','such','very','too','own','same',
    'other','each','every','both','few','many','may','might','shall','should','a','i',
}

def light_stem(word):
    if word in STEM_EXCEPTIONS: return word
    for s in SUFFIXES:
        if word.endswith(s) and len(word)-len(s) >= 4: return word[:-len(s)]
    return word

def tokenize(text):
    expanded = text.lower().replace('_', ' ')
    raw = re.findall(r"[a-zA-Z0-9'-]+", expanded)
    return [light_stem(c) for w in raw for c in [w.strip("'-").lower()] if len(c) > 1]

def content_stems(text):
    return [s for s in tokenize(text) if s not in STOP_WORDS and len(s) > 2]


# ═══════════════════════════════════════════════════════════
# SLA CORPUS — Build-time precomputation
# ═══════════════════════════════════════════════════════════

class SLACorpus:
    """
    Precomputed retrieval index for a body of text.
    
    Build once at ingestion time. Query at runtime with zero API cost
    for high-confidence results.
    """
    
    def __init__(self, paragraphs, labels=None, anchor_k=5, confuser_k=5,
                 neighborhood_radius=2, cluster_map=None):
        """
        Args:
            paragraphs: list of text strings (the corpus)
            labels: optional list of display labels (e.g. verse references)
            anchor_k: number of anchors per paragraph
            confuser_k: number of confusers for contrastive anchor computation
            neighborhood_radius: how far to look for neighbors (+/- N)
            cluster_map: dict mapping paragraph index to cluster label,
                         or None to use sequential adjacency
        """
        self.paragraphs = paragraphs
        self.n = len(paragraphs)
        self.labels = labels or [f"p{i}" for i in range(self.n)]
        self.anchor_k = anchor_k
        self.confuser_k = confuser_k
        self.radius = neighborhood_radius
        self.cluster_map = cluster_map
        
        # Step 1: Tokenize
        self.para_tokens = [content_stems(p) for p in paragraphs]
        
        # Step 2: IDF (SPECTRA core)
        self.vocab = set(s for pt in self.para_tokens for s in pt)
        self.df = defaultdict(int)
        for pt in self.para_tokens:
            for w in set(pt):
                self.df[w] += 1
        self.idf = {w: math.log(self.n / self.df[w]) for w in self.vocab}
        
        # Step 3: TF-IDF vectors
        vocab_list = sorted(self.vocab)
        self.vocab_idx = {w: i for i, w in enumerate(vocab_list)}
        n_vocab = len(vocab_list)
        
        self.tfidf = []
        self.tfidf_normed = []
        for pt in self.para_tokens:
            tf = Counter(pt)
            vec = np.zeros(n_vocab)
            for w, c in tf.items():
                vec[self.vocab_idx[w]] = c * self.idf[w]
            self.tfidf.append(vec)
            n = np.linalg.norm(vec)
            self.tfidf_normed.append(vec / n if n > 0 else vec)
        
        # Step 4: Contrastive anchors
        self._build_contrastive_anchors()
        
        # Step 5: Neighborhood map
        self._build_neighborhoods()
    
    def _build_contrastive_anchors(self):
        """Find confusers per paragraph, compute contrastive anchor scores."""
        # Find confusers via cosine similarity
        self.confusers = {}
        for i in range(self.n):
            sims = []
            for j in range(self.n):
                if i == j: continue
                sim = np.dot(self.tfidf_normed[i], self.tfidf_normed[j])
                sims.append((j, sim))
            sims.sort(key=lambda x: -x[1])
            self.confusers[i] = [idx for idx, _ in sims[:self.confuser_k]]
        
        # Compute contrastive scores
        self.anchors = []
        for i, pt in enumerate(self.para_tokens):
            confuser_indices = self.confusers[i]
            
            word_scores = {}
            for w in set(pt):
                presence = sum(
                    1 for ci in confuser_indices 
                    if w in set(self.para_tokens[ci])
                ) / max(self.confuser_k, 1)
                word_scores[w] = self.idf.get(w, 0) * (1.0 - presence)
            
            ranked = sorted(word_scores.items(), key=lambda x: -x[1])[:self.anchor_k]
            self.anchors.append({w: score for w, score in ranked})
    
    def _build_neighborhoods(self):
        """Build adjacency map — sequential or cluster-aware."""
        self.neighbors = {}
        for i in range(self.n):
            if self.cluster_map:
                # Cluster-aware: only neighbors in same cluster
                my_cluster = self.cluster_map.get(i)
                nbrs = []
                for offset in range(-self.radius, self.radius + 1):
                    ni = i + offset
                    if ni != i and 0 <= ni < self.n:
                        if self.cluster_map.get(ni) == my_cluster:
                            nbrs.append(ni)
                self.neighbors[i] = nbrs
            else:
                # Sequential: +/- radius
                self.neighbors[i] = [
                    ni for ni in range(max(0, i - self.radius), min(self.n, i + self.radius + 1))
                    if ni != i
                ]
    
    # ═══════════════════════════════════════════════════════
    # QUERY TIME
    # ═══════════════════════════════════════════════════════
    
    def query(self, query_text, top_n=5, anchor_weight=15, nbr_weight=10):
        """
        Full SLA pipeline (v2 — layered narrowing):
        
        SPECTRA determines ranking (immutable).
        Anchors + Neighbors adjust confidence margin only.
        Lower layers narrow within higher layers, never override.
        
        Returns: (results_list, margin_percent)
        """
        q_stems = set(content_stems(query_text))
        q_size = max(len(q_stems), 1)
        
        # Layer 1: SPECTRA shortlist — THIS IS THE RANKING, IMMUTABLE
        shortlist = self._spectra_shortlist(q_stems, top_n)
        
        # Build result objects in SPECTRA order
        results = []
        for idx, spectra_score, overlap in shortlist:
            anchor_hits = [w for w in self.anchors[idx] if w in q_stems]
            
            # Neighbor resonance (normalized by query size)
            nbrs = self.neighbors.get(idx, [])
            nbr_resonance = 0.0
            if nbrs:
                total = 0.0
                for ni in nbrs:
                    verse_set = set(self.para_tokens[ni])
                    ov = q_stems & verse_set
                    total += sum(self.idf.get(w, 0) for w in ov)
                nbr_resonance = (total / len(nbrs)) / q_size
            
            results.append({
                'index': idx,
                'label': self.labels[idx],
                'spectra': spectra_score,
                'anchor_hits': anchor_hits,
                'anchor_count': len(anchor_hits),
                'nbr_resonance': nbr_resonance,
                'overlap': overlap,
            })
        
        # Results already in SPECTRA order (from shortlist sort)
        # Layer 2+3: MARGIN ADJUSTMENTS (ranking stays immutable)
        if len(results) >= 2:
            top, runner = results[0], results[1]
            raw_margin = (top['spectra'] - runner['spectra']) / max(top['spectra'], 1e-10) * 100
            
            anchor_diff = top['anchor_count'] - runner['anchor_count']
            anchor_adj = anchor_weight * anchor_diff
            
            max_nbr = max(top['nbr_resonance'], runner['nbr_resonance'], 1e-10)
            nbr_diff = (top['nbr_resonance'] - runner['nbr_resonance']) / max_nbr
            nbr_adj = nbr_weight * nbr_diff
            
            margin = min(max(raw_margin + anchor_adj + nbr_adj, 0.1), 100.0)
        else:
            margin = 100.0
        
        return results, margin
    
    def _spectra_shortlist(self, q_stems, top_n):
        """SPECTRA: IDF-weighted overlap → shortlist."""
        scores = []
        q_size = max(len(q_stems), 1)
        
        for i, pt in enumerate(self.para_tokens):
            verse_set = set(pt)
            overlap = q_stems & verse_set
            score = sum(self.idf.get(w, 0) for w in overlap) / q_size
            scores.append((i, score, overlap))
        
        scores.sort(key=lambda x: -x[1])
        return scores[:top_n]
    

    def confidence_label(self, margin):
        """Human-readable confidence from margin."""
        if margin > 50: return "HIGH"
        if margin > 15: return "MED"
        return "LOW"
    
    def get_anchors(self, idx):
        """Return anchor set for a paragraph."""
        return self.anchors[idx]
    
    def get_confusers(self, idx):
        """Return confuser indices for a paragraph."""
        return self.confusers[idx]


# ═══════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Minimal smoke test
    paragraphs = [
        "The cat sat on the warm mat by the fire and purred contentedly",
        "Dogs love to fetch sticks and play in the park with their owners",
        "The stock market experienced a significant downturn on Tuesday",
        "Scientists discovered a new species of deep sea fish near hydrothermal vents",
        "The chef prepared a delicious risotto with wild mushrooms and truffle oil",
    ]
    labels = ["cat", "dog", "market", "science", "cooking"]
    
    corpus = SLACorpus(paragraphs, labels)
    
    tests = [
        ("cat warm fire purr mat", 0, "cat"),
        ("fetch sticks park dogs play", 1, "dog"),
        ("stock market downturn Tuesday", 2, "market"),
        ("deep sea fish species hydrothermal", 3, "science"),
        ("chef risotto mushrooms truffle", 4, "cooking"),
    ]
    
    correct = 0
    for query, expected, desc in tests:
        results, margin = corpus.query(query)
        hit = results[0]['index'] == expected
        if hit: correct += 1
        conf = corpus.confidence_label(margin)
        anchors = ', '.join(results[0]['anchor_hits']) or '(none)'
        mark = '✓' if hit else '✗'
        print(f"  {mark} {desc:10s} → {results[0]['label']:10s}  margin={margin:5.1f}%  [{conf}]  anchors=[{anchors}]")
    
    print(f"\n  {correct}/{len(tests)} correct")
    print(f"\n  Anchors for 'cat': {corpus.get_anchors(0)}")
    print(f"  Confusers for 'cat': {[labels[c] for c in corpus.get_confusers(0)]}")
    print(f"\n  v2 pipeline: SPECTRA ranks, anchors+neighbors adjust margin only")
