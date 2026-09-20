"""Finished win/loss/perfect after the jingle should use an ~8-frame quiet gap."""

import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock


class ResultSceneBgmSoftHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plays = []
        self.stops = []
        fake = types.ModuleType("pyxel")
        fake.frame_count = 100
        fake.stop = lambda ch: self.stops.append(ch)
        fake.play = lambda ch, sound, loop=False, sec=0: self.plays.append(
            (ch, sound, loop)
        )
        fake.sounds = [MagicMock() for _ in range(64)]
        sys.modules["pyxel"] = fake
        if "game" in sys.modules:
            del sys.modules["game"]
        sys.modules.setdefault("js", types.SimpleNamespace(document=None))
        self.game = importlib.import_module("game")
        self.pyxel = fake
        app = self.game.NumberRush.__new__(self.game.NumberRush)
        app.bgm_on = True
        app.screen = "finished"
        # Cleared while playing; jingle window has elapsed.
        app.scene_music = None
        app.scene_music_pending = None
        app.scene_music_switch_at = 0
        app.result_music_after = 100
        app.round = types.SimpleNamespace(is_perfect=False, won=True)
        app.shiritori = types.SimpleNamespace(
            phase="setup", winner=None, history=[], total=12, mode="solo"
        )
        app.bgm_paused = False
        app.bgm_has_started = False
        self.app = app

    def _battle_stub(self, *, won: bool, perfect: bool):
        """Minimal BattleRound subclass so isinstance + outcome properties work."""

        class StubBattle(self.game.BattleRound):
            def __init__(self):
                self._won = won
                self._perfect = perfect

            @property
            def won(self):
                return self._won

            @property
            def is_perfect(self):
                return self._perfect

        return StubBattle()

    def test_win_after_jingle_defers_audible_start_by_quiet_gap(self):
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "win")
        self.assertEqual(self.app.scene_music_pending, "win")
        self.assertEqual(self.app.scene_music_switch_at, 108)
        self.assertEqual(self.plays, [])

        self.pyxel.frame_count = 107
        self.app.sync_scene_music()
        self.assertEqual(self.plays, [])
        self.assertEqual(self.app.scene_music_pending, "win")

        self.pyxel.frame_count = 108
        self.app.sync_scene_music()
        self.assertIsNone(self.app.scene_music_pending)
        self.assertEqual(self.app.scene_music, "win")
        self.assertTrue(self.plays)

    def test_loss_and_perfect_also_soft_start_from_none(self):
        for track, kwargs in (
            ("loss", {"won": False, "perfect": False}),
            ("perfect", {"won": True, "perfect": True}),
        ):
            with self.subTest(track=track):
                self.plays.clear()
                self.pyxel.frame_count = 200
                self.app.scene_music = None
                self.app.scene_music_pending = None
                self.app.scene_music_switch_at = 0
                self.app.result_music_after = 200
                self.app.round = self._battle_stub(**kwargs)
                self.app.sync_scene_music()
                self.assertEqual(self.app.scene_music, track)
                self.assertEqual(self.app.scene_music_pending, track)
                self.assertEqual(self.plays, [])
                self.pyxel.frame_count = 208
                self.app.sync_scene_music()
                self.assertIsNone(self.app.scene_music_pending)
                self.assertTrue(self.plays)

    def test_cold_menu_silence_still_starts_immediately(self):
        self.app.screen = "ready"
        self.app.scene_music = None
        self.app.scene_music_pending = None
        self.app.scene_music_switch_at = 0
        self.app.round = None
        self.plays.clear()
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "menu")
        self.assertIsNone(self.app.scene_music_pending)
        self.assertTrue(self.plays)

    def test_before_jingle_window_stays_silent(self):
        self.app.result_music_after = 150
        self.app.sync_scene_music()
        self.assertIsNone(self.app.scene_music)
        self.assertIsNone(self.app.scene_music_pending)
        self.assertEqual(self.plays, [])


if __name__ == "__main__":
    unittest.main()
