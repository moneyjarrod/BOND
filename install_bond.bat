@echo off
echo ========================================
echo    BOND — First Setup
echo ========================================
echo.

:: Check Node.js
where node >nul 2>nul || (
    echo [MISSING] Node.js — Install from https://nodejs.org
    echo.
    pause
    exit /b 1
)
echo [OK] Node.js found

:: Check Python
where python >nul 2>nul || (
    echo [MISSING] Python — Install from https://python.org
    echo          Required for ISS and QAIS MCP servers.
    echo.
    pause
    exit /b 1
)
echo [OK] Python found

:: Check numpy
python -c "import numpy" >nul 2>nul || (
    echo [MISSING] numpy — Installing...
    pip install numpy
)
echo [OK] numpy available

:: Install panel dependencies
echo.
echo Installing panel dependencies...
cd /d "%~dp0panel"
call npm install
echo.
echo [OK] Panel installed

:: Initialize state
if not exist "%~dp0state" mkdir "%~dp0state"
if not exist "%~dp0state\active_entity.json" (
    echo {"entity":null,"class":null,"path":null,"entered":null} > "%~dp0state\active_entity.json"
    echo [OK] State initialized
)

:: Write platform config (efficiency hooks use this)
if not exist "%~dp0state\config.json" (
    echo {"save_confirmation":true,"platform":"windows"} > "%~dp0state\config.json"
    echo [OK] Config initialized (platform: windows)
) else (
    :: Check if platform key exists, add if missing
    findstr /C:"platform" "%~dp0state\config.json" >nul 2>nul || (
        echo [NOTE] Adding platform to existing config...
        echo {"save_confirmation":true,"platform":"windows"} > "%~dp0state\config.json"
        echo [OK] Platform added to config
    )
)

:: Initialize data directory (QAIS field storage)
if not exist "%~dp0data" mkdir "%~dp0data"
echo [OK] Data directory ready

echo.
echo ========================================
echo    Setup complete!
echo    Run start_bond.bat to launch.
echo ========================================
echo.
echo ========================================
echo    IMPORTANT: Counter + Command Bridge
echo ========================================
echo.
echo The BOND counter tracks context freshness
echo and the clipboard bridge connects the panel
echo to Claude. Without it, panel commands won't
echo reach Claude and context will degrade.
echo.
echo Requires: AutoHotkey v1.1+ (https://www.autohotkey.com)
echo Script:   Counter\BOND_v8.ahk
echo.
echo If AutoHotkey is installed, the counter will
echo launch automatically with start_bond.bat.
echo.
pause
