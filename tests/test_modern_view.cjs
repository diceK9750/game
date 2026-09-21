const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {parseState, formatTime, posePosition, remainingCommands, nextCell, nextPlayable, shouldLockPlayScroll, isPlayScrollAllowed, markHostInsets} = require('../modern-ui.js');
const state = () => ({v: 1, screen: 'playing', cells: Array.from({length: 40}, (_, i) => ({n: i + 1, owner: null}))});

test('modern bridge activates only for a valid complete 5 by 8 board', () => {
  assert.equal(parseState('broken'), null);
  assert.equal(parseState('null'), null);
  assert.equal(parseState(JSON.stringify({...state(), v: 2})), null);
  assert.equal(parseState(JSON.stringify({...state(), screen: 'unknown'})), null);
  assert.equal(parseState(JSON.stringify({...state(), cells: []})), null);
  for (const value of [0, 41, '1', undefined]) {
    const s = state(); s.cells[0] = {n: value}; assert.equal(parseState(JSON.stringify(s)), null);
  }
  const s = state(); s.cells[0].n = null;
  assert.equal(parseState(JSON.stringify(s)).cells.length, 40);
  for (const screen of ['ready', 'countdown', 'resuming', 'confirm', 'help']) {
    assert.equal(parseState(JSON.stringify({...state(), screen, cells: []})).cells.length, 0);
    assert.equal(parseState(JSON.stringify({...state(), screen, cells: null})).cells.length, 0);
    assert.equal(parseState(JSON.stringify({...state(), screen})), null);
  }
});

test('timer is stable and readable across minute boundaries', () => {
  assert.equal(formatTime(9.25), '9.25 秒'); assert.equal(formatTime(62.5), '1:02.50');
  assert.equal(formatTime(-1), '0.00 秒'); assert.equal(formatTime(NaN), '0.00 秒');
});

test('six original character poses and unknown states map safely', () => {
  assert.deepEqual(['idle', 'celebrate', 'victory', 'hurt', 'frustrated', 'defeat'].map(posePosition), ['0% 0%', '50% 0%', '100% 0%', '0% 100%', '50% 100%', '100% 100%']);
  assert.equal(posePosition('__proto__'), '0% 0%');
});

test('input queue retains unacknowledged taps in order without replaying acknowledged input', () => {
  const commands = [{id: 4, action: 'cell', index: 0}, {id: 5, action: 'cell', index: 1}];
  assert.deepEqual(remainingCommands(JSON.stringify(commands), 4), [commands[1]]);
  assert.deepEqual(remainingCommands('bad', 0), []);
  assert.deepEqual(remainingCommands('{}', 0), []);
  assert.equal(remainingCommands(JSON.stringify(Array.from({length: 200}, (_, i) => ({id: i + 1}))), 0).length, 128);
});

test('keyboard navigation wraps within the fixed 5 by 8 grid', () => {
  assert.equal(nextCell(7, 'ArrowRight'), 0); assert.equal(nextCell(8, 'ArrowLeft'), 15);
  assert.equal(nextCell(39, 'ArrowDown'), 7); assert.equal(nextCell(3, 'ArrowUp'), 35);
  assert.equal(nextCell(10, 'Enter'), 10);
});

test('keyboard focus skips claimed or empty cells and survives a fully cleared row', () => {
  const available = Array(40).fill(false); available[12] = true; available[16] = true;
  assert.equal(nextPlayable(available, 11, 'ArrowRight'), 12);
  assert.equal(nextPlayable(available, 0, 'ArrowRight'), 12);
  assert.equal(nextPlayable(available, 8, 'ArrowDown'), 16);
  assert.equal(nextPlayable(Array(40).fill(false), 39, 'ArrowRight'), -1);
});

test('view preserves no-cooldown input, local assets, safe text and reduced motion', () => {
  const js = fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8');
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  assert.match(js, /event\.detail === 0/); assert.match(js, /addEventListener\('pointerdown'/);
  assert.match(js, /disabled = !playing \|\| empty \|\| claimed/);
  assert.doesNotMatch(js, /innerHTML|setTimeout|fetch\(/);
  assert.match(css, /repeat\(8, minmax\(0, 1fr\)\)/);
  assert.match(css, /repeat\(5, minmax\(24px, 1fr\)\)/);
  assert.match(css, /prefers-reduced-motion/); assert.match(css, /safe-area-inset-top/);
  assert.match(css, /data-host-insets/); assert.match(css, /padding: 0 12px/);
  assert.match(css, /\.nr-cell-effect[^}]*pointer-events: none/);
  assert.match(css, /assets\/backgrounds\/lantern-forest-v2\.png/);
  assert.match(css, /data-feedback='cpu'/);
  assert.match(css, /\.nr-cpu-claim/);
  assert.match(js, /data\.effect === 'cpu'/);
  assert.match(js, /markHostInsets/);
});

test('prefers-reduced-motion keeps static cpu-claim and award without waiting for data-reduced', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  // OS preference alone (before JS data-reduced) must freeze animated feedback into readable static states.
  assert.match(css, /#modern-app \.nr-cpu-claim,\s*#modern-app \.nr-award \{ opacity: 1; animation: none !important; \}/);
  assert.match(css, /#modern-app\[data-reduced='true'\] \.nr-cpu-claim,\s*#modern-app\[data-reduced='true'\] \.nr-award \{ opacity: 1; animation: none !important; \}/);
  // Final media block (not earlier fairy/character rules) carries cell outline + fx parity.
  const idx = css.lastIndexOf('@media (prefers-reduced-motion: reduce)');
  assert.ok(idx > 0, 'feedback reduced-motion media query present');
  const media = css.slice(idx);
  assert.match(media, /data-feedback='wrong'/);
  assert.match(media, /data-feedback='cpu'/);
  assert.match(media, /\.nr-cpu-claim/);
  assert.match(media, /\.nr-award/);
  // Static ring/spark/miss-badge stand-ins (not blank .nr-fx); miss bomb/burst stay hidden.
  assert.match(media, /\.nr-fx \{ opacity: 1; animation: none !important; \}/);
  assert.match(media, /\.nr-bomb,[\s\S]*?\.nr-burst \{ opacity: 0; \}/);
  assert.match(media, /\.nr-ring,[\s\S]*?\.nr-spark,[\s\S]*?\.nr-miss-badge \{[\s\S]*?opacity: 1; transform: none/);
});

test('data-reduced keeps static ring/spark/CPU/miss badge stand-ins instead of blanking .nr-fx', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  // Parent opacity:0 would hide nested .nr-cpu-claim despite its own opacity:1.
  assert.doesNotMatch(css, /#modern-app\[data-reduced='true'\] \.nr-fx \{ opacity: 0/);
  assert.match(css, /#modern-app\[data-reduced='true'\] \.nr-fx \{ opacity: 1; animation: none !important; \}/);
  assert.match(css, /#modern-app\[data-reduced='true'\] \.nr-bomb,[\s\S]*?\.nr-burst \{ opacity: 0; \}/);
  assert.match(css, /#modern-app\[data-reduced='true'\] \.nr-ring,[\s\S]*?\.nr-spark,[\s\S]*?\.nr-miss-badge \{[\s\S]*?opacity: 1; transform: none/);
  // Outlines (#28/#29) remain; FX layer never intercepts taps.
  assert.match(css, /#modern-app\[data-reduced='true'\] \.nr-cell\[data-feedback='correct'\]/);
  assert.match(css, /#modern-app\[data-reduced='true'\] \.nr-cell\[data-feedback='wrong'\]/);
  assert.match(css, /\.nr-fx \{[^}]*pointer-events: none/);
  assert.match(css, /\.nr-cell-effect \{[^}]*pointer-events: none/);
  assert.match(css, /\.nr-miss-badge \{[^}]*pointer-events: none/);
});

test('wrong FX mounts miss badge; reduced CSS shows it while bomb/burst stay hidden', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const js = fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8');
  // Always mounted with bomb/burst for parity with CPU badge mount pattern.
  assert.match(js, /nr-bomb.*nr-burst.*nr-miss-badge/);
  assert.match(js, /'nr-miss-badge', 'ミス'/);
  // Full motion: badge stays opacity 0 (bomb/burst are the cue).
  assert.match(css, /\.nr-miss-badge \{[^}]*opacity: 0/);
  // Reduced / data-reduced: static visible badge; bomb/burst remain hidden.
  assert.match(css, /#modern-app\[data-reduced='true'\] \.nr-miss-badge/);
  const idx = css.lastIndexOf('@media (prefers-reduced-motion: reduce)');
  assert.ok(idx > 0);
  assert.match(css.slice(idx), /\.nr-miss-badge/);
  assert.match(css.slice(idx), /\.nr-bomb,[\s\S]*?\.nr-burst \{ opacity: 0; \}/);
  // Runtime mount under a wrong effect.
  const browser = browserHarness();
  const round = browser.render('playing');
  const cells = browser.cells();
  round.cells[1].effect = 'wrong';
  round.cells[1].effect_id = 'wrong:7';
  browser.render('playing', round);
  const fx = walk(cells[1]).find(n => String(n.className || '').includes('nr-fx-wrong'));
  assert.ok(fx);
  const badge = walk(fx).find(n => n.className === 'nr-miss-badge');
  assert.equal(badge && badge.textContent, 'ミス');
  assert.ok(walk(fx).some(n => n.className === 'nr-bomb'));
  assert.ok(walk(fx).some(n => n.className === 'nr-burst'));
});

test('prefers-reduced-motion kills pose joy/shake; sprite data-pose is the static fallback', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  // Animated bounce/wobble for celebrate/victory/hurt.
  assert.match(css, /\.nr-character-art\[data-pose='celebrate'\], \.nr-character-art\[data-pose='victory'\] \{ animation: nr-joy/);
  assert.match(css, /\.nr-character-art\[data-pose='hurt'\] \{ animation: nr-shake/);
  // Explicit OS + data-reduced kills (local to pose rules; blanket * also covers #modern-app).
  assert.match(css, /@media \(prefers-reduced-motion: reduce\) \{[\s\S]*?data-pose='celebrate'[\s\S]*?data-pose='victory'[\s\S]*?data-pose='hurt'[\s\S]*?animation: none !important/);
  assert.match(css, /#modern-app\[data-reduced='true'\] \.nr-character-art\[data-pose='celebrate'\],[\s\S]*?data-pose='victory'[\s\S]*?data-pose='hurt'[\s\S]*?animation: none !important/);
  // Why no held transform: posePosition/background-position already swaps the portrait
  // frame for celebrate/victory/hurt — that sprite is the durable non-motion cue.
  assert.match(css, /Static fallback is the\s*data-pose sprite frame/);
});

test('forced-colors and prefers-contrast keep miss/CPU/correct/hint/cpu-selecting durable outlines readable', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const contrastIdx = css.indexOf('@media (prefers-contrast: more)');
  assert.ok(contrastIdx > 0, 'prefers-contrast media query present');
  // Higher-contrast pastels: thicker outlines, no soft glow reliance.
  assert.match(css.slice(contrastIdx), /prefers-contrast: more[\s\S]*?data-feedback='wrong'[\s\S]*?outline: 4px solid #d0181c/);
  assert.match(css.slice(contrastIdx), /prefers-contrast: more[\s\S]*?data-feedback='correct'[\s\S]*?outline: 4px solid #0a8f55/);
  assert.match(css.slice(contrastIdx), /prefers-contrast: more[\s\S]*?data-feedback='cpu'[\s\S]*?outline: 4px solid #b01878/);
  assert.match(css.slice(contrastIdx), /prefers-contrast: more[\s\S]*?\.nr-cell\[data-hint='true'\][\s\S]*?outline: 4px solid #0a8f55/);
  assert.match(css.slice(contrastIdx), /prefers-contrast: more[\s\S]*?\.sh-card\[data-hint='true'\][\s\S]*?outline: 4px solid #a07000/);
  assert.match(css.slice(contrastIdx), /prefers-contrast: more[\s\S]*?data-cpu-selecting='true'[\s\S]*?outline: 4px solid #b01878/);
  const forcedIdx = css.indexOf('@media (forced-colors: active)');
  assert.ok(forcedIdx > 0, 'forced-colors media query present');
  // forced-colors is LAST so it wins over reduced-motion pastels (#39).
  assert.ok(forcedIdx > css.indexOf('/* Effects remain understandable'), 'forced-colors after reduced-motion section');
  const forced = css.slice(forcedIdx);
  // System colors so Windows HC / forced-colors themes keep semantic outlines.
  assert.match(forced, /data-feedback='wrong'[^{]*\{[^}]*outline: 4px solid LinkText/);
  assert.match(forced, /data-feedback='correct'[^{]*\{[^}]*outline: 4px solid Highlight/);
  assert.match(forced, /data-feedback='cpu'[^{]*\{[^}]*outline: 4px solid ButtonText/);
  assert.match(forced, /\.nr-cell\[data-hint='true'\][^{]*\{[^}]*outline: 4px solid Highlight/);
  assert.match(forced, /\.sh-card\[data-hint='true'\][^{]*\{[^}]*outline: 4px solid Highlight/);
  assert.match(forced, /data-cpu-selecting='true'[\s\S]*?outline: 4px solid ButtonText/);
  assert.match(forced, /data-feedback='wrong'[^{]*\{[^}]*box-shadow: none/);
  assert.match(forced, /data-feedback='cpu'[^{]*\{[^}]*box-shadow: none/);
  assert.match(forced, /\.nr-cell\[data-hint='true'\][^{]*\{[^}]*box-shadow: none/);
  assert.match(forced, /\.sh-card\[data-hint='true'\][^{]*\{[^}]*box-shadow: none/);
  assert.match(forced, /data-cpu-selecting='true'[\s\S]*?box-shadow: none/);
});

test('forced-colors and prefers-contrast keep static ring/spark/CPU/miss FX cues readable', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  // Base FX stay pointer-events none so contrast overrides cannot revive hit targets.
  assert.match(css, /\.nr-fx \{[^}]*pointer-events: none/);
  assert.match(css, /\.nr-miss-badge \{[^}]*pointer-events: none/);
  const contrastIdx = css.indexOf('@media (prefers-contrast: more)');
  assert.ok(contrastIdx > 0, 'prefers-contrast media query present');
  const contrastEnd = css.indexOf('@media (forced-colors: active)', contrastIdx);
  const contrast = css.slice(contrastIdx, contrastEnd);
  // Higher-contrast solids (no soft pastel / glow) for static stand-ins.
  assert.match(contrast, /\.nr-ring \{[\s\S]*?border-color: #0a8f55/);
  assert.match(contrast, /\.nr-ring-cpu \{ border-color: #b01878; \}/);
  assert.match(contrast, /\.nr-spark \{[\s\S]*?color: #0a8f55;[\s\S]*?text-shadow: none/);
  assert.match(contrast, /\.nr-cpu-claim \{[\s\S]*?background: #6a1048;[\s\S]*?box-shadow: none/);
  assert.match(contrast, /\.nr-miss-badge \{[\s\S]*?background: #8a1010;[\s\S]*?box-shadow: none/);
  const forcedIdx = css.indexOf('@media (forced-colors: active)');
  assert.ok(forcedIdx > 0, 'forced-colors media query present');
  assert.ok(forcedIdx > css.indexOf('/* Effects remain understandable'), 'forced-colors after reduced-motion section');
  const forced = css.slice(forcedIdx);
  // System colors parity with #29 cell outlines (Highlight/ButtonText/LinkText).
  assert.match(forced, /\.nr-ring \{[\s\S]*?border-color: Highlight/);
  assert.match(forced, /\.nr-ring-cpu \{ border-color: ButtonText; \}/);
  assert.match(forced, /\.nr-spark \{[\s\S]*?color: Highlight;[\s\S]*?text-shadow: none/);
  assert.match(forced, /\.nr-cpu-claim \{[\s\S]*?background: ButtonText;[\s\S]*?box-shadow: none/);
  assert.match(forced, /\.nr-miss-badge \{[\s\S]*?background: LinkText;[\s\S]*?box-shadow: none/);
  // Reduced-motion static stand-ins remain (normal/reduced looks not blanked by contrast pass).
  assert.match(css, /#modern-app\[data-reduced='true'\] \.nr-ring,[\s\S]*?\.nr-miss-badge \{[\s\S]*?opacity: 1; transform: none/);
});

test('nr-cell keyboard focus uses ::before ring so durable outlines stay visible', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  // Shell buttons keep outline focus; cells/cards/chooser are excluded so state styles are not clobbered.
  assert.match(css, /#modern-app button:not\(\.nr-cell\):not\(\.sh-card\):not\(\.nr-game-card\):focus-visible/);
  assert.match(css, /#modern-app \.nr-cell:focus-visible, #modern-app \.sh-card:focus-visible, #modern-app \.nr-game-card:focus-visible \{ outline: none; \}/);
  assert.match(css, /#modern-app \.nr-cell:focus-visible::before, #modern-app \.sh-card:focus-visible::before,[\s\S]*?#modern-app \.nr-game-card:focus-visible::before \{[^}]*box-shadow: inset 0 0 0 3px #f9d58a/);
  // Feedback selectors carry #modern-app so they beat focus outline:none when both apply.
  assert.match(css, /#modern-app \.nr-cell\[data-feedback='wrong'\]/);
  assert.match(css, /#modern-app \.nr-cell\[data-feedback='correct'\]/);
  assert.match(css, /#modern-app \.nr-cell\[data-feedback='cpu'\]/);
  assert.match(css, /#modern-app \.nr-cell\[data-cpu-selecting='true'\]/);
  assert.match(css, /#modern-app \.sh-card\[data-cpu-selecting='true'\]/);
  assert.match(css, /#modern-app \.nr-cell\[data-hint='true'\]/);
  // Contrast / forced-colors keep a visible focus ring without reclaiming outline.
  const contrastIdx = css.indexOf('@media (prefers-contrast: more)');
  assert.match(css.slice(contrastIdx), /prefers-contrast: more[\s\S]*?\.nr-game-card:focus-visible::before[\s\S]*?box-shadow: inset 0 0 0 4px #c9a227/);
  const forcedIdx = css.indexOf('@media (forced-colors: active)');
  assert.match(css.slice(forcedIdx), /forced-colors: active[\s\S]*?\.nr-game-card:focus-visible::before[\s\S]*?box-shadow: inset 0 0 0 4px Highlight/);
});

test('nr-game-card keyboard focus uses inset ::before ring parity with cells/cards', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  // Chooser cards host absolute rings (position:relative) and share the #30/#31 inset pattern.
  assert.match(css, /\.nr-home \.nr-game-card \{[^}]*position: relative/);
  assert.match(css, /#modern-app button:not\(\.nr-cell\):not\(\.sh-card\):not\(\.nr-game-card\):focus-visible/);
  assert.match(css, /#modern-app \.nr-game-card:focus-visible \{ outline: none; \}/);
  assert.match(css, /#modern-app \.nr-game-card:focus-visible::before \{[^}]*box-shadow: inset 0 0 0 3px #f9d58a/);
  const contrastIdx = css.indexOf('@media (prefers-contrast: more)');
  assert.match(css.slice(contrastIdx), /\.nr-game-card:focus-visible::before[\s\S]*?box-shadow: inset 0 0 0 4px #c9a227/);
  const forcedIdx = css.indexOf('@media (forced-colors: active)');
  assert.match(css.slice(forcedIdx), /\.nr-game-card:focus-visible::before[\s\S]*?box-shadow: inset 0 0 0 4px Highlight/);
});

test('forced-colors wins over reduced-motion pastel outlines; CPU ::after uses system colors', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const effectsIdx = css.indexOf('/* Effects remain understandable');
  const forcedIdx = css.indexOf('@media (forced-colors: active)');
  assert.ok(effectsIdx > 0 && forcedIdx > effectsIdx, 'forced-colors follows reduced-motion section');
  // Only one forced-colors block, and it is the last media query of that kind.
  assert.equal(css.indexOf('@media (forced-colors: active)'), css.lastIndexOf('@media (forced-colors: active)'));
  // Pastel durable outlines are nested so they do not apply under HC / contrast-more.
  assert.match(css, /@media \(forced-colors: none\) \{[\s\S]*?@media not \(prefers-contrast: more\) \{[\s\S]*?data-reduced='true'[\s\S]*?data-feedback='wrong'/);
  const rmIdx = css.lastIndexOf('@media (prefers-reduced-motion: reduce)');
  const contrastIdx = css.indexOf('@media (prefers-contrast: more)');
  assert.ok(rmIdx > 0 && rmIdx < contrastIdx && contrastIdx < forcedIdx,
    'order: RM → prefers-contrast → forced-colors');
  const rm = css.slice(rmIdx, contrastIdx);
  assert.match(rm, /@media \(forced-colors: none\) \{[\s\S]*?@media not \(prefers-contrast: more\) \{[\s\S]*?data-feedback='wrong'[\s\S]*?#f67f81/);
  assert.match(rm, /data-feedback='correct'/);
  assert.match(rm, /data-feedback='cpu'/);
  // Animation / static FX kills stay outside the nest (still in RM block).
  assert.match(rm, /\.nr-fx \{ opacity: 1; animation: none !important; \}/);
  assert.match(rm, /\.nr-miss-badge \{[\s\S]*?opacity: 1; transform: none/);
  const forced = css.slice(forcedIdx);
  // Corner CPU label no longer stuck on #751887 under HC.
  assert.match(forced, /data-cpu-selecting='true'\]::after[\s\S]*?background: ButtonText/);
  assert.match(forced, /data-cpu-selecting='true'\]::after[\s\S]*?color: Canvas/);
  assert.doesNotMatch(forced, /#751887/);
  // Durable outlines + static FX cues still system-colored.
  assert.match(forced, /data-feedback='wrong'[^{]*\{[^}]*outline: 4px solid LinkText/);
  assert.match(forced, /\.nr-ring \{[\s\S]*?border-color: Highlight/);
  assert.match(forced, /\.nr-miss-badge \{[\s\S]*?background: LinkText/);
});

test('prefers-contrast more wins over reduced-motion pastel outlines (parity with #39)', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const effectsIdx = css.indexOf('/* Effects remain understandable');
  const rmIdx = css.lastIndexOf('@media (prefers-reduced-motion: reduce)');
  const contrastIdx = css.indexOf('@media (prefers-contrast: more)');
  const forcedIdx = css.indexOf('@media (forced-colors: active)');
  assert.ok(effectsIdx > 0 && rmIdx > effectsIdx, 'RM section follows effects header');
  assert.ok(contrastIdx > rmIdx && forcedIdx > contrastIdx,
    'prefers-contrast after RM pastels; forced-colors last');
  // Only one prefers-contrast: more block (moved after RM; not duplicated).
  assert.equal(css.indexOf('@media (prefers-contrast: more)'), css.lastIndexOf('@media (prefers-contrast: more)'));
  // data-reduced pastels gated: higher-specificity selector cannot clobber contrast solids.
  assert.match(css, /@media \(forced-colors: none\) \{[\s\S]*?@media not \(prefers-contrast: more\) \{[\s\S]*?data-reduced='true'[\s\S]*?#f67f81/);
  // OS RM pastels similarly gated (same specificity as contrast; nest + order both protect).
  const rm = css.slice(rmIdx, contrastIdx);
  assert.match(rm, /@media not \(prefers-contrast: more\) \{[\s\S]*?#f67f81/);
  assert.doesNotMatch(rm, /#d0181c/);
  const contrast = css.slice(contrastIdx, forcedIdx);
  assert.match(contrast, /data-feedback='wrong'[\s\S]*?outline: 4px solid #d0181c/);
  assert.match(contrast, /data-feedback='correct'[\s\S]*?outline: 4px solid #0a8f55/);
  assert.match(contrast, /data-feedback='cpu'[\s\S]*?outline: 4px solid #b01878/);
  // Static cues remain in contrast block (RM only toggles opacity/transform, not colors).
  assert.match(contrast, /\.nr-ring \{[\s\S]*?border-color: #0a8f55/);
  assert.match(contrast, /\.nr-miss-badge \{[\s\S]*?background: #8a1010/);
});

test('markHostInsets tags embedded iframe and clears standalone', () => {
  const root = { attrs: {}, setAttribute(k, v) { this.attrs[k] = v; }, removeAttribute(k) { delete this.attrs[k]; } };
  const winEmbedded = {}; winEmbedded.parent = {};
  assert.equal(markHostInsets(winEmbedded, root), true);
  assert.equal(root.attrs['data-host-insets'], 'true');
  const winSolo = {}; winSolo.parent = winSolo;
  assert.equal(markHostInsets(winSolo, root), false);
  assert.equal(root.attrs['data-host-insets'], undefined);
  assert.equal(markHostInsets(null, root), false);
});

// A small DOM harness exercises the actual shipped handlers without a framework.
// Layout/painting still needs real browser verification.
function browserHarness() {
  let document;
  class Element {
    constructor(tag) {
      this.tagName = tag.toUpperCase(); this.children = []; this.dataset = {}; this.style = {};
      this.attributes = new Map(); this.handlers = new Map(); this.hidden = false;
      this.disabled = false; this.className = ''; this.textContent = '';
    }
    append(...children) { for (const child of children) { child.parentElement = this; this.children.push(child); } }
    setAttribute(name, value) { this.attributes.set(name, String(value)); }
    getAttribute(name) { return this.attributes.get(name) ?? null; }
    removeAttribute(name) { this.attributes.delete(name); }
    addEventListener(name, handler) { if (!this.handlers.has(name)) this.handlers.set(name, []); this.handlers.get(name).push(handler); }
    emit(name, event = {}) { for (const fn of this.handlers.get(name) || []) fn({preventDefault() {}, stopPropagation() {}, ...event}); }
    replaceChildren(...children) { this.children = []; this.append(...children); }
    contains(element) { return this === element || this.children.some(child => child.contains(element)); }
    closest() { for (let node = this; node; node = node.parentElement) if (node.hidden) return node; return null; }
    querySelector(selector = '') {
      const nodes = walk(this);
      const parts = String(selector).split(',').map(part => part.trim()).filter(Boolean);
      // Skip [hidden] controls so pause dialogs do not land on hidden nr-primary yes.
      const match = (part) => {
        if (part.includes('button.nr-primary') || (part.includes('.nr-primary') && part.includes('button'))) {
          return nodes.find(node => node.tagName === 'BUTTON' && String(node.className).includes('nr-primary') && !node.disabled && !node.hidden) || null;
        }
        if (part === 'h1' || part.startsWith('h1')) return nodes.find(node => node.tagName === 'H1' && !node.hidden) || null;
        if (part.includes('.nr-target')) return nodes.find(node => node.className === 'nr-target' && !node.hidden) || null;
        if (part.includes('button')) return nodes.find(node => node.tagName === 'BUTTON' && !node.disabled && !node.hidden) || null;
        return null;
      };
      if (parts.length) {
        for (const part of parts) { const found = match(part); if (found) return found; }
        return null;
      }
      return nodes.find(node => !node.hidden && (node.tagName === 'H1' || node.className === 'nr-target' || (node.tagName === 'BUTTON' && !node.disabled))) || null;
    }
    focus() { document.activeElement = this; }
  }
  const root = new Element('html'), app = new Element('div'); app.hidden = true; root.append(app);
  const docHandlers = new Map();
  const posts = [];
  document = {
    documentElement: root, activeElement: root,
    createElement: tag => new Element(tag),
    getElementById: id => id === 'modern-app' ? app : null,
    addEventListener(name, handler) {
      if (!docHandlers.has(name)) docHandlers.set(name, []);
      docHandlers.get(name).push(handler);
    },
    emit(name, event = {}) {
      for (const fn of docHandlers.get(name) || []) fn({preventDefault() {}, stopPropagation() {}, ...event});
    },
  };
  const observers = [];
  const browserWindow = {matchMedia: () => ({matches: false, addEventListener() {}})};
  // Distinct parent mimics the host shell iframe relationship.
  browserWindow.parent = { postMessage: (data, origin) => { posts.push({data, origin}); } };
  browserWindow.rivalCursor=require('../rival-cursor.js').rivalCursor;
  browserWindow.createShiritoriView=({section})=>({page:section('shiritori','sh-page'),update(){},isOverlayOpen:()=>false,headerAction(){}});
  vm.runInNewContext(fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8'), {
    document, window: browserWindow, location: {origin: 'http://localhost'}, console,
    MutationObserver: class { constructor(callback) { observers.push(callback); } observe() {} },
  });
  function notify(attributeName) { for (const observer of observers) observer([{attributeName}]); }
  function render(screen, overrides = {}) {
    const next = {v: 1, screen, kind: 'practice', max_number: 10, mode: 'ordered', difficulty: 'normal',
      ack: 0, bgm: true, sfx: true, target: 1, cells: ['playing', 'finished', 'review'].includes(screen) ? state().cells : [], ...overrides};
    root.setAttribute('data-modern-state', JSON.stringify(next)); notify('data-modern-state'); return next;
  }
  return {root, app, document, render, notify, posts, cells: () => walk(app).filter(node => node.className === 'nr-cell'),
    queue: () => JSON.parse(root.getAttribute('data-modern-commands') || '[]')};
}
function walk(element) { return element.children.flatMap(child => [child, ...walk(child)]); }

test('result warns about unavailable storage without claiming a saved record',()=>{
  const b=browserHarness();
  b.render('home',{chain:{}});
  assert.equal(b.app.hidden,false);
  b.render('finished',{storage_saved:false});
  const record=walk(b.app).find(n=>n.className==='nr-record');
  assert.match(record.textContent,/保存できませんでした/);
  b.render('finished',{storage_saved:true});
  assert.doesNotMatch(record.textContent,/保存できませんでした/);
});

test('both games reuse the same header nodes, positions and game-aware commands',()=>{
  const b=browserHarness();
  const header=walk(b.app).find(n=>n.className==='nr-toolbar');
  const controls=header.children;
  const back=controls.find(n=>n.textContent==='ゲーム選択');
  const pause=controls.find(n=>n.textContent==='一時停止');
  const retry=controls.find(n=>n.textContent==='やり直す');
  for(const [screen,extra] of [['ready',{}],['shiritori',{shiritori:{phase:'intro'}}]]) {
    b.render(screen,extra); assert.equal(back.hidden,false); assert.equal(pause.hidden,true);
    assert.equal(controls.indexOf(back),0);
  }
  back.emit('click'); assert.equal(b.queue().at(-1).action,'sh_exit');
  b.render('shiritori',{shiritori:{phase:'playing'}});
  assert.equal(back.hidden,true); assert.equal(pause.hidden,false); assert.equal(retry.hidden,false);
  pause.emit('click'); assert.equal(b.queue().at(-1).action,'sh_pause');
  b.render('playing'); pause.emit('click'); assert.equal(b.queue().at(-1).action,'pause');
});

test('number rival frame is unique, keeps input enabled and hides for pause or solo',()=>{
  const b=browserHarness(); b.render('playing',{kind:'battle',cpu_progress:.4});
  const selected=b.cells().filter(c=>c.dataset.cpuSelecting==='true');
  assert.equal(selected.length,1); assert.equal(selected[0].disabled,false);
  b.render('confirm',{kind:'battle'}); assert.ok(b.cells().every(c=>c.dataset.cpuSelecting==='false'));
  b.render('playing',{kind:'practice'}); assert.ok(b.cells().every(c=>c.dataset.cpuSelecting==='false'));
});

test('practice play HUD densifies YOU+お題 after CPU score-card hide (#100)', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const js = fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  // Base + compact/short breakpoints reclaim the empty third column.
  assert.match(css, /\.nr-hud:has\(> \.nr-cpu\[hidden\]\) \{[\s\S]*?grid-template-columns: minmax\(0, 1fr\) minmax\(0, 1\.35fr\);/);
  assert.match(css, /\.nr-hud:has\(> \.nr-cpu\[hidden\]\) \{ gap: 8px; grid-template-columns: minmax\(0, 1fr\) minmax\(0, 1\.4fr\); \}/);
  assert.match(css, /\.nr-hud:has\(> \.nr-cpu\[hidden\]\) \{ gap: 12px; grid-template-columns: minmax\(0, 1fr\) minmax\(0, 1\.3fr\); \}/);
  // JS still hides CPU score-card in practice (drives :has).
  assert.match(js, /cpuHud\.hidden = !battle/);
  assert.match(player, /modern-ui\.css\?v=settings-pressed-103-1/);
  assert.match(index, /player\.html\?v=practice-chains-104-1/);

  const b = browserHarness();
  const hudOf = () => walk(b.app).find(n => n.className === 'nr-hud');
  const cpuIn = (hud) => hud && hud.children.find(n => String(n.className).includes('nr-cpu'));
  const youIn = (hud) => hud && hud.children.find(n => String(n.className).includes('nr-you'));
  const targetIn = (hud) => hud && hud.children.find(n => String(n.className).includes('nr-target'));

  b.render('playing', {kind: 'battle', cells: state().cells});
  assert.equal(cpuIn(hudOf()).hidden, false, 'battle HUD shows CPU score-card');
  assert.ok(youIn(hudOf()), 'battle HUD keeps YOU');
  assert.ok(targetIn(hudOf()), 'battle HUD keeps お題');

  b.render('playing', {kind: 'practice', cells: state().cells});
  assert.equal(cpuIn(hudOf()).hidden, true, 'practice HUD hides CPU score-card');
  assert.equal(youIn(hudOf()).hidden, false, 'practice HUD keeps YOU');
  assert.ok(targetIn(hudOf()), 'practice HUD keeps お題');
  // Battle trio grid still declared for the non-:has path.
  assert.match(css, /\.nr-hud \{ display: grid; grid-template-columns: 1fr 1\.05fr 1fr;/);
});

test('practice hides LUNA cast on play stage and result (parity shiritori solo; #80)', () => {
  const js = fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8');
  assert.match(js, /playKoh\.wrap\.hidden = !battle;\s*resultKoh\.wrap\.hidden = !battle/);
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  assert.match(player, /modern-ui\.js\?v=miss-live-guidance-98-1/);
  assert.match(index, /player\.html\?v=practice-chains-104-1/);

  const b = browserHarness();
  const playStage = () => walk(b.app).find(n => n.className === 'nr-play-stage');
  const resultDuo = () => walk(b.app).find(n => n.className === 'nr-result-duo');
  const kohIn = (parent) => parent && parent.children.find(n => String(n.className).includes('nr-koh'));
  const rinIn = (parent) => parent && parent.children.find(n => String(n.className).includes('nr-rin'));

  b.render('playing', {kind: 'battle', cells: state().cells});
  assert.equal(kohIn(playStage()).hidden, false, 'battle play shows LUNA');
  assert.equal(rinIn(playStage()).hidden, false, 'battle play shows RIN');

  b.render('playing', {kind: 'practice', cells: state().cells});
  assert.equal(kohIn(playStage()).hidden, true, 'practice play hides LUNA');
  assert.equal(rinIn(playStage()).hidden, false, 'practice play keeps RIN');

  b.render('finished', {kind: 'battle', perfect: false, won: true, cells: state().cells});
  assert.equal(kohIn(resultDuo()).hidden, false, 'battle result shows LUNA');
  assert.equal(rinIn(resultDuo()).hidden, false, 'battle result shows RIN');

  b.render('finished', {kind: 'practice', perfect: false, won: true, cells: state().cells});
  assert.equal(kohIn(resultDuo()).hidden, true, 'practice result hides LUNA');
  assert.equal(rinIn(resultDuo()).hidden, false, 'practice result keeps RIN');
  // #17 replay focus still lands on もう一度遊ぶ with koh hidden.
  const finished = walk(b.app).find(n => n.dataset.screen === 'finished');
  const retry = walk(finished).find(n => n.tagName === 'BUTTON' && n.textContent === 'もう一度遊ぶ');
  assert.equal(b.document.activeElement, retry, 'practice result still focuses replay (#17)');
});

test('practice hides LUNA+VS on ready hero-cast (parity #80 play+result; #86)', () => {
  const js = fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8');
  assert.match(js, /heroKoh\.wrap\.hidden = !battle;\s*heroVersus\.hidden = !battle;/);
  assert.match(js, /playKoh\.wrap\.hidden = !battle;\s*resultKoh\.wrap\.hidden = !battle/);
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  assert.match(player, /modern-ui\.js\?v=miss-live-guidance-98-1/);
  assert.match(index, /player\.html\?v=practice-chains-104-1/);

  const b = browserHarness();
  const heroCast = () => walk(b.app).find(n => n.className === 'nr-hero-cast');
  const kohIn = (parent) => parent && parent.children.find(n => String(n.className).includes('nr-koh'));
  const rinIn = (parent) => parent && parent.children.find(n => String(n.className).includes('nr-rin'));
  const versusIn = (parent) => parent && parent.children.find(n => n.className === 'nr-versus');

  b.render('ready', {kind: 'battle', cells: []});
  assert.equal(kohIn(heroCast()).hidden, false, 'battle ready shows LUNA');
  assert.equal(versusIn(heroCast()).hidden, false, 'battle ready shows VS');
  assert.equal(rinIn(heroCast()).hidden, false, 'battle ready shows RIN');

  b.render('ready', {kind: 'practice', cells: []});
  assert.equal(kohIn(heroCast()).hidden, true, 'practice ready hides LUNA');
  assert.equal(versusIn(heroCast()).hidden, true, 'practice ready hides VS');
  assert.equal(rinIn(heroCast()).hidden, false, 'practice ready keeps RIN');

  // #80 play+result hide still wired; #50 ready focus still 1から順番.
  b.render('playing', {kind: 'practice', cells: state().cells});
  const playStage = walk(b.app).find(n => n.className === 'nr-play-stage');
  assert.equal(kohIn(playStage).hidden, true, 'practice play still hides LUNA (#80)');
  b.render('finished', {kind: 'practice', perfect: false, won: true, cells: state().cells});
  const resultDuo = walk(b.app).find(n => n.className === 'nr-result-duo');
  assert.equal(kohIn(resultDuo).hidden, true, 'practice result still hides LUNA (#80)');

  // Leave finished → ready so #50 entry focus runs (same-screen ready keeps focus).
  b.render('ready', {kind: 'practice', cells: []});
  const ready = walk(b.app).find(n => n.dataset.screen === 'ready');
  const ordered = walk(ready).find(n =>
    n.tagName === 'BUTTON' && String(n.className).includes('nr-primary'));
  assert.equal(b.document.activeElement, ordered, 'practice ready still focuses 1から順番 (#50)');
});

test('practice result solo-cast denser/centered after LUNA hide; drop redundant visibility CSS (#81)', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const mobile = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  // JS [hidden] owns hide — no leftover visibility:hidden rival slot on play stage.
  assert.ok(!/#modern-app\[data-kind='practice'\] \.nr-play-stage \.nr-koh \{ visibility:\s*hidden/.test(css),
    'redundant practice play visibility:hidden removed');
  // Solo cast (:has koh[hidden]) denser + centered — desktop + short-height + short-LS.
  assert.match(css, /\.nr-result-duo:has\(> \.nr-koh\[hidden\]\) \{ gap: 12px; justify-content: center; \}/);
  assert.match(css, /\.nr-result-duo:has\(> \.nr-koh\[hidden\]\) \{ gap: 6px; justify-content: center; \}/);
  assert.match(mobile, /\.nr-result-duo:has\(> \.nr-koh\[hidden\]\) \{ gap: 2px; justify-content: center; \}/);
  // #80 hide still wired; #17 focus target unchanged.
  assert.match(fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8'),
    /playKoh\.wrap\.hidden = !battle;\s*resultKoh\.wrap\.hidden = !battle/);
  assert.match(player, /modern-ui\.css\?v=settings-pressed-103-1/);
  assert.match(player, /mobile-layout\.css\?v=practice-chains-104-1/);
  assert.match(player, /modern-ui\.js\?v=miss-live-guidance-98-1/);
  assert.match(index, /player\.html\?v=practice-chains-104-1/);

  const b = browserHarness();
  const resultDuo = () => walk(b.app).find(n => n.className === 'nr-result-duo');
  const kohIn = (parent) => parent && parent.children.find(n => String(n.className).includes('nr-koh'));
  const rinIn = (parent) => parent && parent.children.find(n => String(n.className).includes('nr-rin'));

  // Need a previousScreen so finished entry focuses replay (#17), same as #80.
  b.render('playing', {kind: 'practice', cells: state().cells});
  b.render('finished', {kind: 'practice', perfect: false, won: true, cells: state().cells});
  const duo = resultDuo();
  assert.equal(kohIn(duo).hidden, true, 'practice result still hides LUNA (#80)');
  assert.equal(rinIn(duo).hidden, false, 'practice result keeps RIN');
  const finished = walk(b.app).find(n => n.dataset.screen === 'finished');
  const retry = walk(finished).find(n => n.tagName === 'BUTTON' && n.textContent === 'もう一度遊ぶ');
  assert.equal(b.document.activeElement, retry, 'practice solo result still focuses replay (#17)');

  b.render('finished', {kind: 'battle', perfect: false, won: true, cells: state().cells,
    player_points: 12, cpu_points: 5, goal: 12});
  assert.equal(kohIn(resultDuo()).hidden, false, 'battle result still shows LUNA');
});

test('practice play-stage solo cast centers RIN with absolute+left after LUNA hide (#83)', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  // Solo play: center RIN via absolute+left (parity denser result #82); battle duo left/right intact.
  assert.match(css, /\.nr-play-stage:has\(> \.nr-koh\[hidden\]\) \{ justify-content: center; position: relative; \}/);
  assert.match(css, /\.nr-play-stage:has\(> \.nr-koh\[hidden\]\) \.nr-rin \{[\s\S]*?position: absolute;[\s\S]*?left: 0;[\s\S]*?right: 0;[\s\S]*?margin-inline: auto/);
  // Absolute media still pins battle RIN left / LUNA right.
  assert.match(css, /\.nr-play-stage \.nr-rin \{ left: 0; \} \.nr-play-stage \.nr-koh \{ right: 0; \}/);
  // #80/#82 keep: JS hide + denser result solo-cast.
  assert.match(fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8'),
    /playKoh\.wrap\.hidden = !battle;\s*resultKoh\.wrap\.hidden = !battle/);
  assert.match(css, /\.nr-result-duo:has\(> \.nr-koh\[hidden\]\) \{ gap: 12px; justify-content: center; \}/);
  assert.match(player, /modern-ui\.css\?v=settings-pressed-103-1/);
  assert.match(player, /modern-ui\.js\?v=miss-live-guidance-98-1/);
  assert.match(index, /player\.html\?v=practice-chains-104-1/);

  const b = browserHarness();
  const playStage = () => walk(b.app).find(n => n.className === 'nr-play-stage');
  const kohIn = (parent) => parent && parent.children.find(n => String(n.className).includes('nr-koh'));
  const rinIn = (parent) => parent && parent.children.find(n => String(n.className).includes('nr-rin'));

  b.render('playing', {kind: 'practice', cells: state().cells});
  assert.equal(kohIn(playStage()).hidden, true, 'practice play still hides LUNA (#80)');
  assert.equal(rinIn(playStage()).hidden, false, 'practice play keeps RIN');

  b.render('playing', {kind: 'battle', cells: state().cells});
  assert.equal(kohIn(playStage()).hidden, false, 'battle play still shows LUNA');
  assert.equal(rinIn(playStage()).hidden, false, 'battle play still shows RIN');
});



test('modern view starts only after render and releases ownership on backend fallback', () => {
  const browser = browserHarness();
  assert.equal(browser.app.hidden, true); assert.equal(browser.root.getAttribute('data-modern-ready'), null);
  browser.render('ready');
  assert.equal(browser.app.hidden, false); assert.equal(browser.root.getAttribute('data-modern-ready'), 'true');
  browser.root.setAttribute('data-modern-ready', 'false'); browser.notify('data-modern-ready');
  assert.equal(browser.app.hidden, true); assert.equal(browser.root.getAttribute('data-modern-active'), null);
  browser.render('ready'); assert.equal(browser.app.hidden, false);
});

test('first screen is only a two-game chooser, with number options on another screen', () => {
  const browser = browserHarness();
  browser.render('home');
  const screens = walk(browser.app).filter(n => n.dataset.screen);
  assert.deepEqual(screens.filter(n => !n.hidden).map(n => n.dataset.screen), ['home']);
  const home = screens.find(n => n.dataset.screen === 'home');
  const games = walk(home).filter(n => n.tagName === 'BUTTON');
  assert.equal(games.length, 2);
  games[1].emit('click');
  assert.equal(browser.queue()[0].action, 'numbers');
  browser.render('ready');
  assert.deepEqual(screens.filter(n => !n.hidden).map(n => n.dataset.screen), ['ready']);
});

test('real cell handlers enqueue fast taps once and a mistake does not disable the tile', () => {
  const browser = browserHarness(); const round = browser.render('playing');
  const cells = browser.cells(); assert.equal(cells.length, 40);
  cells[0].emit('pointerdown', {button: 0, isPrimary: true}); cells[0].emit('click', {detail: 1});
  cells[1].emit('pointerdown', {button: 0, isPrimary: true}); cells[1].emit('click', {detail: 1});
  assert.deepEqual(browser.queue().map(item => item.index), [0, 1]);
  round.cells[1].effect = 'wrong'; round.cells[1].effect_id = 'wrong:42'; browser.render('playing', round);
  assert.equal(cells[1].disabled, false); assert.equal(cells[1].dataset.feedback, 'wrong');
  cells[1].emit('pointerdown', {button: 0, isPrimary: true});
  assert.deepEqual(browser.queue().map(item => item.index), [0, 1, 1]);
  assert.equal(browser.cells()[1], cells[1], 'board elements retain identity across snapshots');
});

test('miss outline CSS outlasts the bomb burst and stays distinct from CPU/correct', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  assert.match(css, /data-feedback='wrong'[^}]*box-shadow/);
  assert.match(css, /nr-fx-fade 1100ms/);
  assert.match(css, /nr-burst 720ms/);
  assert.match(css, /data-feedback='cpu'/);
});

test('miss feedback stays mounted beside a later correct and clears FX nodes when done', () => {
  const browser = browserHarness();
  const round = browser.render('playing');
  const cells = browser.cells();
  round.cells[1].effect = 'wrong';
  round.cells[1].effect_id = 'wrong:40';
  round.cells[2].effect = 'correct';
  round.cells[2].effect_id = 'correct:50';
  browser.render('playing', round);
  assert.equal(cells[1].dataset.feedback, 'wrong');
  assert.equal(cells[2].dataset.feedback, 'correct');
  assert.equal(cells[1].disabled, false, 'miss outline must not disable the next tap');
  const feedback = walk(browser.app).find(n => n.className === 'nr-feedback');
  // Latest effect wins the stage copy so miss/correct/CPU do not fight confusingly.
  assert.match(feedback.textContent, /ナイス/);
  assert.ok(walk(cells[1]).some(n => String(n.className || '').includes('nr-fx-wrong')));
  round.cells[1].effect_id = 'wrong:60';
  browser.render('playing', round);
  assert.match(feedback.textContent, /ちがう数字/);
  round.cells[1].effect = null;
  round.cells[1].effect_id = null;
  browser.render('playing', round);
  assert.equal(cells[1].dataset.feedback, '');
  assert.ok(!walk(cells[1]).some(n => String(n.className || '').includes('nr-fx')));
});

test('HUD miss copy does not regress when older miss outline outlasts correct/CPU', () => {
  const browser = browserHarness();
  const round = browser.render('playing');
  const feedback = walk(browser.app).find(n => n.className === 'nr-feedback');
  // Miss first — stage copy matches the durable outline.
  round.cells[1].effect = 'wrong';
  round.cells[1].effect_id = 'wrong:40';
  browser.render('playing', round);
  assert.match(feedback.textContent, /ちがう数字/);
  assert.equal(browser.cells()[1].dataset.feedback, 'wrong');
  // Later correct wins the HUD while the miss outline stays mounted (#18).
  round.cells[2].effect = 'correct';
  round.cells[2].effect_id = 'correct:50';
  browser.render('playing', round);
  assert.match(feedback.textContent, /ナイス/);
  assert.equal(browser.cells()[1].dataset.feedback, 'wrong');
  // Correct FX ends first; lingering miss outline must NOT revive stale miss copy.
  round.cells[2].effect = null;
  round.cells[2].effect_id = null;
  browser.render('playing', round);
  assert.equal(browser.cells()[1].dataset.feedback, 'wrong');
  assert.doesNotMatch(feedback.textContent, /ちがう数字/);
  assert.match(feedback.textContent, /あわてず|連続正解|青はあなた/);
  // Fresh miss after the floor clears still updates HUD.
  round.cells[1].effect = null;
  round.cells[1].effect_id = null;
  browser.render('playing', round);
  assert.doesNotMatch(feedback.textContent, /ちがう数字/);
  round.cells[3].effect = 'wrong';
  round.cells[3].effect_id = 'wrong:80';
  browser.render('playing', round);
  assert.match(feedback.textContent, /ちがう数字/);
});

test('HUD miss copy does not regress when older miss outline outlasts CPU claim', () => {
  const browser = browserHarness();
  const round = browser.render('playing', {kind: 'battle', target: 7, streak: 0});
  const feedback = walk(browser.app).find(n => n.className === 'nr-feedback');
  round.cells[1].effect = 'wrong';
  round.cells[1].effect_id = 'wrong:20';
  browser.render('playing', round);
  assert.match(feedback.textContent, /ちがう数字/);
  round.cells[6].owner = 'cpu';
  round.cells[6].effect = 'cpu';
  round.cells[6].effect_id = 'cpu:30';
  browser.render('playing', round);
  assert.match(feedback.textContent, /CPUが先に/);
  round.cells[6].effect = null;
  round.cells[6].effect_id = null;
  browser.render('playing', round);
  assert.equal(browser.cells()[1].dataset.feedback, 'wrong');
  assert.doesNotMatch(feedback.textContent, /ちがう数字/);
  assert.doesNotMatch(feedback.textContent, /CPUが先に/);
});

test('polite live region announces durable miss guidance; visual strip stays non-live', () => {
  const browser = browserHarness();
  const live = walk(browser.app).find(n => n.className === 'nr-sr-only' && n.getAttribute('aria-live') === 'polite');
  const feedback = walk(browser.app).find(n => n.className === 'nr-feedback');
  assert.ok(live, 'polite status live region present');
  assert.equal(live.getAttribute('role'), 'status');
  assert.equal(live.getAttribute('aria-atomic'), 'true');
  // Visual strip must stay non-live so SR hear one channel (#97 strip + #18/#20 floor).
  assert.equal(feedback.getAttribute('aria-live'), null);
  assert.equal(feedback.getAttribute('role'), null);
  const round = browser.render('playing', {target: 3, completed: 2, mistakes: 0});
  assert.match(live.textContent, /次の数字は3/);
  assert.doesNotMatch(live.textContent, /ちがう数字/);
  round.cells[1].effect = 'wrong';
  round.cells[1].effect_id = 'wrong:40';
  round.mistakes = 1;
  browser.render('playing', round);
  assert.match(feedback.textContent, /ちがう数字/);
  assert.match(live.textContent, /ちがう数字！お題を確認して、すぐ押し直そう/);
  assert.match(live.textContent, /ミス1回/);
  // Correct wins HUD + live; miss outline may still linger (#18).
  round.cells[2].effect = 'correct';
  round.cells[2].effect_id = 'correct:50';
  round.completed = 3;
  round.target = 4;
  browser.render('playing', round);
  assert.match(feedback.textContent, /ナイス/);
  assert.match(live.textContent, /ナイス！次のお題も、すぐに見つけよう/);
  assert.doesNotMatch(live.textContent, /ちがう数字/);
  // Correct FX ends; lingering miss must not revive stale guidance in live (#20 floor).
  round.cells[2].effect = null;
  round.cells[2].effect_id = null;
  browser.render('playing', round);
  assert.equal(browser.cells()[1].dataset.feedback, 'wrong');
  assert.doesNotMatch(feedback.textContent, /ちがう数字/);
  assert.doesNotMatch(live.textContent, /ちがう数字/);
  assert.doesNotMatch(live.textContent, /ナイス/);
  assert.match(live.textContent, /次の数字は4/);
});

test('polite live region announces CPU claim guidance without aria-live on feedback strip', () => {
  const browser = browserHarness();
  const live = walk(browser.app).find(n => n.className === 'nr-sr-only' && n.getAttribute('aria-live') === 'polite');
  const feedback = walk(browser.app).find(n => n.className === 'nr-feedback');
  const round = browser.render('playing', {kind: 'battle', target: 7, completed: 1, mistakes: 0});
  round.cells[6].owner = 'cpu';
  round.cells[6].effect = 'cpu';
  round.cells[6].effect_id = 'cpu:30';
  browser.render('playing', round);
  assert.equal(feedback.getAttribute('aria-live'), null);
  assert.match(feedback.textContent, /CPUが先に/);
  assert.match(live.textContent, /CPUが先に見つけた！次のお題を狙おう/);
});

test('CPU claim feedback is distinct from player-correct sparkles', () => {
  const browser = browserHarness();
  const round = browser.render('playing', {kind: 'battle', target: 7});
  const cells = browser.cells();
  round.cells[6].owner = 'cpu';
  round.cells[6].effect = 'cpu';
  round.cells[6].effect_id = 'cpu:99';
  browser.render('playing', round);
  assert.equal(cells[6].dataset.feedback, 'cpu');
  assert.equal(cells[6].dataset.owner, 'cpu');
  assert.match(cells[6].getAttribute('aria-label') || '', /CPU/);
  const fx = walk(cells[6]).find(n => String(n.className || '').includes('nr-fx'));
  assert.ok(fx, 'CPU claim mounts an effect overlay');
  assert.match(String(fx.className), /nr-fx-cpu/);
  assert.doesNotMatch(String(fx.className), /nr-fx-correct/);
  const badge = walk(fx).find(n => n.className === 'nr-cpu-claim');
  assert.equal(badge && badge.textContent, 'CPU');
  const feedback = walk(browser.app).find(n => n.className === 'nr-feedback');
  assert.match(feedback.textContent, /CPUが先に/);
  // Player-correct still uses mint sparkles, not the CPU badge.
  round.cells[0].owner = 'you';
  round.cells[0].effect = 'correct';
  round.cells[0].effect_id = 'correct:100';
  round.cells[6].effect = null;
  round.cells[6].effect_id = null;
  browser.render('playing', round);
  const youFx = walk(cells[0]).find(n => String(n.className || '').includes('nr-fx'));
  assert.match(String(youFx.className), /nr-fx-correct/);
  assert.doesNotMatch(feedback.textContent, /CPUが先に/);
});

test('keyboard focus survives correct selection and Enter is not queued twice', () => {
  const browser = browserHarness(); const round = browser.render('playing');
  const cells = browser.cells(); cells[0].focus();
  round.cells[0].owner = 'you'; browser.render('playing', round);
  assert.equal(browser.document.activeElement, cells[1]);
  browser.app.emit('keydown', {key: 'Enter', repeat: false});
  assert.equal(browser.queue().length, 0, 'focused buttons use their native click activation');
  cells[1].emit('click', {detail: 0}); assert.equal(browser.queue().length, 1);
  const target = walk(browser.app).find(node => node.className === 'nr-target'); target.focus();
  browser.app.emit('keydown', {key: 'ArrowRight'});
  assert.equal(browser.document.activeElement, cells[2]);
});

test('finished screen focuses replay and Enter retries without breaking title/review', () => {
  const b = browserHarness();
  b.render('playing');
  const cells = b.cells();
  cells[0].focus();
  assert.equal(b.document.activeElement, cells[0]);

  b.render('finished', {kind: 'battle', perfect: true, bonus: 1000, won: true});
  const retry = walk(b.app).find(n => n.tagName === 'BUTTON' && n.textContent === 'もう一度遊ぶ');
  const title = walk(b.app).find(n => n.tagName === 'BUTTON' && n.textContent === 'モード選択');
  const review = walk(b.app).find(n => n.tagName === 'BUTTON' && n.textContent === '対戦を振り返る');
  const award = walk(b.app).find(n => n.className === 'nr-award');
  assert.ok(retry && title && review, 'result actions stay available');
  assert.equal(review.hidden, false, 'battle review remains reachable');
  assert.equal(award.hidden, false, 'perfect award stays visible');
  assert.equal(b.document.activeElement, retry, 'result entry focuses primary replay');

  const before = b.queue().length;
  b.app.emit('keydown', {key: 'Enter', repeat: false});
  assert.equal(b.queue().length, before, 'focused replay button keeps native activation (no double command)');

  // Non-button focus (e.g. title heading) still offers a one-key retry path.
  const finishedScreen = walk(b.app).find(n => n.dataset.screen === 'finished');
  const heading = walk(finishedScreen).find(n => n.tagName === 'H1');
  heading.focus();
  b.app.emit('keydown', {key: 'Enter', repeat: false});
  assert.equal(b.queue().at(-1).action, 'retry');

  const afterRetry = b.queue().length;
  title.focus();
  b.app.emit('keydown', {key: ' ', repeat: false});
  assert.equal(b.queue().length, afterRetry, 'title/review buttons keep their own activation path');

  review.emit('click');
  assert.equal(b.queue().at(-1).action, 'review');
  b.render('review', {kind: 'battle', history: [{number: 1, owner: 'you', seconds: 1.25}]});
  const back = walk(b.app).find(n => n.tagName === 'BUTTON' && n.textContent === '結果へ戻る');
  back.focus();
  b.render('finished', {kind: 'battle', perfect: true, bonus: 1000, won: true});
  assert.equal(b.document.activeElement, retry, 'review→result also restores replay focus');
});

test('play start focuses first playable nr-cell for arrow nav; overlays and same-screen spared', () => {
  const b = browserHarness();
  const cellsState = Array.from({length: 40}, (_, i) => ({n: i + 1, owner: i === 0 ? 'you' : null}));

  // countdown → playing: skip claimed cell 0, land on first playable (index 1).
  b.render('countdown', {cells: []});
  const countBtn = walk(b.app).find(n => n.tagName === 'BUTTON' && n.textContent === 'モード選択へ');
  countBtn.focus();
  b.render('playing', {cells: cellsState});
  const cells = b.cells();
  assert.equal(cells[0].disabled, true);
  assert.equal(cells[1].disabled, false);
  assert.equal(b.document.activeElement, cells[1], 'play start focuses first playable cell');

  // Arrow nav continues from that origin without Tab.
  b.app.emit('keydown', {key: 'ArrowRight'});
  assert.equal(b.document.activeElement, cells[2], 'arrows work from auto-focused start cell');

  // Same-screen updates must not yank focus (mouse/touch users mid-board).
  cells[5].focus();
  b.render('playing', {cells: cellsState, completed: 1, target: 2});
  assert.equal(b.document.activeElement, cells[5], 'playing→playing keeps current focus');

  // Enter on a focused cell stays native (no double-queue).
  const before = b.queue().length;
  b.app.emit('keydown', {key: 'Enter', repeat: false});
  assert.equal(b.queue().length, before, 'focused cell keeps native Enter activation');
  cells[5].emit('click', {detail: 0});
  assert.equal(b.queue().at(-1).action, 'cell');
  assert.equal(b.queue().at(-1).index, 5);

  // Confirm (pause) screen: land on resume, never a hidden cell/yes control.
  b.render('confirm', {confirm_action: 'pause', cells: []});
  const resume = walk(b.app).find(n => n.tagName === 'BUTTON' && n.textContent === 'プレイを続ける');
  assert.equal(b.document.activeElement, resume, 'pause entry focuses プレイを続ける');
  assert.notEqual(b.document.activeElement.className, 'nr-cell');

  // Help overlay lands on 戻る (no cell focus while help is the active screen).
  b.render('help', {cells: []});
  const helpScreen = walk(b.app).find(n => n.dataset && n.dataset.screen === 'help');
  const helpBack = walk(helpScreen).find(n => n.tagName === 'BUTTON' && n.textContent === '戻る');
  assert.equal(b.document.activeElement, helpBack, 'help entry focuses 戻る');

  // finished still prefers replay (do not steal with cell focus).
  b.render('playing', {cells: cellsState});
  b.render('finished', {perfect: false, won: true});
  const retry = walk(b.app).find(n => n.tagName === 'BUTTON' && n.textContent === 'もう一度遊ぶ');
  assert.equal(b.document.activeElement, retry, 'result entry still focuses primary replay');
});

test('pause resume restores prior keyboardCell instead of play-start first cell', () => {
  const b = browserHarness();
  const cellsState = Array.from({length: 40}, (_, i) => ({n: i + 1, owner: i === 0 ? 'you' : null}));

  // Establish mid-board keyboard origin via play-start then arrows.
  b.render('countdown', {cells: []});
  b.render('playing', {cells: cellsState});
  const cells = b.cells();
  assert.equal(b.document.activeElement, cells[1], 'play start lands on first playable');
  b.app.emit('keydown', {key: 'ArrowRight'});
  b.app.emit('keydown', {key: 'ArrowRight'});
  b.app.emit('keydown', {key: 'ArrowRight'});
  assert.equal(b.document.activeElement, cells[4], 'pre-pause keyboard cell is mid-board');

  // Pause overlay: board hides; entry focuses resume (not prior cell / hidden yes).
  b.render('confirm', {confirm_action: 'pause', cells: []});
  const resumeBtn = walk(b.app).find(n => n.tagName === 'BUTTON' && n.textContent === 'プレイを続ける');
  assert.equal(b.document.activeElement, resumeBtn, 'pause entry focuses プレイを続ける');

  // Countdown resume screen, then back to playing — must restore cell 4, not cell 1 (#41).
  b.render('resuming', {cells: []});
  b.render('playing', {cells: cellsState, completed: 1, target: 2});
  assert.equal(b.document.activeElement, cells[4], 'resuming→playing restores prior keyboardCell');

  // Arrows continue from restored origin.
  b.app.emit('keydown', {key: 'ArrowRight'});
  assert.equal(b.document.activeElement, cells[5], 'arrows continue from restored cell');

  // Direct confirm→playing (if ever skipped) also restores, not first playable.
  cells[7].focus();
  b.render('confirm', {confirm_action: 'pause', cells: []});
  b.render('playing', {cells: cellsState});
  assert.equal(b.document.activeElement, cells[7], 'confirm→playing restores snapped cell focus');

  // If the prior cell was claimed during pause, fall back to a playable cell (no crash).
  cells[4].focus();
  b.render('confirm', {confirm_action: 'pause', cells: []});
  const claimed = cellsState.map((c, i) => (i === 0 || i === 4) ? {...c, owner: 'you'} : c);
  b.render('resuming', {cells: []});
  b.render('playing', {cells: claimed});
  const after = b.cells();
  assert.equal(after[4].disabled, true);
  assert.equal(b.document.activeElement.className, 'nr-cell');
  assert.equal(b.document.activeElement.disabled, false, 'claimed prior cell falls back to a playable cell');
});

test('countdown/resuming entry focuses モード選択へ or reclaim heading; play-start #41 intact', () => {
  const b = browserHarness();
  const screenOf = (name) => walk(b.app).find(n => n.dataset && n.dataset.screen === name);
  const btnIn = (root, text) => walk(root).find(n => n.tagName === 'BUTTON' && n.textContent === text);
  const cellsState = (owners = {}) => Array.from({length: 40}, (_, i) => ({
    n: i + 1, owner: owners[i] || null,
  }));

  // ready → countdown: land on 「モード選択へ」 (not ready start / ♪ chrome).
  b.render('ready', {cells: []});
  const ordered = walk(screenOf('ready')).find(n =>
    n.tagName === 'BUTTON' && String(n.className).includes('nr-primary'));
  ordered.focus();
  b.render('countdown', {cells: [], countdown: 3});
  const countScreen = screenOf('countdown');
  // resuming shares the same DOM section as countdown.
  const countTitle = btnIn(countScreen, 'モード選択へ');
  const countLabel = walk(countScreen).find(n => n.tagName === 'H1');
  const headerSound = walk(b.app).find(n => n.tagName === 'BUTTON' && n.getAttribute('aria-label') === 'BGMのオン・オフ');
  assert.ok(countTitle && countLabel, 'countdown exposes モード選択へ + heading');
  assert.equal(countTitle.hidden, false, 'countdown shows モード選択へ');
  assert.equal(b.document.activeElement, countTitle, 'countdown entry focuses モード選択へ');
  assert.notEqual(b.document.activeElement, ordered);
  assert.notEqual(b.document.activeElement, headerSound);

  // Same-screen countdown ticks must not yank focus (user may Tab elsewhere briefly).
  headerSound.focus();
  b.render('countdown', {cells: [], countdown: 2});
  assert.equal(b.document.activeElement, headerSound, 'countdown→countdown keeps current focus');

  // Re-enter countdown (e.g. after a brief leave via home path simulation): explicit again.
  b.render('ready', {cells: []});
  b.render('countdown', {cells: [], countdown: 3});
  assert.equal(b.document.activeElement, countTitle, 're-entry still focuses モード選択へ');

  // countdown → playing still prefers first playable cell (#41), not leftover cancel.
  const owners = {0: 'you'};
  countTitle.focus();
  b.render('playing', {cells: cellsState(owners), target: 2});
  const cells = b.cells();
  assert.equal(b.document.activeElement, cells[1], 'countdown→playing still focuses first playable (#41)');

  // Pause → resuming: モード選択へ is hidden; reclaim onto heading (not hidden yes / ♪).
  cells[4].focus();
  b.render('confirm', {confirm_action: 'pause', cells: []});
  const resumeBtn = btnIn(screenOf('confirm'), 'プレイを続ける');
  assert.equal(b.document.activeElement, resumeBtn, 'pause entry still focuses プレイを続ける');
  b.render('resuming', {cells: [], countdown: 2});
  assert.equal(countTitle.hidden, true, 'resuming hides モード選択へ');
  assert.equal(b.document.activeElement, countLabel, 'resuming entry reclaims onto countdown heading');
  assert.notEqual(b.document.activeElement, countTitle, 'must not focus hidden モード選択へ');
  assert.notEqual(b.document.activeElement, headerSound);

  // Same-screen resuming ticks leave focus alone.
  headerSound.focus();
  b.render('resuming', {cells: [], countdown: 1});
  assert.equal(b.document.activeElement, headerSound, 'resuming→resuming keeps current focus');

  // resuming → playing restores prior keyboardCell (#42), not play-start first cell.
  b.render('confirm', {confirm_action: 'pause', cells: []});
  b.render('resuming', {cells: [], countdown: 1});
  assert.equal(b.document.activeElement, countLabel, 're-entry still reclaims heading');
  b.render('playing', {cells: cellsState(owners), target: 2});
  assert.equal(b.document.activeElement, cells[4], 'resuming→playing still restores prior keyboardCell (#42)');

  // ready entry / confirm entry still win over countdown leftovers.
  b.render('ready', {cells: []});
  assert.equal(
    b.document.activeElement,
    walk(screenOf('ready')).find(n => n.tagName === 'BUTTON' && String(n.className).includes('nr-primary')),
    'ready entry still focuses 1から順番 (#50)'
  );
  b.render('playing', {cells: cellsState()});
  b.render('confirm', {confirm_action: 'pause', cells: []});
  assert.equal(
    b.document.activeElement,
    btnIn(screenOf('confirm'), 'プレイを続ける'),
    'pause entry still focuses プレイを続ける (#43)'
  );
});

test('countdown/resuming Tab stays on cancel or heading and does not escape to chrome', () => {
  const b = browserHarness();
  const screenOf = (name) => walk(b.app).find(n => n.dataset && n.dataset.screen === name);
  const btnIn = (root, text) => walk(root).find(n => n.tagName === 'BUTTON' && n.textContent === text);
  const headerSound = walk(b.app).find(n => n.tagName === 'BUTTON' && n.getAttribute('aria-label') === 'BGMのオン・オフ');

  // Countdown: single 「モード選択へ」 stop; Tab/Shift+Tab stay put; chrome reclaim.
  b.render('ready', {cells: []});
  b.render('countdown', {cells: [], countdown: 3});
  const countScreen = screenOf('countdown');
  const countTitle = btnIn(countScreen, 'モード選択へ');
  const countLabel = walk(countScreen).find(n => n.tagName === 'H1');
  assert.ok(countTitle && countLabel, 'countdown exposes モード選択へ + heading');
  assert.equal(countTitle.hidden, false, 'countdown shows モード選択へ');
  assert.equal(b.document.activeElement, countTitle, 'countdown entry still focuses モード選択へ (#55)');

  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, countTitle, 'countdown Tab stays on モード選択へ');
  assert.notEqual(b.document.activeElement, headerSound, 'countdown Tab must not escape to ♪ chrome');
  countTitle.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: true});
  assert.equal(b.document.activeElement, countTitle, 'countdown Shift+Tab also stays on モード選択へ');

  headerSound.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, countTitle, 'Tab from chrome re-enters countdown on モード選択へ');

  // Same-screen tick must not yank focus while trap is active.
  headerSound.focus();
  b.render('countdown', {cells: [], countdown: 2});
  assert.equal(b.document.activeElement, headerSound, 'countdown→countdown still keeps current focus');
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, countTitle, 'Tab after tick still reclaims onto モード選択へ');

  // Resuming: cancel hidden; Tab reclaims onto heading (not ♪ / hidden button).
  b.render('playing', {cells: Array.from({length: 40}, (_, i) => ({n: i + 1, owner: null}))});
  b.render('confirm', {confirm_action: 'pause', cells: []});
  b.render('resuming', {cells: [], countdown: 2});
  assert.equal(countTitle.hidden, true, 'resuming hides モード選択へ');
  assert.equal(b.document.activeElement, countLabel, 'resuming entry still reclaims heading (#55)');

  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, countLabel, 'resuming Tab stays on countdown heading');
  assert.notEqual(b.document.activeElement, headerSound, 'resuming Tab must not escape to ♪ chrome');
  assert.notEqual(b.document.activeElement, countTitle, 'must not focus hidden モード選択へ');
  countLabel.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: true});
  assert.equal(b.document.activeElement, countLabel, 'resuming Shift+Tab also stays on heading');

  headerSound.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, countLabel, 'Tab from chrome re-enters resuming on heading');

  // Confirm trap still works after countdown (#45 regression guard).
  b.render('playing', {cells: Array.from({length: 40}, (_, i) => ({n: i + 1, owner: null}))});
  b.render('confirm', {confirm_action: 'pause', cells: []});
  const resume = btnIn(screenOf('confirm'), 'プレイを続ける');
  assert.equal(b.document.activeElement, resume, 'pause entry still focuses resume');
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.notEqual(b.document.activeElement, headerSound, 'confirm Tab still trapped after countdown');
});

test('confirm/help entry focuses primary dialog control without Tab hunting', () => {
  const b = browserHarness();
  const cellsState = Array.from({length: 40}, (_, i) => ({n: i + 1, owner: null}));
  const screenOf = (name) => walk(b.app).find(n => n.dataset && n.dataset.screen === name);
  const btnIn = (screen, text) => walk(screen).find(n => n.tagName === 'BUTTON' && n.textContent === text);

  // playing → pause: visible resume, not hidden nr-primary yes.
  b.render('playing', {cells: cellsState});
  const cells = b.cells();
  cells[3].focus();
  b.render('confirm', {confirm_action: 'pause', cells: []});
  const confirmScreen = screenOf('confirm');
  const resume = btnIn(confirmScreen, 'プレイを続ける');
  const hiddenYes = walk(confirmScreen).find(n => n.tagName === 'BUTTON' && String(n.className).includes('nr-primary') && n.hidden);
  assert.ok(resume, 'pause exposes プレイを続ける');
  assert.ok(hiddenYes, 'pause keeps affirmative yes hidden');
  assert.equal(b.document.activeElement, resume, 'pause entry focuses プレイを続ける');
  assert.notEqual(b.document.activeElement, hiddenYes, 'pause must not focus hidden yes');

  // Same-screen confirm updates leave mouse/keyboard focus alone.
  const retryExtra = btnIn(confirmScreen, '新しい配置でやり直す');
  retryExtra.focus();
  b.render('confirm', {confirm_action: 'pause', cells: [], sfx: false});
  assert.equal(b.document.activeElement, retryExtra, 'confirm→confirm keeps current focus');

  // retry/title: affirmative primary (はい path → やり直す / 戻る labels).
  b.render('playing', {cells: cellsState});
  cells[2].focus();
  b.render('confirm', {confirm_action: 'retry', cells: []});
  const retryYes = btnIn(screenOf('confirm'), 'やり直す');
  assert.equal(b.document.activeElement, retryYes, 'retry entry focuses affirmative yes');
  assert.equal(retryYes.hidden, false);
  assert.ok(String(retryYes.className).includes('nr-primary'));

  b.render('playing', {cells: cellsState});
  cells[1].focus();
  b.render('confirm', {confirm_action: 'title', cells: []});
  const titleYes = walk(screenOf('confirm')).find(n => n.tagName === 'BUTTON' && n.textContent === '戻る' && String(n.className).includes('nr-primary'));
  assert.equal(b.document.activeElement, titleYes, 'title entry focuses affirmative yes');

  // ready → help: 戻る primary (scoped to help screen; confirm also has a 戻る label).
  b.render('ready', {cells: []});
  const helpBtn = walk(b.app).find(n => n.tagName === 'BUTTON' && n.getAttribute('aria-label') === '遊び方');
  helpBtn.focus();
  b.render('help', {cells: []});
  const helpBack = btnIn(screenOf('help'), '戻る');
  assert.equal(b.document.activeElement, helpBack, 'help entry focuses 戻る');
  assert.ok(String(helpBack.className).includes('nr-primary'));

  // finished → review: primary 「結果へ戻る」 (explicit #43 parity; not only hidden-reclaim).
  const reviewCells = Array.from({length: 40}, (_, i) => ({n: i + 1, owner: null}));
  b.render('finished', {kind: 'battle', cells: reviewCells});
  const reviewOpen = walk(b.app).find(n => n.tagName === 'BUTTON' && n.textContent === '対戦を振り返る');
  reviewOpen.focus();
  b.render('review', {kind: 'battle', history: [{number: 1, owner: 'you', seconds: 1.2}], cells: reviewCells});
  const reviewBack = btnIn(screenOf('review'), '結果へ戻る');
  assert.equal(b.document.activeElement, reviewBack, 'review entry focuses 結果へ戻る');
  assert.ok(String(reviewBack.className).includes('nr-primary'));

  // Same-screen review updates leave current focus alone.
  reviewBack.focus();
  b.render('review', {kind: 'battle', history: [{number: 1, owner: 'you', seconds: 1.2}, {number: 2, owner: 'cpu', seconds: 2.0}], cells: reviewCells});
  assert.equal(b.document.activeElement, reviewBack, 'review→review keeps current focus');

  // Esc on pause still resumes (#16); focus target does not change Esc wiring.
  const before = b.queue().length;
  b.render('confirm', {confirm_action: 'pause', cells: []});
  assert.equal(b.document.activeElement, resume, 're-entry still focuses resume');
  b.app.emit('keydown', {key: 'Escape'});
  assert.equal(b.queue().at(-1).action, 'yes', 'Esc on pause still resumes via yes');
  assert.equal(b.queue().length, before + 1);
});

test('ready entry focuses primary start 1から順番; same-screen and overlays spared', () => {
  const b = browserHarness();
  const screenOf = (name) => walk(b.app).find(n => n.dataset && n.dataset.screen === name);
  const btnIn = (screen, text) => walk(screen).find(n => n.tagName === 'BUTTON' && n.textContent === text);
  // Composite start buttons put labels in child <strong>; class distinguishes primary.
  const primaryStart = (screen) => walk(screen).find(n =>
    n.tagName === 'BUTTON' && String(n.className).includes('nr-primary'));
  const strongLabel = (btn) => {
    const s = walk(btn).find(n => n.tagName === 'STRONG');
    return s ? s.textContent : '';
  };

  // home → ready: land on 「1から順番」 (not kind/range chrome).
  b.render('home', {cells: []});
  const numberGame = walk(screenOf('home')).find(n =>
    n.tagName === 'BUTTON' && String(n.className).includes('nr-number-game'));
  assert.ok(numberGame, 'home exposes 数字さがし card');
  numberGame.focus();
  b.render('ready', {cells: []});
  const readyScreen = screenOf('ready');
  const ordered = primaryStart(readyScreen);
  const random = walk(readyScreen).find(n =>
    n.tagName === 'BUTTON' && String(n.className).includes('nr-secondary'));
  assert.ok(ordered && random, 'ready exposes ordered primary and random secondary');
  assert.equal(strongLabel(ordered), '1から順番');
  assert.equal(strongLabel(random), 'ランダム');
  assert.equal(b.document.activeElement, ordered, 'ready entry focuses 1から順番');

  // Same-screen ready updates must not yank focus (mouse/touch mid-setup).
  const range20 = walk(readyScreen).find(n => n.tagName === 'BUTTON' && n.getAttribute('aria-label') === '1から20まで');
  range20.focus();
  b.render('ready', {cells: [], max_number: 20, kind: 'battle'});
  assert.equal(b.document.activeElement, range20, 'ready→ready keeps current focus');

  // finished → title → ready also restores primary start.
  b.render('finished', {perfect: false, won: true});
  const title = walk(b.app).find(n => n.tagName === 'BUTTON' && n.textContent === 'モード選択');
  title.focus();
  b.render('ready', {cells: []});
  assert.equal(b.document.activeElement, ordered, 'title→ready focuses 1から順番');

  // ready → help still prefers 戻る (#43); help must not be stolen by ready focus.
  b.render('ready', {cells: []});
  assert.equal(b.document.activeElement, ordered, 're-entry still focuses ordered');
  b.render('help', {cells: []});
  const helpBack = btnIn(screenOf('help'), '戻る');
  assert.equal(b.document.activeElement, helpBack, 'help entry still focuses 戻る');

  // help → ready returns to primary start (parity with overlay close).
  b.render('ready', {cells: []});
  assert.equal(b.document.activeElement, ordered, 'help→ready focuses 1から順番');

  // Confirm/pause overlay entry still wins over any ready leftover (#43).
  const cellsState = Array.from({length: 40}, (_, i) => ({n: i + 1, owner: null}));
  b.render('playing', {cells: cellsState});
  b.render('confirm', {confirm_action: 'pause', cells: []});
  const resume = btnIn(screenOf('confirm'), 'プレイを続ける');
  assert.equal(b.document.activeElement, resume, 'pause entry still focuses プレイを続ける');
});

test('ready Tab cycles setup controls and does not escape to chrome', () => {
  const b = browserHarness();
  const screenOf = (name) => walk(b.app).find(n => n.dataset && n.dataset.screen === name);
  const headerSound = walk(b.app).find(n => n.tagName === 'BUTTON' && n.getAttribute('aria-label') === 'BGMのオン・オフ');
  const headerHelp = walk(b.app).find(n => n.tagName === 'BUTTON' && n.textContent === '遊び方');
  const gamesBack = walk(b.app).find(n => n.tagName === 'BUTTON' && n.textContent === 'ゲーム選択');
  const collectStops = (roots) => {
    const stops = [];
    const visit = (node) => {
      if (!node || node.hidden) return;
      if (node.tagName === 'BUTTON' && !node.disabled) stops.push(node);
      for (const child of node.children || []) visit(child);
    };
    for (const root of roots) visit(root);
    return stops;
  };
  const setupRoots = (readyScreen) => {
    const kind = walk(readyScreen).find(n => n.getAttribute && n.getAttribute('aria-label') === '遊び方を選ぶ');
    const ranges = walk(readyScreen).find(n => n.getAttribute && n.getAttribute('aria-label') === '数字の範囲');
    const levels = walk(readyScreen).find(n => n.getAttribute && n.getAttribute('aria-label') === 'CPUの強さ');
    const difficultyWrap = levels && levels.parentElement;
    const ordered = walk(readyScreen).find(n =>
      n.tagName === 'BUTTON' && String(n.className).includes('nr-primary'));
    const random = walk(readyScreen).find(n =>
      n.tagName === 'BUTTON' && String(n.className).includes('nr-secondary'));
    const startGroup = ordered && ordered.parentElement;
    return {kind, ranges, difficultyWrap, startGroup, ordered, random};
  };

  // Battle ready: entry 「1から順番」 (#50); Tab cycles kind/range/difficulty/start only.
  b.render('home', {cells: []});
  b.render('ready', {cells: [], kind: 'battle', max_number: 10, difficulty: 'normal'});
  const readyScreen = screenOf('ready');
  const roots = setupRoots(readyScreen);
  assert.equal(b.document.activeElement, roots.ordered, 'ready entry still focuses 1から順番 (#50)');
  assert.equal(roots.difficultyWrap.hidden, false, 'battle shows difficulty');

  const battleStops = collectStops([roots.kind, roots.ranges, roots.difficultyWrap, roots.startGroup]);
  assert.equal(battleStops.length, 11, 'battle setup exposes kind+range+difficulty+start');
  assert.ok(battleStops.includes(roots.ordered) && battleStops.includes(roots.random));
  assert.ok(!battleStops.includes(headerSound), 'header BGM is outside the trap');
  assert.ok(!battleStops.includes(headerHelp), 'header 遊び方 is outside the trap');
  assert.ok(!battleStops.includes(gamesBack), 'header ゲーム選択 is outside the trap');
  const settings = walk(readyScreen).filter(n =>
    n.tagName === 'BUTTON' && String(n.className).includes('nr-setting'));
  assert.ok(settings.length >= 2, 'ready still exposes sfx/motion settings');
  for (const btn of settings) {
    assert.ok(!battleStops.includes(btn), 'ready settings stay outside the setup trap');
  }

  const orderedIdx = battleStops.indexOf(roots.ordered);
  roots.ordered.focus();
  for (let i = 0; i < battleStops.length; i++) {
    const expected = battleStops[(orderedIdx + i + 1) % battleStops.length];
    b.app.emit('keydown', {key: 'Tab', shiftKey: false});
    assert.equal(b.document.activeElement, expected, `battle Tab step ${i + 1} stays in setup`);
    assert.notEqual(b.document.activeElement, headerSound, 'Tab must not escape to ♪ chrome');
  }
  roots.ordered.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: true});
  assert.equal(
    b.document.activeElement,
    battleStops[(orderedIdx - 1 + battleStops.length) % battleStops.length],
    'Shift+Tab wraps inside setup'
  );

  // Focus already on chrome: Tab pulls back into setup (first kind control).
  headerSound.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, battleStops[0], 'Tab from chrome re-enters setup');

  // Practice hides difficulty; Tab still cycles remaining setup controls only.
  // Leave and re-enter ready so #50 entry focus runs (same-screen ready keeps focus).
  b.render('home', {cells: []});
  b.render('ready', {cells: [], kind: 'practice', max_number: 20});
  assert.equal(b.document.activeElement, roots.ordered, 'practice ready still focuses 1から順番 (#50)');
  assert.equal(roots.difficultyWrap.hidden, true, 'practice hides difficulty');
  const practiceStops = collectStops([roots.kind, roots.ranges, roots.difficultyWrap, roots.startGroup]);
  assert.equal(practiceStops.length, 8, 'practice setup omits hidden difficulty');
  assert.ok(!practiceStops.some(n => walk(roots.difficultyWrap).includes(n)));
  roots.ordered.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, roots.random, 'practice Tab moves to ランダム');
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, practiceStops[0], 'practice Tab wraps to first kind');
  assert.notEqual(b.document.activeElement, headerSound);

  // Confirm trap still works after ready (#45 regression guard).
  const cellsState = Array.from({length: 40}, (_, i) => ({n: i + 1, owner: null}));
  b.render('playing', {cells: cellsState});
  b.render('confirm', {confirm_action: 'pause', cells: []});
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.notEqual(b.document.activeElement, headerSound, 'confirm Tab still trapped after ready');

  // Playing leaves Tab alone (no ready trap bleed).
  b.render('playing', {cells: cellsState});
  const cell = b.cells()[0];
  cell.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, cell, 'playing leaves Tab alone (no preventDefault cycle)');
});

test('home entry focuses first enabled game card; same-screen and ready spared', () => {
  const b = browserHarness();
  const screenOf = (name) => walk(b.app).find(n => n.dataset && n.dataset.screen === name);
  const btnIn = (screen, text) => walk(screen).find(n => n.tagName === 'BUTTON' && n.textContent === text);
  const homeScreen = () => screenOf('home');
  const pictureGame = () => walk(homeScreen()).find(n =>
    n.tagName === 'BUTTON' && String(n.className).includes('nr-picture-game'));
  const numberGame = () => walk(homeScreen()).find(n =>
    n.tagName === 'BUTTON' && String(n.className).includes('nr-number-game'));

  // ready → home (ゲーム選択): land on first enabled card (絵しりとり when available).
  b.render('ready', {cells: []});
  const gamesBack = walk(b.app).find(n => n.tagName === 'BUTTON' && n.textContent === 'ゲーム選択');
  assert.ok(gamesBack, 'ready exposes ゲーム選択');
  gamesBack.focus();
  b.render('home', {cells: []});
  assert.ok(pictureGame() && !pictureGame().disabled, 'harness enables 絵しりとり');
  assert.equal(b.document.activeElement, pictureGame(), 'home entry focuses first enabled card');
  assert.notEqual(b.document.activeElement, gamesBack, 'must not leave focus on header ゲーム選択');

  // Same-screen home updates must not yank focus (mouse/touch mid-chooser).
  numberGame().focus();
  b.render('home', {cells: [], bgm: false});
  assert.equal(b.document.activeElement, numberGame(), 'home→home keeps current focus');

  // When picture is unavailable, fall through to 数字さがし.
  pictureGame().disabled = true;
  b.render('ready', {cells: []});
  gamesBack.focus();
  b.render('home', {cells: []});
  assert.equal(b.document.activeElement, numberGame(), 'disabled picture → focuses 数字さがし');
  pictureGame().disabled = false;

  // home → ready still prefers 「1から順番」 (#50); ready must not be stolen by home.
  numberGame().focus();
  b.render('ready', {cells: []});
  const ordered = walk(screenOf('ready')).find(n =>
    n.tagName === 'BUTTON' && String(n.className).includes('nr-primary'));
  assert.equal(b.document.activeElement, ordered, 'ready entry still focuses 1から順番');

  // ready → help still prefers 戻る (#43).
  b.render('help', {cells: []});
  const helpBack = btnIn(screenOf('help'), '戻る');
  assert.equal(b.document.activeElement, helpBack, 'help entry still focuses 戻る');
});

test('home Tab cycles enabled game cards and does not escape to chrome', () => {
  const b = browserHarness();
  const screenOf = (name) => walk(b.app).find(n => n.dataset && n.dataset.screen === name);
  const homeScreen = () => screenOf('home');
  const pictureGame = () => walk(homeScreen()).find(n =>
    n.tagName === 'BUTTON' && String(n.className).includes('nr-picture-game'));
  const numberGame = () => walk(homeScreen()).find(n =>
    n.tagName === 'BUTTON' && String(n.className).includes('nr-number-game'));
  const headerSound = walk(b.app).find(n =>
    n.tagName === 'BUTTON' && n.getAttribute('aria-label') === 'BGMのオン・オフ');
  const gamesBack = walk(b.app).find(n => n.tagName === 'BUTTON' && n.textContent === 'ゲーム選択');

  // ready → home: entry first card (#51); Tab cycles cards only, never ♪ chrome.
  b.render('ready', {cells: []});
  gamesBack.focus();
  b.render('home', {cells: []});
  assert.equal(b.document.activeElement, pictureGame(), 'home entry still focuses first card (#51)');
  assert.ok(pictureGame() && !pictureGame().disabled, 'harness enables 絵しりとり');

  const homeStops = [];
  (function visit(node) {
    if (!node || node.hidden) return;
    if (node.tagName === 'BUTTON' && !node.disabled) homeStops.push(node);
    for (const child of node.children || []) visit(child);
  })(walk(homeScreen()).find(n => String(n.className).includes('nr-game-choices')));
  assert.deepEqual(homeStops, [pictureGame(), numberGame()], 'home trap is enabled game cards only');
  assert.ok(!homeStops.includes(headerSound), 'header BGM is outside the trap');
  assert.ok(!homeStops.includes(gamesBack), 'ゲーム選択 is outside the trap');

  for (let i = 0; i < homeStops.length; i++) {
    const expected = homeStops[(i + 1) % homeStops.length];
    b.app.emit('keydown', {key: 'Tab', shiftKey: false});
    assert.equal(b.document.activeElement, expected, `Tab step ${i + 1} stays on game cards`);
    assert.notEqual(b.document.activeElement, headerSound, 'Tab must not escape to ♪ chrome');
  }
  pictureGame().focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: true});
  assert.equal(b.document.activeElement, numberGame(), 'Shift+Tab wraps inside chooser');
  assert.notEqual(b.document.activeElement, headerSound);

  // Focus already on chrome: Tab pulls back into the chooser (first enabled card).
  headerSound.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, homeStops[0], 'Tab from chrome re-enters chooser');

  // Disabled picture: single-stop Tab stays on 数字さがし (no chrome escape).
  pictureGame().disabled = true;
  b.render('ready', {cells: []});
  gamesBack.focus();
  b.render('home', {cells: []});
  assert.equal(b.document.activeElement, numberGame(), 'disabled picture still focuses 数字さがし (#51)');
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, numberGame(), 'single-card Tab stays on 数字さがし');
  assert.notEqual(b.document.activeElement, headerSound);
  b.app.emit('keydown', {key: 'Tab', shiftKey: true});
  assert.equal(b.document.activeElement, numberGame(), 'single-card Shift+Tab stays on 数字さがし');
  pictureGame().disabled = false;

  // Ready trap still works after home (#52 regression guard).
  b.render('ready', {cells: []});
  const ordered = walk(screenOf('ready')).find(n =>
    n.tagName === 'BUTTON' && String(n.className).includes('nr-primary'));
  assert.equal(b.document.activeElement, ordered, 'ready entry still focuses 1から順番 (#50)');
  ordered.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.notEqual(b.document.activeElement, headerSound, 'ready Tab still trapped after home');
  assert.notEqual(b.document.activeElement, ordered, 'ready Tab moves inside setup');

  // Playing leaves Tab alone (no home trap bleed).
  const cellsState = Array.from({length: 40}, (_, i) => ({n: i + 1, owner: null}));
  b.render('playing', {cells: cellsState});
  const cell = b.cells()[0];
  cell.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, cell, 'playing leaves Tab alone after home trap');
});


test('confirm Tab cycles dialog controls and does not escape to chrome', () => {
  const b = browserHarness();
  const cellsState = Array.from({length: 40}, (_, i) => ({n: i + 1, owner: null}));
  const screenOf = (name) => walk(b.app).find(n => n.dataset && n.dataset.screen === name);
  const btnIn = (screen, text) => walk(screen).find(n => n.tagName === 'BUTTON' && n.textContent === text);
  const headerSound = walk(b.app).find(n => n.tagName === 'BUTTON' && n.getAttribute('aria-label') === 'BGMのオン・オフ');

  // Pause dialog: resume → extras → settings, then wrap; never land on header ♪.
  b.render('playing', {cells: cellsState});
  b.cells()[0].focus();
  b.render('confirm', {confirm_action: 'pause', cells: []});
  const confirmScreen = screenOf('confirm');
  const resume = btnIn(confirmScreen, 'プレイを続ける');
  assert.equal(b.document.activeElement, resume, 'pause entry still focuses resume (#43)');

  const pauseStops = [];
  (function visit(node) {
    if (!node || node.hidden) return;
    if (node.tagName === 'BUTTON' && !node.disabled) pauseStops.push(node);
    for (const child of node.children || []) visit(child);
  })(confirmScreen);
  assert.ok(pauseStops.length >= 4, 'pause exposes multiple tab stops');
  assert.equal(pauseStops[0], resume);
  assert.ok(!pauseStops.includes(headerSound), 'header BGM is outside the trap');

  for (let i = 0; i < pauseStops.length; i++) {
    const expected = pauseStops[(i + 1) % pauseStops.length];
    b.app.emit('keydown', {key: 'Tab', shiftKey: false});
    assert.equal(b.document.activeElement, expected, `Tab step ${i + 1} stays in dialog`);
    assert.notEqual(b.document.activeElement, headerSound, 'Tab must not escape to ♪ chrome');
  }
  // Shift+Tab wraps backward from resume to the last stop.
  resume.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: true});
  assert.equal(b.document.activeElement, pauseStops[pauseStops.length - 1], 'Shift+Tab wraps inside dialog');
  assert.notEqual(b.document.activeElement, headerSound);

  // Focus already on chrome: Tab pulls back into the dialog instead of leaving.
  headerSound.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, pauseStops[0], 'Tab from chrome re-enters dialog');

  // Esc still resumes (#16) after Tab cycling.
  const beforeEsc = b.queue().length;
  b.app.emit('keydown', {key: 'Escape'});
  assert.equal(b.queue().at(-1).action, 'yes', 'Esc on pause still resumes via yes');
  assert.equal(b.queue().length, beforeEsc + 1);

  // Retry confirm: affirmative yes remains entry (#43); Tab cycles yes/no/settings only.
  b.render('playing', {cells: cellsState});
  b.cells()[2].focus();
  b.render('confirm', {confirm_action: 'retry', cells: []});
  const retryScreen = screenOf('confirm');
  const retryYes = btnIn(retryScreen, 'やり直す');
  assert.equal(b.document.activeElement, retryYes, 'retry entry still focuses affirmative yes');
  const retryStops = [];
  (function visit(node) {
    if (!node || node.hidden) return;
    if (node.tagName === 'BUTTON' && !node.disabled) retryStops.push(node);
    for (const child of node.children || []) visit(child);
  })(retryScreen);
  assert.ok(retryStops.includes(retryYes));
  assert.ok(!retryStops.some(n => n.textContent === '新しい配置でやり直す'), 'pause extras stay hidden on retry');
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, retryStops[1], 'retry Tab moves to next dialog control');
  assert.notEqual(b.document.activeElement, headerSound);

  // Playing screen: Tab is not trapped (board/chrome keep native order).
  b.render('playing', {cells: cellsState});
  const cell = b.cells()[0];
  cell.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, cell, 'playing leaves Tab alone (no preventDefault cycle)');
});

test('help Tab cycles help controls and does not escape to chrome', () => {
  const b = browserHarness();
  const screenOf = (name) => walk(b.app).find(n => n.dataset && n.dataset.screen === name);
  const btnIn = (screen, text) => walk(screen).find(n => n.tagName === 'BUTTON' && n.textContent === text);
  const headerSound = walk(b.app).find(n => n.tagName === 'BUTTON' && n.getAttribute('aria-label') === 'BGMのオン・オフ');

  // ready → help: entry 戻る (#43); single-stop Tab stays on 戻る (no escape to ♪).
  b.render('ready', {cells: []});
  const helpBtn = walk(b.app).find(n => n.tagName === 'BUTTON' && n.getAttribute('aria-label') === '遊び方');
  helpBtn.focus();
  b.render('help', {cells: []});
  const helpScreen = screenOf('help');
  const helpBack = btnIn(helpScreen, '戻る');
  assert.equal(b.document.activeElement, helpBack, 'help entry still focuses 戻る (#43)');
  assert.ok(String(helpBack.className).includes('nr-primary'));

  const helpStops = [];
  (function visit(node) {
    if (!node || node.hidden) return;
    if (node.tagName === 'BUTTON' && !node.disabled) helpStops.push(node);
    for (const child of node.children || []) visit(child);
  })(helpScreen);
  assert.equal(helpStops.length, 1, 'help exposes a single tab stop (戻る)');
  assert.equal(helpStops[0], helpBack);
  assert.ok(!helpStops.includes(headerSound), 'header BGM is outside the trap');

  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, helpBack, 'help Tab stays on 戻る');
  assert.notEqual(b.document.activeElement, headerSound, 'Tab must not escape to ♪ chrome');

  helpBack.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: true});
  assert.equal(b.document.activeElement, helpBack, 'Shift+Tab also stays on 戻る');

  // Focus already on chrome: Tab pulls back into help instead of leaving.
  headerSound.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, helpBack, 'Tab from chrome re-enters help');

  // Esc on help dismisses via 「戻る」/back (parity shiritori help Esc / #16).
  // Tab trap (#47) and entry focus (#43) stay intact above.
  const beforeEsc = b.queue().length;
  b.app.emit('keydown', {key: 'Escape'});
  assert.equal(b.queue().length, beforeEsc + 1, 'Esc on help queues back');
  assert.equal(b.queue().at(-1).action, 'back', 'Esc dismisses help like 戻る');
  assert.equal(b.document.activeElement, helpBack, 'Esc does not steal help entry focus');

  // Confirm trap still works after help (#45 regression guard).
  b.render('playing', {cells: Array.from({length: 40}, (_, i) => ({n: i + 1, owner: null}))});
  b.render('confirm', {confirm_action: 'pause', cells: []});
  const resume = btnIn(screenOf('confirm'), 'プレイを続ける');
  assert.equal(b.document.activeElement, resume, 'pause entry still focuses resume');
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.notEqual(b.document.activeElement, headerSound, 'confirm Tab still trapped after help');
});

test('finished/review Tab cycles result controls and does not escape to chrome', () => {
  const b = browserHarness();
  const screenOf = (name) => walk(b.app).find(n => n.dataset && n.dataset.screen === name);
  const btnIn = (screen, text) => walk(screen).find(n => n.tagName === 'BUTTON' && n.textContent === text);
  const headerSound = walk(b.app).find(n => n.tagName === 'BUTTON' && n.getAttribute('aria-label') === 'BGMのオン・オフ');
  const collectStops = (root) => {
    const stops = [];
    (function visit(node) {
      if (!node || node.hidden) return;
      if (node.tagName === 'BUTTON' && !node.disabled) stops.push(node);
      for (const child of node.children || []) visit(child);
    })(root);
    return stops;
  };

  // Battle result: entry replay (#17); Tab cycles retry/title/review only; never ♪.
  b.render('playing');
  b.render('finished', {kind: 'battle', perfect: true, bonus: 1000, won: true});
  const finishedScreen = screenOf('finished');
  const retry = btnIn(finishedScreen, 'もう一度遊ぶ');
  const title = btnIn(finishedScreen, 'モード選択');
  const reviewBtn = btnIn(finishedScreen, '対戦を振り返る');
  assert.equal(b.document.activeElement, retry, 'result entry still focuses primary replay (#17)');
  assert.equal(reviewBtn.hidden, false, 'battle review remains reachable');

  const finishedStops = collectStops(finishedScreen);
  assert.deepEqual(finishedStops, [retry, title, reviewBtn], 'finished exposes retry/title/review');
  assert.ok(!finishedStops.includes(headerSound), 'header BGM is outside the trap');

  for (let i = 0; i < finishedStops.length; i++) {
    const expected = finishedStops[(i + 1) % finishedStops.length];
    b.app.emit('keydown', {key: 'Tab', shiftKey: false});
    assert.equal(b.document.activeElement, expected, `finished Tab step ${i + 1} stays in result`);
    assert.notEqual(b.document.activeElement, headerSound, 'Tab must not escape to ♪ chrome');
  }
  retry.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: true});
  assert.equal(b.document.activeElement, finishedStops[finishedStops.length - 1], 'Shift+Tab wraps inside finished');

  // Focus already on chrome: Tab pulls back onto replay (first stop).
  headerSound.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, retry, 'Tab from chrome re-enters finished on replay');

  // #17 Enter/Space retry still works when focus is not on a visible button.
  const heading = walk(finishedScreen).find(n => n.tagName === 'H1');
  heading.focus();
  const beforeEnter = b.queue().length;
  b.app.emit('keydown', {key: 'Enter', repeat: false});
  assert.equal(b.queue().at(-1).action, 'retry', 'Enter still retries from non-button focus (#17)');
  assert.equal(b.queue().length, beforeEnter + 1);
  title.focus();
  const afterTitle = b.queue().length;
  b.app.emit('keydown', {key: ' ', repeat: false});
  assert.equal(b.queue().length, afterTitle, 'title button keeps native Space activation');

  // Review: single 結果へ戻る stop; Tab/Shift+Tab stay put; chrome reclaim.
  reviewBtn.emit('click');
  assert.equal(b.queue().at(-1).action, 'review');
  b.render('review', {kind: 'battle', history: [{number: 1, owner: 'you', seconds: 1.25}]});
  const reviewScreen = screenOf('review');
  const back = btnIn(reviewScreen, '結果へ戻る');
  assert.ok(back);
  assert.ok(String(back.className).includes('nr-primary'));
  // Explicit review entry focus (#49 / #43 parity) — no manual pin required.
  assert.equal(b.document.activeElement, back, 'review entry focuses 結果へ戻る');
  const reviewStops = collectStops(reviewScreen);
  assert.equal(reviewStops.length, 1, 'review exposes a single tab stop (結果へ戻る)');
  assert.equal(reviewStops[0], back);
  assert.ok(!reviewStops.includes(headerSound), 'header BGM is outside review trap');

  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, back, 'review Tab stays on 結果へ戻る');
  assert.notEqual(b.document.activeElement, headerSound, 'review Tab must not escape to ♪ chrome');
  back.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: true});
  assert.equal(b.document.activeElement, back, 'review Shift+Tab also stays on 結果へ戻る');

  headerSound.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, back, 'Tab from chrome re-enters review');

  // Practice finished hides review; Tab still cycles remaining result actions only.
  b.render('finished', {kind: 'practice', perfect: false, won: true});
  const practiceScreen = screenOf('finished');
  const practiceRetry = btnIn(practiceScreen, 'もう一度遊ぶ');
  const practiceTitle = btnIn(practiceScreen, 'モード選択');
  const practiceReview = btnIn(practiceScreen, '対戦を振り返る');
  assert.equal(b.document.activeElement, practiceRetry, 'practice result still focuses replay (#17)');
  assert.equal(practiceReview.hidden, true, 'practice hides review action');
  const practiceStops = collectStops(practiceScreen);
  assert.deepEqual(practiceStops, [practiceRetry, practiceTitle], 'practice finished omits hidden review');
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, practiceTitle, 'practice Tab moves to モード選択');
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, practiceRetry, 'practice Tab wraps to replay');
  assert.notEqual(b.document.activeElement, headerSound);

  // Playing leaves Tab alone (no finished trap bleed).
  b.render('playing', {cells: Array.from({length: 40}, (_, i) => ({n: i + 1, owner: null}))});
  const cell = b.cells()[0];
  cell.focus();
  b.app.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(b.document.activeElement, cell, 'playing leaves Tab alone after finished trap');
});

test('shiritori overlay Tab reclaim wiring keeps chrome parity with confirm trap', () => {
  const js = fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8');
  const sh = fs.readFileSync(require.resolve('../shiritori-ui.js'), 'utf8');
  assert.match(sh, /function trapOverlayTab/);
  assert.match(sh, /activeOverlayRoot/);
  assert.match(sh, /function resultTabStops/);
  assert.match(js, /state\?\.screen === 'shiritori' && event\.key === 'Tab'/);
  assert.match(js, /trapOverlayTab\?\.\(event\)/);
});

test('Escape toggles pause confirm and dismisses retry/title without quitting', () => {
  const b = browserHarness();
  b.render('playing');
  b.app.emit('keydown', {key: 'Escape'});
  assert.equal(b.queue().at(-1).action, 'pause');
  const afterPause = b.queue().length;

  b.render('confirm', {confirm_action: 'pause', cells: []});
  b.app.emit('keydown', {key: 'Escape'});
  assert.equal(b.queue().length, afterPause + 1);
  assert.equal(b.queue().at(-1).action, 'yes', 'pause confirm Esc resumes via yes');

  b.render('confirm', {confirm_action: 'retry', cells: []});
  b.app.emit('keydown', {key: 'Escape'});
  assert.equal(b.queue().at(-1).action, 'no', 'retry confirm Esc cancels instead of accepting');

  b.render('confirm', {confirm_action: 'title', cells: []});
  b.app.emit('keydown', {key: 'Escape'});
  assert.equal(b.queue().at(-1).action, 'no', 'title confirm Esc cancels instead of accepting');

  // Help Esc dismisses via back (parity shiritori help / confirm Esc family).
  b.render('help', {cells: []});
  const beforeHelp = b.queue().length;
  b.app.emit('keydown', {key: 'Escape'});
  assert.equal(b.queue().length, beforeHelp + 1, 'Esc on help queues one command');
  assert.equal(b.queue().at(-1).action, 'back', 'help Esc uses back like 戻る');

  const beforeSafe = b.queue().length;
  for (const screen of ['home', 'ready', 'finished', 'review', 'countdown', 'resuming']) {
    b.render(screen, screen === 'finished' || screen === 'review' ? {} : {cells: []});
    b.app.emit('keydown', {key: 'Escape'});
    assert.equal(b.queue().length, beforeSafe, `Esc stays inert on ${screen}`);
  }
});

test('play scroll lock helpers cover numbers and shiritori live phases only', () => {
  assert.equal(shouldLockPlayScroll('playing'), true);
  assert.equal(shouldLockPlayScroll('shiritori', 'playing'), true);
  assert.equal(shouldLockPlayScroll('shiritori', 'blocked'), true);
  assert.equal(shouldLockPlayScroll('shiritori', 'intro'), false);
  assert.equal(shouldLockPlayScroll('ready'), false);
  assert.equal(shouldLockPlayScroll('confirm'), false);
  assert.equal(shouldLockPlayScroll('finished'), false);
  assert.equal(isPlayScrollAllowed({closest: sel => sel.includes('.nr-history') ? {} : null}), true);
  assert.equal(isPlayScrollAllowed({closest: () => null}), false);
  assert.equal(isPlayScrollAllowed(null), false);
});

test('playing locks document scroll and unlocks on pause/result; reading panes stay allowlisted', () => {
  const b = browserHarness();
  b.render('ready');
  assert.equal(b.app.dataset.scrollLock, 'false');
  assert.equal(b.root.dataset.scrollLock, 'false');
  // Harness window.parent !== window → host owns device insets (no iframe re-stack).
  assert.equal(b.root.getAttribute('data-host-insets'), 'true');
  b.render('playing');
  assert.equal(b.app.dataset.scrollLock, 'true');
  assert.equal(b.root.dataset.scrollLock, 'true');
  assert.ok(b.posts.some(p => p.data?.type === 'number-rush-scroll-lock' && p.data.locked === true));
  let prevented = false;
  b.document.emit('touchmove', {
    target: b.cells()[0],
    preventDefault() { prevented = true; },
  });
  assert.equal(prevented, true, 'board touchmove is blocked while playing');
  prevented = false;
  b.document.emit('touchmove', {
    target: {closest: sel => sel.includes('.nr-history') ? {} : null},
    preventDefault() { prevented = true; },
  });
  assert.equal(prevented, false, 'history pane may still scroll');
  b.render('confirm');
  assert.equal(b.app.dataset.scrollLock, 'false');
  b.render('shiritori', {shiritori: {phase: 'playing'}});
  assert.equal(b.app.dataset.scrollLock, 'true');
  b.render('finished');
  assert.equal(b.app.dataset.scrollLock, 'false');
});


test('settings toggles show pressed chrome (parity with segment/range)', () => {
  const css = fs.readFileSync(require('path').join(__dirname, '..', 'modern-ui.css'), 'utf8');
  // Base pressed affordance for 効果音/演出 (.nr-setting) and BGM ♪ (.nr-icon-button).
  assert.match(css, /\.nr-setting\[aria-pressed='true'\],[\s\S]*?\.nr-icon-button\[aria-pressed='true'\][\s\S]*?border-color: var\(--nr-gold\)/);
  // Contrast + forced-colors keep the selected state readable when gold wash remaps.
  assert.match(css, /@media \(prefers-contrast: more\) \{[\s\S]*?\.nr-setting\[aria-pressed='true'\],[\s\S]*?\.nr-icon-button\[aria-pressed='true'\][\s\S]*?border: 2px solid #c9a227/);
  assert.match(css, /forced-colors LAST[\s\S]*@media \(forced-colors: active\) \{[\s\S]*?\.nr-setting\[aria-pressed='true'\],[\s\S]*?\.nr-icon-button\[aria-pressed='true'\][\s\S]*?border: 2px solid Highlight/);
  // JS still wires aria-pressed on these toggles (chrome depends on it).
  const js = fs.readFileSync(require('path').join(__dirname, '..', 'modern-ui.js'), 'utf8');
  assert.match(js, /sound\.setAttribute\('aria-pressed'/);
  assert.match(js, /sfx\.setAttribute\('aria-pressed'/);
  assert.match(js, /motion\.setAttribute\('aria-pressed'/);
});

test('settings toast CSS pulses on show and stays static under reduced-motion', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  assert.match(css, /\.nr-settings-toast\[data-show='true'\]\[data-pulse='0'\]/);
  assert.match(css, /\.nr-settings-toast\[data-show='true'\]\[data-pulse='1'\]/);
  assert.match(css, /@keyframes nr-settings-toast-a/);
  assert.match(css, /@keyframes nr-settings-toast-b/);
  assert.match(css, /@media \(prefers-reduced-motion: reduce\) \{[\s\S]*?\.nr-settings-toast\[data-show='true'\][\s\S]*?animation: none !important/);
  assert.match(css, /#modern-app\[data-reduced='true'\] \.nr-settings-toast\[data-show='true'\][\s\S]*?animation: none !important/);
  assert.match(css, /forced-colors LAST[\s\S]*?@media \(forced-colors: active\) \{[\s\S]*?\.nr-settings-toast/);
});

test('toggling BGM/SFX/motion shows persistence confirm toast; animationend dismisses', () => {
  const b = browserHarness();
  b.render('ready', {bgm: true, sfx: true, reduced: false, storage_saved: true});
  const toast = walk(b.app).find(n => n.className === 'nr-settings-toast');
  assert.ok(toast, 'settings toast node mounted');
  assert.equal(toast.hidden, true);
  assert.equal(toast.textContent, '');

  b.render('ready', {bgm: false, sfx: true, reduced: false, storage_saved: true});
  assert.equal(toast.hidden, false);
  assert.equal(toast.dataset.show, 'true');
  assert.match(toast.textContent, /BGM OFF · 保存しました/);
  const pulseAfterBgm = toast.dataset.pulse;

  b.render('ready', {bgm: false, sfx: false, reduced: false, storage_saved: true});
  assert.match(toast.textContent, /効果音 OFF · 保存しました/);
  assert.notEqual(toast.dataset.pulse, pulseAfterBgm, 'pulse flips to restart CSS animation');

  b.render('ready', {bgm: false, sfx: false, reduced: true, storage_saved: true});
  assert.match(toast.textContent, /演出 ひかえめ · 保存しました/);

  b.render('ready', {bgm: false, sfx: false, reduced: true, storage_saved: false});
  // No prefs change → toast text unchanged (still prior message) until screen change clears.
  assert.match(toast.textContent, /演出 ひかえめ · 保存しました/);

  // Failed save on next toggle:
  b.render('ready', {bgm: true, sfx: false, reduced: true, storage_saved: false});
  assert.match(toast.textContent, /BGM ON · 保存できませんでした/);

  toast.emit('animationend', {target: toast});
  assert.equal(toast.hidden, true);
  assert.equal(toast.dataset.show, 'false');
  assert.equal(toast.textContent, '');
});

test('settings toast clears on screen change when reduced motion has no animationend', () => {
  const b = browserHarness();
  b.render('ready', {bgm: true, sfx: true, reduced: true, storage_saved: true});
  const toast = walk(b.app).find(n => n.className === 'nr-settings-toast');
  b.render('ready', {bgm: false, sfx: true, reduced: true, storage_saved: true});
  assert.match(toast.textContent, /BGM OFF · 保存しました/);
  b.render('home', {bgm: false, sfx: true, reduced: true, storage_saved: true, cells: []});
  assert.equal(toast.hidden, true);
  assert.equal(toast.textContent, '');
});

test('settings toast wiring lives in modern-ui.js with animationend dismiss', () => {
  const js = fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8');
  assert.match(js, /showSettingsToast/);
  assert.match(js, /hideSettingsToast/);
  assert.match(js, /nr-settings-toast/);
  assert.match(js, /animationend/);
  assert.match(js, /prevPrefs/);
});


test('numbers HUD target cue CSS pulses on change and stays static under reduced-motion', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  assert.match(css, /\.nr-target\[data-cue='true'\]\[data-pulse='0'\]/);
  assert.match(css, /\.nr-target\[data-cue='true'\]\[data-pulse='1'\]/);
  assert.match(css, /@keyframes nr-target-cue-a/);
  assert.match(css, /@keyframes nr-target-cue-b/);
  assert.match(css, /@media \(prefers-reduced-motion: reduce\) \{[\s\S]*?\.nr-target\[data-cue='true'\][\s\S]*?animation: none !important/);
  assert.match(css, /#modern-app\[data-reduced='true'\] \.nr-target\[data-cue='true'\][\s\S]*?animation: none !important/);
  assert.match(css, /@media \(prefers-contrast: more\) \{[\s\S]*?\.nr-target\[data-cue='true'\]/);
  assert.match(css, /forced-colors LAST[\s\S]*?@media \(forced-colors: active\) \{[\s\S]*?\.nr-target\[data-cue='true'\]/);
});

test('numbers HUD flashes cue when お題 changes; animationend clears; leave play clears', () => {
  const b = browserHarness();
  b.render('ready', {target: 1, cells: []});
  const wrap = walk(b.app).find(n => n.className === 'nr-target');
  assert.ok(wrap, 'nr-target mounted');
  assert.equal(wrap.dataset.cue, 'false');

  b.render('playing', {target: 1});
  assert.equal(wrap.dataset.cue, 'true', 'entering play cues initial お題');
  const pulseEnter = wrap.dataset.pulse;
  const number = walk(wrap).find(n => n.className === 'nr-target-number');
  assert.equal(number.textContent, '1');

  // Same target re-render: no pulse flip / stay cued until animationend.
  b.render('playing', {target: 1, completed: 0});
  assert.equal(wrap.dataset.pulse, pulseEnter, 'identical お題 does not restart pulse');

  wrap.emit('animationend', {target: wrap});
  assert.equal(wrap.dataset.cue, 'false');

  b.render('playing', {target: 2, completed: 1});
  assert.equal(wrap.dataset.cue, 'true', 'お題 change re-cues');
  assert.equal(number.textContent, '2');
  assert.notEqual(wrap.dataset.pulse, pulseEnter, 'pulse flips to restart CSS animation');
  const pulseChange = wrap.dataset.pulse;

  b.render('playing', {target: 5, completed: 2});
  assert.equal(wrap.dataset.cue, 'true');
  assert.equal(number.textContent, '5');
  assert.notEqual(wrap.dataset.pulse, pulseChange);

  b.render('confirm', {target: 5, cells: []});
  assert.equal(wrap.dataset.cue, 'false', 'leaving play clears cue');
});

test('numbers HUD reduced-motion keeps static cue until next お題 or leave play', () => {
  const b = browserHarness();
  b.render('playing', {target: 3, reduced: true});
  const wrap = walk(b.app).find(n => n.className === 'nr-target');
  assert.equal(wrap.dataset.cue, 'true');
  // No animationend under reduced — cue stays until next change.
  b.render('playing', {target: 3, reduced: true, completed: 0});
  assert.equal(wrap.dataset.cue, 'true');
  b.render('playing', {target: 7, reduced: true, completed: 1});
  assert.equal(wrap.dataset.cue, 'true');
  assert.equal(walk(wrap).find(n => n.className === 'nr-target-number').textContent, '7');
  b.render('finished', {target: null, reduced: true});
  assert.equal(wrap.dataset.cue, 'false');
});

test('numbers HUD target cue wiring lives in modern-ui.js with animationend dismiss', () => {
  const js = fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8');
  assert.match(js, /flashTargetCue/);
  assert.match(js, /clearTargetCue/);
  assert.match(js, /prevTargetKey/);
  assert.match(js, /dataset\.cue/);
  assert.match(js, /targetWrap\.addEventListener\('animationend'/);
  assert.doesNotMatch(js, /setTimeout|setInterval|innerHTML|fetch\(/);
});


test('numbers YOU score-card cue CSS pulses on increment and stays static under reduced-motion', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  assert.match(css, /\.nr-score-card\.nr-you\[data-cue='true'\]\[data-pulse='0'\]/);
  assert.match(css, /\.nr-score-card\.nr-you\[data-cue='true'\]\[data-pulse='1'\]/);
  assert.match(css, /@keyframes nr-you-score-cue-a/);
  assert.match(css, /@keyframes nr-you-score-cue-b/);
  assert.match(css, /@media \(prefers-reduced-motion: reduce\) \{[\s\S]*?\.nr-score-card\.nr-you\[data-cue='true'\][\s\S]*?animation: none !important/);
  assert.match(css, /#modern-app\[data-reduced='true'\] \.nr-score-card\.nr-you\[data-cue='true'\][\s\S]*?animation: none !important/);
  assert.match(css, /@media \(prefers-contrast: more\) \{[\s\S]*?\.nr-score-card\.nr-you\[data-cue='true'\]/);
  assert.match(css, /forced-colors LAST[\s\S]*?@media \(forced-colors: active\) \{[\s\S]*?\.nr-score-card\.nr-you\[data-cue='true'\]/);
  assert.equal(css.indexOf('@media (prefers-contrast: more)'), css.lastIndexOf('@media (prefers-contrast: more)'));
});

test('numbers YOU score-card cues when completed/points increment; animationend clears; leave play clears', () => {
  const b = browserHarness();
  b.render('ready', {completed: 0, player_points: 0, cells: []});
  const you = walk(b.app).find(n => String(n.className).includes('nr-score-card') && String(n.className).includes('nr-you'));
  assert.ok(you, 'YOU score-card mounted');
  assert.equal(you.dataset.cue, 'false');

  b.render('playing', {kind: 'practice', completed: 0, player_points: 0});
  assert.equal(you.dataset.cue, 'false', 'enter play at 0 does not cue');
  const score = walk(you).find(n => n.tagName === 'STRONG');
  assert.equal(score.textContent, '0');

  b.render('playing', {kind: 'practice', completed: 1, player_points: 0});
  assert.equal(you.dataset.cue, 'true', 'completed increment cues');
  assert.equal(score.textContent, '1');
  const pulse1 = you.dataset.pulse;

  b.render('playing', {kind: 'practice', completed: 1, player_points: 0});
  assert.equal(you.dataset.pulse, pulse1, 'identical score does not restart pulse');

  you.emit('animationend', {target: you});
  assert.equal(you.dataset.cue, 'false');

  b.render('playing', {kind: 'practice', completed: 3, player_points: 0});
  assert.equal(you.dataset.cue, 'true');
  assert.notEqual(you.dataset.pulse, pulse1, 'pulse flips to restart CSS animation');
  assert.equal(score.textContent, '3');

  b.render('confirm', {kind: 'practice', cells: []});
  assert.equal(you.dataset.cue, 'false', 'leaving play clears cue');

  b.render('playing', {kind: 'battle', completed: 0, player_points: 0});
  assert.equal(you.dataset.cue, 'false', 'battle enter at 0 does not cue');
  b.render('playing', {kind: 'battle', completed: 1, player_points: 2});
  assert.equal(you.dataset.cue, 'true', 'battle player_points increment cues');
  assert.equal(score.textContent, '2');

  b.render('finished', {kind: 'battle', player_points: 2});
  assert.equal(you.dataset.cue, 'false', 'finished clears cue');
});

test('numbers YOU score-card reduced-motion keeps static cue until next increment or leave play', () => {
  const b = browserHarness();
  b.render('playing', {kind: 'practice', completed: 0, reduced: true});
  const you = walk(b.app).find(n => String(n.className).includes('nr-score-card') && String(n.className).includes('nr-you'));
  assert.equal(you.dataset.cue, 'false');
  b.render('playing', {kind: 'practice', completed: 2, reduced: true});
  assert.equal(you.dataset.cue, 'true');
  b.render('playing', {kind: 'practice', completed: 2, reduced: true});
  assert.equal(you.dataset.cue, 'true');
  b.render('playing', {kind: 'practice', completed: 4, reduced: true});
  assert.equal(you.dataset.cue, 'true');
  b.render('finished', {kind: 'practice', completed: 4, reduced: true});
  assert.equal(you.dataset.cue, 'false');
});

test('numbers YOU score-card cue wiring lives in modern-ui.js with animationend dismiss', () => {
  const js = fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8');
  assert.match(js, /flashYouScoreCue/);
  assert.match(js, /clearYouScoreCue/);
  assert.match(js, /prevYouScoreKey/);
  assert.match(js, /youHud\.dataset\.cue/);
  assert.match(js, /youHud\.addEventListener\('animationend'/);
  assert.doesNotMatch(js, /setTimeout|setInterval|innerHTML|fetch\(/);
});


test('practice hint uses dedicated nr-hint affordance (not muted nr-setting)', () => {
  const js = fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8');
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  assert.match(js, /button\('ヒントを見る', 'hint', undefined, 'nr-hint'\)/);
  assert.ok(!/button\('ヒントを見る', 'hint', undefined, 'nr-setting'\)/.test(js));
  assert.match(js, /hint\.dataset\.used/);
  assert.match(js, /使うとベスト記録対象外/);
  assert.match(css, /\.nr-hint \{/);
  assert.match(css, /\.nr-hint\[data-used='true'\]/);
  assert.match(css, /\.nr-stage-middle > \.nr-hint \{ min-height: 44px/);
  // Short desktop must not shrink below a readable 36px / 11px chip.
  assert.match(css, /\.nr-stage-middle > \.nr-hint \{ position: absolute;[\s\S]*?min-height: 36px;[\s\S]*?font-size: 11px !important/);
  assert.ok(!/\.nr-stage-middle > \.nr-setting \{/.test(css));
  assert.match(css, /@media \(prefers-contrast: more\) \{[\s\S]*?#modern-app \.nr-hint/);
  assert.match(css, /forced-colors LAST[\s\S]*?#modern-app \.nr-hint/);
  assert.match(player, /modern-ui\.css\?v=settings-pressed-103-1/);
  assert.match(player, /modern-ui\.js\?v=miss-live-guidance-98-1/);
  assert.match(player, /mobile-layout\.css\?v=practice-chains-104-1/);
});

test('practice play shows mint hint control; battle hides it; used state updates aria', () => {
  const b = browserHarness();
  b.render('playing', {kind: 'practice', hint_used: false});
  const hint = walk(b.app).find(n =>
    n.tagName === 'BUTTON' && String(n.className).includes('nr-hint'));
  assert.ok(hint, 'nr-hint button mounted');
  assert.equal(hint.hidden, false, 'practice shows hint');
  assert.equal(hint.dataset.used, 'false');
  assert.equal(hint.textContent, 'ヒントを見る');
  assert.match(hint.getAttribute('aria-label') || '', /使うとベスト記録対象外/);
  assert.ok(!String(hint.className).includes('nr-setting'), 'hint is not muted settings chrome');

  b.render('playing', {kind: 'practice', hint_used: true, hint_index: 3});
  assert.equal(hint.dataset.used, 'true');
  assert.equal(hint.textContent, 'ヒント（記録対象外）');
  assert.match(hint.getAttribute('aria-label') || '', /ヒント使用済み/);

  b.render('playing', {kind: 'battle', hint_used: false, player_points: 0, cpu_points: 0});
  assert.equal(hint.hidden, true, 'battle hides practice hint');
});


test('result screen primary score outweighs secondary stats (hierarchy #73)', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  // Primary: larger gold score with weight + tabular nums.
  assert.match(css, /\.nr-result-score \{[^}]*font-size: 52px;[^}]*font-weight: 850/);
  assert.match(css, /\.nr-result-score \{[^}]*font-variant-numeric: tabular-nums/);
  // Secondary: muted / smaller than play HUD defaults when inside result stats.
  assert.match(css, /\.nr-result-stats \.nr-stat > strong \{[^}]*font-size: 14px;[^}]*color: var\(--nr-muted\)/);
  assert.match(player, /modern-ui\.css\?v=settings-pressed-103-1/);
  assert.match(player, /mobile-layout\.css\?v=practice-chains-104-1/);
});

test('finished result still focuses primary replay after score hierarchy (#17)', () => {
  const b = browserHarness();
  b.render('playing', {kind: 'battle', player_points: 12, cpu_points: 5});
  b.render('finished', {
    kind: 'battle', won: true, perfect: false,
    player_points: 12, cpu_points: 5, completed: 12, max_number: 25,
    elapsed: 42, mistakes: 1, max_streak: 4,
  });
  const score = walk(b.app).find(n => n.tagName === 'STRONG' && String(n.className).includes('nr-result-score'));
  assert.ok(score, 'result primary score present');
  assert.match(score.textContent, /12\s*:\s*5/);
  const retry = walk(b.app).find(n => n.tagName === 'BUTTON' && n.textContent === 'もう一度遊ぶ');
  assert.ok(retry, 'replay button present');
  assert.equal(b.document.activeElement, retry, 'result entry focuses primary replay (#17)');
});


test('result award/record contrast: dark PERFECT panel + new-best pill (#74)', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const mobile = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  // Award: dark gold panel + cream label (reads above primary score gold).
  assert.match(css, /\.nr-award \{[\s\S]*?background: linear-gradient\(145deg, #3a2a12f5, #16100af8\)/);
  assert.match(css, /\.nr-award > span \{[\s\S]*?color: #fff8e7/);
  assert.match(css, /\.nr-award > strong \{[\s\S]*?color: #ffe7a8/);
  // Record: muted by default; new-best is a high-contrast pill.
  assert.match(css, /\.nr-record \{[^}]*color: var\(--nr-muted\)/);
  assert.match(css, /\.nr-record\[data-record='new'\] \{[\s\S]*?border-radius: 999px/);
  assert.match(css, /\.nr-record\[data-record='new'\] \{[\s\S]*?color: #fff8e7/);
  // Contrast / forced-colors keep award + new-record readable.
  const contrastIdx = css.indexOf('@media (prefers-contrast: more)');
  assert.match(css.slice(contrastIdx), /prefers-contrast: more[\s\S]*?\.nr-award \{[\s\S]*?border: 2px solid #c9a227/);
  assert.match(css.slice(contrastIdx), /prefers-contrast: more[\s\S]*?\.nr-record\[data-record='new'\]/);
  const forcedIdx = css.indexOf('@media (forced-colors: active)');
  assert.match(css.slice(forcedIdx), /forced-colors: active[\s\S]*?\.nr-award \{[\s\S]*?border: 2px solid Highlight/);
  assert.match(css.slice(forcedIdx), /forced-colors: active[\s\S]*?\.nr-record\[data-record='new'\]/);
  assert.match(mobile, /\.nr-result-card \.nr-record\[data-record='new'\]/);
  assert.match(player, /modern-ui\.css\?v=settings-pressed-103-1/);
  assert.match(player, /modern-ui\.js\?v=miss-live-guidance-98-1/);
  assert.match(player, /mobile-layout\.css\?v=practice-chains-104-1/);
});

test('finished result sets record data-record kinds for contrast styling', () => {
  const b = browserHarness();
  const recordOf = () => walk(b.app).find(n => n.className === 'nr-record');
  const awardOf = () => walk(b.app).find(n => n.className === 'nr-award');

  b.render('finished', {
    kind: 'battle', won: true, perfect: true, bonus: 1500, is_new_best: true,
    player_points: 15, cpu_points: 4, completed: 15, max_number: 20,
    elapsed: 30, mistakes: 0, max_streak: 15, storage_saved: true,
  });
  assert.equal(awardOf().hidden, false, 'PERFECT award visible');
  assert.ok(walk(awardOf()).some(n => /PERFECT BONUS/.test(n.textContent || '')), 'PERFECT label present');
  assert.ok(walk(awardOf()).some(n => /\+\s*1[,.]?500\s*pt/.test(n.textContent || '')), 'bonus value present');
  assert.equal(recordOf().dataset.record, 'new');
  assert.match(recordOf().textContent, /自己ベスト更新/);

  b.render('finished', {
    kind: 'battle', won: true, perfect: false, is_new_best: false, best_points: 12,
    player_points: 10, cpu_points: 8, completed: 10, max_number: 20,
    elapsed: 40, mistakes: 2, max_streak: 5, storage_saved: true,
  });
  assert.equal(awardOf().hidden, true);
  assert.equal(recordOf().dataset.record, 'best');
  assert.match(recordOf().textContent, /自己ベスト 12/);

  b.render('finished', {
    kind: 'practice', perfect: false, hint_used: true, is_new_best: false,
    completed: 20, max_number: 20, elapsed: 55, mistakes: 1, max_streak: 8,
    storage_saved: true,
  });
  assert.equal(recordOf().dataset.record, 'hint');
  assert.match(recordOf().textContent, /ヒント使用/);

  b.render('finished', {
    kind: 'practice', perfect: false, is_new_best: false, storage_saved: false,
    completed: 10, max_number: 20, elapsed: 20, mistakes: 0, max_streak: 3,
  });
  assert.equal(recordOf().dataset.record, 'warn');
  assert.match(recordOf().textContent, /保存できませんでした/);

  // New best + storage fail keeps celebratory 'new' kind (message still appended).
  b.render('finished', {
    kind: 'battle', won: true, perfect: false, is_new_best: true, storage_saved: false,
    player_points: 18, cpu_points: 3, completed: 18, max_number: 20,
    elapsed: 25, mistakes: 0, max_streak: 10,
  });
  assert.equal(recordOf().dataset.record, 'new');
  assert.match(recordOf().textContent, /自己ベスト更新/);
  assert.match(recordOf().textContent, /保存できませんでした/);
});

test('finished result still focuses primary replay after award/record contrast (#17)', () => {
  const b = browserHarness();
  b.render('playing', {kind: 'battle', player_points: 12, cpu_points: 5});
  b.render('finished', {
    kind: 'battle', won: true, perfect: true, bonus: 1000, is_new_best: true,
    player_points: 12, cpu_points: 5, completed: 12, max_number: 20,
    elapsed: 42, mistakes: 0, max_streak: 12, storage_saved: true,
  });
  const retry = walk(b.app).find(n => n.tagName === 'BUTTON' && n.textContent === 'もう一度遊ぶ');
  assert.equal(b.document.activeElement, retry, 'result entry focuses primary replay (#17)');
});

test('practice ready solo hero-cast denser/centered after LUNA+VS hide (shared #89)', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const mobile = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  // Shared ready hero-cast densify (parity result #82; also covers practice after #86).
  assert.match(css, /\.nr-hero-cast:has\(> \.nr-koh\[hidden\]\) \{ gap: 12px; justify-content: center; \}/);
  assert.match(css, /\.nr-hero-cast:has\(> \.nr-koh\[hidden\]\) \.nr-character \{ width: min\(56%, 280px\); \}/);
  assert.match(css, /\.nr-hero-cast:has\(> \.nr-koh\[hidden\]\) \{ gap: 6px; justify-content: center; \}/);
  assert.match(mobile, /\.nr-hero-cast:has\(> \.nr-koh\[hidden\]\) \{ gap: 2px; justify-content: center; \}/);
  // #86 hide still wired.
  assert.match(fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8'),
    /heroKoh\.wrap\.hidden = !battle;\s*heroVersus\.hidden = !battle;/);
  assert.match(player, /modern-ui\.css\?v=settings-pressed-103-1/);
  assert.match(player, /mobile-layout\.css\?v=practice-chains-104-1/);
  assert.match(player, /modern-ui\.js\?v=miss-live-guidance-98-1/);
  assert.match(index, /player\.html\?v=practice-chains-104-1/);

  const b = browserHarness();
  const heroCast = () => walk(b.app).find(n => n.className === 'nr-hero-cast');
  const kohIn = (parent) => parent && parent.children.find(n => String(n.className).includes('nr-koh'));
  const rinIn = (parent) => parent && parent.children.find(n => String(n.className).includes('nr-rin'));
  const versusIn = (parent) => parent && parent.children.find(n => n.className === 'nr-versus');

  b.render('ready', {kind: 'battle', cells: []});
  assert.equal(kohIn(heroCast()).hidden, false, 'battle ready still shows LUNA');
  assert.equal(versusIn(heroCast()).hidden, false, 'battle ready still shows VS');

  b.render('ready', {kind: 'practice', cells: []});
  assert.equal(kohIn(heroCast()).hidden, true, 'practice ready still hides LUNA (#86)');
  assert.equal(versusIn(heroCast()).hidden, true, 'practice ready still hides VS (#86)');
  assert.equal(rinIn(heroCast()).hidden, false, 'practice ready keeps RIN');

  // Leave finished → ready so #50 entry focus runs.
  b.render('finished', {kind: 'practice', perfect: false, won: true, cells: state().cells});
  b.render('ready', {kind: 'practice', cells: []});
  const ready = walk(b.app).find(n => n.dataset.screen === 'ready');
  const ordered = walk(ready).find(n =>
    n.tagName === 'BUTTON' && String(n.className).includes('nr-primary'));
  assert.equal(b.document.activeElement, ordered, 'practice ready still focuses 1から順番 (#50)');
});

test('practice pause copy omits rival/CPU; battle keeps rival stopped (#90)', () => {
  const js = fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8');
  assert.match(js, /タイマーは止まっています。準備ができたら再開しよう。/);
  assert.match(js, /タイマーもライバルも止まっています。準備ができたら再開しよう。/);
  // Kind-aware ternary: battle keeps rival line; practice drops it.
  assert.match(js, /isPause\s*\n\s*\? \(battle\s*\n\s*\? 'タイマーもライバルも止まっています/);
  assert.doesNotMatch(js, /confirmCopy\.textContent = isPause \? 'タイマーもライバルも止まっています/);

  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  assert.match(player, /modern-ui\.js\?v=miss-live-guidance-98-1/);
  assert.match(index, /player\.html\?v=practice-chains-104-1/);

  const b = browserHarness();
  const mutedIn = (screen) => walk(screen).find(n => n.tagName === 'P' && String(n.className).includes('nr-muted'));

  b.render('confirm', {confirm_action: 'pause', kind: 'battle', cells: []});
  const battleConfirm = walk(b.app).find(n => n.dataset?.screen === 'confirm');
  assert.match(mutedIn(battleConfirm).textContent, /ライバルも止まっています/, 'battle pause still mentions rival');

  b.render('confirm', {confirm_action: 'pause', kind: 'practice', cells: []});
  const practiceConfirm = walk(b.app).find(n => n.dataset?.screen === 'confirm');
  const practiceCopy = mutedIn(practiceConfirm).textContent;
  assert.match(practiceCopy, /タイマーは止まっています/, 'practice pause mentions timer only');
  assert.doesNotMatch(practiceCopy, /ライバル/, 'practice pause must not mention rival');
  assert.doesNotMatch(practiceCopy, /CPU/, 'practice pause must not mention CPU');
});

test('practice ready intro-copy omits rival; battle keeps ライバル (#92)', () => {
  const js = fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8');
  assert.match(js, /お題の数字を、自分のペースで見つけよう。/);
  assert.match(js, /お題の数字を、ライバルより先に見つけよう。/);
  // Kind-aware assignment: battle keeps rival line; practice drops it.
  assert.match(js, /introCopy\.textContent = battle\s*\n\s*\? 'お題の数字を、ライバルより先に見つけよう/);
  assert.match(js, /: 'お題の数字を、自分のペースで見つけよう/);

  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  assert.match(player, /modern-ui\.js\?v=miss-live-guidance-98-1/);
  assert.match(index, /player\.html\?v=practice-chains-104-1/);

  const b = browserHarness();
  const introIn = (screen) => walk(screen).find(n => n.tagName === 'P' && String(n.className).includes('nr-intro-copy'));

  b.render('ready', {kind: 'battle', cells: []});
  const battleReady = walk(b.app).find(n => n.dataset?.screen === 'ready');
  assert.match(introIn(battleReady).textContent, /ライバルより先に/, 'battle ready intro still mentions rival');

  b.render('ready', {kind: 'practice', cells: []});
  const practiceReady = walk(b.app).find(n => n.dataset?.screen === 'ready');
  const practiceIntro = introIn(practiceReady).textContent;
  assert.match(practiceIntro, /自分のペースで見つけよう/, 'practice ready intro is pace-focused');
  assert.doesNotMatch(practiceIntro, /ライバル/, 'practice ready intro must not mention rival');
  assert.doesNotMatch(practiceIntro, /対戦/, 'practice ready intro must not sell rivalry');
});

test('practice PERFECT award blurb omits 先取; battle keeps it (#93)', () => {
  const js = fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8');
  assert.match(js, /全問先取・ノーミスの特別賞/);
  assert.match(js, /全問クリア・ノーミスの特別賞/);
  // Kind-aware assignment: battle keeps 先取; practice drops phantom rivalry.
  assert.match(js, /awardBlurb\.textContent = battle\s*\n\s*\? '全問先取・ノーミスの特別賞'/);
  assert.match(js, /: '全問クリア・ノーミスの特別賞'/);

  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  assert.match(player, /modern-ui\.js\?v=miss-live-guidance-98-1/);
  assert.match(index, /player\.html\?v=practice-chains-104-1/);

  const b = browserHarness();
  const awardOf = () => walk(b.app).find(n => n.className === 'nr-award');
  const blurbOf = () => walk(awardOf()).find(n => n.tagName === 'SMALL');

  b.render('finished', {
    kind: 'battle', won: true, perfect: true, bonus: 1000,
    player_points: 10, cpu_points: 0, completed: 10, max_number: 10,
    elapsed: 20, mistakes: 0, max_streak: 10, storage_saved: true,
  });
  assert.equal(awardOf().hidden, false, 'battle PERFECT award visible');
  assert.match(blurbOf().textContent, /全問先取/, 'battle award blurb keeps 先取');
  assert.doesNotMatch(blurbOf().textContent, /クリア/, 'battle award blurb is not practice clear copy');

  b.render('finished', {
    kind: 'practice', perfect: true, bonus: 1000,
    completed: 10, max_number: 10, elapsed: 25, mistakes: 0, max_streak: 10,
    storage_saved: true,
  });
  assert.equal(awardOf().hidden, false, 'practice PERFECT award visible when perfect');
  assert.match(blurbOf().textContent, /全問クリア/, 'practice award blurb is clear-focused');
  assert.doesNotMatch(blurbOf().textContent, /先取/, 'practice award blurb must not say 先取');
  assert.doesNotMatch(blurbOf().textContent, /ライバル|CPU/, 'practice award blurb must not invent a rival');
});

test('practice help pause clause omits CPU; battle keeps it (#94)', () => {
  const js = fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8');
  assert.match(js, /一時停止中はCPUも時計も止まります。/);
  assert.match(js, /一時停止中は時計も止まります。/);
  // Kind-aware assignment: battle keeps CPU; practice drops phantom rival.
  assert.match(js, /helpPracticePause\.textContent = battle\s*\n\s*\? 'ひとりで練習は時間制限なし。ヒントを使うと記録対象外になります。一時停止中はCPUも時計も止まります。'/);
  assert.match(js, /: 'ひとりで練習は時間制限なし。ヒントを使うと記録対象外になります。一時停止中は時計も止まります。'/);
  assert.doesNotMatch(js, /\['練習と休憩も、気軽に', 'ひとりで練習は時間制限なし。ヒントを使うと記録対象外になります。一時停止中はCPUも時計も止まります。'\]/);

  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  assert.match(player, /modern-ui\.js\?v=miss-live-guidance-98-1/);
  assert.match(index, /player\.html\?v=practice-chains-104-1/);

  const b = browserHarness();
  const helpOf = () => walk(b.app).find(n => n.dataset?.screen === 'help');
  const practicePauseP = () => {
    const help = helpOf();
    const items = walk(help).filter(n => n.tagName === 'LI');
    const practiceLi = items.find(li => walk(li).some(n => n.tagName === 'H2' && n.textContent === '練習と休憩も、気軽に'));
    return walk(practiceLi).find(n => n.tagName === 'P');
  };

  b.render('help', {kind: 'battle', cells: []});
  assert.match(practicePauseP().textContent, /一時停止中はCPUも時計も止まります/, 'battle help keeps CPU in pause clause');

  b.render('help', {kind: 'practice', cells: []});
  const practiceCopy = practicePauseP().textContent;
  assert.match(practiceCopy, /一時停止中は時計も止まります/, 'practice help pause mentions clock only');
  assert.doesNotMatch(practiceCopy, /CPU/, 'practice help pause must not invent CPU');
  assert.doesNotMatch(practiceCopy, /ライバル/, 'practice help pause must not invent rival');
});

test('practice help rival bullet uses pace copy; battle keeps rival (#95)', () => {
  const js = fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8');
  assert.match(js, /ライバルより先に見つけよう/);
  assert.match(js, /自分のペースで見つけよう/);
  assert.match(js, /すべての数字を見つけよう。時間制限なしで、自分のペースでクリアを目指します。/);
  // Kind-aware assignment: battle keeps rival heading/body; practice drops phantom rivalry.
  assert.match(js, /helpRivalHeading\.textContent = battle\s*\n\s*\? 'ライバルより先に見つけよう'/);
  assert.match(js, /: '自分のペースで見つけよう'/);
  assert.match(js, /helpRivalBody\.textContent = battle\s*\n\s*\? '青いYOUがあなた、ピンクのCPUがルナ。先に見つけると1点。全体の6割で勝利です。'/);
  assert.match(js, /: '青いYOUがあなた。すべての数字を見つけよう。時間制限なしで、自分のペースでクリアを目指します。'/);
  // Static help list must not hardcode rival-only bullet as the sole practice-visible line.
  assert.doesNotMatch(js, /\['ライバルより先に見つけよう', '青いYOUがあなた、ピンクのCPUがルナ。先に見つけると1点。全体の6割で勝利です。'\]/);

  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  assert.match(player, /modern-ui\.js\?v=miss-live-guidance-98-1/);
  assert.match(index, /player\.html\?v=practice-chains-104-1/);

  const b = browserHarness();
  const helpOf = () => walk(b.app).find(n => n.dataset?.screen === 'help');
  const rivalLi = () => {
    const help = helpOf();
    const items = walk(help).filter(n => n.tagName === 'LI');
    // Second help item is the score/pace bullet (heading swaps by kind).
    return items[1];
  };
  const headingOf = () => walk(rivalLi()).find(n => n.tagName === 'H2');
  const bodyOf = () => walk(rivalLi()).find(n => n.tagName === 'P');

  b.render('help', {kind: 'battle', cells: []});
  assert.match(headingOf().textContent, /ライバルより先に見つけよう/, 'battle help keeps rival heading');
  assert.match(bodyOf().textContent, /ピンクのCPUがルナ/, 'battle help keeps CPU scoring body');
  assert.match(bodyOf().textContent, /6割で勝利/, 'battle help keeps win-line body');

  b.render('help', {kind: 'practice', cells: []});
  assert.match(headingOf().textContent, /自分のペースで見つけよう/, 'practice help heading is pace-focused');
  assert.doesNotMatch(headingOf().textContent, /ライバル/, 'practice help heading must not invent rival');
  const practiceBody = bodyOf().textContent;
  assert.match(practiceBody, /すべての数字を見つけよう/, 'practice help body is find-all');
  assert.match(practiceBody, /自分のペース/, 'practice help body mentions pace');
  assert.doesNotMatch(practiceBody, /ライバル|CPU|6割|先に見つけると1点/, 'practice help body must not invent rivalry/scoring');
});
