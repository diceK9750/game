const {test}=require('node:test');
const assert=require('node:assert/strict');
const {RinTimeline,restingFrame}=require('../assets/characters/fullbody-v1/rin.js');
test('RIN animation coalesces rapid correct inputs into one bounded timeline',()=>{
  const t=new RinTimeline();t.observe(0,0,true);t.observe(1,10,true);
  assert.equal(t.frame(210),2);
  for(let n=2;n<=20;n++)t.observe(n,10+n*10,true);
  assert.equal(t.started,1);assert.equal(t.coalesced,19);assert.equal(t.end,610);
  assert.equal(t.frame(610),0);t.observe(21,620,true);assert.equal(t.started,2);
});
test('RIN does not replay old events after load, pause, reduced motion or round reset',()=>{
  const t=new RinTimeline();t.observe(7,0,true);assert.equal(t.started,0);
  t.observe(8,100,true);assert.equal(t.started,1);
  t.observe(8,110,false);assert.equal(t.end,0);
  t.observe(8,1000,true);assert.equal(t.started,1);
  t.observe(9,1100,false);assert.equal(t.started,1);
  t.observe(0,1200,true);t.observe(1,1300,true);assert.equal(t.started,2);
});
test('RIN keeps the new happy artwork for FEVER and reduced-motion victory',()=>{
  assert.equal(restingFrame('idle',false),0);
  assert.equal(restingFrame('celebrate',false),0);
  assert.equal(restingFrame('celebrate',true),3);
  assert.equal(restingFrame('victory',false),3);
  assert.equal(restingFrame('victory',true),3);
  for(const [pose,frame] of [['hurt',6],['frustrated',7],['defeat',8]]) {
    assert.equal(restingFrame(pose,false),frame);
    assert.equal(restingFrame(pose,true),frame);
  }
  assert.equal(restingFrame('unknown',false),null);
});
