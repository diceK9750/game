"""Pyxelに依存しないNUMBER RUSHのゲーム進行ロジック。"""

from __future__ import annotations

import random
import time
from collections.abc import Callable


class NumberTapRound:
    """1から9までを順番に押す1ラウンドを管理する。"""

    def __init__(
        self,
        *,
        rng: random.Random | None = None,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._rng = rng or random.Random()
        self._clock = clock
        self.numbers: list[int] = []
        self.next_number = 1
        self.mistakes = 0
        self.started_at: float | None = None
        self.finished_at: float | None = None

    @property
    def is_playing(self) -> bool:
        return self.started_at is not None and self.finished_at is None

    @property
    def is_finished(self) -> bool:
        return self.finished_at is not None

    def start(self) -> None:
        """数字を並べ替えて、新しいラウンドの計測を開始する。"""
        self.numbers = list(range(1, 10))
        self._rng.shuffle(self.numbers)
        self.next_number = 1
        self.mistakes = 0
        self.finished_at = None
        self.started_at = self._clock()

    def tap(self, number: int) -> str:
        """押された数字を判定し、判定結果を文字列で返す。"""
        if not self.is_playing:
            return "inactive"

        if number != self.next_number:
            self.mistakes += 1
            return "wrong"

        if self.next_number == 9:
            self.finished_at = self._clock()
            self.next_number = 10
            return "finished"

        self.next_number += 1
        return "correct"

    def elapsed(self) -> float:
        """開始から現在またはクリアまでの経過秒数を返す。"""
        if self.started_at is None:
            return 0.0
        end = self.finished_at if self.finished_at is not None else self._clock()
        return max(0.0, end - self.started_at)

