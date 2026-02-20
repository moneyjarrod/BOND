"""
BOND Phase 6 Switchover Script
Copies real entities from BOND_private → BOND_parallel.
Preserves BOND_parallel's proven framework files.
Removes test entities. Sets active entity to BOND_MASTER.

Run from: C:\Projects\BOND_parallel\
Usage: python switchover.py [--dry]
"""

import shutil, json, sys, os
from pathlib import Path

DRY = '--dry' in sys.argv

PRIVATE = Path(r'C:\Projects\BOND_private')
PARALLEL = Path(r'C:\Projects\BOND_parallel')

PRIVATE_DOCTRINE = PRIVATE / 'doctrine'
PARALLEL_DOCTRINE = PARALLEL / 'doctrine'
PRIVATE_STATE = PRIVATE / 'state'
PARALLEL_STATE = PARALLEL / 'state'

# Entities to copy wholesale (everything except framework entities)
FRAMEWORK_ENTITIES = {'BOND_MASTER', 'PROJECT_MASTER'}

# Test entities to remove
TEST_ENTITIES = {'TEST_DOCTRINE', 'TEST_PROJECT', 'TEST_PROJECT_EMPTY', 'TEST_PERSPECTIVE'}

# State files to copy
STATE_FILES = ['config.json', 'heatmap.json']

# BM proven files to preserve (do NOT overwrite with old versions)
BM_PROVEN_FILES = {
    'BOND_AUDIT.md', 'BOND_ENTITIES.md', 'BOND_MASTER.md', 'BOND_PROTOCOL.md',
    'RELEASE_GOVERNANCE.md', 'SURGICAL_CONTEXT.md', 'VINE_GROWTH_MODEL.md', 'WARM_RESTORE.md',
}

def log(msg):
    print(f"  {msg}")

def copy_dir(src, dst):
    if DRY:
        log(f"[DRY] Would copy {src.name}/ → {dst}")
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    log(f"✓ Copied {src.name}/")

def remove_dir(path):
    if DRY:
        log(f"[DRY] Would remove {path.name}/")
        return
    if path.exists():
        shutil.rmtree(path)
        log(f"✗ Removed {path.name}/")

def copy_file(src, dst):
    if DRY:
        log(f"[DRY] Would copy {src.name} → {dst}")
        return
    os.makedirs(dst.parent, exist_ok=True)
    shutil.copy2(src, dst)
    log(f"✓ Copied {src.name}")

def main():
    mode = "DRY RUN" if DRY else "LIVE"
    print(f"\n{'='*60}")
    print(f"  BOND Phase 6 Switchover — {mode}")
    print(f"{'='*60}")
    print(f"  Source:  {PRIVATE}")
    print(f"  Target:  {PARALLEL}")
    print()

    # Verify source exists
    if not PRIVATE_DOCTRINE.is_dir():
        print(f"❌ Source not found: {PRIVATE_DOCTRINE}")
        return

    # ── Step 1: Copy real entities wholesale ──
    print("── Step 1: Copy real entities ──")
    copied = 0
    for entity_dir in sorted(PRIVATE_DOCTRINE.iterdir()):
        if not entity_dir.is_dir():
            continue
        name = entity_dir.name
        if name in FRAMEWORK_ENTITIES:
            continue
        copy_dir(entity_dir, PARALLEL_DOCTRINE / name)
        copied += 1
    log(f"({copied} entities copied)")
    print()

    # ── Step 2: Update BOND_MASTER ──
    print("── Step 2: Update BOND_MASTER (preserve proven files) ──")
    bm_src = PRIVATE_DOCTRINE / 'BOND_MASTER'
    bm_dst = PARALLEL_DOCTRINE / 'BOND_MASTER'

    # 2a: Copy entity.json (has real links)
    copy_file(bm_src / 'entity.json', bm_dst / 'entity.json')

    # 2b: Copy state/ subdirectory (handoff data)
    bm_state_src = bm_src / 'state'
    bm_state_dst = bm_dst / 'state'
    if bm_state_src.is_dir():
        if DRY:
            log(f"[DRY] Would copy BOND_MASTER/state/")
        else:
            if bm_state_dst.exists():
                shutil.rmtree(bm_state_dst)
            shutil.copytree(bm_state_src, bm_state_dst)
            log(f"✓ Copied BOND_MASTER/state/")

    # 2c: List what we're preserving vs skipping
    log(f"Preserved {len(BM_PROVEN_FILES)} proven .md files (not overwritten)")
    skipped = []
    for f in sorted(bm_src.iterdir()):
        if f.is_file() and f.suffix == '.md' and f.name not in BM_PROVEN_FILES:
            skipped.append(f.name)
    if skipped:
        log(f"Skipped old/absorbed files: {', '.join(skipped)}")
    print()

    # ── Step 3: Remove test entities ──
    print("── Step 3: Remove test entities ──")
    for name in sorted(TEST_ENTITIES):
        remove_dir(PARALLEL_DOCTRINE / name)
    print()

    # ── Step 4: Set active entity ──
    print("── Step 4: Set active entity → BOND_MASTER ──")
    state_data = {
        "entity": "BOND_MASTER",
        "class": "doctrine",
        "display_name": "BOND Master",
        "path": str(PARALLEL_DOCTRINE / 'BOND_MASTER'),
        "entered": None
    }
    if DRY:
        log(f"[DRY] Would set active_entity.json → BOND_MASTER")
    else:
        (PARALLEL_STATE / 'active_entity.json').write_text(
            json.dumps(state_data, indent=2) + '\n', encoding='utf-8')
        log(f"✓ active_entity.json → BOND_MASTER")
    print()

    # ── Step 5: Copy state essentials ──
    print("── Step 5: Copy state files ──")
    for fname in STATE_FILES:
        src = PRIVATE_STATE / fname
        if src.is_file():
            copy_file(src, PARALLEL_STATE / fname)
        else:
            log(f"⚠ {fname} not found in source state/")
    print()

    # ── Summary ──
    print("── Summary ──")
    if DRY:
        print("  DRY RUN complete. No files modified.")
        print("  Run without --dry to execute.")
    else:
        # Count what's in BOND_parallel now
        entities = [d.name for d in PARALLEL_DOCTRINE.iterdir() if d.is_dir()]
        print(f"  Entities in BOND_parallel: {len(entities)}")
        for e in sorted(entities):
            ej = PARALLEL_DOCTRINE / e / 'entity.json'
            cls = '?'
            try:
                cls = json.loads(ej.read_text(encoding='utf-8')).get('class', '?')
            except:
                pass
            print(f"    {e} ({cls})")
        print()
        print(f"  ✅ Switchover complete.")
        print(f"  Next: restart daemon with --root {PARALLEL}")
        print(f"        then run test_acceptance.py to verify")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
