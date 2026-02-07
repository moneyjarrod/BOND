@echo off
:: BOND Panel — Unified Startup
:: Starts the Express sidecar (serves API + built panel if dist/ exists)
:: Run from BOND_private\panel\ or set BOND_PANEL_PATH

cd /d "%~dp0"

:: Load .env if present
if exist .env (
  for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
    if not "%%a"=="" if not "%%a:~0,1%"=="#" set "%%a=%%b"
  )
)

echo 🔥🌊 Starting BOND Panel...
echo    Working dir: %cd%

:: Check node_modules
if not exist node_modules (
  echo    Installing dependencies...
  npm install
)

:: Start sidecar
node server.js
