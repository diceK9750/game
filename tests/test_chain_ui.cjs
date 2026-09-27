const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

test('automatic chain gauges and character tiers work for both owners without buttons', () => {
  const E = (tag,cls='') => ({tag,className:cls,children:[],style:{},dataset:{},append(...c){this.children.push(...c);},setAttribute(k,v){this[k]=v;}});
  const add = (p,...c) => {p.append(...c);return p;};
  const calls=[];
  const window = {chainVoice:{play:(...args)=>calls.push(args)}};
  vm.runInNewContext(fs.readFileSync(require.resolve('../chain-ui.js'),'utf8'),{window});
  const portraits=[{image:E('div')},{image:E('div')}];
  const view=window.createTimedChainView({E,add,portraits});
  const chains={you:{count:4,tier:2,event:4,window:3.15,remaining:1.5},cpu:{count:7,tier:3,event:7,window:1.8,remaining:1.8,waiting:true}};
  view.update(chains,true);
  assert.match(view.root.children[0].children[0].textContent,/4連鎖.*HIGH COMBO/);
  assert.match(view.root.children[1].children[0].textContent,/7連鎖.*RUSH FEVER.*手番待ち/);
  assert.equal(portraits[1].image.style.backgroundPosition,'100% 0%');
  assert.equal(view.root.children[1].hidden,false);
  const burst=view.root.children[0].children[2];
  assert.equal(burst.hidden,true, 'initial snapshots must not replay an old celebration');
  chains.you={...chains.you,count:5,event:5};
  view.update(chains,true);
  assert.equal(burst.hidden,false);
  assert.match(burst.textContent,/YOU  5連鎖！.*HIGH COMBO/);
  const pulse=burst.dataset.pulse;
  view.update(chains,true);
  assert.equal(burst.dataset.pulse,pulse);
  chains.you={...chains.you,count:7,event:7,tier:3};
  view.update(chains,true);
  assert.match(burst.textContent,/RUSH FEVER/);
  assert.notEqual(burst.dataset.pulse,pulse);
  view.update(chains,false);
  assert.equal(view.root.children[1].hidden,true);
  view.update(chains,false,false);
  assert.equal(view.root.hidden,true);
  assert.equal(burst.hidden,true);
  const baseline=calls.length;
  view.update({you:{event:0,count:0}},false);
  view.update({you:{event:1,count:1}},false);
  assert.deepEqual(calls.at(-1),['you',1]);
  view.update({you:{event:2,count:2}},false,false,true);
  assert.deepEqual(calls.at(-1),['you',2]);
  view.update({you:{event:2,count:2}},false,false,true);
  assert.equal(calls.length,baseline+2);
  assert.equal(portraits[0].image.dataset.chainTier,'0');
  const html=fs.readFileSync(require.resolve('../player.html'),'utf8');
  assert.ok(html.indexOf('chain-ui.js')<html.indexOf('shiritori-ui.js'));
  const source=fs.readFileSync(require.resolve('../shiritori-ui.js'),'utf8');
  assert.ok(!source.includes('sh_combo_begin'));
});

test('reduced-motion holds chain burst longer for readability', () => {
  const fs = require('node:fs');
  const vm = require('node:vm');
  const src = fs.readFileSync(require.resolve('../chain-ui.js'),'utf8');
  assert.match(src, /motionReduced\(\) \? 2800 : 1000/);
  assert.match(src, /prefers-reduced-motion:\s*reduce/);
  assert.match(src, /data-reduced/);

  let now = 1_000_000;
  const E = (tag,cls='') => ({tag,className:cls,children:[],style:{},dataset:{},hidden:false,append(...c){this.children.push(...c);},setAttribute(k,v){this[k]=v;}});
  const add = (p,...c) => {p.append(...c);return p;};
  const sandbox = {
    window: {
      chainVoice: {play(){}},
      matchMedia: (q) => ({matches: /prefers-reduced-motion:\s*reduce/.test(String(q))}),
      createTimedChainView: null,
    },
    document: {getElementById: () => null},
    Date: {now: () => now},
  };
  vm.runInNewContext(src, sandbox);
  const portraits=[{image:E('div')},{image:E('div')}];
  const view=sandbox.window.createTimedChainView({E,add,portraits});
  view.update({you:{count:1,tier:1,event:0,window:4.5,remaining:4},cpu:{count:0,tier:0,event:0}}, true);
  now = 1_000_000;
  view.update({you:{count:3,tier:1,event:1,window:4.5,remaining:3.5},cpu:{count:0,tier:0,event:0}}, true);
  const burst=view.root.children[0].children[2];
  assert.equal(burst.hidden, false);
  now = 1_000_000 + 1200;
  view.update({you:{count:3,tier:1,event:1,window:4.5,remaining:3.0},cpu:{count:0,tier:0,event:0}}, true);
  assert.equal(burst.hidden, false, 'RM banner still visible past 1s default');
  now = 1_000_000 + 2900;
  view.update({you:{count:3,tier:1,event:1,window:4.5,remaining:2.0},cpu:{count:0,tier:0,event:0}}, true);
  assert.equal(burst.hidden, true, 'RM banner clears after 2.8s hold');
});

test('RUSH FEVER announces entry once, keeps pause, then clears on timeout, miss or finish', () => {
  const E = (tag, cls='') => ({tag,className:cls,children:[],style:{},dataset:{},hidden:false,
    append(...c){this.children.push(...c);},setAttribute(k,v){this[k]=v;}});
  const add = (p,...c) => {p.append(...c);return p;};
  const window = {chainVoice:{play(){}}};
  vm.runInNewContext(fs.readFileSync(require.resolve('../chain-ui.js'),'utf8'),{window});
  const portraits=[{image:E('div')},{image:E('div')}];
  const view=window.createTimedChainView({E,add,portraits});
  const notice=view.root.children[2];
  let writes=0, value='';
  Object.defineProperty(notice,'textContent',{get:()=>value,set:v=>{writes++;value=v;}});
  const side=(count,event=count) => ({count,event,tier:count>=7?3:count>=4?2:count>=2?1:0,remaining:1.2,window:1.8});
  view.update({you:side(6),cpu:side(0)},true);
  assert.equal(view.root.dataset.feverOwner,'');
  view.update({you:side(7),cpu:side(0)},true);
  assert.equal(view.root.dataset.feverOwner,'you');
  assert.match(value,/RUSH FEVER/);
  assert.equal(portraits[0].image.dataset.pose,'victory');
  assert.equal(portraits[1].image.dataset.pose,'frustrated');
  const entered=writes;
  view.update({you:side(8),cpu:side(0)},true);
  view.update({you:side(8),cpu:side(0)},true);
  assert.equal(writes,entered,'count 8 and repeated frames must not re-announce');
  view.update({you:side(8),cpu:side(0)},true,false);
  assert.equal(notice.textContent,'','pause conceals stale live copy');
  view.update({you:side(8),cpu:side(0)},true);
  assert.equal(writes,entered+1,'pause/resume must not re-announce');
  view.update({you:side(0),cpu:side(0)},true);
  assert.equal(view.root.dataset.feverOwner,'');
  assert.equal(notice.textContent,'');
  view.update({you:side(7,9),cpu:side(0)},true);
  assert.equal(writes,entered+2,'a new real chain may announce again');
  view.update({you:side(7,9),cpu:side(0)},true,false,true);
  assert.equal(view.root.dataset.feverOwner,'','finish removes FEVER treatment');
  view.update({you:side(0),cpu:side(7)},true);
  assert.equal(view.root.dataset.feverOwner,'cpu','same view supports a future CPU FEVER');
  assert.equal(portraits[1].image.dataset.pose,'victory');
});

test('HIGH, FEVER entry, active aura and each hit use a nonblocking fixed layer', () => {
  let now=1000, stingers=0;
  const E=(tag,cls='')=>({tag,className:cls,children:[],style:{},dataset:{},hidden:false,
    append(...c){this.children.push(...c);},setAttribute(k,v){this[k]=v;}});
  const add=(p,...c)=>{p.append(...c);return p;};
  const window={chainVoice:{play(){},stinger(){stingers++;}}};
  vm.runInNewContext(fs.readFileSync(require.resolve('../chain-ui.js'),'utf8'),{window,Date:{now:()=>now},document:{getElementById:()=>null}});
  const view=window.createTimedChainView({E,add,portraits:[{image:E('div')},{image:E('div')}]});
  const fx=view.root.children[3];
  const side=(count,event=count)=>({count,event,tier:count>=7?3:count>=4?2:count>=2?1:0,remaining:1.2,window:1.8});
  view.update({you:side(3),cpu:side(0)},true);
  view.update({you:side(4),cpu:side(0)},true);
  assert.equal(fx.dataset.phase,'high');
  assert.equal(fx.dataset.hit,'true');
  assert.equal(fx.children[2].children.length,16);
  view.update({you:side(7),cpu:side(0)},true);
  assert.equal(fx.dataset.phase,'entry');
  assert.equal(stingers,1);
  now+=900;
  view.update({you:side(7),cpu:side(0)},true);
  assert.equal(fx.dataset.phase,'active');
  view.update({you:side(8),cpu:side(0)},true);
  assert.equal(fx.dataset.hit,'true');
  view.update({you:side(8),cpu:side(0)},true,false);
  assert.equal(fx.dataset.phase,'none');
});

test('FEVER and PERFECT motion reduce to static, contained presentation', () => {
  const character=fs.readFileSync(require.resolve('../character-layout.css'),'utf8');
  const picture=fs.readFileSync(require.resolve('../shiritori-ui.css'),'utf8');
  assert.match(character,/\.timed-chains\[data-fever-owner='you'\]/);
  assert.match(character,/@media \(prefers-reduced-motion: reduce\)\s*\{\s*\.timed-chains \.timed-chain \{ animation: none !important;/);
  assert.match(character,/#modern-app\[data-reduced='true'\] \.timed-chains \.timed-chain \{ animation: none !important;/);
  assert.match(picture,/\.sh-result\[data-perfect='true'\]/);
  assert.match(picture,/@media \(prefers-reduced-motion: reduce\)[\s\S]*?\.sh-result\[data-perfect='true'\] :is\(h1,\.nr-result-score\)/);
  assert.match(picture,/#modern-app\[data-reduced='true'\] \.sh-result\[data-perfect='true'\] :is\(h1,\.nr-result-score\)/);
  assert.match(character,/\.chain-fx \{ position: fixed; inset: 0; z-index: 25; pointer-events: none;/);
  assert.match(picture,/\.sh-perfect-fx \{[^}]*pointer-events: none;/);
});

