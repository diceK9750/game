const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
function boot({rate=48000, reject=false, constructorFailure=false, absent=false}={}) {
  const calls=[], handlers={}, contexts=[];
  class Context {
    constructor(...args) {
      calls.push(['constructor',...args]);
      if(constructorFailure) throw Error('device unavailable');
      this.sampleRate=rate; this.state='suspended'; contexts.push(this);
    }
    createBuffer(c,n,r) {
      calls.push(['buffer',c,n,r]);
      if(reject) {const e=Error('Sample rate is not in the supported range.');e.name='NotSupportedError';throw e;}
      return {numberOfChannels:c,length:n,sampleRate:r};
    }
    resume(){calls.push(['resume']);return Promise.resolve();}
    close(){calls.push(['close']);return Promise.resolve();}
  }
  const window={AudioContext:absent?undefined:Context};
  vm.runInNewContext(fs.readFileSync(require.resolve('../assets/audio-boot.js'),'utf8'), {
    window,document:{addEventListener:(name,fn)=>handlers[name]=fn},console:{info(){},warn(){}}
  });
  return {audio:window.numberRushAudio,calls,contexts,handlers};
}
test('audio preflight retains the native context/rate and hands SDL a real validated silence buffer',()=>{
  for(const rate of [22050,44100,48000,96000]) {
    const b=boot({rate}), module={};
    assert.equal(b.audio.prepare(module),true);
    assert.equal(module.SDL2.audioContext,b.contexts[0]);
    assert.deepEqual(b.calls[0],['constructor']); // no forced frequency
    const buffer=module.SDL2.audioContext.createBuffer(1,1024,rate);
    assert.equal(buffer.sampleRate,rate); assert.equal(buffer.length,1024);
    assert.equal(b.calls.filter(x=>x[0]==='buffer').length,1);
    module.SDL2.audioContext.createBuffer(2,64,rate);
    assert.deepEqual(b.calls.at(-1),['buffer',2,64,rate]);
    assert.equal(b.audio.prepare(module),true);
    assert.equal(b.calls.filter(x=>x[0]==='constructor').length,1);
  }
});
test('createBuffer rejection is contained, diagnosed and disables audio without retrying an arbitrary rate',()=>{
  const b=boot({rate:0,reject:true}), module={};
  assert.equal(b.audio.prepare(module),false);
  assert.equal(b.audio.diagnostic.mode,'silent');
  assert.equal(b.audio.diagnostic.requestedRate,0);
  assert.match(b.audio.diagnostic.error,/NotSupportedError/);
  assert.ok(b.calls.some(x=>x[0]==='close'));
  assert.equal(module.SDL2,undefined);
  b.handlers.pointerdown();
  assert.equal(b.audio.prepare(module),false);
  assert.equal(b.calls.filter(x=>x[0]==='constructor').length,1);
});
test('missing or rejected AudioContext does not propagate an exception',()=>{
  for(const options of [{absent:true},{constructorFailure:true}]) {
    const b=boot(options); assert.equal(b.audio.prepare({}),false);
    assert.equal(b.audio.diagnostic.mode,'silent');
  }
});
test('user gesture retries resume on the accepted context',()=>{
  const b=boot(); b.audio.prepare({});b.handlers.pointerdown();b.handlers.keydown();
  assert.equal(b.calls.filter(x=>x[0]==='resume').length,3);
});
