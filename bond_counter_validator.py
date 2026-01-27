#!/usr/bin/env python3
"""
BOND Counter State Machine Validator
Finds edge cases and failure modes in the counter rules.

"The counter tracks CONTEXT DEGRADATION, not task completion."

Run: python3 bond_counter_validator.py

DISCOVERED RULES:
- Universal thresholds (15, 20) ALWAYS override personal limits
- Emotional carryover is an anti-pattern
- {Save}/{Chunk}/Bonfire do NOT reset counter
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple

class CounterState(Enum):
    NORMAL = auto()      # 🗒️ N ≤ LIMIT
    PAST_LIMIT = auto()  # 🟡 LIMIT < N < 15
    DANGEROUS = auto()   # 🟠 15 ≤ N < 20
    CRITICAL = auto()    # 🔴 N ≥ 20

class Action(Enum):
    MESSAGE = auto()           # Any response
    SYNC = auto()              # {Sync} command
    SAVE = auto()              # {Save} command
    CHUNK = auto()             # {Chunk} command
    BONFIRE = auto()           # Milestone declared
    TASK_COMPLETE = auto()     # Task finished (not bonfire)
    NEW_CONVERSATION = auto()  # Fresh start
    COMPACTION = auto()        # Context compacted (counter lost)

@dataclass
class CounterMachine:
    count: int = 1
    limit: int = 10
    
    def get_state(self) -> CounterState:
        # PRIORITY: Universal thresholds override personal limits
        if self.count >= 20:
            return CounterState.CRITICAL
        elif self.count >= 15:
            return CounterState.DANGEROUS
        elif self.count > self.limit:
            return CounterState.PAST_LIMIT
        else:
            return CounterState.NORMAL
    
    def get_emoji(self) -> str:
        return {
            CounterState.NORMAL: "🗒️",
            CounterState.PAST_LIMIT: "🟡",
            CounterState.DANGEROUS: "🟠",
            CounterState.CRITICAL: "🔴"
        }[self.get_state()]
    
    def apply(self, action: Action) -> Tuple[int, str]:
        if action == Action.SYNC:
            self.count = 1
            return (self.count, "RESET: Fresh context from files")
        elif action == Action.NEW_CONVERSATION:
            self.count = 1
            return (self.count, "RESET: Clean slate")
        elif action == Action.COMPACTION:
            self.count = 15
            return (self.count, "LOST → RESUME at 15 (danger zone)")
        elif action == Action.MESSAGE:
            self.count += 1
            return (self.count, "INCREMENT: Context degrading")
        elif action in [Action.SAVE, Action.CHUNK, Action.BONFIRE, Action.TASK_COMPLETE]:
            self.count += 1
            return (self.count, f"NO RESET: {action.name} ≠ context refresh")
        return (self.count, "UNKNOWN")
    
    def display(self) -> str:
        return f"{self.get_emoji()} {self.count}/{self.limit}"


def test_custom_limits():
    """Test that custom limits work correctly"""
    print("BOND COUNTER VALIDATOR")
    print("=" * 40)
    
    test_cases = [
        (5, 3, "🗒️"),   (5, 5, "🗒️"),   (5, 6, "🟡"),
        (5, 14, "🟡"),  (5, 15, "🟠"),  (10, 10, "🗒️"),
        (10, 11, "🟡"), (15, 12, "🗒️"), (15, 16, "🟠"),
        (15, 15, "🗒️"),
    ]
    
    all_pass = True
    for limit, count, expected in test_cases:
        machine = CounterMachine(count=count, limit=limit)
        actual = machine.get_emoji()
        status = "✅" if actual == expected else "❌"
        if actual != expected:
            all_pass = False
        print(f"  {status} {count}/{limit} → {actual}")
    
    print(f"\n{'✅ All tests passed!' if all_pass else '❌ SOME TESTS FAILED'}")
    return all_pass


if __name__ == "__main__":
    test_custom_limits()
