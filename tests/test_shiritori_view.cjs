const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function harness() {
  const doc = {activeElement: null};
  class Element {
    constructor(tag, cls = '', text = '') {
      this.tagName = tag.toUpperCase(); this.className = cls; this.textContent = text; this.children = [];
      this.style = {}; this.dataset = {}; this.events = {}; this.hidden = false; this.parentElement = null;
    }
    append(...nodes) { for (const n of nodes) { n.parentElement = this; this.children.push(n); } }
    replaceChildren(...nodes) { this.children = []; this.append(...nodes); }
    setAttribute(key, val) { this[key] = val; }
    addEventListener(key, fn) { this.events[key] = fn; }
    emit(key, event = {}) { (this.events[key] || (() => {}))({preventDefault() {}, stopPropagation() {}, ...event}); }
    click() { this.emit('click'); }
    focus() { doc.activeElement = this; }
    contains(el) { return this === el || this.children.some(child => child.contains(el)); }
    closest() { for (let node = this; node; node = node.parentElement) if (node.hidden) return node; return null; }
    querySelectorAll(selector) { const all = this.children.flatMap(n => [n, ...n.querySelectorAll('*')]); return all.filter(n => selector === '*' || selector.split(',').some(s => s.trim().startsWith('.') ? n.className.split(' ').includes(s.trim().slice(1)) : n.tagName === s.trim().toUpperCase())); }
    querySelector(selector) { return this.querySelectorAll(selector)[0]; }
  }
  const E = (tag, cls, text) => new Element(tag, cls, text);
  const add = (parent, ...children) => { parent.append(...children); return parent; };
  const queue = [];
  const command = (action, value) => queue.push({action, value});
  const button = (text, action, value, cls) => { const b = E('button', cls, text); b.click = () => command(typeof action === 'function' ? action() : action, value); return b; };
  const portrait = () => { const image = E('div'); return {wrap: add(E('div'), image), image}; };
  const window = {};
  vm.runInNewContext(fs.readFileSync(require.resolve('../chain-ui.js'), 'utf8'), {window});
  window.rivalCursor=require('../rival-cursor.js').rivalCursor;
  const saved = new Map(); window.localStorage={getItem:k=>saved.get(k)||null,setItem:(k,v)=>saved.set(k,v)};
  vm.runInNewContext(fs.readFileSync(require.resolve('../shiritori-dictionary.js'), 'utf8'), {window});
  vm.runInNewContext(fs.readFileSync(require.resolve('../shiritori-ui.js'), 'utf8'), {window, document: doc});
  const view = window.createShiritoriView({section: (n, c) => E('section', c), E, add, button, portrait, command});
  const state = {phase: 'playing', turn: 'you', required: 'り', last_word: 'しりとり', remaining: 20, limit: 20,
    hints: 3, hint: null, selected: null, message: 'りからはじめよう', mistakes: 0, history: [], winner: null,
    mode:'battle', total:24, stock:0, completed:0, relinks:2, seen:[],
    catalog:[{id:'apple',icon:'🍎',words:['りんご','くだもの','たべもの']}],
    cards: Array.from({length:24}, () => ({id:'apple', icon:'🍎', words:['りんご','くだもの'], owner:null}))};
  return {view, state, queue, doc};
}

test('setup shares number-game hero and controls without story exposition', () => {
  const {view,state}=harness();
  view.update({...state,phase:'intro'});
  const intro=view.page.querySelector('.sh-ready');
  assert.equal(intro.hidden,false);
  assert.ok(intro.className.includes('nr-ready'));
  assert.equal(intro.querySelector('.nr-hero-cast').children.length,3);
  assert.ok(intro.querySelector('.nr-setup'));
  assert.equal(intro.querySelectorAll('.nr-segment').length,3);
  assert.ok(intro.querySelector('.nr-intro-copy').textContent.includes('読み方は自動'));
  assert.ok(!intro.querySelectorAll('*').some(e=>/そそのか|コウ/.test(e.textContent)));
  view.update({...state,phase:'playing'});
  assert.equal(intro.hidden,true);
});

test('leaving an unfinished round for setup requires confirmation',()=>{
  const {view,state,queue,doc}=harness();
  view.update({...state,phase:'paused'});
  const modeButton=view.page.querySelectorAll('button').find(b=>b.textContent==='モード選択へ');
  modeButton.click();
  assert.equal(queue.at(-1).action,'sh_pause');
  view.update({...state,phase:'paused'});
  const dialog=view.page.querySelectorAll('.nr-dialog').find(d=>d.querySelectorAll('h1').some(h=>h.textContent==='モード選択に戻りますか？'));
  assert.equal(dialog.hidden,false);
  assert.equal(doc.activeElement.textContent,'戻る', 'setup-confirm entry focuses affirmative primary');
  assert.ok(!queue.some(c=>c.action==='sh_setup'));
  dialog.querySelectorAll('button').find(b=>b.textContent==='戻る').click();
  assert.equal(queue.at(-1).action,'sh_setup');
});

test('shiritori delegates navigation to the common header and confirms restart after pausing',()=>{
  const {view,state,queue}=harness();
  view.update({...state,phase:'intro'});
  const intro=view.page.querySelector('.sh-ready');
  assert.ok(!intro.querySelectorAll('button').some(b=>b.textContent.includes('ゲーム選択')));
  view.headerAction('help'); assert.equal(view.isOverlayOpen(),true); assert.equal(intro.hidden,true);
  view.update({...state,phase:'playing'});
  assert.ok(!view.page.querySelector('.sh-stage').querySelectorAll('button').some(b=>/休憩|一時停止/.test(b.textContent)));
  view.headerAction('retry'); assert.equal(queue.at(-1).action,'sh_pause');
  assert.ok(!queue.some(c=>c.action==='sh_restart'));
  view.update({...state,phase:'paused'});
  const confirm=view.page.querySelectorAll('.nr-dialog').find(n=>n.querySelectorAll('h1').some(h=>h.textContent==='やり直しますか？'));
  assert.equal(confirm.hidden,false);
  confirm.querySelectorAll('button').find(b=>b.textContent==='やり直す').click();
  assert.equal(queue.at(-1).action,'sh_restart');
  view.update({...state,phase:'playing'}); assert.equal(confirm.hidden,true);
});

test('dictionary collects player answers only, hides undiscovered readings and returns to setup',()=>{
  const {view,state}=harness(); view.update({...state,phase:'intro',cards:[]});
  const open=view.page.querySelectorAll('.sh-dict-open')[0]; open.events.click();
  assert.equal(view.page.querySelector('.sh-dictionary').hidden,false);
  assert.equal(view.page.querySelectorAll('.sh-undiscovered').length,3);
  const back=view.page.querySelector('.sh-dict-header').querySelector('button'); back.events.click();
  assert.equal(view.page.querySelector('.sh-dictionary').hidden,true);
  view.update({...state,history:[{id:'apple',word:'くだもの',owner:'cpu',icon:'🍎'}]});
  assert.match(open.textContent,/0 \/ 3/);
  view.update({...state,history:[{id:'apple',word:'りんご',owner:'you',icon:'🍎'}]});
  assert.match(open.textContent,/1 \/ 3/);
  view.update({...state,phase:'finished',history:[{id:'apple',word:'りんご',owner:'you',icon:'🍎'}]});
  view.page.querySelectorAll('.sh-dict-open')[1].events.click();
  assert.equal(view.page.querySelectorAll('.sh-found').length,1);
  assert.equal(view.page.querySelectorAll('.sh-undiscovered').length,2);
});

test('dictionary challenge reveals each discovered word and celebrates full completion',()=>{
  const {view,state}=harness(); view.update({...state,phase:'intro',cards:[]});
  view.page.querySelectorAll('.sh-dict-open')[0].events.click();
  const challenge=view.page.querySelectorAll('button').find(b=>b.textContent==='発見チャレンジ');
  for(let i=0;i<3;i++) {
    challenge.events.click();
    const choice=view.page.querySelector('.sh-dict-choice');
    choice.events.click(); choice.events.click();
    assert.equal(view.page.querySelectorAll('.sh-found').length,i+1);
  }
  assert.match(view.page.querySelector('.sh-dict-notice').textContent,/コンプリート/);
  assert.match(view.page.querySelector('.sh-dict-progress').textContent,/100.0%/);
  assert.equal(view.page.querySelector('.sh-dict-entry').dataset.complete,'true');
});

test('one tap submits a card with no reading dialog and keeps stable 24 slots', () => {
  const {view, state, queue} = harness(); view.update(state);
  const cards = view.page.querySelectorAll('.sh-card'); assert.equal(cards.length, 24);
  cards[0].click(); assert.deepEqual(queue[0], {action:'sh_card', value:0});
  assert.equal(view.page.querySelector('.sh-overlay'), undefined);
  assert.match(cards[0]['aria-label'], /タップで自動回答/);
  view.update({...state, remaining:17, mistakes:1, message:'ちがうよ −3秒'});
  assert.equal(view.page.querySelectorAll('.sh-card')[0], cards[0]);
  assert.equal(cards[0].disabled, false);
});

test('shiritori rival frame follows target only on CPU turns and clears for pause',()=>{
  const {view,state}=harness(); view.update({...state,turn:'cpu',cpu_target:10,cpu_progress:1});
  const cards=view.page.querySelectorAll('.sh-card');
  assert.equal(cards.filter(c=>c.dataset.cpuSelecting==='true').length,1);
  assert.equal(cards[10].dataset.cpuSelecting,'true');
  view.update({...state,phase:'paused',cards:[]});
  assert.ok(cards.every(c=>c.dataset.cpuSelecting==='false'));
  view.update({...state,mode:'solo',cpu_target:10,cpu_progress:1});
  assert.ok(cards.every(c=>c.dataset.cpuSelecting==='false'));
});

test('12 card course hides surplus slots and 24 card course restores them', () => {
  const {view, state} = harness();
  view.update({...state, total:12, cards:state.cards.slice(0,12)});
  assert.equal(view.page.querySelectorAll('.sh-card').filter(c => !c.hidden).length, 12);
  assert.equal(view.page.querySelector('.sh-board').dataset.count, '12');
  assert.equal(view.page.querySelector('.sh-board-space').dataset.count, '12');
  view.update(state);
  assert.equal(view.page.querySelectorAll('.sh-card').filter(c => !c.hidden).length, 24);
  assert.equal(view.page.querySelector('.sh-board').dataset.count, '24');
  assert.equal(view.page.querySelector('.sh-board-space').dataset.count, '24');
});

test('hint visibly identifies exactly one panel without blocking its input and clears after use', () => {
  const {view, state, queue} = harness();
  view.update({...state, hint:5, hints:2});
  const cards = view.page.querySelectorAll('.sh-card');
  assert.equal(cards.filter(c => c.dataset.hint === 'true').length, 1);
  assert.equal(cards[5].querySelector('.sh-hint-label').hidden, false);
  assert.match(cards[5]['aria-label'], /^ヒント：/);
  assert.equal(cards[5].disabled, false);
  cards[5].click(); assert.deepEqual(queue.pop(), {action:'sh_card', value:5});
  view.update({...state, hint:null});
  assert.ok(cards.every(c => c.querySelector('.sh-hint-label').hidden));
  assert.ok(cards.every(c => c.dataset.hint === 'false'));
});

test('pause conceals cards, CPU turn disables input, result exposes replay and history', () => {
  const {view, state} = harness();
  view.update({...state, turn:'cpu'});
  assert.ok(view.page.querySelectorAll('.sh-card').every(c => c.disabled));
  view.update({...state, phase:'paused', cards:[]});
  assert.equal(view.page.querySelector('.sh-stage').hidden, true);
  assert.equal(view.page.querySelector('.sh-overlay'), undefined);
  view.update({...state, phase:'finished', winner:'you', history:[{word:'りんご', icon:'🍎', owner:'you'}]});
  assert.equal(view.page.querySelector('.sh-log').children.length, 1);
  assert.ok(view.page.querySelectorAll('button').some(b => b.textContent === 'もう一度遊ぶ'));
});

test('finished focuses replay and Enter retries without breaking mode/dict', () => {
  const {view, state, queue, doc} = harness();
  view.update(state);
  const cards = view.page.querySelectorAll('.sh-card');
  cards[0].focus();
  assert.equal(doc.activeElement, cards[0]);

  view.update({...state, phase:'finished', winner:'you', history:[{word:'りんご', icon:'🍎', owner:'you', readings:['りんご']}]});
  const retry = view.page.querySelectorAll('button').find(b => b.textContent === 'もう一度遊ぶ');
  const setup = view.page.querySelectorAll('button').find(b => b.textContent === 'モード選択');
  const dict = view.page.querySelectorAll('.sh-dict-open')[1];
  assert.ok(retry && setup && dict, 'result actions stay available');
  assert.equal(doc.activeElement, retry, 'result entry focuses primary replay');

  const before = queue.length;
  view.page.emit('keydown', {key: 'Enter', repeat: false});
  assert.equal(queue.length, before, 'focused replay button keeps native activation (no double command)');

  // Non-button focus still offers a one-key retry path (parity with number-rush #17).
  const resultHeading = view.page.querySelectorAll('h1').find(h => h.textContent === 'あなたの勝利！');
  assert.ok(resultHeading, 'finished result title is present');
  resultHeading.focus();
  view.page.emit('keydown', {key: 'Enter', repeat: false});
  assert.equal(queue.at(-1).action, 'sh_start');

  const afterRetry = queue.length;
  setup.focus();
  view.page.emit('keydown', {key: ' ', repeat: false});
  assert.equal(queue.length, afterRetry, 'mode-select button keeps its own activation path');

  dict.focus();
  view.page.emit('keydown', {key: 'Enter', repeat: false});
  assert.equal(queue.length, afterRetry, 'dictionary button keeps native activation');

  // Re-entering finished from intro also restores replay focus.
  view.update({...state, phase:'intro', cards:[]});
  view.update({...state, phase:'finished', winner:'draw', history:[{word:'りんご', icon:'🍎', owner:'you', readings:['りんご']}]});
  assert.equal(doc.activeElement, retry, 'intro→result also restores replay focus');
});

test('new mode is shipped in Pages and loaded before its host renderer', () => {
  const html = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  assert.ok(html.indexOf('shiritori-ui.js') < html.indexOf('modern-ui.js'));
  const workflow = fs.readFileSync(require.resolve('../.github/workflows/pages.yml'), 'utf8');
  for (const name of ['shiritori.py', 'shiritori-ui.js', 'shiritori-ui.css']) assert.ok(workflow.includes(name));
});

test('solo setup offers deck counts, hides CPU, and permits immediate replacement selection', () => {
  const {view,state,queue} = harness();
  const solo = {...state, mode:'solo', total:48, stock:24, phase:'intro'};
  view.update(solo);
  const counts = view.page.querySelector('.sh-counts').querySelectorAll('button');
  assert.deepEqual(counts.map(b => b.textContent), ['12枚','24枚','36枚','48枚']);
  counts[3].click(); assert.deepEqual(queue.pop(), {action:'sh_total', value:48});
  assert.equal(view.page.querySelector('.sh-level-settings').hidden, true);
  solo.phase = 'playing'; view.update(solo);
  const card = view.page.querySelectorAll('.sh-card')[0];
  solo.cards[0] = {id:'cat',icon:'🐈',words:['ねこ','こねこ'],owner:null};
  solo.stock = 23; solo.completed = 1; solo.refilled = 0; solo.revision = 1;
  view.update(solo);
  assert.equal(view.page.querySelectorAll('.sh-card')[0], card);
  assert.equal(card.disabled, false);
  assert.equal(card.children[1].textContent, 'NEW');
  assert.equal(view.page.querySelector('.sh-stock').textContent, '山札 23枚');
});

test('blocked solo exposes rescue without any reading choices', () => {
  const {view,state} = harness();
  view.update(state);
  assert.equal(view.page.querySelector('.sh-choices'), undefined);
  view.update({...state, mode:'solo', phase:'blocked', relinks:2});
  const rescue = view.page.querySelectorAll('button').find(b => b.textContent === 'つなぎ直す あと2回');
  assert.equal(rescue.hidden, false);
  assert.ok(view.page.querySelectorAll('.sh-card').every(b => b.disabled));
});

test('shiritori deal motion respects reduced-motion and data-reduced', () => {
  const css = fs.readFileSync(require.resolve('../shiritori-ui.css'), 'utf8');
  assert.match(css, /#modern-app\[data-reduced='true'\] \.sh-icon \{ animation: none/);
  assert.match(css, /@media \(prefers-reduced-motion: reduce\) \{ \.sh-card\[data-dealt\] \.sh-icon \{ animation: none/);
});

test('sh-card keyboard focus uses ::before ring so hint/CPU outlines stay visible', () => {
  const modern = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const css = fs.readFileSync(require.resolve('../shiritori-ui.css'), 'utf8');
  // Cards excluded from shell outline; inset ::before ring leaves outline free for hint/CPU.
  assert.match(modern, /#modern-app button:not\(\.nr-cell\):not\(\.sh-card\):not\(\.nr-game-card\):focus-visible/);
  assert.match(modern, /#modern-app \.nr-cell:focus-visible, #modern-app \.sh-card:focus-visible, #modern-app \.nr-game-card:focus-visible \{ outline: none; \}/);
  assert.match(modern, /#modern-app \.nr-cell:focus-visible::before, #modern-app \.sh-card:focus-visible::before,[\s\S]*?#modern-app \.nr-game-card:focus-visible::before \{[^}]*box-shadow: inset 0 0 0 3px #f9d58a/);
  // Hint + CPU-selecting carry #modern-app so they beat focus outline:none when both apply.
  assert.match(css, /#modern-app \.sh-card\[data-hint='true'\]/);
  assert.match(modern, /#modern-app \.sh-card\[data-cpu-selecting='true'\]/);
  const contrastIdx = modern.indexOf('@media (prefers-contrast: more)');
  assert.match(modern.slice(contrastIdx), /prefers-contrast: more[\s\S]*?\.sh-card:focus-visible::before[\s\S]*?box-shadow: inset 0 0 0 4px #c9a227/);
  assert.match(modern.slice(contrastIdx), /prefers-contrast: more[\s\S]*?\.sh-card\[data-hint='true'\][\s\S]*?outline: 4px solid #a07000/);
  assert.match(modern.slice(contrastIdx), /prefers-contrast: more[\s\S]*?\.sh-card\[data-cpu-selecting='true'\][\s\S]*?outline: 4px solid #b01878/);
  const forcedIdx = modern.indexOf('@media (forced-colors: active)');
  assert.match(modern.slice(forcedIdx), /forced-colors: active[\s\S]*?\.sh-card:focus-visible::before[\s\S]*?box-shadow: inset 0 0 0 4px Highlight/);
  assert.match(modern.slice(forcedIdx), /forced-colors: active[\s\S]*?\.sh-card\[data-hint='true'\][^{]*\{[^}]*outline: 4px solid Highlight/);
  assert.match(modern.slice(forcedIdx), /forced-colors: active[\s\S]*?\.sh-card\[data-cpu-selecting='true'\][\s\S]*?outline: 4px solid ButtonText/);
});


test('nextShCell wraps within rows/cols for variable shiritori boards', () => {
  const {nextShCell, nextPlayableShCard} = require('../shiritori-ui.js');
  // 4×3 board (12 cards).
  assert.equal(nextShCell(0, 'ArrowRight', 4, 12), 1);
  assert.equal(nextShCell(3, 'ArrowRight', 4, 12), 0);
  assert.equal(nextShCell(0, 'ArrowLeft', 4, 12), 3);
  assert.equal(nextShCell(0, 'ArrowDown', 4, 12), 4);
  assert.equal(nextShCell(0, 'ArrowUp', 4, 12), 8);
  // Incomplete final row (10 cards / 4 cols): col1 down from row2 lands on row0 col1.
  assert.equal(nextShCell(9, 'ArrowDown', 4, 10), 1);
  // 8-col / 24-card board mirrors number-rush row wrap.
  assert.equal(nextShCell(7, 'ArrowRight', 8, 24), 0);
  assert.equal(nextShCell(8, 'ArrowLeft', 8, 24), 15);
  const available = Array(12).fill(false); available[1] = true; available[6] = true;
  assert.equal(nextPlayableShCard(available, 0, 'ArrowRight', 4), 1);
  assert.equal(nextPlayableShCard(available, 1, 'ArrowDown', 4), 1); // 1→5 disabled →9 disabled → wrap to 1
  assert.equal(nextPlayableShCard(available, 1, 'ArrowLeft', 4), 1);
  assert.equal(nextPlayableShCard(Array(12).fill(false), 0, 'ArrowRight', 4), -1);
});

test('arrow keys move among playable sh-cards and skip owned; Enter/Space stay native', () => {
  const {view, state, queue, doc} = harness();
  // total 12 → fallback cols=4 when getComputedStyle is absent.
  const cards12 = Array.from({length: 12}, (_, i) => ({id: 'apple', icon: '🍎', words: ['りんご'], owner: i === 1 ? 'you' : null}));
  view.update({...state, total: 12, cards: cards12, phase: 'playing', turn: 'you'});
  const cards = view.page.querySelectorAll('.sh-card').filter(c => !c.hidden);
  assert.equal(cards.length, 12);
  assert.equal(cards[1].disabled, true, 'owned card is disabled');
  assert.equal(cards[0].disabled, false);

  cards[0].focus();
  assert.equal(doc.activeElement, cards[0]);
  view.page.emit('keydown', {key: 'ArrowRight'});
  // Skip owned index 1 → land on 2.
  assert.equal(doc.activeElement, cards[2], 'ArrowRight skips owned card');

  view.page.emit('keydown', {key: 'ArrowLeft'});
  assert.equal(doc.activeElement, cards[0], 'ArrowLeft skips owned card back to 0');

  cards[0].focus();
  view.page.emit('keydown', {key: 'ArrowDown'});
  assert.equal(doc.activeElement, cards[4], 'ArrowDown moves one row in 4-col grid');

  // Enter/Space must not synthesize sh_card when a card already has focus (native click path).
  const before = queue.length;
  view.page.emit('keydown', {key: 'Enter', repeat: false});
  view.page.emit('keydown', {key: ' ', repeat: false});
  assert.equal(queue.length, before, 'Enter/Space do not double-fire card commands');

  // Mouse path still works.
  cards[2].click();
  assert.deepEqual(queue.at(-1), {action: 'sh_card', value: 2});
});

test('arrow keys are inert outside playing and when no playable cards remain', () => {
  const {view, state, doc} = harness();
  view.update({...state, phase: 'intro', cards: []});
  const introFocus = doc.activeElement;
  view.page.emit('keydown', {key: 'ArrowRight'});
  assert.equal(doc.activeElement, introFocus, 'arrows ignored on intro');

  const owned = Array.from({length: 12}, () => ({id: 'apple', icon: '🍎', words: ['りんご'], owner: 'you'}));
  view.update({...state, total: 12, cards: owned, phase: 'playing', turn: 'you'});
  const cards = view.page.querySelectorAll('.sh-card').filter(c => !c.hidden);
  cards[0].focus();
  view.page.emit('keydown', {key: 'ArrowRight'});
  assert.equal(doc.activeElement, cards[0], 'no move when every card is disabled');
});

test('play start focuses first playable sh-card for arrow nav; overlays and CPU turn spared', () => {
  const {view, state, queue, doc} = harness();
  const cards12 = Array.from({length: 12}, (_, i) => ({
    id: 'apple', icon: '🍎', words: ['りんご'], owner: i === 0 ? 'you' : null
  }));

  // intro → playing: skip owned card 0, land on first playable (index 1).
  view.update({...state, phase: 'intro', cards: []});
  view.update({...state, total: 12, cards: cards12, phase: 'playing', turn: 'you'});
  const cards = view.page.querySelectorAll('.sh-card').filter(c => !c.hidden);
  assert.equal(cards[0].disabled, true);
  assert.equal(cards[1].disabled, false);
  assert.equal(doc.activeElement, cards[1], 'play start focuses first playable card');

  // Arrow nav continues from that origin without Tab.
  view.page.emit('keydown', {key: 'ArrowRight'});
  assert.equal(doc.activeElement, cards[2], 'arrows work from auto-focused start card');

  // Same-phase updates must not yank focus (mouse/touch users mid-board).
  cards[5].focus();
  view.update({...state, total: 12, cards: cards12, phase: 'playing', turn: 'you', remaining: 19});
  assert.equal(doc.activeElement, cards[5], 'playing→playing keeps current focus');

  // Mouse path still queues sh_card.
  const before = queue.length;
  cards[2].click();
  assert.equal(queue.length, before + 1);
  assert.deepEqual(queue.at(-1), {action: 'sh_card', value: 2});

  // CPU turn: no playable cards → fall back to HUD prompt (do not leave focus nowhere).
  view.update({...state, phase: 'paused'});
  view.update({...state, total: 12, cards: cards12, phase: 'playing', turn: 'cpu'});
  assert.equal(doc.activeElement, view.page.querySelector('.sh-prompt'), 'CPU turn falls back to HUD prompt');

  // finished still prefers replay (do not steal with card focus).
  view.update({...state, phase: 'finished', winner: 'you', history: [], cards: cards12});
  assert.equal(doc.activeElement, view.page.querySelectorAll('button').find(b => b.textContent === 'もう一度遊ぶ'));

  // Dictionary overlay: entry focuses back; keep that focus (no card steal).
  view.update({...state, phase: 'intro', cards: []});
  const open = view.page.querySelectorAll('.sh-dict-open')[0];
  open.events.click();
  const dictFocus = doc.activeElement;
  assert.equal(dictFocus && dictFocus.textContent, '← 絵しりとりに戻る', 'dict entry focuses back');
  // Force playing while dictionary still open (overlay guard).
  view.update({...state, total: 12, cards: cards12, phase: 'playing', turn: 'you'});
  assert.equal(view.isOverlayOpen(), true);
  assert.equal(doc.activeElement, dictFocus, 'open dictionary keeps focus (no card steal)');
});


test('shiritori overlay entry focuses primary dialog control (parity with numbers #43)', () => {
  const {view, state, queue, doc} = harness();
  const cards12 = Array.from({length: 12}, (_, i) => ({
    id: 'apple', icon: '🍎', words: ['りんご'], owner: null
  }));
  const btn = (root, text) => root.querySelectorAll('button').find(b => b.textContent === text);

  // playing → pause: land on プレイを続ける (nr-primary), not the dialog title.
  view.update({...state, total: 12, cards: cards12, phase: 'playing', turn: 'you'});
  const cards = view.page.querySelectorAll('.sh-card').filter(c => !c.hidden);
  cards[2].focus();
  view.update({...state, total: 12, cards: [], phase: 'paused'});
  const resume = btn(view.page, 'プレイを続ける');
  assert.ok(resume && String(resume.className).includes('nr-primary'));
  assert.equal(doc.activeElement, resume, 'pause entry focuses プレイを続ける');

  // Same-phase pause updates leave mouse/keyboard focus alone.
  const extras = btn(view.page, '新しい配置でやり直す');
  extras.focus();
  view.update({...state, total: 12, cards: [], phase: 'paused', message: 'still paused'});
  assert.equal(doc.activeElement, extras, 'paused→paused keeps current focus');

  // Restart confirm (from header retry): affirmative primary, not the h1 title.
  view.update({...state, total: 12, cards: cards12, phase: 'playing', turn: 'you'});
  view.headerAction('retry');
  assert.equal(queue.at(-1).action, 'sh_pause');
  view.update({...state, total: 12, cards: [], phase: 'paused'});
  const confirm = view.page.querySelectorAll('.nr-dialog').find(n =>
    n.querySelectorAll('h1').some(h => h.textContent === 'やり直しますか？'));
  assert.equal(confirm.hidden, false);
  const yes = btn(confirm, 'やり直す');
  assert.ok(yes && String(yes.className).includes('nr-primary'));
  assert.equal(doc.activeElement, yes, 'restart entry focuses affirmative primary');

  // Mode-select confirm from pause extras: affirmative 戻る primary.
  view.update({...state, total: 12, cards: cards12, phase: 'playing', turn: 'you'});
  view.update({...state, total: 12, cards: [], phase: 'paused'});
  assert.equal(doc.activeElement, resume, 're-pause focuses resume again');
  btn(view.page, 'モード選択へ').click();
  view.update({...state, total: 12, cards: [], phase: 'paused'});
  const setupConfirm = view.page.querySelectorAll('.nr-dialog').find(n =>
    n.querySelectorAll('h1').some(h => h.textContent === 'モード選択に戻りますか？'));
  assert.equal(setupConfirm.hidden, false);
  const setupYes = btn(setupConfirm, '戻る');
  assert.equal(doc.activeElement, setupYes, 'setup-confirm entry focuses affirmative 戻る');

  // Help overlay already lands on 戻る primary (kept). Esc wiring unchanged (#16 family).
  view.update({...state, phase: 'intro', cards: []});
  view.headerAction('help');
  const helpBack = view.page.querySelectorAll('button').find(b => b.textContent === '戻る' && String(b.className).includes('nr-primary'));
  assert.equal(doc.activeElement, helpBack, 'help entry focuses 戻る');
});


test('shiritori overlay Tab cycles dialog controls and does not escape (parity #45)', () => {
  const {view, state, queue, doc} = harness();
  const cards12 = Array.from({length: 12}, (_, i) => ({
    id: 'apple', icon: '🍎', words: ['りんご'], owner: null
  }));
  const btn = (root, text) => root.querySelectorAll('button').find(b => b.textContent === text);
  const stopsOf = (root) => {
    const stops = [];
    (function visit(node) {
      if (!node || node.hidden) return;
      if (node.tagName === 'BUTTON' && !node.disabled) stops.push(node);
      for (const child of node.children || []) visit(child);
    })(root);
    return stops;
  };

  // Pause: entry resume (#44); Tab cycles pause controls only; Shift+Tab wraps.
  view.update({...state, total: 12, cards: cards12, phase: 'playing', turn: 'you'});
  const cards = view.page.querySelectorAll('.sh-card').filter(c => !c.hidden);
  cards[0].focus();
  view.update({...state, total: 12, cards: [], phase: 'paused'});
  const pause = view.page.querySelectorAll('.nr-dialog').find(n =>
    n.querySelectorAll('h1').some(h => h.textContent === 'ひと休みしよう'));
  assert.equal(pause.hidden, false);
  const resume = btn(pause, 'プレイを続ける');
  assert.equal(doc.activeElement, resume, 'pause entry still focuses resume (#44)');
  const pauseStops = stopsOf(pause);
  assert.ok(pauseStops.length >= 3, 'pause exposes multiple tab stops');
  assert.equal(pauseStops[0], resume);
  assert.ok(!pauseStops.includes(cards[0]), 'playable cards stay outside the trap');
  for (let i = 0; i < pauseStops.length; i++) {
    const expected = pauseStops[(i + 1) % pauseStops.length];
    view.page.emit('keydown', {key: 'Tab', shiftKey: false});
    assert.equal(doc.activeElement, expected, `pause Tab step ${i + 1} stays in dialog`);
  }
  resume.focus();
  view.page.emit('keydown', {key: 'Tab', shiftKey: true});
  assert.equal(doc.activeElement, pauseStops[pauseStops.length - 1], 'Shift+Tab wraps inside pause');

  // Esc on pause still requests pause→resume path via playing Esc (#16 family).
  // (While already paused, Esc is inert in shiritori page; cancel is for restart confirm.)
  view.update({...state, total: 12, cards: cards12, phase: 'playing', turn: 'you'});
  const beforeEsc = queue.length;
  view.page.emit('keydown', {key: 'Escape'});
  assert.equal(queue.at(-1).action, 'sh_pause');
  assert.equal(queue.length, beforeEsc + 1);

  // Restart confirm: affirmative primary entry; Tab cycles yes/cancel only.
  view.headerAction('retry');
  view.update({...state, total: 12, cards: [], phase: 'paused'});
  const confirm = view.page.querySelectorAll('.nr-dialog').find(n =>
    n.querySelectorAll('h1').some(h => h.textContent === 'やり直しますか？'));
  assert.equal(confirm.hidden, false);
  const yes = btn(confirm, 'やり直す');
  assert.equal(doc.activeElement, yes, 'restart entry still focuses affirmative (#44)');
  const confirmStops = stopsOf(confirm);
  assert.deepEqual(confirmStops.map(b => b.textContent), ['やり直す', 'キャンセル']);
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(doc.activeElement, confirmStops[1], 'restart Tab moves to キャンセル');
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(doc.activeElement, confirmStops[0], 'restart Tab wraps to やり直す');
  // Esc cancels restart confirm without accepting.
  const beforeCancel = queue.length;
  view.page.emit('keydown', {key: 'Escape'});
  assert.equal(queue.at(-1).action, 'sh_resume', 'Esc on restart confirm still cancels');
  assert.equal(queue.length, beforeCancel + 1);

  // Dictionary: entry back (#44); Tab cycles dict chrome (quiz hidden → no choices).
  view.update({...state, phase: 'intro', cards: []});
  view.page.querySelectorAll('.sh-dict-open')[0].events.click();
  const dict = view.page.querySelector('.sh-dictionary');
  assert.equal(dict.hidden, false);
  const dictBack = btn(dict, '← 絵しりとりに戻る');
  assert.equal(doc.activeElement, dictBack, 'dict entry still focuses back (#44)');
  const dictStops = stopsOf(dict);
  assert.ok(dictStops.includes(dictBack));
  assert.ok(dictStops.length >= 2, 'dict exposes back + actions');
  for (let i = 0; i < dictStops.length; i++) {
    view.page.emit('keydown', {key: 'Tab', shiftKey: false});
    assert.equal(doc.activeElement, dictStops[(i + 1) % dictStops.length], `dict Tab step ${i + 1}`);
  }
  dictBack.events.click();

  // Help: entry 戻る; single-stop Tab stays on 戻る (no escape to intro setup).
  view.headerAction('help');
  const helpPage = view.page.querySelector('.nr-help-card');
  assert.equal(helpPage.hidden, false);
  const helpBack = btn(helpPage, '戻る');
  assert.equal(doc.activeElement, helpBack, 'help entry still focuses 戻る (#44)');
  const helpStops = stopsOf(helpPage);
  assert.equal(helpStops.length, 1);
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(doc.activeElement, helpBack, 'help Tab stays on 戻る');
  const startBtn = btn(view.page, 'はじめる');
  assert.notEqual(doc.activeElement, startBtn, 'help Tab must not escape to setup');

  // Playing: Tab is not trapped (cards keep native order / no cycle).
  view.update({...state, total: 12, cards: cards12, phase: 'playing', turn: 'you'});
  const first = view.page.querySelectorAll('.sh-card').filter(c => !c.hidden)[0];
  first.focus();
  assert.equal(doc.activeElement, first, 'play start still focuses first playable (#35)');
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(doc.activeElement, first, 'playing leaves Tab alone (no preventDefault cycle)');
});


test('intro setup Tab cycles mode/count/difficulty/start only (parity ready #52)', () => {
  const {view, state, doc} = harness();
  const btn = (root, text) => root.querySelectorAll('button').find(b => b.textContent === text);
  const stopsOf = (roots) => {
    const stops = [];
    const visit = (node) => {
      if (!node || node.hidden) return;
      if (node.tagName === 'BUTTON' && !node.disabled) stops.push(node);
      for (const child of node.children || []) visit(child);
    };
    for (const root of roots) visit(root);
    return stops;
  };
  const setupRoots = () => {
    const intro = view.page.querySelector('.sh-ready');
    const modeGroup = intro.querySelector('.sh-modes');
    const countGroup = intro.querySelector('.sh-counts');
    const levels = intro.querySelector('.sh-level-settings');
    const startGroup = intro.querySelector('.sh-start-actions');
    const start = startGroup && startGroup.querySelectorAll('button')[0];
    return {intro, modeGroup, countGroup, levels, startGroup, start};
  };

  // Battle intro: entry focuses intro h1; Tab cycles mode/count/difficulty/start only.
  view.update({...state, phase: 'intro', mode: 'battle', cards: []});
  const roots = setupRoots();
  const heading = roots.intro.querySelector('h1');
  assert.equal(doc.activeElement, heading, 'intro entry still focuses heading h1');
  assert.equal(roots.levels.hidden, false, 'battle shows difficulty');
  assert.equal(roots.start.textContent, '対戦スタート', 'battle start label');

  const battleStops = stopsOf([roots.modeGroup, roots.countGroup, roots.levels, roots.startGroup]);
  // 2 modes + 4 counts + 3 levels + 1 start = 10
  assert.equal(battleStops.length, 10, 'battle setup exposes mode+count+difficulty+start');
  assert.ok(battleStops.includes(roots.start));
  assert.deepEqual(
    battleStops.slice(0, 2).map(b => b.textContent),
    ['CPUと対戦', 'ひとりで練習']
  );
  assert.equal(battleStops[battleStops.length - 1], roots.start);

  const dictOpen = view.page.querySelectorAll('.sh-dict-open')[0];
  assert.ok(dictOpen, 'intro still exposes 読み方ずかん');
  assert.ok(!battleStops.includes(dictOpen), '読み方ずかん stays outside the setup trap');

  // From entry heading (outside ring): Tab enters first mode control.
  heading.focus();
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(doc.activeElement, battleStops[0], 'Tab from heading enters first mode');

  const startIdx = battleStops.indexOf(roots.start);
  roots.start.focus();
  for (let i = 0; i < battleStops.length; i++) {
    const expected = battleStops[(startIdx + i + 1) % battleStops.length];
    view.page.emit('keydown', {key: 'Tab', shiftKey: false});
    assert.equal(doc.activeElement, expected, `battle Tab step ${i + 1} stays in setup`);
    assert.notEqual(doc.activeElement, dictOpen, 'Tab must not escape to 読み方ずかん');
  }
  roots.start.focus();
  view.page.emit('keydown', {key: 'Tab', shiftKey: true});
  assert.equal(
    doc.activeElement,
    battleStops[(startIdx - 1 + battleStops.length) % battleStops.length],
    'Shift+Tab wraps inside setup'
  );

  // Focus already on dict (outside ring): Tab pulls back into setup (first mode).
  dictOpen.focus();
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(doc.activeElement, battleStops[0], 'Tab from dict re-enters setup');

  // Solo hides difficulty; Tab still cycles remaining setup controls only.
  // Leave and re-enter intro so entry focus runs (same-phase keeps focus).
  view.update({...state, phase: 'playing', cards: []});
  view.update({...state, phase: 'intro', mode: 'solo', cards: []});
  assert.equal(doc.activeElement, roots.intro.querySelector('h1'), 'solo intro still focuses heading');
  assert.equal(roots.levels.hidden, true, 'solo hides difficulty');
  const soloStops = stopsOf([roots.modeGroup, roots.countGroup, roots.levels, roots.startGroup]);
  assert.equal(soloStops.length, 7, 'solo setup omits hidden difficulty');
  assert.ok(!soloStops.some(n => {
    let cur = n;
    while (cur) {
      if (cur === roots.levels) return true;
      cur = cur.parentElement;
    }
    return false;
  }), 'solo stops exclude difficulty buttons');
  roots.start.focus();
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(doc.activeElement, soloStops[0], 'solo Tab wraps to first mode');
  assert.notEqual(doc.activeElement, dictOpen);

  // Overlay trap still wins over intro when help is open (#46 regression).
  view.headerAction('help');
  const helpPage = view.page.querySelector('.nr-help-card');
  const helpBack = btn(helpPage, '戻る');
  assert.equal(doc.activeElement, helpBack, 'help entry still focuses 戻る');
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(doc.activeElement, helpBack, 'help Tab stays on 戻る (intro trap idle)');
  assert.notEqual(doc.activeElement, roots.start, 'help Tab must not escape to setup');

  // Playing: Tab is not trapped (no intro bleed).
  const cards12 = Array.from({length: 12}, () => ({id: 'apple', icon: '🍎', words: ['りんご'], owner: null}));
  view.update({...state, total: 12, cards: cards12, phase: 'playing', turn: 'you'});
  const first = view.page.querySelectorAll('.sh-card').filter(c => !c.hidden)[0];
  first.focus();
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(doc.activeElement, first, 'playing leaves Tab alone (no intro trap bleed)');
});
