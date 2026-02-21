"""
Warm Restore — SLA-Powered Session Retrieval Engine
BOND Framework | Session 93+

Indexes handoff files into sections, builds SLA corpus,
and retrieves relevant sections for session continuity.

Two-path Layer 1 architecture (S138):
  Entity active: Direct read of entity-local state (handoff.md + session_chunks.md)
  No entity: Fallback to global handoff glob (original behavior)
  Layer 2: SLA query against archive with confidence badges (unchanged)

P11 consult: Layer 0 replaces Layer 1, not sits above it. Same pipe, one faucet.
FAE consult: Cap chunks at last 3. Strong ROI on upfront tokens.

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
    upper = raw_header.strip().upper()
    if upper in STANDARD_HEADERS: return upper
    if upper in HEADER_ALIASES: return HEADER_ALIASES[upper]
    return raw_header.strip()

def _extract_session_num(stem):
    m = re.search(r'S(\d+)', stem)
    return int(m.group(1)) if m else 0

def parse_handoff(filepath):
    text = Path(filepath).read_text(encoding='utf-8')
    session_match = re.search(r'S(\d+)', Path(filepath).stem)
    if not session_match:
        # Try finding session number in the content (for handoff.md without session in filename)
        session_match = re.search(r'S(\d+)', text[:200])
    session = int(session_match.group(1)) if session_match else 0
    entity = 'UNKNOWN'
    for pattern in [r'^#\s+.*?S\d+.*?[—\-]\s*(.+)$', r'^#\s+.*?:\s*(.+)$']:
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
                if content: sections[current_header] = content
            current_header = _normalize_header(raw)
            current_lines = []
            continue
        if current_header: current_lines.append(line)
    if current_header:
        content = '\n'.join(current_lines).strip()
        if content: sections[current_header] = content
    return {'session': session, 'entity': entity, 'sections': sections, 'filepath': str(filepath)}

def load_all_handoffs(handoffs_dir):
    handoffs = []
    hdir = Path(handoffs_dir)
    if not hdir.exists(): return handoffs
    files = set()
    for pattern in ['HANDOFF_S*.md', 'S*_HANDOFF*.md', 'S*_SESSION*_HANDOFF*.md']:
        files.update(hdir.glob(pattern))
    for f in sorted(files, key=lambda p: _extract_session_num(p.stem)):
        try: handoffs.append(parse_handoff(f))
        except Exception as e: print(f"  Warning: {f.name}: {e}", file=sys.stderr)
    return handoffs

def get_latest_handoff(handoffs_dir):
    hdir = Path(handoffs_dir)
    if not hdir.exists(): return None
    files = set()
    for pattern in ['HANDOFF_S*.md', 'S*_HANDOFF*.md', 'S*_SESSION*_HANDOFF*.md']:
        files.update(hdir.glob(pattern))
    if not files: return None
    latest = max(files, key=lambda p: _extract_session_num(p.stem))
    return parse_handoff(latest)


# ─── Layer 1: Entity-Local State (S138) ───────────────────
# P11: Replaces global handoff glob when entity is active — same pipe, one faucet.
# FAE: Cap chunks to prevent unbounded token accumulation.

CHUNK_CAP = 3
CHUNK_SEPARATOR_RE = re.compile(r'---CHUNK\s+S(\d+)\s+')
CHUNK_END_RE = re.compile(r'---END CHUNK---\s*')

def get_entity_local_state(doctrine_path, entity, state_dir):
    """Read entity-local state files for Layer 1 (entity-active path).
    Returns dict with handoff (parsed), chunks (last N raw), entity config, session number."""
    result = {'handoff': None, 'chunks': None, 'chunk_total': 0, 'entity': entity, 'session': 0, 'config': {}}

    # Read config.json
    config_file = Path(state_dir) / 'config.json'
    if config_file.exists():
        try: result['config'] = json.loads(config_file.read_text())
        except: pass

    entity_state_dir = Path(doctrine_path) / entity / 'state'

    # Read entity-local handoff.md
    handoff_file = entity_state_dir / 'handoff.md'
    if handoff_file.exists():
        try:
            handoff = parse_handoff(handoff_file)
            result['handoff'] = handoff
            result['session'] = handoff['session']
        except Exception as e:
            print(f"  Warning: entity handoff parse failed: {e}", file=sys.stderr)

    # Read session_chunks.md — cap at last N chunks
    chunks_file = entity_state_dir / 'session_chunks.md'
    if chunks_file.exists():
        try:
            raw = chunks_file.read_text(encoding='utf-8')
            # Split on chunk boundaries
            parts = CHUNK_SEPARATOR_RE.split(raw)
            # parts alternates: [preamble, session_num, chunk_text, session_num, chunk_text, ...]
            chunks = []
            for i in range(1, len(parts) - 1, 2):
                session_num = int(parts[i])
                chunk_text = parts[i + 1].strip()
                # Clean trailing separator
                chunk_text = CHUNK_END_RE.sub('', chunk_text).strip()
                if chunk_text:
                    chunks.append({'session': session_num, 'text': chunk_text})
            result['chunk_total'] = len(chunks)
            # Take last N chunks only (FAE: unbounded accumulation kills margin)
            result['chunks'] = chunks[-CHUNK_CAP:] if chunks else []
            # Update session from chunks if newer than handoff
            if chunks and chunks[-1]['session'] > result['session']:
                result['session'] = chunks[-1]['session']
        except Exception as e:
            print(f"  Warning: session_chunks parse failed: {e}", file=sys.stderr)

    return result


class SectionCorpus:
    def __init__(self, handoffs, anchor_k=5, confuser_k=3):
        self.chunks = []
        self.anchor_k = anchor_k
        self.confuser_k = confuser_k
        for h in handoffs:
            for header, text in h['sections'].items():
                if not text.strip(): continue
                self.chunks.append({'session': h['session'], 'entity': h['entity'],
                    'header': header, 'text': text, 'filepath': h.get('filepath', '')})
        self.n = len(self.chunks)
        if self.n == 0: return
        self.tokens = [content_stems(c['text']) for c in self.chunks]
        self.vocab = set(s for pt in self.tokens for s in pt)
        self.df = defaultdict(int)
        for pt in self.tokens:
            for w in set(pt): self.df[w] += 1
        self.idf = {w: math.log(self.n / self.df[w]) for w in self.vocab if self.df[w] > 0}
        self._build_anchors()

    def _cosine_stems(self, a, b):
        sa, sb = set(a), set(b)
        ov = sa & sb
        if not ov: return 0.0
        dot = sum(self.idf.get(w,0)**2 for w in ov)
        ma = math.sqrt(sum(self.idf.get(w,0)**2 for w in sa))
        mb = math.sqrt(sum(self.idf.get(w,0)**2 for w in sb))
        return dot/(ma*mb) if ma and mb else 0.0

    def _build_anchors(self):
        self.anchors = []
        for i in range(self.n):
            sims = sorted([(j, self._cosine_stems(self.tokens[i], self.tokens[j]))
                          for j in range(self.n) if j != i], key=lambda x: -x[1])
            confusers = [idx for idx, _ in sims[:self.confuser_k]]
            scores = {}
            for w in set(self.tokens[i]):
                pres = sum(1 for ci in confusers if w in set(self.tokens[ci])) / max(len(confusers),1)
                scores[w] = self.idf.get(w,0) * (1.0 - pres)
            ranked = sorted(scores.items(), key=lambda x: -x[1])[:self.anchor_k]
            self.anchors.append({w: s for w, s in ranked})

    def query(self, query_text, top_n=5, anchor_weight=15):
        if self.n == 0: return [], 0.0
        q = set(content_stems(query_text))
        qs = max(len(q), 1)
        scores = []
        for i, pt in enumerate(self.tokens):
            ov = q & set(pt)
            score = sum(self.idf.get(w,0) for w in ov) / qs
            scores.append((i, score, ov))
        scores.sort(key=lambda x: -x[1])
        results = []
        for idx, sc, ov in scores[:top_n]:
            if sc == 0: continue
            ah = [w for w in self.anchors[idx] if w in q]
            results.append({'chunk': self.chunks[idx], 'score': sc, 'overlap': list(ov), 'anchor_hits': ah})
        if len(results) >= 2:
            raw = (results[0]['score'] - results[1]['score']) / max(results[0]['score'], 1e-10) * 100
            ad = len(results[0]['anchor_hits']) - len(results[1]['anchor_hits'])
            margin = min(max(raw + anchor_weight * ad, 0.1), 100.0)
        elif len(results) == 1: margin = 100.0
        else: margin = 0.0
        for r in results:
            r['confidence'] = 'HIGH' if margin > 50 else 'MED' if margin > 15 else 'LOW'
        return results, margin

    def expand_with_siblings(self, results):
        seen = set()
        expanded = []
        for r in results:
            key = (r['chunk']['session'], r['chunk']['header'])
            seen.add(key); expanded.append(r)
        sibling_headers = {'CONTEXT', 'STATE', 'Session Summary', 'STATUS'}
        for r in results:
            session = r['chunk']['session']
            for chunk in self.chunks:
                if chunk['session'] == session and chunk['header'] in sibling_headers:
                    key = (chunk['session'], chunk['header'])
                    if key not in seen:
                        seen.add(key)
                        expanded.append({'chunk': chunk, 'score': 0, 'overlap': [], 'anchor_hits': [], 'confidence': 'SIBLING'})
        header_order = {'CONTEXT': 0, 'Session Summary': 0, 'STATUS': 0, 'WORK': 1, 'DECISIONS': 2, 'STATE': 3, 'THREADS': 4, 'FILES': 5}
        expanded.sort(key=lambda r: (r['chunk']['session'], header_order.get(r['chunk']['header'], 99)))
        return expanded

    def save_index(self, filepath):
        index = {'chunk_count': self.n, 'handoff_count': len(set(c['session'] for c in self.chunks)),
                 'sessions': sorted(set(c['session'] for c in self.chunks)), 'vocab_size': len(self.vocab)}
        Path(filepath).write_text(json.dumps(index, indent=2) + '\n')
        return index


def _section_badge(confidence):
    return {'HIGH': '\U0001f7e2', 'MED': '\U0001f7e1', 'LOW': '\U0001f534',
            'SIBLING': '\u26aa', 'LAYER1': '\U0001f7e2', 'ENTITY': '\U0001f7e2'}.get(confidence, '\u26aa')

def _triangle_color(results, margin):
    if not results: return 'RED'
    confidences = [r.get('confidence', 'LOW') for r in results if r.get('confidence') != 'SIBLING']
    if not confidences: return 'GREEN'
    if all(c == 'HIGH' for c in confidences): return 'GREEN'
    if any(c == 'LOW' for c in confidences): return 'RED'
    return 'YELLOW'

def _triangle_badge(color):
    return {'GREEN': '\U0001f7e2', 'YELLOW': '\U0001f7e1',
            'RED': '\U0001f534'}.get(color, '\U0001f534')


def format_restore_output(layer1_handoff, layer2_results, layer2_margin, query_used,
                          entity_local=None):
    """Format restore output. Supports both entity-local and global paths.
    entity_local: if provided, dict from get_entity_local_state() — used instead of layer1_handoff."""
    lines = []
    sessions_loaded = set()

    # ─── Layer 1 ───────────────────────────────────────────
    if entity_local and (entity_local.get('handoff') or entity_local.get('chunks')):
        # Entity-active path: direct local reads
        entity = entity_local['entity']
        handoff = entity_local.get('handoff')
        chunks = entity_local.get('chunks') or []
        chunk_total = entity_local.get('chunk_total', 0)
        config = entity_local.get('config', {})

        # Handoff section
        if handoff:
            s = handoff['session']
            sessions_loaded.add(s)
            lines.append(f"## Layer 1 — Entity State: {entity} (S{s})")
            lines.append("")
            for header, text in handoff['sections'].items():
                lines.append(f"{_section_badge('ENTITY')} **S{s}/{header}**")
                lines.append(text)
                lines.append("")
        else:
            lines.append(f"## Layer 1 — Entity State: {entity} (no handoff)")
            lines.append("")

        # Chunks section — unchunked work since last handoff
        if chunks:
            shown = len(chunks)
            cap_note = f" (showing last {shown} of {chunk_total})" if chunk_total > shown else ""
            lines.append(f"### Session Chunks{cap_note}")
            lines.append("")
            for chunk in chunks:
                sessions_loaded.add(chunk['session'])
                lines.append(f"{_section_badge('ENTITY')} **S{chunk['session']} chunk**")
                lines.append(chunk['text'])
                lines.append("")
            if chunk_total > shown:
                lines.append(f"*{chunk_total - shown} older chunks omitted. Run {{Handoff}} to consolidate.*")
                lines.append("")

        # Config note
        save_conf = config.get('save_confirmation', True)
        lines.append(f"Config: save_confirmation {'ON' if save_conf else 'OFF'}")
        lines.append("")

    elif layer1_handoff:
        # Global fallback path: latest from handoffs/ directory
        s = layer1_handoff['session']
        sessions_loaded.add(s)
        lines.append(f"## Layer 1 — Last Session (S{s})")
        lines.append("")
        for header, text in layer1_handoff['sections'].items():
            lines.append(f"{_section_badge('LAYER1')} **S{s}/{header}**")
            lines.append(text)
            lines.append("")
    else:
        lines.append("## Layer 1 — No handoffs found")
        lines.append("")

    # ─── Layer 2 — Archive Query ───────────────────────────
    if layer2_results:
        l2_filtered = [r for r in layer2_results if r['chunk']['session'] not in sessions_loaded]
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
            if color == 'RED':
                lines.append("\u26a0\ufe0f **Low confidence retrieval.** Query terms spread across sessions or matched weakly. Consider narrowing with more specific terms.")
                lines.append("")
        else:
            lines.append("## Layer 2 — Archive sections already covered by Layer 1")
            lines.append("")
    elif query_used:
        lines.append("## Layer 2 — No archive matches for query")
        lines.append(f"Query: *{query_used}*")
        lines.append("")

    # ─── Footer ────────────────────────────────────────────
    total_words = 0
    if entity_local and entity_local.get('handoff'):
        total_words += sum(len(t.split()) for t in entity_local['handoff']['sections'].values())
    if entity_local and entity_local.get('chunks'):
        total_words += sum(len(c['text'].split()) for c in entity_local['chunks'])
    if not entity_local and layer1_handoff:
        total_words += sum(len(t.split()) for t in layer1_handoff['sections'].values())
    for r in (layer2_results or []):
        if r['chunk']['session'] not in sessions_loaded:
            total_words += len(r['chunk']['text'].split())
    token_est = int(total_words * 0.75)
    session_list = sorted(sessions_loaded | {r['chunk']['session'] for r in (layer2_results or [])})
    lines.append(f"---")
    lines.append(f"Sessions: {', '.join(f'S{s}' for s in session_list)} | ~{token_est} tokens loaded")
    return '\n'.join(lines)


def warm_restore(handoffs_dir, state_dir, query_text=None, entity=None, top_n=3):
    # Resolve active entity
    if not entity:
        state_file = Path(state_dir) / 'active_entity.json'
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
                entity = state.get('entity', '')
            except: entity = ''

    # ─── Layer 1: Two-path architecture (S138) ─────────────
    # P11: entity active → local reads, no entity → global fallback
    entity_local = None
    layer1_global = None
    doctrine_path = str(Path(handoffs_dir).parent / 'doctrine')

    if entity:
        entity_local = get_entity_local_state(doctrine_path, entity, state_dir)
        # If entity-local has no data at all, fall back to global
        if not entity_local.get('handoff') and not entity_local.get('chunks'):
            entity_local = None
            layer1_global = get_latest_handoff(handoffs_dir)
    else:
        layer1_global = get_latest_handoff(handoffs_dir)

    layer1_session = -1
    if entity_local:
        layer1_session = entity_local.get('session', -1)
    elif layer1_global:
        layer1_session = layer1_global['session']

    # ─── Layer 2: SPECTRA archive query (unchanged) ────────
    layer2_results = []
    layer2_margin = 0.0
    signals = []
    if entity: signals.append(entity)
    if query_text: signals.append(query_text)
    query_used = ' '.join(signals)
    if query_used:
        all_handoffs = load_all_handoffs(handoffs_dir)
        archive_handoffs = [h for h in all_handoffs if h['session'] != layer1_session]
        if archive_handoffs:
            corpus = SectionCorpus(archive_handoffs)
            results, layer2_margin = corpus.query(query_used, top_n=top_n)
            layer2_results = corpus.expand_with_siblings(results)
            os.makedirs(state_dir, exist_ok=True)
            corpus.save_index(str(Path(state_dir) / 'warm_restore_index.json'))

    output = format_restore_output(layer1_global, layer2_results, layer2_margin, query_used,
                                   entity_local=entity_local)
    return {'output': output, 'query': query_used, 'entity': entity or '',
            'layer1_session': layer1_session, 'layer2_sections': len(layer2_results),
            'layer2_margin': round(layer2_margin, 1),
            'layer1_path': 'entity-local' if entity_local else 'global'}


if __name__ == '__main__':
    bond_root = os.environ.get('BOND_ROOT', str(Path(__file__).parent))
    handoffs_dir = os.path.join(bond_root, 'handoffs')
    state_dir = os.path.join(bond_root, 'state')
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python warm_restore.py index")
        print('  python warm_restore.py query "your query"')
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
            if ti + 1 < len(sys.argv): top_n = int(sys.argv[ti + 1])
        handoffs = load_all_handoffs(handoffs_dir)
        if not handoffs: print("No handoffs found"); sys.exit(1)
        corpus = SectionCorpus(handoffs)
        results, margin = corpus.query(query_text, top_n=top_n)
        expanded = corpus.expand_with_siblings(results)
        print(f"Query: {query_text}")
        print(f"Margin: {margin:.1f}%")
        print(f"Sections: {len(expanded)} (from {len(results)} direct hits)\n")
        for r in expanded:
            c = r['chunk']
            badge = _section_badge(r['confidence'])
            sc = f"score={r['score']:.4f}" if r['score'] > 0 else ''
            anch = f"anchors={r['anchor_hits']}" if r['anchor_hits'] else ''
            print(f"{badge} S{c['session']}/{c['header']} [{r['confidence']}] {sc} {anch}")
            lines = c['text'].split('\n')
            for line in lines[:3]: print(f"  {line}")
            if len(lines) > 3: print(f"  ... ({len(lines) - 3} more lines)")
            print()
    elif cmd == 'restore':
        query_text = sys.argv[2] if len(sys.argv) > 2 else None
        result = warm_restore(handoffs_dir, state_dir, query_text=query_text)
        print(result['output'])
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
