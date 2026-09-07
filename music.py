"""Lantern League — original chiptune suite, no sampled or quoted music.

Practice: 112.5 BPM / 36 bars. Battle: 150 BPM / 48 bars. Both loop in
76.8 seconds, within Pyxel's 64 sound slots. Scenes keep their own arrangements.
One bar is eight eighth notes / 32 audio steps; all parts use the same clock.
"""

SPEED = 8
TICKS = 32
FORM = tuple(range(32)) + (24, 25, 30, 31)
PHRASE_COUNT = len(FORM)
BATTLE_SPEED = 6
BATTLE_FORM = tuple(range(32)) + tuple(range(16))
BATTLE_PHRASE_COUNT = len(BATTLE_FORM)

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

# Skybound Sprint / D major. Springy rising hook, spacious bridge, bright lift.
# The final A reprise resolves its dominant pickup into the opening D.
BATTLE_SCORE = (
    "d4 f#4 a4:1.5 f#4:0.5 e4 f#4 d4 r",
    "b3 d4 f#4:2 a4 f#4 e4 r",
    "g4:1.5 f#4:0.5 e4 d4 b3 d4 e4 r",
    "c#4 e4 a4:2 g4 e4 c#4 r",
    "f#4 a4 b4:2 a4 f#4 e4 r",
    "b4:1.5 a4:0.5 f#4 d4 f#4 a4 b4 r",
    "g4 b4 a4:2 g4 e4 d4 r",
    "e4:2 c#4 a3 b3 c#4 e4 r",
    "d4 f#4 a4 b4 a4:0.5 g4:0.5 f#4 e4 r",
    "b4 a4 f#4:2 d4 e4 f#4 r",
    "g4:2 b4 a4 g4 f#4 e4 r",
    "a4 g4 e4 c#4 e4:2 a4 r",
    "f#4 a4 b4:1.5 a4:0.5 g4 f#4 e4 r",
    "g4 b4 a4:2 b4 a4 g4 r",
    "e4 g4 b4 a4 g4:2 e4 r",
    "c#4 e4 a4:2 e4 c#4 a3 r",
    "b3:2 d4:2 f#4 e4 d4 r",
    "c#4:2 e4:2 a4 g4 e4 r",
    "b3 d4 g4:2 f#4 e4 d4 r",
    "f#4:2 e4 d4 a3:2 c#4 r",
    "b3 d4 f#4 a4 b4:2 a4 r",
    "a4 g4 f#4:2 e4 c#4 a3 r",
    "b3 e4 g4:2 b4 a4 g4 r",
    "e4:2 c#4 a3 c#4 e4 a4 r",
    "a4 b4 a4 g4 f#4:1.5 e4:0.5 d4 r",
    "f#4 a4 b4 a4 g4 f#4 e4 r",
    "b4:1.5 a4:0.5 g4 f#4 e4 g4 b4 r",
    "a4 e4 c#4 e4 a4:2 g4 r",
    "f#4 a4 b4:2 a4 f#4 d4 r",
    "g4:2 b4 a4 b4 a4 g4 r",
    "e4 g4 b4:1.5 a4:0.5 g4 e4 d4 r",
    "c#4 e4 a4 g4 e4:2 c#4 r",
)
BATTLE_CHORDS = ("D", "Bm", "G", "A", "D", "Bm", "Em", "A") + (
    "D", "Bm", "G", "A", "D", "G", "Em", "A",
    "Bm", "F#m", "G", "D", "Bm", "F#m", "Em", "A",
    "D", "Bm", "G", "A", "D", "G", "Em", "A",
)
BATTLE_BASS = {
    "D": ("d2", "a2", "f#2"), "Bm": ("b1", "f#2", "d2"),
    "G": ("g1", "d2", "b1"), "A": ("a1", "e2", "c#2"),
    "Em": ("e2", "b2", "g2"), "F#m": ("f#1", "c#2", "a1"),
}


def expand_battle_bar(score, peak=3):
    """Sixteenth-note pickups with shaped releases, not hard sustained pulses."""
    from fractions import Fraction
    notes, volumes = [], []
    for event in score.split():
        pitch, _, length = event.partition(":")
        duration = Fraction(length or 1) * 4
        if duration.denominator != 1 or duration < 2:
            raise ValueError("Battle duration must be a whole step, at least a sixteenth")
        duration = int(duration)
        if pitch == "r":
            notes.extend(["r"] * duration)
            volumes.extend([0] * duration)
        else:
            envelope = ([max(1, peak - 1), 0] if duration == 2 else
                        [max(1, peak - 1)] + [peak] * (duration - 3) + [1, 0])
            notes.extend([pitch] * (duration - 1) + ["r"])
            volumes.extend(envelope)
    if len(notes) != TICKS:
        raise ValueError(f"Battle bar must be eight eighth notes: {score}")
    return " ".join(notes), "".join(map(str, volumes))


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


def configure_battle_bgm(sounds):
    for index, bar in enumerate(BATTLE_SCORE, 8):
        notes, volume = expand_battle_bar(bar)
        # A soft triangle lead stays below the dedicated SFX channel.
        sounds[index].set(notes, "t", volume, "n", BATTLE_SPEED)
    for index, (root, fifth, third) in enumerate(BATTLE_BASS.values(), 40):
        pattern = f"{root}:1.5 r:0.5 {fifth} {root} {root}:1.5 {third}:0.5 {fifth} r"
        notes, volume = expand_battle_bar(pattern, peak=2)
        sounds[index].set(notes, "t", volume, "n", BATTLE_SPEED)
    for stage in range(3):
        for ending in (False, True):
            notes, tones = ["r"] * TICKS, ["n"] * TICKS
            volumes, effects = ["0"] * TICKS, ["n"] * TICKS
            # Kick and backbeat anchor an eighth-note hat groove.
            hits = {0: 'kick', 4: 'hat', 8: 'snare', 12: 'hat',
                    16: 'kick', 20: 'hat', 24: 'snare', 28: 'hat'}
            if stage >= 1:
                hits[14] = 'kick'
            if stage == 2:
                hits.update({6: 'hat', 22: 'kick'})
            if ending:
                hits[26] = 'ghost'
            for step, kind in sorted(hits.items()):
                if kind == 'kick':
                    for offset, pitch, level in ((0, 'd1', '3'), (1, 'c1', '1')):
                        notes[step+offset], tones[step+offset] = pitch, 't'
                        volumes[step+offset], effects[step+offset] = level, 'f'
                else:
                    pitch, level = ('d1', '2') if kind == 'snare' else ('f#2', '1')
                    notes[step], volumes[step], effects[step] = pitch, level, 'f'
            sounds[48 + stage + 3 * ending].set(
                " ".join(notes), "".join(tones), "".join(volumes), "".join(effects), BATTLE_SPEED)


def configure_bgm(sounds, *, battle=False):
    if battle:
        configure_battle_bgm(sounds)
        return
    for index, bar in enumerate(SCORE, 8):
        notes, volume = expand_bar(bar, peak=3)
        sounds[index].set(notes, "t", volume, "n", SPEED)
    for index, (root, fifth, third) in enumerate(BASS.values(), 40):
        # Syncopation comes from placement, not extra loudness or a faster clock.
        pattern = f"{root}:2 r {fifth} {third}:2 {fifth} r"
        notes, volume = expand_bar(pattern, peak=2)
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
            if ending:
                # A little turnaround before the silence, never a crash at wrap.
                hits.pop(28, None)
            for step, (note, tone, volume) in hits.items():
                notes[step], tones[step], volumes[step], effects[step] = note, tone, volume, "f"
            sounds[48 + stage + 3 * ending].set(
                " ".join(notes), "".join(tones), "".join(volumes), "".join(effects), SPEED)


def sequences(stage, *, battle=False):
    if stage not in (0, 1, 2):
        raise KeyError(stage)
    harmony, chords = (BATTLE_BASS, BATTLE_CHORDS) if battle else (BASS, CHORDS)
    form = BATTLE_FORM if battle else FORM
    bass_ids = {chord: index for index, chord in enumerate(harmony, 40)}
    # The bridge breathes, then the reprise returns to the selected intensity.
    drums = [48 + (max(0, stage - 1) if 16 <= bar < 24 else stage)
             for bar in range(len(form))]
    for bar in (range(7, len(form), 8) if battle else (7, 15, 23, 31, 35)):
        drums[bar] += 3
    return [8 + bar for bar in form], [bass_ids[chords[bar]] for bar in form], drums


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
