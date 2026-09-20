"""Countdown/scene BGM should soft-hand off into gameplay BGM with a quiet gap."""

import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock


class GameplayBgmSoftHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plays = []
        self.stops = []
        fake = types.ModuleType("pyxel")
        fake.frame_count = 100
        fake.stop = lambda ch: self.stops.append(ch)
        fake.play = lambda ch, sound, loop=False, sec=0: self.plays.append((ch, sound, loop, sec))
        fake.sounds = [MagicMock() for _ in range(64)]
        sys.modules["pyxel"] = fake
        if "game" in sys.modules:
            del sys.modules["game"]
        sys.modules.setdefault("js", types.SimpleNamespace(document=None))
        self.game = importlib.import_module("game")
        self.pyxel = fake
        app = self.game.NumberRush.__new__(self.game.NumberRush)
        app.round = self.game.NumberTapRound()
        app.screen = "playing"
        app.bgm_on = True
        app.bgm_stage = 0
        app.pending_bgm_stage = None
        app.bgm_paused = False
        app.bgm_has_started = False
        app.bgm_origin_frame = 0
        app.bgm_next_phrase_frame = 0
        app.bgm_paused_position_frames = 0
        app.bgm_audible_at = 0
        app.scene_music = "countdown"
        app.scene_music_pending = None
        app.scene_music_switch_at = 0
        self.app = app

    def test_from_scene_music_delays_audible_start_by_quiet_gap(self):
        self.app.start_bgm(0)
        self.assertTrue(self.app.bgm_has_started)
        self.assertEqual(self.app.bgm_stage, 0)
        self.assertIsNone(self.app.scene_music)
        self.assertEqual(self.app.bgm_audible_at, 108)
        self.assertEqual(self.app.current_bgm_position_frames(), 0)
        # Scene channels stopped; gameplay channels not yet started.
        self.assertTrue(self.stops)
        self.assertEqual(self.plays, [])

        self.pyxel.frame_count = 107
        self.app.update_bgm_transition()
        self.assertEqual(self.plays, [])
        self.assertEqual(self.app.bgm_audible_at, 108)

        self.pyxel.frame_count = 108
        self.app.update_bgm_transition()
        self.assertEqual(self.app.bgm_audible_at, 0)
        self.assertEqual(len(self.plays), 3)
        self.assertEqual(self.app.current_bgm_position_frames(), 0)
        self.assertEqual(self.app.bgm_next_phrase_frame, 108 + 128)

    def test_from_silence_still_starts_immediately(self):
        self.app.scene_music = None
        self.app.scene_music_pending = None
        self.app.start_bgm(0)
        self.assertEqual(self.app.bgm_audible_at, 0)
        self.assertEqual(len(self.plays), 3)
        self.assertEqual(self.app.bgm_next_phrase_frame, 100 + 128)


if __name__ == "__main__":
    unittest.main()
