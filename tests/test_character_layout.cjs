const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const css=fs.readFileSync(require.resolve('../character-layout.css'),'utf8');

test('both game renderers opt into one arena contract with width and height sizing',()=>{
  for(const name of ['modern-ui.js','shiritori-ui.js']) {
    const js=fs.readFileSync(require.resolve('../'+name),'utf8');
    assert.ok(js.includes("dataset.gameLayout = 'true'"));
    assert.ok(js.includes("dataset.arena = 'true'"));
    assert.ok(js.includes("dataset.boardSpace = 'true'"));
    assert.ok(js.includes("'game-hud'"));
  }
  assert.ok(css.includes('container-name: board-space'));
  assert.ok(css.includes('@container board-space (max-aspect-ratio: 1 / 1)'));
  assert.ok(css.includes('@container board-space (min-aspect-ratio: 2 / 1)'));
  assert.ok(css.includes('grid-template-rows: var(--hud-block) minmax(0, 1fr)'));
});
test('chain celebrations stay inside a paint-contained meter lane',()=>{
  assert.match(css,/\.timed-chain \{ overflow: clip; contain: paint/);
  assert.match(css,/\.chain-burst \{ inset: 0 0 5px/);
  assert.match(css,/\.chain-burst::before \{ display: none/);
  assert.match(css,/animation: chain-safe-flash/);
});
test('reduced motion keeps a static readable chain banner without opacity pulse',()=>{
  assert.match(css,/#modern-app\[data-reduced='true'\] \.chain-burst\[data-pulse/);
  assert.match(css,/@media \(prefers-reduced-motion: reduce\)/);
  assert.match(css,/animation: none !important; opacity: 1/);
  // Readability under RM: larger type + solid fill (not only opacity:1).
  assert.match(css,/#modern-app\[data-reduced='true'\] \.chain-burst\[data-pulse[\s\S]*?font-size: clamp\(13px/);
  assert.match(css,/#modern-app\[data-reduced='true'\] \.chain-burst\[data-pulse[\s\S]*?background: #0c2433f5/);
  assert.match(css,/@media \(prefers-reduced-motion: reduce\) \{[\s\S]*?\.chain-burst\[data-pulse[\s\S]*?font-size: clamp\(13px/);
  assert.match(css,/#modern-app\[data-reduced='true'\] \.timed-chain\[data-tier='3'\] \.chain-burst\[data-pulse[\s\S]*?background: #483014f5/);
});
test('square cards and separate character lanes share the remaining arena',()=>{
  assert.match(css,/--cell: min\(calc\(\(100cqw/);
  assert.ok(css.includes('100cqh - (var(--board-rows)'));
  assert.ok(css.includes('aspect-ratio: 1 / 1'));
  assert.match(css,/\.nr-ready > \.nr-setup \{ grid-column: 1; grid-row: 1/);
  assert.match(css,/\.nr-ready > \.nr-intro \{ grid-column: 1; grid-row: 2/);
  const js=fs.readFileSync(require.resolve('../shiritori-ui.js'),'utf8');
  assert.match(js,/E\('div', 'sh-arena'\), rin.wrap, boardSpace, koh.wrap/);
});
test('character stylesheet and full-body atlases ship in Pages',()=>{
  const html=fs.readFileSync(require.resolve('../player.html'),'utf8');
  assert.ok(html.indexOf('character-layout.css')>html.indexOf('mobile-layout.css'));
  assert.match(fs.readFileSync(require.resolve('../.github/workflows/pages.yml'),'utf8'),/character-layout\.css/);
  for(const file of ['rin-atlas.png','koh-dark-cutout-atlas.png']) assert.ok(fs.existsSync(require.resolve('../assets/characters/'+file)));
});

test('solo keeps player lane and centered board without inventing an opponent', () => {
  // Solo retains the same slots; the absent rival cannot move the player.
  assert.ok(css.includes('grid-template-columns: var(--cast-lane) minmax(0, 1fr) var(--cast-lane)'));
  assert.ok(css.includes('[data-arena] > .nr-rin { grid-row: 3; }'));
  // Battle duo default still 3 columns.
  assert.ok(css.includes('[data-arena] > .nr-koh { grid-row: 1; }'));
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  assert.match(player, /character-layout\.css\?v=shared-arena-114-2/);
  assert.match(index, /player\.html\?v=shared-arena-114-2/);
  // #80 JS still owns hide.
  const js = fs.readFileSync(require.resolve('../shiritori-ui.js'), 'utf8');
  assert.match(js, /koh\.wrap\.hidden = solo/);
});

test('ready solo hero-cast denser RIN after LUNA+VS hide (#89 parity #82/#84)', () => {
  assert.match(css, /\.nr-ready \.nr-hero-cast:has\(> \.nr-koh\[hidden\]\) \{ gap: 12px; justify-content: center; \}/);
  assert.match(css, /\.nr-ready \.nr-hero-cast:has\(> \.nr-koh\[hidden\]\) \.nr-character \{ width: min\(56cqw, calc\(100cqh - 18px\), 320px\); \}/);
  // Battle duo default width unchanged.
  assert.match(css, /\.nr-ready \.nr-hero-cast \.nr-character \{ display: block; width: min\(43cqw, calc\(100cqh - 18px\), 280px\);/);
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  assert.match(player, /character-layout\.css\?v=shared-arena-114-2/);
  assert.match(index, /player\.html\?v=shared-arena-114-2/);
});
