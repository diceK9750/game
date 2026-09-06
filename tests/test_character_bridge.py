import json
import unittest
from types import SimpleNamespace
from character_layer import CharacterLayer


class Root:
    def __init__(self):
        self.attributes = {}
        self.writes = 0

    def getAttribute(self, key):
        return self.attributes.get(key)

    def setAttribute(self, key, value):
        self.attributes[key] = value
        self.writes += 1


class CharacterBridgeTests(unittest.TestCase):
    def test_native_mode_and_readiness(self):
        self.assertFalse(CharacterLayer().ready)
        root = Root()
        bridge = CharacterLayer(SimpleNamespace(documentElement=root))
        self.assertFalse(bridge.ready)
        root.attributes['data-character-ready'] = 'true'
        self.assertTrue(bridge.ready)

    def test_only_changes_are_sent_without_changing_game_state(self):
        root = Root()
        bridge = CharacterLayer(SimpleNamespace(documentElement=root))
        for _ in range(60):
            bridge.sync('playing', 'celebrate', 'frustrated', False)
        self.assertEqual(root.writes, 1)
        bridge.sync('confirm', 'idle', 'idle', True)
        state = json.loads(root.attributes['data-character-state'])
        self.assertEqual(state['screen'], 'confirm')
        self.assertTrue(state['reduced'])

    def test_broken_browser_bridge_is_nonfatal(self):
        bridge = CharacterLayer(SimpleNamespace(documentElement=object()))
        self.assertFalse(bridge.ready)
        bridge.sync('playing', 'idle', 'idle', False)
