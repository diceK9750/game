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
