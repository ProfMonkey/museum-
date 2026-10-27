/* V29 · parallel universes — reciprocal, opt-in encounters, no private graph sharing. */
(() => {
'use strict';
const V={source:0,target:'',suggestions:[],loadedSource:0,message:''};
const esc=s=>String(s??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[ch]));
const button=(action,text,attrs='')=>'<button type="button" data-pv="'+action+'" '+attrs+'>'+text+'</button>';
const exhibitCard=(e,compact=false)=>{
 if(!e)return '<span class="pv-redacted">🔒 原始展品已不可用</span>';
 return '<div class="pv-object"><div class="pv-object-icon">✦</div><div><div class="pv-object-title">'+
 esc(e.title)+'</div><small>'+esc(e.category)+' · '+esc(e.curator)+'</small></div>'+
 button('exhibit','↗','data-id="'+e.id+'" title="打开真实藏品"')+'</div>';
};
function inviteItem(inv,incoming,mine){
 return '<article class="pv-invite">'+
 '<div class="pv-card-top"><b>'+(incoming?'✉ 来自 ':'✧ 邀请给 ')+esc(incoming?inv.sender:inv.recipient)+'</b><span>'+esc(inv.available?'待双方确认':'暂不可用')+'</span></div>'+
 exhibitCard(inv.sender_exhibit)+
 (incoming&&inv.available&&mine.length?
  '<form class="pv-accept" data-invite="'+inv.id+'"><label>选择你愿意加入的公开展品<select name="exhibit_id" required>'+
  mine.map(x=>'<option value="'+x.id+'">'+esc(x.title)+'</option>').join('')+
  '</select></label><button type="submit" class="pv-primary">✓ 同意并建立连接</button></form>':'')+
 '<div class="pv-row">'+(incoming?button('decline','谢绝邀请','data-id="'+inv.id+'" class="pv-minor"'):
 button('cancel','撤回邀请','data-id="'+inv.id+'" class="pv-minor"'))+'</div></article>';
}
function bridgeItem(x){
 const ok=x.available, p=x.progress||{mine:false,partner:false,both:false};
 return '<article class="pv-bridge '+(ok?'':'pv-offline')+'">'+
 '<div class="pv-card-top"><div><span class="pv-kicker">PARALLEL ENCOUNTER #'+x.id+'</span><h3>'+
 esc(x.sender)+' <span>×</span> '+esc(x.recipient)+'</h3></div><span class="pv-status">'+
 (ok?(p.both?'✧ 双方自行完成':p.mine?'等对方探索':'跨馆连接已建立'):'🔒 暂不可用')+
 '</span></div>'+
 (ok?'<div class="pv-link"><div>'+exhibitCard(x.sender_exhibit,true)+'</div><div class="pv-link-core"><span>✧</span><small>双方自愿会合</small></div><div>'+exhibitCard(x.recipient_exhibit,true)+'</div></div>'+
 '<div class="pv-clue"><strong>共同线索</strong><span>'+esc(x.clue||'无标签/类别交集；此连接由双方自行决定。')+'</span>'+
 '<small>这是元数据重合，不是经过核验的事实或因果关系。</small></div>'+
 '<div class="pv-progress"><span>'+(p.mine?'✅ 我已自行探索':'◯ 我尚未标记')+'</span><span>'+
 (p.partner?'✅ 对方已自行探索':'◯ 对方尚未标记')+'</span></div>':
 '<div class="pv-redaction">原始公开藏品被删除、撤回或所属作品不再公开。原来的名称和连线内容已隐藏。</div>')+
 '<div class="pv-actions">'+(ok?button(p.mine?'unmark':'mark',p.mine?'取消我的探索标记':'✓ 我已探索这次会合','data-id="'+x.id+'" class="pv-primary"'):'')+
 button('close','结束会合','data-id="'+x.id+'" class="pv-minor"')+'</div></article>';
}
async function render(){
 if(!window.S?.user)return '<section class="pv-root pv-guest"><div class="pv-kicker">WONDER ATLAS · WORLD 29</div><h1>🌌 万物平行宇宙</h1><p>邀请另一位真正的馆长，让两座博物馆在双方同意之后相遇。私人星图不会自动分享。</p>'+
 '<button class="pv-primary" data-action="login">登录 / 注册 · 开启会合</button></section>';
 let o;
 try{o=await api('/parallel');V.message='';}catch(e){return '<section class="pv-root"><h1>平行宇宙暂时无法连接</h1><p>'+esc(e.message)+'</p>'+button('reload','重新连接')+'</section>'}
 const mine=o.mine||[];
 if(!mine.some(x=>x.id===V.source)){V.source=mine[0]?.id||0;V.suggestions=[];V.loadedSource=0}
 if(V.source && V.loadedSource!==V.source){
  try{const r=await api('/parallel/suggestions?exhibit_id='+V.source);V.suggestions=r.items||[];V.loadedSource=V.source}
  catch(err){V.suggestions=[];V.message=err.message}
 }
 const sources=mine.map(e=>'<option value="'+e.id+'" '+(e.id===V.source?'selected':'')+'>'+
 esc(e.title)+'</option>').join('');
 return '<div class="pv-root"><section class="pv-hero"><div class="pv-kicker">WONDER ATLAS / V29 / PARALLEL UNIVERSES</div>'+
 '<h1>当两个世界相遇，<br><em>万物便有了新的可能。</em></h1>'+
 '<p>你带来一件公开藏品，对方自由选择是否加入及带来哪件藏品。两人都同意，才会形成一座真正的跨馆桥梁。</p>'+
 '<div class="pv-badges"><span>🔒 私人星图不公开</span><span>🤝 双方自主同意</span><span>✦ 使用真实馆藏</span></div>'+
 '<div class="pv-orbit pv-orbit-a"></div><div class="pv-orbit pv-orbit-b"></div></section>'+
 (V.message?'<p class="pv-alert">'+esc(V.message)+'</p>':'')+
 '<section class="pv-statline"><div><b>'+o.bridges.length+'</b><span>我的跨馆会合</span></div>'+
 '<div><b>'+o.incoming.length+'</b><span>待回应邀请</span></div><div><b>'+o.outgoing.length+'</b><span>已发送邀请</span></div></section>'+
 '<div class="pv-layout"><div><section class="pv-panel"><div class="pv-kicker">01 · SEND A SIGNAL</div>'+
 '<h2>发出平行宇宙信号</h2><p>先挑一件自己当前公开的藏品，再邀请其他馆长。</p>'+
 (mine.length?'<form id="pvInviteForm"><label>从我的哪件展品出发？<select name="exhibit_id" id="pvSource">'+sources+'</select></label>'+
 '<label>邀请哪位馆长？<input id="pvTarget" name="recipient" required minlength="3" maxlength="24" value="'+esc(V.target)+'" placeholder="输入对方准确的用户名"></label>'+
 '<button type="submit" class="pv-primary">✉ 发送私密跨馆邀请</button></form>':
 '<div class="pv-empty">需要先发布至少一件真正公开的藏品，才可以发出会合邀请。私人藏品不能参与。</div>')+
 '</section><section class="pv-panel"><div class="pv-kicker">02 · EXPLAINABLE SIGNALS</div>'+
 '<h2>也许会相遇的世界</h2><p>仅比较现有公开藏品的标签、类别、领域。出现在线索中不代表对方已同意，也不保证事实关联。</p>'+
 (V.suggestions.length?'<div class="pv-suggestions">'+V.suggestions.map(x=>'<article>'+
 '<div class="pv-card-top"><b>'+esc(x.title)+'</b><small>@'+esc(x.curator)+'</small></div>'+
 '<p>'+esc(x.reason)+'</p><div class="pv-row">'+
 button('target','邀请 '+esc(x.curator),'data-user="'+esc(x.curator)+'"')+
 button('exhibit','查看原展品 ↗','data-id="'+x.id+'" class="pv-minor"')+
 '</div></article>').join('')+'</div>':
 '<div class="pv-empty">'+(mine.length?'当前没有找到明确的标签或分类重合。你仍可自行邀请认识的馆长。':'公开一件展品后才能查找交汇线索。')+'</div>')+
 '<p class="pv-tip">建议只使用最近最多 300 件当前公开跨馆藏品，不冒充完整语义搜索或 AI 推理。</p></section></div>'+
 '<div><section class="pv-panel"><div class="pv-kicker">03 · RECIPROCAL CONSENT</div><h2>等待我的回应 <span class="pv-count">'+o.incoming.length+'</span></h2>'+
 (o.incoming.length?o.incoming.map(x=>inviteItem(x,true,mine)).join(''):'<div class="pv-empty">没有等待你回复的会合邀请。</div>')+
 '<h2 class="pv-second-title">已经发出的邀请 <span class="pv-count">'+o.outgoing.length+'</span></h2>'+
 (o.outgoing.length?o.outgoing.map(x=>inviteItem(x,false,mine)).join(''):'<div class="pv-empty">还没有向其他馆长发出信号。</div>')+
 '</section></div></div>'+
 '<section class="pv-panel pv-bridge-panel"><div class="pv-kicker">04 · TWO CURATORS, ONE STORY</div>'+
 '<h2>🤝 我们的跨馆会合 <span class="pv-count">'+o.bridges.length+'</span></h2>'+
 '<p>每位馆长可以自行标记探索。当双方都标记时，这场双人探索会被记录为「双方自行完成」，不代表实际到访或事实认证。</p>'+
 (o.bridges.length?'<div class="pv-bridge-grid">'+o.bridges.map(bridgeItem).join('')+'</div>':
 '<div class="pv-empty pv-big">✧ 尚无已建立的会合。跨越两个世界的第一座桥梁，由双方共同决定。</div>')+'</section>'+
 '<p class="pv-foot">所有邀请仅对双方可见，公开馆藏随来源撤回即时遮蔽；不会暴露 V27 私人星图、V28 私人航线或私密展品。</p></div>';
}
async function refresh(){if(window.S?.view==='parallel'){const main=document.querySelector('#main');if(main)main.innerHTML=await render();}}
document.addEventListener('change',async e=>{
 if(e.target.id!=='pvSource')return;
 V.source=Number(e.target.value);V.loadedSource=0;V.target=document.querySelector('#pvTarget')?.value||'';
 await refresh();
},true);
document.addEventListener('submit',async e=>{
 const f=e.target;
 if(f.id!=='pvInviteForm'&&!f.matches('form.pv-accept'))return;
 e.preventDefault();e.stopImmediatePropagation();
 const data=Object.fromEntries(new FormData(f).entries());
 const submit=f.querySelector('[type="submit"]');if(submit)submit.disabled=true;
 try{
  if(f.id==='pvInviteForm'){
   V.target=String(data.recipient||'').trim();
   await api('/parallel/invitations',{method:'POST',body:{recipient:V.target,exhibit_id:Number(data.exhibit_id)}});
   V.target='';toast('邀请已发送，等待对方同意');await refresh();
  }else{
   await api('/parallel/invitations/'+Number(f.dataset.invite)+'/accept',{method:'POST',body:{exhibit_id:Number(data.exhibit_id)}});
   toast('双方已选择公开藏品，平行世界会合成功 ✧');await refresh();
  }
 }catch(err){V.message=err.message||'操作失败';toast(V.message);await refresh()}
 finally{if(submit)submit.disabled=false}
},true);
document.addEventListener('click',async e=>{
 const b=e.target.closest('[data-pv]');if(!b)return;
 e.preventDefault();e.stopImmediatePropagation();
 const action=b.dataset.pv,id=Number(b.dataset.id||0);
 try{
  if(action==='reload'){await refresh();return}
  if(action==='exhibit'){await openDetail(id);return}
  if(action==='target'){
   V.target=b.dataset.user||'';
   const input=document.querySelector('#pvTarget');
   if(input){input.value=V.target;input.focus();input.scrollIntoView({behavior:'smooth',block:'center'})}
   return;
  }
  if(action==='close'&&!confirm('确定结束这场跨馆会合？双方的探索标记会清除，原始馆藏不会删除。'))return;
  const actions={decline:['POST','/parallel/invitations/'+id+'/decline'],
                 cancel:['POST','/parallel/invitations/'+id+'/cancel'],
                 close:['DELETE','/parallel/bridges/'+id],
                 mark:['PUT','/parallel/bridges/'+id+'/mark'],
                 unmark:['DELETE','/parallel/bridges/'+id+'/mark']};
  const step=actions[action];if(!step)return;
  await api(step[1],{method:step[0]});
  toast({decline:'已谢绝邀请',cancel:'已撤回邀请',close:'跨馆会合已结束',mark:'已自行标记探索',unmark:'已取消探索标记'}[action]);
  await refresh();
 }catch(err){V.message=err.message||'操作未完成';toast(V.message);await refresh()}
},true);
window.WonderParallel={render,refresh};
})();
