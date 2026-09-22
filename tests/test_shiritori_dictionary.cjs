const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
function harness() {
  const window={}; vm.runInNewContext(fs.readFileSync(require.resolve('../shiritori-dictionary.js'),'utf8'),{window});
  const data=new Map(); const storage={getItem:k=>data.get(k)||null,setItem:(k,v)=>data.set(k,v)};
  const catalog=[{id:'apple',icon:'🍎',words:['りんご','くだもの','たべもの']},{id:'orange',icon:'🍊',words:['みかん','くだもの','ふるーつ']},{id:'cat',icon:'🐈',words:['ねこ','どうぶつ','ぺっと']}];
  const create=()=>{const c=window.createShiritoriCollection(storage);c.configure(catalog);return c;};
  return {window,storage,data,catalog,create};
}
test('collection persists exact picture/word pairs and rejects invented words',()=>{
  const {create}=harness(), c=create();
  assert.equal(c.total,9); assert.equal(c.count,0);
  assert.equal(c.discover('apple','くだもの'),true);
  assert.equal(c.discover('apple','くだもの'),false);
  assert.equal(c.discover('missing','くだもの'),false);
  assert.equal(c.discover('apple','でたらめ'),false);
  assert.equal(c.has('orange','くだもの'),false);
  const reloaded=create(); assert.equal(reloaded.count,1); assert.equal(reloaded.has('apple','くだもの'),true);
});
test('corrupt or denied storage does not crash and exposes a warning',()=>{
  const {window,catalog,storage,data}=harness();
  data.set('number-rush.shiritori.dictionary.v1','{broken');
  const c=window.createShiritoriCollection(storage); c.configure(catalog); assert.ok(c.warning);
  const blocked=window.createShiritoriCollection({getItem(){throw Error();},setItem(){throw Error();}});
  blocked.configure(catalog); assert.equal(blocked.discover('apple','りんご'),true);
  assert.equal(blocked.count,1); assert.ok(blocked.warning);
});
test('concurrent collections merge previous saves and ignore unknown saved entries',()=>{
  const {create,data}=harness();
  data.set('number-rush.shiritori.dictionary.v1',JSON.stringify({version:1,found:['bogus:key']}));
  const a=create(), b=create(); assert.equal(a.count,0);
  a.discover('apple','りんご'); b.discover('cat','ねこ');
  assert.equal(create().count,2);
});
test('discovery challenges can complete every reading including n endings without ambiguous panels',()=>{
  const {create}=harness(),c=create();
  for(let i=0;i<c.total;i++) {
    const quiz=c.challenge(()=>0);
    assert.ok(quiz); assert.equal(c.has(quiz.card.id,quiz.word),false);
    assert.equal(quiz.options.filter(card=>card.words.some(w=>w[0]===quiz.word[0])).length,1);
    c.discover(quiz.card.id,quiz.word);
  }
  assert.equal(c.count,c.total); assert.equal(c.has('orange','みかん'),true); assert.equal(c.challenge(),null);
});
test('dictionary ships before its consumer and is included in Pages',()=>{
  const html=fs.readFileSync(require.resolve('../player.html'),'utf8');
  assert.ok(html.indexOf('shiritori-dictionary.js')<html.indexOf('shiritori-ui.js'));
  assert.ok(fs.readFileSync(require.resolve('../.github/workflows/pages.yml'),'utf8').includes('shiritori-dictionary.js'));
});

test('dictionary close() mirrors back and is idempotent',()=>{
  const {window,catalog}=harness();
  const els=[];
  const E=(tag,cls='',text='')=>{
    const n={tagName:String(tag).toUpperCase(),className:cls,textContent:text,hidden:false,children:[],
      style:{},dataset:{},attributes:{},
      setAttribute(k,v){this.attributes[k]=v;},getAttribute(k){return this.attributes[k];},
      addEventListener(type,fn){(this.events||(this.events={}))[type]=fn;},
      focus(){n._focused=true;},click(){this.events?.click?.();},
      replaceChildren(...kids){this.children=kids;},
      querySelector(){return null;},querySelectorAll(){return [];},
    };
    els.push(n); return n;
  };
  const add=(parent,...kids)=>{for(const k of kids){parent.children.push(k); if(k&&typeof k==='object')k.parent=parent;} return parent;};
  let closed=0;
  const dict=window.createShiritoriDictionary({E,add,onClose(){closed++;}});
  dict.collection.configure(catalog);
  dict.open();
  assert.equal(dict.page.hidden,false);
  dict.close();
  assert.equal(dict.page.hidden,true);
  assert.equal(closed,1,'close invokes onClose once');
  dict.close();
  assert.equal(closed,1,'second close is idempotent');
});

test('kana spelling migration preserves old discoveries and does not double count',()=>{
  const {window,storage,data}=harness();
  data.set('number-rush.shiritori.dictionary.v1',JSON.stringify({version:1,found:[
    'gorilla:ごりら','gorilla:ゴリラ','apple:ふるーつ','unknown:ごりら',null]}));
  const c=window.createShiritoriCollection(storage);
  c.configure([{id:'gorilla',words:['ゴリラ']},{id:'apple',words:['りんご','フルーツ','しんしゅうりんご']}]);
  assert.equal(c.count,2);
  assert.equal(c.has('gorilla','ゴリラ'),true);
  assert.equal(c.has('apple','フルーツ'),true);
  assert.equal(c.discover('gorilla','ごりら'),false);
  assert.equal(c.discover('apple','しんしゅうりんご'),true);
  assert.equal(c.count,3);
  assert.equal(c.cards[0].words[0],'ゴリラ');
  const reloaded=window.createShiritoriCollection(storage); reloaded.configure(c.cards);
  assert.equal(reloaded.count,3);
});

test('dictionary challenge excludes same-head decoys across kana scripts',()=>{
  const {window,storage}=harness();
  const c=window.createShiritoriCollection(storage);
  c.configure([{id:'tomato',words:['トマト']},{id:'bird',words:['とり']},{id:'apple',words:['りんご']}]);
  const quiz=c.challenge(()=>0);
  assert.equal(quiz.word,'トマト');
  assert.ok(!quiz.options.some(card=>card.id==='bird'));
});
