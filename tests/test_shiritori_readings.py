"""Capture scoring and board-aware reading selection regressions."""
import random
import unittest

from shiritori import (CARDS, SPECIAL_READINGS, ShiritoriRound, chain_moves,
                       head, normalize_reading, reading_connections, tail)

STEP25_WEAK_COMMON = 17
NEW_CARDS = {
    'sewing_needle': ('🪡', ('ぬいばり', 'はり', 'さいほうどうぐ')),
    'snow_crab': ('🦀', ('ズワイガニ', 'かに', 'シーフード')),
    'blocks': ('🧱', ('つみき', 'ブロック', 'おもちゃ')),
    'golf': ('⛳', ('ゴルフ', 'ホール', 'スポーツ')),
    'gift': ('🎁', ('プレゼント', 'おくりもの', 'ギフト')),
}


class ReadingAndScoreTests(unittest.TestCase):
    def round(self, total=12, mode='solo'):
        game = ShiritoriRound(total=total, mode=mode, rng=random.Random(7), clock=lambda: 0)
        game.start()
        return game

    def test_catalog_audit_identity_graph_and_natural_kana(self):
        graph = reading_connections()
        self.assertEqual(len(CARDS), 73)
        self.assertEqual(sum(len(card[2]) for card in CARDS), 269)
        self.assertEqual(len({card[0] for card in CARDS}), len(CARDS))
        self.assertEqual(len(graph), sum(tail(w) != 'ん' for c in CARDS for w in c[2]))
        for card in CARDS:
            self.assertGreaterEqual(len(card[2]), 3)
            self.assertEqual(len({head(w) for w in card[2]}), len(card[2]))
            for word in card[2]:
                self.assertFalse(any('\u4e00' <= ch <= '\u9fff' for ch in word))
                if word not in SPECIAL_READINGS and tail(word) != 'ん':
                    self.assertGreater(graph[(card[0], word)], 0, (card[0], word))

    def test_five_natural_cards_cover_weak_common_without_reclassification(self):
        by_id = {card[0]: card for card in CARDS}
        self.assertEqual(len(NEW_CARDS), 5)
        for identity, (icon, words) in NEW_CARDS.items():
            with self.subTest(identity=identity):
                self.assertEqual(by_id[identity], (identity, icon, words))
                self.assertNotIn(words[0], SPECIAL_READINGS)
                self.assertNotEqual(tail(words[0]), 'ん')
                self.assertGreater(reading_connections()[(identity, words[0])], 0)
        # These are ordinary, picture-recognizable names, not special-only
        # connector aliases. One blocks picture contributes both つ and ぶ.
        for word in ('ぬいばり', 'ズワイガニ', 'つみき', 'ブロック', 'ゴルフ', 'プレゼント'):
            self.assertNotIn(word, SPECIAL_READINGS)
        for word in ('さいほうどうぐ', 'シーフード', 'ホール', 'スポーツ'):
            self.assertIn(word, SPECIAL_READINGS)
        graph = reading_connections()
        weak = [(identity, word) for (identity, word), count in graph.items()
                if word not in SPECIAL_READINGS and count <= 1]
        dead = [(identity, word) for (identity, word), count in graph.items()
                if word not in SPECIAL_READINGS and count == 0]
        self.assertEqual(dead, [])
        self.assertLessEqual(len(weak), 6)
        self.assertGreaterEqual((STEP25_WEAK_COMMON - len(weak)) / STEP25_WEAK_COMMON, .60)
        self.assertEqual({tail(word) for _, word in weak}, {'る', 'ゆ', 'も', 'ろ'})

    def test_common_continuation_beats_special_dead_end(self):
        game = self.round()
        game.cards = [('test', '🧪', ('いす', 'いぐ')), ('melon', '🍉', ('すいか',))]
        game.stock = []; game.used = {}; game.required = 'い'; game.seen = set()
        game.perfect_route = (); game._chain_advice.clear()
        self.assertEqual(game.choose_move_for_card(0), (0, 'いす'))

    def test_certified_perfect_reading_beats_more_connections(self):
        game = self.round()
        game.cards = [('test', '🧪', ('いす', 'いぬ')),
                      ('melon', '🍉', ('すいか',)), ('sand', '🏖️', ('すな',)),
                      ('teddy', '🧸', ('ぬいぐるみ',))]
        game.stock = []; game.used = {}; game.required = 'い'; game.seen = set()
        game.perfect_route = ()
        state = (tuple(game.cards), (), 'い', frozenset())
        game._chain_advice = {state: ((0, 'いぬ'), {'perfect': True})}
        self.assertEqual(game.choose_move_for_card(0), (0, 'いぬ'))

    def test_board_stock_refill_and_seen_affect_choice(self):
        game = self.round()
        game.cards = [('test', '🧪', ('いぬ', 'いす'))]
        game.stock = [('teddy', '🧸', ('ぬいぐるみ',))]
        game.used = {}; game.required = 'い'; game.seen = set()
        game.perfect_route = (); game._chain_advice.clear()
        self.assertEqual(game.choose_move_for_card(0), (0, 'いぬ'), 'refill makes ぬ available')
        game.cards.append(('melon', '🍉', ('すいか',)))
        game.stock = []
        self.assertEqual(game.choose_move_for_card(0), (0, 'いす'), 'visible board beats catalog')
        game.seen = {normalize_reading('すいか')}
        self.assertEqual(game.choose_move_for_card(0), (0, 'いぬ'), 'seen connector is unavailable')

    def test_full_clear_winner_by_captures_all_sizes(self):
        for total in (12, 24, 36, 48):
            for you_count in (total // 2 - 1, total // 2, total // 2 + 1):
                game = self.round(total, 'battle')
                game.history = [{'owner': 'you'}] * (you_count - 1) + [{'owner': 'cpu'}] * (total - you_count)
                game.cards = [('apple', '🍎', ('りんご',))]; game.stock = []
                game.used = {}; game.turn = 'you'; game.required = 'り'; game.seen = set()
                game.take(0, 'りんご')
                snap = game.snapshot()
                self.assertTrue(snap['perfect_clear'])
                self.assertEqual((snap['you_count'], snap['cpu_count']), (you_count, total-you_count))
                expected = 'you' if you_count > total-you_count else 'cpu' if you_count < total-you_count else 'draw'
                self.assertEqual(snap['winner'], expected)

    def test_no_move_uses_captures_not_last_owner(self):
        for prior_you, prior_cpu, expected in ((3, 1, 'you'), (0, 3, 'cpu'), (1, 2, 'draw')):
            game = self.round(12, 'battle')
            game.history = [{'owner': 'you'}] * prior_you + [{'owner': 'cpu'}] * prior_cpu
            game.cards = [('apple', '🍎', ('りんご',)), ('cat', '🐈', ('ねこ',))]
            game.stock = []; game.used = {}; game.turn = 'you'; game.required = 'り'; game.seen = set()
            game.take(0, 'りんご')
            self.assertEqual(game.winner, expected)
            self.assertFalse(game.snapshot()['perfect_clear'])


if __name__ == '__main__':
    unittest.main()
