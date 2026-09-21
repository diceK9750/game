const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {availableViewport}=require('../viewport.js');
test('embedded browser visual height and rotation fallback preserve usable dimensions',()=>{
  assert.deepEqual(availableViewport(undefined,390,664),{width:390,height:664,left:0,top:0});
  assert.deepEqual(availableViewport({width:390,height:510,offsetTop:12},390,664),{width:390,height:510,left:0,top:12});
  assert.deepEqual(availableViewport({width:0,height:NaN,offsetTop:-2},844,290),{width:844,height:290,left:0,top:0});
});
test('shared mobile stylesheet is deployed last and handles height, dialogs and accessible overflow',()=>{
  const css=fs.readFileSync(require.resolve('../mobile-layout.css'),'utf8');
  const html=fs.readFileSync(require.resolve('../player.html'),'utf8');
  const pages=fs.readFileSync(require.resolve('../.github/workflows/pages.yml'),'utf8');
  assert.ok(html.indexOf('mobile-layout.css')>html.indexOf('shiritori-ui.css'));
  assert.match(pages,/mobile-layout\.css/);
  assert.match(css,/max-height: 700px/);
  assert.match(css,/max-height: 360px/);
  assert.match(css,/max-height: calc\(100dvh - 60px\)/);
  assert.match(css,/overflow: auto/);
  assert.match(css,/min-height: 44px/);
});

test('playing surfaces cannot scroll and board tracks can shrink to remaining height — shared composition', () => {
 const mobile=fs.readFileSync(require.resolve('../mobile-layout.css'),'utf8');
 const css=fs.readFileSync(require.resolve('../character-layout.css'),'utf8');
 assert.match(mobile,/\.nr-play, \.sh-page\[data-layout='play'\].*overflow: clip/);
 assert.ok(css.includes('grid-template-rows: var(--hud-block) minmax(0, 1fr)'));
 assert.ok(css.includes('aspect-ratio: 1 / 1'));
 const view=fs.readFileSync(require.resolve('../shiritori-ui.js'),'utf8');
 assert.ok(view.includes("dictionaryOpen || helpOpen ? 'document' : live ? 'play'"));
});

test('countdown and results are fitted surfaces, not scrolling documents',()=>{
  const css=fs.readFileSync(require.resolve('../mobile-layout.css'),'utf8');
  assert.match(css,/\.nr-count-card, \.nr-result-card \{ max-height: 100%; overflow: clip/);
  assert.match(css,/\.sh-page\[data-layout='result'\], \.sh-page\[data-layout='dialog'\] \{ overflow: clip/);
  assert.match(css,/\.sh-result details\[open\] \{ overflow: auto/);
  assert.match(css,/\.nr-result-card \{ grid-template-columns: 1fr 1fr/);
  assert.match(css,/\.nr-result-card > \.nr-result-actions \{ grid-column: 2 !important/);
  assert.match(css,/\.nr-instructions, \.nr-history, \.nr-help-card \.sh-guide \{ flex: 1 1 auto; min-height: 0; overflow: auto/);
});

test('short-landscape hint restores ≥44px tap (not modern-ui 36px chip) — shared composition', () => {
 const css=fs.readFileSync(require.resolve('../character-layout.css'),'utf8');
 assert.match(css,/\.game-hud \.nr-hint \{[^}]*position: static; min-height: 44px; min-width: 44px/);
 assert.ok(!css.includes('min-height: 32px'));
 assert.ok(!css.includes('.nr-hint { position: absolute'));
});

test('short max-height toolbar pause/help restores ≥44px (not modern-ui 34) (#109)', () => {
  const mobile = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const modern = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  // modern-ui short max-height:500 source itself stays ≥44 (was 34) for cascade safety.
  assert.match(modern, /@media \(max-height: 500px\)[\s\S]*?\.nr-toolbar \.nr-button \{ min-height: 44px;/);
  assert.match(modern, /@media \(max-height: 500px\)[\s\S]*?\.nr-icon-button \{ min-width: 44px;/);
  // Target the toolbar rule line (not the early home-card max-height:500 block).
  const toolbarRule = modern.match(/\.nr-toolbar \.nr-button \{ min-height: \d+px; padding: 5px 12px; font-size: 11px !important; \} \.nr-icon-button \{ min-width: \d+px; \}/);
  assert.ok(toolbarRule, 'modern-ui short toolbar rule present');
  assert.match(toolbarRule[0], /min-height: 44px/);
  assert.match(toolbarRule[0], /min-width: 44px/);
  assert.ok(!/34px/.test(toolbarRule[0]), 'no 34px left in short toolbar rule');
  // mobile-layout compact override still ≥44; extreme-short ≤360 stays densified 32.
  assert.match(mobile, /#modern-app \.nr-toolbar \.nr-button \{ min-height: 44px; min-width: 44px/);
  assert.match(mobile, /@media \(orientation: landscape\) and \(max-height: 360px\)[\s\S]*?#modern-app \.nr-toolbar \.nr-button \{ min-height: 44px; min-width: 44px/);
  assert.match(player, /modern-ui\.css\?v=count-tap-110-1/);
  assert.match(player, /mobile-layout\.css\?v=shared-arena-114-2/);
  assert.match(index, /player\.html\?v=shared-arena-114-2/);
});

test('short max-height countdown control restores ≥44px (not modern-ui 36) (#110)', () => {
  const mobile = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const modern = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  // modern-ui short max-height:500 source itself stays ≥44 (was 36) for cascade safety.
  assert.match(modern, /@media \(max-height: 500px\)[\s\S]*?\.nr-count-card \.nr-button \{ margin-top: 10px; min-height: 44px; \}/);
  const countRule = modern.match(/\.nr-count-card \.nr-button \{ margin-top: 10px; min-height: \d+px; \}/);
  assert.ok(countRule, 'modern-ui short count-card button rule present');
  assert.match(countRule[0], /min-height: 44px/);
  assert.ok(!/min-height: 36px/.test(countRule[0]), 'no 36px left in short count-card button rule');
  // mobile-layout compact override still ≥44; leave ≤360 densify alone.
  assert.match(mobile, /\.nr-count-card \.nr-button \{ margin-top: 6px; min-height: 44px; \}/);
  assert.match(player, /modern-ui\.css\?v=count-tap-110-1/);
  assert.match(player, /mobile-layout\.css\?v=shared-arena-114-2/);
  assert.match(index, /player\.html\?v=shared-arena-114-2/);
});

test('short landscape parks hint beside HUD so board cells can keep ~44px taps — shared composition', () => {
 const css=fs.readFileSync(require.resolve('../character-layout.css'),'utf8');
 assert.match(css,/\.game-hud \{[\s\S]*?grid-template-columns: minmax\(0, 1fr\) minmax\(0, 1fr\)/);
 assert.ok(css.includes('contain: size'));
 assert.ok(css.includes('overflow: auto'));
});

test('short-landscape parks numbers round-progress on board row — shared composition', () => {
 const css=fs.readFileSync(require.resolve('../character-layout.css'),'utf8');
 assert.match(css,/\[data-game-layout\] > \.nr-round-progress \{ position: absolute; bottom: 0; inset-inline: 0; height: 2px/);
 const js=fs.readFileSync(require.resolve('../modern-ui.js'),'utf8');
 assert.ok(js.includes('add(play, playHud, stage, progressTrack)'));
});

test('short-landscape densifies numbers play stats + restores compact feedback — shared composition', () => {
 const css=fs.readFileSync(require.resolve('../character-layout.css'),'utf8');
 assert.match(css,/\.game-hud \.nr-feedback \{[\s\S]*?display: block; white-space: normal/);
 assert.match(css,/\.game-hud \.nr-feedback \{[\s\S]*?overflow: visible/);
 assert.match(css,/\.game-hud \.nr-cpu-clock \{ font-size: 11px/);
});

test('landscape bounds both tracks so supplementary text cannot squeeze the HUD — shared composition', () => {
 const css=fs.readFileSync(require.resolve('../character-layout.css'),'utf8');
 assert.ok(css.includes('grid-template-columns: minmax(0, 1fr) minmax(0, 1fr)'));
 assert.ok(css.includes('grid-template-rows: var(--hud-block) minmax(0, 1fr)'));
 assert.ok(css.includes('overflow-wrap: anywhere'));
});

test('landscape chains, feedback and hint have explicit grid positions — shared composition', () => {
 const css=fs.readFileSync(require.resolve('../character-layout.css'),'utf8');
 assert.match(css,/\.game-hud \.timed-chains \{ grid-column: 1 \/ -1; grid-row: 3/);
 assert.match(css,/\.game-hud \.nr-feedback \{\s*grid-column: 1 \/ -1; grid-row: 4/);
 assert.match(css,/\.game-hud \.nr-hint \{ grid-column: 2; grid-row: 1 \/ 3/);
});

test('compact portrait practice stage densifies + caps timed-chains after cpu-row hide — shared composition', () => {
 const css=fs.readFileSync(require.resolve('../character-layout.css'),'utf8');
 assert.ok(!css.includes('.nr-stage-middle:has('),'practice shares battle geometry');
 assert.ok(css.includes('grid-template-rows: var(--cast-lane) minmax(0, 1fr) var(--cast-lane)'));
 const js=fs.readFileSync(require.resolve('../modern-ui.js'),'utf8');
 assert.ok(js.includes('cpuTrack.parentElement.hidden = !battle'));
});

test('shell and board disable double-tap zoom without blocking pan or Pyxel canvas', () => {
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  assert.match(css, /#modern-app \{[^}]*touch-action: manipulation/);
  assert.match(css, /\.nr-screen, \.nr-play, \.nr-board-wrap, \.nr-board, \.sh-page, \.sh-board, \.sh-board-space \{\s*touch-action: manipulation/);
  assert.match(css, /#modern-app button \{[^}]*touch-action: manipulation/);
  assert.match(css, /\.nr-cell \{[^}]*touch-action: manipulation/);
  assert.match(player, /html, body \{[^}]*touch-action: manipulation/);
  assert.match(player, /canvas \{ touch-action: none;/);
  assert.match(player, /modern-ui\.css\?v=count-tap-110-1/);
  assert.match(index, /html, body \{[^}]*touch-action: manipulation/);
  assert.match(index, /main, #game-box, #game-frame \{ touch-action: manipulation/);
  // Scrollable reading panes keep overflow:auto (manipulation still allows pan).
  const mobile = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  assert.match(mobile, /\.nr-instructions, \.nr-history, \.nr-help-card \.sh-guide \{[^}]*overflow: auto/);
  assert.ok(!/touch-action:\s*none/.test(mobile));
});

test('extreme-short landscape compresses chrome to reclaim board cell height — shared composition', () => {
 const mobile=fs.readFileSync(require.resolve('../mobile-layout.css'),'utf8');
 const css=fs.readFileSync(require.resolve('../character-layout.css'),'utf8');
 assert.ok(mobile.includes('min-height: 44px; min-width: 44px'));
 assert.ok(css.includes('--hud-block: clamp(90px, 16dvh, 120px)'));
 assert.ok(css.includes('minmax(0, 1fr)'));
 assert.ok(!css.includes('667px'));
});

test('narrow portrait tightens board gutters for wider 5×8 cell taps — shared composition', () => {
 const css=fs.readFileSync(require.resolve('../character-layout.css'),'utf8');
 assert.ok(css.includes('--board-cols: 8; --board-rows: 5; --board-gap: 4px'));
 assert.ok(css.includes('100cqw - (var(--board-cols) - 1)'));
 assert.ok(css.includes('100cqh - (var(--board-rows) - 1)'));
 assert.ok(css.includes('aspect-ratio: 1 / 1'));
});

test('host and player lock overscroll; play posts scroll-lock to the shell', () => {
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const js = fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8');
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const viewport = fs.readFileSync(require.resolve('../viewport.js'), 'utf8');
  assert.match(index, /html, body \{[^}]*overscroll-behavior: none/);
  assert.match(player, /html, body \{[^}]*overscroll-behavior: none/);
  assert.match(index, /html\[data-scroll-lock="true"\]/);
  assert.match(css, /#modern-app\[data-scroll-lock='true'\]/);
  assert.match(js, /number-rush-scroll-lock/);
  assert.match(js, /shouldLockPlayScroll/);
  assert.match(js, /passive: false/);
  assert.match(viewport, /number-rush-scroll-lock/);
  assert.match(player, /modern-ui\.js\?v=shared-arena-114-2/);
  assert.match(index, /viewport\.js\?v=5-scroll-lock/);
});

test('host owns device insets; modern shell top/home only when standalone', () => {
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  const css = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const mobile = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const js = fs.readFileSync(require.resolve('../modern-ui.js'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  // Host main pads all four sides (MOBILE-QA).
  assert.match(index, /safe-area-inset-top/);
  assert.match(index, /safe-area-inset-bottom/);
  assert.match(index, /safe-area-inset-left/);
  assert.match(index, /safe-area-inset-right/);
  // Embedded path: base shell gutters are fixed — no env() re-stack on #modern-app alone.
  assert.match(css, /#modern-app \{[^}]*padding: 0 12px/);
  // Standalone player: top + home (+ sides) parity behind :not(data-host-insets).
  assert.match(css, /html:not\(\[data-host-insets='true'\]\) #modern-app/);
  assert.match(css, /safe-area-inset-top/);
  assert.match(css, /padding-bottom: env\(safe-area-inset-bottom/);
  // Children must not re-apply home inset (would double with shell or host).
  assert.doesNotMatch(css, /\.nr-screen \{[^}]*env\(safe-area-inset-bottom\)/);
  assert.doesNotMatch(css, /\.nr-play \{[^}]*env\(safe-area-inset-bottom\)/);
  assert.match(js, /markHostInsets/);
  assert.match(js, /data-host-insets/);
  assert.ok(mobile.includes("html:not([data-host-insets='true']) #modern-app"));
  assert.match(player, /modern-ui\.css\?v=count-tap-110-1/);
  assert.match(player, /modern-ui\.js\?v=shared-arena-114-2/);
  assert.match(player, /mobile-layout\.css\?v=shared-arena-114-2/);
});


test('mobile result keeps primary score heavier than secondary stats (#73)', () => {
  const css = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  assert.match(css, /\.nr-result-score \{ font-size: 34px; font-weight: 850; \}/);
  assert.match(css, /\.nr-result-stats \.nr-stat > strong \{ font-size: 12px; font-weight: 650; color: var\(--nr-muted\); \}/);
  assert.match(css, /\.sh-result-cast > \.nr-result-score \{ font-size: 34px; \}/);
  assert.match(player, /mobile-layout\.css\?v=shared-arena-114-2/);
});


test('mobile result keeps award/record contrast readable on compact cards', () => {
  const css = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  assert.match(css, /\.nr-result-card \.nr-award > span \{ font-size: 9px/);
  assert.match(css, /\.nr-result-card \.nr-record\[data-record='new'\] \{ font-size: 11px; padding: 3px 8px; \}/);
  assert.match(player, /mobile-layout\.css\?v=shared-arena-114-2/);
});


test('short-landscape result stacks primary score above cast so award cannot collide (#75)', () => {
  const css = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  // Score full-width above cast portraits (order:-1 + flex-basis 100%).
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 500px\)/);
  assert.match(css, /\.nr-result-duo \{[\s\S]*?flex-wrap: wrap/);
  assert.match(css, /\.nr-result-duo \.nr-result-score \{[\s\S]*?flex: 1 0 100%; order: -1/);
  assert.match(css, /\.nr-result-duo \.nr-result-score \{[\s\S]*?font-size: 30px; font-weight: 850/);
  assert.match(css, /\.nr-result-duo \.nr-character \{ width: clamp\(22px, 7dvh, 40px\)/);
  // #81: practice solo under stacked score — denser centered, no empty rival gap.
  assert.match(css, /\.nr-result-duo:has\(> \.nr-koh\[hidden\]\) \{ gap: 2px; justify-content: center; \}/);
  // Award stays compact under score (dark panel from #74); no cast overlap.
  assert.match(css, /\.nr-result-card \.nr-award \{ padding: 3px 5px; margin-top: 0/);
  assert.match(css, /\.nr-result-card \.nr-award > strong \{ font-size: 16px; line-height: 1\.1/);
  // Extreme-short drops cast; score+award remain.
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 360px\)/);
  assert.match(css, /\.nr-result-duo \.nr-character \{ display: none/);
  assert.match(css, /\.nr-result-duo \.nr-result-score \{ font-size: 28px/);
  // Two-column result grid + replay actions column intact (#17/#19 focus target).
  assert.match(css, /\.nr-result-card > \.nr-result-actions \{ grid-column: 2 !important/);
  assert.match(player, /mobile-layout\.css\?v=shared-arena-114-2/);
  assert.match(index, /player\.html\?v=shared-arena-114-2/);
});

test('short-landscape result packs secondary stats denser beside stacked score (#76)', () => {
  const css = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 500px\)/);
  // Fixed 3-col pack (no flex wrap + chain summary row crowding half-width).
  assert.match(css, /\.nr-result-stats \{[\s\S]*?grid-template-columns: repeat\(3, minmax\(0, 1fr\)\)/);
  assert.match(css, /\.nr-result-stats \.nr-stat > strong \{ font-size: 11px; font-weight: 650; color: var\(--nr-muted\); \}/);
  assert.match(css, /\.nr-result-stats > \.nr-muted \{ display: none/);
  // Stats stay in right column beside #75 stacked score; actions column intact.
  assert.match(css, /\.nr-result-stats \{ grid-column: 2 !important; grid-row: 1 \/ 3 !important; \}/);
  assert.match(css, /\.nr-result-card > \.nr-result-actions \{ grid-column: 2 !important/);
  // Extreme-short keeps pack, slightly tighter.
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 360px\)/);
  assert.match(css, /\.nr-result-stats \.nr-stat > strong \{ font-size: 10px; \}/);
  assert.match(player, /mobile-layout\.css\?v=shared-arena-114-2/);
  assert.match(index, /player\.html\?v=shared-arena-114-2/);
});

test('short-landscape shiritori packs secondary stats denser (#77)', () => {
  const css = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const sh = fs.readFileSync(require.resolve('../shiritori-ui.css'), 'utf8');
  const js = fs.readFileSync(require.resolve('../shiritori-ui.js'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 500px\)/);
  // Fixed 3-col pack; hide chain-summary wrap crowding half-width column (#76 parity).
  assert.match(css, /\.sh-result-secondary \{[\s\S]*?grid-template-columns: repeat\(3, minmax\(0, 1fr\)\)/);
  assert.match(css, /\.sh-result-secondary \.nr-stat > strong \{ font-size: 11px; font-weight: 650; color: var\(--nr-muted\); \}/);
  assert.match(css, /\.sh-result-secondary > \.nr-muted \{ display: none/);
  // Score + secondary stay left; replay actions column intact (#19).
  assert.match(css, /\.sh-result > h1, \.sh-result > p, \.sh-result-cast \{ grid-column: 1/);
  assert.match(css, /\.sh-result > \.nr-result-actions \{ grid-column: 2/);
  // Extreme-short tightens like numbers #76.
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 360px\)/);
  assert.match(css, /\.sh-result-secondary \.nr-stat > strong \{ font-size: 10px; \}/);
  // Desktop secondary is packed .nr-stat + muted (not a single middot paragraph).
  assert.match(js, /E\('div', 'sh-result-secondary'\)/);
  assert.match(sh, /\.sh-result-secondary \.nr-stat > strong/);
  assert.match(player, /mobile-layout\.css\?v=shared-arena-114-2/);
  assert.match(player, /shiritori-ui\.css\?v=sh-solo-cast-84-1/);
  assert.match(player, /shiritori-ui\.js\?v=shared-arena-114-2/);
  assert.match(index, /player\.html\?v=shared-arena-114-2/);
});


test('short-landscape / mobile review-history density: compact summary + capped log (#78)', () => {
  const css = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  const sh = fs.readFileSync(require.resolve('../shiritori-ui.css'), 'utf8');
  const js = fs.readFileSync(require.resolve('../shiritori-ui.js'), 'utf8');
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 500px\)/);
  // Compact summary still ≥44px (#59 hit target preserved).
  assert.match(css, /\.sh-result-history summary \{[\s\S]*?min-height: 44px; padding: 4px 0/);
  assert.match(sh, /\.sh-result-history summary \{[^}]*min-height: 44px/);
  // Capped open log / details so packed #76/#77 stats are not crowded out.
  assert.match(css, /\.sh-result \.sh-log \{[\s\S]*?max-height: min\(72px, 16dvh\)/);
  assert.match(css, /\.sh-result-history\[open\] \{[\s\S]*?max-height: min\(116px, 26dvh\)/);
  // Numbers review list denser + hard height cap.
  assert.match(css, /\.nr-history \{[\s\S]*?max-height: min\(120px, 32dvh\)/);
  assert.match(css, /\.nr-history strong \{ font-size: 13px/);
  assert.match(css, /\.nr-review-card > \.nr-muted \{ font-size: 10px/);
  // Extreme-short tightens further.
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 360px\)/);
  assert.match(css, /\.sh-result \.sh-log \{ max-height: min\(56px, 14dvh\)/);
  assert.match(css, /\.nr-history \{ max-height: min\(88px, 28dvh\)/);
  // #59 Tab inclusion of history summary stays in JS (no Esc/Tab micro-parity churn).
  assert.match(js, /else if \(node\.tagName === 'SUMMARY'\)/);
  assert.match(js, /onHistorySummary/);
  assert.match(js, /sh-result-history/);
  assert.match(player, /mobile-layout\.css\?v=shared-arena-114-2/);
  assert.match(index, /player\.html\?v=shared-arena-114-2/);
});


test('short-landscape result-actions / dict density: stack buttons + pin dict (#79)', () => {
  const css = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  const js = fs.readFileSync(require.resolve('../shiritori-ui.js'), 'utf8');
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 500px\)/);
  // Column-stack primary actions so half-width column isn't side-by-side cramped.
  assert.match(css, /\.nr-result-actions \{[\s\S]*?flex-direction: row; gap: 3px/);
  // Dict is one grid row (not stretch 2\/4) under actions; history stays full-width row 4.
  assert.match(css, /\.sh-result > \.nr-result-actions \{ grid-column: 2; grid-row: 1 \/ 3/);
  assert.match(css, /\.sh-result > \.nr-button \{ grid-column: 2; grid-row: 3; align-self: stretch/);
  assert.match(css, /\.sh-result > details \{ grid-column: 1; grid-row: 4/);
  // Numbers: actions + battle-only review quiet stay stacked in right column.
  assert.match(css, /\.nr-result-card > \.nr-result-actions \{ grid-column: 2 !important; grid-row: 3 !important/);
  assert.match(css, /\.nr-result-card > \.nr-quiet \{ grid-column: 2 !important; grid-row: 4 !important/);
  // Keep ≥44px hit targets (replay #17/#19).
  assert.match(css, /\.nr-result-actions > \.nr-button,[\s\S]*?min-height: 44px; padding: 4px 6px; font-size: 11px/);
  // Extreme-short tightens padding/type; still ≥44px.
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 360px\)/);
  assert.match(css, /\.nr-result-actions \{ gap: 2px/);
  assert.match(css, /\.nr-result-actions > \.nr-button,[\s\S]*?min-height: 44px; padding: 3px 5px; font-size: 10px/);
  // Dict button still appended on finished result (DOM order unchanged).
  assert.match(js, /result\.append\(dictResult\)/);
  assert.match(js, /読み方ずかん/);
  assert.match(player, /mobile-layout\.css\?v=shared-arena-114-2/);
  assert.match(index, /player\.html\?v=shared-arena-114-2/);
});


test('short-landscape shiritori play HUD/prompt density reclaim without clipping — shared composition', () => {
 const css=fs.readFileSync(require.resolve('../character-layout.css'),'utf8');
 const js=fs.readFileSync(require.resolve('../shiritori-ui.js'),'utf8');
 assert.ok(js.includes("stage.dataset.gameLayout = 'true'"));
 assert.ok(js.includes("add(stage, add(E('div', 'game-hud'), information, auxiliary), arena)"));
 assert.ok(css.includes('.game-hud .sh-status'));
 assert.ok(css.includes('white-space: normal; overflow: visible'));
});

test('ready solo hero-cast denser/centered on compact layout (#89)', () => {
  const css = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const modern = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  assert.match(css, /\.nr-hero-cast:has\(> \.nr-koh\[hidden\]\) \{ gap: 2px; justify-content: center; \}/);
  assert.match(css, /\.nr-hero-cast:has\(> \.nr-koh\[hidden\]\) \.nr-character \{ width: clamp\(48px, 14dvh, 96px\); \}/);
  assert.match(modern, /\.nr-hero-cast:has\(> \.nr-koh\[hidden\]\) \{ gap: 12px; justify-content: center; \}/);
  assert.match(player, /mobile-layout\.css\?v=shared-arena-114-2/);
  assert.match(player, /modern-ui\.css\?v=count-tap-110-1/);
  assert.match(index, /player\.html\?v=shared-arena-114-2/);
});
