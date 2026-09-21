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
  assert.match(view.root.children[0].children[0].textContent,/4連鎖.*SUPER/);
  assert.match(view.root.children[1].children[0].textContent,/7連鎖.*FEVER.*手番待ち/);
  assert.equal(portraits[1].image.style.backgroundPosition,'100% 0%');
  assert.equal(view.root.children[1].hidden,false);
  const burst=view.root.children[0].children[2];
  assert.equal(burst.hidden,true, 'initial snapshots must not replay an old celebration');
  chains.you={...chains.you,count:5,event:5};
  view.update(chains,true);
  assert.equal(burst.hidden,false);
  assert.match(burst.textContent,/YOU  5連鎖！.*SUPER/);
  const pulse=burst.dataset.pulse;
  view.update(chains,true);
  assert.equal(burst.dataset.pulse,pulse);
  chains.you={...chains.you,count:7,event:7,tier:3};
  view.update(chains,true);
  assert.match(burst.textContent,/FEVER/);
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

