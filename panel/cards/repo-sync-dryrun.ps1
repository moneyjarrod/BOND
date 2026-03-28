# BOND Repo Sync Dry Run — Hash-Based Comparison
# Compares BOND_parallel → BOND_github using file content hashes
# instead of timestamps (eliminates false positives from resaved files).
#
# Usage: powershell -File repo-sync-dryrun.ps1
# Or paste directly into PowerShell.

$src = 'C:\Projects\BOND_parallel'
$dst = 'C:\Projects\BOND_github'
$results = @()
$skipped = @()

# --- Root files (framework top-level) ---
$rootFiles = @(
    'README.md', 'GETTING_STARTED.md', 'SKILL.md', 'CHANGELOG.md',
    'start_bond.bat', 'stop_bond.bat', 'start_daemon.bat',
    'start_daemon.sh', 'stop_daemon.bat', 'stop_daemon.sh', 'warm_restore.py', 'install_bond.bat', 'verify_bond.bat'
)
foreach ($f in $rootFiles) {
    $s = Join-Path $src $f
    $d = Join-Path $dst $f
    if (Test-Path $s) {
        if (-not (Test-Path $d)) {
            $results += "[NEW]      $f"
        } elseif ((Get-FileHash $s).Hash -ne (Get-FileHash $d).Hash) {
            $results += "[MODIFIED] $f"
        }
    }
}

# --- Framework directories (non-doctrine code) ---
$frameworkDirs = @('search_daemon', 'QAIS', 'ISS', 'templates', 'docs')
foreach ($dir in $frameworkDirs) {
    $sDir = Join-Path $src $dir
    if (Test-Path $sDir) {
        Get-ChildItem $sDir -Recurse -File | ForEach-Object {
            $rel = $_.FullName.Substring($src.Length + 1)
            $dPath = Join-Path $dst $rel
            if (-not (Test-Path $dPath)) {
                $results += "[NEW]      $rel"
            } elseif ((Get-FileHash $_.FullName).Hash -ne (Get-FileHash $dPath).Hash) {
                $results += "[MODIFIED] $rel"
            }
        }
    }
}

# --- Doctrine (public entities only, skip state/ subdirs) ---
$docSrc = Join-Path $src 'doctrine'
Get-ChildItem $docSrc -Directory | ForEach-Object {
    $ej = Join-Path $_.FullName 'entity.json'
    if (Test-Path $ej) {
        $meta = Get-Content $ej -Raw | ConvertFrom-Json
        if ($meta.public -eq $true) {
            Get-ChildItem $_.FullName -Recurse -File |
                Where-Object { $_.FullName -notlike '*\state\*' } |
                ForEach-Object {
                    $rel = $_.FullName.Substring($src.Length + 1)
                    $dPath = Join-Path $dst $rel
                    if (-not (Test-Path $dPath)) {
                        $results += "[NEW]      $rel"
                    } elseif ((Get-FileHash $_.FullName).Hash -ne (Get-FileHash $dPath).Hash) {
                        $results += "[MODIFIED] $rel"
                    }
                }
        } else {
            $skipped += $_.Name
        }
    }
}

# --- Panel (skip node_modules, exec log, restricted cards) ---
$panelSrc = Join-Path $src 'panel'
if (Test-Path $panelSrc) {
    $blockedCards = @('repo-sync.json', 'entity-delete.json', 'file-delete.json')
    Get-ChildItem $panelSrc -Recurse -File |
        Where-Object {
            $_.FullName -notlike '*node_modules*' -and
            $_.Name -ne 'exec_log.jsonl' -and
            $_.Name -notin $blockedCards
        } |
        ForEach-Object {
            $rel = $_.FullName.Substring($src.Length + 1)
            $dPath = Join-Path $dst $rel
            if (-not (Test-Path $dPath)) {
                $results += "[NEW]      $rel"
            } elseif ((Get-FileHash $_.FullName).Hash -ne (Get-FileHash $dPath).Hash) {
                $results += "[MODIFIED] $rel"
            }
        }
}

# --- Report ---
Write-Host ""
Write-Host "BOND Repo Sync Dry Run (hash-based)" -ForegroundColor Cyan
Write-Host "Source: $src"
Write-Host "Target: $dst"
Write-Host ""

if ($results.Count -eq 0) {
    Write-Host "No changes detected. Repos are content-identical." -ForegroundColor Green
} else {
    Write-Host "$($results.Count) file(s) would be synced:" -ForegroundColor Yellow
    $results | ForEach-Object { Write-Host "  $_" }
}

if ($skipped.Count -gt 0) {
    Write-Host ""
    Write-Host "Skipped (private entities): $($skipped -join ', ')" -ForegroundColor DarkGray
}
