"""
BOND Gate v1.0
Conditional routing for BOND tool activation.

"Default: lean. Gate opens on concrete triggers."

The gate eliminates ambiguous judgment calls. Claude makes ONE decision
(call the gate) and the gate returns exactly what to do. Binary triggers,
not emotional thresholds.

Trigger types:
  restore  - {Sync} or {Full Restore} fired. Always opens.
  crystal  - {Crystal} fired. Capture mode.
  message  - Regular turn. Analyzes text for routing signals.

Returns:
  mode     - "lean" | "deep" | "relational" | "capture"
  actions  - List of tool calls Claude should execute (may be empty)
  reason   - Why the gate opened (for transparency)

Part of the BOND Protocol
https://github.com/moneyjarrod/BOND
Session 77 | J-Dub & Claude | 2026-02-03
"""

import re

# =============================================================================
# TRIGGER PATTERNS - Binary, observable, no ambiguity
# =============================================================================

# Relational signals: partnership language, emotional check-ins, shared identity
# TEMPLATE: Broad defaults that work for any BOND user
RELATIONAL_TRIGGERS = [
    # Direct relational questions
    r'\bwhy\s+do\s+we\b',
    r'\bwhy\s+did\s+we\b',
    r'\bhow\s+come\s+we\b',
    r'\bwhat\s+do\s+you\s+think\b',
    r'\bwhat\s+matters\b',
    r'\bhow\s+do\s+you\s+feel\b',
    r'\bwhat\s+would\s+you\s+want\b',
    # Partnership language
    r'\bour\s+(partnership|relationship|work|project|approach)\b',
    r'\byour\s+(perspective|thoughts|take|opinion|feeling)\b',
    r'\bbetween\s+us\b',
    # Terms of endearment / camaraderie
    r'\b(brother|partner|friend|pal|buddy)\b',
    # Emotional check-ins
    r'\bhow\s+are\s+(you|we)\b',
    r'\bare\s+you\s+(okay|good|ready|sure)\b',
    r'\bthat\s+means\s+(a\s+lot|something)\b',
    r'\bthank\s+you\s+for\b',
    r'\bi\s+(trust|appreciate|value)\s+you\b',
    # Identity / meaning questions
    r'\bwho\s+are\s+(we|you)\b',
    r'\bwhat\s+are\s+we\s+really\b',
    r'\bdoes\s+(this|it|that)\s+matter\b',
]

# Recall signals: past references, history, decisions, evolution
# TEMPLATE: Broad defaults that work for any BOND user
RECALL_TRIGGERS = [
    # Explicit memory / recall
    r'\bremember\s+when\b',
    r'\bdo\s+you\s+remember\b',
    r'\bdo\s+you\s+recall\b',
    # Past decision references
    r'\bwhy\s+we\s+decided\b',
    r'\bwhen\s+did\s+we\b',
    r'\bwe\s+used\s+to\b',
    r'\boriginally\s+we\b',
    r'\bwe\s+agreed\b',
    # Temporal references to shared work
    r'\blast\s+(time|session)\s+we\b',
    r'\bsession\s+\d+\b',
    r'\bback\s+in\s+s\d+\b',
    r'\bearlier\s+we\b',
    r'\bfirst\s+time\s+we\b',
    # History / evolution
    r'\bwhat\s+happened\s+with\b',
    r'\bhistory\s+of\b',
    r'\bhow\s+did\s+(we|this|it)\s+(start|begin|evolve)\b',
    r'\bwhere\s+did\s+(this|we|it)\s+come\s+from\b',
    r'\bhow\s+far\s+we\b',
]

# Architecture signals: design, system thinking, growth, strategy
# TEMPLATE: Broad defaults that work for any BOND user
ARCHITECTURE_TRIGGERS = [
    # Direct architecture terms
    r'\barchitecture\b',
    r'\bframework\b',
    r'\bpipeline\b',
    r'\brefactor\b',
    # Design intent
    r'\bdesign\s+(the|a|our)\b',
    r'\bbuild\s+(the|a|our)\b',
    r'\bfield\s+structure\b',
    r'\bconstraint\s+c\d\b',
    # System-level / strategic
    r'\buniversal\s+model\b',
    r'\btask\s+lens\b',
    r'\bsystem\s+(design|level|wide)\b',
    # Growth / scaling language
    r'\bfrom\s+a\s+.+\s+to\s+a\b',
    r'\bscale\s+(up|this|it|our)\b',
    r'\bgrow\s+(this|it|our)\b',
    r'\bnext\s+(level|step|phase|stage)\b',
    r'\bbig\s+picture\b',
    r'\broad\s*map\b',
    r'\bstrateg(y|ic)\b',
    r'\bwhat\s+can\s+we\s+do\b',
]

# Explicit mode requests
MODE_TRIGGERS = [
    (r'\bwork\s+mode\b', 'lean'),
    (r'\bconversation\s+mode\b', 'relational'),
    (r'\blet\'?s\s+talk\b', 'relational'),
    (r'\blet\'?s\s+build\b', 'lean'),
    (r'\blet\'?s\s+code\b', 'lean'),
    (r'\blet\'?s\s+think\b', 'deep'),
]


# =============================================================================
# BOND GATE
# =============================================================================

class BondGate:
    """
    Binary routing gate for BOND tool activation.
    
    Claude calls gate once. Gate returns plan. Claude executes plan.
    No chains of ambiguous evaluation. No skipped conditions.
    """
    
    def __init__(self):
        self.current_mode = "lean"
    
    def evaluate(self, trigger, context="", message=""):
        """
        Main entry point.
        
        Args:
            trigger: "restore" | "crystal" | "message"
            context: Optional context string (topic, session info)
            message: The user's message text (for "message" trigger)
        
        Returns:
            dict with mode, actions, reason
        """
        if trigger == "restore":
            return self._on_restore(context)
        elif trigger == "crystal":
            return self._on_crystal(context)
        elif trigger == "message":
            return self._on_message(message, context)
        else:
            return self._lean("unknown trigger")
    
    def _on_restore(self, context):
        """
        {Sync} or {Full Restore} happened.
        Always opens. Pull context for the session.
        """
        actions = []
        
        # Always check what's hot from previous session
        actions.append({
            "tool": "heatmap_hot",
            "args": {"top_k": 5},
            "why": "See what was active last session"
        })
        
        # Pull annotated seeds relevant to whatever we're about to work on
        if context:
            actions.append({
                "tool": "qais_passthrough",
                "args": {"text": context},
                "why": "Load relevant grounding for session topic"
            })
        
        self.current_mode = "deep"
        return {
            "mode": "deep",
            "actions": actions,
            "reason": "Restore triggered. Loading session context."
        }
    
    def _on_crystal(self, context):
        """
        {Crystal} fired.
        Capture mode: force-annotate seeds before storing.
        """
        actions = []
        
        # Fire ISS on crystal text to get force signature
        actions.append({
            "tool": "iss_analyze",
            "args": {"text": context},
            "why": "Force-annotate crystal seeds with G/P/E"
        })
        
        # Capture current heatmap state for the crystal record
        actions.append({
            "tool": "heatmap_chunk",
            "args": {},
            "why": "Snapshot concept activity at crystallization"
        })
        
        self.current_mode = "capture"
        return {
            "mode": "capture",
            "actions": actions,
            "reason": "Crystal triggered. Annotating seeds before storage."
        }
    
    def _on_message(self, message, context=""):
        """
        Regular turn. Check for binary triggers.
        Default: lean (no actions).
        """
        msg_lower = message.lower()
        
        # Check explicit mode requests first
        for pattern, mode in MODE_TRIGGERS:
            if re.search(pattern, msg_lower):
                self.current_mode = mode
                return {
                    "mode": mode,
                    "actions": self._actions_for_mode(mode, message),
                    "reason": f"Explicit mode request detected: {mode}"
                }
        
        # Check relational triggers
        for pattern in RELATIONAL_TRIGGERS:
            if re.search(pattern, msg_lower):
                self.current_mode = "relational"
                return {
                    "mode": "relational",
                    "actions": [
                        {
                            "tool": "qais_passthrough",
                            "args": {"text": message},
                            "why": "Relational query — pull grounded context"
                        }
                    ],
                    "reason": f"Relational trigger: {pattern}"
                }
        
        # Check recall triggers
        for pattern in RECALL_TRIGGERS:
            if re.search(pattern, msg_lower):
                self.current_mode = "deep"
                return {
                    "mode": "deep",
                    "actions": [
                        {
                            "tool": "qais_passthrough",
                            "args": {"text": message},
                            "why": "Past reference — pull relevant history"
                        }
                    ],
                    "reason": f"Recall trigger: {pattern}"
                }
        
        # Check architecture triggers
        for pattern in ARCHITECTURE_TRIGGERS:
            if re.search(pattern, msg_lower):
                self.current_mode = "deep"
                return {
                    "mode": "deep",
                    "actions": [
                        {
                            "tool": "qais_passthrough",
                            "args": {"text": message},
                            "why": "Architecture discussion — pull system context"
                        }
                    ],
                    "reason": f"Architecture trigger: {pattern}"
                }
        
        # Default: lean. No actions. Just respond.
        return self._lean("No triggers matched. Lean mode.")
    
    def _actions_for_mode(self, mode, message):
        """Return appropriate actions for an explicit mode switch."""
        if mode == "lean":
            return []
        elif mode in ("relational", "deep"):
            return [
                {
                    "tool": "qais_passthrough",
                    "args": {"text": message},
                    "why": f"Mode shift to {mode} — loading context"
                }
            ]
        return []
    
    def _lean(self, reason):
        """Default response. No overhead."""
        return {
            "mode": "lean",
            "actions": [],
            "reason": reason
        }


# =============================================================================
# SINGLETON
# =============================================================================

GATE = None

def get_gate():
    global GATE
    if GATE is None:
        GATE = BondGate()
    return GATE
