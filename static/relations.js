/* Wonder Atlas V19: opt-in relations and fictional civilization network. */
(() => {
 'use strict';
 const R={scope:'mine',directory:[],public:[],mine:[],config:null,notice:'',error:''};
 const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
 const logged=()=>Boolean(window.S?.user);
 const button=(kind,label,extra='')=>'<button type="button" data-relation="'+kind+'" '+extra+'>'+label+'</button>';
 async function read(){
   R.error='';
   try{
     if(!R.config)R.config=await api('/fantasy/relations/config');
     const [directory,pub,mine]=await Promise.all([
       api('/fantasy/relations/civilizations'),api('/fantasy/relations'),
       logged()?api('/fantasy/relations?scope=mine'):Promise.resolve({items:[]})
     ]);
     R.directory=directory.items||[];R.public=pub.items||[];R.mine=mine.items||[];
   }catch(err){R.error=err.message||'文明关系无法加载';}
 }
 function own(){return R.directory.filter(c=>c.mine);}
 function choices(){
   const sources=own();const targets=R.directory.filter(c=>!c.mine);
   if(!logged())return '<div class="rl-empty">登录并公开自己的文明后，可以向真实的其他馆长发送交流邀请。</div>';
   if(!sources.length)return '<div class="rl-empty">你还没有公开的文明。先到「万界会盟」创建文明并公开。</div>';
   if(!targets.length)return '<div class="rl-empty">还没有其他真实馆长公开文明。这里只显示真实账号，不使用虚构玩家。</div>';
   return '<form id="rl-invite" class="rl-form"><div class="rl-field"><label>派遣使团的文明<select name="source_id">'+
     sources.map(x=>'<option value="'+x.id+'">'+esc(x.name)+' · '+esc(x.world)+'</option>').join('')+'</select></label>'+
     '<label>希望交流的文明<select name="target_id">'+targets.map(x=>'<option value="'+x.id+'">'+esc(x.name)+' · '+esc(x.creator)+'</option>').join('')+'</select></label></div>'+
     '<label>交流形式<select name="kind">'+R.config.kinds.map(x=>'<option>'+esc(x.name)+'</option>').join('')+'</select></label>'+
     '<label>交流意向<textarea name="message" minlength="8" maxlength="350" rows="3" required placeholder="希望与你的文明探讨古代星图与机械之术……"></textarea></label>'+
     '<button type="submit">✉ 发出文明交流邀请</button><p>对方接受后，双方才能在自己未来的纪年中主动选用交流效果。</p></form>';
 }
 function card(r){
   return '<article class="rl-relation"><div class="rl-pills"><span class="rl-state '+esc(r.status)+'">'+
     esc(({pending:'等待对方同意',accepted:'已经建立联系',declined:'邀请已拒绝',withdrawn:'交流已终止'})[r.status]||r.status)+'</span>'+
     '<small>✧ '+esc(r.kind)+'</small></div><h4>'+esc(r.source_name)+' <em>⟷</em> '+esc(r.target_name)+'</h4>'+
     (r.message?'<p>'+esc(r.message)+'</p>':'<p>有一方撤回了公开授权，关联信息已经隐藏。</p>')+
     (r.active?'<small class="rl-active">✓ 可由馆长自主选择应用于下一年</small>':'')+
     '<div class="rl-operations">'+
       (r.can_accept?button('decision','✓ 同意结盟','data-id="'+r.id+'" data-action="accept"'):'')+
       (r.can_decline?button('decision','拒绝','data-id="'+r.id+'" data-action="decline"'):'')+
       (r.can_withdraw?button('decision','撤回关系','data-id="'+r.id+'" data-action="withdraw"'):'')+
     '</div></article>';
 }
 function network(){
   const active=R.public.filter(r=>r.active && r.source_id && r.target_id).slice(0,18);
   if(!active.length)return '<div class="rl-empty">尚无经双方确认且持续公开的文明交流。第一条星际航路仍等待建立。</div>';
   const ids=[...new Set(active.flatMap(r=>[r.source_id,r.target_id]))].slice(0,14);
   const names=new Map();
   active.forEach(r=>{names.set(r.source_id,r.source_name);names.set(r.target_id,r.target_name);});
   const pos=new Map(ids.map((id,i)=>{const a=2*Math.PI*i/ids.length-Math.PI/2;
     return [id,{x:490+365*Math.cos(a),y:225+162*Math.sin(a)}];}));
   const edge=active.filter(r=>pos.has(r.source_id)&&pos.has(r.target_id)).map(r=>{
     const a=pos.get(r.source_id),b=pos.get(r.target_id);
     return '<line x1="'+a.x+'" y1="'+a.y+'" x2="'+b.x+'" y2="'+b.y+
       '" stroke="#e5c18e" stroke-width="2.5" opacity=".5"><title>'+esc(r.kind)+'</title></line>';
   }).join('');
   const points=ids.map(id=>{const p=pos.get(id);
     return '<g><circle cx="'+p.x+'" cy="'+p.y+'" r="25" fill="#293c56" stroke="#e5c18e" stroke-width="2"/>'+
       '<text x="'+p.x+'" y="'+(p.y+5)+'" font-size="20" text-anchor="middle" fill="#e7c98e">✦</text>'+
       '<text x="'+p.x+'" y="'+(p.y+48)+'" font-size="13" fill="#f0dfc1" text-anchor="middle">'+esc(names.get(id).slice(0,9))+'</text></g>';
   }).join('');
   return '<div class="rl-chart"><svg viewBox="0 0 980 470" role="img" aria-label="公开的文明交流连接图">'+edge+points+'</svg></div>';
 }
 async function render(){
   await read();
   return '<section class="rl-root"><div class="rl-header"><div><span class="rl-kicker">V19 / CONSENSUAL CIVILIZATION NETWORK</span>'+
     '<h3>🌌 文明关系网</h3><p>让不同馆长的文明产生联系。邀请需要本人发起，对方明确同意；双方原有世界与历史不被改写。</p></div>'+
     '<div class="rl-count"><b>'+R.public.filter(x=>x.active).length+'</b><small>条公开文明联结</small></div></div>'+
     (R.notice?'<div class="rl-note">'+esc(R.notice)+'</div>':'')+
     (R.error?'<div class="rl-error">'+esc(R.error)+'</div>':'')+
     '<div class="rl-subsection"><h4>✨ 已公开的星际关系图</h4>'+network()+'</div>'+
     '<div class="rl-two"><div class="rl-subsection"><h4>🤝 建立新的文明联系</h4>'+choices()+'</div>'+
     '<div class="rl-subsection"><h4>💎 四种联动方式</h4><div class="rl-effects">'+
     (R.config?.kinds||[]).map(x=>'<div><b>'+esc(x.name)+'</b><span>'+Object.entries(x.effects)
      .map(([key,val])=>esc(({knowledge:'学识',energy:'能量',culture:'文化',stability:'秩序',
      food:'粮储',ecology:'生态'})[key])+(val>0?' +':' ')+val).join(' · ')+'</span></div>').join('')+
     '</div><p class="rl-help">影响仅在馆长主动选择应用于下一年时生效；不会替另一方推进历史、转移财产或修改天律。</p></div></div>'+
     '<div class="rl-subsection"><h4>📨 我的交流往来</h4>'+
       (logged()?(R.mine.length?'<div class="rl-list">'+R.mine.map(card).join('')+'</div>':
          '<div class="rl-empty">还没有邀请或会盟。</div>'):'<div class="rl-empty">登录后可管理自己的邀请。</div>')+
     '</div><p class="rl-help">任何一方关闭世界或文明，双方交流即永久撤回，重新公开不会自动恢复；已发生的虚构年历只保留匿名化的交流类型。</p></section>';
 }
 async function refresh(){if(window.S?.view==='fantasy')document.querySelector('#main').innerHTML=await WonderFantasy.render();}
 document.addEventListener('click',async ev=>{
   const b=ev.target.closest('[data-relation]');if(!b)return;
   ev.preventDefault();ev.stopImmediatePropagation();
   try{
     if(b.dataset.relation==='decision'){
       if(b.dataset.action==='withdraw'&&!window.confirm('确认撤回？后续模拟无法继续使用这段文明关系。'))return;
       await api('/fantasy/relations/'+Number(b.dataset.id),{method:'PATCH',body:{action:b.dataset.action}});
       R.notice='双方关系状态已更新，公开内容与后续交流权限将同步变化。';
       await refresh();
     }
   }catch(err){if(typeof toast==='function')toast(err.message||'操作失败');}
 },true);
 document.addEventListener('submit',async ev=>{
   if(ev.target.id!=='rl-invite')return;
   ev.preventDefault();ev.stopImmediatePropagation();
   const body=Object.fromEntries(new FormData(ev.target));body.source_id=Number(body.source_id);body.target_id=Number(body.target_id);
   try{await api('/fantasy/relations',{method:'POST',body});
     R.notice='邀请已发送，只有受邀馆长主动同意才会正式建立联系。';await refresh();
   }catch(err){if(typeof toast==='function')toast(err.message||'无法发送邀请');}
 },true);
 window.WonderRelations={render};
})();
