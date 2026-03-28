@echo off
REM BOND Search Daemon Launcher — v3.5.0
REM Obliterates any zombie on port 3003 before starting fresh.
REM Writes PID to state\daemon.pid for clean shutdown.

cd /d "%~dp0"
setlocal EnableDelayedExpansion

REM ─── Phase 1: Kill ALL listeners on port 3003 ───────────
REM Loop until port is clear. Catches multiple zombies.
set KILLED=0
:kill_loop
set FOUND_PID=
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":3003 " ^| findstr "LISTENING"') do (
    if not "%%a"=="0" (
        set FOUND_PID=%%a
        taskkill /PID %%a /F >nul 2>&1
        echo   Killed zombie PID: %%a
        set /a KILLED+=1
    )
)
if defined FOUND_PID (
    timeout /t 1 /nobreak >nul
    goto kill_loop
)

if %KILLED% gtr 0 (
    echo   Cleared %KILLED% zombie^(s^) from port 3003.
    timeout /t 1 /nobreak >nul
)

REM ─── Phase 2: Verify port is clear ──────────────────────
netstat -ano 2>nul | findstr ":3003 " | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo   ERROR: Port 3003 still occupied after kill. Cannot start.
    echo   Run: netstat -ano ^| findstr ":3003"
    pause
    exit /b 1
)

REM ─── Phase 3: Clear bytecache (prevents stale code) ─────
set PYTHONDONTWRITEBYTECODE=1
if exist "search_daemon\__pycache__" (
    rmdir /s /q "search_daemon\__pycache__" >nul 2>&1
    echo   Cleared __pycache__
)

REM ─── Phase 4: Start daemon ──────────────────────────────
start "BOND Daemon" /min cmd /c "cd /d "%~dp0" && set PYTHONDONTWRITEBYTECODE=1 && python search_daemon\bond_search.py"

REM Give it a moment to bind
timeout /t 2 /nobreak >nul

REM ─── Phase 5: Capture PID and verify ────────────────────
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":3003 " ^| findstr "LISTENING"') do (
    echo %%a> state\daemon.pid
    echo   BOND Daemon started on port 3003 ^(PID: %%a^)
    goto :done
)

echo   WARNING: Daemon may not have started. Check port 3003.

:done
endlocal
