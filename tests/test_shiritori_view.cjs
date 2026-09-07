const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function harness() {
  const doc = {activeElement: null};
  class Element {
    constructor(tag, cls = '', text = '') { this.tagName = tag.toUpperCase(); this.className = cls; this.textContent = text; this.children = []; this.style = {}; this.dataset = {}; this.events = {}; }
    append(...nodes) { this.children.push(...nodes); }
    replaceChildren(...nodes) { this.children = nodes; }
    setAttribute(key, val) { this[key] = val; }
    addEventListener(key, fn) { this.events[key] = fn; }
    focus() { doc.activeElement = this; }
    querySelectorAll(selector) { const all = this.children.flatMap(n => [n, ...n.querySelectorAll('*')]); return all.filter(n => selector === '*' || selector.split(',').some(s => s.trim().startsWith('.') ? n.className.split(' ').includes(s.trim().slice(1)) : n.tagName === s.trim().toUpperCase())); }
    querySelector(selector) { return this.querySelectorAll(selector)[0]; }
  }
  const E = (tag, cls, text) => new Element(tag, cls, text);
  const add = (parent, ...children) => { parent.append(...children); return parent; };
  const queue = [];
  const command = (action, value) => queue.push({action, value});
  const button = (text, action, value, cls) => { const b = E('button', cls, text); b.click = () => command(action, value); return b; };
  const portrait = () => { const image = E('div'); return {wrap: add(E('div'), image), image}; };
  const window = {};
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

test('new mode is shipped in Pages and loaded before its host renderer', () => {
  const html = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  assert.ok(html.indexOf('shiritori-ui.js') < html.indexOf('modern-ui.js'));
  const workflow = fs.readFileSync(require.resolve('../.github/workflows/pages.yml'), 'utf8');
  for (const name of ['shiritori.py', 'shiritori-ui.js', 'shiritori-ui.css']) assert.ok(workflow.includes(name));
});

test('solo setup offers deck counts, hides CPU, and permits immediate replacement selection', () => {
  const {view,state,queue} = harness();
  const solo = {...state, mode:'solo', total:36, stock:12, phase:'intro'};
  view.update(solo);
  const counts = view.page.querySelector('.sh-counts').querySelectorAll('button');
  assert.deepEqual(counts.map(b => b.textContent), ['12枚','24枚','36枚']);
  counts[2].click(); assert.deepEqual(queue.pop(), {action:'sh_total', value:36});
  assert.equal(view.page.querySelector('.sh-level-settings').hidden, true);
  solo.phase = 'playing'; view.update(solo);
  const card = view.page.querySelectorAll('.sh-card')[0];
  solo.cards[0] = {id:'cat',icon:'🐈',words:['ねこ','こねこ'],owner:null};
  solo.stock = 11; solo.completed = 1; solo.refilled = 0; solo.revision = 1;
  view.update(solo);
  assert.equal(view.page.querySelectorAll('.sh-card')[0], card);
  assert.equal(card.disabled, false);
  assert.equal(card.children[1].textContent, 'NEW');
  assert.equal(view.page.querySelector('.sh-stock').textContent, '山札 11枚');
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
