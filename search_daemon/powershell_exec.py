"""
BOND PowerShell Execution — D13 Governed Shell Execution

Daemon module: verb classification, validation pipeline, execution, audit logging.

Authority stack (D13):
  1. Verb definitions (doctrine/constitutional)
  2. Verb whitelist (config — user toggles)
  3. Operation cards (cards/*.json — user or Claude, both-agree)
  4. D-pad modes (panel fixture — user selection)

All execution flows through validate() → execute() → post_verify() → log().
12-step pipeline (A2 audit renumbered from original 10).
Escalation continuum: Level 0 Pass, Level 1 Flag, Level 2 Hold, Level 3 Deny.
"""

import os
import re
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone


# ─── Verb-to-Cmdlet Map (D13 canonical) ──────────────────

VERB_CMDLET_MAP = {
    "read": [
        "Get-Content", "Get-Item", "Get-ChildItem", "Test-Path",
        "Select-String", "Measure-Object",
    ],
    "copy": ["Copy-Item"],
    "move": ["Move-Item", "Rename-Item"],
    "create": [
        "New-Item", "Set-Content", "Out-File", "Add-Content",
        "New-ItemProperty",
    ],
    "delete": ["Remove-Item", "Clear-Content", "Remove-ItemProperty"],
    "execute": [
        "Invoke-Expression", "Start-Process",
    ],
}

# Reverse map: canonical cmdlet (lowercase) → verb
CMDLET_TO_VERB = {}
for _verb, _cmdlets in VERB_CMDLET_MAP.items():
    for _cmdlet in _cmdlets:
        CMDLET_TO_VERB[_cmdlet.lower()] = _verb


# ─── Alias Resolution (static — no runtime shell) ────────

ALIAS_MAP = {
    "cat": "Get-Content", "gc": "Get-Content", "type": "Get-Content",
    "gi": "Get-Item",
    "gci": "Get-ChildItem", "ls": "Get-ChildItem", "dir": "Get-ChildItem",
    "cp": "Copy-Item", "copy": "Copy-Item", "cpi": "Copy-Item",
    "mv": "Move-Item", "move": "Move-Item", "mi": "Move-Item",
    "ren": "Rename-Item", "rni": "Rename-Item",
    "ni": "New-Item",
    "sc": "Set-Content",
    "rm": "Remove-Item", "del": "Remove-Item", "ri": "Remove-Item",
    "rmdir": "Remove-Item", "rd": "Remove-Item", "erase": "Remove-Item",
    "cls": "Clear-Content", "clc": "Clear-Content",
    "iex": "Invoke-Expression",
    "saps": "Start-Process", "start": "Start-Process",
    "mkdir": "New-Item",
    "sls": "Select-String",
}


# ─── Level 3 Blacklist (permanent deny, no override) ─────

BLACKLIST = [
    "Format-Volume", "Set-ExecutionPolicy", "Invoke-WebRequest",
    "Invoke-RestMethod", "net user", "reg add", "reg delete",
    "Stop-Computer", "Restart-Computer", "Clear-Disk",
    "Get-Credential", "ConvertTo-SecureString",
    "New-PSSession", "Enter-PSSession",
    # A2/S5-F2: Missing dangerous cmdlets
    "Invoke-Command", "Add-Type", "Start-Job", "Start-ThreadJob",
    "New-Service", "Set-Service", "Enable-PSRemoting",
    "certutil", "bitsadmin", "rundll32",
]

BLACKLIST_PATTERNS = [re.compile(re.escape(b), re.IGNORECASE) for b in BLACKLIST]

# A2/S3-F3 (L3 Critical): EncodedCommand bypasses entire inspection pipeline.
# PowerShell accepts abbreviations: -EncodedCommand, -enc, -en, -e
# Also block -ExecutionPolicy bypass when used inline (not via Set-ExecutionPolicy cmdlet).
# A2/S5-F1: .NET direct type access bypasses cmdlet-layer blacklist.
BLACKLIST_REGEX = [
    re.compile(r'(?:^|\s)-enc\w*\b', re.IGNORECASE),         # -EncodedCommand (min abbrev: -enc)
    re.compile(r'\[System\.Net\.', re.IGNORECASE),           # .NET network types
    re.compile(r'\[System\.Diagnostics\.Process\]', re.IGNORECASE),  # .NET process spawning
    re.compile(r'\\\\[^\s]+'),                              # UNC paths (A2/S3-F1)
    re.compile(r'\$env:', re.IGNORECASE),                      # env var expansion (A2/S3-F2)
    re.compile(r'\$HOME\b', re.IGNORECASE),                   # $HOME expansion (A2/S3-F2)
]


# ─── Chain Operator Splitting ─────────────────────────────

CHAIN_SPLIT_RE = re.compile(r'\s*(?:;|\|{1,2}|\&\&)\s*')


# ─── PowerShell Executor ─────────────────────────────────

class PowerShellExecutor:
    """D13 governed PowerShell execution engine."""

    def __init__(self, bond_root):
        self.bond_root = os.path.realpath(bond_root)
        self.ps_dir = os.path.join(bond_root, 'panel', 'powershell')
        self.config_path = os.path.join(self.ps_dir, 'config.json')
        self.cards_dir = os.path.join(self.ps_dir, 'cards')
        self.log_path = os.path.join(self.ps_dir, 'exec_log.jsonl')

    # ─── Config ───────────────────────────────────────────

    def load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"enabled": False, "mode": "right", "verbs": {}}

    def save_config(self, config):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            f.write('\n')

    # ─── Cards ────────────────────────────────────────────

    def load_card(self, card_id):
        card_path = os.path.join(self.cards_dir, f'{card_id}.json')
        try:
            with open(card_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def list_cards(self):
        cards = []
        try:
            for f in sorted(os.listdir(self.cards_dir)):
                if f.endswith('.json'):
                    try:
                        with open(os.path.join(self.cards_dir, f), 'r', encoding='utf-8') as fh:
                            cards.append(json.load(fh))
                    except (json.JSONDecodeError, IOError):
                        pass
        except FileNotFoundError:
            pass
        return cards

    def save_card(self, card):
        card_id = card.get('id', '')
        if not card_id:
            return {'error': 'Card must have an "id" field'}
        if not card.get('verb'):
            return {'error': 'Card must have a "verb" field'}
        if not card.get('command'):
            return {'error': 'Card must have a "command" field'}
        os.makedirs(self.cards_dir, exist_ok=True)
        card_path = os.path.join(self.cards_dir, f'{card_id}.json')
        with open(card_path, 'w', encoding='utf-8') as f:
            json.dump(card, f, indent=2, ensure_ascii=False)
            f.write('\n')
        return {'saved': True, 'card_id': card_id}

    # ─── Alias Resolution ─────────────────────────────────

    def resolve_aliases(self, command):
        """Replace known PowerShell aliases with canonical cmdlet names."""
        tokens = command.split()
        resolved = []
        for token in tokens:
            canonical = ALIAS_MAP.get(token.lower())
            if canonical:
                resolved.append(canonical)
            else:
                resolved.append(token)
        return ' '.join(resolved)

    # ─── Chain Splitting ──────────────────────────────────

    def split_chain(self, command):
        """Split command on chain operators: ; | && ||"""
        segments = CHAIN_SPLIT_RE.split(command)
        return [s.strip() for s in segments if s.strip()]

    # ─── Segment Classification ───────────────────────────

    def classify_segment(self, segment):
        """Determine which verb classes a command segment contains."""
        verbs_found = set()
        segment_lower = segment.lower()

        # .ps1 file references → execute
        if '.ps1' in segment_lower:
            verbs_found.add('execute')

        # & call operator at start of segment → execute
        stripped = segment.strip()
        if stripped.startswith('&') and len(stripped) > 1 and stripped[1] in (' ', '\t', '"', "'"):
            verbs_found.add('execute')

        # Check each known cmdlet (case-insensitive word boundary)
        for cmdlet, verb in CMDLET_TO_VERB.items():
            if re.search(r'(?i)\b' + re.escape(cmdlet) + r'\b', segment):
                verbs_found.add(verb)

        return verbs_found

    # ─── Path Containment ─────────────────────────────────

    def check_path_containment(self, command, scope, active_entity=None):
        """Verify all paths in command resolve inside allowed boundary.
        Returns (ok, message)."""
        path_patterns = [
            r'"([^"]*[/\\][^"]*)"',           # double-quoted paths
            r"'([^']*[/\\][^']*)'",            # single-quoted paths
            r'(?:^|\s)([A-Za-z]:[/\\]\S+)',    # absolute Windows paths (unquoted)
        ]

        paths_found = []
        for pattern in path_patterns:
            paths_found.extend(re.findall(pattern, command))

        bond_norm = self.bond_root.replace('\\', '/').lower()

        for p in paths_found:
            p_resolved = p.replace('{BOND_ROOT}', self.bond_root)
            try:
                resolved = os.path.realpath(p_resolved)
            except (ValueError, OSError):
                return False, f"Cannot resolve path: {p}"

            resolved_norm = resolved.replace('\\', '/').lower()

            if scope == 'entity' and active_entity:
                entity_boundary = os.path.join(self.bond_root, 'doctrine', active_entity)
                entity_norm = os.path.realpath(entity_boundary).replace('\\', '/').lower()
                if not resolved_norm.startswith(entity_norm):
                    return False, f"Entity-scoped path escapes entity boundary: {p}"
            else:
                if not resolved_norm.startswith(bond_norm):
                    return False, f"Path escapes BOND_ROOT: {p}"

        return True, "ok"

    # ─── Blacklist Check ──────────────────────────────────

    def check_blacklist(self, command):
        """Check command against Level 3 blacklist. Returns (clean, pattern_matched)."""
        for i, pattern in enumerate(BLACKLIST_PATTERNS):
            if pattern.search(command):
                return False, BLACKLIST[i]
        # A2: Regex patterns for encoded commands, .NET types, UNC paths, env vars
        for pattern in BLACKLIST_REGEX:
            if pattern.search(command):
                return False, f'regex:{pattern.pattern}'
        return True, None

    # ─── Param Resolution ─────────────────────────────────

    def resolve_params(self, command, card_params, request_params):
        """Resolve parameterized placeholders. Params derive from system state, never user-typed."""
        resolved = command
        resolved = resolved.replace('{BOND_ROOT}', self.bond_root)

        if card_params:
            for param_def in card_params:
                name = param_def.get('name', '')
                source = param_def.get('source', '')
                placeholder = '{' + name + '}'
                if source == 'active_entity':
                    try:
                        state_path = os.path.join(self.bond_root, 'state', 'active_entity.json')
                        with open(state_path, 'r', encoding='utf-8') as f:
                            state = json.load(f)
                        entity = state.get('entity', '')
                        if entity:
                            entity_path = os.path.join(self.bond_root, 'doctrine', entity)
                            resolved = resolved.replace(placeholder, entity_path)
                    except (FileNotFoundError, json.JSONDecodeError):
                        pass
                elif name in request_params:
                    validate = param_def.get('validate', '')
                    value = str(request_params[name])
                    if validate == 'doctrine_path':
                        real_value = os.path.realpath(value)
                        doctrine_norm = os.path.realpath(
                            os.path.join(self.bond_root, 'doctrine')
                        ).replace('\\', '/').lower()
                        if real_value.replace('\\', '/').lower().startswith(doctrine_norm):
                            resolved = resolved.replace(placeholder, value)
                    elif validate == 'bond_root_path':
                        real_value = os.path.realpath(value)
                        bond_norm = self.bond_root.replace('\\', '/').lower()
                        if real_value.replace('\\', '/').lower().startswith(bond_norm):
                            resolved = resolved.replace(placeholder, value)
                        else:
                            pass  # Path escapes BOND_ROOT — param stays unresolved, caught by containment check
                    elif validate == '' or validate is None:
                        # A2/S6-F1: argument-source params require explicit validation
                        if source == 'argument':
                            pass  # reject — unvalidated user input stays unresolved
                        else:
                            resolved = resolved.replace(placeholder, value)

        return resolved

    # ─── Validation Pipeline (D13: 12 steps, A2 renumbered) ────

    def validate_and_execute(self, card_id, dry_run=False, initiator='user', params=None, confirmed=False):
        """Run the full D13 validation pipeline. Returns response dict."""
        params = params or {}
        t0 = time.time()

        # Step 1: Master toggle
        config = self.load_config()
        if not config.get('enabled', False):
            r = self._result('deny', 2, card_id, None, reason='Master toggle is OFF')
            r['duration_ms'] = self._ms(t0)
            self._log(r, initiator, params)
            return r

        # Step 2: Card registration
        card = self.load_card(card_id)
        if not card:
            r = self._result('deny', 2, card_id, None, reason=f'Card not registered: {card_id}')
            r['duration_ms'] = self._ms(t0)
            self._log(r, initiator, params)
            return r

        verb = card.get('verb', '')

        # Step 3: Verb whitelist + expiration
        verbs_config = config.get('verbs', {})
        verb_entry = verbs_config.get(verb, {})
        if not verb_entry.get('enabled', False):
            r = self._result('deny', 2, card_id, verb, reason=f'Verb "{verb}" is disabled')
            r['duration_ms'] = self._ms(t0)
            self._log(r, initiator, params)
            return r

        expires = verb_entry.get('expires')
        if expires:
            try:
                exp_time = datetime.fromisoformat(expires)
                if datetime.now(timezone.utc) > exp_time:
                    r = self._result('deny', 2, card_id, verb,
                                     reason=f'Verb "{verb}" expired — re-authorize')
                    r['duration_ms'] = self._ms(t0)
                    self._log(r, initiator, params)
                    return r
            except (ValueError, TypeError):
                pass

        # Step 4: D-pad mode gate
        mode = config.get('mode', 'right')
        if initiator == 'claude' and mode == 'right':
            r = self._result('deny', 2, card_id, verb,
                             reason='Manual mode active — Claude-initiated execution blocked. Switch to Auto (←) to allow.')
            r['duration_ms'] = self._ms(t0)
            self._log(r, initiator, params)
            return r

        # Step 5: Resolve command with params
        command = card.get('command', '')
        card_params = card.get('params') or []
        command = self.resolve_params(command, card_params, params)

        # Step 6: Alias resolution
        resolved = self.resolve_aliases(command)

        # Step 7: Chain operator splitting
        segments = self.split_chain(resolved)

        # Step 8: Level 3 blacklist scan (on full resolved command)
        clean, matched = self.check_blacklist(resolved)
        if not clean:
            r = self._result('deny', 3, card_id, verb, reason=f'Level 3 blacklist: {matched}')
            r['duration_ms'] = self._ms(t0)
            self._log(r, initiator, params)
            return r

        # Step 9: Verb-to-pattern mismatch — each segment must match declared verb only
        for seg in segments:
            seg_verbs = self.classify_segment(seg)
            # A2/S6-F3: Unrecognized commands (empty verb set) only allowed for 'execute' verb
            if not seg_verbs and seg.strip() and verb != 'execute':
                r = self._result('hold', 1, card_id, verb,
                                 reason=f'Unrecognized command in segment — cannot classify verb: {seg[:80]}')
                r['duration_ms'] = self._ms(t0)
                self._log(r, initiator, params)
                return r
            mismatched = seg_verbs - {verb}
            if mismatched:
                r = self._result('hold', 2, card_id, verb,
                                 reason=f'Verb mismatch: segment contains {mismatched}, card declares "{verb}"')
                r['duration_ms'] = self._ms(t0)
                self._log(r, initiator, params)
                return r

        # Step 10: Path containment
        scope = card.get('scope', 'global')
        active_entity = None
        if scope == 'entity':
            try:
                with open(os.path.join(self.bond_root, 'state', 'active_entity.json'), 'r', encoding='utf-8') as f:
                    active_entity = json.load(f).get('entity')
            except (FileNotFoundError, json.JSONDecodeError):
                pass

        path_ok, path_msg = self.check_path_containment(resolved, scope, active_entity)
        if not path_ok:
            r = self._result('hold', 2, card_id, verb, reason=path_msg)
            r['duration_ms'] = self._ms(t0)
            self._log(r, initiator, params)
            return r

        # Step 11: Confirm gate
        needs_confirm = card.get('confirm', False)
        if verb in ('delete', 'execute'):
            needs_confirm = True  # forced regardless of card declaration
        if needs_confirm and not confirmed:
            r = self._result('hold', 0, card_id, verb,
                             reason='Confirmation required',
                             command_preview=resolved)
            r['duration_ms'] = self._ms(t0)
            self._log(r, initiator, params)
            return r

        # Step 12: Dry-run gate
        if dry_run:
            dry_text = card.get('dry_run_text', f'Would execute: {resolved}')
            r = self._result('preview', 0, card_id, verb,
                             reason='Dry run',
                             command_preview=resolved,
                             dry_run_text=dry_text)
            r['duration_ms'] = self._ms(t0)
            self._log(r, initiator, params)
            return r

        # All validation passed — execute
        return self._execute(card, resolved, verb, initiator, params, t0, resolved_command=resolved)

    # ─── Execution ────────────────────────────────────────

    def _execute(self, card, resolved_command, verb, initiator, params, t0, **kwargs):
        card_id = card.get('id', 'unknown')
        timeout = card.get('timeout', 30)

        try:
            proc = subprocess.run(
                ['powershell', '-NoProfile', '-NonInteractive', '-Command', resolved_command],
                capture_output=True, text=True,
                timeout=timeout, shell=False,
                cwd=self.bond_root,
            )

            output = proc.stdout or ''
            stderr = proc.stderr or ''
            exit_code = proc.returncode

            output_summary = output[:500]
            if stderr:
                output_summary += f'\n[stderr]: {stderr[:200]}'

            post_verify = self._post_verify(card, verb, exit_code)

            if exit_code != 0:
                level = 1  # Flag
            elif post_verify and post_verify not in ('pass', None):
                level = 2  # Hold — verification failed
            else:
                level = 0  # Pass

            status = 'success' if level == 0 else ('flag' if level == 1 else 'hold')

            r = {
                'status': status,
                'level': level,
                'card': card_id,
                'verb': verb,
                'command_preview': resolved_command,  # A2/S2-F1: for audit log
                'output': output_summary,
                'exit_code': exit_code,
                'duration_ms': self._ms(t0),
                'post_verify': post_verify,
            }
            self._log(r, initiator, params)
            return r

        except subprocess.TimeoutExpired:
            r = self._result('error', 2, card_id, verb, reason=f'Timeout after {timeout}s')
            r['duration_ms'] = self._ms(t0)
            self._log(r, initiator, params)
            return r
        except Exception as e:
            r = self._result('error', 2, card_id, verb, reason=str(e))
            r['duration_ms'] = self._ms(t0)
            self._log(r, initiator, params)
            return r

    # ─── Post-Execution Verification (MCSO) ───────────────

    def _post_verify(self, card, verb, exit_code):
        custom = card.get('post_verify')
        if custom:
            return f'custom:{custom}' if exit_code == 0 else 'fail:exit_code'

        if verb == 'read':
            return None
        elif exit_code != 0:
            return 'fail:exit_code'
        else:
            return 'pass'

    # ─── Audit Logging ────────────────────────────────────

    def _log(self, result, initiator, params):
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'card_id': result.get('card', 'unknown'),
            'verb': result.get('verb', ''),
            'initiator': initiator,
            'level': result.get('level', 0),
            'params': params,
            # A2/S2-F1: Log resolved command for forensic reconstruction
            'resolved_command': (result.get('command_preview', '') or '')[:500],
            'exit_code': result.get('exit_code'),
            'duration_ms': result.get('duration_ms', 0),
            'post_verify': result.get('post_verify'),
            'output_summary': (result.get('output', '') or result.get('reason', ''))[:200],
        }
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"  [WARN] exec log write failed: {e}")

    def read_log(self, limit=50):
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            entries = []
            for line in lines[-limit:]:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
            return list(reversed(entries))
        except FileNotFoundError:
            return []

    # ─── Helpers ──────────────────────────────────────────

    def _ms(self, t0):
        return round((time.time() - t0) * 1000)

    def _result(self, status, level, card_id, verb, **extras):
        r = {'status': status, 'level': level, 'card': card_id, 'verb': verb}
        r.update(extras)
        return r
