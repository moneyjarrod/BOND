/**
 * SLA Panel Service — Markdown splitter + SLACorpus integration
 * 
 * Splits doctrine .md files into searchable paragraphs,
 * builds SLACorpus index at {Enter} time, serves queries.
 * 
 * Paragraph rules (hybrid):
 *   - Headers define sections (label inherits header text)
 *   - Double-newlines split paragraphs within sections
 *   - IS statements are individual units
 *   - Code blocks stay whole
 *   - Frontmatter (entity/class/created) skipped
 */

// ═══════════════════════════════════════════════════════════
// INLINE SLA ENGINE (from doctrine/SLA/sla.js v2)
// Zero dependencies. SPECTRA ranking immutable.
// ═══════════════════════════════════════════════════════════

const SUFFIXES = ['ation','tion','sion','ness','ment','able','ible','ful','ous','ing','ed','ly','s'];

const STEM_EXCEPTIONS = new Set([
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
]);

const STOP_WORDS = new Set([
  'the','be','to','of','and','in','that','have','it','for','on','with','he','as','you','do','at',
  'this','but','his','by','from','they','we','say','her','she','or','an','will','my','one','all',
  'would','there','their','what','so','up','out','if','about','who','get','which','go','me','when',
  'make','can','like','no','just','him','know','take','how','could','them','see','than','been','had',
  'its','was','has','does','are','were','did','am','is','not','don','also','ll','re','ve','won',
  'didn','isn','aren','doesn','some','any','much','more','most','such','very','too','own','same',
  'other','each','every','both','few','many','may','might','shall','should','a','i',
]);

function lightStem(word) {
  if (STEM_EXCEPTIONS.has(word)) return word;
  for (const s of SUFFIXES) {
    if (word.endsWith(s) && word.length - s.length >= 4) return word.slice(0, -s.length);
  }
  return word;
}

function tokenize(text) {
  const expanded = text.toLowerCase().replace(/_/g, ' ');
  const raw = expanded.match(/[a-zA-Z0-9'-]+/g) || [];
  const result = [];
  for (const w of raw) {
    const c = w.replace(/^['-]+|['-]+$/g, '').toLowerCase();
    if (c.length > 1) result.push(lightStem(c));
  }
  return result;
}

function contentStems(text) {
  return tokenize(text).filter(s => !STOP_WORDS.has(s) && s.length > 2);
}

function dot(a, b) { let s = 0; for (let i = 0; i < a.length; i++) s += a[i] * b[i]; return s; }
function vnorm(a) { return Math.sqrt(dot(a, a)); }
function normalize(a) { const n = vnorm(a); if (n === 0) return a.slice(); return a.map(v => v / n); }

const CONFIDENCE_THRESHOLDS = { HIGH: 50, MED: 15 };

function confidenceLevel(margin) {
  if (margin > CONFIDENCE_THRESHOLDS.HIGH) return 'HIGH';
  if (margin > CONFIDENCE_THRESHOLDS.MED) return 'MED';
  return 'LOW';
}

function confidenceInfo(margin) {
  const level = confidenceLevel(margin);
  const map = {
    HIGH: { level, icon: '✓', color: '#22c55e', label: 'Strong match', tokens: 0 },
    MED:  { level, icon: '~', color: '#eab308', label: 'Likely match', tokens: 0 },
    LOW:  { level, icon: '?', color: '#ef4444', label: 'Multiple candidates', tokens: 200 },
  };
  return map[level];
}

class SLACorpus {
  constructor(paragraphs, opts = {}) {
    const { labels = null, anchorK = 5, confuserK = 5, neighborRadius = 2, clusterMap = null } = opts;
    this.paragraphs = paragraphs;
    this.n = paragraphs.length;
    this.labels = labels || paragraphs.map((_, i) => `p${i}`);
    this.anchorK = anchorK;
    this.confuserK = confuserK;
    this.radius = neighborRadius;
    this.clusterMap = clusterMap;

    this.paraTokens = paragraphs.map(p => contentStems(p));
    this.df = {};
    this.vocab = new Set();
    for (const pt of this.paraTokens) {
      const unique = new Set(pt);
      for (const w of unique) { this.vocab.add(w); this.df[w] = (this.df[w] || 0) + 1; }
    }
    this.idf = {};
    for (const w of this.vocab) this.idf[w] = Math.log(this.n / this.df[w]);

    const vocabList = [...this.vocab].sort();
    const vocabIdx = {};
    vocabList.forEach((w, i) => vocabIdx[w] = i);
    const nVocab = vocabList.length;

    this.tfidfNormed = [];
    for (const pt of this.paraTokens) {
      const tf = {};
      for (const w of pt) tf[w] = (tf[w] || 0) + 1;
      const vec = new Array(nVocab).fill(0);
      for (const w in tf) vec[vocabIdx[w]] = tf[w] * this.idf[w];
      this.tfidfNormed.push(normalize(vec));
    }

    this._buildContrastiveAnchors();
    this._buildNeighborhoods();
  }

  _buildContrastiveAnchors() {
    this.confusers = {};
    for (let i = 0; i < this.n; i++) {
      const sims = [];
      for (let j = 0; j < this.n; j++) {
        if (i === j) continue;
        sims.push({ idx: j, sim: dot(this.tfidfNormed[i], this.tfidfNormed[j]) });
      }
      sims.sort((a, b) => b.sim - a.sim);
      this.confusers[i] = sims.slice(0, this.confuserK).map(s => s.idx);
    }
    this.anchors = [];
    for (let i = 0; i < this.n; i++) {
      const pt = this.paraTokens[i];
      const confuserIndices = this.confusers[i];
      const wordScores = {};
      for (const w of new Set(pt)) {
        let presence = 0;
        for (const ci of confuserIndices) { if (new Set(this.paraTokens[ci]).has(w)) presence++; }
        presence /= Math.max(this.confuserK, 1);
        wordScores[w] = (this.idf[w] || 0) * (1.0 - presence);
      }
      const ranked = Object.entries(wordScores).sort((a, b) => b[1] - a[1]).slice(0, this.anchorK);
      const anchorMap = {};
      for (const [w, score] of ranked) anchorMap[w] = score;
      this.anchors.push(anchorMap);
    }
  }

  _buildNeighborhoods() {
    this.neighbors = {};
    for (let i = 0; i < this.n; i++) {
      if (this.clusterMap) {
        const my = this.clusterMap[i];
        const nbrs = [];
        for (let off = -this.radius; off <= this.radius; off++) {
          const ni = i + off;
          if (ni !== i && ni >= 0 && ni < this.n && this.clusterMap[ni] === my) nbrs.push(ni);
        }
        this.neighbors[i] = nbrs;
      } else {
        const nbrs = [];
        for (let ni = Math.max(0, i - this.radius); ni < Math.min(this.n, i + this.radius + 1); ni++) {
          if (ni !== i) nbrs.push(ni);
        }
        this.neighbors[i] = nbrs;
      }
    }
  }

  query(queryText, opts = {}) {
    const { topN = 5, anchorWeight = 15, nbrWeight = 10 } = opts;
    const qStems = new Set(contentStems(queryText));
    const shortlist = this._spectraShortlist(qStems, topN);

    const results = [];
    for (const { idx, spectraScore, overlap } of shortlist) {
      const anchorKeys = Object.keys(this.anchors[idx]);
      const anchorHits = anchorKeys.filter(w => qStems.has(w));
      const nbrResonance = this._neighborhoodResonance(qStems, idx);
      results.push({
        index: idx, label: this.labels[idx], text: this.paragraphs[idx],
        spectra: spectraScore, anchorHits, nbrResonance, overlap: [...overlap],
      });
    }

    let margin = 100.0;
    if (results.length >= 2) {
      const top = results[0], runner = results[1];
      const rawMargin = (top.spectra - runner.spectra) / Math.max(top.spectra, 1e-10) * 100;
      const anchorAdj = anchorWeight * (top.anchorHits.length - runner.anchorHits.length);
      const nbrDenom = Math.max(top.nbrResonance, runner.nbrResonance, 1e-10);
      const nbrAdj = nbrWeight * ((top.nbrResonance - runner.nbrResonance) / nbrDenom);
      margin = Math.max(0.1, Math.min(100, rawMargin + anchorAdj + nbrAdj));
    }

    return { results, margin, confidence: confidenceInfo(margin) };
  }

  _spectraShortlist(qStems, topN) {
    const scores = [];
    const qSize = Math.max(qStems.size, 1);
    for (let i = 0; i < this.n; i++) {
      const verseSet = new Set(this.paraTokens[i]);
      const overlap = new Set();
      for (const w of qStems) { if (verseSet.has(w)) overlap.add(w); }
      let score = 0;
      for (const w of overlap) score += (this.idf[w] || 0);
      score /= qSize;
      scores.push({ idx: i, spectraScore: score, overlap });
    }
    scores.sort((a, b) => b.spectraScore - a.spectraScore);
    return scores.slice(0, topN);
  }

  _neighborhoodResonance(qStems, candidateIdx) {
    const nbrs = this.neighbors[candidateIdx] || [];
    if (nbrs.length === 0) return 0.0;
    let total = 0;
    const qSize = Math.max(qStems.size, 1);
    for (const ni of nbrs) {
      const vs = new Set(this.paraTokens[ni]);
      let score = 0;
      for (const w of qStems) { if (vs.has(w)) score += (this.idf[w] || 0); }
      total += score;
    }
    return (total / nbrs.length) / qSize;
  }

  stats() {
    return { paragraphs: this.n, vocabulary: this.vocab.size };
  }
}


// ═══════════════════════════════════════════════════════════
// MARKDOWN PARAGRAPH SPLITTER
// ═══════════════════════════════════════════════════════════

/**
 * Split a doctrine .md file into labeled paragraphs.
 * 
 * Rules:
 *   - Headers (# ## ###) define sections → label
 *   - Double-newline splits paragraphs within a section
 *   - "IS" lines (starts with "- **X IS") become individual units
 *   - Code blocks (``` ... ```) stay whole
 *   - Frontmatter lines (Entity Class:, Created:, Authority:) skipped
 *   - Empty paragraphs (< 3 content words) skipped
 *   - Tables skipped (lines starting with |)
 * 
 * @param {string} text - Raw markdown content
 * @param {string} source - Source label (entity/file name)
 * @returns {{ paragraphs: string[], labels: string[], clusterMap: Object }}
 */
export function splitMarkdown(text, source = '') {
  const paragraphs = [];
  const labels = [];
  const clusterMap = {};
  let currentHeader = source || 'untitled';
  let clusterIdx = 0;

  // Skip frontmatter patterns
  const SKIP_RE = /^(Entity Class:|Created:|Authority:|Domain:|---|\*\*Entity|^\|)/;

  const lines = text.split('\n');
  let i = 0;
  let inCodeBlock = false;
  let codeBuffer = [];

  while (i < lines.length) {
    const line = lines[i];

    // Code block handling
    if (line.trimStart().startsWith('```')) {
      if (!inCodeBlock) {
        inCodeBlock = true;
        codeBuffer = [line];
      } else {
        codeBuffer.push(line);
        const block = codeBuffer.join('\n').trim();
        if (contentStems(block).length >= 3) {
          paragraphs.push(block);
          labels.push(`${currentHeader} [code]`);
          clusterMap[paragraphs.length - 1] = clusterIdx;
        }
        inCodeBlock = false;
        codeBuffer = [];
      }
      i++;
      continue;
    }
    if (inCodeBlock) {
      codeBuffer.push(line);
      i++;
      continue;
    }

    // Header → new section
    const headerMatch = line.match(/^(#{1,4})\s+(.+)/);
    if (headerMatch) {
      currentHeader = headerMatch[2].trim();
      clusterIdx++;
      i++;
      continue;
    }

    // Skip frontmatter/tables
    if (SKIP_RE.test(line.trim())) {
      i++;
      continue;
    }

    // IS statement → individual unit
    if (line.trim().startsWith('- ') && /\bIS\b/.test(line)) {
      const clean = line.replace(/^-\s*\*?\*?/, '').replace(/\*?\*?\s*$/, '').trim();
      if (contentStems(clean).length >= 3) {
        paragraphs.push(clean);
        labels.push(`${currentHeader} [IS]`);
        clusterMap[paragraphs.length - 1] = clusterIdx;
      }
      i++;
      continue;
    }

    // Accumulate paragraph (until blank line or header)
    const paraLines = [];
    while (i < lines.length) {
      const pl = lines[i];
      if (pl.trim() === '' && paraLines.length > 0) { i++; break; }
      if (pl.match(/^#{1,4}\s+/)) break;
      if (pl.trim() !== '') paraLines.push(pl);
      i++;
    }

    if (paraLines.length > 0) {
      const para = paraLines.join(' ').trim();
      if (!SKIP_RE.test(para) && contentStems(para).length >= 3) {
        paragraphs.push(para);
        labels.push(currentHeader);
        clusterMap[paragraphs.length - 1] = clusterIdx;
      }
    }
  }

  return { paragraphs, labels, clusterMap };
}


// ═══════════════════════════════════════════════════════════
// SEARCH INDEX — Builds and queries across entity files
// ═══════════════════════════════════════════════════════════

/**
 * Build an SLA index from multiple entity file contents.
 * 
 * @param {Array<{name: string, content: string}>} files - Entity files
 * @param {string} entityName - Entity name for labeling
 * @returns {SLACorpus|null}
 */
export function buildIndex(files, entityName) {
  const allParagraphs = [];
  const allLabels = [];
  const allClusterMap = {};

  for (const file of files) {
    const { paragraphs, labels, clusterMap } = splitMarkdown(file.content, `${entityName}/${file.name}`);
    const offset = allParagraphs.length;
    for (let i = 0; i < paragraphs.length; i++) {
      allParagraphs.push(paragraphs[i]);
      allLabels.push(`${entityName}/${file.name} → ${labels[i]}`);
      // Offset cluster indices to keep files separate
      allClusterMap[offset + i] = `${file.name}:${clusterMap[i]}`;
    }
  }

  if (allParagraphs.length === 0) return null;

  return new SLACorpus(allParagraphs, {
    labels: allLabels,
    clusterMap: allClusterMap,
  });
}

export { SLACorpus, contentStems, confidenceLevel, confidenceInfo };
