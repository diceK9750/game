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
        self.assertEqual(battle.tap(battle.current_target), "inactive")

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


if __name__ == "__main__":
    unittest.main()
