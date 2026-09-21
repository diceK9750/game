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
  assert.match(css, /\.nr-stage-middle > \.nr-setting \{\s*flex: 0 0 auto; min-height: 44px; min-width: 44px/);
  assert.match(css, /#modern-app \.nr-toolbar \.nr-button \{ min-height: 44px; min-width: 44px/);
  assert.match(css, /\.nr-dialog \.nr-button \{ min-height: 44px/);
  const html = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  assert.match(html, /mobile-layout\.css\?v=7-host-safe/);
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
  assert.match(player, /modern-ui\.css\?v=card-focus-ring-1/);
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
  assert.match(css, /\.nr-stage-middle > \.nr-setting \{[\s\S]*?min-height: 32px; min-width: 32px/);
  assert.match(css, /\.nr-board \{ padding: 1px; gap: 1px/);
  // #21 path for common 844×390 (h=390 > 360) still keeps ≥44px chrome.
  assert.match(css, /@media \(orientation: landscape\) and \(max-height: 500px\)/);
  assert.match(css, /\.nr-hud \{ grid-column: 1; grid-row: 1; min-height: 44px/);
  assert.match(css, /\.nr-stage-middle > \.nr-setting \{\s*flex: 0 0 auto; min-height: 44px; min-width: 44px/);
  const html = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  assert.match(html, /mobile-layout\.css\?v=7-host-safe/);
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
  assert.match(html, /mobile-layout\.css\?v=7-host-safe/);
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
  assert.match(player, /modern-ui\.js\?v=host-safe-1/);
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
  assert.match(player, /modern-ui\.css\?v=card-focus-ring-1/);
  assert.match(player, /modern-ui\.js\?v=host-safe-1/);
  assert.match(player, /mobile-layout\.css\?v=7-host-safe/);
});
