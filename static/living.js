/* V31 · Living Museum: manually curated real-source timeline, watchlist and time comparison. */
(() => {
'use strict';
const M={focus:0,compare:null,left:0,right:0,msg:'',edit:false};
const esc=s=>String(s??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[ch]));
const button=(cmd,label,extra='')=>'<button type="button" data-live="'+cmd+'" '+extra+'>'+label+'</button>';
const icon={observation:'👁',milestone:'🏁',correction:'📝',discovery:'✨'};
const kindLabel={observation:'观察',milestone:'里程碑',correction:'修正记录',discovery:'新发现'};
function entry(e){
 return '<article class="lv-event"><div class="lv-event-rail"><span>'+icon[e.kind]+'</span><i></i></div>'+
 '<div class="lv-event-body"><div class="lv-event-meta"><span>'+esc(e.observed_on)+'</span><b>'+esc(kindLabel[e.kind]||'变化')+'</b></div>'+
 '<h4>'+esc(e.headline)+'</h4><p>'+esc(e.note)+'</p>'+
 (e.source_url?'<a class="lv-source" target="_blank" rel="noopener noreferrer" href="'+esc(e.source_url)+'">↗ 打开馆长提供的原始来源</a>':
 '<span class="lv-no-source">未提供外部来源 · 馆长自述</span>')+
 '<small class="lv-source-note">'+esc(e.source_label||'记录未经平台核验')+'</small></div></article>';
}
function artifact(x,opts={}){
 if(!x)return '<p class="lv-secret">🔒 原始公开藏品已撤回，不展示旧标题。</p>';
 return '<div class="lv-artifact">'+(x.image_url?'<img src="'+esc(x.image_url)+'" loading="lazy" alt="">':'<span class="lv-star">✦</span>')+
 '<div class="lv-artifact-info"><b>'+esc(x.title)+'</b><small>◈ '+esc(x.curator||'原创馆长')+' · '+esc(x.domain)+'</small></div>'+
 button(opts.action||'focus',opts.label||'查看年轮','data-id="'+x.id+'"')+'</div>';
}
function detailPane(d,ownList){
 const x=d.exhibit;
 return '<section class="lv-panel lv-detail"><div class="lv-label">04 / PERSONAL TIME RING</div>'+
 '<div class="lv-heading"><div><h2>✧ '+esc(x.title)+'</h2><p>由 @'+esc(x.curator)+' 持续记录 · '+d.entries.length+' 条有效年轮</p></div>'+
 '<div class="lv-toolkit">'+button('source','原始藏品 ↗','data-id="'+x.id+'" class="lv-quiet"')+
 (window.S?.user?button('watch',d.watching?'♡ 取消关注':'♡ 关注变化','data-id="'+x.id+'" class="lv-outline"'):'')+
 (d.watching&&d.unread?button('seen','✓ 标记本展品已阅','data-id="'+x.id+'" class="lv-outline"'):'')+
 '</div></div>'+
 (d.is_owner?'<div class="lv-author"><div><strong>✍️ 馆长的观察档案</strong><p>为你的藏品追加变化记录。没有外部来源时明确标注自述；不可把未发生的事件记作事实。</p></div>'+
 button('toggle-edit',M.edit?'收起记录':'＋ 记录一条新变化','class="lv-primary"')+'</div>'+
 (M.edit?'<form id="lvRecordForm" class="lv-record-form"><div class="lv-fields">'+
 '<label>变化类型<select name="kind" required><option value="observation">👁 我的观察</option><option value="milestone">🏁 里程碑</option><option value="correction">📝 纠正旧认识</option><option value="discovery">✨ 新发现</option></select></label>'+
 '<label>观察日期（不能选未来）<input type="date" name="observed_on" required max="'+new Date().toISOString().slice(0,10)+'" value="'+new Date().toISOString().slice(0,10)+'"></label></div>'+
 '<label>事件标题<input type="text" name="headline" required minlength="2" maxlength="100" placeholder="例如：公开研究发布了新图谱"></label>'+
 '<label>变化内容<textarea name="note" required minlength="8" maxlength="700" placeholder="这是什么变化？你从哪里观察到？有哪些不确定性？"></textarea></label>'+
 '<label>原始外部来源链接（可空；不自动核验）<input type="url" name="source_url" maxlength="500" placeholder="https://example.org/original-source"></label>'+
 '<button class="lv-primary" type="submit">✦ 保存真实馆长的观察记录</button></form>':'')+'</div>':'')+
 '<div class="lv-timeline"><div class="lv-timeline-top"><span>CHRONICLE / '+d.entries.length+' ENTRIES</span><small>观察日期排列 · 不等于实时同步</small></div>'+
 (d.entries.length?d.entries.map(e=>'<div class="lv-record"><div>'+entry(e)+'</div>'+
 (d.is_owner?button('withdraw','撤回这条记录','data-id="'+e.id+'" class="lv-danger"'):'')+'</div>').join(''):
 '<div class="lv-empty">这件藏品还没有变化记录。第一条变化必须由真正的原作者亲自提交。</div>')+
 '</div></section>';
}
function comparison(data){
 if(!data)return '';
 function pane(d,k){
  return '<section class="lv-compare-col"><div class="lv-label">TIME LINE / '+k+'</div>'+
 '<h3>'+esc(d.exhibit.title)+'</h3><p>@'+esc(d.exhibit.curator)+' · '+d.entries.length+' 条记录</p>'+
 (d.entries.length?d.entries.map(entry).join(''):'<div class="lv-empty">此件藏品尚无公开观察记录。</div>')+'</section>';
 }
 return '<div class="lv-compare-display">'+pane(data.left,'A')+'<div class="lv-compare-axis">≠<span>并列观察</span></div>'+
 pane(data.right,'B')+'</div><p class="lv-notice">'+esc(data.notice)+'</p>';
}
async function render(){
 let feed,pulse;
 try{[feed,pulse]=await Promise.all([api('/living/feed'),api('/living/pulse')]);}
 catch(e){return '<div class="lv-root"><h1>活体博物馆暂时无法加载</h1><p>'+esc(e.message)+'</p></div>'}
 let watches=null,mine=[];
 if(window.S?.user){
  try{[watches,mine]=await Promise.all([api('/living/watchlist'),api('/my/exhibits')])}
  catch(e){M.msg=e.message}
 }
 const museum=mine||[], news=feed.items||[], watchlist=watches?.items||[];
 if(!M.focus)M.focus=museum[0]?.id||watchlist.find(x=>x.available)?.exhibit_id||news[0]?.exhibit.id||0;
 let d=null;
 if(M.focus){try{d=await api('/living/exhibits/'+M.focus)}
 catch(e){M.msg='该藏品已变私密或不存在；请改选其他公开藏品。';M.focus=0;}}
 const choices=[...new Map([
  ...news.map(n=>[n.exhibit.id,n.exhibit]),
  ...watchlist.filter(n=>n.available).map(n=>[n.exhibit_id,n.exhibit])
 ].map(([id,x])=>[id,x])).values()];
 const chosen=(id)=>choices.find(x=>x.id===id);
 const selectOpts=choices.map(x=>'<option value="'+x.id+'">'+esc(x.title)+' · @'+esc(x.curator)+'</option>').join('');
 return '<div class="lv-root"><section class="lv-hero"><div class="lv-circles"></div><div class="lv-label">WONDER ATLAS · WORLD 31 · LIVING MUSEUM</div>'+
 '<h1>万物不是静止的。<br><em>每一次变化，都值得收藏。</em></h1>'+
 '<p>让真正的藏品拥有不断延伸的时间年轮。真实馆长亲自记录、提供来源；游客追踪变化、并列比较两个世界的观察历史。</p>'+
 '<div class="lv-badges"><span>◎ 可追溯观察年轮</span><span>◈ 公开变化观察室</span><span>♡ 站内关注清单</span><span>⇄ 双时空对照</span></div></section>'+
 (M.msg?'<div class="lv-alert">'+esc(M.msg)+'</div>':'')+
 '<section class="lv-stats"><div><strong>'+pulse.recorded_changes_30d+'</strong><span>近30天馆长公开录入变化</span></div>'+
 '<div><strong>'+pulse.active_exhibits_30d+'</strong><span>近30天有记录的公开藏品</span></div>'+
 '<div><strong>'+Number(watches?.unread||0)+'</strong><span>我的站内待阅更新</span></div></section>'+
 '<div class="lv-two-cols"><div><section class="lv-panel"><div class="lv-label">01 / WORLD PULSE</div><h2>🌍 万物脉搏</h2>'+
 '<p>最近 30 天，真实馆长主动记录了什么？这不是自动抓取的新闻数据。</p>'+
 (pulse.domains.length?'<div class="lv-domains">'+pulse.domains.map(x=>'<div><span>'+esc(x.domain)+'</span><meter min="0" max="'+Math.max(...pulse.domains.map(z=>z.count))+'" value="'+x.count+'"></meter><b>'+x.count+'</b></div>').join('')+'</div>':
 '<div class="lv-empty">目前还没有馆长公开记录的变化。没有记录时不生成模拟数据。</div>')+
 '</section><section class="lv-panel"><div class="lv-label">02 / REAL CHANGES</div><h2>✦ 最近发生的记录</h2>'+
 '<p>按馆长提交时间排序，来源可以点击核验。</p>'+
 (news.length?'<div class="lv-news">'+news.map(x=>'<article><div class="lv-news-when">'+esc(x.entry.observed_on)+' · '+esc(kindLabel[x.entry.kind])+'</div>'+
 '<h3>'+esc(x.entry.headline)+'</h3><p>'+esc(x.entry.note.slice(0,190))+'</p>'+
 artifact(x.exhibit)+ '</article>').join('')+'</div>':
 '<div class="lv-empty">暂无公开变化。你可以为自己的藏品记录第一条观察。</div>')+
 '</section></div><div><section class="lv-panel"><div class="lv-label">03 / MY OBSERVATORY</div><h2>♡ 我的观察清单</h2>'+
 (!window.S?.user?'<div class="lv-empty">登录后可以关注公开的活体藏品，查看馆长以后新录入的未读变化。</div>':
 (watchlist.length?'<div class="lv-watchlist">'+watchlist.map(w=>'<div class="lv-watchrow">'+
 (w.available?artifact(w.exhibit,{action:'focus',label:w.unread?'🔔 '+w.unread+' 条新变化':'查看变化'}):
 '<span class="lv-secret">🔒 原始藏品已撤回公开。旧标题不再显示。</span>')+
 button('unwatch','取消关注','data-id="'+w.exhibit_id+'" class="lv-quiet"')+'</div>').join('')+'</div>':
 '<div class="lv-empty">还没有关注任何展品。进入一件真实的公开藏品，点击「关注变化」开始观察。</div>')))+
 '<h3 class="lv-section-sub">我的原始藏品 <span>'+museum.length+'</span></h3>'+
 (museum.length?'<div class="lv-mine">'+museum.map(x=>'<div>'+
 button('focus',esc(x.title)+' '+(x.visibility==='private'?'🔒':''),'data-id="'+x.id+'" class="lv-mine-button"')+'</div>').join('')+'</div>':
 '<div class="lv-empty">发布你的第一件藏品后，就能记录属于它的变化年轮。</div>')+
 '</section><section class="lv-panel"><div class="lv-label">05 / TIME COMPARISON</div><h2>⇄ 双时空观察室</h2>'+
 '<p>选择两件当前公开的藏品并排查看馆长记录。系统不会推断历史因果或自动证明来源真实性。</p>'+
 '<form id="lvCompareForm"><label>左侧公开藏品 ID<input name="left_id" type="number" min="1" required value="'+(M.left||'')+'" placeholder="例如：1"></label>'+
 '<label>右侧公开藏品 ID<input name="right_id" type="number" min="1" required value="'+(M.right||'')+'" placeholder="例如：2"></label>'+
 '<button class="lv-primary" type="submit">✦ 对照真实公开年轮</button></form>'+
 (choices.length?'<p class="lv-tip">可对照的近期藏品：'+choices.slice(0,6).map(x=>'#'+x.id+' '+esc(x.title)).join('、')+'</p>':'')+
 (M.compare?comparison(M.compare):'')+'</section></div></div>'+
 (d?detailPane(d,mine):'<section class="lv-panel lv-empty">请选择一件原始藏品，观察不断延伸的时间年轮。</section>')+
 '<p class="lv-notice">来源链接、观察日期和事件内容均为馆长本人填报，未经平台验证；站内关注仅显示馆长新增记录，不会后台抓取外部网站。撤回来源会立即隐藏公开时间线。</p></div>';
}
async function refresh(){if(window.S?.view==='living'){const root=document.querySelector('#main');if(root)root.innerHTML=await render()}}
document.addEventListener('submit',async e=>{
 if(!['lvRecordForm','lvCompareForm'].includes(e.target.id))return;
 e.preventDefault();e.stopImmediatePropagation();
 const f=e.target, d=Object.fromEntries(new FormData(f).entries()),sub=f.querySelector('[type=submit],button');
 if(sub)sub.disabled=true;
 try{
  if(f.id==='lvCompareForm'){
   M.left=Number(d.left_id);M.right=Number(d.right_id);
   M.compare=await api('/living/compare?left_id='+M.left+'&right_id='+M.right);
  }else{
   await api('/living/exhibits/'+M.focus+'/entries',{method:'POST',
    body:{kind:d.kind,headline:d.headline,note:d.note,observed_on:d.observed_on,source_url:d.source_url||''}});
   M.edit=false;toast('已添加由馆长亲自记录的变化年轮');
  }
  M.msg='';await refresh();
 }catch(err){M.msg=err.message||'暂时无法完成';toast(M.msg);await refresh()}
 finally{if(sub)sub.disabled=false}
},true);
document.addEventListener('click',async e=>{
 const el=e.target.closest('[data-live]');if(!el)return;
 e.preventDefault();e.stopImmediatePropagation();
 const act=el.dataset.live,id=Number(el.dataset.id||0);
 try{
  if(act==='focus'){M.focus=id;M.edit=false;M.msg='';await refresh();return}
  if(act==='source'){await openDetail(id);return}
  if(act==='toggle-edit'){M.edit=!M.edit;await refresh();return}
  if(act==='withdraw'&&!confirm('确认撤回这条由你创建的变化记录？历史关注者将不再看到它。'))return;
  const commands={watch:['POST','/living/exhibits/'+id+'/watch'],
    unwatch:['DELETE','/living/exhibits/'+id+'/watch'],
    seen:['POST','/living/exhibits/'+id+'/seen'],
    withdraw:['POST','/living/entries/'+id+'/withdraw']};
  const command=commands[act];if(!command)return;
  await api(command[1],{method:command[0]});
  toast({watch:'已订阅馆长今后手动提交的新记录',unwatch:'已取消关注',seen:'目前变化已标记为已阅',withdraw:'变化记录已撤回'}[act]);
  M.msg='';await refresh();
 }catch(err){M.msg=err.message||'暂时无法完成';toast(M.msg);await refresh()}
},true);
window.WonderLiving={render,refresh,open(id){M.focus=Number(id)||0}};
})();
