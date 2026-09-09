const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {rivalCursor}=require('../rival-cursor.js');
test('every cursor route moves one adjacent cell at a time and ends on the answer',()=>{
  for(const [count,cols] of [[40,8],[24,8],[24,4],[12,4],[12,3]]) {
    for(let target=0;target<count;target++) {
      let prev=rivalCursor(count,cols,target,0);
      for(let step=1;step<=8;step++) {
        const next=rivalCursor(count,cols,target,step/9+0.0001);
        assert.equal(Math.abs(next%cols-prev%cols)+Math.abs(Math.floor(next/cols)-Math.floor(prev/cols)),1);
        prev=next;
      }
      assert.equal(prev,target); assert.equal(rivalCursor(count,cols,target,1),target);
    }
  }
});
test('invalid targets hide the cursor and observations are deterministic',()=>{
  for(const target of [null,undefined,-1,40]) assert.equal(rivalCursor(40,8,target,0.5),null);
  assert.equal(rivalCursor(40,8,17,0.5),rivalCursor(40,8,17,0.5));
});
test('both character consumers use the female dark rival atlas',()=>{
  for(const [file,asset] of [['modern-ui.css','luna-portraits-v2.png'],['character-layer.css','koh-dark-cutout-atlas.png']]) assert.ok(fs.readFileSync(require.resolve('../'+file),'utf8').includes(asset));
  const png=fs.readFileSync(require.resolve('../assets/characters/koh-dark-cutout-atlas.png'));
  assert.equal(png[25], 6, 'rival PNG has an alpha channel');
  const fairy=fs.readFileSync(require.resolve('../assets/characters/dark-fairy.png'));
  assert.equal(fairy[25], 6, 'fairy PNG has an alpha channel');
  assert.equal(png.readUInt32BE(16),1536);assert.equal(png.readUInt32BE(20),1024);
});
