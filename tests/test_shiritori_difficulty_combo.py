"""Difficulty changes only how often the rival continues a certified combo."""

import random
import unittest
from unittest.mock import Mock, patch

from shiritori import ShiritoriRound
from timed_chain import TimedChain


class RivalDifficultyComboTests(unittest.TestCase):
    def make_game(self, difficulty='normal', seed=7, mode='battle', draws=None):
        now = [0.0]
        game = ShiritoriRound(difficulty=difficulty, total=12, mode=mode,
                              rng=random.Random(seed), clock=lambda: now[0])
        game.start()
        if draws is not None:
            game.rng.random = Mock(side_effect=draws)
        return game, now

    def enter_cpu_turn(self, game, now):
        move, plan = game.chain_advice()
        self.assertTrue(plan['perfect'])
        now[0] += .1
        game.command('card', move[0])
        now[0] += game.combo_remaining() + .01
        game.update()
        self.assertEqual(game.turn, 'cpu')
        self.assertEqual(game.phase, 'playing')

    def cpu_answer(self, game, now):
        expected, plan = game.chain_advice()
        self.assertTrue(plan['perfect'])
        self.assertEqual(game.cpu_move, expected)
        now[0] = game.cpu_due
        game.update()
        self.assertEqual(game.history[-1]['owner'], 'cpu')
        self.assertEqual(game.history[-1]['word'], expected[1])
        return expected

    def test_easy_real_seed_distribution_and_two_card_cap(self):
        two_card_rounds = 0
        for seed in range(1000):
            game, now = self.make_game('easy', seed)
            self.enter_cpu_turn(game, now)
            self.cpu_answer(game, now)
            if game.turn == 'cpu':
                two_card_rounds += 1
                self.cpu_answer(game, now)
            self.assertEqual(game.turn, 'you')
            self.assertIsNone(game.winner)
            self.assertEqual(game.mistakes, 0)
            self.assertLessEqual(game.chain.players['cpu']['best'], 2)
        self.assertGreater(two_card_rounds, 40)
        self.assertLess(two_card_rounds, 160)

    def test_easy_success_reaches_two_but_never_three(self):
        game, now = self.make_game('easy', draws=[0.0])
        self.enter_cpu_turn(game, now)
        self.cpu_answer(game, now)
        self.assertEqual(game.turn, 'cpu')
        self.assertEqual(game.chain.players['cpu']['count'], 1)
        self.cpu_answer(game, now)
        self.assertEqual(game.turn, 'you')
        self.assertEqual(game.chain.players['cpu']['best'], 2)
        self.assertEqual(game.rng.random.call_count, 1)

    def test_exact_probability_boundary_stops_for_each_difficulty(self):
        for difficulty, chance in ShiritoriRound.CPU_CONTINUE_CHANCE.items():
            with self.subTest(difficulty=difficulty):
                game, now = self.make_game(difficulty, draws=[chance])
                self.enter_cpu_turn(game, now)
                self.cpu_answer(game, now)
                self.assertEqual(game.turn, 'you')
                self.assertEqual(game.chain.players['cpu']['best'], 1)
                self.assertEqual(game.rng.random.call_count, 1)

    def test_normal_can_stop_at_one_two_or_three(self):
        for draws, expected_count, expected_draws in (([.65], 1, 1),
                                                       ([.64, .65], 2, 2),
                                                       ([.64, .64], 3, 2)):
            with self.subTest(streak=expected_count):
                game, now = self.make_game('normal', draws=draws)
                self.enter_cpu_turn(game, now)
                for _ in range(expected_count):
                    self.cpu_answer(game, now)
                self.assertEqual(game.turn, 'you')
                self.assertEqual(game.chain.players['cpu']['best'], expected_count)
                self.assertEqual(game.rng.random.call_count, expected_draws)
                self.assertEqual(game.mistakes, 0)

    def test_hard_can_reach_five_but_never_six(self):
        game, now = self.make_game('hard', draws=[.89] * 4)
        self.enter_cpu_turn(game, now)
        for count in range(1, 6):
            self.cpu_answer(game, now)
            if count < 5:
                self.assertEqual(game.turn, 'cpu')
                self.assertAlmostEqual(game.combo_remaining(), TimedChain.window(count))
        self.assertEqual(game.turn, 'you')
        self.assertEqual(game.chain.players['cpu']['best'], 5)
        self.assertEqual(game.rng.random.call_count, 4)

    def test_due_after_combo_window_hands_off_without_draw(self):
        game, now = self.make_game('hard', draws=[])
        self.enter_cpu_turn(game, now)
        original_hit = game.chain.hit

        def short_window(owner, at):
            count = original_hit(owner, at)
            game.chain.players[owner]['remaining'] = 2.1
            return count

        with patch.object(game.chain, 'hit', side_effect=short_window):
            self.cpu_answer(game, now)
        self.assertEqual(game.turn, 'you')
        self.assertIsNone(game.winner)
        self.assertEqual(game.mistakes, 0)
        game.rng.random.assert_not_called()

    def test_all_difficulties_keep_perfect_cpu_step_and_player_hint_suffix(self):
        for difficulty in ('easy', 'normal', 'hard'):
            with self.subTest(difficulty=difficulty):
                game, now = self.make_game(difficulty, draws=[.99])
                self.enter_cpu_turn(game, now)
                self.cpu_answer(game, now)
                self.assertEqual(game.turn, 'you')
                next_move, plan = game.chain_advice()
                self.assertTrue(plan['perfect'])
                game.command('hint')
                self.assertEqual(game.hint, next_move[0])
                self.assertTrue(game.chain_advice()[1]['perfect'])

    def test_pause_does_not_redraw_cpu_decision_or_advance_due(self):
        game, now = self.make_game('normal', draws=[0.0, .99])
        self.enter_cpu_turn(game, now)
        self.cpu_answer(game, now)
        self.assertEqual(game.turn, 'cpu')
        self.assertEqual(game.rng.random.call_count, 1)
        now[0] += .7
        game.command('pause')
        combo_left = game.combo_remaining()
        due_left = game.saved_cpu_remaining
        now[0] += 100
        self.assertAlmostEqual(game.combo_remaining(), combo_left)
        game.command('resume')
        self.assertAlmostEqual(game.combo_remaining(), combo_left)
        self.assertAlmostEqual(game.cpu_due - now[0], due_left)
        self.assertEqual(game.rng.random.call_count, 1)
        self.cpu_answer(game, now)
        self.assertEqual(game.turn, 'you')
        self.assertEqual(game.chain.players['cpu']['best'], 2)
        self.assertEqual(game.rng.random.call_count, 2)

    def test_solo_never_draws_cpu_continuation(self):
        for difficulty in ('easy', 'normal', 'hard'):
            with self.subTest(difficulty=difficulty):
                game, now = self.make_game(difficulty, mode='solo', draws=[])
                now[0] = 1000
                for count in (1, 2, 3):
                    game.command('card', game.chain_advice()[0][0])
                    self.assertEqual(game.turn, 'you')
                    self.assertIsNone(game.combo_owner)
                    self.assertEqual(game.chain.players['you']['count'], count)
                    now[0] += .1
                game.rng.random.assert_not_called()

    def test_player_combo_window_is_independent_of_difficulty(self):
        for difficulty in ('easy', 'normal', 'hard'):
            with self.subTest(difficulty=difficulty):
                game, now = self.make_game(difficulty, draws=[])
                for count in (1, 2, 3):
                    now[0] += .1
                    game.command('card', game.chain_advice()[0][0])
                    self.assertEqual(game.turn, 'you')
                    self.assertAlmostEqual(game.combo_remaining(), TimedChain.window(count))
                game.rng.random.assert_not_called()


if __name__ == '__main__':
    unittest.main()
