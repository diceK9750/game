"""Capture scoring and board-aware reading selection regressions."""
import random
import unittest

from shiritori import (ADDITIONAL_READINGS, CARDS, CONNECTION_CARDS, LEGACY_READINGS, RETIRED_SEMANTIC_READINGS, SPECIAL_READINGS, ShiritoriRound, chain_moves,
                       head, normalize_reading, reading_connections, tail)

STEP25_WEAK_COMMON = 17
# Assess old graph quality separately so new aliases cannot hide regressions.
CONNECTION_IDS = {card[0] for card in CONNECTION_CARDS}
BASE_CARDS = tuple((identity, icon, tuple(word for word in words
                    if word not in ADDITIONAL_READINGS.get(identity, ())))
                   for identity, icon, words in CARDS if identity not in CONNECTION_IDS)
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
        self.assertEqual(len(CARDS), 81)
        self.assertEqual(len(BASE_CARDS), 73)
        self.assertEqual(sum(len(card[2]) for card in BASE_CARDS), 270)
        self.assertEqual(len({card[0] for card in CARDS}), len(CARDS))
        self.assertEqual(len(graph), sum(tail(w) != 'ん' for c in CARDS for w in c[2]))
        for card in CARDS:
            self.assertGreaterEqual(len(card[2]), 3)
            self.assertGreaterEqual(len({head(w) for w in card[2]}), 3)
            for word in card[2]:
                self.assertFalse(any('\u4e00' <= ch <= '\u9fff' for ch in word))
                if (card[0] not in CONNECTION_IDS
                        and word not in ADDITIONAL_READINGS.get(card[0], ())
                        and word not in SPECIAL_READINGS and tail(word) != 'ん'):
                    # 'もも' uses the valid added reading 'もみ' after removing 'もみのき'.
                    graph_for_word = graph if (card[0], word) == ('peach', 'もも') else reading_connections(BASE_CARDS)
                    self.assertGreater(graph_for_word[(card[0], word)], 0, (card[0], word))

    def test_new_readings_are_automatically_selected_and_discovered(self):
        additions = {'dog': 'わんこ', 'cat': 'にゃんこ', 'chair': 'チェア', 'tree': 'ツリー', 'moon': 'おつきさま', 'paint': 'パレット', 'pillow': 'ベッド', 'dragon': 'たつ'}
        by_id = {card[0]: card for card in CARDS}
        for mode in ('solo', 'battle'):
            for identity, reading in additions.items():
                with self.subTest(mode=mode, identity=identity):
                    game = self.round(mode=mode)
                    game.cards = [by_id[identity]]
                    game.stock = []; game.used = {}; game.history = []
                    game.required = head(reading)
                    # Other valid aliases may have the same initial.
                    game.seen = {normalize_reading(word) for word in game.cards[0][2]
                                 if word != reading and head(word) == head(reading)}
                    game.perfect_route = (); game._chain_advice.clear()
                    game.command('card', 0)
                    self.assertEqual(game.history[0]['word'], reading)
                    self.assertIn((identity, reading), game.discoveries)

    def test_five_natural_cards_cover_weak_common_without_reclassification(self):
        by_id = {card[0]: card for card in BASE_CARDS}
        self.assertEqual(len(NEW_CARDS), 5)
        for identity, (icon, words) in NEW_CARDS.items():
            with self.subTest(identity=identity):
                self.assertEqual(by_id[identity], (identity, icon, words))
                self.assertNotIn(words[0], SPECIAL_READINGS)
                self.assertNotEqual(tail(words[0]), 'ん')
                self.assertGreater(reading_connections(BASE_CARDS)[(identity, words[0])], 0)
        # These are ordinary, picture-recognizable names, not special-only
        # connector aliases. One blocks picture contributes both つ and ぶ.
        for word in ('ぬいばり', 'ズワイガニ', 'つみき', 'ブロック', 'ゴルフ', 'プレゼント'):
            self.assertNotIn(word, SPECIAL_READINGS)
        for word in ('さいほうどうぐ', 'シーフード', 'ホール', 'スポーツ'):
            self.assertIn(word, SPECIAL_READINGS)
        graph = reading_connections(BASE_CARDS)
        weak = [(identity, word) for (identity, word), count in graph.items()
                if word not in SPECIAL_READINGS and count <= 1]
        dead = [(identity, word) for (identity, word), count in graph.items()
                if word not in SPECIAL_READINGS and count == 0]
        # The restricted old-only graph no longer contains 'もみのき'.
        self.assertEqual(dead, [('peach', 'もも')])
        # Gameplay includes the valid added reading 'もみ'.
        self.assertGreater(reading_connections(CARDS)[('peach', 'もも')], 0)
        self.assertLessEqual(len(weak), 6)
        self.assertGreaterEqual((STEP25_WEAK_COMMON - len(weak)) / STEP25_WEAK_COMMON, .60)
        self.assertEqual({tail(word) for _, word in weak}, {'る', 'ゆ', 'も', 'ろ'})

    def test_new_connectors_cover_weak_initials_with_natural_pictures(self):
        expected = {'lipstick', 'gloves', 'snowman', 'grapes', 'curry',
                    'pudding', 'thread', 'candle'}
        self.assertEqual(CONNECTION_IDS, expected)
        for identity, icon, words in CONNECTION_CARDS:
            with self.subTest(identity=identity):
                self.assertTrue(icon)
                self.assertNotEqual(tail(words[0]), 'ん')
                self.assertGreaterEqual(len({head(w) for w in words if tail(w) != 'ん'}), 3)
        playable = {sound: {identity for identity, _, words in CARDS
                            if any(head(w) == sound and tail(w) != 'ん' for w in words)}
                    for sound in ('る', 'ぐ', 'ゆ')}
        self.assertIn('lipstick', playable['る'])
        self.assertIn('curry', playable['る'])
        self.assertIn('gloves', playable['ぐ'])
        self.assertIn('grapes', playable['ぐ'])
        self.assertIn('snowman', playable['ゆ'])
        self.assertTrue(all(len(ids) >= 3 for ids in playable.values()))

    def test_new_cards_chain_through_actual_stock_refill(self):
        by_id = {c[0]: c for c in CARDS}
        game = self.round(mode='solo')
        game.total = 4
        game.cards = [by_id['dog'], by_id['gloves'], by_id['cow']]
        game.stock = [by_id['grapes']]
        game.used = {}; game.history = []; game.seen = set(); game.required = 'ど'
        game.perfect_route = (); game._chain_advice.clear()
        game.command('card', 0)
        self.assertEqual(game.history[-1]['word'], 'ドッグ')
        self.assertEqual(game.cards[0][0], 'grapes')
        game.command('card', 1)
        self.assertEqual(game.history[-1]['word'], 'グローブ')
        game.command('card', 0)
        self.assertEqual(game.history[-1]['word'], 'ぶどう')
        game.command('card', 2)
        self.assertEqual(game.history[-1]['word'], 'うし')
        self.assertEqual(game.phase, 'finished')
        self.assertTrue(game.perfect)

    def test_additions_are_unique_and_gameplay_legal_unless_ending_in_n(self):
        by_id = {identity: words for identity, _, words in CARDS}
        self.assertTrue(ADDITIONAL_READINGS)
        self.assertIn('ドッグ', ADDITIONAL_READINGS['dog'])
        for identity, words in ADDITIONAL_READINGS.items():
            self.assertIn(identity, by_id)
            for word in words:
                with self.subTest(identity=identity, word=word):
                    self.assertIn(word, by_id[identity])
                    self.assertEqual(sum(normalize_reading(w) == normalize_reading(word)
                                         for w in by_id[identity]), 1)
                    card = (identity, '', by_id[identity])
                    moves = chain_moves((card,), head(word), frozenset())
                    self.assertEqual((0, word) in moves, tail(word) != 'ん')

    def test_recent_everyday_readings_are_registered_and_usable(self):
        additions = {
            'glasses': ('グラス',),
            'ship': ('きゃくせん', 'りょかくせん', 'クルーズシップ'),
            'chair': ('チェアー',),
            'lipstick': ('リップカラー',),
            'curry': ('カレーソース',),
            'pudding': ('カスタードプリン', 'カラメルプリン'),
            'thread': ('ソーイングスレッド', 'ミシンいと'),
            'candle': ('キャンドルライト',),
        }
        self.assertEqual(sum(map(len, additions.values())), 12)
        cards = {card[0]: card for card in CARDS}
        for identity, words in additions.items():
            for word in words:
                with self.subTest(identity=identity, word=word):
                    self.assertIn(word, cards[identity][2])
                    moves = chain_moves((cards[identity],), head(word), frozenset())
                    self.assertEqual((0, word) in moves, tail(word) != 'ん')

    def test_new_common_aliases_preserve_dictionary_and_legality(self):
        additions = {
            'lipstick': ('べに', 'ぼうべに', 'コスメ'),
            'grapes': ('かじつ',),
            'pudding': ('おかし', 'ようがし'),
            'thread': ('ボビン', 'スプール'),
            'ship': ('クルーズせん',),
            'gift': ('つつみもの',),
        }
        self.assertEqual(sum(map(len, additions.values())), 10)
        cards = {card[0]: card for card in CARDS}
        for identity, words in additions.items():
            for word in words:
                with self.subTest(identity=identity, word=word):
                    self.assertIn(word, cards[identity][2])
                    self.assertEqual(sum(normalize_reading(w) == normalize_reading(word)
                                         for w in cards[identity][2]), 1)
                    moves = chain_moves((cards[identity],), head(word), frozenset())
                    self.assertEqual((0, word) in moves, tail(word) != 'ん')

    def test_added_aliases_remain_legal_and_unique(self):
        additions = {
            'cat': ('にゃー',), 'knife': ('クッキングナイフ',),
            'tree': ('コニファー',),
        }
        self.assertEqual(sum(map(len, additions.values())), 3)
        cards = {card[0]: card for card in CARDS}
        for identity, words in additions.items():
            for word in words:
                with self.subTest(identity=identity, word=word):
                    self.assertIn(word, cards[identity][2])
                    self.assertEqual(sum(normalize_reading(w) == normalize_reading(word)
                                         for w in cards[identity][2]), 1)
                    moves = chain_moves((cards[identity],), head(word), frozenset())
                    self.assertEqual((0, word) in moves, tail(word) != 'ん')

    def test_familiar_names_and_aliases_are_legal_and_unique(self):
        additions = {
            'moon': ('ルナ',), 'ice': ('キューブアイス',),
            'backpack': ('ナップザック', 'ナップサック'),
            'curry': ('ライスカレー',), 'parsley': ('こうそう',),
            'bread': ('スライスパン', 'スライスブレッド'),
            'mouse': ('チューチュー',), 'cow': ('モーモー',),
            'pudding': ('フラン',),
        }
        self.assertEqual(sum(map(len, additions.values())), 11)
        cards = {card[0]: card for card in CARDS}
        for identity, words in additions.items():
            for word in words:
                with self.subTest(identity=identity, word=word):
                    self.assertIn(word, cards[identity][2])
                    self.assertEqual(sum(normalize_reading(w) == normalize_reading(word)
                                         for w in cards[identity][2]), 1)
                    moves = chain_moves((cards[identity],), head(word), frozenset())
                    self.assertEqual((0, word) in moves, tail(word) != 'ん')

    def test_picture_aliases_added_for_recognition(self):
        additions = {
            'curry': ('カリー', 'カレールー', 'カレールウ'),
            'loupe': ('マグニファイア',), 'snowman': ('ゆきにんぎょう',),
            'gift': ('ラッピングボックス',),
        }
        self.assertEqual(sum(map(len, additions.values())), 6)
        cards = {card[0]: card for card in CARDS}
        for identity, words in additions.items():
            for word in words:
                with self.subTest(identity=identity, word=word):
                    self.assertIn(word, cards[identity][2])
                    self.assertEqual(sum(normalize_reading(w) == normalize_reading(word)
                                         for w in cards[identity][2]), 1)
                    moves = chain_moves((cards[identity],), head(word), frozenset())
                    self.assertEqual((0, word) in moves, tail(word) != 'ん')

    def test_additional_recognizable_picture_aliases(self):
        additions = {
            'teddy': ('ベアー',), 'top': ('スピニングトップ',),
            'sand': ('かさ',), 'knife': ('ブレード',),
        }
        cards = {card[0]: card for card in CARDS}
        for identity, words in additions.items():
            for word in words:
                with self.subTest(identity=identity, word=word):
                    self.assertIn(word, cards[identity][2])
                    self.assertEqual(sum(normalize_reading(w) == normalize_reading(word)
                                         for w in cards[identity][2]), 1)
                    moves = chain_moves((cards[identity],), head(word), frozenset())
                    self.assertEqual((0, word) in moves, tail(word) != 'ん')

    def test_expanded_broad_categories_remain_special_readings(self):
        for word in ('ほにゅうるい', 'げっしるい', 'ちょうるい', 'こうかくるい',
                     'かんきつるい', 'きのこるい', 'しんようじゅ'):
            with self.subTest(word=word):
                self.assertIn(word, SPECIAL_READINGS)
                self.assertTrue(any(word in words for _, _, words in CARDS))

    def test_expanded_picture_names_are_selectable_and_discovered(self):
        examples = {'lavender': 'ヒヤシンス', 'dog': 'いぬころ',
                    'trumpet': 'きんぞくがっき', 'ship': 'おふね',
                    'mushroom': 'ファンガス', 'golf': 'ゴルフコース',
                    'gift': 'プレゼントボックス', 'tree': 'しんようじゅ',
                    'mouse': 'ハツカネズミ', 'backpack': 'ランドセル',
                    'top': 'スピニングトップ', 'tomato': 'トメイト', 'pot': 'シチュー',
                    'zucchini': 'ズッキーニ', 'cow': 'めうし',
                    'orange': 'マンダリンオレンジ', 'otter': 'シーオッター',
                    'umbrella': 'ひがさ'}
        by_id = {card[0]: card for card in CARDS}
        for mode in ('solo', 'battle'):
            for identity, word in examples.items():
                with self.subTest(mode=mode, identity=identity, word=word):
                    game = self.round(mode=mode)
                    game.cards = [by_id[identity]]; game.stock = []; game.used = {}
                    game.history = []; game.required = head(word)
                    game.seen = {normalize_reading(other) for other in game.cards[0][2]
                                 if other != word and head(other) == head(word)}
                    game.perfect_route = (); game._chain_advice.clear()
                    game.command('card', 0)
                    self.assertEqual(game.history[-1]['word'], word)
                    self.assertIn((identity, word), game.discoveries)

    def test_new_common_names_and_visible_features_are_playable(self):
        examples = [('backpack', 'バッグ'), ('chicken', 'とさか'),
                    ('riceball', 'こめ'), ('paint', 'えのぐパレット'),
                    ('parsley', 'くき'), ('radish', 'ベジタブル'),
                    ('golf', 'カップ'), ('golf', 'フラグ')]
        by_id = {card[0]: card for card in CARDS}
        for mode in ('solo', 'battle'):
            for identity, word in examples:
                with self.subTest(mode=mode, identity=identity, word=word):
                    game = self.round(mode=mode)
                    game.cards = [by_id[identity]]; game.stock = []; game.used = {}
                    game.history = []; game.required = head(word)
                    game.seen = {normalize_reading(other) for other in game.cards[0][2]
                                 if other != word and head(other) == head(word)}
                    game.perfect_route = (); game._chain_advice.clear()
                    game.command('card', 0)
                    self.assertEqual(game.history[-1]['word'], word)
                    self.assertIn((identity, word), game.discoveries)

    def test_same_initial_aliases_are_candidates_and_selectable(self):
        game = self.round()
        game.cards = [('test', '🐕', ('どうぶつ', 'ドッグ')),
                      ('next', '🎻', ('がっき',))]
        game.stock = []; game.used = {}; game.required = 'ど'; game.seen = set()
        game.perfect_route = (); game._chain_advice.clear()
        self.assertEqual(chain_moves(game.cards, 'ど', set()),
                         [(0, 'どうぶつ'), (0, 'ドッグ')])
        game.seen = {normalize_reading('どうぶつ')}
        game.command('card', 0)
        self.assertEqual(game.history[0]['word'], 'ドッグ')
        self.assertIn(('test', 'ドッグ'), game.discoveries)

    def test_n_ending_never_becomes_a_gameplay_move(self):
        card = ('test', '🥄', ('スプーン', 'すず'))
        self.assertEqual(chain_moves((card,), 'す', frozenset()), [(0, 'すず')])

    def test_solo_relink_prefers_witnessed_longer_chain_and_highlight_matches_reading(self):
        game = ShiritoriRound(mode='solo', clock=lambda: 0)
        game.phase = 'blocked'
        game.cards = [('stray', '', ('こさ',)), ('a', '', ('あす', 'あぬ')),
                      ('b', '', ('すき',)), ('c', '', ('きか',)),
                      ('d', '', ('ぬいぐるみ',)), ('e', '', ('みそ',)),
                      ('f', '', ('そら',))]
        game.stock = []; game.used = {}; game.seen = set()
        game.perfect_route = (); game._chain_advice.clear()
        game.command('relink')
        self.assertEqual((game.phase, game.required, game.hint, game.relinks),
                         ('playing', 'あ', 1, 1))
        state = (tuple(game.cards), (), 'あ', frozenset())
        move, plan = game._chain_advice[state]
        self.assertEqual(move, (1, 'あぬ'))
        self.assertGreaterEqual(plan['length'], 4)
        self.assertFalse(plan['perfect'])
        game.command('card', game.hint)
        self.assertEqual(game.history[-1]['word'], 'あぬ')
        self.assertEqual(game.required, 'ぬ')

    def test_relink_without_legal_readings_leaves_blocked_state_unchanged(self):
        game = ShiritoriRound(mode='solo', clock=lambda: 0)
        game.phase = 'blocked'; game.cards = [('a', '', ('みかん',))]
        game.stock = []; game.used = {}; game.seen = set(); game.relinks = 2
        game.command('relink')
        self.assertEqual((game.phase, game.relinks, game.hint), ('blocked', 2, None))

    def test_ambiguous_reading_prefers_a_longer_witnessed_continuation(self):
        game = self.round()
        game.cards = [('test', '', ('いす', 'いぬ')), ('a', '', ('すいか',)),
                      ('b', '', ('すな',)), ('c', '', ('ぬいぐるみ',)),
                      ('d', '', ('みそ',)), ('e', '', ('そら',))]
        game.stock = []; game.used = {}; game.required = 'い'; game.seen = set()
        game.perfect_route = (); game._chain_advice.clear()
        # Two immediate す choices are shorter than the witnessed ぬ→み→そ path.
        self.assertEqual(game.choose_move_for_card(0), (0, 'いぬ'))

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


    def test_pre_change_catalog_preserves_allowed_words_and_legacy_mappings(self):
        import json
        from pathlib import Path
        fixture = Path(__file__).parent / 'fixtures' / 'shiritori-catalog-pre-particle.json'
        baseline = json.loads(fixture.read_text(encoding='utf-8'))
        self.assertEqual(sum(len(card['words']) for card in baseline), 829)
        self.assertEqual(sum(len(card[2]) for card in CARDS), 731)
        self.assertEqual(sum(len(aliases) for aliases in LEGACY_READINGS.values()), 73)
        self.assertEqual([card['id'] for card in baseline], [card[0] for card in CARDS])
        added = {'curry': ('ごはんりょうり',), 'riceball': ('ごはんりょうり',),
                 'lavender': ('むらさき',)}
        self.assertEqual(sum(map(len, added.values())), 3)
        for old, current in zip(baseline, CARDS):
            identity, icon, words = current
            aliases = LEGACY_READINGS.get(identity, {})
            with self.subTest(identity=identity):
                self.assertEqual(icon, old['icon'])
                self.assertTrue(set(aliases) <= set(old['words']))
                retained = tuple(word for word in old['words']
                                 if word not in aliases and (identity, word) not in RETIRED_SEMANTIC_READINGS)
                self.assertTrue(all(word not in old['words'] for word in added.get(identity, ())))
                self.assertEqual(words, retained + added.get(identity, ()))
                for former, representative in aliases.items():
                    self.assertNotIn(former, words)
                    if representative is not None:
                        self.assertIn(representative, words)
                    self.assertNotIn((0, former), chain_moves((current,), head(former), frozenset()))
        self.assertEqual(LEGACY_READINGS['radish']['にんじんのは'], 'にんじん')
        self.assertEqual(LEGACY_READINGS['tree']['もみのき'], 'もみ')
        for phase in ('intro', 'finished'):
            game = ShiritoriRound()
            game.phase = phase
            catalog = game.snapshot()['catalog']
            self.assertEqual(len(catalog), 81)
            for card in catalog:
                self.assertEqual(card['legacy'], LEGACY_READINGS.get(card['id'], {}))

    def test_semantic_retirements_are_not_active_and_other_759_readings_keep_order(self):
        import json
        from pathlib import Path
        fixture = Path(__file__).parent / 'fixtures' / 'shiritori-catalog-pre-semantic.json'
        before = json.loads(fixture.read_text(encoding='utf-8'))
        self.assertEqual(sum(len(card['words']) for card in before), 759)
        self.assertEqual(len(RETIRED_SEMANTIC_READINGS), 28)
        self.assertEqual([card['id'] for card in before], [card[0] for card in CARDS])
        for old, current in zip(before, CARDS):
            identity, icon, words = current
            self.assertEqual(icon, old['icon'])
            self.assertEqual(words, tuple(w for w in old['words']
                                          if (identity, w) not in RETIRED_SEMANTIC_READINGS))
            for removed_id, removed_word in RETIRED_SEMANTIC_READINGS:
                if removed_id == identity:
                    self.assertIn(removed_word, old['words'])
                    self.assertNotIn(removed_word, words)
                    self.assertNotIn((0, removed_word),
                                     chain_moves((current,), head(removed_word), frozenset()))
        self.assertEqual(LEGACY_READINGS['lavender']['ヒヤシンスのはな'], 'ヒヤシンス')
        self.assertEqual(LEGACY_READINGS['paint']['えのぐのパレット'], 'パレット')
        self.assertEqual(LEGACY_READINGS['plate']['フォークとナイフ'], 'フォーク')
        self.assertIsNone(LEGACY_READINGS['blocks']['レンガのかべ'])

    def test_natural_single_term_categories_are_special_and_discovered(self):
        additions = {'curry': 'ごはんりょうり', 'riceball': 'ごはんりょうり',
                     'lavender': 'むらさき'}
        cards = {card[0]: card for card in CARDS}
        for mode in ('solo', 'battle'):
            for identity, word in additions.items():
                with self.subTest(mode=mode, identity=identity):
                    card = cards[identity]
                    self.assertIn(word, SPECIAL_READINGS)
                    # No playable specific reading on this card begins with
                    # the same character, so a generic category displaces none.
                    self.assertEqual(chain_moves((card,), head(word), frozenset()), [(0, word)])
                    game = self.round(mode=mode)
                    game.cards = [card]
                    game.stock = []; game.used = {}; game.history = []
                    game.required = head(word); game.seen = set()
                    game.perfect_route = (); game._chain_advice.clear()
                    game.command('card', 0)
                    self.assertEqual(game.history[-1]['word'], word)
                    self.assertIn((identity, word), game.discoveries)

        # One shared reading can be discovered per picture, but a round
        # cannot use that same normalized reading for both pictures.
        both = (cards['curry'], cards['riceball'])
        shared = 'ごはんりょうり'
        self.assertEqual(chain_moves(both, 'ご', frozenset()), [(0, shared), (1, shared)])
        self.assertEqual(chain_moves(both, 'ご', frozenset({normalize_reading(shared)})), [])

    def test_new_picture_aliases_are_chosen_and_discovered(self):
        additions = {
            'ramune': ('ラムネびん', 'ラムネボトル', 'ビーだま'),
            'umbrella': ('あまぐ',),
            'top': ('スピニングトップ',),
            'riceball': ('のりおにぎり',),
            'thread': ('いとのまき',),
            'glasses': ('めがねのフレーム',),
            'guitar': ('ギターのげん',),
            'car': ('タイヤ', 'くるまのタイヤ', 'ホイール'),
        }
        cards = {card[0]: card for card in CARDS}
        self.assertEqual(sum(map(len, additions.values())), 12)
        retired = {(i, w) for i, words in additions.items() for w in words if w in LEGACY_READINGS.get(i, {})}
        self.assertEqual(retired, {('thread', 'いとのまき'), ('glasses', 'めがねのフレーム'),
                                   ('guitar', 'ギターのげん'), ('car', 'くるまのタイヤ')})
        for mode in ('solo', 'battle'):
            for identity, words in additions.items():
                for word in words:
                    with self.subTest(mode=mode, identity=identity, word=word):
                        card = cards[identity]
                        if (identity, word) in retired:
                            self.assertNotIn(word, card[2])
                            self.assertIn(LEGACY_READINGS[identity][word], card[2])
                            self.assertNotIn((0, word), chain_moves((card,), head(word), frozenset()))
                            continue
                        self.assertEqual(sum(normalize_reading(w) == normalize_reading(word)
                                             for w in card[2]), 1)
                        self.assertIn(word, card[2])
                        game = self.round(mode=mode)
                        game.cards = [card]
                        game.stock = []; game.used = {}; game.history = []
                        game.required = head(word)
                        game.seen = {normalize_reading(w) for w in card[2]
                                     if w != word and head(w) == head(word)}
                        game.perfect_route = (); game._chain_advice.clear()
                        if tail(word) == 'ん':
                            self.assertNotIn((0, word), game.moves())
                        else:
                            game.command('card', 0)
                            self.assertEqual(game.history[0]['word'], word)
                            self.assertIn((identity, word), game.discoveries)


if __name__ == '__main__':
    unittest.main()
