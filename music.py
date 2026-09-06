"""Lantern League — original chiptune suite, no sampled or quoted music.

Gameplay: 112.5 BPM, 36 bars, 76.8 seconds. 32 written bars plus a four-bar
reprise fit Pyxel's 64 sound slots. Scenes share motifs, not identical loops.
One bar is eight eighth notes / 32 audio steps; all parts use the same clock.
"""

SPEED = 8
TICKS = 32
FORM = tuple(range(32)) + (24, 25, 30, 31)
PHRASE_COUNT = len(FORM)

# Riverlight Walk / G major. Long answers and rests leave room for thinking.
SCORE = (
    "b3:2 d4 e4 d4:2 r:2", "b3:2 g3:2 e3 g3 b3 r",
    "e4:2 d4 c4 e4:2 r:2", "a3:2 f#3 a3 d4:2 r:2",
    "b3 d4 g4:2 f#4 d4 b3 r", "d4:2 b3 a3 f#3:2 r:2",
    "e4 d4 c4:2 e4:2 g3 r", "a3:2 d4:2 c4 a3 f#3 r",
    "d4:2 b3 d4 e4:2 d4 r", "g3 b3 e4:2 d4 b3 g3 r",
    "c4:2 e4:2 g4 e4 d4 r", "f#4:2 e4 d4 a3:2 r:2",
    "d4 b3 g3:2 b3 d4 g4 r", "f#4 d4 b3:2 a3 f#3 d3 r",
    "e4:2 c4:2 a3 c4 e4 r", "f#4:2 e4 d4 c4:2 r:2",
    "b3:3 g3 e3:2 r:2", "a3:2 c4:2 e4:2 r:2",
    "g4:2 e4 d4 c4:2 r:2", "f#4:2 d4:2 a3:2 r:2",
    "g3 b3 e4:2 g4 f#4 e4 r", "e4:2 c4 a3 c4:2 r:2",
    "d4:2 b3 a3 f#3:2 r:2", "a3 c4 d4:2 f#4:2 r:2",
    "b3:2 d4 e4 g4:2 d4 r", "e4:2 b3 g3 e3:2 r:2",
    "g4 e4 c4:2 e4:2 d4 r", "f#4:2 a4 f#4 d4:2 r:2",
    "g4:2 d4 b3 d4:2 r:2", "e4 d4 b3:2 g3 b3 e4 r",
    "e4:2 c4 a3 c4:2 r:2", "a3:2 f#3:2 d4:2 r:2",
)
CHORDS = ("G", "Em", "C", "D", "G", "Bm", "C", "D") * 2 + (
    "Em", "Am", "C", "D", "Em", "Am", "Bm", "D",
    "G", "Em", "C", "D", "G", "Em", "Am", "D",
)
BASS = {
    "G": ("g1", "d2", "b1"), "Em": ("e2", "b2", "g2"),
    "C": ("c2", "g2", "e2"), "D": ("d2", "a2", "f#2"),
    "Bm": ("b1", "f#2", "d2"), "Am": ("a1", "e2", "c2"),
}

# Lantern Rivals / E minor. A compact call, a descending answer, then a lift.
# B major supplies D# only at cadences; the middle eight opens into G major.
BATTLE_SCORE = (
    "e3 b3 e4:2 g4 f#4 e4 r", "g3:2 e4 d4 c4 g3 e3 r",
    "a3 d4 f#4 e4 d4 a3 c4 r", "b3 r d#4 f#4 e4 d#4 b3 r",
    "e4:2 b3 e4 g4:2 f#4 r", "e4 d4 c4:2 g3 c4 e4 r",
    "c4 e4 a3 r b3 c4 e4 r", "f#4 e4 d#4 b3 f#3:2 r:2",
    "b3 e4 g4:2 f#4 e4 d4 r", "e4 g4 c4:2 d4 e4 g4 r",
    "f#4 a4 f#4:2 e4 d4 a3 r", "d#4 f#4 b3 r d#4:2 b3 r",
    "g4 f#4 e4 b3 e4:2 g4 r", "e4:2 c4 g3 c4 d4 e4 r",
    "a3 c4 e4:2 d4 c4 a3 r", "b3 d#4 f#4:2 e4 d#4 b3 r",
    "d4:2 b3 d4 g4:2 r:2", "g4 e4 c4:2 e4:2 d4 r",
    "a3:2 c4 e4 d4:2 c4 r", "f#4 e4 d4:2 a3:2 r:2",
    "b3 d4 g4:2 f#4 d4 b3 r", "c4:2 e4 g4 e4 d4 c4 r",
    "a3 c4 e4:2 g4 e4 c4 r", "f#4:2 d#4 b3 f#3:2 r:2",
    "e4 b3 e4 g4 f#4:2 e4 r", "g4 e4 c4:2 d4 e4 g4 r",
    "a4 f#4 d4:2 e4 f#4 a4 r", "f#4 d#4 b3 r d#4 f#4 b3 r",
    "g4:2 f#4 e4 b3 e4 g4 r", "e4 d4 c4 g3 c4:2 e4 r",
    "e4 c4 a3:2 c4 e4 d4 r", "d#4:2 b3:2 f#3:2 r:2",
)
BATTLE_CHORDS = ("Em", "C", "D", "B", "Em", "C", "Am", "B") * 2 + (
    "G", "C", "Am", "D", "G", "C", "Am", "B",
    "Em", "C", "D", "B", "Em", "C", "Am", "B",
)
BATTLE_BASS = {
    "Em": ("e2", "b2", "g2"), "C": ("c2", "g2", "e2"),
    "D": ("d2", "a2", "f#2"), "B": ("b1", "f#2", "d#2"),
    "Am": ("a1", "e2", "c2"), "G": ("g1", "d2", "b1"),
}


def expand_bar(score, peak=3):
    """Short release and a silent articulation step avoid hard note edges."""
    notes, volumes = [], []
    for event in score.split():
        pitch, _, length = event.partition(":")
        duration = int(length or 1) * 4
        if duration < 4:
            raise ValueError("Duration must be at least one eighth note")
        if pitch == "r":
            notes.extend(["r"] * duration)
            volumes.extend([0] * duration)
        else:
            notes.extend([pitch] * (duration - 1) + ["r"])
            volumes.extend([max(1, peak - 1)] + [peak] * (duration - 4)
                           + [max(1, peak - 1), 1, 0])
    if len(notes) != TICKS:
        raise ValueError(f"Bar must be eight eighth notes: {score}")
    return " ".join(notes), "".join(map(str, volumes))


def configure_bgm(sounds, *, battle=False):
    score, harmony = (BATTLE_SCORE, BATTLE_BASS) if battle else (SCORE, BASS)
    for index, bar in enumerate(score, 8):
        notes, volume = expand_bar(bar, peak=3)
        sounds[index].set(notes, "p" if battle else "t", volume, "n", SPEED)
    for index, (root, fifth, third) in enumerate(harmony.values(), 40):
        # Syncopation comes from placement, not extra loudness or a faster clock.
        pattern = (f"{root} r {root} {fifth} {root} {third} {fifth} r" if battle
                   else f"{root}:2 r {fifth} {third}:2 {fifth} r")
        notes, volume = expand_bar(pattern, peak=3 if battle else 2)
        sounds[index].set(notes, "t", volume, "n", SPEED)
    for stage in range(3):
        for ending in (False, True):
            notes, tones = ["r"] * TICKS, ["n"] * TICKS
            volumes, effects = ["0"] * TICKS, ["n"] * TICKS
            hits = {0: ("c1", "t", "2"), 8: ("c1", "n", "1"),
                    16: ("c1", "t", "2"), 24: ("c1", "n", "1")}
            if stage >= 1:
                hits.update({4: ("c2", "n", "1"), 20: ("c2", "n", "1")})
            if stage == 2:
                hits.update({12: ("c2", "n", "1"), 28: ("c2", "n", "1")})
            if battle:
                hits.update({0: ("c1", "t", "3"), 8: ("d1", "n", "2"),
                             16: ("c1", "t", "3"), 24: ("d1", "n", "2"),
                             4: ("c2", "n", "1"), 20: ("c2", "n", "1")})
                if stage >= 1:
                    hits.update({14: ("c1", "t", "2"), 28: ("c2", "n", "1")})
                if stage == 2:
                    hits.update({6: ("c2", "n", "1"), 22: ("c1", "t", "2")})
            if ending:
                # A little turnaround before the silence, never a crash at wrap.
                hits.pop(28, None)
                if battle:
                    hits[26] = ("d1", "n", "1")
            for step, (note, tone, volume) in hits.items():
                notes[step], tones[step], volumes[step], effects[step] = note, tone, volume, "f"
            sounds[48 + stage + 3 * ending].set(
                " ".join(notes), "".join(tones), "".join(volumes), "".join(effects), SPEED)


def sequences(stage, *, battle=False):
    if stage not in (0, 1, 2):
        raise KeyError(stage)
    harmony, chords = (BATTLE_BASS, BATTLE_CHORDS) if battle else (BASS, CHORDS)
    bass_ids = {chord: index for index, chord in enumerate(harmony, 40)}
    # The bridge breathes, then the reprise returns to the selected intensity.
    drums = [48 + (max(0, stage - 1) if 16 <= bar < 24 else stage)
             for bar in range(PHRASE_COUNT)]
    for bar in (7, 15, 23, 31, 35):
        drums[bar] += 3
    return [8 + bar for bar in FORM], [bass_ids[chords[bar]] for bar in FORM], drums


# Dedicated two-channel scene arrangements, all sharing the new suite's key world.
# speed, eight-eighth-note bars, bass roots
SCENE_SCORES = {
    "menu": (11, (
        "b3:2 d4 e4 d4:2 r:2", "g3 b3 e4:2 d4 b3 g3 r",
        "e4:2 g4:2 e4 d4 c4 r", "a3:2 d4 f#4 e4 d4 a3 r",
        "d4 b3 g3:2 b3 d4 g4 r", "e4:2 b3:2 g3 b3 e4 r",
        "c4 e4 a3:2 c4:2 r:2", "f#4:2 d4:2 a3:2 r:2",
    ), ("g1", "e2", "c2", "d2", "g1", "e2", "a1", "d2")),
    "wait": (14, (
        "b3:3 r g3:2 r:2", "a3:3 r f#3:2 r:2",
    ), ("g1", "d2")),
    "countdown": (6, (
        "e3 r g3 r b3 r e4 r", "f#3 r b3 r d#4 r f#4 r",
    ), ("e2", "b1")),
    "win": (8, (
        "b3 d4 g4:2 a4 g4 d4 r", "e4:2 g4 c4 e4:2 r:2",
        "f#4 a4 d4:2 f#4:2 e4 r", "d4 b3 g3:2 g4:2 r:2",
    ), ("g1", "c2", "d2", "g1")),
    "loss": (12, (
        "g3:2 e3:2 b2:2 r:2", "a3:2 g3 e3 c3:2 r:2",
        "f#3:2 a3 d4:2 c4 r:2", "b3:2 d4:2 g3:2 r:2",
    ), ("e2", "c2", "d2", "g1")),
    "perfect": (8, (
        "g3 b3 d4 g4:2 b4 a4 r", "g4:2 e4 g4 c4:2 r:2",
        "f#4 a4 d4:2 e4 f#4 a4 r", "g4:3 d4 b3:2 r:2",
        "b3 d4 g4:2 d4 g4 b4 r", "a4 g4 e4:2 c4 e4 g4 r",
        "f#4:2 d4 a3 d4 f#4 a4 r", "g4:2 d4 b3 g3:2 r:2",
    ), ("g1", "c2", "d2", "g1", "g1", "c2", "d2", "g1")),
}
SCENE_TRACKS = {name: (54 + i * 2, 55 + i * 2)
                for i, name in enumerate(SCENE_SCORES) if name != "perfect"}
# Two unused slots between the six bass patches and drum bank; stay within 64.
SCENE_TRACKS["perfect"] = (46, 47)


def configure_scene_bgm(sounds):
    for name, (speed, bars, roots) in SCENE_SCORES.items():
        melody, melody_volume, bass, bass_volume = [], [], [], []
        for bar, root in zip(bars, roots):
            notes, volume = expand_bar(bar, peak=2 if name == "wait" else 3)
            melody.append(notes)
            melody_volume.append(volume)
            # Octave replies give scene music motion without a percussion channel.
            octave = root[:-1] + str(int(root[-1]) + 1)
            pattern = (f"{root}:3 r {root}:2 r:2" if name == "wait"
                       else f"{root}:2 r {octave} {root}:2 r:2")
            notes, volume = expand_bar(pattern, peak=2)
            bass.append(notes)
            bass_volume.append(volume)
        lead_id, bass_id = SCENE_TRACKS[name]
        sounds[lead_id].set(" ".join(melody), "t", "".join(melody_volume), "n", speed)
        sounds[bass_id].set(" ".join(bass), "t", "".join(bass_volume), "n", speed)
