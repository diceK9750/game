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

test('playing surfaces cannot scroll and board tracks can shrink to remaining height',()=>{
  const css=fs.readFileSync(require.resolve('../mobile-layout.css'),'utf8');
  assert.match(css,/\.nr-play, \.sh-page\[data-layout='play'\].*overflow: clip/);
  assert.match(css,/\.nr-board-wrap \{ flex: 1 1 0; min-height: 0/);
  assert.match(css,/grid-template-rows: repeat\(5, minmax\(0, 1fr\)\)/);
  assert.ok(!/\.nr-play\s*\{[^}]*overflow: auto/.test(css));
  assert.ok(!/\.nr-board-wrap\s*\{[^}]*min-height: (134|180|244)px/.test(css));
  const view=fs.readFileSync(require.resolve('../shiritori-ui.js'),'utf8');
  assert.match(view,/dictionaryOpen \|\| helpOpen \? 'document' : live \? 'play'/);
  assert.match(view,/s\.phase === 'finished' \? 'result' : 'dialog'/);
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

test('short landscape parks hint beside HUD so board cells can keep ~44px taps', () => {
  const css = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 500px\)/);
  assert.match(css, /\.nr-play \{\s*display: grid;/);
  assert.match(css, /grid-template-columns: minmax\(0, 1fr\) auto/);
  assert.match(css, /\.nr-play-stage \{\s*grid-column: 2; grid-row: 1/);
  assert.match(css, /\.nr-board-wrap \{ grid-column: 1 \/ -1; grid-row: 2/);
  assert.match(css, /\.nr-stage-middle > \.nr-hint \{\s*flex: 0 0 auto; min-height: 44px; min-width: 44px/);
  assert.match(css, /#modern-app \.nr-toolbar \.nr-button \{ min-height: 44px; min-width: 44px/);
  assert.match(css, /\.nr-dialog \.nr-button \{ min-height: 44px/);
  const html = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  assert.match(html, /mobile-layout\.css\?v=ready-hero-solo-89-1/);
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
  assert.match(player, /modern-ui\.css\?v=ready-hero-solo-89-1/);
  assert.match(index, /html, body \{[^}]*touch-action: manipulation/);
  assert.match(index, /main, #game-box, #game-frame \{ touch-action: manipulation/);
  // Scrollable reading panes keep overflow:auto (manipulation still allows pan).
  const mobile = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  assert.match(mobile, /\.nr-instructions, \.nr-history, \.nr-help-card \.sh-guide \{[^}]*overflow: auto/);
  assert.ok(!/touch-action:\s*none/.test(mobile));
});

test('extreme-short landscape compresses chrome to reclaim board cell height', () => {
  const css = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 360px\)/);
  assert.match(css, /\.nr-header \{ min-height: 32px/);
  assert.match(css, /#modern-app \.nr-toolbar \.nr-button \{ min-height: 32px; min-width: 32px/);
  assert.match(css, /\.nr-hud \{ min-height: 32px/);
  assert.match(css, /\.nr-play-stage \{ min-height: 32px/);
  assert.match(css, /\.nr-stage-middle > \.nr-hint \{[\s\S]*?min-height: 32px; min-width: 32px/);
  assert.match(css, /\.nr-board \{ padding: 1px; gap: 1px/);
  // #21 path for common 844×390 (h=390 > 360) still keeps ≥44px chrome.
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 500px\)/);
  assert.match(css, /\.nr-hud \{ grid-column: 1; grid-row: 1; min-height: 44px/);
  assert.match(css, /\.nr-stage-middle > \.nr-hint \{\s*flex: 0 0 auto; min-height: 44px; min-width: 44px/);
  const html = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  assert.match(html, /mobile-layout\.css\?v=ready-hero-solo-89-1/);
});

test('narrow portrait tightens board gutters for wider 5×8 cell taps', () => {
  const css = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const narrow = css.match(/@media \(orientation: portrait\) and \(max-width: 400px\) \{[\s\S]*?\n\}/);
  const extreme = css.match(/@media \(orientation: portrait\) and \(max-width: 360px\) \{[\s\S]*?\n\}/);
  assert.ok(narrow, 'portrait ≤400 media block');
  assert.ok(extreme, 'portrait ≤360 media block');
  // 400px path: app + board gutters shrink; cells gain ~3px width on 375 phones.
  assert.match(narrow[0], /#modern-app \{ padding-left: 2px; padding-right: 2px/);
  assert.match(narrow[0], /\.nr-board \{ padding: 2px; gap: 2px/);
  // 360px path: remaining gutters for QA 320×460 (~+4–5px/cell vs baseline 34px).
  assert.match(extreme[0], /#modern-app \{ padding-left: 0; padding-right: 0/);
  assert.match(extreme[0], /\.nr-board \{ padding: 1px; gap: 1px/);
  // Landscape #21/#23 must remain orientation-scoped (not overridden by portrait).
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 500px\)/);
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 360px\)/);
  assert.match(css, /\.nr-hud \{ grid-column: 1; grid-row: 1; min-height: 44px/);
  assert.match(css, /\.nr-header \{ min-height: 32px/);
  const html = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  assert.match(html, /mobile-layout\.css\?v=ready-hero-solo-89-1/);
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
  assert.match(player, /modern-ui\.js\?v=practice-ready-cast-86-1/);
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
  assert.match(mobile, /Host owns device insets/);
  assert.match(player, /modern-ui\.css\?v=ready-hero-solo-89-1/);
  assert.match(player, /modern-ui\.js\?v=practice-ready-cast-86-1/);
  assert.match(player, /mobile-layout\.css\?v=ready-hero-solo-89-1/);
});


test('mobile result keeps primary score heavier than secondary stats (#73)', () => {
  const css = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  assert.match(css, /\.nr-result-score \{ font-size: 34px; font-weight: 850; \}/);
  assert.match(css, /\.nr-result-stats \.nr-stat > strong \{ font-size: 12px; font-weight: 650; color: var\(--nr-muted\); \}/);
  assert.match(css, /\.sh-result-cast > \.nr-result-score \{ font-size: 34px; \}/);
  assert.match(player, /mobile-layout\.css\?v=ready-hero-solo-89-1/);
});


test('mobile result keeps award/record contrast readable on compact cards', () => {
  const css = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  assert.match(css, /\.nr-result-card \.nr-award > span \{ font-size: 9px/);
  assert.match(css, /\.nr-result-card \.nr-record\[data-record='new'\] \{ font-size: 11px; padding: 3px 8px; \}/);
  assert.match(player, /mobile-layout\.css\?v=ready-hero-solo-89-1/);
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
  assert.match(player, /mobile-layout\.css\?v=ready-hero-solo-89-1/);
  assert.match(index, /player\.html\?v=ready-hero-solo-89-1/);
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
  assert.match(player, /mobile-layout\.css\?v=ready-hero-solo-89-1/);
  assert.match(index, /player\.html\?v=ready-hero-solo-89-1/);
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
  assert.match(player, /mobile-layout\.css\?v=ready-hero-solo-89-1/);
  assert.match(player, /shiritori-ui\.css\?v=sh-solo-cast-84-1/);
  assert.match(player, /shiritori-ui\.js\?v=sh-ready-cast-88-1/);
  assert.match(index, /player\.html\?v=ready-hero-solo-89-1/);
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
  assert.match(player, /mobile-layout\.css\?v=ready-hero-solo-89-1/);
  assert.match(index, /player\.html\?v=ready-hero-solo-89-1/);
});


test('short-landscape result-actions / dict density: stack buttons + pin dict (#79)', () => {
  const css = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  const js = fs.readFileSync(require.resolve('../shiritori-ui.js'), 'utf8');
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 500px\)/);
  // Column-stack primary actions so half-width column isn't side-by-side cramped.
  assert.match(css, /\.nr-result-actions \{[\s\S]*?flex-direction: column; gap: 3px/);
  // Dict is one grid row (not stretch 2\/4) under actions; history stays full-width row 4.
  assert.match(css, /\.sh-result > \.nr-result-actions \{ grid-column: 2; grid-row: 1 \/ 3/);
  assert.match(css, /\.sh-result > \.nr-button \{ grid-column: 2; grid-row: 3; align-self: stretch/);
  assert.match(css, /\.sh-result > details \{ grid-column: 1 \/ -1; grid-row: 4/);
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
  assert.match(player, /mobile-layout\.css\?v=ready-hero-solo-89-1/);
  assert.match(index, /player\.html\?v=ready-hero-solo-89-1/);
});


test('short-landscape shiritori play HUD/prompt density reclaim without clipping (#87)', () => {
  const css = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const cl = fs.readFileSync(require.resolve('../character-layout.css'), 'utf8');
  const shCss = fs.readFileSync(require.resolve('../shiritori-ui.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 500px\)/);
  // Denser 4-row stage: HUD | status strip | arena | actions (parity numbers #21 side-park).
  assert.match(css, /\.sh-stage \{[\s\S]*?grid-template-rows: auto 16px minmax\(0, 1fr\) auto/);
  assert.match(css, /\.sh-hud \{[\s\S]*?grid-column: 1; grid-row: 1/);
  assert.match(css, /\.sh-progress \{[\s\S]*?grid-column: 2; grid-row: 1/);
  assert.match(css, /\.sh-status \{[\s\S]*?grid-column: 1 \/ -1; grid-row: 2/);
  assert.match(css, /\.sh-status \{[\s\S]*?display: block/);
  assert.match(css, /\.sh-arena \{[\s\S]*?grid-column: 1 \/ -1; grid-row: 3/);
  assert.match(css, /\.sh-play-actions \{[\s\S]*?grid-column: 1; grid-row: 4/);
  // Task label + prompt stay readable (not clipped).
  assert.match(css, /\.sh-task span \{ display: block; font-size: 9px/);
  assert.match(css, /\.sh-prompt \{ font-size: clamp\(14px, 2\.6vw, 18px\)/);
  // #65 miss badge bumped for short-landscape readability.
  assert.match(css, /#modern-app \.sh-card\[data-feedback='wrong'\]::after \{[\s\S]*?font-size: 10px/);
  // Portrait-only hide of status at ≤360 — landscape keeps status via #87.
  assert.match(css, /@media \(orientation: portrait\) and \(max-height: 360px\) \{[\s\S]*?\.sh-task span, \.sh-status \{ display: none/);
  // Extreme-short landscape: 4-row + status !important visible.
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 360px\)/);
  assert.match(css, /grid-template-rows: 28px 14px minmax\(0, 1fr\) 44px/);
  assert.match(css, /\.sh-status \{[\s\S]*?display: block !important/);
  assert.match(cl, /grid-template-rows: 28px 14px minmax\(0, 1fr\) 44px/);
  assert.match(cl, /\.sh-arena \{ grid-column: 1 \/ -1; grid-row: 3/);
  // #69-family task pulse + #65 miss outline still defined (not stripped).
  assert.match(shCss, /\.sh-task\[data-cue='true'\]\[data-pulse='0'\]/);
  assert.match(shCss, /#modern-app \.sh-card\[data-feedback='wrong'\]/);
  assert.match(shCss, /content: 'ミス'/);
  assert.match(player, /mobile-layout\.css\?v=ready-hero-solo-89-1/);
  assert.match(player, /character-layout\.css\?v=ready-hero-solo-89-1/);
  assert.match(index, /player\.html\?v=ready-hero-solo-89-1/);
});

test('ready solo hero-cast denser/centered on compact layout (#89)', () => {
  const css = fs.readFileSync(require.resolve('../mobile-layout.css'), 'utf8');
  const modern = fs.readFileSync(require.resolve('../modern-ui.css'), 'utf8');
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  assert.match(css, /\.nr-hero-cast:has\(> \.nr-koh\[hidden\]\) \{ gap: 2px; justify-content: center; \}/);
  assert.match(css, /\.nr-hero-cast:has\(> \.nr-koh\[hidden\]\) \.nr-character \{ width: clamp\(48px, 14dvh, 96px\); \}/);
  assert.match(modern, /\.nr-hero-cast:has\(> \.nr-koh\[hidden\]\) \{ gap: 12px; justify-content: center; \}/);
  assert.match(player, /mobile-layout\.css\?v=ready-hero-solo-89-1/);
  assert.match(player, /modern-ui\.css\?v=ready-hero-solo-89-1/);
  assert.match(index, /player\.html\?v=ready-hero-solo-89-1/);
});
