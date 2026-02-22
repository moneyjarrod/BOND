// DoctrineViewer.jsx — Reads doctrine folders, displays file content
// Left sidebar: file list with 🔒/🌱 icons
// Right panel: file content (pre-formatted for now, markdown renderer in Session 6)

import { useState, useCallback } from 'react';
import { useEntityFiles, useFileContent } from '../hooks/useDoctrine';
// SearchPanel removed S139 (dead code audit) — SPECTRA handles search server-side

// Framework entities — files are read-only
const FRAMEWORK_ENTITIES = ['BOND_MASTER', 'PROJECT_MASTER'];

// Class-appropriate file icons (B69)
const CLASS_FILE_ICON = {
  doctrine: '📜',
  project: '📄',
  perspective: '🌿',
  library: '📄',
};
const GROWTH_ICON = '🌱';
const CORE_ICON = '🔒';

export default function DoctrineViewer({
  viewerTarget,
  activeEntity,
  linkedEntities,
  entityType,
  entityCore,
}) {
  const [selectedFile, setSelectedFile] = useState(null);

  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState(null);
  const [newFileName, setNewFileName] = useState('');
  const [showNewFile, setShowNewFile] = useState(false);
  const linkedNames = new Set((linkedEntities || []).map(e => typeof e === 'string' ? e : e.name));
  const isFramework = FRAMEWORK_ENTITIES.includes(viewerTarget);
  const isRoot = (name) => name?.startsWith('ROOT-');
  const { files, loading: filesLoading, refresh: refreshFiles } = useEntityFiles(viewerTarget);
  const { content, meta, loading: contentLoading, refresh: refreshContent } = useFileContent(viewerTarget, selectedFile);

  const handleEdit = useCallback(() => {
    setEditContent(content || '');
    setEditing(true);
    setSaveMsg(null);
  }, [content]);

  const handleSave = useCallback(async () => {
    setSaving(true);
    setSaveMsg(null);
    try {
      const res = await fetch(`/api/doctrine/${viewerTarget}/${selectedFile}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: editContent }),
      });
      const data = await res.json();
      if (data.saved) {
        setSaveMsg('✅ Saved');
        setEditing(false);
        refreshContent?.();
        refreshFiles?.();
      } else {
        setSaveMsg(`❌ ${data.error || 'Save failed'}`);
      }
    } catch (err) {
      setSaveMsg(`❌ ${err.message}`);
    }
    setSaving(false);
    setTimeout(() => setSaveMsg(null), 3000);
  }, [viewerTarget, selectedFile, editContent, refreshContent, refreshFiles]);

  const handleNewFile = useCallback(async () => {
    if (!newFileName.trim()) return;
    let fname = newFileName.trim();
    if (!fname.endsWith('.md')) fname += '.md';
    setSaving(true);
    setSaveMsg(null);
    try {
      const starter = entityType === 'perspective' && isRoot(fname)
        ? `# ${fname.replace('.md', '')}\n\n<!-- Root identity vector. Not rules — a lens. -->\n`
        : `# ${fname.replace('.md', '')}\n\n`;
      const res = await fetch(`/api/doctrine/${viewerTarget}/${fname}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: starter }),
      });
      const data = await res.json();
      if (data.saved) {
        setShowNewFile(false);
        setNewFileName('');
        refreshFiles?.();
        setSelectedFile(fname);
        setEditContent(starter);
        setEditing(true);
        setSaveMsg(`✅ Created ${fname}`);
      } else {
        setSaveMsg(`❌ ${data.error || 'Create failed'}`);
      }
    } catch (err) {
      setSaveMsg(`❌ ${err.message}`);
    }
    setSaving(false);
    setTimeout(() => setSaveMsg(null), 3000);
  }, [viewerTarget, newFileName, entityType, refreshFiles]);

  if (!viewerTarget) {
    return (
      <div className="placeholder">
        <div className="placeholder-icon">📖</div>
        <div className="placeholder-text">No entity selected</div>
        <div className="placeholder-sub">Click View or Enter on an entity card</div>
      </div>
    );
  }

  const isLinked = linkedNames.has(viewerTarget);
  const isActive = activeEntity?.name === viewerTarget;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Viewer header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '8px 0 12px',
        borderBottom: '1px solid var(--border)',
        marginBottom: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: '1.1rem' }}>📖</span>
          <span style={{ fontWeight: 600 }}>{viewerTarget}</span>
          {isActive && <span className="badge badge-active">ACTIVE</span>}
          {isLinked && !isActive && <span className="badge badge-linked" style={{ background: 'rgba(96,165,250,0.15)', color: '#60a5fa', border: '1px solid rgba(96,165,250,0.3)' }}>LINKED</span>}
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {saveMsg && (
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>{saveMsg}</span>
          )}

        </div>
      </div>



      {/* Main content area */}
      <div style={{ display: 'flex', flex: 1, gap: 12, minHeight: 0 }}>
        {/* File sidebar */}
        <div style={{
          width: 180,
          flexShrink: 0,
          borderRight: '1px solid var(--border)',
          paddingRight: 12,
          overflowY: 'auto',
        }}>
          <div className="text-muted" style={{
            fontSize: '0.65rem',
            fontFamily: 'var(--font-mono)',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            marginBottom: 8,
          }}>
            Files
          </div>

          {filesLoading ? (
            <div className="text-muted" style={{ fontSize: '0.8rem' }}>Loading...</div>
          ) : files.length === 0 ? (
            <div className="text-muted" style={{ fontSize: '0.8rem' }}>No files</div>
          ) : entityType === 'perspective' ? (
            <>
              {/* Roots section */}
              {files.filter(f => isRoot(f.name)).length > 0 && (
                <>
                  <div className="text-muted" style={{
                    fontSize: '0.6rem', fontFamily: 'var(--font-mono)',
                    textTransform: 'uppercase', letterSpacing: '0.5px',
                    marginTop: 4, marginBottom: 4, color: 'var(--accent-amber)',
                  }}>
                    🌳 Roots
                  </div>
                  {files.filter(f => isRoot(f.name)).map(f => (
                    <FileEntry
                      key={f.name} file={f}
                      isSelected={selectedFile === f.name}
                      onClick={() => { setSelectedFile(f.name); setEditing(false); }}
                      entityType={entityType} entityCore={entityCore} isRoot={true}
                    />
                  ))}
                </>
              )}
              {/* Seeds section */}
              {files.filter(f => !isRoot(f.name)).length > 0 && (
                <>
                  <div className="text-muted" style={{
                    fontSize: '0.6rem', fontFamily: 'var(--font-mono)',
                    textTransform: 'uppercase', letterSpacing: '0.5px',
                    marginTop: 10, marginBottom: 4,
                  }}>
                    🌿 Seeds
                  </div>
                  {files.filter(f => !isRoot(f.name)).map(f => (
                    <FileEntry
                      key={f.name} file={f}
                      isSelected={selectedFile === f.name}
                      onClick={() => { setSelectedFile(f.name); setEditing(false); }}
                      entityType={entityType} entityCore={entityCore} isRoot={false}
                    />
                  ))}
                </>
              )}
            </>
          ) : (
            files.map(f => (
              <FileEntry
                key={f.name}
                file={f}
                isSelected={selectedFile === f.name}
                onClick={() => { setSelectedFile(f.name); setEditing(false); }}
                entityType={entityType}
                entityCore={entityCore}
                isRoot={false}
              />
            ))
          )}

          {/* New File button */}
          {!isFramework && (
            <div style={{ marginTop: 12, borderTop: '1px solid var(--border)', paddingTop: 8 }}>
              {showNewFile ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <input
                    type="text"
                    value={newFileName}
                    onChange={e => setNewFileName(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleNewFile()}
                    placeholder={entityType === 'perspective' ? 'ROOT-name or seed-name' : 'filename'}
                    style={{
                      padding: '4px 6px',
                      fontSize: '0.75rem',
                      fontFamily: 'var(--font-mono)',
                      background: 'var(--bg-elevated)',
                      color: 'var(--text-primary)',
                      border: '1px solid var(--border)',
                      borderRadius: 'var(--radius-sm)',
                      outline: 'none',
                    }}
                    autoFocus
                  />
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button
                      onClick={handleNewFile}
                      disabled={saving || !newFileName.trim()}
                      style={{
                        flex: 1,
                        padding: '3px 6px',
                        fontSize: '0.7rem',
                        fontFamily: 'var(--font-mono)',
                        background: 'var(--accent)',
                        color: '#fff',
                        border: 'none',
                        borderRadius: 'var(--radius-sm)',
                        cursor: 'pointer',
                        opacity: saving || !newFileName.trim() ? 0.5 : 1,
                      }}
                    >
                      {saving ? '...' : 'Create'}
                    </button>
                    <button
                      onClick={() => { setShowNewFile(false); setNewFileName(''); }}
                      style={{
                        padding: '3px 6px',
                        fontSize: '0.7rem',
                        fontFamily: 'var(--font-mono)',
                        background: 'var(--bg-elevated)',
                        color: 'var(--text-secondary)',
                        border: '1px solid var(--border)',
                        borderRadius: 'var(--radius-sm)',
                        cursor: 'pointer',
                      }}
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setShowNewFile(true)}
                  style={{
                    width: '100%',
                    padding: '4px 8px',
                    fontSize: '0.75rem',
                    fontFamily: 'var(--font-mono)',
                    background: 'transparent',
                    color: 'var(--text-secondary)',
                    border: '1px dashed var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    cursor: 'pointer',
                  }}
                >
                  + New File
                </button>
              )}
            </div>
          )}
        </div>

        {/* Content panel */}
        <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
          {!selectedFile ? (
            <div className="text-muted" style={{
              fontSize: '0.8rem',
              fontFamily: 'var(--font-mono)',
              padding: 20,
              textAlign: 'center',
            }}>
              Select a file to view
            </div>
          ) : contentLoading ? (
            <div className="text-muted" style={{ fontSize: '0.8rem', padding: 20 }}>Loading...</div>
          ) : (
            <div>
              {/* File header */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border)',
              }}>
                <span>{isRoot(selectedFile) ? '🌳' : meta?.type === 'growth' ? GROWTH_ICON : (CLASS_FILE_ICON[entityType] || '📄')}</span>
                <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{selectedFile}</span>
                <span className="text-muted" style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)' }}>
                  ({isRoot(selectedFile) ? 'root' : meta?.type === 'growth' ? 'growth' : entityType || 'file'})
                </span>
                <div style={{ flex: 1 }} />
                {!isFramework && !editing && (
                  <button
                    onClick={handleEdit}
                    style={{
                      padding: '3px 10px',
                      fontSize: '0.7rem',
                      fontFamily: 'var(--font-mono)',
                      background: 'var(--bg-elevated)',
                      color: 'var(--text-secondary)',
                      border: '1px solid var(--border)',
                      borderRadius: 'var(--radius-sm)',
                      cursor: 'pointer',
                    }}
                  >
                    ✏️ Edit
                  </button>
                )}
              </div>

              {/* File content — edit or read mode */}
              {editing ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <textarea
                    value={editContent}
                    onChange={e => setEditContent(e.target.value)}
                    style={{
                      width: '100%',
                      minHeight: 300,
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.82rem',
                      lineHeight: 1.6,
                      color: 'var(--text-primary)',
                      background: 'var(--bg-elevated)',
                      border: '1px solid var(--accent)',
                      borderRadius: 'var(--radius-sm)',
                      padding: 12,
                      resize: 'vertical',
                      outline: 'none',
                    }}
                    autoFocus
                  />
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button
                      onClick={handleSave}
                      disabled={saving}
                      style={{
                        padding: '5px 16px',
                        fontSize: '0.75rem',
                        fontFamily: 'var(--font-mono)',
                        background: 'var(--accent)',
                        color: '#fff',
                        border: 'none',
                        borderRadius: 'var(--radius-sm)',
                        cursor: 'pointer',
                        opacity: saving ? 0.5 : 1,
                      }}
                    >
                      {saving ? 'Saving...' : '💾 Save'}
                    </button>
                    <button
                      onClick={() => setEditing(false)}
                      style={{
                        padding: '5px 16px',
                        fontSize: '0.75rem',
                        fontFamily: 'var(--font-mono)',
                        background: 'var(--bg-elevated)',
                        color: 'var(--text-secondary)',
                        border: '1px solid var(--border)',
                        borderRadius: 'var(--radius-sm)',
                        cursor: 'pointer',
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <pre style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.82rem',
                  lineHeight: 1.6,
                  color: 'var(--text-primary)',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  padding: 0,
                  margin: 0,
                  background: 'transparent',
                }}>
                  {content}
                </pre>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const ROOT_ICON = '🌳';

function FileEntry({ file, isSelected, onClick, entityType, entityCore, isRoot }) {
  const isCore = entityCore && file.name === entityCore;
  const icon = isCore ? CORE_ICON
    : isRoot ? ROOT_ICON
    : file.type === 'growth' ? GROWTH_ICON
    : (CLASS_FILE_ICON[entityType] || '📄');
  const displayName = file.name.replace('.md', '');

  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        width: '100%',
        padding: '5px 8px',
        marginBottom: 2,
        background: isSelected ? 'var(--bg-hover)' : 'transparent',
        border: 'none',
        borderRadius: 'var(--radius-sm)',
        color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)',
        fontSize: '0.78rem',
        fontFamily: 'var(--font-mono)',
        cursor: 'pointer',
        textAlign: 'left',
        transition: 'all 0.1s ease',
      }}
    >
      <span style={{ fontSize: '0.7rem' }}>{icon}</span>
      <span>{displayName}</span>
    </button>
  );
}
