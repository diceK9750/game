"""Battle combo turn ownership, with an injected clock and certified moves."""

import random
import unittest
from unittest.mock import patch

from shiritori import ShiritoriRound
from timed_chain import TimedChain


class BattleTurnComboTests(unittest.TestCase):
    def setUp(self):
        self.now = [0.0]
        self.game = ShiritoriRound(total=12, mode='battle', rng=random.Random(7),
                                   clock=lambda: self.now[0])
        self.game.start()

    def player_hit(self, delay=0.1):
        self.now[0] += delay
        move, plan = self.game.chain_advice()
        self.assertTrue(plan['perfect'])
        self.game.command('card', move[0])
        self.assertEqual(self.game.history[-1]['word'], move[1])

    def expire_combo(self):
        self.now[0] += self.game.combo_remaining() + 0.01
        self.game.update()

    def test_player_two_and_three_hits_keep_turn_and_shorten_window(self):
        for count in (1, 2, 3):
            self.player_hit()
            self.assertEqual(self.game.turn, 'you')
            self.assertEqual(self.game.combo_owner, 'you')
            self.assertEqual(self.game.snapshot()['combo_owner'], 'you')
            self.assertEqual(self.game.chain.players['you']['count'], count)
            self.assertAlmostEqual(self.game.combo_remaining(), TimedChain.window(count))
        self.assertEqual([row['owner'] for row in self.game.history], ['you'] * 3)
        self.assertEqual(self.game.chain.players['you']['best'], 3)

    def test_combo_expiry_hands_off_without_defeat_and_rejects_late_tap(self):
        self.player_hit()
        next_move = self.game.chain_advice()[0]
        self.now[0] += 4.51
        self.game.command('card', next_move[0])
        self.assertEqual(len(self.game.history), 1)
        self.assertEqual(self.game.turn, 'cpu')
        self.assertEqual(self.game.phase, 'playing')
        self.assertIsNone(self.game.winner)
        self.assertIsNone(self.game.combo_owner)
        self.assertEqual(self.game.chain.players['you']['count'], 0)
        self.assertAlmostEqual(self.game.cpu_due - self.now[0], 2.2)

    def test_ordinary_deadline_and_combo_deadline_are_independent(self):
        self.now[0] = self.game.limit + 0.01
        self.game.update()
        self.assertEqual(self.game.winner, 'cpu')

        self.game.start()
        self.now[0] += self.game.limit - 0.5
        self.player_hit(0)
        ordinary_deadline = self.game.deadline
        self.now[0] += 1.0  # Ordinary time is exhausted, but the combo is open.
        self.assertGreater(self.now[0], ordinary_deadline)
        self.player_hit(0)
        self.assertEqual(self.game.phase, 'playing')
        self.assertEqual(self.game.turn, 'you')
        self.assertEqual(self.game.snapshot()['turn_remaining'], 0)
        self.expire_combo()
        self.assertEqual(self.game.turn, 'cpu')
        self.assertIsNone(self.game.winner)

    def test_wrong_card_breaks_combo_and_preserves_minus_three_rule(self):
        self.player_hit()
        self.now[0] += 1
        wrong = next(i for i in range(len(self.game.cards))
                     if i not in self.game.used and i not in {m[0] for m in self.game.moves()})
        self.game.command('card', wrong)
        self.assertEqual(self.game.mistakes, 1)
        self.assertEqual(self.game.turn, 'you')
        self.assertIsNone(self.game.combo_owner)
        self.assertEqual(self.game.chain.players['you']['count'], 0)
        self.assertAlmostEqual(self.game.deadline, 17.0)
        self.player_hit()
        self.assertEqual(self.game.chain.players['you']['count'], 1)

        self.game.start()
        self.now[0] += self.game.limit - 0.5
        self.player_hit(0)
        self.now[0] += 1
        wrong = next(i for i in range(len(self.game.cards))
                     if i not in self.game.used and i not in {m[0] for m in self.game.moves()})
        self.game.command('card', wrong)
        self.assertEqual(self.game.winner, 'cpu')

    def test_hard_cpu_uses_normal_delay_for_five_certified_answers(self):
        self.game.difficulty = 'hard'
        self.game.rng.random = lambda: 0.0
        self.player_hit()
        self.expire_combo()
        self.assertEqual(self.game.turn, 'cpu')
        for count in range(1, 6):
            expected, plan = self.game.chain_advice()
            self.assertTrue(plan['perfect'])
            self.assertEqual(self.game.cpu_move, expected)
            self.now[0] = self.game.cpu_due - .01
            self.game.update()
            self.assertEqual(len(self.game.history), count)
            self.now[0] = self.game.cpu_due
            self.game.update()
            self.assertEqual(self.game.history[-1]['owner'], 'cpu')
            self.assertEqual(self.game.history[-1]['word'], expected[1])
            if count < 5:
                self.assertEqual(self.game.chain.players['cpu']['count'], count)
                self.assertEqual(self.game.turn, 'cpu')
                self.assertAlmostEqual(self.game.combo_remaining(), TimedChain.window(count))
        self.assertEqual(self.game.turn, 'you')
        self.assertEqual(len(self.game.history), 6)
        self.assertEqual(self.game.chain.players['cpu']['best'], 5)
        self.assertIsNone(self.game.winner)

    def test_hint_during_combo_uses_next_certified_step_without_time_cost(self):
        self.player_hit()
        expected = self.game.chain_advice()[0]
        before = self.game.combo_remaining()
        original = self.game.chain_advice

        def slow_advice():
            self.now[0] += 2
            return original()

        with patch.object(self.game, 'chain_advice', side_effect=slow_advice):
            self.game.command('hint')
        self.assertEqual(self.game.hint, expected[0])
        self.assertAlmostEqual(self.game.combo_remaining(), before)
        self.player_hit(0)
        self.assertEqual(self.game.history[-1]['word'], expected[1])

    def test_hint_cannot_revive_an_already_expired_ordinary_deadline(self):
        self.now[0] = self.game.limit - .5
        self.player_hit(0)
        self.now[0] += 1
        original = self.game.chain_advice

        def slow_advice():
            self.now[0] += 2
            return original()

        with patch.object(self.game, 'chain_advice', side_effect=slow_advice):
            self.game.command('hint')
        self.assertEqual(self.game.remaining(), 0)
        wrong = next(i for i in range(len(self.game.cards))
                     if i not in self.game.used and i not in {m[0] for m in self.game.moves()})
        self.game.command('card', wrong)
        self.assertEqual(self.game.winner, 'cpu')

    def test_pause_freezes_both_combo_and_cpu_schedule(self):
        self.player_hit()
        self.now[0] += 1
        self.game.command('pause')
        before = self.game.snapshot()['combo_remaining']
        self.now[0] += 100
        self.assertEqual(self.game.snapshot()['combo_remaining'], before)
        self.game.command('resume')
        self.assertAlmostEqual(self.game.combo_remaining(), before)
        self.player_hit(0)

        self.expire_combo()
        self.now[0] += 1
        progress = self.game.snapshot()['cpu_progress']
        self.game.command('pause')
        self.now[0] += 100
        self.game.command('resume')
        self.assertAlmostEqual(self.game.snapshot()['cpu_progress'], progress)
        self.now[0] += 1.21
        self.game.update()
        self.assertEqual(self.game.history[-1]['owner'], 'cpu')

    def test_cpu_combo_and_its_next_answer_both_pause(self):
        self.game.rng.random = lambda: 0.0
        self.player_hit()
        self.expire_combo()
        self.now[0] = self.game.cpu_due
        self.game.update()
        self.assertEqual(self.game.chain.players['cpu']['count'], 1)
        self.now[0] += .5
        self.game.command('pause')
        combo_left = self.game.combo_remaining()
        due_left = self.game.saved_cpu_remaining
        self.now[0] += 100
        self.game.command('resume')
        self.assertAlmostEqual(self.game.combo_remaining(), combo_left)
        self.assertAlmostEqual(self.game.cpu_due - self.now[0], due_left)
        self.now[0] = self.game.cpu_due
        self.game.update()
        self.assertEqual(self.game.chain.players['cpu']['count'], 2)
        self.assertEqual(self.game.turn, 'cpu')

    def test_stock_refill_during_combo_keeps_certified_route(self):
        for total in (36, 48):
            with self.subTest(total=total):
                self.now[0] = 0
                game = ShiritoriRound(total=total, mode='battle', rng=random.Random(7),
                                      clock=lambda: self.now[0])
                game.start()
                game.rng.random = lambda: 0.0
                for count in range(3):
                    move, plan = game.chain_advice()
                    self.assertTrue(plan['perfect'])
                    self.now[0] += .1
                    game.command('card', move[0])
                    self.assertEqual(game.refilled, move[0])
                    self.assertEqual(game.turn, 'you')
                    self.assertEqual(game.chain.players['you']['count'], count + 1)
                self.assertTrue(game.chain_advice()[1]['perfect'])
                self.assertEqual(len(game.stock), total - 27)

                # A refilled board follows the same certified route on CPU turns.
                self.now[0] += game.combo_remaining() + .01
                game.update()
                self.assertEqual(game.turn, 'cpu')
                for _ in range(2):
                    expected, plan = game.chain_advice()
                    self.assertTrue(plan['perfect'])
                    self.now[0] = game.cpu_due
                    game.update()
                    self.assertEqual(game.history[-1]['owner'], 'cpu')
                    self.assertEqual(game.history[-1]['word'], expected[1])
                self.assertEqual(len(game.stock), total - 29)
                self.assertTrue(game.chain_advice()[1]['perfect'])

    def test_solo_remains_unlimited_and_consecutive(self):
        self.now[0] = 0
        game = ShiritoriRound(mode='solo', rng=random.Random(7), clock=lambda: self.now[0])
        game.start()
        self.now[0] = 1000
        for count in (1, 2, 3):
            move = game.chain_advice()[0]
            game.command('card', move[0])
            self.assertEqual(game.turn, 'you')
            self.assertIsNone(game.combo_owner)
            self.assertEqual(game.chain.players['you']['count'], count)
            self.now[0] += .1
