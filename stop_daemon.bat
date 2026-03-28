@echo off
REM BOND Search Daemon — Clean Stop (v3.5.0)
REM Uses PID file first, port scan as fallback.
REM Never kills all Python — surgical only.

cd /d "%~dp0"
setlocal EnableDelayedExpansion

set KILLED=0

REM ─── Method 1: PID file ─────────────────────────────────
if exist "state\daemon.pid" (
    set /p SAVED_PID=<state\daemon.pid
    echo   PID file found: !SAVED_PID!
    taskkill /PID !SAVED_PID! /F >nul 2>&1
    if !ERRORLEVEL!==0 (
        echo   Killed daemon PID !SAVED_PID!
        set /a KILLED+=1
    ) else (
        echo   PID !SAVED_PID! not running ^(stale PID file^)
    )
    del "state\daemon.pid" >nul 2>&1
)

REM ─── Method 2: Port scan (catches orphans) ──────────────
:kill_loop
set FOUND_PID=
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":3003 " ^| findstr "LISTENING"') do (
    if not "%%a"=="0" (
        set FOUND_PID=%%a
        taskkill /PID %%a /F >nul 2>&1
        echo   Killed port 3003 occupant PID: %%a
        set /a KILLED+=1
    )
)
if defined FOUND_PID (
    timeout /t 1 /nobreak >nul
    goto kill_loop
)

REM ─── Verify ─────────────────────────────────────────────
netstat -ano 2>nul | findstr ":3003 " | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo   WARNING: Port 3003 still occupied.
    echo   Run manually: netstat -ano ^| findstr ":3003"
) else (
    if %KILLED% gtr 0 (
        echo   Port 3003 clear. %KILLED% process^(es^) stopped.
    ) else (
        echo   Port 3003 was already clear. No daemon running.
    )
)

endlocal
