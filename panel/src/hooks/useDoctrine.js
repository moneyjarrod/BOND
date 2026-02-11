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

  const fetchFiles = useCallback(() => {
    if (!entityName) { setFiles([]); return; }
    setLoading(true);
    setError(null);
    fetch(`/api/doctrine/${encodeURIComponent(entityName)}`)
      .then(res => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return res.json();
      })
      .then(data => setFiles(data.files || []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [entityName]);

  useEffect(() => { fetchFiles(); }, [fetchFiles]);

  return { files, loading, error, refresh: fetchFiles };
}

export function useFileContent(entityName, fileName) {
  const [content, setContent] = useState(null);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchContent = useCallback(() => {
    if (!entityName || !fileName) { setContent(null); setMeta(null); return; }
    setLoading(true);
    fetch(`/api/doctrine/${encodeURIComponent(entityName)}/${encodeURIComponent(fileName)}`)
      .then(res => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return res.json();
      })
      .then(data => {
        setContent(data.content);
        setMeta({ type: data.type, file: data.file, entity: data.entity });
      })
      .finally(() => setLoading(false));
  }, [entityName, fileName]);

  useEffect(() => { fetchContent(); }, [fetchContent]);

  return { content, meta, loading, refresh: fetchContent };
}
