import json
import unittest
from types import SimpleNamespace
from progress import decode, encode
from ui_text import text_width, translate


class ProgressTests(unittest.TestCase):
    def test_oversized_numbers_and_deep_json_do_not_break_loading(self):
        raw=json.dumps({'version':1,'best_times':[[10,'ordered',10**500],[20,'random',3.5]]})
        self.assertEqual(decode(raw)['best_times'], {(20,'random'):3.5})
        self.assertEqual(decode('['*2000+']'*2000)['best_times'], {})

    def test_shiritori_settings_round_trip_and_invalid_fields(self):
        app=SimpleNamespace(best_times={},battle_records={},bonus_bank=0,bgm_on=True,sfx_on=True,reduced_motion=False,
                            shiritori=SimpleNamespace(mode='solo',total=48,difficulty='hard'))
        self.assertEqual(decode(encode(app))['shiritori_settings'],{'mode':'solo','total':48,'difficulty':'hard'})
        self.assertNotIn('shiritori_settings',decode(json.dumps({'version':1,'shiritori_settings':{'mode':[], 'total':True,'difficulty':'invalid'}})))
    def test_round_trip_and_separate_modes(self):
        app = SimpleNamespace(best_times={(10, "ordered"): 3.5, (40, "random"): 42.0},
                              battle_records={(20, "random", "hard"): 12},
                              bonus_bank=3000, bgm_on=False, sfx_on=True,
                              reduced_motion=True)
        restored = decode(encode(app))
        self.assertEqual(restored, vars(app))

    def test_corrupt_save_is_not_fatal(self):
        for raw in (None, "bad json", "[]", "null", '{"version":2}'):
            self.assertEqual(decode(raw)["bonus_bank"], 0)

    def test_invalid_records_rejected_individually(self):
        raw = json.dumps({"version": 1, "bonus_bank": -10, "bgm_on": "false",
                          "best_times": [[10, "ordered", float("nan")], [20, "random", 4.5]],
                          "battle_records": [[40, "random", "hard", 41],
                                             [10, "ordered", "easy", True],
                                             [30, "random", "normal", 18]]})
        state = decode(raw)
        self.assertEqual(state["best_times"], {(20, "random"): 4.5})
        self.assertEqual(state["battle_records"], {(30, "random", "normal"): 18})
        self.assertTrue(state["bgm_on"])
        self.assertEqual(state["bonus_bank"], 0)

    def test_japanese_button_width_is_not_ascii_width(self):
        self.assertEqual(text_width("CPU DUEL"), text_width(translate("CPU DUEL")))
        self.assertLess(text_width("ランダムで開始"), 188)

    def test_last_played_settings_are_optional_and_validated(self):
        values = dict(version=1, selected_max_number=20, selected_mode='random',
                      play_kind='practice', difficulty='easy')
        restored = decode(json.dumps(values))
        for key in values.keys() - {'version'}:
            self.assertEqual(restored[key], values[key])
        invalid = dict(version=1, selected_max_number=True, selected_mode='bad',
                       play_kind=['battle'], difficulty=None)
        restored = decode(json.dumps(invalid))
        for key in invalid.keys() - {'version'}:
            self.assertNotIn(key, restored)
