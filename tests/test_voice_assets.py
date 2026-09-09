import hashlib
from pathlib import Path
import struct
import unittest
import wave


class VoiceAssetTests(unittest.TestCase):
    def test_all_callouts_are_distinct_short_non_silent_pcm(self):
        hashes = set()
        for owner in ('you', 'cpu'):
            for level in range(1, 8):
                path = Path(__file__).resolve().parents[1] / 'assets' / 'voices' / 'cute-v2' / f'{owner}-{level}.wav'
                with wave.open(str(path), 'rb') as wav:
                    self.assertEqual(wav.getsampwidth(), 2)
                    self.assertEqual(wav.getnchannels(), 1)
                    duration = wav.getnframes() / wav.getframerate()
                    self.assertGreater(duration, .2)
                    self.assertLess(duration, 2)
                    pcm = wav.readframes(wav.getnframes())
                    samples = struct.unpack(f'<{len(pcm)//2}h', pcm)
                    self.assertGreater(max(map(abs, samples)), 1000)
                    self.assertLess(max(map(abs, samples)), 32767)
                    hashes.add(hashlib.sha256(pcm).digest())
        self.assertEqual(len(hashes), 14)
