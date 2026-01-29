"""
QAIS Test Script
Run this to verify your QAIS setup works.

Usage:
  python qais_test.py

Expected output:
  All tests should show ✅
  If you see ❌, check the error message.

Part of BOND Protocol | github.com/moneyjarrod/BOND
"""

import sys
import os

# Test 1: Python version
print("=" * 50)
print("QAIS Setup Test")
print("=" * 50)
print()

print("1. Python version...")
if sys.version_info >= (3, 8):
    print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}")
else:
    print(f"   ❌ Python {sys.version_info.major}.{sys.version_info.minor} (need 3.8+)")
    sys.exit(1)

# Test 2: numpy
print("2. Checking numpy...")
try:
    import numpy as np
    print(f"   ✅ numpy {np.__version__}")
except ImportError:
    print("   ❌ numpy not installed")
    print("      Run: pip install numpy")
    sys.exit(1)

# Test 3: Server file exists
print("3. Checking server file...")
script_dir = os.path.dirname(os.path.abspath(__file__))
server_path = os.path.join(script_dir, "qais_mcp_server.py")
if os.path.exists(server_path):
    print(f"   ✅ qais_mcp_server.py found")
else:
    print(f"   ❌ qais_mcp_server.py not found in {script_dir}")
    sys.exit(1)

# Test 4: Import server
print("4. Importing QAIS core...")
try:
    sys.path.insert(0, script_dir)
    from qais_mcp_server import QAISField, seed_to_vector, bind, resonance, N
    print("   ✅ QAIS core imported")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 5: Vector math
print("5. Testing vector math...")
try:
    v1 = seed_to_vector("test")
    v2 = seed_to_vector("test")
    v3 = seed_to_vector("different")
    
    # Same seed = same vector
    assert np.allclose(v1, v2), "Same seed should produce same vector"
    
    # Different seed = different vector
    assert not np.allclose(v1, v3), "Different seed should produce different vector"
    
    # Vector properties
    assert len(v1) == N, f"Vector should be {N} dimensions"
    assert set(np.unique(v1)) == {-1, 1}, "Vector should be bipolar (-1, +1)"
    
    print(f"   ✅ Vectors: {N} dims, bipolar, deterministic")
except Exception as e:
    print(f"   ❌ Vector math failed: {e}")
    sys.exit(1)

# Test 6: Resonance
print("6. Testing resonance...")
try:
    # Create field
    field = QAISField(field_path=":memory:")  # Won't save to disk
    field.identity_field = np.zeros(N, dtype=np.float32)
    field.role_fields = {}
    field.stored = set()
    field.count = 0
    
    # Store a fact
    result = field.store("Alice", "role", "developer")
    assert result["status"] == "stored", "Store should succeed"
    
    # Resonate
    results = field.resonate("Alice", "role", ["developer", "designer", "random"])
    
    # Check ranking
    assert results[0]["fact"] == "developer", "Stored fact should rank first"
    assert results[0]["score"] > 0.9, "Stored fact should score ~1.0"
    assert results[0]["confidence"] == "HIGH", "Should have HIGH confidence"
    
    print(f"   ✅ Resonance working (score: {results[0]['score']:.3f})")
except Exception as e:
    print(f"   ❌ Resonance failed: {e}")
    sys.exit(1)

# Test 7: Existence check
print("7. Testing existence check...")
try:
    exists_result = field.exists("Alice")
    assert exists_result["exists"] == True, "Alice should exist"
    
    not_exists = field.exists("Unknown Person")
    assert not_exists["exists"] == False, "Unknown should not exist"
    
    print(f"   ✅ Existence check working")
except Exception as e:
    print(f"   ❌ Existence check failed: {e}")
    sys.exit(1)

# Done
print()
print("=" * 50)
print("✅ All tests passed! QAIS is ready.")
print("=" * 50)
print()
print("Next steps:")
print("1. Add qais to your claude_desktop_config.json")
print("2. Restart Claude Desktop")
print("3. Ask Claude to store your project identities")
print()
print("See QAIS_SYSTEM.md for full setup instructions.")
