"""Display kana, actual refill witnesses, and safe identity-based rejoining."""
import json
import random
import unittest
from pathlib import Path
from unittest.mock import patch

from shiritori import (CARDS, CONNECTION_CARDS, PERFECT_RING, PERFECT_CANONICAL_SEGMENT, ShiritoriRound,
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
        for word in ('りんご', 'しんしゅうりんご', 'フルーツ'):
            self.assertIn(word, BY_ID['apple'][2])
        # The existing melon identity depicts watermelon, NOT a cantaloupe.
        self.assertEqual(BY_ID['melon'][2][0], 'すいか')

    def test_all_catalog_readings_are_kana_unique_by_pronunciation(self):
        for identity, _, words in CARDS:
            with self.subTest(identity=identity):
                self.assertGreaterEqual(len(words), 3)
                for word in words:
                    self.assertRegex(word, r'^[ぁ-ゖァ-ヶー]+$')
                self.assertEqual(len(words), len(set(map(normalize_reading, words))))
                self.assertGreaterEqual(len(set(map(head, words))), 3)

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

    def test_48_fallback_new_cards_appear_and_refill_route_is_certified(self):
        # Exhausting the randomized search must still offer a full proof, not
        # silently revert to a 48-card deal without the newer pictures.
        witnessed_routes = set()
        with patch('shiritori.starting_route', return_value=None):
            for mode in ('solo', 'battle'):
                for seed in range(20):
                    g = ShiritoriRound(total=48, mode=mode, clock=lambda: 0,
                                       rng=random.Random(seed))
                    g.start()
                    board_ids = {card[0] for card in g.cards}
                    self.assertTrue({card[0] for card in CONNECTION_CARDS} <= board_ids)
                    route = tuple((step.identity, step.reading)
                                  for step in g.initial_perfect_route)
                    witnessed_routes.add(route)
                    self.assertEqual(route[:6], PERFECT_CANONICAL_SEGMENT)
                    self.assertEqual(len({identity for identity, _ in route}), 48)
                    self.assertIsNotNone(certify_route(self.state(g), route))
                    while g.phase == 'playing':
                        move, plan = g.chain_advice()
                        self.assertTrue(plan['perfect'])
                        g.take(*move)
                    self.assertEqual(len(g.history), 48)
                    self.assertEqual(g.stock, [])
        self.assertGreaterEqual(len(witnessed_routes), 2)

    def test_48_search_without_visible_new_pictures_uses_certified_fallback(self):
        route = [(key, BY_ID[key][2][0]) for key in PERFECT_RING[:48]]
        self.assertFalse({card[0] for card in CONNECTION_CARDS} &
                         {identity for identity, _ in route[:24]})
        with patch('shiritori.starting_route', return_value=route):
            game = ShiritoriRound(total=48, rng=random.Random(9), clock=lambda: 0)
            game.start()
        self.assertTrue({card[0] for card in CONNECTION_CARDS} <=
                        {card[0] for card in game.cards})
        proof = [(step.identity, step.reading) for step in game.initial_perfect_route]
        self.assertIsNotNone(certify_route(self.state(game), proof))

    def test_48_deals_keep_all_catalog_pictures_available(self):
        seen = set()
        for seed in range(500):
            game = ShiritoriRound(total=48, rng=random.Random(seed), clock=lambda: 0)
            game.start()
            seen.update(card[0] for card in game.cards + game.stock)
            if len(seen) == len(CARDS):
                break
        self.assertEqual(seen, {card[0] for card in CARDS})

    def test_connector_priority_is_limited_to_48_card_searches(self):
        for total in (12, 24, 36):
            for seed in range(10):
                with self.subTest(total=total, seed=seed):
                    ordinary = starting_route('と', total, {'トースト'}, random.Random(seed))
                    with patch('shiritori.CONNECTION_CARDS', ()):
                        no_priority = starting_route('と', total, {'トースト'}, random.Random(seed))
                    self.assertEqual(ordinary, no_priority)

    def test_48_card_starts_show_new_pictures_across_varied_deals(self):
        newer = {card[0] for card in CONNECTION_CARDS}
        counts, pictures = [], set()
        for seed in range(200):
            g = ShiritoriRound(total=48, rng=random.Random(seed), clock=lambda: 0)
            g.start()
            ids = {card[0] for card in g.cards + g.stock}
            counts.append(len(ids & newer))
            pictures.update(ids)
        self.assertGreaterEqual(sum(counts) / len(counts), 7)
        self.assertEqual(pictures, {card[0] for card in CARDS})

    def test_48_retry_never_reduces_new_cards_and_preserves_game_rng(self):
        # Suppress just the cloned-RNG retry to reproduce the original deal.
        # This compares actual starting boards and stock, not catalog edges.
        newer = {card[0] for card in CONNECTION_CARDS}
        def without_retry(*args, **kwargs):
            if kwargs.get('allow_lipstick'):
                return None
            return starting_route(*args, **kwargs)
        changed = 0
        for seed in range(200):
            with patch('shiritori.starting_route', side_effect=without_retry):
                before = ShiritoriRound(total=48, rng=random.Random(seed), clock=lambda: 0)
                before.start()
            after = ShiritoriRound(total=48, rng=random.Random(seed), clock=lambda: 0)
            after.start()
            def counts(game):
                visible = {card[0] for card in game.cards} & newer
                entire = {card[0] for card in game.cards + game.stock} & newer
                return len(entire), len(visible)
            old_total, old_visible = counts(before)
            new_total, new_visible = counts(after)
            self.assertGreaterEqual(new_total, old_total, seed)
            self.assertGreaterEqual(new_visible, old_visible, seed)
            self.assertEqual(before.rng.getstate(), after.rng.getstate(), seed)
            if (new_total, new_visible) == (old_total, old_visible):
                self.assertEqual(before.initial_perfect_route, after.initial_perfect_route, seed)
            else:
                changed += 1
                proof = [(s.identity, s.reading) for s in after.initial_perfect_route]
                self.assertIsNotNone(certify_route(self.state(after), proof), seed)
        self.assertGreater(changed, 0)

    def test_extra_retry_preserves_counts_and_game_rng(self):
        newer = {card[0] for card in CONNECTION_CARDS}
        def without_extra(*args, **kwargs):
            if kwargs.get('allow_extra'):
                return None
            return starting_route(*args, **kwargs)
        changed = 0
        for seed in range(300):
            with patch('shiritori.starting_route', side_effect=without_extra):
                before = ShiritoriRound(total=48, rng=random.Random(seed), clock=lambda: 0)
                before.start()
            after = ShiritoriRound(total=48, rng=random.Random(seed), clock=lambda: 0)
            after.start()
            def counts(game):
                return (len({card[0] for card in game.cards + game.stock} & newer),
                        len({card[0] for card in game.cards} & newer))
            old_total, old_visible = counts(before)
            new_total, new_visible = counts(after)
            self.assertGreaterEqual(new_total, old_total, seed)
            self.assertGreaterEqual(new_visible, old_visible, seed)
            self.assertEqual(before.rng.getstate(), after.rng.getstate(), seed)
            if (new_total, new_visible) == (old_total, old_visible):
                self.assertEqual(before.initial_perfect_route, after.initial_perfect_route, seed)
            else:
                changed += 1
                proof = [(s.identity, s.reading) for s in after.initial_perfect_route]
                self.assertIsNotNone(certify_route(self.state(after), proof), seed)
        self.assertGreater(changed, 0)

    def test_retry_is_only_used_in_48_card_games(self):
        for total in (12, 24, 36):
            for mode in ('solo', 'battle'):
                with self.subTest(total=total, mode=mode):
                    with patch('shiritori.starting_route', wraps=starting_route) as search:
                        game = ShiritoriRound(total=total, mode=mode,
                                              rng=random.Random(17), clock=lambda: 0)
                        game.start()
                    search.assert_called_once()
                    self.assertNotIn('allow_lipstick', search.call_args.kwargs)

    def test_48_extra_order_keeps_each_new_picture_and_game_rng(self):
        newer = {card[0] for card in CONNECTION_CARDS}
        improved = 0
        for seed in range(5270000, 5270200):
            with patch('shiritori.improve_48_new_cards',
                       side_effect=lambda route, seed, snapshot: route):
                before = ShiritoriRound(total=48, mode='solo', rng=random.Random(seed), clock=lambda: 0)
                before.start()
            after = ShiritoriRound(total=48, mode='solo', rng=random.Random(seed), clock=lambda: 0)
            after.start()
            old_board = {card[0] for card in before.cards} & newer
            new_board = {card[0] for card in after.cards} & newer
            old_entire = {card[0] for card in before.cards + before.stock} & newer
            new_entire = {card[0] for card in after.cards + after.stock} & newer
            self.assertLessEqual(old_board, new_board, seed)
            self.assertLessEqual(old_entire, new_entire, seed)
            self.assertEqual(before.rng.getstate(), after.rng.getstate(), seed)
            route = tuple((step.identity, step.reading) for step in after.initial_perfect_route)
            self.assertIsNotNone(certify_route(self.state(after), route), seed)
            if old_board != new_board or old_entire != new_entire:
                improved += 1
            else:
                self.assertEqual(before.initial_perfect_route, after.initial_perfect_route, seed)
        self.assertGreater(improved, 0)

    def test_48_extra_order_is_not_used_for_battle_or_smaller_games(self):
        modes = [(total, mode) for total in (12, 24, 36) for mode in ('solo', 'battle')]
        modes.append((48, 'battle'))
        for total, mode in modes:
            with self.subTest(total=total, mode=mode):
                with patch('shiritori.improve_48_new_cards') as extra:
                    game = ShiritoriRound(total=total, mode=mode,
                                          rng=random.Random(17), clock=lambda: 0)
                    game.start()
                extra.assert_not_called()
                route = tuple((step.identity, step.reading) for step in game.initial_perfect_route)
                self.assertIsNotNone(certify_route(self.state(game), route))

    def test_battle_deals_are_reproducible_and_exclude_retired_readings(self):
        # Removing retired readings intentionally changes historical deals.
        # The current catalog must still yield deterministic, certified deals.
        from shiritori import LEGACY_READINGS, RETIRED_SEMANTIC_READINGS

        retired = {(identity, normalize_reading(word))
                   for identity, aliases in LEGACY_READINGS.items()
                   for word in aliases}
        retired |= {(identity, normalize_reading(word))
                    for identity, word in RETIRED_SEMANTIC_READINGS}
        for identity, _, words in CARDS:
            for word in words:
                self.assertNotIn((identity, normalize_reading(word)), retired)
        for total in (12, 24, 36, 48):
            for seed in range(100):
                with self.subTest(total=total, seed=seed):
                    games = [ShiritoriRound(total=total, mode='battle',
                                            rng=random.Random(seed), clock=lambda: 0)
                             for _ in range(2)]
                    for game in games:
                        game.start()
                    first, second = games
                    routes = [tuple((step.identity, step.reading)
                                    for step in game.initial_perfect_route)
                              for game in games]
                    self.assertEqual(routes[0], routes[1])
                    self.assertEqual([card[0] for card in first.cards],
                                     [card[0] for card in second.cards])
                    self.assertEqual([card[0] for card in first.stock],
                                     [card[0] for card in second.stock])
                    self.assertEqual(first.rng.getstate(), second.rng.getstate())
                    for identity, word in routes[0]:
                        self.assertNotIn((identity, normalize_reading(word)), retired)
                    self.assertIsNotNone(certify_route(self.state(first), routes[0]))

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

    def test_apple_shinshu_rejoins_certify_remaining_stock_not_just_matching_tail(self):
        for required, reading in [('し', 'しんしゅうりんご')]:
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
        g.required = 'し'
        index = next(i for i, c in enumerate(g.cards) if c[0] == 'apple')
        g.command('card', index)
        self.assertEqual(g.history[-1]['word'], 'しんしゅうりんご')
        with patch('shiritori.longest_chain_move', side_effect=AssertionError('replay suffix')):
            self.assertEqual(g.chain_advice()[0][1], 'ゴリラ')

    def test_actual_legal_detours_rejoin_without_overriding_required(self):
        # Move a legal detour from after parsley to before apple. Unlike a
        # synthetic head override, every transition here is a real player tap.
        for detour, reading in [(['dragon', 'cow'], 'しんしゅうりんご')]:
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
        # Multiple legitimate readings may share the same initial.
        self.assertIn((0, 'トマト'), chain_moves([BY_ID['tomato']], 'と', set()))
        after_seen = chain_moves([BY_ID['tomato']], 'と', {'とまと'})
        self.assertNotIn((0, 'トマト'), after_seen)
        self.assertIn((0, 'トメイト'), after_seen)
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


    def test_hint_tap_keeps_nonperfect_advised_reading_on_same_card(self):
        # The one-step heuristic prefers いす (two next cards), but the actual
        # bounded search proves a longer route via いぬ, without a full clear.
        cards = [('test', '', ('いす', 'いぬ')), ('melon', '', ('すいか',)),
                 ('sand', '', ('すな',)), ('teddy', '', ('ぬいぐるみ',)),
                 ('miso', '', ('みそ',)), ('sky', '', ('そら',))]
        for mode in ('solo', 'battle'):
            with self.subTest(mode=mode):
                g = ShiritoriRound(mode=mode, clock=lambda: 0)
                g.cards, g.stock, g.used = list(cards), [], {}
                g.required, g.seen, g.phase, g.deadline = 'い', set(), 'playing', 100
                g.perfect_route = ()
                g._chain_advice.clear()
                g.command('hint')
                self.assertEqual(g.hint, 0)
                move, plan = g._chain_advice[self.state(g)]
                self.assertEqual(move, (0, 'いぬ'))
                self.assertFalse(plan['perfect'])
                self.assertEqual(plan['length'], 4)
                g.command('card', g.hint)
                self.assertEqual(g.history[-1]['word'], 'いぬ')

    def test_hint_does_not_override_a_different_selected_card(self):
        cards = [('test', '', ('いす', 'いぬ')), ('melon', '', ('すいか',)),
                 ('sand', '', ('すな',)), ('teddy', '', ('ぬいぐるみ',)),
                 ('miso', '', ('みそ',)), ('sky', '', ('そら',)),
                 ('squid', '', ('いか',))]
        g = ShiritoriRound(mode='solo', clock=lambda: 0)
        g.cards, g.stock, g.used = cards, [], {}
        g.required, g.seen, g.phase = 'い', set(), 'playing'
        g.perfect_route = ()
        g.command('hint')
        self.assertEqual(g.hint, 0)
        g.command('card', 6)
        self.assertEqual(g.history[-1]['id'], 'squid')
        self.assertEqual(g.history[-1]['word'], 'いか')

    def test_early_detour_reading_recertifies_shuffled_witness(self):
        cards = [('a', '', ('あすあ',)), ('b', '', ('あかす', 'あかあ')),
                 ('c', '', ('あす',)), ('d', '', ('すきす',)), ('e', '', ('すか',))]
        original = [('a', 'あすあ'), ('b', 'あかあ'), ('c', 'あす'),
                    ('d', 'すきす'), ('e', 'すか')]
        reordered = [original[1], original[0], *original[2:]]
        g = ShiritoriRound(mode='solo', clock=lambda: 0)
        g.cards, g.stock, g.used = cards, [], {}
        g.required, g.seen, g.phase = 'あ', set(), 'playing'
        state = self.state(g)
        self.assertIsNotNone(certify_route(state, reordered))
        g.remember_perfect(certify_route(state, original))
        # A different legal reading of b is tied under the local heuristic.
        # Choosing b must preserve the route only after the replay certifies it.
        with patch('shiritori.longest_chain_move', side_effect=AssertionError('unnecessary search')):
            g.command('card', 1)
            self.assertEqual(g.history[-1]['word'], 'あかあ')
            self.assertTrue(g.chain_advice()[1]['perfect'])
            for identity in ('a', 'c', 'd', 'e'):
                g.command('card', next(i for i, card in enumerate(g.cards)
                                       if card[0] == identity))
        self.assertEqual(len(g.history), 5)
        self.assertEqual(g.phase, 'finished')

    def test_detour_recertification_replays_stock_refill(self):
        cards = [('a', '', ('あすあ',)), ('b', '', ('あかす', 'あかあ')),
                 ('c', '', ('あす',)), ('d', '', ('すきす',)), ('e', '', ('すか',))]
        original = [('a', 'あすあ'), ('b', 'あかあ'), ('c', 'あす'),
                    ('d', 'すきす'), ('e', 'すか')]
        reordered = [original[1], original[0], *original[2:]]
        g = ShiritoriRound(mode='solo', clock=lambda: 0)
        g.cards, g.stock, g.used = cards[:4], cards[4:], {}
        g.required, g.seen, g.phase = 'あ', set(), 'playing'
        state = self.state(g)
        self.assertIsNotNone(certify_route(state, original))
        self.assertIsNotNone(certify_route(state, reordered))
        g.remember_perfect(certify_route(state, original))
        with patch('shiritori.longest_chain_move', side_effect=AssertionError('unnecessary search')):
            g.command('card', 1)
            self.assertEqual(g.history[-1]['word'], 'あかあ')
            self.assertEqual(g.cards[1][0], 'e')
            self.assertEqual(g.stock, [])
            self.assertTrue(g.chain_advice()[1]['perfect'])

    def test_early_detour_must_not_certify_a_seen_remaining_reading(self):
        cards = [('a', '', ('あすあ',)), ('b', '', ('あかす', 'あかあ')),
                 ('c', '', ('あす',)), ('d', '', ('すきす',)), ('e', '', ('すか',))]
        original = [('a', 'あすあ'), ('b', 'あかあ'), ('c', 'あす'),
                    ('d', 'すきす'), ('e', 'すか')]
        reordered = [original[1], original[0], *original[2:]]
        g = ShiritoriRound(mode='solo', clock=lambda: 0)
        g.cards, g.stock, g.used = cards, [], {}
        g.required, g.seen, g.phase = 'あ', set(), 'playing'
        g.remember_perfect(certify_route(self.state(g), original))
        # A changed used-word set invalidates the stored full route.
        g.seen = {normalize_reading('あす')}
        state = self.state(g)
        self.assertIsNone(certify_route(state, reordered))
        self.assertIn(g.choose_move_for_card(1), chain_moves(state[0], state[2], state[3]))
        self.assertFalse(g._chain_advice.get(state, (None, {}))[1].get('perfect', False))


if __name__ == '__main__':
    unittest.main()
