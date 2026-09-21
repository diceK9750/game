# Safari audio startup containment (local, 2026-09-21)

Base: `853f0ca1fc422b9bdf2306f62429fdcaa0b6507c`, main. No deployment.

## Evidence and limits

The user observed `NotSupportedError: Sample rate is not in the supported range.`
at native `createBuffer` followed by WASM frames on iPhone Safari. The failing
device's numerical sample rate and full native stack are **not captured**.
Do not describe a guessed zero, 22050 or 48000 Hz as that device's measured value.

The actual pinned loader is
https://cdn.jsdelivr.net/gh/kitao/pyxel@v2.9.8/wasm/pyxel.js
It loads Pyodide v314.0.2 and
`pyxel-2.9.8-cp311-abi3-emscripten_5_0_3_wasm32.whl`.
The wheel was fetched and inspected in memory, without installing it. Its
`pyxel_binding.abi3.so` embeds SDL2 code that:

1. Constructs `new AudioContext()` (or the prefixed equivalent).
2. Sets the SDL device rate to `SDL2.audioContext.sampleRate`.
3. In the suspended output path calls
   `SDL2.audioContext.createBuffer($0, $1, SDL2.audioContext.sampleRate)`.
   The output arguments are one channel and 1024 frames for this Pyxel build.
4. Uses the silent buffer to keep audio callbacks progressing until resume.

Pyxel synthesizes mono signed 16-bit samples at **22050 Hz**, from an internal
1789773-Hz clock. SDL negotiates float output at the native device rate and
converts the stream. The silence allocation uses the context rate, not the
internal synth rate. No game-owned `createBuffer` existed before this fix.
`pyxel.init` runs before `configure_sounds`; stopping BGM later cannot prevent
an exception in this initialization path.

Primary sources:
- https://github.com/kitao/pyxel/blob/v2.9.8/crates/pyxel-core/src/settings.rs
- https://github.com/kitao/pyxel/blob/v2.9.8/crates/pyxel-core/src/platform/sdl2/platform_sdl2.rs
- https://github.com/libsdl-org/SDL/blob/release-2.32.10/src/audio/emscripten/SDL_emscriptenaudio.c
- https://github.com/WebKit/WebKit/blob/main/Source/WebCore/Modules/webaudio/AudioBuffer.cpp
- https://github.com/WebKit/WebKit/blob/main/Source/WebCore/Modules/webaudio/BaseAudioContext.cpp

Current WebKit main uses this exact exception text when its supported-rate
check fails; its current check is 3000 through 384000 Hz. This is not proof of
the user's installed Safari version's bounds, nor why its context supplied a
rejected rate. The SDL allocation path is reproducible; the device-specific
trigger remains to be confirmed with the diagnostic page or console.

All 28 repository WAVs are uncompressed PCM, 22050 Hz, mono, 16-bit.
The current voice code decodes the 14 cute-v2 files via decodeAudioData and
contains its own unlock failures. BGM/SFX use Pyxel sound definitions, not PCM
file loading. No WAV conversion or melody changes were made.

Official issue searches for `Safari audio`, `sampleRate`, `createBuffer` found
no matching startup-range issue in the searched results. Issue 596 concerns
resume after backgrounding, not this exact startup failure:
https://github.com/kitao/pyxel/issues/596
The checked main settings retain 22050 Hz / 1024 web frames. No dependency
update was made; being on 2.9.8 does not establish compatibility by itself.

## Minimal containment

`assets/audio-boot.js` probes the exact native silence-buffer allocation before
the Python call to pyxel.init. A successful native context is reused by SDL,
with the validated buffer handed to SDL once. Other allocations use the native
method. No UA test, global prototype patch, arbitrary rate clamp, relabelling
of PCM, or replacement AudioBuffer is used. User gestures can resume a valid
suspended context.

On failure, close the rejected context and set `SDL_AUDIODRIVER=dummy` BEFORE
pyxel.init. With the actual pinned WASM, this produced SDL device-open failure
and Pyxel's nonfatal `Failed to initialize audio device` diagnostic, followed
by a working game loop. Do NOT describe this build as having a functioning
dummy output device: the verified path is SDL returning device ID 0 and
Pyxel's existing `start_audio` handling that return without throwing into WASM.
There is no re-init of partially initialized Pyxel state and no runtime fork.
No-audio mode keeps BGM/SFX off and disabled, suppresses new chain-voice unlocks,
and preserves saved sound preferences even when other settings/scores are saved.
Reloading retries capability detection. It does not retry a failed device live
inside an already initialized SDL session.

The guard is shipped inside the already copied assets directory. Existing
Pages workflow and all layout CSS/keyboard handlers remain unchanged.
The guard is scoped to startup: unrelated future device-loss or arbitrary
WebAudio errors are not claimed to be universally recovered.

## Reproduction and regression

Serve the repository and open `/tests/audio-startup.html`.
Cases A/B/C/D are init only, init+stop, init+SFX, init+BGM. Select the case,
click Start, then the Pyxel startup image. The report includes the observed
rate, context state, guard result and advancing frame count.

`?fault=reject` is TEST-ONLY injection: force SDL's suspended branch and reject
createBuffer with the reported exception. It does not emulate all of Safari.

| Case | Native capability + guard | Injected reject without guard | Injected reject + guard |
|---|---|---|---|
| A init | running | fatal before game loop | running, silent |
| B stop | running | fatal before game loop | running, silent |
| C SFX | running | fatal before game loop | running, silent |
| D BGM | running | fatal before game loop | running, silent |

Chromium's measured rate was 48000 Hz. The injection intentionally rejects
that otherwise valid rate; it is NOT the failing iPhone's measured rate.

`/tests/audio-game.html?fault=reject` runs the actual game with the same
injection. Verified game chooser, settings, disabled sound controls, gameplay,
legal number tap, score 0 to 1 and advancing next target.

Automated commands:
```powershell
node --test tests/*.cjs
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p 'test_*.py'
node --check assets/audio-boot.js
node --check tests/audio-fault.js
git diff --check
```

Browser regression: `/tests/browser-layout.html`, Run all sizes / states.
552/552 passed; 48/48 stable boards; squeezed-HUD negative control detected.
This checks DOM fixtures, separately from the actual-WASM tests above.
JavaScript: 195 tests passed. Python: 204 tests passed. Syntax/diff checks passed.
The known unrelated MutationObserver non-Node diagnostic appeared on normal
page load; normal game startup, legal tap and pause still worked. It was not
changed or attributed to the audio fix.

## Device acceptance still needed

Local server: port 8030, LAN IPv4 at verification time 192.168.1.13.
Open `http://192.168.1.13:8030/` on the same LAN, tap startup, start either game
and select a correct panel. Acceptable containment: game works with sound OR
game works silently with sound controls OFF/disabled, no fatal overlay.
Normal native audio quality on iPhone still requires listening on that device.
The numeric failing device rate remains unknown until actual diagnostic capture.
No firewall, Pages configuration, commit, push, PR, merge or public upload.
