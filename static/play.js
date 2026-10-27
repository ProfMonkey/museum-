/* V21 Wonder Atlas: interactive science mini-labs & opt-in relay routes.
   Experiments are simplified models. Routes contain real public contributions only. */
(() => {
'use strict';
const P={tab:'experiments',kind:'orbit',config:null,params:{kind:'orbit',a:1,b:1,c:1,iterations:55},
  result:null,relays:[],relayId:0,relay:null,sources:[],query:'',selected:0,
  notice:'',error:'',drawToken:0};
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
const fmt=x=>Number(x).toLocaleString('zh-CN',{maximumFractionDigits:4});
const logged=()=>Boolean(window.S?.user);
const click=(action,label,attr='')=>'<button type="button" data-play="'+action+'" '+attr+'>'+label+'</button>';
async function load(){
 P.error='';
 try{
  if(!P.config)P.config=await api('/play/config');
  if(P.tab==='relays'){
    P.relays=(await api('/play/relays')).items||[];
    if(!P.relays.some(x=>x.id===P.relayId))P.relayId=P.relays[0]?.id||0;
    P.relay=P.relayId?await api('/play/relays/'+P.relayId):null;
    P.sources=(await api('/play/sources?q='+encodeURIComponent(P.query))).items||[];
    if(!P.sources.some(x=>x.id===P.selected))P.selected=P.sources[0]?.id||0;
  }
 }catch(e){P.error=e.message||'无法读取互动展馆';P.relay=null;}
}
function head(){
 return '<section class="pl-hero"><span>WONDER ATLAS · V21 · EVERYTHING IS INTERACTIVE</span>'+
  '<h1>万物皆可玩。<br><em>让好奇心动起来。</em></h1>'+
  '<p>改变参数，观察规律；沿着别人留下的奇妙线索，从化石走到芯片，从古画走到宇宙。你可以成为探索者，也可以成为下一站的建造者。</p>'+
  '<div class="pl-badges">✦ 互动科学 · 数学艺术 · 真实馆藏接力</div></section>';
}
function tabs(){
 return '<div class="pl-tabs" role="tablist" aria-label="万物互动展馆">'+
  [['experiments','⚙ 可玩的万物实验'],['relays','🔗 万物接力计划'],['studio','✦ 万物造物工坊']].map(([key,text])=>
  click('tab',text,'data-tab="'+key+'" role="tab" aria-selected="'+(P.tab===key)+'" class="'+(P.tab===key?'active':'')+'"')).join('')+'</div>';
}
const labFields={
 orbit:[['a','轨道半径（AU）',.3,6,.1],['b','中心恒星质量（太阳=1）',.1,3,.1]],
 gears:[['a','主动齿轮齿数',8,120,1],['b','从动齿轮齿数',8,120,1],['c','输入转速（rpm）',5,120,1]],
 fractal:[['a','视点横坐标',-2,1,.1],['b','视点纵坐标',-1.5,1.5,.1],['c','放大倍数',.8,5,.1],['iterations','最大迭代次数',20,90,5]]
};
const defaults={orbit:{a:1,b:1,c:1,iterations:55},gears:{a:24,b:48,c:60,iterations:55},
 fractal:{a:-.6,b:0,c:1,iterations:55}};
function form(){
 return '<div class="pl-grid"><section class="pl-panel"><span class="pl-kicker">01 / HANDS-ON EXHIBITS</span>'+
 '<h2>⚙ 动手改变世界的参数</h2><p>这里呈现的是简化的教育模型，不是天体预测、实际机械设计或精确的数学证明。</p>'+
 '<div class="pl-models">'+P.config.models.map(x=>click('model',esc(x.title),
   'data-kind="'+x.kind+'" class="'+(P.kind===x.kind?'active':'')+'"')).join('')+'</div>'+
 '<form id="pl-form" class="pl-form"><div class="pl-fields">'+labFields[P.kind].map(([id,label,min,max,step])=>
 '<label>'+label+'<input name="'+id+'" type="number" min="'+min+'" max="'+max+'" step="'+step+'" value="'+P.params[id]+'" required></label>').join('')+'</div>'+
 '<button type="submit" class="pl-primary">▶ 运行互动模型</button></form>'+
 '<div class="pl-formula"><b>实验知识卡</b><p>'+(P.kind==='orbit'?'轨道周期与半径、中心质量的关系；简化二体圆轨道。':
 P.kind==='gears'?'理想外啮合齿轮具有反向转动与齿数比关系。':'复平面上的迭代方程会生成复杂的分形图像。')+'</p></div></section>'+
 '<section class="pl-panel pl-visual"><span class="pl-kicker">LIVE INTERACTIVE VIEW</span><h2>✦ 参数可视化</h2>'+
 '<canvas id="pl-canvas" width="520" height="310" role="img" aria-label="互动模型画布">此浏览器不支持 Canvas。</canvas>'+
 (P.result?'<div class="pl-summary"><h3>'+esc(P.result.name)+'</h3>'+
  Object.entries(P.result.outcome).map(([k,v])=>'<div><span>'+esc(({
   period_years:'公转周期（地球年）',speed_kms:'轨道速度（km/s）',output_rpm:'输出转速（rpm）',
   ideal_torque_ratio:'理想扭矩比',max_iterations:'最大迭代',window_width:'观察窗口宽度'})[k]||k)+'</span><b>'+fmt(v)+'</b></div>').join('')+
  '<p>'+esc(P.result.formula)+'</p><small>'+esc(P.result.note)+'</small>'+
  (logged()?click('record','♡ 保存为私人实验藏品','class="pl-save"'):
  '<p>登录后可将自己的实验参数收藏为私人藏品。</p>')+'</div>':
  '<div class="pl-empty"><b>◉</b><p>左侧选择参数并点击「运行互动模型」。<br>轨道和齿轮会动起来，分形图像也会随着参数变化。</p></div>')+
 '</section></div>';
}
function sourceList(){
 return '<div class="pl-sources">'+(P.sources.length?P.sources.map(x=>click('source','<b>'+esc(x.title)+'</b><small>'+esc(x.category)+' · '+esc(x.curator)+'</small>',
  'data-id="'+x.id+'" class="'+(x.id===P.selected?'active':'')+'"')).join(''):
  '<div class="pl-empty">没有找到仍公开的社区藏品；请尝试其他关键词。</div>')+'</div>';
}
function relayCards(){
 return '<div class="pl-relay-grid">'+(P.relays.length?P.relays.map(x=>click('relay','<span>NO. '+x.id+' · '+x.count+' 站</span><b>'+esc(x.title)+'</b><small>'+esc(x.first)+' → '+esc(x.last)+'</small>',
 'data-id="'+x.id+'" class="'+(x.id===P.relayId?'active':'')+'"')).join(''):
 '<div class="pl-empty">还没有任何公开的接力路线。第一条路线由你开启。</div>')+'</div>';
}
function relayBody(){
 const r=P.relay;
 if(!r)return '<section class="pl-panel"><h2>🏛 接力图鉴</h2><p>选择一条存在的路线，查看其他馆长的真实接力记录。</p></section>';
 return '<section class="pl-panel"><div class="pl-headerline"><div><span class="pl-kicker">COMMUNITY ROUTE · '+r.count+' STOPS</span>'+
 '<h2>'+esc(r.title)+'</h2><p>发起者：'+esc(r.creator)+' · '+(r.is_open?'仍然可以参与':'已结束接力')+'</p></div>'+
 (r.is_owner?'<div class="pl-ops">'+click('toggle',r.is_open?'⏹ 结束接力':'▶ 重新开放',
 'data-next="'+(r.is_open?'false':'true')+'"')+click('delete','删除接力')+'</div>':'')+'</div>'+
 '<div class="pl-steps">'+r.steps.map((s,i)=>'<article><div class="pl-step-index">'+String(i+1).padStart(2,'0')+'</div>'+
 '<div class="pl-step-content"><small>'+esc(s.category)+' · 藏品来自：'+esc(s.curator)+'</small>'+
 '<h3>'+esc(s.title)+'</h3><p>'+esc(s.reason)+'</p>'+
 '<div class="pl-step-meta"><span>'+esc(s.relation)+' · 接力人：'+esc(s.contributor)+'</span>'+
 (s.source_url?'<a href="'+esc(s.source_url)+'" target="_blank" rel="noopener noreferrer">投稿者提供的参考链接 ↗（未经本站核验）</a>':'')+
 click('exhibit','查看原始藏品','data-id="'+s.exhibit_id+'"')+'</div></div></article>').join('')+'</div>'+
 '<p class="pl-warning">仅展示目前仍公开且顺序完整的接力。中间藏品撤回公开后，后续历史不再显示，接力无法继续追加。</p></section>';
}
function relaysView(){
 return '<section class="pl-panel"><span class="pl-kicker">02 / THE WONDER RELAY</span>'+
 '<h2>🔗 一个人收藏一件，所有人串起世界</h2>'+
 '<p>从「陨石」联想到「太阳系」，再联想到「航天器」——每一站都必须指向真实公开的社区藏品。联想不等于科学因果；参考网址也不代表经过本站审查。</p>'+
 relayCards()+'</section>'+relayBody()+
 '<div class="pl-grid"><section class="pl-panel"><h2>🔎 找到下一个万物节点</h2>'+
 '<form id="pl-search" class="pl-search"><label>按藏品标题、简介搜索<input name="query" value="'+esc(P.query)+'" maxlength="70" placeholder="陨石 / 恐龙 / 机械 / 游戏"></label><button type="submit">搜索</button></form>'+
 '<p class="pl-warning">请选择下面一件已经由真实馆长公开的展品。你无法上传伪造的社区来源作为节点。</p>'+
 sourceList()+'</section>'+
 '<section class="pl-panel"><h2>✦ '+(P.relay?.is_open?'加入一段新联系':'开辟探索路线')+'</h2>'+
 (!logged()?'<div class="pl-empty">注册或登录后即可开启自己的接力，或帮助别人连接下一站。</div>':
 '<form id="pl-create-relay" class="pl-mini-form"><h3>创造新的万物接力</h3>'+
 '<label>路线名称<input name="title" required minlength="2" maxlength="60" placeholder="一块化石通往星空"></label>'+
 '<p>起点：'+esc(P.sources.find(x=>x.id===P.selected)?.title||'请先选择公开展品')+'</p>'+
 '<button class="pl-primary" type="submit" '+(!P.selected?'disabled':'')+'>从所选展品发起</button></form>'+
 (P.relay?.is_open?'<form id="pl-link-form" class="pl-mini-form"><h3>把所选展品接到当前路线</h3>'+
 '<label>关系类型<select name="relation"><option>创意联想</option><option>来源线索</option></select></label>'+
 '<label>两件事物为什么有关联？<textarea name="reason" minlength="8" maxlength="280" rows="3" required placeholder="这是一条启发性的创意联想，并非必然的科学因果。"></textarea></label>'+
 '<label>来源网址（仅来源线索填写 HTTPS）<input name="source_url" maxlength="320" placeholder="https://..."></label>'+
 '<button class="pl-primary" type="submit" '+(!P.selected||P.relay.count>=12?'disabled':'')+'>🔗 我来接力下一站</button>'+
 '<p class="pl-warning">每条路线最多 12 站，每位馆长最多参与 3 站；来源线索需要提供 HTTPS 参考链接，但本站不会自动认定其正确性。</p></form>':'')
 )+'</section></div>';
}
async function render(){
 await load();
 return '<div class="pl-root">'+head()+tabs()+(P.notice?'<div class="pl-notice">'+esc(P.notice)+'</div>':'')+
 (P.error?'<div class="pl-error">'+esc(P.error)+'</div>':'')+
 (P.tab==='experiments'?form():P.tab==='relays'?relaysView():await WonderStudio.render())+
 '<footer class="pl-warning">现实藏品不等于已经证实；模型推演不等于科学测量。公开与私人内容保持隔离。</footer></div>';
}
function afterMount(){
 P.drawToken++;
 const canvas=document.getElementById('pl-canvas');
 if(!canvas || P.tab!=='experiments')return;
 const ctx=canvas.getContext('2d');if(!ctx)return;
 const {width:w,height:h}=canvas;const token=P.drawToken;
 if(!P.result){ctx.fillStyle='#111d2d';ctx.fillRect(0,0,w,h);return;}
 const data=P.result,p=data.params;
 function back(){
  ctx.fillStyle='#091827';ctx.fillRect(0,0,w,h);
  ctx.strokeStyle='rgba(226,195,132,.12)';ctx.lineWidth=1;
  for(let y=25;y<h;y+=40){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}
  for(let x=20;x<w;x+=40){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke();}
 }
 if(data.kind==='fractal'){
  const pix=ctx.createImageData(w,h),iter=p.iterations,scale=3.4/(w*p.zoom);
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
   const cr=p.center_x+(x-w/2)*scale,ci=p.center_y+(y-h/2)*scale;
   let zr=0,zi=0,n=0;while(n<iter && zr*zr+zi*zi<=4){
    const next=zr*zr-zi*zi+cr;zi=2*zr*zi+ci;zr=next;n++;
   }
   const off=(y*w+x)*4,shade=n===iter?0:n/iter;
   pix.data[off]=n===iter?10:Math.round(55+170*Math.sqrt(shade));
   pix.data[off+1]=n===iter?23:Math.round(65+120*Math.sin(shade*2.1));
   pix.data[off+2]=n===iter?40:Math.round(80+145*Math.sin(shade*3.3));
   pix.data[off+3]=255;
  }ctx.putImageData(pix,0,0);return;
 }
 function gear(x,y,r,angle,tone){
  ctx.save();ctx.translate(x,y);ctx.rotate(angle);
  ctx.beginPath();const n=48;
  for(let i=0;i<n;i++){const a=2*Math.PI*i/n,rr=r*(i%4===0||i%4===1?1.13:1);
   if(i===0)ctx.moveTo(rr*Math.cos(a),rr*Math.sin(a));else ctx.lineTo(rr*Math.cos(a),rr*Math.sin(a));}
  ctx.closePath();ctx.fillStyle=tone;ctx.fill();ctx.strokeStyle='#dfcb96';ctx.lineWidth=3;ctx.stroke();
  for(let i=0;i<6;i++){const a=i*Math.PI/3;ctx.strokeStyle='#d4c4ab';
   ctx.lineWidth=6;ctx.beginPath();ctx.moveTo(14*Math.cos(a),14*Math.sin(a));
   ctx.lineTo((r-12)*Math.cos(a),(r-12)*Math.sin(a));ctx.stroke();}
  ctx.fillStyle='#0b1521';ctx.beginPath();ctx.arc(0,0,13,0,2*Math.PI);ctx.fill();ctx.restore();
 }
 const t0=performance.now(),speed=window.matchMedia('(prefers-reduced-motion: reduce)').matches?0:1;
 function frame(t){
  if(token!==P.drawToken||window.S?.view!=='play'||P.tab!=='experiments')return;
  back();
  const time=Math.min((t-t0)/1000,100000);
  if(data.kind==='orbit'){
   const radius=Math.min(122,40+p.radius_au*17),angle=time*2*Math.PI/Math.max(3,Math.min(24,data.outcome.period_years*7))*speed;
   ctx.strokeStyle='#b9a47a';ctx.lineWidth=1.7;ctx.beginPath();ctx.ellipse(w/2,h/2,radius,radius*.65,0,0,2*Math.PI);ctx.stroke();
   const g=ctx.createRadialGradient(w/2,h/2,3,w/2,h/2,30);
   g.addColorStop(0,'#fff5cf');g.addColorStop(.35,'#f0c870');g.addColorStop(1,'rgba(251,174,73,.08)');
   ctx.fillStyle=g;ctx.beginPath();ctx.arc(w/2,h/2,30,0,2*Math.PI);ctx.fill();
   ctx.fillStyle='#a6c8fa';ctx.shadowColor='#83afe4';ctx.shadowBlur=13;
   ctx.beginPath();ctx.arc(w/2+radius*Math.cos(angle),h/2+radius*.65*Math.sin(angle),10,0,2*Math.PI);ctx.fill();ctx.shadowBlur=0;
  }else{
   const rpm=p.input_rpm,ratio=p.driver_teeth/p.driven_teeth;
   const a=time*2*Math.PI*(rpm/60)*speed;
   const r1=50,r2=50/ratio>100?100:50/ratio<34?34:50/ratio;
   const x1=w/2-r1*.82,x2=w/2+r2*.84;
   gear(x1,h/2,r1,a,'#97764d');gear(x2,h/2,r2,-a*ratio,'#476b81');
   ctx.fillStyle='#d9c8a3';ctx.font='12px sans-serif';ctx.textAlign='center';
   ctx.fillText('主动 '+p.driver_teeth+' 齿',x1,h/2+Math.max(r1,r2)+35);
   ctx.fillText('从动 '+p.driven_teeth+' 齿',x2,h/2+Math.max(r1,r2)+35);
  }
  if(speed)requestAnimationFrame(frame);
 }
 requestAnimationFrame(frame);
}
async function refresh(){
 if(window.S?.view!=='play')return;
 document.querySelector('#main').innerHTML=await render();
 requestAnimationFrame(afterMount);
}
document.addEventListener('click',async ev=>{
 const b=ev.target.closest('[data-play]');if(!b)return;
 ev.preventDefault();ev.stopImmediatePropagation();
 const k=b.dataset.play,id=Number(b.dataset.id||0);
 try{
  if(k==='tab'){window.WonderStudio?.stop();P.tab=b.dataset.tab;P.notice='';await refresh();}
  else if(k==='model'){
   P.kind=b.dataset.kind;P.params={kind:P.kind,...defaults[P.kind]};P.result=null;P.notice='';await refresh();
  }else if(k==='record'){
   const r=await api('/play/records',{method:'POST',body:P.params});
   P.notice='♡ 已存入私人藏品 NO. '+r.id+'，不会自动公开。';await refresh();
  }else if(k==='relay'){P.relayId=id;await refresh();}
  else if(k==='source'){P.selected=id;await refresh();}
  else if(k==='toggle'){
   await api('/play/relays/'+P.relayId,{method:'PATCH',body:{open:b.dataset.next==='true'}});
   P.notice='接力开放状态已更新';await refresh();
  }else if(k==='delete'){
   if(!confirm('确认删除这一条万物接力？原始藏品不会删除。'))return;
   await api('/play/relays/'+P.relayId,{method:'DELETE'});P.relayId=0;P.notice='路线已删除';await refresh();
  }else if(k==='exhibit' && typeof openDetail==='function'){await openDetail(id);}
 }catch(err){if(typeof toast==='function')toast(err.message||'操作失败');}
},true);
document.addEventListener('submit',async ev=>{
 const name=ev.target.id;if(!['pl-form','pl-search','pl-create-relay','pl-link-form'].includes(name))return;
 ev.preventDefault();ev.stopImmediatePropagation();
 const body=Object.fromEntries(new FormData(ev.target));
 try{
  if(name==='pl-form'){
   const params={kind:P.kind,...defaults[P.kind]};
   for(const x of labFields[P.kind])params[x[0]]=Number(body[x[0]]);
   const r=await api('/play/preview',{method:'POST',body:params});
   P.params=params;P.result=r.result;P.notice='参数已重新计算。模型结果不是现实测量。';
  }else if(name==='pl-search'){P.query=body.query.trim();}
  else if(name==='pl-create-relay'){
   const r=await api('/play/relays',{method:'POST',body:{source_id:P.selected,title:body.title}});
   P.relayId=r.id;P.notice='接力已经创建，其他真实馆长可以继续连接下一站。';
  }else if(name==='pl-link-form'){
   await api('/play/relays/'+P.relayId+'/steps',{method:'POST',
    body:{source_id:P.selected,relation:body.relation,reason:body.reason,source_url:body.source_url.trim()}});
   P.notice='接力成功，你的关联理由已写入这条万物路线。';
  }
  await refresh();
 }catch(err){if(typeof toast==='function')toast(err.message||'操作失败');}
},true);
window.WonderPlay={render,afterMount,stop(){P.drawToken++;window.WonderStudio?.stop();},startFromExhibit(id,title){P.tab='relays';P.selected=Number(id);P.query=String(title||'');P.relayId=0;P.notice='已选中该公开藏品，可以从此创建接力路线。';}};
})();