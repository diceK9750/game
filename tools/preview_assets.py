"""Render the actual Pyxel artwork and music for local review.

Run: .venv/Scripts/python.exe tools/preview_assets.py
Outputs are generated under the ignored build/preview directory.
"""

from pathlib import Path
import sys
import wave
from array import array
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pyxel
import game
from characters import ACTIONS, draw_rival
from music import configure_bgm, configure_scene_bgm, sequences, SCENE_TRACKS, SCENE_SCORES


def main():
    out = Path(__file__).resolve().parents[1] / "build" / "preview"
    out.mkdir(parents=True, exist_ok=True)
    pyxel.init(640, 360, headless=True)
    with patch.object(pyxel, "init"), patch.object(pyxel, "run"):
        app = game.NumberRush()
    app.draw()
    pyxel.screenshot(str(out / "menu.png"), scale=2)
    app.start_round("ordered")
    pyxel.stop()
    app.draw()
    pyxel.screenshot(str(out / "battle.png"), scale=2)
    app.handle_tap(app.round.board_cells.index(1))
    app.draw()
    pyxel.screenshot(str(out / "correct.png"), scale=2)
    app.round.ready_at = app.round.elapsed()  # A separate staged QA image, not gameplay.
    app.handle_tap(app.round.board_cells.index(3))
    app.draw()
    pyxel.screenshot(str(out / "miss.png"), scale=2)
    pyxel.stop()

    pyxel.cls(game.BACKGROUND)
    for row, species in enumerate(("otter", "fox")):
        for col, action in enumerate(ACTIONS):
            x, y = 20 + col * 102, 62 + row * 148
            draw_rival(pyxel, x, y, species, action)
            pyxel.text(x, y + 70, action.upper(), game.CARD)
    pyxel.screenshot(str(out / "character-poses.png"), scale=2)

    for battle, label in ((True, "lantern-rivals"), (False, "riverlight-walk")):
        configure_bgm(pyxel.sounds, battle=battle)
        # Write two copies so the first loop boundary is definitely in the WAV.
        parts = [part * 2 for part in sequences(1, battle=battle)]
        pyxel.musics[0].set(*parts)
        pyxel.musics[0].save(str(out / label), 80.8)
    configure_scene_bgm(pyxel.sounds)
    for name, ids in SCENE_TRACKS.items():
        pyxel.musics[0].set(*([index] for index in ids))
        speed, bars, _ = SCENE_SCORES[name]
        pyxel.musics[0].save(str(out / name), len(bars) * 32 * speed / 120)

    # Validate the real engine's PCM, not an approximation of the synthesizer.
    for path in sorted(out.glob("*.wav")):
        with wave.open(str(path), "rb") as wav:
            assert wav.getsampwidth() == 2
            rate, channels, frames = wav.getframerate(), wav.getnchannels(), wav.getnframes()
            values = array("h", wav.readframes(frames))
        peak = max(abs(value) for value in values)
        assert 0 < peak < 32767, (path.name, peak)
        duration = frames / rate
        print(f"{path.name}: {duration:.3f}s, peak={peak}/32767")
        if path.stem in {"lantern-rivals", "riverlight-walk"}:
            seam = round(76.8 * rate) * channels
            assert any(values[seam:seam + rate * channels]), "Silent second loop"
            jump = max(abs(values[seam + c] - values[seam + c - channels])
                       for c in range(channels))
            assert jump < 2000, (path.name, "loop discontinuity", jump)
            print(f"  loop boundary sample jump: {jump}")
    print(f"Preview files: {out}")


if __name__ == "__main__":
    main()
