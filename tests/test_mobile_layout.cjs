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
