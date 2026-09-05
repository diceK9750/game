import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock, patch
from fractions import Fraction

from game_logic import BattleRound, NumberTapRound


class CapturedSound:
    def __init__(self) -> None:
        self.spec = None

    def set(self, notes, tone, volume, effect, speed) -> None:
        if self.spec is not None:
            raise AssertionError("sound slot was defined more than once")
        self.spec = (notes, tone, volume, effect, speed)


fake_pyxel = types.ModuleType("pyxel")
fake_pyxel.sounds = [CapturedSound() for _ in range(64)]
fake_pyxel.frame_count = 0
sys.modules["pyxel"] = fake_pyxel
game = importlib.import_module("game")


class BgmStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        game.NumberRush.configure_sounds()

    def test_loop_is_32_phrases_and_about_eighty_seconds(self) -> None:
        numerator = (
            game.BGM_NOTES_PER_PHRASE * game.BGM_SOUND_SPEED * game.FPS
        )
        self.assertEqual(numerator % game.PYXEL_AUDIO_TICKS_PER_SECOND, 0)
        self.assertEqual(game.BGM_PHRASE_COUNT, 32)
        self.assertEqual(game.BGM_PHRASE_FRAMES, 144)
        self.assertEqual(game.BGM_LOOP_FRAMES, 4608)
        self.assertEqual(
            Fraction(game.BGM_LOOP_FRAMES, game.FPS),
            Fraction(384, 5),
        )

    def test_all_stage_channel_sequences_have_32_phrases(self) -> None:
        for stage in range(3):
            parts = game.NumberRush.bgm_sequences(stage)
            self.assertEqual(len(parts), 3)
            self.assertEqual(
                [len(part) for part in parts],
                [game.BGM_PHRASE_COUNT] * 3,
            )

        with self.assertRaises(KeyError):
            game.NumberRush.bgm_sequences(3)

    def test_arrangement_changes_keep_melody_and_harmony(self):
        base = game.NumberRush.bgm_sequences(0)
        for stage in (1, 2):
            parts = game.NumberRush.bgm_sequences(stage)
            self.assertEqual(parts[:2], base[:2])
            self.assertNotEqual(parts[2], base[2])

    def test_melody_has_breaths_soft_tone_and_bounded_volume(self):
        for sound in game.NumberRush.bgm_sequences(0)[0]:
            notes, tone, volume, effect, _ = fake_pyxel.sounds[sound].spec
            self.assertEqual(tone, "t")
            self.assertEqual(effect, "n")
            self.assertLessEqual(max(map(int, volume)), 4)
            self.assertGreaterEqual(notes.split().count("r"), 4)
            self.assertEqual(len(volume), 32)

    def test_drums_leave_space_and_loop_ends_quietly(self):
        for stage in range(3):
            melody, bass, drums = game.NumberRush.bgm_sequences(stage)
            for sound in set(drums):
                notes, _, volume, _, _ = fake_pyxel.sounds[sound].spec
                self.assertLessEqual(max(map(int, volume)), 2)
                self.assertGreaterEqual(notes.split().count("r"), 24)
            for sound in (melody[-1], bass[-1], drums[-1]):
                notes = fake_pyxel.sounds[sound].spec[0].split()
                self.assertEqual(notes[-3:], ["r"] * 3)

    def test_every_referenced_sound_is_defined_and_has_32_notes(self) -> None:
        referenced = set()
        for stage in range(3):
            for part in game.NumberRush.bgm_sequences(stage):
                referenced.update(part)

        self.assertTrue(referenced.isdisjoint(range(5)))
        for sound_index in referenced:
            spec = fake_pyxel.sounds[sound_index].spec
            self.assertIsNotNone(spec, f"sound {sound_index} is not defined")
            notes, _tone, _volume, _effect, speed = spec
            self.assertEqual(len(notes.split()), game.BGM_NOTES_PER_PHRASE)
            self.assertEqual(speed, game.BGM_SOUND_SPEED)

    def test_melody_bass_and_drums_use_separate_sound_banks(self) -> None:
        melody_ids = set()
        bass_ids = set()
        drum_ids = set()
        for stage in range(3):
            melody, bass, drums = game.NumberRush.bgm_sequences(stage)
            melody_ids.update(melody)
            bass_ids.update(bass)
            drum_ids.update(drums)

        self.assertTrue(melody_ids.isdisjoint(bass_ids))
        self.assertTrue(melody_ids.isdisjoint(drum_ids))
        self.assertTrue(bass_ids.isdisjoint(drum_ids))

    def test_long_form_is_not_a_short_pattern_repeated(self) -> None:
        for stage in range(3):
            form = list(zip(*game.NumberRush.bgm_sequences(stage)))
            for period in (1, 2, 4, 8, 16):
                repeats = all(
                    form[index] == form[index % period]
                    for index in range(len(form))
                )
                self.assertFalse(
                    repeats,
                    f"stage {stage} repeats every {period} phrases",
                )


class BattleUiTests(unittest.TestCase):
    def setUp(self):
        self.runtime = MagicMock()
        self.runtime.frame_count = 100
        self.runtime.mouse_x = self.runtime.mouse_y = -1
        self.runtime.btnp.return_value = False
        self.runtime_patch = patch.object(game, "pyxel", self.runtime)
        self.runtime_patch.start()
        self.addCleanup(self.runtime_patch.stop)
        with patch.object(game.NumberRush, "configure_sounds"):
            self.app = game.NumberRush()

    def test_battle_and_practice_screens_render(self):
        for kind in ("battle", "practice"):
            self.app.play_kind = kind
            self.app.selected_max_number = 10
            self.app.start_round("ordered")
            for screen in ("ready", "playing", "confirm", "resuming", "countdown"):
                self.app.screen = screen
                self.app.draw()

    def test_win_and_loss_results_and_reactions(self):
        for win in (True, False):
            self.app.start_round("random")
            self.app.round.player_points = 24 if win else 0
            self.app.finish_battle()
            self.app.draw()
            self.assertEqual(self.app.screen, "finished")
            self.assertEqual(self.app.character_actions(),
                             ("victory", "defeat") if win else ("hurt", "celebrate"))

    def test_confirmation_cancel_keeps_clock_paused_until_countdown(self):
        self.app.start_round("ordered")
        self.app.open_confirmation("retry")
        self.assertTrue(self.app.round.is_paused)
        self.app.cancel_confirmation()
        self.assertEqual(self.app.screen, "resuming")
        self.assertTrue(self.app.round.is_paused)
        self.runtime.frame_count = self.app.resume_end_frame
        self.app.update()
        self.assertEqual(self.app.screen, "playing")
        self.assertFalse(self.app.round.is_paused)


class VisualFeedbackTests(unittest.TestCase):
    def setUp(self) -> None:
        fake_pyxel.frame_count = 100
        self.app = game.NumberRush.__new__(game.NumberRush)
        self.app.screen = "playing"
        self.app.wrong_cell = None
        self.app.wrong_started_frame = 0
        self.app.wrong_until_frame = 0
        self.app.correct_cell = None
        self.app.correct_started_frame = 0
        self.app.correct_until_frame = 0
        self.app.cell_effects = []
        self.app.milestone_value = 0
        self.app.milestone_until_frame = 0

    def test_characters_react_as_opponents_to_latest_result(self) -> None:
        self.app.correct_cell = 4
        self.assertEqual(
            self.app.character_actions(),
            ("celebrate", "frustrated"),
        )

        self.app.correct_cell = None
        self.app.wrong_cell = 7
        self.app.milestone_until_frame = 200
        self.assertEqual(
            self.app.character_actions(),
            ("hurt", "celebrate"),
        )

        self.app.screen = "finished"
        self.assertEqual(
            self.app.character_actions(),
            ("victory", "defeat"),
        )

    def test_clear_feedback_removes_every_temporary_effect(self) -> None:
        self.app.wrong_cell = 3
        self.app.wrong_started_frame = 90
        self.app.wrong_until_frame = 140
        self.app.correct_cell = 5
        self.app.correct_started_frame = 95
        self.app.correct_until_frame = 130
        self.app.cell_effects = [("wrong", 3, 90), ("correct", 5, 95)]
        self.app.milestone_value = 5
        self.app.milestone_until_frame = 160

        self.app.clear_feedback()

        self.assertIsNone(self.app.wrong_cell)
        self.assertIsNone(self.app.correct_cell)
        self.assertEqual(self.app.cell_effects, [])
        self.assertEqual(self.app.milestone_until_frame, 0)

    def test_effects_do_not_block_a_later_correct_tap(self) -> None:
        self.app.round = NumberTapRound(max_number=3)
        self.app.round.start("ordered")
        self.app.streak = 0
        self.app.max_streak = 0
        self.app.score = 0
        self.app.bgm_stage = 0
        self.app.pending_bgm_stage = None
        self.app.selected_mode = "ordered"
        self.app.best_times = {}
        self.app.play_sfx = lambda *args, **kwargs: None

        wrong_index = self.app.round.board_cells.index(2)
        first_target_index = self.app.round.board_cells.index(1)

        self.app.handle_tap(wrong_index)
        self.assertEqual(self.app.round.mistakes, 1)
        self.assertEqual(self.app.cell_effects[-1][0], "wrong")

        self.app.handle_tap(first_target_index)
        self.app.handle_tap(wrong_index)

        self.assertEqual(self.app.round.found_numbers, {1, 2})
        self.assertEqual(self.app.round.current_target, 3)
        self.assertEqual(self.app.cell_effects[-1][0], "correct")


if __name__ == "__main__":
    unittest.main()
