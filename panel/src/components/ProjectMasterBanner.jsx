// ProjectMasterBanner.jsx — PROJECT_MASTER distinguished slot
// Sits below BOND_MASTER banner on Doctrine tab. Project lifecycle authority.
// S92: Created — peer to BOND_MASTER, governs project-class entities.
// S92: Bindings view — shows entity-to-link dependency map when active.

import { useState, useCallback, useRef, useEffect } from 'react';

const PM_ENTITY = 'PROJECT_MASTER';

const CLASS_META = {
  doctrine:    { icon: '📜' },
  project:     { icon: '⚒️' },
  perspective: { icon: '🔭' },
  library:     { icon: '📚' },
  unknown:     { icon: '❓' },
};

export default function ProjectMasterBanner({ entities, allEntities, activeEntity, linkedEntities = [], onEnter, onView, onExit, onLink }) {
  const master = entities.find(e => e.name === PM_ENTITY);
  const [showLinkPicker, setShowLinkPicker] = useState(false);
  const [bindings, setBindings] = useState(null);
  const pickerRef = useRef(null);
  const isActive = activeEntity?.name === PM_ENTITY;

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

  // Fetch bindings when PM becomes active
  useEffect(() => {
    if (!isActive) { setBindings(null); return; }
    fetch('/api/bindings')
      .then(r => r.json())
      .then(data => setBindings(data.bindings || {}))
      .catch(() => setBindings(null));
  }, [isActive]);

  if (!master) return null;

  const displayName = master.display_name || 'Project Master';
  const fileCount = master.files?.length || 0;

  // Linkable entities: everything except PM, BOND_MASTER, and already-linked
  const linkedNames = new Set(linkedEntities.map(l => l.name));
  const linkable = (allEntities || entities).filter(e =>
    e.name !== PM_ENTITY && e.name !== 'BOND_MASTER' && !linkedNames.has(e.name)
  );

  const handleLinkSelect = useCallback((entity) => {
    setShowLinkPicker(false);
    onLink(entity);
  }, [onLink]);

  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(180,140,60,0.06) 0%, rgba(180,140,60,0.02) 100%)',
      border: `1px solid ${isActive ? 'rgba(180,140,60,0.5)' : 'rgba(180,140,60,0.2)'}`,
      borderRadius: 'var(--radius-md)',
      padding: '12px 16px',
      marginBottom: 16,
      transition: 'all 0.2s ease',
      boxShadow: isActive
        ? '0 0 0 1px rgba(180,140,60,0.3), 0 3px 12px rgba(180,140,60,0.08)'
        : 'none',
    }}>
      {/* Top row: icon + title + badges */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 8,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '1.2rem' }}>⚒️</span>
          <div>
            <div style={{
              fontSize: '0.95rem',
              fontWeight: 700,
              color: '#b48c3c',
              letterSpacing: '0.5px',
            }}>
              {displayName}
            </div>
            <div style={{
              fontSize: '0.65rem',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-muted)',
              marginTop: 1,
            }}>
              Project Authority · {fileCount} doctrine files
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
              fontSize: '0.6rem',
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
              fontSize: '0.6rem',
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
            background: 'rgba(180,140,60,0.12)',
            border: '1px solid rgba(180,140,60,0.25)',
            borderRadius: 'var(--radius-sm)',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.6rem',
            fontWeight: 600,
            color: '#b48c3c',
            letterSpacing: '0.5px',
            textTransform: 'uppercase',
          }}>
            DC
          </span>
        </div>
      </div>

      {/* Description */}
      <div style={{
        fontSize: '0.73rem',
        color: 'var(--text-secondary)',
        marginBottom: 10,
        lineHeight: 1.5,
      }}>
        Doctrine defines the pattern. CORE defines the project. Enter to manage project lifecycle and linking.
      </div>

      {/* Divider */}
      <div style={{
        borderTop: '1px solid rgba(180,140,60,0.12)',
        marginBottom: 10,
      }} />

      {/* Action row */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', position: 'relative' }}>
        {isActive ? (
          <PMBtn label="Exit" onClick={onExit} variant="exit" />
        ) : (
          <PMBtn label="Enter" onClick={() => onEnter(master)} variant="primary" />
        )}
        <PMBtn label="View" onClick={() => onView(master)} variant="secondary" />

        {/* Link button — only when PM is active and linkable entities exist */}
        {isActive && linkable.length > 0 && (
          <div ref={pickerRef} style={{ position: 'relative' }}>
            <PMBtn
              label="🔗 Link"
              onClick={() => setShowLinkPicker(!showLinkPicker)}
              variant="link"
            />
            {showLinkPicker && (
              <div style={{
                position: 'absolute',
                bottom: '100%',
                left: 0,
                marginBottom: 6,
                background: '#1e2030',
                border: '1px solid rgba(180,140,60,0.4)',
                borderRadius: 'var(--radius-md)',
                boxShadow: '0 -8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(180,140,60,0.15)',
                minWidth: 220,
                maxHeight: 260,
                overflowY: 'auto',
                zIndex: 1000,
                padding: '6px 0',
              }}>
                {linkable.map(entity => {
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
                        fontSize: '0.75rem',
                        cursor: 'pointer',
                        textAlign: 'left',
                        transition: 'background 0.1s ease',
                      }}
                      onMouseEnter={e => {
                        e.currentTarget.style.background = 'rgba(180,140,60,0.1)';
                      }}
                      onMouseLeave={e => {
                        e.currentTarget.style.background = 'transparent';
                      }}
                    >
                      <span style={{ flexShrink: 0 }}>{cm.icon}</span>
                      <span style={{ flex: 1 }}>{entity.display_name || entity.name}</span>
                      <span style={{
                        fontSize: '0.55rem',
                        color: 'var(--text-muted)',
                        textTransform: 'uppercase',
                        flexShrink: 0,
                      }}>
                        {entity.type?.slice(0, 3)}
                      </span>
                    </button>
                  );
                })}
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
          <PMToolPill icon="📁" label="Files" enabled />
          <PMToolPill icon="📐" label="ISS" enabled />
          <PMToolPill icon="🔮" label="QAIS" enabled={false} />
          <PMToolPill icon="🔥" label="Heat" enabled={false} />
          <PMToolPill icon="💎" label="Crystal" enabled={false} />
        </div>
      </div>

      {/* Bindings Map — only shown when PM is active */}
      {isActive && bindings && Object.keys(bindings).length > 0 && (
        <>
          <div style={{
            borderTop: '1px solid rgba(180,140,60,0.12)',
            marginTop: 12,
            marginBottom: 10,
          }} />
          <div style={{
            fontSize: '0.7rem',
            fontFamily: 'var(--font-mono)',
            fontWeight: 600,
            color: '#b48c3c',
            marginBottom: 8,
            letterSpacing: '0.5px',
            textTransform: 'uppercase',
          }}>
            Dependency Map
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {Object.entries(bindings).map(([entityName, info]) => (
              <div key={entityName} style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                fontSize: '0.72rem',
                fontFamily: 'var(--font-mono)',
                color: 'var(--text-secondary)',
              }}>
                <span style={{ fontSize: '0.8rem' }}>
                  {(CLASS_META[info.class] || CLASS_META.unknown).icon}
                </span>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)', minWidth: 100 }}>
                  {info.display_name || entityName}
                </span>
                <span style={{ color: 'var(--text-muted)', flexShrink: 0 }}>→</span>
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  {info.links.map(link => (
                    <span key={link.entity} style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 3,
                      padding: '1px 6px',
                      background: 'rgba(180,140,60,0.08)',
                      border: '1px solid rgba(180,140,60,0.2)',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.65rem',
                    }}>
                      <span style={{ fontSize: '0.6rem' }}>
                        {(CLASS_META[link.class] || CLASS_META.unknown).icon}
                      </span>
                      {link.display_name || link.entity}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function PMBtn({ label, onClick, variant = 'secondary', disabled = false }) {
  const styles = {
    primary: {
      bg: 'rgba(180,140,60,0.12)',
      border: 'rgba(180,140,60,0.45)',
      color: '#b48c3c',
      hoverBg: 'rgba(180,140,60,0.22)',
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
    link: {
      bg: 'rgba(180,140,60,0.06)',
      border: 'rgba(180,140,60,0.3)',
      color: '#b48c3c',
      hoverBg: 'rgba(180,140,60,0.15)',
    },
  };
  const s = styles[variant] || styles.secondary;

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        padding: '4px 12px',
        fontSize: '0.75rem',
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

function PMToolPill({ icon, label, enabled }) {
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 3,
      padding: '2px 5px',
      fontSize: '0.6rem',
      fontFamily: 'var(--font-mono)',
      background: enabled ? 'rgba(180,140,60,0.08)' : 'transparent',
      color: enabled ? '#b48c3c' : 'var(--text-muted)',
      border: `1px solid ${enabled ? 'rgba(180,140,60,0.25)' : 'transparent'}`,
      borderRadius: 'var(--radius-sm)',
      opacity: enabled ? 1 : 0.35,
    }}>
      <span style={{ fontSize: '0.55rem' }}>{icon}</span>
      {label}
    </span>
  );
}
