# title: Number Rush
# author: diceK9750 / Codex
# desc: Tap the shuffled numbers from 1 to 9 as fast as possible.
# site: https://dicek9750.github.io/game/
# version: 1.0

"""Pyxelで動く数字タップゲーム NUMBER RUSH。"""

from __future__ import annotations

import pyxel

from game_logic import NumberTapRound


WIDTH = 360
HEIGHT = 540
GRID_X = 33
GRID_Y = 145
CELL_SIZE = 90
CELL_GAP = 12

START_BUTTON = (70, 392, 220, 62)
REPLAY_BUTTON = (70, 438, 220, 58)

# Pyxelの16色パレット内で、背景・通常・成功・失敗を見分けやすくする。
BACKGROUND = 1
PANEL = 5
PANEL_HOVER = 6
PANEL_PRESSED = 3
OUTLINE = 12
TEXT = 7
MUTED = 13
ACCENT = 10
SUCCESS = 11
ERROR = 8
SHADOW = 0

DIGITS = {
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


def draw_large_digit(x: int, y: int, number: int, color: int, scale: int = 7) -> None:
    """5×7のビットマップ数字を拡大して描く。"""
    pattern = DIGITS[str(number)]
    for row, bits in enumerate(pattern):
        for column, bit in enumerate(bits):
            if bit == "1":
                pyxel.rect(x + column * scale, y + row * scale, scale, scale, color)


class NumberRush:
    """描画と入力を受け持つPyxelアプリケーション。"""

    def __init__(self) -> None:
        pyxel.init(WIDTH, HEIGHT, title="NUMBER RUSH", fps=60)
        pyxel.mouse(True)
        self.round = NumberTapRound()
        self.screen = "ready"
        self.wrong_cell: int | None = None
        self.wrong_until_frame = 0
        self.best_time: float | None = None
        pyxel.run(self.update, self.draw)

    def update(self) -> None:
        clicked = pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)
        confirm_key = pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN)

        if self.screen == "ready":
            if confirm_key or (
                clicked and point_in_rect(pyxel.mouse_x, pyxel.mouse_y, START_BUTTON)
            ):
                self.start_round()
            return

        if self.screen == "finished":
            if confirm_key or (
                clicked and point_in_rect(pyxel.mouse_x, pyxel.mouse_y, REPLAY_BUTTON)
            ):
                self.start_round()
            return

        if clicked:
            cell_index = self.cell_at(pyxel.mouse_x, pyxel.mouse_y)
            if cell_index is not None:
                result = self.round.tap(self.round.numbers[cell_index])
                if result == "wrong":
                    self.wrong_cell = cell_index
                    self.wrong_until_frame = pyxel.frame_count + 30
                elif result == "finished":
                    elapsed = self.round.elapsed()
                    self.best_time = (
                        elapsed if self.best_time is None else min(self.best_time, elapsed)
                    )
                    self.screen = "finished"

        if pyxel.frame_count >= self.wrong_until_frame:
            self.wrong_cell = None

    def start_round(self) -> None:
        self.round.start()
        self.screen = "playing"
        self.wrong_cell = None
        self.wrong_until_frame = 0

    @staticmethod
    def cell_at(x: int, y: int) -> int | None:
        for index in range(9):
            row, column = divmod(index, 3)
            left = GRID_X + column * (CELL_SIZE + CELL_GAP)
            top = GRID_Y + row * (CELL_SIZE + CELL_GAP)
            if point_in_rect(x, y, (left, top, CELL_SIZE, CELL_SIZE)):
                return index
        return None

    def draw(self) -> None:
        pyxel.cls(BACKGROUND)
        self.draw_background()

        centered_text(24, "N U M B E R   R U S H", ACCENT)
        centered_text(42, "TAP 1 TO 9 AS FAST AS YOU CAN", MUTED)

        if self.screen == "ready":
            self.draw_ready_screen()
        else:
            self.draw_game_board()
            if self.screen == "finished":
                self.draw_finished_panel()
            else:
                self.draw_playing_status()

    @staticmethod
    def draw_background() -> None:
        for x, y in ((18, 84), (329, 104), (15, 504), (338, 482)):
            pyxel.rect(x, y, 4, 4, PANEL)
            pyxel.rect(x + 4, y + 4, 4, 4, PANEL)
        pyxel.line(28, 64, WIDTH - 29, 64, PANEL)

    def draw_ready_screen(self) -> None:
        centered_text(104, "READY?", TEXT)
        centered_text(126, "THE TIMER STARTS WHEN YOU PRESS START", MUTED)

        # 開始前にも3×3の構成が伝わるように、装飾用の空マスを表示する。
        for index in range(9):
            row, column = divmod(index, 3)
            x = GRID_X + column * (CELL_SIZE + CELL_GAP)
            y = GRID_Y + row * (CELL_SIZE + CELL_GAP)
            pyxel.rect(x + 4, y + 5, CELL_SIZE, CELL_SIZE, SHADOW)
            pyxel.rect(x, y, CELL_SIZE, CELL_SIZE, PANEL)
            pyxel.rectb(x, y, CELL_SIZE, CELL_SIZE, OUTLINE)
            pyxel.circ(x + CELL_SIZE // 2, y + CELL_SIZE // 2, 4, MUTED)

        self.draw_button(START_BUTTON, "START")
        centered_text(474, "CLICK / TAP  |  SPACE / ENTER", MUTED)

    def draw_game_board(self) -> None:
        for index, number in enumerate(self.round.numbers):
            row, column = divmod(index, 3)
            x = GRID_X + column * (CELL_SIZE + CELL_GAP)
            y = GRID_Y + row * (CELL_SIZE + CELL_GAP)
            already_pressed = number < self.round.next_number
            is_wrong = index == self.wrong_cell
            is_hovered = self.screen == "playing" and point_in_rect(
                pyxel.mouse_x, pyxel.mouse_y, (x, y, CELL_SIZE, CELL_SIZE)
            )

            color = PANEL_PRESSED if already_pressed else PANEL
            if is_hovered and not already_pressed:
                color = PANEL_HOVER
            if is_wrong:
                color = ERROR

            pyxel.rect(x + 4, y + 5, CELL_SIZE, CELL_SIZE, SHADOW)
            pyxel.rect(x, y, CELL_SIZE, CELL_SIZE, color)
            pyxel.rectb(
                x,
                y,
                CELL_SIZE,
                CELL_SIZE,
                SUCCESS if already_pressed else OUTLINE,
            )

            digit_color = SUCCESS if already_pressed else TEXT
            if is_wrong:
                digit_color = TEXT
            digit_width = 5 * 7
            digit_height = 7 * 7
            draw_large_digit(
                x + (CELL_SIZE - digit_width) // 2,
                y + (CELL_SIZE - digit_height) // 2,
                number,
                digit_color,
            )

            if already_pressed:
                pyxel.line(x + 66, y + 69, x + 72, y + 75, SUCCESS)
                pyxel.line(x + 72, y + 75, x + 82, y + 61, SUCCESS)

    def draw_playing_status(self) -> None:
        elapsed = self.round.elapsed()
        pyxel.text(34, 90, f"NEXT  {self.round.next_number}", TEXT)
        pyxel.text(139, 90, f"TIME  {elapsed:05.2f}s", ACCENT)
        pyxel.text(276, 90, f"MISS  {self.round.mistakes}", MUTED)

        if self.wrong_cell is not None:
            centered_text(475, f"WRONG!  TAP {self.round.next_number}", ERROR)
            pyxel.rectb(24, 462, WIDTH - 48, 34, ERROR)
        else:
            centered_text(475, f"FIND NUMBER {self.round.next_number}", MUTED)

    def draw_finished_panel(self) -> None:
        # 盤面の上に読みやすい結果パネルを重ねる。
        pyxel.dither(0.75)
        pyxel.rect(44, 184, WIDTH - 88, 234, SHADOW)
        pyxel.dither(1.0)
        pyxel.rect(50, 178, WIDTH - 100, 234, PANEL)
        pyxel.rectb(50, 178, WIDTH - 100, 234, SUCCESS)
        centered_text(207, "CLEAR!", SUCCESS)
        centered_text(238, "YOUR TIME", MUTED)
        centered_text(263, f"{self.round.elapsed():.2f} SECONDS", TEXT)
        centered_text(295, f"MISSES  {self.round.mistakes}", MUTED)
        if self.best_time is not None:
            centered_text(320, f"BEST  {self.best_time:.2f} SECONDS", ACCENT)
        centered_text(354, "GREAT REFLEXES!", TEXT)
        self.draw_button(REPLAY_BUTTON, "PLAY AGAIN")

    @staticmethod
    def draw_button(rect: tuple[int, int, int, int], label: str) -> None:
        x, y, width, height = rect
        hovered = point_in_rect(pyxel.mouse_x, pyxel.mouse_y, rect)
        color = ACCENT if hovered else SUCCESS
        pyxel.rect(x + 4, y + 5, width, height, SHADOW)
        pyxel.rect(x, y, width, height, color)
        pyxel.rectb(x, y, width, height, TEXT)
        pyxel.text(
            x + (width - len(label) * 4) // 2,
            y + (height - 6) // 2,
            label,
            SHADOW,
        )


if __name__ == "__main__":
    NumberRush()
