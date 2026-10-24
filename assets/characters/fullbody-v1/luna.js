/* LUNA presentation pilot. Reads snapshots; never writes engine commands. */
(function(){
 'use strict';
 const POSES=Object.freeze({idle:0,celebrate:1,victory:2,hurt:3,frustrated:4,defeat:5});
 class LunaTimeline {
  constructor(){this.event=null;this.end=0;this.start=0;this.started=0;this.coalesced=0;}
  observe(event,now,enabled){
   const fresh=this.event!==null&&event>this.event,reset=this.event!==null&&event<this.event;
   this.event=event;
   if(!enabled||reset)this.cancel();
   else if(fresh){if(now<this.end)this.coalesced++;else{this.start=now;this.end=now+600;this.started++;}}
  }
  frame(now){return [0,1,1,2,1,0][Math.min(5,Math.max(0,Math.floor((now-this.start)/100)))];}
  cancel(){this.end=0;}
 }
 function lunaFrame(pose){return Object.hasOwn(POSES,pose)?POSES[pose]:null;}
 if(typeof module!=='undefined')module.exports={LunaTimeline,lunaFrame};
 if(typeof document==='undefined')return;
 const root=document.documentElement,app=document.getElementById('modern-app');if(!app)return;
 const source=new URL('luna-expression-sheet.png',document.currentScript.src).href;
 const media=matchMedia('(prefers-reduced-motion: reduce)'),timeline=new LunaTimeline(),overlays=new Map();
 let ready=false,failed=false,current=null,raf=0,key='',rest=0,frame=0;
 const reduced=()=>media.matches||app.dataset.reduced==='true';
 function paint(index){frame=index;if(current){current.style.backgroundPosition=`${index*20}% 0%`;current.dataset.frame=String(index);}}
 function clear(){if(raf)cancelAnimationFrame(raf);raf=0;timeline.cancel();current=null;
  for(const [p,o]of overlays){p.removeAttribute('data-luna-pilot');o.hidden=true;}}
 function tick(now){raf=0;if(!current||document.hidden||reduced()){timeline.cancel();paint(rest);return;}
  paint(now<timeline.end?timeline.frame(now):rest);if(now<timeline.end)raf=requestAnimationFrame(tick);}
 function update(){
  let s;try{s=JSON.parse(root.getAttribute('data-modern-state'));}catch{clear();return;}
  const picture=s?.screen==='shiritori',state=picture?s.shiritori:s;
  const live=picture?state?.phase==='playing':s?.screen==='playing';
  const nextKey=picture?'shiritori':'numbers';if(key!==nextKey){timeline.event=null;key=nextKey;}
  const parents=[...app.querySelectorAll('.nr-koh .nr-character-art')].filter(e=>e.getClientRects().length&&!e.closest('[hidden]'));
  const parent=parents.find(e=>e.closest('[data-arena]'))||parents[0],pose=parent?.dataset.pose||'idle';
  const still=parent?lunaFrame(pose):null,active=ready&&still!==null&&!document.hidden;
  const now=performance.now(),positive=['idle','celebrate','victory'].includes(pose);
  timeline.observe(Number(state?.chain?.cpu?.event)||0,now,active&&live&&positive&&!reduced());
  if(!active){clear();return;}rest=still;
  for(const [p,o]of overlays)if(!parents.includes(p)){p.removeAttribute('data-luna-pilot');o.hidden=true;}
  for(const p of parents){
   if(!overlays.has(p)){const o=document.createElement('span');o.className='pilot-luna-art';o.setAttribute('aria-hidden','true');o.style.backgroundImage=`url("${source}")`;p.append(o);overlays.set(p,o);}
   const o=overlays.get(p),index=lunaFrame(p.dataset.pose||'idle');
   if(index===null){p.removeAttribute('data-luna-pilot');o.hidden=true;continue;}
   o.hidden=false;p.dataset.lunaPilot='ready';o.style.backgroundPosition=`${index*20}% 0%`;o.dataset.frame=String(index);
  }
  current=overlays.get(parent);paint(now<timeline.end?timeline.frame(now):rest);
  if(!raf&&now<timeline.end)raf=requestAnimationFrame(tick);
 }
 const image=new Image();image.onload=async()=>{try{
  if(image.naturalWidth!==1536||image.naturalHeight!==256)throw Error('Unexpected LUNA atlas dimensions');
  if(image.decode)await image.decode();ready=true;root.dataset.lunaPilotAsset='ready';update();
 }catch{image.onerror();}};
 image.onerror=()=>{ready=false;failed=true;root.dataset.lunaPilotAsset='fallback';clear();};image.src=source;
 new MutationObserver(update).observe(root,{attributes:true,attributeFilter:['data-modern-state']});
 document.addEventListener('visibilitychange',update);media.addEventListener('change',update);
 Object.defineProperty(window,'lunaPilotDiagnostics',{get:()=>({ready,failed,frame,started:timeline.started,coalesced:timeline.coalesced,running:!!raf,overlays:overlays.size})});
 update();
})();
