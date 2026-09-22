"""Illustrated word-chain duel. Pure Python rules with an injectable clock/RNG."""
import random
import time
import unicodedata
from functools import lru_cache
from typing import NamedTuple
from timed_chain import TimedChain

# Emoji are platform pictograms, not artwork copied from a commercial game.
# Finite picture names, categories and visible features; one reading per head.
CARDS = (
    ("apple", "🍎", ("りんご", "くだもの", "フルーツ", "たべもの", "しんしゅうりんご", "すりおろしりんご")),
    ("gorilla", "🦍", ("ゴリラ", "さる", "どうぶつ", "るいじんえん")),
    ("trumpet", "🎺", ("ラッパ", "がっき", "トランペット", "きんかんがっき")),
    ("panda", "🐼", ("パンダ", "くま", "どうぶつ", "ジャイアントパンダ")),
    ("daruma", "🔴", ("だるま", "おきもの", "えんぎもの", "にんぎょう")),
    ("camel", "🐪", ("らくだ", "どうぶつ", "ひとこぶらくだ")),
    ("radish", "🥕", ("にんじん", "やさい", "キャロット", "こんさい", "たべもの")),
    ("dog", "🐕", ("いぬ", "こいぬ", "どうぶつ", "ペット")),
    ("teddy", "🧸", ("ぬいぐるみ", "くま", "おもちゃ", "テディベア", "にんぎょう")),
    ("orange", "🍊", ("みかん", "くだもの", "フルーツ", "たべもの")),
    ("turtle", "🐢", ("かめ", "りくがめ", "どうぶつ", "はちゅうるい")),
    ("glasses", "👓", ("めがね", "がんきょう", "レンズ", "フレーム")),
    ("cat", "🐈", ("ねこ", "こねこ", "どうぶつ", "ペット")),
    ("tree", "🌲", ("まつ", "き", "しょくぶつ", "じゅもく")),
    ("moon", "🌙", ("つき", "よぞら", "みかづき", "てんたい")),
    ("fox", "🦊", ("きつね", "どうぶつ", "けもの", "フォックス")),
    ("mouse", "🐁", ("ねずみ", "どうぶつ", "マウス", "けもの")),
    ("ear", "👂", ("みみ", "からだ", "じかく", "ちょうかくきかん")),
    ("bee", "🐝", ("みつばち", "はち", "むし", "こんちゅう")),
    ("butterfly", "🦋", ("ちょう", "むし", "こんちゅう", "バタフライ")),
    ("rabbit", "🐇", ("うさぎ", "どうぶつ", "ラビット", "けもの")),
    ("guitar", "🎸", ("ギター", "がっき", "エレキギター", "げんがっき")),
    ("octopus", "🐙", ("たこ", "うみのいきもの", "なんたいどうぶつ", "オクトパス")),
    ("bird", "🐦", ("とり", "ことり", "どうぶつ", "バード")),
    ("squirrel", "🐿️", ("りす", "どうぶつ", "けもの")),
    ("melon", "🍉", ("すいか", "くだもの", "フルーツ", "たべもの")),
    ("umbrella", "☂️", ("かさ", "あまがさ", "ようがさ", "レイングッズ")),
    ("fish", "🐟", ("さかな", "ぎょるい", "うみのいきもの", "フィッシュ")),
    ("eggplant", "🍆", ("なす", "やさい", "たべもの", "しょくざい")),
    ("bell", "🔔", ("すず", "かね", "ベル", "がっき")),
    ("trousers", "👖", ("ズボン", "ふく", "ジーンズ", "デニム", "ボトムス")),
    ("ship", "🚢", ("ふね", "のりもの", "きせん", "シップ")),
    ("mushroom", "🍄", ("きのこ", "しょくざい", "マッシュルーム")),
    ("ice", "🧊", ("こおり", "アイスキューブ", "ロックアイス", "ひょうかい")),
    ("car", "🚗", ("くるま", "じどうしゃ", "のりもの", "マイカー")),
    ("mountain", "⛰️", ("やま", "さん", "マウンテン", "みね")),
    ("peach", "🍑", ("もも", "くだもの", "ピーチ", "フルーツ", "たべもの")),
    ("bread", "🍞", ("パン", "しょくパン", "トースト", "ブレッド", "たべもの")),
    ("lion", "🦁", ("ライオン", "どうぶつ", "しし", "けもの")),
    ("top", "🌀", ("こま", "おもちゃ", "かいてんたい")),
    ("pillow", "🛏️", ("まくら", "しんぐ", "ねどこ")),
    ("otter", "🦦", ("らっこ", "どうぶつ", "うみのいきもの")),
    ("koala", "🐨", ("コアラ", "どうぶつ", "ゆうたいるい")),
    ("ramune", "🍾", ("ラムネ", "のみもの", "たんさんいんりょう")),
    ("tie", "👔", ("ネクタイ", "ふく", "えりもと")),
    ("chair", "🪑", ("いす", "かぐ", "ざせき")),
    ("zucchini", "🥒", ("ズッキーニ", "やさい", "たべもの")),
    ("chicken", "🐔", ("にわとり", "とり", "どうぶつ")),
    ("backpack", "🎒", ("リュック", "かばん", "にもつ")),
    ("scarf", "🧣", ("マフラー", "えりまき", "ぼうかんぐ")),
    ("radio", "📻", ("ラジオ", "じゅしんき", "おんきょうきき")),
    ("riceball", "🍙", ("おにぎり", "ごはん", "たべもの")),
    ("dragon", "🐉", ("りゅう", "ドラゴン", "でんせつのいきもの")),
    ("cow", "🐄", ("うし", "どうぶつ", "かちく")),
    ("salt", "🧂", ("しお", "ちょうみりょう", "ソルト")),
    ("plate", "🍽️", ("おさら", "しょっき", "プレート")),
    ("lavender", "🪻", ("ラベンダー", "はな", "しょくぶつ")),
    ("diamond", "💎", ("ダイヤ", "ほうせき", "きせき")),
    ("beans", "🫘", ("まめ", "しょくざい", "たね")),
    ("medaka", "🐟", ("めだか", "さかな", "ぎょるい")),
    ("sand", "🏖️", ("すな", "はまべ", "ビーチ")),
    ("pot", "🍲", ("なべ", "りょうり", "しょっき")),
    ("bagel", "🥯", ("ベーグル", "パン", "たべもの")),
    ("loupe", "🔍", ("ルーペ", "むしめがね", "かくだいきょう")),
    ("paint", "🎨", ("ペンキ", "とりょう", "いろ")),
    ("knife", "🔪", ("ナイフ", "ほうちょう", "カトラリー")),
    ("tomato", "🍅", ("トマト", "やさい", "たべもの")),
    ("parsley", "🌿", ("パセリ", "ハーブ", "やさい", "かおりづけ")),
)
# Indivisible display-reading block in every initial certified route.
PERFECT_CANONICAL_SEGMENT = (
    ('tomato', 'トマト'), ('bird', 'とり'), ('apple', 'りんご'),
    ('gorilla', 'ゴリラ'), ('trumpet', 'ラッパ'), ('parsley', 'パセリ'),
)
# Certified fallback spine, not a freely rotating ring: rotation could split
# the canonical block. Retain the existing name for the catalog witness.
PERFECT_RING = (
    'tomato', 'bird', 'apple', 'gorilla', 'trumpet', 'parsley',
    'squirrel', 'bell', 'zucchini', 'chicken', 'backpack', 'car',
    'scarf', 'radio', 'riceball', 'dragon', 'cow', 'salt', 'plate', 'lavender',
    'diamond', 'mountain', 'beans', 'medaka', 'umbrella', 'fish', 'eggplant',
    'sand', 'pot', 'bagel', 'loupe', 'paint', 'mushroom', 'koala', 'camel',
    'daruma', 'tree', 'moon', 'fox', 'mouse', 'bee', 'butterfly', 'rabbit',
    'guitar', 'octopus', 'top', 'pillow', 'otter', 'ice',
)
SMALL = str.maketrans("ゃゅょぁぃぅぇぉっゎ", "やゆよあいうえおつわ")

# Durable miss outline (~1.2s): parity with numbers WRONG_EFFECT_FRAMES (~72 @ 60fps).
# Short-landscape status truncates the miss copy, so the wrong card itself must stay marked.
MISS_OUTLINE_SECONDS = 1.2


@lru_cache(maxsize=2048)
def normalize_reading(word):
    """Comparison key only; never replace a display/history reading with it.

    NFC joins voiced kana. Keep internal small kana and long marks (different
    words must not collapse); head/tail apply the house boundary rules.
    """
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c
                   for c in unicodedata.normalize('NFC', word))


@lru_cache(maxsize=2048)
def head(word):
    return normalize_reading(word)[:1].translate(SMALL)


@lru_cache(maxsize=2048)
def tail(word):
    """House rule: long marks use preceding kana; small kana become full-size."""
    return normalize_reading(word).rstrip("ー")[-1:].translate(SMALL)


@lru_cache(maxsize=4096)
def _readings_from(card, required):
    """Catalog-local cache; no board/stock state is retained here."""
    return tuple((word, normalize_reading(word)) for word in card[2]
                 if head(word) == required and tail(word) != 'ん')


def chain_moves(cards, required, seen):
    """Pure legal-move enumeration; None is a consumed board slot."""
    required = head(required)
    seen = {normalize_reading(w) for w in seen}
    return [(i, word) for i, card in enumerate(cards) if card is not None
            for word, key in _readings_from(card, required) if key not in seen]


def starting_route(required, total, seen, rng, node_budget=256):
    """Bounded randomized chain with the six-card block as one atomic edge."""
    reserved = {identity for identity, _ in PERFECT_CANONICAL_SEGMENT}
    by_head = {}
    for card in CARDS:
        if card[0] in reserved:
            continue
        for word in card[2]:
            if tail(word) != "ん":
                by_head.setdefault(head(word), []).append(((card[0], word),))
    by_head.setdefault('と', []).append(PERFECT_CANONICAL_SEGMENT)
    nodes = 0

    def search(required, route, ids, words):
        nonlocal nodes
        if len(route) == total:
            return route if reserved <= ids else None
        if nodes >= node_budget:
            return None
        nodes += 1
        choices = list(by_head.get(required, ()))
        rng.shuffle(choices)
        for block in choices:
            new_ids = {identity for identity, _ in block}
            new_words = {normalize_reading(word) for _, word in block}
            if new_ids & ids or new_words & words or len(route) + len(block) > total:
                continue
            if not reserved <= (ids | new_ids) and total - len(route) - len(block) < 6:
                continue
            found = search(tail(block[-1][1]), route + list(block), ids | new_ids, words | new_words)
            if found is not None:
                return found
            if nodes >= node_budget:
                break
        return None

    return search(head(required), [], set(), {normalize_reading(w) for w in seen})


def chain_step(cards, stock, seen, move):
    """Simulate the real refill/rescue rules without touching the live round."""
    i, word = move
    cards, stock = list(cards), list(stock)
    seen = {normalize_reading(w) for w in seen} | {normalize_reading(word)}
    required = tail(word)
    cards[i] = stock.pop(0) if stock else None
    if cards[i] is not None and not chain_moves(cards, required, seen):
        for j, card in enumerate(stock):
            if chain_moves((card,), required, seen):
                cards[i], stock[j] = card, cards[i]
                break
    return tuple(cards), tuple(stock), required, frozenset(seen)


def longest_chain_move(cards, stock, required, seen, node_budget=4096):
    """Cooperative longest continuation, with a fair bounded search per root.

    A full route is a proof of possibility, not a prediction of player input.
    On cutoff, scores are achieved path lengths, never invented exact optima.
    """
    required = head(required)
    initial = (tuple(cards), tuple(stock), required, frozenset(normalize_reading(w) for w in seen))
    candidates = chain_moves(initial[0], required, initial[3])
    if not candidates:
        return None, {"length": 0, "perfect": False, "exact": True, "nodes": 0, "route": ()}
    remaining = sum(c is not None for c in cards) + len(stock)
    per_move = max(1, node_budget // len(candidates))
    best_move, best_length, total_nodes, all_exact = candidates[0], 0, 0, True
    best_route = ()
    for move in candidates:
        memo, nodes = {}, 0

        def search(state):
            nonlocal nodes
            if state in memo:
                return memo[state], True
            if nodes >= per_move:
                return (), False
            nodes += 1
            board, deck, head, words = state
            bound = sum(c is not None for c in board) + len(deck)
            options = chain_moves(board, head, words)
            best, exact = (), True
            for option in options:
                suffix, complete = search(chain_step(board, deck, words, option))
                route = (option,) + suffix
                if len(route) > len(best):
                    best = route
                exact = exact and complete
                if len(best) == bound:
                    memo[state] = best
                    return best, True
                if nodes >= per_move:
                    exact = False
                    break
            if exact:
                memo[state] = best
            return best, exact

        suffix, exact = search(chain_step(initial[0], initial[1], initial[3], move))
        route = (move,) + suffix
        length = len(route)
        total_nodes += nodes
        all_exact = all_exact and exact
        if length > best_length:
            best_move, best_length = move, length
            best_route = route
        if length == remaining:
            return move, {"length": length, "perfect": True, "exact": True, "nodes": total_nodes, "route": route}
    return best_move, {"length": best_length, "perfect": False, "exact": all_exact, "nodes": total_nodes, "route": best_route}


class PerfectStep(NamedTuple):
    identity: str
    reading: str
    key: str
    required: str


def certify_route(state, identity_route):
    """Resolve identities on the current board, replay refill, prove exhaustion.

    Never infer availability from board+stock membership alone: a connector
    stranded in stock must actually become visible under chain_step's rules.
    """
    witnesses = []
    for identity, word in identity_route:
        move = next((m for m in chain_moves(state[0], state[2], state[3])
                     if state[0][m[0]][0] == identity and m[1] == word), None)
        if move is None:
            return None
        witnesses.append((state, move, PerfectStep(identity, word, normalize_reading(word), tail(word))))
        state = chain_step(state[0], state[1], state[3], move)
    return witnesses if not any(state[0]) and not state[1] else None


class ShiritoriRound:
    def __init__(self, difficulty="normal", rng=None, clock=None, mode="battle", total=24):
        self.rng = rng or random.Random()
        self.clock = clock or time.monotonic
        self.difficulty = difficulty if difficulty in ("easy", "normal", "hard") else "normal"
        self.limit = {"easy": 30, "normal": 20, "hard": 12}[self.difficulty]
        self.phase = "intro"
        self.mode = mode if mode in ("battle", "solo") else "battle"
        self.total = total if type(total) is int and total in (12, 24, 36, 48) else 24
        self.stock = []
        self.seen = set()
        self.relinks = 2
        self.resume_phase = "playing"
        self.refilled = None
        self.break_next = False
        self.cards = []
        self.discoveries = set()  # Retain earned readings across pause/restart snapshots.
        self.history = []
        self.used = {}
        self.message = "絵をタップ！つながる読み方を自動で選ぶよ。"
        self.required = "り"
        self.last_word = "しりとり"
        self.selected = None
        self.mistakes = 0
        self.miss_card = None
        self.miss_until = 0
        self.hints = 3
        self.hint = None
        self.winner = None
        self.turn = "you"
        self.deadline = 0
        self.saved_remaining = 0
        self.revision = 0
        self.cpu_move = None
        self._chain_advice = {}
        self.perfect_route = ()  # Identity-based certificate, never sent to UI.
        self.initial_perfect_route = ()
        self.chain = TimedChain(self.clock())

    def start(self):
        self.chain = TimedChain(self.clock())
        self._chain_advice.clear()
        by_id = {card[0]: card for card in CARDS}
        seed = self.rng.choice(CARDS)[2][0]
        route_words = starting_route(tail(seed), self.total, {seed}, self.rng)
        if route_words is None:
            seed = 'トースト'
            route_words = [(key, by_id[key][2][0]) for key in PERFECT_RING[:self.total]]
        chosen = [by_id[key] for key, _ in route_words]
        self.cards, self.stock = chosen[:24], chosen[24:]
        self.rng.shuffle(self.cards)
        self.used = {}
        self.history = []
        self.last_word, self.required = seed, tail(seed)
        self.seen = {normalize_reading(seed)}
        self.turn, self.phase = "you", "playing"
        self.winner = None
        self.cpu_move = None
        self.selected = self.hint = None
        self.mistakes, self.hints = 0, 3
        self.miss_card = None
        self.miss_until = 0
        self.relinks = 2
        self.refilled = None
        self.break_next = False
        self.message = f"「{self.required}」から始まる絵をさがそう。"
        self.deadline = self.clock() + self.limit
        # Replay the witness using the same transition rules as planning.
        state = (tuple(self.cards), tuple(self.stock), self.required, frozenset(self.seen))
        witnesses = certify_route(state, route_words)
        if witnesses is None:
            raise ValueError('Invalid perfect starting route or refill witness')
        self.remember_perfect(witnesses)
        self.initial_perfect_route = self.perfect_route
        self.revision += 1

    def moves(self):
        return chain_moves(tuple(None if i in self.used else c for i, c in enumerate(self.cards)),
                           self.required, self.seen)

    def finish(self, winner, reason):
        self.phase, self.winner, self.message = "finished", winner, reason
        self.selected = self.hint = None
        self.miss_card = None
        self.miss_until = 0
        self.chain.sync(self.clock(), ())
        self.revision += 1

    def remaining(self):
        return max(0, self.saved_remaining if self.phase == "paused" else self.deadline - self.clock())

    def update(self):
        self.chain.sync(self.clock(), (self.turn,) if self.phase == 'playing' else ())
        if self.phase != "playing":
            return
        if self.mode == "solo":
            return
        if self.turn == "you" and self.remaining() <= 0:
            self.finish("cpu", "時間切れ。次は読み方の候補も使ってみよう！")
        elif self.turn == "cpu":
            if self.cpu_move is None:
                self.prepare_cpu()
            if self.remaining() <= 0 and self.cpu_move is not None:
                self.take(*self.cpu_move)

    def prepare_cpu(self):
        moves = self.moves()
        if not moves:
            self.finish("you", "ルナがつなげなくなった！")
            return
        self.cpu_move, self.cpu_plan = self.chain_advice()

    def remember_perfect(self, witnesses):
        """Install only a fully replayed proof, with exact-state suffix caches."""
        self._chain_advice.clear()
        self.perfect_route = tuple(step for _, _, step in witnesses)
        route = tuple(move for _, move, _ in witnesses)
        for i, (state, move, _) in enumerate(witnesses):
            self._chain_advice[state] = (move, {'length': len(route)-i, 'perfect': True,
                'exact': True, 'nodes': 0, 'route': route[i:], 'witness': self.perfect_route[i:]})

    def chain_advice(self):
        """Exact proof first, identity re-sync second, bounded replanning last.

        A search cutoff is UNKNOWN, not proof that perfect is impossible.
        Display/history spelling never participates in the state comparison.
        """
        board = tuple(None if i in self.used else c for i, c in enumerate(self.cards))
        state = (board, tuple(self.stock), head(self.required), frozenset(normalize_reading(w) for w in self.seen))
        if state in self._chain_advice:
            return self._chain_advice[state]
        remaining_ids = {c[0] for c in board + tuple(self.stock) if c is not None}
        suffix = [(s.identity, s.reading) for s in self.perfect_route if s.identity in remaining_ids]
        if suffix and {identity for identity, _ in suffix} == remaining_ids:
            # Also accept another reading of the next picture (apple: し/す -> ご).
            # Each candidate is replayed to the end; matching tails alone is not proof.
            candidates = [suffix] + [[(suffix[0][0], word)] + suffix[1:]
                for i, word in chain_moves(board, state[2], state[3])
                if board[i][0] == suffix[0][0] and word != suffix[0][1]]
            for candidate in candidates:
                witnesses = certify_route(state, candidate)
                if witnesses:
                    self.remember_perfect(witnesses)
                    return self._chain_advice[state]
        self._chain_advice.clear()
        move, plan = longest_chain_move(*state)
        self._chain_advice[state] = (move, plan)
        if plan['perfect']:
            replay, identities = state, []
            for index, word in plan['route']:
                identities.append((replay[0][index][0], word))
                replay = chain_step(replay[0], replay[1], replay[3], (index, word))
            self.remember_perfect(certify_route(state, identities))
        return move, plan

    def take(self, index, word):
        owner = self.turn
        self.chain.hit(owner, self.clock())
        self.cpu_move = None
        self.miss_card = None
        self.miss_until = 0
        if owner == "you":
            self.discoveries.add((self.cards[index][0], word))
        self.used[index] = owner
        self.history.append({"word": word, "owner": owner, "icon": self.cards[index][1], "id": self.cards[index][0], "readings": self.cards[index][2], "relinked": self.break_next})
        self.break_next = False
        self.seen = {normalize_reading(w) for w in self.seen} | {normalize_reading(word)}
        self.last_word, self.required = word, tail(word)
        self.selected = self.hint = None
        self.revision += 1
        if self.required == "ん":
            self.finish("cpu" if owner == "you" else "you", "「ん」で終わったので負け！別の読み方にも注目しよう。")
            return
        self.turn = "you" if self.mode == "solo" else "cpu" if owner == "you" else "you"
        self.message = f"{'リン' if owner == 'you' else 'ルナ'}：{word} → 次は「{self.required}」"
        self.refilled = None
        if self.stock:
            self.cards[index] = self.stock.pop(0)
            del self.used[index]
            # Shared rescue rule: do not end a match with a connector stranded
            # in stock. Exchange only the newly dealt card, not existing cards.
            if not self.moves():
                for j, card in enumerate(self.stock):
                    if chain_moves((card,), self.required, self.seen):
                        self.cards[index], self.stock[j] = card, self.cards[index]
                        break
            self.refilled = index
            self.message += " · 同じ場所に新しい絵！"
        if not self.stock and len(self.used) == len(self.cards):
            self.finish("you" if self.mode == "solo" else "draw", "すべての絵をつないだ！" if self.mode == "solo" else "すべての絵をつないだ！仲良く引き分け。")
        elif not self.moves():
            if self.mode == "solo":
                self.check_solo_blocked()
            else:
                self.finish(owner, f"{'ルナ' if self.turn == 'cpu' else 'リン'}がつなげる絵がなくなった！")
        else:
            self.deadline = self.clock() + (2.2 if self.turn == "cpu" else self.limit)
            if self.turn == "cpu":
                self.prepare_cpu()

        self.chain.sync(self.clock(), (self.turn,) if self.phase == 'playing' else ())

    def check_solo_blocked(self):
        if self.relinks and any(tail(w) != "ん" and normalize_reading(w) not in self.seen
                                for i, c in enumerate(self.cards) if i not in self.used for w in c[2]):
            self.phase = "blocked"
            self.message = "つながる絵がないよ。「つなぎ直す」で別の文字から続けよう。"
        else:
            self.finish("draw", "ここまでつながった！次は別の読み方にも挑戦しよう。")

    def command(self, action, value=None):
        self.update()  # Expired timers cannot be bypassed by late commands.
        if action == "setup" and self.phase in ("paused", "finished"):
            self.phase = "intro"
            self.selected = None
        elif action == "mode" and self.phase == "intro" and isinstance(value, str) and value in ("battle", "solo"):
            self.mode = value
        elif action == "total" and self.phase == "intro" and type(value) is int and value in (12, 24, 36, 48):
            self.total = value
        elif action == "difficulty" and self.phase == "intro" and isinstance(value, str) and value in ("easy", "normal", "hard"):
            self.difficulty = value
            self.limit = {"easy": 30, "normal": 20, "hard": 12}[value]
        elif action == "start" and self.phase in ("intro", "finished"):
            self.start()
        elif action == "pause" and self.phase in ("playing", "blocked"):
            self.saved_remaining = self.remaining()
            self.resume_phase = self.phase
            self.phase = "paused"
            self.chain.sync(self.clock(), ())
            self.selected = None
        elif action == "resume" and self.phase == "paused":
            self.deadline = self.clock() + self.saved_remaining
            self.phase = self.resume_phase
            self.chain.sync(self.clock(), (self.turn,) if self.phase == 'playing' else ())
        elif action == "restart" and self.phase == "paused":
            self.start()
        elif action == "relink" and self.phase == "blocked" and self.mode == "solo" and self.relinks:
            choices = [(i, w) for i, c in enumerate(self.cards) if i not in self.used
                       for w in c[2] if tail(w) != "ん" and normalize_reading(w) not in self.seen]
            if choices:
                self.chain.miss('you')
                self.chain.sync(self.clock(), ('you',))
                self.relinks -= 1
                self.miss_card = None
                self.miss_until = 0
                self.required = head(choices[0][1])
                self.last_word = "つなぎ直し"
                self.break_next = True
                self.hint = choices[0][0]
                self.phase = "playing"
                self.message = f"「{self.required}」からもう一度つなごう！"
        elif action == "end" and self.phase == "paused" and self.mode == "solo":
            self.finish("draw", "ここまでの結果。自分のペースでまた遊ぼう！")
        elif self.phase == "playing" and self.turn == "you":
            if action == "card" and type(value) is int and 0 <= value < len(self.cards) and value not in self.used:
                move = next((m for m in self.moves() if m[0] == value), None)
                if move is not None:
                    self.take(*move)
                else:
                    self.chain.miss('you')
                    self.mistakes += 1
                    self.miss_card = value
                    self.miss_until = self.clock() + MISS_OUTLINE_SECONDS
                    if self.mode != "solo":
                        self.deadline -= 3
                    self.message = f"この絵は「{self.required}」につながらないよ（使用済み・ん終わりも不可）。" + (" 選び直そう。" if self.mode == "solo" else " −3秒")
                    self.revision += 1
                    self.update()
            elif action == "hint" and self.hints and self.moves():
                self.hints -= 1
                started = self.clock()
                self.chain.sync(started, ())
                move, plan = self.chain_advice()
                self.chain.sync(self.clock(), (self.turn,))
                # Thinking for a hint must not consume the player's turn time.
                if self.mode == "battle":
                    self.deadline += max(0, self.clock() - started)
                self.hint = move[0]
                self.message = ("完走につながるルートを発見！光る絵をつなごう。" if plan['perfect']
                                else "長くつながる候補を探したよ。光る絵をつなごう。")

    def active_miss_card(self):
        """Wrong-card outline while playing/blocked and within the durable TTL."""
        if self.miss_card is None or self.clock() >= self.miss_until:
            return None
        if self.phase not in ("playing", "blocked"):
            return None
        return self.miss_card

    def snapshot(self):
        visible = self.phase in ("playing", "blocked", "finished")
        return {"phase": self.phase, "turn": self.turn, "required": self.required,
                "chain": self.chain.snapshot(self.clock(), (self.turn,) if self.phase == "playing" else ()),
                "cpu_target": self.cpu_move[0] if self.cpu_move is not None and self.phase == "playing" and self.turn == "cpu" and self.mode == "battle" else None,
                "cpu_progress": max(0, min(1, 1-self.remaining()/2.2)) if self.phase == "playing" and self.turn == "cpu" and self.mode == "battle" else 0,
                "last_word": self.last_word, "remaining": round(self.remaining(), 1) if self.phase in ("playing", "paused") else 0,
                "limit": self.limit, "difficulty": self.difficulty, "message": self.message, "winner": self.winner,
                "mistakes": self.mistakes, "miss_card": self.active_miss_card(),
                "hints": self.hints, "hint": self.hint,
                "selected": self.selected, "revision": self.revision,
                "mode": self.mode, "total": self.total, "stock": len(self.stock), "completed": len(self.history),
                "relinks": self.relinks, "refilled": self.refilled, "seen": sorted(self.seen) if visible else [],
                "cards": [{"id": c[0], "icon": c[1], "words": c[2], "owner": self.used.get(i)} for i, c in enumerate(self.cards)] if visible else [],
                "catalog": [{"id": c[0], "icon": c[1], "words": c[2]} for c in CARDS] if self.phase in ("intro", "finished") else [],
                "discoveries": [{"id": i, "word": w, "owner": "you"} for i, w in sorted(self.discoveries)],
                "history": self.history if visible else []}
