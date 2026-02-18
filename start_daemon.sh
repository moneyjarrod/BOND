#!/bin/bash
# BOND Search Daemon Launcher
# Transition fitting: Panel calls this script, not Python directly.
# User can run manually if panel coupling fails.

cd "$(dirname "$0")"

# Check if port 3003 is already in use
if lsof -i :3003 -sTCP:LISTEN -t > /dev/null 2>&1; then
    echo "Daemon already running on port 3003. Killing existing..."
    kill $(lsof -i :3003 -sTCP:LISTEN -t) 2>/dev/null
    sleep 1
fi

# Start daemon in background
python3 search_daemon/bond_search.py &
DAEMON_PID=$!

echo "Started BOND Search Daemon on port 3003 (PID: $DAEMON_PID)"

# Write PID for panel cleanup
echo $DAEMON_PID > state/daemon.pid
