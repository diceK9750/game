/* Collection keys are picture + reading: shared category words count per picture. */
(function () {
  'use strict';
  const KEY = 'number-rush.shiritori.dictionary.v1';
  const keyOf = (id, word) => `${id}:${word}`;
  window.createShiritoriCollection = function (storage) {
    let catalog = [], valid = new Set(), found = new Set(), warning = '', revision = 0;
    function mergeSaved() {
      try {
        const raw = storage.getItem(KEY);
        if (!raw) return;
        const saved = JSON.parse(raw);
        if (saved?.version !== 1 || !Array.isArray(saved.found)) throw Error('format');
        for (const key of saved.found) if (valid.has(key)) found.add(key);
      } catch (_) { warning = '保存データを読み込めません。このページ内で収集を続けられます。'; }
    }
    return {
      configure(cards) {
        if (!cards?.length) return;
        catalog = cards;
        valid = new Set(cards.flatMap(c => c.words.map(w => keyOf(c.id, w))));
        found = new Set([...found].filter(k => valid.has(k)));
        mergeSaved(); revision++;
      },
      discover(id, word) {
        const key = keyOf(id, word);
        if (!valid.has(key)) return false;
        mergeSaved();
        if (found.has(key)) return false;
        found.add(key); revision++;
        try { storage.setItem(KEY, JSON.stringify({version:1, found:[...found]})); warning = ''; }
        catch (_) { warning = '保存できません。収集はこのページを閉じるまで有効です。'; }
        return true;
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
        const decoys = shuffle(catalog.filter(c => !c.words.some(w => w[0] === target.word[0]))).slice(0,5);
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
    const back = localButton('← 絵しりとりに戻る',()=>{ page.hidden=true; onClose(); });
    const filter = localButton('未完成の絵だけ表示',()=>{ onlyMissing=!onlyMissing; lastKey=''; render(); });
    const challenge = localButton('発見チャレンジ',newChallenge);
    const next = localButton('次の未発見をさがす',newChallenge); next.hidden=true;
    add(quiz, question, E('p','','頭文字に合う読み方を持つ絵をタップ。「ん」終わりも、この練習では発見として登録できます。'), choices, answer, next);
    add(page, add(E('div','sh-dict-header'),title,back), progress, notice, warning,
      E('p','','自分でつないだ読み方が絵ごとに登録されます。CPUの回答・一覧を見るだけでは登録されません。未発見の読みは「？？？」です。'),
      add(E('div','sh-actions'),challenge,filter),quiz,list);
    function picture(c) { const icon=E('span',`sh-dict-icon${c.id==='daruma'?' sh-daruma':''}`,c.id==='daruma'?'':c.icon); icon.setAttribute('aria-hidden','true'); return icon; }
    function newChallenge() {
      pending=collection.challenge(); solved=false; quiz.hidden=false; next.hidden=true; answer.textContent='';
      if (!pending) { question.textContent='全読み方コンプリート！'; choices.replaceChildren(); return; }
      question.textContent=`「${pending.word[0]}」から始まる読み方の絵はどれ？`;
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
      open() { lastKey=''; quiz.hidden=true; page.hidden=false; render(); title.tabIndex=-1; title.focus(); },
      refresh:render
    };
  };
})();
