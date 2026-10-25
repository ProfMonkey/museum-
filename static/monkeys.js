/* Animated web companions adapted from the user-supplied ProfMonkey Desktop sprites.
   No desktop integration, keyboard monitoring or mouse automation. */
const MONKEY_FRAMES={idle:4,walk:8,sleep:4,eat_banana:6,slip:4,wake:5,fall:6,get_up:6,blink:4,dragged:2};
let colony=[];let monkeyLoop=0;let lastTick=0;
const reduceMotion=()=>window.matchMedia('(prefers-reduced-motion: reduce)').matches;
function monkeyAsset(state,frame){return `/static/assets/monkey/${state}_${frame%MONKEY_FRAMES[state]}.webp`}
function monkeyAction(m,action){m.state=action;m.frame=0;m.actionUntil=performance.now()+({eat_banana:2800,slip:2000,sleep:3600,blink:600,wake:1000}[action]||1400)}
function renderMonkey(m){m.el.style.left=Math.max(0,Math.min(innerWidth-70,m.x))+'px';m.el.style.top=Math.max(0,Math.min(innerHeight-90,m.y))+'px';m.img.src=monkeyAsset(m.state,m.frame);m.el.style.transform=`scaleX(${m.dir})`}
function setupMonkeys(){document.querySelectorAll('.wa-monkey').forEach(x=>x.remove());colony=[];cancelAnimationFrame(monkeyLoop);
 const toggle=document.getElementById('monkey-toggle');if(toggle)toggle.textContent=W.monkeyMode==='off'?'🐒 猴子已关闭':`🐒 ${W.monkeyCount} 只 · ${W.monkeyMode==='quiet'?'安静':'猴山'}`;
 if(W.monkeyMode==='off')return;
 let count=innerWidth<620?Math.min(W.monkeyCount,2):W.monkeyCount;
 for(let i=0;i<count;i++){
  const node=document.createElement('div');node.className='wa-monkey';node.title='点击猴子：看看它会干什么（也可以拖动）';node.setAttribute('role','button');node.setAttribute('aria-label','ProfMonkey 网页猴子 '+(i+1));node.tabIndex=0;
  const img=document.createElement('img');img.alt='';img.draggable=false;node.appendChild(img);document.body.appendChild(node);
  let m={el:node,img,x:Math.max(12,innerWidth-140-i*96),y:Math.max(55,innerHeight-150),state:'idle',frame:0,dir:i%2?1:-1,actionUntil:0,drag:false};colony.push(m);
  node.addEventListener('pointerdown',e=>{if(e.button!==0)return;m.drag={ox:e.clientX-m.x,oy:e.clientY-m.y,originX:e.clientX,originY:e.clientY,moved:false};node.setPointerCapture(e.pointerId);e.preventDefault()});
  node.addEventListener('pointermove',e=>{if(!m.drag)return;m.drag.moved=m.drag.moved||Math.hypot(e.clientX-m.drag.originX,e.clientY-m.drag.originY)>7;m.x=e.clientX-m.drag.ox;m.y=e.clientY-m.drag.oy;renderMonkey(m)});
  node.addEventListener('pointerup',()=>{if(!m.drag)return;let moved=m.drag.moved;m.drag=false;if(!moved)monkeyAction(m,'eat_banana')});
  node.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();monkeyAction(m,'eat_banana')}});
  renderMonkey(m);
 }
 if(!reduceMotion())monkeyLoop=requestAnimationFrame(tickMonkeys);
}
function tickMonkeys(time){const rate=W.monkeyMode==='wild'?130:220;if(time-lastTick>=rate){lastTick=time;colony.forEach((m,i)=>{
 if(m.drag)return;
 if(time>m.actionUntil){if(m.state!=='walk'&&m.state!=='idle')m.state='idle';if(Math.random()<(W.monkeyMode==='wild'?.043:.018)){
  let acts=['walk','idle','blink','sleep','eat_banana','slip'];monkeyAction(m,acts[Math.floor(Math.random()*acts.length)])
 }}
 m.frame=(m.frame+1)%MONKEY_FRAMES[m.state];
 if(m.state==='walk'){m.x+=m.dir*(W.monkeyMode==='wild'?8:4);if(m.x<8||m.x>innerWidth-105)m.dir*=-1}
 renderMonkey(m);
 })}if(W.monkeyMode!=='off')monkeyLoop=requestAnimationFrame(tickMonkeys)}
function playMonkeyBanana(){if(W.monkeyMode==='off'){W.monkeyMode='quiet';localStorage.setItem('wa-monkey-mode','quiet');setupMonkeys()}colony.forEach((m,i)=>setTimeout(()=>monkeyAction(m,'eat_banana'),i*160));toast('🍌 猴子们正在吃香蕉！')}
const monkButton=document.createElement('button');monkButton.id='monkey-toggle';monkButton.className='monkey-toggle';monkButton.textContent='🐒 猴子设置';monkButton.addEventListener('click',()=>featureModule(7));document.body.appendChild(monkButton);
setupMonkeys();
window.addEventListener('resize',()=>{colony.forEach(m=>{m.x=Math.min(innerWidth-90,m.x);m.y=Math.min(innerHeight-80,m.y);renderMonkey(m)})});
window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener?.('change',setupMonkeys);