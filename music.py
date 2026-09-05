"""Forest Stroll: 100 BPM / C major / 32 bars / 76.8 seconds.

Original score. Every arrangement shares the same melody and harmony, so
progress changes add rhythmic detail without suddenly changing the song.
Durations in the score are eighth notes (four Pyxel ticks each).
"""

SPEED = 9
TICKS = 32

# A / A' / B / return. Phrases breathe instead of playing constant sixteenths.
# Each bar has eight eighth notes, including rests.
SCORE = (
    "e3:2 g3 a3 g3:2 r:2",          # C: invitation
    "e3:2 a3:2 c4 b3 a3 r",        # Am: answer
    "a3:2 g3 f3 a3:2 r:2",         # F
    "g3:2 d3 g3 b3:2 r:2",         # G
    "e3 g3 c4:2 b3 g3 e3 r",       # C
    "g3:2 e3 g3 b3:2 r:2",         # Em
    "a3:2 f3:2 g3 a3 f3 r",        # F
    "d3:2 g3:2 a3 b3 g3 r",        # G
    "e3:2 g3 a3 c4:2 g3 r",        # C: varied invitation
    "a3:2 c4:2 b3 a3 e3 r",        # Am
    "f3 a3 c4:2 a3 g3 f3 r",       # F
    "g3:2 b3 a3 g3:2 r:2",         # G
    "e3:2 g3:2 c4:3 r",            # C: held response
    "b3:2 g3 e3 g3:2 r:2",         # Em
    "a3 g3 f3:2 a3:2 r:2",         # F
    "g3:2 a3 b3 d4:2 b3 r",        # G: into bridge
    "c4:2 a3:2 e3 g3 a3 r",        # Am: warmer bridge
    "g3:2 b3:2 e4:2 r:2",          # Em
    "c4:2 a3 g3 f3:2 r:2",         # F
    "a3:2 f3:2 d3 f3 a3 r",        # Dm
    "a3 c4 e4:2 d4 c4 a3 r",       # Am: one small peak
    "b3:2 g3:2 e3:3 r",            # Em
    "f3 a3 c4:2 a3:2 g3 r",        # F
    "b3 a3 g3:2 d3:2 r:2",         # G
    "e3:2 g3 a3 g3:2 c4 r",        # C: return home
    "c4:2 b3 a3 e3:2 r:2",         # Am
    "a3:2 g3 f3 c4:2 a3 r",        # F
    "b3:2 a3 g3 d3:2 r:2",         # G
    "e3 g3 c4:2 g3:2 e3 r",        # C
    "a3:2 c4 b3 a3:2 r:2",         # Am
    "a3 g3 f3:2 e3 f3 a3 r",       # F
    "g3:2 d3:2 b3:2 r:2",          # G: breath, then E over C
)

CHORDS = ("C", "Am", "F", "G", "C", "Em", "F", "G") * 2 + (
    "Am", "Em", "F", "Dm", "Am", "Em", "F", "G",
    "C", "Am", "F", "G", "C", "Am", "F", "G",
)
BASS = {
    "C": ("c2", "g2", "e2"),
    "Am": ("a1", "e2", "c2"),
    "F": ("f1", "c2", "a1"),
    "G": ("g1", "d2", "b1"),
    "Em": ("e1", "b1", "g1"),
    "Dm": ("d2", "a2", "f2"),
}


def expand_bar(score, peak=4):
    """Sustain notes with a gentle envelope; reserve a quiet tail for breathing."""
    notes, volumes = [], []
    for event in score.split():
        pitch, _, length = event.partition(":")
        duration = int(length or 1) * 4
        notes.extend([pitch] * duration)
        if pitch == "r":
            volumes.extend([0] * duration)
        else:
            volumes.extend([max(1, peak - 1)] + [peak] * (duration - 3)
                           + [max(1, peak - 1), 1])
    if len(notes) != TICKS:
        raise ValueError(f"Bar must be eight eighth notes: {score}")
    return " ".join(notes), "".join(map(str, volumes))


def configure_bgm(sounds):
    for index, bar in enumerate(SCORE, 8):
        notes, volume = expand_bar(bar)
        sounds[index].set(notes, "t", volume, "n", SPEED)
    for index, (root, fifth, third) in enumerate(BASS.values(), 40):
        # Root and fifth establish a clear pulse; a quiet third colors the chord.
        notes, volume = expand_bar(f"{root}:2 r {fifth} {root}:2 {third} r", peak=3)
        sounds[index].set(notes, "t", volume, "n", SPEED)
    for stage in range(3):
        for ending in (False, True):
            notes, tones, volumes, effects = ["r"] * TICKS, ["n"] * TICKS, ["0"] * TICKS, ["n"] * TICKS
            hits = {0: ("c1", "t", "2"), 8: ("c1", "n", "1"),
                    16: ("c1", "t", "2"), 24: ("c1", "n", "1")}
            if stage >= 1:
                hits.update({4: ("c2", "n", "1"), 20: ("c2", "n", "1")})
            if stage == 2:
                hits.update({12: ("c2", "n", "1"), 28: ("c2", "n", "1")})
            if ending:
                hits.pop(28, None)  # Never end with a noisy fill at the loop seam.
            for tick, (note, tone, volume) in hits.items():
                notes[tick], tones[tick], volumes[tick], effects[tick] = note, tone, volume, "f"
            sounds[48 + stage + 3 * ending].set(
                " ".join(notes), "".join(tones), "".join(volumes), "".join(effects), SPEED)


def sequences(stage):
    if stage not in (0, 1, 2):
        raise KeyError(stage)
    bass_ids = {chord: index for index, chord in enumerate(BASS, 40)}
    return list(range(8, 40)), [bass_ids[chord] for chord in CHORDS], [48 + stage] * 31 + [51 + stage]


# Each scene gets two dedicated slots; gameplay and SFX are never overwritten.
# (tempo speed, melody bars, chord roots). All tunes are original.
SCENE_SCORES = {
    "menu": (12, (
        "e3:2 g3:2 c4:2 r:2", "b3 a3 g3:2 e3:2 r:2",
        "a3:2 c4:2 a3 g3 f3 r", "g3:3 b3 d4:2 r:2",
        "g3:2 e3 g3 c4:2 r:2", "c4:2 a3:2 e3 g3 a3 r",
        "a3 g3 f3:2 a3:2 r:2", "g3:2 d3:2 b3:2 r:2",
    ), ("c2", "e2", "f2", "g2", "c2", "a1", "f2", "g2")),
    "wait": (15, (
        "e3:3 r g3:2 r:2", "d3:3 r g3:2 r:2",
    ), ("c2", "g1")),
    "countdown": (6, (
        "c3 r e3 r g3 r c4 r", "d3 r g3 r b3 r d4 r",
    ), ("c2", "g1")),
    "win": (9, (
        "c4:2 e4 g4 e4:2 r:2", "c4:2 a3 c4 f4:2 r:2",
        "d4:2 b3 g3 b3 d4 r:2", "e4:2 c4:3 g3 r:2",
    ), ("c2", "f2", "g2", "c2")),
    "loss": (12, (
        "e3:2 c3:2 a2:2 r:2", "f3:2 e3 d3 c3:2 r:2",
        "d3:2 g3:2 b3 a3 g3 r", "e3:2 g3:2 c4:2 r:2",
    ), ("a1", "f1", "g1", "c2")),
}
SCENE_TRACKS = {name: (54 + i * 2, 55 + i * 2)
                for i, name in enumerate(SCENE_SCORES)}


def configure_scene_bgm(sounds):
    for name, (speed, bars, roots) in SCENE_SCORES.items():
        melody, melody_volume, bass, bass_volume = [], [], [], []
        for bar, root in zip(bars, roots):
            notes, volume = expand_bar(bar, peak=2 if name == "wait" else 3)
            melody.append(notes)
            melody_volume.append(volume)
            notes, volume = expand_bar(f"{root}:3 r {root}:2 r:2", peak=2)
            bass.append(notes)
            bass_volume.append(volume)
        lead_id, bass_id = SCENE_TRACKS[name]
        sounds[lead_id].set(" ".join(melody), "t", "".join(melody_volume), "n", speed)
        sounds[bass_id].set(" ".join(bass), "t", "".join(bass_volume), "n", speed)
