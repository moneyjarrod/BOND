// ModuleBay — Module management hub with expandable detail panels
// Session 3: Replaces raw SystemStatus cards with interactive bay
import { useState, useCallback } from 'react';
import { useModules } from '../hooks/useModules';
import ModuleRenderer from './ModuleRenderer';

export default function ModuleBay() {
  const { modules, loading, refresh, toggleModule } = useModules();
  const [expandedModule, setExpandedModule] = useState(null);

  const handleExpand = useCallback((mod) => {
    if (expandedModule?.id === mod.id) {
      setExpandedModule(null);
    } else {
      setExpandedModule(mod);
    }
  }, [expandedModule]);

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

  // Separate active vs inactive
  const active = modules.filter(m => m.enabled && m.status === 'active');
  const enabled = modules.filter(m => m.enabled && m.status !== 'active');
  const disabled = modules.filter(m => !m.enabled);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Bay Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span className="text-muted" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
            {active.length} active · {enabled.length} waiting · {disabled.length} off
          </span>
        </div>
        <button onClick={refresh} className="btn-icon" title="Refresh all">
          ↻ Refresh
        </button>
      </div>

      {/* Module Cards */}
      <div className="module-bay-grid">
        {modules.map((mod) => (
          <ModuleBayCard
            key={mod.id}
            module={mod}
            expanded={expandedModule?.id === mod.id}
            onToggle={() => toggleModule(mod.id)}
            onExpand={() => handleExpand(mod)}
          />
        ))}
      </div>

      {/* Expanded Detail Panel */}
      {expandedModule && (
        <ModuleRenderer
          key={expandedModule.id}
          module={expandedModule}
          onClose={() => setExpandedModule(null)}
        />
      )}
    </div>
  );
}

function ModuleBayCard({ module, expanded, onToggle, onExpand }) {
  const isEnabled = module.enabled;
  const isLive = module.status === 'active';

  const borderColor = isEnabled
    ? (isLive ? 'var(--amber)' : 'var(--teal)')
    : 'var(--border)';

  return (
    <div
      className={`card module-bay-card ${expanded ? 'expanded' : ''}`}
      style={{
        borderLeft: `3px solid ${borderColor}`,
        opacity: isEnabled ? 1 : 0.5,
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
      onClick={onExpand}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '1.2rem' }}>{module.icon}</span>
          <div>
            <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{module.name}</span>
            {isLive && (
              <span style={{
                marginLeft: 8,
                display: 'inline-block',
                width: 6, height: 6,
                borderRadius: '50%',
                background: 'var(--amber)',
                boxShadow: '0 0 4px var(--amber)',
              }} />
            )}
          </div>
        </div>

        {/* Toggle — stop propagation so it doesn't expand */}
        <button
          onClick={(e) => { e.stopPropagation(); onToggle(); }}
          title={isEnabled ? 'Disable' : 'Enable'}
          style={{
            position: 'relative',
            width: 36,
            height: 20,
            borderRadius: 10,
            border: `1px solid ${isEnabled ? 'transparent' : 'var(--border)'}`,
            background: isEnabled ? (isLive ? 'var(--amber)' : 'var(--teal)') : 'var(--bg-elevated)',
            cursor: 'pointer',
            transition: 'background 0.2s',
            padding: 0,
            flexShrink: 0,
          }}
        >
          <span style={{
            position: 'absolute',
            top: 2,
            left: isEnabled ? 18 : 2,
            width: 14,
            height: 14,
            borderRadius: '50%',
            background: isEnabled ? '#fff' : 'var(--text-muted)',
            transition: 'left 0.2s',
            boxShadow: '0 1px 2px rgba(0,0,0,0.3)',
          }} />
        </button>
      </div>

      {/* Compact stats when not expanded */}
      {isEnabled && isLive && module.data && !expanded && (
        <div className="text-muted" style={{
          fontSize: '0.7rem',
          fontFamily: 'var(--font-mono)',
          marginTop: 6,
          display: 'flex',
          gap: 10,
          flexWrap: 'wrap',
        }}>
          {(module.display_fields || []).slice(0, 3).map((field) => {
            const value = module.data[field.key];
            return value !== undefined ? (
              <span key={field.key}>
                {field.icon} <span style={{ color: 'var(--amber)' }}>{String(value)}</span>
              </span>
            ) : null;
          })}
        </div>
      )}

      {!isEnabled && (
        <div className="text-muted" style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', marginTop: 4 }}>
          Disabled
        </div>
      )}
    </div>
  );
}
