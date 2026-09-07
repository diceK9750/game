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

    # Earn the award through real round logic with a deterministic QA clock.
    app.start_round("ordered")
    now = [0.0]
    app.round = game.BattleRound(max_number=40, clock=lambda: now[0])
    app.round.start("ordered")
    while not app.round.is_finished:
        now[0] = app.round.ready_at + 0.1
        app.handle_tap(app.round.board_cells.index(app.round.current_target))
    for age in (0, 45, 90):
        with patch.object(pyxel, "frame_count", app.result_started_frame + age):
            app.draw()
            pyxel.screenshot(str(out / f"perfect-{age:03d}.png"), scale=2)
    app.screen = "review"
    app.draw()
    pyxel.screenshot(str(out / "review.png"), scale=2)
    app.screen = "help"
    app.draw()
    pyxel.screenshot(str(out / "help.png"), scale=2)
    app.play_kind = "practice"
    app.start_round("random")
    app.hint_used = True
    app.hint_until = pyxel.frame_count + 120
    app.draw()
    pyxel.screenshot(str(out / "practice-hint.png"), scale=2)
    pyxel.stop()

    pyxel.cls(game.BACKGROUND)
    for row, species in enumerate(("rabbit", "red_panda")):
        for col, action in enumerate(ACTIONS):
            x, y = 20 + col * 102, 62 + row * 148
            with patch.object(pyxel, "frame_count", 42):
                draw_rival(pyxel, x, y, species, action)
            pyxel.text(x, y + 70, action.upper(), game.CARD)
    pyxel.screenshot(str(out / "character-poses.png"), scale=2)

    audio_paths = []
    for battle, label, stage in ((True, "skybound-sprint", 1),
                                 (True, "skybound-sprint-opening", 0),
                                 (True, "skybound-sprint-finale", 2),
                                 (False, "riverlight-walk", 1)):
        configure_bgm(pyxel.sounds, battle=battle)
        # Write two copies so the first loop boundary is definitely in the WAV.
        parts = [part * 2 for part in sequences(stage, battle=battle)]
        pyxel.musics[0].set(*parts)
        pyxel.musics[0].save(str(out / label), 80.8)
        audio_paths.append(out / f"{label}.wav")
    configure_scene_bgm(pyxel.sounds)
    for name, ids in SCENE_TRACKS.items():
        pyxel.musics[0].set(*([index] for index in ids))
        speed, bars, _ = SCENE_SCORES[name]
        pyxel.musics[0].save(str(out / name), len(bars) * 32 * speed / 120)
        audio_paths.append(out / f"{name}.wav")

    # Validate the real engine's PCM, not an approximation of the synthesizer.
    for path in sorted(audio_paths):
        with wave.open(str(path), "rb") as wav:
            assert wav.getsampwidth() == 2
            rate, channels, frames = wav.getframerate(), wav.getnchannels(), wav.getnframes()
            values = array("h", wav.readframes(frames))
        peak = max(abs(value) for value in values)
        assert 0 < peak < 32767, (path.name, peak)
        duration = frames / rate
        print(f"{path.name}: {duration:.3f}s, peak={peak}/32767")
        if path.stem.startswith("skybound-sprint") or path.stem == "riverlight-walk":
            seam = round(76.8 * rate) * channels
            assert any(values[seam:seam + rate * channels]), "Silent second loop"
            jump = max(abs(values[seam + c] - values[seam + c - channels])
                       for c in range(channels))
            assert jump < 2000, (path.name, "loop discontinuity", jump)
            print(f"  loop boundary sample jump: {jump}")
    print(f"Preview files: {out}")


if __name__ == "__main__":
    main()
