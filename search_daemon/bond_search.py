"""
BOND Search Daemon — Local Paragraph-Level Search Engine
Phase 1: TF-IDF + Contrastive Anchors (ported from warm_restore SectionCorpus)

Standalone process that:
  - Watches doctrine/ and state/ for changes
  - Derives scope from active_entity.json + link graph
  - Indexes entity .md files at paragraph level
  - Serves search queries via HTTP on port 3003
  - Loads external corpora for SLA v2 retrieval

Usage:
    python bond_search.py                # start daemon
    python bond_search.py --port 3004    # custom port
    python bond_search.py --once "query" # one-shot query, no server

Search Endpoints (Hot Water — SLA pipeline):
    GET /search?q=backflow+prevention          # query the index (auto mode)
    GET /search?q=query&mode=explore             # force editorial weights
    GET /search?q=the+lord+is+my+shepherd&mode=retrieve  # force SLA v2 retrieval
    GET /search?q=pressure&scope=all           # search all entities
    GET /search?q=pressure&entity=P11-Plumber  # local valve: single entity
    GET /load?path=C:/texts/psalms.md          # load external corpus (auto-retrieve)
    GET /load?path=C:/texts/bible/&name=Bible  # load directory with custom name
    GET /unload                                # return to doctrine index
    GET /duplicates                            # find similar paragraphs
    GET /duplicates?threshold=0.6              # lower = more results
    GET /duplicates?exclude_shared=true        # skip shared framework files
    GET /orphans                               # find isolated paragraphs
    GET /orphans?max_sim=0.3                   # higher = more results
    GET /coverage?entity=P11-Plumber           # seed-to-ROOT resonance map
    GET /similarity                            # entity vocabulary overlap
    GET /status                                # index stats, scope, health
    GET /reindex                               # force rebuild

File Ops Endpoints (Cold Water — verbatim, no processing):
    GET  /manifest                             # all files with entity, class, size
    GET  /manifest?entity=P11-Plumber          # single entity manifest
    GET  /read?path=doctrine/P11/ROOT-x.md     # read file verbatim
    POST /write  {"path": "...", "content": "..."}  # write file verbatim
    GET  /copy?from=...&to=...                 # copy file verbatim
    GET  /export                               # full doctrine export to state/export.md
    GET  /export?entity=P11-Plumber            # single entity export
"""

import sys, os, re, json, math, time, threading
from pathlib import Path
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs, unquote

# ─── Config ────────────────────────────────────────────────

BOND_ROOT = os.environ.get('BOND_ROOT', str(Path(__file__).parent.parent))
DOCTRINE_PATH = os.path.join(BOND_ROOT, 'doctrine')
STATE_PATH = os.path.join(BOND_ROOT, 'state')
DEFAULT_PORT = 3003
WATCH_INTERVAL = 2.0  # seconds between file change checks
MIN_PARAGRAPH_LENGTH = 20  # characters — skip tiny fragments

# ─── Text Processing (from warm_restore.py) ────────────────

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
    if word in STEM_EXCEPTIONS:
        return word
    for s in SUFFIXES:
        if word.endswith(s) and len(word) - len(s) >= 4:
            return word[:-len(s)]
    return word

def tokenize(text):
    expanded = text.lower().replace('_', ' ')
    raw = re.findall(r"[a-zA-Z0-9'-]+", expanded)
    return [light_stem(c) for w in raw for c in [w.strip("'-").lower()] if len(c) > 1]

def content_stems(text):
    return [s for s in tokenize(text) if s not in STOP_WORDS and len(s) > 2]


# ─── Scope Derivation ─────────────────────────────────────

def get_active_scope():
    """Read active_entity.json + follow link graph to determine search scope."""
    state_file = Path(STATE_PATH) / 'active_entity.json'
    scope = {
        'active_entity': None,
        'active_class': None,
        'entities': [],
        'mode': 'all',
    }
    try:
        state = json.loads(state_file.read_text(encoding='utf-8'))
        if state.get('entity'):
            scope['active_entity'] = state['entity']
            scope['active_class'] = state.get('class', 'unknown')
            scope['mode'] = 'active'
            scope['entities'].append(state['entity'])
            try:
                config_path = Path(DOCTRINE_PATH) / state['entity'] / 'entity.json'
                config = json.loads(config_path.read_text(encoding='utf-8'))
                for link in config.get('links', []):
                    if link not in scope['entities']:
                        scope['entities'].append(link)
            except Exception:
                pass
    except Exception:
        pass
    if not scope['entities']:
        scope['mode'] = 'all'
        try:
            for entry in Path(DOCTRINE_PATH).iterdir():
                if entry.is_dir():
                    scope['entities'].append(entry.name)
        except Exception:
            pass
    return scope


# ─── Paragraph Extractors ─────────────────────────────────

HEADING_RE = re.compile(r'^(#{1,3})\s+(.+)$')

def _parse_paragraphs(text, entity, filename):
    """Core paragraph parser for both doctrine and external files."""
    paragraphs = []
    current_heading = None
    current_lines = []

    def flush():
        nonlocal current_lines
        if current_lines:
            content = '\n'.join(current_lines).strip()
            if len(content) >= MIN_PARAGRAPH_LENGTH:
                paragraphs.append({
                    'entity': entity,
                    'file': filename,
                    'heading': current_heading,
                    'text': content,
                })
            current_lines = []

    for line in text.split('\n'):
        hm = HEADING_RE.match(line)
        if hm:
            flush()
            current_heading = hm.group(2).strip()
            continue
        if not line.strip():
            flush()
            continue
        if line.strip() in ('---', '```') or line.strip().startswith('<!--'):
            continue
        current_lines.append(line)
    flush()
    return paragraphs


def extract_paragraphs(filepath):
    """Split a doctrine markdown file into paragraphs with metadata."""
    try:
        text = Path(filepath).read_text(encoding='utf-8')
    except Exception:
        return []
    filename = Path(filepath).name
    entity = Path(filepath).parent.name
    return _parse_paragraphs(text, entity, filename)


def extract_external_paragraphs(filepath, corpus_name=None):
    """Extract paragraphs from any .md or .txt file outside doctrine/."""
    fp = Path(filepath)
    if not fp.exists():
        return []
    if not corpus_name:
        corpus_name = fp.parent.name or fp.stem
    try:
        text = fp.read_text(encoding='utf-8')
    except Exception:
        return []
    return _parse_paragraphs(text, corpus_name, fp.name)


def load_external_corpus(path, corpus_name=None):
    """Load paragraphs from a file or directory of files.

    Returns (paragraphs, corpus_name, file_count).
    """
    p = Path(path)
    if not p.exists():
        return [], None, 0
    if not corpus_name:
        corpus_name = p.stem if p.is_file() else p.name
    all_paragraphs = []
    file_count = 0
    if p.is_file():
        all_paragraphs = extract_external_paragraphs(p, corpus_name)
        file_count = 1
    elif p.is_dir():
        for f in sorted(p.iterdir()):
            if f.suffix.lower() in ('.md', '.txt'):
                all_paragraphs.extend(extract_external_paragraphs(f, corpus_name))
                file_count += 1
    return all_paragraphs, corpus_name, file_count


# ─── Search Index ──────────────────────────────────────────

class SearchIndex:
    """TF-IDF + Contrastive Anchor index over paragraphs."""

    def __init__(self, anchor_k=5, confuser_k=3):
        self.anchor_k = anchor_k
        self.confuser_k = confuser_k
        self.paragraphs = []
        self.tokens = []
        self.vocab = set()
        self.df = defaultdict(int)
        self.idf = {}
        self.anchors = []
        self.n = 0
        self.scope = {}
        self.built_at = None
        self.build_time_ms = 0
        self._lock = threading.Lock()

    def build(self, scope=None, force_scope=None, corpus_origin='doctrine'):
        start = time.time()
        if force_scope:
            scope_info = {
                'active_entity': None, 'active_class': None,
                'entities': force_scope if isinstance(force_scope, list) else [force_scope],
                'mode': 'explicit', 'corpus_origin': corpus_origin,
            }
        else:
            scope_info = scope or get_active_scope()
            scope_info['corpus_origin'] = 'doctrine'
        all_paragraphs = []
        for entity_name in scope_info['entities']:
            entity_dir = Path(DOCTRINE_PATH) / entity_name
            if not entity_dir.is_dir():
                continue
            for md_file in entity_dir.glob('*.md'):
                all_paragraphs.extend(extract_paragraphs(md_file))
        stats = self._index_paragraphs(all_paragraphs, scope_info, start)
        return stats

    def build_external(self, path, corpus_name=None):
        start = time.time()
        paragraphs, name, file_count = load_external_corpus(path, corpus_name)
        if not paragraphs:
            return {'error': f'No paragraphs found at {path}', 'paragraphs': 0, 'files': 0}
        scope_info = {
            'active_entity': None, 'active_class': None,
            'entities': [name], 'mode': 'external',
            'corpus_origin': 'external', 'source_path': str(path),
        }
        stats = self._index_paragraphs(paragraphs, scope_info, start)
        stats['corpus_name'] = name
        stats['files'] = file_count
        return stats

    def _index_paragraphs(self, all_paragraphs, scope_info, start):
        def searchable_text(p):
            parts = []
            if p.get('heading'):
                parts.append(p['heading'])
            parts.append(p['file'].replace('.md', '').replace('.txt', '').replace('-', ' '))
            parts.append(p['text'])
            return ' '.join(parts)
        tokens_list = [content_stems(searchable_text(p)) for p in all_paragraphs]
        vocab = set(s for pt in tokens_list for s in pt)
        n = len(all_paragraphs)
        df = defaultdict(int)
        for pt in tokens_list:
            for w in set(pt):
                df[w] += 1
        idf = {}
        for w in vocab:
            if df[w] > 0:
                idf[w] = math.log(n / df[w]) if n > 0 else 0.0
        anchors = []
        if n <= 500:
            anchors = self._build_anchors(n, tokens_list, idf)
        else:
            for i in range(n):
                scores = {w: idf.get(w, 0) for w in set(tokens_list[i])}
                ranked = sorted(scores.items(), key=lambda x: -x[1])[:self.anchor_k]
                anchors.append({w: s for w, s in ranked})
        elapsed = (time.time() - start) * 1000
        with self._lock:
            self.paragraphs = all_paragraphs
            self.tokens = tokens_list
            self.vocab = vocab
            self.df = df
            self.idf = idf
            self.anchors = anchors
            self.n = n
            self.scope = scope_info
            self.built_at = time.strftime('%Y-%m-%dT%H:%M:%S')
            self.build_time_ms = round(elapsed)
        return {
            'paragraphs': n, 'entities': len(scope_info['entities']),
            'vocab': len(vocab), 'build_time_ms': round(elapsed),
            'scope_mode': scope_info['mode'],
        }

    def _build_anchors(self, n, tokens_list, idf):
        anchors = []
        for i in range(n):
            sims = []
            for j in range(n):
                if j == i: continue
                sims.append((j, self._cosine(tokens_list[i], tokens_list[j], idf)))
            sims.sort(key=lambda x: -x[1])
            confusers = [idx for idx, _ in sims[:self.confuser_k]]
            scores = {}
            for w in set(tokens_list[i]):
                presence = sum(1 for ci in confusers if w in set(tokens_list[ci])) / max(len(confusers), 1)
                scores[w] = idf.get(w, 0) * (1.0 - presence)
            ranked = sorted(scores.items(), key=lambda x: -x[1])[:self.anchor_k]
            anchors.append({w: s for w, s in ranked})
        return anchors

    def _cosine(self, a, b, idf):
        sa, sb = set(a), set(b)
        overlap = sa & sb
        if not overlap: return 0.0
        dot = sum(idf.get(w, 0) ** 2 for w in overlap)
        ma = math.sqrt(sum(idf.get(w, 0) ** 2 for w in sa))
        mb = math.sqrt(sum(idf.get(w, 0) ** 2 for w in sb))
        return dot / (ma * mb) if ma and mb else 0.0

    def _bm25(self, tf, df, dl, avgdl, k1=1.5, b=0.75):
        idf = math.log((self.n - df + 0.5) / (df + 0.5) + 1.0)
        tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (dl / avgdl)))
        return idf * tf_norm

    def _phrase_proximity(self, tokens, q_stems):
        if len(q_stems) < 2: return 0.0
        positions = {}
        for i, t in enumerate(tokens):
            if t in q_stems:
                if t not in positions: positions[t] = []
                positions[t].append(i)
        if len(positions) < 2: return 0.0
        all_pos = []
        for stem, pos_list in positions.items():
            for p in pos_list: all_pos.append((p, stem))
        all_pos.sort()
        min_span = float('inf')
        for i in range(len(all_pos)):
            for j in range(i + 1, len(all_pos)):
                if all_pos[j][1] != all_pos[i][1]:
                    span = all_pos[j][0] - all_pos[i][0]
                    min_span = min(min_span, span)
                    break
        if min_span == float('inf'): return 0.0
        return 1.0 / min_span

    def _neighborhood_resonance(self, idx, q_unique):
        p = self.paragraphs[idx]
        neighbors = []
        for j in range(max(0, idx - 2), min(self.n, idx + 3)):
            if j == idx: continue
            pj = self.paragraphs[j]
            if pj['entity'] == p['entity'] and pj['file'] == p['file']:
                neighbors.append(j)
        if not neighbors: return 0.0
        total = 0.0
        for ni in neighbors:
            overlap = q_unique & set(self.tokens[ni])
            total += sum(self.idf.get(w, 0) for w in overlap)
        return total / len(neighbors)

    def _resolve_mode(self, mode):
        if mode != 'auto': return mode
        origin = self.scope.get('corpus_origin', 'doctrine')
        if origin == 'external': return 'retrieve'
        return 'explore'

    def search(self, query_text, top_n=10, anchor_weight=15, nbr_weight=10,
               entity_boost=1.3, entity_filter=None, mode='auto'):
        with self._lock:
            if self.n == 0:
                return {'results': [], 'margin': 0.0, 'query': query_text, 'indexed': 0}
            mode = self._resolve_mode(mode)
            q_stems = content_stems(query_text)
            q_unique = set(q_stems)
            if not q_unique:
                return {'results': [], 'margin': 0.0, 'query': query_text, 'indexed': self.n}
            avgdl = sum(len(pt) for pt in self.tokens) / max(self.n, 1)
            boosted_entities = set()
            active = self.scope.get('active_entity')
            if active:
                boosted_entities.add(active)
                for ent in self.scope.get('entities', []): boosted_entities.add(ent)
            qs = max(len(q_unique), 1)
            scores = []
            for i, pt in enumerate(self.tokens):
                p = self.paragraphs[i]
                if entity_filter and p['entity'] != entity_filter: continue
                overlap = q_unique & set(pt)
                if not overlap:
                    scores.append((i, 0.0, overlap))
                    continue
                dl = len(pt)
                bm25_score = 0.0
                for w in overlap:
                    tf = pt.count(w)
                    df = self.df.get(w, 1)
                    bm25_score += self._bm25(tf, df, dl, avgdl)
                coverage = len(overlap) / qs
                score = bm25_score * (1.0 + coverage * 0.5)
                proximity = self._phrase_proximity(pt, q_unique)
                score *= (1.0 + proximity * 0.5)
                if mode == 'explore':
                    fname = p['file']
                    if fname.startswith('ROOT-') or fname.startswith('ROOT_'): score *= 1.5
                    elif fname.startswith('G-pruned-') or fname.startswith('_pruned_'): score *= 0.5
                    if boosted_entities and p['entity'] in boosted_entities: score *= entity_boost
                scores.append((i, score, overlap))
            scores.sort(key=lambda x: -x[1])
            seen_groups = {}
            deduped = []
            for idx, sc, overlap in scores:
                if sc == 0: continue
                p = self.paragraphs[idx]
                group_key = (p['entity'], p['file'], p['heading'] or '')
                if group_key in seen_groups:
                    seen_groups[group_key][2] += 1
                    continue
                anchor_hits = []
                if idx < len(self.anchors):
                    anchor_hits = [w for w in self.anchors[idx] if w in q_unique]
                result = {
                    'entity': p['entity'], 'file': p['file'], 'heading': p['heading'],
                    'text': p['text'], 'score': round(sc, 4),
                    'overlap': list(overlap), 'anchor_hits': anchor_hits, 'siblings': 0,
                }
                seen_groups[group_key] = [result, idx, 1]
                deduped.append(group_key)
                if len(deduped) >= top_n: break
            results = []
            result_indices = []
            for key in deduped:
                r, idx, count = seen_groups[key]
                r['siblings'] = count - 1
                results.append(r)
                result_indices.append(idx)
            if len(results) >= 2:
                raw = (results[0]['score'] - results[1]['score']) / max(results[0]['score'], 1e-10) * 100
                ad = len(results[0].get('anchor_hits', [])) - len(results[1].get('anchor_hits', []))
                anchor_adj = anchor_weight * ad
                if mode == 'retrieve':
                    top_nbr = self._neighborhood_resonance(result_indices[0], q_unique)
                    run_nbr = self._neighborhood_resonance(result_indices[1], q_unique)
                    if max(top_nbr, run_nbr) > 0:
                        nbr_diff = (top_nbr - run_nbr) / max(top_nbr, run_nbr)
                    else: nbr_diff = 0.0
                    nbr_adj = nbr_weight * nbr_diff
                    type_adj = 0.0
                    for ri, r in enumerate(results[:2]):
                        fname = r['file']
                        sign = 1.0 if ri == 0 else -1.0
                        if fname.startswith('ROOT-') or fname.startswith('ROOT_'): type_adj += sign * 5.0
                        elif fname.startswith('G-pruned-') or fname.startswith('_pruned_'): type_adj -= sign * 5.0
                    margin = min(max(raw + anchor_adj + nbr_adj + type_adj, 0.1), 100.0)
                else:
                    margin = min(max(raw + anchor_adj, 0.1), 100.0)
            elif len(results) == 1: margin = 100.0
            else: margin = 0.0
            if mode == 'retrieve':
                gate = 'HIGH' if margin > 50 else 'MED' if margin > 15 else 'LOW'
                for r in results: r['confidence'] = gate
            else:
                top_score = results[0]['score'] if results else 0.0
                for r in results:
                    if top_score == 0: r['confidence'] = 'LOW'
                    else:
                        ratio = r['score'] / top_score
                        r['confidence'] = 'HIGH' if ratio >= 0.7 else 'MED' if ratio >= 0.35 else 'LOW'
            return {
                'results': results, 'margin': round(margin, 1), 'query': query_text,
                'mode': mode, 'indexed': self.n,
                'scope': self.scope.get('mode', 'unknown'),
                'active_entity': self.scope.get('active_entity'),
            }

    def find_duplicates(self, threshold=0.75, top_n=20, exclude_shared=False):
        with self._lock:
            if self.n == 0: return {'duplicates': [], 'scanned': 0}
            pairs = []
            for i in range(self.n):
                for j in range(i + 1, self.n):
                    pi, pj = self.paragraphs[i], self.paragraphs[j]
                    if pi['entity'] == pj['entity'] and pi['file'] == pj['file']: continue
                    if exclude_shared and pi['file'] == pj['file'] and pi['entity'] != pj['entity']: continue
                    sim = self._cosine(self.tokens[i], self.tokens[j], self.idf)
                    if sim >= threshold:
                        pairs.append({
                            'similarity': round(sim, 4),
                            'a': {'entity': pi['entity'], 'file': pi['file'], 'heading': pi['heading'], 'text': pi['text'][:200]},
                            'b': {'entity': pj['entity'], 'file': pj['file'], 'heading': pj['heading'], 'text': pj['text'][:200]},
                        })
            pairs.sort(key=lambda x: -x['similarity'])
            return {'duplicates': pairs[:top_n], 'total_found': len(pairs),
                    'threshold': threshold, 'exclude_shared': exclude_shared, 'scanned': self.n}

    def find_orphans(self, max_sim=0.25, top_n=20):
        with self._lock:
            if self.n == 0: return {'orphans': [], 'scanned': 0}
            isolation_scores = []
            for i in range(self.n):
                if not self.tokens[i]: continue
                max_cosine = 0.0
                for j in range(self.n):
                    if j == i: continue
                    sim = self._cosine(self.tokens[i], self.tokens[j], self.idf)
                    if sim > max_cosine: max_cosine = sim
                p = self.paragraphs[i]
                if max_cosine <= max_sim:
                    fname = p['file']
                    if fname.startswith('ROOT-') or fname.startswith('ROOT_'): doc_type = 'root'
                    elif fname.startswith('G-pruned-') or fname.startswith('_pruned_'): doc_type = 'pruned'
                    elif fname.startswith('CORE') or fname == 'entity.json': doc_type = 'core'
                    else: doc_type = 'seed'
                    isolation_scores.append({
                        'max_similarity': round(max_cosine, 4), 'entity': p['entity'],
                        'file': p['file'], 'heading': p['heading'],
                        'doc_type': doc_type, 'text': p['text'][:200],
                    })
            isolation_scores.sort(key=lambda x: x['max_similarity'])
            return {'orphans': isolation_scores[:top_n], 'total_found': len(isolation_scores),
                    'max_sim_threshold': max_sim, 'scanned': self.n}

    def seed_coverage(self, entity_name):
        with self._lock:
            if self.n == 0: return {'error': 'Index empty'}
            root_indices = []
            seed_indices = []
            for i, p in enumerate(self.paragraphs):
                if p['entity'] != entity_name: continue
                fname = p['file']
                if fname.startswith('ROOT-') or fname.startswith('ROOT_'): root_indices.append(i)
                elif not fname.startswith('G-pruned-') and not fname.startswith('_pruned_'): seed_indices.append(i)
            if not root_indices: return {'entity': entity_name, 'error': 'No ROOTs found', 'roots': 0, 'seeds': 0}
            if not seed_indices: return {'entity': entity_name, 'error': 'No seeds found', 'roots': len(root_indices), 'seeds': 0}
            coverage = []
            for si in seed_indices:
                best_root_sim = 0.0
                best_root = None
                for ri in root_indices:
                    sim = self._cosine(self.tokens[si], self.tokens[ri], self.idf)
                    if sim > best_root_sim:
                        best_root_sim = sim
                        best_root = self.paragraphs[ri]['file']
                sp = self.paragraphs[si]
                coverage.append({'file': sp['file'], 'heading': sp['heading'],
                                 'best_root': best_root, 'root_similarity': round(best_root_sim, 4)})
            coverage.sort(key=lambda x: -x['root_similarity'])
            avg_sim = sum(c['root_similarity'] for c in coverage) / len(coverage) if coverage else 0
            weak = [c for c in coverage if c['root_similarity'] < 0.1]
            return {'entity': entity_name, 'roots': len(set(self.paragraphs[i]['file'] for i in root_indices)),
                    'seeds': len(set(self.paragraphs[i]['file'] for i in seed_indices)),
                    'avg_root_similarity': round(avg_sim, 4), 'weak_seeds': len(weak), 'coverage': coverage}

    def entity_similarity(self):
        with self._lock:
            if self.n == 0: return {'pairs': [], 'entities': 0}
            entity_tokens = defaultdict(set)
            for i, p in enumerate(self.paragraphs):
                entity_tokens[p['entity']].update(set(self.tokens[i]))
            entities = sorted(entity_tokens.keys())
            pairs = []
            for i in range(len(entities)):
                for j in range(i + 1, len(entities)):
                    ea, eb = entities[i], entities[j]
                    sa, sb = entity_tokens[ea], entity_tokens[eb]
                    overlap = sa & sb
                    sim = len(overlap) / len(sa | sb) if overlap else 0.0
                    pairs.append({'a': ea, 'b': eb, 'similarity': round(sim, 4),
                                  'shared_terms': len(overlap), 'a_terms': len(sa), 'b_terms': len(sb)})
            pairs.sort(key=lambda x: -x['similarity'])
            return {'pairs': pairs, 'entities': len(entities)}

    def status(self):
        with self._lock:
            return {
                'paragraphs': self.n, 'entities': self.scope.get('entities', []),
                'entity_count': len(self.scope.get('entities', [])),
                'vocab_size': len(self.vocab), 'scope_mode': self.scope.get('mode', 'none'),
                'corpus_origin': self.scope.get('corpus_origin', 'doctrine'),
                'source_path': self.scope.get('source_path'),
                'active_entity': self.scope.get('active_entity'),
                'built_at': self.built_at, 'build_time_ms': self.build_time_ms,
                'anchors': len(self.anchors),
            }


# ─── File Watcher ──────────────────────────────────────────

class FileWatcher:
    def __init__(self, index, interval=WATCH_INTERVAL):
        self.index = index
        self.interval = interval
        self._signatures = {}
        self._running = False
        self._paused = False
        self._thread = None

    def _snapshot(self):
        sigs = {}
        state_file = Path(STATE_PATH) / 'active_entity.json'
        try: sigs['__state__'] = state_file.stat().st_mtime
        except Exception: pass
        scope = get_active_scope()
        for entity_name in scope['entities']:
            entity_dir = Path(DOCTRINE_PATH) / entity_name
            if not entity_dir.is_dir(): continue
            for md_file in entity_dir.glob('*.md'):
                try: sigs[str(md_file)] = md_file.stat().st_mtime
                except Exception: pass
        return sigs, scope

    def _watch_loop(self):
        while self._running:
            try:
                if not self._paused:
                    new_sigs, scope = self._snapshot()
                    if new_sigs != self._signatures:
                        self._signatures = new_sigs
                        stats = self.index.build(scope=scope)
                        ts = time.strftime('%H:%M:%S')
                        print(f"  [{ts}] Reindexed: {stats['paragraphs']} paragraphs from {stats['entities']} entities ({stats['build_time_ms']}ms)")
            except Exception as e:
                print(f"  Watch error: {e}", file=sys.stderr)
            time.sleep(self.interval)

    def start(self):
        self._running = True
        sigs, scope = self._snapshot()
        self._signatures = sigs
        stats = self.index.build(scope=scope)
        print(f"  Initial index: {stats['paragraphs']} paragraphs, {stats['vocab']} vocab, {stats['entities']} entities ({stats['build_time_ms']}ms)")
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False
        self._signatures = {}


# ─── File Operations (Cold Water) ──────────────────────────
# Raw read/write/copy/export — no SLA pipeline, no tokenization.
# All paths scoped to BOND_ROOT. Write ops logged.

class FileOps:
    """Verbatim file operations within BOND_ROOT. No processing."""

    def __init__(self, bond_root, state_path, doctrine_path):
        self.bond_root = Path(bond_root).resolve()
        self.state_path = Path(state_path)
        self.doctrine_path = Path(doctrine_path)
        self.log_path = self.state_path / 'file_ops.log'

    def _safe_path(self, rel_path):
        """Resolve path and verify it's within BOND_ROOT."""
        resolved = (self.bond_root / rel_path).resolve()
        if not str(resolved).startswith(str(self.bond_root)):
            return None, 'Path escapes BOND_ROOT boundary'
        return resolved, None

    def _log(self, op, path, detail=''):
        """Append-only write log for auditability."""
        ts = time.strftime('%Y-%m-%dT%H:%M:%S')
        entry = f"[{ts}] {op}: {path}"
        if detail: entry += f" | {detail}"
        try:
            os.makedirs(self.state_path, exist_ok=True)
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(entry + '\n')
        except Exception: pass

    def manifest(self, entity_filter=None):
        """List all files with metadata. Computed on call, never cached."""
        files = []
        if not self.doctrine_path.is_dir():
            return {'files': files, 'entities': 0, 'total_size': 0}
        entities_found = set()
        for entity_dir in sorted(self.doctrine_path.iterdir()):
            if not entity_dir.is_dir(): continue
            entity_name = entity_dir.name
            if entity_filter and entity_name != entity_filter: continue
            entities_found.add(entity_name)
            entity_class = 'unknown'
            try:
                ej = json.loads((entity_dir / 'entity.json').read_text(encoding='utf-8'))
                entity_class = ej.get('class', 'unknown')
            except Exception: pass
            for f in sorted(entity_dir.iterdir()):
                if f.is_dir():
                    for sf in sorted(f.iterdir()):
                        if sf.is_file():
                            stat = sf.stat()
                            files.append({
                                'entity': entity_name, 'class': entity_class,
                                'path': str(sf.relative_to(self.bond_root)),
                                'file': f"{f.name}/{sf.name}", 'size': stat.st_size,
                                'modified': time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(stat.st_mtime)),
                            })
                elif f.is_file():
                    stat = f.stat()
                    files.append({
                        'entity': entity_name, 'class': entity_class,
                        'path': str(f.relative_to(self.bond_root)),
                        'file': f.name, 'size': stat.st_size,
                        'modified': time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(stat.st_mtime)),
                    })
        total_size = sum(f['size'] for f in files)
        return {'files': files, 'entities': len(entities_found), 'total_size': total_size, 'file_count': len(files)}

    def read(self, rel_path):
        """Read file verbatim. Returns raw content."""
        resolved, err = self._safe_path(rel_path)
        if err: return {'error': err}
        if not resolved.is_file(): return {'error': f'Not a file: {rel_path}'}
        try:
            content = resolved.read_text(encoding='utf-8')
            return {'path': rel_path, 'content': content, 'size': len(content), 'lines': content.count('\n') + 1}
        except Exception as e:
            return {'error': f'Read failed: {e}'}

    def write(self, rel_path, content):
        """Write content verbatim to file."""
        resolved, err = self._safe_path(rel_path)
        if err: return {'error': err}
        try:
            os.makedirs(resolved.parent, exist_ok=True)
            existed = resolved.is_file()
            resolved.write_text(content, encoding='utf-8')
            op = 'OVERWRITE' if existed else 'CREATE'
            self._log(op, rel_path, f"{len(content)} bytes")
            return {'path': rel_path, 'operation': op.lower(), 'size': len(content), 'lines': content.count('\n') + 1}
        except Exception as e:
            return {'error': f'Write failed: {e}'}

    def copy(self, from_rel, to_rel):
        """Copy file verbatim from one path to another."""
        from_resolved, err = self._safe_path(from_rel)
        if err: return {'error': f'Source: {err}'}
        to_resolved, err = self._safe_path(to_rel)
        if err: return {'error': f'Destination: {err}'}
        if not from_resolved.is_file(): return {'error': f'Source not found: {from_rel}'}
        try:
            content = from_resolved.read_text(encoding='utf-8')
            os.makedirs(to_resolved.parent, exist_ok=True)
            existed = to_resolved.is_file()
            to_resolved.write_text(content, encoding='utf-8')
            op = 'COPY_OVER' if existed else 'COPY_NEW'
            self._log(op, f"{from_rel} -> {to_rel}", f"{len(content)} bytes")
            return {'from': from_rel, 'to': to_rel, 'operation': op.lower(), 'size': len(content)}
        except Exception as e:
            return {'error': f'Copy failed: {e}'}

    def export(self, entity_filter=None, output_path=None):
        """Assemble all doctrine files into a single markdown document, verbatim."""
        if not output_path: output_path = self.state_path / 'export.md'
        else: output_path = Path(output_path)
        lines = ['# BOND Doctrine Export']
        lines.append(f"_Generated: {time.strftime('%Y-%m-%dT%H:%M:%S')}_")
        lines.append('')
        file_count = 0
        total_chars = 0
        entities_exported = set()
        for entity_dir in sorted(self.doctrine_path.iterdir()):
            if not entity_dir.is_dir(): continue
            entity_name = entity_dir.name
            if entity_filter and entity_name != entity_filter: continue
            entity_class = 'unknown'
            try:
                ej = json.loads((entity_dir / 'entity.json').read_text(encoding='utf-8'))
                entity_class = ej.get('class', 'unknown')
            except Exception: pass
            entities_exported.add(entity_name)
            lines.append(f"---")
            lines.append(f"## {entity_name} ({entity_class})")
            lines.append('')
            for f in sorted(entity_dir.iterdir()):
                if not f.is_file(): continue
                try:
                    content = f.read_text(encoding='utf-8')
                    lines.append(f"### {f.name}")
                    lines.append(f"<!-- {len(content)} chars -->")
                    lines.append('')
                    lines.append(content)
                    lines.append('')
                    file_count += 1
                    total_chars += len(content)
                except Exception:
                    lines.append(f"### {f.name}")
                    lines.append('_[read error]_')
                    lines.append('')
        lines.append('---')
        lines.append(f"_Export complete: {file_count} files from {len(entities_exported)} entities, ~{total_chars} chars_")
        output_text = '\n'.join(lines)
        os.makedirs(output_path.parent, exist_ok=True)
        output_path.write_text(output_text, encoding='utf-8')
        self._log('EXPORT', str(output_path), f"{file_count} files, {len(entities_exported)} entities")
        return {
            'output_path': str(output_path), 'entities': len(entities_exported),
            'files': file_count, 'total_chars': total_chars,
            'token_estimate': int(total_chars * 0.25),
        }


file_ops = FileOps(BOND_ROOT, STATE_PATH, DOCTRINE_PATH)


# ─── HTTP Server ───────────────────────────────────────────

index = SearchIndex()
watcher = FileWatcher(index)


class SearchHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        params = parse_qs(parsed.query)

        if path == '/search':
            query = params.get('q', [''])[0]
            if not query:
                self._json(400, {'error': 'Missing ?q= parameter'})
                return
            top_n = int(params.get('top', ['10'])[0])
            scope_override = params.get('scope', [None])[0]
            entity_filter = params.get('entity', [None])[0]
            mode = params.get('mode', ['auto'])[0]
            if mode not in ('auto', 'explore', 'retrieve'): mode = 'auto'
            if scope_override == 'all':
                all_entities = []
                try:
                    for entry in Path(DOCTRINE_PATH).iterdir():
                        if entry.is_dir(): all_entities.append(entry.name)
                except Exception: pass
                temp = SearchIndex()
                temp.build(force_scope=all_entities)
                result = temp.search(query, top_n=top_n, entity_filter=entity_filter, mode=mode)
            else:
                result = index.search(query, top_n=top_n, entity_filter=entity_filter, mode=mode)
            self._json(200, result)

        elif path == '/load':
            file_path = params.get('path', [''])[0]
            if not file_path:
                self._json(400, {'error': 'Missing ?path= parameter'})
                return
            file_path = unquote(file_path)
            corpus_name = params.get('name', [None])[0]
            watcher.pause()
            stats = index.build_external(file_path, corpus_name)
            if 'error' in stats:
                watcher.resume()
                self._json(400, stats)
            else:
                ts = time.strftime('%H:%M:%S')
                print(f"  [{ts}] External corpus loaded: {stats['paragraphs']} paragraphs from {stats.get('files', '?')} files ({stats['build_time_ms']}ms)")
                self._json(200, {'loaded': True, 'watcher': 'paused', **stats})

        elif path == '/unload':
            watcher.resume()
            ts = time.strftime('%H:%M:%S')
            print(f"  [{ts}] External corpus unloaded, resuming doctrine watch")
            self._json(200, {'unloaded': True, 'watcher': 'resumed'})

        elif path == '/status':
            self._json(200, index.status())
        elif path == '/reindex':
            stats = index.build()
            self._json(200, {'reindexed': True, **stats})
        elif path == '/duplicates':
            threshold = float(params.get('threshold', ['0.75'])[0])
            top_n = int(params.get('top', ['20'])[0])
            exclude_shared = params.get('exclude_shared', ['false'])[0].lower() == 'true'
            result = index.find_duplicates(threshold=threshold, top_n=top_n, exclude_shared=exclude_shared)
            self._json(200, result)
        elif path == '/orphans':
            max_sim = float(params.get('max_sim', ['0.25'])[0])
            top_n = int(params.get('top', ['20'])[0])
            result = index.find_orphans(max_sim=max_sim, top_n=top_n)
            self._json(200, result)
        elif path == '/coverage':
            entity = params.get('entity', [None])[0]
            if not entity:
                self._json(400, {'error': 'Missing ?entity= parameter'})
                return
            result = index.seed_coverage(entity)
            self._json(200, result)
        elif path == '/similarity':
            result = index.entity_similarity()
            self._json(200, result)

        # ── File Operations (Cold Water) ──
        elif path == '/manifest':
            entity = params.get('entity', [None])[0]
            result = file_ops.manifest(entity_filter=entity)
            self._json(200, result)

        elif path == '/read':
            file_path = params.get('path', [''])[0]
            if not file_path:
                self._json(400, {'error': 'Missing ?path= parameter'})
                return
            file_path = unquote(file_path)
            result = file_ops.read(file_path)
            if 'error' in result: self._json(400, result)
            else: self._json(200, result)

        elif path == '/copy':
            from_path = params.get('from', [''])[0]
            to_path = params.get('to', [''])[0]
            if not from_path or not to_path:
                self._json(400, {'error': 'Missing ?from= and ?to= parameters'})
                return
            from_path = unquote(from_path)
            to_path = unquote(to_path)
            result = file_ops.copy(from_path, to_path)
            if 'error' in result: self._json(400, result)
            else: self._json(200, result)

        elif path == '/export':
            entity = params.get('entity', [None])[0]
            output = params.get('output', [None])[0]
            if output: output = unquote(output)
            result = file_ops.export(entity_filter=entity, output_path=output)
            if 'error' in result: self._json(400, result)
            else: self._json(200, result)

        else:
            self._json(404, {'error': 'Endpoints: /search, /load, /unload, /duplicates, /orphans, /coverage, /similarity, /status, /reindex, /manifest, /read, /write, /copy, /export'})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        if path == '/write':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length).decode('utf-8'))
            except Exception as e:
                self._json(400, {'error': f'Invalid JSON body: {e}'})
                return
            file_path = body.get('path', '')
            content = body.get('content', '')
            if not file_path:
                self._json(400, {'error': 'Missing "path" in body'})
                return
            if content is None:
                self._json(400, {'error': 'Missing "content" in body'})
                return
            result = file_ops.write(file_path, content)
            if 'error' in result: self._json(400, result)
            else: self._json(200, result)
        else:
            self._json(404, {'error': 'POST endpoints: /write'})

    def _json(self, code, data):
        body = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        if args and '404' in str(args[0]):
            super().log_message(format, *args)


# ─── CLI Entry Point ──────────────────────────────────────

def write_results_file(results, output_path=None):
    if not output_path:
        output_path = os.path.join(STATE_PATH, 'search_results.md')
    lines = [f"# Search Results", f"_Query: {results['query']}_", '']
    if not results['results']:
        lines.append('No results found.')
    else:
        lines.append(f"**{len(results['results'])} results** | Scope: {results.get('scope', 'unknown')} | Margin: {results.get('margin', 0)}%")
        lines.append('')
        for i, r in enumerate(results['results'], 1):
            conf = {'HIGH': '\U0001f7e2', 'MED': '\U0001f7e1', 'LOW': '\U0001f534'}.get(r.get('confidence', 'LOW'), '\u26aa')
            heading = f" > {r['heading']}" if r.get('heading') else ''
            sibling_tag = f" (+{r['siblings']} more)" if r.get('siblings', 0) > 0 else ''
            lines.append(f"### {conf} {i}. {r['entity']}/{r['file']}{heading}{sibling_tag}")
            lines.append(f"Score: {r['score']} | Overlap: {', '.join(r.get('overlap', []))} | Anchors: {', '.join(r.get('anchor_hits', []))}")
            lines.append('')
            text = r['text']
            if len(text) > 500: text = text[:500] + '...'
            lines.append(text)
            lines.append('')
    Path(output_path).write_text('\n'.join(lines), encoding='utf-8')
    return output_path


if __name__ == '__main__':
    port = DEFAULT_PORT
    if '--port' in sys.argv:
        pi = sys.argv.index('--port')
        if pi + 1 < len(sys.argv): port = int(sys.argv[pi + 1])
    if '--once' in sys.argv:
        qi = sys.argv.index('--once')
        if qi + 1 >= len(sys.argv):
            print('Usage: python bond_search.py --once "your query"')
            sys.exit(1)
        query = sys.argv[qi + 1]
        stats = index.build()
        print(f"Indexed {stats['paragraphs']} paragraphs from {stats['entities']} entities ({stats['build_time_ms']}ms)")
        results = index.search(query)
        path = write_results_file(results)
        print(f"\nQuery: {query}")
        print(f"Results: {len(results['results'])} | Margin: {results['margin']}%")
        for r in results['results']:
            conf = {'HIGH': '\U0001f7e2', 'MED': '\U0001f7e1', 'LOW': '\U0001f534'}.get(r.get('confidence'), '\u26aa')
            sib = f" (+{r['siblings']})" if r.get('siblings', 0) > 0 else ''
            print(f"  {conf} {r['entity']}/{r['file']} -- {r['score']} -- {r.get('heading', '')}{sib}")
        print(f"\nResults written to: {path}")
        sys.exit(0)

    print(f"\U0001f50d BOND Search Daemon starting on port {port}")
    print(f"   BOND_ROOT: {BOND_ROOT}")
    print(f"   Doctrine:  {DOCTRINE_PATH}")
    print(f"   State:     {STATE_PATH}")
    print()
    watcher.start()
    print()
    print(f"   Search (Hot Water):")
    print(f"     GET http://localhost:{port}/search?q=your+query")
    print(f"     GET http://localhost:{port}/search?q=query&mode=retrieve")
    print(f"     GET http://localhost:{port}/search?q=query&scope=all")
    print(f"     GET http://localhost:{port}/load?path=C:/texts/psalms.md")
    print(f"     GET http://localhost:{port}/unload")
    print(f"     GET http://localhost:{port}/duplicates")
    print(f"     GET http://localhost:{port}/orphans")
    print(f"     GET http://localhost:{port}/coverage?entity=P11-Plumber")
    print(f"     GET http://localhost:{port}/similarity")
    print(f"     GET http://localhost:{port}/status")
    print(f"     GET http://localhost:{port}/reindex")
    print()
    print(f"   File Ops (Cold Water):")
    print(f"     GET  http://localhost:{port}/manifest")
    print(f"     GET  http://localhost:{port}/manifest?entity=P11-Plumber")
    print(f"     GET  http://localhost:{port}/read?path=doctrine/P11-Plumber/ROOT-build-for-access.md")
    print(f"     POST http://localhost:{port}/write  body: {{\"path\": \"...\", \"content\": \"...\"}}")
    print(f"     GET  http://localhost:{port}/copy?from=...&to=...")
    print(f"     GET  http://localhost:{port}/export")
    print(f"     GET  http://localhost:{port}/export?entity=P11-Plumber")
    print()

    class ThreadedServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

    try:
        server = ThreadedServer(('127.0.0.1', port), SearchHandler)
        print(f"\U0001f525 Search daemon listening on http://localhost:{port}")
        print(f"   Watching for file changes every {WATCH_INTERVAL}s")
        print()
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\U0001f6d1 Search daemon stopped")
        watcher.stop()
        sys.exit(0)
