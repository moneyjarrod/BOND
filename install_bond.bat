@echo off
echo ========================================
echo    BOND Control Panel - First Setup
echo ========================================
echo.

:: Get BOND root (parent of this script's directory)
set "BOND_ROOT=%~dp0"
:: Remove trailing backslash
if "%BOND_ROOT:~-1%"=="\" set "BOND_ROOT=%BOND_ROOT:~0,-1%"

:: ── Check Node.js ─────────────────────────
where node >nul 2>nul || (
    echo [MISSING] Node.js - Install from https://nodejs.org
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('node -v') do set NODE_VER=%%v
echo [OK] Node.js %NODE_VER%

:: ── Check Python ──────────────────────────
where python >nul 2>nul || (
    echo [MISSING] Python 3.8+ - Install from https://python.org
    echo          Required for: search daemon, QAIS, ISS
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [OK] %PY_VER%

:: ── Check numpy ───────────────────────────
python -c "import numpy" >nul 2>nul || (
    echo [MISSING] numpy - Installing...
    pip install numpy --break-system-packages >nul 2>nul || pip install numpy >nul 2>nul
    python -c "import numpy" >nul 2>nul || (
        echo [FAILED] Could not install numpy. Run: pip install numpy
        echo.
        pause
        exit /b 1
    )
)
echo [OK] numpy

:: ── Install panel dependencies ────────────
echo.
echo Installing panel dependencies...
cd /d "%BOND_ROOT%\panel"
call npm install
echo.
echo [OK] Panel installed

:: ── Initialize .env ───────────────────────
cd /d "%BOND_ROOT%"
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [OK] .env initialized from .env.example
    )
) else (
    echo [OK] .env already exists
)

:: ── MCP Configuration Check ───────────────
echo.
echo ── MCP Configuration ──────────────────
echo.
echo Claude Desktop needs MCP server paths in its config.
echo.
echo Config location (check both):
echo   %%APPDATA%%\Claude\claude_desktop_config.json
echo   %%LOCALAPPDATA%%\AnthropicClaude\claude_desktop_config.json
echo.
echo Required MCP entries (add to "mcpServers"):
echo.
echo   "qais": {
echo     "command": "python",
echo     "args": ["%BOND_ROOT%\QAIS\qais_mcp_server.py"],
echo     "env": { "BOND_ROOT": "%BOND_ROOT%" }
echo   },
echo   "iss": {
echo     "command": "python",
echo     "args": ["%BOND_ROOT%\ISS\iss_mcp_server.py"],
echo     "env": { "BOND_ROOT": "%BOND_ROOT%" }
echo   }
echo.

:: ── Summary ───────────────────────────────
echo ========================================
echo    Setup complete!
echo.
echo    Next steps:
echo    1. Add MCP config above (if not done)
echo    2. Restart Claude Desktop
echo    3. Double-click start_bond.bat to launch
echo ========================================
pause
