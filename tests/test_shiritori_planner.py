import random
import unittest

from shiritori import ShiritoriRound, chain_moves, chain_step, longest_chain_move


def card(name, *words):
    return (name, '絵', words)


class ChainPlannerTests(unittest.TestCase):
    def route_game(self):
        game = ShiritoriRound(mode='solo', clock=lambda: 0)
        game.cards = [card('end', 'あい'), card('start', 'あう'), card('bridge', 'うあ')]
        game.required, game.phase = 'あ', 'playing'
        return game

    def test_hint_chooses_perfect_route_without_playing_or_awarding_a_word(self):
        game = self.route_game()
        game.command('hint')
        self.assertEqual(game.hint, 1)
        self.assertEqual(game.hints, 2)
        self.assertIn('完走', game.message)
        self.assertEqual(game.history, [])
        self.assertEqual(game.discoveries, set())
        self.assertEqual(game.seen, set())

    def test_perfect_suffix_is_reused_and_each_step_remains_legal(self):
        game = self.route_game()
        move, plan = game.chain_advice()
        route = plan['route']
        self.assertEqual(len(route), 3)
        for expected in route:
            move, plan = game.chain_advice()
            self.assertEqual(move, expected)
            self.assertIn(move, game.moves())
            self.assertTrue(plan['perfect'])
            self.assertEqual(plan['nodes'], 0)
            game.take(*move)
        self.assertEqual(game.phase, 'finished')
        self.assertEqual(len(game.history), 3)

    def test_player_deviation_seen_words_and_restart_invalidate_advice(self):
        game = self.route_game()
        game.chain_advice()
        game.seen.add('あう')
        move, plan = game.chain_advice()
        self.assertEqual(move, (0, 'あい'))
        self.assertFalse(plan['perfect'])
        self.assertEqual(len(game._chain_advice), 1)
        game.start()
        self.assertEqual(game._chain_advice, {})

    def test_returned_route_replays_with_refill_and_shared_readings(self):
        for seed in range(20):
            game = ShiritoriRound(total=36, rng=random.Random(seed))
            game.start()
            move, plan = game.chain_advice()
            state = (tuple(game.cards), tuple(game.stock), game.required, frozenset(game.seen))
            self.assertEqual(len(plan['route']), plan['length'])
            for step in plan['route']:
                self.assertIn(step, chain_moves(state[0], state[2], state[3]))
                state = chain_step(state[0], state[1], state[3], step)
            if plan['perfect']:
                self.assertFalse(any(state[0]) or state[1])

    def test_hint_search_time_is_not_charged_to_player(self):
        game = self.route_game()
        now = [0]
        game.mode, game.clock, game.deadline = 'battle', lambda: now[0], 20
        advice = game.chain_advice
        def delayed_advice():
            now[0] += .25
            return advice()
        game.chain_advice = delayed_advice
        game.command('hint')
        self.assertEqual(game.remaining(), 20)

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
