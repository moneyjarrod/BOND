// BOND Control Panel — App Shell
// B69: Four-Class Entity Architecture

import { useState, useEffect, useCallback, useContext } from 'react';
import Header from './components/Header';
import CommandBar from './components/CommandBar';
import SystemStatus from './components/SystemStatus';
import ModuleBay from './components/ModuleBay';
import EntityCards from './components/EntityCards';
import DoctrineViewer from './components/DoctrineViewer';
import CreateEntity from './components/CreateEntity';
import EntityBar from './components/EntityBar';
import DoctrineBanner from './components/DoctrineBanner';
import ProjectMasterBanner from './components/ProjectMasterBanner';
import HandoffGenerator from './components/HandoffGenerator';
import { useEntities } from './hooks/useDoctrine';
// useBridge removed S85 (Dead Code Audit) — clipboard is native in App.jsx
import { useModules } from './hooks/useModules';
import { useSearch } from './hooks/useSearch';
import { WebSocketProvider, WebSocketContext } from './context/WebSocketContext';
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
  return (
    <WebSocketProvider>
      <AppInner />
    </WebSocketProvider>
  );
}

function AppInner() {
  const [activeTab, setActiveTab] = useState('doctrine');
  const [viewerTarget, setViewerTarget] = useState(null);
  const [activeEntity, setActiveEntity] = useState(null);
  const [linkedEntities, setLinkedEntities] = useState([]);
  const [bondConfig, setBondConfig] = useState({ save_confirmation: true });
  const [ahkRunning, setAhkRunning] = useState(null); // null=unknown, true/false
  const [ahkDismissed, setAhkDismissed] = useState(false);
  // LOADED state removed S90 — replaced by ACTIVE + LINKED badges

  const { entities, loading, error, refresh } = useEntities();
  const { modules } = useModules();
  const search = useSearch(activeEntity?.name, linkedEntities);

  // Load active entity state + config from server on mount + tab focus
  const refreshState = useCallback(() => {
    fetch('/api/state').then(r => r.json()).then(state => {
      if (state.entity) {
        setActiveEntity({ name: state.entity, type: state.class, display_name: state.display_name });
      } else {
        setActiveEntity(null);
      }
      if (state.links && state.links.length > 0) {
        setLinkedEntities(state.links.map(l => ({ name: l.entity, type: l.class, display_name: l.display_name })));
      } else {
        setLinkedEntities([]);
      }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    refreshState();
    fetch('/api/config/bond').then(r => r.json()).then(cfg => {
      setBondConfig(cfg);
    }).catch(() => {});
  }, [refreshState]);

  // Re-sync state when tab regains focus
  useEffect(() => {
    const onFocus = () => { if (document.visibilityState === 'visible') refreshState(); };
    document.addEventListener('visibilitychange', onFocus);
    return () => document.removeEventListener('visibilitychange', onFocus);
  }, [refreshState]);

  // Poll AHK status for banner
  useEffect(() => {
    const poll = () => {
      fetch('/api/ahk-status').then(r => r.json()).then(s => {
        setAhkRunning(s.running ?? false);
        if (s.running) setAhkDismissed(false); // reset dismiss when AHK comes back
      }).catch(() => setAhkRunning(false));
    };
    poll();
    const id = setInterval(poll, 5000);
    return () => clearInterval(id);
  }, []);

  // ─── WebSocket live updates ─────────────────────────────
  const { lastEvent, connected: wsConnected } = useContext(WebSocketContext);

  useEffect(() => {
    if (!lastEvent) return;
    const { type } = lastEvent;
    if (type === 'file_added' || type === 'file_changed' || type === 'link_changed') {
      refresh();
    }
    if (type === 'state_changed') {
      refreshState();
    }
    if (type === 'config_changed' && lastEvent.detail?.config) {
      setBondConfig(lastEvent.detail.config);
    }
    if (type === 'entity_changed' || type === 'tool_toggled') {
      refresh();
    }
  }, [lastEvent, refresh, refreshState]);

  // ─── Entity actions ─────────────────────────────────────

  const handleView = useCallback((entity) => {
    setViewerTarget(entity.name);
    setActiveTab('viewer');
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
        setActiveEntity({ name: entity.name, type: entity.type, display_name: entity.display_name });
        // Hydrate links from server response
        if (data.state?.links?.length > 0) {
          setLinkedEntities(data.state.links.map(l => ({ name: l.entity, type: l.class, display_name: l.display_name })));
        } else {
          setLinkedEntities([]);
        }
        setViewerTarget(entity.name);
        setActiveTab('viewer');
        try { await navigator.clipboard.writeText(`BOND:{Enter ${entity.name}}`); } catch {}
      }
    } catch (err) {
      console.error('Enter failed:', err);
    }
  }, []);

  const handleExit = useCallback(async () => {
    try {
      await fetch('/api/state/exit', { method: 'POST' });
      setActiveEntity(null);
      setLinkedEntities([]);
      try { await navigator.clipboard.writeText('BOND:{Exit}'); } catch {}
    } catch (err) {
      console.error('Exit failed:', err);
    }
  }, []);

  const handleLink = useCallback(async (entity) => {
    try {
      const res = await fetch('/api/state/link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entity: entity.name }),
      });
      const data = await res.json();
      if (data.linked && data.state?.links) {
        setLinkedEntities(data.state.links.map(l => ({ name: l.entity, type: l.class, display_name: l.display_name })));
      }
    } catch (err) {
      console.error('Link failed:', err);
    }
  }, []);

  const handleUnlink = useCallback(async (entityName) => {
    try {
      const res = await fetch('/api/state/unlink', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entity: entityName }),
      });
      const data = await res.json();
      if (data.unlinked && data.state?.links) {
        setLinkedEntities(data.state.links.map(l => ({ name: l.entity, type: l.class, display_name: l.display_name })));
      } else if (data.unlinked) {
        setLinkedEntities(prev => prev.filter(e => e.name !== entityName));
      }
    } catch (err) {
      console.error('Unlink failed:', err);
    }
  }, []);



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

  // Save confirmation toggle
  const handleSaveConfirmToggle = useCallback(async () => {
    const newVal = !bondConfig.save_confirmation;
    setBondConfig(prev => ({ ...prev, save_confirmation: newVal }));
    try {
      await fetch('/api/config/bond', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ save_confirmation: newVal }),
      });
    } catch (err) {
      console.error('Config toggle failed:', err);
    }
  }, [bondConfig]);

  // Count entities by class for header
  const classCounts = {
    doctrine: entities.filter(e => e.type === 'doctrine').length,
    project: entities.filter(e => e.type === 'project').length,
    perspective: entities.filter(e => e.type === 'perspective').length,
    library: entities.filter(e => e.type === 'library').length,
  };

  // Warm Restore handler
  const [warmRestoreStatus, setWarmRestoreStatus] = useState(null);
  const handleWarmRestore = useCallback(async () => {
    const query = window.prompt('Warm Restore query (leave empty for entity-only):');
    if (query === null) return; // cancelled
    setWarmRestoreStatus('running');
    try {
      const res = await fetch('/api/warm-restore', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query || '' }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
        window.alert(`Warm Restore error: ${errData.error || errData.stderr || res.status}`);
        setWarmRestoreStatus('error');
        setTimeout(() => setWarmRestoreStatus(null), 3000);
        return;
      }
      const data = await res.json();
      if (data.success) {
        // Bridge to Claude — Claude reads state/warm_restore_output.md
        try { await navigator.clipboard.writeText('BOND:{Warm Restore}'); } catch {}
        setWarmRestoreStatus('done');
        setTimeout(() => setWarmRestoreStatus(null), 2000);
      } else {
        window.alert(`Warm Restore failed: ${data.error || 'Unknown error'}`);
        setWarmRestoreStatus('error');
        setTimeout(() => setWarmRestoreStatus(null), 3000);
      }
    } catch (err) {
      window.alert(`Warm Restore fetch error: ${err.message}`);
      setWarmRestoreStatus('error');
      setTimeout(() => setWarmRestoreStatus(null), 3000);
    }
  }, []);

  // Entity Warm Restore — perspective-local crystal field (S116)
  const handleEntityWarmRestore = useCallback(async (entityName) => {
    try {
      await navigator.clipboard.writeText(`BOND:{Entity Warm Restore} ${entityName}`);
    } catch {}
  }, []);

  // Entity Crystal — perspective-local crystal (S116)
  const handleEntityCrystal = useCallback(async () => {
    try {
      await navigator.clipboard.writeText('BOND:{Crystal}');
    } catch {}
  }, []);

  // Handoff generator modal
  const [showHandoff, setShowHandoff] = useState(false);

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
        saveConfirmation={bondConfig.save_confirmation}
        onSaveConfirmToggle={handleSaveConfirmToggle}
        wsConnected={wsConnected}
      />

      {ahkRunning === false && !ahkDismissed && (
        <div style={{
          background: 'rgba(248,81,73,0.15)',
          border: '1px solid rgba(248,81,73,0.4)',
          borderRadius: 'var(--radius-sm)',
          padding: '8px 14px',
          margin: '0 12px 4px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          color: '#f85149',
          animation: 'fadeIn 0.3s ease',
        }}>
          <span>
            ⚠️ <strong>Counter not detected.</strong> Panel buttons copy to clipboard but won't reach Claude without the AHK bridge.
            Run <code style={{ background: 'rgba(248,81,73,0.2)', padding: '1px 5px', borderRadius: 3 }}>Counter/BOND_v8.ahk</code> to connect.
          </span>
          <button
            onClick={() => setAhkDismissed(true)}
            style={{
              background: 'none', border: 'none', color: '#f85149',
              cursor: 'pointer', fontSize: '1rem', padding: '0 4px', opacity: 0.6,
            }}
            title="Dismiss (will return if AHK still not detected)"
          >×</button>
        </div>
      )}

      <EntityBar activeEntity={activeEntity} linkedEntities={linkedEntities} onExit={handleExit} onUnlink={handleUnlink} onEntityWarmRestore={handleEntityWarmRestore} onEntityCrystal={handleEntityCrystal} />

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
            <>
            <DoctrineBanner
              entities={entities}
              allEntities={entities}
              activeEntity={activeEntity}
              linkedEntities={linkedEntities}
              onEnter={handleEnter}
              onView={handleView}
              onExit={handleExit}
              onLink={handleLink}
            />
            <ProjectMasterBanner
              entities={entities}
              allEntities={entities}
              activeEntity={activeEntity}
              linkedEntities={linkedEntities}
              onEnter={handleEnter}
              onView={handleView}
              onExit={handleExit}
              onLink={handleLink}
            />
            </>
          )}
          <EntityCards
            entities={currentTab.filter === 'doctrine'
              ? entities.filter(e => e.name !== 'BOND_MASTER' && e.name !== 'PROJECT_MASTER')
              : entities}
            filter={currentTab.filter}
            linkedEntities={linkedEntities}
            activeEntity={activeEntity}
            onView={handleView}
            onEnter={handleEnter}
            onToolToggle={handleToolToggle}
            onRename={handleRename}
            onExit={handleExit}
            onCreate={() => setShowCreate(currentTab.filter)}
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
            linkedEntities={linkedEntities}
            entityType={entities.find(e => e.name === viewerTarget)?.type}
            entityCore={entities.find(e => e.name === viewerTarget)?.core}
            search={search}
          />
        )}
      </main>

      <CommandBar
        onGenerateHandoff={() => setShowHandoff(true)}
        onWarmRestore={handleWarmRestore}
      />

      {showCreate && (
        <CreateEntity
          entityClass={showCreate}
          onCreated={handleEntityCreated}
          onCancel={() => setShowCreate(null)}
        />
      )}

      {showHandoff && (
        <HandoffGenerator onClose={() => setShowHandoff(false)} />
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
