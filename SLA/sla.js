/**
 * SLA — Spectral Linguistic Anchorage
 * JavaScript Reference Implementation v2 (Session 90)
 * 
 * Zero dependencies. Runs in browser or Node.
 * 
 * v2 DIFFERENTIAL: SPECTRA ranking is IMMUTABLE.
 * Anchors and neighbors adjust confidence margin only,
 * never reorder candidates. Aligns with CM principle:
 * lower layers narrow within higher layers, never override.
 * 
 * Usage:
 *   const corpus = new SLACorpus(paragraphs, { labels });
 *   const { results, margin, confidence } = corpus.query('search terms');
 */

// ═══════════════════════════════════════════════════════════
// ROSETTA — Stemmer + Stop Words (from doctrine)
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


// ═══════════════════════════════════════════════════════════
// VECTOR MATH — replaces numpy (minimal, no dependencies)
// ═══════════════════════════════════════════════════════════

function dot(a, b) {
  let sum = 0;
  for (let i = 0; i < a.length; i++) sum += a[i] * b[i];
  return sum;
}

function vnorm(a) {
  return Math.sqrt(dot(a, a));
}

function normalize(a) {
  const n = vnorm(a);
  if (n === 0) return a.slice();
  return a.map(v => v / n);
}


// ═══════════════════════════════════════════════════════════
// CONFIDENCE GATE — Hardcoded thresholds. Never drifts.
// ═══════════════════════════════════════════════════════════

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


// ═══════════════════════════════════════════════════════════
// SLA CORPUS — Build-time precomputation + query-time pipeline
// v2 DIFFERENTIAL: SPECTRA ranking immutable, anchors adjust
// confidence margin only. CM principle enforced.
// ═══════════════════════════════════════════════════════════

class SLACorpus {
  /**
   * @param {string[]} paragraphs - Array of text strings (the corpus)
   * @param {Object} [opts]
   * @param {string[]} [opts.labels] - Display labels per paragraph
   * @param {number} [opts.anchorK=5] - Anchors per paragraph
   * @param {number} [opts.confuserK=5] - Confusers for contrastive anchors
   * @param {number} [opts.neighborRadius=2] - Neighborhood window (+/-)
   * @param {Object} [opts.clusterMap] - { paraIndex: clusterLabel }
   */
  constructor(paragraphs, opts = {}) {
    const {
      labels = null,
      anchorK = 5,
      confuserK = 5,
      neighborRadius = 2,
      clusterMap = null,
    } = opts;

    this.paragraphs = paragraphs;
    this.n = paragraphs.length;
    this.labels = labels || paragraphs.map((_, i) => `p${i}`);
    this.anchorK = anchorK;
    this.confuserK = confuserK;
    this.radius = neighborRadius;
    this.clusterMap = clusterMap;

    // Step 1: Tokenize
    this.paraTokens = paragraphs.map(p => contentStems(p));

    // Step 2: IDF (SPECTRA core)
    this.df = {};
    this.vocab = new Set();
    for (const pt of this.paraTokens) {
      const unique = new Set(pt);
      for (const w of unique) {
        this.vocab.add(w);
        this.df[w] = (this.df[w] || 0) + 1;
      }
    }
    this.idf = {};
    for (const w of this.vocab) {
      this.idf[w] = Math.log(this.n / this.df[w]);
    }

    // Step 3: TF-IDF vectors (for confuser cosine similarity)
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

    // Step 4: Contrastive anchors
    this._buildContrastiveAnchors();

    // Step 5: Neighborhoods
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
      const uniqueWords = new Set(pt);
      for (const w of uniqueWords) {
        let presence = 0;
        for (const ci of confuserIndices) {
          if (new Set(this.paraTokens[ci]).has(w)) presence++;
        }
        presence /= Math.max(this.confuserK, 1);
        wordScores[w] = (this.idf[w] || 0) * (1.0 - presence);
      }
      const ranked = Object.entries(wordScores)
        .sort((a, b) => b[1] - a[1])
        .slice(0, this.anchorK);
      const anchorMap = {};
      for (const [w, score] of ranked) anchorMap[w] = score;
      this.anchors.push(anchorMap);
    }
  }

  _buildNeighborhoods() {
    this.neighbors = {};
    for (let i = 0; i < this.n; i++) {
      if (this.clusterMap) {
        const myCluster = this.clusterMap[i];
        const nbrs = [];
        for (let offset = -this.radius; offset <= this.radius; offset++) {
          const ni = i + offset;
          if (ni !== i && ni >= 0 && ni < this.n) {
            if (this.clusterMap[ni] === myCluster) nbrs.push(ni);
          }
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

  // ═══════════════════════════════════════════════════════
  // QUERY TIME — v2 DIFFERENTIAL
  // SPECTRA ranking is immutable. Anchors adjust margin only.
  // ═══════════════════════════════════════════════════════

  /**
   * Full SLA pipeline.
   * @param {string} queryText
   * @param {Object} [opts]
   * @param {number} [opts.topN=5] - Shortlist size
   * @param {number} [opts.anchorWeight=15] - pp per anchor hit differential
   * @param {number} [opts.nbrWeight=10] - pp scaling for neighborhood differential
   * @returns {{ results: Array, margin: number, confidence: Object }}
   */
  query(queryText, opts = {}) {
    const { topN = 5, anchorWeight = 15, nbrWeight = 10 } = opts;
    const qStems = new Set(contentStems(queryText));

    // Layer 1: SPECTRA shortlist — THIS DETERMINES RANKING (immutable)
    const shortlist = this._spectraShortlist(qStems, topN);

    // Build result objects in SPECTRA order (fixed, never reordered)
    const results = [];
    for (const { idx, spectraScore, overlap } of shortlist) {
      const anchorKeys = Object.keys(this.anchors[idx]);
      const anchorHits = anchorKeys.filter(w => qStems.has(w));
      const anchorRatio = anchorHits.length / Math.max(anchorKeys.length, 1);
      const nbrResonance = this._neighborhoodResonance(qStems, idx);

      results.push({
        index: idx,
        label: this.labels[idx],
        text: this.paragraphs[idx],
        spectra: spectraScore,
        anchorHits,
        anchorRatio,
        nbrResonance,
        overlap: [...overlap],
      });
    }

    // Results stay in SPECTRA rank order — DO NOT REORDER

    // Layers 2+3: DIFFERENTIAL confidence adjustment
    // Compare #1 vs #2 anchor and neighbor evidence
    let margin = 100.0;
    if (results.length >= 2) {
      const top = results[0];
      const runner = results[1];

      // Raw SPECTRA margin
      const rawMargin = (top.spectra - runner.spectra) / Math.max(top.spectra, 1e-10) * 100;

      // Anchor differential: +/- pp per hit difference
      const anchorDiff = top.anchorHits.length - runner.anchorHits.length;
      const anchorAdj = anchorWeight * anchorDiff;

      // Neighborhood differential
      const topNbr = top.nbrResonance;
      const runnerNbr = runner.nbrResonance;
      const nbrDenom = Math.max(topNbr, runnerNbr, 1e-10);
      const nbrDiff = (topNbr - runnerNbr) / nbrDenom;
      const nbrAdj = nbrWeight * nbrDiff;

      // Final margin: clamped to [0.1, 100]
      margin = Math.max(0.1, Math.min(100, rawMargin + anchorAdj + nbrAdj));
    }

    const confidence = confidenceInfo(margin);
    return { results, margin, confidence };
  }

  _spectraShortlist(qStems, topN) {
    const scores = [];
    const qSize = Math.max(qStems.size, 1);

    for (let i = 0; i < this.n; i++) {
      const verseSet = new Set(this.paraTokens[i]);
      const overlap = new Set();
      for (const w of qStems) {
        if (verseSet.has(w)) overlap.add(w);
      }
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
      const verseSet = new Set(this.paraTokens[ni]);
      let score = 0;
      for (const w of qStems) {
        if (verseSet.has(w)) score += (this.idf[w] || 0);
      }
      total += score;
    }
    return (total / nbrs.length) / qSize;
  }

  // ═══════════════════════════════════════════════════════
  // ACCESSORS
  // ═══════════════════════════════════════════════════════

  getAnchors(idx) { return this.anchors[idx]; }
  getConfusers(idx) { return this.confusers[idx]; }
  getNeighbors(idx) { return this.neighbors[idx]; }
  getLabel(idx) { return this.labels[idx]; }
  getText(idx) { return this.paragraphs[idx]; }

  /** Get build stats */
  stats() {
    return {
      paragraphs: this.n,
      vocabulary: this.vocab.size,
      anchorsPerPara: this.anchorK,
      confusersPerPara: this.confuserK,
      neighborRadius: this.radius,
    };
  }
}


// ═══════════════════════════════════════════════════════════
// EXPORTS (works in both module and script contexts)
// ═══════════════════════════════════════════════════════════

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { SLACorpus, contentStems, lightStem, tokenize, confidenceLevel, confidenceInfo };
}

if (typeof window !== 'undefined') {
  window.SLA = { SLACorpus, contentStems, lightStem, tokenize, confidenceLevel, confidenceInfo };
}
