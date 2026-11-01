"""Runtime reuse of already witnessed, exact-state shiritori routes."""
import random
import unittest
from unittest.mock import patch

import shiritori
from shiritori import ShiritoriRound


class RouteCacheTests(unittest.TestCase):
    def test_certified_accessor_never_searches_and_rejects_changed_state(self):
        game = ShiritoriRound(mode='solo', total=48, rng=random.Random(13), clock=lambda: 0)
        game.start()
        with patch('shiritori.longest_chain_move', side_effect=AssertionError('unexpected search')):
            first = game.cached_perfect_move()
            self.assertEqual(first, game.chain_advice()[0])
            game.command('card', first[0])
            self.assertEqual(game.cached_perfect_move(), game.chain_advice()[0])
            game.seen.add('別のことば')
            self.assertIsNone(game.cached_perfect_move())

    def test_partial_witness_suffixes_are_reused_without_claiming_perfect(self):
        cards = [('test', '', ('いす', 'いぬ')), ('melon', '', ('すいか',)),
                 ('sand', '', ('すな',)), ('teddy', '', ('ぬいぐるみ',)),
                 ('miso', '', ('みそ',)), ('sky', '', ('そら',))]
        game = ShiritoriRound(mode='solo', clock=lambda: 0)
        game.cards, game.stock, game.used = list(cards), [], {}
        game.required, game.seen, game.phase, game.deadline = 'い', set(), 'playing', 100
        with patch('shiritori.longest_chain_move', wraps=shiritori.longest_chain_move) as search:
            move, plan = game.chain_advice()
            self.assertEqual(move, (0, 'いぬ'))
            self.assertFalse(plan['perfect'])
            self.assertEqual(plan['length'], 4)
            game.command('card', move[0])
            for remaining in (3, 2, 1):
                move, suffix = game.chain_advice()
                self.assertEqual(suffix['length'], remaining)
                self.assertFalse(suffix['perfect'])
                self.assertFalse(suffix['exact'])
                self.assertEqual(suffix['nodes'], 0)
                self.assertIsNone(game.cached_perfect_move())
                game.command('card', move[0])
            self.assertEqual(search.call_count, 1)
            self.assertEqual([step['word'] for step in game.history],
                             ['いぬ', 'ぬいぐるみ', 'みそ', 'そら'])

    def test_cutoff_path_is_replanned_on_next_state(self):
        cards = [('a', '', ('あか',)), ('b', '', ('かき',)),
                 ('c', '', ('きく',)), ('unused', '', ('そら',))]
        game = ShiritoriRound(mode='solo', clock=lambda: 0)
        game.cards, game.stock, game.used = cards, [], {}
        game.required, game.seen, game.phase = 'あ', set(), 'playing'
        search = shiritori.longest_chain_move
        def cutoff(*args, **kwargs):
            move, plan = search(*args, **kwargs)
            return move, dict(plan, exact=False)
        with patch('shiritori.longest_chain_move', side_effect=cutoff) as wrapped:
            move, plan = game.chain_advice()
            self.assertFalse(plan['exact'])
            game.command('card', move[0])
            game.chain_advice()
            self.assertEqual(wrapped.call_count, 2)

    def test_partial_cache_is_not_used_after_state_changes(self):
        game = ShiritoriRound(mode='solo', clock=lambda: 0)
        game.cards = [('a', '', ('あか',)), ('b', '', ('かき',)),
                      ('c', '', ('きく',)), ('unused', '', ('そら',))]
        game.stock, game.used = [], {}
        game.required, game.seen, game.phase = 'あ', set(), 'playing'
        game.chain_advice()
        game.command('card', 0)
        game.seen.add('かき')
        with patch('shiritori.longest_chain_move', wraps=shiritori.longest_chain_move) as search:
            move, _ = game.chain_advice()
            self.assertIsNone(move)
            self.assertEqual(search.call_count, 1)


if __name__ == '__main__':
    unittest.main()
