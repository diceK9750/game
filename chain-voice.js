/* Local, original synthesized callouts. One source at a time; never queue old chains. */
(function () {
  let context, source, enabled=false, buffers=new Map();
  function stop() { if (source) { try { source.stop(); } catch (_) {} source=null; } }
  async function unlock() {
    try {
      const Context=window.AudioContext || window.webkitAudioContext;
      if (!Context) return;
      if (!context) {
        context=new Context();
        for (const owner of ['you','cpu']) for (let level=1; level<=7; level++) {
          const key=`${owner}-${level}`;
          fetch(`assets/voices/cute-v2/${key}.wav`).then(r=>{if(!r.ok) throw Error('voice unavailable'); return r.arrayBuffer();})
            .then(b=>context.decodeAudioData(b)).then(b=>buffers.set(key,b)).catch(()=>{});
        }
      }
      await context.resume();
    } catch (_) { /* Sound restrictions must never prevent a panel selection. */ }
  }
  document.addEventListener('pointerdown', unlock, {passive:true});
  document.addEventListener('keydown', unlock);
  document.addEventListener('visibilitychange',()=>{if(document.hidden) stop();});
  window.chainVoice={
    setEnabled(value) { enabled=!!value; if(!enabled) stop(); },
    play(owner,count) {
      if(!enabled || document.hidden || !context || context.state!=='running' || count<1) return;
      const buffer=buffers.get(`${owner}-${Math.min(7,count)}`);
      if(!buffer) return;
      stop();
      source=context.createBufferSource(); source.buffer=buffer;
      const gain=context.createGain(); gain.gain.value=.75;
      const playingSource=source;
      source.onended=()=>{playingSource.disconnect(); gain.disconnect(); if(source===playingSource) source=null;};
      source.connect(gain); gain.connect(context.destination); source.start();
    }
  };
})();
