// BOND Control Panel — App Shell
// B69: Four-Class Entity Architecture

import { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import CommandBar from './components/CommandBar';
import SystemStatus from './components/SystemStatus';
import ModuleBay from './components/ModuleBay';
import EntityCards from './components/EntityCards';
import DoctrineViewer from './components/DoctrineViewer';
import CreateEntity from './components/CreateEntity';
import EntityBar from './components/EntityBar';
import DoctrineBanner from './components/DoctrineBanner';
import { useEntities } from './hooks/useDoctrine';
// useBridge removed S85 (Dead Code Audit) — clipboard is native in App.jsx
import { useModules } from './hooks/useModules';
import './styles/bond.css';

const TABS = [
  { id: 'doctrine',     label: 'Doctrine',     icon: '📜', filter: 'doctrine' },
  { id: 'projects',     label: 'Projects',     icon: '⚒️', filter: 'project' },
  { id: 'perspectives', label: 'Perspectives', icon: '🔭', filter: 'perspective' },
  { id: 'library',      label: 'Library',      icon: '📚', filter: 'library' },
  { id: 'systems',      label: 'Systems',      icon: '⚙️', filter: null },
  { id: 'viewer',       label: 'Viewer',       icon: '📖', filter: null },
];

// Uses Vite proxy in dev, relative in prod

export default function App() {
  const [activeTab, setActiveTab] = useState('doctrine');
  const [viewerTarget, setViewerTarget] = useState(null);
  const [activeEntity, setActiveEntity] = useState(null);
  const [loadedEntities, setLoadedEntities] = useState(() => {
    try { return JSON.parse(localStorage.getItem('bond_loaded') || '[]'); }
    catch { return []; }
  });

  const { entities, loading, error, refresh } = useEntities();
  const { modules } = useModules();

  // Load active entity state from server on mount
  useEffect(() => {
    fetch('/api/state').then(r => r.json()).then(state => {
      if (state.entity) {
        setActiveEntity({ name: state.entity, type: state.class, display_name: state.display_name });
      }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    localStorage.setItem('bond_loaded', JSON.stringify(loadedEntities));
  }, [loadedEntities]);

  // ─── Entity actions ─────────────────────────────────────

  const handleView = useCallback((entity) => {
    setViewerTarget(entity.name);
    setActiveTab('viewer');
  }, []);

  const handleLoad = useCallback((entity) => {
    setLoadedEntities(prev => {
      if (prev.includes(entity.name)) return prev;
      return [...prev, entity.name];
    });
  }, []);

  const handleEnter = useCallback(async (entity) => {
    try {
      const res = await fetch('/api/state/enter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entity: entity.name }),
      });
      const data = await res.json();
      if (data.entered) {
        handleLoad(entity);
        setActiveEntity({ name: entity.name, type: entity.type, display_name: entity.display_name });
        setViewerTarget(entity.name);
        setActiveTab('viewer');
        try { await navigator.clipboard.writeText(`BOND:{Enter ${entity.name}}`); } catch {}
      }
    } catch (err) {
      console.error('Enter failed:', err);
    }
  }, [handleLoad]);

  const handleExit = useCallback(async () => {
    try {
      await fetch('/api/state/exit', { method: 'POST' });
      setActiveEntity(null);
      try { await navigator.clipboard.writeText('BOND:{Exit}'); } catch {}
    } catch (err) {
      console.error('Exit failed:', err);
    }
  }, []);

  const handleUnload = useCallback((entityName) => {
    setLoadedEntities(prev => prev.filter(n => n !== entityName));
    if (activeEntity?.name === entityName) {
      setActiveEntity(null);
    }
  }, [activeEntity]);

  // Rename entity display name
  const handleRename = useCallback(async (entityName, displayName) => {
    try {
      await fetch(`/api/doctrine/${entityName}/name`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ display_name: displayName }),
      });
      // Update activeEntity if it's the one being renamed
      if (activeEntity?.name === entityName) {
        setActiveEntity(prev => ({ ...prev, display_name: displayName }));
      }
      refresh();
    } catch (err) {
      console.error('Rename failed:', err);
    }
  }, [refresh, activeEntity]);

  // B69: Tool toggle — persists to entity.json via sidecar
  const handleToolToggle = useCallback(async (entityName, toolId, value) => {
    try {
      await fetch(`/api/doctrine/${entityName}/tools`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tools: { [toolId]: value } }),
      });
      refresh(); // Re-fetch entities to get updated tool state
    } catch (err) {
      console.error('Tool toggle failed:', err);
    }
  }, [refresh]);

  // Count entities by class for header
  const classCounts = {
    doctrine: entities.filter(e => e.type === 'doctrine').length,
    project: entities.filter(e => e.type === 'project').length,
    perspective: entities.filter(e => e.type === 'perspective').length,
    library: entities.filter(e => e.type === 'library').length,
  };

  // Create entity modal
  const [showCreate, setShowCreate] = useState(null); // null or class string

  const handleEntityCreated = useCallback((data) => {
    setShowCreate(null);
    refresh();
    // Auto-navigate to the new entity in viewer
    setViewerTarget(data.name);
    setActiveTab('viewer');
  }, [refresh]);

  const currentTab = TABS.find(t => t.id === activeTab);

  return (
    <div className="app-shell">
      <Header
        activeEntity={activeEntity}
        modules={modules}
        classCounts={classCounts}
      />

      <EntityBar activeEntity={activeEntity} onExit={handleExit} />

      <nav className="tab-bar">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </nav>

      <main className="app-content">
        {currentTab?.filter && (
          loading ? <LoadingState /> :
          error ? <ErrorState error={error} onRetry={refresh} /> :
          <>
          {currentTab.filter === 'doctrine' && (
            <DoctrineBanner
              entities={entities}
              activeEntity={activeEntity}
              onEnter={handleEnter}
              onView={handleView}
              onExit={handleExit}
            />
          )}
          <EntityCards
            entities={currentTab.filter === 'doctrine'
              ? entities.filter(e => e.name !== 'BOND_MASTER')
              : entities}
            filter={currentTab.filter}
            loadedEntities={loadedEntities}
            activeEntity={activeEntity}
            onView={handleView}
            onLoad={handleLoad}
            onEnter={handleEnter}
            onToolToggle={handleToolToggle}
            onRename={handleRename}
            onExit={handleExit}
          />
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: 12 }}>
            <button
              className="btn-create-entity"
              onClick={() => setShowCreate(currentTab.filter)}
            >
              + New {currentTab.label.replace(/s$/, '')}
            </button>
          </div>
          </>
        )}

        {activeTab === 'systems' && <ModuleBay />}

        {activeTab === 'viewer' && (
          <DoctrineViewer
            viewerTarget={viewerTarget}
            activeEntity={activeEntity}
            loadedEntities={loadedEntities}
            onUnload={handleUnload}
            entityType={entities.find(e => e.name === viewerTarget)?.type}
            entityCore={entities.find(e => e.name === viewerTarget)?.core}
          />
        )}
      </main>

      <CommandBar />

      {showCreate && (
        <CreateEntity
          entityClass={showCreate}
          onCreated={handleEntityCreated}
          onCancel={() => setShowCreate(null)}
        />
      )}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="placeholder">
      <div className="placeholder-text" style={{ fontFamily: 'var(--font-mono)' }}>
        Loading entities...
      </div>
    </div>
  );
}

function ErrorState({ error, onRetry }) {
  return (
    <div className="placeholder">
      <div className="placeholder-icon">⚠️</div>
      <div className="placeholder-text">Could not reach sidecar</div>
      <div className="placeholder-sub" style={{ maxWidth: 400, textAlign: 'center' }}>
        {error}
      </div>
      <button
        onClick={onRetry}
        style={{
          marginTop: 12,
          padding: '6px 16px',
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-sm)',
          color: 'var(--text-secondary)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.8rem',
          cursor: 'pointer',
        }}
      >
        Retry
      </button>
    </div>
  );
}
