# title: Number Rush
# author: diceK9750 / Codex
# desc: Find 1 to 10, 20, 30, or 40 in order or in a shuffled sequence.
# site: https://dicek9750.github.io/game/
# version: 12.0

"""横持ちブラウザ向けの数字タップゲーム NUMBER RUSH。"""

from __future__ import annotations

import pyxel
import math
import progress
from ui_text import text as ui_text, text_width, translate
from characters import draw_rival
from character_layer import CharacterLayer
from modern_ui import ModernUI
try:
    from js import document as browser_document
    from pyodide.ffi import create_proxy
except ImportError:
    browser_document = None
from music import configure_bgm, configure_scene_bgm, SCENE_TRACKS, sequences as music_sequences
from music import SPEED, TICKS, PHRASE_COUNT, BATTLE_SPEED, BATTLE_PHRASE_COUNT

from game_logic import (
    BOARD_CELL_COUNT,
    NumberTapRound,
    BattleRound,
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
PLAY_BUTTONS = {"battle": (124, 76, 188, 28), "practice": (328, 76, 188, 28)}
DIFFICULTY_BUTTONS = {"easy": (124, 169, 120, 26), "normal": (260, 169, 120, 26), "hard": (396, 169, 120, 26)}
YES_BUTTON = (200, 220, 110, 42)
NO_BUTTON = (330, 220, 110, 42)
EXTRA_BUTTON = (222, 282, 196, 30)
PAUSE_BUTTON = (308, 9, 56, 32)
HINT_BUTTON = (182, 301, 110, 32)

COUNTDOWN_FRAMES = 180
WRONG_EFFECT_FRAMES = 48
BOMB_FUSE_FRAMES = 10
EXPLOSION_END_FRAME = 30
CORRECT_EFFECT_FRAMES = 34
BGM_NOTES_PER_PHRASE = TICKS
BGM_SOUND_SPEED = SPEED
PYXEL_AUDIO_TICKS_PER_SECOND = 120
BGM_PHRASE_COUNT = PHRASE_COUNT
BGM_PHRASE_FRAMES = (
    BGM_NOTES_PER_PHRASE * BGM_SOUND_SPEED * FPS // PYXEL_AUDIO_TICKS_PER_SECOND
)
BGM_LOOP_FRAMES = BGM_PHRASE_FRAMES * BGM_PHRASE_COUNT
BATTLE_BGM_PHRASE_FRAMES = (
    BGM_NOTES_PER_PHRASE * BATTLE_SPEED * FPS // PYXEL_AUDIO_TICKS_PER_SECOND
)
BATTLE_BGM_LOOP_FRAMES = BATTLE_BGM_PHRASE_FRAMES * BATTLE_PHRASE_COUNT

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

# 暗い筐体と明るい数字を分離した専用パレット。
PALETTE = [
    0x101321, 0x202840, 0x73456A, 0x356B65,
    0xA87958, 0x35435F, 0x71849A, 0xFAF6E8,
    0xE56569, 0xDB8A4D, 0xF8CC70, 0x91D9BA,
    0x78C6EE, 0xA1B4C3, 0xEE9CB5, 0xF5DEB0,
]

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

LETTERS = {
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
}


def pixel_label(x, y, label, color, scale=2):
    """Large, crisp labels for the central prompt and results."""
    for index, letter in enumerate(label):
        rows = LETTERS.get(letter, DIGITS.get(letter, ()))
        for row, bits in enumerate(rows):
            for col, bit in enumerate(bits):
                if bit == "1":
                    pyxel.rect(x + (index * 6 + col) * scale, y + row * scale, scale, scale, color)


def centered_text(y: int, label: str, color: int) -> None:
    """Pyxel標準フォントの文字列を画面中央に描く。"""
    ui_text(pyxel, (WIDTH - text_width(label)) // 2, y, label, color)


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
        # Escape belongs to our pause/help UI, not Pyxel's default quit shortcut.
        pyxel.init(WIDTH, HEIGHT, title="NUMBER RUSH", fps=FPS, quit_key=pyxel.KEY_NONE)
        pyxel.colors.from_list(PALETTE)
        pyxel.mouse(True)
        self.configure_sounds()
        self.character_layer = CharacterLayer(browser_document)
        self.modern_ui = ModernUI(browser_document)
        self.selected_max_number = 40
        self.round = NumberTapRound(max_number=self.selected_max_number)
        self.screen = "ready"
        self.selected_mode = "ordered"
        self.play_kind = "battle"
        self.difficulty = "normal"
        self.cpu_reaction_until = 0
        self.resume_end_frame = 0
        self.battle_records = {}
        self.bonus_bank = 0
        self._settled_round = None
        self.result_started_frame = 0
        self.confirm_action: str | None = None
        self.countdown_end_frame = 0
        self.go_until_frame = 0
        self.wrong_cell: int | None = None
        self.wrong_started_frame = 0
        self.wrong_until_frame = 0
        self.correct_cell: int | None = None
        self.correct_started_frame = 0
        self.correct_until_frame = 0
        self.cell_effects: list[tuple[str, int, int]] = []
        self.milestone_value = 0
        self.milestone_until_frame = 0
        self.score = 0
        self.streak = 0
        self.max_streak = 0
        self.bgm_on = True
        self.scene_music = None
        self.cursor_cell = 0
        self.keyboard_cursor = False
        self.auto_suspended = False
        self.result_music_after = 0
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
        self.reduced_motion = False
        self.hint_until = 0
        self.hint_used = False
        self.storage_saved = False
        for field, value in progress.load().items():
            setattr(self, field, value)
        # RAF may stop entirely in a hidden Safari tab. Pause at the event itself.
        if browser_document is not None:
            self._visibility_listener = create_proxy(lambda *_: self.update_visibility())
            browser_document.addEventListener("visibilitychange", self._visibility_listener)
        pyxel.run(self.update, self.draw)

    @staticmethod
    def configure_sounds() -> None:
        """効果音と柔らかなオリジナルBGMを登録する。"""
        pyxel.sounds[0].set("b3e4g4", "t", "454", "nnf", 4)
        pyxel.sounds[1].set("c2g1c1", "n", "432", "fff", 4)
        pyxel.sounds[2].set("g3b3d4g4", "t", "4454", "nnnf", 5)
        pyxel.sounds[3].set("g3b3d4g4b4g4", "t", "445554", "nnnnnf", 5)
        pyxel.sounds[4].set("e3g3b3e4", "t", "3443", "nnnf", 5)
        pyxel.sounds[5].set("b3g3e3", "p", "443", "nnf", 5)
        pyxel.sounds[6].set("e4b3g3e3b2", "t", "44332", "nnnnf", 9)
        pyxel.sounds[7].set("g3b3d4g4rd4g4a4b4g4", "t", "4455045543", "nnnnnnnnnf", 6)

        configure_bgm(pyxel.sounds)
        configure_scene_bgm(pyxel.sounds)

    def update(self) -> None:
        if self.update_visibility():
            return
        modern = getattr(self, "modern_ui", None)
        if modern is not None:
            modern.consume(self)
        self.update_frame()
        self.sync_scene_music()

    def update_visibility(self) -> bool:
        hidden = browser_document is not None and bool(browser_document.hidden)
        if hidden:
            if not self.auto_suspended:
                if self.screen == "shiritori":
                    self.shiritori.command("pause")
                if self.screen == "playing":
                    self.open_confirmation("pause")
                elif self.screen in {"countdown", "resuming"}:
                    self.suspended_at_frame = pyxel.frame_count
                self.pause_bgm()
                self.stop_scene_music()
                pyxel.stop(3)
                self.auto_suspended = True
            return True
        if self.auto_suspended:
            if self.screen == "countdown":
                self.countdown_end_frame += pyxel.frame_count - self.suspended_at_frame
            elif self.screen == "resuming":
                self.resume_end_frame += pyxel.frame_count - self.suspended_at_frame
            self.auto_suspended = False
        return False

    def update_frame(self) -> None:
        modern = getattr(self, "modern_ui", None)
        if self.screen == "shiritori":
            if modern is None or not modern.ready:
                self.screen = "ready"
            else:
                self.shiritori.update()
            return
        if modern is not None and modern.ready:
            # HTML owns all input in this renderer. Keep only the existing
            # simulation clocks here so pointer/key events cannot fire twice.
            self.update_visual_feedback()
            if self.screen == "playing":
                self.update_bgm_transition()
                self.update_cpu_turn()
            elif self.screen == "resuming" and pyxel.frame_count >= self.resume_end_frame:
                self.round.resume()
                self.screen = "playing"
                self.resume_bgm()
            elif self.screen == "countdown" and pyxel.frame_count >= self.countdown_end_frame:
                self.start_round(self.selected_mode)
            return
        clicked = pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)
        mouse = (pyxel.mouse_x, pyxel.mouse_y)
        self.update_visual_feedback()

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
            if clicked and point_in_rect(*mouse, PAUSE_BUTTON):
                self.open_confirmation("pause")
                return
            if (pyxel.btnp(pyxel.KEY_H) or clicked and point_in_rect(*mouse, HINT_BUTTON)):
                if not isinstance(self.round, BattleRound):
                    self.show_hint()
                    clicked = False

        if self.screen == "ready":
            if clicked and point_in_rect(*mouse, EXTRA_BUTTON):
                self.toggle_motion()
                return
            if pyxel.btnp(pyxel.KEY_H) or (clicked and point_in_rect(*mouse, RETRY_BUTTON)):
                self.screen = "help"
                return
            for kind, button in PLAY_BUTTONS.items():
                if clicked and point_in_rect(*mouse, button):
                    self.play_kind = kind
                    return
            for difficulty, button in DIFFICULTY_BUTTONS.items():
                if clicked and point_in_rect(*mouse, button):
                    self.difficulty = difficulty
                    return
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

        if self.screen == "help":
            if (pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_RETURN)
                    or clicked and point_in_rect(*mouse, YES_BUTTON)):
                self.screen = "ready"
            return

        if self.screen == "resuming":
            if pyxel.frame_count >= self.resume_end_frame:
                self.round.resume()
                self.screen = "playing"
                self.resume_bgm()
            return

        if self.screen == "countdown":
            if pyxel.btnp(pyxel.KEY_T) or (
                clicked and point_in_rect(*mouse, TITLE_BUTTON)
            ):
                self.clear_feedback()
                self.screen = "ready"
            elif pyxel.frame_count >= self.countdown_end_frame:
                self.start_round(self.selected_mode)
            return

        if self.screen == "confirm":
            if self.confirm_action == "pause":
                if pyxel.btnp(pyxel.KEY_RETURN) or clicked and point_in_rect(*mouse, YES_BUTTON):
                    self.cancel_confirmation()
                elif pyxel.btnp(pyxel.KEY_T) or clicked and point_in_rect(*mouse, NO_BUTTON):
                    self.confirm_action = "title"
                return
            if pyxel.btnp(pyxel.KEY_Y) or (
                clicked and point_in_rect(*mouse, YES_BUTTON)
            ):
                self.accept_confirmation()
            elif pyxel.btnp(pyxel.KEY_N) or (
                clicked and point_in_rect(*mouse, NO_BUTTON)
            ):
                self.cancel_confirmation()
            return

        if self.screen == "review":
            if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_RETURN) or clicked and point_in_rect(*mouse, EXTRA_BUTTON):
                self.screen = "finished"
            return

        if self.screen == "finished":
            if isinstance(self.round, BattleRound) and (pyxel.btnp(pyxel.KEY_H) or clicked and point_in_rect(*mouse, EXTRA_BUTTON)):
                self.screen = "review"
                return
            if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN) or (
                clicked and point_in_rect(*mouse, REPLAY_BUTTON)
            ):
                self.begin_countdown(self.selected_mode)
            elif pyxel.btnp(pyxel.KEY_M) or (
                clicked and point_in_rect(*mouse, MODE_BUTTON)
            ):
                self.clear_feedback()
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

        if pyxel.btnp(pyxel.KEY_ESCAPE):
            self.open_confirmation("pause")
            return

        for key, dx, dy in ((pyxel.KEY_LEFT, -1, 0), (pyxel.KEY_RIGHT, 1, 0),
                            (pyxel.KEY_UP, 0, -1), (pyxel.KEY_DOWN, 0, 1)):
            if pyxel.btnp(key, 15, 5):
                row, col = divmod(self.cursor_cell, GRID_COLUMNS)
                self.cursor_cell = ((row + dy) % GRID_ROWS) * GRID_COLUMNS + (col + dx) % GRID_COLUMNS
                self.keyboard_cursor = True
        if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE):
            self.keyboard_cursor = True
            self.handle_tap(self.cursor_cell)

        if clicked:
            cell_index = self.cell_at(*mouse)
            if cell_index is not None:
                self.keyboard_cursor = False
                self.cursor_cell = cell_index
                self.handle_tap(cell_index)
        # 入力を先に判定し、同一フレームの競合はプレイヤー優先にする。
        self.update_cpu_turn()

    def update_cpu_turn(self) -> None:
        """Advance the original CPU once, after either renderer's player input."""
        if self.screen == "playing" and isinstance(self.round, BattleRound):
            number = self.round.update_cpu()
            if number is not None:
                self.clear_feedback()
                self.cpu_reaction_until = pyxel.frame_count + 48
                self.streak = 0
                self.add_cell_effect("cpu", self.round.board_cells.index(number))
                self.play_sfx(5)
                self.update_battle_progress()
                if self.round.is_finished:
                    self.finish_battle()

    def show_hint(self) -> None:
        if self.screen == "playing" and not isinstance(self.round, BattleRound):
            self.hint_used = True
            self.hint_until = pyxel.frame_count + 120

    def toggle_motion(self) -> None:
        self.reduced_motion = not self.reduced_motion
        self.storage_saved = progress.save(self)

    def update_visual_feedback(self) -> None:
        """期限切れのリアクションと盤面エフェクトを片付ける。"""
        if pyxel.frame_count >= self.wrong_until_frame:
            self.wrong_cell = None
            self.wrong_started_frame = 0
        if pyxel.frame_count >= self.correct_until_frame:
            self.correct_cell = None
            self.correct_started_frame = 0
        self.cell_effects = [
            effect
            for effect in self.cell_effects
            if pyxel.frame_count - effect[2]
            < (
                WRONG_EFFECT_FRAMES
                if effect[0] == "wrong"
                else CORRECT_EFFECT_FRAMES
            )
        ]

    def clear_feedback(self) -> None:
        """画面遷移時に一時的な勝敗リアクションをすべて消す。"""
        self.wrong_cell = None
        self.cpu_reaction_until = 0
        self.wrong_started_frame = 0
        self.wrong_until_frame = 0
        self.correct_cell = None
        self.correct_started_frame = 0
        self.correct_until_frame = 0
        self.cell_effects = []
        self.milestone_value = 0
        self.milestone_until_frame = 0

    def add_cell_effect(self, kind: str, cell_index: int) -> None:
        """入力を妨げない描画専用エフェクトを追加する。"""
        self.cell_effects = [effect for effect in self.cell_effects if effect[1] != cell_index]
        self.cell_effects.append((kind, cell_index, pyxel.frame_count))
        self.cell_effects = self.cell_effects[-12:]

    def begin_countdown(self, mode: str) -> None:
        """盤面を伏せたまま3秒カウントし、同時スタートを準備する。"""
        self.stop_bgm()
        self.selected_mode = mode
        self.storage_saved = progress.save(self)
        self.screen = "countdown"
        self.countdown_end_frame = pyxel.frame_count + COUNTDOWN_FRAMES
        self.confirm_action = None
        self.clear_feedback()

    def start_round(self, mode: str) -> None:
        self.selected_mode = mode
        # Gameplay banks are shared; scene tracks occupy slots 46-47 and 54-63.
        # Rebuild only at a new round, never on pause/resume or stage changes.
        configure_bgm(pyxel.sounds, battle=self.play_kind == "battle")
        self.round = (BattleRound(max_number=self.selected_max_number, difficulty=self.difficulty)
                      if self.play_kind == "battle" else NumberTapRound(max_number=self.selected_max_number))
        self.round.start(mode)
        self.cursor_cell = next(i for i, n in enumerate(self.round.board_cells) if n is not None)
        self.keyboard_cursor = False
        self.screen = "playing"
        self.score = 0
        self.hint_used = False
        self.hint_until = 0
        self.streak = 0
        self.max_streak = 0
        self.is_new_best = False
        self.clear_feedback()
        self.go_until_frame = pyxel.frame_count + 30
        self.bgm_stage = 0
        self.pending_bgm_stage = None
        if self.bgm_on:
            self.start_bgm(0)
        self.play_sfx(4)

    def handle_tap(self, cell_index: int) -> None:
        number = self.round.board_cells[cell_index]
        if number in self.round.found_numbers:
            return
        result = self.round.tap(number)
        if result == "empty":
            return
        if result == "wrong":
            self.streak = 0
            self.milestone_until_frame = 0
            self.correct_cell = None
            self.correct_started_frame = 0
            self.wrong_cell = cell_index
            self.wrong_started_frame = pyxel.frame_count
            self.wrong_until_frame = pyxel.frame_count + WRONG_EFFECT_FRAMES
            self.add_cell_effect("wrong", cell_index)
            self.play_sfx(1)
            return
        if result not in {"correct", "finished"}:
            return

        self.streak += 1
        self.cpu_reaction_until = 0
        self.max_streak = max(self.max_streak, self.streak)
        self.score += correct_points(self.streak)
        self.wrong_cell = None
        self.wrong_started_frame = 0
        self.correct_cell = cell_index
        self.correct_started_frame = pyxel.frame_count
        self.correct_until_frame = pyxel.frame_count + CORRECT_EFFECT_FRAMES
        self.add_cell_effect("correct", cell_index)
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
            if isinstance(self.round, BattleRound):
                self.finish_battle()
                return
            elapsed = self.round.elapsed()
            result_key = (self.round.max_number, self.selected_mode)
            best = self.best_times.get(result_key)
            self.is_new_best = not self.hint_used and (best is None or elapsed < best)
            if self.is_new_best:
                self.best_times[result_key] = elapsed
            self.storage_saved = progress.save(self)
            self.stop_bgm()
            self.play_sfx(3, protect_frames=15)
            self.screen = "finished"
            self.result_music_after = pyxel.frame_count + (45 if self.sfx_on else 0)

    def update_battle_progress(self):
        self.pending_bgm_stage = music_stage_for_progress(
            self.round.completed_count, max_number=self.round.max_number)

    def finish_battle(self):
        if self._settled_round is self.round:
            return
        self._settled_round = self.round
        self.bonus_bank += self.round.special_bonus
        self.result_started_frame = pyxel.frame_count
        key = (self.round.max_number, self.selected_mode, self.difficulty)
        previous = self.battle_records.get(key, -1)
        self.is_new_best = self.round.player_points > previous
        self.battle_records[key] = max(previous, self.round.player_points)
        self.storage_saved = progress.save(self)
        self.stop_bgm()
        self.play_sfx(7 if self.round.is_perfect else 3 if self.round.won else 6, protect_frames=15)
        self.screen = "finished"
        self.result_music_after = pyxel.frame_count + (45 if self.sfx_on else 0)

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
            self.clear_feedback()
            self.screen = "ready"

    def cancel_confirmation(self) -> None:
        self.confirm_action = None
        self.screen = "resuming"
        self.resume_end_frame = pyxel.frame_count + 120

    def toggle_bgm(self) -> None:
        self.bgm_on = not self.bgm_on
        self.storage_saved = progress.save(self)
        if not self.bgm_on:
            self.pause_bgm()
            self.stop_scene_music()
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

    def stop_scene_music(self):
        if self.scene_music is not None:
            for channel in range(3):
                pyxel.stop(channel)
            self.scene_music = None

    def sync_scene_music(self):
        """Select once per transition, never restart a loop on every frame."""
        if not self.bgm_on or self.screen == "playing":
            self.stop_scene_music()
            return
        desired = {"ready": "menu", "confirm": "wait",
                   "help": "menu", "review": "wait",
                   "resuming": "countdown", "countdown": "countdown"}.get(self.screen)
        if self.screen == "shiritori":
            phase = self.shiritori.phase
            desired = ("win" if self.shiritori.winner == "you" else "wait" if self.shiritori.mode == "solo" else "loss") if phase == "finished" else "wait" if phase == "paused" else "menu"
        if self.screen == "finished" and pyxel.frame_count >= self.result_music_after:
            desired = ("perfect" if isinstance(self.round, BattleRound) and self.round.is_perfect
                       else "loss" if isinstance(self.round, BattleRound) and not self.round.won else "win")
        if desired == self.scene_music:
            return
        self.stop_scene_music()
        if desired is not None:
            for channel, sound in enumerate(SCENE_TRACKS[desired]):
                pyxel.play(channel, sound, loop=True)
            pyxel.stop(2)
            self.scene_music = desired

    def toggle_sfx(self) -> None:
        self.sfx_on = not self.sfx_on
        self.storage_saved = progress.save(self)
        if not self.sfx_on:
            pyxel.stop(3)
            self.sfx_priority_until_frame = 0

    @staticmethod
    def bgm_sequences(stage: int, *, battle=False) -> tuple[list[int], list[int], list[int]]:
        """全段階で和声・旋律を保ち、軽いリズムだけを加える。"""
        return music_sequences(stage, battle=battle)

    def play_bgm_channels(self, stage: int, position_frames: int) -> None:
        melody, bass, drums = self.bgm_sequences(stage, battle=isinstance(self.round, BattleRound))
        position_seconds = position_frames / FPS
        pyxel.play(0, melody, sec=position_seconds, loop=True)
        pyxel.play(1, bass, sec=position_seconds, loop=True)
        pyxel.play(2, drums, sec=position_seconds, loop=True)

    def bgm_timing(self) -> tuple[int, int]:
        """対戦曲と練習曲、それぞれのテンポに合った句・ループ長を返す。"""
        if isinstance(self.round, BattleRound):
            return BATTLE_BGM_PHRASE_FRAMES, BATTLE_BGM_LOOP_FRAMES
        return BGM_PHRASE_FRAMES, BGM_LOOP_FRAMES

    def start_bgm(
        self,
        stage: int,
        position_frames: int = 0,
        *,
        clear_pending: bool = True,
    ) -> None:
        """指定した曲位置から3パートを同期して開始する。"""
        self.stop_scene_music()
        phrase_frames, loop_frames = self.bgm_timing()
        position_frames %= loop_frames
        self.bgm_stage = stage
        if clear_pending:
            self.pending_bgm_stage = None
        self.play_bgm_channels(stage, position_frames)
        self.bgm_origin_frame = pyxel.frame_count - position_frames
        phrase_offset = position_frames % phrase_frames
        frames_to_boundary = phrase_frames - phrase_offset
        self.bgm_next_phrase_frame = pyxel.frame_count + frames_to_boundary
        self.bgm_paused_position_frames = position_frames
        self.bgm_paused = False
        self.bgm_has_started = True

    def current_bgm_position_frames(self) -> int:
        if self.bgm_paused:
            return self.bgm_paused_position_frames
        if not self.bgm_has_started:
            return 0
        _phrase_frames, loop_frames = self.bgm_timing()
        return (pyxel.frame_count - self.bgm_origin_frame) % loop_frames

    def update_bgm_transition(self) -> None:
        """進行度による編曲変更を、次の句境界まで待って適用する。"""
        if not self.bgm_on or self.bgm_paused or not self.bgm_has_started:
            return
        if pyxel.frame_count < self.bgm_next_phrase_frame:
            return
        position_frames = self.current_bgm_position_frames()
        if self.pending_bgm_stage is not None:
            # 曲中の現在位置を保ったまま編曲だけを切り替える。
            self.start_bgm(self.pending_bgm_stage, position_frames)
            return
        phrase_frames, _loop_frames = self.bgm_timing()
        phrase_offset = position_frames % phrase_frames
        self.bgm_next_phrase_frame = (
            pyxel.frame_count + phrase_frames - phrase_offset
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
        self.scene_music = None
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
        modern = getattr(self, "modern_ui", None)
        if modern is not None:
            modern.sync(self, pyxel.frame_count)
            if modern.ready:
                return
        left, right = self.character_actions()
        self.character_layer.sync(self.screen, left, right, self.reduced_motion,
                                  isinstance(self.round, BattleRound) and self.round.is_perfect,
                                  self.play_kind)
        pyxel.cls(BACKGROUND)
        self.draw_background()
        self.draw_header()
        if self.screen == "review":
            self.draw_review_panel()
            return
        if self.screen == "help":
            self.draw_box(96, 62, 448, 232, BLUE)
            centered_text(82, "HOW TO PLAY - LANTERN LEAGUE", YELLOW)
            for y, label in ((107, "FIND THE LARGE TARGET BEFORE THE FOX."),
                             (125, "FIRST CORRECT ANSWER WINS 1 POINT."),
                             (143, "REACH THE GOLD LINE: 6 / 12 / 18 / 24 POINTS."),
                             (161, "MISS? A BOMB APPEARS. YOU CAN STILL TAP THAT CELL."),
                             (179, "BLUE = YOU    PINK = CPU    EMPTY CELLS ARE IGNORED."),
                             (197, "CLICK / TAP, OR ARROW KEYS + ENTER.  ESC = PAUSE.")):
                centered_text(y, label, CARD)
            self.draw_button(YES_BUTTON, "BACK", BLUE)
            return

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
        if self.screen == "resuming":
            self.draw_box(170, 95, 300, 165, BLUE)
            centered_text(120, "RESUMING - BOARD HIDDEN", CARD)
            draw_number(320, 150, max(1, (self.resume_end_frame - pyxel.frame_count + 59) // 60), YELLOW, 8)
            return

        self.draw_progress_frame(
            self.round.completed_count,
            self.round.max_number,
        )
        self.draw_side_console()
        self.draw_game_board()
        if (self.screen == "playing" and not isinstance(self.round, BattleRound)
                and pyxel.frame_count < self.hint_until):
            index = self.round.board_cells.index(self.round.current_target)
            row, col = divmod(index, GRID_COLUMNS)
            x, y = GRID_X + col * (CELL_WIDTH + CELL_GAP), GRID_Y + row * (CELL_HEIGHT + CELL_GAP)
            pyxel.rectb(x, y, CELL_WIDTH, CELL_HEIGHT, GREEN)
            pyxel.rectb(x + 1, y + 1, CELL_WIDTH - 2, CELL_HEIGHT - 2, GREEN)
        self.draw_characters()
        if self.screen == "finished":
            self.draw_finished_panel()
            if isinstance(self.round, BattleRound):
                self.draw_button(EXTRA_BUTTON, "対戦をふりかえる  [H]", BLUE)
        else:
            self.draw_message_panel()

    @staticmethod
    def draw_background() -> None:
        # Lantern League: all decoration stays outside the searchable grid.
        for x in range(12, WIDTH, 41):
            pyxel.pset(x, 241 + x % 29, PANEL)
        for x in (19, 136, 494, 613):
            pyxel.rect(x, 275, 4, 42, 4)
            # Rounded foliage echoes the soft storybook character silhouettes.
            pyxel.elli(x - 17, 266, 37, 34, DEEP_BLUE)
            pyxel.elli(x - 13, 255, 29, 28, DEEP_BLUE)
            pyxel.elli(x - 14, 275, 23, 17, 3)
        # Two warm lamps frame the stage without flashing behind the numbers.
        for x in (24, 610):
            pyxel.rect(x - 1, 253, 2, 62, 4)
            pyxel.line(x - 8, 256, x + 8, 256, YELLOW)
            pyxel.rect(x - 6, 259, 13, 19, DEEP_BLUE)
            pyxel.rect(x - 4, 260, 9, 15, YELLOW)
            pyxel.rect(x - 2, 261, 5, 11, PEACH)
            pyxel.rect(x - 6, 276, 13, 2, 4)
        pyxel.line(18, 48, WIDTH - 19, 48, DEEP_BLUE)
        pyxel.line(18, 50, 100, 50, BLUE)
        pyxel.line(WIDTH - 101, 50, WIDTH - 19, 50, PINK)
        pyxel.rect(0, 312, WIDTH, 48, DEEP_BLUE)
        pyxel.line(0, 312, WIDTH, 312, 4)
        pyxel.line(0, 314, WIDTH, 314, PEACH)
        for y in (321, 340, 359):
            pyxel.line(0, y, WIDTH, y, PANEL)
            for x in range((y % 2) * 16, WIDTH, 48):
                pyxel.line(x, y - 6, x + 5, y - 6, PANEL)
        for x in (90, 550):
            pyxel.elli(x - 35, 332, 70, 14, PANEL)
            pyxel.ellib(x - 35, 332, 70, 14, 4)
        for x, y in ((9, 64), (626, 63), (8, 340), (628, 337)):
            pyxel.rect(x, y, 3, 3, BLUE)
            pyxel.rect(x + 3, y + 3, 3, 3, DEEP_BLUE)

    def draw_header(self) -> None:
        ui_text(pyxel, 18, 18, "N U M B E R  R U S H", YELLOW)
        if self.screen == "ready":
            ui_text(pyxel, 116, 18, f"RANGE 1-{self.selected_max_number}", MUTED)
            self.draw_small_button(RETRY_BUTTON, "HELP", BLUE, True)
        else:
            mode = "ORDER" if self.selected_mode == "ordered" else "RANDOM"
            ui_text(pyxel, 116, 18, f"{self.selected_max_number} {mode}", MUTED)
        if self.screen in {"playing", "finished"}:
            ui_text(pyxel, 188, 18, f"T {self.round.elapsed():05.1f}", CARD)
            score_label = (f"YOU {self.round.player_points}:{self.round.cpu_points}" if isinstance(self.round, BattleRound) else f"S {self.score:05d}")
            ui_text(pyxel, 242, 18, score_label, YELLOW)
            if self.screen == "playing":
                self.draw_small_button(PAUSE_BUTTON, "休憩", BLUE, True)
        if self.screen in {"playing", "countdown"}:
            self.draw_small_button(RETRY_BUTTON, "RETRY", GREEN, self.screen == "playing")
            self.draw_small_button(TITLE_BUTTON, "TITLE", BLUE, True)
        self.draw_small_button(BGM_BUTTON, "BGM ON" if self.bgm_on else "BGM OFF", GREEN, True)
        self.draw_small_button(SFX_BUTTON, "SFX ON" if self.sfx_on else "SFX OFF", PINK, True)

    def draw_progress_frame(self, completed: int, max_number: int) -> None:
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
                if isinstance(self.round, BattleRound) and self.screen in {"playing", "finished"}:
                    target = self.round.targets[index * max_number // GRID_CELL_COUNT]
                    fill = BLUE if self.round.owners.get(target) == "you" else PINK
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

            fill = DEEP_BLUE if already_found else CARD
            border = PANEL if already_found else YELLOW
            if is_hovered and not already_found:
                fill = PEACH
                border = BLUE
            if is_wrong:
                fill = ERROR
                border = CARD
            elif is_correct:
                border = BLUE

            pyxel.rect(x + 3, y + 3, CELL_WIDTH, CELL_HEIGHT, DEEP_BLUE)
            pyxel.rect(x, y, CELL_WIDTH, CELL_HEIGHT, fill)
            pyxel.rectb(x, y, CELL_WIDTH, CELL_HEIGHT, border)
            pyxel.rectb(x + 2, y + 2, CELL_WIDTH - 4, CELL_HEIGHT - 4, border)

            if already_found:
                self.draw_locked_pattern(x, y)
                owner = self.round.owners.get(number, "you") if isinstance(self.round, BattleRound) else "you"
                owner_color = BLUE if owner == "you" else PINK
                pyxel.rectb(x, y, CELL_WIDTH, CELL_HEIGHT, owner_color)
                ui_text(pyxel, x + 4, y + 4, owner.upper(), owner_color)
            else:
                pyxel.line(x + 4, y + 3, x + CELL_WIDTH - 5, y + 3, CARD)
                pyxel.line(x + 4, y + CELL_HEIGHT - 4, x + CELL_WIDTH - 5, y + CELL_HEIGHT - 4, PRESSED)
                draw_number(
                    x + CELL_WIDTH // 2,
                    y + (CELL_HEIGHT - 21) // 2,
                    number,
                    CARD if is_wrong else BACKGROUND,
                )
        # Thin corner brackets leave the digits readable, even when cursors overlap.
        if self.screen == "playing":
            player_index = self.cursor_cell if self.keyboard_cursor else self.cell_at(pyxel.mouse_x, pyxel.mouse_y)
            if player_index is not None:
                self.draw_cursor(player_index, BLUE, 0)
            if isinstance(self.round, BattleRound):
                cpu_index = self.round.cpu_cursor
                if cpu_index is not None:
                    self.draw_cursor(cpu_index, PINK, 2)
        self.draw_cell_effects()

    @staticmethod
    def draw_cursor(index, color, inset):
        row, col = divmod(index, GRID_COLUMNS)
        x = GRID_X + col * (CELL_WIDTH + CELL_GAP) + inset
        y = GRID_Y + row * (CELL_HEIGHT + CELL_GAP) + inset
        w, h = CELL_WIDTH - inset * 2, CELL_HEIGHT - inset * 2
        for xx, dx in ((x, 1), (x + w - 1, -1)):
            for yy, dy in ((y, 1), (y + h - 1, -1)):
                pyxel.line(xx, yy, xx + dx * 8, yy, color)
                pyxel.line(xx, yy, xx, yy + dy * 7, color)

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
        ui_text(pyxel, x + 21, y + 14, "--", MUTED)

    @staticmethod
    def draw_locked_pattern(x: int, y: int) -> None:
        for offset_y in range(7, CELL_HEIGHT - 5, 7):
            for offset_x in range(7, CELL_WIDTH - 5, 7):
                color = MUTED if (offset_x + offset_y) % 2 else PANEL
                pyxel.rect(x + offset_x, y + offset_y, 3, 3, color)

    def draw_cell_effects(self) -> None:
        if self.reduced_motion:
            for kind, index, _ in self.cell_effects:
                row, col = divmod(index, GRID_COLUMNS)
                x = GRID_X + col * (CELL_WIDTH + CELL_GAP)
                y = GRID_Y + row * (CELL_HEIGHT + CELL_GAP)
                if kind == "wrong":
                    self.draw_bomb_explosion(x, y, 16)
                else:
                    self.draw_success_effect(x, y, 8)
            return
        """全セルの上に正解光と爆弾・爆発を重ねて描く。"""
        for kind, cell_index, started_frame in self.cell_effects:
            row, column = divmod(cell_index, GRID_COLUMNS)
            x = GRID_X + column * (CELL_WIDTH + CELL_GAP)
            y = GRID_Y + row * (CELL_HEIGHT + CELL_GAP)
            age = max(0, pyxel.frame_count - started_frame)
            if kind == "wrong":
                self.draw_bomb_explosion(x, y, age)
            elif kind == "cpu":
                pyxel.rectb(x - 1, y - 1, CELL_WIDTH + 2, CELL_HEIGHT + 2, PINK)
                ui_text(pyxel, x + 15, y + 14, "CPU +1", CARD)
            else:
                self.draw_success_effect(x, y, age)
                t = min(1.0, age / CORRECT_EFFECT_FRAMES)
                pyxel.circ(int((x + CELL_WIDTH // 2) * (1 - t) + 43 * t),
                           int(y * (1 - t) + 190 * t - 22 * math.sin(t * math.pi)), 2, YELLOW)

    @staticmethod
    def draw_bomb_explosion(x: int, y: int, age: int) -> None:
        """爆弾化、爆発、煙の3段階エフェクトを描く。"""
        if age >= WRONG_EFFECT_FRAMES:
            return
        center_x = x + CELL_WIDTH // 2
        center_y = y + CELL_HEIGHT // 2

        if age < BOMB_FUSE_FRAMES:
            pulse = (age // 2) % 2
            pyxel.circ(center_x, center_y + 2, 7 + pulse, PANEL)
            pyxel.circb(center_x, center_y + 2, 7 + pulse, CARD)
            pyxel.rect(center_x - 2, center_y - 8, 5, 4, PANEL)
            pyxel.line(
                center_x + 2,
                center_y - 7,
                center_x + 8,
                center_y - 12,
                CARD,
            )
            spark_color = CARD if pulse else YELLOW
            pyxel.line(center_x + 7, center_y - 13, center_x + 11, center_y - 13, spark_color)
            pyxel.line(center_x + 9, center_y - 15, center_x + 9, center_y - 11, spark_color)
            pyxel.pset(center_x + 12, center_y - 16, ERROR)
            ui_text(pyxel, x + 3, y + 3, "BOMB", CARD)
            return

        if age < EXPLOSION_END_FRAME:
            blast_age = age - BOMB_FUSE_FRAMES
            radius = max(3, int(15 * math.sin(math.pi * (blast_age + 1) / 21)))
            reach = min(17, radius + 3)
            pyxel.line(center_x - reach, center_y, center_x + reach, center_y, YELLOW)
            pyxel.line(center_x, center_y - reach, center_x, center_y + reach, YELLOW)
            diagonal = max(5, reach * 2 // 3)
            pyxel.line(
                center_x - diagonal,
                center_y - diagonal,
                center_x + diagonal,
                center_y + diagonal,
                ERROR,
            )
            pyxel.line(
                center_x + diagonal,
                center_y - diagonal,
                center_x - diagonal,
                center_y + diagonal,
                ERROR,
            )
            pyxel.circ(center_x, center_y, radius, ERROR)
            pyxel.circ(center_x, center_y, max(3, radius - 5), YELLOW)
            pyxel.circ(center_x, center_y, max(1, radius - 10), CARD)
            return

        smoke_age = age - EXPLOSION_END_FRAME
        rise = smoke_age // 3
        smoke_radius = max(1, 4 - smoke_age // 6)
        smoke_clouds = ((-10, 4), (-2, -1), (8, 3), (4, -5))
        for index, (offset_x, offset_y) in enumerate(smoke_clouds):
            drift = -1 if index % 2 else 1
            pyxel.circ(
                center_x + offset_x + drift * rise,
                center_y + offset_y - rise,
                smoke_radius,
                MUTED if index % 2 else PANEL,
            )
        shard_distance = 8 + smoke_age // 2
        pyxel.pset(center_x - shard_distance, center_y + 6, ERROR)
        pyxel.pset(center_x + shard_distance, center_y + 3, YELLOW)
        pyxel.pset(center_x - 4, center_y - shard_distance // 2, CARD)

    @staticmethod
    def draw_success_effect(x: int, y: int, age: int) -> None:
        """正解を示す発光枠、チェック、火花を描く。"""
        if age >= CORRECT_EFFECT_FRAMES:
            return

        center_x = x + CELL_WIDTH // 2
        center_y = y + CELL_HEIGHT // 2
        ring_radius = min(15, 5 + age // 2)
        pyxel.circb(center_x, center_y, ring_radius, BLUE)
        if age < 8:
            flash_color = CARD if age < 3 else BLUE
            pyxel.rectb(x - 2, y - 2, CELL_WIDTH + 4, CELL_HEIGHT + 4, flash_color)
            pyxel.rectb(x + 1, y + 1, CELL_WIDTH - 2, CELL_HEIGHT - 2, YELLOW)

        if age < 23:
            reach = 6 + age // 2
            pyxel.line(center_x, center_y - reach, center_x, center_y - 4, GREEN)
            pyxel.line(center_x, center_y + 4, center_x, center_y + reach, GREEN)
            pyxel.line(center_x - reach, center_y, center_x - 5, center_y, GREEN)
            pyxel.line(center_x + 5, center_y, center_x + reach, center_y, GREEN)
            pyxel.line(center_x - 9, center_y, center_x - 2, center_y + 7, CARD)
            pyxel.line(center_x - 2, center_y + 7, center_x + 11, center_y - 8, CARD)

        spark_age = max(0, age - 8)
        for index, (direction_x, direction_y) in enumerate(
            ((-2, -1), (-1, 2), (1, -2), (2, 1), (-2, 1), (2, -1))
        ):
            distance = min(15, 5 + spark_age // 2)
            spark_x = center_x + direction_x * distance // 2
            spark_y = center_y + direction_y * distance // 2
            pyxel.pset(spark_x, spark_y, YELLOW if index % 2 else GREEN)

    def character_actions(self) -> tuple[str, str]:
        """左プレイヤーと右CPUへ、互いに逆のリアクションを返す。"""
        if self.screen == "finished":
            if isinstance(getattr(self, "round", None), BattleRound) and not self.round.won:
                return "defeat", "victory"
            return "victory", "defeat"
        if pyxel.frame_count < getattr(self, "cpu_reaction_until", 0):
            return "frustrated", "celebrate"
        if self.wrong_cell is not None:
            return "hurt", "celebrate"
        if self.correct_cell is not None:
            return "celebrate", "frustrated"
        if pyxel.frame_count < self.milestone_until_frame:
            return "celebrate", "frustrated"
        return "idle", "idle"

    def draw_characters(self) -> None:
        if self.character_layer.ready:
            return
        player_action, cpu_action = self.character_actions()
        bob = (pyxel.frame_count // 18) % 2
        reaction_tick = (pyxel.frame_count // 4) % 2
        jump = round(6 * abs(math.sin(pyxel.frame_count * math.pi / 18)))
        player_jump = jump if player_action in {"celebrate", "victory"} else 0
        cpu_jump = jump if cpu_action == "celebrate" else 0
        player_shake = (2 if reaction_tick else -2) if player_action in {"hurt", "frustrated"} else 0
        cpu_shake = (2 if reaction_tick else -2) if cpu_action == "frustrated" else 0
        cpu_slump = 3 if cpu_action == "defeat" else 0
        if self.reduced_motion:
            bob = player_jump = cpu_jump = player_shake = cpu_shake = 0
        if (self.screen == "finished" and isinstance(getattr(self, "round", None), BattleRound)
                and self.round.is_perfect):
            # A personal gold halo makes this distinct from the ordinary crown.
            pyxel.circb(89, 307, 27, YELLOW)
            for i in range(8):
                angle = i * math.pi / 4 + (0 if self.reduced_motion else pyxel.frame_count / 90)
                sx = round(89 + 26 * math.cos(angle))
                sy = round(307 + 26 * math.sin(angle))
                pyxel.line(sx - 2, sy, sx + 2, sy, YELLOW)
                pyxel.line(sx, sy - 2, sx, sy + 2, YELLOW)
        pyxel.ellib(65, 335, 46, 5, DEEP_BLUE)
        pyxel.ellib(526, 334, 48, 5, DEEP_BLUE)

        pyxel.rect(61, 252, 56, 14, PANEL)
        pyxel.rectb(61, 252, 56, 14, BLUE)
        ui_text(pyxel, 69, 257, "RIN / YOU", BLUE)
        pyxel.rect(523, 252, 56, 14, PANEL)
        pyxel.rectb(523, 252, 56, 14, PINK)
        ui_text(pyxel, 531, 257, "KOH / CPU", PINK)

        if player_action == "celebrate":
            ui_text(pyxel, 78, 270, "NICE!", BLUE)
        elif player_action == "hurt":
            ui_text(pyxel, 78, 270, "OUCH!", BLUE)
        elif player_action == "victory":
            ui_text(pyxel, 78, 270, "WIN!", YELLOW)
        elif player_action == "frustrated":
            ui_text(pyxel, 72, 270, "TOO SLOW!", BLUE)
        if cpu_action == "celebrate":
            ui_text(pyxel, 545, 270, "HA!", PINK)
        elif cpu_action == "frustrated":
            ui_text(pyxel, 537, 270, "GRR...", ERROR)
        elif cpu_action == "defeat":
            ui_text(pyxel, 539, 270, "OH NO", MUTED)
        elif self.screen == "playing" and isinstance(self.round, BattleRound):
            ui_text(pyxel, 534, 270, "SEARCH" + "." * (1 + pyxel.frame_count // 20 % 3), PINK)

        self.draw_rabbit(
            58 + player_shake,
            282 - bob - player_jump,
            player_action,
        )
        self.draw_red_panda(
            518 + cpu_shake,
            280 - bob - cpu_jump + cpu_slump,
            cpu_action,
        )

    def draw_rabbit(self, x: int, y: int, action: str) -> None:
        draw_rival(pyxel, x, y, "rabbit", action, motion=not self.reduced_motion)

    def draw_red_panda(self, x: int, y: int, action: str) -> None:
        draw_rival(pyxel, x, y, "red_panda", action, motion=not self.reduced_motion)

    def draw_side_console(self) -> None:
        if isinstance(self.round, BattleRound):
            for x, points, label, color in ((24, self.round.player_points, "YOU", BLUE),
                                           (579, self.round.cpu_points, "CPU", PINK)):
                self.draw_box(x, 58, 38, 172, color)
                ui_text(pyxel, x + 12, 69, label, color)
                pyxel.rect(x + 12, 91, 14, 104, DEEP_BLUE)
                height = int(104 * points / self.round.max_number)
                pyxel.rect(x + 12, 195 - height, 14, height, color)
                draw_number(x + 19, 207, points, color, 2)
                if label == "YOU":
                    goal_y = 195 - int(104 * self.round.goal / self.round.max_number)
                    pyxel.line(x + 7, goal_y, x + 34, goal_y, YELLOW)
                    pyxel.tri(x + 36, goal_y, x + 42, goal_y - 3, x + 42, goal_y + 3, YELLOW)
            return
        self.draw_box(38, 58, 40, 174, BLUE)
        ui_text(pyxel, 48, 68, "SCAN", YELLOW)
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
        ui_text(pyxel,
            42,
            207,
            f"{self.round.completed_count:02d}/{self.round.max_number:02d}",
            CARD,
        )
        ui_text(pyxel, 46, 220, "FOUND", MUTED)

        self.draw_box(570, 58, 62, 174, GREEN)
        ui_text(pyxel, 589, 68, "ENERGY", YELLOW)
        pyxel.rect(581, 88, 40, 112, DEEP_BLUE)
        energy_height = int(
            108 * self.round.completed_count / self.round.max_number
        )
        pyxel.rect(583, 198 - energy_height, 36, energy_height, GREEN)
        for line_y in range(94, 198, 12):
            pyxel.line(583, line_y, 618, line_y, PANEL)
        pyxel.rectb(581, 88, 40, 112, CARD)
        ui_text(pyxel, 584, 208, f"LEVEL {self.bgm_stage + 1}", CARD)
        ui_text(pyxel, 585, 220, "DRIVE", MUTED)

    def draw_message_panel(self) -> None:
        if isinstance(self.round, BattleRound):
            self.draw_box(158, 250, 324, 94, YELLOW)
            ui_text(pyxel, 183, 270, "ちがうよ" if self.wrong_cell is not None else "さがすのは", ERROR if self.wrong_cell is not None else YELLOW)
            draw_number(320, 260, self.round.current_target, CARD, 5)
            ui_text(pyxel, 383, 270, "を先に!", YELLOW)
            # Show the last claim beside, never instead of, the live target.
            if self.correct_cell is not None or pyxel.frame_count < self.cpu_reaction_until:
                owner = self.round.last_owner
                response = self.round.last_response
                detail = f"{'YOU' if owner == 'you' else 'CPU'} +1"
                if response is not None:
                    detail += f" / {response:.2f}s"
                ui_text(pyxel, 175, 291, detail, BLUE if owner == "you" else PINK)
            duration = max(0.01, self.round.cpu_at - self.round.ready_at)
            progress = min(1, max(0, (self.round.elapsed() - self.round.ready_at) / duration))
            ui_text(pyxel, 170, 306, "CPU接近", PINK)
            ui_text(pyxel, 390, 292, f"あと{max(0, self.round.cpu_at - self.round.elapsed()):.1f}秒", PINK)
            pyxel.rect(238, 306, 210, 5, DEEP_BLUE)
            pyxel.rect(238, 306, int(210 * progress), 5, PINK)
            if self.round.won:
                status = "勝利ライン到達! 最後まで記録を伸ばそう"
            elif not self.round.can_still_win:
                status = f"ここからは自己ベストに挑戦 / 現在{self.round.player_points}点"
            else:
                status = f"勝利まで あと{self.round.points_needed}点 / 残り{self.round.max_number - self.round.completed_count}問"
            centered_text(326, status, YELLOW)
            return
        if self.wrong_cell is not None:
            border = ERROR
        elif self.correct_cell is not None:
            border = GREEN
        else:
            border = BLUE
        self.draw_box(170, 250, 300, 94, border)
        target = self.round.current_target or self.round.max_number

        ui_text(pyxel, 190, 269, "さがすのは", MUTED)
        draw_number(320, 260, target, CARD, scale=5)
        ui_text(pyxel, 381, 274, "!", YELLOW)

        self.draw_small_button(HINT_BUTTON, "ヒント [H]", BLUE, True)
        ui_text(pyxel, 310, 305, "ヒント利用は記録対象外", MUTED)
        ui_text(pyxel, 310, 320, f"発見 {self.round.completed_count}/{self.round.max_number} / ミス {self.round.mistakes}", GREEN)

    def draw_ready_panel(self) -> None:
        self.draw_box(112, 54, 416, 222, BLUE)
        centered_text(63, "NUMBER RUSH - LANTERN LEAGUE", YELLOW)
        for kind, button in PLAY_BUTTONS.items():
            self.draw_button(button, "CPU DUEL" if kind == "battle" else "SOLO PRACTICE", BLUE, selected=self.play_kind == kind)
        centered_text(114, "CHOOSE NUMBER RANGE", CARD)
        for max_number, button in RANGE_BUTTONS.items():
            self.draw_button(
                button,
                f"1-{max_number}",
                BLUE,
                selected=max_number == self.selected_max_number,
            )
        for difficulty, button in DIFFICULTY_BUTTONS.items():
            self.draw_button(button, {"easy": "ゆっくり", "normal": "ふつう", "hard": "てごわい"}[difficulty], PINK if self.play_kind == "battle" else MUTED,
                             selected=self.play_kind == "battle" and difficulty == self.difficulty)
        self.draw_button(EXTRA_BUTTON, "演出ひかえめ: ON" if self.reduced_motion else "演出ひかえめ: OFF", MUTED)
        self.draw_button(ORDER_BUTTON, "START ORDER", GREEN)
        self.draw_button(RANDOM_BUTTON, "START RANDOM", BLUE)
        centered_text(260, "FIRST TO FIND = 1 POINT. REACH 60% TO WIN." if self.play_kind == "battle" else "NO CPU. FIND EVERY NUMBER AT YOUR OWN PACE.", MUTED)

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
        if self.confirm_action == "pause":
            centered_text(116, "PAUSED - TAKE YOUR TIME", YELLOW)
            centered_text(151, "CPU AND TIMER ARE STOPPED", CARD)
            centered_text(177, "RESUME WHEN YOU ARE READY", MUTED)
            self.draw_button(YES_BUTTON, "RESUME", BLUE)
            self.draw_button(NO_BUTTON, "TITLE", PINK)
            return
        question = "RESTART THIS RUN?" if self.confirm_action == "retry" else "RETURN TO TITLE?"
        centered_text(116, "CONFIRM", YELLOW)
        centered_text(149, question, CARD)
        centered_text(177, "TIMER PAUSED / BOARD HIDDEN", MUTED)
        self.draw_button(YES_BUTTON, "YES", GREEN)
        self.draw_button(NO_BUTTON, "NO", ERROR)
        ui_text(pyxel, 238, 282, "KEY Y", MUTED)
        ui_text(pyxel, 369, 282, "KEY N", MUTED)

    def draw_finished_panel(self) -> None:
        if isinstance(self.round, BattleRound):
            if self.round.is_perfect:
                self.draw_perfect_panel()
                return
            color = GREEN if self.round.won else PINK
            self.draw_box(118, 62, 404, 214, color)
            label = "YOU WIN" if self.round.won else "CPU WINS"
            pixel_label((WIDTH - len(label) * 12) // 2, 80, label, color)
            centered_text(110, f"1-{self.round.max_number} / {self.selected_mode.upper()} / {self.difficulty.upper()}", MUTED)
            centered_text(133, f"あなた {self.round.player_points} : {self.round.cpu_points} CPU / 勝利ライン {self.round.goal}点", YELLOW)
            avg = (f"{sum(self.round.response_times) / len(self.round.response_times):.2f}s" if self.round.response_times else "--")
            centered_text(154, f"時間 {self.round.elapsed():.2f}秒 / 平均発見 {avg}", CARD)
            centered_text(176, f"ミス {self.round.mistakes}回 / 最高連続 {self.max_streak}回", CARD)
            key = (self.round.max_number, self.selected_mode, self.difficulty)
            centered_text(197, f"最高記録 {self.battle_records.get(key, 0)} 点", color)
            self.draw_button(REPLAY_BUTTON, "PLAY AGAIN", GREEN)
            self.draw_button(MODE_BUTTON, "MODE SELECT", BLUE)
            return
        pyxel.dither(0.85)
        pyxel.rect(112, 67, 416, 214, DEEP_BLUE)
        pyxel.dither(1.0)
        self.draw_box(118, 62, 404, 214, GREEN)
        mode = "ORDER MODE" if self.selected_mode == "ordered" else "RANDOM MODE"
        mode_label = f"1-{self.round.max_number} / {mode}"
        centered_text(92, "SCAN COMPLETE", GREEN)
        centered_text(112, mode_label, YELLOW)
        centered_text(137, f"時間 {self.round.elapsed():.2f}秒 / スコア {self.score}", CARD)
        centered_text(157, f"ミス {self.round.mistakes}回 / 最高連続 {self.max_streak}回", CARD)
        best = self.best_times.get((self.round.max_number, self.selected_mode))
        if self.hint_used:
            centered_text(181, "ヒント使用のため記録対象外 / 練習おつかれさま!", YELLOW)
        elif self.is_new_best:
            centered_text(181, f"新記録!  {best:.2f}秒", PINK)
        elif best is not None:
            centered_text(181, f"最高記録  {best:.2f}s", MUTED)
        self.draw_button(REPLAY_BUTTON, "PLAY AGAIN", GREEN)
        self.draw_button(MODE_BUTTON, "MODE SELECT", BLUE)
        ui_text(pyxel, 196, 282, "SPACE", MUTED)
        ui_text(pyxel, 430, 282, "KEY M", MUTED)

    def draw_review_panel(self):
        self.draw_box(96, 62, 448, 256, BLUE)
        centered_text(76, "対戦レポート / 次の一戦につなげよう", YELLOW)
        history = self.round.history
        centered_text(98, "青=あなた  桃=CPU / 棒は発見までの秒数", CARD)
        maximum = max((item["seconds"] for item in history), default=1) or 1
        width = 400 / max(1, len(history))
        for i, item in enumerate(history):
            x = 120 + int(i * width)
            height = int(62 * item["seconds"] / maximum)
            pyxel.rect(x, 185 - height, max(2, int(width) - 2), height,
                       BLUE if item["owner"] == "you" else PINK)
            ui_text(pyxel, x, 188, str(item["number"]), CARD)
            ui_text(pyxel, x, 198, "Y" if item["owner"] == "you" else "C", MUTED)
        owned = [item for item in history if item["owner"] == "you"]
        if owned:
            fastest = min(owned, key=lambda item: item["seconds"])
            centered_text(218, f'最速発見 {fastest["number"]} / {fastest["seconds"]:.2f}秒', GREEN)
        else:
            centered_text(218, "まずは練習か「ゆっくり」でリズムをつかもう", GREEN)
        advice = ("ミスを減らすには、お題を確認してから押そう" if self.round.mistakes
                  else "行ごとに探すと、見落としを減らせるよ")
        centered_text(239, advice, CARD)
        centered_text(257, "記録はこのブラウザに保存済み" if self.storage_saved else "保存不可: この起動中のみ記録を保持", MUTED)
        self.draw_button(EXTRA_BUTTON, "結果に戻る", BLUE)

    def draw_perfect_panel(self) -> None:
        """A skippable celebration: awards settle once, drawing only animates."""
        age = max(0, pyxel.frame_count - self.result_started_frame)
        self.draw_box(118, 62, 404, 214, YELLOW)
        # Confetti stays in side gutters, outside all text and action buttons.
        if age < 300 and not self.reduced_motion:
            for i in range(30):
                side = i % 2
                x = (121 if side == 0 else 491) + (i * 7 % 24)
                y = 68 + (i * 29 + age * (1 + i % 3)) % 144
                pyxel.rect(x, y, 2 + i % 2, 2, (YELLOW, BLUE, PINK, CARD)[i % 4])
        pixel_label(278, 78, "PERFECT", YELLOW)
        centered_text(101, f"全{self.round.max_number}問を獲得 / ノーミス!", CARD)
        centered_text(117, f"YOU {self.round.player_points} : 0 CPU / {self.difficulty.upper()}", BLUE)
        # A gold trophy on either side of the title, plus Milo's victory crown.
        for x in (170, 458):
            pyxel.rectb(x - 5, 80, 20, 10, YELLOW)
            pyxel.rect(x - 1, 77, 12, 14, YELLOW)
            pyxel.rect(x + 4, 90, 3, 9, YELLOW)
            pyxel.rect(x - 3, 99, 16, 3, YELLOW)
            pyxel.line(x + 1, 79, x + 1, 86, CARD)
        pyxel.rect(182, 131, 276, 41, DEEP_BLUE)
        pyxel.rectb(182, 131, 276, 41, YELLOW)
        centered_text(136, "SPECIAL BONUS", YELLOW)
        amount = self.round.special_bonus
        shown = amount if self.reduced_motion else min(amount, amount * age // 90)
        pixel_label(290, 149, f"+{shown:04d}", YELLOW)
        centered_text(181, f"累計ボーナス {self.bonus_bank}  /  勝敗の点数とは別", CARD)
        centered_text(196, f"時間 {self.round.elapsed():.2f}秒 / 最高連続 {self.max_streak}回", MUTED)
        centered_text(211, f"1-{self.round.max_number} / {self.selected_mode.upper()} / PERFECT AWARD", BLUE)
        self.draw_button(REPLAY_BUTTON, "PLAY AGAIN", GREEN)
        self.draw_button(MODE_BUTTON, "MODE SELECT", BLUE)

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
        ui_text(pyxel,
            x + (width - text_width(label)) // 2,
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
        ui_text(pyxel, x + (width - text_width(label)) // 2, y + 13, label, color)


if __name__ == "__main__":
    NumberRush()
