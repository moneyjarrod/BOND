# PowerShell Installation Script for BOND
# Usage: irm https://moneyjarrod.github.io/BOND/install.ps1 | iex

try {

# Allow scripts to run in this session (needed for npm.ps1 wrapper)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force 2>$null

Write-Host ""
Write-Host "  BOND Installer" -ForegroundColor Yellow
Write-Host "  ====================================" -ForegroundColor DarkGray
Write-Host ""

$BOND_ROOT = "C:\BOND"
$BOND_PORT = 3000

# ─── Prerequisites ────────────────────────────────
Write-Host "[1/5] Checking prerequisites..." -ForegroundColor Cyan
Write-Host ""

# Check Git
try { $null = Get-Command git -ErrorAction Stop; Write-Host "   [OK] Git" -ForegroundColor Green }
catch {
    Write-Host "   [MISSING] Git" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Git is required. Install it from:" -ForegroundColor Yellow
    Write-Host "   https://git-scm.com/download/win" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   After installing Git, close this window and run the install command again." -ForegroundColor Yellow
    Write-Host ""; Read-Host "Press Enter to exit"; exit 1
}

# Check Node
try { $null = Get-Command node -ErrorAction Stop; Write-Host "   [OK] Node.js" -ForegroundColor Green }
catch {
    Write-Host "   [MISSING] Node.js" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Node.js is required. Install it from:" -ForegroundColor Yellow
    Write-Host "   https://nodejs.org (pick the LTS version)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   After installing Node.js, close this window and run the install command again." -ForegroundColor Yellow
    Write-Host ""; Read-Host "Press Enter to exit"; exit 1
}

# Check Python
try { $null = Get-Command python -ErrorAction Stop; Write-Host "   [OK] Python" -ForegroundColor Green }
catch {
    Write-Host "   [MISSING] Python" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Python is required for QAIS and ISS. Install it from:" -ForegroundColor Yellow
    Write-Host "   https://python.org (check 'Add to PATH' during install)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   After installing Python, close this window and run the install command again." -ForegroundColor Yellow
    Write-Host ""; Read-Host "Press Enter to exit"; exit 1
}

# Check numpy
$numpyCheck = python -c "import numpy" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   Installing numpy..." -ForegroundColor Yellow
    pip.cmd install numpy 2>&1 | Out-Null
}
Write-Host "   [OK] numpy" -ForegroundColor Green

Write-Host ""

# ─── Clone Repository ─────────────────────────────
Write-Host "[2/5] Downloading BOND..." -ForegroundColor Cyan
Write-Host ""

if (Test-Path "$BOND_ROOT\.git") {
    Write-Host "   BOND already installed at $BOND_ROOT" -ForegroundColor Yellow
    Write-Host "   Updating to latest version..." -ForegroundColor Yellow
    Push-Location $BOND_ROOT
    git pull 2>&1 | Out-Null
    Pop-Location
} else {
    $cloneOutput = git clone https://github.com/moneyjarrod/BOND.git $BOND_ROOT 2>&1
    foreach ($line in $cloneOutput) { Write-Host "   $line" -ForegroundColor DarkGray }
    if (-not (Test-Path "$BOND_ROOT\panel")) {
        Write-Host ""
        Write-Host "   [ERROR] Download failed. Check your internet connection." -ForegroundColor Red
        Write-Host ""; Read-Host "Press Enter to exit"; exit 1
    }
}
Write-Host "   [OK] BOND downloaded" -ForegroundColor Green
Write-Host ""

# ─── Install Dependencies ─────────────────────────
Write-Host "[3/5] Installing dependencies..." -ForegroundColor Cyan
Write-Host ""

Push-Location "$BOND_ROOT\panel"
npm.cmd install 2>&1 | ForEach-Object { Write-Host "   $_" -ForegroundColor DarkGray }
Pop-Location

# Create data directory
if (-not (Test-Path "$BOND_ROOT\data")) { New-Item -ItemType Directory -Path "$BOND_ROOT\data" | Out-Null }

Write-Host "   [OK] Dependencies installed" -ForegroundColor Green
Write-Host ""

# ─── Clear Port ───────────────────────────────────
Write-Host "[4/5] Preparing to start..." -ForegroundColor Cyan
Write-Host ""

$portListeners = netstat -ano | Select-String ":$BOND_PORT\s" | Select-String "LISTENING"
foreach ($line in $portListeners) {
    $parts = $line -split '\s+'
    $pid = $parts[$parts.Count - 1]
    if ($pid -and $pid -match '^\d+$') {
        Write-Host "   Clearing port $BOND_PORT (PID: $pid)..." -ForegroundColor Yellow
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
}
Write-Host "   [OK] Port $BOND_PORT clear" -ForegroundColor Green
Write-Host ""

# ─── Start Server ─────────────────────────────────
Write-Host "[5/5] Starting BOND..." -ForegroundColor Cyan
Write-Host ""

# Start sidecar using cmd (avoids PowerShell execution policy issues)
Start-Process cmd -ArgumentList "/c cd /d `"$BOND_ROOT\panel`" && node server.js" -WindowStyle Minimized
Write-Host "   [OK] Server starting..." -ForegroundColor Green

# Check for production build
if (Test-Path "$BOND_ROOT\panel\dist\index.html") {
    Write-Host "   [OK] Serving production build" -ForegroundColor Green
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:$BOND_PORT"
} else {
    Start-Process cmd -ArgumentList "/c cd /d `"$BOND_ROOT\panel`" && npx vite" -WindowStyle Minimized
    Write-Host "   [OK] Dev server starting..." -ForegroundColor Green
    Start-Sleep -Seconds 5
    Start-Process "http://localhost:5173"
}

Write-Host ""
Write-Host "  ====================================" -ForegroundColor DarkGray
Write-Host "  BOND is running!" -ForegroundColor Green
Write-Host "  ====================================" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Panel:   http://localhost:$BOND_PORT" -ForegroundColor Cyan
Write-Host "  Stop:    $BOND_ROOT\stop_bond.bat" -ForegroundColor DarkGray
Write-Host "  Counter: $BOND_ROOT\Counter\BOND_v8.ahk" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Next: Add the BOND skill to a Claude Project," -ForegroundColor Yellow
Write-Host "  configure MCP servers, then type {Sync}" -ForegroundColor Yellow
Write-Host ""

} catch {
    Write-Host ""
    Write-Host "  [ERROR] Something went wrong: $_" -ForegroundColor Red
    Write-Host "  Please report this at: https://github.com/moneyjarrod/BOND/issues" -ForegroundColor Yellow
    Write-Host ""
}
