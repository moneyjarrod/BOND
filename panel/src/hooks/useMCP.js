// useMCP — Direct MCP tool invocation from panel components
// Session 4: Connects panel UI to real QAIS/ISS/EAP/Limbic servers
// S81 fix: useCallback wrapping functions, not object literals
import { useState, useCallback } from 'react';

const API = 'http://localhost:3000';

export function useMCP() {
  const [loading, setLoading] = useState(false);
  const [lastResult, setLastResult] = useState(null);
  const [lastError, setLastError] = useState(null);

  const invoke = useCallback(async (system, tool, input = '') => {
    setLoading(true);
    setLastError(null);
    setLastResult(null);

    try {
      const res = await fetch(`${API}/api/mcp/${system}/invoke`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool, input }),
        signal: AbortSignal.timeout(15000),
      });

      const data = await res.json();

      if (data.error) {
        setLastError(data.error);
        return { error: data.error };
      }

      setLastResult(data);
      return { data };
    } catch (err) {
      const msg = err.name === 'TimeoutError' ? 'Request timed out' : err.message;
      setLastError(msg);
      return { error: msg };
    } finally {
      setLoading(false);
    }
  }, []);

  // Convenience wrappers — proper functions
  const qaisStats = useCallback(() => invoke('qais', 'stats'), [invoke]);
  const qaisExists = useCallback((identity) => invoke('qais', 'exists', identity), [invoke]);
  const qaisResonate = useCallback((identity, role, candidates) =>
    invoke('qais', 'resonate', `${identity}|${role}|${candidates.join(',')}`), [invoke]);

  const issAnalyze = useCallback((text) => invoke('iss', 'analyze', text), [invoke]);
  const issCompare = useCallback((texts) => invoke('iss', 'compare', texts.join('\n')), [invoke]);
  const issStatus = useCallback(() => invoke('iss', 'status'), [invoke]);

  return {
    invoke,
    loading,
    lastResult,
    lastError,
    qais: { stats: qaisStats, exists: qaisExists, resonate: qaisResonate },
    iss: { analyze: issAnalyze, compare: issCompare, status: issStatus },
  };
}
