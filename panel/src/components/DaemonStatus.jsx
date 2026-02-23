// 🔍 BOND Search Daemon — Status indicator + restart control
// S120: CM insight — daemon's response IS its health. One ping on mount, self-reports after.
// S120: P11 insight — launcher script as transition fitting between Node and Python.

import { useState, useEffect, useCallback } from 'react';

export default function DaemonStatus() {
  const [status, setStatus] = useState(null); // null = loading, { online, error, ... }
  const [starting, setStarting] = useState(false);

  const checkStatus = useCallback(async () => {
    try {
      const r = await fetch('/api/daemon/status', { cache: 'no-store' });
      const data = await r.json();
      setStatus(data);
    } catch {
      setStatus({ online: false, error: 'Panel cannot reach daemon API' });
    }
  }, []);

  // One ping on mount + heartbeat every 30s
  // CM: no separate /health endpoint. But panel needs to detect drops.
  useEffect(() => {
    checkStatus();
    const id = setInterval(checkStatus, 30000);
    return () => clearInterval(id);
  }, [checkStatus]);

  const handleRestart = async () => {
    setStarting(true);
    try {
      const r = await fetch('/api/daemon/start', { method: 'POST' });
      const data = await r.json();
      if (data.online) {
        setStatus({ online: true, timestamp: data.timestamp });
      } else {
        // Launcher ran but daemon slow — retry after 3s
        setTimeout(async () => {
          await checkStatus();
          setStarting(false);
        }, 3000);
        return;
      }
    } catch {
      setStatus({ online: false, error: 'Failed to start daemon' });
    }
    setStarting(false);
  };

  const online = status?.online ?? false;
  const loading = status === null;

  return (
    <span
      className="status-item"
      title={
        loading ? 'Checking daemon...'
        : online ? 'Search daemon online'
        : `Search daemon offline${status?.error ? `: ${status.error}` : ''}`
      }
      style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
    >
      <span className="status-label">🔍</span>
      {/* Status dot */}
      <span style={{
        width: 7, height: 7, borderRadius: '50%', display: 'inline-block',
        background: loading ? '#e3b341'
          : online ? '#3fb950'
          : '#f85149',
        boxShadow: online ? '0 0 4px rgba(63,185,80,0.5)' : 'none',
        transition: 'background 0.3s, box-shadow 0.3s',
      }} />
      {/* Restart button — only when offline */}
      {!loading && !online && (
        <span
          onClick={starting ? undefined : handleRestart}
          style={{
            fontSize: '0.6rem',
            padding: '1px 5px',
            borderRadius: 3,
            background: starting ? 'rgba(227,179,65,0.2)' : 'rgba(248,81,73,0.15)',
            border: `1px solid ${starting ? 'rgba(227,179,65,0.4)' : 'rgba(248,81,73,0.3)'}`,
            color: starting ? '#e3b341' : '#f85149',
            cursor: starting ? 'wait' : 'pointer',
            userSelect: 'none',
            fontFamily: 'var(--font-mono)',
            letterSpacing: '0.5px',
          }}
        >
          {starting ? '...' : '↻'}
        </span>
      )}
    </span>
  );
}

