// DoctrineViewer.jsx — Reads doctrine folders, displays file content
// Left sidebar: file list with 🔒/🌱 icons
// Right panel: file content (pre-formatted for now, markdown renderer in Session 6)

import { useState } from 'react';
import { useEntityFiles, useFileContent } from '../hooks/useDoctrine';
import SearchPanel from './SearchPanel';

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
  search,
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [showSearch, setShowSearch] = useState(false);
  const linkedNames = new Set((linkedEntities || []).map(e => typeof e === 'string' ? e : e.name));
  const { files, loading: filesLoading } = useEntityFiles(viewerTarget);
  const { content, meta, loading: contentLoading } = useFileContent(viewerTarget, selectedFile);

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
        <div style={{ display: 'flex', gap: 6 }}>
          {search && (
            <button
              onClick={() => setShowSearch(s => !s)}
              style={{
                padding: '4px 12px',
                fontSize: '0.75rem',
                fontFamily: 'var(--font-mono)',
                background: showSearch ? 'var(--accent)' : 'var(--bg-elevated)',
                color: showSearch ? '#fff' : 'var(--text-secondary)',
                border: `1px solid ${showSearch ? 'var(--accent)' : 'var(--border)'}`,
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
              }}
            >
              🔍 Search
            </button>
          )}

        </div>
      </div>

      {/* Search panel (collapsible) */}
      {showSearch && search && (
        <div style={{
          padding: '8px 0 12px',
          borderBottom: '1px solid var(--border)',
          marginBottom: 12,
        }}>
          <SearchPanel {...search} />
        </div>
      )}

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
          ) : (
            files.map(f => (
              <FileEntry
                key={f.name}
                file={f}
                isSelected={selectedFile === f.name}
                onClick={() => setSelectedFile(f.name)}
                entityType={entityType}
                entityCore={entityCore}
              />
            ))
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
                <span>{meta?.type === 'growth' ? GROWTH_ICON : (CLASS_FILE_ICON[entityType] || '📄')}</span>
                <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{selectedFile}</span>
                <span className="text-muted" style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)' }}>
                  ({meta?.type === 'growth' ? 'growth' : entityType || 'file'})
                </span>
              </div>

              {/* File content */}
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
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function FileEntry({ file, isSelected, onClick, entityType, entityCore }) {
  const isCore = entityCore && file.name === entityCore;
  const icon = isCore ? CORE_ICON
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
