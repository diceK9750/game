"""Illustrated word-chain duel. Pure Python rules with an injectable clock/RNG."""
import random
import time
from timed_chain import TimedChain

# Emoji are platform pictograms, not artwork copied from a commercial game.
# Finite picture names, categories and visible features; one reading per head.
CARDS = (
    ("apple", "🍎", ("りんご", "くだもの", "ふるーつ", "たべもの")),
    ("gorilla", "🦍", ("ごりら", "さる", "どうぶつ", "るいじんえん")),
    ("trumpet", "🎺", ("らっぱ", "がっき", "とらんぺっと", "きんかんがっき")),
    ("panda", "🐼", ("ぱんだ", "くま", "どうぶつ", "じゃいあんとぱんだ")),
    ("daruma", "🔴", ("だるま", "おきもの", "えんぎもの", "にんぎょう")),
    ("camel", "🐪", ("らくだ", "どうぶつ", "ひとこぶらくだ")),
    ("radish", "🥕", ("にんじん", "やさい", "きゃろっと", "こんさい", "たべもの")),
    ("dog", "🐕", ("いぬ", "こいぬ", "どうぶつ", "ぺっと")),
    ("teddy", "🧸", ("ぬいぐるみ", "くま", "おもちゃ", "てでぃべあ", "にんぎょう")),
    ("orange", "🍊", ("みかん", "くだもの", "ふるーつ", "たべもの")),
    ("turtle", "🐢", ("かめ", "りくがめ", "どうぶつ", "はちゅうるい")),
    ("glasses", "👓", ("めがね", "がんきょう", "れんず", "ふれーむ")),
    ("cat", "🐈", ("ねこ", "こねこ", "どうぶつ", "ぺっと")),
    ("tree", "🌲", ("まつ", "き", "しょくぶつ", "じゅもく")),
    ("moon", "🌙", ("つき", "よぞら", "みかづき", "てんたい")),
    ("fox", "🦊", ("きつね", "どうぶつ", "けもの", "ふぉっくす")),
    ("mouse", "🐁", ("ねずみ", "どうぶつ", "まうす", "けもの")),
    ("ear", "👂", ("みみ", "からだ", "じかく", "ちょうかくきかん")),
    ("bee", "🐝", ("みつばち", "はち", "むし", "こんちゅう")),
    ("butterfly", "🦋", ("ちょう", "むし", "こんちゅう", "ばたふらい")),
    ("rabbit", "🐇", ("うさぎ", "どうぶつ", "らびっと", "けもの")),
    ("guitar", "🎸", ("ぎたー", "がっき", "えれきぎたー", "げんがっき")),
    ("octopus", "🐙", ("たこ", "うみのいきもの", "なんたいどうぶつ", "おくとぱす")),
    ("bird", "🐦", ("ことり", "とり", "どうぶつ", "ばーど")),
    ("squirrel", "🐿️", ("りす", "どうぶつ", "けもの")),
    ("melon", "🍉", ("すいか", "くだもの", "ふるーつ", "たべもの")),
    ("umbrella", "☂️", ("かさ", "あまがさ", "ようがさ", "れいんぐっず")),
    ("fish", "🐟", ("さかな", "ぎょるい", "うみのいきもの", "ふぃっしゅ")),
    ("eggplant", "🍆", ("なす", "やさい", "たべもの", "しょくざい")),
    ("bell", "🔔", ("すず", "かね", "べる", "がっき")),
    ("trousers", "👖", ("ずぼん", "ふく", "じーんず", "でにむ", "ぼとむす")),
    ("ship", "🚢", ("ふね", "のりもの", "きせん", "しっぷ")),
    ("mushroom", "🍄", ("きのこ", "しょくざい", "まっしゅるーむ")),
    ("ice", "🧊", ("こおり", "あいすきゅーぶ", "ろっくあいす", "ひょうかい")),
    ("car", "🚗", ("くるま", "じどうしゃ", "のりもの", "まいかー")),
    ("mountain", "⛰️", ("やま", "さん", "まうんてん", "みね")),
    ("peach", "🍑", ("もも", "くだもの", "ぴーち", "ふるーつ", "たべもの")),
    ("bread", "🍞", ("ぱん", "しょくぱん", "とーすと", "ぶれっど", "たべもの")),
    ("lion", "🦁", ("らいおん", "どうぶつ", "しし", "けもの")),
    ("top", "🌀", ("こま", "おもちゃ", "かいてんたい")),
    ("pillow", "🛏️", ("まくら", "しんぐ", "ねどこ")),
    ("otter", "🦦", ("らっこ", "どうぶつ", "うみのいきもの")),
    ("koala", "🐨", ("こあら", "どうぶつ", "ゆうたいるい")),
    ("ramune", "🍾", ("らむね", "のみもの", "たんさんいんりょう")),
    ("tie", "👔", ("ねくたい", "ふく", "えりもと")),
    ("chair", "🪑", ("いす", "かぐ", "ざせき")),
    ("zucchini", "🥒", ("ずっきーに", "やさい", "たべもの")),
    ("chicken", "🐔", ("にわとり", "とり", "どうぶつ")),
    ("backpack", "🎒", ("りゅっく", "かばん", "にもつ")),
    ("scarf", "🧣", ("まふらー", "えりまき", "ぼうかんぐ")),
    ("radio", "📻", ("らじお", "じゅしんき", "おんきょうきき")),
    ("riceball", "🍙", ("おにぎり", "ごはん", "たべもの")),
    ("dragon", "🐉", ("りゅう", "どらごん", "でんせつのいきもの")),
    ("cow", "🐄", ("うし", "どうぶつ", "かちく")),
    ("salt", "🧂", ("しお", "ちょうみりょう", "そると")),
    ("plate", "🍽️", ("おさら", "しょっき", "ぷれーと")),
    ("lavender", "🪻", ("らべんだー", "はな", "しょくぶつ")),
    ("diamond", "💎", ("だいや", "ほうせき", "きせき")),
    ("beans", "🫘", ("まめ", "しょくざい", "たね")),
    ("medaka", "🐟", ("めだか", "さかな", "ぎょるい")),
    ("sand", "🏖️", ("すな", "はまべ", "びーち")),
    ("pot", "🍲", ("なべ", "りょうり", "しょっき")),
    ("bagel", "🥯", ("べーぐる", "ぱん", "たべもの")),
    ("loupe", "🔍", ("るーぺ", "むしめがね", "かくだいきょう")),
    ("paint", "🎨", ("ぺんき", "とりょう", "いろ")),
    ("knife", "🔪", ("ないふ", "ほうちょう", "かとらりー")),
)
# Each distinct picture's primary reading connects to the next, including wrap.
# A window of at most 48 cards leaves the initial prompt outside the board.
PERFECT_RING = (
    'apple', 'gorilla', 'trumpet', 'panda', 'daruma', 'tree', 'moon', 'fox',
    'mouse', 'bee', 'butterfly', 'rabbit', 'guitar', 'octopus', 'top', 'pillow',
    'otter', 'koala', 'ramune', 'tie', 'chair', 'melon', 'turtle', 'glasses',
    'cat', 'ice', 'squirrel', 'bell', 'zucchini', 'chicken', 'backpack', 'car',
    'scarf', 'radio', 'riceball', 'dragon', 'cow', 'salt', 'plate', 'lavender',
    'diamond', 'mountain', 'beans', 'medaka', 'umbrella', 'fish', 'eggplant',
    'sand', 'pot', 'bagel', 'loupe', 'paint', 'mushroom', 'bird',
)
SMALL = str.maketrans("ゃゅょぁぃぅぇぉっゎ", "やゆよあいうえおつわ")


def tail(word):
    """House rule: long marks use preceding kana; small kana become full-size."""
    return word.rstrip("ー")[-1].translate(SMALL)


def chain_moves(cards, required, seen):
    """Pure legal-move enumeration; None is a consumed board slot."""
    return [(i, word) for i, card in enumerate(cards) if card is not None
            for word in card[2] if word[0] == required and tail(word) != "ん" and word not in seen]


def starting_route(required, total, seen, rng, node_budget=256):
    """Randomized catalog-wide chain; a bounded miss uses the certified ring."""
    by_head = {}
    for card in CARDS:
        for word in card[2]:
            if tail(word) != "ん":
                by_head.setdefault(word[0], []).append((card[0], word))
    nodes = 0

    def search(head, route, ids, words):
        nonlocal nodes
        if len(route) == total:
            return route
        if nodes >= node_budget:
            return None
        nodes += 1
        choices = list(by_head.get(head, ()))
        rng.shuffle(choices)
        for identity, word in choices:
            if identity in ids or word in words:
                continue
            found = search(tail(word), route + [(identity, word)], ids | {identity}, words | {word})
            if found is not None:
                return found
            if nodes >= node_budget:
                break
        return None

    return search(required, [], set(), set(seen))


def chain_step(cards, stock, seen, move):
    """Simulate the real refill/rescue rules without touching the live round."""
    i, word = move
    cards, stock = list(cards), list(stock)
    seen = seen | {word}
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
    initial = (tuple(cards), tuple(stock), required, frozenset(seen))
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
        self.hints = 3
        self.hint = None
        self.winner = None
        self.turn = "you"
        self.deadline = 0
        self.saved_remaining = 0
        self.revision = 0
        self.cpu_move = None
        self._chain_advice = {}
        self.chain = TimedChain(self.clock())

    def start(self):
        self.chain = TimedChain(self.clock())
        self._chain_advice.clear()
        by_id = {card[0]: card for card in CARDS}
        offset = self.rng.randrange(len(PERFECT_RING))
        seed = by_id[PERFECT_RING[offset]][2][0]
        route_ids = [PERFECT_RING[(offset + step) % len(PERFECT_RING)] for step in range(1, self.total + 1)]
        route_words = starting_route(tail(seed), self.total, {seed}, self.rng)
        if route_words is None:
            route_words = [(key, by_id[key][2][0]) for key in route_ids]
        chosen = [by_id[key] for key, _ in route_words]
        self.cards, self.stock = chosen[:24], chosen[24:]
        self.rng.shuffle(self.cards)
        self.used = {}
        self.history = []
        self.last_word, self.required = seed, tail(seed)
        self.seen = {seed}
        self.turn, self.phase = "you", "playing"
        self.winner = None
        self.cpu_move = None
        self.selected = self.hint = None
        self.mistakes, self.hints = 0, 3
        self.relinks = 2
        self.refilled = None
        self.break_next = False
        self.message = f"「{self.required}」から始まる絵をさがそう。"
        self.deadline = self.clock() + self.limit
        # Replay the witness using the same transition rules as planning.
        state = (tuple(self.cards), tuple(self.stock), self.required, frozenset(self.seen))
        witnesses = []
        for identity, word in route_words:
            index = next(i for i, c in enumerate(state[0]) if c is not None and c[0] == identity)
            move = (index, word)
            if move not in chain_moves(state[0], state[2], state[3]):
                raise ValueError('Invalid perfect starting route')
            witnesses.append((state, move))
            state = chain_step(state[0], state[1], state[3], move)
        if any(state[0]) or state[1]:
            raise ValueError('Perfect starting route did not consume the deck')
        route = tuple(move for _, move in witnesses)
        for i, (state, move) in enumerate(witnesses):
            self._chain_advice[state] = (move, {'length': len(route)-i, 'perfect': True,
                                               'exact': True, 'nodes': 0, 'route': route[i:]})
        self.revision += 1

    def moves(self):
        return [(i, word) for i, card in enumerate(self.cards) if i not in self.used
                for word in card[2] if word[0] == self.required and tail(word) != "ん" and word not in self.seen]

    def finish(self, winner, reason):
        self.phase, self.winner, self.message = "finished", winner, reason
        self.selected = self.hint = None
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

    def chain_advice(self):
        """Share advice with hints; reuse only an exact matching game state.

        Retain proven perfect suffixes so bounded replanning cannot lose them.
        A player's different choice invalidates the old plan automatically.
        """
        board = tuple(None if i in self.used else c for i, c in enumerate(self.cards))
        state = (board, tuple(self.stock), self.required, frozenset(self.seen))
        if state in self._chain_advice:
            return self._chain_advice[state]
        self._chain_advice.clear()
        move, plan = longest_chain_move(board, self.stock, self.required, self.seen)
        self._chain_advice[state] = (move, plan)
        if plan['perfect']:
            for offset, step in enumerate(plan['route']):
                suffix = plan['route'][offset:]
                self._chain_advice[state] = (step, {"length": len(suffix), "perfect": True,
                                                  "exact": True, "nodes": 0, "route": suffix})
                state = chain_step(state[0], state[1], state[3], step)
        return move, plan

    def take(self, index, word):
        owner = self.turn
        self.chain.hit(owner, self.clock())
        self.cpu_move = None
        if owner == "you":
            self.discoveries.add((self.cards[index][0], word))
        self.used[index] = owner
        self.history.append({"word": word, "owner": owner, "icon": self.cards[index][1], "id": self.cards[index][0], "readings": self.cards[index][2], "relinked": self.break_next})
        self.break_next = False
        self.seen.add(word)
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
                    if any(w[0] == self.required and tail(w) != "ん" and w not in self.seen for w in card[2]):
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
        if self.relinks and any(tail(w) != "ん" and w not in self.seen
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
                       for w in c[2] if tail(w) != "ん" and w not in self.seen]
            if choices:
                self.chain.miss('you')
                self.chain.sync(self.clock(), ('you',))
                self.relinks -= 1
                self.required = choices[0][1][0]
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

    def snapshot(self):
        visible = self.phase in ("playing", "blocked", "finished")
        return {"phase": self.phase, "turn": self.turn, "required": self.required,
                "chain": self.chain.snapshot(self.clock(), (self.turn,) if self.phase == "playing" else ()),
                "cpu_target": self.cpu_move[0] if self.cpu_move is not None and self.phase == "playing" and self.turn == "cpu" and self.mode == "battle" else None,
                "cpu_progress": max(0, min(1, 1-self.remaining()/2.2)) if self.phase == "playing" and self.turn == "cpu" and self.mode == "battle" else 0,
                "last_word": self.last_word, "remaining": round(self.remaining(), 1) if self.phase in ("playing", "paused") else 0,
                "limit": self.limit, "difficulty": self.difficulty, "message": self.message, "winner": self.winner,
                "mistakes": self.mistakes, "hints": self.hints, "hint": self.hint,
                "selected": self.selected, "revision": self.revision,
                "mode": self.mode, "total": self.total, "stock": len(self.stock), "completed": len(self.history),
                "relinks": self.relinks, "refilled": self.refilled, "seen": sorted(self.seen) if visible else [],
                "cards": [{"id": c[0], "icon": c[1], "words": c[2], "owner": self.used.get(i)} for i, c in enumerate(self.cards)] if visible else [],
                "catalog": [{"id": c[0], "icon": c[1], "words": c[2]} for c in CARDS] if self.phase in ("intro", "finished") else [],
                "discoveries": [{"id": i, "word": w, "owner": "you"} for i, w in sorted(self.discoveries)],
                "history": self.history if visible else []}
