"""Battle and practice songs must keep their own phrase clock when switching."""

import importlib
import unittest
from unittest.mock import MagicMock, patch

from game_logic import BattleRound, NumberTapRound


class BattleMusicClockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Delay the import so discovery remains compatible with the suite's
        # existing fake Pyxel module, while this test can also run by itself.
        cls.game = importlib.import_module("game")

    def setUp(self):
        self.runtime = MagicMock()
        self.runtime.frame_count = 100
        runtime_patch = patch.object(self.game, "pyxel", self.runtime)
        runtime_patch.start()
        self.addCleanup(runtime_patch.stop)
        self.app = self.game.NumberRush.__new__(self.game.NumberRush)
        self.app.round = BattleRound()
        self.app.screen = "playing"
        self.app.scene_music = None
        self.app.bgm_on = True
        self.app.bgm_stage = 0
        self.app.pending_bgm_stage = None
        self.app.bgm_paused = False
        self.app.bgm_has_started = False
        self.app.bgm_origin_frame = 0
        self.app.bgm_next_phrase_frame = 0
        self.app.bgm_paused_position_frames = 0

    def test_tempo_changes_phrase_length_but_preserves_loop_duration(self):
        self.assertEqual(self.app.bgm_timing(), (96, 4608))
        self.app.round = NumberTapRound()
        self.assertEqual(self.app.bgm_timing(), (128, 4608))

    def test_stage_change_waits_for_the_matching_phrase_boundary(self):
        for round_type, phrase_frames in ((BattleRound, 96), (NumberTapRound, 128)):
            with self.subTest(round_type=round_type.__name__):
                self.runtime.frame_count = 100
                self.app.round = round_type()
                self.app.start_bgm(0)
                self.app.pending_bgm_stage = 2
                self.runtime.play.reset_mock()
                self.runtime.frame_count += phrase_frames - 1
                self.app.update_bgm_transition()
                self.runtime.play.assert_not_called()
                self.assertEqual(self.app.bgm_stage, 0)
                self.runtime.frame_count += 1
                self.app.update_bgm_transition()
                self.assertEqual(self.app.bgm_stage, 2)
                self.assertIsNone(self.app.pending_bgm_stage)
                self.assertEqual(self.app.current_bgm_position_frames(), phrase_frames)
                self.assertEqual(self.app.bgm_next_phrase_frame, 100 + 2 * phrase_frames)
                self.assertEqual(self.runtime.play.call_count, 3)
                for call in self.runtime.play.call_args_list:
                    self.assertEqual(call.kwargs, {"sec": phrase_frames / 60, "loop": True})

    def test_pause_resume_preserves_song_position_and_pending_stage(self):
        self.app.start_bgm(0)
        self.runtime.frame_count += 123
        self.app.pending_bgm_stage = 1
        self.app.pause_bgm()
        self.assertEqual(self.app.current_bgm_position_frames(), 123)
        self.runtime.frame_count += 777
        self.assertEqual(self.app.current_bgm_position_frames(), 123)
        self.app.resume_bgm()
        self.assertEqual(self.app.current_bgm_position_frames(), 123)
        self.assertEqual(self.app.pending_bgm_stage, 1)
        self.assertEqual(self.app.bgm_next_phrase_frame, self.runtime.frame_count + 69)
        self.runtime.frame_count += 68
        self.app.update_bgm_transition()
        self.assertEqual(self.app.bgm_stage, 0)
        self.runtime.frame_count += 1
        self.app.update_bgm_transition()
        self.assertEqual(self.app.bgm_stage, 1)
        self.assertEqual(self.app.current_bgm_position_frames(), 192)

    def test_loop_wrap_and_nonboundary_resume_keep_battle_alignment(self):
        self.app.start_bgm(0, 4608 + 95)
        self.assertEqual(self.app.current_bgm_position_frames(), 95)
        self.assertEqual(self.app.bgm_next_phrase_frame, 101)
        self.runtime.frame_count += 4608 - 95
        self.assertEqual(self.app.current_bgm_position_frames(), 0)
        self.app.update_bgm_transition()
        self.assertEqual(self.app.bgm_next_phrase_frame, self.runtime.frame_count + 96)

    def test_mute_pauses_and_new_round_uses_its_own_tempo(self):
        self.app.start_bgm(0)
        self.runtime.frame_count += 25
        self.app.pause_bgm()
        self.app.bgm_on = False
        self.runtime.play.reset_mock()
        self.app.resume_bgm()
        self.runtime.play.assert_not_called()
        self.app.stop_bgm()
        self.app.round = NumberTapRound()
        self.app.bgm_on = True
        self.app.resume_bgm()
        self.assertEqual(self.app.current_bgm_position_frames(), 0)
        self.assertEqual(self.app.bgm_next_phrase_frame, self.runtime.frame_count + 128)


if __name__ == "__main__":
    unittest.main()
