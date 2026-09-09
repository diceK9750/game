/* Responsive, accessible presentation. Python remains the only game engine. */
(function () {
  'use strict';
  const SCREENS = new Set(['home', 'ready', 'playing', 'countdown', 'resuming', 'confirm', 'help', 'finished', 'review', 'shiritori']);
  const POSES = Object.freeze({idle: 0, celebrate: 1, victory: 2, hurt: 3, frustrated: 4, defeat: 5});
  const integer = (value, fallback = 0) => Number.isInteger(value) ? value : fallback;
  const finite = (value, fallback = 0) => Number.isFinite(value) ? value : fallback;
  function parseState(raw) {
    try {
      const state = JSON.parse(raw);
      if (!state || state.v !== 1 || !SCREENS.has(state.screen)) return null;
      const boardVisible = ['playing', 'finished', 'review'].includes(state.screen);
      if (!boardVisible && state.cells == null) state.cells = [];
      if (!Array.isArray(state.cells) || (boardVisible ? state.cells.length !== 40 : state.cells.length !== 0)) return null;
      if (state.cells.some(cell => !cell || !(cell.n === null || (Number.isInteger(cell.n) && cell.n >= 1 && cell.n <= 40)))) return null;
      return state;
    } catch { return null; }
  }
  function formatTime(seconds) {
    const time = Math.max(0, finite(seconds));
    return time < 60 ? `${time.toFixed(2)} 秒` : `${Math.floor(time / 60)}:${(time % 60).toFixed(2).padStart(5, '0')}`;
  }
  function posePosition(pose) {
    const value = Object.hasOwn(POSES, pose) ? POSES[pose] : 0;
    return `${value % 3 * 50}% ${Math.floor(value / 3) * 100}%`;
  }
  function remainingCommands(raw, ack) {
    try {
      const commands = JSON.parse(raw || '[]');
      return Array.isArray(commands) ? commands.filter(c => c && Number.isSafeInteger(c.id) && c.id > ack).slice(0, 128) : [];
    } catch { return []; }
  }
  function nextCell(index, key) {
    const row = Math.floor(index / 8), col = index % 8;
    return key === 'ArrowRight' ? row * 8 + (col + 1) % 8
      : key === 'ArrowLeft' ? row * 8 + (col + 7) % 8
      : key === 'ArrowDown' ? ((row + 1) % 5) * 8 + col
      : key === 'ArrowUp' ? ((row + 4) % 5) * 8 + col : index;
  }
  function nextPlayable(available, index, key) {
    let next = nextCell(index, key);
    for (let count = 0; count < 40; count++) {
      if (available[next]) return next;
      next = nextCell(next, key);
    }
    // A whole row/column can be cleared; still provide a way back into the board.
    return available.findIndex(Boolean);
  }
  if (typeof module !== 'undefined') module.exports = {parseState, formatTime, posePosition, remainingCommands, nextCell, nextPlayable};
  if (typeof document === 'undefined') return;
  const root = document.documentElement, app = document.getElementById('modern-app');
  if (!app) return;
  const media = window.matchMedia('(prefers-reduced-motion: reduce)');
  let state = null, sequence = 0, active = false, previousScreen = '', announcement = '', historyKey = '';
  let keyboardCell = 0;
  const E = (tag, className, text) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  };
  const add = (parent, ...children) => { parent.append(...children); return parent; };
  function command(action, value, index) {
    if (!state) return;
    if (state.screen === 'shiritori') {
      if (['help', 'retry'].includes(action)) { shiritori.headerAction(action); update(); return; }
      if (action === 'home') action = 'sh_exit';
      if (action === 'pause') action = 'sh_pause';
    }
    const queue = remainingCommands(root.getAttribute('data-modern-commands'), integer(state.ack));
    if (queue.length >= 128) return;
    sequence = Math.max(sequence, integer(state.ack), ...queue.map(c => c.id)) + 1;
    const item = {id: sequence, action};
    if (value !== undefined) item.value = value;
    if (index !== undefined) item.index = index;
    queue.push(item);
    root.setAttribute('data-modern-commands', JSON.stringify(queue));
  }
  function button(text, action, value, className = '') {
    const element = E('button', `nr-button ${className}`, text);
    element.type = 'button';
    element.addEventListener('click', () => command(typeof action === 'function' ? action() : action, value));
    return element;
  }
  function section(name, className) {
    const element = E('section', `nr-screen ${className || ''}`);
    element.dataset.screen = name;
    element.hidden = true;
    app.append(element);
    return element;
  }
  function portrait(who, label) {
    const wrap = E('div', `nr-character nr-${who}`);
    const image = E('div', 'nr-character-art');
    image.setAttribute('role', 'img');
    image.setAttribute('aria-label', who === 'rin' ? 'うさぎのリン' : '闇の魔法少女ルナ（レッサーパンダ）');
    add(wrap, image, E('span', 'nr-character-name', label));
    if (who === 'koh') {
      const fairy = E('div', 'nr-dark-fairy');
      fairy.setAttribute('role', 'img');
      fairy.setAttribute('aria-label', '闇の妖精');
      wrap.append(fairy);
    }
    return {wrap, image};
  }
  const live = E('div', 'nr-sr-only');
  live.setAttribute('role', 'status'); live.setAttribute('aria-live', 'polite'); live.setAttribute('aria-atomic', 'true');
  const header = E('header', 'nr-header');
  const brand = add(E('div', 'nr-brand'), E('span', 'nr-brand-symbol', '✦'), add(E('div'), E('span', 'nr-brand-name', 'NUMBER RUSH'), E('span', 'nr-brand-sub', 'ランタン・リーグ')));
  const headerContext = E('span', 'nr-header-context');
  const topControls = E('nav', 'nr-toolbar'); topControls.setAttribute('aria-label', 'ゲーム操作');
  const sound = button('BGM', 'bgm', undefined, 'nr-icon-button');
  sound.setAttribute('aria-label', 'BGMのオン・オフ');
  const help = button('?', 'help', undefined, 'nr-icon-button nr-help-button'); help.setAttribute('aria-label', '遊び方');
  const pause = button('一時停止', 'pause', undefined, 'nr-quiet');
  const retry = button('やり直す', 'retry', undefined, 'nr-quiet nr-play-retry');
  const gamesBack = button('ゲーム選択', 'home', undefined, 'nr-quiet nr-games-back');
  add(topControls, gamesBack, sound, help, retry, pause); add(header, brand, headerContext, topControls); app.append(header, live);

  const home = section('home', 'nr-home');
  const homeChoices = E('div', 'nr-game-choices');
  const pictureGame = button('', 'shiritori', undefined, 'nr-game-card nr-picture-game');
  add(pictureGame, E('span', 'nr-game-icon', '🍎 → 🦍'), E('strong', '', '絵しりとり'), E('span', '', 'ことばをつなぐ、ひらめきパズル'), E('small', '', '一人でじっくり ／ CPUと対戦 →'));
  pictureGame.disabled = !window.createShiritoriView;
  const numberGame = button('', 'numbers', undefined, 'nr-game-card nr-number-game');
  add(numberGame, E('span', 'nr-game-icon', '1  2  3'), E('strong', '', '数字さがし'), E('span', '', '見つけてタップ、集中力チャレンジ'), E('small', '', '一人で練習 ／ CPUと対戦 →'));
  add(homeChoices, pictureGame, numberGame);
  add(home, E('span', 'nr-eyebrow', 'LANTERN LEAGUE'), E('h1', '', 'どちらで遊ぶ？'), homeChoices);
  const ready = section('ready', 'nr-ready');
  const intro = E('div', 'nr-intro');
  const heroCast = E('div', 'nr-hero-cast');
  const heroRin = portrait('rin', 'RIN / あなた'), heroKoh = portrait('koh', 'LUNA / ライバル');
  const title = E('h1', '', '見つけた！が、勝負になる。');
  add(intro, E('span', 'nr-eyebrow', 'QUICK EYES. BRIGHT MOMENTS.'), title,
    E('p', 'nr-intro-copy', 'お題の数字を、ライバルより先に見つけよう。\n順番・ランダムのお題で対戦。一人での練習も楽しめます。'),
    add(heroCast, heroRin.wrap, E('span', 'nr-versus', 'VS'), heroKoh.wrap));
  const setup = E('div', 'nr-setup nr-surface');
  add(setup, E('div', 'nr-setup-heading', '今日のチャレンジ'));
  const kindGroup = E('div', 'nr-segment nr-kind-group'); kindGroup.setAttribute('role', 'group'); kindGroup.setAttribute('aria-label', '遊び方を選ぶ');
  const kindButtons = ['battle', 'practice'].map((kind, i) => button(i ? 'ひとりで練習' : 'CPUと対戦', 'kind', kind)); add(kindGroup, ...kindButtons);
  const kindDescription = E('p', 'nr-field-hint');
  add(setup, kindGroup, kindDescription, E('h2', 'nr-field-label', '数字の範囲'));
  const ranges = E('div', 'nr-range-grid'); ranges.setAttribute('role', 'group'); ranges.setAttribute('aria-label', '数字の範囲');
  const rangeButtons = [10, 20, 30, 40].map(n => {
    const b = button('', 'range', n, 'nr-range'); add(b, E('span', 'nr-range-prefix', '1 —'), E('strong', '', n));
    b.setAttribute('aria-label', `1から${n}まで`); return b;
  }); add(ranges, ...rangeButtons); add(setup, ranges);
  const difficultyWrap = E('div', 'nr-difficulty-wrap');
  const levels = E('div', 'nr-segment nr-levels'); levels.setAttribute('role', 'group'); levels.setAttribute('aria-label', 'CPUの強さ');
  const levelButtons = ['easy', 'normal', 'hard'].map((value, i) => button(['ゆったり', 'ふつう', 'てごわい'][i], 'difficulty', value));
  add(levels, ...levelButtons); add(difficultyWrap, E('h2', 'nr-field-label', 'ライバルの強さ'), levels); setup.append(difficultyWrap);
  const startGroup = E('div', 'nr-start-group');
  const ordered = button('', 'start', 'ordered', 'nr-primary');
  add(ordered, E('strong', '', '1から順番'), E('span', '', '小さい数字から、すばやく →'));
  const random = button('', 'start', 'random', 'nr-secondary');
  add(random, E('strong', '', 'ランダム'), E('span', '', 'お題を見て、見つけよう →'));
  add(startGroup, ordered, random); setup.append(startGroup);
  const settings = E('div', 'nr-settings');
  const sfx = button('効果音 ON', 'sfx', undefined, 'nr-setting');
  const motion = button('演出 通常', 'motion', undefined, 'nr-setting');
  add(settings, sfx, motion); setup.append(settings);
  const readyRecord = E('p', 'nr-ready-record'); setup.append(readyRecord);
  add(ready, intro, setup);

  const play = section('playing', 'nr-play');
  const hud = E('div', 'nr-hud');
  const youScore = E('strong', '', '0'), cpuScore = E('strong', '', '0');
  const youGoal = E('span', 'nr-score-note');
  const youHud = add(E('div', 'nr-score-card nr-you'), add(E('div'), E('span', 'nr-overline', 'YOU / リン'), youGoal), youScore);
  const cpuHud = add(E('div', 'nr-score-card nr-cpu'), add(E('div'), E('span', 'nr-overline', 'CPU / ルナ'), E('span', 'nr-score-note', '同じお題を探しています')), cpuScore);
  const target = E('strong', 'nr-target-number', '1');
  const targetWrap = add(E('div', 'nr-target'), E('span', 'nr-overline', 'この数字をさがそう'), target);
  add(hud, youHud, targetWrap, cpuHud);
  const boardWrap = E('div', 'nr-board-wrap');
  const board = E('div', 'nr-board'); board.setAttribute('role', 'group'); board.setAttribute('aria-label', '数字パネル 5行8列');
  const cells = Array.from({length: 40}, (_, index) => {
    const cell = E('button', 'nr-cell'); cell.type = 'button'; cell.dataset.index = index;
    const number = E('span', 'nr-cell-number'), owner = E('span', 'nr-cell-owner'), effect = E('span', 'nr-cell-effect');
    effect.setAttribute('aria-hidden', 'true'); add(cell, number, owner, effect);
    cell.addEventListener('pointerdown', event => {
      if (event.button !== 0 || !event.isPrimary || cell.disabled || state?.screen !== 'playing') return;
      event.preventDefault(); keyboardCell = index; cell.focus({preventScroll: true}); command('cell', undefined, index);
    });
    // Pointer input is already handled on down. detail=0 is keyboard/assistive activation.
    cell.addEventListener('click', event => {
      if (event.detail === 0 && !cell.disabled && state?.screen === 'playing') command('cell', undefined, index);
    });
    board.append(cell); return {cell, number, owner, effect, effectId: null};
  });
  add(boardWrap, board);
  const progressTrack = E('div', 'nr-round-progress'); progressTrack.setAttribute('role', 'progressbar'); progressTrack.setAttribute('aria-label', '見つけた数字');
  const progressFill = E('div'); progressTrack.append(progressFill);
  const stage = E('footer', 'nr-play-stage');
  const playRin = portrait('rin', 'RIN'), playKoh = portrait('koh', 'LUNA');
  const playStats = E('div', 'nr-play-stats');
  const elapsed = E('strong'), completed = E('strong'), mistakes = E('strong'), streak = E('strong');
  function stat(label, value) { return add(E('div', 'nr-stat'), E('span', '', label), value); }
  add(playStats, stat('TIME', elapsed), stat('見つけた', completed), stat('ミス', mistakes), stat('連続正解', streak));
  const cpuTrack = E('div', 'nr-cpu-timer'); cpuTrack.setAttribute('role', 'progressbar'); cpuTrack.setAttribute('aria-label', 'CPUが数字を見つけるまで'); cpuTrack.setAttribute('aria-valuemin', '0'); cpuTrack.setAttribute('aria-valuemax', '100');
  const cpuFill = E('div'); cpuTrack.append(cpuFill);
  const cpuClock = E('span', 'nr-cpu-clock');
  const feedback = E('p', 'nr-feedback', 'お題を見て、落ち着いて。');
  const hint = button('ヒントを見る', 'hint', undefined, 'nr-setting');
  const middle = add(E('div', 'nr-stage-middle'), playStats, add(E('div', 'nr-cpu-row'), cpuClock, cpuTrack), feedback, hint);
  const timedChain = window.createTimedChainView?.({E, add, portraits:[playRin,playKoh]});
  if (timedChain) middle.append(timedChain.root);
  add(stage, playRin.wrap, middle, playKoh.wrap); add(play, hud, boardWrap, progressTrack, stage);

  const countdown = section('countdown', 'nr-centered');
  const countLabel = E('h1'), countNumber = E('strong', 'nr-count-number');
  const countTitle = button('モード選択へ', 'title', undefined, 'nr-quiet');
  add(countdown, add(E('div', 'nr-count-card nr-surface'), E('span', 'nr-eyebrow', 'GET READY'), countLabel, countNumber, E('p', 'nr-muted', '合図で数字が現れます'), countTitle));

  const confirm = section('confirm', 'nr-centered');
  const confirmTitle = E('h1'), confirmCopy = E('p', 'nr-muted');
  const confirmYes = button('はい', 'yes', undefined, 'nr-primary'), confirmNo = button('いいえ', () => state?.confirm_action === 'pause' ? 'yes' : 'no', undefined, 'nr-secondary');
  const pausedActions = add(E('div', 'nr-pause-extras'), button('新しい配置でやり直す', 'retry'), button('モード選択へ', 'title'));
  const pauseSfx = button('効果音', 'sfx', undefined, 'nr-setting'), pauseMotion = button('演出', 'motion', undefined, 'nr-setting');
  const confirmCard = add(E('div', 'nr-dialog nr-surface'), E('span', 'nr-eyebrow', 'TAKE A BREATH'), confirmTitle, confirmCopy, add(E('div', 'nr-dialog-actions'), confirmYes, confirmNo), pausedActions, add(E('div', 'nr-settings'), pauseSfx, pauseMotion));
  add(confirm, confirmCard);

  const helpScreen = section('help', 'nr-centered');
  const instructions = E('ol', 'nr-instructions');
  for (const [heading, text] of [
    ['お題と同じ数字をタップ', '盤面はいつも5行×8列。1から順番、またはランダムなお題を探します。'],
    ['ライバルより先に見つけよう', '青いYOUがあなた、ピンクのCPUがルナ。先に見つけると1点。全体の6割で勝利です。'],
    ['ミスしても、すぐ次へ', 'まちがいは爆弾の演出でお知らせ。同じマスはすぐ押し直せます。正解後も待ち時間はありません。'],
    ['練習と休憩も、気軽に', 'ひとりで練習は時間制限なし。ヒントを使うと記録対象外になります。一時停止中はCPUも時計も止まります。'],
  ]) add(instructions, add(E('li'), E('h2', '', heading), E('p', '', text)));
  add(helpScreen, add(E('div', 'nr-help-card nr-surface'), E('span', 'nr-eyebrow', 'HOW TO PLAY'), E('h1', '', '遊び方'), instructions, E('p', 'nr-muted', 'PC：クリック、または矢印キー＋Enter。Escで一時停止。スマートフォンは横持ちがおすすめ。'), button('戻る', 'back', undefined, 'nr-primary')));

  const finished = section('finished', 'nr-centered');
  const resultRin = portrait('rin', 'RIN / YOU'), resultKoh = portrait('koh', 'LUNA / CPU');
  const resultTitle = E('h1'), resultTag = E('span', 'nr-eyebrow'), resultCopy = E('p', 'nr-muted');
  const resultScore = E('strong', 'nr-result-score');
  const resultStats = E('div', 'nr-result-stats');
  const resultTime = E('strong'), resultMiss = E('strong'), resultStreak = E('strong');
  add(resultStats, stat('タイム', resultTime), stat('ミス', resultMiss), stat('最大連続正解', resultStreak));
  const chainSummary = E('p', 'nr-muted'); resultStats.append(chainSummary);
  const award = E('div', 'nr-award'); const awardValue = E('strong');
  add(award, E('span', '', '✦ PERFECT BONUS ✦'), awardValue, E('small', '', '全問先取・ノーミスの特別賞'));
  const record = E('p', 'nr-record');
  const reviewButton = button('対戦を振り返る', 'review', undefined, 'nr-quiet');
  const resultCard = add(E('div', 'nr-result-card nr-surface'), resultTag, resultTitle,
    add(E('div', 'nr-result-duo'), resultRin.wrap, resultScore, resultKoh.wrap), resultCopy, resultStats, award, record,
    add(E('div', 'nr-result-actions'), button('もう一度遊ぶ', 'retry', undefined, 'nr-primary'), button('モード選択', 'title', undefined, 'nr-secondary')), reviewButton);
  finished.append(resultCard);

  const review = section('review', 'nr-centered');
  const reviewSummary = E('p', 'nr-muted'), history = E('ol', 'nr-history');
  add(review, add(E('div', 'nr-review-card nr-surface'), E('span', 'nr-eyebrow', 'ROUND INSIGHTS'), E('h1', '', '対戦を振り返る'), reviewSummary, history, button('結果へ戻る', 'back', undefined, 'nr-primary')));
  const screenMap = {home, ready, playing: play, countdown, resuming: countdown, confirm, help: helpScreen, finished, review};
  const shSettings = [];
  function settingsControls() {
    const effects=button('効果音','sfx',undefined,'nr-setting');
    const animation=button('演出','motion',undefined,'nr-setting');
    shSettings.push([effects,animation]);
    return add(E('div','nr-settings'),effects,animation);
  }
  const shiritori = window.createShiritoriView?.({section, E, add, button, portrait, command, settingsControls, onNavigationChange: update});
  if (shiritori) screenMap.shiritori = shiritori.page;
  const allPortraits = [[heroRin, 'left'], [heroKoh, 'right'], [playRin, 'left'], [playKoh, 'right'], [resultRin, 'left'], [resultKoh, 'right']];
  function select(buttons, values, value) { buttons.forEach((b, i) => b.setAttribute('aria-pressed', String(values[i] === value))); }
  function update() {
    const incoming = parseState(root.getAttribute('data-modern-state'));
    if (!incoming) { if (active) fallback(); return; }
    const focusedIndex = cells.findIndex(item => item.cell === document.activeElement);
    state = incoming;
    const changedScreen = previousScreen !== state.screen;
    app.dataset.screen = state.screen;
    app.dataset.kind = state.kind;
    app.dataset.reduced = String(state.reduced === true || media.matches);
    for (const element of new Set(Object.values(screenMap))) element.hidden = element !== screenMap[state.screen];
    const playing = state.screen === 'playing', battle = state.kind === 'battle';
    headerContext.textContent = state.screen === 'ready' ? 'ひと目で見つける、ひと勝負。' : `1–${state.max_number} · ${state.mode === 'ordered' ? '順番' : 'ランダム'}${battle ? ' · 対戦' : ' · 練習'}`;
    if (state.screen === 'home') headerContext.textContent = 'ゲームを選ぶ';
    if (state.screen === 'shiritori') { headerContext.textContent = '絵しりとり'; shiritori.update(state.shiritori); }
    sound.textContent = state.bgm ? '♪ ON' : '♪ OFF'; sound.setAttribute('aria-pressed', String(!!state.bgm));
    help.hidden = !['ready', 'help'].includes(state.screen); help.disabled = state.screen === 'help';
    const shPhase = state.screen === 'shiritori' ? state.shiritori?.phase : null;
    const shMenu = shPhase === 'intro' && !shiritori?.isOverlayOpen();
    gamesBack.hidden = !(state.screen === 'ready' || shMenu);
    if (shPhase) { help.hidden = shPhase !== 'intro'; help.disabled = shiritori.isOverlayOpen(); }
    const shPlaying = ['playing', 'blocked'].includes(shPhase);
    pause.hidden = !(playing || shPlaying); retry.hidden = !(playing || shPlaying);
    const reduced = state.reduced === true;
    sfx.textContent = pauseSfx.textContent = `効果音 ${state.sfx ? 'ON' : 'OFF'}`;
    sfx.setAttribute('aria-pressed', String(!!state.sfx)); pauseSfx.setAttribute('aria-pressed', String(!!state.sfx));
    motion.textContent = pauseMotion.textContent = `演出 ${reduced ? 'ひかえめ' : '通常'}`;
    motion.setAttribute('aria-pressed', String(reduced)); pauseMotion.setAttribute('aria-pressed', String(reduced));
    for (const [effects,animation] of shSettings) {
      effects.textContent=sfx.textContent; effects.setAttribute('aria-pressed',String(!!state.sfx));
      animation.textContent=motion.textContent; animation.setAttribute('aria-pressed',String(reduced));
    }
    select(kindButtons, ['battle', 'practice'], state.kind); select(rangeButtons, [10, 20, 30, 40], state.max_number); select(levelButtons, ['easy', 'normal', 'hard'], state.difficulty);
    difficultyWrap.hidden = !battle;
    kindDescription.textContent = battle ? `先に見つけると1点。${state.goal || Math.ceil(state.max_number * .6)}点以上で勝利！` : '自分のペースで、すべての数字を見つけよう。';
    readyRecord.textContent = state.bonus_bank ? `✦ 集めたボーナス ${integer(state.bonus_bank).toLocaleString()} pt` : 'いつでも一時停止できます。音量を調節して楽しもう。';
    for (const [p, side] of allPortraits) {
      const pose = state[side] || 'idle'; p.image.style.backgroundPosition = posePosition(pose); p.image.dataset.pose = pose;
    }
    target.textContent = state.target == null ? '✓' : state.target;
    youScore.textContent = battle ? integer(state.player_points) : integer(state.completed);
    cpuScore.textContent = battle ? integer(state.cpu_points) : integer(state.max_number);
    youGoal.textContent = battle ? `${integer(state.goal)}点で勝利` : '見つけた数字';
    cpuHud.hidden = !battle; youHud.dataset.practice = String(!battle);
    elapsed.textContent = formatTime(state.elapsed); completed.textContent = `${integer(state.completed)} / ${state.max_number}`;
    mistakes.textContent = integer(state.mistakes); streak.textContent = `${integer(state.streak)} 連続`;
    timedChain?.update(state.chain, battle, playing);
    progressTrack.setAttribute('aria-valuemin', '0'); progressTrack.setAttribute('aria-valuemax', String(state.max_number)); progressTrack.setAttribute('aria-valuenow', String(integer(state.completed)));
    progressFill.style.width = `${Math.min(100, integer(state.completed) / Math.max(1, state.max_number) * 100)}%`;
    cpuTrack.parentElement.hidden = !battle;
    const cpuProgress = Math.min(1, Math.max(0, finite(state.cpu_progress)));
    cpuFill.style.transform = `scaleX(${cpuProgress})`; cpuTrack.setAttribute('aria-valuenow', String(Math.round(cpuProgress * 100)));
    cpuClock.textContent = `CPU あと ${Math.max(0, finite(state.cpu_remaining)).toFixed(1)} 秒`;
    cpuTrack.dataset.urgent = String(cpuProgress > .75);
    hint.hidden = battle; hint.textContent = state.hint_used ? 'ヒント（記録対象外）' : 'ヒントを見る';
    let recent = '';
    const cpuCursor = playing && battle ? window.rivalCursor?.(40,8,state.cells.findIndex(c=>c.n===state.target),cpuProgress) : null;
    if (!playing) cells.forEach(item=>{ item.cell.dataset.cpuSelecting='false'; });
    state.cells.forEach((data, index) => {
      const item = cells[index], claimed = !!data.owner, empty = data.n == null;
      item.number.textContent = empty ? '' : data.n;
      item.cell.disabled = !playing || empty || claimed;
      item.cell.dataset.owner = data.owner || ''; item.cell.dataset.empty = String(empty);
      item.cell.dataset.feedback = data.effect || '';
      item.cell.dataset.hint = String(playing && index === state.hint_index);
      item.cell.dataset.cpuSelecting = String(index === cpuCursor);
      item.owner.textContent = data.owner === 'cpu' ? 'CPU' : claimed ? '✓' : '';
      item.cell.setAttribute('aria-label', empty ? '空のマス' : `${data.n}${data.owner === 'cpu' ? ' CPUが獲得' : claimed ? ' 獲得済み' : ''}`);
      if (data.effect && data.effect_id !== item.effectId) {
        item.effectId = data.effect_id;
        const type = data.effect === 'wrong' ? 'wrong' : 'correct';
        const effect = E('span', `nr-fx nr-fx-${type}`);
        if (type === 'wrong') add(effect, E('i', 'nr-bomb'), E('i', 'nr-burst'));
        else add(effect, E('i', 'nr-ring'), E('i', 'nr-spark', '✦'));
        item.effect.replaceChildren(effect);
      }
      if (data.effect === 'wrong') recent = 'ちがう数字！お題を確認して、すぐ押し直そう。';
      else if (data.effect === 'correct' && !recent) recent = 'ナイス！次のお題も、すぐに見つけよう。';
    });
    feedback.textContent = recent || (state.streak >= 3 ? `${state.streak}連続正解！いいリズム。` : battle ? '青はあなた、ピンクはCPU。先に見つけよう。' : 'あわてず、ひとつずつ。');
    if (playing && focusedIndex >= 0 && cells[focusedIndex].cell.disabled) {
      const next = nextPlayable(cells.map(item => !item.cell.disabled), focusedIndex, 'ArrowRight');
      if (next >= 0) { keyboardCell = next; cells[next].cell.focus({preventScroll: true}); }
    }
    countLabel.textContent = state.screen === 'resuming' ? 'まもなく再開' : '準備はいい？';
    countTitle.hidden = state.screen === 'resuming';
    countNumber.textContent = Math.max(1, Math.ceil(finite(state.countdown, 3)));
    const isPause = state.confirm_action === 'pause';
    confirmTitle.textContent = isPause ? 'ひと休みしよう' : state.confirm_action === 'retry' ? 'やり直しますか？' : 'モード選択に戻りますか？';
    confirmCopy.textContent = isPause ? 'タイマーもライバルも止まっています。準備ができたら再開しよう。' : '現在のプレイを終了します。';
    confirmYes.hidden = isPause; confirmNo.textContent = isPause ? 'プレイを続ける' : 'キャンセル';
    confirmYes.textContent = state.confirm_action === 'retry' ? 'やり直す' : '戻る'; pausedActions.hidden = !isPause;
    resultTag.textContent = state.perfect ? 'PERFECT VICTORY' : battle ? state.won ? 'YOU WIN' : 'NEXT CHALLENGE' : 'COMPLETE';
    resultTitle.textContent = state.perfect ? 'パーフェクト！' : battle ? state.won ? 'あなたの勝利！' : 'ナイスチャレンジ！' : 'ぜんぶ見つけた！';
    resultScore.textContent = battle ? `${integer(state.player_points)} : ${integer(state.cpu_points)}` : `${integer(state.completed)} / ${state.max_number}`;
    chainSummary.textContent = state.chain?.you && state.chain?.cpu ? `最大${state.chain.you.best}連鎖 · ${state.chain.you.bonus}連鎖ボーナス${battle ? ` ／ CPU最大${state.chain.cpu.best}連鎖 · ${state.chain.cpu.bonus}ボーナス` : ''}` : '';
    resultCopy.textContent = battle ? state.won ? '見つける力が、勝利につながった。' : 'ひと呼吸して、次の勝負へ。' : 'ひとつずつの発見が、スピードになる。';
    resultTime.textContent = formatTime(state.elapsed); resultMiss.textContent = `${integer(state.mistakes)} 回`; resultStreak.textContent = `${integer(state.max_streak)} 回`;
    award.hidden = !state.perfect; awardValue.textContent = `+ ${integer(state.bonus).toLocaleString()} pt`;
    resultCard.dataset.perfect = String(!!state.perfect);
    record.textContent = state.hint_used ? 'ヒント使用のため、ベスト記録には保存されません。' : state.is_new_best ? '✦ 自己ベスト更新！' : battle && state.best_points != null ? `自己ベスト ${state.best_points} 点` : state.best_time != null ? `自己ベスト ${formatTime(state.best_time)}` : '';
    if (state.screen === 'finished' && state.storage_saved === false) record.textContent += ' このブラウザに保存できませんでした。記録はページを閉じると失われる場合があります。';
    reviewButton.hidden = !battle;
    if (state.screen === 'review') {
      const rows = Array.isArray(state.history) ? state.history : [];
      const key = JSON.stringify(rows);
      if (key !== historyKey) {
        historyKey = key; history.replaceChildren();
        for (const [index, row] of rows.entries()) {
          const item = E('li', row.owner === 'cpu' ? 'nr-history-cpu' : 'nr-history-you');
          add(item, E('span', 'nr-history-index', String(index + 1).padStart(2, '0')), E('strong', '', row.number), E('span', '', row.owner === 'cpu' ? 'CPU' : 'YOU'), E('span', '', formatTime(row.seconds)));
          history.append(item);
        }
      }
      const own = rows.filter(row => row.owner === 'you');
      reviewSummary.textContent = own.length ? `あなたが見つけた数字：${own.length}個。最速 ${formatTime(Math.min(...own.map(row => finite(row.seconds))))}。青があなた、ピンクがCPUです。` : 'ピンクがCPUの獲得した数字です。ゆったりモードで練習してみよう。';
    }
    const nextAnnouncement = playing ? `次の数字は${state.target}。${integer(state.completed)}個見つけました。ミス${integer(state.mistakes)}回。` : state.screen === 'finished' ? `${resultTitle.textContent} ${resultScore.textContent}` : state.screen === 'confirm' ? confirmTitle.textContent : '';
    if (nextAnnouncement !== announcement) { announcement = nextAnnouncement; live.textContent = announcement; }
    if (changedScreen) {
      screenMap[state.screen].scrollTop = 0;
      if (previousScreen && document.activeElement && app.contains(document.activeElement) && document.activeElement.closest('[hidden]')) {
        const focusTarget = screenMap[state.screen].querySelector('h1, .nr-target, button:not(:disabled)');
        if (focusTarget) { if (focusTarget.tagName !== 'BUTTON') focusTarget.tabIndex = -1; focusTarget.focus({preventScroll: true}); }
      }
    }
    previousScreen = state.screen;
    // Reveal only after a whole valid snapshot rendered successfully.
    if (!active) {
      active = true; app.hidden = false; root.setAttribute('data-modern-active', 'true');
      root.setAttribute('data-modern-ready', 'true');
      if (window.parent !== window) window.parent.postMessage({type: 'number-rush-modern-ready'}, location.origin);
    }
  }
  function fallback() {
    active = false; app.hidden = true; root.removeAttribute('data-modern-active');
    root.setAttribute('data-modern-ready', 'false');
    if (window.parent !== window) window.parent.postMessage({type: 'number-rush-modern-fallback'}, location.origin);
  }
  function safeUpdate() {
    try { update(); } catch (error) { fallback(); console.warn('Modern view unavailable; using Pyxel.', error); }
  }
  app.addEventListener('keydown', event => {
    if (state?.screen === 'playing') {
      if (event.key === 'Escape') { event.preventDefault(); command('pause'); }
      else if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) {
        event.preventDefault();
        const focused = cells.findIndex(item => item.cell === document.activeElement);
        const next = nextPlayable(cells.map(item => !item.cell.disabled), focused >= 0 ? focused : keyboardCell, event.key);
        if (next >= 0) { keyboardCell = next; cells[next].cell.focus({preventScroll: true}); }
      } else if ((event.key === 'Enter' || event.key === ' ') && document.activeElement?.tagName !== 'BUTTON') {
        event.preventDefault();
        const index = !cells[keyboardCell].cell.disabled ? keyboardCell : cells.findIndex(item => !item.cell.disabled);
        if (index >= 0 && !event.repeat) { keyboardCell = index; cells[index].cell.focus({preventScroll: true}); command('cell', undefined, index); }
      }
    }
    // Prevent Pyxel's legacy key handlers from processing the same event.
    event.stopPropagation();
  });
  new MutationObserver(records => {
    if (records.some(record => record.attributeName === 'data-modern-ready') && root.getAttribute('data-modern-ready') === 'false') {
      // Do not re-enable from the stale snapshot that preceded a backend error.
      if (active) fallback();
      return;
    }
    if (records.some(record => record.attributeName === 'data-modern-state')) safeUpdate();
  }).observe(root, {attributes: true, attributeFilter: ['data-modern-state', 'data-modern-ready']});
  media.addEventListener('change', () => { if (active) safeUpdate(); });
  safeUpdate();
})();
