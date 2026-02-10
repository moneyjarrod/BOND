// Handoff Generator — S94
// Modal: pre-fills CONTEXT + STATE from panel, sends {Handoff} to Claude via bridge,
// Claude returns WORK/DECISIONS/THREADS/FILES, user reviews + writes to disc.

import { useState, useEffect, useCallback } from 'react';

const BRIDGE_PREFIX = 'BOND:';

const SECTION_ORDER = ['context', 'work', 'decisions', 'state', 'threads', 'files'];
const SECTION_LABELS = {
  context: 'CONTEXT',
  work: 'WORK',
  decisions: 'DECISIONS',
  state: 'STATE',
  threads: 'THREADS',
  files: 'FILES',
};
const SECTION_SOURCES = {
  context: 'pre-filled by panel',
  work: 'Claude-drafted',
  decisions: 'Claude-drafted',
  state: 'pre-filled by panel',
  threads: 'Claude-drafted',
  files: 'Claude-drafted',
};

export default function HandoffGenerator({ onClose }) {
  const [sessionNum, setSessionNum] = useState(null);
  const [entityName, setEntityName] = useState(null);
  const [sections, setSections] = useState({
    context: '',
    work: '',
    decisions: '',
    state: '',
    threads: '',
    files: '',
  });
  const [loading, setLoading] = useState(true);
  const [bridgeSent, setBridgeSent] = useState(false);
  const [writing, setWriting] = useState(false);
  const [written, setWritten] = useState(null);
  const [error, setError] = useState(null);

  // Fetch next session number + pre-fill on mount
  useEffect(() => {
    let cancelled = false;
    fetch('/api/handoff/next')
      .then(r => r.json())
      .then(data => {
        if (cancelled) return;
        setSessionNum(data.nextSession);
        setEntityName(data.entityName);
        setSections(prev => ({
          ...prev,
          context: data.context || '',
          state: data.state || '',
        }));
        setLoading(false);
      })
      .catch(err => {
        if (cancelled) return;
        setError(err.message);
        setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  // Update a single section
  const updateSection = useCallback((key, value) => {
    setSections(prev => ({ ...prev, [key]: value }));
  }, []);

  // Send {Handoff} through clipboard bridge to Claude
  const handleBridgeSend = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(BRIDGE_PREFIX + '{Handoff}');
      setBridgeSent(true);
      setTimeout(() => setBridgeSent(false), 2000);
    } catch (err) {
      // Fallback: textarea copy
      const ta = document.createElement('textarea');
      ta.value = BRIDGE_PREFIX + '{Handoff}';
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setBridgeSent(true);
      setTimeout(() => setBridgeSent(false), 2000);
    }
  }, []);

  // Parse Claude's response from clipboard
  const handleParseResponse = useCallback(async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (!text) return;

      // Parse ===SECTION=== delimited format
      const parsed = {};
      const sectionRegex = /===(\w+)===/g;
      let match;
      const markers = [];
      while ((match = sectionRegex.exec(text)) !== null) {
        markers.push({ key: match[1].toLowerCase(), index: match.index + match[0].length });
      }

      for (let i = 0; i < markers.length; i++) {
        const start = markers[i].index;
        const end = i + 1 < markers.length
          ? text.lastIndexOf('===', markers[i + 1].index - markers[i + 1].key.length - 3)
          : text.length;
        const content = text.substring(start, end).trim();
        if (SECTION_ORDER.includes(markers[i].key)) {
          parsed[markers[i].key] = content;
        }
      }

      // Only update sections that were parsed (Claude-drafted ones)
      if (Object.keys(parsed).length > 0) {
        setSections(prev => ({ ...prev, ...parsed }));
      }
    } catch {
      // Clipboard read failed — user can paste manually
    }
  }, []);

  // Write handoff to disc
  const handleWrite = useCallback(async () => {
    if (!sessionNum) return;
    setWriting(true);
    setError(null);
    try {
      const res = await fetch('/api/handoff/write', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session: sessionNum,
          entityName,
          ...sections,
        }),
      });
      const data = await res.json();
      if (data.written) {
        setWritten(data.filename);
      } else {
        setError(data.error || 'Write failed');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setWriting(false);
    }
  }, [sessionNum, entityName, sections]);

  if (loading) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="handoff-modal" onClick={e => e.stopPropagation()}>
          <div className="handoff-loading">Loading handoff data...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="handoff-modal" onClick={e => e.stopPropagation()}>
        <div className="handoff-header">
          <span className="handoff-title">
            GENERATE HANDOFF — S{sessionNum}
          </span>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {error && <div className="handoff-error">{error}</div>}
        {written && (
          <div className="handoff-success">
            Handoff S{sessionNum} written to disc: {written}
          </div>
        )}

        {/* Bridge controls — numbered steps */}
        <div className="handoff-bridge-bar">
          <button
            className={`handoff-bridge-btn ${bridgeSent ? 'sent' : ''}`}
            onClick={handleBridgeSend}
          >
            {bridgeSent ? '✓ {Handoff} sent' : <><span className="step-number">①</span> ⚡ Send {'{'} Handoff {'}'} to Claude</>}
          </button>
          <button className="handoff-bridge-btn" onClick={handleParseResponse}>
            <span className="step-number">②</span> 📋 Parse Claude Response
          </button>
        </div>

        {/* 6 editable sections */}
        <div className="handoff-sections">
          {SECTION_ORDER.map(key => (
            <div key={key} className="handoff-section">
              <label className="handoff-section-label">
                {SECTION_LABELS[key]}
                <span className="handoff-section-source">
                  {SECTION_SOURCES[key]}
                </span>
              </label>
              <textarea
                className="handoff-textarea"
                value={sections[key]}
                onChange={e => updateSection(key, e.target.value)}
                rows={key === 'work' || key === 'files' ? 6 : 4}
                placeholder={`${SECTION_LABELS[key]} content...`}
              />
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="handoff-actions">
          <button className="btn-cancel" onClick={onClose}>Cancel</button>
          <button
            className="btn-confirm"
            onClick={handleWrite}
            disabled={writing || !!written || (!sections.work && !sections.decisions && !sections.threads && !sections.files)}
            title={(!sections.work && !sections.decisions && !sections.threads && !sections.files) ? 'Complete steps ① and ② first' : ''}
          >
            {writing ? 'Writing...' : written ? `✓ ${written}` : <><span className="step-number">③</span> Write Handoff S{sessionNum}</>}
          </button>
        </div>
      </div>
    </div>
  );
}
