/* V35 · 万界文明大使馆 · collaborative fiction with two real curators. */
(() => {
'use strict';
const E={focus:0,note:'',edit:false,openLetter:false};
const esc=x=>String(x??'').replace(/[&<>"']/g,k=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[k]));
const btn=(act,label,attrs='')=>'<button type="button" data-emb="'+act+'" '+attrs+'>'+label+'</button>';
const logged=()=>Boolean(window.S?.user);
function civ(c,side){
 return '<article class="eb-civ"><div class="eb-overline">CIVILIZATION '+side+'</div>'+
 '<div class="eb-civ-glyph">'+(side==='A'?'◈':'✧')+'</div>'+
 '<h3>'+esc(c?.name||'源文明暂不可用')+'</h3>'+
 '<p>'+esc(c?.world_name||'已关闭或来源撤回')+'</p>'+
 '<small>馆长 @'+esc(c?.owner||'未知')+' · '+Number(c?.turns||0)+' 个历史时代</small>'+
 (c?.id?btn('goto-civ','浏览原始文明 ↗','data-id="'+c.id+'" class="eb-quiet"'):'')+'</article>';
}
function letter(l,n){
 return '<article class="eb-letter"><div class="eb-letter-head"><span>LETTER '+String(n).padStart(2,'0')+'</span>'+
 '<b>✍ @'+esc(l.curator)+'</b></div><h4>'+esc(l.subject)+'</h4>'+
 '<p>'+esc(l.message)+'</p><div class="eb-letter-bottom"><small>'+esc(l.created_at)+'</small>'+
 (l.is_mine?btn('remove-letter','撤回我写的信','data-id="'+l.id+'" class="eb-danger"'):'')+'</div></article>';
}
function myControls(d){
 if(!d.is_member)return '';
 let controls='';
 if(d.state==='pending')controls=d.my_role==='b'?
 btn('accept','✓ 接受外交邀请','class="eb-gold" '+(!d.available?'disabled':''))+btn('decline','婉拒邀请','class="eb-danger"'):
 btn('cancel','撤回邀请','class="eb-quiet"');
 if(d.state==='accepted'||d.state==='public'){
  const myApprove=d.approved?.[d.my_role];
  controls='<div class="eb-votes">'+
 '<div class="'+(d.approved.a?'yes':'')+'">'+(d.approved.a?'✔':'○')+' '+esc(d.curators[0])+' 同意</div>'+
 '<div class="'+(d.approved.b?'yes':'')+'">'+(d.approved.b?'✔':'○')+' '+esc(d.curators[1])+' 同意</div></div>'+
 '<div class="eb-actions">'+
 (d.available?btn('approve',myApprove?'✓ 当前版本已批准':'✓ 我批准当前共同版本',
 'class="eb-gold" '+(myApprove?'disabled':'')):'')+
 btn('retract','撤销共同公开批准','class="eb-quiet"')+
 btn('toggle-letter',E.openLetter?'收起信函':'✍️ 亲笔写一封外交信','class="eb-quiet"')+
 btn('toggle-edit',E.edit?'收起标题修改':'编辑共同标题','class="eb-quiet"')+
 btn('refresh-sources','↻ 重新核验两个文明','class="eb-quiet"')+
 btn('close','结束本次会盟','class="eb-danger"')+'</div>'+
 '<p class="eb-instruction">任何人添加或撤回自己的信函，都会使整个外交纪事回到私密状态；两人必须重新同意最新版本。</p>'+
 (E.openLetter?'<form id="ebLetterForm" class="eb-form"><label>外交书信主题<input name="subject" maxlength="80" minlength="3" required placeholder="例如：来自机械国度的第一封信"></label>'+
 '<label>以自己的名义书写外交纪事<textarea name="message" maxlength="820" minlength="20" required placeholder="写下本国文明的观点，不能冒充另一位馆长。"></textarea></label>'+
 '<button class="eb-gold" type="submit">✉️ 作为真实馆长发送原创信函</button></form>':'')+
 (E.edit?'<form id="ebEditForm" class="eb-form"><label>会盟标题<input name="title" maxlength="80" minlength="3" value="'+esc(d.title)+'" required></label>'+
 '<label>两国相遇的舞台前言<textarea name="preface" maxlength="440" minlength="15" required>'+esc(d.preface)+'</textarea></label>'+
 '<button class="eb-gold" type="submit">保存新版本并撤销旧批准</button></form>':'');
 }else if(d.state!=='pending'){
  controls='<p class="eb-finished">此外交邀请已'+(d.state==='declined'?'被拒绝':'结束')+'。原始文明仍然保留。</p>';
 }
 return '<section class="eb-author"><div class="eb-overline">CURATOR STUDIO / 双馆真实外交工作台</div>'+
 '<h3>🏛️ 我们的外交协议 · 第 '+d.revision+' 版</h3>'+
 (!d.available?'<p class="eb-warning">⚠️ 原始文明已变化或撤回，当前公开内容隐藏。你们可以在双方文明重新合法公开后，执行「重新核验」，再共同审批。</p>':'')+
 controls+'</section>';
}
function showroom(d){
 return '<section class="eb-panel eb-show"><div class="eb-overline">04 / DIPLOMACY RECORD · #'+d.id+'</div>'+
 '<div class="eb-show-header"><div><h2>'+esc(d.title)+'</h2>'+
 '<p>'+esc(d.preface||'源文明已暂时撤回，历史故事被遮蔽。')+'</p></div>'+
 '<span class="eb-state '+(d.state==='public'&&d.available?'public':'')+'">'+
 (d.state==='public'&&d.available?'◉ 公开联合外交':d.state==='pending'?'⌛ 等待对方同意':d.state==='accepted'?'✧ 双方共同策展中':'○ 不再公开')+
 '</span></div>'+
 (d.available?'<div class="eb-civs">'+civ(d.a,'A')+'<div class="eb-bridge">🤝<span>联结两个世界</span></div>'+civ(d.b,'B')+'</div>'+
 '<div class="eb-scroll"><div class="eb-overline">ORIGINAL LETTERS · '+d.letters.length+' / 12</div><h3>📜 双国历史书信</h3>'+
 (d.letters.length?d.letters.map((l,i)=>letter(l,i+1)).join(''):
 '<div class="eb-empty">仍然没有外交书信。双方馆长各亲自写下至少一封信后，才能共同发布。</div>')+'</div>':
 '<div class="eb-hidden">🔒 任一真实文明或原始来源已经不可用。联合前言、书信与源作品标题已动态遮蔽。</div>')+
 myControls(d)+
 '<p class="eb-disclaimer">'+esc(d.notice)+'</p></section>';
}
function invitationList(items){
 if(!items.length)return '<div class="eb-empty">暂无合作邀请。你可以成为第一位文明外交使者！</div>';
 return '<div class="eb-invitations">'+items.map(x=>btn('select',
 '<strong>'+esc(x.title)+'</strong><small>'+esc(x.curators.join(' × '))+' · '+(x.state==='pending'?'⌛ 待同意':x.state==='public'&&x.available?'◎ 已公开':x.state==='accepted'?'联合编写中':x.state==='declined'?'已拒绝':'已关闭')+
 (!x.available?' · 🔒 来源已变化':'')+'</small>',
 'data-id="'+x.id+'" class="'+(x.id===E.focus?'active':'')+'"')).join('')+'</div>';
}
async function render(){
 let publicData,my={items:[],my_civilizations:[],other_civilizations:[]};
 try{publicData=await api('/embassies/public');
  if(logged())my=await api('/embassies/mine');
 }catch(err){return '<div class="eb-root"><h2>文明大使馆暂时不可用</h2><p>'+esc(err.message)+'</p></div>'}
 const myItems=my.items||[],pubItems=publicData.items||[];
 if(!E.focus)E.focus=myItems[0]?.id||pubItems[0]?.id||0;
 let detail=null;
 if(E.focus){
  try{detail=await api('/embassies/'+E.focus)}
  catch(err){E.focus=0;E.note='这座大使馆不再公开或来源已撤回。';}
 }
 return '<div class="eb-root"><section class="eb-hero"><div class="eb-orbits"></div>'+
 '<div class="eb-overline">WONDER ATLAS · WORLD 35 · CIVILIZATION EMBASSIES</div>'+
 '<h1>让两个文明相遇，<br><em>让两位真实馆长共同书写历史。</em></h1>'+
 '<p>不是机器人替他们谈判。这里的每次邀请、每封书信、每个公开许可，都由两位文明创作者亲自决定。</p>'+
 '<div class="eb-tags"><span>🤝 双向外交许可</span><span>✉️ 亲笔国书</span><span>🏛️ 联合世界纪事</span><span>🔐 版本双重批准</span></div></section>'+
 (E.note?'<div class="eb-notice">'+esc(E.note)+'</div>':'')+
 '<div class="eb-two"><section class="eb-panel"><div class="eb-overline">01 / SEND AN ENVOY</div>'+
 '<h2>✉️ 派出一位真正的文明使者</h2>'+
 (logged()?'<p>只有在自己已经公开的 V34 文明之间才能发出邀请。对方必须是真实存在、不同账户的文明馆长。</p>'+
 (my.my_civilizations.length&&my.other_civilizations.length?
 '<form id="ebInviteForm" class="eb-form"><label>选择我的公开文明<select name="my_civ_id">'+
 my.my_civilizations.map(x=>'<option value="'+x.id+'">'+esc(x.name)+' · @'+esc(x.owner)+'</option>').join('')+'</select></label>'+
 '<label>邀请另一位真实馆长的公开文明<select name="other_civ_id">'+
 my.other_civilizations.map(x=>'<option value="'+x.id+'">'+esc(x.name)+' · @'+esc(x.owner)+'</option>').join('')+'</select></label>'+
 '<label>联合外交纪事名称<input name="title" minlength="3" maxlength="80" required placeholder="例如：青铜王国和机械帝国的第一次会晤"></label>'+
 '<label>馆长 A 的邀请前言<textarea name="preface" minlength="15" maxlength="440" required placeholder="用架空故事介绍两座文明为何相遇。"></textarea></label>'+
 '<button class="eb-gold" type="submit">✉️ 发出私密外交邀请</button></form>':
 '<div class="eb-empty">暂缺两位来自不同真实账户、仍公开且全部来源有效的 V34 文明。可以先建设公开文明，或等待其他馆长创建自己的世界。</div>')+
 btn('goto-civs','🏛️ 前往文明演化实验室','class="eb-quiet"'):
 '<div class="eb-empty">登录后可以选择属于自己的公开 V34 文明发出外交邀请。游客无需登录也能浏览双方已批准的公开纪事。</div>'+
 btn('login','登录 / 注册','class="eb-gold"'))+'</section>'+
 '<section class="eb-panel"><div class="eb-overline">02 / YOUR EMISSARIES</div><h2>📨 我的使馆与来函</h2>'+
 (logged()?invitationList(myItems):'<div class="eb-empty">登录后查看被邀请的文明与共同外交工作台。</div>')+'</section></div>'+
 '<section class="eb-panel"><div class="eb-overline">03 / DIPLOMATIC ARCHIVES</div><h2>🌍 已双方批准的万界外交纪事</h2>'+
 '<p>只有双方创作者各自写过信、都批准同一版本，而且两国原始文明始终仍合法公开，才能被所有游客看到。</p>'+
 (pubItems.length?'<div class="eb-public">'+pubItems.map(x=>btn('select',
 '<strong>✧ '+esc(x.title)+'</strong><small>'+esc(x.curators.join(' × '))+' · '+x.letters+' 封真实馆长原创外交信</small>',
 'data-id="'+x.id+'" class="'+(x.id===E.focus?'active':'')+'"')).join('')+'</div>':
 '<div class="eb-empty">世界外交仍待真正的文明馆长们书写。这里不会虚构已发表的历史、外交官或热门联盟。</div>')+'</section>'+
 (detail?showroom(detail):'<section class="eb-panel eb-empty">选择一座可查看的大使馆，或者亲自创建第一封外交邀请。</section>')+
 '<p class="eb-footer">⚖️ 外交书信与文明世界均属原创虚构故事。系统不代表另一位真实用户发表立场。来自 V33/V34 的原始公开来源发生变化后，相关故事立即停止公共展示。</p></div>';
}
async function refresh(){if(window.S?.view==='embassies'){const main=document.querySelector('#main');if(main)main.innerHTML=await render()}}
document.addEventListener('submit',async e=>{
 const f=e.target;
 if(!['ebInviteForm','ebLetterForm','ebEditForm'].includes(f.id))return;
 e.preventDefault();e.stopImmediatePropagation();
 const d=Object.fromEntries(new FormData(f).entries()),button=f.querySelector('[type=submit],button');
 if(button)button.disabled=true;
 try{
  if(f.id==='ebInviteForm'){
   const r=await api('/embassies',{method:'POST',body:{
    my_civ_id:Number(d.my_civ_id),other_civ_id:Number(d.other_civ_id),
    title:d.title,preface:d.preface}});
   E.focus=r.id;E.note='已向对方真实馆长发出私人邀请。对方同意前不会公开。';
  }else if(f.id==='ebLetterForm'){
   await api('/embassies/'+E.focus+'/letters',{method:'POST',body:{
    subject:d.subject,message:d.message}});
   E.openLetter=false;E.note='原创外交书信已记录。之前的公开许可已全部撤销，需要双方再次确认。';
  }else{
   await api('/embassies/'+E.focus,{method:'PUT',body:{title:d.title,preface:d.preface}});
   E.edit=false;E.note='联合标题已修改。双方旧版批准失效，重新审批后可公开。';
  }
  await refresh();
 }catch(err){E.note=err.message||'操作未完成';toast(E.note);await refresh()}
 finally{if(button)button.disabled=false}
},true);
document.addEventListener('click',async e=>{
 const x=e.target.closest('[data-emb]');if(!x)return;
 e.preventDefault();e.stopImmediatePropagation();
 const action=x.dataset.emb,id=Number(x.dataset.id||0);
 try{
  if(action==='login'){document.querySelector('#loginTop')?.click();return}
  if(action==='goto-civs'){await navigate('civilizations');return}
  if(action==='goto-civ'){window.WonderCivilizations?.open(id);await navigate('civilizations');return}
  if(action==='select'){
   E.focus=id;E.note='';E.edit=false;E.openLetter=false;await refresh();return;
  }
  if(action==='toggle-letter'){E.openLetter=!E.openLetter;await refresh();return}
  if(action==='toggle-edit'){E.edit=!E.edit;await refresh();return}
  if(['decline','cancel','close','retract','remove-letter'].includes(action)){
   const msg={
    decline:'拒绝这位真实馆长的邀请？',
    cancel:'撤回尚待对方同意的私人邀请？',
    close:'结束两位真实馆长的联合使馆？公开纪事将停止展示。',
    retract:'撤销双方现有的联合发布批准，重新进入私人草稿？',
    'remove-letter':'只撤回你自己写的这封书信？全部旧版批准同时撤销。'
   }[action];
   if(!confirm(msg))return;
  }
  const command={
   accept:['POST','/embassies/'+E.focus+'/accept'],
   decline:['POST','/embassies/'+E.focus+'/decline'],
   cancel:['POST','/embassies/'+E.focus+'/cancel'],
   approve:['POST','/embassies/'+E.focus+'/approve'],
   retract:['POST','/embassies/'+E.focus+'/retract'],
   'refresh-sources':['POST','/embassies/'+E.focus+'/refresh'],
   close:['POST','/embassies/'+E.focus+'/close'],
   'remove-letter':['DELETE','/embassies/'+E.focus+'/letters/'+id]
  }[action];
  if(!command)return;
  await api(command[1],{method:command[0]});
  E.note={
   accept:'🤝 真实被邀请的馆长已同意开始外交。现在双方都可以写信。',
   decline:'已拒绝，原始文明不受影响。',
   cancel:'私人邀请已经撤回。',
   approve:'你的批准已记录；只有另一位馆长也批准同一版本才公开。',
   retract:'双方批准均已撤销，公开纪事暂停。',
   'refresh-sources':'已重新核验两个真实文明的当前版本。双方必须重新审批。',
   close:'双向外交已经结束，原始世界不受影响。',
   'remove-letter':'你的外交书信已撤回；所有旧版批准同时失效。'
  }[action];
  await refresh();
 }catch(err){E.note=err.message||'操作失败';toast(E.note);await refresh()}
},true);
window.WonderEmbassies={render,refresh,open(id){E.focus=Number(id)||0}};
})();
