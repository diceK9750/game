/* Full-colour character portraits. Presentation only; no game input handlers. */
const CHARACTER_POSES = Object.freeze({idle: 0, celebrate: 1, victory: 2,
  hurt: 3, frustrated: 4, defeat: 5});
const CHARACTER_SCREENS = new Set(['ready', 'countdown', 'playing', 'finished']);
const CHARACTER_RECTS = Object.freeze([[18, 246, 92, 108], [530, 246, 92, 108]]);
// Only scenery: keep the complete board/effects and the lower central UI clear.
const SCENERY_HOLES = Object.freeze({
  ready: [[112, 244, 420, 36], [222, 282, 200, 34]],
  playing: [[158, 250, 328, 98]],
  practice: [[170, 250, 304, 98]],
  countdown: [[190, 244, 260, 28]],
  finished: [[112, 244, 420, 72]],
});
function sceneryClip(screen, kind = 'battle') {
  const holes = SCENERY_HOLES[screen === 'playing' && kind === 'practice' ? 'practice' : screen];
  if (!holes) return 'inset(100%)';
  const rect = ([x,y,w,h]) => `M${x} ${y}H${x+w}V${y+h}H${x}Z`;
  return `path(evenodd, '${rect([0,244,640,116])} ${holes.map(rect).join(' ')}')`;
}

function portraitPosition(action) {
  const pose = CHARACTER_POSES[action] ?? 0;
  return `${(pose % 3) * 50}% ${Math.floor(pose / 3) * 100}%`;
}

function parseCharacterState(raw) {
  try {
    const data = JSON.parse(raw);
    if (!data || typeof data !== 'object') return null;
    return {screen: data.screen, kind: data.kind, visible: CHARACTER_SCREENS.has(data.screen),
      left: Object.hasOwn(CHARACTER_POSES, data.left) ? data.left : 'idle',
      right: Object.hasOwn(CHARACTER_POSES, data.right) ? data.right : 'idle',
      reduced: data.reduced === true, perfect: data.perfect === true};
  } catch { return null; }
}

if (typeof module !== 'undefined') {
  module.exports = {portraitPosition, parseCharacterState, CHARACTER_RECTS, SCENERY_HOLES, sceneryClip};
}

if (typeof document !== 'undefined') {
  const root = document.documentElement;
  const layer = document.getElementById('character-layer');
  const scenery = document.getElementById('forest-stage');
  const portraits = [document.getElementById('rin-portrait'), document.getElementById('koh-portrait')];
  let loaded = false;
  // Independent loading: a missing background must never disable the portraits.
  const environment = new Image();
  environment.onload = () => { scenery.hidden = false; layer.dataset.scenery = 'true'; };
  environment.src = 'assets/backgrounds/lantern-forest.png';
  const media = window.matchMedia('(prefers-reduced-motion: reduce)');
  function update() {
    const state = parseCharacterState(root.getAttribute('data-character-state'));
    layer.hidden = !loaded || !state?.visible || document.hidden;
    if (!state) return;
    scenery.style.clipPath = sceneryClip(state.screen, state.kind);
    layer.dataset.reduced = String(state.reduced || media.matches);
    layer.dataset.perfect = String(state.perfect);
    for (const [i, action] of [state.left, state.right].entries()) {
      portraits[i].style.backgroundPosition = portraitPosition(action);
      portraits[i].dataset.pose = action;
    }
  }
  const images = ['assets/characters/rin-atlas.png', 'assets/characters/koh-dark-cutout-atlas.png'];
  Promise.all(images.map(src => new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => image.naturalWidth === 1536 && image.naturalHeight === 1024
      ? resolve() : reject(new Error('Invalid character atlas dimensions'));
    image.onerror = reject;
    image.src = src;
  }))).then(() => {
    loaded = true;
    root.setAttribute('data-character-ready', 'true');
    update();
  }).catch(() => { root.removeAttribute('data-character-ready'); update(); });
  new MutationObserver(update).observe(root, {attributes: true, attributeFilter: ['data-character-state']});
  document.addEventListener('visibilitychange', update);
  media.addEventListener('change', update);
}
