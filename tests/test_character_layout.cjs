const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const css=fs.readFileSync(require.resolve('../character-layout.css'),'utf8');
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
  assert.match(css,/100cqh - \(var\(--sh-rows\)/);
  assert.match(css,/\.sh-arena \.sh-card \{ aspect-ratio: 1/);
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

test('shiritori solo arena collapses empty LUNA column on desktop (#85 parity #83)', () => {
  // Desktop/landscape: 3-col → 2-col when koh[hidden]; portrait keeps 1-col + row collapse.
  assert.match(css, /\.sh-arena:has\(> \.nr-koh\[hidden\]\) \{[\s\S]*?grid-template-columns: clamp\(40px, 15vw, 180px\) minmax\(0, 1fr\);/);
  assert.match(css, /@media \(orientation: portrait\) \{[\s\S]*?\.sh-arena:has\(> \.nr-koh\[hidden\]\) \{[\s\S]*?grid-template-columns: minmax\(0, 1fr\);[\s\S]*?grid-template-rows: var\(--cast-height\) minmax\(0, 1fr\);/);
  // Battle duo default still 3 columns.
  assert.match(css, /\.sh-arena \{[\s\S]*?grid-template-columns: clamp\(40px, 15vw, 180px\) minmax\(0, 1fr\) clamp\(40px, 15vw, 180px\);/);
  const player = fs.readFileSync(require.resolve('../player.html'), 'utf8');
  const index = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  assert.match(player, /character-layout\.css\?v=ready-hero-solo-89-1/);
  assert.match(index, /player\.html\?v=count-tap-110-1/);
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
  assert.match(player, /character-layout\.css\?v=ready-hero-solo-89-1/);
  assert.match(index, /player\.html\?v=count-tap-110-1/);
});
