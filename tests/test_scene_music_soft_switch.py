import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock


class SceneMusicSoftSwitchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plays = []
        self.stops = []
        fake = types.ModuleType("pyxel")
        fake.frame_count = 0
        fake.stop = lambda ch: self.stops.append(ch)
        fake.play = lambda ch, sound, loop=False, sec=0: self.plays.append((ch, sound, loop))
        fake.sounds = [MagicMock() for _ in range(64)]
        sys.modules["pyxel"] = fake
        if "game" in sys.modules:
            del sys.modules["game"]
        sys.modules.setdefault("js", types.SimpleNamespace(document=None))
        self.game = importlib.import_module("game")
        self.pyxel = fake
        app = self.game.NumberRush.__new__(self.game.NumberRush)
        app.bgm_on = True
        app.screen = "ready"
        app.scene_music = None
        app.scene_music_pending = None
        app.scene_music_switch_at = 0
        app.result_music_after = 0
        app.round = None
        app.shiritori = types.SimpleNamespace(phase="setup", winner=None, history=[], total=12, mode="solo")
        self.app = app

    def test_silence_starts_immediately_and_switch_uses_quiet_gap(self):
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "menu")
        self.assertIsNone(self.app.scene_music_pending)
        self.assertTrue(self.plays)
        self.plays.clear()

        self.app.screen = "confirm"
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "wait")
        self.assertEqual(self.app.scene_music_pending, "wait")
        self.assertEqual(self.plays, [])

        self.pyxel.frame_count = 8
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "wait")
        self.assertIsNone(self.app.scene_music_pending)
        self.assertTrue(self.plays)


if __name__ == "__main__":
    unittest.main()
