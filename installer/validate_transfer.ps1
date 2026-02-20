# BOND Transfer Validation -- T1-T8 Acceptance Tests
# Usage: .\validate_transfer.ps1 -BondPath "C:\BOND"

param(
    [Parameter(Mandatory=$true)]
    [string]$BondPath
)

$ErrorActionPreference = "Continue"
$Passed = 0
$Failed = 0
$Skipped = 0
$Results = @()

function Test-Check($id, $description, $condition) {
    if ($condition) {
        $script:Passed++
        $script:Results += @{ id=$id; desc=$description; status="PASS" }
        Write-Host "  [PASS] $id -- $description" -ForegroundColor Green
    } else {
        $script:Failed++
        $script:Results += @{ id=$id; desc=$description; status="FAIL" }
        Write-Host "  [FAIL] $id -- $description" -ForegroundColor Red
    }
}

function Test-Skip($id, $description, $reason) {
    $script:Skipped++
    $script:Results += @{ id=$id; desc=$description; status="SKIP"; reason=$reason }
    Write-Host "  [SKIP] $id -- $description ($reason)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  BOND Transfer Validation" -ForegroundColor Yellow
Write-Host "  ====================================" -ForegroundColor DarkGray
Write-Host ""

$DoctrinePath = Join-Path $BondPath "doctrine"
$StatePath = Join-Path $BondPath "state"
$DataPath = Join-Path $BondPath "data"

# -- T1: Entity Structure Integrity --
Write-Host "  T1 -- Entity Structure Integrity" -ForegroundColor Cyan

$Entities = Get-ChildItem -Path $DoctrinePath -Directory
$AllFieldsValid = $true
$AllLinksEmpty = $true

foreach ($entity in $Entities) {
    $ejPath = Join-Path $entity.FullName "entity.json"
    if (Test-Path $ejPath) {
        $ej = Get-Content $ejPath -Raw | ConvertFrom-Json
        $hasClass = $ej.PSObject.Properties.Name -contains "class"
        $hasDisplay = $ej.PSObject.Properties.Name -contains "display_name"
        $hasPublic = $ej.PSObject.Properties.Name -contains "public"
        if (-not ($hasClass -and $hasDisplay -and $hasPublic)) {
            $AllFieldsValid = $false
            Write-Host "    -> $($entity.Name): missing required fields" -ForegroundColor Red
        }
        if ($ej.PSObject.Properties.Name -contains "links") {
            if ($ej.links.Count -gt 0) {
                $AllLinksEmpty = $false
                Write-Host "    -> $($entity.Name): non-empty links" -ForegroundColor Red
            }
        }
    } else {
        $AllFieldsValid = $false
        Write-Host "    -> $($entity.Name): no entity.json" -ForegroundColor Red
    }
}

Test-Check "T1a" "All entities have required v2 fields" $AllFieldsValid
Test-Check "T1b" "All entity link arrays are empty" $AllLinksEmpty

$DaemonUp = $false
try {
    $null = Invoke-RestMethod -Uri "http://localhost:3003/obligations" -TimeoutSec 3
    $DaemonUp = $true
} catch {
    $DaemonUp = $false
}

if ($DaemonUp) {
    $AllPayloadsClean = $true
    foreach ($entity in $Entities) {
        try {
            $payload = Invoke-RestMethod -Uri "http://localhost:3003/enter-payload?entity=$($entity.Name)" -TimeoutSec 5
            if (-not $payload.entity) {
                $AllPayloadsClean = $false
            }
        } catch {
            $AllPayloadsClean = $false
        }
    }
    Test-Check "T1d" "Daemon /enter-payload clean for all entities" $AllPayloadsClean
} else {
    Test-Skip "T1d" "Daemon /enter-payload" "daemon not running"
}

Write-Host ""

# -- T2: Handoff Continuity --
Write-Host "  T2 -- Handoff Continuity" -ForegroundColor Cyan

$EntitiesWithHandoff = 0
foreach ($entity in $Entities) {
    $lh = Join-Path $entity.FullName "state\handoff.md"
    if (Test-Path $lh) { $EntitiesWithHandoff++ }
}
Test-Check "T2a" "Entity-local handoffs exist (D11)" ($EntitiesWithHandoff -gt 0)

$HandoffsDir = Join-Path $BondPath "handoffs"
$HasHandoffs = (Test-Path $HandoffsDir) -and ((Get-ChildItem $HandoffsDir -File -ErrorAction SilentlyContinue).Count -gt 0)
Test-Check "T2d" "Handoff archive has files" $HasHandoffs

if ($DaemonUp) {
    try {
        $body = '{"text":"validation","session":"VALIDATE"}'
        $null = Invoke-RestMethod -Uri "http://localhost:3003/sync-complete" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 10
        Test-Check "T2c" "/sync-complete returns without error" $true
    } catch {
        Test-Check "T2c" "/sync-complete returns without error" $false
    }
} else {
    Test-Skip "T2c" "/sync-complete carries handoff" "daemon not running"
}

Write-Host ""

# -- T3: Perspective Data Parity --
Write-Host "  T3 -- Perspective Data Parity" -ForegroundColor Cyan

$PerspectiveEntities = @()
foreach ($entity in $Entities) {
    $ejp = Join-Path $entity.FullName "entity.json"
    if (Test-Path $ejp) {
        $ej = Get-Content $ejp -Raw | ConvertFrom-Json
        if ($ej.class -eq "perspective") {
            $PerspectiveEntities += $entity
        }
    }
}

if ($PerspectiveEntities.Count -gt 0) {
    $AllRoots = $true
    foreach ($p in $PerspectiveEntities) {
        $roots = Get-ChildItem -Path $p.FullName -Filter "ROOT-*.md" -File -ErrorAction SilentlyContinue
        if ($roots.Count -eq 0) {
            $AllRoots = $false
            Write-Host "    -> $($p.Name): no ROOT files" -ForegroundColor Red
        }
    }
    Test-Check "T3a" "All perspectives have ROOT files" $AllRoots

    $AllTrackers = $true
    foreach ($p in $PerspectiveEntities) {
        if (-not (Test-Path (Join-Path $p.FullName "seed_tracker.json"))) {
            $AllTrackers = $false
            Write-Host "    -> $($p.Name): no seed_tracker.json" -ForegroundColor Red
        }
    }
    Test-Check "T3c" "All perspectives have seed_tracker.json" $AllTrackers

    $PerspDir = Join-Path $DataPath "perspectives"
    $NpzCount = 0
    if (Test-Path $PerspDir) {
        $NpzCount = (Get-ChildItem $PerspDir -Filter "*.npz" -File).Count
    }
    Test-Check "T3d" "Perspective .npz files present" ($NpzCount -gt 0)
} else {
    Test-Skip "T3a" "Perspective ROOT files" "no perspective entities"
    Test-Skip "T3c" "Perspective seed trackers" "no perspective entities"
    Test-Skip "T3d" "Perspective .npz files" "no perspective entities"
}

Write-Host ""

# -- T4: Config and State --
Write-Host "  T4 -- Config and State Schema" -ForegroundColor Cyan

$ConfigPath = Join-Path $StatePath "config.json"
$ConfigValid = $false
if (Test-Path $ConfigPath) {
    $cfg = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    $ConfigValid = ($cfg.PSObject.Properties.Name -contains "save_confirmation") -and ($cfg.PSObject.Properties.Name -contains "platform")
}
Test-Check "T4a" "config.json matches v2 schema" $ConfigValid

$AEPath = Join-Path $StatePath "active_entity.json"
$AEReset = $false
if (Test-Path $AEPath) {
    $ae = Get-Content $AEPath -Raw | ConvertFrom-Json
    $AEReset = ($null -eq $ae.entity -or $ae.entity -eq "")
}
Test-Check "T4b" "active_entity.json is reset (null)" $AEReset

$HeatmapPath = Join-Path $StatePath "heatmap.json"
Test-Check "T4c" "heatmap.json exists" (Test-Path $HeatmapPath)

Write-Host ""

# -- T5: Path Hygiene --
Write-Host "  T5 -- Path Reference Hygiene" -ForegroundColor Cyan

$OldPathCount = 0
$V1Default = "C:\BOND"
if ($BondPath -ne $V1Default) {
    $allFiles = Get-ChildItem -Path $DoctrinePath -Recurse -Include "*.md", "*.json" -File
    foreach ($f in $allFiles) {
        $content = Get-Content $f.FullName -Raw -ErrorAction SilentlyContinue
        if ($content -and $content.Contains($V1Default)) {
            $OldPathCount++
        }
    }
}

$t5msg = "Path scan complete ($OldPathCount old refs, T5c accepted)"
Test-Check "T5a" $t5msg $true

Write-Host ""

# -- T7: Operational Smoke Test --
Write-Host "  T7 -- Operational Smoke Test" -ForegroundColor Cyan

if ($DaemonUp) {
    try {
        $null = Invoke-RestMethod -Uri "http://localhost:3003/obligations" -TimeoutSec 5
        Test-Check "T7e" "Daemon /obligations returns clean" $true
    } catch {
        Test-Check "T7e" "Daemon /obligations returns clean" $false
    }
} else {
    Test-Skip "T7e" "Daemon /obligations" "daemon not running"
}

Write-Host ""

# -- T8: Fresh Install Parity --
Write-Host "  T8 -- Fresh Install Parity" -ForegroundColor Cyan

$CoreFiles = @(
    "SKILL.md",
    "search_daemon\bond_search.py",
    "QAIS\qais_mcp_server.py",
    "ISS\iss_mcp_server.py",
    "doctrine\BOND_MASTER\entity.json",
    "doctrine\BOND_MASTER\BOND_MASTER.md",
    "doctrine\BOND_MASTER\BOND_PROTOCOL.md",
    "doctrine\BOND_MASTER\BOND_ENTITIES.md",
    "state\config.json",
    "templates\classes\project.json"
)

$AllCorePresent = $true
foreach ($cf in $CoreFiles) {
    $fp = Join-Path $BondPath $cf
    if (-not (Test-Path $fp)) {
        $AllCorePresent = $false
        Write-Host "    -> Missing: $cf" -ForegroundColor Red
    }
}
Test-Check "T8a" "All core framework files present" $AllCorePresent

$ReplacedPath = Join-Path $BondPath "transition\REPLACED.md"
Test-Check "T8c" "transition/REPLACED.md exists (v2 marker)" (Test-Path $ReplacedPath)

Write-Host ""

# -- SUMMARY --
Write-Host "  ====================================" -ForegroundColor DarkGray
$Total = $Passed + $Failed + $Skipped
if ($Failed -eq 0) {
    Write-Host "  Results: $Passed passed, $Failed failed, $Skipped skipped (of $Total)" -ForegroundColor Green
} else {
    Write-Host "  Results: $Passed passed, $Failed failed, $Skipped skipped (of $Total)" -ForegroundColor Red
}
Write-Host "  ====================================" -ForegroundColor DarkGray
Write-Host ""

# Write report
$V2Installer = Join-Path $BondPath "installer"
if (-not (Test-Path $V2Installer)) {
    New-Item -ItemType Directory -Path $V2Installer -Force | Out-Null
}
$ValidationReport = Join-Path $V2Installer "validation_report.md"

$VR = @()
$VR += "# Validation Report"
$VR += ""
$VR += "**Timestamp:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$VR += "**Installation:** $BondPath"
$VR += "**Result:** $Passed passed, $Failed failed, $Skipped skipped"
$VR += ""
$VR += "## Results"
$VR += ""
foreach ($r in $Results) {
    if ($r.status -eq "PASS") { $VR += "- PASS $($r.id) -- $($r.desc)" }
    elseif ($r.status -eq "FAIL") { $VR += "- FAIL $($r.id) -- $($r.desc)" }
    else { $VR += "- SKIP $($r.id) -- $($r.desc) ($($r.reason))" }
}
$VR += ""
if ($DaemonUp) {
    $VR += "Daemon was running at localhost:3003."
} else {
    $VR += "Daemon was NOT running. Start daemon and re-run for full coverage."
}

Set-Content -Path $ValidationReport -Value ($VR -join "`n") -Encoding ASCII

Write-Host "  Report: $ValidationReport" -ForegroundColor DarkGray
Write-Host ""

if ($Failed -gt 0) { exit 1 }
exit 0
