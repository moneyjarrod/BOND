// EntityCards.jsx — Four-Class Entity Architecture (B69)
// S130: Tools are universal. Class shapes behavior, not tool availability.
// All entity classes have access to all BOND tools.

import { useState, useMemo, useCallback, useContext, useEffect, useRef } from 'react';
import { WebSocketContext } from '../context/WebSocketContext';

// Tool definitions — universal per BOND_ENTITIES doctrine (S130)
const TOOLS = [
  { id: 'filesystem', icon: '📁', label: 'Files' },
  { id: 'iss',        icon: '📐', label: 'ISS' },
  { id: 'qais',       icon: '🔮', label: 'QAIS' },
  { id: 'heatmap',    icon: '🔥', label: 'Heat' },
  { id: 'crystal',    icon: '💎', label: 'Crystal' },
];

// Class display info
const CLASS_META = {
  doctrine:    { icon: '📜', label: 'DC', badge: 'badge-dc', name: 'Doctrine' },
  project:     { icon: '⚒️', label: 'PC', badge: 'badge-pc', name: 'Project' },
  perspective: { icon: '🔭', label: 'PP', badge: 'badge-pp', name: 'Perspective' },
  library:     { icon: '📚', label: 'LB', badge: 'badge-lb', name: 'Library' },
};


export default function EntityCards({
  entities,
  filter,          // 'doctrine', 'project', 'perspective', or 'library'
  linkedEntities,
  activeEntity,
  onView,
  onEnter,
  onRename,
  onExit,
  onCreate,
  onLink,
}) {
  const linkedNames = new Set((linkedEntities || []).map(e => typeof e === 'string' ? e : e.name));
  const cards = useMemo(() => {
    return entities
      .filter(e => e.type === filter)
      .map(e => ({ ...e, isBase: false, label: null }));
  }, [entities, filter]);

  const meta = CLASS_META[filter] || CLASS_META.library;

  if (cards.length === 0) {
    return (
      <div className="placeholder">
        <div className="placeholder-icon">{meta.icon}</div>
        <div className="placeholder-text">No {meta.name.toLowerCase()} entities found</div>
        <div className="placeholder-sub">Add a folder with entity.json to doctrine/ directory</div>
        {onCreate && (
          <button
            className="btn-create-entity"
            style={{ marginTop: 16 }}
            onClick={onCreate}
          >
            + New {meta.name}
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="card-grid">
      {cards.map(entity => (
        <EntityCard
          key={entity.name}
          entity={entity}
          isLinked={linkedNames.has(entity.name)}
          isActive={activeEntity?.name === entity.name}
          onView={onView}
          onEnter={onEnter}
          onRename={onRename}
          onExit={onExit}
          onLink={onLink}
        />
      ))}
    </div>
  );
}

function EntityCard({ entity, isLinked, isActive, onView, onEnter, onExit, onRename, onLink }) {
  const isEmpty = entity.files.length === 0 && (entity.seed_count || 0) === 0;
  const meta = CLASS_META[entity.type] || CLASS_META.library;
  const [editing, setEditing] = useState(false);
  const [editValue, setEditValue] = useState('');
  const [saved, setSaved] = useState(false);
  const [seeding, setSeeding] = useState(entity.seeding || false);
  const [seedingLoading, setSeedingLoading] = useState(false);
  const [showLinkPicker, setShowLinkPicker] = useState(false);
  const [linkable, setLinkable] = useState([]);
  const pickerRef = useRef(null);
  const [showConsultPicker, setShowConsultPicker] = useState(false);
  const [consultable, setConsultable] = useState([]);
  const consultPickerRef = useRef(null);

  const { lastEvent } = useContext(WebSocketContext);

  // Fetch linkable entities when active and picker opens
  useEffect(() => {
    if (!isActive || !showLinkPicker) return;
    fetch('/api/state/linkable').then(r => r.json()).then(data => {
      setLinkable((data.linkable || []).map(l => ({ name: l.entity, type: l.class, display_name: l.display_name })));
    }).catch(() => setLinkable([]));
  }, [isActive, showLinkPicker]);

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

  // Fetch consultable entities when consult picker opens
  useEffect(() => {
    if (!isActive || !showConsultPicker) return;
    fetch('/api/state/consultable').then(r => r.json()).then(data => {
      setConsultable((data.consultable || []).map(c => ({ name: c.entity, type: c.class, display_name: c.display_name })));
    }).catch(() => setConsultable([]));
  }, [isActive, showConsultPicker]);

  // Close consult picker on outside click
  useEffect(() => {
    if (!showConsultPicker) return;
    const handler = (e) => {
      if (consultPickerRef.current && !consultPickerRef.current.contains(e.target)) {
        setShowConsultPicker(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showConsultPicker]);

  const handleLinkSelect = useCallback((ent) => {
    setShowLinkPicker(false);
    if (onLink) onLink(ent);
  }, [onLink]);

  const handleConsultSelect = useCallback(async (ent) => {
    setShowConsultPicker(false);
    try {
      await navigator.clipboard.writeText(`BOND:{Consult ${ent.name}}`);
    } catch {}
  }, []);

  // Sync seeding state from WebSocket events
  useEffect(() => {
    if (!lastEvent) return;
    if (lastEvent.type === 'seed_toggled' && lastEvent.entity === entity.name) {
      setSeeding(lastEvent.detail.seeding);
    }
  }, [lastEvent, entity.name]);

  const handleEditStart = useCallback(() => {
    setEditValue(entity.display_name || entity.name);
    setEditing(true);
  }, [entity.display_name, entity.name]);

  const handleEditSave = useCallback(() => {
    const trimmed = editValue.trim();
    if (trimmed && trimmed !== entity.name && onRename) {
      onRename(entity.name, trimmed);
      setSaved(true);
      setTimeout(() => setSaved(false), 1200);
    } else if ((!trimmed || trimmed === entity.name) && onRename) {
      onRename(entity.name, null);
    }
    setEditing(false);
  }, [editValue, entity.name, onRename]);

  const handleEditKey = useCallback((e) => {
    if (e.key === 'Enter') handleEditSave();
    if (e.key === 'Escape') setEditing(false);
  }, [handleEditSave]);

  const handleSeedToggle = useCallback(async () => {
    if (entity.type !== 'perspective' || seedingLoading) return;
    setSeedingLoading(true);
    try {
      const res = await fetch(`/api/doctrine/${entity.name}/seeding`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ seeding: !seeding }),
      });
      if (res.ok) setSeeding(!seeding);
    } catch (err) {
      console.error('Seed toggle failed:', err);
    } finally {
      setSeedingLoading(false);
    }
  }, [entity.name, entity.type, seeding, seedingLoading]);

  const displayName = entity.display_name || entity.name;
  const showFolder = entity.display_name && entity.display_name !== entity.name;

  return (
    <div className={`card ${isActive ? 'card-active' : ''}`} style={isActive ? activeStyle : {}}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '1.1rem' }}>{meta.icon}</span>
          {editing ? (
            <input
              autoFocus
              value={editValue}
              onChange={e => setEditValue(e.target.value)}
              onKeyDown={handleEditKey}
              onBlur={handleEditSave}
              style={{
                fontWeight: 600, fontSize: '0.95rem',
                background: 'var(--bg-elevated)', color: 'var(--text-primary)',
                border: '1px solid var(--accent-amber)', borderRadius: 'var(--radius-sm)',
                padding: '2px 6px', fontFamily: 'var(--font-mono)',
                outline: 'none', width: 160,
              }}
            />
          ) : (
            <>
              <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>{displayName}</span>
              {showFolder && (
                <span className="text-muted" style={{ fontSize: '0.7rem' }}>({entity.name})</span>
              )}
              {!isEmpty && (
                <button
                  onClick={handleEditStart}
                  title="Rename"
                  style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    fontSize: '0.75rem', color: saved ? 'var(--accent-amber)' : 'var(--text-muted)', padding: '0 2px',
                    opacity: saved ? 1 : 0.6, transition: 'all 0.15s',
                  }}
                  onMouseEnter={e => { if (!saved) e.target.style.opacity = 1; }}
                  onMouseLeave={e => { if (!saved) e.target.style.opacity = 0.6; }}
                >{saved ? '✅' : '✏️'}</button>
              )}
            </>
          )}
          {entity.label && (
            <span className="text-muted" style={{ fontSize: '0.75rem', fontStyle: 'italic' }}>
              — {entity.label}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {isLinked && <span className="badge badge-linked" style={{ background: 'rgba(96,165,250,0.15)', color: '#60a5fa', border: '1px solid rgba(96,165,250,0.3)' }}>LINKED</span>}
          {(() => { const sameClass = (entity.linked_by || []).filter(l => l.class === entity.type); return sameClass.length > 0 ? (
            <span className="badge" title={`Linked by: ${sameClass.map(l => l.display_name || l.entity).join(', ')}`} style={{ background: 'rgba(168,130,255,0.12)', color: '#a882ff', border: '1px solid rgba(168,130,255,0.3)', fontSize: '0.6rem' }}>🔗 {sameClass.length}</span>
          ) : null; })()}
          {isActive && <span className="badge badge-active">ACTIVE</span>}
          {entity.core && <span className="badge badge-core">🔒 CORE</span>}
          <span className={`badge ${meta.badge}`}>{meta.label}</span>
        </div>
      </div>

      {/* Counts */}
      {isEmpty ? (
        <div className="text-muted" style={{ fontSize: '0.8rem', marginBottom: 8, fontFamily: 'var(--font-mono)' }}>
          Empty — no files yet
        </div>
      ) : (
        <div className="text-secondary" style={{ fontSize: '0.8rem', marginBottom: 8, fontFamily: 'var(--font-mono)' }}>
          {entity.type === 'doctrine' && (
            <>🔒 {entity.doctrine_count} doctrine</>
          )}
          {entity.type === 'project' && (
            <>🔒 {entity.doctrine_count} core · 📄 {entity.files.length} files</>
          )}
          {entity.type === 'perspective' && (
            <span style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <span>
                {entity.root_count > 0 ? `🌳 ${entity.root_count} roots · ` : ''}
                🌿 {entity.seed_count} seeds ·
                {' '}🌱 {entity.growth_count} vine
                {entity.tracker && entity.tracker.max_exposure > 0 && (
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                    {' · '}{entity.tracker.max_exposure}/{entity.tracker.prune_window} exp
                    {entity.tracker.at_risk > 0 && (
                      <span style={{ color: '#e94560' }}> · ✂️ {entity.tracker.at_risk}</span>
                    )}
                  </span>
                )}
                {entity.pruned_count > 0 && (
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                    {' · '}🪵 {entity.pruned_count} pruned
                  </span>
                )}
              </span>
              <button
                onClick={(e) => { e.stopPropagation(); handleSeedToggle(); }}
                disabled={seedingLoading || isEmpty}
                title={seeding ? 'Seed collection ON — click to pause' : 'Seed collection OFF — click to arm'}
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 3,
                  padding: '1px 7px', fontSize: '0.65rem', fontFamily: 'var(--font-mono)',
                  background: seeding ? 'rgba(76,175,80,0.15)' : 'transparent',
                  color: seeding ? '#4caf50' : 'var(--text-muted)',
                  border: `1px solid ${seeding ? 'rgba(76,175,80,0.4)' : 'var(--border)'}`,
                  borderRadius: 'var(--radius-sm)', cursor: isEmpty ? 'not-allowed' : 'pointer',
                  transition: 'all 0.15s ease', opacity: seedingLoading ? 0.5 : 1,
                }}
              >
                <span style={{ fontSize: '0.6rem' }}>{seeding ? '🟢' : '⏸️'}</span>
                <span>{seeding ? 'SEED ON' : 'SEED OFF'}</span>
              </button>
            </span>
          )}
          {entity.type === 'library' && (
            <>📄 {entity.files.length} files</>
          )}
        </div>
      )}

      {/* Tool indicators — universal per BOND_ENTITIES doctrine (S130) */}
      <div style={{
        display: 'flex',
        gap: 4,
        marginBottom: 10,
        padding: '6px 0',
        borderTop: '1px solid var(--border)',
        borderBottom: '1px solid var(--border)',
      }}>
        {TOOLS.map(tool => (
          <ToolBadge
            key={tool.id}
            icon={tool.icon}
            label={tool.label}
            allowed={true}
            enabled={true}
          />
        ))}
      </div>

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', position: 'relative' }}>
        <ActionBtn label="View" disabled={isEmpty} onClick={() => onView(entity)} />
        {isActive ? (
          <ActionBtn label="Exit" disabled={false} primary={true} onClick={() => onExit && onExit()} />
        ) : (
          <ActionBtn label="Enter" disabled={false} primary={true} onClick={() => onEnter(entity)} />
        )}
        {isActive && entity.type === 'project' && (
          <div ref={consultPickerRef} style={{ position: 'relative' }}>
            <ActionBtn label="🔭 Consult" disabled={false} onClick={() => setShowConsultPicker(!showConsultPicker)} />
            {showConsultPicker && (
              <div style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                marginTop: 6,
                background: '#1e2030',
                border: '1px solid rgba(168,130,255,0.4)',
                borderRadius: 'var(--radius-md)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
                minWidth: 220,
                maxHeight: 260,
                overflowY: 'auto',
                zIndex: 1000,
                padding: '6px 0',
              }}>
                {consultable.length === 0 ? (
                  <div style={{
                    padding: '12px 16px',
                    fontSize: '0.75rem',
                    color: 'var(--text-muted)',
                    fontFamily: 'var(--font-mono)',
                  }}>
                    No consultable entities
                  </div>
                ) : (
                  consultable.map(ent => {
                    const cm = CLASS_META[ent.type] || CLASS_META.library;
                    return (
                      <button
                        key={ent.name}
                        onClick={() => handleConsultSelect(ent)}
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
                        onMouseEnter={e => { e.currentTarget.style.background = 'rgba(168,130,255,0.12)'; }}
                        onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}
                      >
                        <span style={{ flexShrink: 0 }}>{cm.icon}</span>
                        <span style={{ flex: 1 }}>{ent.display_name || ent.name}</span>
                        <span style={{
                          fontSize: '0.6rem',
                          color: 'var(--text-muted)',
                          textTransform: 'uppercase',
                          flexShrink: 0,
                        }}>
                          {ent.type?.slice(0, 3)}
                        </span>
                      </button>
                    );
                  })
                )}
              </div>
            )}
          </div>
        )}
        {isActive && onLink && (
          <div ref={pickerRef} style={{ position: 'relative' }}>
            <ActionBtn label="🔗 Link" disabled={false} onClick={() => setShowLinkPicker(!showLinkPicker)} />
            {showLinkPicker && (
              <div style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                marginTop: 6,
                background: '#1e2030',
                border: '1px solid rgba(96,165,250,0.4)',
                borderRadius: 'var(--radius-md)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
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
                    No compatible entities to link
                  </div>
                ) : (
                  linkable.map(ent => {
                    const cm = CLASS_META[ent.type] || CLASS_META.library;
                    return (
                      <button
                        key={ent.name}
                        onClick={() => handleLinkSelect(ent)}
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
                        onMouseEnter={e => { e.currentTarget.style.background = 'rgba(96,165,250,0.12)'; }}
                        onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}
                      >
                        <span style={{ flexShrink: 0 }}>{cm.icon}</span>
                        <span style={{ flex: 1 }}>{ent.display_name || ent.name}</span>
                        <span style={{
                          fontSize: '0.6rem',
                          color: 'var(--text-muted)',
                          textTransform: 'uppercase',
                          flexShrink: 0,
                        }}>
                          {ent.type?.slice(0, 3)}
                        </span>
                      </button>
                    );
                  })
                )}
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}

function ToolBadge({ icon, label, allowed, enabled, onClick }) {
  return (
    <button
      onClick={onClick}
      disabled={!allowed}
      title={!allowed ? `${label}: not available for this class` : enabled ? `${label}: on` : `${label}: off`}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 3,
        padding: '2px 6px',
        fontSize: '0.7rem',
        fontFamily: 'var(--font-mono)',
        background: enabled ? 'rgba(209,154,102,0.15)' : 'transparent',
        color: !allowed ? 'var(--text-muted)' : enabled ? 'var(--accent-amber)' : 'var(--text-secondary)',
        border: `1px solid ${!allowed ? 'transparent' : enabled ? 'rgba(209,154,102,0.4)' : 'var(--border)'}`,
        borderRadius: 'var(--radius-sm)',
        cursor: allowed ? 'pointer' : 'not-allowed',
        opacity: allowed ? 1 : 0.35,
        transition: 'all 0.15s ease',
      }}
    >
      <span style={{ fontSize: '0.65rem' }}>{icon}</span>
      <span>{label}</span>
    </button>
  );
}

function ActionBtn({ label, disabled, primary, onClick }) {
  return (
    <button
      disabled={disabled}
      onClick={onClick}
      style={{
        padding: '5px 14px',
        fontSize: '0.78rem',
        fontFamily: 'var(--font-mono)',
        background: disabled ? 'transparent' : primary ? 'var(--accent-dim)' : 'var(--bg-elevated)',
        color: disabled ? 'var(--text-muted)' : primary ? 'var(--accent)' : 'var(--text-secondary)',
        border: `1px solid ${disabled ? 'var(--border)' : primary ? 'rgba(233,69,96,0.4)' : 'var(--border)'}`,
        borderRadius: 'var(--radius-sm)',
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.15s ease',
      }}
    >
      {label}
    </button>
  );
}

const activeStyle = {
  borderColor: 'var(--accent)',
  boxShadow: '0 0 0 1px var(--accent), 0 4px 12px rgba(233, 69, 96, 0.2)',
};
