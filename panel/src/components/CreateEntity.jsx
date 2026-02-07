// BOND Control Panel — CreateEntity Modal
// B69: Four-Class Architecture — create new entity folders

import { useState } from 'react';

const CLASS_INFO = {
  doctrine: { icon: '📜', desc: 'Static truth. IS statements. Immutable method.' },
  project:  { icon: '⚒️', desc: 'Active work. Has CORE boundary + growth.' },
  perspective: { icon: '🔭', desc: 'Evolving lens. Seeds that grow through resonance.' },
  library:  { icon: '📚', desc: 'Read-only reference. Knowledge store.' },
};

export default function CreateEntity({ entityClass, onCreated, onCancel }) {
  const [name, setName] = useState('');
  const [error, setError] = useState(null);
  const [creating, setCreating] = useState(false);

  const info = CLASS_INFO[entityClass] || CLASS_INFO.library;

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;

    setCreating(true);
    setError(null);

    try {
      const res = await fetch('/api/doctrine', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: trimmed, class: entityClass }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Creation failed');
        setCreating(false);
        return;
      }
      onCreated(data);
    } catch (err) {
      setError(err.message);
      setCreating(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <span>{info.icon} New {entityClass.charAt(0).toUpperCase() + entityClass.slice(1)}</span>
          <button className="modal-close" onClick={onCancel}>✕</button>
        </div>

        <p className="modal-desc">{info.desc}</p>

        <form onSubmit={handleSubmit}>
          <label className="modal-label">
            Entity Name
            <input
              type="text"
              className="modal-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={entityClass === 'perspective' ? 'P12-Name' : 'EntityName'}
              autoFocus
              disabled={creating}
            />
          </label>

          <p className="modal-hint">
            Letters, numbers, hyphens, underscores only. Becomes the folder name.
          </p>

          {error && <p className="modal-error">⚠️ {error}</p>}

          <div className="modal-actions">
            <button type="button" className="btn-cancel" onClick={onCancel} disabled={creating}>
              Cancel
            </button>
            <button type="submit" className="btn-confirm" disabled={!name.trim() || creating}>
              {creating ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
