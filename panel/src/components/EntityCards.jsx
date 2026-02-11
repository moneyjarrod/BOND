// EntityCards.jsx — Four-Class Entity Architecture (B69)
// Doctrine: IS statements, Files + ISS
// Project: Bounded workspace, Files + QAIS + Heatmap + Crystal + ISS, has CORE
// Perspective: Unbounded growth, Files + QAIS + Heatmap + Crystal
// Library: Reference shelf, Files only

import { useState, useMemo, useCallback, useContext, useEffect } from 'react';
import { WebSocketContext } from '../context/WebSocketContext';

// Tool definitions with class availability
const TOOLS = [
  { id: 'filesystem', icon: '📁', label: 'Files',   classes: ['doctrine','project','perspective','library'] },
  { id: 'iss',        icon: '📐', label: 'ISS',     classes: ['doctrine','project'] },
  { id: 'qais',       icon: '🔮', label: 'QAIS',    classes: ['project','perspective'] },
  { id: 'heatmap',    icon: '🔥', label: 'Heat',    classes: ['project','perspective'] },
  { id: 'crystal',    icon: '💎', label: 'Crystal', classes: ['project','perspective'] },
];

// Class display info
const CLASS_META = {
  doctrine:    { icon: '📜', label: 'DC', badge: 'badge-dc', name: 'Doctrine' },
  project:     { icon: '⚒️', label: 'PC', badge: 'badge-pc', name: 'Project' },
  perspective: { icon: '🔭', label: 'PP', badge: 'badge-pp', name: 'Perspective' },
  library:     { icon: '📚', label: 'LB', badge: 'badge-lb', name: 'Library' },
};

// Base perspective slots (P01-P10)
const BASE_PERSPECTIVES = Array.from({ length: 10 }, (_, i) => {
  const num = String(i + 1).padStart(2, '0');
  return {
    name: `P${num}`,
    type: 'perspective',
    files: [],
    tools: { filesystem: true, qais: true, heatmap: true, crystal: true },
    seed_count: 0,
    root_count: 0,
    growth_count: 0,
    doctrine_count: 0,
    core: null,
    isBase: true,
    label: num === '10' ? 'Wildcard' : null,
  };
});

export default function EntityCards({
  entities,
  filter,          // 'doctrine', 'project', 'perspective', or 'library'
  linkedEntities,
  activeEntity,
  onView,
  onEnter,
  onToolToggle,
  onRename,
  onExit,
  onCreate,
}) {
  const linkedNames = new Set((linkedEntities || []).map(e => typeof e === 'string' ? e : e.name));
  const cards = useMemo(() => {
    if (filter === 'perspective') {
      const detected = entities.filter(e => e.type === 'perspective');
      const detectedNames = new Set(detected.map(e => e.name));

      const base = BASE_PERSPECTIVES.map(bp => {
        const match = detected.find(d => d.name.startsWith(bp.name));
        if (match) return { ...match, isBase: true, label: bp.label };
        return bp;
      });

      const userCreated = detected.filter(d => {
        const num = parseInt(d.name.match(/^P(\d+)/)?.[1] || '0', 10);
        return num > 10;
      }).map(e => ({ ...e, isBase: false, label: null }));

      return [...base, ...userCreated];
    }

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
          onToolToggle={onToolToggle}
          onRename={onRename}
          onExit={onExit}
        />
      ))}
    </div>
  );
}

function EntityCard({ entity, isLinked, isActive, onView, onEnter, onExit, onToolToggle, onRename }) {
  const isEmpty = entity.isBase && entity.seed_count === 0 && entity.files.length === 0;
  const meta = CLASS_META[entity.type] || CLASS_META.library;
  const tools = entity.tools || {};
  const [editing, setEditing] = useState(false);
  const [editValue, setEditValue] = useState('');
  const [saved, setSaved] = useState(false);
  const [seeding, setSeeding] = useState(entity.seeding || false);
  const [seedingLoading, setSeedingLoading] = useState(false);
  const { lastEvent } = useContext(WebSocketContext);

  // Sync seeding state from WebSocket events
  useEffect(() => {
    if (!lastEvent) return;
    if (lastEvent.type === 'seed_toggled' && lastEvent.entity === entity.name) {
      setSeeding(lastEvent.detail.seeding);
    }
  }, [lastEvent, entity.name]);

  const handleToggle = useCallback((toolId) => {
    if (onToolToggle) {
      onToolToggle(entity.name, toolId, !tools[toolId]);
    }
  }, [entity.name, tools, onToolToggle]);

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
      const res = await fetch(`http://localhost:3000/api/doctrine/${entity.name}/seeding`, {
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

      {/* Tool toggles (B69) */}
      <div style={{
        display: 'flex',
        gap: 4,
        marginBottom: 10,
        padding: '6px 0',
        borderTop: '1px solid var(--border)',
        borderBottom: '1px solid var(--border)',
      }}>
        {TOOLS.map(tool => {
          const allowed = tool.classes.includes(entity.type);
          const enabled = allowed && tools[tool.id];

          return (
            <ToolBadge
              key={tool.id}
              icon={tool.icon}
              label={tool.label}
              allowed={allowed}
              enabled={enabled}
              onClick={allowed ? () => handleToggle(tool.id) : undefined}
            />
          );
        })}
      </div>

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: 8 }}>
        <ActionBtn label="View" disabled={isEmpty} onClick={() => onView(entity)} />
        {isActive ? (
          <ActionBtn label="Exit" disabled={false} primary={true} onClick={() => onExit && onExit()} />
        ) : (
          <ActionBtn label="Enter" disabled={false} primary={true} onClick={() => onEnter(entity)} />
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
