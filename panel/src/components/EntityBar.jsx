// EntityBar.jsx — Active entity status strip with Exit button
// Shows when an entity is entered. Sits between Header and tab-bar.

const CLASS_META = {
  doctrine:    { icon: '📜', label: 'Doctrine',    color: 'var(--accent-amber)' },
  project:     { icon: '⚒️', label: 'Project',     color: 'var(--accent-teal)' },
  perspective: { icon: '🔭', label: 'Perspective', color: 'var(--accent)' },
  library:     { icon: '📚', label: 'Library',     color: 'var(--text-secondary)' },
};

export default function EntityBar({ activeEntity, onExit }) {
  if (!activeEntity) return null;

  const meta = CLASS_META[activeEntity.type] || CLASS_META.doctrine;
  const label = activeEntity.display_name || activeEntity.name;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '6px 16px',
      background: 'rgba(209,154,102,0.08)',
      borderBottom: '1px solid var(--border)',
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
        onMouseEnter={e => {
          e.target.style.background = 'rgba(233,69,96,0.1)';
        }}
        onMouseLeave={e => {
          e.target.style.background = 'transparent';
        }}
      >
        Exit
      </button>
    </div>
  );
}
