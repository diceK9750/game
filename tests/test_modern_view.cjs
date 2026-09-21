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
  // Shell buttons keep outline focus; cells/cards are excluded so feedback outlines are not clobbered.
  assert.match(css, /#modern-app button:not\(\.nr-cell\):not\(\.sh-card\):focus-visible/);
  assert.match(css, /#modern-app \.nr-cell:focus-visible, #modern-app \.sh-card:focus-visible \{ outline: none; \}/);
  assert.match(css, /#modern-app \.nr-cell:focus-visible::before, #modern-app \.sh-card:focus-visible::before \{[^}]*box-shadow: inset 0 0 0 3px #f9d58a/);
  // Feedback selectors carry #modern-app so they beat focus outline:none when both apply.
  assert.match(css, /#modern-app \.nr-cell\[data-feedback='wrong'\]/);
  assert.match(css, /#modern-app \.nr-cell\[data-feedback='correct'\]/);
  assert.match(css, /#modern-app \.nr-cell\[data-feedback='cpu'\]/);
  assert.match(css, /#modern-app \.nr-cell\[data-cpu-selecting='true'\]/);
  assert.match(css, /#modern-app \.sh-card\[data-cpu-selecting='true'\]/);
  assert.match(css, /#modern-app \.nr-cell\[data-hint='true'\]/);
  // Contrast / forced-colors keep a visible focus ring without reclaiming outline.
  const contrastIdx = css.indexOf('@media (prefers-contrast: more)');
  assert.match(css.slice(contrastIdx), /prefers-contrast: more[\s\S]*?\.sh-card:focus-visible::before[\s\S]*?box-shadow: inset 0 0 0 4px #c9a227/);
  const forcedIdx = css.indexOf('@media (forced-colors: active)');
  assert.match(css.slice(forcedIdx), /forced-colors: active[\s\S]*?\.sh-card:focus-visible::before[\s\S]*?box-shadow: inset 0 0 0 4px Highlight/);
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

  // Esc on help stays inert (#16 family); entry focus path unchanged.
  const beforeEsc = b.queue().length;
  b.app.emit('keydown', {key: 'Escape'});
  assert.equal(b.queue().length, beforeEsc, 'Esc stays inert on help');
  assert.equal(b.document.activeElement, helpBack, 'Esc does not move help focus');

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
  // Entry may land via hidden-focus reclaim; pin focus for trap assertions.
  back.focus();
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

  const beforeSafe = b.queue().length;
  for (const screen of ['home', 'ready', 'help', 'finished', 'review', 'countdown', 'resuming']) {
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
