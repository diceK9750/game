/* Local, original synthesized callouts. One source at a time; never queue old chains. */
(function () {
  let context, source, gainNode, enabled = false, buffers = new Map();
  const FADE_IN = 0.04;
  const FADE_OUT = 0.1;
  const LEVEL = 0.75;
  const flourishNodes = new Set();
  const voicePending = new Set(), voiceRetryAt = new Map();
  const VOICE_RETRY_DELAY = 15000;

  function stop(immediate) {
    if (!source) return;
    const playing = source;
    const g = gainNode;
    source = null;
    gainNode = null;
    try {
      if (immediate || !context || !g) {
        playing.stop();
      } else {
        const now = context.currentTime;
        g.gain.cancelScheduledValues(now);
        g.gain.setValueAtTime(Math.max(0, g.gain.value), now);
        g.gain.linearRampToValueAtTime(0, now + FADE_OUT);
        playing.stop(now + FADE_OUT);
      }
    } catch (_) { /* already stopped */ }
  }

  function loadVoices(isRetry) {
    if (document.hidden || (isRetry && !enabled)) return;
    const now = Date.now();
    for (const owner of ['you', 'cpu']) for (let level = 1; level <= 7; level++) {
      const key = `${owner}-${level}`;
      if (buffers.has(key) || voicePending.has(key) || now < (voiceRetryAt.get(key) || 0)) continue;
      voicePending.add(key);
      // Starting in a promise also catches a synchronous fetch exception and
      // still lets the other independently loadable voices proceed.
      Promise.resolve().then(() => fetch(`assets/voices/cute-v2/${key}.wav`)).then(r => {
        if (!r.ok) throw Error('voice unavailable');
        return r.arrayBuffer();
      }).then(b => context.decodeAudioData(b)).then(b => {
        buffers.set(key, b);
        voiceRetryAt.delete(key);
      }).catch(() => { voiceRetryAt.set(key, Date.now() + VOICE_RETRY_DELAY); })
        .finally(() => { voicePending.delete(key); });
    }
  }

  async function unlock() {
    if (window.numberRushAudio?.diagnostic.mode === 'silent') return;
    try {
      const Context = window.AudioContext || window.webkitAudioContext;
      if (!Context) return;
      const firstUnlock = !context;
      if (firstUnlock) context = new Context();
      loadVoices(!firstUnlock);
      await context.resume();
    } catch (_) { /* Sound restrictions must never prevent a panel selection. */ }
  }

  document.addEventListener('pointerdown', unlock, { passive: true });
  // The modern game UI stops bubbling keys to protect the Pyxel engine.
  // Capture without cancelling so keyboard-only play can also retry voices.
  document.addEventListener('keydown', unlock, { capture: true });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) { stop(true); stopFlourishes(); }
  });

  function finishFlourish(node) {
    if (!flourishNodes.delete(node)) return;
    try { node.oscillator.disconnect(); } catch (_) {}
    try { node.envelope.disconnect(); } catch (_) {}
  }

  function stopFlourishes() {
    for (const node of flourishNodes) {
      try { node.oscillator.stop(); } catch (_) { /* already stopped */ }
      finishFlourish(node);
    }
  }

  function flourish(notes, level = 0.085) {
    if (!enabled || document.hidden || !context || context.state !== 'running') return;
    let now;
    try { now = context.currentTime; } catch (_) { return; }
    notes.forEach(([offset, frequency, duration], index) => {
      let node;
      try {
        const oscillator = context.createOscillator(), envelope = context.createGain();
        node = {oscillator, envelope};
        flourishNodes.add(node);
        oscillator.onended = () => finishFlourish(node);
        oscillator.type = index % 2 ? 'sine' : 'triangle';
        oscillator.frequency.setValueAtTime(frequency, now + offset);
        envelope.gain.setValueAtTime(0, now + offset);
        envelope.gain.linearRampToValueAtTime(level, now + offset + .014);
        envelope.gain.exponentialRampToValueAtTime(.001, now + offset + duration);
        oscillator.connect(envelope); envelope.connect(context.destination);
        oscillator.start(now + offset); oscillator.stop(now + offset + duration + .01);
      } catch (_) {
        // A partial audio graph must not leak or block subsequent interaction.
        if (node) {
          try { node.oscillator.stop(); } catch (_) {}
          finishFlourish(node);
        }
      }
    });
  }

  window.chainVoice = {
    setEnabled(value) {
      enabled = !!value;
      if (!enabled) { stop(true); stopFlourishes(); }
    },
    stinger() { flourish([[0, 392, .12], [.07, 523.25, .15], [.15, 659.25, .22], [.23, 783.99, .31]]); },
    counterCue() { flourish([[0, 466.16, .10], [.09, 622.25, .16]], .045); },
    fanfare(winner = 'you') {
      if (winner === 'you') flourish([[0, 523.25, .18], [.14, 659.25, .18], [.28, 783.99, .2], [.42, 1046.5, .55]], .11);
      else flourish([[0, 392, .18], [.16, winner === 'cpu' ? 349.23 : 440, .22], [.32, 523.25, .38]], .07);
    },
    play(owner, count) {
      if (!enabled || document.hidden || !context || context.state !== 'running' || count < 1) return;
      const buffer = buffers.get(`${owner}-${Math.min(7, count)}`);
      if (!buffer) return;
      stop(false);
      let playingSource, playingGain;
      try {
        const now = context.currentTime;
        playingSource = context.createBufferSource();
        playingSource.buffer = buffer;
        playingGain = context.createGain();
        playingGain.gain.setValueAtTime(0, now);
        playingGain.gain.linearRampToValueAtTime(LEVEL, now + FADE_IN);
        source = playingSource;
        gainNode = playingGain;
        playingSource.onended = () => {
          try { playingSource.disconnect(); } catch (_) {}
          try { playingGain.disconnect(); } catch (_) {}
          if (source === playingSource) {
            source = null;
            gainNode = null;
          }
        };
        playingSource.connect(playingGain);
        playingGain.connect(context.destination);
        playingSource.start();
      } catch (_) {
        // Audio failure must never disable the game UI. Release any partially
        // constructed graph so the next call can try again normally.
        if (source === playingSource) { source = null; gainNode = null; }
        try { playingSource?.stop(); } catch (_) {}
        try { playingSource?.disconnect(); } catch (_) {}
        try { playingGain?.disconnect(); } catch (_) {}
      }
    }
  };
})();
