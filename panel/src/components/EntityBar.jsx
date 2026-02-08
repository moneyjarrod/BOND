// EntityBar.jsx — Active entity status strip with Exit button
// Shows when an entity is entered. Sits between Header and tab-bar.
// S85: Added linked entity indicator + Unlink button.

const CLASS_META = {
  doctrine:    { icon: '📜', label: 'Doctrine',    color: 'var(--accent-amber)' },
  project:     { icon: '⚒️', label: 'Project',     color: 'var(--accent-teal)' },
  perspective: { icon: '🔭', label: 'Perspective', color: 'var(--accent)' },
  library:     { icon: '📚', label: 'Library',     color: 'var(--text-secondary)' },
};

export default function EntityBar({ activeEntity, linkedEntity, onExit, onUnlink }) {
  if (!activeEntity) return null;

  const meta = CLASS_META[activeEntity.type] || CLASS_META.doctrine;
  const label = activeEntity.display_name || activeEntity.name;

  const linkedMeta = linkedEntity ? (CLASS_META[linkedEntity.type] || CLASS_META.library) : null;
  const linkedLabel = linkedEntity ? (linkedEntity.display_name || linkedEntity.name) : null;

  return (
    <div style={{ borderBottom: '1px solid var(--border)' }}>
      {/* Primary row */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '6px 16px',
        background: 'rgba(209,154,102,0.08)',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.8rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 4,
            padding: '2px 8px',
            background: 'rgba(209,154,102,0.15)',
            border: '1px solid rgba(209,154,102,0.3)',
            borderRadius: 'var(--radius-sm)',
            color: meta.color,
            fontWeight: 600,
          }}>
            {meta.icon} {label}
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
            {meta.label} · entered
          </span>
        </div>
        <button
          onClick={onExit}
          style={{
            padding: '3px 12px',
            fontSize: '0.75rem',
            fontFamily: 'var(--font-mono)',
            background: 'transparent',
            color: 'var(--accent)',
            border: '1px solid rgba(233,69,96,0.4)',
            borderRadius: 'var(--radius-sm)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={e => { e.target.style.background = 'rgba(233,69,96,0.1)'; }}
          onMouseLeave={e => { e.target.style.background = 'transparent'; }}
        >
          Exit
        </button>
      </div>

      {/* Linked row — only shows when linked */}
      {linkedEntity && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '4px 16px',
          background: 'rgba(86,212,221,0.04)',
          borderTop: '1px solid rgba(86,212,221,0.1)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{
              fontSize: '0.7rem',
              color: 'var(--text-muted)',
            }}>
              🔗
            </span>
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
              padding: '1px 7px',
              background: 'rgba(86,212,221,0.08)',
              border: '1px solid rgba(86,212,221,0.25)',
              borderRadius: 'var(--radius-sm)',
              color: linkedMeta.color,
              fontWeight: 600,
              fontSize: '0.73rem',
            }}>
              {linkedMeta.icon} {linkedLabel}
            </span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.68rem' }}>
              {linkedMeta.label} · linked
            </span>
          </div>
          <button
            onClick={onUnlink}
            style={{
              padding: '2px 10px',
              fontSize: '0.68rem',
              fontFamily: 'var(--font-mono)',
              background: 'transparent',
              color: 'var(--text-muted)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
            onMouseEnter={e => {
              e.target.style.background = 'rgba(233,69,96,0.1)';
              e.target.style.color = 'var(--accent)';
              e.target.style.borderColor = 'rgba(233,69,96,0.4)';
            }}
            onMouseLeave={e => {
              e.target.style.background = 'transparent';
              e.target.style.color = 'var(--text-muted)';
              e.target.style.borderColor = 'var(--border)';
            }}
          >
            Unlink
          </button>
        </div>
      )}
    </div>
  );
}
