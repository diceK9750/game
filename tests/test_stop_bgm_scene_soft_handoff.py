"""stop_bgm must not wipe scene identity; sync keeps ~8-frame quiet gaps."""

import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock


class StopBgmSceneSoftHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plays = []
        self.stops = []
        fake = types.ModuleType("pyxel")
        fake.frame_count = 100
        fake.stop = lambda ch: self.stops.append(ch)
        fake.play = lambda ch, sound, loop=False, sec=0: self.plays.append((ch, sound, loop))
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
        app.scene_music = "win"
        app.scene_music_pending = None
        app.scene_music_switch_at = 0
        app.result_music_after = 0
        app.round = types.SimpleNamespace(is_perfect=False, won=True)
        app.shiritori = types.SimpleNamespace(
            phase="setup", winner=None, history=[], total=12, mode="solo"
        )
        app.bgm_paused = False
        app.bgm_has_started = True
        app.bgm_audible_at = 0
        app.bgm_channel_stop_at = 0
        app.pending_bgm_stage = None
        app.bgm_origin_frame = 0
        app.bgm_paused_position_frames = 0
        app.selected_mode = "random"
        app.storage_saved = True
        app.confirm_action = None
        # progress.save is used by begin_countdown; stub via monkeypatch below.
        self.app = app
        self._orig_save = self.game.progress.save
        self.game.progress.save = lambda _app: True

    def tearDown(self) -> None:
        self.game.progress.save = self._orig_save

    def test_finished_result_to_ready_uses_quiet_gap(self):
        """Direct mode-select return already soft-switches via sync_scene_music."""
        self.app.screen = "ready"
        self.plays.clear()
        self.stops.clear()
        release = self.game.PAUSE_BGM_RELEASE_FRAMES
        audible_at = 100 + release + 8
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "menu")
        self.assertEqual(self.app.scene_music_pending, "menu")
        self.assertEqual(self.app.bgm_channel_stop_at, 100 + release)
        self.assertEqual(self.app.scene_music_switch_at, audible_at)
        self.assertEqual(self.plays, [])
        self.assertEqual(self.stops, [])

        self.pyxel.frame_count = audible_at
        self.app.sync_scene_music()
        self.assertIsNone(self.app.scene_music_pending)
        self.assertTrue(self.plays)

    def test_begin_countdown_from_result_keeps_quiet_gap(self):
        """Replay used to hard-cut because stop_bgm cleared scene_music."""
        self.plays.clear()
        self.stops.clear()
        release = self.game.PAUSE_BGM_RELEASE_FRAMES
        audible_at = 100 + release + 8
        self.app.begin_countdown("random")
        self.assertEqual(self.app.screen, "countdown")
        # Gameplay BGM flags cleared; scene identity preserved for soft switch.
        self.assertFalse(self.app.bgm_has_started)
        self.assertEqual(self.app.scene_music, "win")
        # stop_bgm already silenced channels; soft switch must not cut again.
        self.stops.clear()
        self.app.sync_scene_music()
        self.assertEqual(self.app.scene_music, "countdown")
        self.assertEqual(self.app.scene_music_pending, "countdown")
        self.assertEqual(self.app.bgm_channel_stop_at, 100 + release)
        self.assertEqual(self.app.scene_music_switch_at, audible_at)
        self.assertEqual(self.plays, [])
        self.assertEqual(self.stops, [])

        self.pyxel.frame_count = audible_at
        self.app.sync_scene_music()
        self.assertIsNone(self.app.scene_music_pending)
        self.assertTrue(self.plays)

    def test_stop_bgm_preserves_scene_fields_on_stubs(self):
        """__new__ stubs may omit scene fields; stop_bgm must not require them."""
        bare = self.game.NumberRush.__new__(self.game.NumberRush)
        bare.bgm_paused = True
        bare.bgm_has_started = True
        bare.pending_bgm_stage = 1
        bare.bgm_origin_frame = 9
        bare.bgm_paused_position_frames = 3
        # Intentionally no scene_music* / bgm_audible_at attrs.
        bare.stop_bgm()
        self.assertFalse(bare.bgm_has_started)
        self.assertFalse(bare.bgm_paused)
        self.assertIsNone(bare.pending_bgm_stage)
        self.assertFalse(hasattr(bare, "scene_music"))


if __name__ == "__main__":
    unittest.main()
