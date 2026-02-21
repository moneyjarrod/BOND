// BOND Control Panel — GiftPackImport
// S138: Import pre-built perspectives from Gift Pack

import { useState, useEffect } from 'react';

export default function GiftPackImport({ onImported, onCancel }) {
  const [manifest, setManifest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(null); // id of perspective being imported
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/api/starters')
      .then(r => r.json())
      .then(data => {
        if (data.error) setError(data.error);
        else setManifest(data);
        setLoading(false);
      })
      .catch(err => { setError(err.message); setLoading(false); });
  }, []);

  const handleImport = async (id) => {
    setImporting(id);
    setError(null);
    try {
      const res = await fetch('/api/starters/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Import failed');
        setImporting(null);
        return;
      }
      // Mark as installed in local state
      setManifest(prev => ({
        ...prev,
        perspectives: prev.perspectives.map(p =>
          p.id === id ? { ...p, installed: true } : p
        ),
      }));
      setImporting(null);
      if (onImported) onImported(data);
    } catch (err) {
      setError(err.message);
      setImporting(null);
    }
  };

  if (loading) return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <p>Loading Gift Pack...</p>
      </div>
    </div>
  );

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '520px' }}>
        <div className="modal-header">
          <span>Gift Pack</span>
          <button className="modal-close" onClick={onCancel}>&#x2715;</button>
        </div>

        <p className="modal-desc">{manifest?.description || 'Pre-built starter perspectives'}</p>

        {error && <p className="modal-error">{error}</p>}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', margin: '16px 0' }}>
          {manifest?.perspectives?.map(p => (
            <div key={p.id} style={{
              border: '1px solid var(--border, #333)',
              borderRadius: '8px',
              padding: '12px',
              opacity: p.installed ? 0.6 : 1,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <strong>{p.icon} {p.display_name}</strong>
                  <div style={{ fontSize: '0.85em', opacity: 0.7, marginTop: '2px' }}>{p.tagline}</div>
                  <div style={{ fontSize: '0.8em', opacity: 0.5, marginTop: '4px' }}>{p.root_count} roots</div>
                </div>
                <button
                  className="btn-confirm"
                  disabled={p.installed || importing === p.id}
                  onClick={() => handleImport(p.id)}
                  style={{ minWidth: '80px' }}
                >
                  {p.installed ? 'Installed' : importing === p.id ? 'Importing...' : 'Import'}
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="modal-actions">
          <button className="btn-cancel" onClick={onCancel}>Close</button>
        </div>
      </div>
    </div>
  );
}
