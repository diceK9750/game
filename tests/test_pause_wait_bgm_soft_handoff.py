"""Gameplay pause → confirm/wait scene BGM should use an ~8-frame quiet gap."""

import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock


class PauseWaitBgmSoftHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plays = []
        self.stops = []
        fake = types.ModuleType("pyxel")
        fake.frame_count = 100
        fake.stop = lambda ch: self.stops.append(ch)
        fake.play = lambda ch, sound, loop=False, sec=0: self.plays.append(
            (ch, sound, loop)
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
        app.scene_music = None  # cleared while playing
        app.scene_music_pending = None
        app.scene_music_switch_at = 0
        app.result_music_after = 0
        app.round = types.SimpleNamespace(
            pause=lambda: None,
            resume=lambda: None,
            is_paused=True,
            completed_count=0,
            max_number=20,
        )
        app.shiritori = types.SimpleNamespace(
            phase="setup", winner=None, history=[], total=12, mode="solo"
        )
        app.bgm_paused = False
        app.bgm_has_started = True
        app.bgm_stage = 0
        app.bgm_audible_at = 0
        app.bgm_channel_stop_at = 0
        app.pending_bgm_stage = None
        app.bgm_origin_frame = 50
        app.bgm_next_phrase_frame = 178
        app.bgm_paused_position_frames = 0
        app.confirm_action = None
        app.resume_end_frame = 0
        self.app = app

    def test_open_confirmation_delays_wait_track_by_quiet_gap(self):
        self.app.open_confirmation("pause")
        self.assertEqual(self.app.screen, "confirm")
        self.assertTrue(self.app.bgm_paused)
        self.assertEqual(self.app.bgm_paused_position_frames, 50)
        # Soft pause defers channel stop; position already frozen.
        release = self.game.PAUSE_BGM_RELEASE_FRAMES
        self.assertEqual(self.app.bgm_channel_stop_at, 100 + release)
        self.assertEqual(self.stops, [])
        self.plays.clear()
        self.stops.clear()

        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "wait")
        self.assertEqual(self.app.scene_music_pending, "wait")
        # Quiet gap starts after deferred stop so ~8 silent frames remain.
        self.assertEqual(self.app.scene_music_switch_at, 100 + release + 8)
        self.assertEqual(self.plays, [])
        self.assertEqual(self.stops, [])

        # Still releasing: channels not stopped yet.
        self.pyxel.frame_count = 100 + release - 1
        self.app.sync_scene_music()
        self.assertEqual(self.stops, [])
        self.assertEqual(self.plays, [])

        # Deferred stop fires; wait still pending through quiet gap.
        self.pyxel.frame_count = 100 + release
        self.app.sync_scene_music()
        self.assertEqual(self.stops, [0, 1, 2])
        self.assertEqual(self.app.bgm_channel_stop_at, 0)
        self.assertEqual(self.plays, [])
        self.assertEqual(self.app.scene_music_pending, "wait")

        self.stops.clear()
        self.pyxel.frame_count = 100 + release + 7
        self.app.sync_scene_music()
        self.assertEqual(self.plays, [])
        self.assertEqual(self.app.scene_music_pending, "wait")

        self.pyxel.frame_count = 100 + release + 8
        self.app.sync_scene_music()
        self.assertIsNone(self.app.scene_music_pending)
        self.assertEqual(self.app.scene_music, "wait")
        self.assertTrue(self.plays)

    def test_cancel_resume_preserves_position_without_double_music(self):
        self.app.open_confirmation("pause")
        self.app.sync_scene_music()
        paused_at = self.app.bgm_paused_position_frames
        self.plays.clear()

        self.app.cancel_confirmation()
        self.assertEqual(self.app.screen, "resuming")
        self.app.sync_scene_music()
        # Still deferred (wait→countdown soft switch); no audible wait stack.
        self.assertEqual(self.app.scene_music, "countdown")
        self.assertEqual(self.app.scene_music_pending, "countdown")
        self.assertEqual(self.plays, [])

        self.pyxel.frame_count = self.app.resume_end_frame
        self.app.screen = "playing"
        self.app.resume_bgm()
        self.assertFalse(self.app.bgm_paused)
        self.assertEqual(self.app.current_bgm_position_frames(), paused_at)
        # Scene cleared; gameplay may still be in its own quiet gap.
        self.assertIsNone(self.app.scene_music)
        self.assertIsNone(self.app.scene_music_pending)
        # No immediate channel play while soft-starting from scene handoff.
        self.assertEqual(self.plays, [])
        self.assertEqual(self.app.bgm_audible_at, self.pyxel.frame_count + 8)

        self.pyxel.frame_count = self.app.bgm_audible_at
        self.app.update_bgm_transition()
        self.assertEqual(self.app.bgm_audible_at, 0)
        self.assertEqual(len(self.plays), 3)
        self.assertEqual(self.app.current_bgm_position_frames(), paused_at)

    def test_cold_silence_still_starts_wait_immediately(self):
        self.app.bgm_paused = False
        self.app.bgm_has_started = False
        self.app.screen = "confirm"
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "wait")
        self.assertIsNone(self.app.scene_music_pending)
        self.assertTrue(self.plays)

    def test_bgm_paused_getattr_safe_on_bare_stub(self):
        bare = self.game.NumberRush.__new__(self.game.NumberRush)
        bare.bgm_on = True
        bare.screen = "confirm"
        bare.scene_music = None
        bare.scene_music_pending = None
        bare.scene_music_switch_at = 0
        bare.result_music_after = 0
        bare.round = None
        bare.shiritori = types.SimpleNamespace(
            phase="setup", winner=None, history=[], total=12, mode="solo"
        )
        # Intentionally omit bgm_paused / bgm_has_started.
        bare.sync_scene_music()
        self.assertEqual(bare.scene_music, "wait")
        self.assertIsNone(bare.scene_music_pending)
        self.assertTrue(self.plays)


if __name__ == "__main__":
    unittest.main()
