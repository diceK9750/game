# title: Number Rush
# author: diceK9750 / Codex
# desc: Find 1 to 10, 20, 30, or 40 in order or in a shuffled sequence.
# site: https://dicek9750.github.io/game/
# version: 6.3

"""横持ちブラウザ向けの数字タップゲーム NUMBER RUSH。"""

from __future__ import annotations

import pyxel

from game_logic import (
    BOARD_CELL_COUNT,
    NumberTapRound,
    correct_points,
    music_stage_for_progress,
)


WIDTH = 640
HEIGHT = 360
FPS = 60
GRID_COLUMNS = 8
GRID_ROWS = 5
GRID_X = 96
GRID_Y = 58
CELL_WIDTH = 54
CELL_HEIGHT = 32
CELL_GAP = 3
GRID_CELL_COUNT = GRID_COLUMNS * GRID_ROWS
NUMBER_LIMITS = (10, 20, 30, 40)
if GRID_CELL_COUNT != BOARD_CELL_COUNT:
    raise ValueError("The UI grid and game board must contain the same cells")

RANGE_BUTTONS = {
    10: (124, 126, 86, 32),
    20: (226, 126, 86, 32),
    30: (328, 126, 86, 32),
    40: (430, 126, 86, 32),
}
ORDER_BUTTON = (124, 204, 188, 44)
RANDOM_BUTTON = (328, 204, 188, 44)
REPLAY_BUTTON = (124, 226, 188, 44)
MODE_BUTTON = (328, 226, 188, 44)
RETRY_BUTTON = (368, 9, 58, 32)
TITLE_BUTTON = (430, 9, 58, 32)
BGM_BUTTON = (492, 9, 66, 32)
SFX_BUTTON = (562, 9, 66, 32)
YES_BUTTON = (200, 220, 110, 42)
NO_BUTTON = (330, 220, 110, 42)

COUNTDOWN_FRAMES = 180
BGM_NOTES_PER_PHRASE = 32
BGM_SOUND_SPEED = 9
PYXEL_AUDIO_TICKS_PER_SECOND = 120
BGM_PHRASE_COUNT = 32
BGM_PHRASE_FRAMES = (
    BGM_NOTES_PER_PHRASE * BGM_SOUND_SPEED * FPS // PYXEL_AUDIO_TICKS_PER_SECOND
)
BGM_LOOP_FRAMES = BGM_PHRASE_FRAMES * BGM_PHRASE_COUNT

# Pyxel標準16色パレット。
BACKGROUND = 0
DEEP_BLUE = 1
PANEL = 5
PRESSED = 6
CARD = 7
ERROR = 8
YELLOW = 10
GREEN = 11
BLUE = 12
MUTED = 13
PINK = 14
PEACH = 15

DIGITS = {
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
}


def centered_text(y: int, label: str, color: int) -> None:
    """Pyxel標準フォントの文字列を画面中央に描く。"""
    pyxel.text((WIDTH - len(label) * 4) // 2, y, label, color)


def point_in_rect(x: int, y: int, rect: tuple[int, int, int, int]) -> bool:
    """点が(x, y, 幅, 高さ)形式の長方形内にあるかを返す。"""
    left, top, width, height = rect
    return left <= x < left + width and top <= y < top + height


def draw_number(x: int, y: int, number: int, color: int, scale: int = 3) -> None:
    """5×7のビットマップ数字を1桁または2桁で描く。"""
    label = str(number)
    digit_width = 5 * scale
    digit_gap = scale
    total_width = len(label) * digit_width + (len(label) - 1) * digit_gap

    for digit_index, digit in enumerate(label):
        digit_x = x - total_width // 2 + digit_index * (digit_width + digit_gap)
        for row, bits in enumerate(DIGITS[digit]):
            for column, bit in enumerate(bits):
                if bit == "1":
                    pyxel.rect(
                        digit_x + column * scale,
                        y + row * scale,
                        scale,
                        scale,
                        color,
                    )


class NumberRush:
    """描画と入力を受け持つPyxelアプリケーション。"""

    def __init__(self) -> None:
        pyxel.init(WIDTH, HEIGHT, title="NUMBER RUSH", fps=FPS)
        pyxel.mouse(True)
        self.configure_sounds()
        self.selected_max_number = 40
        self.round = NumberTapRound(max_number=self.selected_max_number)
        self.screen = "ready"
        self.selected_mode = "ordered"
        self.confirm_action: str | None = None
        self.countdown_end_frame = 0
        self.go_until_frame = 0
        self.wrong_cell: int | None = None
        self.wrong_until_frame = 0
        self.correct_cell: int | None = None
        self.correct_until_frame = 0
        self.milestone_value = 0
        self.milestone_until_frame = 0
        self.score = 0
        self.streak = 0
        self.max_streak = 0
        self.bgm_on = True
        self.bgm_stage = 0
        self.pending_bgm_stage: int | None = None
        self.bgm_paused = False
        self.bgm_has_started = False
        self.bgm_origin_frame = 0
        self.bgm_next_phrase_frame = 0
        self.bgm_paused_position_frames = 0
        self.sfx_on = True
        self.sfx_priority_until_frame = 0
        self.is_new_best = False
        self.best_times: dict[tuple[int, str], float] = {}
        pyxel.run(self.update, self.draw)

    @staticmethod
    def configure_sounds() -> None:
        """外部素材を使わず、独自の効果音と高速チップチューンを作る。"""
        pyxel.sounds[0].set("d3f3a3", "p", "677", "nnf", 4)
        pyxel.sounds[1].set("c2c1", "n", "76", "ff", 5)
        pyxel.sounds[2].set("d3a3d4f4", "p", "6677", "nnnv", 5)
        pyxel.sounds[3].set("d3f3a3d4f4a4", "ps", "667777", "nnnnvf", 5)
        pyxel.sounds[4].set("a2d3f3a3", "p", "4567", "nssn", 5)

        def set_phrase(
            index: int,
            notes: str,
            tone: str,
            volume: str,
            effect: str = "n",
        ) -> None:
            if len(notes.split()) != BGM_NOTES_PER_PHRASE:
                raise ValueError(
                    f"BGM phrase {index} must contain "
                    f"{BGM_NOTES_PER_PHRASE} notes"
                )
            pyxel.sounds[index].set(notes, tone, volume, effect, BGM_SOUND_SPEED)

        # Dドリアンを基調にした完全オリジナルのA-A'-B-C構成。
        lead_phrases = (
            "d3 f3 a3 d4 c4 a3 g3 f3 e3 f3 g3 a3 c4 a3 g3 e3 "
            "d3 r a3 d4 f4 e4 d4 c4 a3 g3 f3 e3 f3 a3 g3 r",
            "d3 a3 f3 a3 d4 a3 f3 e3 g3 c4 a3 c4 e4 c4 a3 g3 "
            "f3 a3 d4 c4 a3 g3 f3 e3 d3 f3 e3 c3 d3 a2 d3 r",
            "f3 a3 c4 d4 f4 d4 c4 a3 g3 a3 c4 e4 d4 c4 a3 g3 "
            "a3 c4 f4 e4 d4 c4 a3 f3 g3 a3 c4 a3 g3 e3 f3 r",
            "g3 a3 c4 e4 g4 e4 c4 a3 f3 a3 d4 f4 e4 d4 c4 a3 "
            "g3 c4 e4 d4 c4 a3 g3 e3 f3 g3 a3 c4 a3 g3 e3 r",
            "a3 d4 f4 a4 f4 d4 c4 a3 g3 c4 e4 g4 e4 c4 a3 g3 "
            "f3 a3 c4 f4 e4 c4 a3 f3 e3 g3 a3 c4 a3 g3 f3 r",
            "d4 c4 a3 f3 g3 a3 c4 d4 f4 e4 d4 c4 a3 g3 f3 e3 "
            "d3 f3 a3 c4 d4 f4 e4 d4 c4 a3 g3 f3 e3 f3 d3 r",
            "f3 g3 a3 c4 d4 c4 a3 g3 e3 g3 a3 c4 e4 d4 c4 a3 "
            "f3 a3 d4 f4 e4 d4 c4 a3 g3 f3 e3 f3 a3 c4 d4 r",
            "a3 c4 d4 f4 a4 f4 d4 c4 g3 a3 c4 e4 g4 e4 c4 a3 "
            "f3 a3 d4 c4 a3 g3 f3 e3 d3 f3 a3 c4 a3 g3 a3 r",
        )
        high_phrases = (
            "a3 d4 f4 a4 b4 a4 f4 e4 d4 f4 a4 b4 a4 f4 e4 d4 "
            "c4 d4 f4 a4 f4 e4 d4 c4 a3 c4 d4 f4 e4 d4 c4 r",
            "d4 f4 a4 a4 b4 a4 f4 e4 g4 a4 b4 g4 a4 b4 a4 g4 "
            "f4 a4 a4 b4 a4 g4 f4 e4 d4 f4 e4 c4 d4 a3 d4 r",
            "f4 a4 b4 a4 g4 b4 a4 g4 a4 b4 g4 b4 g4 b4 a4 g4 "
            "f4 a4 a4 a4 g4 a4 b4 a4 g4 f4 e4 f4 a4 b4 a4 r",
            "a4 f4 d4 c4 e4 g4 b4 g4 a4 b4 a4 g4 f4 a4 a4 a4 "
            "g4 a4 b4 a4 g4 f4 e4 d4 c4 d4 f4 a4 g4 a4 a4 r",
        )
        bass_phrases = (
            "d1 a1 d2 a1 d1 a1 c2 a1 f1 c2 f2 c2 f1 c2 e2 c2 "
            "g1 d2 g2 d2 g1 d2 a1 e2 a1 e2 a2 e2 a1 e2 c2 a1",
            "f1 c2 f2 c2 f1 c2 a1 e2 g1 d2 g2 d2 g1 d2 e2 b1 "
            "d1 a1 d2 a1 d1 a1 f1 c2 g1 d2 a1 e2 a1 e2 c2 a1",
            "a1 e2 a2 e2 a1 e2 g1 d2 f1 c2 f2 c2 f1 c2 e2 b1 "
            "g1 d2 g2 d2 a1 e2 a2 e2 d1 a1 d2 a1 c2 a1 d2 a1",
            "g1 d2 g2 d2 g1 d2 a1 e2 f1 c2 f2 c2 e1 b1 e2 b1 "
            "d1 a1 d2 a1 f1 c2 a1 e2 g1 d2 a1 e2 c2 a1 d2 a1",
        )
        # 長尺フォーム後半用の独自変奏。短い動機を入れ替えながら、
        # 前半の探索感から中盤の応酬、終盤の上昇へ段階的に展開する。
        lead_variations = (
            "r a3 c4 d4 f4 d4 c4 a3 r g3 a3 c4 e4 c4 a3 g3 "
            "r f3 a3 d4 c4 a3 g3 f3 e3 f3 g3 a3 c4 a3 g3 r",
            "r d4 a3 f3 r e3 g3 a3 c4 r a3 g3 f3 e3 d3 r "
            "r f3 a3 c4 d4 r c4 a3 g3 f3 e3 f3 a3 g3 d3 r",
            "r f3 g3 a3 c4 d4 f4 e4 r d4 c4 a3 g3 a3 c4 d4 "
            "r a3 c4 e4 g4 e4 c4 a3 g3 f3 e3 f3 a3 c4 d4 r",
            "d4 r d4 f4 a4 r f4 e4 c4 r c4 e4 g4 r e4 d4 "
            "a3 r c4 d4 f4 r d4 c4 g3 a3 c4 a3 g3 f3 e3 r",
            "d3 e3 f3 a3 c4 a3 f3 e3 g3 a3 c4 e4 g4 e4 c4 a3 "
            "f3 g3 a3 d4 f4 d4 c4 a3 e3 f3 g3 a3 c4 a3 f3 r",
            "g3 a3 b3 d4 e4 d4 b3 a3 f3 a3 c4 e4 f4 e4 c4 a3 "
            "g3 b3 d4 f4 e4 d4 b3 a3 f3 g3 a3 c4 b3 a3 g3 r",
            "a3 c4 d4 f4 a4 f4 d4 c4 b3 d4 e4 g4 b4 g4 e4 d4 "
            "c4 e4 f4 a4 b4 a4 f4 e4 d4 c4 b3 a3 g3 a3 c4 r",
            "f4 e4 d4 c4 a3 g3 f3 e3 d3 f3 a3 d4 c4 a3 g3 e3 "
            "f3 a3 c4 e4 d4 c4 a3 g3 f3 e3 d3 c3 a2 e3 a3 r",
        )
        bass_variations = (
            "d1 a1 d2 a1 f1 c2 f2 c2 g1 d2 g2 d2 a1 e2 a2 e2 "
            "d1 a1 f2 a1 c2 g1 e2 g1 f1 c2 a2 c2 g1 d2 a2 e2",
            "c1 g1 c2 g1 e1 b1 e2 b1 f1 c2 f2 c2 g1 d2 g2 d2 "
            "a1 e2 a2 e2 f1 c2 a2 c2 e1 b1 g2 b1 a1 e2 c2 a1",
            "f1 c2 f2 c2 a1 e2 a2 e2 g1 d2 g2 d2 e1 b1 e2 b1 "
            "d1 a1 d2 a1 f1 c2 f2 c2 g1 d2 a2 d2 c2 g1 d2 a1",
            "g1 d2 g2 d2 a1 e2 a2 e2 f1 c2 f2 c2 e1 b1 e2 b1 "
            "d1 a1 f2 a1 g1 d2 e2 b1 f1 c2 g2 c2 a1 e2 d2 a1",
        )
        high_variations = (
            "d4 f4 a4 b4 a4 f4 e4 d4 c4 e4 g4 b4 a4 g4 e4 c4 "
            "d4 f4 a4 g4 f4 e4 d4 c4 a3 c4 d4 f4 e4 d4 a3 r",
            "e4 g4 b4 a4 g4 e4 d4 c4 f4 a4 b4 a4 f4 e4 d4 c4 "
            "g4 b4 a4 g4 e4 d4 c4 a3 d4 e4 f4 a4 g4 f4 e4 r",
            "a3 d4 a4 d4 f4 d4 a4 d4 c4 e4 b4 e4 g4 e4 b4 e4 "
            "f4 a4 c4 a4 d4 a4 f4 a4 g4 b4 d4 b4 e4 d4 c4 r",
            "b3 d4 g4 b4 a4 g4 d4 b3 c4 e4 a4 c4 b4 a4 e4 c4 "
            "d4 f4 a4 d4 c4 a3 f3 a3 g3 b3 d4 g4 f4 e4 d4 r",
            "f4 f4 a4 b4 a4 f4 e4 d4 a4 a4 b4 a4 g4 e4 d4 c4 "
            "g4 g4 b4 a4 g4 e4 d4 c4 f4 a4 g4 f4 e4 d4 c4 r",
            "a4 f4 d4 f4 a4 b4 a4 g4 e4 c4 e4 g4 b4 a4 g4 e4 "
            "f4 d4 c4 d4 f4 a4 g4 f4 e4 g4 b4 a4 g4 f4 e4 r",
            "d4 a4 f4 a4 d4 a4 f4 a4 e4 b4 g4 b4 e4 b4 g4 b4 "
            "f4 a4 c4 a4 f4 a4 c4 a4 g4 b4 d4 b4 g4 a4 b4 r",
            "a4 g4 f4 e4 d4 f4 a4 b4 a4 g4 f4 e4 d4 c4 a3 c4 "
            "d4 f4 a4 g4 f4 e4 d4 c4 a3 g3 f3 e3 d3 a3 d4 r",
        )
        drum_variations = (
            "c2 r c1 c1 c2 r c1 c1 c2 c1 c1 c2 c1 r c2 c1 "
            "c2 r c1 c1 c2 c1 c2 c1 c2 c1 c1 c2 c2 c1 c2 c1",
            "c2 c1 c1 c2 c1 c2 c1 c1 c2 c1 c2 c1 c2 c1 c2 c1 "
            "c2 c1 c1 c2 c1 c2 c2 c1 c2 c2 c1 c2 c2 c1 c2 c2",
            "c2 c1 c2 c1 c2 c1 c2 c1 c2 c2 c1 c2 c2 c1 c2 c1 "
            "c2 c1 c2 c2 c1 c2 c2 c1 c2 c2 c2 c1 c2 c2 c2 c1",
            "c2 c1 c1 c2 c1 c2 c1 c1 c2 c1 c2 c1 c2 c2 c1 c2 "
            "c2 c2 c1 c2 c2 c2 c1 c2 c2 c2 c2 c2 c1 c2 c1 r",
        )

        for index, notes in enumerate(lead_phrases, start=8):
            set_phrase(index, notes, "ppps", "6776", "nnvn")
        for index, notes in enumerate(bass_phrases, start=16):
            set_phrase(index, notes, "t", "5556")
        set_phrase(20, "c1 r c1 c1 " * 8, "n", "5034", "f")
        set_phrase(21, "c2 c1 c1 c1 " * 8, "n", "6453", "f")
        set_phrase(22, "c2 c1 c1 c2 c1 c1 c2 c1 " * 4, "n", "65536443", "f")
        set_phrase(23, "c2 c2 c1 c2 c1 c2 c1 c1 " * 4, "n", "76646554", "f")
        for index, notes in enumerate(high_phrases, start=24):
            set_phrase(index, notes, "pssp", "6777", "nvnn")
        for index, notes in enumerate(lead_variations, start=28):
            set_phrase(index, notes, "ppss", "6776", "nvvn")
        for index, notes in enumerate(bass_variations, start=36):
            set_phrase(index, notes, "t", "5666", "nnvn")
        for index, notes in enumerate(high_variations, start=40):
            set_phrase(index, notes, "pssp", "6777", "nvnn")
        for index, notes in enumerate(drum_variations, start=48):
            set_phrase(index, notes, "n", "6765", "f")

    def update(self) -> None:
        clicked = pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)
        mouse = (pyxel.mouse_x, pyxel.mouse_y)

        if pyxel.btnp(pyxel.KEY_B) or (
            clicked and point_in_rect(*mouse, BGM_BUTTON)
        ):
            self.toggle_bgm()
            clicked = False

        if pyxel.btnp(pyxel.KEY_S) or (
            clicked and point_in_rect(*mouse, SFX_BUTTON)
        ):
            self.toggle_sfx()
            clicked = False

        if self.screen == "playing":
            self.update_bgm_transition()

        if self.screen == "ready":
            range_keys = (pyxel.KEY_1, pyxel.KEY_2, pyxel.KEY_3, pyxel.KEY_4)
            for key, max_number in zip(range_keys, NUMBER_LIMITS):
                if pyxel.btnp(key):
                    self.selected_max_number = max_number
            for max_number, button in RANGE_BUTTONS.items():
                if clicked and point_in_rect(*mouse, button):
                    self.selected_max_number = max_number
                    return

            if pyxel.btnp(pyxel.KEY_O) or (
                clicked and point_in_rect(*mouse, ORDER_BUTTON)
            ):
                self.begin_countdown("ordered")
            elif pyxel.btnp(pyxel.KEY_R) or (
                clicked and point_in_rect(*mouse, RANDOM_BUTTON)
            ):
                self.begin_countdown("random")
            return

        if self.screen == "countdown":
            if pyxel.btnp(pyxel.KEY_T) or (
                clicked and point_in_rect(*mouse, TITLE_BUTTON)
            ):
                self.screen = "ready"
            elif pyxel.frame_count >= self.countdown_end_frame:
                self.start_round(self.selected_mode)
            return

        if self.screen == "confirm":
            if pyxel.btnp(pyxel.KEY_Y) or (
                clicked and point_in_rect(*mouse, YES_BUTTON)
            ):
                self.accept_confirmation()
            elif pyxel.btnp(pyxel.KEY_N) or (
                clicked and point_in_rect(*mouse, NO_BUTTON)
            ):
                self.cancel_confirmation()
            return

        if self.screen == "finished":
            if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN) or (
                clicked and point_in_rect(*mouse, REPLAY_BUTTON)
            ):
                self.begin_countdown(self.selected_mode)
            elif pyxel.btnp(pyxel.KEY_M) or (
                clicked and point_in_rect(*mouse, MODE_BUTTON)
            ):
                self.screen = "ready"
            return

        if pyxel.btnp(pyxel.KEY_R) or (
            clicked and point_in_rect(*mouse, RETRY_BUTTON)
        ):
            self.open_confirmation("retry")
            return
        if pyxel.btnp(pyxel.KEY_T) or (
            clicked and point_in_rect(*mouse, TITLE_BUTTON)
        ):
            self.open_confirmation("title")
            return

        if clicked:
            cell_index = self.cell_at(*mouse)
            if cell_index is not None:
                self.handle_tap(cell_index)

        if pyxel.frame_count >= self.wrong_until_frame:
            self.wrong_cell = None
        if pyxel.frame_count >= self.correct_until_frame:
            self.correct_cell = None

    def begin_countdown(self, mode: str) -> None:
        """盤面を伏せたまま3秒カウントし、同時スタートを準備する。"""
        self.stop_bgm()
        self.selected_mode = mode
        self.screen = "countdown"
        self.countdown_end_frame = pyxel.frame_count + COUNTDOWN_FRAMES
        self.confirm_action = None
        self.wrong_cell = None
        self.correct_cell = None

    def start_round(self, mode: str) -> None:
        self.selected_mode = mode
        self.round = NumberTapRound(max_number=self.selected_max_number)
        self.round.start(mode)
        self.screen = "playing"
        self.score = 0
        self.streak = 0
        self.max_streak = 0
        self.is_new_best = False
        self.wrong_cell = None
        self.correct_cell = None
        self.milestone_value = 0
        self.go_until_frame = pyxel.frame_count + 30
        self.bgm_stage = 0
        self.pending_bgm_stage = None
        if self.bgm_on:
            self.start_bgm(0)
        self.play_sfx(4)

    def handle_tap(self, cell_index: int) -> None:
        number = self.round.board_cells[cell_index]
        result = self.round.tap(number)
        if result == "empty":
            return
        if result == "wrong":
            self.streak = 0
            self.wrong_cell = cell_index
            self.wrong_until_frame = pyxel.frame_count + 30
            self.play_sfx(1)
            return
        if result not in {"correct", "finished"}:
            return

        self.streak += 1
        self.max_streak = max(self.max_streak, self.streak)
        self.score += correct_points(self.streak)
        self.correct_cell = cell_index
        self.correct_until_frame = pyxel.frame_count + 18
        max_number = self.round.max_number
        milestone_counts = {
            (max_number + 3) // 4,
            (max_number + 1) // 2,
            (3 * max_number + 3) // 4,
        }
        milestone_counts.discard(max_number)
        is_milestone = self.round.completed_count in milestone_counts
        if is_milestone:
            self.milestone_value = self.round.completed_count
            self.milestone_until_frame = pyxel.frame_count + 60

        # 節目とクリアでは専用音だけを鳴らし、同一chでの即時上書きを避ける。
        if result == "finished":
            pass
        elif is_milestone:
            self.play_sfx(2, protect_frames=10)
        else:
            self.play_sfx(0)

        next_stage = music_stage_for_progress(
            self.round.completed_count,
            max_number=self.round.max_number,
        )
        if next_stage != self.bgm_stage:
            self.pending_bgm_stage = next_stage

        if result == "finished":
            elapsed = self.round.elapsed()
            result_key = (self.round.max_number, self.selected_mode)
            best = self.best_times.get(result_key)
            self.is_new_best = best is None or elapsed < best
            if self.is_new_best:
                self.best_times[result_key] = elapsed
            self.stop_bgm()
            self.play_sfx(3, protect_frames=15)
            self.screen = "finished"

    def open_confirmation(self, action: str) -> None:
        self.round.pause()
        self.pause_bgm()
        self.confirm_action = action
        self.screen = "confirm"

    def accept_confirmation(self) -> None:
        action = self.confirm_action
        self.confirm_action = None
        if action == "retry":
            self.begin_countdown(self.selected_mode)
        else:
            self.stop_bgm()
            self.screen = "ready"

    def cancel_confirmation(self) -> None:
        self.round.resume()
        self.confirm_action = None
        self.screen = "playing"
        self.resume_bgm()

    def toggle_bgm(self) -> None:
        self.bgm_on = not self.bgm_on
        if not self.bgm_on:
            self.pause_bgm()
        elif self.screen == "playing":
            if self.bgm_has_started:
                self.resume_bgm()
            else:
                self.start_bgm(
                    music_stage_for_progress(
                        self.round.completed_count,
                        max_number=self.round.max_number,
                    )
                )

    def toggle_sfx(self) -> None:
        self.sfx_on = not self.sfx_on
        if not self.sfx_on:
            pyxel.stop(3)
            self.sfx_priority_until_frame = 0

    @staticmethod
    def bgm_sequences(stage: int) -> tuple[list[int], list[int], list[int]]:
        """約77秒の同じ長さに揃えた旋律・ベース・ドラム列を返す。"""
        melody_sequences = {
            0: [
                8, 28, 9, 29, 10, 30, 11, 31,
                12, 28, 13, 29, 14, 30, 15, 32,
                10, 33, 11, 34, 12, 35, 13, 31,
                14, 32, 15, 33, 9, 34, 8, 35,
            ],
            1: [
                8, 28, 24, 29, 10, 30, 25, 31,
                12, 32, 26, 29, 14, 30, 27, 33,
                28, 40, 29, 41, 32, 42, 33, 43,
                12, 44, 14, 45, 32, 46, 34, 47,
            ],
            2: [
                24, 25, 40, 41, 26, 27, 42, 43,
                40, 41, 44, 45, 42, 43, 46, 47,
                24, 40, 25, 41, 26, 44, 27, 45,
                42, 43, 46, 47, 44, 45, 46, 47,
            ],
        }
        bass_sequences = {
            0: [
                16, 16, 17, 17, 18, 18, 19, 19,
                16, 17, 18, 19, 16, 17, 18, 19,
                17, 18, 19, 16, 18, 19, 17, 16,
                18, 17, 19, 16, 17, 18, 19, 39,
            ],
            1: [
                16, 36, 17, 37, 18, 38, 19, 39,
                36, 17, 37, 19, 36, 18, 38, 39,
                37, 38, 39, 36, 38, 39, 37, 36,
                38, 37, 39, 36, 37, 38, 39, 39,
            ],
            2: [
                36, 36, 37, 37, 38, 38, 39, 39,
                36, 37, 38, 39, 36, 37, 38, 39,
                37, 38, 39, 36, 38, 39, 37, 36,
                38, 37, 39, 36, 37, 38, 39, 39,
            ],
        }
        drum_sequences = {
            0: [
                20, 20, 20, 21, 20, 20, 21, 48,
                20, 21, 20, 21, 20, 21, 21, 48,
                21, 21, 20, 21, 21, 22, 21, 49,
                21, 22, 21, 22, 21, 22, 21, 51,
            ],
            1: [
                21, 21, 22, 21, 21, 22, 21, 49,
                21, 22, 21, 22, 22, 21, 22, 49,
                22, 22, 21, 22, 22, 23, 22, 50,
                22, 23, 22, 23, 22, 23, 49, 51,
            ],
            2: [
                22, 22, 23, 22, 23, 22, 23, 49,
                22, 23, 22, 23, 23, 22, 23, 50,
                23, 23, 22, 23, 23, 50, 23, 50,
                23, 50, 23, 50, 23, 50, 49, 51,
            ],
        }
        return melody_sequences[stage], bass_sequences[stage], drum_sequences[stage]

    def play_bgm_channels(self, stage: int, position_frames: int) -> None:
        melody, bass, drums = self.bgm_sequences(stage)
        position_seconds = position_frames / FPS
        pyxel.play(0, melody, sec=position_seconds, loop=True)
        pyxel.play(1, bass, sec=position_seconds, loop=True)
        pyxel.play(2, drums, sec=position_seconds, loop=True)

    def start_bgm(
        self,
        stage: int,
        position_frames: int = 0,
        *,
        clear_pending: bool = True,
    ) -> None:
        """指定した曲位置から3パートを同期して開始する。"""
        position_frames %= BGM_LOOP_FRAMES
        self.bgm_stage = stage
        if clear_pending:
            self.pending_bgm_stage = None
        self.play_bgm_channels(stage, position_frames)
        self.bgm_origin_frame = pyxel.frame_count - position_frames
        phrase_offset = position_frames % BGM_PHRASE_FRAMES
        frames_to_boundary = BGM_PHRASE_FRAMES - phrase_offset
        self.bgm_next_phrase_frame = pyxel.frame_count + frames_to_boundary
        self.bgm_paused_position_frames = position_frames
        self.bgm_paused = False
        self.bgm_has_started = True

    def current_bgm_position_frames(self) -> int:
        if self.bgm_paused:
            return self.bgm_paused_position_frames
        if not self.bgm_has_started:
            return 0
        return (pyxel.frame_count - self.bgm_origin_frame) % BGM_LOOP_FRAMES

    def update_bgm_transition(self) -> None:
        """進行度による編曲変更を、次の句境界まで待って適用する。"""
        if not self.bgm_on or self.bgm_paused or not self.bgm_has_started:
            return
        if pyxel.frame_count < self.bgm_next_phrase_frame:
            return
        position_frames = self.current_bgm_position_frames()
        if self.pending_bgm_stage is not None:
            # 32句形式の現在位置を保ったまま編曲だけを切り替える。
            self.start_bgm(self.pending_bgm_stage, position_frames)
            return
        phrase_offset = position_frames % BGM_PHRASE_FRAMES
        self.bgm_next_phrase_frame = (
            pyxel.frame_count + BGM_PHRASE_FRAMES - phrase_offset
        )

    def pause_bgm(self) -> None:
        if self.screen == "playing" and self.bgm_has_started and not self.bgm_paused:
            self.bgm_paused_position_frames = self.current_bgm_position_frames()
            pyxel.stop(0)
            pyxel.stop(1)
            pyxel.stop(2)
            self.bgm_paused = True

    def resume_bgm(self) -> None:
        if not self.bgm_on or self.screen != "playing":
            return
        if not self.bgm_has_started:
            self.start_bgm(
                music_stage_for_progress(
                    self.round.completed_count,
                    max_number=self.round.max_number,
                )
            )
        elif self.bgm_paused:
            self.start_bgm(
                self.bgm_stage,
                self.bgm_paused_position_frames,
                clear_pending=False,
            )

    def stop_bgm(self) -> None:
        pyxel.stop(0)
        pyxel.stop(1)
        pyxel.stop(2)
        self.bgm_paused = False
        self.bgm_has_started = False
        self.pending_bgm_stage = None
        self.bgm_origin_frame = 0
        self.bgm_paused_position_frames = 0

    def play_sfx(self, sound_index: int, *, protect_frames: int = 0) -> None:
        if not self.sfx_on:
            return
        # 節目音の直後だけ通常正解音を抑え、ミス音は即時フィードバックする。
        if sound_index == 0 and pyxel.frame_count < self.sfx_priority_until_frame:
            return
        pyxel.play(3, sound_index)
        if protect_frames:
            self.sfx_priority_until_frame = pyxel.frame_count + protect_frames

    @staticmethod
    def cell_at(x: int, y: int) -> int | None:
        for index in range(GRID_CELL_COUNT):
            row, column = divmod(index, GRID_COLUMNS)
            left = GRID_X + column * (CELL_WIDTH + CELL_GAP)
            top = GRID_Y + row * (CELL_HEIGHT + CELL_GAP)
            if point_in_rect(x, y, (left, top, CELL_WIDTH, CELL_HEIGHT)):
                return index
        return None

    def draw(self) -> None:
        pyxel.cls(BACKGROUND)
        self.draw_background()
        self.draw_header()

        if self.screen == "ready":
            self.draw_placeholder_grid()
            self.draw_progress_frame(0, self.selected_max_number)
            self.draw_characters()
            self.draw_ready_panel()
            return
        if self.screen == "countdown":
            self.draw_placeholder_grid()
            self.draw_progress_frame(0, self.selected_max_number)
            self.draw_characters()
            self.draw_countdown_panel()
            return
        if self.screen == "confirm":
            self.draw_confirmation_panel()
            return

        self.draw_progress_frame(
            self.round.completed_count,
            self.round.max_number,
        )
        self.draw_side_console()
        self.draw_game_board()
        self.draw_characters()
        if self.screen == "finished":
            self.draw_finished_panel()
        else:
            self.draw_message_panel()

    @staticmethod
    def draw_background() -> None:
        pyxel.line(18, 48, WIDTH - 19, 48, DEEP_BLUE)
        pyxel.line(18, 50, 100, 50, BLUE)
        pyxel.line(WIDTH - 101, 50, WIDTH - 19, 50, PINK)
        pyxel.rect(0, 302, WIDTH, 58, PANEL)
        pyxel.line(0, 302, WIDTH, 302, CARD)
        pyxel.line(0, 306, WIDTH, 306, MUTED)
        for x in range(0, WIDTH, 32):
            pyxel.rect(x, 350, 20, 3, DEEP_BLUE)
            pyxel.rect(x + 12, 310, 3, 3, PRESSED)
        for x, y in ((9, 64), (626, 63), (8, 340), (628, 337)):
            pyxel.rect(x, y, 3, 3, BLUE)
            pyxel.rect(x + 3, y + 3, 3, 3, DEEP_BLUE)

    def draw_header(self) -> None:
        pyxel.text(18, 18, "N U M B E R  R U S H", YELLOW)
        if self.screen == "ready":
            pyxel.text(116, 18, f"RANGE 1-{self.selected_max_number}", MUTED)
        else:
            mode = "ORDER" if self.selected_mode == "ordered" else "RANDOM"
            pyxel.text(116, 18, f"{self.selected_max_number} {mode}", MUTED)
        if self.screen in {"playing", "finished"}:
            pyxel.text(188, 18, f"T {self.round.elapsed():05.1f}", CARD)
            pyxel.text(242, 18, f"S {self.score:05d}", YELLOW)
            pyxel.text(306, 18, f"M {self.round.mistakes}", ERROR if self.round.mistakes else MUTED)
        if self.screen in {"playing", "countdown"}:
            self.draw_small_button(RETRY_BUTTON, "RETRY", GREEN, self.screen == "playing")
            self.draw_small_button(TITLE_BUTTON, "TITLE", BLUE, True)
        self.draw_small_button(BGM_BUTTON, "BGM ON" if self.bgm_on else "BGM OFF", GREEN, True)
        self.draw_small_button(SFX_BUTTON, "SFX ON" if self.sfx_on else "SFX OFF", PINK, True)

    @staticmethod
    def draw_progress_frame(completed: int, max_number: int) -> None:
        """盤面を囲む40個のセグメントで進行を表示する。"""
        segments: list[tuple[int, int, int, int]] = []
        for index in range(16):
            segments.append((100 + index * 28, 45, 25, 8))
        for index in range(4):
            segments.append((555, 58 + index * 43, 8, 40))
        for index in range(16):
            segments.append((520 - index * 28, 234, 25, 8))
        for index in range(4):
            segments.append((86, 187 - index * 43, 8, 40))

        filled_segments = completed * GRID_CELL_COUNT // max_number
        for index, (x, y, width, height) in enumerate(segments):
            if index < filled_segments:
                fill = GREEN
                border = CARD
            elif index == filled_segments and completed < max_number:
                fill = YELLOW
                border = CARD
            else:
                fill = DEEP_BLUE
                border = MUTED
            pyxel.rect(x, y, width, height, fill)
            pyxel.rectb(x, y, width, height, border)

    def draw_placeholder_grid(self) -> None:
        for index in range(GRID_CELL_COUNT):
            row, column = divmod(index, GRID_COLUMNS)
            x = GRID_X + column * (CELL_WIDTH + CELL_GAP)
            y = GRID_Y + row * (CELL_HEIGHT + CELL_GAP)
            pyxel.rect(x + 3, y + 3, CELL_WIDTH, CELL_HEIGHT, DEEP_BLUE)
            pyxel.rect(x, y, CELL_WIDTH, CELL_HEIGHT, PANEL)
            pyxel.rectb(x, y, CELL_WIDTH, CELL_HEIGHT, BLUE)
            pyxel.rectb(x + 2, y + 2, CELL_WIDTH - 4, CELL_HEIGHT - 4, BLUE)
            for dot_x in range(12, CELL_WIDTH - 7, 12):
                pyxel.rect(x + dot_x, y + 18, 4, 4, MUTED)

    def draw_game_board(self) -> None:
        for index, number in enumerate(self.round.board_cells):
            row, column = divmod(index, GRID_COLUMNS)
            x = GRID_X + column * (CELL_WIDTH + CELL_GAP)
            y = GRID_Y + row * (CELL_HEIGHT + CELL_GAP)
            if number is None:
                self.draw_empty_panel(x, y)
                continue

            already_found = number in self.round.found_numbers
            is_wrong = index == self.wrong_cell
            is_correct = index == self.correct_cell
            is_hovered = point_in_rect(
                pyxel.mouse_x,
                pyxel.mouse_y,
                (x, y, CELL_WIDTH, CELL_HEIGHT),
            )

            fill = PRESSED if already_found else CARD
            border = PANEL if already_found else BLUE
            if is_hovered and not already_found:
                fill = PEACH
                border = YELLOW
            if is_wrong:
                fill = ERROR
                border = CARD
            elif is_correct:
                border = GREEN

            pyxel.rect(x + 3, y + 3, CELL_WIDTH, CELL_HEIGHT, DEEP_BLUE)
            pyxel.rect(x, y, CELL_WIDTH, CELL_HEIGHT, fill)
            pyxel.rectb(x, y, CELL_WIDTH, CELL_HEIGHT, border)
            pyxel.rectb(x + 2, y + 2, CELL_WIDTH - 4, CELL_HEIGHT - 4, border)

            if already_found:
                self.draw_locked_pattern(x, y)
                pyxel.text(x + 4, y + 4, "HIT" if is_correct else "OK", GREEN if is_correct else MUTED)
            else:
                draw_number(
                    x + CELL_WIDTH // 2,
                    y + (CELL_HEIGHT - 21) // 2,
                    number,
                    CARD if is_wrong else PANEL,
                )
            if is_correct:
                self.draw_burst(x, y)

    @staticmethod
    def draw_empty_panel(x: int, y: int) -> None:
        """選択範囲で使わない、押せないマスを描く。"""
        pyxel.rect(x + 3, y + 3, CELL_WIDTH, CELL_HEIGHT, BACKGROUND)
        pyxel.rect(x, y, CELL_WIDTH, CELL_HEIGHT, DEEP_BLUE)
        pyxel.rectb(x, y, CELL_WIDTH, CELL_HEIGHT, MUTED)
        pyxel.rectb(x + 2, y + 2, CELL_WIDTH - 4, CELL_HEIGHT - 4, PANEL)
        for offset_x in range(8, CELL_WIDTH - 5, 9):
            pyxel.line(x + offset_x, y + 6, x + offset_x - 5, y + 11, PANEL)
            pyxel.line(
                x + offset_x,
                y + CELL_HEIGHT - 7,
                x + offset_x + 5,
                y + CELL_HEIGHT - 12,
                PANEL,
            )
        pyxel.text(x + 21, y + 14, "--", MUTED)

    @staticmethod
    def draw_locked_pattern(x: int, y: int) -> None:
        for offset_y in range(7, CELL_HEIGHT - 5, 7):
            for offset_x in range(7, CELL_WIDTH - 5, 7):
                color = MUTED if (offset_x + offset_y) % 2 else PANEL
                pyxel.rect(x + offset_x, y + offset_y, 3, 3, color)

    @staticmethod
    def draw_burst(x: int, y: int) -> None:
        center_x = x + CELL_WIDTH // 2
        center_y = y + CELL_HEIGHT // 2
        pyxel.line(center_x, y - 3, center_x, y + 2, GREEN)
        pyxel.line(center_x, y + CELL_HEIGHT - 2, center_x, y + CELL_HEIGHT + 3, GREEN)
        pyxel.line(x - 3, center_y, x + 2, center_y, GREEN)
        pyxel.line(x + CELL_WIDTH - 2, center_y, x + CELL_WIDTH + 3, center_y, GREEN)

    def character_action(self) -> str:
        if self.screen == "finished":
            return "clear"
        if pyxel.frame_count < self.milestone_until_frame:
            return "cheer"
        if self.wrong_cell is not None:
            return "wrong"
        if self.correct_cell is not None:
            return "correct"
        return "idle"

    def draw_characters(self) -> None:
        action = self.character_action()
        bob = (pyxel.frame_count // 18) % 2
        jump = 4 if action in {"cheer", "clear"} and (pyxel.frame_count // 5) % 2 else 0
        self.draw_otter(58, 282 - bob - jump, action)
        self.draw_fox(518, 280 - bob - jump, action)

    @staticmethod
    def draw_otter(x: int, y: int, action: str) -> None:
        """青緑の2頭身カワウソ探検家を図形だけで描く。"""
        blink = pyxel.frame_count % 180 < 7
        # 太い尾、脚、胴体。
        pyxel.circ(x + 7, y + 39, 10, DEEP_BLUE)
        pyxel.circ(x + 8, y + 38, 7, GREEN)
        pyxel.rect(x + 19, y + 29, 25, 24, DEEP_BLUE)
        pyxel.rect(x + 21, y + 29, 21, 22, GREEN)
        pyxel.circ(x + 31, y + 43, 10, GREEN)
        pyxel.circ(x + 31, y + 44, 6, CARD)
        pyxel.rect(x + 19, y + 49, 9, 6, DEEP_BLUE)
        pyxel.rect(x + 36, y + 49, 9, 6, DEEP_BLUE)

        # 頭と耳。頭と胴体をほぼ1:1にして2頭身にする。
        pyxel.circ(x + 18, y + 9, 7, DEEP_BLUE)
        pyxel.circ(x + 44, y + 9, 7, DEEP_BLUE)
        pyxel.circ(x + 18, y + 9, 4, GREEN)
        pyxel.circ(x + 44, y + 9, 4, GREEN)
        pyxel.circ(x + 31, y + 17, 16, DEEP_BLUE)
        pyxel.circ(x + 31, y + 17, 14, GREEN)
        pyxel.circ(x + 31, y + 23, 8, PEACH)
        pyxel.rect(x + 29, y + 19, 5, 4, PANEL)

        if blink or action == "wrong":
            pyxel.line(x + 22, y + 15, x + 26, y + 15, PANEL)
            pyxel.line(x + 37, y + 15, x + 41, y + 15, PANEL)
        else:
            pyxel.rect(x + 23, y + 13, 3, 5, PANEL)
            pyxel.rect(x + 37, y + 13, 3, 5, PANEL)
            pyxel.pset(x + 24, y + 13, CARD)
            pyxel.pset(x + 38, y + 13, CARD)
        pyxel.pset(x + 31, y + 22, CARD)

        # ピンクのスカーフでオリジナルの探検家らしさを出す。
        pyxel.rect(x + 20, y + 28, 23, 4, PINK)
        pyxel.tri(x + 39, y + 31, x + 48, y + 36, x + 40, y + 39, PINK)

        if action in {"correct", "cheer", "clear"}:
            pyxel.line(x + 20, y + 34, x + 10, y + 25, GREEN)
            pyxel.line(x + 42, y + 34, x + 52, y + 24, GREEN)
            pyxel.circ(x + 9, y + 24, 3, GREEN)
            pyxel.circ(x + 53, y + 23, 3, GREEN)
            pyxel.pset(x + 5, y + 17, YELLOW)
            pyxel.pset(x + 57, y + 16, YELLOW)
        else:
            pyxel.line(x + 21, y + 35, x + 13, y + 42, GREEN)
            pyxel.line(x + 41, y + 35, x + 49, y + 42, GREEN)
        if action == "wrong":
            pyxel.tri(x + 47, y + 9, x + 51, y + 15, x + 43, y + 15, BLUE)

    @staticmethod
    def draw_fox(x: int, y: int, action: str) -> None:
        """橙色の2頭身キツネライバルを図形だけで描く。"""
        blink = (pyxel.frame_count + 70) % 170 < 7
        # 大きな尾を背面に描く。
        pyxel.circ(x + 51, y + 40, 15, DEEP_BLUE)
        pyxel.circ(x + 50, y + 39, 12, YELLOW)
        pyxel.circ(x + 57, y + 34, 7, CARD)

        pyxel.rect(x + 18, y + 29, 25, 24, DEEP_BLUE)
        pyxel.rect(x + 20, y + 29, 21, 22, YELLOW)
        pyxel.circ(x + 30, y + 43, 10, YELLOW)
        pyxel.circ(x + 30, y + 44, 6, PEACH)
        pyxel.rect(x + 17, y + 49, 10, 6, DEEP_BLUE)
        pyxel.rect(x + 36, y + 49, 10, 6, DEEP_BLUE)

        # 三角耳と大きな頭。
        pyxel.tri(x + 15, y + 9, x + 20, y - 5, x + 28, y + 7, DEEP_BLUE)
        pyxel.tri(x + 34, y + 7, x + 43, y - 5, x + 48, y + 10, DEEP_BLUE)
        pyxel.tri(x + 18, y + 7, x + 21, y, x + 25, y + 8, ERROR)
        pyxel.tri(x + 37, y + 7, x + 42, y, x + 45, y + 9, ERROR)
        pyxel.circ(x + 31, y + 17, 16, DEEP_BLUE)
        pyxel.circ(x + 31, y + 17, 14, YELLOW)
        pyxel.circ(x + 31, y + 24, 8, CARD)
        pyxel.rect(x + 29, y + 20, 5, 4, PANEL)

        # 青いゴーグルがライバルの識別記号。
        pyxel.rectb(x + 18, y + 11, 11, 8, BLUE)
        pyxel.rectb(x + 34, y + 11, 11, 8, BLUE)
        pyxel.line(x + 29, y + 14, x + 34, y + 14, BLUE)
        if blink:
            pyxel.line(x + 21, y + 15, x + 26, y + 15, PANEL)
            pyxel.line(x + 37, y + 15, x + 42, y + 15, PANEL)
        else:
            eye_y = y + 13 if action != "wrong" else y + 15
            pyxel.rect(x + 23, eye_y, 2, 4, PANEL)
            pyxel.rect(x + 38, eye_y, 2, 4, PANEL)
        pyxel.pset(x + 31, y + 23, PANEL)

        if action == "wrong":
            # プレイヤーのミスには得意げなポーズ。
            pyxel.line(x + 20, y + 35, x + 10, y + 31, YELLOW)
            pyxel.line(x + 41, y + 35, x + 48, y + 27, YELLOW)
            pyxel.line(x + 27, y + 26, x + 31, y + 29, ERROR)
            pyxel.line(x + 31, y + 29, x + 35, y + 26, ERROR)
        elif action in {"cheer", "clear"}:
            pyxel.line(x + 20, y + 34, x + 10, y + 24, YELLOW)
            pyxel.line(x + 42, y + 34, x + 51, y + 23, YELLOW)
            pyxel.circ(x + 9, y + 23, 3, YELLOW)
            pyxel.circ(x + 52, y + 22, 3, YELLOW)
        else:
            pyxel.line(x + 20, y + 35, x + 12, y + 42, YELLOW)
            pyxel.line(x + 41, y + 35, x + 48, y + 42, YELLOW)

    def draw_side_console(self) -> None:
        self.draw_box(38, 58, 40, 174, BLUE)
        pyxel.text(48, 68, "SCAN", YELLOW)
        gauge_x = 51
        gauge_y = 88
        gauge_height = 108
        pyxel.rect(gauge_x, gauge_y, 12, gauge_height, DEEP_BLUE)
        progress_height = int(
            (gauge_height - 4)
            * self.round.completed_count
            / self.round.max_number
        )
        pyxel.rect(
            gauge_x + 2,
            gauge_y + gauge_height - 2 - progress_height,
            8,
            progress_height,
            BLUE,
        )
        pyxel.rectb(gauge_x, gauge_y, 12, gauge_height, CARD)
        cursor_y = gauge_y + gauge_height - 2 - progress_height
        pyxel.tri(57, cursor_y - 5, 52, cursor_y, 57, cursor_y + 5, PINK)
        pyxel.tri(57, cursor_y - 5, 62, cursor_y, 57, cursor_y + 5, PINK)
        pyxel.circ(57, cursor_y, 2, CARD)
        pyxel.line(63, cursor_y, 84, cursor_y, CARD)
        pyxel.text(
            42,
            207,
            f"{self.round.completed_count:02d}/{self.round.max_number:02d}",
            CARD,
        )
        pyxel.text(46, 220, "FOUND", MUTED)

        self.draw_box(570, 58, 62, 174, GREEN)
        pyxel.text(589, 68, "ENERGY", YELLOW)
        pyxel.rect(581, 88, 40, 112, DEEP_BLUE)
        energy_height = int(
            108 * self.round.completed_count / self.round.max_number
        )
        pyxel.rect(583, 198 - energy_height, 36, energy_height, GREEN)
        for line_y in range(94, 198, 12):
            pyxel.line(583, line_y, 618, line_y, PANEL)
        pyxel.rectb(581, 88, 40, 112, CARD)
        pyxel.text(584, 208, f"LEVEL {self.bgm_stage + 1}", CARD)
        pyxel.text(585, 220, "DRIVE", MUTED)

    def draw_message_panel(self) -> None:
        border = ERROR if self.wrong_cell is not None else BLUE
        self.draw_box(170, 250, 300, 94, border)
        target = self.round.current_target or self.round.max_number

        pyxel.text(198, 269, "FIND THE", MUTED)
        draw_number(320, 260, target, CARD, scale=5)
        pyxel.text(381, 274, "!", YELLOW)

        if self.wrong_cell is not None:
            centered_text(308, "MISS!  TRY THE SAME TARGET", ERROR)
        elif pyxel.frame_count < self.milestone_until_frame:
            centered_text(
                308,
                f"CHECKPOINT {self.milestone_value}/{self.round.max_number} - DRIVE UP!",
                GREEN,
            )
        elif pyxel.frame_count < self.go_until_frame:
            centered_text(308, "GO!  SCAN THE BOARD", GREEN)
        elif self.selected_mode == "ordered":
            centered_text(
                308,
                f"NEXT IN ORDER  /  HIT 1 TO {self.round.max_number}",
                YELLOW,
            )
        else:
            centered_text(308, "SHUFFLED TARGET  /  FOLLOW THE SIGNAL", YELLOW)

        progress = self.round.completed_count / self.round.max_number
        pyxel.rect(194, 328, 252, 7, DEEP_BLUE)
        pyxel.rect(196, 330, int(248 * progress), 3, GREEN)

    def draw_ready_panel(self) -> None:
        pyxel.dither(0.8)
        pyxel.rect(112, 83, 416, 194, DEEP_BLUE)
        pyxel.dither(1.0)
        self.draw_box(118, 78, 404, 194, BLUE)
        centered_text(96, "CHOOSE RANGE, THEN RULE", CARD)
        centered_text(110, "NUMBERS ARE SHUFFLED ACROSS ALL 40 CELLS", MUTED)
        for max_number, button in RANGE_BUTTONS.items():
            self.draw_button(
                button,
                f"1-{max_number}",
                BLUE,
                selected=max_number == self.selected_max_number,
            )
        locked_count = GRID_CELL_COUNT - self.selected_max_number
        centered_text(
            169,
            f"{self.selected_max_number} TARGETS / {locked_count} LOCKED PANELS",
            YELLOW,
        )
        centered_text(186, "SELECT PLAY RULE", MUTED)
        self.draw_button(ORDER_BUTTON, "START ORDER", GREEN)
        self.draw_button(RANDOM_BUTTON, "START RANDOM", BLUE)
        centered_text(260, "KEY 1-4: RANGE   O: ORDER   R: RANDOM", MUTED)

    def draw_countdown_panel(self) -> None:
        remaining = max(0, self.countdown_end_frame - pyxel.frame_count)
        count = max(1, (remaining + 59) // 60)
        pyxel.dither(0.85)
        pyxel.rect(190, 82, 260, 190, DEEP_BLUE)
        pyxel.dither(1.0)
        self.draw_box(196, 76, 248, 190, PINK)
        centered_text(94, "GET READY", YELLOW)
        mode = "ORDER" if self.selected_mode == "ordered" else "RANDOM"
        centered_text(112, f"1-{self.selected_max_number} / {mode}", MUTED)
        draw_number(WIDTH // 2, 132, count, CARD, scale=10)
        centered_text(218, "NUMBERS APPEAR AT GO", MUTED)
        centered_text(238, "TITLE CAN CANCEL", BLUE)

    def draw_confirmation_panel(self) -> None:
        # 不意な盤面の記憶を防ぐため、確認中は盤面全体を不透明に隠す。
        pyxel.rect(8, 52, 624, 300, BACKGROUND)
        pyxel.dither(0.85)
        pyxel.rect(138, 92, 376, 186, DEEP_BLUE)
        pyxel.dither(1.0)
        self.draw_box(144, 86, 352, 186, PINK)
        question = "RESTART THIS RUN?" if self.confirm_action == "retry" else "RETURN TO TITLE?"
        centered_text(116, "CONFIRM", YELLOW)
        centered_text(149, question, CARD)
        centered_text(177, "TIMER PAUSED / BOARD HIDDEN", MUTED)
        self.draw_button(YES_BUTTON, "YES", GREEN)
        self.draw_button(NO_BUTTON, "NO", ERROR)
        pyxel.text(238, 282, "KEY Y", MUTED)
        pyxel.text(369, 282, "KEY N", MUTED)

    def draw_finished_panel(self) -> None:
        pyxel.dither(0.85)
        pyxel.rect(112, 67, 416, 214, DEEP_BLUE)
        pyxel.dither(1.0)
        self.draw_box(118, 62, 404, 214, GREEN)
        mode = "ORDER MODE" if self.selected_mode == "ordered" else "RANDOM MODE"
        mode_label = f"1-{self.round.max_number} / {mode}"
        centered_text(92, "SCAN COMPLETE", GREEN)
        centered_text(112, mode_label, YELLOW)
        centered_text(137, f"TIME {self.round.elapsed():.2f}s    SCORE {self.score}", CARD)
        centered_text(157, f"MISSES {self.round.mistakes}    MAX STREAK {self.max_streak}", CARD)
        best = self.best_times.get((self.round.max_number, self.selected_mode))
        if self.is_new_best:
            centered_text(181, f"NEW BEST!  {best:.2f}s", PINK)
        elif best is not None:
            centered_text(181, f"SESSION BEST  {best:.2f}s", MUTED)
        self.draw_button(REPLAY_BUTTON, "PLAY AGAIN", GREEN)
        self.draw_button(MODE_BUTTON, "MODE SELECT", BLUE)
        pyxel.text(196, 282, "SPACE", MUTED)
        pyxel.text(430, 282, "KEY M", MUTED)

    @staticmethod
    def draw_box(x: int, y: int, width: int, height: int, border: int) -> None:
        pyxel.rect(x + 4, y + 4, width, height, DEEP_BLUE)
        pyxel.rect(x, y, width, height, PANEL)
        pyxel.rectb(x, y, width, height, CARD)
        pyxel.rectb(x + 3, y + 3, width - 6, height - 6, border)

    @staticmethod
    def draw_button(
        rect: tuple[int, int, int, int],
        label: str,
        base_color: int,
        *,
        selected: bool = False,
    ) -> None:
        x, y, width, height = rect
        hovered = point_in_rect(pyxel.mouse_x, pyxel.mouse_y, rect)
        fill = YELLOW if hovered or selected else base_color
        outer_border = GREEN if selected else CARD
        pyxel.rect(x + 4, y + 4, width, height, DEEP_BLUE)
        pyxel.rect(x, y, width, height, fill)
        pyxel.rectb(x, y, width, height, outer_border)
        pyxel.rectb(x + 2, y + 2, width - 4, height - 4, PANEL)
        pyxel.text(
            x + (width - len(label) * 4) // 2,
            y + (height - 6) // 2,
            label,
            BACKGROUND,
        )

    @staticmethod
    def draw_small_button(
        rect: tuple[int, int, int, int],
        label: str,
        base_color: int,
        enabled: bool,
    ) -> None:
        x, y, width, height = rect
        hovered = enabled and point_in_rect(pyxel.mouse_x, pyxel.mouse_y, rect)
        fill = YELLOW if hovered else (base_color if enabled else PANEL)
        color = BACKGROUND if enabled else MUTED
        pyxel.rect(x + 2, y + 2, width, height, DEEP_BLUE)
        pyxel.rect(x, y, width, height, fill)
        pyxel.rectb(x, y, width, height, CARD if enabled else MUTED)
        pyxel.text(x + (width - len(label) * 4) // 2, y + 13, label, color)


if __name__ == "__main__":
    NumberRush()
