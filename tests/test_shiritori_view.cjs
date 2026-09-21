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
  assert.equal(card.dataset.refilled, 'true');
  assert.match(card['aria-label'] || '', /NEW補充/);
  assert.equal(view.page.querySelectorAll('.sh-card')[1].dataset.refilled, 'false');
  assert.equal(view.page.querySelector('.sh-stock').textContent, '山札 23枚');
  // Cleared after next take / when refilled index moves away.
  solo.refilled = null;
  view.update(solo);
  assert.equal(card.dataset.refilled, 'false');
  assert.equal(card.children[1].textContent, '');
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

test('blocked entry focuses rescue primary; overlays and play-start spared', () => {
  const {view, state, doc} = harness();
  const cards12 = Array.from({length: 12}, () => ({
    id: 'apple', icon: '🍎', words: ['りんご'], owner: null
  }));
  const btn = (root, text) => root.querySelectorAll('button').find(b => b.textContent === text);

  // playing → blocked: land on 「つなぎ直す」 (nr-primary), not HUD heading / disabled cards.
  view.update({...state, mode: 'solo', total: 12, cards: cards12, phase: 'playing', turn: 'you'});
  const cards = view.page.querySelectorAll('.sh-card').filter(c => !c.hidden);
  assert.equal(doc.activeElement, cards[0], 'play start still focuses first playable (#35)');
  cards[3].focus();
  view.update({...state, mode: 'solo', total: 12, cards: cards12, phase: 'blocked', turn: 'you', relinks: 2});
  const rescue = btn(view.page, 'つなぎ直す あと2回');
  assert.ok(rescue && String(rescue.className).includes('nr-primary'));
  assert.equal(rescue.hidden, false);
  assert.equal(doc.activeElement, rescue, 'blocked entry focuses つなぎ直す');
  assert.ok(cards.every(c => c.disabled), 'all cards disabled while blocked');

  // Same-phase blocked updates leave mouse/keyboard focus alone.
  const prompt = view.page.querySelector('.sh-prompt');
  prompt.focus();
  view.update({...state, mode: 'solo', total: 12, cards: cards12, phase: 'blocked', turn: 'you', relinks: 2, message: 'still blocked'});
  assert.equal(doc.activeElement, prompt, 'blocked→blocked keeps current focus');

  // blocked → playing (after relink): restore play-start first-playable focus (#35).
  view.update({...state, mode: 'solo', total: 12, cards: cards12, phase: 'playing', turn: 'you', relinks: 1});
  assert.equal(doc.activeElement, cards[0], 'blocked→playing restores first playable (#35)');

  // Pause overlay still wins entry focus (#44); no rescue steal while paused.
  view.update({...state, mode: 'solo', total: 12, cards: cards12, phase: 'blocked', turn: 'you', relinks: 1});
  assert.equal(doc.activeElement, btn(view.page, 'つなぎ直す あと1回'), 're-blocked focuses rescue again');
  view.update({...state, mode: 'solo', total: 12, cards: [], phase: 'paused'});
  assert.equal(doc.activeElement, btn(view.page, 'プレイを続ける'), 'pause entry still focuses resume (#44)');

  // Dictionary overlay: keep back-button focus (no rescue steal) (#44/#46).
  view.update({...state, mode: 'solo', phase: 'intro', cards: []});
  const open = view.page.querySelectorAll('.sh-dict-open')[0];
  open.events.click();
  const dictFocus = doc.activeElement;
  assert.equal(dictFocus && dictFocus.textContent, '← 絵しりとりに戻る', 'dict entry focuses back');
  view.update({...state, mode: 'solo', total: 12, cards: cards12, phase: 'blocked', turn: 'you', relinks: 2});
  assert.equal(view.isOverlayOpen(), true);
  assert.equal(doc.activeElement, dictFocus, 'open dictionary keeps focus (no rescue steal)');
});

test('blocked Tab stays on rescue つなぎ直す and does not escape (parity help #46)', () => {
  const {view, state, queue, doc} = harness();
  const cards12 = Array.from({length: 12}, (_, i) => ({
    id: 'apple', icon: '🍎', words: ['りんご'], owner: null
  }));
  const btn = (root, text) => root.querySelectorAll('button').find(b => b.textContent === text);

  view.update({...state, mode: 'solo', total: 12, cards: cards12, phase: 'playing', turn: 'you', hints: 2});
  view.update({...state, mode: 'solo', total: 12, cards: cards12, phase: 'blocked', turn: 'you', relinks: 2, hints: 2});
  const rescue = btn(view.page, 'つなぎ直す あと2回');
  assert.equal(doc.activeElement, rescue, 'blocked entry still focuses rescue (#60)');

  // Single enabled play-action: Tab / Shift+Tab stay on rescue (no escape to setup/dict).
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(doc.activeElement, rescue, 'blocked Tab stays on つなぎ直す');
  view.page.emit('keydown', {key: 'Tab', shiftKey: true});
  assert.equal(doc.activeElement, rescue, 'blocked Shift+Tab stays on つなぎ直す');

  // Hint remains disabled and out of the ring; cards stay disabled.
  const hint = view.page.querySelectorAll('button').find(b => /^ヒント/.test(b.textContent || ''));
  assert.ok(hint && hint.disabled, 'hint stays disabled while blocked');
  assert.ok(view.page.querySelectorAll('.sh-card').filter(c => !c.hidden).every(b => b.disabled),
    'visible cards stay disabled while blocked');

  // Esc still requests pause (#16 family) while blocked.
  const beforeEsc = queue.length;
  view.page.emit('keydown', {key: 'Escape'});
  assert.equal(queue.length, beforeEsc + 1);
  assert.equal(queue.at(-1).action, 'sh_pause', 'Esc on blocked still pauses');

  // Playing: Tab is still not trapped (cards keep native order / no cycle).
  view.update({...state, mode: 'solo', total: 12, cards: cards12, phase: 'playing', turn: 'you', hints: 2});
  const first = view.page.querySelectorAll('.sh-card').filter(c => !c.hidden)[0];
  first.focus();
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(doc.activeElement, first, 'playing leaves Tab alone (no preventDefault cycle)');
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
  // Esc dismisses dict via close()/back (parity help Esc / numbers help #63).
  // Re-land on back then Esc; Tab trap (#46) + entry (#44) stay intact above.
  dictBack.focus();
  const dictOpenBtn = view.page.querySelectorAll('.sh-dict-open')[0];
  view.page.emit('keydown', {key: 'Escape'});
  assert.equal(dict.hidden, true, 'Esc closes dictionary via close()/back');
  assert.equal(view.isOverlayOpen(), false, 'Esc clears dictionary overlay flag');
  assert.equal(doc.activeElement, dictOpenBtn, 'Esc restores intro 読み方ずかん focus (onClose)');
  // Re-open for help section independence.
  dictOpenBtn.events.click();
  assert.equal(dict.hidden, false);
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

test('finished result Tab cycles replay/mode/history/dict and does not escape (parity #48/#58)', () => {
  const {view, state, queue, doc} = harness();
  const collectStops = (root) => {
    const stops = [];
    (function visit(node) {
      if (!node || node.hidden) return;
      if (node.tagName === 'BUTTON' && !node.disabled) stops.push(node);
      else if (node.tagName === 'SUMMARY') stops.push(node);
      for (const child of node.children || []) visit(child);
    })(root);
    return stops;
  };

  // Battle result: entry replay (#19); Tab cycles retry/mode/history summary/dict.
  view.update({...state, phase: 'playing'});
  view.update({
    ...state,
    phase: 'finished',
    winner: 'you',
    history: [{id: 'apple', word: 'りんご', icon: '🍎', owner: 'you', readings: ['りんご']}],
  });
  const result = view.page.querySelector('.sh-result');
  assert.ok(result && result.hidden === false, 'result screen is visible');
  const retry = result.querySelectorAll('button').find(b => b.textContent === 'もう一度遊ぶ');
  const setup = result.querySelectorAll('button').find(b => b.textContent === 'モード選択');
  const dict = result.querySelector('.sh-dict-open');
  const history = result.querySelector('.sh-result-history');
  const historySummary = history && history.querySelector('summary');
  assert.ok(retry && setup && dict, 'result actions stay available');
  assert.ok(history && historySummary, 'result history <details>/<summary> is present');
  assert.equal(historySummary.textContent, 'ことばと別の読み方を振り返る');
  assert.equal(doc.activeElement, retry, 'result entry still focuses primary replay (#19)');

  const finishedStops = collectStops(result);
  assert.deepEqual(finishedStops, [retry, setup, historySummary, dict], 'finished exposes retry/mode/history/dict');
  // Intro dict (outside result) must not join the ring.
  const introDict = view.page.querySelectorAll('.sh-dict-open')[0];
  assert.ok(introDict && introDict !== dict);
  assert.ok(!finishedStops.includes(introDict), 'intro 読み方ずかん stays outside result trap');

  for (let i = 0; i < finishedStops.length; i++) {
    const expected = finishedStops[(i + 1) % finishedStops.length];
    view.page.emit('keydown', {key: 'Tab', shiftKey: false});
    assert.equal(doc.activeElement, expected, `finished Tab step ${i + 1} stays in result`);
    assert.notEqual(doc.activeElement, introDict, 'Tab must not escape to intro dict');
  }
  retry.focus();
  view.page.emit('keydown', {key: 'Tab', shiftKey: true});
  assert.equal(doc.activeElement, finishedStops[finishedStops.length - 1], 'Shift+Tab wraps inside finished');

  // Focus already outside ring (heading): Tab pulls back onto replay (first stop).
  const heading = result.querySelectorAll('h1').find(h => h.textContent === 'あなたの勝利！');
  assert.ok(heading, 'finished result title is present');
  heading.focus();
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(doc.activeElement, retry, 'Tab from heading re-enters result on replay');

  // #19 Enter/Space retry still works when focus is not on a visible button/summary.
  heading.focus();
  const beforeEnter = queue.length;
  view.page.emit('keydown', {key: 'Enter', repeat: false});
  assert.equal(queue.at(-1).action, 'sh_start', 'Enter still retries from non-button focus (#19)');
  assert.equal(queue.length, beforeEnter + 1);
  setup.focus();
  const afterSetup = queue.length;
  view.page.emit('keydown', {key: ' ', repeat: false});
  assert.equal(queue.length, afterSetup, 'mode-select button keeps native Space activation');

  // History <summary>: Enter/Space must NOT steal into replay (#19); leave native toggle.
  historySummary.focus();
  const beforeSummary = queue.length;
  view.page.emit('keydown', {key: 'Enter', repeat: false});
  assert.equal(queue.length, beforeSummary, 'Enter on history summary does not retry');
  view.page.emit('keydown', {key: ' ', repeat: false});
  assert.equal(queue.length, beforeSummary, 'Space on history summary does not retry');

  // Solo finished: same four stops (history summary stays in the ring).
  view.update({...state, phase: 'intro', mode: 'solo', cards: []});
  view.update({
    ...state,
    phase: 'finished',
    mode: 'solo',
    winner: 'you',
    history: [{id: 'apple', word: 'りんご', icon: '🍎', owner: 'you', readings: ['りんご']}],
  });
  assert.equal(doc.activeElement, retry, 'solo result still focuses replay (#19)');
  const soloStops = collectStops(result);
  assert.deepEqual(soloStops, [retry, setup, historySummary, dict], 'solo finished keeps retry/mode/history/dict');
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(doc.activeElement, setup, 'solo Tab moves to モード選択');
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(doc.activeElement, historySummary, 'solo Tab moves to history summary');
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(doc.activeElement, dict, 'solo Tab moves to 読み方ずかん');
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(doc.activeElement, retry, 'solo Tab wraps to replay');

  // Overlay trap still wins when dictionary opens from result (#46 regression).
  dict.events.click();
  assert.equal(view.isOverlayOpen(), true, 'dictionary opens from result');
  const dictBack = view.page.querySelector('.sh-dict-header').querySelector('button');
  assert.equal(doc.activeElement, dictBack, 'dict entry still focuses back (#44)');
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.notEqual(doc.activeElement, retry, 'dict Tab must not escape to result replay');
  assert.ok(
    view.page.querySelector('.sh-dictionary').contains(doc.activeElement),
    'dict Tab stays inside dictionary overlay'
  );
  // Close dict so later playing check is not still trapped in the overlay.
  dictBack.events.click();
  assert.equal(view.isOverlayOpen(), false, 'dictionary closes back to result');
  assert.equal(doc.activeElement, dict, 'dict close restores result 読み方ずかん focus');

  // Playing: Tab is not trapped (no result trap bleed).
  const cards12 = Array.from({length: 12}, () => ({id: 'apple', icon: '🍎', words: ['りんご'], owner: null}));
  view.update({...state, total: 12, cards: cards12, phase: 'playing', turn: 'you'});
  const first = view.page.querySelectorAll('.sh-card').filter(c => !c.hidden)[0];
  first.focus();
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.equal(doc.activeElement, first, 'playing leaves Tab alone (no result trap bleed)');
});

test('result history details summary is in Tab ring and keeps 44px hit target', () => {
  const sh = fs.readFileSync(require.resolve('../shiritori-ui.js'), 'utf8');
  const css = fs.readFileSync(require.resolve('../shiritori-ui.css'), 'utf8');
  assert.match(sh, /sh-result-history/);
  assert.match(sh, /else if \(node\.tagName === 'SUMMARY'\)/);
  assert.match(sh, /onHistorySummary/);
  assert.match(css, /\.sh-result-history summary \{[^}]*min-height: 44px/);
});

test('dictionary Esc dismisses via close()/back path (parity help Esc / #63)', () => {
  const {view, state, queue, doc} = harness();
  const btn = (root, text) => root.querySelectorAll('button').find(b => b.textContent === text);

  // Intro: open dict (entry #44 on back), Esc closes via same onClose as ←戻る.
  view.update({...state, phase: 'intro', cards: []});
  const introDict = view.page.querySelectorAll('.sh-dict-open')[0];
  introDict.events.click();
  const dict = view.page.querySelector('.sh-dictionary');
  assert.equal(dict.hidden, false);
  assert.equal(view.isOverlayOpen(), true);
  const dictBack = btn(dict, '← 絵しりとりに戻る');
  assert.equal(doc.activeElement, dictBack, 'dict entry still focuses back (#44)');

  // Tab trap still works before Esc (#46 regression guard).
  view.page.emit('keydown', {key: 'Tab', shiftKey: false});
  assert.ok(dict.contains(doc.activeElement), 'dict Tab stays inside before Esc');
  assert.notEqual(doc.activeElement, introDict, 'Tab must not escape to intro dict button');

  const beforeEsc = queue.length;
  view.page.emit('keydown', {key: 'Escape'});
  assert.equal(dict.hidden, true, 'Esc hides dictionary page');
  assert.equal(view.isOverlayOpen(), false, 'Esc clears dictionaryOpen');
  assert.equal(doc.activeElement, introDict, 'Esc restores intro 読み方ずかん via onClose');
  assert.equal(queue.length, beforeEsc, 'Esc on dict does not enqueue game commands');

  // Finished: same Esc→close()/back path restores result dict button.
  view.update({
    ...state,
    phase: 'finished',
    winner: 'you',
    history: [{id: 'apple', word: 'りんご', icon: '🍎', owner: 'you', readings: ['りんご']}],
  });
  const resultDict = view.page.querySelectorAll('.sh-dict-open')[1];
  resultDict.events.click();
  assert.equal(dict.hidden, false);
  assert.equal(doc.activeElement, dictBack, 'result dict entry focuses back (#44)');
  view.page.emit('keydown', {key: 'Escape'});
  assert.equal(dict.hidden, true, 'Esc closes dictionary from result');
  assert.equal(view.isOverlayOpen(), false);
  assert.equal(doc.activeElement, resultDict, 'Esc restores result 読み方ずかん focus');

  // Help Esc still works (parity / no regression).
  view.update({...state, phase: 'intro', cards: []});
  view.headerAction('help');
  const helpPage = view.page.querySelector('.nr-help-card');
  assert.equal(helpPage.hidden, false);
  view.page.emit('keydown', {key: 'Escape'});
  assert.equal(helpPage.hidden, true, 'help Esc still dismisses via 戻る');
});


test('wrong miss_card paints durable feedback outline on that sh-card', () => {
  const {view, state} = harness();
  view.update({...state, miss_card: 3, message: 'この絵は「り」につながらないよ'});
  const cards = view.page.querySelectorAll('.sh-card');
  assert.equal(cards[3].dataset.feedback, 'wrong');
  assert.equal(cards[0].dataset.feedback, '');
  assert.match(cards[3]['aria-label'] || '', /ミス/);
  // Cleared when miss_card is null (TTL expired / correct take).
  view.update({...state, miss_card: null});
  assert.equal(cards[3].dataset.feedback, '');
  // Non-live phases drop the cue even if a stale index arrives.
  view.update({...state, phase: 'finished', winner: 'you', miss_card: 3, history: []});
  assert.equal(cards[3].dataset.feedback, '');
});

test('shiritori miss outline CSS mirrors numbers durable wrong feedback', () => {
  const sh = fs.readFileSync(require.resolve('../shiritori-ui.css'), 'utf8');
  const modern = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  assert.match(sh, /#modern-app \.sh-card\[data-feedback='wrong'\]/);
  assert.match(sh, /#modern-app \.sh-card\[data-feedback='wrong'\]::after/);
  assert.match(sh, /content: 'ミス'/);
  const contrastIdx = modern.indexOf('@media (prefers-contrast: more)');
  assert.match(modern.slice(contrastIdx), /prefers-contrast: more[\s\S]*?\.sh-card\[data-feedback='wrong'\][\s\S]*?outline: 4px solid #d0181c/);
  const forcedIdx = modern.indexOf('@media (forced-colors: active)');
  assert.match(modern.slice(forcedIdx), /forced-colors: active[\s\S]*?\.sh-card\[data-feedback='wrong'\][\s\S]*?outline: 4px solid LinkText/);
  assert.match(player, /shiritori-ui\.css\?v=result-score-hierarchy-1/);
  assert.match(player, /shiritori-ui\.js\?v=result-score-hierarchy-1/);
  assert.match(player, /modern-ui\.css\?v=result-score-hierarchy-1/);
});

test('NEW refill badge CSS is gold-distinct with contrast/forced-colors', () => {
  const sh = fs.readFileSync(require.resolve('../shiritori-ui.css'), 'utf8');
  const modern = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  assert.match(sh, /#modern-app \.sh-card\[data-refilled='true'\]/);
  assert.match(sh, /#modern-app \.sh-card\[data-refilled='true'\] small/);
  assert.match(sh, /@keyframes sh-refill-glow/);
  assert.match(sh, /prefers-reduced-motion: reduce[\s\S]*?data-refilled='true'[\s\S]*?animation: none/);
  assert.match(sh, /max-width: 600px[\s\S]*?data-refilled='true'\] small[\s\S]*?font-size: 11px/);
  const contrastIdx = modern.indexOf('@media (prefers-contrast: more)');
  assert.match(modern.slice(contrastIdx), /prefers-contrast: more[\s\S]*?\.sh-card\[data-refilled='true'\][\s\S]*?outline: 4px solid #a07000/);
  const forcedIdx = modern.indexOf('@media (forced-colors: active)');
  assert.match(modern.slice(forcedIdx), /forced-colors: active[\s\S]*?\.sh-card\[data-refilled='true'\][\s\S]*?outline: 4px solid Highlight/);
  assert.match(player, /shiritori-ui\.css\?v=result-score-hierarchy-1/);
  assert.match(player, /shiritori-ui\.js\?v=result-score-hierarchy-1/);
  assert.match(player, /modern-ui\.css\?v=result-score-hierarchy-1/);
});

test('shiritori HUD required cue CSS pulses on change and stays static under reduced-motion', () => {
  const css = fs.readFileSync(require.resolve('../shiritori-ui.css'), 'utf8');
  const modern = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  assert.match(css, /\.sh-task\[data-cue='true'\]\[data-pulse='0'\]/);
  assert.match(css, /\.sh-task\[data-cue='true'\]\[data-pulse='1'\]/);
  assert.match(css, /@keyframes sh-task-cue-a/);
  assert.match(css, /@keyframes sh-task-cue-b/);
  assert.match(css, /@media \(prefers-reduced-motion: reduce\) \{[\s\S]*?\.sh-task\[data-cue='true'\][\s\S]*?animation: none !important/);
  assert.match(css, /#modern-app\[data-reduced='true'\] \.sh-task\[data-cue='true'\][\s\S]*?animation: none !important/);
  const contrastIdx = modern.indexOf('@media (prefers-contrast: more)');
  assert.match(modern.slice(contrastIdx), /prefers-contrast: more[\s\S]*?\.sh-task\[data-cue='true'\]/);
  const forcedIdx = modern.indexOf('forced-colors LAST');
  assert.match(modern.slice(forcedIdx), /forced-colors: active[\s\S]*?\.sh-task\[data-cue='true'\]/);
});

test('shiritori HUD flashes cue when required changes; animationend clears; leave live clears', () => {
  const {view, state} = harness();
  view.update({...state, phase: 'intro', cards: []});
  const wrap = view.page.querySelector('.sh-task');
  assert.ok(wrap, 'sh-task mounted');
  assert.equal(wrap.dataset.cue, 'false');

  view.update({...state, phase: 'playing', required: 'り', last_word: 'しりとり'});
  assert.equal(wrap.dataset.cue, 'true', 'entering live cues initial required');
  const pulseEnter = wrap.dataset.pulse;
  const prompt = view.page.querySelector('.sh-prompt');
  assert.match(prompt.textContent, /「り」/);

  // Same required re-render: no pulse flip / stay cued until animationend.
  view.update({...state, phase: 'playing', required: 'り', last_word: 'しりとり', remaining: 19});
  assert.equal(wrap.dataset.pulse, pulseEnter, 'identical required does not restart pulse');

  wrap.emit('animationend', {target: wrap});
  assert.equal(wrap.dataset.cue, 'false');

  view.update({...state, phase: 'playing', required: 'ん', last_word: 'りんご', completed: 1});
  assert.equal(wrap.dataset.cue, 'true', 'required change re-cues');
  assert.match(prompt.textContent, /「ん」/);
  assert.notEqual(wrap.dataset.pulse, pulseEnter, 'pulse flips to restart CSS animation');
  const pulseChange = wrap.dataset.pulse;

  view.update({...state, phase: 'playing', required: 'ご', last_word: 'りんご', completed: 2});
  assert.equal(wrap.dataset.cue, 'true');
  assert.match(prompt.textContent, /「ご」/);
  assert.notEqual(wrap.dataset.pulse, pulseChange);

  view.update({...state, phase: 'paused', required: 'ご'});
  assert.equal(wrap.dataset.cue, 'false', 'leaving live clears cue');
});

test('shiritori HUD reduced-motion keeps static cue until next required or leave live', () => {
  const {view, state} = harness();
  view.update({...state, phase: 'playing', required: 'あ', last_word: 'スタート'});
  const wrap = view.page.querySelector('.sh-task');
  assert.equal(wrap.dataset.cue, 'true');
  // No animationend under reduced — cue stays until next change.
  view.update({...state, phase: 'playing', required: 'あ', last_word: 'スタート', remaining: 18});
  assert.equal(wrap.dataset.cue, 'true');
  view.update({...state, phase: 'playing', required: 'か', last_word: 'あか'});
  assert.equal(wrap.dataset.cue, 'true');
  assert.match(view.page.querySelector('.sh-prompt').textContent, /「か」/);
  view.update({...state, phase: 'finished', required: 'か', winner: 'you', history: []});
  assert.equal(wrap.dataset.cue, 'false');
});

test('shiritori HUD required cue wiring lives in shiritori-ui.js with animationend dismiss', () => {
  const js = fs.readFileSync(require.resolve('../shiritori-ui.js'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  assert.match(js, /flashRequiredCue/);
  assert.match(js, /clearRequiredCue/);
  assert.match(js, /prevRequiredKey/);
  assert.match(js, /dataset\.cue/);
  assert.match(js, /taskWrap\.addEventListener\('animationend'/);
  assert.doesNotMatch(js, /setTimeout|setInterval|innerHTML|fetch\(/);
  assert.match(player, /shiritori-ui\.css\?v=result-score-hierarchy-1/);
  assert.match(player, /shiritori-ui\.js\?v=result-score-hierarchy-1/);
  assert.match(player, /modern-ui\.css\?v=result-score-hierarchy-1/);
});


test('shiritori finished splits primary score vs secondary stats (hierarchy #73)', () => {
  const {view, state, doc} = harness();
  view.update({
    ...state,
    phase: 'finished',
    mode: 'solo',
    winner: 'you',
    total: 24,
    mistakes: 2,
    hints: 1,
    relinks: 1,
    history: [
      {word: 'りんご', icon: '🍎', owner: 'you', readings: ['りんご']},
      {word: 'ゴリラ', icon: '🦍', owner: 'you', readings: ['ごりら']},
    ],
    chain: {you: {best: 3, bonus: 1}, cpu: {best: 1, bonus: 0}},
  });
  const result = view.page.querySelector('.sh-result');
  assert.ok(result && result.hidden === false, 'result visible');
  const score = result.querySelector('.nr-result-score');
  const secondary = result.querySelector('.sh-result-secondary');
  assert.ok(score, 'primary score element present');
  assert.ok(secondary, 'secondary stats element present');
  assert.equal(score.textContent, '2 / 24');
  assert.match(secondary.textContent, /ミス2回/);
  assert.match(secondary.textContent, /ヒント2回/);
  assert.match(secondary.textContent, /つなぎ直し1回/);
  assert.match(secondary.textContent, /最大3連鎖/);
  // Must not glue primary into the secondary line.
  assert.ok(!secondary.textContent.includes('2 / 24'), 'secondary omits primary score');
  const retry = result.querySelectorAll('button').find(b => b.textContent === 'もう一度遊ぶ');
  assert.equal(doc.activeElement, retry, 'result entry focuses primary replay (#19)');
});

test('shiritori result score hierarchy CSS + cache-bust (#73)', () => {
  const sh = fs.readFileSync(require.resolve('../shiritori-ui.css'), 'utf8');
  const js = fs.readFileSync(require.resolve('../shiritori-ui.js'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  assert.match(js, /nr-result-score/);
  assert.match(js, /sh-result-secondary/);
  assert.match(sh, /\.sh-result-secondary \{/);
  assert.match(sh, /\.sh-result > \.nr-result-score/);
  assert.match(player, /shiritori-ui\.css\?v=result-score-hierarchy-1/);
  assert.match(player, /shiritori-ui\.js\?v=result-score-hierarchy-1/);
  assert.match(player, /modern-ui\.css\?v=result-score-hierarchy-1/);
});
