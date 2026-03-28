#!/bin/bash
# BOND Search Daemon — Clean Stop (v3.5.0)
# Uses PID file first, port scan as fallback.

cd "$(dirname "$0")"

KILLED=0

# ─── Method 1: PID file ─────────────────────────────────
if [ -f "state/daemon.pid" ]; then
    SAVED_PID=$(cat state/daemon.pid)
    echo "  PID file found: $SAVED_PID"
    if kill -0 "$SAVED_PID" 2>/dev/null; then
        kill -9 "$SAVED_PID" 2>/dev/null
        echo "  Killed daemon PID $SAVED_PID"
        KILLED=$((KILLED + 1))
    else
        echo "  PID $SAVED_PID not running (stale PID file)"
    fi
    rm -f state/daemon.pid
fi

# ─── Method 2: Port scan (catches orphans) ──────────────
while true; do
    PIDS=$(lsof -i :3003 -sTCP:LISTEN -t 2>/dev/null)
    if [ -z "$PIDS" ]; then
        break
    fi
    for PID in $PIDS; do
        kill -9 "$PID" 2>/dev/null
        echo "  Killed port 3003 occupant PID: $PID"
        KILLED=$((KILLED + 1))
    done
    sleep 1
done

# ─── Verify ─────────────────────────────────────────────
if lsof -i :3003 -sTCP:LISTEN -t > /dev/null 2>&1; then
    echo "  WARNING: Port 3003 still occupied."
else
    if [ "$KILLED" -gt 0 ]; then
        echo "  Port 3003 clear. $KILLED process(es) stopped."
    else
        echo "  Port 3003 was already clear. No daemon running."
    fi
fi
