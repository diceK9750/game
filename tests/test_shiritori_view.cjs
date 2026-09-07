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
  vm.runInNewContext(fs.readFileSync(require.resolve('../shiritori-ui.js'), 'utf8'), {window, document: doc});
  const view = window.createShiritoriView({section: (n, c) => E('section', c), E, add, button, portrait, command});
  const state = {phase: 'playing', turn: 'you', required: 'り', last_word: 'しりとり', remaining: 20, limit: 20,
    hints: 3, hint: null, selected: null, message: 'りからはじめよう', mistakes: 0, history: [], winner: null,
    mode:'battle', total:24, stock:12, completed:0, relinks:2, seen:[],
    cards: Array.from({length:12}, () => ({id:'apple', icon:'🍎', words:['りんご','くだもの'], owner:null}))};
  return {view, state, queue, doc};
}

test('shiritori renderer keeps 12 stable cards and sends explicit reading commands', () => {
  const {view, state, queue} = harness(); view.update(state);
  const cards = view.page.querySelectorAll('.sh-card'); assert.equal(cards.length, 12);
  cards[0].click(); assert.equal(queue[0].action, 'sh_card'); assert.equal(queue[0].value, 0);
  view.update({...state, selected:0});
  const options = view.page.querySelector('.sh-choices').querySelectorAll('button');
  assert.deepEqual(options.map(n => n.textContent), ['りんご', 'くだもの']);
  options[1].click(); assert.equal(queue[1].action, 'sh_word'); assert.equal(queue[1].value, 'くだもの');
  view.update({...state, selected:0, remaining:17, mistakes:1, message:'ちがうよ −3秒'});
  assert.equal(view.page.querySelectorAll('.sh-card')[0], cards[0]);
  assert.equal(cards[0].disabled, false);
  assert.equal(view.page.querySelector('.sh-choices').querySelectorAll('button')[0], options[0]);
});

test('pause conceals cards, CPU turn disables input, result exposes replay and history', () => {
  const {view, state} = harness();
  view.update({...state, turn:'cpu'});
  assert.ok(view.page.querySelectorAll('.sh-card').every(c => c.disabled));
  view.update({...state, phase:'paused', cards:[]});
  assert.equal(view.page.querySelector('.sh-stage').hidden, true);
  assert.equal(view.page.querySelector('.sh-overlay').hidden, true);
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
  const solo = {...state, mode:'solo', total:36, stock:24, phase:'intro'};
  view.update(solo);
  const counts = view.page.querySelector('.sh-counts').querySelectorAll('button');
  assert.deepEqual(counts.map(b => b.textContent), ['12枚','24枚','36枚']);
  counts[2].click(); assert.deepEqual(queue.pop(), {action:'sh_total', value:36});
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

test('used readings are labelled and disabled, while blocked solo exposes rescue', () => {
  const {view,state} = harness();
  view.update({...state, selected:0, seen:['くだもの']});
  const options = view.page.querySelector('.sh-choices').querySelectorAll('button');
  assert.equal(options[1].disabled, true);
  assert.match(options[1].textContent, /使用済み/);
  view.update({...state, mode:'solo', phase:'blocked', relinks:2});
  const rescue = view.page.querySelectorAll('button').find(b => b.textContent === 'つなぎ直す あと2回');
  assert.equal(rescue.hidden, false);
  assert.ok(view.page.querySelectorAll('.sh-card').every(b => b.disabled));
});
