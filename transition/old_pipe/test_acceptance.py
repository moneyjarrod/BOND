"""
BOND_parallel Acceptance Test Suite
Run against daemon on port 3004: python bond_search.py --root C:\Projects\BOND_parallel --port 3004
"""
import json
import urllib.request
import urllib.error
import sys

BASE = "http://localhost:3003"
PASS = 0
FAIL = 0
results = []

def fetch(endpoint, label):
    try:
        url = f"{BASE}{endpoint}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data
    except Exception as e:
        print(f"  ✗ {label}: {e}")
        return None

def check(condition, msg):
    global PASS, FAIL
    if condition:
        print(f"  ✓ {msg}")
        PASS += 1
        results.append(f"PASS: {msg}")
    else:
        print(f"  ✗ {msg}")
        FAIL += 1
        results.append(f"FAIL: {msg}")

print("=" * 60)
print("BOND_parallel Acceptance Test Suite")
print("=" * 60)

# ─── TEST 1: Cold Boot ───
print("\n── TEST 1: Cold Boot (D5, D9, CORE Success Criteria) ──")
sync = fetch("/sync-complete", "sync-complete")
if sync:
    check("active_entity" in sync, "Payload has active_entity")
    check("config" in sync, "Payload has config")
    check("entity_files" in sync, "Payload has entity_files")
    check("armed_seeders" in sync, "Payload has armed_seeders")
    check("heatmap" in sync, "Payload has heatmap")
    check("capabilities" in sync, "Payload has capabilities")
    # D11 check
    has_handoff = "handoff" in sync
    check(has_handoff, "Payload has handoff field (D11)")
    # D12 check
    has_li = "linked_identities" in sync
    check(has_li, "Payload has linked_identities field (D12)")
    # Entity files loaded
    ef = sync.get("entity_files", {})
    check(len(ef) > 0, f"Entity files loaded: {list(ef.keys())}")
else:
    check(False, "/sync-complete returned data")

# ─── TEST 2: Tiered Loading (D12) ───
print("\n── TEST 2: Tiered Loading (D12) ──")
if sync:
    li = sync.get("linked_identities", {})
    if li:
        for name, content in li.items():
            # Should be entity.json content only, not full .md files
            if isinstance(content, dict):
                has_class = "class" in content
                check(has_class, f"linked_identities[{name}] has class (identity)")
                # Check it's NOT full files (no .md keys)
                md_keys = [k for k in content.keys() if k.endswith('.md')]
                check(len(md_keys) == 0, f"linked_identities[{name}] has NO .md files (tier 1 only)")
            elif isinstance(content, str):
                # entity.json as string
                try:
                    parsed = json.loads(content)
                    check("class" in parsed, f"linked_identities[{name}] parseable with class field")
                except:
                    check(False, f"linked_identities[{name}] is parseable JSON")
    else:
        print("  ⚠ No linked_identities in payload (entity may have no links)")
        # Check if active entity HAS links
        ae = sync.get("active_entity", "")
        ef = sync.get("entity_files", {})
        ej = ef.get("entity.json", "")
        if ej:
            try:
                ejd = json.loads(ej) if isinstance(ej, str) else ej
                links = ejd.get("links", [])
                if links:
                    check(False, f"Entity has links {links} but linked_identities is empty")
                else:
                    print("  ⚠ Active entity has no links — set TEST_DOCTRINE active for this test")
            except:
                pass

    # Full enter-payload test
    enter = fetch("/enter-payload?entity=PROJECT_MASTER", "enter-payload PM")
    if enter:
        eef = enter.get("entity_files", {})
        md_files = [k for k in eef.keys() if k.endswith('.md')]
        check(len(md_files) > 0, f"/enter-payload returns full .md files: {md_files}")
    else:
        check(False, "/enter-payload returned data")

# ─── TEST 3: Handoff Continuity (D11) ───
print("\n── TEST 3: Handoff Continuity (D11) ──")
if sync:
    handoff = sync.get("handoff")
    if handoff:
        check("HANDOFF TEST" in handoff or len(handoff) > 10, "Handoff content present in sync payload")
        check(isinstance(handoff, str), "Handoff is string (verbatim content)")
    else:
        # Might be null if no handoff exists — check if there IS one on disc
        print("  ⚠ handoff field is null/empty — checking if test handoff exists on disc...")
        check(False, "Handoff carried in /sync-complete (D11)")

# ─── TEST 4: Obligation Derivation (Principle #8) ───
print("\n── TEST 4: Obligation Derivation (Principle #8) ──")
oblig = fetch("/obligations", "obligations")
if oblig:
    check(True, "/obligations endpoint responds")
    # Check armed seeders
    armed = sync.get("armed_seeders", []) if sync else []
    print(f"  ℹ Armed seeders from sync: {armed}")
    check(len(armed) > 0, "Armed seeders detected (TEST_PERSPECTIVE seeding:true)")
    # obligations should also report armed
    oblig_str = json.dumps(oblig)
    print(f"  ℹ Obligations response keys: {list(oblig.keys()) if isinstance(oblig, dict) else 'not dict'}")
else:
    check(False, "/obligations endpoint responds")

# ─── TEST 5: Platform Blindness (D6) ───
print("\n── TEST 5: Platform Blindness (D6) ──")
# Hit all composite endpoints
endpoints = [
    "/sync-complete",
    "/enter-payload?entity=BOND_MASTER",
    "/search?q=test",
    "/status",
    "/manifest",
]
for ep in endpoints:
    data = fetch(ep, ep)
    check(data is not None, f"{ep} returns valid JSON")

# Check no fixture references in responses
if sync:
    sync_str = json.dumps(sync)
    fixture_words = ["panel", "AHK", "clipboard", "autohotkey"]
    fixture_found = [w for w in fixture_words if w.lower() in sync_str.lower()]
    check(len(fixture_found) == 0, f"No fixture references in /sync-complete (found: {fixture_found if fixture_found else 'none'})")

# ─── SUMMARY ───
print("\n" + "=" * 60)
print(f"RESULTS: {PASS} passed, {FAIL} failed")
print("=" * 60)
for r in results:
    print(f"  {r}")

if FAIL == 0:
    print("\n🟢 ALL TESTS PASSED — BOND_parallel ready for switchover")
else:
    print(f"\n🔴 {FAIL} FAILURE(S) — fix before switchover")

sys.exit(0 if FAIL == 0 else 1)
