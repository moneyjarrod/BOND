"""
BOND Tool Authorization v2.0
Entity awareness for MCP tool dispatch.

All tools are universal across all entity classes (S121).
Class shapes Claude's behavior inside an entity, not tool access.
This module provides entity context — no tool blocking.

Part of the BOND Protocol
https://github.com/moneyjarrod/BOND
"""

import json
import os

BOND_ROOT = os.environ.get('BOND_ROOT',
    os.path.join(os.path.dirname(__file__), '..'))
STATE_FILE = os.path.join(BOND_ROOT, 'state', 'active_entity.json')
DOCTRINE_PATH = os.path.join(BOND_ROOT, 'doctrine')

TOOL_CAPABILITY = {
    'iss_analyze': 'iss', 'iss_compare': 'iss', 'iss_limbic': 'iss', 'iss_status': 'iss',
    'qais_resonate': 'qais', 'qais_exists': 'qais', 'qais_store': 'qais',
    'qais_stats': 'qais', 'qais_get': 'qais', 'qais_passthrough': 'qais',
    'perspective_store': 'qais', 'perspective_check': 'qais',
    'perspective_remove': 'qais', 'perspective_crystal_restore': 'qais',
    'heatmap_touch': 'heatmap', 'heatmap_hot': 'heatmap',
    'heatmap_chunk': 'heatmap', 'heatmap_clear': 'heatmap',
    'crystal': 'crystal', 'bond_gate': 'crystal',
    'daemon_fetch': 'daemon',
}

def get_active_entity():
    """Return (entity_name, entity_class) or (None, None) if unscoped."""
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        entity = state.get('entity')
        if not entity:
            return None, None
        entity_class = state.get('class')
        if entity_class:
            return entity, entity_class
        config_path = os.path.join(DOCTRINE_PATH, entity, 'entity.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        return entity, config.get('class', 'library')
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None, None

def has_armed_seeders():
    """Check if any perspective entities have seeding: true."""
    try:
        for entry in os.listdir(DOCTRINE_PATH):
            config_path = os.path.join(DOCTRINE_PATH, entry, 'entity.json')
            if not os.path.isfile(config_path):
                continue
            with open(config_path, 'r') as f:
                config = json.load(f)
            if config.get('class') == 'perspective' and config.get('seeding'):
                return True
    except (OSError, json.JSONDecodeError):
        pass
    return False

def validate_tool_call(tool_name):
    """All tools are universally available (S121).
    Returns (True, None) always. Entity context available via get_active_entity().
    Kept for API compatibility — callers don't need to change."""
    return True, None
