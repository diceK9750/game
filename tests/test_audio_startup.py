"""Exercise the pre-SDL boundary without importing/launching the native engine."""
import ast
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


class AudioStartupTests(unittest.TestCase):
    def run_preflight(self, result=True, error=None, native=False):
        tree = ast.parse((Path(__file__).parents[1] / 'game.py').read_text(encoding='utf-8'))
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'prepare_web_audio')
        ns = {'os': os, 'browser_document': None if native else object()}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), 'game.py', 'exec'), ns)
        prepare = Mock(return_value=result, side_effect=error)
        module = object()
        window = SimpleNamespace(numberRushAudio=SimpleNamespace(prepare=prepare),
                                 pyxelContext=SimpleNamespace(pyodide=SimpleNamespace(_module=module)))
        with patch.dict('sys.modules', {'js': SimpleNamespace(window=window)}), \
             patch.dict(os.environ, {}, clear=True):
            available = ns['prepare_web_audio']()
            return available, os.environ.get('SDL_AUDIODRIVER'), prepare, module

    def test_native_and_accepted_web_audio_do_not_change_driver(self):
        for native in (True, False):
            available, driver, prepare, module = self.run_preflight(native=native)
            self.assertTrue(available)
            self.assertIsNone(driver)
            if native:
                prepare.assert_not_called()
            else:
                prepare.assert_called_once_with(module)

    def test_rejected_web_audio_selects_dummy_before_init(self):
        available, driver, _, _ = self.run_preflight(result=False)
        self.assertFalse(available)
        self.assertEqual(driver, 'dummy')

    def test_broken_browser_bridge_also_falls_back(self):
        available, driver, _, _ = self.run_preflight(error=RuntimeError('bridge unavailable'))
        self.assertFalse(available)
        self.assertEqual(driver, 'dummy')
