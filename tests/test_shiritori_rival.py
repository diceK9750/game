"""Deterministic rival tactics; reading quality and scoring remain shared."""

import random
import unittest
from unittest.mock import Mock

from shiritori import ShiritoriRound


PROFILES = {
    'chain': {'easy': (.10, 2, 2.2), 'normal': (.65, 3, 2.2), 'hard': (.90, 5, 2.2)},
    'speed': {'easy': (.05, 2, 2.0), 'normal': (.40, 2, 1.6), 'hard': (.70, 4, 1.3)},
    'counter': {'easy': (.05, 2, 2.2), 'normal': (.50, 3, 2.2), 'hard': (.75, 5, 2.2)},
}
POWERED = {'easy': (.15, 2, 2.2), 'normal': (.80, 5, 2.2), 'hard': (.95, 7, 2.2)}


class RivalTacticsTests(unittest.TestCase):
    def game(self, style='chain', difficulty='normal', mode='battle'):
        now = [0.0]
        game = ShiritoriRound(difficulty=difficulty, rival_style=style, mode=mode,
                              total=12, rng=random.Random(7), clock=lambda: now[0])
        game.start()
        return game, now

    def player_hits(self, game, now, count):
        for _ in range(count):
            now[0] += .1
            move, proof = game.chain_advice()
            self.assertTrue(proof['perfect'])
            game.command('card', move[0])
            self.assertEqual(game.history[-1]['word'], move[1])

    def cpu_turn(self, game, now):
        now[0] += game.combo_remaining() + .01
        game.update()
        self.assertEqual(game.turn, 'cpu')
        self.assertEqual(game.phase, 'playing')

    def cpu_hits(self, game, now, count):
        for _ in range(count):
            expected, proof = game.chain_advice()
            self.assertTrue(proof['perfect'])
            self.assertEqual(game.cpu_move, expected)
            now[0] = game.cpu_due
            game.update()
            self.assertEqual(game.history[-1]['owner'], 'cpu')
            self.assertEqual(game.history[-1]['word'], expected[1])

    def test_default_chain_and_invalid_style_preserve_published_balance(self):
        self.assertEqual(ShiritoriRound().rival_style, 'chain')
        self.assertEqual(ShiritoriRound(rival_style='unknown').rival_style, 'chain')
        for difficulty in PROFILES['chain']:
            game, _ = self.game(difficulty=difficulty)
            self.assertEqual(game.cpu_profile(), PROFILES['chain'][difficulty])
            self.assertEqual(game.cpu_profile()[:2],
                             (game.CPU_CONTINUE_CHANCE[difficulty], game.CPU_MAX_STREAK[difficulty]))
            self.assertEqual(game.cpu_delay(), game.CPU_ANSWER_DELAY)

    def test_each_style_and_difficulty_has_exact_base_profile(self):
        for style, levels in PROFILES.items():
            for difficulty, expected in levels.items():
                with self.subTest(style=style, difficulty=difficulty):
                    game, now = self.game(style, difficulty)
                    self.assertEqual(game.cpu_profile(), expected)
                    self.player_hits(game, now, 1)
                    self.cpu_turn(game, now)
                    self.assertAlmostEqual(game.cpu_due-now[0], expected[2])
                    self.assertEqual(game.snapshot()['effective_cpu_delay'], expected[2])

    def test_all_styles_keep_certified_perfect_openings_and_capture_scoring(self):
        for style in PROFILES:
            for total in (12, 24, 36, 48):
                for mode in ('battle', 'solo'):
                    with self.subTest(style=style, total=total, mode=mode):
                        game = ShiritoriRound(rival_style=style, total=total, mode=mode,
                                              rng=random.Random(7), clock=lambda: 0)
                        game.start()
                        self.assertEqual(len(game.initial_perfect_route), total)
                        _, proof = game.chain_advice()
                        self.assertTrue(proof['perfect'])
        for style in PROFILES:
            with self.subTest(style=style, score=True):
                game, now = self.game(style)
                self.player_hits(game, now, 1)
                self.cpu_turn(game, now)
                game.rng.random = Mock(return_value=1.0)
                self.cpu_hits(game, now, 1)
                self.assertEqual((game.snapshot()['you_count'], game.snapshot()['cpu_count']), (1, 1))
                self.assertEqual(game.winner_by_captures(), 'draw')

    def test_threshold_boundary_uses_profile_without_changing_answer_quality(self):
        for style, levels in PROFILES.items():
            for difficulty, (chance, maximum, delay) in levels.items():
                with self.subTest(style=style, difficulty=difficulty):
                    game, now = self.game(style, difficulty)
                    self.player_hits(game, now, 1)
                    self.cpu_turn(game, now)
                    game.rng.random = Mock(return_value=chance)
                    self.cpu_hits(game, now, 1)
                    self.assertEqual(game.turn, 'you')
                    self.assertEqual(game.chain.players['cpu']['best'], 1)
                    game.rng.random.assert_called_once()
                    self.assertEqual(game.mistakes, 0)

    def test_three_does_not_trigger_four_readies_next_cpu_turn_once(self):
        game, now = self.game('counter', 'normal')
        self.player_hits(game, now, 3)
        self.assertFalse(game.counter_ready)
        self.player_hits(game, now, 1)
        self.assertTrue(game.counter_ready)
        self.assertFalse(game.counter_active)
        self.assertEqual(game.snapshot()['counter_event'], 0)
        self.cpu_turn(game, now)
        self.assertFalse(game.counter_ready)
        self.assertTrue(game.counter_active)
        self.assertEqual(game.counter_event, 1)
        self.assertEqual(game.cpu_profile(), POWERED['normal'])
        game.rng.random = Mock(return_value=1.0)
        self.cpu_hits(game, now, 1)
        self.assertEqual(game.turn, 'you')
        self.assertFalse(game.counter_active)
        self.assertEqual(game.counter_event, 1)
        self.player_hits(game, now, 1)
        self.cpu_turn(game, now)
        self.assertFalse(game.counter_active)
        self.assertEqual(game.counter_event, 1)
        self.assertEqual(game.cpu_profile(), PROFILES['counter']['normal'])

    def test_counter_caps_and_cpu_owned_fever(self):
        for difficulty, (_, maximum, _) in POWERED.items():
            with self.subTest(difficulty=difficulty):
                game, now = self.game('counter', difficulty)
                self.player_hits(game, now, 4)
                self.cpu_turn(game, now)
                game.rng.random = Mock(return_value=0.0)
                self.cpu_hits(game, now, maximum)
                self.assertEqual(game.chain.players['cpu']['best'], maximum)
                self.assertEqual(game.rng.random.call_count, maximum-1)
                if difficulty == 'hard':
                    self.assertTrue(game.cpu_fever_hold)
                    self.assertEqual(game.turn, 'cpu')
                    self.assertEqual(game.snapshot()['chain']['cpu']['tier'], 3)
                    self.assertEqual(game.snapshot()['chain']['you']['tier'], 0)
                    now[0] += game.CPU_FEVER_HOLD + .01
                    game.update()
                self.assertEqual(game.turn, 'you')
                self.assertFalse(game.counter_active)
                self.assertFalse(game.cpu_fever_hold)

    def test_powered_hard_counter_tolerates_browser_update_jitter(self):
        for lag, expected in ((0, 7), (.04, 7), (.06, 7), (.1, 7), (.2, 7), (.3, 6)):
            with self.subTest(lag=lag):
                game, now = self.game('counter', 'hard')
                self.player_hits(game, now, 4)
                self.cpu_turn(game, now)
                game.rng.random = Mock(return_value=0.0)
                for _ in range(6):
                    now[0] = game.cpu_due + lag
                    game.update()
                self.assertEqual(game.chain.players['cpu']['best'], 6)
                self.assertAlmostEqual(game.cpu_delay(), 2.0)
                now[0] = game.cpu_due + lag
                game.update()
                self.assertEqual(game.chain.players['cpu']['best'], expected)
                self.assertEqual(game.cpu_fever_hold, expected == 7)
                if expected == 7:
                    self.assertAlmostEqual(game.snapshot()['effective_cpu_delay'], game.CPU_FEVER_HOLD)

    def test_pause_preserves_ready_active_due_and_rng(self):
        game, now = self.game('counter', 'normal')
        self.player_hits(game, now, 4)
        game.command('pause')
        self.assertTrue(game.counter_ready)
        now[0] += 100
        game.command('resume')
        self.assertTrue(game.counter_ready)
        self.cpu_turn(game, now)
        game.rng.random = Mock(return_value=0.0)
        self.cpu_hits(game, now, 1)
        self.assertEqual(game.rng.random.call_count, 1)
        event = game.counter_event
        due = game.cpu_due-now[0]
        game.command('pause')
        now[0] += 100
        game.command('resume')
        self.assertTrue(game.counter_active)
        self.assertEqual(game.counter_event, event)
        self.assertAlmostEqual(game.cpu_due-now[0], due)
        self.assertEqual(game.rng.random.call_count, 1)

    def test_restart_and_setup_clear_counter_but_solo_never_uses_it(self):
        game, now = self.game('counter', 'hard')
        self.player_hits(game, now, 4)
        game.command('pause')
        game.command('restart')
        self.assertFalse(game.counter_ready or game.counter_active)
        self.assertEqual(game.counter_event, 0)
        game.command('pause')
        game.command('setup')
        self.assertEqual(game.phase, 'intro')
        self.assertFalse(game.counter_ready or game.counter_active)
        solo, now = self.game('counter', 'hard', 'solo')
        self.player_hits(solo, now, 4)
        self.assertFalse(solo.counter_ready or solo.counter_active)
        self.assertEqual(solo.turn, 'you')
        self.assertFalse(solo.snapshot()['counter_active'])


if __name__ == '__main__':
    unittest.main()
