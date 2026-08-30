import importlib
import sys
import types
import unittest
from fractions import Fraction


class CapturedSound:
    def __init__(self) -> None:
        self.spec = None

    def set(self, notes, tone, volume, effect, speed) -> None:
        if self.spec is not None:
            raise AssertionError("sound slot was defined more than once")
        self.spec = (notes, tone, volume, effect, speed)


fake_pyxel = types.ModuleType("pyxel")
fake_pyxel.sounds = [CapturedSound() for _ in range(64)]
sys.modules["pyxel"] = fake_pyxel
game = importlib.import_module("game")


class BgmStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        game.NumberRush.configure_sounds()

    def test_loop_is_32_phrases_and_about_eighty_seconds(self) -> None:
        numerator = (
            game.BGM_NOTES_PER_PHRASE * game.BGM_SOUND_SPEED * game.FPS
        )
        self.assertEqual(numerator % game.PYXEL_AUDIO_TICKS_PER_SECOND, 0)
        self.assertEqual(game.BGM_PHRASE_COUNT, 32)
        self.assertEqual(game.BGM_PHRASE_FRAMES, 144)
        self.assertEqual(game.BGM_LOOP_FRAMES, 4608)
        self.assertEqual(
            Fraction(game.BGM_LOOP_FRAMES, game.FPS),
            Fraction(384, 5),
        )

    def test_all_stage_channel_sequences_have_32_phrases(self) -> None:
        for stage in range(3):
            parts = game.NumberRush.bgm_sequences(stage)
            self.assertEqual(len(parts), 3)
            self.assertEqual(
                [len(part) for part in parts],
                [game.BGM_PHRASE_COUNT] * 3,
            )

        with self.assertRaises(KeyError):
            game.NumberRush.bgm_sequences(3)

    def test_every_referenced_sound_is_defined_and_has_32_notes(self) -> None:
        referenced = set()
        for stage in range(3):
            for part in game.NumberRush.bgm_sequences(stage):
                referenced.update(part)

        self.assertTrue(referenced.isdisjoint(range(5)))
        for sound_index in referenced:
            spec = fake_pyxel.sounds[sound_index].spec
            self.assertIsNotNone(spec, f"sound {sound_index} is not defined")
            notes, _tone, _volume, _effect, speed = spec
            self.assertEqual(len(notes.split()), game.BGM_NOTES_PER_PHRASE)
            self.assertEqual(speed, game.BGM_SOUND_SPEED)

    def test_melody_bass_and_drums_use_separate_sound_banks(self) -> None:
        melody_ids = set()
        bass_ids = set()
        drum_ids = set()
        for stage in range(3):
            melody, bass, drums = game.NumberRush.bgm_sequences(stage)
            melody_ids.update(melody)
            bass_ids.update(bass)
            drum_ids.update(drums)

        self.assertTrue(melody_ids.isdisjoint(bass_ids))
        self.assertTrue(melody_ids.isdisjoint(drum_ids))
        self.assertTrue(bass_ids.isdisjoint(drum_ids))

    def test_long_form_is_not_a_short_pattern_repeated(self) -> None:
        for stage in range(3):
            form = list(zip(*game.NumberRush.bgm_sequences(stage)))
            for period in (1, 2, 4, 8, 16):
                repeats = all(
                    form[index] == form[index % period]
                    for index in range(len(form))
                )
                self.assertFalse(
                    repeats,
                    f"stage {stage} repeats every {period} phrases",
                )


if __name__ == "__main__":
    unittest.main()
