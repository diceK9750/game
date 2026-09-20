"""Scene A→B soft switches: immediate identity, deferred outgoing stop, then quiet gap."""

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
        app.bgm_channel_stop_at = 0
        app.bgm_paused = False
        app.result_music_after = 0
        app.round = None
        app.shiritori = types.SimpleNamespace(phase="setup", winner=None, history=[], total=12, mode="solo")
        self.app = app

    def test_silence_starts_immediately_and_switch_uses_release_then_quiet(self):
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "menu")
        self.assertIsNone(self.app.scene_music_pending)
        self.assertTrue(self.plays)
        self.plays.clear()
        self.stops.clear()

        release = self.game.PAUSE_BGM_RELEASE_FRAMES
        self.app.screen = "confirm"
        self.app.sync_scene_music()
        # Logical identity flips immediately; no restart yet.
        self.assertEqual(self.app.scene_music, "wait")
        self.assertEqual(self.app.scene_music_pending, "wait")
        self.assertEqual(self.app.bgm_channel_stop_at, release)
        self.assertEqual(self.app.scene_music_switch_at, release + 8)
        self.assertEqual(self.plays, [])
        self.assertEqual(self.stops, [])

        # Outgoing menu keeps sounding through the release window.
        self.pyxel.frame_count = release - 1
        self.app.sync_scene_music()
        self.assertEqual(self.stops, [])
        self.assertEqual(self.plays, [])
        self.assertEqual(self.app.scene_music, "wait")

        # Deferred stop fires; quiet gap continues before wait is audible.
        self.pyxel.frame_count = release
        self.app.sync_scene_music()
        self.assertEqual(self.stops, [0, 1, 2])
        self.assertEqual(self.app.bgm_channel_stop_at, 0)
        self.assertEqual(self.plays, [])
        self.assertEqual(self.app.scene_music_pending, "wait")

        self.stops.clear()
        self.pyxel.frame_count = release + 7
        self.app.sync_scene_music()
        self.assertEqual(self.plays, [])
        self.assertEqual(self.app.scene_music_pending, "wait")

        self.pyxel.frame_count = release + 8
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "wait")
        self.assertIsNone(self.app.scene_music_pending)
        self.assertTrue(self.plays)

    def test_mute_still_hard_stops_outgoing_scene(self):
        self.app.sync_scene_music()
        self.plays.clear()
        self.stops.clear()
        self.app.screen = "confirm"
        self.app.sync_scene_music()
        self.assertEqual(self.app.bgm_channel_stop_at, self.game.PAUSE_BGM_RELEASE_FRAMES)
        self.stops.clear()

        self.app.bgm_on = False
        self.app.sync_scene_music()
        self.assertIsNone(self.app.scene_music)
        self.assertIsNone(self.app.scene_music_pending)
        self.assertEqual(self.app.bgm_channel_stop_at, 0)
        self.assertEqual(self.stops, [0, 1, 2])
        self.assertEqual(self.plays, [])


if __name__ == "__main__":
    unittest.main()
