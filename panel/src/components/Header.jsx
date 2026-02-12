// 🔥🌊 BOND Control — Header with Van Damme branding + four-class status

const CLASS_COLORS = {
  doctrine:    { bg: 'rgba(210,153,34,0.15)', border: 'rgba(210,153,34,0.4)', color: '#d29922', label: 'DC' },
  project:     { bg: 'rgba(209,154,102,0.15)', border: 'rgba(209,154,102,0.4)', color: '#d19a66', label: 'PC' },
  perspective: { bg: 'rgba(88,166,255,0.15)', border: 'rgba(88,166,255,0.3)', color: '#58a6ff', label: 'PP' },
  library:     { bg: 'rgba(139,148,158,0.15)', border: 'rgba(139,148,158,0.3)', color: '#8b949e', label: 'LB' },
};

import { useState, useEffect } from 'react';

export default function Header({
  activeEntity = null,
  modules = [],
  classCounts = {},
  saveConfirmation = true,
  onSaveConfirmToggle,
}) {
  const [version, setVersion] = useState(null);

  useEffect(() => {
    fetch('/api/version')
      .then(r => r.json())
      .then(setVersion)
      .catch(() => {});
  }, []);
  const activeCount = modules.filter(m => m.status === 'active').length;
  const qais = modules.find(m => m.id === 'qais');
  const iss = modules.find(m => m.id === 'iss');

  const qaisLabel = qais?.status === 'active'
    ? (qais.data?.total_bindings ?? '✓')
    : '--';
  const issLabel = iss?.status === 'active'
    ? (iss.data?.version ?? '✓')
    : '--';

  return (
    <header className="header">
      <div className="header-title">
        <span className="header-logo">🔥🌊</span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
          <span className="header-label">BOND Control</span>
          <span style={{
            fontSize: '0.6rem',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-muted)',
            letterSpacing: '1.5px',
            textTransform: 'uppercase',
            lineHeight: 1,
            marginTop: -1,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}>
            BOND-Claude Van Damme
            {version?.local && (
              <a
                href={version.updateAvailable ? 'https://github.com/moneyjarrod/BOND' : undefined}
                target="_blank"
                rel="noopener noreferrer"
                title={version.updateAvailable
                  ? `Update available: v${version.local} → v${version.remote}. Click to visit repo.`
                  : `v${version.local} — up to date`}
                style={{
                  fontSize: '0.65rem',
                  padding: '2px 7px',
                  borderRadius: 3,
                  background: version.updateAvailable ? 'rgba(210,153,34,0.25)' : 'rgba(139,148,158,0.2)',
                  color: version.updateAvailable ? '#e8b030' : '#b0b8c4',
                  border: `1px solid ${version.updateAvailable ? 'rgba(210,153,34,0.5)' : 'rgba(139,148,158,0.35)'}`,
                  textDecoration: 'none',
                  cursor: version.updateAvailable ? 'pointer' : 'default',
                  letterSpacing: '0.5px',
                  fontWeight: 600,
                }}
              >
                {version.updateAvailable ? `↑ v${version.remote}` : `v${version.local}`}
              </a>
            )}
          </span>
        </div>
        {activeEntity && <ActiveEntityBadge entity={activeEntity} />}
      </div>
      <div className="header-status">
        <StatusItem label="Sys" value={`${activeCount}/${modules.length}`} className={activeCount > 0 ? 'active' : ''} />
        <Sep />
        <StatusItem label="Q" value={String(qaisLabel)} className={qais?.status === 'active' ? 'active' : ''} />
        <Sep />
        <StatusItem label="ISS" value={String(issLabel)} className={iss?.status === 'active' ? 'active' : ''} />
        <Sep />
        <StatusItem label="📋" value="clip" className="active" />
        <Sep />
        <span
          className="status-item"
          onClick={onSaveConfirmToggle}
          title={saveConfirmation ? 'Save confirmation: ON — click to toggle' : 'Save confirmation: OFF — click to toggle'}
          style={{ cursor: 'pointer', userSelect: 'none' }}
        >
          <span className="status-label">💾</span>
          <span className={`status-value ${saveConfirmation ? 'active' : ''}`}
            style={{ opacity: saveConfirmation ? 1 : 0.4 }}
          >{saveConfirmation ? '✓' : '—'}</span>
        </span>
      </div>
    </header>
  );
}

function ActiveEntityBadge({ entity }) {
  const cls = CLASS_COLORS[entity.type] || CLASS_COLORS.library;
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      marginLeft: 12,
      padding: '2px 10px',
      background: cls.bg,
      border: `1px solid ${cls.border}`,
      borderRadius: 'var(--radius-sm)',
      fontFamily: 'var(--font-mono)',
      fontSize: '0.78rem',
      color: cls.color,
    }}>
      <span style={{
        fontSize: '0.6rem',
        opacity: 0.7,
        fontWeight: 600,
      }}>{cls.label}</span>
      {entity.name}
    </span>
  );
}

function StatusItem({ label, value, className = '' }) {
  return (
    <span className="status-item">
      <span className="status-label">{label}</span>
      <span className={`status-value ${className}`}>{value}</span>
    </span>
  );
}

function Sep() {
  return <span className="status-sep">·</span>;
}
