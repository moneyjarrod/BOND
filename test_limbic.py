"""Quick test of iss_limbic function standalone."""
import sys
import os

# Add ISS dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ISS'))

# Import and test
from iss_mcp_server import LIMBIC, analyze

print("=== Testing ISS analyze ===")
result = analyze("test stuck in a loop")
print(f"analyze OK: gap={result['gap']}")

print("\n=== Testing LIMBIC.load_field() ===")
LIMBIC.load_field()
print(f"loaded: {LIMBIC._loaded}")
print(f"bindings: {len(LIMBIC.stored)}")
print(f"roles: {list(LIMBIC.role_fields.keys())[:10]}...")

print("\n=== Testing LIMBIC.run() ===")
try:
    result = LIMBIC.run("what if we get stuck and compromise core design", "GSG mining")
    print(f"SUCCESS: {result}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Testing minimal ===")
try:
    result = LIMBIC.run("hello")
    print(f"SUCCESS: {result}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Testing JSON serialization ===")
import json
try:
    result = LIMBIC.run("hello")
    j = json.dumps(result, indent=2)
    print(f"JSON OK, length={len(j)}")
    print(j)
except Exception as e:
    print(f"JSON ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
