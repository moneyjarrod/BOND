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
    python bond_search.py                          # start daemon
    python bond_search.py --port 3004              # custom port
    python bond_search.py --root C:/Projects/BOND  # custom BOND_ROOT
    python bond_search.py --once "query"            # one-shot query, no server

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

Composite Payloads (Data Assembly Layer — one call replaces many):
    GET  /sync-complete                        # {Sync} steps 1-5 (no vine scores)
    POST /sync-complete {"text": "...", "session": "S124"}  # steps 1-5 + vine scores + tracker writes
    # D11: sync-complete includes state/handoff.md content
    # D12: linked entities return entity.json identity only (tier 1)
    GET  /enter-payload?entity=BOND_MASTER     # {Enter} in one call: entity files + linked files
    GET  /vine-data?perspective=P11-Plumber    # vine lifecycle: tracker, roots, seeds, pruned
    GET  /obligations                          # derived obligations + warnings from state

Daemon Heat Map (bypasses class matrix):
    GET /heatmap-touch?concepts=a,b,c&context=why         # mark concepts active
    GET /heatmap-hot                                      # top concepts by recency
    GET /heatmap-chunk                                    # formatted for {Chunk}
    GET /heatmap-clear                                    # reset for new session

QAIS Resonance (Daemon-local vine scoring):
    GET /resonance-test?perspective=P11-Plumber&text=...  # single perspective
    GET /resonance-multi?text=...                         # all armed perspectives

"""

import sys, os, re, json, math, time, threading, shutil, fnmatch
from pathlib import Path
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs, unquote

# D13: PowerShell Execution module
try:
    from powershell_exec import PowerShellExecutor
except ImportError:
    PowerShellExecutor = None

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
        """Build index from doctrine entity files. Thread-safe.

        corpus_origin: 'doctrine' (default) or 'external'
        Set at ingest time — determines auto mode routing.
        """
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
        """Build index from an external file or directory. Sets corpus_origin='external'.

        This is the ingest path for alien corpora (Psalms, etc).
        Auto mode will resolve to 'retrieve' for all searches.
        """
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
        """Shared indexing logic for both doctrine and external builds."""
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
        """Contrastive anchors — words that distinguish each paragraph from its neighbors."""
        anchors = []
        for i in range(n):
            sims = []
            for j in range(n):
                if j == i:
                    continue
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
        if not overlap:
            return 0.0
        dot = sum(idf.get(w, 0) ** 2 for w in overlap)
        ma = math.sqrt(sum(idf.get(w, 0) ** 2 for w in sa))
        mb = math.sqrt(sum(idf.get(w, 0) ** 2 for w in sb))
        return dot / (ma * mb) if ma and mb else 0.0

    def _bm25(self, tf, df, dl, avgdl, k1=1.5, b=0.75):
        idf = math.log((self.n - df + 0.5) / (df + 0.5) + 1.0)
        tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (dl / avgdl)))
        return idf * tf_norm

    def _phrase_proximity(self, tokens, q_stems):
        if len(q_stems) < 2:
            return 0.0
        positions = {}
        for i, t in enumerate(tokens):
            if t in q_stems:
                if t not in positions:
                    positions[t] = []
                positions[t].append(i)
        if len(positions) < 2:
            return 0.0
        all_pos = []
        for stem, pos_list in positions.items():
            for p in pos_list:
                all_pos.append((p, stem))
        all_pos.sort()
        min_span = float('inf')
        for i in range(len(all_pos)):
            for j in range(i + 1, len(all_pos)):
                if all_pos[j][1] != all_pos[i][1]:
                    span = all_pos[j][0] - all_pos[i][0]
                    min_span = min(min_span, span)
                    break
        if min_span == float('inf'):
            return 0.0
        return 1.0 / min_span

    def _neighborhood_resonance(self, idx, q_unique):
        """Average IDF overlap of a paragraph's sequential neighbors with query."""
        p = self.paragraphs[idx]
        neighbors = []
        for j in range(max(0, idx - 2), min(self.n, idx + 3)):
            if j == idx:
                continue
            pj = self.paragraphs[j]
            if pj['entity'] == p['entity'] and pj['file'] == p['file']:
                neighbors.append(j)
        if not neighbors:
            return 0.0
        total = 0.0
        for ni in neighbors:
            overlap = q_unique & set(self.tokens[ni])
            total += sum(self.idf.get(w, 0) for w in overlap)
        return total / len(neighbors)

    def _resolve_mode(self, mode):
        """Auto-resolve search mode from context.

        corpus_origin is authoritative — set when the index is built,
        not guessed from file naming conventions.
        """
        if mode != 'auto':
            return mode
        origin = self.scope.get('corpus_origin', 'doctrine')
        if origin == 'external':
            return 'retrieve'
        return 'explore'

    def search(self, query_text, top_n=10, anchor_weight=15, nbr_weight=10,
               entity_boost=1.3, entity_filter=None, mode='auto'):
        """Search the index.

        mode='auto'     — daemon decides from context (default)
        mode='explore'  — editorial weights in score (doctrine browsing)
        mode='retrieve' — pure BM25 ranking, adjustments to margin only (SLA v2)
        """
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
                for ent in self.scope.get('entities', []):
                    boosted_entities.add(ent)

            qs = max(len(q_unique), 1)
            scores = []
            for i, pt in enumerate(self.tokens):
                p = self.paragraphs[i]
                if entity_filter and p['entity'] != entity_filter:
                    continue
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
                # Mode-dependent scoring
                if mode == 'explore':
                    fname = p['file']
                    if fname.startswith('ROOT-') or fname.startswith('ROOT_'):
                        score *= 1.5
                    elif fname.startswith('G-pruned-') or fname.startswith('_pruned_'):
                        score *= 0.5
                    if boosted_entities and p['entity'] in boosted_entities:
                        score *= entity_boost
                scores.append((i, score, overlap))

            scores.sort(key=lambda x: -x[1])

            # Dedup
            seen_groups = {}
            deduped = []
            for idx, sc, overlap in scores:
                if sc == 0:
                    continue
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
                if len(deduped) >= top_n:
                    break

            results = []
            result_indices = []
            for key in deduped:
                r, idx, count = seen_groups[key]
                r['siblings'] = count - 1
                results.append(r)
                result_indices.append(idx)

            # Margin calculation
            if len(results) >= 2:
                raw = (results[0]['score'] - results[1]['score']) / max(results[0]['score'], 1e-10) * 100
                ad = len(results[0].get('anchor_hits', [])) - len(results[1].get('anchor_hits', []))
                anchor_adj = anchor_weight * ad
                if mode == 'retrieve':
                    top_nbr = self._neighborhood_resonance(result_indices[0], q_unique)
                    run_nbr = self._neighborhood_resonance(result_indices[1], q_unique)
                    if max(top_nbr, run_nbr) > 0:
                        nbr_diff = (top_nbr - run_nbr) / max(top_nbr, run_nbr)
                    else:
                        nbr_diff = 0.0
                    nbr_adj = nbr_weight * nbr_diff
                    type_adj = 0.0
                    for ri, r in enumerate(results[:2]):
                        fname = r['file']
                        sign = 1.0 if ri == 0 else -1.0
                        if fname.startswith('ROOT-') or fname.startswith('ROOT_'):
                            type_adj += sign * 5.0
                        elif fname.startswith('G-pruned-') or fname.startswith('_pruned_'):
                            type_adj -= sign * 5.0
                    margin = min(max(raw + anchor_adj + nbr_adj + type_adj, 0.1), 100.0)
                else:
                    margin = min(max(raw + anchor_adj, 0.1), 100.0)
            elif len(results) == 1:
                margin = 100.0
            else:
                margin = 0.0

            # Confidence gate — SLA Layer 4
            if mode == 'retrieve':
                if margin > 50:
                    gate = 'HIGH'
                elif margin > 15:
                    gate = 'MED'
                else:
                    gate = 'LOW'
                for r in results:
                    r['confidence'] = gate
            else:
                top_score = results[0]['score'] if results else 0.0
                for r in results:
                    if top_score == 0:
                        r['confidence'] = 'LOW'
                    else:
                        ratio = r['score'] / top_score
                        if ratio >= 0.7:
                            r['confidence'] = 'HIGH'
                        elif ratio >= 0.35:
                            r['confidence'] = 'MED'
                        else:
                            r['confidence'] = 'LOW'

            return {
                'results': results, 'margin': round(margin, 1), 'query': query_text,
                'mode': mode, 'indexed': self.n,
                'scope': self.scope.get('mode', 'unknown'),
                'active_entity': self.scope.get('active_entity'),
            }

    def find_duplicates(self, threshold=0.75, top_n=20, exclude_shared=False):
        with self._lock:
            if self.n == 0:
                return {'duplicates': [], 'scanned': 0}
            pairs = []
            for i in range(self.n):
                for j in range(i + 1, self.n):
                    pi, pj = self.paragraphs[i], self.paragraphs[j]
                    if pi['entity'] == pj['entity'] and pi['file'] == pj['file']:
                        continue
                    if exclude_shared and pi['file'] == pj['file'] and pi['entity'] != pj['entity']:
                        continue
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
            if self.n == 0:
                return {'orphans': [], 'scanned': 0}
            isolation_scores = []
            for i in range(self.n):
                if not self.tokens[i]:
                    continue
                max_cosine = 0.0
                for j in range(self.n):
                    if j == i:
                        continue
                    sim = self._cosine(self.tokens[i], self.tokens[j], self.idf)
                    if sim > max_cosine:
                        max_cosine = sim
                p = self.paragraphs[i]
                if max_cosine <= max_sim:
                    fname = p['file']
                    if fname.startswith('ROOT-') or fname.startswith('ROOT_'):
                        doc_type = 'root'
                    elif fname.startswith('G-pruned-') or fname.startswith('_pruned_'):
                        doc_type = 'pruned'
                    elif fname.startswith('CORE') or fname == 'entity.json':
                        doc_type = 'core'
                    else:
                        doc_type = 'seed'
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
            if self.n == 0:
                return {'error': 'Index empty'}
            root_indices = []
            seed_indices = []
            for i, p in enumerate(self.paragraphs):
                if p['entity'] != entity_name:
                    continue
                fname = p['file']
                if fname.startswith('ROOT-') or fname.startswith('ROOT_'):
                    root_indices.append(i)
                elif not fname.startswith('G-pruned-') and not fname.startswith('_pruned_'):
                    seed_indices.append(i)
            if not root_indices:
                return {'entity': entity_name, 'error': 'No ROOTs found', 'roots': 0, 'seeds': 0}
            if not seed_indices:
                return {'entity': entity_name, 'error': 'No seeds found', 'roots': len(root_indices), 'seeds': 0}
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
            if self.n == 0:
                return {'pairs': [], 'entities': 0}
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
    """Polls for file changes and triggers reindex."""

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
        try:
            sigs['__state__'] = state_file.stat().st_mtime
        except Exception:
            pass
        scope = get_active_scope()
        for entity_name in scope['entities']:
            entity_dir = Path(DOCTRINE_PATH) / entity_name
            if not entity_dir.is_dir():
                continue
            for md_file in entity_dir.glob('*.md'):
                try:
                    sigs[str(md_file)] = md_file.stat().st_mtime
                except Exception:
                    pass
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
        """Pause watching — used when external corpus is loaded."""
        self._paused = True

    def resume(self):
        """Resume watching and rebuild doctrine index."""
        self._paused = False
        # Force immediate rebuild on resume
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
        if detail:
            entry += f" | {detail}"
        try:
            os.makedirs(self.state_path, exist_ok=True)
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(entry + '\n')
        except Exception:
            pass

    def manifest(self, entity_filter=None):
        """List all files with metadata. Computed on call, never cached."""
        files = []
        if not self.doctrine_path.is_dir():
            return {'files': files, 'entities': 0, 'total_size': 0}

        entities_found = set()
        for entity_dir in sorted(self.doctrine_path.iterdir()):
            if not entity_dir.is_dir():
                continue
            entity_name = entity_dir.name
            if entity_filter and entity_name != entity_filter:
                continue
            entities_found.add(entity_name)

            # Read class from entity.json
            entity_class = 'unknown'
            try:
                ej = json.loads((entity_dir / 'entity.json').read_text(encoding='utf-8'))
                entity_class = ej.get('class', 'unknown')
            except Exception:
                pass

            for f in sorted(entity_dir.iterdir()):
                if f.is_dir():
                    # Include subdirectory files (e.g. state/, RELEASE_GOVERNANCE/)
                    for sf in sorted(f.iterdir()):
                        if sf.is_file():
                            stat = sf.stat()
                            files.append({
                                'entity': entity_name,
                                'class': entity_class,
                                'path': str(sf.relative_to(self.bond_root)),
                                'file': f"{f.name}/{sf.name}",
                                'size': stat.st_size,
                                'modified': time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(stat.st_mtime)),
                            })
                elif f.is_file():
                    stat = f.stat()
                    files.append({
                        'entity': entity_name,
                        'class': entity_class,
                        'path': str(f.relative_to(self.bond_root)),
                        'file': f.name,
                        'size': stat.st_size,
                        'modified': time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(stat.st_mtime)),
                    })

        total_size = sum(f['size'] for f in files)
        return {'files': files, 'entities': len(entities_found), 'total_size': total_size, 'file_count': len(files)}

    def read(self, rel_path):
        """Read file verbatim. Returns raw content."""
        resolved, err = self._safe_path(rel_path)
        if err:
            return {'error': err}
        if not resolved.is_file():
            return {'error': f'Not a file: {rel_path}'}
        try:
            content = resolved.read_text(encoding='utf-8')
            return {
                'path': rel_path,
                'content': content,
                'size': len(content),
                'lines': content.count('\n') + 1,
            }
        except Exception as e:
            return {'error': f'Read failed: {e}'}

    def write(self, rel_path, content):
        """Write content verbatim to file."""
        resolved, err = self._safe_path(rel_path)
        if err:
            return {'error': err}
        try:
            os.makedirs(resolved.parent, exist_ok=True)
            existed = resolved.is_file()
            resolved.write_text(content, encoding='utf-8')
            op = 'OVERWRITE' if existed else 'CREATE'
            self._log(op, rel_path, f"{len(content)} bytes")
            return {
                'path': rel_path,
                'operation': op.lower(),
                'size': len(content),
                'lines': content.count('\n') + 1,
            }
        except Exception as e:
            return {'error': f'Write failed: {e}'}

    def copy(self, from_rel, to_rel):
        """Copy file verbatim from one path to another."""
        from_resolved, err = self._safe_path(from_rel)
        if err:
            return {'error': f'Source: {err}'}
        to_resolved, err = self._safe_path(to_rel)
        if err:
            return {'error': f'Destination: {err}'}
        if not from_resolved.is_file():
            return {'error': f'Source not found: {from_rel}'}
        try:
            content = from_resolved.read_text(encoding='utf-8')
            os.makedirs(to_resolved.parent, exist_ok=True)
            existed = to_resolved.is_file()
            to_resolved.write_text(content, encoding='utf-8')
            op = 'COPY_OVER' if existed else 'COPY_NEW'
            self._log(op, f"{from_rel} -> {to_rel}", f"{len(content)} bytes")
            return {
                'from': from_rel,
                'to': to_rel,
                'operation': op.lower(),
                'size': len(content),
            }
        except Exception as e:
            return {'error': f'Copy failed: {e}'}

    def export(self, entity_filter=None, output_path=None):
        """Assemble all doctrine files into a single markdown document, verbatim."""
        if not output_path:
            output_path = self.state_path / 'export.md'
        else:
            output_path = Path(output_path)

        lines = ['# BOND Doctrine Export']
        lines.append(f"_Generated: {time.strftime('%Y-%m-%dT%H:%M:%S')}_")
        lines.append('')

        file_count = 0
        total_chars = 0
        entities_exported = set()

        for entity_dir in sorted(self.doctrine_path.iterdir()):
            if not entity_dir.is_dir():
                continue
            entity_name = entity_dir.name
            if entity_filter and entity_name != entity_filter:
                continue

            # Read class
            entity_class = 'unknown'
            try:
                ej = json.loads((entity_dir / 'entity.json').read_text(encoding='utf-8'))
                entity_class = ej.get('class', 'unknown')
            except Exception:
                pass

            entities_exported.add(entity_name)
            lines.append(f"---")
            lines.append(f"## {entity_name} ({entity_class})")
            lines.append('')

            for f in sorted(entity_dir.iterdir()):
                if not f.is_file():
                    continue
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
            'output_path': str(output_path),
            'entities': len(entities_exported),
            'files': file_count,
            'total_chars': total_chars,
            'token_estimate': int(total_chars * 0.25),
        }


file_ops = None  # initialized in __main__ (after --root parse)


# ─── QAIS Resonance (Perspective Vine Scoring) ────────
# Phase 2 of daemon consolidation: daemon reads perspective .npz fields
# and computes resonance scores locally. No MCP round-trip needed.
# Math extracted from qais_mcp_server.py text_to_vector_v5.
# P11: daemon reads only, MCP writes only. No concurrent write risk.

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

QAIS_N = 4096

QAIS_STOPWORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
    'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
    'shall', 'can', 'need', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
    'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'under', 'again',
    'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each',
    'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
    'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or', 'because', 'until', 'while',
    'this', 'that', 'these', 'those', 'it', 'its', 'i', 'me', 'my', 'we', 'our', 'you', 'your',
    'he', 'him', 'his', 'she', 'her', 'they', 'them', 'their', 'what', 'which', 'who', 'whom',
    'about', 'let', 'tell', 'know', 'think', 'make', 'take', 'see', 'come', 'look', 'use', 'find',
    'give', 'got', 'get', 'put', 'said', 'say', 'like', 'also', 'well', 'back', 'much', 'way',
    'even', 'new', 'want', 'first', 'any', 'happens', 'mean', 'work', 'works', 'things', 'thing',
    'session', 'chunk', 'crystallization',
}

QAIS_SYNONYMS = {
    'meter': ['m', 'meters', 'metre'], 'm': ['meter', 'meters'], 'meters': ['m', 'meter'],
    'config': ['configuration', 'configure'], 'configuration': ['config'],
    'params': ['parameters', 'param'], 'parameters': ['params'],
    'derive': ['compute', 'calculate', 'derived'], 'compute': ['derive', 'calculate'],
    'store': ['save', 'persist', 'stored'], 'save': ['store', 'persist'],
}

QAIS_UNIT_EXPANSIONS = {
    'm': 'meter', 'ms': 'millisecond', 's': 'second', 'km': 'kilometer', 'cm': 'centimeter',
}


def qais_seed_to_vector(seed):
    """Deterministic seed → bipolar vector."""
    import hashlib
    h = hashlib.sha512(seed.encode()).digest()
    rng = np.random.RandomState(list(h[:4]))
    return rng.choice([-1, 1], size=QAIS_N).astype(np.float32)


def qais_normalize_number_units(text):
    result = text
    for abbrev, full in QAIS_UNIT_EXPANSIONS.items():
        pattern = r'(\d+)' + abbrev + r'\b'
        replacement = r'\1 ' + full
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def qais_expand_synonyms(keywords):
    expanded = set(keywords)
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in QAIS_SYNONYMS:
            expanded.update(QAIS_SYNONYMS[kw_lower])
    return list(expanded)


def qais_text_to_keywords_v5(text):
    text = qais_normalize_number_units(text)
    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text.lower())
    keywords = [w for w in words if len(w) > 2 and w not in QAIS_STOPWORDS]
    keywords = qais_expand_synonyms(keywords)
    base_words = [w for w in words if len(w) > 2 and w not in QAIS_STOPWORDS]
    for i in range(len(base_words) - 1):
        bigram = f"{base_words[i]}_{base_words[i+1]}"
        keywords.append(bigram)
    return list(set(keywords))


def qais_text_to_vector_v5(text):
    """Text → bundled bipolar vector via keyword extraction + synonym expansion + bigrams."""
    keywords = qais_text_to_keywords_v5(text)
    if not keywords:
        return qais_seed_to_vector(text)
    bundle = np.zeros(QAIS_N, dtype=np.float32)
    for kw in keywords:
        bundle += qais_seed_to_vector(kw)
    result = np.sign(bundle)
    result[result == 0] = 1
    return result.astype(np.float32)


class PerspectiveReader:
    """Read-only access to perspective .npz fields for vine resonance scoring.
    
    Daemon reads, MCP writes. No concurrent write risk.
    Loads field fresh each call (no caching) to always see latest MCP writes.
    """

    def __init__(self, bond_root):
        self.perspectives_dir = os.path.join(bond_root, 'data', 'perspectives')

    def available(self):
        """Check if numpy is available and perspectives dir exists."""
        return HAS_NUMPY and os.path.isdir(self.perspectives_dir)

    def _load_field(self, perspective):
        """Load perspective .npz and return stored keys. Fresh read each time."""
        field_path = os.path.join(self.perspectives_dir, f"{perspective}.npz")
        if not os.path.exists(field_path):
            return None, f"No field file for {perspective}"
        try:
            data = np.load(field_path, allow_pickle=True)
            stored = set(data['stored'].tolist())
            count = int(data['count'])
            return {'stored': stored, 'count': count}, None
        except Exception as e:
            return None, f"Failed to load {perspective}.npz: {e}"

    def check(self, perspective, text):
        """Score text against perspective's seed field.
        
        Replicates perspective_check from qais_mcp_server.py exactly.
        Returns same format: {perspective, matches, field_count}
        """
        if not HAS_NUMPY:
            return {'error': 'numpy not available'}

        field_data, err = self._load_field(perspective)
        if err:
            return {'error': err}

        if field_data['count'] == 0:
            return {
                'perspective': perspective,
                'matches': [],
                'field_count': 0,
                'note': 'Field empty — no seeds stored yet.',
            }

        text_vec = qais_text_to_vector_v5(text)
        matches = []
        seen = set()

        for key in field_data['stored']:
            parts = key.split('|', 2)
            if len(parts) == 3:
                title, role, content = parts
                if title in seen:
                    continue
                seen.add(title)
                seed_vec = qais_text_to_vector_v5(content)
                score = float(np.dot(text_vec, seed_vec) / QAIS_N)
                matches.append({
                    'seed': title,
                    'content_preview': content[:80],
                    'score': round(score, 4),
                })

        matches.sort(key=lambda x: -x['score'])
        return {
            'perspective': perspective,
            'matches': matches,
            'field_count': field_data['count'],
            'source': 'daemon',
        }

    def check_multi(self, perspectives, text):
        """Score text against multiple perspectives in one call.
        
        Returns dict of perspective_name → check result.
        Used by /sync-complete for all armed seeders at once.
        """
        results = {}
        for p in perspectives:
            results[p] = self.check(p, text)
        return results


perspective_reader = None  # initialized in __main__


# ——— Vine Processor (Tracker Bookkeeping) ————————————————
# Phase 4 of daemon consolidation: daemon scores AND writes tracker updates.
# Claude no longer does manual exposure/hit/rain bookkeeping.
# Daemon handles the math. Claude handles judgment (auto-seed, prune, ROOT lens).

class VineProcessor:
    """Vine lifecycle tracker updates during {Sync}.
    
    Scores come from PerspectiveReader (Phase 2-3).
    This class applies those scores to seed_tracker.json:
      - Increment exposures on ALL tracked seeds
      - Record hits (score >= sunshine threshold)
      - Record rain (rain_floor <= score < threshold), 1 per seed per Sync pass
      - Write updated tracker to disk
    
    What daemon does: score + tracker bookkeeping + disk write.
    What Claude still does: auto-seed judgment, prune decisions, narrative annotation.
    """

    def __init__(self, doctrine_path):
        self.doctrine_path = Path(doctrine_path)

    def _rain_floor(self, seed_threshold):
        """Compute rain floor: seed_threshold × 0.625, rounded to nearest 0.005."""
        raw = seed_threshold * 0.625
        return round(raw * 200) / 200

    def process(self, perspective, resonance_result, tracker, config, session_label=''):
        """Process vine lifecycle for one perspective after resonance scoring.
        
        Args:
            perspective: entity name (e.g. 'P11-Plumber')
            resonance_result: output from PerspectiveReader.check()
            tracker: current seed_tracker.json contents (dict)
            config: {seed_threshold, prune_window, entity, ...}
            session_label: e.g. 'S124' for tracker annotations
            
        Returns: {
            tracker: updated tracker dict (also written to disk),
            changes: list of {seed, event, score, ...},
            thresholds: {sunshine, rain_floor},
            written: bool,
        }
        """
        threshold = config.get('seed_threshold', 0.04)
        rain_floor = self._rain_floor(threshold)
        changes = []

        if not resonance_result or 'matches' not in resonance_result:
            return {
                'tracker': tracker, 'changes': [],
                'thresholds': {'sunshine': threshold, 'rain_floor': rain_floor},
                'written': False, 'reason': 'no resonance data',
            }

        # Build score lookup from resonance matches.
        # Seeds in tracker are bare names; resonance may have bare or 'root:' prefix.
        score_map = {}
        for m in resonance_result.get('matches', []):
            seed_name = m['seed']
            score_map[seed_name] = m['score']
            if seed_name.startswith('root:'):
                score_map[seed_name[5:]] = m['score']

        # Process each tracked seed
        for seed_name, entry in tracker.items():
            # Increment exposures on ALL tracked seeds
            entry['exposures'] = entry.get('exposures', 0) + 1

            # Find score — try exact name, then with root: prefix
            score = score_map.get(seed_name)
            if score is None:
                score = score_map.get(f'root:{seed_name}')
            if score is None:
                changes.append({
                    'seed': seed_name, 'event': 'exposure_only',
                    'exposures': entry['exposures'],
                })
                continue

            label = f"{session_label} — {score:.4f}" if session_label else f"{score:.4f}"

            # Sunshine hit (score >= threshold)
            if score >= threshold:
                entry['hits'] = entry.get('hits', 0) + 1
                entry['last_hit'] = label
                changes.append({
                    'seed': seed_name, 'event': 'hit',
                    'score': round(score, 4),
                    'hits': entry['hits'], 'exposures': entry['exposures'],
                })
            # Rain band (rain_floor <= score < threshold)
            elif score >= rain_floor:
                # Cap: 1 rain per seed per Sync pass (natural enforcement)
                entry['rain'] = entry.get('rain', 0) + 1
                entry['last_rain'] = label
                changes.append({
                    'seed': seed_name, 'event': 'rain',
                    'score': round(score, 4),
                    'rain': entry['rain'], 'exposures': entry['exposures'],
                })
            # Dry (below rain floor)
            else:
                changes.append({
                    'seed': seed_name, 'event': 'dry',
                    'score': round(score, 4),
                    'exposures': entry['exposures'],
                })

        # Write updated tracker to disk
        tracker_path = self.doctrine_path / perspective / 'seed_tracker.json'
        written = False
        try:
            tracker_path.write_text(
                json.dumps(tracker, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            written = True
        except Exception as e:
            changes.append({'error': f'Tracker write failed: {e}'})

        return {
            'tracker': tracker,
            'changes': changes,
            'thresholds': {'sunshine': threshold, 'rain_floor': rain_floor},
            'written': written,
        }


vine_processor = None  # initialized in __main__


# ─── Session Heat Map (Daemon-Internal) ───────────────────
# Phase 5 of daemon consolidation: heatmap moves from MCP to daemon.
# Bypasses class matrix entirely — works during doctrine sessions.
# Persists to state/heatmap.json so it survives daemon restarts.
# Session-scoped: Claude calls /heatmap-clear at session start.

class DaemonHeatMap:
    """Session heat map with disk persistence.
    
    Same scoring logic as MCP SessionHeatMap but:
    - Persists to state/heatmap.json (survives daemon restart)
    - No class matrix — works for any active entity
    - Snapshot included in /sync-complete
    """

    def __init__(self, state_path):
        self.state_file = os.path.join(state_path, 'heatmap.json')
        self.concepts = {}
        self.session_start = time.time()
        self._load()

    def _load(self):
        try:
            data = json.loads(Path(self.state_file).read_text(encoding='utf-8'))
            self.concepts = data.get('concepts', {})
            self.session_start = data.get('session_start', time.time())
        except Exception:
            pass

    def _save(self):
        try:
            Path(self.state_file).write_text(json.dumps({
                'concepts': self.concepts,
                'session_start': self.session_start,
            }, indent=2), encoding='utf-8')
        except Exception:
            pass

    def touch(self, concepts, context=''):
        now = time.time()
        results = []
        for concept in concepts:
            concept = concept.lower()
            if concept not in self.concepts:
                self.concepts[concept] = {
                    'count': 0, 'first': now, 'last': 0, 'contexts': [],
                }
            entry = self.concepts[concept]
            entry['count'] += 1
            entry['last'] = now
            if context:
                entry['contexts'].append(context)
                entry['contexts'] = entry['contexts'][-5:]  # cap at 5
            results.append({'concept': concept, 'count': entry['count']})
        self._save()
        return {'touched': len(results), 'concepts': results}

    def hot(self, top_k=10):
        now = time.time()
        scored = []
        for concept, entry in self.concepts.items():
            age_minutes = (now - entry['last']) / 60
            if age_minutes < 5:
                recency = 2.0
            elif age_minutes < 15:
                recency = 1.5
            elif age_minutes < 30:
                recency = 1.0
            else:
                recency = 0.5
            score = entry['count'] * recency
            scored.append({
                'concept': concept, 'count': entry['count'],
                'score': round(score, 2),
                'last_touch_mins': round(age_minutes, 1),
                'contexts': entry['contexts'][-3:],
            })
        scored.sort(key=lambda x: -x['score'])
        return scored[:top_k]

    def for_chunk(self):
        hot = self.hot(10)
        now = time.time()
        session_mins = (now - self.session_start) / 60
        cold = [c for c, e in self.concepts.items() if (now - e['last']) / 60 > 15]
        hot_names = [h['concept'] for h in hot[:5]]
        return {
            'session_minutes': round(session_mins, 1),
            'total_concepts': len(self.concepts),
            'total_touches': sum(e['count'] for e in self.concepts.values()),
            'hot': [{'concept': h['concept'], 'count': h['count'], 'why': h['contexts']} for h in hot],
            'cold': cold[:5],
            'summary': f"{len(self.concepts)} concepts, hot: {', '.join(hot_names)}",
        }

    def clear(self):
        count = len(self.concepts)
        self.concepts.clear()
        self.session_start = time.time()
        self._save()
        return {'cleared': count, 'status': 'reset'}


daemon_heatmap = None  # initialized in __main__


# ─── RepoSync: REMOVED (A1/F2 — S153) ────────────────
# Dead pipe: required sync_manifest.json (never created).
# Repo sync runs via PowerShell card through /exec endpoint.
# Class removed, ~200 lines reclaimed.
class _RepoSyncRemoved:
    """Binary-safe repository sync from BOND_private to BOND_github.
    
    One-way valve: reads source, writes target. Never reads target content.
    Dry-run default. Entity self-declaration via 'public' flag in entity.json.
    All ops logged to state/file_ops.log.
    """

    # Text extensions for type-aware reporting
    TEXT_EXTS = {'.md', '.json', '.py', '.js', '.jsx', '.ts', '.tsx', '.css',
                 '.html', '.bat', '.sh', '.txt', '.yml', '.yaml', '.toml',
                 '.cfg', '.ini', '.env', '.gitignore', '.gitattributes'}

    def __init__(self, bond_root, state_path, doctrine_path):
        self.bond_root = Path(bond_root).resolve()
        self.state_path = Path(state_path)
        self.doctrine_path = Path(doctrine_path)
        self.log_path = self.state_path / 'file_ops.log'
        self.manifest_path = self.state_path / 'sync_manifest.json'

    def _log(self, op, detail=''):
        ts = time.strftime('%Y-%m-%dT%H:%M:%S')
        entry = f"[{ts}] REPO-SYNC {op}"
        if detail:
            entry += f" | {detail}"
        try:
            os.makedirs(self.state_path, exist_ok=True)
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(entry + '\n')
        except Exception:
            pass

    def _load_manifest(self):
        """Load sync_manifest.json. Returns config dict or error."""
        try:
            return json.loads(self.manifest_path.read_text(encoding='utf-8')), None
        except FileNotFoundError:
            return None, 'sync_manifest.json not found in state/'
        except json.JSONDecodeError as e:
            return None, f'sync_manifest.json parse error: {e}'

    def _is_blocked_dir(self, rel_parts, manifest):
        """Check if any path component matches blocked_dirs."""
        blocked = manifest.get('blocked_dirs', [])
        # Check each path prefix
        for i in range(len(rel_parts)):
            partial = '/'.join(rel_parts[:i+1])
            if partial in blocked:
                return True
            # Also check individual directory names
            if rel_parts[i] in blocked:
                return True
        return False

    def _is_blocked_file(self, filename, manifest):
        """Check if filename matches blocked_files or blocked_patterns."""
        if filename in manifest.get('blocked_files', []):
            return True
        for pattern in manifest.get('blocked_patterns', []):
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False

    def _is_doctrine_public(self, entity_name):
        """Check entity.json public flag. Default: False (safe)."""
        try:
            config_path = self.doctrine_path / entity_name / 'entity.json'
            config = json.loads(config_path.read_text(encoding='utf-8'))
            return config.get('public', False)
        except Exception:
            return False

    def _classify_file(self, filepath):
        """Return 'text' or 'binary' based on extension."""
        return 'text' if filepath.suffix.lower() in self.TEXT_EXTS else 'binary'

    def _file_meta(self, filepath):
        """Get mtime + size for diff comparison."""
        try:
            st = filepath.stat()
            return st.st_mtime, st.st_size
        except Exception:
            return None, None

    def _collect_syncable(self, manifest):
        """Walk source tree, apply filters, return list of syncable files.
        
        Returns: (syncable_files, personal_flags)
        syncable_files: list of {'rel_path': str, 'abs_path': Path, 'type': str, 'size': int}
        personal_flags: list of {'path': str, 'reason': str}
        """
        target = Path(manifest['target']).resolve()
        syncable = []
        personal = []
        uses_entity_flags = manifest.get('doctrine_uses_entity_flags', True)
        state_defaults_only = manifest.get('state_defaults_only', True)

        for root, dirs, files in os.walk(self.bond_root):
            root_path = Path(root)
            rel_root = root_path.relative_to(self.bond_root)
            rel_parts = list(rel_root.parts) if str(rel_root) != '.' else []

            # Skip blocked directories (prune walk)
            dirs[:] = [d for d in dirs if not self._is_blocked_dir(rel_parts + [d], manifest)]

            # Doctrine entity filtering via public flag
            if rel_parts and rel_parts[0] == 'doctrine' and len(rel_parts) >= 2:
                entity_name = rel_parts[1]
                if uses_entity_flags and not self._is_doctrine_public(entity_name):
                    personal.append({
                        'path': str(rel_root),
                        'reason': f'entity.json: public=false ({entity_name})',
                    })
                    dirs[:] = []  # prune this entity's subdirectories
                    continue
                # Block entity-local state/ subdirectories (runtime data)
                if len(rel_parts) >= 3 and rel_parts[2] == 'state':
                    for f in files:
                        personal.append({
                            'path': str(rel_root / f).replace('\\', '/'),
                            'reason': f'entity-local state: runtime data ({entity_name}/state/)',
                        })
                    dirs[:] = []
                    continue

            # State directory: allowlist mode when state_defaults_only=true
            # Only explicitly allowed files sync. Everything else is runtime data.
            if rel_parts and rel_parts[0] == 'state' and state_defaults_only:
                allowed = set(manifest.get('state_allowed_files', ['.gitkeep']))
                for f in files:
                    filepath = root_path / f
                    rel_path = str(rel_root / f).replace('\\', '/')
                    if f in allowed and not self._is_blocked_file(f, manifest):
                        syncable.append({
                            'rel_path': rel_path,
                            'abs_path': filepath,
                            'type': self._classify_file(filepath),
                            'size': filepath.stat().st_size,
                        })
                    else:
                        personal.append({
                            'path': rel_path,
                            'reason': 'state_defaults_only: runtime data (not in state_allowed_files)',
                        })
                continue

            for f in files:
                if self._is_blocked_file(f, manifest):
                    continue
                filepath = root_path / f
                rel_path = str(rel_root / f).replace('\\', '/') if rel_parts else f
                syncable.append({
                    'rel_path': rel_path,
                    'abs_path': filepath,
                    'type': self._classify_file(filepath),
                    'size': filepath.stat().st_size,
                })

        return syncable, personal

    def _diff_against_target(self, syncable, target_path):
        """Compare syncable files against target. Returns categorized lists."""
        new_files = []
        updated_files = []
        unchanged_files = []

        for entry in syncable:
            target_file = target_path / entry['rel_path']
            if not target_file.exists():
                new_files.append(entry)
            else:
                src_mtime, src_size = self._file_meta(entry['abs_path'])
                tgt_mtime, tgt_size = self._file_meta(target_file)
                if src_size != tgt_size or (src_mtime and tgt_mtime and src_mtime > tgt_mtime):
                    updated_files.append(entry)
                else:
                    unchanged_files.append(entry)

        return new_files, updated_files, unchanged_files

    def _format_size(self, size):
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f}KB"
        else:
            return f"{size/(1024*1024):.1f}MB"

    def sync(self, dry_run=True):
        """Execute repository sync. Dry-run by default.
        
        Returns structured report suitable for Claude to present.
        """
        manifest, err = self._load_manifest()
        if err:
            return {'error': err}

        target_str = manifest.get('target')
        if not target_str:
            return {'error': 'No target defined in sync_manifest.json'}

        target_path = Path(target_str).resolve()

        # Validate target has .git (safety check)
        if not (target_path / '.git').is_dir():
            return {'error': f'Target has no .git directory: {target_str}. Refusing to sync to non-repo.'}

        # Validate target doesn't escape to unexpected locations
        target_str_resolved = str(target_path)
        if self.bond_root == target_path:
            return {'error': 'Target cannot be the same as source (BOND_ROOT)'}

        # Collect syncable files
        syncable, personal_flags = self._collect_syncable(manifest)

        # Diff against target
        new_files, updated_files, unchanged_files = self._diff_against_target(syncable, target_path)

        to_sync = new_files + updated_files

        # Type breakdown
        text_count = sum(1 for f in to_sync if f['type'] == 'text')
        binary_count = sum(1 for f in to_sync if f['type'] == 'binary')

        # Build report
        report = {
            'dry_run': dry_run,
            'source': str(self.bond_root),
            'target': target_str,
            'authority': manifest.get('authority', 'unknown'),
            'personal_flags': personal_flags,
            'summary': {
                'total_syncable': len(syncable),
                'new': len(new_files),
                'updated': len(updated_files),
                'unchanged': len(unchanged_files),
                'to_sync': len(to_sync),
                'text': text_count,
                'binary': binary_count,
            },
            'files_to_sync': [
                {
                    'action': 'NEW' if f in new_files else 'UPDATE',
                    'path': f['rel_path'],
                    'type': f['type'],
                    'size': self._format_size(f['size']),
                }
                for f in to_sync
            ],
            'gitignore_parity': self._check_gitignore(target_path),
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
        }

        # Execute if not dry run
        if not dry_run and to_sync:
            copied = 0
            errors = []
            for entry in to_sync:
                dest = target_path / entry['rel_path']
                try:
                    os.makedirs(dest.parent, exist_ok=True)
                    shutil.copy2(str(entry['abs_path']), str(dest))
                    copied += 1
                    self._log('COPY', f"{entry['rel_path']} ({self._format_size(entry['size'])})")
                except Exception as e:
                    errors.append({'path': entry['rel_path'], 'error': str(e)})
                    self._log('ERROR', f"{entry['rel_path']}: {e}")

            report['execution'] = {
                'copied': copied,
                'errors': errors,
                'status': 'complete' if not errors else 'partial',
            }
            self._log('SYNC_COMPLETE', f"{copied} files synced, {len(errors)} errors")
        elif not dry_run and not to_sync:
            report['execution'] = {'copied': 0, 'errors': [], 'status': 'nothing_to_sync'}

        # Human-readable summary line
        s = report['summary']
        report['summary_line'] = (
            f"{s['to_sync']} files to sync "
            f"({s['new']} new, {s['updated']} updated, {s['unchanged']} unchanged) "
            f"| {s['text']} text, {s['binary']} binary"
        )

        return report

    def _check_gitignore(self, target_path):
        """Check if target .gitignore exists and report basic parity."""
        gi_path = target_path / '.gitignore'
        if not gi_path.is_file():
            return {'exists': False, 'note': 'No .gitignore in target'}
        try:
            content = gi_path.read_text(encoding='utf-8')
            lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]
            return {'exists': True, 'entries': len(lines)}
        except Exception:
            return {'exists': True, 'entries': 'unknown'}


# repo_sync: REMOVED (A1/F2). Repo sync runs via PowerShell /exec card.


# ─── Composite Payloads (Data Assembly Layer) ──────────────
# One call replaces 5-15 individual file reads.
# The daemon's response IS its health — no separate /health endpoint.
# CM layered narrowing: each call narrows scope, no layer overrides higher.
# P11 build-for-access: capability manifest tells Claude what's available.

class PayloadAssembler:
    """Pre-assembled composite payloads for Claude.
    
    Replaces cascading file reads with single HTTP calls.
    Every response includes a capabilities manifest —
    Claude discovers what's available from the data itself.
    """

    CAPABILITIES = {
        'search': ['GET /search?q=', 'GET /search?q=&mode=retrieve', 'GET /search?q=&scope=all'],
        'file_ops': ['GET /manifest', 'GET /read?path=', 'POST /write', 'GET /copy?from=&to=', 'GET /export'],
        'analysis': ['GET /duplicates', 'GET /orphans', 'GET /coverage?entity=', 'GET /similarity'],
        'corpus': ['GET /load?path=', 'GET /unload'],
        'composite': ['GET /sync-complete', 'POST /sync-complete', 'GET /sync-payload', 'GET /enter-payload?entity=', 'GET /vine-data?perspective=', 'GET /obligations'],
        'heatmap': ['GET /heatmap-touch?concepts=', 'GET /heatmap-hot', 'GET /heatmap-chunk', 'GET /heatmap-clear'],
        'resonance': ['GET /resonance-test?perspective=&text=', 'GET /resonance-multi?text='],
    }

    def __init__(self, bond_root, state_path, doctrine_path):
        self.bond_root = Path(bond_root)
        self.state_path = Path(state_path)
        self.doctrine_path = Path(doctrine_path)

    def _read_json(self, path):
        try:
            return json.loads(Path(path).read_text(encoding='utf-8'))
        except Exception:
            return None

    def _read_file(self, path):
        try:
            return Path(path).read_text(encoding='utf-8')
        except Exception:
            return None

    def _entity_files(self, entity_name):
        """Read all files for an entity. Returns dict of filename→content."""
        entity_dir = self.doctrine_path / entity_name
        if not entity_dir.is_dir():
            return {}
        files = {}
        for f in sorted(entity_dir.iterdir()):
            if f.is_file():
                content = self._read_file(f)
                if content is not None:
                    files[f.name] = content
        return files

    # D14: Class defaults for mandatory file sets
    CLASS_DEFAULTS = {
        'project': ['CORE.md', 'ACTIVE.md'],
        'doctrine': None,  # entity_name + ".md" — resolved dynamically
        'perspective': None,  # ROOT-*.md glob + CORE.md + ACTIVE.md — resolved dynamically
        'library': [],  # entity.json only
    }

    def _resolve_mandatory(self, entity_path, entity_json):
        """D14: Resolve mandatory file set for an entity.

        Returns list of mandatory filenames (excluding entity.json, which is always included separately).
        """
        entity_path = Path(entity_path)

        # If entity.json has explicit "mandatory" array, use it
        if entity_json and 'mandatory' in entity_json:
            mandatory = list(entity_json['mandatory'])
            # Filter to files that actually exist
            return [f for f in mandatory if (entity_path / f).is_file()]

        # Apply class defaults
        entity_class = entity_json.get('class', 'unknown') if entity_json else 'unknown'

        if entity_class == 'project':
            candidates = ['CORE.md', 'ACTIVE.md']
            return [f for f in candidates if (entity_path / f).is_file()]

        elif entity_class == 'doctrine':
            # entity_name + ".md"
            entity_name = entity_path.name
            candidate = entity_name + '.md'
            return [candidate] if (entity_path / candidate).is_file() else []

        elif entity_class == 'perspective':
            # ROOT-*.md glob + CORE.md + ACTIVE.md (if they exist)
            import glob as glob_mod
            root_files = sorted([
                Path(p).name for p in glob_mod.glob(str(entity_path / 'ROOT-*.md'))
            ])
            extras = [f for f in ['CORE.md', 'ACTIVE.md'] if (entity_path / f).is_file()]
            return root_files + extras

        elif entity_class == 'library':
            return []  # entity.json only

        else:
            # Unknown class — load ALL files (backward compatible)
            return None  # signal to caller: load everything

    def _deferred_manifest(self, entity_path, mandatory_files):
        """D14: Build deferred manifest for non-mandatory files.

        Returns sorted list of {name, size_kb} for files not in the mandatory set.
        """
        entity_path = Path(entity_path)
        if not entity_path.is_dir():
            return []

        excluded = set(mandatory_files or [])
        excluded.add('entity.json')

        deferred = []
        for f in sorted(entity_path.iterdir()):
            if not f.is_file():
                continue
            if f.suffix not in ('.md', '.json'):
                continue
            if f.name in excluded:
                continue
            size_kb = round(f.stat().st_size / 1024, 1)
            deferred.append({'name': f.name, 'size_kb': size_kb})

        return deferred

    def _load_files(self, entity_path, filenames):
        """Load specific files from entity directory. Returns dict of filename→content.

        Always includes entity.json. If filenames is None, loads ALL files (backward compat).
        """
        entity_path = Path(entity_path)
        if not entity_path.is_dir():
            return {}

        # None means unknown class — load everything
        if filenames is None:
            files = {}
            for f in sorted(entity_path.iterdir()):
                if f.is_file():
                    content = self._read_file(f)
                    if content is not None:
                        files[f.name] = content
            return files

        files = {}
        # Always include entity.json
        all_to_load = set(filenames) | {'entity.json'}
        for name in sorted(all_to_load):
            path = entity_path / name
            if path.is_file():
                content = self._read_file(path)
                if content is not None:
                    files[name] = content
        return files

    def _linked_entities(self, entity_name):
        """Get links array from entity.json."""
        config = self._read_json(self.doctrine_path / entity_name / 'entity.json')
        if config and 'links' in config:
            return config['links']
        return []

    def _armed_seeders(self):
        """Scan for perspective entities with seeding: true."""
        armed = []
        if not self.doctrine_path.is_dir():
            return armed
        for entity_dir in sorted(self.doctrine_path.iterdir()):
            if not entity_dir.is_dir():
                continue
            config = self._read_json(entity_dir / 'entity.json')
            if config and config.get('class') == 'perspective' and config.get('seeding'):
                armed.append({
                    'entity': entity_dir.name,
                    'seed_threshold': config.get('seed_threshold', 0.04),
                    'prune_window': config.get('prune_window', 10),
                })
        return armed

    def sync_complete(self, conversation_text=None, session_label=''):
        """One call replaces {Sync} steps 1-5.
        
        Returns everything Claude needs:
          - Active entity + config (step 2-3)
          - Entity files (full) + linked identities (entity.json only) (step 3-4)
          - Armed seeders + vine resonance scores (step 5)
          - Seed trackers for each armed perspective
          - Handoff content from state/handoff.md (D11)
          - Capability manifest
        
        D11: Handoff carried in payload (no separate file read needed).
        D12: Linked entities return entity.json identity only (tier 1).
             Full linked content available via /enter-payload (tier 3).
        
        If conversation_text provided, scores against all armed perspectives.
        If not, returns armed list without scores (Claude can score later).
        """
        # Steps 1-4: entity state
        active = self._read_json(self.state_path / 'active_entity.json')
        entity_name = active.get('entity') if active else None
        entity_class = active.get('class') if active else None

        config = self._read_json(self.state_path / 'config.json') or {}

        entity_files = {}
        deferred = []
        linked_identities = {}  # D12: tiered loading — identity only
        links = []
        if entity_name:
            # D14: mandatory set + deferred manifest
            entity_path = self.doctrine_path / entity_name
            entity_json = self._read_json(entity_path / 'entity.json')
            mandatory_filenames = self._resolve_mandatory(entity_path, entity_json)
            entity_files = self._load_files(entity_path, mandatory_filenames)
            deferred = self._deferred_manifest(entity_path, mandatory_filenames)
            links = self._linked_entities(entity_name)
            # D12: linked entities get entity.json only (tier 1: identity)
            # Full content available via /enter-payload (tier 3: full)
            for linked_name in links:
                identity = self._read_json(self.doctrine_path / linked_name / 'entity.json')
                if identity:
                    linked_identities[linked_name] = identity

        # Step 5: armed seeders + vine data
        armed = self._armed_seeders()

        vine = {}
        for seeder in armed:
            p_name = seeder['entity']
            v = {
                'config': seeder,
                'tracker': self._read_json(
                    self.doctrine_path / p_name / 'seed_tracker.json') or {},
            }
            # Resonance scores + tracker updates (daemon-local, no MCP)
            # Phase 2-3: daemon scores. Phase 4: daemon writes tracker.
            if conversation_text and perspective_reader.available():
                v['resonance'] = perspective_reader.check(p_name, conversation_text)
                # Phase 4: daemon processes tracker bookkeeping
                vine_result = vine_processor.process(
                    p_name, v['resonance'], v['tracker'], seeder, session_label)
                v['tracker'] = vine_result['tracker']
                v['vine_processing'] = {
                    'changes': vine_result['changes'],
                    'thresholds': vine_result['thresholds'],
                    'written': vine_result['written'],
                }
            else:
                v['resonance'] = None
            vine[p_name] = v

        # D11: Sync carries handoff (entity-local state, then global fallback)
        handoff = None
        if entity_name:
            handoff = self._read_file(self.doctrine_path / entity_name / 'state' / 'handoff.md')
        if handoff is None:
            handoff = self._read_file(self.state_path / 'handoff.md')

        return {
            'active_entity': entity_name,
            'active_class': entity_class,
            'config': config,
            'entity_files': entity_files,
            'deferred_manifest': deferred,  # D14: non-mandatory files available via /read
            'links': links,
            'linked_identities': linked_identities,  # D12: entity.json only
            'armed_seeders': armed,
            'vine': vine,
            'handoff': handoff,
            'heatmap': daemon_heatmap.for_chunk(),
            # A3/T1-F1: capabilities removed — dead weight (~300 tokens/sync). Available via /status.
            'daemon_version': '3.0.0',
        }

    def sync_payload(self):
        """One call replaces {Sync} steps 1-4 + armed seeder scan.
        
        Returns: active entity, config, entity files, linked entity files,
        armed seeders, and capability manifest.
        Kept for backward compatibility. Use sync_complete for full vine pass.
        """
        # Active entity
        active = self._read_json(self.state_path / 'active_entity.json')
        entity_name = active.get('entity') if active else None
        entity_class = active.get('class') if active else None

        # Config
        config = self._read_json(self.state_path / 'config.json') or {}

        # Entity files + linked files
        entity_files = {}
        linked_files = {}
        links = []
        if entity_name:
            entity_files = self._entity_files(entity_name)
            links = self._linked_entities(entity_name)
            for linked_name in links:
                linked_files[linked_name] = self._entity_files(linked_name)

        # Armed seeders
        armed = self._armed_seeders()

        return {
            'active_entity': entity_name,
            'active_class': entity_class,
            'config': config,
            'entity_files': entity_files,
            'links': links,
            'linked_files': linked_files,
            'armed_seeders': armed,
            'capabilities': self.CAPABILITIES,
            'daemon_version': '2.0.0',
        }

    def enter_payload(self, entity_name):
        """One call replaces {Enter} file cascade.

        D14: Same mandatory/deferred split as sync_complete.
        Returns: entity config, mandatory entity files, deferred manifest, linked entity files.
        """
        entity_path = self.doctrine_path / entity_name
        config = self._read_json(entity_path / 'entity.json')
        if not config:
            return {'error': f'Entity not found: {entity_name}'}

        # D14: mandatory set + deferred manifest
        mandatory_filenames = self._resolve_mandatory(entity_path, config)
        entity_files = self._load_files(entity_path, mandatory_filenames)
        deferred = self._deferred_manifest(entity_path, mandatory_filenames)

        links = config.get('links', [])
        linked_files = {}
        for linked_name in links:
            linked_files[linked_name] = self._entity_files(linked_name)

        return {
            'entity': entity_name,
            'class': config.get('class', 'unknown'),
            'config': config,
            'entity_files': entity_files,
            'deferred_manifest': deferred,  # D14
            'links': links,
            'linked_files': linked_files,
        }

    def vine_data(self, perspective_name):
        """One call assembles all vine lifecycle data.
        
        Returns: seed_tracker, seed files, ROOT file list, entity config.
        """
        config = self._read_json(self.doctrine_path / perspective_name / 'entity.json')
        if not config:
            return {'error': f'Perspective not found: {perspective_name}'}
        if config.get('class') != 'perspective':
            return {'error': f'{perspective_name} is {config.get("class")}-class, not perspective'}

        # Seed tracker
        tracker = self._read_json(self.doctrine_path / perspective_name / 'seed_tracker.json') or {}

        # Categorize files
        entity_dir = self.doctrine_path / perspective_name
        roots = {}
        seeds = {}
        pruned = {}
        other = {}

        for f in sorted(entity_dir.iterdir()):
            if not f.is_file() or f.suffix not in ('.md', '.json'):
                continue
            name = f.name
            content = self._read_file(f)
            if content is None:
                continue
            if name.startswith('ROOT-') or name.startswith('ROOT_'):
                roots[name] = content
            elif name.startswith('G-pruned-') or name.startswith('_pruned_'):
                pruned[name] = content
            elif name in ('entity.json', 'seed_tracker.json', 'SHOWCASE.md'):
                other[name] = content
            else:
                seeds[name] = content

        return {
            'perspective': perspective_name,
            'config': config,
            'seed_threshold': config.get('seed_threshold', 0.04),
            'seeding_armed': config.get('seeding', False),
            'tracker': tracker,
            'roots': roots,
            'seeds': seeds,
            'pruned': pruned,
            'other': other,
            'counts': {
                'roots': len(roots),
                'seeds': len(seeds),
                'pruned': len(pruned),
                'tracked': len(tracker),
            },
        }

    def obligations(self):
        """Derive obligations from state. What MUST happen.
        
        Armed subsystems create non-optional obligations.
        Server generates from state, not self-report.
        """
        obligations = []
        warnings = []

        # 1. Active entity check
        active = self._read_json(self.state_path / 'active_entity.json')
        entity_name = active.get('entity') if active else None

        # 2. Armed seeders → vine pass obligated during Sync
        armed = self._armed_seeders()
        for seeder in armed:
            obligations.append({
                'type': 'vine_pass',
                'entity': seeder['entity'],
                'reason': f"Perspective {seeder['entity']} has seeding armed",
                'trigger': '{Sync} step 5',
            })

        # 3. Empty CORE check (project entities)
        for entity_dir in sorted(self.doctrine_path.iterdir()):
            if not entity_dir.is_dir():
                continue
            config = self._read_json(entity_dir / 'entity.json')
            if not config or config.get('class') != 'project':
                continue
            core_path = entity_dir / 'CORE.md'
            if not core_path.is_file():
                warnings.append({
                    'type': 'empty_core',
                    'entity': entity_dir.name,
                    'reason': 'Project has no CORE.md file',
                })
            else:
                content = self._read_file(core_path)
                if content and len(content.strip()) < 10:
                    warnings.append({
                        'type': 'empty_core',
                        'entity': entity_dir.name,
                        'reason': 'CORE.md exists but is effectively empty',
                    })

        # 4. Stale handoff check
        handoff_path = self.state_path / 'handoff.md'
        if handoff_path.is_file():
            try:
                mtime = handoff_path.stat().st_mtime
                age_hours = (time.time() - mtime) / 3600
                if age_hours > 48:
                    warnings.append({
                        'type': 'stale_handoff',
                        'age_hours': round(age_hours, 1),
                        'reason': 'Global handoff is more than 48 hours old',
                    })
            except Exception:
                pass

        # 5. Config state
        config = self._read_json(self.state_path / 'config.json') or {}

        return {
            'obligations': obligations,
            'warnings': warnings,
            'active_entity': entity_name,
            'save_confirmation': config.get('save_confirmation', True),
            'armed_seeders': len(armed),
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
        }


payloads = None  # initialized in __main__


# ─── HTTP Server ───────────────────────────────────────────

index = None  # initialized in __main__
watcher = None  # initialized in __main__


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
            if mode not in ('auto', 'explore', 'retrieve'):
                mode = 'auto'
            if scope_override == 'all':
                all_entities = []
                try:
                    for entry in Path(DOCTRINE_PATH).iterdir():
                        if entry.is_dir():
                            all_entities.append(entry.name)
                except Exception:
                    pass
                temp = SearchIndex()
                temp.build(force_scope=all_entities)
                result = temp.search(query, top_n=top_n, entity_filter=entity_filter, mode=mode)
            else:
                result = index.search(query, top_n=top_n, entity_filter=entity_filter, mode=mode)
            self._json(200, result)

        elif path == '/load':
            # Load external corpus — pauses doctrine watcher
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
            # Return to doctrine index — resumes watcher
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
            if 'error' in result:
                self._json(400, result)
            else:
                self._json(200, result)

        elif path == '/copy':
            from_path = params.get('from', [''])[0]
            to_path = params.get('to', [''])[0]
            if not from_path or not to_path:
                self._json(400, {'error': 'Missing ?from= and ?to= parameters'})
                return
            from_path = unquote(from_path)
            to_path = unquote(to_path)
            result = file_ops.copy(from_path, to_path)
            if 'error' in result:
                self._json(400, result)
            else:
                self._json(200, result)

        elif path == '/export':
            entity = params.get('entity', [None])[0]
            output = params.get('output', [None])[0]
            if output:
                output = unquote(output)
            result = file_ops.export(entity_filter=entity, output_path=output)
            if 'error' in result:
                self._json(400, result)
            else:
                self._json(200, result)

        # ── Composite Payloads (Data Assembly Layer) ──
        elif path == '/sync-complete':
            # GET: entity state + armed seeders + trackers (no vine scores)
            # POST with {"text": "..."}: adds vine resonance scores
            result = payloads.sync_complete(conversation_text=None)
            self._json(200, result)

        elif path == '/sync-payload':
            result = payloads.sync_payload()
            self._json(200, result)

        elif path == '/enter-payload':
            entity = params.get('entity', [None])[0]
            if not entity:
                self._json(400, {'error': 'Missing ?entity= parameter'})
                return
            result = payloads.enter_payload(entity)
            if 'error' in result:
                self._json(400, result)
            else:
                self._json(200, result)

        elif path == '/vine-data':
            perspective = params.get('perspective', [None])[0]
            if not perspective:
                self._json(400, {'error': 'Missing ?perspective= parameter'})
                return
            result = payloads.vine_data(perspective)
            if 'error' in result:
                self._json(400, result)
            else:
                self._json(200, result)

        elif path == '/obligations':
            result = payloads.obligations()
            self._json(200, result)

        # ── Daemon Heat Map (bypasses class matrix) ──
        elif path == '/heatmap-touch':
            concepts_raw = params.get('concepts', [''])[0]
            context = params.get('context', [''])[0]
            if not concepts_raw:
                self._json(400, {'error': 'Requires ?concepts=a,b,c'})
                return
            concepts = [c.strip() for c in unquote(concepts_raw).split(',') if c.strip()]
            result = daemon_heatmap.touch(concepts, unquote(context) if context else '')
            self._json(200, result)

        elif path == '/heatmap-hot':
            top_k = int(params.get('top_k', ['10'])[0])
            result = daemon_heatmap.hot(top_k)
            self._json(200, result)

        elif path == '/heatmap-chunk':
            result = daemon_heatmap.for_chunk()
            self._json(200, result)

        elif path == '/heatmap-clear':
            result = daemon_heatmap.clear()
            self._json(200, result)

        # ── QAIS Resonance (Daemon-local vine scoring) ──
        elif path == '/resonance-test':
            perspective = params.get('perspective', [None])[0]
            text = params.get('text', [''])[0]
            if not perspective or not text:
                self._json(400, {'error': 'Requires ?perspective=NAME&text=...'})
                return
            text = unquote(text)
            if not perspective_reader.available():
                self._json(500, {'error': 'numpy not available or perspectives dir missing'})
                return
            result = perspective_reader.check(perspective, text)
            if 'error' in result:
                self._json(400, result)
            else:
                self._json(200, result)

        elif path == '/resonance-multi':
            # Score text against all armed perspectives at once
            text = params.get('text', [''])[0]
            if not text:
                self._json(400, {'error': 'Requires ?text=...'})
                return
            text = unquote(text)
            if not perspective_reader.available():
                self._json(500, {'error': 'numpy not available or perspectives dir missing'})
                return
            # Get armed seeders from payload assembler
            armed = payloads._armed_seeders()
            perspectives = [s['entity'] for s in armed]
            if not perspectives:
                self._json(200, {'matches': {}, 'note': 'No armed seeders found'})
                return
            results = perspective_reader.check_multi(perspectives, text)
            self._json(200, {'armed': perspectives, 'results': results})

        else:
            self._json(404, {'error': 'Endpoints: /search, /load, /unload, /duplicates, /orphans, /coverage, /similarity, /status, /reindex, /manifest, /read, /write, /copy, /export, /sync-complete, /enter-payload, /vine-data, /obligations, /heatmap-touch, /heatmap-hot, /heatmap-chunk, /heatmap-clear, /resonance-test, /resonance-multi'})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')

        if path == '/sync-complete':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length).decode('utf-8'))
            except Exception as e:
                self._json(400, {'error': f'Invalid JSON body: {e}'})
                return
            text = body.get('text', '')
            session_label = body.get('session', '')
            if not text:
                self._json(400, {'error': 'Missing "text" in body (conversation context for vine scoring)'})
                return
            result = payloads.sync_complete(conversation_text=text, session_label=session_label)
            self._json(200, result)

        elif path == '/write':
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
            if 'error' in result:
                self._json(400, result)
            else:
                self._json(200, result)

        # ── D13: PowerShell Execution ──
        elif path == '/exec':
            if not ps_executor:
                self._json(500, {'error': 'PowerShell execution module not available'})
                return
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length).decode('utf-8'))
            except Exception as e:
                self._json(400, {'error': f'Invalid JSON body: {e}'})
                return
            card_id = body.get('card_id', '')
            if not card_id:
                self._json(400, {'error': 'Missing "card_id" in body'})
                return
            result = ps_executor.validate_and_execute(
                card_id=card_id,
                dry_run=body.get('dry_run', False),
                initiator=body.get('initiator', 'user'),
                params=body.get('params', {}),
                confirmed=body.get('confirmed', False),
            )
            level = result.get('level', 0)
            status_code = 200 if level < 3 else 403
            self._json(status_code, result)

        else:
            self._json(404, {'error': 'POST endpoints: /sync-complete, /write, /exec'})

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
            if len(text) > 500:
                text = text[:500] + '...'
            lines.append(text)
            lines.append('')
    Path(output_path).write_text('\n'.join(lines), encoding='utf-8')
    return output_path


if __name__ == '__main__':
    # --root: override BOND_ROOT (default: parent of search_daemon/)
    if '--root' in sys.argv:
        ri = sys.argv.index('--root')
        if ri + 1 < len(sys.argv):
            BOND_ROOT = sys.argv[ri + 1]
            DOCTRINE_PATH = os.path.join(BOND_ROOT, 'doctrine')
            STATE_PATH = os.path.join(BOND_ROOT, 'state')

    # Initialize all objects with (possibly overridden) paths
    file_ops = FileOps(BOND_ROOT, STATE_PATH, DOCTRINE_PATH)
    perspective_reader = PerspectiveReader(BOND_ROOT)
    vine_processor = VineProcessor(DOCTRINE_PATH)
    daemon_heatmap = DaemonHeatMap(STATE_PATH)
    payloads = PayloadAssembler(BOND_ROOT, STATE_PATH, DOCTRINE_PATH)
    ps_executor = PowerShellExecutor(BOND_ROOT) if PowerShellExecutor else None
    index = SearchIndex()
    watcher = FileWatcher(index)

    port = DEFAULT_PORT
    if '--port' in sys.argv:
        pi = sys.argv.index('--port')
        if pi + 1 < len(sys.argv):
            port = int(sys.argv[pi + 1])
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
    print(f"   Composite Payloads (Data Assembly Layer):")
    print(f"     GET  http://localhost:{port}/sync-complete              (steps 1-5 no scores)")
    print(f"     POST http://localhost:{port}/sync-complete              (steps 1-5 + vine scores)")
    print(f"     GET  http://localhost:{port}/enter-payload?entity=BOND_MASTER")
    print(f"     GET  http://localhost:{port}/vine-data?perspective=P11-Plumber")
    print(f"     GET  http://localhost:{port}/obligations")
    print()
    print(f"   Daemon Heat Map (bypasses class matrix):")
    print(f"     GET http://localhost:{port}/heatmap-touch?concepts=a,b,c&context=why")
    print(f"     GET http://localhost:{port}/heatmap-hot")
    print(f"     GET http://localhost:{port}/heatmap-chunk")
    print(f"     GET http://localhost:{port}/heatmap-clear")
    print()
    print(f"   QAIS Resonance (Vine Scoring):")
    print(f"     GET http://localhost:{port}/resonance-test?perspective=P11-Plumber&text=...")
    print(f"     GET http://localhost:{port}/resonance-multi?text=...")
    numpy_status = 'available' if HAS_NUMPY else 'NOT FOUND'
    print(f"     numpy: {numpy_status}")
    print(f"     perspectives: {perspective_reader.perspectives_dir}")
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
