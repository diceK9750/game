/* Mobile-first view only; Python owns cards, stock, timers, and decisions. */
(function () {
  'use strict';
  window.createShiritoriView = function ({section, E, add, button, portrait, command, settingsControls, onNavigationChange = () => {}}) {
    const page = section('shiritori', 'sh-page');
    const intro = E('div', 'nr-ready sh-ready');
    const hero = E('div', 'nr-intro');
    const heroRin = portrait('rin', 'RIN / あなた'), heroRival = portrait('koh', 'LUNA / ライバル');
    add(hero, E('span', 'nr-eyebrow', 'PICTURE WORD CHALLENGE'), E('h1', '', '絵を見つけて、つなごう。'),
      E('p', 'nr-intro-copy', 'お題の文字につながる絵をタップ。読み方は自動で選択。\nどの枚数でも、全札をつなげられる配置でスタート！'),
      add(E('div', 'nr-hero-cast'), heroRin.wrap, E('span', 'nr-versus', 'VS'), heroRival.wrap));
    const setup = E('div', 'nr-setup nr-surface sh-ready-settings');
    const modeButtons = [button('CPUと対戦', 'sh_mode', 'battle'), button('ひとりで練習', 'sh_mode', 'solo')];
    const modeHint = E('p', 'sh-setting-note');
    const counts = [12,24,36,48];
    const countButtons = counts.map(n => button(`${n}枚`, 'sh_total', n));
    const countHint = E('p', 'sh-setting-note');
    const levels = E('div', 'sh-level-settings');
    const levelButtons = [['easy','ゆったり'],['normal','ふつう'],['hard','てごわい']].map(([v,label]) => button(label, 'sh_difficulty', v));
    const limit = E('p', 'sh-setting-note');
    add(levels, E('h2', 'nr-field-label', 'ライバルの強さ'), add(E('div', 'nr-segment sh-actions sh-levels'), ...levelButtons), limit);
    const guide = add(E('details', 'sh-guide'), E('summary', '', '遊び方・読み方のルール'),
      E('p', '', '絵を1回タップするだけ！必要な頭文字につながる未使用の読み方を自動確定。「ん」終わりは自動で除外します。各絵に頭文字の異なる3〜5種類の読み方があります。'),
      E('p', '', '対戦は交互に回答。時間切れ・つながる札がないと負け。一人用は時間無制限で、詰まったら2回つなぎ直せます。'),
      E('p', '', '画面は最大24枚。36・48枚では使った場所に新しい札が登場。開始時には必ず全札をつなぐルートがあります。途中の選び方によっては行き詰まるため、ヒントも活用しよう。山札の補充条件は両者共通です。'),
      E('p', '', 'ヒントは3回。小さい文字は大きく（ちゃ→や）、長音は直前の文字（ぎたー→た）。濁点は区別。札とことばの再使用はできません。'),
      E('p', '', '正解後、連鎖ゲージがなくなる前に次も正解すると自動で連鎖！猶予は4.5秒から徐々に短くなり、最短1.2秒。ミスで終了します。対戦は相手の手番中、自分のゲージが止まります。CPUも同じ条件で連鎖します。'));
    const start = button('はじめる', 'sh_start', undefined, 'nr-primary');
    add(setup, E('div', 'nr-setup-heading', '絵しりとりのチャレンジ'),
      add(E('div', 'sh-config'), E('h2', 'nr-field-label', '遊び方'), add(E('div', 'nr-segment sh-actions sh-modes'), ...modeButtons), modeHint,
        E('h2', 'nr-field-label', '絵の総枚数'), add(E('div', 'nr-segment sh-actions sh-counts'), ...countButtons), countHint),
      add(E('div', 'sh-config'), levels),
      add(E('div', 'sh-actions sh-start-actions'), start));
    add(intro, hero, setup);
    if (settingsControls) setup.append(settingsControls());
    const stage = E('div', 'sh-stage');
    const rin = portrait('rin', 'RIN / あなた'), koh = portrait('koh', 'LUNA / CPU');
    const hud = E('div', 'sh-hud nr-surface');
    const prompt = E('strong', 'sh-prompt'), turn = E('span'), clock = E('strong', 'sh-clock');
    add(hud, rin.wrap, add(E('div', 'sh-task'), turn, prompt), clock, koh.wrap);
    const status = E('p', 'sh-status'); status.setAttribute('role', 'status');
    const stock = E('span', 'sh-stock'), completed = E('span');
    const board = E('div', 'sh-board'); board.setAttribute('role', 'group'); board.setAttribute('aria-label', 'しりとりの絵札');
    const boardSpace = add(E('div', 'sh-board-space'), board);
    const slots = Array.from({length:24}, (_, i) => {
      const card = button('', 'sh_card', i, 'sh-card');
      const icon = E('span', 'sh-icon'), mark = E('small'); icon.setAttribute('aria-hidden', 'true');
      const hintLabel = E('span', 'sh-hint-label', '◆ ヒント'); hintLabel.hidden = true; hintLabel.setAttribute('aria-hidden', 'true');
      add(card, icon, mark, hintLabel); board.append(card); return {card, icon, mark, hintLabel, identity:null};
    });
    const hint = button('ヒント', 'sh_hint');
    const timedChain = window.createTimedChainView?.({E, add, portraits:[rin,koh]});
    const relink = button('つなぎ直す', 'sh_relink', undefined, 'nr-primary');
    const toolbar = add(E('div', 'sh-actions sh-play-actions'), hint, relink);
    add(stage, hud, add(E('div', 'sh-progress'), completed, stock), status, boardSpace, toolbar);
    if (timedChain) stage.append(timedChain.root);
    const pause = E('div', 'sh-intro nr-dialog nr-surface');
    const endSolo = button('ここまでの結果を見る', 'sh_end');
    add(pause, E('h1', '', 'ひと休みしよう'), E('p', '', '札を隠して休憩中。設定変更・ゲーム選択へ戻ると現在のプレイは終了します。'),
      add(E('div', 'nr-dialog-actions'), button('プレイを続ける', 'sh_resume', undefined, 'nr-primary')),
      add(E('div', 'nr-pause-extras'), button('新しい配置でやり直す', () => { restartRequested='sh_restart'; return 'sh_pause'; }), button('モード選択へ', () => { restartRequested='sh_setup'; return 'sh_pause'; })), endSolo);
    if (settingsControls) pause.append(settingsControls());
    const result = E('div', 'sh-intro sh-result nr-surface');
    const resultTitle = E('h1'), reason = E('p'), tally = E('p');
    const resultRin = portrait('rin', 'RIN'), resultKoh = portrait('koh', 'LUNA');
    const log = E('ol', 'sh-log');
    add(result, resultTitle, add(E('div', 'sh-result-cast'), resultRin.wrap, resultKoh.wrap), reason, tally,
      add(E('div', 'nr-result-actions'), button('もう一度遊ぶ', 'sh_start', undefined, 'nr-primary'), button('モード選択', 'sh_setup', undefined, 'nr-secondary')),
      add(E('details'), E('summary', '', 'ことばと別の読み方を振り返る'), log));
    add(page, intro, stage, pause, result);
    let lastPhase = '', historyKey = '', latest = null, helpOpen=false, restartRequested=false;
    const helpPage=E('div','sh-intro nr-help-card nr-surface');
    const closeHelp=E('button','nr-button nr-primary','戻る'); closeHelp.type='button';
    closeHelp.addEventListener('click',()=>{helpOpen=false; helpPage.hidden=true; intro.hidden=false; onNavigationChange(); intro.querySelector('h1').focus();});
    guide.open=true;
    add(helpPage,E('span','nr-eyebrow','HOW TO PLAY'),E('h1','','遊び方'),guide,closeHelp);
    const restartPage=E('div','sh-intro nr-dialog nr-surface');
    const cancelRestart=E('button','nr-button nr-secondary','キャンセル'); cancelRestart.type='button';
    cancelRestart.addEventListener('click',()=>{restartRequested=false; command('sh_resume');});
    const confirmTitle=E('h1','','やり直しますか？'), confirmCopy=E('p');
    const confirmAction=button('やり直す',()=>restartRequested || 'sh_restart',undefined,'nr-primary');
    add(restartPage,confirmTitle,confirmCopy,add(E('div','nr-dialog-actions'),confirmAction,cancelRestart));
    helpPage.hidden=restartPage.hidden=true; page.append(helpPage,restartPage);
    let dictionaryOpen = false, catalogLoaded = false, discoveryHistory = '', newFind = '';
    const dictionary = window.createShiritoriDictionary?.({E, add, onClose() {
      dictionaryOpen=false; intro.hidden=latest?.phase!=='intro'; result.hidden=latest?.phase!=='finished';
      onNavigationChange();
      (latest?.phase==='finished'?dictResult:dictIntro).focus();
    }});
    function dictionaryButton() {
      const b=E('button','nr-button sh-dict-open','読み方ずかん'); b.type='button';
      b.addEventListener('click',()=>{
        if (!dictionary || !['intro','finished'].includes(latest?.phase)) return;
        dictionaryOpen=true; intro.hidden=result.hidden=true; dictionary.open(); page.scrollTop=0;
        onNavigationChange();
      });
      return b;
    }
    const dictIntro=dictionaryButton(), dictResult=dictionaryButton();
    const discovery=E('p','sh-discovery'); discovery.setAttribute('role','status');
    if (dictionary) { setup.append(dictIntro); result.append(dictResult); page.append(dictionary.page); }
    result.append(discovery);
    function pose(p, value) { p.image.style.backgroundPosition = value; }
    function pressed(buttons, values, value) { buttons.forEach((b,i) => b.setAttribute('aria-pressed', String(values[i] === value))); }
    page.addEventListener('keydown', event => {
      if (event.key !== 'Escape') return;
      if (helpOpen) { closeHelp.click(); event.preventDefault(); return; }
      if (restartRequested && latest?.phase==='paused') { cancelRestart.click(); event.preventDefault(); return; }
      if (event.key === 'Escape' && ['playing','blocked'].includes(latest?.phase)) command('sh_pause');
    });
    return {page, isOverlayOpen:()=>dictionaryOpen || helpOpen,
      headerAction(action) {
        if (action==='help' && latest?.phase==='intro' && !dictionaryOpen) { helpOpen=true; intro.hidden=true; helpPage.hidden=false; closeHelp.focus(); }
        if (action==='retry' && ['playing','blocked'].includes(latest?.phase)) { restartRequested='sh_restart'; command('sh_pause'); }
      }, update(s) {
      if (!s) return;
      latest = s;
      if (dictionary) {
        if (!catalogLoaded && s.catalog?.length) { dictionary.collection.configure(s.catalog); catalogLoaded=true; }
        const earned=s.discoveries || s.history;
        const history=JSON.stringify(earned);
        if (discoveryHistory!==history) {
          discoveryHistory=history;
          for (const row of earned) if (row.owner==='you' && dictionary.collection.discover(row.id,row.word)) newFind=`ずかんに新登録：${row.word}`;
        }
        if (s.phase==='intro' && lastPhase!=='intro') newFind='';
        const c=dictionary.collection;
        dictIntro.textContent=dictResult.textContent=`読み方ずかん ${c.count} / ${c.total}`;
        discovery.textContent=c.warning || (c.total&&c.count===c.total?'🏆 読み方ずかんコンプリート！':newFind);
        if (dictionaryOpen) dictionary.refresh();
      }
      const solo = s.mode === 'solo', live = ['playing','blocked'].includes(s.phase);
      page.dataset.layout = dictionaryOpen || helpOpen ? 'document' : live ? 'play' :
        s.phase === 'intro' ? 'setup' : s.phase === 'finished' ? 'result' : 'dialog';
      intro.hidden = s.phase !== 'intro'; stage.hidden = !live;
      pause.hidden = s.phase !== 'paused'; result.hidden = s.phase !== 'finished';
      if (s.phase!=='intro') helpOpen=false;
      if (!['paused','playing','blocked'].includes(s.phase) || (lastPhase==='paused' && s.phase!=='paused')) restartRequested=false;
      helpPage.hidden=!helpOpen;
      const wasConfirmHidden=restartPage.hidden;
      restartPage.hidden=!(restartRequested && s.phase==='paused');
      confirmTitle.textContent=restartRequested==='sh_setup'?'モード選択に戻りますか？':'やり直しますか？';
      confirmCopy.textContent=restartRequested==='sh_setup'?'現在のプレイを終了します。':'現在のプレイを終了し、新しい配置で始めます。';
      confirmAction.textContent=restartRequested==='sh_setup'?'戻る':'やり直す';
      if (wasConfirmHidden && !restartPage.hidden) { confirmTitle.tabIndex=-1; confirmTitle.focus(); }
      if (!restartPage.hidden) pause.hidden=true;
      if (dictionaryOpen || helpOpen) intro.hidden=result.hidden=true;
      pressed(modeButtons, ['battle','solo'], s.mode); pressed(countButtons, counts, s.total); pressed(levelButtons, ['easy','normal','hard'], s.difficulty);
      modeHint.textContent = solo ? '時間無制限。自分のペースで最後までつなごう。' : 'ライバルと交互に回答。制限時間内につながる絵を見つけよう。';
      countHint.textContent = s.total > 24 ? `画面24枚＋山札${s.total - 24}枚。使った場所に補充。` : `${s.total}枚を並べてスタート。補充なし。`;
      levels.hidden = solo;
      limit.textContent = `1手${s.limit}秒。誤答は−3秒。ルナは全札完走を優先し、長くつながる手を探します。`;
      start.textContent = solo ? '一人でスタート' : '対戦スタート';
      const mine = s.turn === 'you';
      turn.textContent = solo ? '一人でじっくり' : mine ? 'あなたの番' : 'ルナが考えています…';
      prompt.textContent = `${s.last_word} →「${s.required}」`;
      clock.textContent = solo ? '時間無制限' : mine ? `${s.remaining.toFixed(1)} 秒` : '…';
      clock.dataset.urgent = String(!solo && mine && s.remaining < 5);
      status.textContent = s.message + (newFind ? ` · ${newFind}` : '');
      stock.textContent = `山札 ${s.stock || 0}枚`; completed.textContent = `${s.completed || 0} / ${s.total || 24}枚 つながった`;
      hint.textContent = `ヒント ${s.hints}回`; hint.disabled = !mine || !s.hints || s.phase !== 'playing';
      relink.hidden = s.phase !== 'blocked'; relink.textContent = `つなぎ直す あと${s.relinks}回`;
      endSolo.hidden = !solo; koh.wrap.hidden = solo; resultKoh.wrap.hidden = solo;
      const last = s.history[s.history.length - 1];
      pose(rin, last?.owner === 'you' ? '50% 0%' : '0% 0%'); pose(koh, last?.owner === 'cpu' ? '50% 0%' : '0% 0%');
      timedChain?.update(s.chain, !solo, live, s.phase === 'finished');
      board.dataset.count = String(Math.min(s.total || 24, 24));
      boardSpace.dataset.count = board.dataset.count;
      board.setAttribute('aria-label', `しりとりの絵札 ${Math.min(s.total || 24, 24)}枚`);
      slots.forEach((item, i) => { item.card.hidden = i >= s.cards.length; if(!live||solo||mine) item.card.dataset.cpuSelecting='false'; });
      const columns=Number(window.getComputedStyle?.(boardSpace).getPropertyValue('--sh-cols')) || (s.total>12?8:4);
      const cpuCursor=!solo && live && !mine ? window.rivalCursor?.(s.cards.length,columns,s.cpu_target,s.cpu_progress) : null;
      s.cards.forEach((data, i) => {
        const item = slots[i], {card, icon, mark} = item;
        if (item.identity !== data.id) {
          const replaced = item.identity != null;
          item.identity = data.id;
          item.dealFlip = !item.dealFlip;
          icon.textContent = data.id === 'daruma' ? '' : data.icon;
          icon.className = `sh-icon${data.id === 'daruma' ? ' sh-daruma' : ''}`;
          card.dataset.dealt = replaced ? String(Number(item.dealFlip)) : '';
        }
        mark.textContent = data.owner === 'you' ? 'YOU ✓' : data.owner === 'cpu' ? 'CPU ✓' : s.refilled === i ? 'NEW' : '';
        card.disabled = !mine || !!data.owner || s.phase !== 'playing';
        const hinted = live && s.hint === i && !data.owner;
        card.dataset.owner = data.owner || ''; card.dataset.hint = String(hinted);
        item.hintLabel.hidden = !hinted;
        card.dataset.cpuSelecting = String(i===cpuCursor);
        card.setAttribute('aria-label', `${hinted ? 'ヒント：' : ''}絵札${i + 1} ${data.words[0]}${data.owner ? ' 使用済み' : ' タップで自動回答'}`);
      });
      resultTitle.textContent = solo ? s.winner === 'you' ? 'ぜんぶつながった！' : '今回のチャレンジ結果' : s.winner === 'you' ? 'あなたの勝利！' : s.winner === 'draw' ? 'ふたりでつなぎきった！' : 'ルナの勝利！';
      reason.textContent = s.message;
      tally.textContent = `${s.history.length} / ${s.total || 24}枚 · ミス${s.mistakes}回 · ヒント${3 - s.hints}回${solo ? ` · つなぎ直し${2 - s.relinks}回` : ''}`;
      if (s.chain) tally.textContent += ` · 最大${s.chain.you.best}連鎖 · ${s.chain.you.bonus}ボーナス${solo ? '' : ` ／ CPU最大${s.chain.cpu.best}連鎖 · ${s.chain.cpu.bonus}ボーナス`}`;
      pose(resultRin, s.winner === 'cpu' ? '100% 100%' : '100% 0%');
      pose(resultKoh, s.winner === 'you' ? '100% 100%' : '100% 0%');
      const key = JSON.stringify(s.history);
      if (key !== historyKey) {
        historyKey = key;
        log.replaceChildren(...s.history.map(row => add(E('li'), E('strong', '', `${row.relinked ? '↪ つなぎ直し · ' : ''}${row.owner === 'you' ? 'リン' : 'ルナ'}：${row.icon} ${row.word}`), E('small', '', `読み方：${(row.readings || [row.word]).join(' ／ ')}`))));
      }
      if (lastPhase !== s.phase) {
        const heading = (s.phase === 'intro' ? intro : s.phase === 'paused' ? (restartRequested ? restartPage : pause) : s.phase === 'finished' ? result : hud).querySelector('h1, strong');
        if (heading) { heading.tabIndex = -1; heading.focus({preventScroll: true}); }
        page.scrollTop = 0;
      }
      lastPhase = s.phase;
    }};
  };
})();
