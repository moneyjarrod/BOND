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

:: Launch Counter + Clipboard Bridge (if AHK installed)
set "AHK_SCRIPT=%~dp0Counter\BOND_v8.ahk"
if exist "%AHK_SCRIPT%" (
    where autohotkey >nul 2>nul && (
        start "" "%AHK_SCRIPT%"
        echo [OK] Counter + clipboard bridge launched
    ) || (
        echo [WARN] AutoHotkey not found — counter won't run.
        echo        Install from https://www.autohotkey.com
        echo        Then run Counter\BOND_v8.ahk manually.
    )
) else (
    echo [WARN] Counter script not found at Counter\BOND_v8.ahk
)

echo.
echo ========================================
echo    BOND is running.
echo    Close this window anytime — servers
echo    run in their own windows (minimized).
echo ========================================
echo.
pause
