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

    def test_loop_is_36_phrases_and_about_eighty_seconds(self) -> None:
        numerator = (
            game.BGM_NOTES_PER_PHRASE * game.BGM_SOUND_SPEED * game.FPS
        )
        self.assertEqual(numerator % game.PYXEL_AUDIO_TICKS_PER_SECOND, 0)
        self.assertEqual(game.BGM_PHRASE_COUNT, 36)
        self.assertEqual(game.BGM_PHRASE_FRAMES, 128)
        self.assertEqual(game.BGM_LOOP_FRAMES, 4608)
        self.assertEqual(
            Fraction(game.BGM_LOOP_FRAMES, game.FPS),
            Fraction(384, 5),
        )

    def test_all_stage_channel_sequences_have_the_same_form(self) -> None:
        for stage in range(3):
            parts = game.NumberRush.bgm_sequences(stage)
            self.assertEqual(len(parts), 3)
            self.assertEqual(
                [len(part) for part in parts],
                [game.BGM_PHRASE_COUNT] * 3,
            )

        with self.assertRaises(KeyError):
            game.NumberRush.bgm_sequences(3)

    def test_scene_tracks_are_defined_synchronized_and_separate(self):
        from music import SCENE_TRACKS, SCENE_SCORES
        ids = []
        for name, pair in SCENE_TRACKS.items():
            speed, bars, roots = SCENE_SCORES[name]
            self.assertEqual(len(bars), len(roots))
            for index in pair:
                ids.append(index)
                notes, tone, volume, effect, actual_speed = fake_pyxel.sounds[index].spec
                self.assertEqual(len(notes.split()), len(bars) * 32)
                self.assertEqual(len(volume), len(bars) * 32)
                self.assertEqual(actual_speed, speed)
                self.assertLessEqual(max(map(int, volume)), 3)
                self.assertEqual(tone, "t")
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(index in (46, 47) or 54 <= index < 64 for index in ids))
        self.assertEqual(SCENE_TRACKS["perfect"], (46, 47))
        for battle in (False, True):
            for part in game.NumberRush.bgm_sequences(2, battle=battle):
                self.assertTrue(set(ids).isdisjoint(part))

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


class DuelMusicTests(unittest.TestCase):
    def test_score_form_reprise_and_articulation(self):
        from music import FORM, BATTLE_FORM, BATTLE_SCORE, SCORE, expand_bar, expand_battle_bar
        self.assertEqual(len(FORM), 36)
        self.assertEqual(FORM[-4:], (24, 25, 30, 31))
        self.assertEqual(len(BATTLE_FORM), 48)
        self.assertEqual(BATTLE_FORM[-16:], tuple(range(16)))
        for score, expand in ((SCORE, expand_bar), (BATTLE_SCORE, expand_battle_bar)):
            self.assertEqual(len(score), 32)
            for bar in score:
                notes, volumes = expand(bar)
                self.assertEqual(len(notes.split()), len(volumes))
                for note, volume in zip(notes.split(), volumes):
                    self.assertEqual(note == "r", volume == "0")

    def test_bridge_relaxes_drums_without_changing_parts(self):
        from music import sequences
        for battle in (False, True):
            melody, bass, drums = sequences(2, battle=battle)
            self.assertEqual(drums[16], 49)
            self.assertEqual(drums[24], 50)
            self.assertEqual(drums[-1], 53)
            self.assertEqual(len(melody), len(bass))

    def test_battle_score_uses_distinct_melody_and_equal_length_parts(self):
        from music import configure_bgm, sequences, BATTLE_SCORE, SCORE, BATTLE_SPEED, BATTLE_PHRASE_COUNT
        sounds = [MagicMock() for _ in range(64)]
        configure_bgm(sounds, battle=True)
        self.assertNotEqual(BATTLE_SCORE, SCORE)
        for stage in range(3):
            for part in sequences(stage, battle=True):
                self.assertEqual(len(part), BATTLE_PHRASE_COUNT)
                for index in part:
                    notes, tone, volume, effect, speed = sounds[index].set.call_args.args
                    self.assertEqual(len(notes.split()), 32)
                    self.assertEqual(speed, BATTLE_SPEED)
                    self.assertLessEqual(max(map(int, volume)), 3)
        for index in list(range(8)) + [46, 47] + list(range(54, 64)):
            sounds[index].set.assert_not_called()

    def test_switch_to_practice_restores_original_score(self):
        from music import configure_bgm
        sounds = [MagicMock() for _ in range(64)]
        configure_bgm(sounds)
        original = {i: sounds[i].set.call_args for i in range(8, 54)}
        configure_bgm(sounds, battle=True)
        self.assertNotEqual(sounds[8].set.call_args, original[8])
        configure_bgm(sounds)
        self.assertEqual({i: sounds[i].set.call_args for i in range(8, 54)}, original)

    def test_battle_arrangements_share_harmony_and_have_a_quiet_seam(self):
        from music import configure_bgm, sequences
        sounds = [MagicMock() for _ in range(64)]
        configure_bgm(sounds, battle=True)
        for stage in range(3):
            parts = sequences(stage, battle=True)
            self.assertEqual(parts[:2], sequences(0, battle=True)[:2])
            for part in parts:
                notes = sounds[part[-1]].set.call_args.args[0].split()
                self.assertEqual(notes[-3:], ['r'] * 3)

    def test_sprint_is_bright_articulated_and_has_room_for_effects(self):
        from music import BATTLE_SCORE, BATTLE_CHORDS, BATTLE_FORM, configure_bgm
        sounds = [MagicMock() for _ in range(64)]
        configure_bgm(sounds, battle=True)
        self.assertEqual(BATTLE_CHORDS[0], 'D')
        self.assertEqual(BATTLE_CHORDS[BATTLE_FORM[-1]], 'A')
        self.assertGreaterEqual(sum(':0.5' in bar for bar in BATTLE_SCORE), 6)
        allowed = {'d', 'e', 'f#', 'g', 'a', 'b', 'c#'}
        for index in range(8, 40):
            notes, tone, volumes, _, speed = sounds[index].set.call_args.args
            self.assertEqual(tone, 't')
            self.assertTrue(all(n == 'r' or n[:-1] in allowed for n in notes.split()))
            self.assertTrue(all(n == 'r' or n[-1] in '01234' for n in notes.split()))
            self.assertEqual(speed, 6)
            self.assertLessEqual(max(map(int, volumes)), 3)
        for index in range(40, 46):
            self.assertLessEqual(max(map(int, sounds[index].set.call_args.args[2])), 2)
        for bad in ('d4:0.25', 'd4:9', 'd4:0.6'):
            from music import expand_battle_bar
            with self.assertRaises(ValueError):
                expand_battle_bar(bad)


class BattleUiTests(unittest.TestCase):
    def test_success_animation_keeps_next_target_visible_and_playable(self):
        self.app.start_round("ordered")
        now = [0.0]
        self.app.round = BattleRound(max_number=10, clock=lambda: now[0])
        self.app.round.start("ordered")
        self.app.handle_tap(self.app.round.board_cells.index(1))
        self.assertIsNotNone(self.app.correct_cell)
        with patch.object(game, "draw_number") as draw_number:
            self.app.draw_message_panel()
            draw_number.assert_called_with(320, 260, 2, game.CARD, 5)
        now[0] += 0.03
        self.app.handle_tap(self.app.round.board_cells.index(2))
        self.assertEqual(self.app.round.player_points, 2)
        self.assertEqual(self.app.round.current_target, 3)
        self.assertEqual(len(self.app.cell_effects), 2)

    def test_hint_completion_is_not_a_record(self):
        self.app.play_kind = "practice"
        self.app.selected_max_number = 10
        self.app.start_round("ordered")
        self.app.hint_used = True
        for n in range(1, 11):
            self.app.handle_tap(self.app.round.board_cells.index(n))
        self.assertEqual(self.app.screen, "finished")
        self.assertEqual(self.app.best_times, {})
        self.assertFalse(self.app.is_new_best)

    def test_touch_pause_and_hint_are_separate_controls(self):
        self.app.start_round("ordered")
        self.runtime.mouse_x, self.runtime.mouse_y = game.PAUSE_BUTTON[:2]
        self.runtime.btnp.side_effect = lambda key, *args: key == self.runtime.MOUSE_BUTTON_LEFT
        self.app.update_frame()
        self.assertEqual(self.app.screen, "confirm")
        self.assertTrue(self.app.round.is_paused)
        self.app.play_kind = "practice"
        self.app.start_round("random")
        self.runtime.mouse_x, self.runtime.mouse_y = game.HINT_BUTTON[:2]
        self.app.update_frame()
        self.assertTrue(self.app.hint_used)
        self.assertGreater(self.app.hint_until, self.runtime.frame_count)

    def test_review_does_not_change_awards(self):
        self.complete_perfect()
        bank = self.app.bonus_bank
        self.runtime.btnp.side_effect = lambda key, *args: key == self.runtime.KEY_H
        self.app.update_frame()
        self.assertEqual(self.app.screen, "review")
        self.app.draw()
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "wait")
        self.assertEqual(self.app.bonus_bank, bank)

    def complete_perfect(self, count=10):
        self.app.selected_max_number = count
        self.app.start_round("ordered")
        now = [0.0]
        self.app.round = BattleRound(max_number=count, clock=lambda: now[0])
        self.app.round.start("ordered")
        while not self.app.round.is_finished:
            now[0] = self.app.round.ready_at + 0.1
            self.app.handle_tap(self.app.round.board_cells.index(self.app.round.current_target))

    def test_perfect_award_is_once_per_round_and_accumulates(self):
        self.complete_perfect()
        self.assertEqual(self.app.bonus_bank, 1000)
        self.app.finish_battle()
        for age in (0, 45, 90, 360):
            self.runtime.frame_count = self.app.result_started_frame + age
            self.app.draw()
        self.assertEqual(self.app.bonus_bank, 1000)
        self.assertEqual(self.app.round.player_points, 10)
        self.complete_perfect(20)
        self.assertEqual(self.app.bonus_bank, 3000)

    def test_perfect_music_and_fanfare_respect_mute(self):
        self.complete_perfect()
        self.assertIn(((3, 7), {}), self.runtime.play.call_args_list)
        self.runtime.frame_count = self.app.result_music_after
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "perfect")
        self.app.toggle_bgm()
        self.app.toggle_sfx()
        self.runtime.play.reset_mock()
        self.complete_perfect()
        self.app.sync_scene_music()
        self.runtime.play.assert_not_called()
        self.assertEqual(self.app.bonus_bank, 2000)

    def test_perfect_animation_never_blocks_replay_or_menu(self):
        for key in (self.runtime.KEY_RETURN, self.runtime.KEY_M):
            self.runtime.btnp.return_value = False
            self.runtime.btnp.side_effect = None
            self.complete_perfect()
            bank = self.app.bonus_bank
            self.runtime.btnp.side_effect = lambda candidate, *args: candidate == key
            self.app.update()
            self.assertEqual(self.app.screen, "countdown" if key == self.runtime.KEY_RETURN else "ready")
            self.assertEqual(self.app.bonus_bank, bank)

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

    def test_new_round_selects_the_matching_score(self):
        with patch.object(game, "configure_bgm") as configure:
            for kind in ("battle", "practice", "battle"):
                self.app.play_kind = kind
                self.app.start_round("random")
                configure.assert_called_with(self.runtime.sounds, battle=kind == "battle")

    def test_keyboard_moves_cursor_and_confirms_target(self):
        self.app.start_round("ordered")
        self.app.cursor_cell = 7
        self.runtime.btnp.side_effect = lambda key, *args: key == self.runtime.KEY_RIGHT
        self.app.update()
        self.assertEqual(self.app.cursor_cell, 0)
        self.assertTrue(self.app.keyboard_cursor)
        self.app.cursor_cell = self.app.round.board_cells.index(1)
        self.runtime.btnp.side_effect = lambda key, *args: key == self.runtime.KEY_RETURN
        self.app.update()
        self.assertEqual(self.app.round.player_points, 1)

    def test_escape_pauses_instead_of_quitting_runtime(self):
        self.assertEqual(self.runtime.init.call_args.kwargs["quit_key"], self.runtime.KEY_NONE)
        self.app.start_round("ordered")
        self.runtime.btnp.side_effect = lambda key, *args: key == self.runtime.KEY_ESCAPE
        self.app.update()
        self.assertEqual(self.app.screen, "confirm")
        self.assertEqual(self.app.confirm_action, "pause")
        self.assertTrue(self.app.round.is_paused)

    def test_pause_can_request_title_without_resuming_cpu(self):
        self.app.start_round("ordered")
        self.app.open_confirmation("pause")
        self.runtime.btnp.side_effect = lambda key, *args: key == self.runtime.KEY_T
        self.app.update()
        self.assertEqual(self.app.screen, "confirm")
        self.assertEqual(self.app.confirm_action, "title")
        self.assertTrue(self.app.round.is_paused)

    def test_help_opens_and_returns_without_starting_round(self):
        self.runtime.btnp.side_effect = lambda key, *args: key == self.runtime.KEY_H
        self.app.update()
        self.assertEqual(self.app.screen, "help")
        self.app.draw()
        self.runtime.btnp.side_effect = lambda key, *args: key == self.runtime.KEY_RETURN
        self.app.update()
        self.assertEqual(self.app.screen, "ready")
        self.assertFalse(self.app.round.is_playing)

    def test_hidden_page_pauses_and_requires_explicit_resume(self):
        self.app.start_round("ordered")
        document = types.SimpleNamespace(hidden=True)
        with patch.object(game, "browser_document", document):
            self.assertTrue(self.app.update_visibility())
            self.assertTrue(self.app.round.is_paused)
            self.assertEqual(self.app.confirm_action, "pause")
            document.hidden = False
            self.app.update()
            self.assertEqual(self.app.screen, "confirm")
            self.assertTrue(self.app.round.is_paused)
            self.app.draw()

    def test_pixel_labels_include_all_used_characters(self):
        for word in ("CPU +1", "YOU +1", "MISS", "FIND", "PERFECT"):
            for char in word.replace(" ", ""):
                self.assertTrue(char in game.LETTERS or char in game.DIGITS)

    def test_scene_selection_and_no_restart_per_frame(self):
        for screen, track in (("ready", "menu"), ("countdown", "countdown"),
                              ("confirm", "wait"), ("resuming", "countdown")):
            self.app.screen = screen
            self.app.sync_scene_music()
            self.assertEqual(self.app.scene_music, track)
            self.runtime.play.reset_mock()
            self.app.sync_scene_music()
            self.runtime.play.assert_not_called()

    def test_scene_mute_and_unmute(self):
        self.app.sync_scene_music()
        self.app.toggle_bgm()
        self.app.sync_scene_music()
        self.assertIsNone(self.app.scene_music)
        self.app.toggle_bgm()
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "menu")

    def test_resume_preserves_game_song_position(self):
        self.app.start_round("ordered")
        self.runtime.frame_count += 123
        position = self.app.current_bgm_position_frames()
        self.app.open_confirmation("retry")
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "wait")
        self.app.cancel_confirmation()
        self.app.sync_scene_music()
        self.runtime.frame_count = self.app.resume_end_frame
        self.app.update()
        self.assertEqual(self.app.current_bgm_position_frames(), position)
        self.assertIsNone(self.app.scene_music)

    def test_result_tracks_follow_jingle_and_outcome(self):
        for win in (False, True):
            self.app.start_round("random")
            self.app.round.player_points = 40 if win else 0
            self.app.finish_battle()
            self.app.sync_scene_music()
            self.assertIsNone(self.app.scene_music)
            self.runtime.frame_count = self.app.result_music_after
            self.app.sync_scene_music()
            self.assertEqual(self.app.scene_music, "win" if win else "loss")

    def test_win_and_loss_results_and_reactions(self):
        for win in (True, False):
            self.app.start_round("random")
            self.app.round.player_points = 24 if win else 0
            self.app.finish_battle()
            self.app.draw()
            self.assertEqual(self.app.screen, "finished")
            self.assertEqual(self.app.character_actions(),
                             ("victory", "defeat") if win else ("defeat", "victory"))

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
