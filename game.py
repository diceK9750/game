# title: Number Rush
# author: diceK9750 / Codex
# desc: Find 1 to 10, 20, 30, or 40 in order or in a shuffled sequence.
# site: https://dicek9750.github.io/game/
# version: 7.1

"""横持ちブラウザ向けの数字タップゲーム NUMBER RUSH。"""

from __future__ import annotations

import pyxel
import math
from music import configure_bgm, sequences as music_sequences

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

COUNTDOWN_FRAMES = 180
WRONG_EFFECT_FRAMES = 48
BOMB_FUSE_FRAMES = 10
EXPLOSION_END_FRAME = 30
CORRECT_EFFECT_FRAMES = 34
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

# 暗い筐体と明るい数字を分離した専用パレット。
PALETTE = [
    0x090E19, 0x142339, 0x714260, 0x327568,
    0xB37649, 0x283B52, 0x70869A, 0xF1F6ED,
    0xF15D65, 0xF29D52, 0xFFD166, 0x62DFB3,
    0x66BEF3, 0x91A8BD, 0xEB91BC, 0xFFE4B7,
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
        pyxel.colors.from_list(PALETTE)
        pyxel.mouse(True)
        self.configure_sounds()
        self.selected_max_number = 40
        self.round = NumberTapRound(max_number=self.selected_max_number)
        self.screen = "ready"
        self.selected_mode = "ordered"
        self.play_kind = "battle"
        self.difficulty = "normal"
        self.cpu_reaction_until = 0
        self.resume_end_frame = 0
        self.battle_records = {}
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
        """効果音と柔らかなオリジナルBGMを登録する。"""
        pyxel.sounds[0].set("d3f3a3", "p", "677", "nnf", 4)
        pyxel.sounds[1].set("c2c1", "n", "76", "ff", 5)
        pyxel.sounds[2].set("d3a3d4f4", "p", "6677", "nnnv", 5)
        pyxel.sounds[3].set("d3f3a3d4f4a4", "ps", "667777", "nnnnvf", 5)
        pyxel.sounds[4].set("a2d3f3a3", "p", "4567", "nssn", 5)
        pyxel.sounds[5].set("a3f3d3a2", "t", "5543", "nnnf", 6)
        pyxel.sounds[6].set("d3c3a2f2d2", "t", "55443", "nnnnf", 9)

        configure_bgm(pyxel.sounds)

    def update(self) -> None:
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

        if self.screen == "ready":
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

        if clicked:
            cell_index = self.cell_at(*mouse)
            if cell_index is not None:
                self.handle_tap(cell_index)
        # 入力を先に判定し、同一フレームの競合はプレイヤー優先にする。
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
        self.screen = "countdown"
        self.countdown_end_frame = pyxel.frame_count + COUNTDOWN_FRAMES
        self.confirm_action = None
        self.clear_feedback()

    def start_round(self, mode: str) -> None:
        self.selected_mode = mode
        self.round = (BattleRound(max_number=self.selected_max_number, difficulty=self.difficulty)
                      if self.play_kind == "battle" else NumberTapRound(max_number=self.selected_max_number))
        self.round.start(mode)
        self.screen = "playing"
        self.score = 0
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
            self.is_new_best = best is None or elapsed < best
            if self.is_new_best:
                self.best_times[result_key] = elapsed
            self.stop_bgm()
            self.play_sfx(3, protect_frames=15)
            self.screen = "finished"

    def update_battle_progress(self):
        self.pending_bgm_stage = music_stage_for_progress(
            self.round.completed_count, max_number=self.round.max_number)

    def finish_battle(self):
        key = (self.round.max_number, self.selected_mode, self.difficulty)
        previous = self.battle_records.get(key, -1)
        self.is_new_best = self.round.player_points > previous
        self.battle_records[key] = max(previous, self.round.player_points)
        self.stop_bgm()
        self.play_sfx(3 if self.round.won else 6, protect_frames=15)
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
            self.clear_feedback()
            self.screen = "ready"

    def cancel_confirmation(self) -> None:
        self.confirm_action = None
        self.screen = "resuming"
        self.resume_end_frame = pyxel.frame_count + 120

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
        """全段階で和声・旋律を保ち、軽いリズムだけを加える。"""
        return music_sequences(stage)

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
        self.draw_characters()
        if self.screen == "finished":
            self.draw_finished_panel()
        else:
            self.draw_message_panel()

    @staticmethod
    def draw_background() -> None:
        # オリジナルの夜の森。盤面領域には模様を置かない。
        for x in range(8, WIDTH, 43):
            pyxel.pset(x, 247 + x % 31, MUTED)
        for x in (20, 130, 493, 610):
            pyxel.rect(x, 280, 5, 32, 4)
            pyxel.tri(x - 17, 294, x + 2, 260, x + 22, 294, 3)
            pyxel.tri(x - 13, 281, x + 2, 252, x + 18, 281, DEEP_BLUE)
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
            score_label = (f"YOU {self.round.player_points}:{self.round.cpu_points}" if isinstance(self.round, BattleRound) else f"S {self.score:05d}")
            pyxel.text(242, 18, score_label, YELLOW)
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
                owner = self.round.owners.get(number, "you") if isinstance(self.round, BattleRound) else "you"
                owner_color = GREEN if owner == "you" else PINK
                pyxel.rectb(x, y, CELL_WIDTH, CELL_HEIGHT, owner_color)
                pyxel.text(x + 4, y + 4, owner.upper(), owner_color)
            else:
                pyxel.line(x + 4, y + 3, x + CELL_WIDTH - 5, y + 3, CARD)
                pyxel.line(x + 4, y + CELL_HEIGHT - 4, x + CELL_WIDTH - 5, y + CELL_HEIGHT - 4, PRESSED)
                draw_number(
                    x + CELL_WIDTH // 2,
                    y + (CELL_HEIGHT - 21) // 2,
                    number,
                    CARD if is_wrong else BACKGROUND,
                )
        self.draw_cell_effects()

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

    def draw_cell_effects(self) -> None:
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
                pyxel.text(x + 15, y + 14, "CPU +1", CARD)
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
            pyxel.text(x + 3, y + 3, "BOMB", CARD)
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
        pyxel.circb(center_x, center_y, ring_radius, GREEN)
        if age < 8:
            flash_color = CARD if (age // 2) % 2 else GREEN
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
                return "hurt", "celebrate"
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
        player_action, cpu_action = self.character_actions()
        bob = (pyxel.frame_count // 18) % 2
        reaction_tick = (pyxel.frame_count // 4) % 2
        jump = round(6 * abs(math.sin(pyxel.frame_count * math.pi / 18)))
        player_jump = jump if player_action in {"celebrate", "victory"} else 0
        cpu_jump = jump if cpu_action == "celebrate" else 0
        player_shake = (2 if reaction_tick else -2) if player_action in {"hurt", "frustrated"} else 0
        cpu_shake = (2 if reaction_tick else -2) if cpu_action == "frustrated" else 0
        cpu_slump = 3 if cpu_action == "defeat" else 0
        pyxel.ellib(65, 335, 46, 5, DEEP_BLUE)
        pyxel.ellib(526, 334, 48, 5, DEEP_BLUE)

        pyxel.rect(61, 252, 56, 14, PANEL)
        pyxel.rectb(61, 252, 56, 14, GREEN)
        pyxel.text(83, 257, "YOU", GREEN)
        pyxel.rect(523, 252, 56, 14, PANEL)
        pyxel.rectb(523, 252, 56, 14, ERROR)
        pyxel.text(545, 257, "CPU", ERROR)

        if player_action == "celebrate":
            pyxel.text(78, 270, "NICE!", GREEN)
        elif player_action == "hurt":
            pyxel.text(78, 270, "OUCH!", BLUE)
        elif player_action == "victory":
            pyxel.text(78, 270, "WIN!", YELLOW)
        elif player_action == "frustrated":
            pyxel.text(72, 270, "TOO SLOW!", BLUE)
        if cpu_action == "celebrate":
            pyxel.text(545, 270, "HA!", PINK)
        elif cpu_action == "frustrated":
            pyxel.text(537, 270, "GRR...", ERROR)
        elif cpu_action == "defeat":
            pyxel.text(539, 270, "OH NO", MUTED)
        elif self.screen == "playing" and isinstance(self.round, BattleRound):
            pyxel.text(534, 270, "SEARCH" + "." * (1 + pyxel.frame_count // 20 % 3), PINK)

        self.draw_otter(
            58 + player_shake,
            282 - bob - player_jump,
            player_action,
        )
        self.draw_fox(
            518 + cpu_shake,
            280 - bob - cpu_jump + cpu_slump,
            cpu_action,
        )

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
        pyxel.circ(x + 27, y + 12, 7, BLUE)
        pyxel.circ(x + 29, y + 14, 7, GREEN)
        pyxel.circ(x + 31, y + 23, 8, PEACH)
        pyxel.rect(x + 29, y + 19, 5, 4, PANEL)

        if blink or action in {"hurt", "frustrated"}:
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

        if action in {"celebrate", "victory"}:
            pyxel.line(x + 20, y + 34, x + 10, y + 25, GREEN)
            pyxel.line(x + 42, y + 34, x + 52, y + 24, GREEN)
            pyxel.circ(x + 9, y + 24, 3, GREEN)
            pyxel.circ(x + 53, y + 23, 3, GREEN)
            pyxel.pset(x + 5, y + 17, YELLOW)
            pyxel.pset(x + 57, y + 16, YELLOW)
            pyxel.line(x + 27, y + 25, x + 31, y + 27, PANEL)
            pyxel.line(x + 31, y + 27, x + 35, y + 25, PANEL)
        else:
            pyxel.line(x + 21, y + 35, x + 13, y + 42, GREEN)
            pyxel.line(x + 41, y + 35, x + 49, y + 42, GREEN)
        if action in {"hurt", "frustrated"}:
            pyxel.tri(x + 47, y + 9, x + 51, y + 15, x + 43, y + 15, BLUE)
            pyxel.line(x + 28, y + 27, x + 31, y + 25, PANEL)
            pyxel.line(x + 31, y + 25, x + 34, y + 27, PANEL)
        elif action == "victory":
            pyxel.line(x + 3, y + 6, x + 8, y + 6, YELLOW)
            pyxel.line(x + 5, y + 4, x + 5, y + 9, YELLOW)
            pyxel.line(x + 55, y + 4, x + 60, y + 4, CARD)
            pyxel.line(x + 57, y + 2, x + 57, y + 7, CARD)

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
        pyxel.circ(x + 27, y + 12, 7, PEACH)
        pyxel.circ(x + 30, y + 14, 7, YELLOW)
        pyxel.circ(x + 31, y + 24, 8, CARD)
        pyxel.rect(x + 29, y + 20, 5, 4, PANEL)

        # 青いゴーグルがライバルの識別記号。
        pyxel.rectb(x + 18, y + 11, 11, 8, BLUE)
        pyxel.rectb(x + 34, y + 11, 11, 8, BLUE)
        pyxel.line(x + 29, y + 14, x + 34, y + 14, BLUE)
        if blink or action in {"celebrate", "defeat"}:
            pyxel.line(x + 21, y + 15, x + 26, y + 15, PANEL)
            pyxel.line(x + 37, y + 15, x + 42, y + 15, PANEL)
        else:
            eye_y = y + 15 if action == "frustrated" else y + 13
            pyxel.rect(x + 23, eye_y, 2, 4, PANEL)
            pyxel.rect(x + 38, eye_y, 2, 4, PANEL)
        pyxel.pset(x + 31, y + 23, PANEL)

        if action == "celebrate":
            pyxel.line(x + 20, y + 34, x + 10, y + 24, YELLOW)
            pyxel.line(x + 42, y + 34, x + 51, y + 23, YELLOW)
            pyxel.circ(x + 9, y + 23, 3, YELLOW)
            pyxel.circ(x + 52, y + 22, 3, YELLOW)
            pyxel.line(x + 27, y + 26, x + 31, y + 29, PANEL)
            pyxel.line(x + 31, y + 29, x + 35, y + 26, PANEL)
            pyxel.line(x + 5, y + 15, x + 10, y + 15, PINK)
            pyxel.line(x + 7, y + 13, x + 7, y + 18, PINK)
            pyxel.line(x + 54, y + 10, x + 59, y + 10, YELLOW)
            pyxel.line(x + 56, y + 8, x + 56, y + 13, YELLOW)
        elif action == "frustrated":
            pyxel.line(x + 20, y + 35, x + 39, y + 43, YELLOW)
            pyxel.line(x + 41, y + 35, x + 22, y + 43, YELLOW)
            pyxel.line(x + 27, y + 28, x + 31, y + 25, ERROR)
            pyxel.line(x + 31, y + 25, x + 35, y + 28, ERROR)
            pyxel.line(x + 48, y + 4, x + 55, y + 4, ERROR)
            pyxel.line(x + 51, y + 1, x + 51, y + 8, ERROR)
            pyxel.line(x + 47, y, x + 55, y + 8, ERROR)
        elif action == "defeat":
            pyxel.line(x + 20, y + 35, x + 12, y + 46, YELLOW)
            pyxel.line(x + 41, y + 35, x + 49, y + 46, YELLOW)
            pyxel.line(x + 28, y + 28, x + 31, y + 26, PANEL)
            pyxel.line(x + 31, y + 26, x + 34, y + 28, PANEL)
            pyxel.tri(x + 45, y + 17, x + 49, y + 24, x + 41, y + 24, BLUE)
        else:
            pyxel.line(x + 20, y + 35, x + 12, y + 42, YELLOW)
            pyxel.line(x + 41, y + 35, x + 48, y + 42, YELLOW)

    def draw_side_console(self) -> None:
        if isinstance(self.round, BattleRound):
            for x, points, label, color in ((24, self.round.player_points, "YOU", GREEN),
                                           (579, self.round.cpu_points, "CPU", PINK)):
                self.draw_box(x, 58, 38, 172, color)
                pyxel.text(x + 12, 69, label, color)
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
        if isinstance(self.round, BattleRound):
            self.draw_box(158, 250, 324, 94, YELLOW)
            if self.round.in_transition:
                owner = self.round.last_owner.upper()
                centered_text(266, f"{owner} TAKES {self.round.last_number}!", GREEN if owner == "YOU" else PINK)
                centered_text(290, "NEXT TARGET...", CARD)
            else:
                pyxel.text(185, 270, "MISS!" if self.wrong_cell is not None else "FIND", ERROR if self.wrong_cell is not None else YELLOW)
                draw_number(320, 260, self.round.current_target, CARD, 5)
                pyxel.text(391, 270, "FIRST!", YELLOW)
                # 探索状況だけを示し、正解位置は漏らさない。
                duration = max(0.01, self.round.cpu_at - self.round.ready_at)
                progress = min(1, max(0, (self.round.elapsed() - self.round.ready_at) / duration))
                pyxel.text(186, 306, "CPU SEARCH", PINK)
                pyxel.rect(238, 306, 210, 5, DEEP_BLUE)
                pyxel.rect(238, 306, int(210 * progress), 5, PINK)
            needed = max(0, self.round.goal - self.round.player_points)
            centered_text(326, f"NEED {needed} MORE TO WIN  /  {self.round.completed_count}/{self.round.max_number} FOUND", YELLOW)
            return
        if self.wrong_cell is not None:
            border = ERROR
        elif self.correct_cell is not None:
            border = GREEN
        else:
            border = BLUE
        self.draw_box(170, 250, 300, 94, border)
        target = self.round.current_target or self.round.max_number

        pyxel.text(198, 269, "FIND THE", MUTED)
        draw_number(320, 260, target, CARD, scale=5)
        pyxel.text(381, 274, "!", YELLOW)

        if self.wrong_cell is not None:
            centered_text(308, "MISS!  CPU CHEERS - TARGET STAYS", ERROR)
        elif pyxel.frame_count < self.milestone_until_frame:
            centered_text(
                308,
                f"CHECKPOINT {self.milestone_value}/{self.round.max_number} - DRIVE UP!",
                GREEN,
            )
        elif self.correct_cell is not None:
            centered_text(308, f"PLAYER HIT!  STREAK {self.streak}", GREEN)
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
        self.draw_box(112, 54, 416, 222, BLUE)
        centered_text(63, "NUMBER RUSH - FOREST DUEL", YELLOW)
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
            self.draw_button(button, difficulty.upper(), PINK if self.play_kind == "battle" else MUTED,
                             selected=self.play_kind == "battle" and difficulty == self.difficulty)
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
        question = "RESTART THIS RUN?" if self.confirm_action == "retry" else "RETURN TO TITLE?"
        centered_text(116, "CONFIRM", YELLOW)
        centered_text(149, question, CARD)
        centered_text(177, "TIMER PAUSED / BOARD HIDDEN", MUTED)
        self.draw_button(YES_BUTTON, "YES", GREEN)
        self.draw_button(NO_BUTTON, "NO", ERROR)
        pyxel.text(238, 282, "KEY Y", MUTED)
        pyxel.text(369, 282, "KEY N", MUTED)

    def draw_finished_panel(self) -> None:
        if isinstance(self.round, BattleRound):
            color = GREEN if self.round.won else PINK
            self.draw_box(118, 62, 404, 214, color)
            centered_text(85, "YOU WIN!" if self.round.won else "CPU WINS - TRY AGAIN!", color)
            centered_text(110, f"1-{self.round.max_number} / {self.selected_mode.upper()} / {self.difficulty.upper()}", MUTED)
            centered_text(133, f"YOU {self.round.player_points}  :  {self.round.cpu_points} CPU    GOAL {self.round.goal}", YELLOW)
            avg = (f"{sum(self.round.response_times) / len(self.round.response_times):.2f}s" if self.round.response_times else "--")
            centered_text(154, f"TIME {self.round.elapsed():.2f}s   AVG RESPONSE {avg}", CARD)
            centered_text(176, f"MISSES {self.round.mistakes}   BEST STREAK {self.max_streak}", CARD)
            key = (self.round.max_number, self.selected_mode, self.difficulty)
            centered_text(197, f"SESSION BEST {self.battle_records.get(key, 0)} POINTS", color)
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
