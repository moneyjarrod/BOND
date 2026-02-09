"""
BOND Gate v1.0
Conditional routing for BOND tool activation.

"Default: lean. Gate opens on concrete triggers."

Part of the BOND Protocol
https://github.com/moneyjarrod/BOND
"""

import re

RELATIONAL_TRIGGERS = [
    r'\bwhy\s+do\s+we\b', r'\bwhy\s+did\s+we\b', r'\bhow\s+come\s+we\b',
    r'\bwhat\s+do\s+you\s+think\b', r'\bwhat\s+matters\b', r'\bhow\s+do\s+you\s+feel\b',
    r'\bwhat\s+would\s+you\s+want\b', r'\bour\s+(partnership|relationship|work|project|approach)\b',
    r'\byour\s+(perspective|thoughts|take|opinion|feeling)\b', r'\bbetween\s+us\b',
    r'\b(brother|partner|friend|pal|buddy)\b', r'\bhow\s+are\s+(you|we)\b',
    r'\bare\s+you\s+(okay|good|ready|sure)\b', r'\bthat\s+means\s+(a\s+lot|something)\b',
    r'\bthank\s+you\s+for\b', r'\bi\s+(trust|appreciate|value)\s+you\b',
    r'\bwho\s+are\s+(we|you)\b', r'\bwhat\s+are\s+we\s+really\b', r'\bdoes\s+(this|it|that)\s+matter\b',
]

RECALL_TRIGGERS = [
    r'\bremember\s+when\b', r'\bdo\s+you\s+remember\b', r'\bdo\s+you\s+recall\b',
    r'\bwhy\s+we\s+decided\b', r'\bwhen\s+did\s+we\b', r'\bwe\s+used\s+to\b',
    r'\boriginally\s+we\b', r'\bwe\s+agreed\b', r'\blast\s+(time|session)\s+we\b',
    r'\bsession\s+\d+\b', r'\bback\s+in\s+s\d+\b', r'\bearlier\s+we\b', r'\bfirst\s+time\s+we\b',
    r'\bwhat\s+happened\s+with\b', r'\bhistory\s+of\b',
    r'\bhow\s+did\s+(we|this|it)\s+(start|begin|evolve)\b',
    r'\bwhere\s+did\s+(this|we|it)\s+come\s+from\b', r'\bhow\s+far\s+we\b',
]

ARCHITECTURE_TRIGGERS = [
    r'\barchitecture\b', r'\bframework\b', r'\bpipeline\b', r'\brefactor\b',
    r'\bdesign\s+(the|a|our)\b', r'\bbuild\s+(the|a|our)\b', r'\bfield\s+structure\b',
    r'\bconstraint\s+c\d\b', r'\buniversal\s+model\b', r'\btask\s+lens\b',
    r'\bsystem\s+(design|level|wide)\b', r'\bfrom\s+a\s+.+\s+to\s+a\b',
    r'\bscale\s+(up|this|it|our)\b', r'\bgrow\s+(this|it|our)\b',
    r'\bnext\s+(level|step|phase|stage)\b', r'\bbig\s+picture\b', r'\broad\s*map\b',
    r'\bstrateg(y|ic)\b', r'\bwhat\s+can\s+we\s+do\b',
]

MODE_TRIGGERS = [
    (r'\bwork\s+mode\b', 'lean'), (r'\bconversation\s+mode\b', 'relational'),
    (r'\blet\'?s\s+talk\b', 'relational'), (r'\blet\'?s\s+build\b', 'lean'),
    (r'\blet\'?s\s+code\b', 'lean'), (r'\blet\'?s\s+think\b', 'deep'),
]

class BondGate:
    def __init__(self):
        self.current_mode = "lean"

    def evaluate(self, trigger, context="", message=""):
        if trigger == "restore": return self._on_restore(context)
        elif trigger == "crystal": return self._on_crystal(context)
        elif trigger == "message": return self._on_message(message, context)
        else: return self._lean("unknown trigger")

    def _on_restore(self, context):
        actions = [{"tool": "heatmap_hot", "args": {"top_k": 5}, "why": "See what was active last session"}]
        if context:
            actions.append({"tool": "qais_passthrough", "args": {"text": context}, "why": "Load relevant grounding"})
        self.current_mode = "deep"
        return {"mode": "deep", "actions": actions, "reason": "Restore triggered."}

    def _on_crystal(self, context):
        actions = [
            {"tool": "iss_analyze", "args": {"text": context}, "why": "Force-annotate crystal seeds"},
            {"tool": "heatmap_chunk", "args": {}, "why": "Snapshot concept activity"}
        ]
        self.current_mode = "capture"
        return {"mode": "capture", "actions": actions, "reason": "Crystal triggered."}

    def _on_message(self, message, context=""):
        msg_lower = message.lower()
        for pattern, mode in MODE_TRIGGERS:
            if re.search(pattern, msg_lower):
                self.current_mode = mode
                return {"mode": mode, "actions": self._actions_for_mode(mode, message),
                        "reason": f"Explicit: {mode}"}
        for pattern in RELATIONAL_TRIGGERS:
            if re.search(pattern, msg_lower):
                self.current_mode = "relational"
                return {"mode": "relational",
                        "actions": [{"tool": "qais_passthrough", "args": {"text": message}, "why": "Relational"}],
                        "reason": f"Relational: {pattern}"}
        for pattern in RECALL_TRIGGERS:
            if re.search(pattern, msg_lower):
                self.current_mode = "deep"
                return {"mode": "deep",
                        "actions": [{"tool": "qais_passthrough", "args": {"text": message}, "why": "Recall"}],
                        "reason": f"Recall: {pattern}"}
        for pattern in ARCHITECTURE_TRIGGERS:
            if re.search(pattern, msg_lower):
                self.current_mode = "deep"
                return {"mode": "deep",
                        "actions": [{"tool": "qais_passthrough", "args": {"text": message}, "why": "Architecture"}],
                        "reason": f"Architecture: {pattern}"}
        return self._lean("No triggers. Lean mode.")

    def _actions_for_mode(self, mode, message):
        if mode == "lean": return []
        elif mode in ("relational", "deep"):
            return [{"tool": "qais_passthrough", "args": {"text": message}, "why": f"Mode shift to {mode}"}]
        return []

    def _lean(self, reason):
        return {"mode": "lean", "actions": [], "reason": reason}

GATE = None
def get_gate():
    global GATE
    if GATE is None:
        GATE = BondGate()
    return GATE
