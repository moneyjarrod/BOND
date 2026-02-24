// GnoiseModule — D17 Inverted Resonance Auditor UI
// Custom renderer for the GNOISE module bay tile.
// Entity selector, scan trigger, findings list, holding cell reader, triage controls.
import { useState, useEffect, useCallback, useRef } from 'react';

const PRIORITY_META = {
  high:   { color: '#e74c3c', label: 'HIGH' },
  medium: { color: '#f39c12', label: 'MED' },
  low:    { color: 'var(--text-muted)', label: 'LOW' },
};

export default function GnoiseModule({ module, onClose }) {
  const [entities, setEntities] = useState([]);
  const [entity, setEntity] = useState('');
  const [threshold, setThreshold] = useState('0.10');
  const [scanResult, setScanResult] = useState(null);
  const [allResult, setAllResult] = useState(null);    // D25: /gnoise-all response
  const [cellResult, setCellResult] = useState(null);
  const [scanLoading, setScanLoading] = useState(false);
  const [cellLoading, setCellLoading] = useState(false);
  const [triageLoading, setTriageLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(new Set());
  const [exemptDays, setExemptDays] = useState('14');
  const [showSettings, setShowSettings] = useState(false);
  const [scanMode, setScanMode] = useState('entity');   // 'entity' | 'all'
  const [hasActiveEntity, setHasActiveEntity] = useState(false);

  // Load entities + active entity on mount
  useEffect(() => {
    Promise.all([
      fetch('/api/doctrine').then(r => r.json()).catch(() => []),
      fetch('/api/state').then(r => r.json()).catch(() => ({})),
    ]).then(([ents, state]) => {
      const list = Array.isArray(ents) ? ents : (ents?.entities || []);
      setEntities(list);
      const active = state.entity || state.active_entity?.name || state.active_entity || '';
      if (active) {
        setEntity(active);
        setHasActiveEntity(true);
      } else if (list.length > 0) {
        setEntity(list[0].name || list[0]);
      }
    });
  }, []);

  const runScan = useCallback(async () => {
    setScanLoading(true);
    setError(null);
    setScanResult(null);
    setAllResult(null);
    setSelected(new Set());
    try {
      const t = parseFloat(threshold) || 0.10;
      const ed = parseInt(exemptDays) || 14;

      if (scanMode === 'all') {
        // D25: Full system sweep
        const res = await fetch(`/api/daemon/gnoise-all?threshold=${t}&exempt_days=${ed}`, {
          signal: AbortSignal.timeout(30000),
        });
        const data = await res.json();
        if (data.error) {
          setError(data.error);
        } else {
          setAllResult(data);
        }
      } else {
        // Single entity scan
        if (!entity) { setScanLoading(false); return; }
        const res = await fetch(`/api/daemon/gnoise?entity=${encodeURIComponent(entity)}&threshold=${t}&exempt_days=${ed}`, {
          signal: AbortSignal.timeout(15000),
        });
        const data = await res.json();
        if (data.error) {
          setError(data.error);
        } else {
          setScanResult(data);
        }
      }
    } catch (err) {
      setError(err.name === 'TimeoutError' ? 'Scan timed out' : err.message);
    }
    setScanLoading(false);
  }, [entity, threshold, exemptDays, scanMode]);

  const readCell = useCallback(async () => {
    setCellLoading(true);
    setError(null);
    try {
      const url = entity
        ? `/api/daemon/gnoise-cell?entity=${encodeURIComponent(entity)}`
        : '/api/daemon/gnoise-cell';
      const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
      const data = await res.json();
      setCellResult(data);
    } catch (err) {
      setError(err.name === 'TimeoutError' ? 'Timed out' : err.message);
    }
    setCellLoading(false);
  }, [entity]);

  const triageSelected = useCallback(async (action) => {
    if (selected.size === 0) return;
    setTriageLoading(true);
    setError(null);
    try {
      const indices = Array.from(selected).sort((a, b) => a - b).join(',');
      const res = await fetch(
        `/api/daemon/gnoise-triage?entity=${encodeURIComponent(entity)}&indices=${indices}&action=${action}`,
        { signal: AbortSignal.timeout(5000) }
      );
      const data = await res.json();
      if (data.error) {
        setError(data.error);
      } else {
        setSelected(new Set());
        // Refresh cell view
        readCell();
      }
    } catch (err) {
      setError(err.message);
    }
    setTriageLoading(false);
  }, [selected, entity, readCell]);

  const toggleSelect = (idx) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const selectAll = (findings) => {
    if (!findings) return;
    const untriaged = findings
      .map((f, i) => ({ ...f, idx: i }))
      .filter(f => !f.triaged);
    if (selected.size === untriaged.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(untriaged.map(f => f.idx)));
    }
  };

  // Priority breakdown from scan findings
  const priorityBreakdown = scanResult?.findings
    ? {
        high: scanResult.findings.filter(f => f.priority === 'high').length,
        medium: scanResult.findings.filter(f => f.priority === 'medium').length,
        low: scanResult.findings.filter(f => f.priority === 'low').length,
      }
    : null;

  return (
    <div className="module-renderer">
      {/* Header */}
      <div className="module-renderer-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: '1.5rem' }}>{module.icon}</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>GNOISE</div>
            <div className="text-muted" style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', marginTop: 1 }}>
              Noise Gnome
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button onClick={onClose} className="btn-icon" title="Close">{'\u2715'}</button>
        </div>
      </div>

      {/* Entity Selector + Scan Controls */}
      <div style={{ padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
        {/* D25: Mode toggle — Active Entity vs Full System */}
        <div style={{ display: 'flex', gap: 0, marginBottom: 10 }}>
          <ModeTab
            label="Active Entity"
            active={scanMode === 'entity'}
            disabled={!hasActiveEntity}
            tooltip={!hasActiveEntity ? 'No entity active' : undefined}
            onClick={() => hasActiveEntity && setScanMode('entity')}
            side="left"
          />
          <ModeTab
            label="Full System"
            active={scanMode === 'all'}
            onClick={() => setScanMode('all')}
            side="right"
          />
        </div>

        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          {scanMode === 'entity' && (
            <EntityDropdown
              entities={entities}
              value={entity}
              onChange={setEntity}
            />
          )}
          <button
            onClick={runScan}
            disabled={(scanMode === 'entity' && !entity) || scanLoading}
            style={{
              padding: '5px 14px', fontSize: '0.78rem', fontFamily: 'var(--font-mono)',
              fontWeight: 600, background: 'var(--amber)', color: '#000',
              border: 'none', borderRadius: 'var(--radius-sm, 4px)',
              cursor: ((scanMode === 'entity' && !entity) || scanLoading) ? 'not-allowed' : 'pointer',
              opacity: ((scanMode === 'entity' && !entity) || scanLoading) ? 0.5 : 1,
            }}
          >
            {scanLoading ? '\u23F3 Scanning...' : scanMode === 'all' ? 'SCAN ALL' : 'SCAN'}
          </button>
          <button
            onClick={readCell}
            disabled={cellLoading}
            style={{
              padding: '5px 10px', fontSize: '0.75rem', fontFamily: 'var(--font-mono)',
              background: 'var(--bg-elevated)', color: 'var(--text-muted)',
              border: '1px solid var(--border)', borderRadius: 'var(--radius-sm, 4px)',
              cursor: cellLoading ? 'not-allowed' : 'pointer',
            }}
          >
            {cellLoading ? '\u23F3' : 'Read Cell'}
          </button>
          <button
            onClick={() => setShowSettings(!showSettings)}
            style={{
              padding: '5px 8px', fontSize: '0.7rem', fontFamily: 'var(--font-mono)',
              background: 'var(--bg-elevated)', color: 'var(--text-muted)',
              border: '1px solid var(--border)', borderRadius: 'var(--radius-sm, 4px)',
              cursor: 'pointer',
            }}
            title="Scan settings"
          >
            {'\u2699'} Settings
          </button>
        </div>

        {/* Settings panel (collapsible) */}
        {showSettings && (
          <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="text-muted" style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', width: 75 }}>
                Threshold:
              </span>
              <input
                type="number"
                step="0.01"
                min="0.01"
                max="1.0"
                value={threshold}
                onChange={(e) => setThreshold(e.target.value)}
                className="module-tool-input"
                style={{ width: 70, fontSize: '0.75rem' }}
              />
              <span className="text-muted" style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)' }}>
                lower = stricter, default 0.10
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="text-muted" style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', width: 75 }}>
                Exempt:
              </span>
              <input
                type="number"
                step="1"
                min="0"
                max="90"
                value={exemptDays}
                onChange={(e) => setExemptDays(e.target.value)}
                className="module-tool-input"
                style={{ width: 70, fontSize: '0.75rem' }}
              />
              <span className="text-muted" style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)' }}>
                days — new content needs time to settle
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div style={{
          padding: '8px 12px', margin: '8px 0',
          background: 'rgba(231,76,60,0.1)', border: '1px solid rgba(231,76,60,0.3)',
          borderRadius: 'var(--radius-sm, 4px)', fontSize: '0.75rem',
          color: '#e74c3c', fontFamily: 'var(--font-mono)',
        }}>
          {error}
        </div>
      )}

      {/* Scan Result: Skipped (library class) */}
      {scanResult?.skipped && (
        <div style={{
          padding: '12px 16px', margin: '8px 0',
          background: 'rgba(86,212,221,0.08)', border: '1px solid rgba(86,212,221,0.2)',
          borderRadius: 'var(--radius-sm, 4px)',
        }}>
          <div style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--teal)' }}>
            {scanResult.entity}
          </div>
          <div className="text-muted" style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', marginTop: 4 }}>
            {scanResult.reason}
          </div>
        </div>
      )}

      {/* Scan Result: Findings */}
      {scanResult && !scanResult.skipped && !scanResult.error && (
        <div style={{ padding: '8px 0' }}>
          {/* Stats row */}
          <div style={{
            display: 'flex', gap: 16, padding: '8px 0', flexWrap: 'wrap',
            borderBottom: '1px solid var(--border)', marginBottom: 8,
          }}>
            <StatCell label="Scanned" value={scanResult.scanned} />
            <StatCell label="Findings" value={scanResult.findings_total} color={scanResult.findings_total > 0 ? '#e74c3c' : 'var(--amber)'} />
            <StatCell label="New" value={scanResult.findings_new} />
            <StatCell label="Dedup" value={scanResult.findings_duplicate} />
            <StatCell label="Skipped (recent)" value={scanResult.skipped_recent} />
            <StatCell label="Identity" value={scanResult.identity_files?.join(', ')} small />
          </div>

          {/* Priority breakdown */}
          {priorityBreakdown && scanResult.findings_total > 0 && (
            <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
              {Object.entries(PRIORITY_META).map(([key, meta]) => (
                <span key={key} style={{
                  fontSize: '0.65rem', fontFamily: 'var(--font-mono)',
                  padding: '2px 8px', borderRadius: 3,
                  background: meta.color + '18', color: meta.color,
                }}>
                  {meta.label}: {priorityBreakdown[key]}
                </span>
              ))}
            </div>
          )}

          {/* Findings list */}
          {scanResult.findings?.length > 0 && (
            <FindingsList
              findings={scanResult.findings}
              selected={selected}
              onToggle={toggleSelect}
              onSelectAll={() => selectAll(scanResult.findings)}
            />
          )}

          {/* Recency explanation when files were skipped */}
          {scanResult.skipped_recent > 0 && (
            <div style={{
              padding: '6px 10px', margin: '4px 0',
              background: 'rgba(86,212,221,0.06)', border: '1px solid rgba(86,212,221,0.15)',
              borderRadius: 'var(--radius-sm, 4px)',
              fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)',
            }}>
              {scanResult.skipped_recent} file{scanResult.skipped_recent !== 1 ? 's' : ''} skipped
              {' \u2014 modified in the last '}{scanResult.exempt_days}{' days.'}
              {' New content scores low naturally; that\u2019s growth, not noise.'}
              {' Adjust in '}<span onClick={() => setShowSettings(true)} style={{ color: 'var(--teal)', cursor: 'pointer' }}>{'\u2699 settings'}</span>{' to include newer files.'}
            </div>
          )}

          {scanResult.findings_total === 0 && (
            <div className="text-muted" style={{
              fontSize: '0.75rem', fontFamily: 'var(--font-mono)', padding: '12px 0', textAlign: 'center',
            }}>
              {scanResult.skipped_recent > 0
                ? `All auditable content passed at ${scanResult.threshold}. Try reducing the exemption window to scan newer files.`
                : `No noise detected at threshold ${scanResult.threshold}`
              }
            </div>
          )}
        </div>
      )}

      {/* D25: Full System Sweep Results */}
      {allResult && (
        <div style={{ padding: '8px 0' }}>
          {/* Summary stats */}
          <div style={{
            display: 'flex', gap: 16, padding: '8px 0', flexWrap: 'wrap',
            borderBottom: '1px solid var(--border)', marginBottom: 8,
          }}>
            <StatCell label="Entities" value={allResult.summary.total_entities} />
            <StatCell label="Scanned" value={allResult.summary.scanned} />
            <StatCell label="Libraries" value={allResult.summary.skipped_library} color="var(--text-muted)" />
            <StatCell label="Errors" value={allResult.summary.skipped_error} color={allResult.summary.skipped_error > 0 ? '#e74c3c' : 'var(--text-muted)'} />
            <StatCell label="Findings" value={allResult.summary.total_findings} color={allResult.summary.total_findings > 0 ? '#e74c3c' : 'var(--amber)'} />
            <StatCell label="With Issues" value={allResult.summary.entities_with_findings} />
          </div>

          {/* Per-entity results */}
          <div style={{ maxHeight: 400, overflowY: 'auto' }}>
            {allResult.entities.map((ent, i) => (
              <AllEntityRow key={ent.entity || i} result={ent} />
            ))}
          </div>
        </div>
      )}

      {/* Cell View */}
      {cellResult && (
        <div style={{ padding: '8px 0', borderTop: '1px solid var(--border)' }}>
          <div className="text-muted" style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', marginBottom: 8 }}>
            HOLDING CELL
          </div>
          <div style={{ display: 'flex', gap: 16, marginBottom: 8 }}>
            <StatCell label="Total" value={cellResult.total} />
            <StatCell label="Untriaged" value={cellResult.untriaged} color={cellResult.untriaged > 0 ? '#f39c12' : undefined} />
            <StatCell label="Triaged" value={cellResult.triaged} />
          </div>

          {cellResult.findings?.length > 0 && (
            <FindingsList
              findings={cellResult.findings}
              selected={selected}
              onToggle={toggleSelect}
              onSelectAll={() => selectAll(cellResult.findings)}
              showTriaged
            />
          )}

          {cellResult.total === 0 && (
            <div className="text-muted" style={{
              fontSize: '0.75rem', fontFamily: 'var(--font-mono)', padding: '8px 0', textAlign: 'center',
            }}>
              Holding cell empty
            </div>
          )}
        </div>
      )}

      {/* Triage Controls */}
      {selected.size > 0 && (
        <div style={{
          position: 'sticky', bottom: 0,
          background: 'var(--bg)', borderTop: '1px solid var(--border)',
          padding: '8px 0', display: 'flex', gap: 8, alignItems: 'center',
        }}>
          <span className="text-muted" style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)' }}>
            {selected.size} selected
          </span>
          <div style={{ flex: 1 }} />
          <TriageBtn label="Dismiss" action="dismiss" loading={triageLoading} onClick={() => triageSelected('dismiss')} />
          <TriageBtn label="Fixed" action="fixed" loading={triageLoading} onClick={() => triageSelected('fixed')} color="#2ecc71" />
          <TriageBtn label="Defer" action="deferred" loading={triageLoading} onClick={() => triageSelected('deferred')} color="#3498db" />
        </div>
      )}
    </div>
  );
}


// ─── Sub-components ──────────────────────────────────────

function StatCell({ label, value, color, small }) {
  return (
    <div>
      <div className="text-muted" style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)' }}>
        {label}
      </div>
      <div style={{
        color: color || 'var(--amber)', fontWeight: 700,
        fontSize: small ? '0.7rem' : '0.9rem', fontFamily: 'var(--font-mono)',
      }}>
        {value !== undefined && value !== null ? String(value) : '\u2014'}
      </div>
    </div>
  );
}

function FindingsList({ findings, selected, onToggle, onSelectAll, showTriaged }) {
  return (
    <div style={{ maxHeight: 350, overflowY: 'auto' }}>
      {/* Select all header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '4px 0', borderBottom: '1px solid var(--border)', marginBottom: 4,
      }}>
        <input
          type="checkbox"
          checked={selected.size > 0 && selected.size === findings.filter(f => !f.triaged).length}
          onChange={onSelectAll}
          style={{ cursor: 'pointer' }}
        />
        <span className="text-muted" style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)' }}>
          FILE
        </span>
        <span style={{ flex: 1 }} />
        <span className="text-muted" style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', width: 40, textAlign: 'right' }}>
          SCORE
        </span>
        <span className="text-muted" style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', width: 35 }}>
          PRI
        </span>
      </div>

      {findings.map((f, i) => {
        const pm = PRIORITY_META[f.priority] || PRIORITY_META.low;
        const isTr = f.triaged;

        return (
          <div
            key={i}
            style={{
              padding: '6px 0',
              borderBottom: '1px solid var(--border)',
              opacity: isTr ? 0.4 : 1,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="checkbox"
                checked={selected.has(i)}
                onChange={() => onToggle(i)}
                disabled={isTr}
                style={{ cursor: isTr ? 'not-allowed' : 'pointer' }}
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                    {f.source_file}
                  </span>
                  {f.heading && (
                    <span className="text-muted" style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)' }}>
                      {'\u00BB'} {f.heading}
                    </span>
                  )}
                </div>
              </div>
              <span style={{
                fontSize: '0.7rem', fontFamily: 'var(--font-mono)',
                width: 40, textAlign: 'right', color: pm.color,
              }}>
                {f.score}
              </span>
              <span style={{
                fontSize: '0.6rem', fontFamily: 'var(--font-mono)',
                padding: '1px 5px', borderRadius: 3, width: 35, textAlign: 'center',
                background: pm.color + '18', color: pm.color,
              }}>
                {pm.label}
              </span>
            </div>

            {/* Text preview */}
            {f.text_preview && (
              <div className="text-muted" style={{
                fontSize: '0.65rem', fontFamily: 'var(--font-mono)',
                marginTop: 3, marginLeft: 24,
                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                maxWidth: '90%',
              }}>
                {f.text_preview}
              </div>
            )}

            {/* Triage status (in cell view) */}
            {showTriaged && isTr && (
              <div style={{
                fontSize: '0.6rem', fontFamily: 'var(--font-mono)',
                marginTop: 2, marginLeft: 24,
                color: f.triage_action === 'fixed' ? '#2ecc71'
                  : f.triage_action === 'deferred' ? '#3498db'
                  : 'var(--text-muted)',
              }}>
                {'\u2713'} {f.triage_action} {f.triage_timestamp ? `(${f.triage_timestamp})` : ''}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function EntityDropdown({ entities, value, onChange }) {
  const [open, setOpen] = useState(false);
  const pickerRef = useRef(null);

  // Close on outside click — exact BM pattern
  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (pickerRef.current && !pickerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  const current = entities.find(e => (e.name || e) === value);
  const displayValue = current ? (current.name || current) : value || 'Select entity...';

  return (
    <div ref={pickerRef} style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          padding: '5px 14px',
          fontSize: '0.78rem',
          fontFamily: 'var(--font-mono)',
          background: 'rgba(86,212,221,0.08)',
          color: 'var(--teal)',
          border: '1px solid rgba(86,212,221,0.3)',
          borderRadius: 'var(--radius-sm)',
          cursor: 'pointer',
          transition: 'all 0.15s ease',
          minWidth: 160,
          textAlign: 'left',
        }}
        onMouseEnter={e => { e.currentTarget.style.background = 'rgba(86,212,221,0.15)'; }}
        onMouseLeave={e => { e.currentTarget.style.background = 'rgba(86,212,221,0.08)'; }}
      >
        {displayValue} {open ? '\u25B2' : '\u25BC'}
      </button>
      {open && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          marginTop: 6,
          background: '#1e2030',
          border: '1px solid rgba(86,212,221,0.5)',
          borderRadius: 'var(--radius-md)',
          boxShadow: '0 -8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(86,212,221,0.2)',
          minWidth: 220,
          maxHeight: 260,
          overflowY: 'auto',
          zIndex: 1000,
          padding: '6px 0',
        }}>
          {entities.map(e => {
            const name = e.name || e;
            const cls = e.type || e.class || '';
            const isSelected = name === value;
            return (
              <button
                key={name}
                onClick={() => { onChange(name); setOpen(false); }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  width: '100%',
                  padding: '8px 14px',
                  background: isSelected ? 'rgba(86,212,221,0.12)' : 'transparent',
                  border: 'none',
                  color: 'var(--text-primary)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.78rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'background 0.1s ease',
                }}
                onMouseEnter={ev => { ev.currentTarget.style.background = 'rgba(86,212,221,0.12)'; }}
                onMouseLeave={ev => { if (!isSelected) ev.currentTarget.style.background = 'transparent'; }}
              >
                <span style={{ flex: 1 }}>{name}</span>
                {cls && (
                  <span style={{
                    fontSize: '0.6rem',
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                    flexShrink: 0,
                  }}>
                    {cls.slice(0, 3)}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

function ModeTab({ label, active, disabled, tooltip, onClick, side }) {
  const radius = side === 'left' ? '4px 0 0 4px' : '0 4px 4px 0';
  return (
    <button
      onClick={disabled ? undefined : onClick}
      title={tooltip}
      style={{
        padding: '4px 14px', fontSize: '0.7rem', fontFamily: 'var(--font-mono)',
        fontWeight: active ? 700 : 400,
        background: active ? 'var(--amber)' : 'var(--bg-elevated)',
        color: active ? '#000' : disabled ? 'var(--text-muted)' : 'var(--text-primary)',
        border: `1px solid ${active ? 'var(--amber)' : 'var(--border)'}`,
        borderRadius: radius,
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.4 : 1,
        transition: 'all 0.15s ease',
      }}
    >
      {label}
    </button>
  );
}

function AllEntityRow({ result }) {
  const isSkipped = result.status === 'skipped';
  const isError = result.status === 'error';
  const hasFindings = !isSkipped && !isError && result.findings_total > 0;
  const isClean = !isSkipped && !isError && result.findings_total === 0;

  return (
    <div style={{
      padding: '5px 0',
      borderBottom: '1px solid var(--border)',
      display: 'flex', alignItems: 'center', gap: 8,
    }}>
      {/* Status indicator */}
      <span style={{
        fontSize: '0.7rem', width: 14, textAlign: 'center',
        color: isError ? '#e74c3c' : isSkipped ? 'var(--text-muted)' : hasFindings ? '#f39c12' : '#2ecc71',
      }}>
        {isError ? '\u2717' : isSkipped ? '\u2014' : hasFindings ? '\u26A0' : '\u2713'}
      </span>

      {/* Entity name */}
      <span style={{
        fontSize: '0.75rem', fontFamily: 'var(--font-mono)', fontWeight: 600,
        flex: 1, minWidth: 0,
        color: isSkipped ? 'var(--text-muted)' : 'var(--text-primary)',
        opacity: isSkipped ? 0.5 : 1,
      }}>
        {result.entity}
      </span>

      {/* Right-side info */}
      {isSkipped && (
        <span className="text-muted" style={{ fontSize: '0.6rem', fontFamily: 'var(--font-mono)' }}>
          library
        </span>
      )}
      {isError && (
        <span style={{ fontSize: '0.6rem', fontFamily: 'var(--font-mono)', color: '#e74c3c' }}>
          {result.error}
        </span>
      )}
      {isClean && (
        <span style={{ fontSize: '0.6rem', fontFamily: 'var(--font-mono)', color: '#2ecc71' }}>
          clean
        </span>
      )}
      {hasFindings && (
        <span style={{
          fontSize: '0.6rem', fontFamily: 'var(--font-mono)',
          padding: '1px 6px', borderRadius: 3,
          background: 'rgba(243,156,18,0.15)', color: '#f39c12',
        }}>
          {result.findings_total} finding{result.findings_total !== 1 ? 's' : ''}
        </span>
      )}

      {/* Scanned count */}
      {!isSkipped && !isError && (
        <span className="text-muted" style={{ fontSize: '0.6rem', fontFamily: 'var(--font-mono)', width: 30, textAlign: 'right' }}>
          {result.scanned || 0}p
        </span>
      )}
    </div>
  );
}

function TriageBtn({ label, action, loading, onClick, color }) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      style={{
        padding: '4px 10px', fontSize: '0.7rem', fontFamily: 'var(--font-mono)',
        background: color ? color + '18' : 'var(--bg-elevated)',
        color: color || 'var(--text-muted)',
        border: `1px solid ${color ? color + '44' : 'var(--border)'}`,
        borderRadius: 'var(--radius-sm, 4px)',
        cursor: loading ? 'not-allowed' : 'pointer',
      }}
    >
      {loading ? '\u23F3' : label}
    </button>
  );
}
