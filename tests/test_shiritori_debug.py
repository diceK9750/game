import random
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from modern_ui import ModernUI
from shiritori import ShiritoriRound


class ShiritoriDebugTests(unittest.TestCase):
    def setUp(self):
        self.game = ShiritoriRound(total=48, mode="solo", rng=random.Random(184), clock=lambda: 0)
        self.game.start()
        self.app = SimpleNamespace(screen="shiritori", shiritori=self.game, play_sfx=lambda *_: None)

    def send(self, action, value=None):
        ModernUI._dispatch(self.app, {"action": action, "value": value})

    def test_default_denies_debug_hint_and_requires_strict_opt_in(self):
        self.send("sh_debug_hint")
        self.assertIsNone(self.game.hint)
        self.send("sh_debug_mode", 1)
        self.send("sh_debug_hint")
        self.assertIsNone(self.game.hint)
        self.send("sh_debug_mode", True)
        self.send("sh_debug_hint")
        self.assertIsNotNone(self.game.hint)
        self.assertEqual(self.game.hints, 3)
        self.send("sh_debug_mode", False)
        self.game.hint = None
        self.send("sh_debug_hint")
        self.assertIsNone(self.game.hint)

    def test_support_replays_full_48_without_consuming_hints(self):
        self.send("sh_debug_mode", True)
        for i in range(48):
            self.send("sh_debug_hint")
            self.assertIsNotNone(self.game.hint, f"missing support after {i} cards")
            self.game.command("card", self.game.hint)
        self.assertTrue(self.game.perfect)
        self.assertEqual(len(self.game.history), 48)
        self.assertEqual(self.game.hints, 3)
        self.assertEqual(self.game.relinks, 2)

    def test_unproved_state_never_launches_search(self):
        self.send("sh_debug_mode", True)
        with patch.object(self.game, "cached_perfect_move", return_value=None), \
             patch.object(self.game, "chain_advice", side_effect=AssertionError("unexpected search")):
            self.send("sh_debug_hint")
        self.assertIsNone(self.game.hint)
        self.assertEqual(self.game.hints, 3)

    def test_only_available_when_player_is_actively_playing(self):
        self.send("sh_debug_mode", True)
        self.game.phase = "paused"
        self.send("sh_debug_hint")
        self.assertIsNone(self.game.hint)
        self.game.phase = "playing"
        self.game.turn = "cpu"
        self.send("sh_debug_hint")
        self.assertIsNone(self.game.hint)


if __name__ == "__main__":
    unittest.main()
