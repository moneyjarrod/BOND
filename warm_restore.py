"""
Warm Restore — SLA-Powered Session Retrieval Engine
BOND Framework | Session 93+

Indexes handoff files into sections, builds SLA corpus,
and retrieves relevant sections for session continuity.

Two-layer architecture:
  Layer 1: Always loads most recent handoff (guaranteed context)
  Layer 2: SLA query against archive with confidence badges

Usage:
    python warm_restore.py index              # rebuild index
    python warm_restore.py query "GSG panel"  # retrieve sections
    python warm_restore.py query "text" --top 5  # more results
    python warm_restore.py restore            # full two-layer restore
    python warm_restore.py restore "bridge work"  # restore with context
"""

import sys, os, re, json, math
from pathlib import Path
from collections import defaultdict, Counter


# ═══════════════════════════════════════════════════════════
# ROSETTA — Stemmer + Stop Words (shared with SLA)
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
# HANDOFF PARSER
# ═══════════════════════════════════════════════════════════

STANDARD_HEADERS = {'CONTEXT', 'WORK', 'DECISIONS', 'STATE', 'THREADS', 'FILES'}

HEADER_ALIASES = {
    'WHAT WAS DONE THIS SESSION': 'WORK',
    'WHAT WAS BUILT': 'WORK',
    'THE BREAKTHROUGH': 'WORK',
    'SESSION SUMMARY': 'CONTEXT',
    'WHAT HAPPENED': 'WORK',
    'WHAT HAPPENED THIS SESSION': 'WORK',
    'WHAT NEEDS TO HAPPEN NEXT': 'THREADS',
    'NEXT STEPS': 'THREADS',
    'KEY FILES CHANGED': 'FILES',
    'ACTIVE STATE': 'STATE',
    'DESIGN DECISIONS': 'DECISIONS',
    'DESIGN DECISIONS AGREED': 'DECISIONS',
}

def _normalize_header(raw_header):
    """Map raw ## header text to a canonical section name."""
    upper = raw_header.strip().upper()
    if upper in STANDARD_HEADERS:
        return upper
    if upper in HEADER_ALIASES:
        return HEADER_ALIASES[upper]
    return raw_header.strip()


def _extract_session_num(stem):
    """Extract session number from filename for sorting."""
    m = re.search(r'S(\d+)', stem)
    return int(m.group(1)) if m else 0


def parse_handoff(filepath):
    """Parse a handoff into sections.
    
    Handles both standardized template and legacy freeform formats.
    Any ## header becomes a section boundary.
    """
    text = Path(filepath).read_text(encoding='utf-8')
    
    session_match = re.search(r'S(\d+)', Path(filepath).stem)
    session = int(session_match.group(1)) if session_match else 0
    
    entity = 'UNKNOWN'
    for pattern in [
        r'^#\s+.*?S\d+.*?[—\-]\s*(.+)$',
        r'^#\s+.*?:\s*(.+)$',
    ]:
        m = re.search(pattern, text, re.MULTILINE)
        if m:
            entity = m.group(1).strip()
            break
    
    sections = {}
    current_header = None
    current_lines = []
    
    for line in text.split('\n'):
        hm = re.match(r'^##\s+(.+)$', line)
        if hm:
            raw = hm.group(1)
            if re.match(r'^(Written|Date|Session|Bonfire):', raw, re.IGNORECASE):
                continue
            if current_header:
                content = '\n'.join(current_lines).strip()
                if content:
                    sections[current_header] = content
            current_header = _normalize_header(raw)
            current_lines = []
            continue
        if current_header:
            current_lines.append(line)
    
    if current_header:
        content = '\n'.join(current_lines).strip()
        if content:
            sections[current_header] = content
    
    return {
        'session': session,
        'entity': entity,
        'sections': sections,
        'filepath': str(filepath),
    }


def load_all_handoffs(handoffs_dir):
    """Load and parse all handoffs from directory."""
    handoffs = []
    hdir = Path(handoffs_dir)
    if not hdir.exists():
        return handoffs
    
    files = set()
    for pattern in ['HANDOFF_S*.md', 'S*_HANDOFF*.md', 'S*_SESSION*_HANDOFF*.md']:
        files.update(hdir.glob(pattern))
    
    for f in sorted(files, key=lambda p: _extract_session_num(p.stem)):
        try:
            handoffs.append(parse_handoff(f))
        except Exception as e:
            print(f"  Warning: {f.name}: {e}", file=sys.stderr)
    
    return handoffs


def get_latest_handoff(handoffs_dir):
    """Get the most recent handoff by session number (Layer 1)."""
    hdir = Path(handoffs_dir)
    if not hdir.exists():
        return None
    
    files = set()
    for pattern in ['HANDOFF_S*.md', 'S*_HANDOFF*.md', 'S*_SESSION*_HANDOFF*.md']:
        files.update(hdir.glob(pattern))
    
    if not files:
        return None
    
    latest = max(files, key=lambda p: _extract_session_num(p.stem))
    return parse_handoff(latest)


# ═══════════════════════════════════════════════════════════
# SLA SECTION CORPUS — Section-level retrieval
# ═══════════════════════════════════════════════════════════

class SectionCorpus:
    """SLA corpus built from handoff sections. SPECTRA ranking immutable."""
    
    def __init__(self, handoffs, anchor_k=5, confuser_k=3):
        self.chunks = []
        self.anchor_k = anchor_k
        self.confuser_k = confuser_k
        
        for h in handoffs:
            for header, text in h['sections'].items():
                if not text.strip():
                    continue
                self.chunks.append({
                    'session': h['session'],
                    'entity': h['entity'],
                    'header': header,
                    'text': text,
                    'filepath': h.get('filepath', ''),
                })
        
        self.n = len(self.chunks)
        if self.n == 0:
            return
        
        self.tokens = [content_stems(c['text']) for c in self.chunks]
        
        self.vocab = set(s for pt in self.tokens for s in pt)
        self.df = defaultdict(int)
        for pt in self.tokens:
            for w in set(pt):
                self.df[w] += 1
        self.idf = {w: math.log(self.n / self.df[w]) for w in self.vocab if self.df[w] > 0}
        
        self._build_anchors()
    
    def _cosine_stems(self, stems_a, stems_b):
        set_a, set_b = set(stems_a), set(stems_b)
        overlap = set_a & set_b
        if not overlap:
            return 0.0
        dot = sum(self.idf.get(w, 0) ** 2 for w in overlap)
        mag_a = math.sqrt(sum(self.idf.get(w, 0) ** 2 for w in set_a))
        mag_b = math.sqrt(sum(self.idf.get(w, 0) ** 2 for w in set_b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)
    
    def _build_anchors(self):
        self.anchors = []
        for i in range(self.n):
            sims = sorted(
                [(j, self._cosine_stems(self.tokens[i], self.tokens[j]))
                 for j in range(self.n) if j != i],
                key=lambda x: -x[1]
            )
            confuser_indices = [idx for idx, _ in sims[:self.confuser_k]]
            
            word_scores = {}
            for w in set(self.tokens[i]):
                presence = sum(
                    1 for ci in confuser_indices
                    if w in set(self.tokens[ci])
                ) / max(len(confuser_indices), 1)
                word_scores[w] = self.idf.get(w, 0) * (1.0 - presence)
            
            ranked = sorted(word_scores.items(), key=lambda x: -x[1])[:self.anchor_k]
            self.anchors.append({w: score for w, score in ranked})
    
    def query(self, query_text, top_n=5, anchor_weight=15):
        if self.n == 0:
            return [], 0.0
        
        q_stems = set(content_stems(query_text))
        q_size = max(len(q_stems), 1)
        
        scores = []
        for i, pt in enumerate(self.tokens):
            chunk_set = set(pt)
            overlap = q_stems & chunk_set
            score = sum(self.idf.get(w, 0) for w in overlap) / q_size
            scores.append((i, score, overlap))
        
        scores.sort(key=lambda x: -x[1])
        
        results = []
        for idx, spectra_score, overlap in scores[:top_n]:
            if spectra_score == 0:
                continue
            anchor_hits = [w for w in self.anchors[idx] if w in q_stems]
            results.append({
                'chunk': self.chunks[idx],
                'score': spectra_score,
                'overlap': list(overlap),
                'anchor_hits': anchor_hits,
            })
        
        if len(results) >= 2:
            top_score = results[0]['score']
            runner_score = results[1]['score']
            raw_margin = (top_score - runner_score) / max(top_score, 1e-10) * 100
            anchor_diff = len(results[0]['anchor_hits']) - len(results[1]['anchor_hits'])
            margin = min(max(raw_margin + anchor_weight * anchor_diff, 0.1), 100.0)
        elif len(results) == 1:
            margin = 100.0
        else:
            margin = 0.0
        
        for r in results:
            r['confidence'] = 'HIGH' if margin > 50 else 'MED' if margin > 15 else 'LOW'
        
        return results, margin
    
    def expand_with_siblings(self, results):
        """For each selected section, also include CONTEXT and STATE siblings."""
        seen = set()
        expanded = []
        
        for r in results:
            key = (r['chunk']['session'], r['chunk']['header'])
            seen.add(key)
            expanded.append(r)
        
        sibling_headers = {'CONTEXT', 'STATE', 'Session Summary', 'STATUS'}
        for r in results:
            session = r['chunk']['session']
            for chunk in self.chunks:
                if chunk['session'] == session and chunk['header'] in sibling_headers:
                    key = (chunk['session'], chunk['header'])
                    if key not in seen:
                        seen.add(key)
                        expanded.append({
                            'chunk': chunk,
                            'score': 0,
                            'overlap': [],
                            'anchor_hits': [],
                            'confidence': 'SIBLING',
                        })
        
        header_order = {'CONTEXT': 0, 'Session Summary': 0, 'STATUS': 0,
                        'WORK': 1, 'DECISIONS': 2, 'STATE': 3, 'THREADS': 4, 'FILES': 5}
        expanded.sort(key=lambda r: (
            r['chunk']['session'],
            header_order.get(r['chunk']['header'], 99),
        ))
        
        return expanded
    
    def save_index(self, filepath):
        index = {
            'chunk_count': self.n,
            'handoff_count': len(set(c['session'] for c in self.chunks)),
            'sessions': sorted(set(c['session'] for c in self.chunks)),
            'vocab_size': len(self.vocab),
        }
        Path(filepath).write_text(json.dumps(index, indent=2) + '\n')
        return index


# ═══════════════════════════════════════════════════════════
# CONFIDENCE BADGE FORMATTER
# ═══════════════════════════════════════════════════════════

def _section_badge(confidence):
    """Map confidence level to display badge."""
    return {
        'HIGH': '\U0001f7e2',     # green circle
        'MED': '\U0001f7e1',      # yellow circle
        'LOW': '\U0001f534',      # red circle
        'SIBLING': '\u26aa',      # white circle
        'LAYER1': '\U0001f7e2',   # green circle (guaranteed)
    }.get(confidence, '\u26aa')


def _triangle_color(results, margin):
    """Determine overall triangle badge color from results and margin."""
    if not results:
        return 'RED'
    confidences = [r.get('confidence', 'LOW') for r in results if r.get('confidence') != 'SIBLING']
    if not confidences:
        return 'GREEN'  # only siblings = came from Layer 1
    if all(c == 'HIGH' for c in confidences):
        return 'GREEN'
    if any(c == 'LOW' for c in confidences):
        return 'RED'
    return 'YELLOW'


def _triangle_badge(color):
    """Confidence header badge — colored circle matching state."""
    return {
        'GREEN': '\U0001f7e2',     # green circle
        'YELLOW': '\U0001f7e1',    # yellow circle
        'RED': '\U0001f534',       # red circle
    }.get(color, '\U0001f534')


def format_restore_output(layer1_handoff, layer2_results, layer2_margin, query_used):
    """
    Format the full {Warm Restore} output with confidence badges.
    
    Args:
        layer1_handoff: parsed handoff dict from get_latest_handoff() (or None)
        layer2_results: list of expanded results from SectionCorpus (or [])
        layer2_margin: confidence margin from Layer 2 query
        query_used: the query string that was used for Layer 2
    
    Returns:
        Formatted string for Claude to present to user.
    """
    lines = []
    sessions_loaded = set()
    
    # ── Layer 1: Most Recent Handoff ──
    if layer1_handoff:
        s = layer1_handoff['session']
        sessions_loaded.add(s)
        lines.append(f"## Layer 1 — Last Session (S{s})")
        lines.append("")
        
        # Load all sections from Layer 1 handoff
        for header, text in layer1_handoff['sections'].items():
            lines.append(f"{_section_badge('LAYER1')} **S{s}/{header}**")
            lines.append(text)
            lines.append("")
    else:
        lines.append("## Layer 1 — No handoffs found")
        lines.append("")
    
    # ── Layer 2: Archive Query ──
    if layer2_results:
        # Filter out sections already loaded in Layer 1
        l2_filtered = [
            r for r in layer2_results
            if r['chunk']['session'] not in sessions_loaded
        ]
        
        if l2_filtered:
            color = _triangle_color(l2_filtered, layer2_margin)
            lines.append(f"## Layer 2 — Archive Query {_triangle_badge(color)}")
            lines.append(f"Query: *{query_used}*")
            lines.append("")
            
            for r in l2_filtered:
                c = r['chunk']
                badge = _section_badge(r['confidence'])
                conf_tag = r['confidence']
                score_str = f" — score {r['score']:.2f}" if r['score'] > 0 else ""
                anchor_str = ""
                if r.get('anchor_hits'):
                    anchor_str = f", anchors: {', '.join(r['anchor_hits'])}"
                
                lines.append(f"{badge} **S{c['session']}/{c['header']}** [{conf_tag}{score_str}{anchor_str}]")
                lines.append(c['text'])
                lines.append("")
            
            # Cautionary note on RED
            if color == 'RED':
                lines.append("\u26a0\ufe0f **Low confidence retrieval.** Query terms were spread across sessions or matched weakly. Consider narrowing your query with more specific terms.")
                lines.append("")
        else:
            lines.append("## Layer 2 — Archive sections already covered by Layer 1")
            lines.append("")
    elif query_used:
        lines.append("## Layer 2 — No archive matches for query")
        lines.append(f"Query: *{query_used}*")
        lines.append("")
    
    # ── Token Summary ──
    total_words = 0
    if layer1_handoff:
        total_words += sum(len(t.split()) for t in layer1_handoff['sections'].values())
    for r in (layer2_results or []):
        if r['chunk']['session'] not in sessions_loaded:
            total_words += len(r['chunk']['text'].split())
    
    token_est = int(total_words * 0.75)
    session_list = sorted(sessions_loaded | {r['chunk']['session'] for r in (layer2_results or [])})
    lines.append(f"---")
    lines.append(f"Sessions: {', '.join(f'S{s}' for s in session_list)} | ~{token_est} tokens loaded")
    
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════
# WARM RESTORE — Top-level orchestration
# ═══════════════════════════════════════════════════════════

def warm_restore(handoffs_dir, state_dir, query_text=None, entity=None, top_n=3):
    """
    Full {Warm Restore} pipeline — both layers.
    
    Returns dict with 'output' (formatted badge display) and metadata.
    """
    # ── Layer 1: Most recent handoff ──
    layer1 = get_latest_handoff(handoffs_dir)
    layer1_session = layer1['session'] if layer1 else -1
    
    # ── Read active entity if not provided ──
    if not entity:
        state_file = Path(state_dir) / 'active_entity.json'
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
                entity = state.get('entity', '')
            except:
                entity = ''
    
    # ── Layer 2: SLA archive query ──
    layer2_results = []
    layer2_margin = 0.0
    query_used = ''
    
    signals = []
    if entity:
        signals.append(entity)
    if query_text:
        signals.append(query_text)
    query_used = ' '.join(signals)
    
    if query_used:
        # Load all handoffs EXCEPT Layer 1 (already loaded)
        all_handoffs = load_all_handoffs(handoffs_dir)
        archive_handoffs = [h for h in all_handoffs if h['session'] != layer1_session]
        
        if archive_handoffs:
            corpus = SectionCorpus(archive_handoffs)
            results, layer2_margin = corpus.query(query_used, top_n=top_n)
            layer2_results = corpus.expand_with_siblings(results)
            
            # Save index
            os.makedirs(state_dir, exist_ok=True)
            index_file = Path(state_dir) / 'warm_restore_index.json'
            corpus.save_index(index_file)
    
    # ── Format output ──
    output = format_restore_output(layer1, layer2_results, layer2_margin, query_used)
    
    return {
        'output': output,
        'query': query_used,
        'entity': entity or '',
        'layer1_session': layer1_session,
        'layer2_sections': len(layer2_results),
        'layer2_margin': round(layer2_margin, 1),
    }


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    bond_root = os.environ.get('BOND_ROOT', str(Path(__file__).parent))
    handoffs_dir = os.path.join(bond_root, 'handoffs')
    state_dir = os.path.join(bond_root, 'state')
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python warm_restore.py index")
        print('  python warm_restore.py query "your query"')
        print('  python warm_restore.py query "your query" --top 5')
        print('  python warm_restore.py restore')
        print('  python warm_restore.py restore "context message"')
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'index':
        handoffs = load_all_handoffs(handoffs_dir)
        corpus = SectionCorpus(handoffs)
        os.makedirs(state_dir, exist_ok=True)
        index = corpus.save_index(os.path.join(state_dir, 'warm_restore_index.json'))
        print(f"Indexed {index['chunk_count']} sections from {index['handoff_count']} handoffs")
        print(f"Sessions: {index['sessions']}")
        print(f"Vocabulary: {index['vocab_size']} stems")
    
    elif cmd == 'query':
        if len(sys.argv) < 3:
            print('Usage: python warm_restore.py query "your query"')
            sys.exit(1)
        
        query_text = sys.argv[2]
        top_n = 3
        if '--top' in sys.argv:
            ti = sys.argv.index('--top')
            if ti + 1 < len(sys.argv):
                top_n = int(sys.argv[ti + 1])
        
        handoffs = load_all_handoffs(handoffs_dir)
        if not handoffs:
            print("No handoffs found")
            sys.exit(1)
        
        corpus = SectionCorpus(handoffs)
        results, margin = corpus.query(query_text, top_n=top_n)
        expanded = corpus.expand_with_siblings(results)
        
        print(f"Query: {query_text}")
        print(f"Margin: {margin:.1f}%")
        print(f"Sections: {len(expanded)} (from {len(results)} direct hits)")
        print()
        
        for r in expanded:
            c = r['chunk']
            badge = _section_badge(r['confidence'])
            sc = f"score={r['score']:.4f}" if r['score'] > 0 else ''
            anch = f"anchors={r['anchor_hits']}" if r['anchor_hits'] else ''
            print(f"{badge} S{c['session']}/{c['header']} [{r['confidence']}] {sc} {anch}")
            lines = c['text'].split('\n')
            for line in lines[:3]:
                print(f"  {line}")
            if len(lines) > 3:
                print(f"  ... ({len(lines) - 3} more lines)")
            print()
    
    elif cmd == 'restore':
        query_text = sys.argv[2] if len(sys.argv) > 2 else None
        result = warm_restore(handoffs_dir, state_dir, query_text=query_text)
        print(result['output'])
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
