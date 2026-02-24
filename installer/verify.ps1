# ================================================================
#  BOND System Verification -- D22
#  14 checks across 4 tiers: prerequisites, services,
#  round-trips, info. Cascade skips on dependency failures.
# ================================================================

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$BOND_ROOT = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$stateDir  = Join-Path $BOND_ROOT 'state'
$tempFile  = Join-Path $stateDir '.verify_test'

# ── Counters ──────────────────────────────────────────────
$pass    = 0
$fail    = 0
$skip    = 0
$total   = 14
$failed  = $false

# ── Cascade flags ─────────────────────────────────────────
$hasNode    = $false
$hasPython  = $false
$panelUp    = $false
$daemonUp   = $false

# ── Output helpers ────────────────────────────────────────
function Write-Pass  ($msg) { Write-Host "  [" -NoNewline; Write-Host ([char]0x2713) -ForegroundColor Green -NoNewline; Write-Host "] $msg"; $script:pass++ }
function Write-Fail  ($msg, $hint) { Write-Host "  [" -NoNewline; Write-Host ([char]0x2717) -ForegroundColor Red -NoNewline; Write-Host "] $msg"; if ($hint) { Write-Host "      -> $hint" -ForegroundColor Red }; $script:fail++; $script:failed = $true }
function Write-Skip  ($msg, $reason) { Write-Host "  [" -NoNewline; Write-Host ([char]0x2014) -ForegroundColor Yellow -NoNewline; Write-Host "] $msg " -NoNewline; Write-Host "(skipped $([char]0x2014) $reason)" -ForegroundColor Yellow; $script:skip++ }
function Write-Info  ($msg) { Write-Host "  $msg" -ForegroundColor Cyan }
function Write-Section ($name) { Write-Host ""; Write-Host "  $name" -ForegroundColor White }

# ══════════════════════════════════════════════════════════
Write-Host ""
Write-Host "  BOND System Verification" -ForegroundColor White
Write-Host "  ========================" -ForegroundColor DarkGray

# ── 1. Prerequisites ─────────────────────────────────────
Write-Section "Prerequisites"

# Check 1: Node.js v18+
try {
    $nodeVer = (node -v 2>$null)
    if ($nodeVer -match 'v(\d+)') {
        $major = [int]$Matches[1]
        if ($major -ge 18) {
            $hasNode = $true
            Write-Pass "Node.js $nodeVer"
        } else {
            Write-Fail "Node.js $nodeVer (below v18)" "Node.js not found or below v18. Install from https://nodejs.org"
        }
    } else {
        Write-Fail "Node.js not detected" "Node.js not found or below v18. Install from https://nodejs.org"
    }
} catch {
    Write-Fail "Node.js not found" "Node.js not found or below v18. Install from https://nodejs.org"
}

# Check 2: Python v3.10+
try {
    $pyRaw = (python --version 2>&1) | Out-String
    if ($pyRaw -match '(\d+)\.(\d+)') {
        $pyMajor = [int]$Matches[1]
        $pyMinor = [int]$Matches[2]
        if ($pyMajor -ge 3 -and $pyMinor -ge 10) {
            $hasPython = $true
            $pyLabel = $pyRaw.Trim()
            Write-Pass $pyLabel
        } else {
            Write-Fail "$($pyRaw.Trim()) (below 3.10)" "Python not found or below 3.10. Install from https://python.org"
        }
    } else {
        Write-Fail "Python not detected" "Python not found or below 3.10. Install from https://python.org"
    }
} catch {
    Write-Fail "Python not found" "Python not found or below 3.10. Install from https://python.org"
}

# Check 3: SKILL.md exists
if (Test-Path (Join-Path $BOND_ROOT 'SKILL.md')) {
    Write-Pass "SKILL.md present"
} else {
    Write-Fail "SKILL.md missing" "SKILL.md not found. Your BOND installation may be incomplete."
}

# Check 4: BOND_MASTER entity
if (Test-Path (Join-Path $BOND_ROOT 'doctrine\BOND_MASTER\entity.json')) {
    Write-Pass "BOND_MASTER entity exists"
} else {
    Write-Fail "BOND_MASTER entity missing" "BOND_MASTER entity missing. Run install_bond.bat to restore."
}

# Check 5: Panel node_modules (depends on Node)
if (-not $hasNode) {
    Write-Skip "Panel dependencies" "Node.js not available"
} elseif (Test-Path (Join-Path $BOND_ROOT 'panel\node_modules')) {
    Write-Pass "Panel dependencies installed"
} else {
    Write-Fail "Panel dependencies missing" "Panel dependencies not installed. Run: cd panel && npm install"
}

# Check 6: Daemon Python dependencies (depends on Python)
if (-not $hasPython) {
    Write-Skip "Daemon dependencies" "Python not available"
} else {
    try {
        $depCheck = python -c "import numpy; import hashlib; print('ok')" 2>&1 | Out-String
        if ($depCheck.Trim() -eq 'ok') {
            Write-Pass "Daemon dependencies installed"
        } else {
            Write-Fail "Daemon dependencies" "Daemon Python dependencies missing. Run: pip install numpy"
        }
    } catch {
        Write-Fail "Daemon dependencies" "Daemon Python dependencies missing. Run: pip install numpy"
    }
}

# ── 2. Services ───────────────────────────────────────────
Write-Section "Services"

# Check 7: Panel on :3000 (depends on Node)
if (-not $hasNode) {
    Write-Skip "Panel sidecar on :3000" "Node.js not available"
} else {
    try {
        $r = Invoke-WebRequest -Uri 'http://localhost:3000/' -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        if ($r.StatusCode -eq 200) {
            $panelUp = $true
            Write-Pass "Panel sidecar on :3000"
        } else {
            Write-Fail "Panel sidecar on :3000" "Panel not responding on port 3000. Run start_bond.bat"
        }
    } catch {
        Write-Fail "Panel sidecar on :3000" "Panel not responding on port 3000. Run start_bond.bat"
    }
}

# Check 7b: Panel build integrity (depends on Node)
if (-not $hasNode) {
    Write-Skip "Panel build integrity" "Node.js not available"
} else {
    $indexHtml = Join-Path $BOND_ROOT 'panel\dist\index.html'
    if (-not (Test-Path $indexHtml)) {
        Write-Fail "Panel build integrity" "Panel build is stale or broken. Run: cd panel && npm run build"
    } else {
        $htmlContent = Get-Content $indexHtml -Raw
        if ($htmlContent -match 'src="/assets/(index-[^"]+\.js)"') {
            $jsFile = $Matches[1]
            $jsPath = Join-Path $BOND_ROOT "panel\dist\assets\$jsFile"
            if (Test-Path $jsPath) {
                Write-Pass "Panel build integrity ($jsFile)"
            } else {
                Write-Fail "Panel build integrity" "Panel build is stale or broken. Run: cd panel && npm run build"
            }
        } else {
            Write-Fail "Panel build integrity" "Panel build is stale or broken. Run: cd panel && npm run build"
        }
    }
}

# Check 8: Daemon on :3003 (depends on Python)
$daemonVersion = $null
if (-not $hasPython) {
    Write-Skip "Daemon on :3003" "Python not available"
} else {
    try {
        $r = Invoke-WebRequest -Uri 'http://localhost:3003/status' -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        if ($r.StatusCode -eq 200) {
            $daemonUp = $true
            $statusJson = $r.Content | ConvertFrom-Json
            Write-Pass "Daemon on :3003 ($($statusJson.entity_count) entities indexed)"
        } else {
            Write-Fail "Daemon on :3003" "Daemon not responding on port 3003. Run start_daemon.bat"
        }
    } catch {
        Write-Fail "Daemon on :3003" "Daemon not responding on port 3003. Run start_daemon.bat"
    }
}

# Check 9: Daemon version via /sync-complete (depends on daemon being up)
if (-not $hasPython) {
    Write-Skip "Daemon version" "Python not available"
} elseif (-not $daemonUp) {
    Write-Skip "Daemon version" "daemon offline"
} else {
    try {
        $vr = Invoke-WebRequest -Uri 'http://localhost:3003/sync-complete' -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        $vrJson = $vr.Content | ConvertFrom-Json
        $daemonVersion = $vrJson.daemon_version
        $expectedVersion = '3.2.0'
        if ($daemonVersion -eq $expectedVersion) {
            Write-Pass "Daemon version $daemonVersion"
        } else {
            Write-Fail "Daemon version mismatch" "Daemon version mismatch. Expected $expectedVersion, got $daemonVersion. Update daemon."
        }
    } catch {
        Write-Fail "Daemon version" "Could not retrieve daemon version. Daemon may need restart."
    }
}

# Check 10: QAIS module importable (depends on Python)
if (-not $hasPython) {
    Write-Skip "QAIS MCP server" "Python not available"
} else {
    try {
        $qaisDir = Join-Path $BOND_ROOT 'QAIS'
        $qaisResult = python -c "import sys; sys.path.insert(0, r'$qaisDir'); import qais_mcp_server; print('ok')" 2>&1 | Out-String
        if ($qaisResult.Trim() -eq 'ok') {
            Write-Pass "QAIS MCP server importable"
        } else {
            Write-Fail "QAIS MCP server" "QAIS module failed to import. Check QAIS/qais_mcp_server.py and Python dependencies."
        }
    } catch {
        Write-Fail "QAIS MCP server" "QAIS module failed to import. Check QAIS/qais_mcp_server.py and Python dependencies."
    }
}

# ── 3. Round-trip Tests ───────────────────────────────────
Write-Section "Round-trip Tests"

# Check 11: /file-op write + read (depends on daemon)
if (-not $hasPython) {
    Write-Skip "/file-op write + read" "Python not available"
} elseif (-not $daemonUp) {
    Write-Skip "/file-op write + read" "daemon offline"
} else {
    try {
        # "BOND verify — ✓ test → pass" built via char codes (PS5.1 encoding-safe)
        $testString = "BOND verify $([char]0x2014) $([char]0x2713) test $([char]0x2192) pass"
        $testPath   = 'state/.verify_test'

        # Write via /file-op
        $writeBody = @{ op = 'write'; path = $testPath; content = $testString; confirmed = $true; initiator = 'verify' } | ConvertTo-Json
        $wr = Invoke-WebRequest -Uri 'http://localhost:3003/file-op' -Method POST -Body ([System.Text.Encoding]::UTF8.GetBytes($writeBody)) -ContentType 'application/json; charset=utf-8' -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop

        # Read back via /read
        $rr = Invoke-WebRequest -Uri "http://localhost:3003/read?path=$testPath" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        $readJson = $rr.Content | ConvertFrom-Json
        $readBack = $readJson.content

        if ($readBack -eq $testString) {
            Write-Pass "/file-op write + read (Unicode round-trip)"
        } else {
            Write-Fail "/file-op write + read" "File operation round-trip failed. Check daemon write permissions and UTF-8 encoding."
        }
    } catch {
        Write-Fail "/file-op write + read" "File operation round-trip failed. Check daemon write permissions and UTF-8 encoding."
    } finally {
        # Always clean up temp file
        if (Test-Path $tempFile) { Remove-Item $tempFile -Force -ErrorAction SilentlyContinue }
    }
}

# Check 12: /sync-complete payload (depends on daemon)
if (-not $hasPython) {
    Write-Skip "/sync-complete payload" "Python not available"
} elseif (-not $daemonUp) {
    Write-Skip "/sync-complete payload" "daemon offline"
} else {
    try {
        $r = Invoke-WebRequest -Uri 'http://localhost:3003/sync-complete' -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        $syncJson = $r.Content | ConvertFrom-Json
        # active_entity field must exist (value may be null on fresh install)
        $hasField = ($null -ne $syncJson.PSObject.Properties.Match('active_entity')) -or ($syncJson.PSObject.Properties.Name -contains 'active_entity')
        if ($hasField) {
            Write-Pass "/sync-complete payload valid"
        } else {
            Write-Fail "/sync-complete payload" "Sync endpoint not returning valid data. Daemon may need restart."
        }
    } catch {
        Write-Fail "/sync-complete payload" "Sync endpoint not returning valid data. Daemon may need restart."
    }
}

# Check 13: Panel proxies to daemon (depends on panel + daemon)
if (-not $hasNode) {
    Write-Skip "Panel -> daemon proxy" "Node.js not available"
} elseif (-not $panelUp) {
    Write-Skip "Panel -> daemon proxy" "panel offline"
} elseif (-not $daemonUp) {
    Write-Skip "Panel -> daemon proxy" "daemon offline"
} else {
    try {
        $r = Invoke-WebRequest -Uri 'http://localhost:3000/api/daemon/status' -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        $proxyJson = $r.Content | ConvertFrom-Json
        if ($proxyJson.online -eq $true) {
            Write-Pass "Panel -> daemon proxy"
        } else {
            Write-Fail "Panel -> daemon proxy" "Panel cannot reach daemon. Check DAEMON_URL in panel config."
        }
    } catch {
        Write-Fail "Panel -> daemon proxy" "Panel cannot reach daemon. Check DAEMON_URL in panel config."
    }
}

# ── 4. Info ───────────────────────────────────────────────
Write-Section "Info"

# A: AHK counter
$ahkFile = Join-Path $env:APPDATA 'BOND\turn_counter.txt'
if (Test-Path $ahkFile) {
    $turnVal = (Get-Content $ahkFile -Raw).Trim()
    Write-Info "AHK counter: found (turn $turnVal)"
} else {
    Write-Info "AHK counter: not found (optional)"
}

# B: Active entity
$aeFile = Join-Path $stateDir 'active_entity.json'
if (Test-Path $aeFile) {
    try {
        $ae = Get-Content $aeFile -Raw | ConvertFrom-Json
        $eName = $ae.name
        if ($eName) {
            Write-Info "Active entity: $eName"
        } else {
            Write-Info "No active entity"
        }
    } catch {
        Write-Info "No active entity"
    }
} else {
    Write-Info "No active entity"
}

# C: Doctrine entity count
$doctrineDir = Join-Path $BOND_ROOT 'doctrine'
if (Test-Path $doctrineDir) {
    $entityCount = (Get-ChildItem $doctrineDir -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'entity.json') }).Count
    Write-Info "Entities: $entityCount"
} else {
    Write-Info "Entities: 0"
}

# D: Git status
try {
    $gitStatus = git -C $BOND_ROOT status --porcelain 2>$null
    if (-not $gitStatus) {
        Write-Info "Git: clean"
    } else {
        $changeCount = ($gitStatus | Measure-Object -Line).Lines
        Write-Info "Git: $changeCount uncommitted changes"
    }
} catch {
    Write-Info "Git: not a repository"
}

# ── Summary ───────────────────────────────────────────────
Write-Host ""
$bar = [string]::new([char]0x2550, 32)
Write-Host "  $bar" -ForegroundColor DarkGray

$parts = @("$pass/$total checks passed.")
if ($fail -gt 0) { $parts += "$fail failed." }
if ($skip -gt 0) { $parts += "$skip skipped." }
$summary = $parts -join ' '

if ($failed) {
    Write-Host "  $summary" -ForegroundColor Red
} else {
    $suffix = if ($skip -gt 0) { $summary } else { "$summary BOND is ready." }
    Write-Host "  $suffix" -ForegroundColor Green
}

Write-Host "  $bar" -ForegroundColor DarkGray
Write-Host ""

if ($failed) { exit 1 } else { exit 0 }
