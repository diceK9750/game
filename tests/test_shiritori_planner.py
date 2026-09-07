import random
import unittest

from shiritori import ShiritoriRound, chain_moves, chain_step, longest_chain_move


def card(name, *words):
    return (name, '絵', words)


class ChainPlannerTests(unittest.TestCase):
    def test_full_clear_beats_immediate_dead_end_in_every_difficulty(self):
        for difficulty in ('easy', 'normal', 'hard'):
            game = ShiritoriRound(difficulty, clock=lambda: 0)
            game.cards = [card('end', 'あい'), card('start', 'あう'), card('bridge', 'うあ')]
            game.required, game.turn, game.phase = 'あ', 'cpu', 'playing'
            game.prepare_cpu()
            self.assertEqual(game.cpu_move, (1, 'あう'))
            self.assertEqual(game.cpu_plan['length'], 3)
            self.assertTrue(game.cpu_plan['perfect'])

    def test_longest_route_when_full_clear_is_impossible(self):
        cards = [card('end', 'あい'), card('start', 'あう'), card('bridge', 'うあ'), card('isolated', 'えお')]
        move, plan = longest_chain_move(cards, [], 'あ', set())
        self.assertEqual(move, (1, 'あう'))
        self.assertEqual(plan['length'], 3)
        self.assertTrue(plan['exact'])
        self.assertFalse(plan['perfect'])

    def test_seen_words_n_endings_and_consumed_cells_are_excluded(self):
        cards = [None, card('bad', 'あん'), card('seen', 'あい'), card('good', 'あう')]
        move, plan = longest_chain_move(cards, [], 'あ', {'あい'})
        self.assertEqual(move, (3, 'あう'))
        self.assertEqual(plan['length'], 1)

    def test_refill_and_rescue_match_live_game_without_mutation(self):
        game = ShiritoriRound(mode='solo', clock=lambda: 0)
        game.cards = [card('start', 'あい'), card('other', 'かき')]
        game.stock = [card('decoy', 'えお'), card('connector', 'いう')]
        game.phase, game.required = 'playing', 'あ'
        before = (game.cards[:], game.stock[:], game.seen.copy(), game.rng.getstate())
        move, _ = longest_chain_move(game.cards, game.stock, game.required, game.seen)
        expected = chain_step(tuple(game.cards), tuple(game.stock), frozenset(game.seen), move)
        self.assertEqual(before, (game.cards, game.stock, game.seen, game.rng.getstate()))
        game.take(*move)
        self.assertEqual(expected, (tuple(game.cards), tuple(game.stock), game.required, frozenset(game.seen)))
        self.assertEqual(game.cards[0][0], 'connector')

    def test_full_route_includes_cards_still_in_stock(self):
        move, plan = longest_chain_move([card('a', 'あい')], [card('b', 'いう'), card('c', 'うえ')], 'あ', set())
        self.assertEqual(move, (0, 'あい'))
        self.assertTrue(plan['perfect'])
        self.assertEqual(plan['length'], 3)

    def test_small_boards_match_exhaustive_longest_path(self):
        def oracle(board, head, seen):
            scores = []
            for i, word in chain_moves(board, head, seen):
                rest = list(board)
                rest[i] = None
                scores.append(1 + oracle(tuple(rest), word[-1], seen | {word}))
            return max(scores, default=0)
        rng = random.Random(21)
        for _ in range(80):
            board = tuple(card(str(i), *(a + rng.choice('あいうえ') for a in rng.sample(list('あいうえ'), 2))) for i in range(6))
            move, plan = longest_chain_move(board, [], 'あ', set())
            self.assertTrue(plan['exact'])
            self.assertEqual(plan['length'], oracle(board, 'あ', set()))
            if move:
                rest, _, head, seen = chain_step(board, (), frozenset(), move)
                self.assertEqual(plan['length'], 1 + oracle(rest, head, seen))

    def test_budget_cutoff_is_bounded_and_does_not_claim_impossibility(self):
        board = tuple(card(str(i), 'あ' + 'い' * i + 'あ') for i in range(12))
        move, plan = longest_chain_move(board, [], 'あ', set(), node_budget=24)
        self.assertIn(move, chain_moves(board, 'あ', set()))
        self.assertLessEqual(plan['nodes'], 24)
        self.assertFalse(plan['exact'])
        self.assertFalse(plan['perfect'])


if __name__ == '__main__':
    unittest.main()
