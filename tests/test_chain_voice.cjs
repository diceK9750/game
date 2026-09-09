const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
test('all seven local callouts, capped level, CPU, mute and no overlapping queue',async()=>{
  const handlers={}, played=[]; let stopped=0;
  const document={hidden:false,addEventListener:(k,v)=>handlers[k]=v};
  class AudioContext {
    state='running'; destination={};
    resume(){return Promise.resolve();}
    decodeAudioData(b){return Promise.resolve(b);}
    createGain(){return {gain:{},connect(){}};}
    createBufferSource(){return {connect(){},start(){played.push(this.buffer);},stop(){stopped++;}};}
  }
  const window={AudioContext};
  vm.runInNewContext(fs.readFileSync(require.resolve('../chain-voice.js'),'utf8'),{window,document,fetch:async url=>({ok:true,arrayBuffer:async()=>url})});
  await handlers.pointerdown(); await new Promise(resolve=>setImmediate(resolve));
  window.chainVoice.setEnabled(true);
  for(let i=1;i<=8;i++) window.chainVoice.play('you',i);
  assert.equal(new Set(played.slice(0,7)).size,7);
  assert.equal(played[6],played[7]); assert.equal(stopped,7);
  window.chainVoice.play('cpu',2); assert.match(played.at(-1),/cpu-2.wav/);
  window.chainVoice.setEnabled(false); window.chainVoice.play('you',1); assert.equal(played.length,9);
  window.chainVoice.setEnabled(true); document.hidden=true; window.chainVoice.play('you',1); assert.equal(played.length,9);
  for(const owner of ['you','cpu']) for(let i=1;i<=7;i++) {
    const wav=fs.readFileSync(require.resolve(`../assets/voices/cute-v2/${owner}-${i}.wav`));
    assert.equal(wav.toString('ascii',0,4),'RIFF'); assert.ok(wav.length>10000);
  }
});
