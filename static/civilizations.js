/* V34 · Civilization engine — user-authored history, deterministic toy simulator. */
(() => {
'use strict';
const T={focus:0,notice:'',compareTurn:1,comparePolicy:'research',compareActive:false};
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const btn=(a,text,attributes='')=>'<button type="button" data-civ="'+a+'" '+attributes+'>'+text+'</button>';
const logged=()=>Boolean(window.S?.user);
const colors={knowledge:'#91c8f4',supplies:'#eec789',ecology:'#8ee2bf',cohesion:'#e7a5cb',culture:'#beaff5'};
function statBars(values,model){
 return '<div class="cv-stats">'+model.stats.map(s=>'<div class="cv-stat"><div class="cv-stat-label"><span>'+esc(s.label)+'</span><b>'+Number(values[s.key]||0)+'/100</b></div>'+
 '<div class="cv-meter"><i style="width:'+Math.min(100,Math.max(0,Number(values[s.key]||0)))+'%;background:'+colors[s.key]+'"></i></div></div>').join('')+'</div>';
}
function source(x){
 return '<div class="cv-source">'+(x?.image_url?'<img loading="lazy" alt="" src="'+esc(x.image_url)+'">':'<span>✦</span>')+
 '<div><b>'+esc(x?.title||'原始来源已不可用')+'</b><small>@'+esc(x?.curator||'未知')+' · '+esc(x?.domain||'')+'</small></div>'+
 (x?btn('source','↗','data-id="'+x.id+'" title="查看原始公开馆藏"'):'')+'</div>';
}
function worldCard(x){return '<div class="cv-world-card"><b>🪐 '+esc(x.title)+'</b><small>V33 世界 #'+x.id+' · '+esc(x.law)+' · '+x.civilization_count+'/6 文明</small>'+
 '<div>'+x.sources.map(source).join('')+'</div></div>'}
function history(d,model){
 return '<div class="cv-history"><h3>⏳ 不可重来的历史抉择</h3>'+
 (d.turns.length?d.turns.map(t=>'<article class="cv-chapter"><div class="cv-chapter-index">'+
 '<span>ERA '+String(t.turn).padStart(2,'0')+'</span><b>'+esc(t.policy_label)+'</b></div>'+
 '<h4>'+esc(t.chapter)+'</h4><p>'+esc(t.narrative)+'</p><div class="cv-chapter-footer">'+
 '<span>'+esc(t.event)+'</span><small>'+Object.entries(t.delta).map(([k,n])=>(n>=0?'+':'')+n+' '+esc(model.stats.find(s=>s.key===k)?.label||k)).join(' · ')+'</small></div></article>').join(''):
 '<div class="cv-empty">文明尚无历史决策；原作者可以编写第一轮。</div>')+'</div>';
}
function editPanel(d,model){
 if(!logged()||window.S.user.username!==d.owner)return '';
 return '<section class="cv-author"><div class="cv-author-header"><h3>✍️ 文明创世者控制台</h3>'+
 '<p>每一轮选择都由透明固定规则计算。只有你编写的事件故事属于你的原创文明历史。</p></div>'+
 '<div class="cv-toolrow">'+
 (d.status==='public'?btn('unpublish','暂停公开','class="cv-muted"'):btn('publish','✦ 审核并公开文明','class="cv-primary" '+(d.turns.length<2?'disabled':'')))+
 (d.turns.length?btn('undo','↶ 撤回最后一轮（下架并重审）','class="cv-muted"'):'')+
 btn('delete','删除我的文明','class="cv-danger"')+'</div>'+
 '<form id="cvEditForm" class="cv-form"><h4>📝 修订文明宣言</h4>'+
 '<label>文明名称<input name="name" required minlength="3" maxlength="80" value="'+esc(d.name)+'"></label>'+
 '<label>文明宣言<textarea name="charter" required minlength="20" maxlength="580">'+esc(d.charter)+'</textarea></label>'+
 '<button class="cv-muted" type="submit">✓ 保存新宣言并回到私密草稿</button></form>'+
 (d.turns.length<8?'<form id="cvTurnForm" class="cv-form"><h4>⚡ 时代抉择 · 第 '+(d.turns.length+1)+' 轮</h4>'+
 '<label>选择一项文明政策<select name="policy">'+model.policies.map(x=>'<option value="'+x.id+'">'+esc(x.label)+' · '+esc(x.caption)+'</option>').join('')+'</select></label>'+
 '<label>原创篇章名称<input name="chapter" minlength="3" maxlength="90" required placeholder="例如：第一座图书馆与饥荒的代价"></label>'+
 '<label>写下发生在你的虚构文明里的事件<textarea name="narrative" minlength="12" maxlength="620" required placeholder="由你讲述本轮发展、冲突、人物和历史；数值仅按照游戏规则变化。"></textarea></label>'+
 '<button class="cv-primary">＋ 提交一次重大文明抉择</button></form>':
 '<div class="cv-empty">已经走过八轮关键抉择。你可以公开或撤销最后一轮改写历史。</div>')+
 '</section>';
}
function experiment(d,model,result){
 if(!d.turns.length)return '';
 const turns=d.turns.map(x=>'<option value="'+x.turn+'" '+(T.compareTurn===x.turn?'selected':'')+'>'+
 '第 '+x.turn+' 轮 · '+esc(x.policy_label)+'</option>').join('');
 return '<section class="cv-counter"><div class="cv-overline">03 / BRANCHING HISTORY MICROSCOPE</div>'+
 '<h3>🔬 如果历史在那一刻改写？</h3>'+
 '<p>选择文明史上一个真实记录过的决策轮次，然后替换为另一项规则。后面的历史决策保持不变，计算差异不会修改原文明。</p>'+
 '<form id="cvCompareForm" class="cv-compare-form"><label>历史分岔点<select name="turn">'+turns+'</select></label>'+
 '<label>假设当时选择了……<select name="policy">'+model.policies.map(x=>'<option value="'+x.id+'" '+(T.comparePolicy===x.id?'selected':'')+'>'+esc(x.label)+'</option>').join('')+'</select></label>'+
 '<button class="cv-primary">⚡ 演算另一个未来</button></form>'+
 (result?'<div class="cv-compare-grid"><article><div class="cv-overline">ACTUAL HISTORY</div><h4>馆长原来的决定</h4>'+
 statBars(result.actual_final,model)+'</article><article><div class="cv-overline">ALTERNATE FUTURE</div>'+
 '<h4>假设当时改了决策</h4>'+statBars(result.alternative_final,model)+'</article></div>'+
 '<div class="cv-difference"><b>两条文明最终指标相差：</b>'+
 model.stats.map(s=>'<span>'+esc(s.label)+'：'+(result.difference[s.key]>0?'+':'')+result.difference[s.key]+'</span>').join('')+'</div>'+
 '<div class="cv-alternative-list">'+result.alternative_history.map(t=>'<div>'+
 '<b>第'+t.turn+'轮 · '+esc(t.policy_label)+'</b><span>'+esc(t.event)+'</span></div>').join('')+'</div>'+
 '<p class="cv-disclaimer">'+esc(result.notice)+'</p>':'')+'</section>';
}
function showroom(d,model,result){
 return '<section class="cv-panel cv-show"><div class="cv-overline">02 / CIVILIZATION #'+d.id+
 ' · MODEL '+d.model_version+'</div><div class="cv-show-heading"><div><h2>'+esc(d.name)+'</h2>'+
 '<p>来自 @'+esc(d.owner)+' 的架空世界 · '+(d.status==='public'?'◉ 作者已公开':'○ 仅作者可见')+'</p></div>'+
 '<div class="cv-age">文明纪元<strong>'+d.turns.length+' / 8</strong></div></div>'+
 '<div class="cv-charter">✧ '+esc(d.charter)+'</div>'+
 '<div class="cv-sources"><div><small>宇宙起源</small><b>'+esc(d.world_title)+'</b>'+
 btn('world','↗ 回到 V33 碰撞世界','data-id="'+d.world_id+'" class="cv-muted"')+'</div>'+
 '<div><small>文明种子</small>'+source(d.seed)+'</div></div>'+
 '<div class="cv-stats-shell"><div class="cv-overline">CIVILIZATION STATE · MODEL 1</div>'+
 '<h3>五维虚构文明状态</h3>'+statBars(d.final,model)+'</div>'+
 history(d,model)+experiment(d,model,result)+editPanel(d,model)+'</section>';
}
async function render(){
 let gallery,model,mine={items:[]},worlds={items:[]};
 try{[gallery,model]=await Promise.all([api('/civilizations'),api('/civilizations/policies')]);
 if(logged())[mine,worlds]=await Promise.all([api('/civilizations/mine'),api('/civilizations/worlds')]);}
 catch(e){return '<section class="cv-root cv-panel"><h2>文明演化实验室暂不可用</h2><p>'+esc(e.message)+'</p></section>';}
 const all=[...mine.items,...gallery.items];
 if(!T.focus)T.focus=all.find(x=>x.available)?.id||0;
 let current=null,result=null;
 if(T.focus){
  try{current=await api('/civilizations/'+T.focus)}
  catch(e){T.focus=0;T.compareActive=false;T.notice='旧文明已经私密或其原始来源已撤回。';}
 }
 if(current&&current.turns.length){
  T.compareTurn=Math.max(1,Math.min(current.turns.length,T.compareTurn));
  if(T.compareActive){
   try{result=await api('/civilizations/'+T.focus+'/counterfactual?turn='+T.compareTurn+
       '&policy='+encodeURIComponent(T.comparePolicy))}
   catch(e){T.compareActive=false;T.notice='历史分支当前无法对照，请重新选择。';}
  }
 }
 return '<div class="cv-root"><section class="cv-hero"><div class="cv-planet"></div>'+
 '<div class="cv-overline">WONDER ATLAS · WORLD 34 · CIVILIZATION LABORATORY</div>'+
 '<h1>一件藏品，<br><em>能创造多少种文明？</em></h1>'+
 '<p>让 V33 的一个公开碰撞世界孕育最多六个文明。你写下八个时代的抉择；游客再用「历史分岔显微镜」观察：如果曾经作出另一种选择，最终结局会有多大不同？</p>'+
 '<div class="cv-hero-pills"><span>🏛 文明创造</span><span>🌱 物件种子</span><span>⏳ 八轮历史</span><span>🔬 反事实显微镜</span><span>⚖️ 透明模拟规则</span></div></section>'+
 (T.notice?'<p class="cv-alert">'+esc(T.notice)+'</p>':'')+
 '<section class="cv-panel"><div class="cv-overline">01 / PUBLIC CIVILIZATION GALLERY</div><h2>🌍 真实作者公开的虚构文明</h2>'+
 '<p>只显示可追溯到当前仍公开的 V33 世界和真实公开藏品的创作；没有内容时不制造“热门文明”。</p>'+
 (gallery.items.length?'<div class="cv-cards">'+gallery.items.map(x=>'<article><div class="cv-overline">WORLD '+x.world_id+
 ' · '+esc(x.world_law)+'</div><h3>'+esc(x.name)+'</h3><small>✍️ @'+esc(x.owner)+' · 已完成 '+x.turn_count+' 轮</small>'+
 btn('select','◈ 进入文明年轮','data-id="'+x.id+'" class="cv-primary"')+'</article>').join('')+'</div>':
 '<div class="cv-empty">目前还没有真实用户公开的文明。你可以在自己的 V33 碰撞世界中开启第一部虚构编年史。</div>')+'</section>'+
 (current?showroom(current,model,result):
 '<section class="cv-panel cv-empty">选择一座已经公开的文明，或在下面创建属于自己的文明实验。</section>')+
 '<section class="cv-panel"><div class="cv-overline">04 / MY CIVILIZATION STUDIO</div><h2>✍️ 新文明的创世图纸</h2>'+
 (logged()?'<p>只有 V33 世界的原作者，才能在自己当下公开的碰撞世界里创建文明。每个世界最多六个文明，每个文明最多八轮历史。</p>'+
 (worlds.items.length?'<form id="cvCreateForm" class="cv-form"><label>选择来源与种子（必须出自本人已发布 V33 世界）'+
 '<select name="origin">'+worlds.items.flatMap(w=>w.remaining>0?w.sources.map(s=>'<option value="'+w.id+':'+s.id+'">'+
 esc(w.title)+' · 文明种子：'+esc(s.title)+'</option>'):[]).join('')+'</select></label>'+
 '<label>文明名称<input name="name" required minlength="3" maxlength="80" placeholder="例如：钟声与米线之国"></label>'+
 '<label>文明宣言（至少20字）<textarea name="charter" required minlength="20" maxlength="580" placeholder="在这个虚构世界，文明从哪里来？最重要的信念是什么？"></textarea></label>'+
 '<button class="cv-primary">＋ 开辟一座私人文明</button></form>'+
 '<div class="cv-worlds">'+worlds.items.map(worldCard).join('')+'</div>':
 '<div class="cv-empty">还没有可用的本人公开 V33 碰撞世界。先去「万物碰撞机」选择两件公开藏品并发表一个原创世界，才能让文明诞生。</div>')+
 btn('goto-collision','⚗️ 前往万物碰撞机','class="cv-muted"')+
 '<h3 class="cv-mine-title">我的文明档案</h3>'+
 (mine.items.length?'<div class="cv-personal">'+mine.items.map(x=>'<div>'+
 btn('select',esc(x.name)+' · '+(x.available?(x.status==='public'?'已公开':'私密草稿'):'🔒 来源已撤回'),
 'data-id="'+x.id+'" class="cv-muted"')+
 (!x.available?btn('delete-id','删除不可用文明','data-id="'+x.id+'" class="cv-danger"'):'')+'</div>').join('')+'</div>':
 '<div class="cv-empty">你尚未创造文明。</div>')+
 '</section>':
 '<div class="cv-empty">登录后可以创造属于你的文明、逐轮记录历史。游客无需登录也可阅读公开文明和演算反事实。</div>'+
 btn('login','登录 / 注册','class="cv-primary"')+'</section>')+
 '<p class="cv-disclaimer">⚖️ 本模块的数值与世界法则都是有限、固定、公开的玩具游戏规则，并非科学化社会模拟、现实政策建议或历史预测。所有情节由真实用户撰写；原始作品及世界撤回后整个公开文明立即不可访问。</p></div>';
}
async function refresh(){if(window.S?.view==='civilizations'){const main=document.querySelector('#main');if(main)main.innerHTML=await render();}}
document.addEventListener('submit',async e=>{
 const f=e.target;if(!['cvCreateForm','cvTurnForm','cvCompareForm','cvEditForm'].includes(f.id))return;
 e.preventDefault();e.stopImmediatePropagation();
 const d=Object.fromEntries(new FormData(f).entries()),submit=f.querySelector('[type=submit],button');
 if(submit)submit.disabled=true;
 try{
  if(f.id==='cvCompareForm'){
   T.compareTurn=Number(d.turn);T.comparePolicy=d.policy;T.compareActive=true;
  }else if(f.id==='cvEditForm'){
   await api('/civilizations/'+T.focus,{method:'PUT',body:{name:d.name,charter:d.charter}});
   T.compareActive=false;T.notice='文明名称与宣言已保存为新私密草稿，需要你重新主动公开。';
  }else if(f.id==='cvCreateForm'){
   const ids=(d.origin||'').split(':').map(Number);
   if(ids.length!==2||ids.some(x=>!Number.isInteger(x)||x<1))throw Error('请先创建并公开属于你自己的 V33 世界');
   const r=await api('/civilizations',{method:'POST',body:{
    world_id:ids[0],seed_exhibit_id:ids[1],name:d.name,charter:d.charter}});
   T.focus=r.id;T.compareActive=false;T.notice='一座新的私密文明已经诞生！请先写两轮历史后主动公开。';
  }else{
   const r=await api('/civilizations/'+T.focus+'/turns',{method:'POST',body:{
    policy:d.policy,chapter:d.chapter,narrative:d.narrative}});
   T.compareActive=false;T.notice='✨ 文明进入第 '+r.turn+' 轮。数值由明确的游戏规则计算；最新版本已经自动转为私密草稿。';
  }
  await refresh();
 }catch(err){T.notice=err.message||'无法完成';toast(T.notice);await refresh();}
 finally{if(submit)submit.disabled=false;}
},true);
document.addEventListener('click',async e=>{
 const x=e.target.closest('[data-civ]');if(!x)return;
 e.preventDefault();e.stopImmediatePropagation();
 const command=x.dataset.civ,id=Number(x.dataset.id||0);
 try{
  if(command==='login'){document.querySelector('#loginTop')?.click();return;}
  if(command==='source'){await openDetail(id);return;}
  if(command==='goto-collision'){await navigate('collision');return;}
  if(command==='world'){window.WonderCollision?.open(id);await navigate('collision');return;}
  if(command==='select'){T.focus=id;T.notice='';T.compareActive=false;T.compareTurn=1;await refresh();
   document.querySelector('.cv-show')?.scrollIntoView({behavior:'smooth',block:'start'});return;}
  if(['undo','unpublish','delete','delete-id'].includes(command)&&!confirm({
   undo:'撤回文明最新一轮历史？公开文明将先下架，作者需要重新发布。',
   unpublish:'将当前文明恢复为私密，暂时不允许游客查看？',
   delete:'永久删除自己写下的文明和全部虚构历史？原始 V33 世界不会删除。',
   'delete-id':'删除这座已经失去原始来源的个人文明？'
  }[command]))return;
  const civId=command==='delete-id'?id:T.focus;
  const commands={
   publish:['POST','/civilizations/'+civId+'/publish'],
   unpublish:['POST','/civilizations/'+civId+'/unpublish'],
   undo:['DELETE','/civilizations/'+civId+'/turns/latest'],
   delete:['DELETE','/civilizations/'+civId],
   'delete-id':['DELETE','/civilizations/'+civId],
  };
  const operation=commands[command];if(!operation)return;
  await api(operation[1],{method:operation[0]});
  if(command==='delete'||command==='delete-id')T.focus=0;
  T.compareActive=false;
  T.notice={publish:'✦ 文明编年史已公开，当前合法来源可供游客参观。',
   unpublish:'文明已恢复私密草稿。',undo:'已撤回最后一个时代；重新公开前仅作者能查看。',
   delete:'文明已删除。','delete-id':'原始来源失效的文明已删除。'}[command];
  await refresh();
 }catch(err){T.notice=err.message||'操作暂未完成';toast(T.notice);await refresh();}
},true);
window.WonderCivilizations={render,refresh,open(id){T.focus=Number(id)||0;T.compareActive=false}};
})();