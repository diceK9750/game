/* Collection keys are picture + reading: shared category words count per picture. */
(function () {
  'use strict';
  const KEY = 'number-rush.shiritori.dictionary.v1';
  const PROTECTED_KEY = 'number-rush.shiritori.dictionary.v1.protected';
  // Stable pronunciation keys preserve v1 collections across spelling updates.
  // Match Python normalize_reading; boundary small-kana folding is separate.
  const normalize = word => word.normalize('NFC').replace(/[ァ-ヶ]/g, c => String.fromCharCode(c.charCodeAt(0)-0x60));
  const head = word => normalize(word)[0]?.replace(/[ゃゅょぁぃぅぇぉっゎ]/g, c => 'やゆよあいうえおつわ'['ゃゅょぁぃぅぇぉっゎ'.indexOf(c)]);
  const keyOf = (id, word) => `${id}:${normalize(word)}`;
  window.createShiritoriCollection = function (storage) {
    let catalog = [], valid = new Set(), legacy = new Map(), found = new Set(), warning = '', revision = 0, dirty = false;
    let primaryRaw = null, protectedRaw = null, primaryEnvelope = {}, protectedEnvelope = {};
    // Preserve discoveries not present in this catalog and protect them from
    // older versions that only know the original storage key.
    const retained = new Map();
    function canonicalSavedKey(value) {
      if (typeof value !== 'string' || !value.includes(':')) return null;
      const split = value.indexOf(':');
      return keyOf(value.slice(0, split), value.slice(split + 1));
    }
    function readEnvelope(raw) {
      if (raw == null) return {};
      const saved = JSON.parse(raw);
      if (saved?.version !== 1 || !Array.isArray(saved.found)) throw Error('format');
      return saved;
    }
    function mergeSaved() {
      function read(key) {
        try {
          const raw = storage.getItem(key);
          return {raw, data:readEnvelope(raw), ok:true};
        } catch (_) { return {raw:null, data:{}, ok:false}; }
      }
      const primary = read(KEY), protectedData = read(PROTECTED_KEY);
      primaryRaw = primary.raw; protectedRaw = protectedData.raw;
      primaryEnvelope = primary.data; protectedEnvelope = protectedData.data;
      let changed = false;
      // A valid protected copy can still be displayed when the original is
      // unreadable. No writes occur until both stored values are readable.
      for (const savedKey of [...(primary.data.found || []), ...(protectedData.data.found || [])]) {
        const key = canonicalSavedKey(savedKey);
        if (key !== null && valid.has(key)) {
          if (!found.has(key)) { found.add(key); changed = true; }
        } else {
          // Keep the original discovery for rollback or an older open tab.
          retained.set(JSON.stringify(savedKey), savedKey);
          // Only explicitly retired readings may credit a valid reading on
          // the same picture. Unknown future keys remain opaque and intact.
          const replacement = key !== null ? legacy.get(key) : null;
          if (replacement && !found.has(replacement)) {
            found.add(replacement); changed = true;
          }
        }
      }
      if (changed) revision++;
      if (!primary.ok || !protectedData.ok) {
        warning = '保存データを読み込めません。記録を保護してこのページ内で収集を続けます。';
        return false;
      }
      return true;
    }
    function entries() {
      const unknown = [...retained.values()].filter(value => {
        const key = canonicalSavedKey(value);
        return key === null || !valid.has(key);
      });
      return [...found, ...unknown];
    }
    function protectedText(values) {
      return JSON.stringify({...primaryEnvelope, ...protectedEnvelope, version:1, found:values});
    }
    function protectExisting() {
      if (!primaryRaw && !protectedRaw) return true;
      const value = protectedText(entries());
      if (value === protectedRaw) return true;
      try {
        storage.setItem(PROTECTED_KEY, value);
        protectedRaw = value; protectedEnvelope = JSON.parse(value);
        return true;
      } catch (_) {
        dirty = true;
        warning = '保存できません。収集はこのページを閉じるまで有効です。';
        return false;
      }
    }
    function savePending() {
      if (!dirty || !mergeSaved()) return !dirty;
      const values = entries();
      try {
        // Store the protected union first. If the old key write later fails,
        // current versions can still recover the discovery on reload.
        storage.setItem(PROTECTED_KEY, protectedText(values));
        storage.setItem(KEY, JSON.stringify({...protectedEnvelope, ...primaryEnvelope, version:1, found:values}));
        dirty = false; warning = ''; return true;
      } catch (_) {
        warning = '保存できません。収集はこのページを閉じるまで有効です。';
        return false;
      }
    }
    function sync() {
      if (!mergeSaved()) return false;
      if (dirty) return savePending();
      if (!protectExisting()) return false;
      warning = '';
      return true;
    }
    return {
      configure(cards) {
        if (!cards?.length) return;
        catalog = cards;
        valid = new Set(cards.flatMap(c => c.words.map(w => keyOf(c.id, w))));
        legacy = new Map();
        for (const card of cards) {
          if (!card.legacy || typeof card.legacy !== 'object' || Array.isArray(card.legacy)) continue;
          for (const [oldWord, newWord] of Object.entries(card.legacy)) {
            if (typeof newWord !== 'string') continue;
            const oldKey = keyOf(card.id, oldWord), newKey = keyOf(card.id, newWord);
            if (!valid.has(oldKey) && valid.has(newKey)) legacy.set(oldKey, newKey);
          }
        }
        for (const key of found) if (!valid.has(key)) retained.set(JSON.stringify(key), key);
        found = new Set([...found].filter(k => valid.has(k)));
        for (const [signature, value] of retained) {
          const key = canonicalSavedKey(value);
          if (key !== null && valid.has(key)) { found.add(key); retained.delete(signature); }
          else if (key !== null && legacy.has(key)) found.add(legacy.get(key));
        }
        if (mergeSaved()) protectExisting(); revision++;
      },
      discover(id, word) {
        const key = keyOf(id, word);
        if (!valid.has(key)) return false;
        const readable = mergeSaved();
        const isNew = !found.has(key);
        if (isNew) { found.add(key); revision++; dirty = true; }
        // Retrying an already discovered entry also retries a previous failure.
        if (dirty && readable) savePending();
        return isNew;
      },
      sync,
      refresh() {
        const readable = mergeSaved();
        if (readable && !dirty) warning = '';
        return readable;
      },
      has: (id, word) => found.has(keyOf(id, word)),
      get cards() { return catalog; },
      get count() { return found.size; },
      get total() { return valid.size; },
      get warning() { return warning; },
      get revision() { return revision; },
      challenge(random = Math.random) {
        const missing = catalog.flatMap(c => c.words.filter(w => !found.has(keyOf(c.id,w))).map(word => ({card:c, word})));
        if (!missing.length) return null;
        const target = missing[Math.floor(random() * missing.length)];
        const shuffle = items => { for (let i=items.length-1;i>0;i--) { const j=Math.floor(random()*(i+1)); [items[i],items[j]]=[items[j],items[i]]; } return items; };
        const decoys = shuffle(catalog.filter(c => !c.words.some(w => head(w) === head(target.word)))).slice(0,5);
        return {...target, options:shuffle([target.card,...decoys])};
      }
    };
  };
  window.createShiritoriDictionary = function ({E, add, onClose}) {
    let storage;
    try { storage = window.localStorage; } catch (_) {}
    const collection = window.createShiritoriCollection(storage);
    const page = E('div','sh-dictionary nr-surface'); page.hidden = true;
    const title = E('h1','','読み方ずかん'), progress = E('p','sh-dict-progress');
    const notice = E('p','sh-dict-notice'); notice.setAttribute('role','status');
    const warning = E('p','sh-dict-warning');
    const list = E('div','sh-dict-list'), quiz = E('div','sh-dict-quiz'); quiz.hidden = true;
    const question = E('h2'), answer = E('p'); answer.setAttribute('role','status');
    const choices = E('div','sh-dict-choices');
    let pending = null, solved = false, onlyMissing = false, lastKey = '';
    function localButton(label, action) { const b=E('button','nr-button',label); b.type='button'; b.addEventListener('click',action); return b; }
    function close() { if (page.hidden) return; page.hidden=true; onClose(); }
    const back = localButton('← 絵しりとりに戻る', close);
    const filter = localButton('未完成の絵だけ表示',()=>{ onlyMissing=!onlyMissing; lastKey=''; render(); });
    const retry = localButton('保存を再試行',()=>{ collection.sync(); render(); }); retry.hidden=true;
    // A different tab may discover a reading while this list is open. Reading
    // the new state here does not write back and cannot create event loops.
    if (typeof window.addEventListener === 'function') window.addEventListener('storage', event => {
      if (!page.hidden && (event.key === KEY || event.key === PROTECTED_KEY)) {
        collection.refresh(); render();
      }
    });
    const challenge = localButton('発見チャレンジ',newChallenge);
    const next = localButton('次の未発見をさがす',newChallenge); next.hidden=true;
    add(quiz, question, E('p','','頭文字に合う読み方を持つ絵をタップ。「ん」終わりも、この練習では発見として登録できます。'), choices, answer, next);
    add(page, add(E('div','sh-dict-header'),title,back), progress, notice, warning, retry,
      E('p','','自分でつないだ読み方が絵ごとに登録されます。CPUの回答・一覧を見るだけでは登録されません。未発見の読みは「？？？」です。'),
      add(E('div','sh-actions'),challenge,filter),quiz,list);
    function picture(c) { const custom=['daruma','top','ramune','zucchini','medaka','snow_crab','blocks','parsley','mushroom','paint'].includes(c.id); const icon=E('span',`sh-dict-icon${c.id==='daruma'?' sh-daruma':''}${custom?` sh-art-${c.id}`:''}`,custom?'':c.icon); icon.setAttribute('aria-hidden','true'); return icon; }
    function newChallenge() {
      pending=collection.challenge(); solved=false; quiz.hidden=false; next.hidden=true; answer.textContent='';
      if (!pending) { question.textContent='全読み方コンプリート！'; choices.replaceChildren(); return; }
      question.textContent=`「${head(pending.word)}」から始まる読み方の絵はどれ？`;
      choices.replaceChildren(...pending.options.map(c=>{
        const b=localButton('',()=>{
          if (solved) return;
          if (c.id !== pending.card.id) { answer.textContent='この絵ではないよ。もう一度さがそう！'; return; }
          collection.discover(c.id,pending.word); solved=true;
          answer.textContent=`新発見！ ${pending.word} を登録しました。`;
          next.hidden=false; render();
        });
        b.className='sh-dict-choice'; b.setAttribute('aria-label',`チャレンジの絵 ${c.words[0]}`); add(b,picture(c)); return b;
      }));
    }
    function render() {
      const count=collection.count, total=collection.total;
      progress.textContent=`${count} / ${total} 読み方 · ${total?(count/total*100).toFixed(1):'0.0'}%`;
      notice.textContent=count===total&&total?'🏆 全読み方コンプリート！ ことばマスター！':`あと${total-count}種類でコンプリート！`;
      warning.textContent=collection.warning; warning.hidden=!collection.warning;
      retry.hidden=!collection.warning;
      filter.textContent=onlyMissing?'すべての絵を表示':'未完成の絵だけ表示'; filter.setAttribute('aria-pressed',String(onlyMissing));
      const key=`${collection.revision}:${onlyMissing}`;
      if (key===lastKey) return;
      lastKey=key;
      list.replaceChildren(...collection.cards.filter(c=>!onlyMissing||c.words.some(w=>!collection.has(c.id,w))).map(c=>{
        const known=c.words.filter(w=>collection.has(c.id,w)).length;
        const row=E('article','sh-dict-entry'); row.dataset.complete=String(known===c.words.length);
        return add(row,add(E('div','sh-dict-picture'),picture(c),E('strong','',`${known}/${c.words.length}${known===c.words.length?' ★':''}`)),
          add(E('ul'),...c.words.map(w=>E('li',collection.has(c.id,w)?'sh-found':'sh-undiscovered',collection.has(c.id,w)?w:'？？？'))));
      }));
    }
    return {page, collection,
      open() { collection.sync(); lastKey=''; quiz.hidden=true; page.hidden=false; render(); back.focus({preventScroll: true}); },
      close,
      refresh:render
    };
  };
})();
