// useModules — Fetch module configs, toggle enable/disable, poll live status
import { useState, useEffect, useCallback } from 'react';

const API = 'http://localhost:3000';
const STORAGE_KEY = 'bond_modules_enabled';

function loadEnabled() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
  catch { return {}; }
}

function saveEnabled(map) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(map));
}

export function useModules() {
  const [modules, setModules] = useState([]);
  const [enabledMap, setEnabledMap] = useState(loadEnabled);
  const [loading, setLoading] = useState(true);

  const fetchModules = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/modules`);
      const data = await res.json();

      const withStatus = await Promise.all(
        data.modules.map(async (mod) => {
          const enabled = enabledMap[mod.id] !== false; // default ON
          let status = 'offline';
          let liveData = null;

          if (enabled) {
            try {
              const statusRes = await fetch(`${API}${mod.status_endpoint}`, {
                signal: AbortSignal.timeout(2000),
              });
              if (statusRes.ok) {
                liveData = await statusRes.json();
                status = 'active';
              }
            } catch { /* offline */ }
          }

          return { ...mod, enabled, status, data: liveData };
        })
      );

      setModules(withStatus);
    } catch {
      setModules([]);
    } finally {
      setLoading(false);
    }
  }, [enabledMap]);

  const toggleModule = useCallback((id) => {
    setEnabledMap(prev => {
      const current = prev[id] !== false;
      const next = { ...prev, [id]: !current };
      saveEnabled(next);
      return next;
    });
  }, []);

  useEffect(() => {
    fetchModules();
    const interval = setInterval(fetchModules, 30000);
    return () => clearInterval(interval);
  }, [fetchModules]);

  return { modules, loading, refresh: fetchModules, toggleModule };
}
