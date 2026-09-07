import json
import random
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import game
from game_logic import BattleRound, NumberTapRound
from modern_ui import ModernUI


class Root:
    def __init__(self):
        self.attributes = {"data-modern-ready": "true"}
        self.writes = []
        self.fail_write = False

    def getAttribute(self, key):
        return self.attributes.get(key)

    def setAttribute(self, key, value):
        if self.fail_write:
            raise RuntimeError("unavailable document")
        self.attributes[key] = value
        self.writes.append((key, value))


class ModernUITests(unittest.TestCase):
    def test_saved_shiritori_settings_restore_and_changes_save_immediately(self):
        self.app.shiritori_settings={'mode':'battle','total':36,'difficulty':'hard'}
        self.queue({'action':'shiritori'})
        self.bridge.consume(self.app)
        self.assertEqual((self.app.shiritori.mode,self.app.shiritori.total,self.app.shiritori.difficulty),('battle',36,'hard'))
        game.progress.save.reset_mock()
        self.queue({'action':'sh_total','value':12})
        self.bridge.consume(self.app)
        game.progress.save.assert_called_once_with(self.app)
        self.assertTrue(self.app.storage_saved)
        game.progress.save.reset_mock()
        self.queue({'action':'sh_total','value':13})
        self.bridge.consume(self.app)
        game.progress.save.assert_not_called()

    def test_completed_draw_uses_success_music_and_storage_status_is_exposed(self):
        self.queue({'action':'shiritori'})
        self.bridge.consume(self.app)
        self.app.shiritori.history=[{}]*self.app.shiritori.total
        self.app.shiritori.finish('draw','complete')
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music,'win')
        self.app.storage_saved=False
        self.assertFalse(self.bridge.snapshot(self.app)['storage_saved'])
    def setUp(self):
        self.runtime = MagicMock()
        self.runtime.frame_count = 100
        self.runtime.btnp.return_value = False
        for patcher in (patch.object(game, "pyxel", self.runtime),
                        patch.object(game, "browser_document", None),
                        patch.object(game.progress, "load", return_value={}),
                        patch.object(game.progress, "save", return_value=True)):
            patcher.start()
            self.addCleanup(patcher.stop)
        with patch.object(game.NumberRush, "configure_sounds"):
            self.app = game.NumberRush()
        self.root = Root()
        self.bridge = ModernUI(SimpleNamespace(documentElement=self.root))
        self.app.modern_ui = self.bridge
        self.app.game_selected = True
        self.now = [0.0]
        self.serial = 0

    def start(self, kind="battle", mode="ordered"):
        self.app.play_kind = kind
        self.app.selected_max_number = 10
        self.app.start_round(mode)
        round_class = BattleRound if kind == "battle" else NumberTapRound
        self.app.round = round_class(max_number=10, rng=random.Random(31), clock=lambda: self.now[0])
        self.app.round.start(mode)

    def queue(self, *commands):
        entries = []
        for command in commands:
            self.serial += 1
            entries.append({"id": self.serial, **command})
        self.root.attributes["data-modern-commands"] = json.dumps(entries)

    def cell(self, number):
        return {"action": "cell", "index": self.app.round.board_cells.index(number)}

    def test_shiritori_launch_pause_exit_keeps_number_settings(self):
        self.app.selected_max_number = 20
        self.queue({"action": "shiritori"})
        self.bridge.consume(self.app)
        self.assertEqual(self.app.screen, "shiritori")
        self.assertEqual(self.bridge.snapshot(self.app)["shiritori"]["phase"], "intro")
        self.queue({"action": "sh_start"})
        self.bridge.consume(self.app)
        self.assertEqual(len(self.bridge.snapshot(self.app)["shiritori"]["cards"]), 24)
        self.queue({"action": "sh_exit"})
        self.bridge.consume(self.app)
        self.assertEqual(self.app.screen, "shiritori")
        self.queue({"action": "sh_pause"})
        self.bridge.consume(self.app)
        self.assertEqual(self.bridge.snapshot(self.app)["shiritori"]["cards"], [])
        self.queue({"action": "sh_exit"})
        self.bridge.consume(self.app)
        self.assertEqual(self.app.screen, "ready")
        self.assertEqual(self.app.selected_max_number, 20)

    def test_game_chooser_separates_settings_and_remembers_shiritori_choice(self):
        self.app.game_selected = False
        self.assertEqual(self.bridge.snapshot(self.app)['screen'], 'home')
        self.queue({'action':'start', 'value':'ordered'})
        self.bridge.consume(self.app)
        self.assertEqual(self.bridge.snapshot(self.app)['screen'], 'home')
        self.queue({'action':'numbers'})
        self.bridge.consume(self.app)
        self.assertEqual(self.bridge.snapshot(self.app)['screen'], 'ready')
        self.queue({'action':'home'}, {'action':'shiritori'}, {'action':'sh_total','value':48}, {'action':'sh_mode','value':'solo'}, {'action':'sh_exit'})
        self.bridge.consume(self.app)
        self.assertEqual(self.bridge.snapshot(self.app)['screen'], 'home')
        self.queue({'action':'shiritori'})
        self.bridge.consume(self.app)
        self.assertEqual(self.app.shiritori.total, 48)
        self.assertEqual(self.app.shiritori.mode, 'solo')

    def test_shiritori_auto_pause_and_native_fallback(self):
        self.queue({"action": "shiritori"}, {"action": "sh_start"})
        self.bridge.consume(self.app)
        with patch.object(game, "browser_document", SimpleNamespace(hidden=True)):
            self.assertTrue(self.app.update_visibility())
        self.assertEqual(self.app.shiritori.phase, "paused")
        self.root.attributes["data-modern-ready"] = "false"
        self.app.update_frame()
        self.assertEqual(self.app.screen, "ready")

    def test_shiritori_scene_music_uses_existing_original_tracks(self):
        self.queue({"action": "shiritori"})
        self.bridge.consume(self.app)
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "menu")
        self.app.shiritori.start()
        self.app.shiritori.command("pause")
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "wait")
        self.app.shiritori.finish("you", "test")
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "win")

    def test_native_and_broken_document_are_nonfatal(self):
        self.assertFalse(ModernUI().ready)
        ModernUI().consume(self.app)
        ModernUI().sync(object())
        broken = ModernUI(SimpleNamespace(documentElement=object()))
        self.assertFalse(broken.ready)
        broken.consume(self.app)
        broken.sync(self.app)

    def test_two_fast_taps_in_one_batch_beat_cpu_without_duplicate_native_input(self):
        self.start()
        self.now[0] = self.app.round.cpu_at + 0.01
        self.queue(self.cell(1), self.cell(2))
        self.app.update()
        self.assertEqual(self.app.round.player_points, 2)
        self.assertEqual(self.app.round.cpu_points, 0)
        self.assertEqual(self.app.round.current_target, 3)
        self.assertEqual(len(self.app.cell_effects), 2)
        self.runtime.btnp.assert_not_called()
        self.assertEqual(self.bridge.ack, 2)

    def test_wrong_cell_remains_immediately_available(self):
        self.start()
        self.queue(self.cell(2), self.cell(1), self.cell(2))
        self.app.update()
        self.assertEqual(self.app.round.mistakes, 1)
        self.assertEqual(self.app.round.player_points, 2)
        self.assertEqual(self.app.round.current_target, 3)
        effects = {index: kind for kind, index, _ in self.app.cell_effects}
        self.assertEqual(effects[self.app.round.board_cells.index(2)], "correct")

    def test_every_range_order_and_difficulty_keeps_fast_input_and_results(self):
        for kind in ('battle', 'practice'):
            for count in (10, 20, 30, 40):
                for mode in ('ordered', 'random'):
                    for difficulty in (('easy', 'normal', 'hard') if kind == 'battle' else ('normal',)):
                        with self.subTest(kind=kind, count=count, mode=mode, difficulty=difficulty):
                            self.app.play_kind = kind
                            self.app.selected_max_number = count
                            self.app.difficulty = difficulty
                            self.app.start_round(mode)
                            args = dict(max_number=count, rng=random.Random(19), clock=lambda: self.now[0])
                            self.app.round = (BattleRound(difficulty=difficulty, **args) if kind == 'battle'
                                              else NumberTapRound(**args))
                            self.app.round.start(mode)
                            self.queue(*(self.cell(number) for number in self.app.round.targets))
                            self.app.update()
                            state = self.bridge.snapshot(self.app)
                            self.assertEqual((state['screen'], state['completed'], state['mistakes']),
                                             ('finished', count, 0))
                            self.assertEqual(len(state['cells']), 40)
                            self.assertEqual(sum(cell['owner'] == 'you' for cell in state['cells']), count)
                            if kind == 'battle':
                                self.assertEqual((state['player_points'], state['cpu_points'], state['bonus']),
                                                 (count, 0, count * 100))
                                self.assertTrue(state['perfect'])

    def test_invalid_indexes_and_types_cannot_touch_board(self):
        self.start()
        commands = [{"action": "cell", "index": index} for index in (-1, 40, 1000000, True, False, "1", 1.5, None, [], {})]
        self.queue(*commands, {"action": ["cell"], "index": 0})
        self.app.update()
        self.assertEqual(self.app.round.player_points, 0)
        self.assertEqual(self.app.round.mistakes, 0)
        self.assertEqual(self.bridge.ack, len(commands) + 1)

    def test_selection_and_start_are_restricted_to_ready(self):
        self.queue({"action": "kind", "value": "practice"}, {"action": "range", "value": 20},
                   {"action": "difficulty", "value": "hard"}, {"action": "start", "value": "random"})
        self.app.update()
        self.assertEqual(self.app.screen, "countdown")
        self.assertEqual((self.app.play_kind, self.app.selected_max_number, self.app.difficulty,
                          self.app.selected_mode), ("practice", 20, "hard", "random"))
        self.queue({"action": "kind", "value": "battle"}, {"action": "range", "value": 40},
                   {"action": "start", "value": "ordered"})
        self.app.update()
        self.assertEqual((self.app.play_kind, self.app.selected_max_number, self.app.selected_mode),
                         ("practice", 20, "random"))

    def test_malformed_selector_values_are_ignored(self):
        for value in (True, None, [], {}, 9, 41, "10"):
            self.queue({"action": "range", "value": value}, {"action": "kind", "value": value},
                       {"action": "difficulty", "value": value}, {"action": "start", "value": value})
            self.bridge.consume(self.app)
        self.assertEqual(self.app.screen, "ready")
        self.assertEqual((self.app.selected_max_number, self.app.play_kind, self.app.difficulty), (40, "battle", "normal"))

    def test_queue_is_bounded_and_malformed_payloads_are_ignored(self):
        for raw in ("{", "null", "{}", "x" * 65537,
                    json.dumps([{"id": i + 1, "action": "bgm"} for i in range(129)])):
            self.root.attributes["data-modern-commands"] = raw
            self.bridge.consume(self.app)
            self.assertTrue(self.app.bgm_on)
            self.assertEqual(self.root.attributes["data-modern-commands"], "[]")
        self.assertEqual(self.bridge.ack, 0)

    def test_command_ids_are_monotonic_and_deduplicated(self):
        self.root.attributes["data-modern-commands"] = json.dumps([
            {"id": True, "action": "bgm"}, {"id": "1", "action": "bgm"},
            {"id": 1.1, "action": "bgm"}, {"id": -1, "action": "bgm"},
            {"id": 1, "action": "bgm"}, {"id": 1, "action": "bgm"},
            {"id": ModernUI.MAX_ID + 1, "action": "bgm"}])
        self.bridge.consume(self.app)
        self.assertFalse(self.app.bgm_on)
        self.assertEqual(self.bridge.ack, 1)
        self.root.attributes["data-modern-commands"] = '[{"id":1,"action":"bgm"}]'
        self.bridge.consume(self.app)
        self.assertFalse(self.app.bgm_on)

    def test_failed_queue_drain_does_not_execute_or_acknowledge(self):
        self.queue({"action": "bgm"})
        self.root.fail_write = True
        self.bridge.consume(self.app)
        self.bridge.sync(self.app)
        self.assertTrue(self.app.bgm_on)
        self.assertEqual(self.bridge.ack, 0)

    def test_snapshot_failure_releases_modern_renderer(self):
        self.bridge.sync(object())
        self.assertFalse(self.bridge.ready)

    def test_finished_elapsed_keeps_centisecond_precision(self):
        self.start("practice")
        self.now[0] = 12.347
        self.queue(*(self.cell(number) for number in range(1, 11)))
        self.app.update()
        self.assertEqual(self.bridge.snapshot(self.app)["elapsed"], 12.35)

    def test_pause_resume_keeps_round_frozen_until_countdown_ends(self):
        self.start()
        self.queue({"action": "pause"})
        self.app.update()
        self.assertEqual((self.app.screen, self.app.confirm_action), ("confirm", "pause"))
        self.assertTrue(self.app.round.is_paused)
        self.now[0] = 30.0
        self.queue({"action": "yes"}, self.cell(1))
        self.app.update()
        self.assertEqual(self.app.screen, "resuming")
        self.assertEqual(self.app.round.player_points, 0)
        self.runtime.frame_count = self.app.resume_end_frame
        self.app.update()
        self.assertEqual(self.app.screen, "playing")
        self.assertFalse(self.app.round.is_paused)
        self.assertEqual(self.app.round.elapsed(), 0)

    def test_paused_retry_and_title_require_confirmation(self):
        for action, screen in (("retry", "countdown"), ("title", "ready")):
            self.start()
            self.queue({"action": "pause"}, {"action": action})
            self.app.update()
            self.assertEqual(self.app.screen, "confirm")
            self.assertEqual(self.app.confirm_action, action)
            self.assertTrue(self.app.round.is_paused)
            self.queue({"action": "yes"})
            self.app.update()
            self.assertEqual(self.app.screen, screen)

    def test_countdown_cancellation_and_help(self):
        self.queue({"action": "help"}, {"action": "start", "value": "ordered"})
        self.app.update()
        self.assertEqual(self.app.screen, "help")
        self.queue({"action": "back"}, {"action": "start", "value": "ordered"}, {"action": "title"})
        self.app.update()
        self.assertEqual(self.app.screen, "ready")

    def test_hint_only_affects_active_practice(self):
        self.start()
        self.queue({"action": "hint"})
        self.app.update()
        self.assertFalse(self.app.hint_used)
        self.start("practice")
        self.queue({"action": "hint"})
        self.app.update()
        state = self.bridge.snapshot(self.app, self.runtime.frame_count)
        self.assertTrue(state["hint_used"])
        self.assertEqual(state["hint_index"], self.app.round.board_cells.index(1))

    def test_snapshot_hides_board_targets_and_history_on_obscured_screens(self):
        self.start()
        self.queue(self.cell(1))
        self.app.update()
        state = self.bridge.snapshot(self.app, 100)
        self.assertEqual(len(state["cells"]), 40)
        self.assertEqual(state["cells"][self.app.round.board_cells.index(1)]["owner"], "you")
        self.assertEqual(state["history"], [])
        self.assertEqual(state["target"], 2)
        for screen in ("ready", "countdown", "confirm", "resuming", "help"):
            self.app.screen = screen
            state = self.bridge.snapshot(self.app, 100)
            self.assertEqual(state["cells"], [], screen)
            self.assertIsNone(state["target"], screen)
            self.assertEqual(state["history"], [], screen)

    def test_snapshot_uses_active_round_not_next_menu_selection(self):
        self.start()
        self.app.selected_max_number = 40
        self.app.selected_mode = "random"
        self.app.play_kind = "practice"
        state = self.bridge.snapshot(self.app)
        self.assertEqual((state["max_number"], state["mode"], state["kind"]), (10, "ordered", "battle"))
        self.app.screen = "ready"
        state = self.bridge.snapshot(self.app)
        self.assertEqual((state["max_number"], state["mode"], state["kind"]), (40, "random", "practice"))

    def test_snapshot_is_sent_before_handshake_and_only_on_change(self):
        self.root.attributes["data-modern-ready"] = "false"
        self.bridge.sync(self.app, 100)
        self.assertIn("data-modern-state", self.root.attributes)
        for frame in range(101, 161):
            self.bridge.sync(self.app, frame)
        self.assertEqual(len(self.root.writes), 1)
        self.assertFalse(self.bridge.ready)
        self.root.attributes["data-modern-ready"] = "true"
        self.assertTrue(self.bridge.ready)

    def test_perfect_completion_review_and_retry_preserve_awards(self):
        self.start()
        self.queue(*(self.cell(number) for number in range(1, 11)))
        self.app.update()
        self.assertEqual(self.app.screen, "finished")
        state = self.bridge.snapshot(self.app)
        self.assertTrue(state["perfect"])
        self.assertEqual((state["bonus"], state["bonus_bank"]), (1000, 1000))
        self.assertEqual(len(state["history"]), 10)
        self.queue({"action": "review"})
        self.app.update()
        self.assertEqual(self.app.screen, "review")
        self.queue({"action": "back"}, {"action": "retry"})
        self.app.update()
        self.assertEqual(self.app.screen, "countdown")
        self.assertEqual(self.app.bonus_bank, 1000)


if __name__ == "__main__":
    unittest.main()
