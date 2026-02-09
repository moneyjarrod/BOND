"""
BOND Tool Authorization Middleware v1.0
Runtime capability enforcement based on entity class.

Reads active_entity.json → resolves entity class → checks CLASS_TOOLS matrix.
Called before every MCP tool dispatch. Rejects forbidden tools with structured error.

Part of the BOND Protocol
https://github.com/moneyjarrod/BOND
"""

import json
import os

BOND_ROOT = os.environ.get('BOND_ROOT',
    os.path.join(os.path.dirname(__file__), '..'))
STATE_FILE = os.path.join(BOND_ROOT, 'state', 'active_entity.json')
DOCTRINE_PATH = os.path.join(BOND_ROOT, 'doctrine')

CLASS_TOOLS = {
    'doctrine':    {'filesystem': True, 'iss': True,  'qais': False, 'heatmap': False, 'crystal': False},
    'project':     {'filesystem': True, 'iss': True,  'qais': True,  'heatmap': True,  'crystal': True},
    'perspective': {'filesystem': True, 'iss': False, 'qais': True,  'heatmap': True,  'crystal': True},
    'library':     {'filesystem': True, 'iss': False, 'qais': False, 'heatmap': False, 'crystal': False},
}

TOOL_CAPABILITY = {
    'iss_analyze': 'iss', 'iss_compare': 'iss', 'iss_limbic': 'iss', 'iss_status': 'iss',
    'qais_resonate': 'qais', 'qais_exists': 'qais', 'qais_store': 'qais',
    'qais_stats': 'qais', 'qais_get': 'qais', 'qais_passthrough': 'qais',
    'heatmap_touch': 'heatmap', 'heatmap_hot': 'heatmap',
    'heatmap_chunk': 'heatmap', 'heatmap_clear': 'heatmap',
    'crystal': 'crystal', 'bond_gate': 'crystal',
}

def get_active_entity():
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

def validate_tool_call(tool_name):
    entity, entity_class = get_active_entity()
    if not entity or not entity_class:
        return True, None
    capability = TOOL_CAPABILITY.get(tool_name)
    if capability is None:
        return True, None
    allowed = CLASS_TOOLS.get(entity_class, CLASS_TOOLS['library'])
    if allowed.get(capability, False):
        return True, None
    return False, {
        'blocked': True, 'tool': tool_name, 'capability': capability,
        'entity': entity, 'entity_class': entity_class,
        'reason': f"Tool '{tool_name}' requires '{capability}' capability, "
                  f"which is not permitted for {entity_class}-class entity '{entity}'.",
    }
