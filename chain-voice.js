/* Local, original synthesized callouts. One source at a time; never queue old chains. */
(function () {
  let context, source, gainNode, enabled = false, buffers = new Map();
  const FADE_IN = 0.04;
  const FADE_OUT = 0.1;
  const LEVEL = 0.75;

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

  async function unlock() {
    try {
      const Context = window.AudioContext || window.webkitAudioContext;
      if (!Context) return;
      if (!context) {
        context = new Context();
        for (const owner of ['you', 'cpu']) for (let level = 1; level <= 7; level++) {
          const key = `${owner}-${level}`;
          fetch(`assets/voices/cute-v2/${key}.wav`).then(r => {
            if (!r.ok) throw Error('voice unavailable');
            return r.arrayBuffer();
          }).then(b => context.decodeAudioData(b)).then(b => buffers.set(key, b)).catch(() => {});
        }
      }
      await context.resume();
    } catch (_) { /* Sound restrictions must never prevent a panel selection. */ }
  }

  document.addEventListener('pointerdown', unlock, { passive: true });
  document.addEventListener('keydown', unlock);
  document.addEventListener('visibilitychange', () => { if (document.hidden) stop(true); });

  window.chainVoice = {
    setEnabled(value) {
      enabled = !!value;
      if (!enabled) stop(true);
    },
    play(owner, count) {
      if (!enabled || document.hidden || !context || context.state !== 'running' || count < 1) return;
      const buffer = buffers.get(`${owner}-${Math.min(7, count)}`);
      if (!buffer) return;
      stop(false);
      const now = context.currentTime;
      source = context.createBufferSource();
      source.buffer = buffer;
      gainNode = context.createGain();
      gainNode.gain.setValueAtTime(0, now);
      gainNode.gain.linearRampToValueAtTime(LEVEL, now + FADE_IN);
      const playingSource = source;
      const playingGain = gainNode;
      source.onended = () => {
        try { playingSource.disconnect(); playingGain.disconnect(); } catch (_) {}
        if (source === playingSource) {
          source = null;
          gainNode = null;
        }
      };
      source.connect(gainNode);
      gainNode.connect(context.destination);
      source.start();
    }
  };
})();
