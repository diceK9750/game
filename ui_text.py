"""Compact Japanese UI using M+ bitmap glyphs; no external font download."""
from ui_glyphs import GLYPHS

LABELS = {
    "HOW TO PLAY - LANTERN LEAGUE": "あそびかた / ランタン・リーグ",
    "FIND THE LARGE TARGET BEFORE THE FOX.": "下のお題と同じ数字を、CPUより先に見つけよう。",
    "FIRST CORRECT ANSWER WINS 1 POINT.": "先に見つけると1点。青があなた、桃がCPU。",
    "REACH THE GOLD LINE: 6 / 12 / 18 / 24 POINTS.": "金色の目標ラインで勝利! 全問ノーミスで特別賞。",
    "MISS? A BOMB APPEARS. YOU CAN STILL TAP THAT CELL.": "ミスしてもマスは押せる。CPU加速は1問に1回だけ。",
    "BLUE = YOU    PINK = CPU    EMPTY CELLS ARE IGNORED.": "練習はヒントあり。ヒント使用時は記録対象外。",
    "CLICK / TAP, OR ARROW KEYS + ENTER.  ESC = PAUSE.": "タップ / クリック / 矢印+Enter。Escで一時停止。",
    "BACK": "戻る", "HELP": "遊び方", "TITLE": "戻る",
    "RETRY": "再挑戦", "RESUME": "続ける", "YES": "はい", "NO": "いいえ",
    "CPU DUEL": "CPUと対戦", "SOLO PRACTICE": "ひとりで練習",
    "CHOOSE NUMBER RANGE": "数字の範囲を選ぼう / 盤面はいつも5×8",
    "NUMBER RUSH - LANTERN LEAGUE": "数字さがし / ランタン・リーグ",
    "START ORDER": "1から順番に開始", "START RANDOM": "ランダムで開始",
    "FIRST TO FIND = 1 POINT. REACH 60% TO WIN.": "先に見つけて1点 / 全体の6割で勝利",
    "NO CPU. FIND EVERY NUMBER AT YOUR OWN PACE.": "時間制限なし / ヒントを使って練習できるよ",
    "GET READY": "準備はいい?", "NUMBERS APPEAR AT GO": "合図で数字が見えるよ",
    "TITLE CAN CANCEL": "「戻る」でキャンセル",
    "RESUMING - BOARD HIDDEN": "もうすぐ再開 / 盤面はかくれているよ",
    "PAUSED - TAKE YOUR TIME": "ひと休みしよう",
    "CPU AND TIMER ARE STOPPED": "CPUもタイマーも止まっています",
    "RESUME WHEN YOU ARE READY": "準備ができたら「続ける」",
    "RESTART THIS RUN?": "新しい配置でやり直しますか?",
    "RETURN TO TITLE?": "選択画面に戻りますか?",
    "CONFIRM": "確認", "TIMER PAUSED / BOARD HIDDEN": "現在の対戦は終了します",
    "PLAY AGAIN": "もう一度遊ぶ", "MODE SELECT": "モード選択",
    "SCAN COMPLETE": "ぜんぶ見つけた!",
    "SPECIAL BONUS": "スペシャルボーナス",
    "MISS!  CPU CHEERS - TARGET STAYS": "ちがうよ! お題をもう一度見てね",
    "GO!  SCAN THE BOARD": "スタート! あわてず探そう",
    "SHUFFLED TARGET  /  FOLLOW THE SIGNAL": "毎回、下のお題を確認しよう",
}

def translate(label):
    return LABELS.get(label, label)

def text_width(label):
    return sum(10 if ord(c) > 127 else 4 for c in translate(label))

def text(g, x, y, label, color):
    label = translate(label)
    for c in label:
        if ord(c) < 128:
            g.text(x, y + 2, c, color)
            x += 4
            continue
        rows = GLYPHS.get(c)
        if rows is None:
            g.rectb(x, y, 9, 9, color)
        else:
            for row, bits in enumerate(rows):
                for col in range(10):
                    if bits & (1 << (9 - col)):
                        g.pset(x + col, y + row, color)
        x += 10
