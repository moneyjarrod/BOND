@echo off
echo Populating templates from proven doctrine...

set ROOT=C:\Projects\BOND_parallel

REM BOND_MASTER templates (8 .md + entity.json)
set BM_SRC=%ROOT%\doctrine\BOND_MASTER
set BM_DST=%ROOT%\templates\doctrine\BOND_MASTER

copy "%BM_SRC%\BOND_MASTER.md" "%BM_DST%\BOND_MASTER.md"
copy "%BM_SRC%\BOND_PROTOCOL.md" "%BM_DST%\BOND_PROTOCOL.md"
copy "%BM_SRC%\BOND_ENTITIES.md" "%BM_DST%\BOND_ENTITIES.md"
copy "%BM_SRC%\BOND_AUDIT.md" "%BM_DST%\BOND_AUDIT.md"
copy "%BM_SRC%\VINE_GROWTH_MODEL.md" "%BM_DST%\VINE_GROWTH_MODEL.md"
copy "%BM_SRC%\WARM_RESTORE.md" "%BM_DST%\WARM_RESTORE.md"
copy "%BM_SRC%\SURGICAL_CONTEXT.md" "%BM_DST%\SURGICAL_CONTEXT.md"
copy "%BM_SRC%\RELEASE_GOVERNANCE.md" "%BM_DST%\RELEASE_GOVERNANCE.md"
copy "%BM_SRC%\entity.json" "%BM_DST%\entity.json"

REM PROJECT_MASTER templates (3 .md + entity.json)
set PM_SRC=%ROOT%\doctrine\PROJECT_MASTER
set PM_DST=%ROOT%\templates\doctrine\PROJECT_MASTER

copy "%PM_SRC%\PROJECT_MASTER.md" "%PM_DST%\PROJECT_MASTER.md"
copy "%PM_SRC%\PROJECT_BOUNDARIES.md" "%PM_DST%\PROJECT_BOUNDARIES.md"
copy "%PM_SRC%\PERSPECTIVE_REGISTRY.md" "%PM_DST%\PERSPECTIVE_REGISTRY.md"
copy "%PM_SRC%\entity.json" "%PM_DST%\entity.json"

echo.
echo Done. 13 files copied to templates.
echo Templates now match proven doctrine.
pause
