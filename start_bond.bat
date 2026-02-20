@echo off
echo Starting BOND Control Panel...
echo.

cd /d "%~dp0panel"

:: Force rebuild with --rebuild flag
if "%1"=="--rebuild" (
  echo [!] Forcing clean rebuild...
  if exist dist rmdir /s /q dist
  call npx vite build
  echo [OK] Clean rebuild complete.
  echo.
)

:: Check if dist/ exists
if not exist dist (
  echo [!] No dist/ found — building panel...
  call npx vite build
  echo.
)

:: Start Express sidecar (serves API + dist/)
start "BOND Sidecar" /min cmd /c "node server.js"
echo [OK] Sidecar starting on http://localhost:3000

:: Start Search Daemon (requires Python)
where python >nul 2>&1
if %errorlevel%==0 (
  start "BOND Search" /min cmd /c "python "%~dp0search_daemon\bond_search.py""
  echo [OK] Search daemon starting on http://localhost:3003
) else (
  echo [WARN] Python not found — search daemon disabled
  echo        Install Python 3.8+ and add to PATH to enable search
)

:: Dev mode: pass --dev to also launch Vite HMR
if "%1"=="--dev" (
  start "BOND Vite Dev" /min cmd /c "npx vite"
  echo [OK] Vite dev server on http://localhost:5173
  set PANEL_URL=http://localhost:5173
) else (
  set PANEL_URL=http://localhost:3000
)

:: Wait for server to be ready
timeout /t 3 /nobreak >nul

:: Open browser
start %PANEL_URL%
echo [OK] Browser opened — %PANEL_URL%

echo.
echo ========================================
echo    BOND Control Panel is running.
echo    Close this window anytime - servers
echo    run in their own windows (minimized).
echo    Panel:  http://localhost:3000
echo    Search: http://localhost:3003
echo ========================================
echo.
if "%1"=="--dev" (
  echo    Mode: DEVELOPMENT (Vite HMR active)
  echo    Caution: rapid file edits may cause
  echo    browser instability.
) else (
  echo    Mode: PRODUCTION (serving dist/)
  echo    Run with --dev for hot reload.
)
echo.
:: Start AHK Counter Bridge
if exist "%~dp0bridge\BOND_v8.ahk" (
  start "" "%~dp0bridge\BOND_v8.ahk"
  echo [OK] Counter bridge started (BOND_v8.ahk)
) else (
  echo [WARN] AHK counter not found at bridge\BOND_v8.ahk
)
echo.
pause
