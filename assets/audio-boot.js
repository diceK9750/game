/* Pyxel 2.9.8 / SDL2 WebAudio startup guard. No UA or sample-rate override. */
(function () {
  let context;
  const diagnostic = {mode: 'pending', requestedRate: null, error: null};
  function resume() {
    if (!context || context.state !== 'suspended') return;
    try { Promise.resolve(context.resume()).catch(error => console.warn('[audio] resume deferred', error)); }
    catch (error) { console.warn('[audio] resume deferred', error); }
  }
  window.numberRushAudio = {
    diagnostic,
    prepare(module) {
      if (diagnostic.mode !== 'pending') return diagnostic.mode === 'native';
      try {
        const Context = window.AudioContext || window.webkitAudioContext;
        if (!Context || !module) throw new Error('WebAudio runtime unavailable');
        context = module.SDL2?.audioContext || new Context();
        const rate = context.sampleRate;
        diagnostic.requestedRate = rate;
        // SDL2's suspended-output path uses one channel, 1024 frames and the
        // native context rate (NOT Pyxel's internal 22050-Hz synthesis rate).
        const create = context.createBuffer.bind(context);
        let silence = create(1, 1024, rate);
        // Hand the validated buffer to SDL once. No global prototype changes,
        // PCM relabelling, resampling or fabricated AudioBuffer objects.
        context.createBuffer = function (channels, length, sampleRate) {
          if (silence && channels === 1 && length === 1024 && sampleRate === rate) {
            const buffer = silence; silence = null; return buffer;
          }
          return create(channels, length, sampleRate);
        };
        module.SDL2 ||= {};
        module.SDL2.audioContext = context;
        diagnostic.mode = 'native';
        resume();
        console.info('[audio] native startup', {...diagnostic});
        return true;
      } catch (error) {
        diagnostic.mode = 'silent';
        diagnostic.error = `${error.name}: ${error.message}`;
        try { Promise.resolve(context?.close()).catch(() => {}); } catch (_) {}
        context = null;
        console.warn('[audio] requesting silent SDL startup; reload to retry', {...diagnostic});
        return false;
      }
    }
  };
  document.addEventListener('pointerdown', resume, {passive: true});
  document.addEventListener('keydown', resume);
})();
