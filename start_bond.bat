@echo off
echo Starting BOND...
echo.

:: Start Express sidecar
cd /d "%~dp0panel"
start "BOND Sidecar" /min cmd /c "node server.js"
echo [OK] Sidecar starting on http://localhost:3000

:: Check if production build exists
if exist "%~dp0panel\dist\index.html" (
    echo [OK] Serving production build from dist/
    timeout /t 2 /nobreak >nul
    start http://localhost:3000
) else (
    :: Dev mode — start Vite
    start "BOND Panel" /min cmd /c "npx vite"
    echo [OK] Dev server starting on http://localhost:5173
    timeout /t 3 /nobreak >nul
    start http://localhost:5173
)

echo.
echo ========================================
echo    BOND is running.
echo    Close this window anytime — servers
echo    run in their own windows (minimized).
echo ========================================
echo.
echo Optional: Run Counter\BOND_v8.ahk
echo for counter + command bridge.
echo.
pause
