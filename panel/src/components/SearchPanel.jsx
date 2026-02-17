// SearchPanel.jsx — Search interface backed by local search daemon (port 3003)
// Replaces SLA client-side search. Zero browser computation.

import { useState, useCallback, useEffect } from 'react';

const SEARCH_URL = 'http://localhost:3003';

const CONFIDENCE_STYLES = {
  HIGH: { bg: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.3)', icon: '🟢' },
  MED:  { bg: 'rgba(234,179,8,0.12)', border: '1px solid rgba(234,179,8,0.3)', icon: '🟡' },
  LOW:  { bg: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', icon: '🔴' },
};

function formatEscalation(queryText, results) {
  const topConf = results.results[0]?.confidence || 'LOW';
  const candidates = results.results.slice(0, 5).map((r, i) => {
    const sib = r.siblings > 0 ? ` (+${r.siblings} more)` : '';
    return `[${i + 1}] ${r.entity}/${r.file}${r.heading ? ' > ' + r.heading : ''}${sib}\n${r.text.slice(0, 300)}${r.text.length > 300 ? '...' : ''}`;
  }).join('\n\n');

  return `BOND:search:results — ${topConf} confidence (${results.margin}% margin)
Query: "${queryText}"
Scope: ${results.scope || 'all'} | ${results.results.length} results

${candidates}`;
}

export default function SearchPanel() {
  const [input, setInput] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [daemonUp, setDaemonUp] = useState(null);
  const [daemonStats, setDaemonStats] = useState(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);

  // Check daemon health on mount
  useEffect(() => {
    fetch(`${SEARCH_URL}/status`)
      .then(r => r.json())
      .then(data => {
        setDaemonUp(true);
        setDaemonStats(data);
      })
      .catch(() => setDaemonUp(false));
  }, []);

  const handleSearch = useCallback(async () => {
    if (!input.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${SEARCH_URL}/search?q=${encodeURIComponent(input.trim())}`);
      const data = await res.json();
      setResults(data);
    } catch (err) {
      setError('Search daemon unreachable');
      setResults(null);
    }
    setLoading(false);
  }, [input]);

  const handleClear = useCallback(() => {
    setResults(null);
    setInput('');
    setError(null);
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
        {daemonUp === null && <span>⏳ Checking daemon...</span>}
        {daemonUp === false && <span style={{ color: 'var(--status-suspend)' }}>⚠️ Search daemon offline — start with start_bond.bat</span>}
        {daemonUp && daemonStats && (
          <span>🔍 Index: {daemonStats.paragraphs} paragraphs, {daemonStats.vocab_size} terms, {daemonStats.entity_count} entities</span>
        )}
      </div>

      {/* Search input */}
      <div style={{ display: 'flex', gap: 6 }}>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={daemonUp ? 'Search doctrine... (Enter to search, Esc to clear)' : 'Daemon offline...'}
          disabled={!daemonUp}
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
          disabled={!daemonUp || !input.trim() || loading}
          style={{
            padding: '6px 14px',
            background: daemonUp ? 'var(--accent)' : 'var(--bg-elevated)',
            border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
            color: daemonUp ? '#fff' : 'var(--text-muted)',
            fontFamily: 'var(--font-mono)', fontSize: '0.78rem', cursor: 'pointer',
          }}
        >
          {loading ? '...' : 'Search'}
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

      {/* Error */}
      {error && (
        <div style={{ fontSize: '0.75rem', color: 'var(--status-suspend)', fontFamily: 'var(--font-mono)' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Results */}
      {results && results.results.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4 }}>
          {/* Summary bar */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '4px 10px', borderRadius: 'var(--radius-sm)',
            background: 'rgba(168,130,255,0.08)',
            border: '1px solid rgba(168,130,255,0.2)',
            fontSize: '0.75rem', fontFamily: 'var(--font-mono)',
          }}>
            <span>{results.results.length} results</span>
            <span style={{ color: 'var(--text-muted)' }}>margin: {results.margin}%</span>
            <span style={{ color: 'var(--text-muted)' }}>scope: {results.scope}</span>
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
              {copied ? '✓ Copied' : 'Send to Claude →'}
            </button>
          </div>

          {/* Result cards */}
          {results.results.map((r, i) => {
            const style = CONFIDENCE_STYLES[r.confidence] || CONFIDENCE_STYLES.LOW;
            const sib = r.siblings > 0 ? ` (+${r.siblings})` : '';
            return (
              <div key={i} style={{
                padding: '8px 10px',
                background: i === 0 ? 'var(--bg-hover)' : 'transparent',
                border: `1px solid ${i === 0 ? 'rgba(168,130,255,0.3)' : 'var(--border)'}`,
                borderRadius: 'var(--radius-sm)',
              }}>
                {/* Result header */}
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4,
                  fontSize: '0.72rem', fontFamily: 'var(--font-mono)',
                }}>
                  <span>{style.icon}</span>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    #{i + 1}
                  </span>
                  <span style={{ color: 'var(--text-secondary)', flex: 1 }}>
                    {r.entity}/{r.file}{r.heading ? ` > ${r.heading}` : ''}{sib}
                  </span>
                  {r.anchor_hits && r.anchor_hits.length > 0 && (
                    <span style={{ color: 'var(--accent)', fontSize: '0.65rem' }}>
                      ⚓ {r.anchor_hits.join(', ')}
                    </span>
                  )}
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>
                    {r.score}
                  </span>
                </div>

                {/* Paragraph text (truncated for non-top results) */}
                <div style={{
                  fontSize: '0.8rem', lineHeight: 1.5,
                  color: i === 0 ? 'var(--text-primary)' : 'var(--text-secondary)',
                  maxHeight: i === 0 ? 'none' : 80, overflow: 'hidden',
                  whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                }}>
                  {r.text}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* No results */}
      {results && results.results.length === 0 && (
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', padding: 12, textAlign: 'center' }}>
          No results for "{results.query}"
        </div>
      )}
    </div>
  );
}
