"""pause_bgm soft path defers channel stop; mute/clock paths stay instant."""

import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock


class PauseBgmSoftStopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plays = []
        self.stops = []
        fake = types.ModuleType("pyxel")
        fake.frame_count = 200
        fake.stop = lambda ch: self.stops.append(ch)
        fake.play = lambda ch, sound, loop=False, sec=0: self.plays.append(
            (ch, sound, loop, sec)
        )
        fake.sounds = [MagicMock() for _ in range(64)]
        sys.modules["pyxel"] = fake
        if "game" in sys.modules:
            del sys.modules["game"]
        sys.modules.setdefault("js", types.SimpleNamespace(document=None))
        self.game = importlib.import_module("game")
        self.pyxel = fake
        app = self.game.NumberRush.__new__(self.game.NumberRush)
        app.bgm_on = True
        app.screen = "playing"
        app.scene_music = None
        app.scene_music_pending = None
        app.scene_music_switch_at = 0
        app.result_music_after = 0
        app.round = types.SimpleNamespace(
            pause=lambda: None,
            resume=lambda: None,
            is_paused=False,
            completed_count=0,
            max_number=20,
        )
        app.shiritori = types.SimpleNamespace(
            phase="setup", winner=None, history=[], total=12, mode="solo"
        )
        app.bgm_paused = False
        app.bgm_has_started = True
        app.bgm_stage = 1
        app.bgm_audible_at = 0
        app.bgm_channel_stop_at = 0
        app.pending_bgm_stage = 2
        app.bgm_origin_frame = 150
        app.bgm_next_phrase_frame = 278
        app.bgm_paused_position_frames = 0
        app.confirm_action = None
        app.resume_end_frame = 0
        self.app = app

    def test_hard_pause_stops_immediately_and_preserves_position(self):
        self.app.pause_bgm()
        self.assertTrue(self.app.bgm_paused)
        self.assertEqual(self.app.bgm_paused_position_frames, 50)
        self.assertEqual(self.app.bgm_channel_stop_at, 0)
        self.assertEqual(self.stops, [0, 1, 2])
        self.assertEqual(self.app.pending_bgm_stage, 2)
        self.pyxel.frame_count += 40
        self.assertEqual(self.app.current_bgm_position_frames(), 50)

    def test_soft_pause_defers_stop_then_flushes(self):
        self.app.pause_bgm(soft=True)
        release = self.game.PAUSE_BGM_RELEASE_FRAMES
        self.assertTrue(self.app.bgm_paused)
        self.assertEqual(self.app.bgm_paused_position_frames, 50)
        self.assertEqual(self.app.bgm_channel_stop_at, 200 + release)
        self.assertEqual(self.stops, [])
        self.pyxel.frame_count = 200 + release - 1
        self.app._flush_bgm_channel_stop()
        self.assertEqual(self.stops, [])
        self.pyxel.frame_count = 200 + release
        self.app._flush_bgm_channel_stop()
        self.assertEqual(self.stops, [0, 1, 2])
        self.assertEqual(self.app.bgm_channel_stop_at, 0)
        self.assertEqual(self.app.current_bgm_position_frames(), 50)

    def test_resume_cancels_pending_soft_stop_without_double_music(self):
        self.app.pause_bgm(soft=True)
        self.stops.clear()
        self.plays.clear()
        # Resume before release fires: must silence bleed then soft-start.
        self.app.scene_music = "wait"
        self.app.resume_bgm()
        self.assertFalse(self.app.bgm_paused)
        self.assertEqual(self.app.bgm_channel_stop_at, 0)
        # Cancelled pending stop silenced channels; scene soft handoff defers play.
        # cancel soft-stop + stop_scene_music may both silence channels.
        self.assertGreaterEqual(len(self.stops), 3)
        self.assertEqual(self.stops[:3], [0, 1, 2])
        self.assertEqual(self.plays, [])
        self.assertEqual(self.app.bgm_audible_at, self.pyxel.frame_count + 8)
        self.assertEqual(self.app.current_bgm_position_frames(), 50)
        self.assertEqual(self.app.pending_bgm_stage, 2)

        self.pyxel.frame_count = self.app.bgm_audible_at
        self.app.update_bgm_transition()
        self.assertEqual(len(self.plays), 3)
        self.assertEqual(self.app.current_bgm_position_frames(), 50)

    def test_stop_bgm_clears_pending_soft_stop(self):
        self.app.pause_bgm(soft=True)
        self.stops.clear()
        self.app.stop_bgm()
        self.assertEqual(self.app.bgm_channel_stop_at, 0)
        self.assertFalse(self.app.bgm_paused)
        self.assertFalse(self.app.bgm_has_started)
        self.assertEqual(self.stops, [0, 1, 2])

    def test_flush_getattr_safe_on_bare_stub(self):
        bare = self.game.NumberRush.__new__(self.game.NumberRush)
        # Intentionally omit bgm_channel_stop_at.
        bare._flush_bgm_channel_stop()
        bare._cancel_bgm_channel_stop(stop_now=True)
        self.assertEqual(self.stops, [])


if __name__ == "__main__":
    unittest.main()
