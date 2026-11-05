const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
function harness() {
  const window={}; vm.runInNewContext(fs.readFileSync(require.resolve('../shiritori-dictionary.js'),'utf8'),{window});
  const data=new Map(); const storage={getItem:k=>data.has(k)?data.get(k):null,setItem:(k,v)=>data.set(k,v)};
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

test('adding a reading keeps existing discoveries and allows the new one',()=>{
  const {window,storage,catalog,create}=harness();
  const before=create(); assert.equal(before.discover('cat','ねこ'),true);
  const extended=catalog.map(card=>card.id==='cat'?{...card,words:[...card.words,'にゃんこ']}:card);
  const after=window.createShiritoriCollection(storage); after.configure(extended);
  assert.equal(after.total,before.total+1); assert.equal(after.has('cat','ねこ'),true);
  assert.equal(after.discover('cat','にゃんこ'),true);
  const reloaded=window.createShiritoriCollection(storage); reloaded.configure(extended);
  assert.equal(reloaded.has('cat','ねこ'),true); assert.equal(reloaded.has('cat','にゃんこ'),true);
});

test('same-initial old and new readings can both be discovered in challenges',()=>{
  const {window,storage}=harness(), c=window.createShiritoriCollection(storage);
  c.configure([{id:'dog',words:['どうぶつ','ドッグ']},
               {id:'door',words:['ドア']},{id:'cat',words:['ねこ']}]);
  for(const expected of ['どうぶつ','ドッグ']) {
    const quiz=c.challenge(()=>0);
    assert.equal(quiz.card.id,'dog'); assert.equal(quiz.word,expected);
    assert.ok(!quiz.options.some(card=>card.id==='door'));
    assert.equal(c.discover(quiz.card.id,quiz.word),true);
  }
  const reloaded=window.createShiritoriCollection(storage); reloaded.configure(c.cards);
  assert.equal(reloaded.has('dog','どうぶつ'),true);
  assert.equal(reloaded.has('dog','ドッグ'),true);
});

test('n-ending reading remains discoverable through dictionary challenge',()=>{
  const {window,storage}=harness(), c=window.createShiritoriCollection(storage);
  c.configure([{id:'spoon',words:['スプーン']},{id:'cat',words:['ねこ']}]);
  const quiz=c.challenge(()=>0);
  assert.equal(quiz.word,'スプーン');
  assert.equal(c.discover(quiz.card.id,quiz.word),true);
  const reloaded=window.createShiritoriCollection(storage); reloaded.configure(c.cards);
  assert.equal(reloaded.has('spoon','スプーン'),true);
});


test('old catalog preserves discoveries from a concurrently open newer catalog',()=>{
  const {window,storage,data}=harness();
  const oldCatalog=[{id:'cat',words:['ねこ']},{id:'dog',words:['いぬ']}];
  const newCatalog=[{id:'cat',words:['ねこ','にゃー']},{id:'dog',words:['いぬ']}];
  const old=window.createShiritoriCollection(storage); old.configure(oldCatalog);
  const newer=window.createShiritoriCollection(storage); newer.configure(newCatalog);
  assert.equal(newer.discover('cat','にゃー'),true);
  assert.equal(old.discover('dog','いぬ'),true);
  const persisted=JSON.parse(data.get('number-rush.shiritori.dictionary.v1'));
  assert.ok(persisted.found.includes('cat:にゃー'));
  const loaded=window.createShiritoriCollection(storage); loaded.configure(newCatalog);
  assert.equal(loaded.has('cat','にゃー'),true);
  assert.equal(loaded.has('dog','いぬ'),true);
  assert.equal(old.count,1,'unknown entries do not inflate old catalog progress');
});

test('unknown saved entries survive writes and become visible if later supported',()=>{
  const {window,storage,data}=harness(), key='number-rush.shiritori.dictionary.v1';
  data.set(key,JSON.stringify({version:1,found:['future:よみ',null]}));
  const c=window.createShiritoriCollection(storage);
  c.configure([{id:'cat',words:['ねこ']}]);
  assert.equal(c.count,0);
  assert.equal(c.discover('cat','ねこ'),true);
  const saved=JSON.parse(data.get(key));
  assert.ok(saved.found.includes('future:よみ'));
  assert.ok(saved.found.includes(null));
  c.configure([{id:'cat',words:['ねこ']},{id:'future',words:['よみ']}]);
  assert.equal(c.has('future','よみ'),true);
  assert.equal(c.count,2);
});

test('unreadable or unsupported saved data is never overwritten on discovery',()=>{
  const {window,storage,data}=harness(), key='number-rush.shiritori.dictionary.v1';
  for(const raw of ['', '{broken',JSON.stringify({version:2,found:['future:よみ'],extra:'keep'})]) {
    data.set(key,raw);
    const c=window.createShiritoriCollection(storage); c.configure([{id:'cat',words:['ねこ']}]);
    assert.ok(c.warning);
    assert.equal(c.discover('cat','ねこ'),true);
    assert.equal(data.get(key),raw,'unreadable data remains byte-for-byte intact');
    assert.ok(c.warning);
    assert.equal(c.sync(),false);
    assert.equal(data.get(key),raw);
  }
});

test('a transient storage failure retries the same discovery without a new find',()=>{
  const {window,data}=harness(), key='number-rush.shiritori.dictionary.v1';
  let failed=false;
  const storage={getItem:k=>data.get(k)||null,setItem(k,v){if(!failed){failed=true;throw Error('temporary');}data.set(k,v);}};
  const c=window.createShiritoriCollection(storage); c.configure([{id:'cat',words:['ねこ']}]);
  assert.equal(c.discover('cat','ねこ'),true);
  assert.ok(c.warning); assert.equal(data.has(key),false);
  assert.equal(c.discover('cat','ねこ'),false,'a retry is not a second discovery');
  assert.equal(c.warning,'');
  const loaded=window.createShiritoriCollection(storage);loaded.configure([{id:'cat',words:['ねこ']}]);
  assert.equal(loaded.has('cat','ねこ'),true);
});

test('unreadable storage is not written and pending discoveries save after recovery',()=>{
  const {window,data}=harness(), key='number-rush.shiritori.dictionary.v1';
  data.set(key,JSON.stringify({version:1,found:['dog:いぬ']}));
  let blocked=true, writes=0;
  const storage={getItem(k){if(blocked)throw Error('temporary');return data.get(k)||null;},
    setItem(k,v){writes++;data.set(k,v);}};
  const catalog=[{id:'cat',words:['ねこ']},{id:'dog',words:['いぬ']}];
  const c=window.createShiritoriCollection(storage);c.configure(catalog);
  assert.equal(c.discover('cat','ねこ'),true);assert.equal(writes,0);
  blocked=false;assert.equal(c.sync(),true);assert.equal(writes,2);assert.equal(c.warning,'');
  const loaded=window.createShiritoriCollection(storage);loaded.configure(catalog);
  assert.equal(loaded.has('cat','ねこ'),true);assert.equal(loaded.has('dog','いぬ'),true);
});

test('merging a discovery from another tab invalidates dictionary rendering',()=>{
  const {create}=harness(), a=create(), b=create();
  const before=b.revision;
  assert.equal(a.discover('cat','ねこ'),true);
  assert.equal(b.discover('cat','ねこ'),false);
  assert.ok(b.revision>before);
  assert.equal(b.has('cat','ねこ'),true);
});

test('dictionary offers retry and saves a pending discovery after recovery',()=>{
  const {window,data,catalog}=harness(), key='number-rush.shiritori.dictionary.v1';
  let blocked=true;
  window.localStorage={getItem:k=>data.get(k)||null,setItem(k,v){if(blocked)throw Error('temporary');data.set(k,v);}};
  const elements=[];
  const E=(tag,cls='',text='')=>{const n={tagName:tag.toUpperCase(),className:cls,textContent:text,hidden:false,children:[],dataset:{},
    setAttribute(){},addEventListener(type,fn){(this.events||(this.events={}))[type]=fn;},focus(){},
    replaceChildren(...children){this.children=children;}};elements.push(n);return n;};
  const add=(parent,...children)=>{parent.children.push(...children);return parent;};
  const dict=window.createShiritoriDictionary({E,add,onClose(){}});dict.collection.configure(catalog);
  dict.collection.discover('cat','ねこ');dict.open();
  const retry=elements.find(e=>e.textContent==='保存を再試行');
  assert.ok(retry);assert.equal(retry.hidden,false);assert.equal(data.has(key),false);
  blocked=false;retry.events.click();assert.equal(retry.hidden,true);
  const loaded=window.createShiritoriCollection(window.localStorage);loaded.configure(catalog);
  assert.equal(loaded.has('cat','ねこ'),true);
});


test('protected union survives writes from the previously released implementation',()=>{
  const {window,storage,data}=harness(), key='number-rush.shiritori.dictionary.v1';
  const oldCatalog=[{id:'cat',words:['ねこ']},{id:'dog',words:['いぬ']}];
  const newCatalog=[{id:'cat',words:['ねこ','にゃー']},{id:'dog',words:['いぬ']}];
  // Reproduce the released implementation: it reads only the v1 key,
  // filters against its own catalog, then overwrites that key.
  const valid=new Set(['cat:ねこ','dog:いぬ']);
  const oldFound=new Set();
  function legacyDiscover(keyToAdd) {
    const raw=storage.getItem(key);
    if(raw) for(const k of JSON.parse(raw).found) if(valid.has(k)) oldFound.add(k);
    if(oldFound.has(keyToAdd)) return false;
    oldFound.add(keyToAdd);storage.setItem(key,JSON.stringify({version:1,found:[...oldFound]}));return true;
  }
  const newer=window.createShiritoriCollection(storage);newer.configure(newCatalog);
  assert.equal(newer.discover('cat','にゃー'),true);
  assert.equal(legacyDiscover('dog:いぬ'),true);
  assert.equal(JSON.parse(data.get(key)).found.includes('cat:にゃー'),false,'legacy still overwrites the old key');
  const loaded=window.createShiritoriCollection(storage);loaded.configure(newCatalog);
  assert.equal(loaded.has('cat','にゃー'),true,'protected copy restores newer discovery');
  assert.equal(loaded.has('dog','いぬ'),true,'legacy discovery is merged');
});

test('opening an existing collection protects it before an old tab writes',()=>{
  const {window,storage,data}=harness(), key='number-rush.shiritori.dictionary.v1';
  data.set(key,JSON.stringify({version:1,found:['cat:にゃー'],extra:'keep'}));
  const catalog=[{id:'cat',words:['にゃー']},{id:'dog',words:['いぬ']}];
  const c=window.createShiritoriCollection(storage);c.configure(catalog);
  data.set(key,JSON.stringify({version:1,found:['dog:いぬ']})); // legacy tab
  const loaded=window.createShiritoriCollection(storage);loaded.configure(catalog);
  assert.equal(loaded.has('cat','にゃー'),true);
  assert.equal(loaded.has('dog','いぬ'),true);
  assert.equal(loaded.discover('cat','にゃー'),false);
});

test('a failed original-key write remains recoverable from the protected copy',()=>{
  const {window,data}=harness(), key='number-rush.shiritori.dictionary.v1';
  const storage={getItem:k=>data.get(k)??null,setItem(k,v){if(k===key)throw Error('temporary');data.set(k,v);}};
  const catalog=[{id:'cat',words:['ねこ']}];
  const c=window.createShiritoriCollection(storage);c.configure(catalog);
  assert.equal(c.discover('cat','ねこ'),true);assert.ok(c.warning);
  assert.equal(data.has(key),false);
  const loaded=window.createShiritoriCollection(storage);loaded.configure(catalog);
  assert.equal(loaded.has('cat','ねこ'),true);
});

test('malformed protected data blocks overwriting either stored value',()=>{
  const {window,data,storage}=harness(), key='number-rush.shiritori.dictionary.v1';
  const shadow=key+'.protected';
  const primary=JSON.stringify({version:1,found:['dog:いぬ'],extra:'retain'});
  data.set(key,primary);data.set(shadow,'{broken');
  const c=window.createShiritoriCollection(storage);c.configure([{id:'cat',words:['ねこ']}]);
  assert.ok(c.warning);assert.equal(c.discover('cat','ねこ'),true);
  assert.equal(data.get(key),primary);assert.equal(data.get(shadow),'{broken');
});

test('unknown envelope fields survive a version-one collection write',()=>{
  const {window,data,storage}=harness(), key='number-rush.shiritori.dictionary.v1';
  data.set(key,JSON.stringify({version:1,found:['cat:ねこ'],extra:{keep:'yes'}}));
  const c=window.createShiritoriCollection(storage);c.configure([{id:'cat',words:['ねこ']},{id:'dog',words:['いぬ']}]);
  c.discover('dog','いぬ');
  assert.deepEqual(JSON.parse(data.get(key)).extra,{keep:'yes'});
});


test('readable protected copy remains visible when the original is corrupt',()=>{
  const {window,data,storage}=harness(), key='number-rush.shiritori.dictionary.v1';
  const shadow=key+'.protected', protectedRaw=JSON.stringify({version:1,found:['cat:ねこ']});
  data.set(key,'{broken');data.set(shadow,protectedRaw);
  const catalog=[{id:'cat',words:['ねこ']},{id:'dog',words:['いぬ']}];
  const c=window.createShiritoriCollection(storage);c.configure(catalog);
  assert.equal(c.has('cat','ねこ'),true);assert.ok(c.warning);
  assert.equal(c.discover('dog','いぬ'),true);
  assert.equal(data.get(key),'{broken');assert.equal(data.get(shadow),protectedRaw);
  data.set(key,JSON.stringify({version:1,found:[]}));
  assert.equal(c.sync(),true);
  const loaded=window.createShiritoriCollection(storage);loaded.configure(catalog);
  assert.equal(loaded.has('cat','ねこ'),true);assert.equal(loaded.has('dog','いぬ'),true);
});


test('an open dictionary refreshes after another tab saves without writing back',()=>{
  const {window,storage,data,catalog}=harness(), key='number-rush.shiritori.dictionary.v1';
  const listeners={};window.localStorage=storage;window.addEventListener=(name,fn)=>{listeners[name]=fn;};
  const elements=[];
  const E=(tag,cls='',text='')=>{const n={tagName:tag.toUpperCase(),className:cls,textContent:text,hidden:false,children:[],dataset:{},
    setAttribute(){},addEventListener(type,fn){(this.events||(this.events={}))[type]=fn;},focus(){},
    replaceChildren(...children){this.children=children;}};elements.push(n);return n;};
  const add=(parent,...children)=>{parent.children.push(...children);return parent;};
  const dict=window.createShiritoriDictionary({E,add,onClose(){}});dict.collection.configure(catalog);dict.open();
  const other=window.createShiritoriCollection(storage);other.configure(catalog);other.discover('cat','ねこ');
  const before=JSON.stringify([...data]);
  listeners.storage({key,storageArea:storage});
  const progress=elements.find(e=>e.className==='sh-dict-progress');
  assert.ok(progress.textContent.startsWith('1 / 9'));
  assert.equal(dict.collection.has('cat','ねこ'),true);
  assert.equal(JSON.stringify([...data]),before,'refresh does not cause a cross-tab write loop');
});



function actualSnapshotCatalog() {
  const {execFileSync}=require('node:child_process');
  const path=require('node:path');
  const root=path.resolve(__dirname,'..');
  const json=execFileSync('python',['-B','-c',
    "import json,shiritori;print(json.dumps(shiritori.ShiritoriRound().snapshot()['catalog'],ensure_ascii=False))"],
    {cwd:root,encoding:'utf8',env:{...process.env,PYTHONIOENCODING:'utf-8'}});
  return JSON.parse(json);
}
function oldSnapshot(filename) {
  const path=require('node:path');
  return JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures',filename),'utf8'));
}
function normalizedKey(id, word) {
  const normalized=word.normalize('NFC').replace(/[ァ-ヶ]/g,
    c=>String.fromCharCode(c.charCodeAt(0)-0x60));
  return id+':'+normalized;
}


const SEMANTIC_RETIRED = {
  apple:['すりおろしりんご'],
  ramune:['シャンパン','シャンペン','スパークリングワイン','コルク','ワイン','ワインボトル'],
  zucchini:['きゅうり','キューカンバー','ピクルス','つけもの'],
  top:['うずまき','スパイラル','うず','らせん','うずまきもよう',
       'サイクロン','ハリケーン','たいふう','たつまき','トルネード'],
  blocks:['れんが','ブリック','レンガづみ','レンガブロック','かべ'],
  parsley:['バジル','ミント']
};
const semanticRetiredKeys = new Set(Object.entries(SEMANTIC_RETIRED)
  .flatMap(([id,words])=>words.map(word=>normalizedKey(id,word))));
const unrelatedLegacyKeys = new Set([...semanticRetiredKeys, normalizedKey('blocks','レンガのかべ')]);

test('real 817, 829 and 759-reading saves preserve old keys without crediting unrelated readings',()=>{
  const current=actualSnapshotCatalog();
  assert.equal(current.length,81);
  assert.equal(current.reduce((n,card)=>n+card.words.length,0),731);
  assert.equal(current.reduce((n,card)=>n+Object.keys(card.legacy).length,0),73);
  assert.equal(semanticRetiredKeys.size,28);
  const byId=new Map(current.map(card=>[card.id,card]));
  assert.equal(byId.get('blocks').legacy['レンガのかべ'],null);
  assert.equal(byId.get('lavender').legacy['ヒヤシンスのはな'],'ヒヤシンス');
  assert.equal(byId.get('paint').legacy['えのぐのパレット'],'パレット');
  assert.equal(byId.get('plate').legacy['フォークとナイフ'],'フォーク');
  for(const [filename, expectedCount] of [
    ['shiritori-catalog-ad2c423.json',817],
    ['shiritori-catalog-pre-particle.json',829],
    ['shiritori-catalog-pre-semantic.json',759],
  ]) {
    const baseline=oldSnapshot(filename);
    const oldKeys=baseline.flatMap(card=>card.words.map(word=>normalizedKey(card.id,word)));
    assert.equal(oldKeys.length,expectedCount);
    assert.equal(new Set(oldKeys).size,expectedCount);
    const {window,storage,data}=harness(),key='number-rush.shiritori.dictionary.v1';
    data.set(key,JSON.stringify({version:1,found:oldKeys,extra:'preserved'}));
    const collection=window.createShiritoriCollection(storage);
    collection.configure(current);
    assert.equal(collection.total,731);
    const expectedFound=new Set();
    for(const card of baseline) {
      const now=byId.get(card.id);
      assert.ok(now);
      for(const word of card.words) {
        const oldKey=normalizedKey(card.id,word);
        if(now.words.some(w=>normalizedKey(card.id,w)===oldKey)) {
          expectedFound.add(oldKey);
          assert.equal(collection.has(card.id,word),true);
        } else {
          assert.equal(collection.has(card.id,word),false,'retired reading remains hidden');
          const replacement=now.legacy[word];
          if(typeof replacement==='string') {
            const target=normalizedKey(card.id,replacement);
            expectedFound.add(target);
            assert.equal(collection.has(card.id,replacement),true,'valid grammatical equivalent is credited');
          } else {
            assert.ok(unrelatedLegacyKeys.has(oldKey),card.id+':'+word+' is an unexpected uncredited retirement');
          }
        }
      }
    }
    assert.equal(collection.count,expectedFound.size);
    const protectedInitial=JSON.parse(data.get(key+'.protected'));
    const protectedKeys=new Set(protectedInitial.found);
    for(const oldKey of oldKeys) assert.ok(protectedKeys.has(oldKey),filename+': '+oldKey);
    assert.equal(protectedInitial.extra,'preserved');
    const newlyAdded=[['curry','ごはんりょうり'],['riceball','ごはんりょうり'],
                 ['lavender','むらさき']];
    for(const [id,word] of newlyAdded) {
      assert.ok(byId.get(id).words.includes(word));
      assert.equal(collection.has(id,word),oldKeys.includes(normalizedKey(id,word)),
        id+':'+word+' reflects whether the old version had recorded it');
    }
    let newFinds=0;
    while(collection.count<collection.total) {
      const quiz=collection.challenge(()=>0);
      assert.ok(quiz);
      assert.ok(byId.get(quiz.card.id).words.includes(quiz.word));
      assert.equal(collection.discover(quiz.card.id,quiz.word),true);
      assert.ok(++newFinds<=731,'challenge must progress');
    }
    if(expectedCount===829) assert.equal(newFinds,3,'three new readings follow the 829-key migration');
    if(expectedCount===759) assert.equal(newFinds,0,'all still-valid 759 keys were already found');
    assert.equal(collection.challenge(),null);
    const reloaded=window.createShiritoriCollection(storage);
    reloaded.configure(current);
    assert.equal(reloaded.count,731);
    for(const card of current) for(const word of card.words)
      assert.equal(reloaded.has(card.id,word),true);
    const protectedFinal=new Set(JSON.parse(data.get(key+'.protected')).found);
    for(const oldKey of oldKeys) assert.ok(protectedFinal.has(oldKey),'after reload: '+oldKey);
  }
});

test('each semantically unrelated old discovery stays preserved without inventing a new discovery',()=>{
  const current=actualSnapshotCatalog(), byId=new Map(current.map(card=>[card.id,card]));
  assert.equal(semanticRetiredKeys.size,28);
  for(const [id,words] of Object.entries(SEMANTIC_RETIRED)) {
    for(const word of words) {
      const oldKey=normalizedKey(id,word), card=byId.get(id);
      assert.ok(card);
      assert.equal(card.words.some(w=>normalizedKey(id,w)===oldKey),false,oldKey+' is not offered');
      assert.notEqual(typeof card.legacy[word],'string',oldKey+' has no unrelated alias');
      const {window,storage,data}=harness(),key='number-rush.shiritori.dictionary.v1';
      data.set(key,JSON.stringify({version:1,found:[oldKey]}));
      const c=window.createShiritoriCollection(storage);c.configure(current);
      assert.equal(c.total,731);
      assert.equal(c.count,0,oldKey+' must not count another meaning');
      assert.equal(c.has(id,word),false,oldKey+' is not discoverable');
      assert.ok(JSON.parse(data.get(key+'.protected')).found.includes(oldKey),oldKey+' was retained');
      const reloaded=window.createShiritoriCollection(storage);reloaded.configure(current);
      assert.equal(reloaded.count,0,oldKey+' remains uncredited on reload');
      assert.ok(JSON.parse(data.get(key+'.protected')).found.includes(oldKey),oldKey+' survived reload');
    }
  }
});

test('every grammatical legacy retains its key and credits only a semantically valid replacement',()=>{
  const current=actualSnapshotCatalog();
  let migrated=0, unrelated=0;
  for(const card of current) for(const [oldWord,replacement] of Object.entries(card.legacy)) {
    const {window,storage,data}=harness(),key='number-rush.shiritori.dictionary.v1';
    const oldKey=normalizedKey(card.id,oldWord);
    data.set(key,JSON.stringify({version:1,found:[oldKey]}));
    const c=window.createShiritoriCollection(storage);c.configure(current);
    if(typeof replacement==='string') {
      assert.equal(c.count,1,oldKey);
      assert.equal(c.has(card.id,replacement),true,oldKey);
      migrated++;
    } else {
      assert.equal(card.id,'blocks');
      assert.equal(oldWord,'レンガのかべ');
      assert.equal(c.count,0,oldKey+' is unrelated to toy blocks');
      unrelated++;
    }
    assert.equal(c.has(card.id,oldWord),false,oldKey);
    assert.ok(JSON.parse(data.get(key+'.protected')).found.includes(oldKey),oldKey);
    const loaded=window.createShiritoriCollection(storage);loaded.configure(current);
    assert.equal(loaded.count,typeof replacement==='string'?1:0,oldKey);
  }
  assert.equal(migrated,72);
  assert.equal(unrelated,1);
});

test('retired readings credit only their same-picture replacement and retain the original',()=>{
  const {window,storage,data}=harness(), key='number-rush.shiritori.dictionary.v1';
  const original='radish:にんじんのは';
  data.set(key,JSON.stringify({version:1,found:[original,'other:にんじんのは','future:よみ']}));
  const cards=[{id:'radish',words:['にんじん','やさい'],legacy:{'にんじんのは':'にんじん'}},
               {id:'other',words:['にんじん']}];
  const c=window.createShiritoriCollection(storage);c.configure(cards);
  assert.equal(c.has('radish','にんじん'),true);
  assert.equal(c.has('radish','にんじんのは'),false);
  assert.equal(c.has('other','にんじん'),false,'unknown same word on a different picture is not mapped');
  assert.equal(c.count,1);
  const shadow=JSON.parse(data.get(key+'.protected'));
  assert.ok(shadow.found.includes(original),'the historical key remains recoverable');
  assert.ok(shadow.found.includes('radish:にんじん'));
  assert.ok(shadow.found.includes('other:にんじんのは'));
  assert.equal(c.discover('radish','やさい'),true);
  const saved=JSON.parse(data.get(key));
  assert.ok(saved.found.includes(original),'later writes keep the retired reading');
  assert.ok(saved.found.includes('future:よみ'));
  const reloaded=window.createShiritoriCollection(storage);reloaded.configure(cards);
  assert.equal(reloaded.count,2);
  assert.equal(reloaded.has('radish','にんじん'),true);
  assert.equal(reloaded.has('radish','やさい'),true);
  assert.ok(!reloaded.cards.some(card=>card.words.includes('にんじんのは')));
});

test('retired discoveries collapsing into one replacement count only once',()=>{
  const {window,storage,data}=harness(),key='number-rush.shiritori.dictionary.v1';
  data.set(key,JSON.stringify({version:1,found:['radish:にんじんのは','radish:にんじんのね','radish:にんじん']}));
  const cards=[{id:'radish',words:['にんじん'],legacy:{
    'にんじんのは':'にんじん','にんじんのね':'にんじん'}}];
  const c=window.createShiritoriCollection(storage);c.configure(cards);
  assert.equal(c.count,1);assert.equal(c.total,1);
  assert.equal(c.challenge(),null);
  const shadow=JSON.parse(data.get(key+'.protected'));
  assert.ok(shadow.found.includes('radish:にんじんのは'));
  assert.ok(shadow.found.includes('radish:にんじんのね'));
  assert.ok(shadow.found.includes('radish:にんじん'));
});

test('invalid migration metadata cannot credit an invented or different-picture reading',()=>{
  const {window,storage,data}=harness(),key='number-rush.shiritori.dictionary.v1';
  data.set(key,JSON.stringify({version:1,found:['radish:きゅうよみ','other:きゅうよみ','radish:にんじん']}));
  const cards=[{id:'radish',words:['にんじん'],legacy:{
    'きゅうよみ':'ねこ','にんじん':'でたらめ','ふせい':null}},
    {id:'other',words:['ねこ']}];
  const c=window.createShiritoriCollection(storage);c.configure(cards);
  assert.equal(c.count,1);assert.equal(c.has('radish','にんじん'),true);
  assert.equal(c.has('other','ねこ'),false);
  assert.ok(JSON.parse(data.get(key+'.protected')).found.includes('radish:きゅうよみ'));
});

test('a corrupt primary prevents migration writes while the protected copy stays visible',()=>{
  const {window,storage,data}=harness(),key='number-rush.shiritori.dictionary.v1';
  const backup=JSON.stringify({version:1,found:['radish:にんじんのは']});
  data.set(key,'{broken');data.set(key+'.protected',backup);
  const cards=[{id:'radish',words:['にんじん','やさい'],legacy:{'にんじんのは':'にんじん'}}];
  const c=window.createShiritoriCollection(storage);c.configure(cards);
  assert.equal(c.has('radish','にんじん'),true);assert.ok(c.warning);
  assert.equal(c.discover('radish','やさい'),true);
  assert.equal(data.get(key),'{broken');assert.equal(data.get(key+'.protected'),backup);
  data.set(key,JSON.stringify({version:1,found:[]}));
  assert.equal(c.sync(),true);
  const reloaded=window.createShiritoriCollection(storage);reloaded.configure(cards);
  assert.equal(reloaded.has('radish','にんじん'),true);
  assert.equal(reloaded.has('radish','やさい'),true);
  assert.ok(JSON.parse(data.get(key)).found.includes('radish:にんじんのは'));
});

test('an old open tab discovery refreshes a new dictionary without losing the retired key',()=>{
  const {window,storage,data}=harness(),key='number-rush.shiritori.dictionary.v1';
  const oldCards=[{id:'radish',words:['にんじん','にんじんのは']}];
  const newCards=[{id:'radish',words:['にんじん'],legacy:{'にんじんのは':'にんじん'}}];
  const old=window.createShiritoriCollection(storage);old.configure(oldCards);
  const listeners={};window.localStorage=storage;window.addEventListener=(name,fn)=>{listeners[name]=fn;};
  const elements=[];
  const E=(tag,cls='',text='')=>{const n={tagName:tag.toUpperCase(),className:cls,textContent:text,hidden:false,children:[],dataset:{},
    setAttribute(){},addEventListener(type,fn){(this.events||(this.events={}))[type]=fn;},focus(){},
    replaceChildren(...children){this.children=children;}};elements.push(n);return n;};
  const add=(parent,...children)=>{parent.children.push(...children);return parent;};
  const dict=window.createShiritoriDictionary({E,add,onClose(){}});
  dict.collection.configure(newCards);dict.open();
  assert.equal(dict.collection.count,0);
  assert.equal(old.discover('radish','にんじんのは'),true);
  const before=JSON.stringify([...data]);
  listeners.storage({key,storageArea:storage});
  assert.equal(dict.collection.has('radish','にんじん'),true);
  assert.equal(dict.collection.has('radish','にんじんのは'),false);
  assert.equal(dict.collection.count,1);
  assert.ok(elements.find(e=>e.className==='sh-dict-progress').textContent.startsWith('1 / 1'));
  assert.equal(JSON.stringify([...data]),before,'storage refresh only reads, avoiding event loops');
  assert.ok(JSON.parse(data.get(key)).found.includes('radish:にんじんのは'));
  dict.collection.sync();
  const reloaded=window.createShiritoriCollection(storage);reloaded.configure(newCards);
  assert.equal(reloaded.has('radish','にんじん'),true);
  assert.ok(JSON.parse(data.get(key+'.protected')).found.includes('radish:にんじんのは'));
});

test('an unsaved retired discovery survives in-memory reconfiguration and retry',()=>{
  const {window,data}=harness(),key='number-rush.shiritori.dictionary.v1';
  let offline=true;
  const storage={getItem(k){if(offline)throw Error('offline');return data.has(k)?data.get(k):null;},
    setItem(k,v){if(offline)throw Error('offline');data.set(k,v);}};
  const c=window.createShiritoriCollection(storage);
  c.configure([{id:'radish',words:['にんじんのは']}]);
  assert.equal(c.discover('radish','にんじんのは'),true);assert.ok(c.warning);
  const cards=[{id:'radish',words:['にんじん'],legacy:{'にんじんのは':'にんじん'}}];
  c.configure(cards);
  assert.equal(c.has('radish','にんじん'),true);assert.equal(c.count,1);
  offline=false;assert.equal(c.sync(),true);
  const loaded=window.createShiritoriCollection(storage);loaded.configure(cards);
  assert.equal(loaded.has('radish','にんじん'),true);
  assert.ok(JSON.parse(data.get(key)).found.includes('radish:にんじんのは'));
});


test('old tab discovery of a semantically retired reading is retained but never credited as a different object',()=>{
  const {window,storage,data}=harness(), key='number-rush.shiritori.dictionary.v1';
  const oldCards=[{id:'ramune',words:['ラムネ','ワイン']}];
  const newCards=[{id:'ramune',words:['ラムネ'],legacy:{}}];
  const old=window.createShiritoriCollection(storage);
  const current=window.createShiritoriCollection(storage);
  old.configure(oldCards);current.configure(newCards);
  assert.equal(old.discover('ramune','ワイン'),true);
  assert.equal(current.refresh(),true);
  assert.equal(current.count,0,'wine must not credit ramune');
  assert.equal(current.has('ramune','ラムネ'),false);
  assert.equal(current.sync(),true);
  assert.ok(JSON.parse(data.get(key+'.protected')).found.includes('ramune:わいん'));
  assert.equal(current.discover('ramune','ラムネ'),true);
  const loaded=window.createShiritoriCollection(storage);loaded.configure(newCards);
  assert.equal(loaded.count,1);
  assert.equal(loaded.has('ramune','ラムネ'),true);
  assert.ok(JSON.parse(data.get(key+'.protected')).found.includes('ramune:わいん'));
});


test('fork-and-knife legacy credits the named fork and never the unrelated plate',()=>{
  const current=actualSnapshotCatalog(), {window,storage,data}=harness();
  const key='number-rush.shiritori.dictionary.v1';
  const oldKey=normalizedKey('plate','フォークとナイフ');
  const card=current.find(c=>c.id==='plate');
  assert.equal(card.legacy['フォークとナイフ'],'フォーク');
  data.set(key,JSON.stringify({version:1,found:[oldKey]}));
  const collection=window.createShiritoriCollection(storage);
  collection.configure(current);
  assert.equal(collection.count,1);
  assert.equal(collection.has('plate','フォーク'),true);
  assert.equal(collection.has('plate','おさら'),false,'a plate was not discovered');
  assert.ok(JSON.parse(data.get(key+'.protected')).found.includes(oldKey));
  const reloaded=window.createShiritoriCollection(storage);reloaded.configure(current);
  assert.equal(reloaded.has('plate','フォーク'),true);
  assert.equal(reloaded.has('plate','おさら'),false);
  assert.ok(JSON.parse(data.get(key+'.protected')).found.includes(oldKey));
});

test('dictionary retries a temporarily unavailable localStorage getter without losing discoveries',()=>{
  const {window,storage,data}=harness();
  const key='number-rush.shiritori.dictionary.v1';
  data.set(key,JSON.stringify({version:1,found:['dog:いぬ','retired:よみ'],future:'keep'}));
  data.set(key+'.protected',JSON.stringify({version:1,found:['dog:いぬ','legacy:よみ']}));
  let blocked=true;
  Object.defineProperty(window,'localStorage',{get(){if(blocked)throw Error('temporarily denied');return storage;}});
  const E=(tag,cls='',text='')=>({tagName:tag.toUpperCase(),className:cls,textContent:text,
    hidden:false,children:[],dataset:{},setAttribute(){},addEventListener(){},focus(){},replaceChildren(){}});
  const add=(parent,...children)=>{parent.children.push(...children);return parent;};
  const dict=window.createShiritoriDictionary({E,add,onClose(){}});
  const catalog=[{id:'cat',words:['ねこ']},{id:'dog',words:['いぬ']}];
  dict.collection.configure(catalog);
  assert.equal(dict.collection.discover('cat','ねこ'),true);
  assert.ok(dict.collection.warning);
  assert.deepEqual(JSON.parse(data.get(key)).found,['dog:いぬ','retired:よみ']);
  blocked=false;
  assert.equal(dict.collection.sync(),true);
  assert.equal(dict.collection.warning,'');
  for(const storageKey of [key,key+'.protected']) {
    const saved=JSON.parse(data.get(storageKey));
    for(const found of ['cat:ねこ','dog:いぬ','retired:よみ','legacy:よみ']) assert.ok(saved.found.includes(found));
    assert.equal(saved.future,'keep');
  }
  const reloaded=window.createShiritoriCollection(storage);reloaded.configure(catalog);
  assert.equal(reloaded.has('cat','ねこ'),true);
  assert.equal(reloaded.has('dog','いぬ'),true);
});
