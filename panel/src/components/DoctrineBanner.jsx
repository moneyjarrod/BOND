// DoctrineBanner.jsx — BOND_MASTER distinguished slot
// Sits above entity grid on Doctrine tab. Constitutional authority.
// S85: Added Link capability — BOND_MASTER exclusive.

import { useState, useCallback, useRef, useEffect } from 'react';

const MASTER_ENTITY = 'BOND_MASTER';

const CLASS_META = {
  doctrine:    { icon: '📜' },
  project:     { icon: '⚒️' },
  perspective: { icon: '🔭' },
  library:     { icon: '📚' },
};

export default function DoctrineBanner({ entities, allEntities, activeEntity, linkedEntities = [], onEnter, onView, onExit, onLink }) {
  const master = entities.find(e => e.name === MASTER_ENTITY);
  const [auditSent, setAuditSent] = useState(false);
  const [showLinkPicker, setShowLinkPicker] = useState(false);
  const pickerRef = useRef(null);
  const isActive = activeEntity?.name === MASTER_ENTITY;

  // Close picker on outside click
  useEffect(() => {
    if (!showLinkPicker) return;
    const handler = (e) => {
      if (pickerRef.current && !pickerRef.current.contains(e.target)) {
        setShowLinkPicker(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showLinkPicker]);

  if (!master) return null;

  const displayName = master.display_name || 'BOND Master';
  const fileCount = master.files?.length || 0;

  // Linkable entities: everything except BOND_MASTER and already-linked
  const linkedNames = new Set(linkedEntities.map(l => l.name));
  const linkable = (allEntities || entities).filter(e => e.name !== MASTER_ENTITY && !linkedNames.has(e.name));

  const handleAudit = useCallback(async () => {
    if (!isActive) {
      onEnter(master);
    }
    try {
      await navigator.clipboard.writeText('BOND:Audit the panel against BOND_MASTER doctrine');
      setAuditSent(true);
      setTimeout(() => setAuditSent(false), 2000);
    } catch {}
  }, [isActive, master, onEnter]);

  const handleLinkSelect = useCallback((entity) => {
    setShowLinkPicker(false);
    onLink(entity);
  }, [onLink]);

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
          {isActive && linkedEntities.length > 0 && (
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 3,
              padding: '2px 8px',
              background: 'rgba(86,212,221,0.12)',
              border: '1px solid rgba(86,212,221,0.3)',
              borderRadius: 'var(--radius-sm)',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.65rem',
              fontWeight: 600,
              color: 'var(--teal)',
              letterSpacing: '0.5px',
              textTransform: 'uppercase',
            }}>
              🔗 {linkedEntities.length}
            </span>
          )}
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
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', position: 'relative' }}>
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

        {/* Link button — only when BOND_MASTER is active and entities available */}
        {isActive && linkable.length > 0 && (
          <div ref={pickerRef} style={{ position: 'relative' }}>
            <BannerBtn
              label="🔗 Link"
              onClick={() => setShowLinkPicker(!showLinkPicker)}
              variant="link"
            />
            {showLinkPicker && (
              <div style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                marginTop: 6,
                background: '#1e2030',
                border: '1px solid rgba(210,153,34,0.5)',
                borderRadius: 'var(--radius-md)',
                boxShadow: '0 -8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(210,153,34,0.2)',
                minWidth: 220,
                maxHeight: 260,
                overflowY: 'auto',
                zIndex: 1000,
                padding: '6px 0',
              }}>
                {linkable.length === 0 ? (
                  <div style={{
                    padding: '12px 16px',
                    fontSize: '0.75rem',
                    color: 'var(--text-muted)',
                    fontFamily: 'var(--font-mono)',
                  }}>
                    No entities to link
                  </div>
                ) : (
                  linkable.map(entity => {
                    const cm = CLASS_META[entity.type] || CLASS_META.library;
                    return (
                      <button
                        key={entity.name}
                        onClick={() => handleLinkSelect(entity)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                          width: '100%',
                          padding: '8px 14px',
                          background: 'transparent',
                          border: 'none',
                          color: 'var(--text-primary)',
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.78rem',
                          cursor: 'pointer',
                          textAlign: 'left',
                          transition: 'background 0.1s ease',
                        }}
                        onMouseEnter={e => {
                          e.currentTarget.style.background = 'rgba(210,153,34,0.12)';
                        }}
                        onMouseLeave={e => {
                          e.currentTarget.style.background = 'transparent';
                        }}
                      >
                        <span style={{ flexShrink: 0 }}>{cm.icon}</span>
                        <span style={{ flex: 1 }}>{entity.display_name || entity.name}</span>
                        <span style={{
                          fontSize: '0.6rem',
                          color: 'var(--text-muted)',
                          textTransform: 'uppercase',
                          flexShrink: 0,
                        }}>
                          {entity.type?.slice(0, 3)}
                        </span>
                      </button>
                    );
                  })
                )}
              </div>
            )}
          </div>
        )}

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
    link: {
      bg: 'rgba(210,153,34,0.08)',
      border: 'rgba(210,153,34,0.35)',
      color: '#d29922',
      hoverBg: 'rgba(210,153,34,0.18)',
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
