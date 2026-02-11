// hooks/useWebSocket.js — WebSocket connection with exponential backoff reconnect
// Returns { lastEvent, connected } for use via WebSocketContext

import { useState, useEffect, useRef, useCallback } from 'react';

// In dev (Vite 5173), connect directly to Express on 3000
// In prod (served from 3000), connect to same origin
const isDev = window.location.port === '5173';
const WS_URL = isDev
  ? `ws://${window.location.hostname}:3000`
  : `ws://${window.location.hostname}:${window.location.port || 3000}`;
const MAX_BACKOFF = 30000;

export function useWebSocket() {
  const [lastEvent, setLastEvent] = useState(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const backoffRef = useRef(1000);
  const reconnectTimer = useRef(null);
  const unmountedRef = useRef(false);

  const connect = useCallback(() => {
    if (unmountedRef.current) return;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        backoffRef.current = 1000; // reset backoff on successful connect
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastEvent(data);
        } catch { /* ignore non-JSON */ }
      };

      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;
        if (!unmountedRef.current) {
          reconnectTimer.current = setTimeout(() => {
            backoffRef.current = Math.min(backoffRef.current * 2, MAX_BACKOFF);
            connect();
          }, backoffRef.current);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      // WebSocket constructor can throw if URL is invalid
      setConnected(false);
    }
  }, []);

  useEffect(() => {
    unmountedRef.current = false;
    connect();
    return () => {
      unmountedRef.current = true;
      clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect on intentional close
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { lastEvent, connected };
}
