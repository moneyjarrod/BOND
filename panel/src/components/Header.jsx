// 🔥🌊 BOND Control — Header with gear menu + AHK bridge controls

const CLASS_COLORS = {
  doctrine:    { bg: 'rgba(210,153,34,0.15)', border: 'rgba(210,153,34,0.4)', color: '#d29922', label: 'DC' },
  project:     { bg: 'rgba(209,154,102,0.15)', border: 'rgba(209,154,102,0.4)', color: '#d19a66', label: 'PC' },
  perspective: { bg: 'rgba(88,166,255,0.15)', border: 'rgba(88,166,255,0.3)', color: '#58a6ff', label: 'PP' },
  library:     { bg: 'rgba(139,148,158,0.15)', border: 'rgba(139,148,158,0.3)', color: '#8b949e', label: 'LB' },
};

import { useState, useEffect, useRef } from 'react';

export default function Header({
  activeEntity = null,
  modules = [],
  classCounts = {},
  saveConfirmation = true,
  onSaveConfirmToggle,
  wsConnected = false,
}) {
  const [version, setVersion] = useState(null);
  const [ahkStatus, setAhkStatus] = useState(null);
  const [gearOpen, setGearOpen] = useState(false);
  const gearRef = useRef(null);

  // Fetch version
  useEffect(() => {
    fetch('/api/version')
      .then(r => r.json())
      .then(setVersion)
      .catch(() => {});
  }, []);

  // Poll AHK status (file-based, lightweight)
  useEffect(() => {
    const poll = () => {
      fetch('/api/ahk-status')
        .then(r => r.json())
        .then(setAhkStatus)
        .catch(() => setAhkStatus(null));
    };
    poll();
    const id = setInterval(poll, 3000);
    return () => clearInterval(id);
  }, []);

  // Close gear menu on outside click
  useEffect(() => {
    if (!gearOpen) return;
    const handler = (e) => {
      if (gearRef.current && !gearRef.current.contains(e.target)) {
        setGearOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [gearOpen]);

  const activeCount = modules.filter(m => m.status === 'active').length;
  const qais = modules.find(m => m.id === 'qais');
  const iss = modules.find(m => m.id === 'iss');

  const qaisLabel = qais?.status === 'active'
    ? (qais.data?.total_bindings ?? '✓')
    : '--';
  const issLabel = iss?.status === 'active'
    ? (iss.data?.version ?? '✓')
    : '--';

  const bridgeOn = ahkStatus?.bridge_active ?? false;
  const bondOn = ahkStatus?.bond_active ?? false;
  const ahkRunning = ahkStatus?.running ?? false;

  const handleBridgeToggle = async () => {
    try { await navigator.clipboard.writeText('BOND:__BRIDGE_TOGGLE__'); } catch {}
  };

  const handleBondToggle = async () => {
    try { await navigator.clipboard.writeText('BOND:__BOND_TOGGLE__'); } catch {}
  };

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
        {/* WebSocket indicator */}
        <span
          className="status-item"
          title={wsConnected ? 'WebSocket connected' : 'WebSocket disconnected'}
        >
          <span style={{
            width: 7, height: 7, borderRadius: '50%', display: 'inline-block',
            background: wsConnected ? '#3fb950' : '#f85149',
            boxShadow: wsConnected ? '0 0 4px rgba(63,185,80,0.5)' : 'none',
          }} />
        </span>
        <Sep />
        <StatusItem label="Sys" value={`${activeCount}/${modules.length}`} className={activeCount > 0 ? 'active' : ''} />
        <Sep />
        <StatusItem label="Q" value={String(qaisLabel)} className={qais?.status === 'active' ? 'active' : ''} />
        <Sep />
        <StatusItem label="ISS" value={String(issLabel)} className={iss?.status === 'active' ? 'active' : ''} />
        <Sep />
        {/* Bridge status — clickable toggle */}
        <span
          className="status-item"
          onClick={handleBridgeToggle}
          title={!ahkRunning ? 'AHK not running' : bridgeOn ? 'Bridge ON — click to pause' : 'Bridge PAUSED — click to resume'}
          style={{ cursor: 'pointer', userSelect: 'none' }}
        >
          <span className="status-label">{bridgeOn ? '📋' : '⏸️'}</span>
          <span className={`status-value ${bridgeOn ? 'active' : ''}`}
            style={{ opacity: bridgeOn ? 1 : 0.4 }}
          >{ahkRunning ? (bridgeOn ? 'clip' : 'off') : '—'}</span>
        </span>
        <Sep />
        {/* Gear menu */}
        <span ref={gearRef} style={{ position: 'relative' }}>
          <span
            className="status-item"
            onClick={() => setGearOpen(!gearOpen)}
            title="Settings"
            style={{ cursor: 'pointer', userSelect: 'none' }}
          >
            <span className="status-label">⚙️</span>
          </span>
          {gearOpen && (
            <GearMenu
              saveConfirmation={saveConfirmation}
              onSaveConfirmToggle={() => { onSaveConfirmToggle(); }}
              ahkStatus={ahkStatus}
              onBondToggle={handleBondToggle}
              onBridgeToggle={handleBridgeToggle}
            />
          )}
        </span>
      </div>
    </header>
  );
}

function GearMenu({ saveConfirmation, onSaveConfirmToggle, ahkStatus, onBondToggle, onBridgeToggle }) {
  const running = ahkStatus?.running ?? false;
  const bondOn = ahkStatus?.bond_active ?? false;
  const bridgeOn = ahkStatus?.bridge_active ?? false;
  const turn = ahkStatus?.turn ?? 0;
  const limit = ahkStatus?.limit ?? 10;
  const cmds = ahkStatus?.commands_typed ?? 0;

  return (
    <div style={{
      position: 'absolute',
      top: '100%',
      right: 0,
      marginTop: 6,
      width: 220,
      background: 'var(--bg-elevated)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-sm)',
      boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
      zIndex: 1000,
      padding: '8px 0',
      fontFamily: 'var(--font-mono)',
      fontSize: '0.75rem',
    }}>
      {/* Section: Save */}
      <GearLabel text="Save" />
      <GearToggle
        label="💾 Confirm writes"
        active={saveConfirmation}
        onClick={onSaveConfirmToggle}
      />

      <GearDivider />

      {/* Section: Counter + Bridge */}
      <GearLabel text="Counter / Bridge" />
      {!running ? (
        <div style={{ padding: '4px 14px', color: '#f85149', fontSize: '0.7rem' }}>
          ⚠ AHK not detected
        </div>
      ) : (
        <>
          <GearToggle
            label="🔥 BOND counter"
            active={bondOn}
            onClick={onBondToggle}
          />
          <GearToggle
            label="📋 Clipboard bridge"
            active={bridgeOn}
            onClick={onBridgeToggle}
          />
          <div style={{
            padding: '4px 14px',
            color: 'var(--text-muted)',
            fontSize: '0.65rem',
            display: 'flex',
            justifyContent: 'space-between',
          }}>
            <span>Turn: {turn}/{limit}</span>
            <span>Cmds: {cmds}</span>
          </div>
        </>
      )}

      <GearDivider />

      {/* Section: Info */}
      <GearLabel text="Shortcuts" />
      <div style={{ padding: '2px 14px', color: 'var(--text-muted)', fontSize: '0.65rem', lineHeight: 1.6 }}>
        <div>Ctrl+Shift+B — Toggle BOND</div>
        <div>Ctrl+Shift+R — Reset counter</div>
        <div>Ctrl+Shift+P — Pin panel</div>
      </div>
    </div>
  );
}

function GearLabel({ text }) {
  return (
    <div style={{
      padding: '2px 14px 3px',
      fontSize: '0.6rem',
      color: 'var(--text-muted)',
      textTransform: 'uppercase',
      letterSpacing: '1.5px',
      fontWeight: 600,
    }}>{text}</div>
  );
}

function GearToggle({ label, active, onClick }) {
  return (
    <div
      onClick={onClick}
      style={{
        padding: '5px 14px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        cursor: 'pointer',
        color: 'var(--text-secondary)',
      }}
      onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      <span>{label}</span>
      <span style={{
        width: 28, height: 14, borderRadius: 7,
        background: active ? 'rgba(63,185,80,0.4)' : 'rgba(139,148,158,0.3)',
        position: 'relative',
        transition: 'background 0.15s',
        display: 'inline-block',
      }}>
        <span style={{
          width: 10, height: 10, borderRadius: '50%',
          background: active ? '#3fb950' : '#8b949e',
          position: 'absolute',
          top: 2,
          left: active ? 16 : 2,
          transition: 'left 0.15s, background 0.15s',
        }} />
      </span>
    </div>
  );
}

function GearDivider() {
  return <div style={{ margin: '4px 0', borderTop: '1px solid var(--border)' }} />;
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
