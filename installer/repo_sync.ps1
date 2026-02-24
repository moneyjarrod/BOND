# BOND v2 Repo Sync: BOND_parallel -> BOND_github
# Run this to prepare the GitHub repo for push

$src = "C:\Projects\BOND_parallel"
$dst = "C:\Projects\BOND_github"

Write-Host "`n  BOND Repo Sync (parallel -> github)" -ForegroundColor Cyan
Write-Host "  ====================================" -ForegroundColor Cyan

# --- Root files ---
Write-Host "`n  [1/9] Root files..."
$rootFiles = @("README.md", "GETTING_STARTED.md", "SKILL.md", "CHANGELOG.md", "start_bond.bat", "stop_bond.bat", "start_daemon.bat", "start_daemon.sh", "stop_daemon.bat", "warm_restore.py", "install_bond.bat", "verify_bond.bat")
foreach ($f in $rootFiles) {
    $s = Join-Path $src $f
    if (Test-Path $s) {
        Copy-Item $s (Join-Path $dst $f) -Force
        Write-Host "    [OK] $f" -ForegroundColor Green
    } else {
        Write-Host "    [SKIP] $f (not found)" -ForegroundColor Yellow
    }
}

# --- Framework directories (full replace) ---
Write-Host "`n  [2/9] Framework directories..."
$frameworkDirs = @("search_daemon", "QAIS", "ISS", "templates", "docs")
foreach ($d in $frameworkDirs) {
    $s = Join-Path $src $d
    $dd = Join-Path $dst $d
    if (Test-Path $s) {
        if (Test-Path $dd) { Remove-Item $dd -Recurse -Force }
        Copy-Item $s $dd -Recurse -Force
        Write-Host "    [OK] $d/" -ForegroundColor Green
    }
}

# --- Doctrine (public entities only) ---
Write-Host "`n  [3/9] Doctrine (public entities)..."
$docDst = Join-Path $dst "doctrine"
if (-not (Test-Path $docDst)) { New-Item -ItemType Directory -Path $docDst -Force | Out-Null }
$docSrc = Join-Path $src "doctrine"
Get-ChildItem $docSrc -Directory | ForEach-Object {
    $entityJson = Join-Path $_.FullName "entity.json"
    if (Test-Path $entityJson) {
        $meta = Get-Content $entityJson -Raw | ConvertFrom-Json
        if ($meta.public -eq $true) {
            $dd = Join-Path $docDst $_.Name
            if (Test-Path $dd) { Remove-Item $dd -Recurse -Force }
            Copy-Item $_.FullName $dd -Recurse -Force
            # Strip state/ from public copy (personal session data)
            $stateDir = Join-Path $dd "state"
            if (Test-Path $stateDir) { Remove-Item $stateDir -Recurse -Force }
            Write-Host "    [OK] doctrine/$($_.Name)/ (public)" -ForegroundColor Green
        }
    }
}

# --- New v2 directories ---
Write-Host "`n  [4/9] New v2 directories..."
foreach ($d in @("transition", "platforms", "bridge")) {
    $s = Join-Path $src $d
    $dd = Join-Path $dst $d
    if (Test-Path $s) {
        if (Test-Path $dd) { Remove-Item $dd -Recurse -Force }
        Copy-Item $s $dd -Recurse -Force
        Write-Host "    [OK] $d/" -ForegroundColor Green
    }
}

# --- Installer (scripts only, no personal artifacts) ---
Write-Host "`n  [5/9] Installer..."
$instDst = Join-Path $dst "installer"
if (-not (Test-Path $instDst)) { New-Item -ItemType Directory -Path $instDst -Force | Out-Null }
foreach ($f in @("Install-BOND.ps1", "transfer_pump.ps1", "validate_transfer.ps1", "verify.ps1", "repo_sync.ps1")) {
    $s = Join-Path $src "installer\$f"
    if (Test-Path $s) {
        Copy-Item $s (Join-Path $instDst $f) -Force
        Write-Host "    [OK] installer/$f" -ForegroundColor Green
    }
}
# Include compiled .exe
$outDir = Join-Path $instDst "output"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$exeSrc = Join-Path $src "installer\output\BOND_Setup.exe"
if (Test-Path $exeSrc) {
    Copy-Item $exeSrc (Join-Path $outDir "BOND_Setup.exe") -Force
    Write-Host "    [OK] installer/output/BOND_Setup.exe" -ForegroundColor Green
}

# --- Data (framework only) ---
Write-Host "`n  [6/9] Data (framework only)..."
$dataDst = Join-Path $dst "data"
if (-not (Test-Path $dataDst)) { New-Item -ItemType Directory -Path $dataDst -Force | Out-Null }
$dataFiles = @("iss_projections.npz", "iss_projections_st.npz")
foreach ($f in $dataFiles) {
    $s = Join-Path $src "data\$f"
    if (Test-Path $s) {
        Copy-Item $s (Join-Path $dataDst $f) -Force
        Write-Host "    [OK] data/$f" -ForegroundColor Green
    }
}

# --- Panel (minus node_modules) ---
Write-Host "`n  [7/9] Panel..."
$panelSrc = Join-Path $src "panel"
$panelDst = Join-Path $dst "panel"
if (Test-Path $panelSrc) {
    if (Test-Path $panelDst) { Remove-Item $panelDst -Recurse -Force }
    Copy-Item $panelSrc $panelDst -Recurse -Force
    $nm = Join-Path $panelDst "node_modules"
    if (Test-Path $nm) { Remove-Item $nm -Recurse -Force }
    Write-Host "    [OK] panel/ (node_modules excluded)" -ForegroundColor Green
    # Remove dev-only cards (keep user-facing cards only)
    $devCards = @("repo-sync.json", "entity-delete.json", "file-delete.json")
    foreach ($c in $devCards) {
        $cardPath = Join-Path $panelDst "powershell\cards\$c"
        if (Test-Path $cardPath) {
            Remove-Item $cardPath -Force
            Write-Host "    [OK] Removed dev card: $c" -ForegroundColor Green
        }
    }
    # Clear personal audit trail (keep empty file for daemon)
    $execLog = Join-Path $panelDst "powershell\exec_log.jsonl"
    if (Test-Path $execLog) {
        Set-Content $execLog "" -Encoding ASCII
        Write-Host "    [OK] powershell/exec_log.jsonl cleared" -ForegroundColor Green
    }
}

# --- Starters (Gift Pack) ---
Write-Host "`n  [8/9] Starters..."
$starterSrc = Join-Path $src "starters"
$starterDst = Join-Path $dst "starters"
if (Test-Path $starterSrc) {
    if (Test-Path $starterDst) { Remove-Item $starterDst -Recurse -Force }
    Copy-Item $starterSrc $starterDst -Recurse -Force
    Write-Host "    [OK] starters/" -ForegroundColor Green
}

# --- State (clean defaults only) ---
Write-Host "`n  [9/9] State defaults..."
$stateDst = Join-Path $dst "state"
if (-not (Test-Path $stateDst)) { New-Item -ItemType Directory -Path $stateDst -Force | Out-Null }
'{"save_confirmation": true, "platform": "windows"}' | Set-Content (Join-Path $stateDst "config.json") -Encoding ASCII
Write-Host "    [OK] state/config.json (default)" -ForegroundColor Green

# --- Cleanup v1-only ---
Write-Host "`n  Cleaning v1-only artifacts..."
$v1Only = @("Counter", "skills")
foreach ($d in $v1Only) {
    $dd = Join-Path $dst $d
    if (Test-Path $dd) {
        Remove-Item $dd -Recurse -Force
        Write-Host "    [REMOVED] $d/ (replaced in v2)" -ForegroundColor Yellow
    }
}

Write-Host "`n  ====================================" -ForegroundColor Cyan
Write-Host "  Repo sync complete!" -ForegroundColor Cyan
Write-Host "  Open GitHub Desktop to review changes and push." -ForegroundColor Cyan
Write-Host ""
