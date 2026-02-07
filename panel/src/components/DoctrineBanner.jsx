// DoctrineBanner.jsx — BOND_MASTER distinguished slot
// Sits above entity grid on Doctrine tab. Constitutional authority.
// Amber theme, full-width, Enter + Audit actions.

import { useState, useCallback } from 'react';

const MASTER_ENTITY = 'BOND_MASTER';

export default function DoctrineBanner({ entities, activeEntity, onEnter, onView, onExit }) {
  const master = entities.find(e => e.name === MASTER_ENTITY);
  const [auditSent, setAuditSent] = useState(false);
  const isActive = activeEntity?.name === MASTER_ENTITY;

  if (!master) return null;

  const displayName = master.display_name || 'BOND Master';
  const fileCount = master.files?.length || 0;

  const handleAudit = useCallback(async () => {
    // Enter + write audit command to clipboard
    if (!isActive) {
      onEnter(master);
    }
    try {
      await navigator.clipboard.writeText('BOND:Audit the panel against BOND_MASTER doctrine');
      setAuditSent(true);
      setTimeout(() => setAuditSent(false), 2000);
    } catch {}
  }, [isActive, master, onEnter]);

  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(210,153,34,0.08) 0%, rgba(209,154,102,0.04) 100%)',
      border: `1px solid ${isActive ? 'rgba(210,153,34,0.6)' : 'rgba(210,153,34,0.25)'}`,
      borderRadius: 'var(--radius-md)',
      padding: '16px 20px',
      marginBottom: 16,
      transition: 'all 0.2s ease',
      boxShadow: isActive
        ? '0 0 0 1px rgba(210,153,34,0.4), 0 4px 16px rgba(210,153,34,0.1)'
        : 'none',
    }}>
      {/* Top row: icon + title + badges */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 10,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: '1.4rem' }}>🔥🌊</span>
          <div>
            <div style={{
              fontSize: '1.05rem',
              fontWeight: 700,
              color: '#d29922',
              letterSpacing: '0.5px',
            }}>
              {displayName}
            </div>
            <div style={{
              fontSize: '0.7rem',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-muted)',
              marginTop: 1,
            }}>
              Constitutional Authority · {fileCount} doctrine files
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {isActive && (
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '2px 8px',
              background: 'rgba(63,185,80,0.15)',
              border: '1px solid rgba(63,185,80,0.3)',
              borderRadius: 'var(--radius-sm)',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.65rem',
              fontWeight: 600,
              color: 'var(--status-active)',
              letterSpacing: '0.5px',
              textTransform: 'uppercase',
            }}>
              ACTIVE
            </span>
          )}
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            padding: '2px 8px',
            background: 'rgba(210,153,34,0.15)',
            border: '1px solid rgba(210,153,34,0.3)',
            borderRadius: 'var(--radius-sm)',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.65rem',
            fontWeight: 600,
            color: '#d29922',
            letterSpacing: '0.5px',
            textTransform: 'uppercase',
          }}>
            DC
          </span>
        </div>
      </div>

      {/* Description */}
      <div style={{
        fontSize: '0.78rem',
        color: 'var(--text-secondary)',
        marginBottom: 12,
        lineHeight: 1.5,
      }}>
        The protocol IS the product. Enter to consult BOND doctrine, audit the codebase, or learn the system.
      </div>

      {/* Divider */}
      <div style={{
        borderTop: '1px solid rgba(210,153,34,0.15)',
        marginBottom: 12,
      }} />

      {/* Action row */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        {isActive ? (
          <BannerBtn label="Exit" onClick={onExit} variant="exit" />
        ) : (
          <BannerBtn label="Enter" onClick={() => onEnter(master)} variant="primary" />
        )}
        <BannerBtn label="View" onClick={() => onView(master)} variant="secondary" />
        <BannerBtn
          label={auditSent ? '✓ Sent' : '🔍 Audit'}
          onClick={handleAudit}
          variant="audit"
          disabled={auditSent}
        />

        {/* Spacer + tools summary */}
        <div style={{ flex: 1 }} />
        <div style={{
          display: 'flex',
          gap: 4,
          alignItems: 'center',
        }}>
          <ToolPill icon="📁" label="Files" enabled />
          <ToolPill icon="📐" label="ISS" enabled />
          <ToolPill icon="🔮" label="QAIS" enabled={false} />
          <ToolPill icon="🔥" label="Heat" enabled={false} />
          <ToolPill icon="💎" label="Crystal" enabled={false} />
        </div>
      </div>
    </div>
  );
}

function BannerBtn({ label, onClick, variant = 'secondary', disabled = false }) {
  const styles = {
    primary: {
      bg: 'rgba(210,153,34,0.15)',
      border: 'rgba(210,153,34,0.5)',
      color: '#d29922',
      hoverBg: 'rgba(210,153,34,0.25)',
    },
    secondary: {
      bg: 'var(--bg-elevated)',
      border: 'var(--border)',
      color: 'var(--text-secondary)',
      hoverBg: 'var(--bg-hover)',
    },
    exit: {
      bg: 'transparent',
      border: 'rgba(233,69,96,0.4)',
      color: 'var(--accent)',
      hoverBg: 'rgba(233,69,96,0.1)',
    },
    audit: {
      bg: 'rgba(86,212,221,0.08)',
      border: 'rgba(86,212,221,0.3)',
      color: 'var(--teal)',
      hoverBg: 'rgba(86,212,221,0.15)',
    },
  };
  const s = styles[variant] || styles.secondary;

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        padding: '5px 14px',
        fontSize: '0.78rem',
        fontFamily: 'var(--font-mono)',
        fontWeight: variant === 'primary' ? 600 : 400,
        background: s.bg,
        color: disabled ? 'var(--text-muted)' : s.color,
        border: `1px solid ${disabled ? 'var(--border)' : s.border}`,
        borderRadius: 'var(--radius-sm)',
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.15s ease',
      }}
      onMouseEnter={e => { if (!disabled) e.target.style.background = s.hoverBg; }}
      onMouseLeave={e => { if (!disabled) e.target.style.background = s.bg; }}
    >
      {label}
    </button>
  );
}

function ToolPill({ icon, label, enabled }) {
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 3,
      padding: '2px 6px',
      fontSize: '0.65rem',
      fontFamily: 'var(--font-mono)',
      background: enabled ? 'rgba(209,154,102,0.1)' : 'transparent',
      color: enabled ? 'var(--accent-amber)' : 'var(--text-muted)',
      border: `1px solid ${enabled ? 'rgba(209,154,102,0.3)' : 'transparent'}`,
      borderRadius: 'var(--radius-sm)',
      opacity: enabled ? 1 : 0.35,
    }}>
      <span style={{ fontSize: '0.6rem' }}>{icon}</span>
      {label}
    </span>
  );
}
