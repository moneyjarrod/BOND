// src/hooks/useSearch.js
// SLA search hook — builds index when entity is entered, exposes query()

import { useState, useCallback, useEffect, useRef } from 'react';
import { buildIndex } from '../services/sla';

/**
 * Hook: useSearch
 * 
 * On {Enter}, fetches all entity files and builds an SLA index.
 * Exposes query() for instant client-side search.
 * 
 * @param {string|null} activeEntityName - Currently entered entity
 * @param {Array} linkedEntities - Linked entity names to include
 * @returns {{ query, indexReady, indexStats, indexing, error }}
 */
export function useSearch(activeEntityName, linkedEntities = []) {
  const [corpus, setCorpus] = useState(null);
  const [indexing, setIndexing] = useState(false);
  const [indexReady, setIndexReady] = useState(false);
  const [indexStats, setIndexStats] = useState(null);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);

  // Build index when active entity changes
  useEffect(() => {
    if (!activeEntityName) {
      setCorpus(null);
      setIndexReady(false);
      setIndexStats(null);
      return;
    }

    // Abort any previous build
    if (abortRef.current) abortRef.current.abort = true;
    const ctrl = { abort: false };
    abortRef.current = ctrl;

    async function build() {
      setIndexing(true);
      setError(null);
      setIndexReady(false);

      try {
        // Gather all entities to index (active + linked)
        const entityNames = [activeEntityName, ...linkedEntities.map(e =>
          typeof e === 'string' ? e : e.name
        )];

        const allFiles = [];

        for (const name of entityNames) {
          if (ctrl.abort) return;

          // Fetch file list
          const listRes = await fetch(`/api/doctrine/${encodeURIComponent(name)}`);
          if (!listRes.ok) continue;
          const listData = await listRes.json();
          const fileList = listData.files || [];

          // Fetch each file's content (S118: expanded to .md, .txt, .pdf, .docx)
          const SEARCHABLE_EXT = ['.md', '.txt', '.pdf', '.docx', '.html'];
          for (const f of fileList) {
            if (ctrl.abort) return;
            if (!SEARCHABLE_EXT.some(ext => f.name.toLowerCase().endsWith(ext))) continue;

            const contentRes = await fetch(
              `/api/doctrine/${encodeURIComponent(name)}/${encodeURIComponent(f.name)}`
            );
            if (!contentRes.ok) continue;
            const contentData = await contentRes.json();

            allFiles.push({
              name: `${name}/${f.name}`,
              content: contentData.content || '',
            });
          }
        }

        if (ctrl.abort) return;

        // Build index
        const idx = buildIndex(allFiles, activeEntityName);
        if (idx && !ctrl.abort) {
          setCorpus(idx);
          setIndexStats(idx.stats());
          setIndexReady(true);
        }
      } catch (err) {
        if (!ctrl.abort) setError(err.message);
      } finally {
        if (!ctrl.abort) setIndexing(false);
      }
    }

    build();

    return () => { ctrl.abort = true; };
  }, [activeEntityName, linkedEntities.map(e => typeof e === 'string' ? e : e.name).join(',')]);

  // Query function
  const query = useCallback((queryText) => {
    if (!corpus || !queryText.trim()) return null;
    return corpus.query(queryText);
  }, [corpus]);

  return { query, indexReady, indexStats, indexing, error };
}
