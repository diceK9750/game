const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {parseState, formatTime, posePosition, remainingCommands, nextCell, nextPlayable} = require('../modern-ui.js');
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
  assert.match(css, /prefers-reduced-motion/); assert.match(css, /safe-area-inset/);
  assert.match(css, /\.nr-cell-effect[^}]*pointer-events: none/);
  assert.match(css, /assets\/backgrounds\/lantern-forest\.png/);
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
    querySelector() { return walk(this).find(node => node.tagName === 'H1' || node.className === 'nr-target' || (node.tagName === 'BUTTON' && !node.disabled)) || null; }
    focus() { document.activeElement = this; }
  }
  const root = new Element('html'), app = new Element('div'); app.hidden = true; root.append(app);
  document = {documentElement: root, activeElement: root, createElement: tag => new Element(tag), getElementById: id => id === 'modern-app' ? app : null};
  const observers = [];
  const browserWindow = {matchMedia: () => ({matches: false, addEventListener() {}})}; browserWindow.parent = browserWindow;
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
  return {root, app, document, render, notify, cells: () => walk(app).filter(node => node.className === 'nr-cell'),
    queue: () => JSON.parse(root.getAttribute('data-modern-commands') || '[]')};
}
function walk(element) { return element.children.flatMap(child => [child, ...walk(child)]); }

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
