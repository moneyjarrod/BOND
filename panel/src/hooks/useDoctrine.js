// src/hooks/useDoctrine.js
// Fetches entity list and individual files from Express sidecar on :3000

import { useState, useEffect, useCallback } from 'react';

export function useEntities() {
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch('/api/doctrine');
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();
      setEntities(data.entities || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return { entities, loading, error, refresh };
}

export function useEntityFiles(entityName) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!entityName) { setFiles([]); return; }
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetch(`/api/doctrine/${encodeURIComponent(entityName)}`)
      .then(res => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return res.json();
      })
      .then(data => { if (!cancelled) setFiles(data.files || []); })
      .catch(err => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [entityName]);

  return { files, loading, error };
}

export function useFileContent(entityName, fileName) {
  const [content, setContent] = useState(null);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!entityName || !fileName) { setContent(null); setMeta(null); return; }
    let cancelled = false;
    setLoading(true);
    fetch(`/api/doctrine/${encodeURIComponent(entityName)}/${encodeURIComponent(fileName)}`)
      .then(res => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return res.json();
      })
      .then(data => {
        if (!cancelled) {
          setContent(data.content);
          setMeta({ type: data.type, file: data.file, entity: data.entity });
        }
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [entityName, fileName]);

  return { content, meta, loading };
}
