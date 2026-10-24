const{test}=require('node:test'),assert=require('node:assert/strict');
const{LunaTimeline,lunaFrame}=require('../assets/characters/fullbody-v1/luna.js');
test('LUNA all six expressions use one full-body atlas',()=>{
 for(const [i,p]of ['idle','celebrate','victory','hurt','frustrated','defeat'].entries())assert.equal(lunaFrame(p),i);
 assert.equal(lunaFrame('unknown'),null);
});
test('LUNA coalesces CPU answers and cancels for negative poses or pause',()=>{
 const t=new LunaTimeline();t.observe(0,0,true);t.observe(1,10,true);
 for(let n=2;n<=10;n++)t.observe(n,n*20,true);
 assert.equal(t.started,1);assert.equal(t.coalesced,9);assert.equal(t.end,610);
 assert.equal(t.frame(310),2);t.observe(10,320,false);assert.equal(t.end,0);
 t.observe(10,1000,true);assert.equal(t.started,1);
 t.observe(11,1100,true);assert.equal(t.started,2);
});
test('LUNA does not replay events after loading, reduced motion or reset',()=>{
 const t=new LunaTimeline();t.observe(7,0,false);t.observe(7,100,true);assert.equal(t.started,0);
 t.observe(8,200,false);t.observe(8,300,true);assert.equal(t.started,0);
 t.observe(0,400,true);t.observe(1,500,true);assert.equal(t.started,1);
});
