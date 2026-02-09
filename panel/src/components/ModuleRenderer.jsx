// ModuleRenderer — Expanded module detail view with live stats + tool invocation
// S3/S4: Renders full module panel when clicked from ModuleBay
// S81 polish: data-driven tools, offline/error distinction, loading states
import { useState, useEffect, useCallback } from 'react';

const API = 'http://localhost:3000';

// Tools defined as data — adding a module means adding an entry here, not editing JSX
const MODULE_TOOLS = {
  qais: [
    { id: 'resonate', label: 'Resonate', icon: '🔮', inputLabel: 'Identity|Role|Candidates (comma-sep)', needsInput: true },
    { id: 'exists', label: 'Exists?', icon: '❓', inputLabel: 'Identity to check', needsInput: true },
    { id: 'store', label: 'Store', icon: '💾', inputLabel: 'Identity|Role|Fact', needsInput: true },
    { id: 'get', label: 'Get', icon: '📥', inputLabel: 'Identity|Role', needsInput: true },
    { id: 'stats', label: 'Full Stats', icon: '📊', needsInput: false },
  ],
  iss: [
    { id: 'analyze', label: 'Analyze', icon: '📐', inputLabel: 'Text to analyze', needsInput: true },
    { id: 'compare', label: 'Compare', icon: '⚖️', inputLabel: 'Texts (one per line)', needsInput: true },
    { id: 'status', label: 'Status', icon: '📋', needsInput: false },
  ],
  eap: [
    { id: 'schema', label: 'Schema', icon: '🧬', needsInput: false },
  ],
  limbic: [
    { id: 'scan', label: 'Limbic Scan', icon: '🧠', inputLabel: 'Text to scan', needsInput: true },
    { id: 'status', label: 'Status', icon: '📋', needsInput: false },
  ],
};

// Allow custom modules to define tools in their JSON
function getTools(module) {
  if (module.tools && Array.isArray(module.tools)) return module.tools;
  return MODULE_TOOLS[module.id] || [];
}

export default function ModuleRenderer({ module, onClose }) {
  const [stats, setStats] = useState(module.data || null);
  const [statsError, setStatsError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toolResult, setToolResult] = useState(null);
  const [toolInput, setToolInput] = useState('');
  const [activeTool, setActiveTool] = useState(null);
  const [toolLoading, setToolLoading] = useState(false);

  const tools = getTools(module);

  const refreshStats = useCallback(async () => {
    setLoading(true);
    setStatsError(null);
    try {
      const res = await fetch(`${API}${module.status_endpoint}`, {
        signal: AbortSignal.timeout(3000),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'error' || data.error) {
          setStatsError(data.error || 'Server returned error');
          setStats(data);
        } else {
          setStats(data);
        }
      } else {
        setStatsError(`HTTP ${res.status}`);
      }
    } catch (err) {
      setStatsError(err.name === 'TimeoutError' ? 'Timed out' : 'Offline');
    }
    setLoading(false);
  }, [module.status_endpoint]);

  const invokeTool = useCallback(async (tool) => {
    if (tool.needsInput && !toolInput.trim()) return;
    setToolLoading(true);
    setToolResult(null);

    try {
      const res = await fetch(`${API}/api/mcp/${module.id}/invoke`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool: tool.id, input: toolInput }),
        signal: AbortSignal.timeout(10000),
      });
      const data = await res.json();
      setToolResult({ data, error: null });
    } catch (err) {
      setToolResult({ data: null, error: err.message });
    }
    setToolLoading(false);
  }, [module.id, toolInput]);

  useEffect(() => {
    refreshStats();
  }, [refreshStats]);

  // Status indicator
  const statusLabel = statsError ? (statsError === 'Offline' ? 'offline' : 'error')
    : stats?.status || 'unknown';
  const statusColor = statusLabel === 'active' ? 'var(--amber)'
    : statusLabel === 'error' ? 'var(--red, #e74c3c)'
    : statusLabel === 'offline' ? 'var(--text-muted)'
    : 'var(--text-muted)';

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
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{
            display: 'inline-block',
            width: 8, height: 8,
            borderRadius: '50%',
            background: statusColor,
            boxShadow: statusLabel === 'active' ? `0 0 6px ${statusColor}` : 'none',
          }} />
          <span className="text-muted" style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
            {statusLabel}
          </span>
          {statsError && statusLabel === 'error' && (
            <span style={{ fontSize: '0.65rem', color: 'var(--red, #e74c3c)', fontFamily: 'var(--font-mono)' }}>
              ({statsError})
            </span>
          )}
          <button onClick={refreshStats} className="btn-icon" title="Refresh">
            {loading ? '⏳' : '↻'}
          </button>
          <button onClick={onClose} className="btn-icon" title="Close">✕</button>
        </div>
      </div>

      {/* Stats Grid */}
      {stats && module.display_fields && statusLabel === 'active' && (
        <div className="module-stats-grid">
          {module.display_fields.map((field) => {
            const value = stats[field.key];
            return (
              <div key={field.key} className="module-stat-cell">
                <div className="text-muted" style={{ fontSize: '0.7rem', marginBottom: 4 }}>
                  {field.icon} {field.label}
                </div>
                <div style={{ color: 'var(--amber)', fontWeight: 700, fontSize: '1.1rem', fontFamily: 'var(--font-mono)' }}>
                  {value !== undefined ? String(value) : '—'}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Offline/Error state */}
      {statusLabel === 'offline' && (
        <div className="module-status-banner offline">
          ⚫ Offline — server not responding. Check Python path and sidecar.
        </div>
      )}
      {statusLabel === 'error' && (
        <div className="module-status-banner error">
          🔴 Error — server returned: {statsError}
        </div>
      )}

      {/* Raw Stats (collapsible) */}
      {stats && <RawStats data={stats} />}

      {/* Tools */}
      {tools.length > 0 && (
        <div className="module-tools-section">
          <div className="text-muted" style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', marginBottom: 8 }}>
            TOOLS
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {tools.map((tool) => (
              <button
                key={tool.id}
                className={`module-tool-btn ${activeTool?.id === tool.id ? 'active' : ''}`}
                onClick={() => {
                  if (activeTool?.id === tool.id) {
                    setActiveTool(null);
                    setToolResult(null);
                    setToolLoading(false);
                  } else {
                    setActiveTool(tool);
                    setToolInput('');
                    setToolResult(null);
                    setToolLoading(false);
                    // Auto-fire no-input tools
                    if (!tool.needsInput) {
                      // Defer so state is clean before invocation
                      setTimeout(() => {
                        setToolLoading(true);
                        fetch(`${API}/api/mcp/${module.id}/invoke`, {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ tool: tool.id, input: '' }),
                          signal: AbortSignal.timeout(10000),
                        })
                          .then(r => r.json())
                          .then(data => setToolResult({ data, error: null }))
                          .catch(err => setToolResult({ data: null, error: err.message }))
                          .finally(() => setToolLoading(false));
                      }, 0);
                    }
                  }
                }}
              >
                {tool.icon} {tool.label}
              </button>
            ))}
          </div>

          {/* Tool Input */}
          {activeTool?.needsInput && (
            <div style={{ marginTop: 10 }}>
              <div className="text-muted" style={{ fontSize: '0.7rem', marginBottom: 4 }}>
                {activeTool.inputLabel}
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                <input
                  type="text"
                  value={toolInput}
                  onChange={(e) => setToolInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && invokeTool(activeTool)}
                  className="module-tool-input"
                  placeholder="..."
                  autoFocus
                />
                <button
                  onClick={() => invokeTool(activeTool)}
                  className="module-tool-btn active"
                  disabled={!toolInput.trim() || toolLoading}
                >
                  {toolLoading ? '⏳' : '▶'}
                </button>
                {toolInput && (
                  <button
                    onClick={() => { setToolInput(''); setToolResult(null); }}
                    className="module-tool-btn"
                    title="Clear input"
                  >
                    ✕
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Loading indicator for no-input tools */}
          {toolLoading && !activeTool?.needsInput && (
            <div className="module-tool-result" style={{ color: 'var(--amber)' }}>
              ⏳ Running {activeTool?.label}...
            </div>
          )}

          {/* Tool Result */}
          {toolResult && !toolLoading && (
            <div className="module-tool-result" style={{ position: 'relative' }}>
              {toolResult.error ? (
                <span style={{ color: 'var(--red, #e74c3c)' }}>Error: {toolResult.error}</span>
              ) : (
                <>
                  <button
                    onClick={() => {
                      const text = JSON.stringify(toolResult.data, null, 2);
                      navigator.clipboard.writeText(text).then(() => {
                        const btn = document.getElementById(`copy-btn-${module.id}`);
                        if (btn) { btn.textContent = '✓'; setTimeout(() => btn.textContent = '📋', 1500); }
                      });
                    }}
                    id={`copy-btn-${module.id}`}
                    title="Copy to clipboard"
                    style={{
                      position: 'absolute', top: 6, right: 6,
                      background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                      color: 'var(--text-muted)', padding: '2px 6px', borderRadius: 'var(--radius-sm, 4px)',
                      fontSize: '0.7rem', cursor: 'pointer', transition: 'all 0.15s',
                    }}
                  >
                    📋
                  </button>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', paddingRight: 30 }}>
                    {JSON.stringify(toolResult.data, null, 2)}
                  </pre>
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function RawStats({ data }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div style={{ marginTop: 8 }}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-muted"
        style={{
          background: 'none', border: 'none', cursor: 'pointer',
          fontSize: '0.7rem', fontFamily: 'var(--font-mono)', padding: 0,
          color: 'var(--text-muted)',
        }}
      >
        {expanded ? '▾' : '▸'} Raw JSON
      </button>
      {expanded && (
        <pre className="module-tool-result" style={{ marginTop: 4 }}>
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}
