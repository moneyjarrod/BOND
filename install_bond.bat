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

:: Initialize data directory (QAIS field storage)
if not exist "%~dp0data" mkdir "%~dp0data"
echo [OK] Data directory ready

echo.
echo ========================================
echo    Setup complete!
echo    Run start_bond.bat to launch.
echo ========================================
echo.
echo Optional: Run bridge\BOND_v8.ahk for
echo counter + command bridge (Windows).
echo.
pause
