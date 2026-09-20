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
        # Reloading game is heavy; import music SCENE_TRACKS and patch a thin adapter.
        if "game" in sys.modules:
            del sys.modules["game"]
        # Provide minimal browser stubs used at import time.
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

    def test_scene_change_waits_quiet_gap_before_play(self):
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music_pending, "menu")
        self.assertIsNone(self.app.scene_music)
        self.assertEqual(self.plays, [])
        self.pyxel.frame_count = 8
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "menu")
        self.assertIsNone(self.app.scene_music_pending)
        self.assertTrue(self.plays)


if __name__ == "__main__":
    unittest.main()
