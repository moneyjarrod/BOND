#!/bin/bash
# BOND Search Daemon Launcher — v3.5.0
# Obliterates any zombie on port 3003 before starting fresh.
# Writes PID to state/daemon.pid for clean shutdown.

cd "$(dirname "$0")"

# ─── Phase 1: Kill ALL listeners on port 3003 ───────────
KILLED=0
while true; do
    PIDS=$(lsof -i :3003 -sTCP:LISTEN -t 2>/dev/null)
    if [ -z "$PIDS" ]; then
        break
    fi
    for PID in $PIDS; do
        kill -9 "$PID" 2>/dev/null
        echo "  Killed zombie PID: $PID"
        KILLED=$((KILLED + 1))
    done
    sleep 1
done

if [ "$KILLED" -gt 0 ]; then
    echo "  Cleared $KILLED zombie(s) from port 3003."
    sleep 1
fi

# ─── Phase 2: Verify port is clear ──────────────────────
if lsof -i :3003 -sTCP:LISTEN -t > /dev/null 2>&1; then
    echo "  ERROR: Port 3003 still occupied after kill. Cannot start."
    exit 1
fi

# ─── Phase 3: Clear bytecache ────────────────────────────
export PYTHONDONTWRITEBYTECODE=1
if [ -d "search_daemon/__pycache__" ]; then
    rm -rf "search_daemon/__pycache__"
    echo "  Cleared __pycache__"
fi

# ─── Phase 4: Start daemon ──────────────────────────────
python3 search_daemon/bond_search.py &
DAEMON_PID=$!

sleep 2

# ─── Phase 5: Verify and write PID ──────────────────────
if lsof -i :3003 -sTCP:LISTEN -t > /dev/null 2>&1; then
    echo "$DAEMON_PID" > state/daemon.pid
    echo "  BOND Daemon started on port 3003 (PID: $DAEMON_PID)"
else
    echo "  WARNING: Daemon may not have started. Check port 3003."
fi
