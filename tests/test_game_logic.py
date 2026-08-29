import random
import unittest

from game_logic import NumberTapRound


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class NumberTapRoundTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        self.round = NumberTapRound(rng=random.Random(1234), clock=self.clock)

    def test_start_creates_each_number_once(self) -> None:
        self.round.start()

        self.assertEqual(sorted(self.round.numbers), list(range(1, 10)))
        self.assertEqual(len(set(self.round.numbers)), 9)
        self.assertTrue(self.round.is_playing)
        self.assertEqual(self.round.next_number, 1)

    def test_wrong_number_is_visible_to_logic_and_does_not_advance(self) -> None:
        self.round.start()

        self.assertEqual(self.round.tap(2), "wrong")
        self.assertEqual(self.round.next_number, 1)
        self.assertEqual(self.round.mistakes, 1)

    def test_correct_sequence_finishes_and_freezes_elapsed_time(self) -> None:
        self.round.start()
        for number in range(1, 9):
            self.assertEqual(self.round.tap(number), "correct")

        self.clock.now = 4.25
        self.assertEqual(self.round.tap(9), "finished")
        self.assertTrue(self.round.is_finished)
        self.assertAlmostEqual(self.round.elapsed(), 4.25)

        self.clock.now = 99.0
        self.assertAlmostEqual(self.round.elapsed(), 4.25)
        self.assertEqual(self.round.tap(1), "inactive")

    def test_start_resets_previous_result(self) -> None:
        self.round.start()
        self.round.tap(2)
        for number in range(1, 10):
            self.round.tap(number)

        self.clock.now = 10.0
        self.round.start()

        self.assertTrue(self.round.is_playing)
        self.assertFalse(self.round.is_finished)
        self.assertEqual(self.round.mistakes, 0)
        self.assertEqual(self.round.next_number, 1)
        self.assertEqual(self.round.elapsed(), 0.0)


if __name__ == "__main__":
    unittest.main()
