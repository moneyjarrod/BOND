# BOND Transfer Pump -- v1 to v2
# Phase B: Pumps personal data into the v2 skeleton
# Copies, never moves. v1 remains functional after transfer.
# Usage: .\transfer_pump.ps1 -V1Path "C:\BOND" -V2Path "C:\BOND_v2"

param(
    [Parameter(Mandatory=$true)]
    [string]$V1Path,
    [Parameter(Mandatory=$true)]
    [string]$V2Path
)

$ErrorActionPreference = "Stop"
$Report = @()
$Warnings = @()
$Errs = @()
$TransferredEntities = @()
$SkippedEntities = @()
$TransferredFiles = 0

function Add-Info($msg) {
    $script:Report += "- $msg"
    Write-Host "  [OK] $msg" -ForegroundColor Green
}
function Add-Warning($msg) {
    $script:Warnings += "- $msg"
    Write-Host "  [WARN] $msg" -ForegroundColor Yellow
}
function Add-Err($msg) {
    $script:Errs += "- $msg"
    Write-Host "  [ERROR] $msg" -ForegroundColor Red
}

# -- T6: BACKUP --
Write-Host ""
Write-Host "  BOND Transfer Pump" -ForegroundColor Yellow
Write-Host "  ====================================" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  [1/6] Creating v1 backup..." -ForegroundColor Cyan

$BackupPath = Join-Path $V2Path "installer\v1_backup"
$BackupTimestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $BackupPath "v1_$BackupTimestamp"

try {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    Copy-Item -Path (Join-Path $V1Path "*") -Destination $BackupDir -Recurse -Force -ErrorAction Stop
    Add-Info "v1 backup created at: $BackupDir"
} catch {
    Add-Err "BACKUP FAILED: $_"
    Write-Host "  TRANSFER ABORTED" -ForegroundColor Red
    exit 1
}

# -- DISCOVERY --
Write-Host ""
Write-Host "  [2/6] Discovering v1 entities..." -ForegroundColor Cyan

$FrameworkEntities = @("BOND_MASTER", "PROJECT_MASTER")
$V1DoctrinePath = Join-Path $V1Path "doctrine"
$V2DoctrinePath = Join-Path $V2Path "doctrine"

if (-not (Test-Path $V1DoctrinePath)) {
    Add-Err "No doctrine directory found at $V1DoctrinePath"
    exit 1
}

$V1Entities = Get-ChildItem -Path $V1DoctrinePath -Directory | Select-Object -ExpandProperty Name

foreach ($entity in $V1Entities) {
    if ($FrameworkEntities -contains $entity) {
        $SkippedEntities += $entity
        Add-Info "Skipping framework entity: $entity"
    }
}

$UserEntities = $V1Entities | Where-Object { $FrameworkEntities -notcontains $_ }
Add-Info "Found $($UserEntities.Count) user entities to transfer"

# -- ENTITY TRANSFER --
Write-Host ""
Write-Host "  [3/6] Transferring entities..." -ForegroundColor Cyan

foreach ($entity in $UserEntities) {
    $SourceDir = Join-Path $V1DoctrinePath $entity
    $DestDir = Join-Path $V2DoctrinePath $entity

    try {
        Copy-Item -Path $SourceDir -Destination $DestDir -Recurse -Force -ErrorAction Stop

        $EntityJson = Join-Path $DestDir "entity.json"
        if (Test-Path $EntityJson) {
            $json = Get-Content $EntityJson -Raw | ConvertFrom-Json

            # T1b: Zero links
            if ($json.PSObject.Properties.Name -contains "links") {
                $originalLinks = $json.links
                $json.links = @()
                if ($originalLinks.Count -gt 0) {
                    Add-Warning "$entity -- cleared $($originalLinks.Count) link(s)"
                }
            }

            # T1a: Ensure v2 fields
            if (-not ($json.PSObject.Properties.Name -contains "display_name")) {
                $json | Add-Member -NotePropertyName "display_name" -NotePropertyValue $entity
                Add-Warning "$entity -- added missing display_name"
            }
            if (-not ($json.PSObject.Properties.Name -contains "public")) {
                $json | Add-Member -NotePropertyName "public" -NotePropertyValue $false
                Add-Warning "$entity -- added missing public field"
            }

            $json | ConvertTo-Json -Depth 10 | Set-Content $EntityJson -Encoding UTF8
        } else {
            Add-Warning "$entity -- no entity.json, creating default"
            $defaultJson = @{ class = "project"; display_name = $entity; public = $false } | ConvertTo-Json -Depth 10
            Set-Content -Path $EntityJson -Value $defaultJson -Encoding UTF8
        }

        # T1c: Ensure state dir
        $EntityState = Join-Path $DestDir "state"
        if (-not (Test-Path $EntityState)) {
            New-Item -ItemType Directory -Path $EntityState -Force | Out-Null
        }

        $TransferredEntities += $entity
        $TransferredFiles += (Get-ChildItem -Path $DestDir -Recurse -File).Count
        Add-Info "Transferred: $entity"
    } catch {
        Add-Err "Failed to transfer $entity -- $_"
    }
}

# -- PERSPECTIVE DATA --
Write-Host ""
Write-Host "  [4/6] Transferring QAIS/perspective data..." -ForegroundColor Cyan

$V1Perspectives = Join-Path $V1Path "data\perspectives"
$V2Perspectives = Join-Path $V2Path "data\perspectives"

if (Test-Path $V1Perspectives) {
    if (-not (Test-Path $V2Perspectives)) {
        New-Item -ItemType Directory -Path $V2Perspectives -Force | Out-Null
    }
    $npzFiles = Get-ChildItem -Path $V1Perspectives -Filter "*.npz"
    foreach ($npz in $npzFiles) {
        try {
            Copy-Item -Path $npz.FullName -Destination (Join-Path $V2Perspectives $npz.Name) -Force
            $TransferredFiles++
            Add-Info "Transferred: $($npz.Name)"
        } catch {
            Add-Err "Failed: $($npz.Name) -- $_"
        }
    }
} else {
    Add-Info "No v1 perspective data found"
}

$SeedDecisions = Join-Path $V1Path "data\seed_decisions.jsonl"
if (Test-Path $SeedDecisions) {
    $V2Data = Join-Path $V2Path "data"
    if (-not (Test-Path $V2Data)) {
        New-Item -ItemType Directory -Path $V2Data -Force | Out-Null
    }
    Copy-Item -Path $SeedDecisions -Destination (Join-Path $V2Data "seed_decisions.jsonl") -Force
    $TransferredFiles++
    Add-Info "Transferred seed_decisions.jsonl"
}

# -- HANDOFFS AND STATE --
Write-Host ""
Write-Host "  [5/6] Transferring handoffs and state..." -ForegroundColor Cyan

$V1Handoffs = Join-Path $V1Path "handoffs"
$V2Handoffs = Join-Path $V2Path "handoffs"

if (Test-Path $V1Handoffs) {
    if (-not (Test-Path $V2Handoffs)) {
        New-Item -ItemType Directory -Path $V2Handoffs -Force | Out-Null
    }
    $handoffFiles = Get-ChildItem -Path $V1Handoffs -File
    foreach ($hf in $handoffFiles) {
        try {
            Copy-Item -Path $hf.FullName -Destination (Join-Path $V2Handoffs $hf.Name) -Force
            $TransferredFiles++
        } catch {
            Add-Err "Failed handoff $($hf.Name) -- $_"
        }
    }
    Add-Info "Transferred $($handoffFiles.Count) handoff file(s)"
} else {
    Add-Info "No v1 handoffs directory found"
}

$V2State = Join-Path $V2Path "state"
if (-not (Test-Path $V2State)) {
    New-Item -ItemType Directory -Path $V2State -Force | Out-Null
}

$V1Heatmap = Join-Path $V1Path "state\heatmap.json"
$V2Heatmap = Join-Path $V2Path "state\heatmap.json"
if (Test-Path $V1Heatmap) {
    Copy-Item -Path $V1Heatmap -Destination $V2Heatmap -Force
    $TransferredFiles++
    Add-Info "Transferred heatmap.json"
}

$V1Config = Join-Path $V1Path "state\config.json"
$V2Config = Join-Path $V2Path "state\config.json"
if (Test-Path $V1Config) {
    $v1Cfg = Get-Content $V1Config -Raw | ConvertFrom-Json
    $v2Cfg = @{ save_confirmation = $true; platform = "windows" }
    if ($v1Cfg.PSObject.Properties.Name -contains "save_confirmation") {
        $v2Cfg.save_confirmation = $v1Cfg.save_confirmation
    }
    if ($v1Cfg.PSObject.Properties.Name -contains "platform") {
        $v2Cfg.platform = $v1Cfg.platform
    }
    $v2Cfg | ConvertTo-Json -Depth 10 | Set-Content $V2Config -Encoding UTF8
    Add-Info "Config merged with v2 schema"
} else {
    Add-Info "No v1 config -- using v2 defaults"
}

$ActiveEntity = Join-Path $V2Path "state\active_entity.json"
'{"entity": null, "path": null}' | Set-Content $ActiveEntity -Encoding UTF8
Add-Info "Active entity reset to null"

# -- T5: PATH HYGIENE --
Write-Host ""
Write-Host "  [6/6] Checking path references..." -ForegroundColor Cyan

$OldPathRefs = @()
$V1PathForward = $V1Path.Replace('\', '/')

foreach ($entity in $TransferredEntities) {
    $EntityDir = Join-Path $V2DoctrinePath $entity
    $files = Get-ChildItem -Path $EntityDir -Recurse -Include "*.md", "*.json" -File
    foreach ($file in $files) {
        $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
        if ($content -and ($content.Contains($V1Path) -or $content.Contains($V1PathForward))) {
            $OldPathRefs += "$entity\$($file.Name)"
        }
    }
}

if ($OldPathRefs.Count -gt 0) {
    Add-Warning "Found $($OldPathRefs.Count) file(s) with old path refs (T5c accepted debt):"
    foreach ($ref in $OldPathRefs) {
        Add-Warning "  -> $ref"
    }
} else {
    Add-Info "No old path references found"
}

# -- REPORT --
$V2Installer = Join-Path $V2Path "installer"
if (-not (Test-Path $V2Installer)) {
    New-Item -ItemType Directory -Path $V2Installer -Force | Out-Null
}
$ReportPath = Join-Path $V2Installer "transfer_report.md"
$TL = ($TransferredEntities | ForEach-Object { "- $_" }) -join "`n"
$SL = ($SkippedEntities | ForEach-Object { "- $_" }) -join "`n"
$AL = ($Report) -join "`n"
$WL = ($Warnings) -join "`n"
$EL = ($Errs) -join "`n"

$R = @()
$R += "# Transfer Report"
$R += ""
$R += "**Timestamp:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$R += "**v1 Source:** $V1Path"
$R += "**v2 Destination:** $V2Path"
$R += "**v1 Backup:** $BackupDir"
$R += ""
$R += "## Summary"
$R += ""
$R += "- Entities transferred: $($TransferredEntities.Count)"
$R += "- Entities skipped: $($SkippedEntities.Count)"
$R += "- Files transferred: $TransferredFiles"
$R += "- Warnings: $($Warnings.Count)"
$R += "- Errors: $($Errs.Count)"
$R += ""
$R += "## Transferred Entities"
$R += ""
$R += $TL
$R += ""
$R += "## Skipped Entities"
$R += ""
$R += $SL
$R += ""
$R += "## Actions"
$R += ""
$R += $AL

if ($Warnings.Count -gt 0) {
    $R += ""
    $R += "## Warnings"
    $R += ""
    $R += $WL
}
if ($Errs.Count -gt 0) {
    $R += ""
    $R += "## Errors"
    $R += ""
    $R += $EL
}

$R += ""
$R += "## Accepted Debt"
$R += ""
$R += "- T5c: Historical v1 path mentions preserved as-is in entity prose."
$R += "- T1b: All link arrays emptied. Re-link deliberately in v2."
$R += ""
$R += "## v1 Status"
$R += ""
$R += "v1 at $V1Path was NOT modified. Transfer copied all data."

Set-Content -Path $ReportPath -Value ($R -join "`n") -Encoding ASCII

# -- SUMMARY --
Write-Host ""
Write-Host "  ====================================" -ForegroundColor DarkGray
Write-Host "  Transfer complete!" -ForegroundColor Green
Write-Host "  ====================================" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Entities: $($TransferredEntities.Count) transferred, $($SkippedEntities.Count) skipped" -ForegroundColor Cyan
Write-Host "  Files:    $TransferredFiles total" -ForegroundColor Cyan
Write-Host "  Warnings: $($Warnings.Count)" -ForegroundColor Cyan
Write-Host "  Errors:   $($Errs.Count)" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Report: $ReportPath" -ForegroundColor DarkGray
Write-Host "  Backup: $BackupDir" -ForegroundColor DarkGray
Write-Host ""

if ($Errs.Count -gt 0) { exit 1 }
exit 0
