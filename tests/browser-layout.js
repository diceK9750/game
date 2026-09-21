/* Browser-native geometry regression. No production test hooks or rule changes. */
const sizes = [[393,852],[375,667],[360,800],[852,393],[667,375],[1280,720],
  [667,360],[667,320],[667,300],[667,250],[666,375],[668,375]];
const fixture = document.querySelector('#fixture');
const sizeSelect = document.querySelector('#size');
sizes.forEach(([w,h]) => sizeSelect.add(new Option(`${w}x${h}`, `${w},${h}`)));
const settle = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
const chainSide = {count:7,best:12,bonus:140,remaining:1.2,window:1.5,ratio:.8,tier:3};
function snapshot(game, mode, phase) {
  const updated = phase === 'updated' || phase === 'result';
  const s = {v:1, screen:({setup:'ready',countdown:'countdown',play:'playing',updated:'playing',pause:'confirm',result:'finished'})[phase],
    kind:mode === 'solo'?'practice':'battle',max_number:40,mode:'random',difficulty:'hard',ack:0,bgm:true,sfx:false,
    target:40,points:updated?23:0,player_points:updated?23:0,completed:updated?39:0,streak:12,goal:24,cpu_points:updated?17:0,elapsed:updated?123.45:0,mistakes:2,
    countdown:3,confirm_action:'pause',cpu_progress:.75,cpu_remaining:1.4,remaining:20,
    hint_used:false,perfect:true,storage_saved:false,winner:'you',left:'celebrate',right:'frustrated',
    chain:{you:{...chainSide,event:updated?1:0},cpu:{...chainSide,event:updated?1:0}}, history:[],
    cells:['play','updated','result'].includes(phase)?Array.from({length:40},(_,i)=>({n:i+1,owner:updated&&i<3?(i%2?'cpu':'you'):null,effect:updated&&i===1?'cpu':updated&&i===2?'correct':''})):[]};
  if(game==='shiritori') {
    const shPhase=({setup:'intro',play:'playing',updated:'playing',pause:'paused',result:'finished'})[phase];
    // Shiritori starts immediately in the real game; it has no countdown phase.
    s.screen='shiritori';s.cells=[];
    s.shiritori={phase:shPhase,mode,total:mode==='solo'?48:24,difficulty:'hard',turn:'you',
      required:'り',last_word:updated?'ことばをつなげるしりとり':'しりとり',remaining:18.7,limit:20,hints:3,hint:null,
      selected:null,message:updated?'新しい読み方を発見！次の絵もつないでパーフェクトを目指そう。':'「り」からはじめよう',
      mistakes:2,history:[],winner:'you',stock:mode==='solo'?23:0,completed:updated?21:0,relinks:2,seen:[],
      chain:s.chain,catalog:[{id:'apple',icon:'🍎',words:['りんご','くだもの','たべもの']}],
      cards:Array.from({length:24},(_,i)=>({id:'apple',icon:'🍎',words:['りんご','くだもの'],owner:null}))};
  }
  return s;
}
async function show(w,h,game,mode,phase,variant={}) {
  // Match the host's 4px gutters; iframe viewport is the remaining content box.
  fixture.style.width=`${w-8}px`;fixture.style.height=`${h-8}px`;
  const doc=fixture.contentDocument;
  const state=snapshot(game,mode,phase);
  if(variant.count&&game==='numbers') {
    state.max_number=variant.count;state.target=variant.count;state.mode=variant.order;
    state.cells=state.cells.map((c,i)=>i<variant.count?c:{n:null,owner:null,effect:''});
  } else if(variant.count) {
    state.shiritori.total=variant.count;
    state.shiritori.cards=state.shiritori.cards.slice(0,Math.min(24,variant.count));
    state.shiritori.stock=Math.max(0,variant.count-24);
  }
  doc.documentElement.setAttribute('data-modern-state',JSON.stringify(state));
  await settle();
  // Compare settled boxes, not the temporary 1.04x celebration transform.
  // Burst content remains visible; only finite animations advance to the end.
  for(const animation of doc.getAnimations()) {
    if(Number.isFinite(animation.effect.getComputedTiming().endTime)) animation.finish();
  }
  await settle();
}
function measure() {
  const doc=fixture.contentDocument,win=fixture.contentWindow;
  const visible=e=>e.getClientRects().length && !e.closest('[hidden]') && win.getComputedStyle(e).display!=='none';
  const rect=e=>e.getBoundingClientRect();
  const buttons=[...doc.querySelectorAll('#modern-app button')].filter(visible);
  const outside=buttons.filter(e=>{const r=rect(e);return r.left < -1 || r.top < -1 || r.right>win.innerWidth+1 || r.bottom>win.innerHeight+1;}).map(e=>e.textContent);
  const clippedButtons=buttons.filter(e=>{
    const b=rect(e);
    for(let p=e.parentElement;p&&p!==doc.body;p=p.parentElement){
      const s=win.getComputedStyle(p),r=rect(p);
      if(/auto|scroll|hidden|clip/.test(s.overflowX)&&(b.left<r.left-1||b.right>r.right+1))return true;
      if(/auto|scroll|hidden|clip/.test(s.overflowY)&&(b.top<r.top-1||b.bottom>r.bottom+1))return true;
    }
    return false;
  }).map(e=>e.textContent);
  const nav=buttons.filter(e=>e.closest('.nr-toolbar,.sh-play-actions') || e.matches('.nr-hint'));
  const small=nav.filter(e=>rect(e).height<43.9||rect(e).width<43.9).map(e=>({text:e.textContent,w:rect(e).width,h:rect(e).height}));
  const hud=doc.querySelector('.nr-hud');
  const hudVisible=visible(hud);
  const hudOverflow=hudVisible && hud.scrollWidth>hud.clientWidth+2;
  const text= [...doc.querySelectorAll('.nr-hud .nr-overline,.nr-hud strong,.nr-hud .nr-score-card span:not(:has(*)),.nr-play-stats strong,.nr-cpu-clock,.sh-prompt,.sh-clock')].filter(visible);
  const overlaps=[];
  for(let i=0;i<text.length;i++) for(let j=i+1;j<text.length;j++) {
    if(text[i].contains(text[j])||text[j].contains(text[i]))continue;
    const a=rect(text[i]),b=rect(text[j]);
    if(Math.min(a.right,b.right)-Math.max(a.left,b.left)>1 && Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1) overlaps.push([text[i].textContent,text[j].textContent]);
  }
  const documentOverflow=doc.documentElement.scrollHeight>win.innerHeight+1||doc.documentElement.scrollWidth>win.innerWidth+1;
  const contentOverflow=[...doc.querySelectorAll('.nr-hud,.nr-score-card,.nr-target,.nr-play-stats,.nr-stage-middle,.sh-hud,.sh-task,.nr-result-card,.sh-result,.nr-setup')]
    .filter(visible).filter(e=>e.scrollWidth>e.clientWidth+2||e.scrollHeight>e.clientHeight+2)
    .map(e=>({selector:e.className,client:[e.clientWidth,e.clientHeight],scroll:[e.scrollWidth,e.scrollHeight]}));
  const cards=[...doc.querySelectorAll('.nr-cell,.sh-card')].filter(visible);
  const minCard=cards.length?Math.min(...cards.map(e=>rect(e).height)):null;
  const squareErrors=cards.filter(e=>Math.abs(rect(e).width-rect(e).height)>.6)
    .map(e=>({text:e.textContent,width:rect(e).width,height:rect(e).height}));
  const arena=[...doc.querySelectorAll('[data-arena]')].find(visible);
  const board=arena?.querySelector('.nr-board,.sh-board');
  const boardBox=board?{x:rect(board).x,y:rect(board).y,width:rect(board).width,height:rect(board).height}:null;
  const characterErrors=[];
  const portrait=win.innerHeight>win.innerWidth;
  if(arena&&board){
    const b=rect(board);
    for(const side of ['rin','koh']) {
      const e=arena.querySelector(`.nr-${side}`);
      if(e.hidden){if(side==='rin')characterErrors.push('player hidden');continue;}
      const a=rect(e),img=rect(e.querySelector('.nr-character-art'));
      if(!visible(e)||a.width<1||a.height<1)characterErrors.push(`${side} missing`);
      const placed=portrait?(side==='rin'?a.top>=b.bottom-1:a.bottom<=b.top+1):(side==='rin'?a.right<=b.left+1:a.left>=b.right-1);
      if(!placed)characterErrors.push(`${side} wrong side or overlaps board`);
      if(img.top<0||img.bottom>win.innerHeight+1)characterErrors.push(`${side} art outside viewport`);
    }
  }
  // Cast-only screens use the same direction; pause/countdown have no cast.
  for(const cast of [...doc.querySelectorAll('.nr-hero-cast,.nr-result-duo,.sh-result-cast')].filter(visible)) {
    const you=cast.querySelector('.nr-rin'),cpu=cast.querySelector('.nr-koh');
    if(!you||!cpu||!visible(you)||!visible(cpu))continue;
    const a=rect(you),b=rect(cpu);
    if(portrait?a.top<b.bottom-1:a.right>b.left+1)characterErrors.push('setup/result cast order');
  }
  const hudRegion=[...doc.querySelectorAll('.game-hud')].find(visible);
  const hudInterference=!!(hudRegion&&board&&
    Math.min(rect(hudRegion).right,rect(board).right)-Math.max(rect(hudRegion).left,rect(board).left)>1&&
    Math.min(rect(hudRegion).bottom,rect(board).bottom)-Math.max(rect(hudRegion).top,rect(board).top)>1);
  return {active:!doc.querySelector('#modern-app').hidden,errors:win.fixtureErrors,
    squareErrors,characterErrors,hudInterference,boardBox,clippedButtons,
    documentOverflow,contentOverflow,outside,small,overlaps,hudOverflow,hud:hudVisible?{width:hud.clientWidth,scroll:hud.scrollWidth}:null,
    minTap:nav.length?Math.min(...nav.map(e=>Math.min(rect(e).width,rect(e).height))):null,minCard};
}
document.querySelector('#show').onclick=async()=>{
  const [w,h]=sizeSelect.value.split(',').map(Number),game=document.querySelector('#game').value,phase=document.querySelector('#state').value;
  if(game==='shiritori'&&phase==='countdown'){document.querySelector('#status').textContent='Shiritori has no countdown';return;}
  await show(w,h,game,document.querySelector('#mode').value,phase);
  document.querySelector('#report').textContent=JSON.stringify(measure(),null,2);
};
document.querySelector('#run').onclick=async()=>{
  const results=[];document.querySelector('#run').disabled=true;
  const passed=r=>r.active&&!r.errors.length&&!r.documentOverflow&&!r.contentOverflow.length&&!r.outside.length&&!r.clippedButtons.length&&!r.small.length&&!r.overlaps.length&&!r.hudOverflow&&!r.squareErrors.length&&!r.characterErrors.length&&!r.hudInterference;
  for(const [w,h]of sizes)for(const game of ['numbers','shiritori'])for(const mode of ['battle','solo'])for(const phase of ['setup','countdown','play','updated','pause','result']){
    if(game==='shiritori'&&phase==='countdown')continue;
    await show(w,h,game,mode,phase);
    const result={size:`${w}x${h}`,game,mode,phase,...measure()};
    result.pass=passed(result);
    results.push(result);document.querySelector('#status').textContent=`Checking ${results.length}`;
  }
  // Range/order and picture-count variants exercise empty cells and both grid
  // shapes. They share the same arena and must not regress the square contract.
  for(const [w,h] of sizes)for(const game of ['numbers','shiritori'])for(const mode of ['battle','solo']){
    for(const count of (game==='numbers'?[10,20,30,40]:[12,24,36,48]))for(const order of (game==='numbers'?['ordered','random']:['auto'])){
      await show(w,h,game,mode,'play',{count,order});
      const result={size:`${w}x${h}`,game,mode,phase:'range/order',count,order,...measure()};
      result.pass=passed(result);results.push(result);
      document.querySelector('#status').textContent=`Checking ${results.length}`;
    }
  }
  // New composition no longer has the old sibling hierarchy. Negative control
  // explicitly squeezes its HUD; geometry must still detect the original fault.
  await show(667,375,'numbers','battle','updated');
  const regression=fixture.contentDocument.createElement('style');
  regression.textContent='#modern-app .game-hud .nr-hud{width:13px}';
  fixture.contentDocument.head.append(regression);await settle();
  const detectsOldHud=measure().hudOverflow;
  regression.remove();await settle();
  const independence=[];
  for(const [w,h] of sizes)for(const game of ['numbers','shiritori'])for(const mode of ['battle','solo']){
    await show(w,h,game,mode,'play');const before=measure().boardBox;
    await show(w,h,game,mode,'updated');const updated=measure().boardBox;
    const doc=fixture.contentDocument;
    const labels=[...doc.querySelectorAll('.nr-target>.nr-overline,.nr-feedback,.sh-prompt,.sh-status')];
    const original=labels.map(e=>e.textContent);
    labels.forEach(e=>e.textContent='長い説明やステータスが増えても盤面を押し縮めない。'.repeat(16));
    await settle();const stressed=measure().boardBox;
    const stable=[updated,stressed].every(b=>Object.keys(before).every(k=>Math.abs(before[k]-b[k])<.6));
    independence.push({size:`${w}x${h}`,game,mode,stable});
    labels.forEach((e,i)=>e.textContent=original[i]);
  }
  const failed=results.filter(r=>!r.pass);
  document.querySelector('#report').textContent=JSON.stringify({total:results.length,failed:failed.length,detectsOldHud,independence,failures:failed,results},null,2);
  document.querySelector('#status').textContent=`DONE: ${results.length-failed.length}/${results.length} passed; detects old HUD: ${detectsOldHud}; stable boards: ${independence.filter(r=>r.stable).length}/${independence.length}`;
  document.querySelector('#run').disabled=false;
};
