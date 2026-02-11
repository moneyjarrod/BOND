// context/WebSocketContext.jsx — Provides WebSocket state to all components
// Usage: const { lastEvent, connected } = useContext(WebSocketContext);

import { createContext } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

export const WebSocketContext = createContext({ lastEvent: null, connected: false });

export function WebSocketProvider({ children }) {
  const ws = useWebSocket();
  return (
    <WebSocketContext.Provider value={ws}>
      {children}
    </WebSocketContext.Provider>
  );
}
