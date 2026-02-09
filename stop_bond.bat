@echo off
echo Stopping BOND...
taskkill /fi "windowtitle eq BOND Sidecar" /f >nul 2>nul
taskkill /fi "windowtitle eq BOND Panel" /f >nul 2>nul
echo [OK] Servers stopped.
timeout /t 2 /nobreak >nul
