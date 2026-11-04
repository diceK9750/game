import json
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import progress


class Store:
    def __init__(self, raw=None):
        self.data = {} if raw is None else {progress.KEY: raw}
        self.fail_read = False
        self.fail_write = False

    def getItem(self, key):
        if self.fail_read:
            raise OSError('read unavailable')
        return self.data.get(key)

    def setItem(self, key, value):
        if self.fail_write:
            raise OSError('write unavailable')
        self.data[key] = value


def app_from_storage():
    return SimpleNamespace(**progress.load())


class ProgressSafetyTests(unittest.TestCase):
    def setUp(self):
        initial = {'version': 1, 'best_times': [[10, 'ordered', 12.0]],
                   'battle_records': [[10, 'ordered', 'easy', 4]],
                   'bonus_bank': 1000, 'bgm_on': True, 'sfx_on': False,
                   'reduced_motion': False, 'selected_mode': 'ordered'}
        self.store = Store(json.dumps(initial))
        self.module_patch = patch.dict(sys.modules, {'js': SimpleNamespace(localStorage=self.store)})
        self.module_patch.start()
        self.addCleanup(self.module_patch.stop)

    def test_two_tabs_keep_better_times_and_scores(self):
        first, second = app_from_storage(), app_from_storage()
        first.best_times[(10, 'ordered')] = 5.0
        first.battle_records[(10, 'ordered', 'easy')] = 9
        self.assertTrue(progress.save(first))
        second.selected_mode = 'random'
        self.assertTrue(progress.save(second))
        restored = progress.decode(self.store.getItem(progress.KEY))
        self.assertEqual(restored['best_times'][(10, 'ordered')], 5.0)
        self.assertEqual(restored['battle_records'][(10, 'ordered', 'easy')], 9)
        self.assertEqual(second.best_times[(10, 'ordered')], 5.0)
        self.assertEqual(second.battle_records[(10, 'ordered', 'easy')], 9)
        self.assertEqual(restored['selected_mode'], 'random')

    def test_duplicate_records_preserve_best_in_either_order(self):
        for reverse in (False, True):
            with self.subTest(reverse=reverse):
                times = [[10, 'ordered', 5.0], [10, 'ordered', 12.0]]
                scores = [[10, 'ordered', 'easy', 9], [10, 'ordered', 'easy', 2]]
                if reverse:
                    times.reverse()
                    scores.reverse()
                data = {'version': 1, 'best_times': times, 'battle_records': scores}
                self.store.data[progress.KEY] = json.dumps(data)
                app = app_from_storage()
                self.assertEqual(app.best_times[(10, 'ordered')], 5.0)
                self.assertEqual(app.battle_records[(10, 'ordered', 'easy')], 9)
                self.assertTrue(progress.save(app))
                restored = progress.decode(self.store.data[progress.KEY])
                self.assertEqual(restored['best_times'][(10, 'ordered')], 5.0)
                self.assertEqual(restored['battle_records'][(10, 'ordered', 'easy')], 9)

    def test_two_tabs_add_each_bonus_once_and_repeat_save_does_not_duplicate(self):
        first, second = app_from_storage(), app_from_storage()
        first.bonus_bank += 300
        second.bonus_bank += 200
        self.assertTrue(progress.save(first))
        self.assertTrue(progress.save(second))
        self.assertEqual(progress.decode(self.store.getItem(progress.KEY))['bonus_bank'], 1500)
        self.assertEqual(second.bonus_bank, 1500)
        self.assertTrue(progress.save(second))
        self.assertEqual(progress.decode(self.store.getItem(progress.KEY))['bonus_bank'], 1500)
        self.assertTrue(progress.save(first))
        self.assertEqual(first.bonus_bank, 1500)

    def test_existing_tab_preserves_bonus_if_storage_disappears_or_regresses(self):
        for replacement in (None, {'version': 1, 'bonus_bank': 100}):
            with self.subTest(replacement=replacement):
                self.setUp_store()
                app = app_from_storage()
                app.bonus_bank += 300
                if replacement is None:
                    self.store.data.pop(progress.KEY)
                else:
                    self.store.data[progress.KEY] = json.dumps(replacement)
                self.assertTrue(progress.save(app))
                self.assertEqual(app.bonus_bank, 1300)
                self.assertEqual(progress.decode(self.store.data[progress.KEY])['bonus_bank'], 1300)

    def setUp_store(self):
        self.store.data[progress.KEY] = json.dumps({
            'version': 1, 'best_times': [[10, 'ordered', 12.0]],
            'battle_records': [[10, 'ordered', 'easy', 4]],
            'bonus_bank': 1000, 'bgm_on': True, 'sfx_on': False,
            'reduced_motion': False, 'selected_mode': 'ordered',
        })

    def test_unknown_or_corrupt_envelope_is_not_overwritten(self):
        for raw in ('', 'bad json', '[]', 'null', '{"version":2,"score":42}'):
            with self.subTest(raw=raw):
                self.store.data[progress.KEY] = raw
                app = app_from_storage()
                app.selected_mode = 'random'
                self.assertFalse(progress.save(app))
                self.assertEqual(self.store.data[progress.KEY], raw)

    def test_pyodide_jsnull_is_missing_but_other_objects_are_not(self):
        jsnull = object()
        unknown = object()
        ffi = SimpleNamespace(jsnull=jsnull)
        with patch.dict(sys.modules, {'pyodide.ffi': ffi}):
            self.store.data[progress.KEY] = jsnull
            app = app_from_storage()
            self.assertTrue(progress.save(app))
            self.assertEqual(progress.decode(self.store.data[progress.KEY])['bonus_bank'], 0)
            self.store.data[progress.KEY] = unknown
            app = app_from_storage()
            self.assertFalse(progress.save(app))
            self.assertIs(self.store.data[progress.KEY], unknown)

    def test_read_exception_cannot_overwrite_existing_values(self):
        raw = self.store.data[progress.KEY]
        self.store.fail_read = True
        app = app_from_storage()
        self.assertFalse(progress.save(app))
        self.assertEqual(self.store.data[progress.KEY], raw)
        self.store.fail_read = False
        self.assertTrue(progress.save(app))
        self.assertEqual(progress.decode(self.store.data[progress.KEY])['bonus_bank'], 1000)
        self.assertEqual(app.best_times[(10, 'ordered')], 12.0)

    def test_bonus_earned_during_read_failure_is_added_once_after_recovery(self):
        self.store.fail_read = True
        app = app_from_storage()
        app.bonus_bank += 300
        self.assertFalse(progress.save(app))
        self.store.fail_read = False
        self.assertTrue(progress.save(app))
        self.assertEqual(app.bonus_bank, 1300)
        self.assertTrue(progress.save(app))
        self.assertEqual(progress.decode(self.store.data[progress.KEY])['bonus_bank'], 1300)

    def test_failed_write_retry_does_not_double_bonus(self):
        app = app_from_storage()
        app.bonus_bank += 300
        self.store.fail_write = True
        self.assertFalse(progress.save(app))
        self.assertEqual(app.bonus_bank, 1300)
        self.store.fail_write = False
        self.assertTrue(progress.save(app))
        self.assertTrue(progress.save(app))
        self.assertEqual(progress.decode(self.store.data[progress.KEY])['bonus_bank'], 1300)

    def test_unknown_v1_fields_and_entries_are_retained(self):
        data = json.loads(self.store.data[progress.KEY])
        data['future'] = {'retain': ['future']}
        data['best_times'].append([50, 'ordered', 1.0])
        data['battle_records'].append(['future record'])
        self.store.data[progress.KEY] = json.dumps(data)
        app = app_from_storage()
        self.assertTrue(progress.save(app))
        restored = json.loads(self.store.data[progress.KEY])
        self.assertEqual(restored['future'], data['future'])
        self.assertIn([50, 'ordered', 1.0], restored['best_times'])
        self.assertIn(['future record'], restored['battle_records'])

    def test_settings_and_temporarily_silent_audio_preferences_survive(self):
        data = json.loads(self.store.data[progress.KEY])
        data['shiritori_settings'] = {'mode': 'solo', 'total': 48,
                                     'difficulty': 'hard', 'rival_style': 'counter',
                                     'future_setting': 'keep'}
        self.store.data[progress.KEY] = json.dumps(data)
        app = app_from_storage()
        app.audio_available = False
        app.audio_preferences = {'bgm_on': True, 'sfx_on': False}
        app.bgm_on = app.sfx_on = False
        app.shiritori = SimpleNamespace(mode='solo', total=48, difficulty='hard', rival_style='counter')
        self.assertTrue(progress.save(app))
        restored = json.loads(self.store.data[progress.KEY])
        self.assertTrue(restored['bgm_on'])
        self.assertFalse(restored['sfx_on'])
        self.assertEqual(restored['selected_mode'], 'ordered')
        self.assertEqual(restored['shiritori_settings'], data['shiritori_settings'])

    def test_old_tab_saving_records_does_not_undo_other_tab_settings(self):
        data = json.loads(self.store.data[progress.KEY])
        data['shiritori_settings'] = {'mode': 'solo', 'total': 24, 'difficulty': 'normal', 'rival_style': 'chain'}
        self.store.data[progress.KEY] = json.dumps(data)
        first, second = app_from_storage(), app_from_storage()
        first.shiritori = SimpleNamespace(**first.shiritori_settings)
        second.shiritori = SimpleNamespace(**second.shiritori_settings)
        first.bgm_on = False
        first.reduced_motion = True
        first.selected_mode = 'random'
        first.shiritori.total = 48
        self.assertTrue(progress.save(first))
        second.best_times[(10, 'ordered')] = 5.0
        self.assertTrue(progress.save(second))
        self.assertTrue(progress.save(second))
        restored = progress.decode(self.store.data[progress.KEY])
        self.assertFalse(restored['bgm_on'])
        self.assertTrue(restored['reduced_motion'])
        self.assertEqual(restored['selected_mode'], 'random')
        self.assertEqual(restored['shiritori_settings']['total'], 48)
        self.assertEqual(restored['best_times'][(10, 'ordered')], 5.0)
        # A later deliberate change in the stale tab is still saved.
        second.shiritori.total = 36
        self.assertTrue(progress.save(second))
        self.assertEqual(progress.decode(self.store.data[progress.KEY])['shiritori_settings']['total'], 36)

    def test_temporary_silent_tab_does_not_restore_other_tabs_audio_setting(self):
        first, silent = app_from_storage(), app_from_storage()
        silent.audio_available = False
        silent.audio_preferences = {'bgm_on': True, 'sfx_on': False}
        silent.bgm_on = silent.sfx_on = False
        first.bgm_on = False
        self.assertTrue(progress.save(first))
        self.assertTrue(progress.save(silent))
        self.assertFalse(progress.decode(self.store.data[progress.KEY])['bgm_on'])

    def test_explicit_setting_revert_after_failed_save_is_preserved(self):
        first, second = app_from_storage(), app_from_storage()
        second.bgm_on = False
        self.assertTrue(progress.save(second))
        first.bgm_on = False
        self.store.fail_write = True
        self.assertFalse(progress.save(first))
        first.bgm_on = True
        self.store.fail_write = False
        self.assertTrue(progress.save(first))
        self.assertTrue(progress.decode(self.store.data[progress.KEY])['bgm_on'])

    def test_setting_revert_survives_multiple_failed_saves(self):
        first, second = app_from_storage(), app_from_storage()
        second.bgm_on = False
        self.assertTrue(progress.save(second))
        first.bgm_on = False
        self.store.fail_read = True
        self.assertFalse(progress.save(first))
        first.bgm_on = True
        self.assertFalse(progress.save(first))
        self.store.fail_read = False
        self.assertTrue(progress.save(first))
        self.assertTrue(progress.decode(self.store.data[progress.KEY])['bgm_on'])

    def test_explicit_picture_setting_revert_after_failed_save_is_preserved(self):
        data = json.loads(self.store.data[progress.KEY])
        data['shiritori_settings'] = {'mode': 'solo', 'total': 24, 'difficulty': 'normal', 'rival_style': 'chain'}
        self.store.data[progress.KEY] = json.dumps(data)
        first, second = app_from_storage(), app_from_storage()
        first.shiritori = SimpleNamespace(**first.shiritori_settings)
        second.shiritori = SimpleNamespace(**second.shiritori_settings)
        second.shiritori.total = 48
        self.assertTrue(progress.save(second))
        first.shiritori.total = 36
        self.store.fail_write = True
        self.assertFalse(progress.save(first))
        first.shiritori.total = 24
        self.store.fail_write = False
        self.assertTrue(progress.save(first))
        self.assertEqual(progress.decode(self.store.data[progress.KEY])['shiritori_settings']['total'], 24)

    def test_picture_revert_survives_multiple_failed_saves(self):
        data = json.loads(self.store.data[progress.KEY])
        data['shiritori_settings'] = {'mode': 'solo', 'total': 24, 'difficulty': 'normal', 'rival_style': 'chain'}
        self.store.data[progress.KEY] = json.dumps(data)
        first, second = app_from_storage(), app_from_storage()
        first.shiritori = SimpleNamespace(**first.shiritori_settings)
        second.shiritori = SimpleNamespace(**second.shiritori_settings)
        second.shiritori.total = 48
        self.assertTrue(progress.save(second))
        first.shiritori.total = 36
        self.store.fail_write = True
        self.assertFalse(progress.save(first))
        first.shiritori.total = 24
        self.assertFalse(progress.save(first))
        self.store.fail_write = False
        self.assertTrue(progress.save(first))
        self.assertEqual(progress.decode(self.store.data[progress.KEY])['shiritori_settings']['total'], 24)

    def test_first_use_defaults_do_not_undo_other_tabs_new_settings(self):
        self.store.data.clear()
        first, second = app_from_storage(), app_from_storage()
        for app in (first, second):
            app.selected_max_number, app.selected_mode = 40, 'ordered'
            app.play_kind, app.difficulty = 'battle', 'normal'
            app.shiritori = SimpleNamespace(mode='solo', total=24, difficulty='normal', rival_style='chain')
        first.selected_mode = 'random'
        first.shiritori.total = 48
        self.assertTrue(progress.save(first))
        second.best_times[(10, 'ordered')] = 5.0
        self.assertTrue(progress.save(second))
        restored = progress.decode(self.store.data[progress.KEY])
        self.assertEqual(restored['selected_mode'], 'random')
        self.assertEqual(restored['shiritori_settings']['total'], 48)

    def test_first_shiritori_open_after_difficulty_change_does_not_override_other_tab(self):
        first, second = app_from_storage(), app_from_storage()
        first.difficulty = 'hard'
        second.difficulty = 'normal'
        self.assertTrue(progress.save(first))
        second.shiritori = SimpleNamespace(mode='solo', total=24, difficulty='easy', rival_style='chain')
        self.assertTrue(progress.save(second))
        # The first tab derives the initial picture-game difficulty from its
        # own number-game choice, without the player changing this field.
        first.shiritori = SimpleNamespace(mode='solo', total=24, difficulty='hard', rival_style='chain')
        self.assertTrue(progress.save(first))
        restored = progress.decode(self.store.data[progress.KEY])
        self.assertEqual(restored['shiritori_settings']['difficulty'], 'easy')

    def test_failed_difficulty_save_then_first_shiritori_open_preserves_other_tab(self):
        first, second = app_from_storage(), app_from_storage()
        first.difficulty, second.difficulty = 'hard', 'normal'
        self.store.fail_write = True
        self.assertFalse(progress.save(first))
        self.store.fail_write = False
        second.shiritori = SimpleNamespace(mode='solo', total=24, difficulty='easy', rival_style='chain')
        self.assertTrue(progress.save(second))
        first.shiritori = SimpleNamespace(mode='solo', total=24, difficulty='hard', rival_style='chain')
        self.assertTrue(progress.save(first))
        self.assertEqual(progress.decode(self.store.data[progress.KEY])['shiritori_settings']['difficulty'], 'easy')

    def test_first_save_with_inherited_difficulty_preserves_other_tab(self):
        first, second = app_from_storage(), app_from_storage()
        first.difficulty, second.difficulty = 'hard', 'normal'
        second.shiritori = SimpleNamespace(mode='solo', total=24, difficulty='easy', rival_style='chain')
        self.assertTrue(progress.save(second))
        first.shiritori = SimpleNamespace(mode='solo', total=24, difficulty='hard', rival_style='chain')
        self.assertTrue(progress.save(first))
        self.assertEqual(progress.decode(self.store.data[progress.KEY])['shiritori_settings']['difficulty'], 'easy')

    def test_first_shiritori_explicit_difficulty_is_not_treated_as_inherited(self):
        first, second = app_from_storage(), app_from_storage()
        first.difficulty, second.difficulty = 'hard', 'normal'
        second.shiritori = SimpleNamespace(mode='solo', total=24, difficulty='normal', rival_style='chain')
        self.assertTrue(progress.save(second))
        first.shiritori = SimpleNamespace(mode='solo', total=24, difficulty='easy', rival_style='chain')
        self.assertTrue(progress.save(first))
        self.assertEqual(progress.decode(self.store.data[progress.KEY])['shiritori_settings']['difficulty'], 'easy')

    def test_malformed_record_container_is_not_overwritten(self):
        data = json.loads(self.store.data[progress.KEY])
        data['best_times'] = {'future-format': 5}
        self.store.data[progress.KEY] = json.dumps(data)
        original = self.store.data[progress.KEY]
        app = app_from_storage()
        self.assertFalse(progress.save(app))
        self.assertEqual(self.store.data[progress.KEY], original)

    def test_more_than_100_existing_records_are_not_overwritten(self):
        for field, entry in (('best_times', [10, 'ordered', 5.0]),
                             ('battle_records', [10, 'ordered', 'easy', 9])):
            with self.subTest(field=field):
                data = {'version': 1, field: [['future']] * 100 + [entry]}
                self.store.data[progress.KEY] = json.dumps(data)
                original = self.store.data[progress.KEY]
                app = app_from_storage()
                self.assertFalse(progress.save(app))
                self.assertEqual(self.store.data[progress.KEY], original)

    def test_new_merged_records_cannot_exceed_safe_limit(self):
        for field, key, value in (('best_times', (10, 'ordered'), 5.0),
                                  ('battle_records', (10, 'ordered', 'easy'), 9)):
            with self.subTest(field=field):
                self.store.data[progress.KEY] = json.dumps({'version': 1, field: [['future']] * 100})
                original = self.store.data[progress.KEY]
                app = app_from_storage()
                getattr(app, field)[key] = value
                self.assertFalse(progress.save(app))
                self.assertEqual(self.store.data[progress.KEY], original)

    def test_concurrent_new_record_indicator_respects_latest_record(self):
        original = self.store.data[progress.KEY]
        for kind in ('practice', 'battle'):
            with self.subTest(kind=kind):
                self.store.data[progress.KEY] = original
                first, second = app_from_storage(), app_from_storage()
                first.play_kind = second.play_kind = kind
                first.selected_mode = second.selected_mode = 'ordered'
                first.difficulty = second.difficulty = 'easy'
                first.round = second.round = SimpleNamespace(max_number=10)
                first.is_new_best = second.is_new_best = True
                if kind == 'practice':
                    first.best_times[(10, 'ordered')] = 5.0
                    second.best_times[(10, 'ordered')] = 8.0
                else:
                    first.battle_records[(10, 'ordered', 'easy')] = 9
                    second.battle_records[(10, 'ordered', 'easy')] = 7
                self.assertTrue(progress.save(first))
                self.assertTrue(progress.save(second))
                self.assertFalse(second.is_new_best)
                self.assertTrue(first.is_new_best)
                self.assertTrue(progress.save(first))
                self.assertTrue(first.is_new_best)


if __name__ == '__main__':
    unittest.main()
