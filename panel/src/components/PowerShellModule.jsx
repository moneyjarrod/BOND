// PowerShellModule — D13 Governed Shell Execution UI
// Custom renderer for the PowerShell module bay tile.
// Master toggle, mode selector, verb switches, card list, execution, log.
import { useState, useEffect, useCallback } from 'react';

// S139: Use relative paths — Vite proxy handles dev routing

const VERB_META = {
  read:    { color: '#2ecc71', risk: 'None',   label: 'Read' },
  copy:    { color: '#3498db', risk: 'Low',    label: 'Copy' },
  move:    { color: '#f39c12', risk: 'Medium', label: 'Move' },
  create:  { color: '#f39c12', risk: 'Medium', label: 'Create' },
  delete:  { color: '#e74c3c', risk: 'High',   label: 'Delete' },
  execute: { color: '#e74c3c', risk: 'High',   label: 'Execute' },
};

const VERB_ORDER = ['read', 'copy', 'move', 'create', 'delete', 'execute'];

export default function PowerShellModule({ module, onClose }) {
  const [config, setConfig] = useState(null);
  const [cards, setCards] = useState([]);
  const [log, setLog] = useState([]);
  const [loading, setLoading] = useState(true);
  const [execResult, setExecResult] = useState(null);
  const [execLoading, setExecLoading] = useState(null);
  const [showNewCard, setShowNewCard] = useState(false);
  const [showLog, setShowLog] = useState(false);

  const refreshAll = useCallback(async () => {
    setLoading(true);
    try {
      const [cfgR, cardsR, logR] = await Promise.all([
        fetch('/api/powershell/config').then(r => r.json()).catch(() => null),
        fetch('/api/powershell/cards').then(r => r.json()).catch(() => ({ cards: [] })),
        fetch('/api/powershell/log').then(r => r.json()).catch(() => ({ entries: [] })),
      ]);
      if (cfgR) setConfig(cfgR);
      setCards(cardsR.cards || []);
      setLog(logR.entries || []);
    } catch {}
    setLoading(false);
  }, []);

  useEffect(() => { refreshAll(); }, [refreshAll]);

  const updateConfig = async (updates) => {
    try {
      const res = await fetch('/api/powershell/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      if (res.ok) {
        const data = await res.json();
        setConfig(data.config);
      }
    } catch {}
  };

  const pollJob = async (jobId, cardId) => {
    const maxAttempts = 60;  // 30 seconds at 500ms intervals
    for (let i = 0; i < maxAttempts; i++) {
      await new Promise(r => setTimeout(r, 500));
      try {
        const res = await fetch(`/api/powershell/job/${jobId}`);
        const data = await res.json();
        if (data.status === 'running') {
          setExecResult({ card: cardId, status: 'running', async: true, elapsed_ms: data.elapsed_ms });
          continue;
        }
        // Job complete
        setExecResult({ card: cardId, ...data });
        setExecLoading(null);
        // Refresh log
        const logR = await fetch('/api/powershell/log').then(r => r.json()).catch(() => ({ entries: [] }));
        setLog(logR.entries || []);
        return;
      } catch (err) {
        setExecResult({ card: cardId, error: `Poll error: ${err.message}` });
        setExecLoading(null);
        return;
      }
    }
    // Timeout
    setExecResult({ card: cardId, error: 'Job timed out waiting for result' });
    setExecLoading(null);
  };

  const executeCard = async (cardId, dryRun = false, params = {}) => {
    setExecLoading(cardId);
    setExecResult(null);
    try {
      const res = await fetch('/api/powershell/exec', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ card_id: cardId, dry_run: dryRun, initiator: 'user', params }),
        signal: AbortSignal.timeout(36000),
      });
      const data = await res.json();
      if (data.async && data.job_id) {
        // D18: Enter polling mode — don't clear execLoading
        setExecResult({ card: cardId, status: 'accepted', async: true, job_id: data.job_id });
        pollJob(data.job_id, cardId);
      } else {
        setExecResult({ card: cardId, dryRun, ...data });
        // Refresh log
        const logR = await fetch('/api/powershell/log').then(r => r.json()).catch(() => ({ entries: [] }));
        setLog(logR.entries || []);
        setExecLoading(null);
      }
    } catch (err) {
      setExecResult({ card: cardId, error: err.message });
      setExecLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="module-renderer">
        <div className="module-renderer-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: '1.5rem' }}>{module.icon}</span>
            <span style={{ fontWeight: 700 }}>{module.name}</span>
          </div>
          <button onClick={onClose} className="btn-icon">✕</button>
        </div>
        <div className="text-muted" style={{ padding: 20, textAlign: 'center', fontFamily: 'var(--font-mono)' }}>
          Loading...
        </div>
      </div>
    );
  }

  const enabled = config?.enabled || false;
  const mode = config?.mode || 'right';
  const verbs = config?.verbs || {};

  return (
    <div className="module-renderer">
      {/* Header */}
      <div className="module-renderer-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: '1.5rem' }}>{module.icon}</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>{module.name}</div>
            <div className="text-muted" style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
              {module.description}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button onClick={refreshAll} className="btn-icon" title="Refresh">↻</button>
          <button onClick={onClose} className="btn-icon" title="Close">✕</button>
        </div>
      </div>

      {/* Master Toggle + Mode */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="text-muted" style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>MASTER</span>
          <ToggleSwitch on={enabled} onToggle={() => updateConfig({ enabled: !enabled })} color={enabled ? 'var(--amber)' : undefined} />
          <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: enabled ? 'var(--amber)' : 'var(--text-muted)' }}>
            {enabled ? 'ON' : 'OFF'}
          </span>
        </div>
        <div style={{ borderLeft: '1px solid var(--border)', paddingLeft: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="text-muted" style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>MODE</span>
          <button
            onClick={() => updateConfig({ mode: 'left' })}
            style={{
              padding: '2px 8px', fontSize: '0.75rem', fontFamily: 'var(--font-mono)',
              background: mode === 'left' ? 'var(--amber)' : 'var(--bg-elevated)',
              color: mode === 'left' ? '#000' : 'var(--text-muted)',
              border: `1px solid ${mode === 'left' ? 'var(--amber)' : 'var(--border)'}`,
              borderRadius: 'var(--radius-sm, 4px)', cursor: 'pointer',
            }}
          >
            ← Auto
          </button>
          <button
            onClick={() => updateConfig({ mode: 'right' })}
            style={{
              padding: '2px 8px', fontSize: '0.75rem', fontFamily: 'var(--font-mono)',
              background: mode === 'right' ? 'var(--teal)' : 'var(--bg-elevated)',
              color: mode === 'right' ? '#000' : 'var(--text-muted)',
              border: `1px solid ${mode === 'right' ? 'var(--teal)' : 'var(--border)'}`,
              borderRadius: 'var(--radius-sm, 4px)', cursor: 'pointer',
            }}
          >
            Manual →
          </button>
        </div>
      </div>

      {/* Verb Whitelist */}
      <div style={{ padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
        <div className="text-muted" style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', marginBottom: 8 }}>
          VERB WHITELIST
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {VERB_ORDER.map(verb => {
            const meta = VERB_META[verb];
            const entry = verbs[verb] || {};
            const verbOn = entry.enabled || false;
            return (
              <div key={verb} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <ToggleSwitch
                  on={verbOn}
                  onToggle={() => {
                    const updated = { [verb]: { enabled: !verbOn } };
                    updateConfig({ verbs: updated });
                  }}
                  color={verbOn ? meta.color : undefined}
                  small
                />
                <span style={{
                  fontSize: '0.7rem', fontFamily: 'var(--font-mono)',
                  color: verbOn ? meta.color : 'var(--text-muted)',
                }}>
                  {meta.label}
                </span>
                <span className="text-muted" style={{ fontSize: '0.6rem' }}>({meta.risk})</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Card List */}
      <div style={{ padding: '12px 0' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <span className="text-muted" style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)' }}>
            CARDS ({cards.length})
          </span>
          <button
            onClick={() => setShowNewCard(!showNewCard)}
            style={{
              fontSize: '0.7rem', fontFamily: 'var(--font-mono)',
              background: 'var(--bg-elevated)', border: '1px solid var(--border)',
              color: 'var(--text-muted)', padding: '2px 8px',
              borderRadius: 'var(--radius-sm, 4px)', cursor: 'pointer',
            }}
          >
            + New Card
          </button>
        </div>

        {cards.length === 0 && (
          <div className="text-muted" style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', padding: '8px 0' }}>
            No cards registered. Drop .json into panel/powershell/cards/ or use "+ New Card".
          </div>
        )}

        {cards.map(card => (
          <CardRow
            key={card.id}
            card={card}
            verbs={verbs}
            masterOn={enabled}
            executing={execLoading === card.id}
            execResult={execResult?.card === card.id ? execResult : null}
            onExecute={(params) => executeCard(card.id, false, params)}
            onDryRun={(params) => executeCard(card.id, true, params)}
          />
        ))}
      </div>

      {/* New Card Form */}
      {showNewCard && <NewCardForm onCreated={() => { setShowNewCard(false); refreshAll(); }} />}

      {/* Execution Result */}
      {execResult && (
        <ExecResultPanel result={execResult} onDismiss={() => setExecResult(null)} />
      )}

      {/* Log Toggle */}
      <div style={{ borderTop: '1px solid var(--border)', paddingTop: 8 }}>
        <button
          onClick={() => setShowLog(!showLog)}
          className="text-muted"
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            fontSize: '0.7rem', fontFamily: 'var(--font-mono)', padding: 0,
            color: 'var(--text-muted)',
          }}
        >
          {showLog ? '▾' : '▸'} Audit Log ({log.length} entries)
        </button>
        {showLog && <LogViewer entries={log} />}
      </div>
    </div>
  );
}


// ─── Sub-components ──────────────────────────────────────

function ToggleSwitch({ on, onToggle, color, small }) {
  const w = small ? 28 : 36;
  const h = small ? 16 : 20;
  const dot = small ? 10 : 14;
  return (
    <button
      onClick={onToggle}
      style={{
        position: 'relative', width: w, height: h, borderRadius: h / 2,
        border: `1px solid ${on ? 'transparent' : 'var(--border)'}`,
        background: on ? (color || 'var(--teal)') : 'var(--bg-elevated)',
        cursor: 'pointer', padding: 0, flexShrink: 0, transition: 'background 0.2s',
      }}
    >
      <span style={{
        position: 'absolute', top: (h - dot) / 2 - 1, left: on ? (w - dot - 3) : 2,
        width: dot, height: dot, borderRadius: '50%',
        background: on ? '#fff' : 'var(--text-muted)',
        transition: 'left 0.2s', boxShadow: '0 1px 2px rgba(0,0,0,0.3)',
      }} />
    </button>
  );
}

function CardRow({ card, verbs, masterOn, executing, execResult, onExecute, onDryRun }) {
  const meta = VERB_META[card.verb] || { color: 'var(--text-muted)', label: card.verb };
  const verbEnabled = verbs[card.verb]?.enabled || false;
  const canRun = masterOn && verbEnabled;

  // D16: dry-run tracking
  const requiresDry = card.requires_dry_run || card.verb === 'delete' || card.verb === 'execute';
  const [dryRunDone, setDryRunDone] = useState(false);

  // Track successful dry runs from exec results
  if (execResult?.dryRun && execResult?.status === 'preview' && !dryRunDone) {
    setDryRunDone(true);
  }

  const canExecute = canRun && (!requiresDry || dryRunDone);

  // Detect argument params that need user input
  const argParams = (card.params || []).filter(p => p.source === 'argument');
  const needsInput = argParams.length > 0;
  const [showParams, setShowParams] = useState(false);
  const [paramValues, setParamValues] = useState({});

  const handleAction = (isDry) => {
    if (needsInput) {
      // Check if all params filled
      const allFilled = argParams.every(p => paramValues[p.name]?.trim());
      if (!allFilled) {
        setShowParams(true);
        return;
      }
      (isDry ? onDryRun : onExecute)(paramValues);
      if (!isDry) {
        setParamValues({});
        setShowParams(false);
      }
    } else {
      (isDry ? onDryRun : onExecute)({});
    }
  };

  return (
    <div style={{
      padding: '8px 10px', marginBottom: 4,
      background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm, 4px)',
      borderLeft: `3px solid ${meta.color}`,
      opacity: canRun ? 1 : 0.5,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{card.name}</span>
            <span style={{
              fontSize: '0.6rem', fontFamily: 'var(--font-mono)',
              padding: '1px 5px', borderRadius: 3,
              background: meta.color + '22', color: meta.color,
            }}>
              {card.verb}
            </span>
            <span className="text-muted" style={{ fontSize: '0.6rem', fontFamily: 'var(--font-mono)' }}>
              {card.scope}
            </span>
            {requiresDry && (
              <span style={{ fontSize: '0.6rem', color: dryRunDone ? '#2ecc71' : 'var(--amber)' }}
                    title={dryRunDone ? 'Dry run complete' : 'Requires dry run'}>
                {dryRunDone ? '\u2705' : '\uD83D\uDD12'}
              </span>
            )}
            {needsInput && (
              <span style={{ fontSize: '0.6rem', color: 'var(--teal)' }} title="Requires parameters">{'\uD83D\uDCDD'}</span>
            )}
          </div>
          {card.description && (
            <div className="text-muted" style={{ fontSize: '0.7rem', marginTop: 2 }}>{card.description}</div>
          )}
        </div>
        <div style={{ display: 'flex', gap: 4, flexShrink: 0, marginLeft: 8 }}>
          <button
            onClick={() => handleAction(true)}
            disabled={!canRun || executing}
            title="Dry run"
            style={{
              fontSize: '0.65rem', fontFamily: 'var(--font-mono)',
              padding: '3px 6px', cursor: canRun ? 'pointer' : 'not-allowed',
              background: 'var(--bg)', border: '1px solid var(--border)',
              color: 'var(--text-muted)', borderRadius: 'var(--radius-sm, 4px)',
            }}
          >
            DRY
          </button>
          <button
            onClick={() => handleAction(false)}
            disabled={!canExecute || executing}
            title={requiresDry && !dryRunDone ? 'Run DRY first' : 'Run'}
            style={{
              fontSize: '0.65rem', fontFamily: 'var(--font-mono)',
              padding: '3px 8px', cursor: canExecute ? 'pointer' : 'not-allowed',
              background: canExecute ? meta.color : 'var(--bg-elevated)',
              color: canExecute ? '#fff' : 'var(--text-muted)',
              border: 'none', borderRadius: 'var(--radius-sm, 4px)',
            }}
          >
            {executing ? '\u23F3' : 'RUN'}
          </button>
        </div>
      </div>

      {/* Parameter input panel — shown for argument-sourced params */}
      {showParams && (
        <div style={{
          marginTop: 8, padding: '8px 10px',
          background: 'var(--bg)', borderRadius: 'var(--radius-sm, 4px)',
          border: '1px solid var(--border)',
        }}>
          {argParams.map(p => (
            <div key={p.name} style={{ marginBottom: 6 }}>
              <label className="text-muted" style={{ fontSize: '0.6rem', fontFamily: 'var(--font-mono)', display: 'block', marginBottom: 2 }}>
                {p.name} {p.validate ? `(${p.validate})` : ''}
              </label>
              <input
                type="text"
                value={paramValues[p.name] || ''}
                onChange={e => setParamValues({ ...paramValues, [p.name]: e.target.value })}
                placeholder={p.name}
                className="module-tool-input"
                style={{ width: '100%', fontSize: '0.75rem' }}
                onKeyDown={e => {
                  if (e.key === 'Enter') {
                    const allFilled = argParams.every(ap => (ap.name === p.name ? e.target.value : paramValues[ap.name])?.trim());
                    if (allFilled) handleAction(false);
                  }
                }}
              />
            </div>
          ))}
          <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
            <button
              onClick={() => setShowParams(false)}
              style={{
                fontSize: '0.6rem', fontFamily: 'var(--font-mono)',
                padding: '2px 8px', background: 'var(--bg-elevated)',
                border: '1px solid var(--border)', borderRadius: 'var(--radius-sm, 4px)',
                color: 'var(--text-muted)', cursor: 'pointer',
              }}
            >Cancel</button>
            <button
              onClick={() => handleAction(true)}
              style={{
                fontSize: '0.6rem', fontFamily: 'var(--font-mono)',
                padding: '2px 8px', background: 'var(--bg-elevated)',
                border: '1px solid var(--border)', borderRadius: 'var(--radius-sm, 4px)',
                color: 'var(--text-muted)', cursor: 'pointer',
              }}
            >DRY</button>
            <button
              onClick={() => handleAction(false)}
              disabled={!argParams.every(p => paramValues[p.name]?.trim())}
              style={{
                fontSize: '0.6rem', fontFamily: 'var(--font-mono)',
                padding: '2px 8px', background: meta.color,
                border: 'none', borderRadius: 'var(--radius-sm, 4px)',
                color: '#fff', cursor: 'pointer', fontWeight: 600,
              }}
            >RUN</button>
          </div>
        </div>
      )}
    </div>
  );
}

function ExecResultPanel({ result, onDismiss }) {
  const levelColors = { 0: '#2ecc71', 1: '#f39c12', 2: '#e74c3c', 3: '#8e44ad' };
  const levelNames = { 0: 'Pass', 1: 'Flag', 2: 'Hold', 3: 'Deny' };
  const isAsyncRunning = result.async && (result.status === 'running' || result.status === 'accepted');
  const level = isAsyncRunning ? -1 : (result.level ?? -1);
  const color = isAsyncRunning ? 'var(--amber)' : (levelColors[level] || 'var(--text-muted)');

  return (
    <div style={{
      background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm, 4px)',
      padding: 12, marginTop: 8, border: `1px solid ${color}33`,
      position: 'relative',
    }}>
      <button
        onClick={onDismiss}
        style={{
          position: 'absolute', top: 6, right: 8,
          background: 'none', border: 'none', color: 'var(--text-muted)',
          cursor: 'pointer', fontSize: '0.8rem',
        }}
      >✕</button>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span style={{
          display: 'inline-block', width: 10, height: 10, borderRadius: '50%',
          background: color,
        }} />
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', fontWeight: 700 }}>
          {result.status?.toUpperCase() || 'RESULT'}
        </span>
        {level >= 0 && (
          <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color }}>
            L{level} {levelNames[level]}
          </span>
        )}
        {result.duration_ms !== undefined && (
          <span className="text-muted" style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)' }}>
            {result.duration_ms}ms
          </span>
        )}
      </div>

      {isAsyncRunning && (
        <div style={{ fontSize: '0.75rem', marginBottom: 6, color: 'var(--amber)', fontFamily: 'var(--font-mono)' }}>
          {'\u23F3'} Running...{result.elapsed_ms ? ` (${Math.round(result.elapsed_ms / 1000)}s)` : ''}
        </div>
      )}

      {result.reason && (
        <div style={{ fontSize: '0.75rem', marginBottom: 6, color }}>
          {result.reason}
        </div>
      )}

      {result.command_preview && (
        <pre style={{
          fontSize: '0.7rem', fontFamily: 'var(--font-mono)',
          background: 'var(--bg)', padding: 8, borderRadius: 4,
          margin: '4px 0', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
          color: 'var(--text)',
        }}>
          {result.command_preview}
        </pre>
      )}

      {result.output && (
        <pre style={{
          fontSize: '0.7rem', fontFamily: 'var(--font-mono)',
          background: 'var(--bg)', padding: 8, borderRadius: 4,
          marginTop: 6, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
          maxHeight: 200, overflow: 'auto', color: 'var(--text)',
        }}>
          {result.output}
        </pre>
      )}

      {result.error && (
        <div style={{ fontSize: '0.75rem', color: '#e74c3c' }}>
          Error: {result.error}
        </div>
      )}
    </div>
  );
}

function NewCardForm({ onCreated }) {
  const [form, setForm] = useState({
    id: '', name: '', description: '', verb: 'read', scope: 'global',
    requires_dry_run: false, command: '', dry_run_command: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const handleSave = async () => {
    if (!form.id || !form.name || !form.command) {
      setError('ID, Name, and Command are required');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      // Write card JSON directly via the cards directory (server reads it)
      // For now, we'll POST to a simple endpoint — but the card is just a file.
      // Use the daemon /write or just save via server.
      // Simplest: POST the card data and let server write it
      const card = { ...form, params: [], post_verify: null };
      const res = await fetch('/api/powershell/cards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(card),
      });
      if (res.ok) {
        onCreated();
      } else {
        const data = await res.json();
        setError(data.error || 'Save failed');
      }
    } catch (err) {
      setError(err.message);
    }
    setSaving(false);
  };

  return (
    <div style={{
      background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm, 4px)',
      padding: 12, marginBottom: 8, border: '1px solid var(--border)',
    }}>
      <div className="text-muted" style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', marginBottom: 8 }}>
        NEW CARD
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        <FormField label="ID" value={form.id} onChange={v => setForm({ ...form, id: v })} placeholder="my-task" />
        <FormField label="Name" value={form.name} onChange={v => setForm({ ...form, name: v })} placeholder="My Task" />
      </div>
      <FormField label="Description" value={form.description} onChange={v => setForm({ ...form, description: v })} placeholder="What this card does" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginTop: 8 }}>
        <div>
          <label className="text-muted" style={{ fontSize: '0.6rem', fontFamily: 'var(--font-mono)', display: 'block', marginBottom: 2 }}>Verb</label>
          <select value={form.verb} onChange={e => setForm({ ...form, verb: e.target.value })} className="module-tool-input" style={{ width: '100%' }}>
            {VERB_ORDER.map(v => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>
        <div>
          <label className="text-muted" style={{ fontSize: '0.6rem', fontFamily: 'var(--font-mono)', display: 'block', marginBottom: 2 }}>Scope</label>
          <select value={form.scope} onChange={e => setForm({ ...form, scope: e.target.value })} className="module-tool-input" style={{ width: '100%' }}>
            <option value="global">global</option>
            <option value="entity">entity</option>
          </select>
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6, paddingBottom: 2 }}>
          <ToggleSwitch on={form.requires_dry_run} onToggle={() => setForm({ ...form, requires_dry_run: !form.requires_dry_run })} small />
          <span className="text-muted" style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)' }}>Dry Run Gate</span>
        </div>
      </div>
      <FormField label="Command" value={form.command} onChange={v => setForm({ ...form, command: v })} placeholder="Get-ChildItem ..." />
      <FormField label="Dry Run Command" value={form.dry_run_command} onChange={v => setForm({ ...form, dry_run_command: v })} placeholder="Get-ChildItem ... (read-only preview command)" />

      {error && <div style={{ color: '#e74c3c', fontSize: '0.7rem', marginTop: 4 }}>{error}</div>}

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 8 }}>
        <button onClick={onCreated} style={{ fontSize: '0.7rem', padding: '4px 10px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm, 4px)', cursor: 'pointer', color: 'var(--text-muted)' }}>
          Cancel
        </button>
        <button onClick={handleSave} disabled={saving} style={{ fontSize: '0.7rem', padding: '4px 10px', background: 'var(--amber)', border: 'none', borderRadius: 'var(--radius-sm, 4px)', cursor: 'pointer', color: '#000', fontWeight: 600 }}>
          {saving ? '...' : 'Save Card'}
        </button>
      </div>
    </div>
  );
}

function FormField({ label, value, onChange, placeholder }) {
  return (
    <div style={{ marginTop: 6 }}>
      <label className="text-muted" style={{ fontSize: '0.6rem', fontFamily: 'var(--font-mono)', display: 'block', marginBottom: 2 }}>
        {label}
      </label>
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="module-tool-input"
        style={{ width: '100%' }}
      />
    </div>
  );
}

function LogViewer({ entries }) {
  if (entries.length === 0) {
    return <div className="text-muted" style={{ fontSize: '0.7rem', padding: '8px 0' }}>No log entries yet.</div>;
  }

  const levelColors = { 0: '#2ecc71', 1: '#f39c12', 2: '#e74c3c', 3: '#8e44ad' };

  return (
    <div style={{ marginTop: 6, maxHeight: 250, overflowY: 'auto' }}>
      {entries.map((entry, i) => (
        <div key={i} style={{
          display: 'flex', gap: 8, alignItems: 'center',
          padding: '4px 0', borderBottom: '1px solid var(--border)',
          fontSize: '0.65rem', fontFamily: 'var(--font-mono)',
        }}>
          <span style={{
            width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
            background: levelColors[entry.level] || 'var(--text-muted)',
          }} />
          <span className="text-muted" style={{ flexShrink: 0, width: 55 }}>
            {entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : '??'}
          </span>
          <span style={{ color: 'var(--amber)', flexShrink: 0, width: 80 }}>{entry.card_id}</span>
          <span style={{ color: VERB_META[entry.verb]?.color || 'var(--text-muted)', flexShrink: 0, width: 50 }}>
            {entry.verb}
          </span>
          <span className="text-muted" style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {entry.output_summary || ''}
          </span>
          {entry.duration_ms !== undefined && (
            <span className="text-muted" style={{ flexShrink: 0 }}>{entry.duration_ms}ms</span>
          )}
        </div>
      ))}
    </div>
  );
}
