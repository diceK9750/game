"""Pending mid-gap retarget keeps release-then-quiet; mute stays hard."""

import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock


class PendingRetargetSoftGapTests(unittest.TestCase):
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
        app.shiritori = types.SimpleNamespace(
            phase="setup", winner=None, history=[], total=12, mode="solo"
        )
        self.app = app

    def _start_menu_to_wait_handoff(self) -> int:
        self.app.sync_scene_music()
        self.plays.clear()
        self.stops.clear()
        release = self.game.PAUSE_BGM_RELEASE_FRAMES
        self.app.screen = "confirm"
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "wait")
        self.assertEqual(self.app.scene_music_pending, "wait")
        self.assertEqual(self.app.bgm_channel_stop_at, release)
        self.assertEqual(self.app.scene_music_switch_at, release + 8)
        return release

    def test_retarget_during_release_keeps_outgoing_until_stop(self):
        release = self._start_menu_to_wait_handoff()

        # Confirm → countdown while release still pending: no hard cut.
        self.pyxel.frame_count = 1
        self.app.screen = "countdown"
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "countdown")
        self.assertEqual(self.app.scene_music_pending, "countdown")
        self.assertEqual(self.app.bgm_channel_stop_at, release)
        self.assertEqual(self.app.scene_music_switch_at, release + 8)
        self.assertEqual(self.stops, [])
        self.assertEqual(self.plays, [])

        # Deferred stop still fires on schedule.
        self.pyxel.frame_count = release
        self.app.sync_scene_music()
        self.assertEqual(self.stops, [0, 1, 2])
        self.assertEqual(self.app.bgm_channel_stop_at, 0)
        self.assertEqual(self.plays, [])
        self.assertEqual(self.app.scene_music_pending, "countdown")

        self.stops.clear()
        self.pyxel.frame_count = release + 7
        self.app.sync_scene_music()
        self.assertEqual(self.plays, [])
        self.assertEqual(self.stops, [])

        self.pyxel.frame_count = release + 8
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "countdown")
        self.assertIsNone(self.app.scene_music_pending)
        self.assertTrue(self.plays)

    def test_retarget_during_quiet_keeps_remaining_gap(self):
        release = self._start_menu_to_wait_handoff()

        self.pyxel.frame_count = release
        self.app.sync_scene_music()
        self.assertEqual(self.stops, [0, 1, 2])
        self.stops.clear()
        self.plays.clear()

        # Already quiet; retarget to countdown — no extra stops, keep remaining quiet.
        self.pyxel.frame_count = release + 3
        self.app.screen = "resuming"
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "countdown")
        self.assertEqual(self.app.scene_music_pending, "countdown")
        self.assertEqual(self.app.scene_music_switch_at, release + 8)
        self.assertEqual(self.stops, [])
        self.assertEqual(self.plays, [])

        self.pyxel.frame_count = release + 8
        self.app.sync_scene_music()
        self.assertIsNone(self.app.scene_music_pending)
        self.assertTrue(self.plays)

    def test_mute_during_pending_release_still_hard_stops(self):
        self._start_menu_to_wait_handoff()
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
