# BOND Entity Export — Combine all .md files from entity into single export
# Verb: execute | Scope: entity
# Usage: powershell -File entity_export.ps1 -EntityPath <path> -BondRoot <path>

param(
    [Parameter(Mandatory=$true)][string]$EntityPath,
    [Parameter(Mandatory=$true)][string]$BondRoot
)

$ts = Get-Date -Format 'yyyy-MM-dd_HHmmss'
$entity = Split-Path $EntityPath -Leaf
$bkDir = Join-Path $BondRoot 'backups'
if (-not (Test-Path $bkDir)) { New-Item -ItemType Directory -Path $bkDir -Force | Out-Null }

$out = Join-Path $bkDir "${entity}_export_$ts.md"
$files = Get-ChildItem $EntityPath -Filter '*.md'

$content = @("# $entity - Export ($ts)", '')
foreach ($f in $files) {
    $content += "## $($f.Name)", '', (Get-Content $f.FullName -Raw), '', '---', ''
}

$content | Out-File $out -Encoding utf8
Write-Host "Exported $($files.Count) files to backups\${entity}_export_$ts.md"
