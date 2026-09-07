import random
import unittest

from shiritori import CARDS, ShiritoriRound, tail


class ShiritoriTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.game = ShiritoriRound(rng=random.Random(3), clock=lambda: self.now)
        self.game.start()

    def test_boards_are_unique_and_have_a_move_across_500_seeds(self):
        for seed in range(500):
            game = ShiritoriRound(rng=random.Random(seed))
            game.start()
            self.assertEqual(len(game.cards), min(game.total, 24))
            self.assertEqual(len({c[0] for c in game.cards + game.stock}), 24)
            self.assertTrue(game.moves())

    def test_catalog_and_house_rules(self):
        self.assertEqual(len(CARDS), len({c[0] for c in CARDS}))
        for _, _, words in CARDS:
            self.assertGreaterEqual(len(words), 3)
            self.assertEqual(len(words), len({w[0] for w in words}))
            self.assertEqual(len(words), len(set(words)))
            self.assertTrue(all(all('ぁ' <= c <= 'ん' or c == 'ー' for c in word) for word in words))
        self.assertEqual(tail('おもちゃ'), 'や')
        self.assertEqual(tail('ぎたー'), 'た')
        self.assertEqual(tail('うさぎ'), 'ぎ')

    def test_settings_accept_only_supported_values_before_start(self):
        game = ShiritoriRound()
        for n in [12,24,36]:
            game.command('total', n)
            self.assertEqual(game.total, n)
        for n in [0,13,100,True,'12',None,{}]:
            game.command('total', n)
            self.assertEqual(game.total, 36)
        game.command('mode', 'solo')
        game.command('mode', {})
        self.assertEqual(game.mode, 'solo')
        game.start()
        game.command('total', 12)
        game.command('mode', 'battle')
        self.assertEqual((game.total, game.mode), (36, 'solo'))

    def test_solo_has_no_deadline_or_cpu_and_refills_in_place(self):
        game = ShiritoriRound(mode='solo', total=36, rng=random.Random(2), clock=lambda:self.now)
        game.start()
        original = [c[0] for c in game.cards]
        self.now = 10000
        game.update()
        self.assertEqual(game.phase, 'playing')
        i, word = game.moves()[0]
        game.command('card', i)
        self.assertEqual(game.turn, 'you')
        self.assertEqual(len(game.stock), 11)
        self.assertNotEqual(game.cards[i][0], original[i])
        self.assertEqual([c[0] for j,c in enumerate(game.cards) if j != i], [c for j,c in enumerate(original) if j != i])
        self.assertNotIn(i, game.used)
        self.assertEqual(game.refilled, i)
        self.assertEqual(len(game.history), 1)

    def test_connector_in_stock_is_dealt_before_declaring_a_block(self):
        game = self.game
        game.cards = [('apple','🍎',('りんご',)), ('cat','🐈',('ねこ',))]
        game.stock = [('tree','🌲',('まつ',)), ('gorilla','🦍',('ごりら',))]
        game.required, game.seen = 'り', set()
        game.command('card', 0)
        self.assertEqual(game.cards[0][0], 'gorilla')
        self.assertEqual(len(game.stock), 1)
        self.assertTrue(game.moves())
        self.assertEqual(game.phase, 'playing')

    def test_solo_relinks_are_bounded_and_marked_in_history(self):
        game = ShiritoriRound(mode='solo')
        game.start()
        game.cards = [('apple','🍎',('りんご',)), ('cat','🐈',('ねこ',)), ('tree','🌲',('まつ',))]
        game.stock = []
        game.required, game.seen = 'り', set()
        game.command('card', 0)
        self.assertEqual(game.phase, 'blocked')
        game.command('pause')
        self.assertFalse(game.snapshot()['cards'])
        game.command('resume')
        self.assertEqual(game.phase, 'blocked')
        game.command('relink')
        self.assertEqual(game.relinks, 1)
        i,w = game.moves()[0]
        game.command('card', i)
        self.assertTrue(game.history[-1]['relinked'])
        game.command('relink')
        self.assertEqual(game.relinks, 0)
        i,w = game.moves()[0]
        game.command('card', i)
        self.assertEqual(game.winner, 'you')
        self.assertEqual(game.phase, 'finished')

    def test_stock_stays_hidden_and_setup_keeps_selected_options(self):
        game = ShiritoriRound(total=36, mode='solo')
        game.start()
        snapshot = game.snapshot()
        self.assertEqual(snapshot['stock'], 12)
        self.assertEqual(len(snapshot['cards']), 24)
        self.assertNotIn('deck', snapshot)
        game.command('pause')
        game.command('setup')
        self.assertEqual((game.phase, game.mode, game.total), ('intro','solo',36))
        self.assertFalse(game.snapshot()['cards'])
        game.command('start')
        self.assertEqual(len(game.stock), 12)

    def test_solo_can_end_at_rest_and_wrong_reading_does_not_spend_cards(self):
        game = ShiritoriRound(mode='solo')
        game.start()
        i = next(i for i,c in enumerate(game.cards) if not any(w[0] == game.required and tail(w) != 'ん' and w not in game.seen for w in c[2]))
        before = len(game.stock)
        game.command('card', i)
        self.assertEqual(game.mistakes, 1)
        self.assertEqual(len(game.stock), before)
        self.assertEqual(game.phase, 'playing')
        game.command('pause')
        game.command('end')
        self.assertEqual((game.phase, game.winner), ('finished','draw'))

    def test_all_modes_and_deck_sizes_conserve_cards_through_complete_games(self):
        for mode in ('solo','battle'):
            for total in (12,24,36):
                for difficulty in ('easy','normal','hard'):
                    for seed in range(50):
                        game = ShiritoriRound(difficulty, mode=mode, total=total, rng=random.Random(seed), clock=lambda:self.now)
                        game.start()
                        for _ in range(total + 4):
                            active = [c for i,c in enumerate(game.cards) if i not in game.used]
                            identities = [r['id'] for r in game.history] + [c[0] for c in active + game.stock]
                            self.assertEqual(len(identities), total)
                            self.assertEqual(len(set(identities)), total)
                            self.assertEqual(len(game.cards), min(game.total, 24))
                            if game.phase == 'finished':
                                break
                            if game.phase == 'blocked':
                                game.command('relink')
                            elif game.turn == 'you':
                                i,w = game.moves()[0]
                                game.command('card', i)
                            else:
                                self.now += 3
                                game.update()
                        self.assertEqual(game.phase, 'finished')
                        for a,b in zip(game.history, game.history[1:]):
                            if not b['relinked']:
                                self.assertEqual(tail(a['word']), b['word'][0])

    def test_every_starting_rotation_has_fourteen_linked_moves(self):
        ring = ['りんご', 'ごりら', 'らっぱ', 'ぱんだ', 'だるま', 'まつ', 'つき',
                'きつね', 'ねずみ', 'みつばち', 'ちょう', 'うさぎ', 'ぎたー', 'たこ', 'ことり']
        for offset in range(15):
            rng = random.Random(offset)
            rng.randrange = lambda *args, n=offset: n
            game = ShiritoriRound(rng=rng)
            game.start()
            self.assertEqual(game.last_word, ring[offset])
            for word in ring[offset + 1:] + ring[:offset]:
                self.assertEqual(game.phase, 'playing')
                index = next(i for i, reading in game.moves() if reading == word)
                game.take(index, word)
            self.assertEqual(len(game.history), 14)

    def test_difficulty_only_changes_before_start(self):
        game = ShiritoriRound()
        for level, limit in [('easy', 30), ('normal', 20), ('hard', 12)]:
            game.command('difficulty', level)
            self.assertEqual(game.limit, limit)
        game.command('difficulty', [])
        self.assertEqual(game.limit, 12)
        game.start()
        game.command('difficulty', 'easy')
        self.assertEqual(game.limit, 12)

    def test_valid_word_changes_turn_and_consumes_only_one_card(self):
        self.game.total = 12
        self.game.start()
        index, word = self.game.moves()[0]
        self.game.command('card', index)
        self.assertEqual(self.game.used, {index: 'you'})
        self.assertEqual(self.game.history[0]['word'], word)
        self.assertEqual(self.game.required, tail(word))
        self.assertEqual(len(self.game.history), 1)

    def test_wrong_reading_costs_three_seconds_not_the_card(self):
        index = next(i for i, c in enumerate(self.game.cards) if not any(w[0] == self.game.required and tail(w) != 'ん' and w not in self.game.seen for w in c[2]))
        self.game.command('card', index)
        self.assertEqual(self.game.mistakes, 1)
        self.assertNotIn(index, self.game.used)
        self.assertEqual(self.game.remaining(), 17)
        self.assertIsNone(self.game.selected)

    def test_unknown_reading_and_malformed_indices_are_ignored(self):
        for value in (-1, 24, True, '1', None, {}, []):
            self.game.command('card', value)
        for value in ('りんご', 'でたらめ', {}, []):
            self.game.command('word', value)
        self.assertFalse(self.game.history)
        self.assertEqual(self.game.mistakes, 0)

    def test_pause_hides_board_and_freezes_both_turns(self):
        for turn in ('you', 'cpu'):
            self.game.start()
            self.game.turn = turn
            self.game.command('pause')
            remaining = self.game.remaining()
            self.now += 100
            self.game.update()
            self.assertEqual(self.game.snapshot()['cards'], [])
            self.assertEqual(self.game.snapshot()['history'], [])
            self.game.command('resume')
            self.assertEqual(self.game.remaining(), remaining)
            self.assertEqual(self.game.turn, turn)

    def test_timeout_and_late_input_lose(self):
        index, word = self.game.moves()[0]
        self.now = 21
        self.game.command('card', index)
        self.assertEqual(self.game.winner, 'cpu')
        self.assertFalse(self.game.used)

    def test_ending_n_is_not_automatically_committed(self):
        self.game.cards = [('orange', '🍊', ('みかん', 'くだもの'))]
        self.game.required = 'み'
        self.game.command('card', 0)
        self.assertEqual(self.game.mistakes, 1)
        self.assertFalse(self.game.history)
        self.assertNotIn(0, self.game.used)

    def test_secondary_reading_is_selected_with_one_tap(self):
        self.game.cards = [('cat', '🐈', ('ねこ', 'こねこ', 'どうぶつ'))]
        self.game.stock = []
        self.game.required, self.game.seen = 'ど', set()
        self.game.command('card', 0)
        self.assertEqual(self.game.history[0]['word'], 'どうぶつ')
        self.assertIsNone(self.game.selected)

    def test_every_catalog_reading_is_automatically_resolved_or_safely_rejected(self):
        for card in CARDS:
            for word in card[2]:
                with self.subTest(card=card[0], word=word):
                    game = ShiritoriRound(mode='solo')
                    game.phase, game.cards = 'playing', [card]
                    game.required = word[0]
                    game.command('card', 0)
                    if tail(word) == 'ん':
                        self.assertFalse(game.history)
                        self.assertEqual(game.mistakes, 1)
                    else:
                        self.assertEqual([r['word'] for r in game.history], [word])

    def test_consecutive_solo_taps_need_no_reading_command_or_delay(self):
        game = ShiritoriRound(mode='solo')
        game.cards = [('apple','🍎',('りんご',)), ('gorilla','🦍',('ごりら',)), ('trumpet','🎺',('らっぱ',))]
        game.phase, game.required = 'playing', 'り'
        for index in range(3):
            game.command('card', index)
        self.assertEqual([r['word'] for r in game.history], ['りんご','ごりら','らっぱ'])
        self.assertEqual(game.winner, 'you')

    def test_legacy_word_command_cannot_commit_a_second_answer(self):
        game = ShiritoriRound(mode='solo')
        game.start()
        index, word = game.moves()[0]
        game.command('card', index)
        game.command('word', word)
        self.assertEqual(len(game.history), 1)

    def test_repeated_word_is_rejected_on_a_different_card(self):
        self.game.cards = [('teddy', '🧸', ('くま',))]
        self.game.required = 'く'
        self.game.seen.add('くま')
        self.game.command('card', 0)
        self.assertEqual(self.game.mistakes, 1)
        self.assertFalse(self.game.moves())

    def test_cpu_uses_public_legal_moves_and_turn_delay(self):
        self.game.turn = 'cpu'
        self.game.deadline = 2.2
        legal = self.game.moves()
        self.now = 2
        self.game.update()
        self.assertFalse(self.game.history)
        self.now = 2.2
        self.game.update()
        self.assertEqual(len(self.game.history), 1)
        row = self.game.history[0]
        self.assertEqual(row['owner'], 'cpu')
        self.assertIn(row['word'], [word for _, word in legal])

    def test_blocked_opponent_and_all_used_draw(self):
        self.game.stock = []
        self.game.cards = [('apple', '🍎', ('りんご',)), ('cat', '🐈', ('ねこ',))]
        self.game.required = 'り'
        self.game.seen = set()
        self.game.command('card', 0)
        self.assertEqual(self.game.winner, 'you')
        self.game.start()
        self.game.stock = []
        self.game.cards = [('apple', '🍎', ('りんご',))]
        self.game.required = 'り'
        self.game.seen = set()
        self.game.command('card', 0)
        self.assertEqual(self.game.winner, 'draw')

    def test_hints_bounded_and_restart_clears_state(self):
        for _ in range(8):
            self.game.command('hint')
        self.assertEqual(self.game.hints, 0)
        self.assertIn(self.game.hint, [index for index, _ in self.game.moves()])
        self.game.command('pause')
        self.game.command('restart')
        self.assertEqual(self.game.hints, 3)
        self.assertIsNone(self.game.hint)
        self.assertFalse(self.game.history)

    def test_simulated_games_terminate_with_valid_nonrepeating_words(self):
        for difficulty in ('easy', 'normal', 'hard'):
            for seed in range(60):
                game = ShiritoriRound(difficulty, rng=random.Random(seed), clock=lambda: self.now)
                game.start()
                for _ in range(30):
                    if game.phase == 'finished':
                        break
                    if game.turn == 'you':
                        index, word = game.moves()[0]
                        game.command('card', index)
                    else:
                        self.now += 3
                        game.update()
                self.assertEqual(game.phase, 'finished')
                words = [row['word'] for row in game.history]
                self.assertEqual(len(words), len(set(words)))
                for a, b in zip(words, words[1:]):
                    self.assertEqual(tail(a), b[0])


if __name__ == '__main__':
    unittest.main()
