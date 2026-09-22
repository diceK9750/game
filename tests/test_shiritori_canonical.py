"""Display kana, actual refill witnesses, and safe identity-based rejoining."""
import random
import unittest
from unittest.mock import patch

from shiritori import (CARDS, PERFECT_CANONICAL_SEGMENT, ShiritoriRound,
                       chain_moves, chain_step, certify_route, head, tail,
                       normalize_reading, starting_route)

BY_ID = {c[0]: c for c in CARDS}


class CanonicalRouteTests(unittest.TestCase):
    def state(self, g):
        return (tuple(None if i in g.used else c for i, c in enumerate(g.cards)),
                tuple(g.stock), head(g.required), frozenset(normalize_reading(w) for w in g.seen))

    def test_exact_display_spellings_and_normalized_boundaries(self):
        for identity, word in PERFECT_CANONICAL_SEGMENT:
            self.assertEqual(BY_ID[identity][2][0], word)
        for word, expected in [('トマト', 'とまと'), ('ゴリラ', 'ごりら'),
                               ('ラッパ', 'らっぱ'), ('パセリ', 'ぱせり'),
                               ('とり', 'とり'), ('りんご', 'りんご')]:
            self.assertEqual(normalize_reading(word), expected)
        self.assertEqual(tail('ギター'), 'た')
        self.assertEqual(tail('おもチャ'), 'や')
        self.assertEqual(tail('ラッパー'), 'ぱ')
        self.assertEqual(normalize_reading('コ\u3099リラ'), 'ごりら')
        for word in ('りんご', 'しんしゅうりんご', 'すりおろしりんご', 'フルーツ'):
            self.assertIn(word, BY_ID['apple'][2])
        # The existing melon identity depicts watermelon, NOT a cantaloupe.
        self.assertEqual(BY_ID['melon'][2][0], 'すいか')

    def test_all_catalog_readings_are_kana_unique_by_pronunciation_and_head(self):
        for identity, _, words in CARDS:
            with self.subTest(identity=identity):
                self.assertGreaterEqual(len(words), 3)
                for word in words:
                    self.assertRegex(word, r'^[ぁ-ゖァ-ヶー]+$')
                self.assertEqual(len(words), len(set(map(normalize_reading, words))))
                self.assertEqual(len(words), len(set(map(head, words))))

    def test_200_seeds_each_size_mode_replay_real_refill_and_canonical_block(self):
        boards, paths = set(), set()
        for total in (12, 24, 36, 48):
            for mode in ('solo', 'battle'):
                for seed in range(200):
                    g = ShiritoriRound(total=total, mode=mode, rng=random.Random(seed), clock=lambda: 0)
                    g.start()
                    route = tuple((s.identity, s.reading) for s in g.initial_perfect_route)
                    self.assertEqual(len(route), total)
                    self.assertTrue(any(route[i:i+6] == PERFECT_CANONICAL_SEGMENT for i in range(total-5)))
                    proof = certify_route(self.state(g), route)
                    self.assertIsNotNone(proof, (total, mode, seed))
                    state = self.state(g)
                    for before, move, step in proof:
                        self.assertEqual(state, before)
                        self.assertEqual(step.key, normalize_reading(step.reading))
                        state = chain_step(state[0], state[1], state[3], move)
                        self.assertEqual(state[2], step.required)
                    self.assertFalse(any(state[0]) or state[1])
                    boards.add(tuple(c[0] for c in g.cards))
                    paths.add(route)
        self.assertGreater(len(boards), 200)
        self.assertGreater(len(paths), 20)

    def test_zero_search_budget_uses_certified_canonical_fallback(self):
        self.assertIsNone(starting_route('と', 48, set(), random.Random(4), node_budget=0))
        with patch('shiritori.starting_route', return_value=None):
            for total in (12, 24, 36, 48):
                g = ShiritoriRound(total=total, clock=lambda: 0)
                g.start()
                self.assertEqual(tuple((s.identity, s.reading) for s in g.perfect_route[:6]), PERFECT_CANONICAL_SEGMENT)
                self.assertTrue(g.chain_advice()[1]['perfect'])

    def canonical_game(self, total=48):
        with patch('shiritori.starting_route', return_value=None):
            g = ShiritoriRound(total=total, mode='solo', clock=lambda: 0, rng=random.Random(11))
            g.start()
        return g

    def test_hint_and_cpu_preserve_witness_without_search_for_full_stock_game(self):
        for mode in ('solo', 'battle'):
            g = self.canonical_game()
            g.mode = mode
            with patch('shiritori.longest_chain_move', side_effect=AssertionError('lost certificate')):
                for n in range(48):
                    move, plan = g.chain_advice()
                    self.assertTrue(plan['perfect'])
                    self.assertEqual(plan['length'], 48-n)
                    if g.turn == 'cpu':
                        g.prepare_cpu()
                        self.assertEqual(g.cpu_move, move)
                    elif g.hints:
                        g.command('hint')
                        self.assertEqual(g.hint, move[0])
                    # Exercise the actual one-tap auto-reading path, not only take().
                    if g.turn == 'you':
                        g.command('card', move[0])
                    else:
                        g.take(*g.cpu_move)
                self.assertEqual(g.phase, 'finished')
                self.assertEqual(len(g.history), 48)
                self.assertEqual(g.stock, [])
                self.assertEqual([r['word'] for r in g.history[:6]], [w for _, w in PERFECT_CANONICAL_SEGMENT])

    def test_apple_both_rejoins_certify_remaining_stock_not_just_matching_tail(self):
        for required, reading in [('し', 'しんしゅうりんご'), ('す', 'すりおろしりんご')]:
            for mode in ('solo', 'battle'):
                g = self.canonical_game()
                g.take(*g.chain_advice()[0])  # tomato
                g.take(*g.chain_advice()[0])  # bird
                g.required = required  # Another legal prefix can arrive at this head.
                g.mode = mode
                with patch('shiritori.longest_chain_move', side_effect=AssertionError('suffix should rejoin')):
                    move, plan = g.chain_advice()
                    self.assertEqual(move[1], reading)
                    self.assertTrue(plan['perfect'])
                    self.assertEqual(plan['witness'][1].reading, 'ゴリラ')
                    g.command('hint')
                    self.assertEqual(g.hint, move[0])
                    g.command('card', move[0])
                    self.assertEqual(g.required, 'ご')
                    while g.phase == 'playing':
                        g.take(*g.chain_advice()[0])
                self.assertEqual(len(g.history), 48)
                self.assertEqual([r['word'] for r in g.history[2:6]], [reading, 'ゴリラ', 'ラッパ', 'パセリ'])

    def test_player_deviation_before_hint_resynchronizes_and_keeps_display(self):
        g = self.canonical_game(12)
        for _ in range(2):
            g.take(*g.chain_advice()[0])
        g.required = 'す'
        index = next(i for i, c in enumerate(g.cards) if c[0] == 'apple')
        g.command('card', index)
        self.assertEqual(g.history[-1]['word'], 'すりおろしりんご')
        with patch('shiritori.longest_chain_move', side_effect=AssertionError('replay suffix')):
            self.assertEqual(g.chain_advice()[0][1], 'ゴリラ')

    def test_actual_legal_detours_rejoin_without_overriding_required(self):
        # Move a legal detour from after parsley to before apple. Unlike a
        # synthetic head override, every transition here is a real player tap.
        for detour, reading in [(['dragon', 'cow'], 'しんしゅうりんご'),
                                 (['squirrel'], 'すりおろしりんご')]:
            identities = [i for i, _ in PERFECT_CANONICAL_SEGMENT] + detour
            g = ShiritoriRound(mode='solo', clock=lambda: 0)
            g.cards = [BY_ID[i] for i in identities]
            g.required, g.phase = 'と', 'playing'
            original = list(PERFECT_CANONICAL_SEGMENT) + [(i, BY_ID[i][2][0]) for i in detour]
            g.remember_perfect(certify_route(self.state(g), original))
            for identity in ['tomato', 'bird'] + detour:
                index = identities.index(identity)
                self.assertIn(index, [i for i, _ in g.moves()])
                g.command('card', index)
            with patch('shiritori.longest_chain_move', side_effect=AssertionError('safe detour suffix')):
                move, plan = g.chain_advice()
                self.assertEqual(move[1], reading)
                self.assertTrue(plan['perfect'])
                g.command('hint')
                self.assertEqual(g.hint, identities.index('apple'))
                for identity in ['apple', 'gorilla', 'trumpet', 'parsley']:
                    g.command('card', identities.index(identity))
            self.assertEqual(g.phase, 'finished')
            self.assertEqual(g.winner, 'you')
            self.assertEqual([r['word'] for r in g.history[-4:]], [reading, 'ゴリラ', 'ラッパ', 'パセリ'])

    def test_physical_shuffle_resolves_identity_not_old_index(self):
        g = self.canonical_game()
        g.cards.reverse()
        with patch('shiritori.longest_chain_move', side_effect=AssertionError('identity proof')):
            move, plan = g.chain_advice()
        self.assertEqual(g.cards[move[0]][0], 'tomato')
        self.assertTrue(plan['perfect'])

    def test_seen_spelling_variants_block_moves_and_rescue_uses_keys(self):
        self.assertFalse(chain_moves([BY_ID['gorilla']], 'ゴ', {'ごりら'}))
        self.assertFalse(chain_moves([BY_ID['gorilla']], 'ご', {'ゴリラ'}))
        self.assertEqual(chain_moves([BY_ID['tomato']], 'と', set()), [(0, 'トマト')])
        cards = (BY_ID['apple'], BY_ID['cat'])
        after = chain_step(cards, (BY_ID['tree'], BY_ID['gorilla']), frozenset(), (0, 'りんご'))
        self.assertEqual(after[0][0][0], 'gorilla')
        self.assertEqual(after[2], 'ご')

    def test_invalid_suffix_is_not_certified_and_impossible_board_uses_fallback(self):
        g = self.canonical_game(12)
        g.cards = [BY_ID[k] for k in ('apple', 'gorilla', 'trumpet', 'parsley')]
        g.stock, g.used, g.seen, g.required = [], {}, {'ゴリラ'}, 'し'
        state = self.state(g)
        self.assertIsNone(certify_route(state, [('apple','しんしゅうりんご')] + list(PERFECT_CANONICAL_SEGMENT[3:])))
        from shiritori import longest_chain_move
        with patch('shiritori.longest_chain_move', wraps=longest_chain_move) as search:
            move, plan = g.chain_advice()
        search.assert_called_once()
        self.assertIn(move, g.moves())
        self.assertFalse(plan['perfect'])
        self.assertTrue(plan['exact'])

    def test_stock_membership_alone_is_not_a_certificate(self):
        # An unrelated legal board move prevents rescue of gorilla from stock.
        state = ((BY_ID['apple'], ('other', '絵', ('ごま',))),
                 (BY_ID['tree'], BY_ID['gorilla']), 'り', frozenset())
        self.assertIsNone(certify_route(state, [('apple', 'りんご'), ('gorilla', 'ゴリラ')]))


if __name__ == '__main__':
    unittest.main()
