"""Pyxelに依存しないNUMBER RUSHのゲーム進行ロジック。"""

from __future__ import annotations

import random
import time
from collections.abc import Callable


BOARD_CELL_COUNT = 40


def correct_points(streak: int) -> int:
    """正解1回分の得点。連続正解ボーナスは200点を上限にする。"""
    if streak < 1:
        raise ValueError("streak must be at least 1")
    return 100 + min(streak * 10, 200)


def music_stage_for_progress(completed: int, *, max_number: int = 40) -> int:
    """発見数に応じてBGMの厚みを0～2の段階で返す。"""
    if max_number < 1:
        raise ValueError("max_number must be at least 1")
    if not 0 <= completed <= max_number:
        raise ValueError("completed must be within the round")
    stage_two_at = (3 * max_number + 3) // 4
    stage_one_at = (max_number + 1) // 2
    if completed >= stage_two_at:
        return 2
    if completed >= stage_one_at:
        return 1
    return 0


class NumberTapRound:
    """1から指定した最大値までを順番に押す1ラウンドを管理する。"""

    def __init__(
        self,
        *,
        max_number: int = 40,
        rng: random.Random | None = None,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        if not 1 <= max_number <= BOARD_CELL_COUNT:
            raise ValueError(
                f"max_number must be between 1 and {BOARD_CELL_COUNT}"
            )
        self.max_number = max_number
        self._rng = rng or random.Random()
        self._clock = clock
        self.mode = "ordered"
        self.numbers: list[int] = []
        self.board_cells: list[int | None] = []
        self.targets: list[int] = []
        self.target_index = 0
        self.found_numbers: set[int] = set()
        self.mistakes = 0
        self.started_at: float | None = None
        self.finished_at: float | None = None
        self.paused_at: float | None = None
        self.total_paused = 0.0

    @property
    def is_playing(self) -> bool:
        return self.started_at is not None and self.finished_at is None

    @property
    def is_finished(self) -> bool:
        return self.finished_at is not None

    @property
    def is_paused(self) -> bool:
        return self.paused_at is not None

    @property
    def current_target(self) -> int | None:
        """現在探す数字。開始前とクリア後はNone。"""
        if not self.is_playing:
            return None
        return self.targets[self.target_index]

    @property
    def next_number(self) -> int:
        """旧UIとの互換用。現在のお題、未開始時は1、終了時は最大値+1。"""
        if self.is_finished:
            return self.max_number + 1
        return self.current_target or 1

    @property
    def completed_count(self) -> int:
        return len(self.found_numbers)

    def start(self, mode: str = "ordered") -> None:
        """盤面とお題を並べ替えて、新しいラウンドの計測を開始する。"""
        if mode not in {"ordered", "random"}:
            raise ValueError("mode must be 'ordered' or 'random'")

        self.mode = mode
        board_cells: list[int | None] = list(range(1, self.max_number + 1))
        board_cells.extend([None] * (BOARD_CELL_COUNT - self.max_number))
        self._rng.shuffle(board_cells)
        self.board_cells = board_cells
        self.numbers = [number for number in board_cells if number is not None]
        self.targets = list(range(1, self.max_number + 1))
        if mode == "random":
            self._rng.shuffle(self.targets)
            if self.max_number > 1 and self.targets == list(range(1, self.max_number + 1)):
                self.targets = self.targets[1:] + self.targets[:1]
        self.target_index = 0
        self.found_numbers = set()
        self.mistakes = 0
        self.finished_at = None
        self.paused_at = None
        self.total_paused = 0.0
        self.started_at = self._clock()

    def tap(self, number: int | None) -> str:
        """押された数字を判定し、判定結果を文字列で返す。"""
        if not self.is_playing or self.is_paused:
            return "inactive"

        if number is None:
            return "empty"

        if number != self.current_target:
            self.mistakes += 1
            return "wrong"

        self.found_numbers.add(number)
        self.target_index += 1
        if self.target_index == self.max_number:
            self.finished_at = self._clock()
            return "finished"

        return "correct"

    def pause(self) -> None:
        """進行中のラウンドだけを一時停止する。"""
        if self.is_playing and not self.is_paused:
            self.paused_at = self._clock()

    def resume(self) -> None:
        """一時停止時間を計測対象から除外して再開する。"""
        if self.paused_at is not None:
            self.total_paused += max(0.0, self._clock() - self.paused_at)
            self.paused_at = None

    def elapsed(self) -> float:
        """開始から現在またはクリアまでの経過秒数を返す。"""
        if self.started_at is None:
            return 0.0
        if self.finished_at is not None:
            end = self.finished_at
        elif self.paused_at is not None:
            end = self.paused_at
        else:
            end = self._clock()
        return max(0.0, end - self.started_at - self.total_paused)


class BattleRound(NumberTapRound):
    """同じお題を取り合う対戦。CPUの期限は入力と独立して抽選する。"""

    SPEEDS = {"easy": (4.0, 6.0), "normal": (2.4, 4.2), "hard": (1.3, 2.6)}
    RESULT_SECONDS = 0.65

    def __init__(self, *, difficulty="normal", **kwargs):
        super().__init__(**kwargs)
        if difficulty not in self.SPEEDS:
            raise ValueError("unknown difficulty")
        self.difficulty = difficulty
        self.owners = {}
        self.player_points = self.cpu_points = 0
        self.response_times = []
        self.ready_at = self.cpu_at = 0.0
        self.last_owner = None
        self.last_number = None

    @property
    def goal(self):
        return (self.max_number * 3 + 4) // 5

    @property
    def won(self):
        return self.player_points >= self.goal

    @property
    def in_transition(self):
        return self.elapsed() < self.ready_at

    def start(self, mode="random"):
        super().start(mode)
        self.owners = {}
        self.player_points = self.cpu_points = 0
        self.response_times = []
        self.last_owner = self.last_number = None
        self._schedule(0.0)

    def _schedule(self, delay):
        self.ready_at = self.elapsed() + delay
        low, high = self.SPEEDS[self.difficulty]
        self.cpu_at = self.ready_at + self._rng.uniform(low, high)

    def _claim(self, owner):
        number = self.current_target
        self.owners[number] = owner
        self.last_owner, self.last_number = owner, number
        if owner == "you":
            self.player_points += 1
            self.response_times.append(max(0.0, self.elapsed() - self.ready_at))
        else:
            self.cpu_points += 1
        result = super().tap(number)
        if not self.is_finished:
            self._schedule(self.RESULT_SECONDS)
        return result

    def tap(self, number):
        if not self.is_playing or self.is_paused or self.in_transition:
            return "inactive"
        if number is None or number in self.found_numbers:
            return "empty"
        if number != self.current_target:
            self.mistakes += 1
            # ミスはCPUを少し加速するが、期限を延長せず入力も封じない。
            now = self.elapsed()
            self.cpu_at = min(self.cpu_at, max(now + 0.25, self.cpu_at - 0.3))
            return "wrong"
        return self._claim("you")

    def update_cpu(self):
        if (self.is_playing and not self.is_paused
                and not self.in_transition and self.elapsed() >= self.cpu_at):
            self._claim("cpu")
            return self.last_number
        return None
