/* RIN presentation pilot. Reads engine snapshots; never sends game commands. */
(function () {
  'use strict';
  class RinTimeline {
    constructor() { this.event = null; this.start = 0; this.end = 0; this.started = 0; this.coalesced = 0; }
    observe(event, now, enabled) {
      const fresh = this.event !== null && event > this.event;
      const reset = this.event !== null && event < this.event;
      this.event = event;
      if (!enabled || reset) this.end = 0;
      else if (fresh) {
        if (now < this.end) this.coalesced++;
        else { this.start = now; this.end = now + 600; this.started++; }
      }
      return this.frame(now);
    }
    frame(now) { return now < this.end ? Math.min(5, Math.floor((now - this.start) / 100)) : 0; }
    cancel() { this.end = 0; }
  }
  function restingFrame(pose, reduced) {
    if (pose === 'hurt') return 6;
    if (pose === 'frustrated') return 7;
    if (pose === 'defeat') return 8;
    if (pose === 'victory') return 3;
    if (pose === 'celebrate') return reduced ? 3 : 0;
    return pose === 'idle' ? 0 : null;
  }
  if (typeof module !== 'undefined') module.exports = {RinTimeline, restingFrame};
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  const app = document.getElementById('modern-app');
  if (!app) return;
  const source = new URL('rin-expression-sheet.png', document.currentScript.src).href;
  const media = window.matchMedia('(prefers-reduced-motion: reduce)');
  const timeline = new RinTimeline();
  let ready = false, failed = false, current = null, raf = 0, key = '', frame = 0, restFrame = 0;
  const overlays = new Map();
  function reduced() { return media.matches || app.dataset.reduced === 'true'; }
  function paint(index) {
    frame = index;
    if (current) {
      current.style.backgroundPosition = `${index * 12.5}% 0%`;
      current.dataset.frame = String(index);
    }
  }
  function tick(now) {
    raf = 0;
    if (!current || document.hidden || reduced()) { timeline.cancel(); paint(restFrame); return; }
    paint(now < timeline.end ? timeline.frame(now) : restFrame);
    if (now < timeline.end) raf = requestAnimationFrame(tick);
  }
  function clear() {
    if (raf) cancelAnimationFrame(raf);
    raf = 0; timeline.cancel(); current = null;
    for (const [parent, overlay] of overlays) { parent.removeAttribute('data-rin-pilot'); overlay.hidden = true; }
  }
  function update() {
    let s;
    try { s = JSON.parse(root.getAttribute('data-modern-state')); } catch (_) { clear(); return; }
    const picture = s?.screen === 'shiritori';
    const state = picture ? s.shiritori : s;
    const live = picture ? state?.phase === 'playing' : s?.screen === 'playing';
    const nextKey = picture ? 'shiritori' : 'numbers';
    if (key !== nextKey) { timeline.event = null; key = nextKey; }
    const parents = [...app.querySelectorAll('.nr-rin .nr-character-art')]
      .filter(e => e.getClientRects().length && !e.closest('[hidden]'));
    const parent = parents.find(e => e.closest('[data-arena]')) || parents[0];
    const still = parent ? restingFrame(parent.dataset.pose || 'idle', reduced()) : null;
    const allowed = still !== null;
    const active = ready && allowed && !document.hidden;
    const now = performance.now();
    const positive = ['idle','celebrate','victory'].includes(parent?.dataset.pose || 'idle');
    timeline.observe(Number(state?.chain?.you?.event) || 0, now, active && live && positive && !reduced());
    if (!active) { clear(); return; }
    restFrame = still;
    for (const [other, overlay] of overlays) if (!parents.includes(other)) { other.removeAttribute('data-rin-pilot'); overlay.hidden = true; }
    for (const p of parents) {
      if (!overlays.has(p)) {
        const overlay = document.createElement('span');
        overlay.className = 'pilot-rin-art'; overlay.setAttribute('aria-hidden', 'true');
        overlay.style.backgroundImage = `url("${source}")`;
        p.append(overlay); overlays.set(p, overlay);
      }
      const overlay = overlays.get(p), index = restingFrame(p.dataset.pose || 'idle', reduced());
      if (index === null) { p.removeAttribute('data-rin-pilot'); overlay.hidden = true; continue; }
      overlay.hidden = false; p.dataset.rinPilot = 'ready';
      overlay.style.backgroundPosition = `${index * 12.5}% 0%`; overlay.dataset.frame = String(index);
    }
    current = overlays.get(parent); current.hidden = false; parent.dataset.rinPilot = 'ready';
    paint(now < timeline.end ? timeline.frame(now) : restFrame);
    if (!raf && now < timeline.end) raf = requestAnimationFrame(tick);
  }
  const image = new Image();
  image.onload = async () => {
    try {
      if (image.naturalWidth !== 2304 || image.naturalHeight !== 256) throw new Error('Unexpected strip dimensions');
      if (image.decode) await image.decode();
      ready = true; root.dataset.rinPilotAsset = 'ready'; update();
    } catch (_) { image.onerror(); }
  };
  image.onerror = () => { ready = false; failed = true; root.dataset.rinPilotAsset = 'fallback'; clear(); };
  image.src = source;
  new MutationObserver(update).observe(root, {attributes: true, attributeFilter: ['data-modern-state']});
  document.addEventListener('visibilitychange', update);
  media.addEventListener('change', update);
  Object.defineProperty(window, 'rinPilotDiagnostics', {get: () => ({ready, failed, frame,
    started: timeline.started, coalesced: timeline.coalesced, running: !!raf, overlays: overlays.size})});
  update();
})();
