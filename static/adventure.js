/* V25 · Destiny Relay. Each stage is an actual server draw from a real private wheel.
   Demo suggestions are explicitly synthetic templates, not community submissions. */
(() => {
'use strict';
const A={config:null,wheels:[],cards:[],selected:0,detail:null,stageWheelIds:[],
 demo:{steps:[],running:false},busy:false,notice:'',error:'',drawing:0};
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const btn=(act,title,attrs='')=>'<button type="button" data-destiny="'+act+'" '+attrs+'>'+title+'</button>';
const signed=()=>Boolean(window.S?.user);
const palettes=['#e4b676','#94bdbc','#dd9c98','#9fb2e1','#bb9cce'];
const DEMO=[
 {title:'🍜 吃什么',options:['米线','菌子火锅','牛排','烤鱼','烧烤']},
 {title:'🧭 去哪玩',options:['湖边散步','逛一座博物馆','去看展','公园放空']},
 {title:'🎨 做什么',options:['拍摄一组照片','画一张画','做一个小实验','读一本书']},
 {title:'🌌 探索万物',options:['黑洞','恐龙化石','古代瓷器','分形数学']}
];
function lastDemo(){return A.demo.steps;}
function stages(){return signed()?A.detail?.stages||[]:
 DEMO.map((d,i)=>({number:i+1,topic_label:d.title,wheel_title:'游客演示灵感（非真实社区投稿）',
     completed:i<A.demo.steps.length,label:A.demo.steps[i]?.label||null,
     exhibit_id:null,available:true}));}
function project(){return signed()?A.detail:{id:null,title:'今天的万物奇遇 · 游客体验',
 stage_count:DEMO.length,completed_count:A.demo.steps.length,finished:A.demo.steps.length===DEMO.length,
 visibility:'private',share_path:null,stages:stages()};}
function selectedItemOptions(id){
 return '<option value="">选择你自己的转盘</option>'+A.wheels.map(w=>
 '<option value="'+w.id+'" '+(Number(id)===w.id?'selected':'')+'>'+esc(w.title)+' · '+esc(w.topic_label||w.topic)+
 ' · '+w.count+' 个有效选项'+(w.count<2?' (不可用)':'')+'</option>').join('');
}
function chooseDefault(){
 if(A.stageWheelIds.length||!A.wheels.length)return;
 const topics=['food','travel','activity','custom','watch'];
 const eligible=A.wheels.filter(w=>w.count>=2);
 A.stageWheelIds=[];
 for(const topic of topics){
  const wheel=eligible.find(w=>w.topic===topic&&!A.stageWheelIds.includes(w.id));
  if(wheel)A.stageWheelIds.push(wheel.id);
  if(A.stageWheelIds.length>=4)break;
 }
 for(const wheel of eligible){
  if(A.stageWheelIds.length>=4)break;
  if(!A.stageWheelIds.includes(wheel.id))A.stageWheelIds.push(wheel.id);
 }
 while(A.stageWheelIds.length<Math.min(4,Math.max(2,eligible.length)))A.stageWheelIds.push(0);
}
async function load(){
 A.error='';
 try{
  if(!A.config)A.config=await api('/adventures/config');
  if(signed()){
   const res=await Promise.all([api('/wheels'),api('/adventures')]);
   A.wheels=res[0].items||[];A.cards=res[1].items||[];
   chooseDefault();
   if(!A.cards.some(x=>x.id===A.selected))A.selected=A.cards[0]?.id||0;
   A.detail=A.selected?await api('/adventures/'+A.selected):null;
  }else{A.wheels=[];A.cards=[];A.selected=0;A.detail=null;}
 }catch(err){A.error=err.message||'连接命运接力失败';}
}
function intro(){
 return '<section class="dr-hero"><div class="dr-upper">WONDER ATLAS · V25 · YOUR DAY, YOUR ADVENTURE</div>'+
 '<h1>✨ 今天，<em>来一场万物命运接力。</em></h1>'+
 '<p>先抽吃什么，再抽去哪儿、做什么、探索什么。四次命运选择组成一张奇遇卡。每一个结果都来自你挑选的真实转盘，绝不是随意拼凑的假投稿。</p>'+
 '<div class="dr-pills"><span>🍜 吃什么</span><span>🧭 去哪里</span><span>🎨 做什么</span>'+
 '<span>🌌 探索什么</span><span>🔐 默认私人</span></div></section>';
}
function collection(){
 if(!signed())return '<section class="dr-panel dr-onboard"><div class="dr-small-title">INSTANT PLAY · NO SIGN IN</div>'+
 '<h2>🎁 不登录，也能玩四站奇遇</h2><p>以下是系统内置的演示候选项，不是其他用户真实创作的作品。每一站都会调用服务端公平随机抽取接口。</p>'+
 '<p>登录后可以用自己收藏的真实万物转盘创建永久奇遇卡，完成后还可自愿分享。</p></section>';
 return '<section class="dr-panel"><div class="dr-split"><div><span class="dr-small-title">YOUR REAL WHEELS</span>'+
 '<h2>🪐 选择你的命运站点</h2><p>挑选 2–5 个不同的私人转盘，按顺序组成奇遇路线；每个转盘至少要有两个有效选项。</p></div>'+
 '<div class="dr-note">'+A.wheels.filter(w=>w.count>=2).length+' 个可用转盘</div></div>'+
 '<form id="dr-compose"><label>今日奇遇标题<input name="title" maxlength="70" minlength="2" required value="我的今日奇遇" placeholder="今晚吃什么，然后去哪儿？"></label>'+
 '<div class="dr-composer">'+A.stageWheelIds.map((id,i)=>'<label class="dr-choice">'+
 '<span class="dr-stepno">'+(i+1)+'</span><span>第 '+(i+1)+' 站</span>'+
 '<select name="stage'+i+'" data-stage-id="'+i+'" required>'+selectedItemOptions(id)+'</select></label>').join('')+'</div>'+
 '<div class="dr-actions">'+btn('add-stage','＋ 增加一站',''+(A.stageWheelIds.length>=5?'disabled':''))+
 btn('remove-stage','− 减少一站',''+(A.stageWheelIds.length<=2?'disabled':''))+
 '<button class="dr-primary" type="submit" '+(A.wheels.filter(x=>x.count>=2).length<2?'disabled':'')+'>✦ 创建私人奇遇卡</button></div>'+
 '</form>'+(!A.wheels.length?'<p class="dr-hint">还没有个人转盘。先进入「🎡 万物转盘」添加美食和其他选择。</p>'+
 btn('go-wheels','去创建我的转盘 ↗'):'')+
 '<div class="dr-cards">'+A.cards.map(x=>btn('select-card','<span>✦ '+esc(x.title)+'</span>'+
 '<small>'+x.completed_count+' / '+x.stage_count+' 站 · '+(x.is_public?'已公开':'私人')+'</small>',
 'data-id="'+x.id+'" class="dr-item '+(A.selected===x.id?'active':'')+'"')).join('')+'</div>'+
 '</section>';
}
function routeCard(){
 const p=project();if(!p)return '<section class="dr-panel dr-empty">创建一张奇遇卡，或先前往万物转盘收集至少两个不同主题的候选项。</section>';
 const s=stages(),done=s.filter(x=>x.completed).length;
 const next=s.find(x=>!x.completed);
 const canDraw=!A.busy&&(signed()?Boolean(A.selected):true);
 return '<section class="dr-panel dr-stage-panel"><div class="dr-split"><div><span class="dr-small-title">DESTINY REEL · '+done+' / '+s.length+'</span>'+
 '<h2>🔮 '+esc(p.title)+'</h2><p>每抽一站，命运就向前一步。随时可以离开，登录用户的进度保存在私人奇遇记录中。</p></div>'+
 (signed()?'<div class="dr-actions">'+(p.finished?
 btn('visibility',p.is_public?'🔒 撤回分享':'✨ 主动生成分享链接',
 'data-status="'+(p.is_public?'private':'public')+'"'):'')+
 btn('delete','删除这张奇遇')+'</div>':'')+'</div>'+
 '<div class="dr-path">'+s.map((x,i)=>'<div class="dr-stage '+(x.completed?'done':i===done?'current':'locked')+'">'+
 '<div class="dr-stage-index">'+(x.completed?'✓':i+1)+'</div>'+
 '<div class="dr-stage-content"><small>STAGE '+String(i+1).padStart(2,'0')+' · '+esc(x.topic_label)+'</small>'+
 '<h3>'+esc(x.completed?x.label:'待命运揭晓')+'</h3>'+
 '<span>'+esc(x.wheel_title)+'</span>'+
 (x.completed&&x.exhibit_id?btn('look-exhibit','🏛 查看来源','data-id="'+x.exhibit_id+'"'):'')+
 (x.completed&&!x.available?'<p class="dr-hint">馆藏已被撤回，不再显示原始内容。</p>':'')+'</div></div>').join('')+'</div>'+
 (next?'<div class="dr-action-zone"><span>下一站：'+esc(next.topic_label)+'</span>'+
 '<p>随机结果由后端计算；正在抽取的阶段不能跳过或手动改写。</p>'+
 btn('advance',A.busy?'随机抽取中…':'🎲 抽取下一站','class="dr-primary dr-spin" '+(!canDraw?'disabled':''))+
 '</div>':'<div class="dr-complete"><b>🎉 奇遇全部完成！</b><p>你已经组合出一次独一无二的万物探索路线。</p>'+
 btn('image','📸 保存奇遇卡图片','class="dr-primary"')+
 (p.share_path?btn('share','🔗 复制我的公开奇遇链接'):'')+
 (!signed()?btn('restart','↻ 再来一次'):'')+'</div>')+
 '</section>';
}
function shareInfo(){
 const p=project();
 if(!p||!p.finished||!signed())return '';
 return '<section class="dr-panel"><span class="dr-small-title">PRIVATE BY DEFAULT · SHARE BY CHOICE</span>'+
 '<h2>✦ 分享属于你的今日奇遇</h2><p>默认只有你自己能查看。主动公开后，会生成一条难以猜测的独立链接；撤回后旧链接立即失效。</p>'+
 (p.share_path?'<div class="dr-link"><input readonly aria-label="分享网址" value="'+esc(location.origin+p.share_path)+'">'+
 btn('share','复制链接','class="dr-primary"')+
 btn('open-share','打开分享卡')+'</div>':
 '<p class="dr-hint">本张奇遇尚未公开。图片可自己保存；只有明确点击上方「主动生成分享链接」才会公开。</p>')+
 '<p class="dr-hint">馆藏源如果后来撤回或删除，公开奇遇卡将实时遮蔽来源；手工文字由作者主动分享后仍可见。</p></section>';
}
function drawCardPng(){
 const p=project();if(!p?.finished)throw Error('完成奇遇全部站点后才能保存图片');
 const canvas=document.createElement('canvas');canvas.width=1080;canvas.height=1350;
 const ctx=canvas.getContext('2d');if(!ctx)throw Error('当前浏览器不支持 Canvas');
 const bg=ctx.createLinearGradient(0,0,1080,1350);bg.addColorStop(0,'#0f2339');bg.addColorStop(1,'#2d243a');ctx.fillStyle=bg;ctx.fillRect(0,0,1080,1350);
 ctx.strokeStyle='#ddbd86';ctx.lineWidth=4;ctx.strokeRect(44,44,992,1262);
 ctx.fillStyle='#ecc890';ctx.font='bold 26px sans-serif';ctx.fillText('✳ WONDER ATLAS · MY DESTINY CARD',80,110);
 ctx.fillStyle='#fff0cc';ctx.font='bold 47px sans-serif';ctx.fillText(p.title.slice(0,24),80,192);
 ctx.fillStyle='#b9c9d3';ctx.font='25px sans-serif';ctx.fillText('收藏万物 · 接力命运 · 每站真实随机',80,255);
 stages().forEach((s,i)=>{
  const y=316+i*171;ctx.fillStyle='#20334b';ctx.fillRect(75,y,930,147);
  ctx.fillStyle=palettes[i%palettes.length];ctx.fillRect(75,y,10,147);
  ctx.fillStyle='#d8c5a8';ctx.font='24px sans-serif';ctx.fillText('第 '+(i+1)+' 站 · '+s.topic_label.slice(0,16),105,y+43);
  ctx.fillStyle='#fff3da';ctx.font='bold 39px sans-serif';
  const label=s.label||'未抽取';ctx.fillText(label.length>22?label.slice(0,20)+'…':label,105,y+105);
 });
 ctx.fillStyle='#aabdcf';ctx.font='22px sans-serif';ctx.fillText('随机娱乐 · 资料来源以当前公开状态为准 · 万物博物馆',79,1262);
 const link=document.createElement('a');link.href=canvas.toDataURL('image/png');
 link.download='万物奇遇卡-'+(p.title||'今日')+'.png';link.click();
}
function friendlyError(msg){A.error=msg;if(typeof toast==='function')toast(msg);}
async function rerender(){
 if(window.S?.view!=='adventure')return;
 const main=document.querySelector('#main');
 if(main)main.innerHTML=await render();
}
async function advance(){
 if(A.busy)return;
 A.busy=true;A.error='';
 let final;
 try{
  if(signed()){
   const r=await api('/adventures/'+A.selected+'/advance',{method:'POST'});
   final=r.stage;
  }else{
   const index=A.demo.steps.length;
   if(index>=DEMO.length)throw Error('游客奇遇已经全部完成');
   const r=await api('/wheels/preview',{method:'POST',body:{options:DEMO[index].options,no_repeat:false}});
   final={label:r.label};
   A.demo.steps.push(final);
  }
  const currentStage=stages().find(x=>!x.completed);
  // The result has already been committed on the server; this is only a brief
  // motion cue, never an independently generated or manipulable client draw.
  const button=document.querySelector('[data-destiny="advance"]');
  if(button){button.textContent='✨ 命运正在揭晓…';button.disabled=true;}
  await new Promise(resolve=>setTimeout(resolve,720));
  A.notice='✨ 本站命运已揭晓：'+final.label;
  await rerender();
 }finally{A.busy=false;}
}
document.addEventListener('click',async e=>{
 const b=e.target.closest('[data-destiny]');if(!b)return;
 e.preventDefault();e.stopImmediatePropagation();
 const act=b.dataset.destiny,id=Number(b.dataset.id||0);
 try{
  if(act==='advance'){await advance();await rerender();return;}
  if(A.busy)return;
  if(act==='add-stage'){
   if(A.stageWheelIds.length>=5)return;
   A.stageWheelIds.push(0);
  }else if(act==='remove-stage'){
   if(A.stageWheelIds.length<=2)return;
   A.stageWheelIds.pop();
  }else if(act==='select-card'){A.selected=id;A.notice='';}
  else if(act==='go-wheels'){
   await navigate('wheels');return;
  }else if(act==='visibility'){
   if(b.dataset.status==='public'&&!window.confirm('公开后，获得链接的任何人都能看见你这张奇遇卡里所有手动选项的结果。确认吗？'))return;
   await api('/adventures/'+A.selected+'/visibility',{method:'PATCH',body:{visibility:b.dataset.status}});
   A.notice=b.dataset.status==='public'?'✦ 分享链接已生成':'分享权限已撤回，旧链接立即失效';
  }else if(act==='share'){
   const path=A.detail?.share_path;
   if(!path)throw Error('先主动公开，才会生成分享链接');
   const url=location.origin+path;
   try{await navigator.clipboard.writeText(url);A.notice='✅ 分享链接已复制';}
   catch(_){window.prompt('复制下面的链接分享：',url);A.notice='请复制分享网址';}
  }else if(act==='open-share'){
   if(A.detail?.share_path)window.open(A.detail.share_path,'_blank','noopener');
   return;
  }else if(act==='look-exhibit'){
   if(typeof openDetail==='function')await openDetail(id);
   return;
  }else if(act==='image'){drawCardPng();return;}
  else if(act==='delete'){
   if(!window.confirm('删除这张奇遇卡和它的步骤结果？不会删除原有转盘和藏品。'))return;
   await api('/adventures/'+A.selected,{method:'DELETE'});
   A.selected=0;A.notice='已经删除这张奇遇卡';}
  else if(act==='restart'){A.demo.steps=[];A.notice='重新开始一场演示奇遇';}
  await rerender();
 }catch(err){friendlyError(err.message||'操作未能完成');await rerender();}
},true);
document.addEventListener('change',e=>{
 const select=e.target.closest('[data-stage-id]');
 if(!select)return;
 const form=document.getElementById('dr-compose');
 if(form){A.stageWheelIds=A.stageWheelIds.map((x,i)=>Number(form.elements['stage'+i]?.value||0));}
},true);
document.addEventListener('submit',async e=>{
 if(e.target.id!=='dr-compose')return;
 e.preventDefault();e.stopImmediatePropagation();
 const form=e.target;
 try{
  const fd=new FormData(form),ids=A.stageWheelIds.map((_,i)=>Number(fd.get('stage'+i)));
  const r=await api('/adventures',{method:'POST',body:{title:String(fd.get('title')||'').trim(),wheel_ids:ids}});
  A.selected=r.id;A.notice='🌠 私人命运接力已创建！抽取下一站即可开始。';
  await rerender();
 }catch(err){friendlyError(err.message||'不能创建奇遇');}
},true);
async function render(){await load();return '<div class="dr-root">'+intro()+
 (A.notice?'<div class="dr-notice">'+esc(A.notice)+'</div>':'')+
 (A.error?'<div class="dr-error">'+esc(A.error)+'</div>':'')+
 '<div class="dr-layout"><div>'+collection()+'</div><div>'+routeCard()+shareInfo()+'</div></div>'+
 '<p class="dr-footer">随机选择不是现实建议；请结合自身实际情况决策。用户内容未经本站事实认证。</p></div>';}
window.WonderAdventure={render,stop:()=>{A.drawing++;}};
})();
