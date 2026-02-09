// SearchPanel.jsx — SLA search interface for doctrine entities
// Renders in DoctrineViewer when an entity is entered.

import { useState, useCallback } from 'react';

const CONFIDENCE_STYLES = {
  HIGH: { bg: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.3)', icon: '🟢' },
  MED:  { bg: 'rgba(234,179,8,0.12)', border: '1px solid rgba(234,179,8,0.3)', icon: '🟡' },
  LOW:  { bg: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', icon: '🔴' },
};

/**
 * Format SLA shortlist as a compact escalation prompt for Claude.
 * ~200 tokens instead of shipping full corpus.
 */
function formatEscalation(queryText, results) {
  const level = results.confidence.level;
  const candidates = results.results.map((r, i) =>
    `[${i + 1}] ${r.label}\n${r.text.slice(0, 300)}${r.text.length > 300 ? '...' : ''}`
  ).join('\n\n');

  const header = level === 'LOW'
    ? `SLA found ${results.results.length} candidates but can't discriminate. Which best answers the query?`
    : `SLA matched #1 at ${level} confidence (${results.margin.toFixed(1)}% margin). Here's the shortlist for context:`;

  return `BOND:escalate:SLA Search — ${level} confidence (${results.margin.toFixed(1)}% margin)
Query: "${queryText}"

${header}

${candidates}`;
}

export default function SearchPanel({ query, indexReady, indexStats, indexing, error }) {
  const [input, setInput] = useState('');
  const [results, setResults] = useState(null);
  const [copied, setCopied] = useState(false);

  const handleSearch = useCallback(() => {
    if (!input.trim() || !query) return;
    const res = query(input);
    setResults(res);
  }, [input, query]);

  const handleClear = useCallback(() => {
    setResults(null);
    setInput('');
  }, []);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter') handleSearch();
    if (e.key === 'Escape') handleClear();
  }, [handleSearch, handleClear]);

  const handleEscalate = useCallback(async () => {
    if (!results || !input.trim()) return;
    const prompt = formatEscalation(input, results);
    try {
      await navigator.clipboard.writeText(prompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback: select prompt in a temporary textarea
      console.error('Clipboard write failed');
    }
  }, [input, results]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {/* Status bar */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)',
      }}>
        {indexing && <span>⏳ Building index...</span>}
        {indexReady && indexStats && (
          <span>🔍 Index: {indexStats.paragraphs} paragraphs, {indexStats.vocabulary} terms</span>
        )}
        {error && <span style={{ color: 'var(--status-suspend)' }}>⚠️ {error}</span>}
      </div>

      {/* Search input */}
      <div style={{ display: 'flex', gap: 6 }}>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={indexReady ? 'Search doctrine... (Esc to clear)' : 'Waiting for index...'}
          disabled={!indexReady}
          style={{
            flex: 1, padding: '6px 10px',
            background: 'var(--bg-elevated)', border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)',
            fontFamily: 'var(--font-mono)', fontSize: '0.82rem',
            outline: 'none',
          }}
        />
        <button
          onClick={handleSearch}
          disabled={!indexReady || !input.trim()}
          style={{
            padding: '6px 14px',
            background: indexReady ? 'var(--accent)' : 'var(--bg-elevated)',
            border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
            color: indexReady ? '#fff' : 'var(--text-muted)',
            fontFamily: 'var(--font-mono)', fontSize: '0.78rem', cursor: 'pointer',
          }}
        >
          Search
        </button>
        {results && (
          <button
            onClick={handleClear}
            style={{
              padding: '6px 10px',
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)', fontSize: '0.78rem', cursor: 'pointer',
            }}
          >
            ✕
          </button>
        )}
      </div>

      {/* Results */}
      {results && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4 }}>
          {/* Confidence badge */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '4px 10px', borderRadius: 'var(--radius-sm)',
            ...CONFIDENCE_STYLES[results.confidence.level],
            fontSize: '0.75rem', fontFamily: 'var(--font-mono)',
          }}>
            <span>{CONFIDENCE_STYLES[results.confidence.level].icon}</span>
            <span>{results.confidence.label}</span>
            <span style={{ color: 'var(--text-muted)' }}>margin: {results.margin.toFixed(1)}%</span>
            <button
              onClick={handleEscalate}
              style={{
                marginLeft: 'auto', padding: '2px 8px',
                background: 'transparent',
                border: `1px solid ${copied ? 'rgba(34,197,94,0.3)' : 'var(--border)'}`,
                borderRadius: 'var(--radius-sm)',
                color: copied ? '#22c55e' : 'var(--text-secondary)',
                fontFamily: 'var(--font-mono)', fontSize: '0.7rem',
                cursor: 'pointer', transition: 'all 0.15s',
              }}
            >
              {copied ? '✓ Copied — paste to Claude' : results.confidence.level === 'LOW' ? 'Escalate to Claude →' : 'Send to Claude →'}
            </button>
          </div>

          {/* Result cards */}
          {results.results.map((r, i) => (
            <div key={i} style={{
              padding: '8px 10px',
              background: i === 0 ? 'var(--bg-hover)' : 'transparent',
              border: `1px solid ${i === 0 ? 'var(--accent-muted, var(--border))' : 'var(--border)'}`,
              borderRadius: 'var(--radius-sm)',
            }}>
              {/* Result header */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4,
                fontSize: '0.72rem', fontFamily: 'var(--font-mono)',
              }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  #{i + 1}
                </span>
                <span style={{ color: 'var(--text-secondary)', flex: 1 }}>
                  {r.label}
                </span>
                {r.anchorHits.length > 0 && (
                  <span style={{ color: 'var(--accent)', fontSize: '0.65rem' }}>
                    ⚓ {r.anchorHits.join(', ')}
                  </span>
                )}
                <span style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>
                  {r.spectra.toFixed(3)}
                </span>
              </div>

              {/* Paragraph text (truncated) */}
              <div style={{
                fontSize: '0.8rem', lineHeight: 1.5,
                color: i === 0 ? 'var(--text-primary)' : 'var(--text-secondary)',
                maxHeight: i === 0 ? 'none' : 80, overflow: 'hidden',
                whiteSpace: 'pre-wrap', wordBreak: 'break-word',
              }}>
                {r.text}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
