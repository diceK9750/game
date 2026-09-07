import random
import unittest

from game_logic import BattleRound


class BattleTests(unittest.TestCase):
    def make_round(self, count=10, difficulty="normal", mode="random"):
        self.now = 0.0
        battle = BattleRound(max_number=count, difficulty=difficulty,
                             clock=lambda: self.now, rng=random.Random(17))
        battle.start(mode)
        return battle

    def test_all_24_combinations_and_goal(self):
        for count in (10, 20, 30, 40):
            for difficulty in BattleRound.SPEEDS:
                for mode in ("ordered", "random"):
                    with self.subTest(count=count, difficulty=difficulty, mode=mode):
                        battle = self.make_round(count, difficulty, mode)
                        self.assertEqual(len(battle.board_cells), 40)
                        self.assertEqual(battle.goal, count * 3 // 5)
                        for _ in range(count):
                            self.now = battle.ready_at + 0.1
                            battle.tap(battle.current_target)
                        self.assertTrue(battle.won)
                        self.assertTrue(battle.is_finished)
                        self.assertEqual(battle.player_points, count)
                        self.assertEqual(len(battle.owners), count)
                        self.assertTrue(battle.is_perfect)
                        self.assertEqual(battle.special_bonus, count * 100)

    def test_perfect_requires_completion_without_misses_or_cpu_claims(self):
        for fault in ("incomplete", "miss", "cpu"):
            battle = self.make_round(mode="ordered")
            if fault == "miss":
                battle.tap(2)
            elif fault == "cpu":
                self.now = battle.cpu_at
                battle.update_cpu()
            while not battle.is_finished:
                self.now = battle.ready_at + 0.1
                if fault == "incomplete" and battle.completed_count == 9:
                    break
                battle.tap(battle.current_target)
            self.assertTrue(battle.won)
            self.assertFalse(battle.is_perfect)
            self.assertEqual(battle.special_bonus, 0)

    def test_new_round_resets_perfect_award(self):
        battle = self.make_round()
        while not battle.is_finished:
            self.now = battle.ready_at + 0.1
            battle.tap(battle.current_target)
        self.assertEqual(battle.special_bonus, 1000)
        battle.start()
        self.assertFalse(battle.is_perfect)
        self.assertEqual(battle.special_bonus, 0)

    def test_cpu_can_finish_every_target_without_input(self):
        battle = self.make_round()
        for _ in range(10):
            self.now = battle.cpu_at
            self.assertIsNotNone(battle.update_cpu())
        self.assertTrue(battle.is_finished)
        self.assertFalse(battle.won)
        self.assertEqual(battle.cpu_points, 10)
        self.assertIsNone(battle.update_cpu())

    def test_same_frame_player_wins_and_no_double_claim(self):
        battle = self.make_round()
        self.now = battle.cpu_at
        target = battle.current_target
        self.assertEqual(battle.tap(target), "correct")
        self.assertIsNone(battle.update_cpu())
        self.assertEqual(battle.owners[target], "you")
        self.assertEqual(battle.tap(target), "empty")
        self.assertEqual(battle.player_points, 1)
        self.assertEqual(battle.tap(battle.current_target), "correct")
        self.assertEqual(battle.player_points, 2)

    def test_pause_preserves_cpu_deadline(self):
        battle = self.make_round()
        deadline = battle.cpu_at
        self.now = 1
        battle.pause()
        self.now = 200
        self.assertIsNone(battle.update_cpu())
        self.assertEqual(battle.tap(battle.current_target), "inactive")
        battle.resume()
        self.assertEqual(battle.elapsed(), 1)
        self.assertEqual(battle.cpu_at, deadline)
        self.assertIsNone(battle.update_cpu())

    def test_wrong_cell_remains_selectable(self):
        battle = self.make_round(mode="ordered")
        deadline = battle.cpu_at
        self.assertEqual(battle.tap(2), "wrong")
        self.assertAlmostEqual(battle.cpu_at, deadline - 0.3)
        battle.tap(1)
        self.now = battle.ready_at
        self.assertEqual(battle.tap(2), "correct")
        self.assertEqual(battle.player_points, 2)

    def test_repeated_miss_penalty_is_capped_per_target(self):
        battle = self.make_round(mode="ordered")
        deadline = battle.cpu_at
        for _ in range(8):
            battle.tap(2)
        self.assertAlmostEqual(battle.cpu_at, deadline - 0.3)
        battle.tap(1)
        self.assertEqual(battle.history[0]["mistakes"], 8)
        self.assertEqual(battle.history[0]["owner"], "you")
        self.now = battle.ready_at
        deadline = battle.cpu_at
        battle.tap(3)
        self.assertAlmostEqual(battle.cpu_at, deadline - 0.3)

    def test_history_accounts_for_cpu_and_excludes_transition_time(self):
        battle = self.make_round(mode="ordered")
        self.now = 0.5
        battle.tap(1)
        self.now = battle.cpu_at
        battle.update_cpu()
        self.assertEqual([x["owner"] for x in battle.history], ["you", "cpu"])
        self.assertEqual(battle.history[0]["seconds"], 0.5)
        self.assertGreater(battle.history[1]["seconds"], 0)
        battle.start()
        self.assertEqual(battle.history, [])

    def test_miss_does_not_extend_an_imminent_deadline(self):
        battle = self.make_round(mode="ordered")
        deadline = battle.cpu_at
        self.now = deadline - 0.1
        battle.tap(2)
        self.assertLessEqual(battle.cpu_at, deadline)

    def test_empty_and_owned_cells_do_not_count_as_misses(self):
        battle = self.make_round(mode="ordered")
        self.assertEqual(battle.tap(None), "empty")
        battle.tap(1)
        self.now = battle.ready_at
        self.assertEqual(battle.tap(1), "empty")
        self.assertEqual(battle.mistakes, 0)

    def test_exact_threshold_wins_and_one_below_loses(self):
        for player_count in (5, 6):
            battle = self.make_round()
            for i in range(10):
                if i < player_count:
                    self.now = battle.ready_at
                    battle.tap(battle.current_target)
                else:
                    self.now = battle.cpu_at
                    battle.update_cpu()
            self.assertEqual(battle.won, player_count == 6)
            self.assertEqual(battle.player_points + battle.cpu_points, 10)

    def test_restart_resets_ownership_and_statistics(self):
        battle = self.make_round()
        battle.tap(battle.current_target)
        battle.start()
        self.assertEqual(battle.owners, {})
        self.assertEqual(battle.response_times, [])
        self.assertEqual(battle.player_points, 0)
        self.assertEqual(battle.cpu_points, 0)

    def test_search_cursor_is_cosmetic_and_walks_adjacent_cells(self):
        battle = self.make_round()
        deadline = battle.cpu_at
        for t in (0, 0.3, 0.7, 1):
            self.now = t
            index = battle.cpu_cursor
            self.assertIn(index, range(40))
            self.assertEqual(battle.cpu_at, deadline)
            self.assertEqual(battle.completed_count, 0)
        battle.tap(battle.current_target)
        self.assertIsNotNone(battle.cpu_cursor)
        self.now = battle.ready_at
        previous = battle.cpu_cursor
        duration = battle.cpu_at - battle.ready_at
        for step in range(1, 9):
            self.now = battle.ready_at + duration * (step / 9 + .0001)
            index = battle.cpu_cursor
            self.assertEqual(abs(index % 8 - previous % 8) + abs(index // 8 - previous // 8), 1)
            previous = index
        self.assertEqual(battle.board_cells[previous], battle.current_target)

    def test_search_cursor_freezes_during_pause(self):
        battle = self.make_round()
        battle.pause()
        index = battle.cpu_cursor
        self.now += 100
        self.assertEqual(battle.cpu_cursor, index)

    def test_victory_line_and_remaining_chances(self):
        battle = self.make_round()
        self.assertEqual(battle.points_needed, 6)
        self.assertTrue(battle.can_still_win)
        for _ in range(5):
            self.now = battle.cpu_at
            battle.update_cpu()
        self.assertFalse(battle.can_still_win)
        self.assertEqual(battle.points_needed, 6)

    def test_response_feedback_excludes_result_hold(self):
        battle = self.make_round(mode="ordered")
        self.now = 0.5
        battle.tap(1)
        self.assertEqual(battle.last_response, 0.5)
        self.now = battle.ready_at + 0.4
        battle.tap(2)
        self.assertAlmostEqual(battle.last_response, 0.4)

    def test_rapid_inputs_in_all_ranges_and_modes(self):
        for count in (10, 20, 30, 40):
            for mode in ("ordered", "random"):
                battle = self.make_round(count=count, mode=mode)
                for i in range(count):
                    self.now += 0.03  # Much shorter than the former 0.65s lock.
                    self.assertEqual(battle.tap(battle.current_target),
                                     "finished" if i == count - 1 else "correct")
                    self.assertIsNone(battle.update_cpu())
                self.assertTrue(battle.is_perfect)
                self.assertAlmostEqual(battle.elapsed(), count * 0.03)
                for response in battle.response_times:
                    self.assertAlmostEqual(response, 0.03)

    def test_immediate_input_after_cpu_claim(self):
        battle = self.make_round()
        self.now = battle.cpu_at
        battle.update_cpu()
        self.now += 0.01
        self.assertEqual(battle.tap(battle.current_target), "correct")
        self.assertEqual((battle.player_points, battle.cpu_points), (1, 1))


if __name__ == "__main__":
    unittest.main()
