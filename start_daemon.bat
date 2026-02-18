@echo off
REM BOND Search Daemon Launcher
REM Transition fitting: Panel calls this script, not Python directly.
REM User can run manually if panel coupling fails.

cd /d "%~dp0"

REM Check if port 3003 is already in use
netstat -ano | findstr ":3003 " | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo Daemon already running on port 3003.
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3003 " ^| findstr "LISTENING"') do (
        echo Found PID: %%a
        taskkill /PID %%a /F >nul 2>&1
        echo Killed existing daemon.
    )
    timeout /t 1 /nobreak >nul
)

REM Start daemon in NEW WINDOW so this script can exit
start "BOND Daemon" /min python search_daemon\bond_search.py

echo Started BOND Search Daemon on port 3003.
