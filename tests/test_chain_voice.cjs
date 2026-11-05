const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
test('all seven local callouts, capped level, CPU, mute and no overlapping queue',async()=>{
  const handlers={}, played=[]; let stopped=0;
  const document={hidden:false,addEventListener:(k,v)=>handlers[k]=v};
  class AudioContext {
    state='running'; destination={}; currentTime=0;
    resume(){return Promise.resolve();}
    decodeAudioData(b){return Promise.resolve(b);}
    createGain(){
      return {
        gain:{
          value:0,
          setValueAtTime(v){ this.value=v; return this; },
          linearRampToValueAtTime(v){ this.value=v; return this; },
          cancelScheduledValues(){ return this; },
        },
        connect(){},
        disconnect(){},
      };
    }
    createBufferSource(){
      return {
        connect(){},
        disconnect(){},
        start(){played.push(this.buffer);},
        stop(){stopped++;},
      };
    }
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

test('COUNTER cue, FEVER stinger and PERFECT fanfare honor mute and audio faults',async()=>{
  const handlers={};let notes=0, fail=false;
  const document={hidden:false,addEventListener:(k,v)=>handlers[k]=v};
  class AudioContext {
    state='running';destination={};currentTime=0;
    resume(){return Promise.resolve();}
    decodeAudioData(b){return Promise.resolve(b);}
    createGain(){return {gain:{setValueAtTime(){},linearRampToValueAtTime(){},exponentialRampToValueAtTime(){}},connect(){},disconnect(){}};}
    createOscillator(){if(fail)throw Error('oscillator denied');return {frequency:{setValueAtTime(){}},connect(){},disconnect(){},start(){notes++;},stop(){}};}
  }
  const window={AudioContext};
  vm.runInNewContext(fs.readFileSync(require.resolve('../chain-voice.js'),'utf8'),{window,document,fetch:async()=>({ok:false})});
  await handlers.pointerdown();
  window.chainVoice.stinger();assert.equal(notes,0,'muted by default');
  window.chainVoice.setEnabled(true);
  window.chainVoice.stinger();window.chainVoice.fanfare();window.chainVoice.fanfare('cpu');
  window.chainVoice.counterCue();assert.equal(notes,13);
  window.chainVoice.setEnabled(false);window.chainVoice.fanfare();window.chainVoice.counterCue();assert.equal(notes,13);
  window.chainVoice.setEnabled(true);fail=true;
  assert.doesNotThrow(()=>window.chainVoice.stinger());
  assert.doesNotThrow(()=>window.chainVoice.counterCue());
  document.hidden=true;window.chainVoice.fanfare();window.chainVoice.counterCue();assert.equal(notes,13);
});

test('mute and page hiding cancel scheduled flourish notes and allow later playback', async () => {
  const handlers = {}, oscillators = [], gains = [];
  const document = {hidden:false, addEventListener:(key, fn) => {handlers[key] = fn;}};
  const param = () => ({setValueAtTime(){}, linearRampToValueAtTime(){}, exponentialRampToValueAtTime(){}});
  class AudioContext {
    state = 'running'; destination = {}; currentTime = 10;
    resume(){return Promise.resolve();}
    decodeAudioData(data){return Promise.resolve(data);}
    createGain(){const gain = {gain:param(), connect(){}, disconnected:0, disconnect(){this.disconnected++;}}; gains.push(gain); return gain;}
    createOscillator(){
      const osc = {frequency:param(), stops:[], disconnected:0, connect(){}, start(){},
        stop(time){this.stops.push(time);}, disconnect(){this.disconnected++;}};
      oscillators.push(osc); return osc;
    }
  }
  const window = {AudioContext};
  vm.runInNewContext(fs.readFileSync(require.resolve('../chain-voice.js'), 'utf8'),
    {window, document, fetch:async () => ({ok:false})});
  await handlers.pointerdown();
  window.chainVoice.setEnabled(true);
  window.chainVoice.fanfare();
  assert.equal(oscillators.length, 4);
  assert.ok(oscillators.every(osc => osc.stops.length === 1 && osc.stops[0] > 10), 'normal envelopes keep their scheduled decay');
  oscillators[0].onended();
  assert.equal(oscillators[0].disconnected, 1, 'naturally finished notes are released');
  window.chainVoice.setEnabled(false);
  assert.equal(oscillators[0].stops.length, 1, 'finished notes are not stopped twice');
  for (const osc of oscillators.slice(1)) {
    assert.equal(osc.stops.length, 2);
    assert.equal(osc.stops[1], undefined, 'mute cancels scheduled playback immediately');
    assert.equal(osc.disconnected, 1);
  }
  assert.ok(gains.every(gain => gain.disconnected === 1));
  window.chainVoice.setEnabled(true);
  window.chainVoice.stinger();
  assert.equal(oscillators.length, 8, 'audio may play again when enabled');
  // A browser may reject stopping an already-finished oscillator. It must not
  // prevent the remaining scheduled notes from being stopped and disconnected.
  oscillators[4].stop = function(time) { this.stops.push(time); if (time === undefined) throw Error('already stopped'); };
  document.hidden = true;
  assert.doesNotThrow(() => handlers.visibilitychange());
  for (const osc of oscillators.slice(4)) {
    assert.equal(osc.stops.length, 2);
    assert.equal(osc.stops[1], undefined, 'hiding the page cancels scheduled playback immediately');
    assert.equal(osc.disconnected, 1);
  }
  handlers.visibilitychange();
  assert.ok(oscillators.every(osc => osc.disconnected === 1), 'cleanup remains idempotent');
});

test('voice graph failures do not propagate and later playback still works', async () => {
  const handlers = {}, sources = [], gains = [];
  const document = {hidden:false, addEventListener:(key, fn) => { handlers[key] = fn; }};
  let failure = '';
  class AudioContext {
    state = 'running'; destination = {}; currentTime = 10;
    resume(){ return Promise.resolve(); }
    decodeAudioData(data){ return Promise.resolve(data); }
    createBufferSource() {
      if (failure === 'source') throw Error('source unavailable');
      const item = {connected:0, disconnected:0, stopped:0, started:0,
        connect(){ if (failure === 'source-connect') throw Error('connect failed'); this.connected++; },
        disconnect(){ this.disconnected++; }, stop(){ this.stopped++; },
        start(){ if (failure === 'start') throw Error('start failed'); this.started++; }};
      sources.push(item); return item;
    }
    createGain() {
      if (failure === 'gain') throw Error('gain unavailable');
      const item = {disconnected:0,
        gain:{value:0, setValueAtTime(){}, linearRampToValueAtTime(){ if (failure === 'envelope') throw Error('envelope failed'); }, cancelScheduledValues(){}},
        connect(){ if (failure === 'gain-connect') throw Error('connect failed'); },
        disconnect(){ this.disconnected++; }};
      gains.push(item); return item;
    }
  }
  const window = {AudioContext};
  vm.runInNewContext(fs.readFileSync(require.resolve('../chain-voice.js'), 'utf8'),
    {window, document, fetch:async () => ({ok:true, arrayBuffer:async () => new ArrayBuffer(1)})});
  await handlers.pointerdown(); await new Promise(resolve => setImmediate(resolve));
  window.chainVoice.setEnabled(true);
  for (const stage of ['source', 'gain', 'envelope', 'source-connect', 'gain-connect', 'start']) {
    failure = stage;
    const previousSources = sources.length, previousGains = gains.length;
    assert.doesNotThrow(() => window.chainVoice.play('you', 1), `${stage} must not break game updates`);
    if (sources.length > previousSources) {
      assert.equal(sources.at(-1).stopped, 1, `${stage} source stopped`);
      assert.equal(sources.at(-1).disconnected, 1, `${stage} source disconnected`);
    }
    if (gains.length > previousGains) assert.equal(gains.at(-1).disconnected, 1, `${stage} gain disconnected`);
    failure = '';
    window.chainVoice.play('you', 2);
    assert.equal(sources.at(-1).started, 1, `${stage} does not prevent later playback`);
    window.chainVoice.setEnabled(false);
    assert.equal(sources.at(-1).stopped, 1, 'muting still stops successful playback');
    window.chainVoice.setEnabled(true);
  }
  window.chainVoice.play('cpu', 1);
  document.hidden = true;
  handlers.visibilitychange();
  assert.equal(sources.at(-1).stopped, 1, 'hiding still stops successful playback');
});

test('voice loading retries only failed files after cooldown and never duplicates in-flight requests', async () => {
  const handlers = {}, registrations = {}, requests = new Map(), played = [];
  const document = {hidden:false, addEventListener:(key, fn, options) => { handlers[key] = fn; registrations[key] = options; }};
  let now = 100000, failing = true, completePending;
  class Clock extends Date { static now(){ return now; } }
  class AudioContext {
    state = 'running'; destination = {}; currentTime = 1;
    resume(){ return Promise.resolve(); }
    decodeAudioData(value){
      if (failing && value.endsWith('you-3.wav')) return Promise.reject(Error('decode'));
      return Promise.resolve(value);
    }
    createGain(){return {gain:{value:0, setValueAtTime(){}, linearRampToValueAtTime(){}, cancelScheduledValues(){}}, connect(){}, disconnect(){}};}
    createBufferSource(){return {connect(){}, disconnect(){}, start(){played.push(this.buffer);}, stop(){}};}
  }
  const fetch = url => {
    requests.set(url, (requests.get(url) || 0) + 1);
    if (failing && url.endsWith('you-1.wav')) throw Error('synchronous network failure');
    if (failing && url.endsWith('you-2.wav')) return Promise.resolve({ok:false});
    if (failing && url.endsWith('you-5.wav')) return Promise.reject(Error('asynchronous network failure'));
    if (url.endsWith('cpu-7.wav')) return new Promise(resolve => { completePending = () => resolve({ok:true, arrayBuffer:async()=>url}); });
    return Promise.resolve({ok:true, arrayBuffer:async()=>url});
  };
  const count = suffix => [...requests].find(([url]) => url.endsWith(suffix))?.[1] || 0;
  const flush = () => new Promise(resolve => setImmediate(resolve));
  const window = {AudioContext};
  vm.runInNewContext(fs.readFileSync(require.resolve('../chain-voice.js'), 'utf8'), {window, document, fetch, Date:Clock});
  await handlers.pointerdown(); await flush();
  assert.equal(registrations.keydown?.capture, true, 'keyboard retry runs before the game stops bubbling');
  assert.equal(requests.size, 14, 'normal startup attempts every local voice');
  window.chainVoice.setEnabled(true);
  window.chainVoice.play('you', 4);
  assert.match(played.at(-1), /you-4\.wav$/, 'successful voices remain playable');
  for (let i = 0; i < 20; i++) handlers.keydown();
  await flush();
  assert.equal(count('you-1.wav'), 1, 'rapid gestures do not bypass cooldown');
  assert.equal(count('cpu-7.wav'), 1, 'pending fetch is never duplicated');
  now += 15000; failing = false;
  document.hidden = true; await handlers.pointerdown(); await flush();
  assert.equal(count('you-1.wav'), 1, 'hidden pages do not retry');
  document.hidden = false; window.chainVoice.setEnabled(false);
  await handlers.pointerdown(); await flush();
  assert.equal(count('you-1.wav'), 1, 'disabled sound does not retry');
  window.chainVoice.setEnabled(true);
  const keyEvent = {preventDefault(){throw Error('default must not be blocked');}, stopPropagation(){throw Error('propagation must not be blocked');}};
  await Promise.all([handlers.keydown(keyEvent), handlers.pointerdown(), handlers.keydown(keyEvent)]); await flush();
  for (const name of ['you-1.wav', 'you-2.wav', 'you-3.wav', 'you-5.wav']) assert.equal(count(name), 2, `${name} retried after failure`);
  assert.equal(count('you-4.wav'), 1, 'successful voices are not fetched again');
  assert.equal(count('cpu-7.wav'), 1, 'still-pending voice remains a single request');
  completePending(); await flush();
  window.chainVoice.play('you', 1); window.chainVoice.play('you', 2); window.chainVoice.play('you', 3); window.chainVoice.play('you', 5); window.chainVoice.play('cpu', 7);
  assert.deepEqual(played.slice(-5).map(url => url.split('/').at(-1)), ['you-1.wav','you-2.wav','you-3.wav','you-5.wav','cpu-7.wav']);
});
