import random
import unittest

from game_logic import NumberTapRound, correct_points, music_stage_for_progress


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

        self.assertEqual(sorted(self.round.numbers), list(range(1, 41)))
        self.assertEqual(len(set(self.round.numbers)), 40)
        self.assertTrue(self.round.is_playing)
        self.assertEqual(self.round.mode, "ordered")
        self.assertEqual(self.round.next_number, 1)
        self.assertEqual(self.round.current_target, 1)
        self.assertEqual(self.round.completed_count, 0)

    def test_wrong_number_is_visible_to_logic_and_does_not_advance(self) -> None:
        self.round.start()

        self.assertEqual(self.round.tap(2), "wrong")
        self.assertEqual(self.round.next_number, 1)
        self.assertEqual(self.round.mistakes, 1)
        self.assertEqual(self.round.completed_count, 0)

    def test_correct_sequence_finishes_and_freezes_elapsed_time(self) -> None:
        self.round.start()
        for number in range(1, 40):
            self.assertEqual(self.round.tap(number), "correct")

        self.clock.now = 4.25
        self.assertEqual(self.round.tap(40), "finished")
        self.assertTrue(self.round.is_finished)
        self.assertEqual(self.round.completed_count, 40)
        self.assertIsNone(self.round.current_target)
        self.assertAlmostEqual(self.round.elapsed(), 4.25)

        self.clock.now = 99.0
        self.assertAlmostEqual(self.round.elapsed(), 4.25)
        self.assertEqual(self.round.tap(1), "inactive")

    def test_start_resets_previous_result(self) -> None:
        self.round.start()
        self.round.tap(2)
        for number in range(1, 41):
            self.round.tap(number)

        self.clock.now = 10.0
        self.round.start()

        self.assertTrue(self.round.is_playing)
        self.assertFalse(self.round.is_finished)
        self.assertEqual(self.round.mistakes, 0)
        self.assertEqual(self.round.next_number, 1)
        self.assertEqual(self.round.completed_count, 0)
        self.assertEqual(self.round.elapsed(), 0.0)

    def test_custom_max_number_is_supported(self) -> None:
        short_round = NumberTapRound(max_number=3, rng=random.Random(5), clock=self.clock)
        short_round.start()

        self.assertEqual(sorted(short_round.numbers), [1, 2, 3])
        self.assertEqual(short_round.tap(1), "correct")
        self.assertEqual(short_round.tap(2), "correct")
        self.assertEqual(short_round.tap(3), "finished")

    def test_random_mode_uses_each_target_once_in_random_order(self) -> None:
        self.round.start("random")

        self.assertEqual(self.round.mode, "random")
        self.assertEqual(sorted(self.round.targets), list(range(1, 41)))
        self.assertNotEqual(self.round.targets, list(range(1, 41)))

        target_order = self.round.targets.copy()
        for target in target_order[:-1]:
            self.assertEqual(self.round.current_target, target)
            self.assertEqual(self.round.tap(target), "correct")
        self.assertEqual(self.round.tap(target_order[-1]), "finished")
        self.assertEqual(self.round.completed_count, 40)

    def test_unknown_mode_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.round.start("mystery")

    def test_pause_excludes_wait_time_and_blocks_input(self) -> None:
        self.round.start()
        self.clock.now = 3.0
        self.round.pause()

        self.assertTrue(self.round.is_paused)
        self.clock.now = 30.0
        self.assertAlmostEqual(self.round.elapsed(), 3.0)
        self.assertEqual(self.round.tap(1), "inactive")

        self.round.resume()
        self.assertFalse(self.round.is_paused)
        self.clock.now = 32.5
        self.assertAlmostEqual(self.round.elapsed(), 5.5)
        self.assertEqual(self.round.tap(1), "correct")

    def test_pause_before_start_and_after_finish_has_no_effect(self) -> None:
        self.round.pause()
        self.assertFalse(self.round.is_paused)

        self.round.start()
        for number in range(1, 41):
            self.round.tap(number)
        self.round.pause()
        self.assertFalse(self.round.is_paused)

    def test_max_number_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            NumberTapRound(max_number=0)

    def test_score_uses_capped_streak_bonus(self) -> None:
        self.assertEqual(correct_points(1), 110)
        self.assertEqual(correct_points(20), 300)
        self.assertEqual(correct_points(21), 300)
        self.assertEqual(sum(correct_points(streak) for streak in range(1, 41)), 10100)

        with self.assertRaises(ValueError):
            correct_points(0)

    def test_music_stage_changes_at_twenty_and_thirty(self) -> None:
        self.assertEqual(music_stage_for_progress(0), 0)
        self.assertEqual(music_stage_for_progress(19), 0)
        self.assertEqual(music_stage_for_progress(20), 1)
        self.assertEqual(music_stage_for_progress(29), 1)
        self.assertEqual(music_stage_for_progress(30), 2)
        self.assertEqual(music_stage_for_progress(40), 2)

        with self.assertRaises(ValueError):
            music_stage_for_progress(41)


if __name__ == "__main__":
    unittest.main()
