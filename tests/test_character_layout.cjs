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
