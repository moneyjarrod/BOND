@echo off
REM BOND Search Daemon — Force Stop (PowerShell method)
REM Tries multiple methods to kill port 3003

echo === Method 1: PowerShell ===
powershell -Command "Get-NetTCPConnection -LocalPort 3003 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force; Write-Host ('Killed PID: ' + $_.OwningProcess) }"

echo === Method 2: Kill all python ===
taskkill /IM python.exe /F 2>nul
taskkill /IM python3.exe /F 2>nul
taskkill /IM pythonw.exe /F 2>nul

echo === Checking port 3003 ===
netstat -ano | findstr ":3003"

echo.
echo If lines appeared above, the port is still held.
echo If nothing appeared, daemon is dead.
pause
