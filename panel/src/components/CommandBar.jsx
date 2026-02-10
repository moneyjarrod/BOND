// Command Bar — Bottom bar with BOND commands
// Clipboard bridge: copies "BOND:{command}" → AHK picks it up via OnClipboardChange

import { useState, useCallback } from 'react';

const COMMANDS = [
  { icon: '🔄', label: 'Restore', value: '{Full Restore}' },
  { icon: '⚡', label: 'Sync',    value: '{Sync}' },
  { icon: '💾', label: 'Save',    value: '{Save}' },
  { icon: '💎', label: 'Crystal', value: '{Crystal}' },
  { icon: '📍', label: 'Tick',    value: '{Tick}' },
  { icon: '🌀', label: 'Chunk',   value: '{Chunk}' },
];

const BRIDGE_PREFIX = 'BOND:';

export default function CommandBar({ onGenerateHandoff }) {
  const [sentCmd, setSentCmd] = useState(null);

  const handleClick = useCallback(async (cmd) => {
    try {
      await navigator.clipboard.writeText(BRIDGE_PREFIX + cmd.value);
      setSentCmd(cmd.value);
      setTimeout(() => setSentCmd(null), 1200);
    } catch (err) {
      console.error('Clipboard write failed:', err);
      // Fallback: textarea copy
      const ta = document.createElement('textarea');
      ta.value = BRIDGE_PREFIX + cmd.value;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setSentCmd(cmd.value);
      setTimeout(() => setSentCmd(null), 1200);
    }
  }, []);

  return (
    <div className="command-bar">
      <span
        title="Clipboard bridge — clicks copy to AHK"
        style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          background: 'var(--status-active)',
          marginRight: 8,
          flexShrink: 0,
          boxShadow: '0 0 6px rgba(63, 185, 80, 0.5)',
        }}
      />
      {COMMANDS.map((cmd) => (
        <button
          key={cmd.value}
          className={`cmd-btn ${sentCmd === cmd.value ? 'sent' : ''}`}
          onClick={() => handleClick(cmd)}
          title={cmd.value}
        >
          <span className="cmd-icon">{cmd.icon}</span>
          <span>{cmd.label}</span>
        </button>
      ))}
      <span style={{ width: 1, height: 20, background: 'var(--border)', flexShrink: 0 }} />
      <button
        className="cmd-btn cmd-btn-handoff"
        onClick={onGenerateHandoff}
        title="Generate session handoff document"
      >
        <span className="cmd-icon">📋</span>
        <span>Handoff</span>
      </button>
    </div>
  );
}
