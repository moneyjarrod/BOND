@echo off
echo Copying new_pipe files to BOND_parallel...

set SRC=C:\Projects\BOND_private\doctrine\BOND_OVERHAUL\new_pipe
set DST=C:\Projects\BOND_parallel\doctrine\BOND_MASTER

copy "%SRC%\BOND_MASTER.md" "%DST%\BOND_MASTER.md"
copy "%SRC%\BOND_PROTOCOL.md" "%DST%\BOND_PROTOCOL.md"
copy "%SRC%\BOND_ENTITIES.md" "%DST%\BOND_ENTITIES.md"
copy "%SRC%\BOND_AUDIT.md" "%DST%\BOND_AUDIT.md"
copy "%SRC%\VINE_GROWTH_MODEL.md" "%DST%\VINE_GROWTH_MODEL.md"
copy "%SRC%\WARM_RESTORE.md" "%DST%\WARM_RESTORE.md"
copy "%SRC%\SURGICAL_CONTEXT.md" "%DST%\SURGICAL_CONTEXT.md"
copy "%SRC%\RELEASE_GOVERNANCE.md" "%DST%\RELEASE_GOVERNANCE.md"

REM Copy PROJECT_MASTER files
set PM_SRC=C:\Projects\BOND_private\doctrine\PROJECT_MASTER
set PM_DST=C:\Projects\BOND_parallel\doctrine\PROJECT_MASTER

copy "%PM_SRC%\PROJECT_MASTER.md" "%PM_DST%\PROJECT_MASTER.md"
copy "%PM_SRC%\PROJECT_BOUNDARIES.md" "%PM_DST%\PROJECT_BOUNDARIES.md"
copy "%PM_SRC%\PERSPECTIVE_REGISTRY.md" "%PM_DST%\PERSPECTIVE_REGISTRY.md"
copy "%PM_SRC%\entity.json" "%PM_DST%\entity.json"

REM Copy daemon
copy "C:\Projects\BOND_private\search_daemon\bond_search.py" "C:\Projects\BOND_parallel\search_daemon\bond_search.py"

echo Done. 12 files copied.
pause