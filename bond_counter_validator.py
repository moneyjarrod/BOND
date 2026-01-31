#!/usr/bin/env python3
"""
BOND Counter Validator - Single Source of Truth

THE MATH:
    LIMIT ← CONFIG ∨ 10
    
    🗒️ : N ≤ LIMIT
    🟡 : N > LIMIT
    🟠 : N ≥ 15
    🔴 : N ≥ 20

STACKING:
    🟡🟠 : (N > LIMIT) ∧ (N ≥ 15)
    🟡🔴 : (N > LIMIT) ∧ (N ≥ 20)

EVALUATION:
    N=10, LIMIT=10:  10 ≤ 10 = TRUE  → 🗒️
    N=11, LIMIT=10:  11 > 10 = TRUE  → 🟡

Import this module in any BOND tool that needs counter logic.
"""

from dataclasses import dataclass
from typing import Tuple, List


@dataclass
class CounterResult:
    """Result of counter evaluation"""
    n: int
    limit: int
    emoji: str
    states: List[str]
    
    def display(self) -> str:
        return f"{self.emoji} {self.n}/{self.limit}"


def evaluate_counter(n: int, limit: int = 10) -> CounterResult:
    """
    N, LIMIT → emoji
    
    🗒️ : N ≤ LIMIT
    🟡 : N > LIMIT  
    🟠 : N ≥ 15
    🔴 : N ≥ 20
    """
    states = []
    emoji_parts = []
    
    # ========================================
    # RULE 1: Personal limit (relative)
    # 🗒️ when N ≤ LIMIT
    # 🟡 when N > LIMIT (strictly greater, NOT at)
    # ========================================
    if n > limit:
        states.append("OVER_LIMIT")
        emoji_parts.append("🟡")
    else:
        states.append("NORMAL")
    
    # ========================================
    # RULE 2: Danger zone (absolute, N ≥ 15)
    # Always applies regardless of personal limit
    # ========================================
    if n >= 15:
        states.append("DANGER")
        emoji_parts.append("🟠")
    
    # ========================================
    # RULE 3: Critical zone (absolute, N ≥ 20)
    # Replaces danger, always applies
    # ========================================
    if n >= 20:
        # Remove danger, add critical
        if "🟠" in emoji_parts:
            emoji_parts.remove("🟠")
        if "DANGER" in states:
            states.remove("DANGER")
        states.append("CRITICAL")
        emoji_parts.append("🔴")
    
    # ========================================
    # BUILD FINAL EMOJI
    # 🗒️ only if no warning states
    # Otherwise combine warnings
    # ========================================
    if not emoji_parts:
        emoji = "🗒️"
    else:
        emoji = "".join(emoji_parts)
    
    return CounterResult(n=n, limit=limit, emoji=emoji, states=states)


def validate_counter_display(display: str, n: int, limit: int) -> Tuple[bool, str]:
    """
    Validate that a counter display string is correct.
    
    Args:
        display: The display string (e.g., "🗒️ 5/10" or "🟡🟠 16/12")
        n: Expected message count
        limit: Expected limit
    
    Returns:
        (is_valid, message)
    """
    expected = evaluate_counter(n, limit)
    expected_display = expected.display()
    
    if display.strip() == expected_display:
        return (True, f"✅ Correct: {display}")
    else:
        return (False, f"❌ WRONG: got '{display}', expected '{expected_display}'")


# ============================================================
# TEST SUITE - The proof that 2 + 2 = 4
# ============================================================

def run_tests():
    """
    Proof: ∀ test cases, evaluate_counter(N, LIMIT) = expected
    """
    print("BOND COUNTER VALIDATOR")
    print("=" * 50)
    print()
    print("🗒️ : N ≤ LIMIT")
    print("🟡 : N > LIMIT")
    print("🟠 : N ≥ 15")
    print("🔴 : N ≥ 20")
    print()
    print("=" * 50)
    
    # Test cases: (n, limit, expected_emoji, math)
    test_cases = [
        # === N = LIMIT ===
        (10, 10, "🗒️", "10 ≤ 10 = TRUE"),
        (11, 10, "🟡", "11 > 10 = TRUE"),
        
        # === N < LIMIT ===
        (1, 10, "🗒️", "1 ≤ 10 = TRUE"),
        (5, 10, "🗒️", "5 ≤ 10 = TRUE"),
        (9, 10, "🗒️", "9 ≤ 10 = TRUE"),
        
        # === Variable LIMIT ===
        (5, 5, "🗒️", "5 ≤ 5 = TRUE"),
        (6, 5, "🟡", "6 > 5 = TRUE"),
        (12, 15, "🗒️", "12 ≤ 15 = TRUE"),
        (15, 15, "🟠", "15 ≤ 15 ∧ 15 ≥ 15"),
        (16, 15, "🟡🟠", "16 > 15 ∧ 16 ≥ 15"),
        
        # === N ≥ 15 ===
        (15, 10, "🟡🟠", "15 > 10 ∧ 15 ≥ 15"),
        (15, 20, "🟠", "15 ≤ 20 ∧ 15 ≥ 15"),
        (17, 10, "🟡🟠", "17 > 10 ∧ 17 ≥ 15"),
        (19, 10, "🟡🟠", "19 > 10 ∧ 19 ≥ 15"),
        
        # === N ≥ 20 ===
        (20, 10, "🟡🔴", "20 > 10 ∧ 20 ≥ 20"),
        (20, 25, "🔴", "20 ≤ 25 ∧ 20 ≥ 20"),
        (25, 10, "🟡🔴", "25 > 10 ∧ 25 ≥ 20"),
        
        # === Edge ===
        (1, 1, "🗒️", "1 ≤ 1 = TRUE"),
        (2, 1, "🟡", "2 > 1 = TRUE"),
        (14, 10, "🟡", "14 > 10 ∧ 14 < 15"),
        (14, 14, "🗒️", "14 ≤ 14 ∧ 14 < 15"),
        (14, 15, "🗒️", "14 ≤ 15 ∧ 14 < 15"),
    ]
    
    passed = 0
    failed = 0
    
    for n, limit, expected, math in test_cases:
        result = evaluate_counter(n, limit)
        actual = result.emoji
        
        if actual == expected:
            status = "✓"
            passed += 1
        else:
            status = "✗"
            failed += 1
        
        print(f"  {status} {n:2}/{limit:2} → {actual:4} | {math}")
        if actual != expected:
            print(f"       expected: {expected}")
    
    print()
    print("=" * 50)
    print(f"{passed}/{passed+failed}")
    
    if failed == 0:
        print("∀ tests: PASS")
    else:
        print(f"{failed} FAIL")
    
    return failed == 0


# ============================================================
# USAGE BY OTHER BOND TOOLS
# ============================================================

def get_counter_emoji(n: int, limit: int = 10) -> str:
    """
    Simple interface for other BOND tools.
    
    Usage:
        from bond_counter_validator import get_counter_emoji
        emoji = get_counter_emoji(n=10, limit=10)  # Returns "🗒️"
        emoji = get_counter_emoji(n=11, limit=10)  # Returns "🟡"
    """
    return evaluate_counter(n, limit).emoji


def get_counter_display(n: int, limit: int = 10) -> str:
    """
    Full display string for other BOND tools.
    
    Usage:
        from bond_counter_validator import get_counter_display
        display = get_counter_display(n=16, limit=12)  # Returns "🟡🟠 16/12"
    """
    return evaluate_counter(n, limit).display()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
