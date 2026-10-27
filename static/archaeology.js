/* V37 · Museum Archaeology — public origins, curator-authored fiction, layered excavation. */
(() => {
'use strict';
const A={focus:0,civ:0,source:0,query:'',role:'memory',era:1,edit:0,notice:'',layers:{},detailRevision:0,echoes:null};
const h=x=>String(x??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const btn=(cmd,text,opts='')=>'<button type="button" data-arch="'+cmd+'" '+opts+'>'+text+'</button>';
const user=()=>Boolean(window.S?.user);
const names=['','🔍 第一层 · 表层痕迹','📜 第二层 · 深层碑文','🪐 第三层 · 馆长最终假说'];
const mark={sacred:'✧',tool:'⚒',warning:'⚡',currency:'◈',memory:'⏳',mystery:'?'};
function object(c){
 if(!c)return '<div class="ar-object ar-blank">等待选择一件真实公开的原始藏品</div>';
 return '<div class="ar-object">'+(c.image_url?'<img src="'+h(c.image_url)+'" alt="" loading="lazy">':'<span class="ar-object-glyph">✧</span>')+
 '<div><strong>'+h(c.title)+'</strong><small>真实原藏品 #'+c.id+' · @'+h(c.curator)+' · '+h(c.domain)+'</small></div></div>';
}
function card(r){
 return '<article class="ar-card"><div class="ar-overline">CHRONICLE · #'+r.id+' · 第 '+r.era+' 纪元</div>'+
 '<div class="ar-symbol">'+(mark[r.role]||'✧')+'</div><h3>'+h(r.title)+'</h3>'+
 '<p>'+h(r.introduction)+'</p>'+
 '<div class="ar-metas"><span>'+h(r.role_label)+'</span><span>♜ '+h(r.civilization.name)+'</span></div>'+
 '<div class="ar-true-object">'+object(r.exhibit)+'</div>'+
 btn('view','⚒ 进入考古现场','data-id="'+r.id+'" class="ar-gold"')+'</article>';
}
function exhibitExplorer(r){
 if(!r.available)return '<section class="ar-panel ar-redact" id="arDetail"><h2>🔒 这处考古遗址已封闭</h2><p>原藏品或架空文明已更改。旧故事文本、图像与真实展品名称不会继续公开。</p>'+
 (user()?btn('rebase','↻ 作者重新核验当前来源','data-id="'+r.id+'" class="ar-gold"'):'')+'</section>';
 let layerContent='';
 if(r.status==='public'){
  const visible=A.layers[r.id]||{},max=Math.max(...Object.keys(visible).map(Number),0);
  layerContent='<div class="ar-layerboard">'+[1,2,3].map(n=>'<article class="'+(visible[n]?'is-open':'')+'"><div class="ar-layer-label">'+names[n]+'</div>'+
  (visible[n]?'<div class="ar-layer-text">'+h(visible[n].content)+'</div>':
   '<div class="ar-layer-hidden">未开启的想象考古卷轴 ✧</div>')+
  btn('unearth',visible[n]?'✓ 再读这一层':'⛏ 发掘第 '+n+' 层',
     'data-layer="'+n+'" data-id="'+r.id+'" class="ar-outline" '+(n>max+1?'disabled':'') )+
  '</article>').join('')+'</div>';
 }else if(r.my_role||r.surface){
  layerContent='<div class="ar-layerboard">'+[1,2,3].map((n,i)=>
   '<article><div class="ar-layer-label">'+names[n]+'</div><div class="ar-layer-text">'+h(r[['surface','inscription','interpretation'][i]]||'')+'</div></article>').join('')+'</div>';
 }
 return '<section class="ar-panel" id="arDetail"><div class="ar-overline">03 / EXCAVATION SITE #'+r.id+'</div>'+
 '<div class="ar-detail-head"><div><h2>🏺 '+h(r.title)+'</h2><p>虚构纪元 '+r.era+' · '+h(r.role_label)+' · 解释作者 @'+h(r.author)+'</p></div>'+
 '<div class="ar-actions">'+(r.surface?btn('edit','✎ 修订我的考古记录','data-id="'+r.id+'" class="ar-outline"'):'')+
 (r.surface&&r.status!=='closed'?btn(r.status==='public'?'retract':'publish',r.status==='public'?'🔒 撤回公开':'✦ 主动公开档案',
 'data-id="'+r.id+'" class="ar-gold"'):'')+
 (r.surface?btn('close','结束存档','data-id="'+r.id+'" class="ar-danger"'):'')+'</div></div>'+
 '<div class="ar-context">'+object(r.exhibit)+'<div><div class="ar-overline">FICTIONAL CIVILIZATION</div>'+
 '<strong>'+h(r.civilization.name)+'</strong><small>时代：第 '+r.era+' 纪元</small></div></div>'+
 '<blockquote class="ar-intro">'+h(r.introduction)+'</blockquote>'+
 '<div class="ar-layer-title"><div class="ar-overline">THREE LAYERS OF IMAGINED ARCHAEOLOGY</div><h3>一点一点，挖出同一件物品的另一种命运</h3>'+
 '<p>发掘顺序是探索游戏体验，不是内容加密。层次中的考古叙事只是馆长虚构故事。</p></div>'+
 layerContent+
 '<div class="ar-explore-actions">'+btn('echoes','🌌 进入同一藏品的平行误读图谱','data-id="'+r.exhibit.id+'" class="ar-gold"')+
 btn('original','↗ 看真实原始藏品','data-id="'+r.exhibit.id+'" class="ar-outline"')+'</div>'+
 '<p class="ar-ethics">'+h(r.notice||'这只是原创虚构解释，并非真实历史资料。')+'</p></section>';
}
function studio(civs,objects,roles,editItem){
 const possible=civs||[],current=possible.find(c=>c.id===A.civ)||possible[0];
 const options=objects||[];
 const src=options.find(s=>s.id===A.source)||null;
 const ed=editItem?.surface?editItem:null;
 return '<section class="ar-panel" id="arStudio"><div class="ar-overline">04 / CURATOR ARCHAEOLOGY STUDIO</div>'+
 '<h2>✍️ 我来编写一段异世界考古史</h2>'+
 '<p>先在 V34「文明演化实验室」公开自己创造的文明，再选一件目前确实公开的原始馆藏，写出它在这个架空世界里的三层不同意义。</p>'+
 (!user()?'<div class="ar-empty">登录后即可创建原创考古档案。游客可阅读全部当前公开档案，但无法冒充馆长。</div>':
 (!possible.length?'<div class="ar-empty">还没有你本人创建且目前合法公开的 V34 文明。请先从真实藏品开始建造自己的文明并公开至少两轮历史。</div>'+
 btn('goto-civ','🏛️ 去万物文明演化实验室','class="ar-outline"'):
 '<form id="arSearch" class="ar-search"><input name="q" value="'+h(A.query)+'" placeholder="搜索真实藏品：标题、标签、分类"><button type="submit">搜寻原物</button></form>'+
 '<div class="ar-picker">'+options.map(x=>'<button type="button" data-arch="pick" data-id="'+x.id+'" class="'+(A.source===x.id?'active':'')+'">'+
 object(x)+'</button>').join('')+(options.length?'':'<div class="ar-empty">没有匹配的公开原始藏品，请换一个关键词。</div>')+'</div>'+
 '<div class="ar-picked">'+object(src)+'</div>'+
 (ed?'<div class="ar-edit-note">正在修改 #'+ed.id+' 原创考古档案。更改文字会撤回旧公开，进度重置。不能换源文明和原物。</div>':'')+
 '<form id="arForm"><div class="ar-form-columns"><label>我创建的已公开文明<select name="civilization_id" required '+(ed?'disabled':'')+'>'+
 possible.map(x=>'<option value="'+x.id+'" '+((ed?.civilization?.id||A.civ)===x.id?'selected':'')+'>'+h(x.name)+' · '+x.turn_count+'轮历史</option>').join('')+'</select></label>'+
 '<label>故事发生在第几个虚构历史轮次<select name="era" required>'+Array.from({length:current?.turn_count||2},(_,i)=>'<option value="'+(i+1)+'" '+((ed?.era||A.era)===i+1?'selected':'')+'>第 '+(i+1)+' 纪元</option>').join('')+'</select></label></div>'+
 '<label>该文明如何理解这件真实物品？<select name="role">'+(roles||[]).map(x=>'<option value="'+h(x.id)+'" '+((ed?.role||A.role)===x.id?'selected':'')+'>'+h(x.label)+'</option>').join('')+'</select></label>'+
 '<label>考古档案名称<input name="title" required minlength="3" maxlength="90" value="'+h(ed?.title||'')+'" placeholder="例如：千年后，一片芯片被奉为月亮"></label>'+
 '<label>遗址引子（18—520字）<textarea name="introduction" required minlength="18" maxlength="520" placeholder="在这个虚构文明的第几纪元，考古者为何遇见它？">'+h(ed?.introduction||'')+'</textarea></label>'+
 '<label>🔍 第一层 · 表层痕迹<textarea name="surface" required minlength="15" maxlength="520" placeholder="游客先看到什么奇怪的痕迹？">'+h(ed?.surface||'')+'</textarea></label>'+
 '<label>📜 第二层 · 深层碑文<textarea name="inscription" required minlength="20" maxlength="720" placeholder="发掘之后，古代居民写下了怎样的说法？">'+h(ed?.inscription||'')+'</textarea></label>'+
 '<label>🪐 第三层 · 馆长最终假说<textarea name="interpretation" required minlength="30" maxlength="1100" placeholder="为什么同一个物件，会在这个虚构文明里被误解成完全不同的东西？">'+h(ed?.interpretation||'')+'</textarea></label>'+
 '<div class="ar-actions"><button class="ar-gold" type="submit" '+(!ed&&!src?'disabled':'')+'>'+(ed?'✎ 保存新私密版本':'＋ 创建私密考古草稿')+'</button>'+
 (ed?btn('clear-edit','取消编辑','class="ar-outline"'):'')+'</div></form>'))+
 '</section>';
}
function echoesPane(data){
 if(!data)return '';
 return '<section class="ar-panel" id="arEchoes"><div class="ar-overline">05 / PARALLEL INTERPRETATION MAP</div>'+
 '<h2>🌌 同一件物品，几种文明解释？</h2>'+object(data.exhibit)+
 '<p>当前由 '+data.items.length+' 座有效、主动公开的考古档案解释此物件，涉及 '+data.unique_roles+
 ' 种不同的游戏身份。数字只统计真实作者创作的作品，不代表学术分歧或历史真相。</p>'+
 (data.items.length?'<div class="ar-echo-grid">'+data.items.map(x=>'<article><div class="ar-overline">♜ '+h(x.civilization.name)+'</div>'+
 '<h3>'+h(x.title)+'</h3><span>'+h(x.role_label)+'</span><p>'+h(x.introduction)+'</p>'+
 btn('view','⛏ 查看这套文明解释','data-id="'+x.id+'" class="ar-outline"')+'</article>').join('')+'</div>':
 '<div class="ar-empty">这件公开原物目前还没有任何馆长亲笔创作的有效考古解释。</div>')+
 '</section>';
}
async function render(){
 let gallery,civs={items:[]},sources={items:[]},roles={items:[]},mine={items:[]};
 try{
  [gallery,roles,sources]=await Promise.all([api('/archaeology/public'),api('/archaeology/roles'),api('/archaeology/sources?q='+encodeURIComponent(A.query))]);
  if(user())[civs,mine]=await Promise.all([api('/archaeology/civilizations'),api('/archaeology/mine')]);
 }catch(e){return '<div class="ar-root ar-panel"><h2>文明考古局暂时不可访问</h2><p>'+h(e.message)+'</p></div>'}
 if(!A.civ)A.civ=civs.items?.[0]?.id||0;
 if(!A.source)A.source=sources.items?.[0]?.id||0;
 if(!A.focus)A.focus=(mine.items||[])[0]?.id||(gallery.items||[])[0]?.id||0;
 let record=null,editRecord=null;
 if(A.focus){
  try{record=await api('/archaeology/'+A.focus);
   if(A.detailRevision!==record.revision||record.id!==A.lastRecord||!record.available){
    A.layers={};A.detailRevision=record.revision||0;A.lastRecord=record.id;
   }
  }catch(e){A.focus=0;A.layers={};A.notice='原始来源或考古档案已撤回公开，旧叙事已从页面移除。'}
 }
 if(A.edit){
  if(record?.id===A.edit)editRecord=record;
  else try{editRecord=await api('/archaeology/'+A.edit)}catch(e){A.edit=0;}
  if(editRecord?.civilization?.id)A.civ=editRecord.civilization.id;
 }
 if(A.echoes){
  try{A.echoes=await api('/archaeology/exhibit/'+A.echoes.exhibit.id+'/echoes')}
  catch(e){A.echoes=null;A.notice='该原始藏品已不再公开，同源解释图谱已隐藏。'}
 }
 const list=gallery.items||[];
 return '<div class="ar-root"><section class="ar-hero"><div class="ar-ring"></div>'+
 '<div class="ar-overline">WONDER ATLAS · WORLD 37 · ARCHAEOLOGY OF IMPOSSIBLE CIVILIZATIONS</div>'+
 '<h1>一件真实的物品，<br><em>千万种不可能的历史。</em></h1>'+
 '<p>将一件真实公开的藏品放入自己创建的虚构文明中，亲笔写下一段三层考古谜题，再让游客发掘并比较不同文明的解释。</p>'+
 '<div class="ar-tags"><span>⛏ 三层线索发掘</span><span>🏺 架空遗迹档案</span><span>🌌 同源误读图谱</span><span>🧭 文明年代定位</span><span>🔒 实时来源保护</span></div></section>'+
 (A.notice?'<p class="ar-alert">'+h(A.notice)+'</p>':'')+
 '<section class="ar-panel"><div class="ar-overline">01 / PUBLIC CURATED FICTION</div><h2>🏺 万界考古遗址大厅</h2>'+
 '<p>只陈列由真实馆长自主发布、原始展品和所有上游文明来源仍可公开的架空考古故事。</p>'+
 (list.length?'<div class="ar-grid">'+list.map(card).join('')+'</div>':
 '<div class="ar-empty">万物尚未留下任何公开的平行文明考古记录。成为第一位创造遗迹故事的馆长吧！</div>')+'</section>'+
 (record?exhibitExplorer(record):'')+
 (user()?'<section class="ar-panel"><div class="ar-overline">02 / MY IMAGINARY RELICS</div><h2>我的文明考古档案</h2>'+
 ((mine.items||[]).length?'<div class="ar-my">'+mine.items.map(x=>btn('view','#'+x.id+' · '+h(x.title)+' · '+(x.available?x.status:'来源不可用'),
 'data-id="'+x.id+'" class="ar-outline"')).join('')+'</div>':'<div class="ar-empty">还没有你的原创考古档案。</div>')+'</section>':'')+
 studio(civs.items||[],sources.items||[],roles.items||[],editRecord)+echoesPane(A.echoes)+
 '<footer class="ar-fine">⚖️ “考古”是游戏叙事形式，不是考古学认证、真实出土、官方展览或原始藏品作者的认可。三层线索都由真实馆长亲笔创作；真实原物仍属于原作者。</footer></div>';
}
async function refresh(){if(window.S?.view==='archaeology'){const main=document.querySelector('#main');if(main)main.innerHTML=await render();}}
document.addEventListener('submit',async e=>{
 const f=e.target;if(!['arSearch','arForm'].includes(f.id))return;
 e.preventDefault();e.stopImmediatePropagation();
 const d=Object.fromEntries(new FormData(f).entries()),b=f.querySelector('button[type=submit]');
 if(b)b.disabled=true;
 try{
  if(f.id==='arSearch'){A.query=String(d.q||'').trim();A.source=0;await refresh();return;}
  let data={civilization_id:A.edit?A.civ:Number(d.civilization_id),
   exhibit_id:A.edit?A.source:Number(A.source),era:Number(d.era),role:d.role,
   title:d.title,introduction:d.introduction,surface:d.surface,inscription:d.inscription,interpretation:d.interpretation};
  const endpoint=A.edit?'/archaeology/'+A.edit:'/archaeology';
  const result=await api(endpoint,{method:A.edit?'PUT':'POST',body:data});
  A.focus=A.edit||result.id;A.edit=0;A.layers={};A.notice='新档案已保存为私密草稿。请确认来源后由你本人主动公开。';
  await refresh();
 }catch(err){A.notice=err.message||'本次操作失败';toast(A.notice);await refresh();}
 finally{if(b)b.disabled=false;}
},true);
document.addEventListener('click',async e=>{
 const el=e.target.closest('[data-arch]');if(!el)return;
 e.preventDefault();e.stopImmediatePropagation();
 const cmd=el.dataset.arch,id=Number(el.dataset.id||0);
 try{
  if(cmd==='goto-civ'){await navigate('civilizations');return;}
  if(cmd==='original'){await openDetail(id);return;}
  if(cmd==='pick'){A.source=id;A.edit=0;A.notice='已选择真实公开的原物，写下它在虚构文明中的另一重历史。';await refresh();return;}
  if(cmd==='view'){A.focus=id;A.layers={};A.edit=0;A.detailRevision=0;A.echoes=null;A.notice='';await refresh();
   document.querySelector('#arDetail')?.scrollIntoView({behavior:'smooth',block:'start'});return;}
  if(cmd==='echoes'){
   A.echoes=await api('/archaeology/exhibit/'+id+'/echoes');await refresh();
   document.querySelector('#arEchoes')?.scrollIntoView({behavior:'smooth',block:'start'});return;}
  if(cmd==='unearth'){
   const layer=Number(el.dataset.layer);
   const response=await api('/archaeology/'+id+'/layer/'+layer);
   A.layers[id]={...(A.layers[id]||{}),[layer]:response};
   A.notice='第 '+layer+' 层真实作者的虚构考古叙事已展开。';
   await refresh();document.querySelector('#arDetail')?.scrollIntoView({behavior:'smooth',block:'start'});return;}
  if(cmd==='edit'){let d=await api('/archaeology/'+id);if(!d.available)throw Error('请先恢复当前原始来源');
   A.edit=id;A.civ=d.civilization.id;A.source=d.exhibit.id;A.focus=id;await refresh();
   document.querySelector('#arStudio')?.scrollIntoView({behavior:'smooth',block:'start'});return;}
  if(cmd==='clear-edit'){A.edit=0;await refresh();return;}
  if(['close','retract'].includes(cmd)&&!confirm(cmd==='close'?'封存这件原创考古档案？原藏品与文明不会删除。':'撤回公开并重置该版本的游客挖掘进度？'))return;
  if(!['publish','retract','rebase','close'].includes(cmd))return;
  const result=await api('/archaeology/'+id+'/'+cmd,{method:'POST'});
  A.notice=result.notice||'完成作者的当前操作';A.layers={};await refresh();
 }catch(err){A.notice=err.message||'当前内容不可用';toast(A.notice);await refresh();}
},true);
window.WonderArchaeology={render,refresh,open(id){A.focus=Number(id)||0}};
})();