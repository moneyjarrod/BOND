// System Status — Module cards with toggle activation
import { useModules } from '../hooks/useModules';

export default function SystemStatus() {
  const { modules, loading, refresh, toggleModule } = useModules();

  if (loading) {
    return (
      <div className="placeholder">
        <div className="placeholder-text" style={{ fontFamily: 'var(--font-mono)' }}>
          Loading modules...
        </div>
      </div>
    );
  }

  if (modules.length === 0) {
    return (
      <div className="placeholder">
        <div className="placeholder-icon">⚙️</div>
        <div className="placeholder-text">No modules found</div>
        <div className="placeholder-sub">
          Add .json configs to panel/modules/
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 4 }}>
        <button
          onClick={refresh}
          style={{
            padding: '4px 12px',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            cursor: 'pointer',
          }}
        >
          ↻ Refresh
        </button>
      </div>
      <div className="card-grid">
        {modules.map((mod) => (
          <ModuleCard key={mod.id} module={mod} onToggle={() => toggleModule(mod.id)} />
        ))}
      </div>
    </div>
  );
}

function ModuleCard({ module, onToggle }) {
  const isEnabled = module.enabled;
  const isLive = module.status === 'active';

  return (
    <div className="card" style={{
      borderLeft: isEnabled
        ? (isLive ? '3px solid var(--amber)' : '3px solid var(--teal)')
        : '3px solid var(--border)',
      opacity: isEnabled ? 1 : 0.6,
      transition: 'opacity 0.2s, border-color 0.2s',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '1.3rem' }}>{module.icon}</span>
          <span style={{ fontWeight: 600, fontSize: '1rem' }}>{module.name}</span>
        </div>
        <ToggleSwitch enabled={isEnabled} live={isLive} onToggle={onToggle} />
      </div>

      {/* Description */}
      <div className="text-secondary" style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', marginBottom: 10 }}>
        {module.description}
      </div>

      {/* Data fields — only when enabled AND live */}
      {isEnabled && isLive && module.data && module.display_fields ? (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 6,
          padding: '8px 0',
          borderTop: '1px solid var(--border)',
        }}>
          {module.display_fields.map((field) => {
            const value = module.data[field.key];
            return (
              <div key={field.key} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.8rem',
              }}>
                <span className="text-muted">
                  {field.icon} {field.label}
                </span>
                <span style={{ color: 'var(--amber)', fontWeight: 600 }}>
                  {value !== undefined ? String(value) : '—'}
                </span>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-muted" style={{
          fontSize: '0.75rem',
          marginTop: 8,
          fontFamily: 'var(--font-mono)',
          paddingTop: 8,
          borderTop: '1px solid var(--border)',
        }}>
          {!isEnabled ? 'Disabled — click toggle to enable'
            : isLive ? 'Connected — no data fields configured'
            : 'Enabled — waiting for MCP server'}
        </div>
      )}
    </div>
  );
}

function ToggleSwitch({ enabled, live, onToggle }) {
  const bgColor = enabled
    ? (live ? 'var(--amber)' : 'var(--teal)')
    : 'var(--bg-elevated)';

  return (
    <button
      onClick={onToggle}
      title={enabled ? 'Click to disable' : 'Click to enable'}
      style={{
        position: 'relative',
        width: 44,
        height: 24,
        borderRadius: 12,
        border: `1px solid ${enabled ? 'transparent' : 'var(--border)'}`,
        background: bgColor,
        cursor: 'pointer',
        transition: 'background 0.2s, border-color 0.2s',
        padding: 0,
        flexShrink: 0,
      }}
    >
      <span style={{
        position: 'absolute',
        top: 3,
        left: enabled ? 22 : 3,
        width: 16,
        height: 16,
        borderRadius: '50%',
        background: enabled ? '#fff' : 'var(--text-muted)',
        transition: 'left 0.2s',
        boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
      }} />
    </button>
  );
}
