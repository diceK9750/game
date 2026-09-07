/* Mobile-first view only; Python owns cards, stock, timers, and decisions. */
(function () {
  'use strict';
  window.createShiritoriView = function ({section, E, add, button, portrait, command}) {
    const page = section('shiritori', 'sh-page');
    const intro = E('div', 'sh-intro sh-setup nr-surface');
    const modeButtons = [button('一人でじっくり', 'sh_mode', 'solo'), button('CPUと対戦', 'sh_mode', 'battle')];
    const modeHint = E('p', 'sh-setting-note');
    const countButtons = [12,24,36].map(n => button(`${n}枚`, 'sh_total', n));
    const countHint = E('p', 'sh-setting-note');
    const levels = E('div', 'sh-level-settings');
    const levelButtons = [['easy','ゆったり'],['normal','ふつう'],['hard','てごわい']].map(([v,label]) => button(label, 'sh_difficulty', v));
    const limit = E('p', 'sh-setting-note');
    add(levels, E('h2', '', 'ライバルの強さ'), add(E('div', 'sh-actions sh-levels'), ...levelButtons), limit);
    const guide = add(E('details', 'sh-guide'), E('summary', '', '遊び方・読み方のルール'),
      E('p', '', '絵を押して読み方を選び、前のことばの最後の文字につなぎます。「ん」と同じことばの再使用に注意。'),
      E('p', '', '対戦は交互に回答。時間切れ・「ん」・つながる札がないと負け。一人用は時間無制限で、詰まったら2回つなぎ直せます。'),
      E('p', '', '画面は12枚。24・36枚では使った場所に新しい札が登場。つながる札が盤面にない場合、山札にある札を優先して補充します（両者共通）。'),
      E('p', '', 'ヒントは3回。小さい文字は大きく（ちゃ→や）、長音は直前の文字（ぎたー→た）。濁点は区別。札とことばの再使用はできません。'));
    const start = button('はじめる', 'sh_start', undefined, 'nr-primary');
    add(intro, E('h1', '', '絵しりとり'),
      add(E('div', 'sh-config'), E('h2', '', '遊び方'), add(E('div', 'sh-actions sh-modes'), ...modeButtons), modeHint,
        E('h2', '', '絵の総枚数'), add(E('div', 'sh-actions sh-counts'), ...countButtons), countHint),
      add(E('div', 'sh-config'), levels, guide),
      add(E('div', 'sh-actions sh-start-actions'), button('← ゲーム選択', 'sh_exit'), start));
    const stage = E('div', 'sh-stage');
    const rin = portrait('rin', 'RIN / あなた'), koh = portrait('koh', 'KOH / CPU');
    const hud = E('div', 'sh-hud nr-surface');
    const prompt = E('strong', 'sh-prompt'), turn = E('span'), clock = E('strong', 'sh-clock');
    add(hud, rin.wrap, add(E('div', 'sh-task'), turn, prompt), clock, koh.wrap);
    const status = E('p', 'sh-status'); status.setAttribute('role', 'status');
    const stock = E('span', 'sh-stock'), completed = E('span');
    const board = E('div', 'sh-board'); board.setAttribute('role', 'group'); board.setAttribute('aria-label', 'しりとりの絵札 12枚');
    const slots = Array.from({length:12}, (_, i) => {
      const card = button('', 'sh_card', i, 'sh-card');
      const icon = E('span', 'sh-icon'), mark = E('small'); icon.setAttribute('aria-hidden', 'true');
      add(card, icon, mark); board.append(card); return {card, icon, mark, identity:null};
    });
    const hint = button('ヒント', 'sh_hint');
    const relink = button('つなぎ直す', 'sh_relink', undefined, 'nr-primary');
    const toolbar = add(E('div', 'sh-actions sh-play-actions'), hint, relink, button('休憩 / 終了', 'sh_pause'));
    add(stage, hud, add(E('div', 'sh-progress'), completed, stock), status, board, toolbar);
    const pause = E('div', 'sh-intro nr-surface');
    const endSolo = button('ここまでの結果を見る', 'sh_end');
    add(pause, E('h1', '', 'ひと休みしよう'), E('p', '', '札を隠して休憩中。設定変更・ゲーム選択へ戻ると現在のプレイは終了します。'),
      add(E('div', 'sh-actions'), button('プレイを続ける', 'sh_resume', undefined, 'nr-primary'), button('新しい配置でやり直す', 'sh_restart')),
      add(E('div', 'sh-actions'), button('絵しりとりの設定へ', 'sh_setup'), button('ゲーム選択へ', 'sh_exit')), endSolo);
    const result = E('div', 'sh-intro nr-surface');
    const resultTitle = E('h1'), reason = E('p'), tally = E('p');
    const resultRin = portrait('rin', 'RIN'), resultKoh = portrait('koh', 'KOH');
    const log = E('ol', 'sh-log');
    add(result, resultTitle, add(E('div', 'sh-result-cast'), resultRin.wrap, resultKoh.wrap), reason, tally,
      add(E('div', 'sh-actions'), button('もう一度遊ぶ', 'sh_start', undefined, 'nr-primary'), button('枚数・遊び方を変える', 'sh_setup'), button('ゲーム選択へ', 'sh_exit')),
      add(E('details'), E('summary', '', 'ことばと別の読み方を振り返る'), log));
    const overlay = E('div', 'sh-overlay'); overlay.hidden = true;
    const dialog = E('div', 'sh-dialog nr-surface'); dialog.setAttribute('role', 'dialog'); dialog.setAttribute('aria-modal', 'true'); dialog.setAttribute('aria-label', '絵の読み方を選ぶ');
    const choiceTitle = E('h2'), choiceClock = E('p'), choices = E('div', 'sh-choices');
    const choiceMessage = E('p'); choiceMessage.setAttribute('role', 'status');
    const cancel = button('ほかの絵を見る', 'sh_cancel');
    add(dialog, choiceTitle, choiceClock, choiceMessage, choices, cancel); overlay.append(dialog);
    add(page, intro, stage, pause, result, overlay);
    let selected = null, choiceKey = '', lastPhase = '', historyKey = '', latest = null;
    function pose(p, value) { p.image.style.backgroundPosition = value; }
    function pressed(buttons, values, value) { buttons.forEach((b,i) => b.setAttribute('aria-pressed', String(values[i] === value))); }
    overlay.addEventListener('keydown', event => {
      if (event.key === 'Escape') { event.preventDefault(); command('sh_cancel'); }
      if (event.key === 'Tab') {
        const list = [...choices.querySelectorAll('button'), cancel].filter(b => !b.disabled);
        const index = list.indexOf(document.activeElement);
        event.preventDefault(); list[(index + (event.shiftKey ? list.length - 1 : 1)) % list.length].focus();
      }
    });
    page.addEventListener('keydown', event => {
      if (event.key === 'Escape' && ['playing','blocked'].includes(latest?.phase) && latest.selected == null) command('sh_pause');
    });
    return {page, update(s) {
      if (!s) return;
      latest = s;
      const solo = s.mode === 'solo', live = ['playing','blocked'].includes(s.phase);
      intro.hidden = s.phase !== 'intro'; stage.hidden = !live;
      pause.hidden = s.phase !== 'paused'; result.hidden = s.phase !== 'finished';
      pressed(modeButtons, ['solo','battle'], s.mode); pressed(countButtons, [12,24,36], s.total); pressed(levelButtons, ['easy','normal','hard'], s.difficulty);
      modeHint.textContent = solo ? '時間無制限。自分のペースで最後までつなごう。' : 'リンとコウが交互につなぐ、ことばの対決。';
      countHint.textContent = s.total > 12 ? `画面12枚＋山札${s.total - 12}枚。使った場所に補充。` : '12枚を並べてスタート。補充なしの短いコース。';
      levels.hidden = solo;
      limit.textContent = `1手${s.limit}秒。誤答は−3秒。「てごわい」は一手先も考えます。`;
      start.textContent = solo ? '一人でスタート' : '対戦スタート';
      const mine = s.turn === 'you';
      turn.textContent = solo ? '一人でじっくり' : mine ? 'あなたの番' : 'コウが考えています…';
      prompt.textContent = `${s.last_word} →「${s.required}」`;
      clock.textContent = solo ? '時間無制限' : mine ? `${s.remaining.toFixed(1)} 秒` : '…';
      clock.dataset.urgent = String(!solo && mine && s.remaining < 5);
      status.textContent = s.message;
      stock.textContent = `山札 ${s.stock || 0}枚`; completed.textContent = `${s.completed || 0} / ${s.total || 24}枚 つながった`;
      hint.textContent = `ヒント ${s.hints}回`; hint.disabled = !mine || !s.hints || s.phase !== 'playing';
      relink.hidden = s.phase !== 'blocked'; relink.textContent = `つなぎ直す あと${s.relinks}回`;
      endSolo.hidden = !solo; koh.wrap.hidden = solo; resultKoh.wrap.hidden = solo;
      const last = s.history[s.history.length - 1];
      pose(rin, last?.owner === 'you' ? '50% 0%' : '0% 0%'); pose(koh, last?.owner === 'cpu' ? '50% 0%' : '0% 0%');
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
        card.dataset.owner = data.owner || ''; card.dataset.hint = String(s.hint === i);
        card.setAttribute('aria-label', `絵札${i + 1} ${data.words[0]}${data.owner ? ' 使用済み' : ' 読み方を見る'}`);
      });
      const show = s.phase === 'playing' && mine && s.selected != null;
      overlay.hidden = !show;
      if (show) {
        const data = s.cards[s.selected];
        choiceTitle.textContent = `${data.icon} 読み方を選ぶ`;
        choiceClock.textContent = `「${s.required}」から始めよう · ${solo ? '時間無制限' : `あと${s.remaining.toFixed(1)}秒`}`;
        choiceMessage.textContent = s.message;
        const key = `${s.selected}:${data.id}:${JSON.stringify(s.seen || [])}`;
        if (choiceKey !== key) {
          choices.replaceChildren(...data.words.map(w => {
            const used = (s.seen || []).includes(w);
            const b = button(`${w}${used ? '（使用済み）' : w.endsWith('ん') ? ' ⚠ ん' : ''}`, 'sh_word', w, 'nr-primary');
            b.disabled = used;
            return b;
          }));
          const focus = [...choices.querySelectorAll('button')].find(b => !b.disabled) || cancel;
          focus.focus();
          choiceKey = key;
        }
      } else {
        choiceKey = '';
        if (selected != null && s.phase === 'playing') {
          const focusCard = slots.find(slot => !slot.card.disabled);
          if (focusCard) focusCard.card.focus({preventScroll: true});
        }
      }
      selected = show ? s.selected : null;
      resultTitle.textContent = solo ? s.winner === 'you' ? 'ぜんぶつながった！' : '今回のチャレンジ結果' : s.winner === 'you' ? 'あなたの勝利！' : s.winner === 'draw' ? 'ふたりでつなぎきった！' : 'コウの勝利！';
      reason.textContent = s.message;
      tally.textContent = `${s.history.length} / ${s.total || 24}枚 · ミス${s.mistakes}回 · ヒント${3 - s.hints}回${solo ? ` · つなぎ直し${2 - s.relinks}回` : ''}`;
      pose(resultRin, s.winner === 'cpu' ? '100% 100%' : '100% 0%');
      pose(resultKoh, s.winner === 'you' ? '100% 100%' : '100% 0%');
      const key = JSON.stringify(s.history);
      if (key !== historyKey) {
        historyKey = key;
        log.replaceChildren(...s.history.map(row => add(E('li'), E('strong', '', `${row.relinked ? '↪ つなぎ直し · ' : ''}${row.owner === 'you' ? 'リン' : 'コウ'}：${row.icon} ${row.word}`), E('small', '', `読み方：${(row.readings || [row.word]).join(' ／ ')}`))));
      }
      if (lastPhase !== s.phase) {
        const heading = (s.phase === 'intro' ? intro : s.phase === 'paused' ? pause : s.phase === 'finished' ? result : hud).querySelector('h1, strong');
        if (heading) { heading.tabIndex = -1; heading.focus({preventScroll: true}); }
        page.scrollTop = 0;
      }
      lastPhase = s.phase;
    }};
  };
})();
