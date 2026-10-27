/* Wonder Atlas V20 — everything lab. Real entries only; private capsules stay sealed. */
(() => {
'use strict';
const L={tab:'surprise',cfg:null,albums:[],scope:'mine',albumId:0,album:null,
  capsules:[],stamps:[],domain:'全部',kind:'all',pick:null,results:[],query:'',
  notice:'',error:''};
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
const logged=()=>Boolean(window.S?.user);
const btn=(action,label,attr='')=>'<button type="button" data-lab="'+action+'" '+attr+'>'+label+'</button>';
const uid=v=>Number(v||0);
const intro=v=>esc(String(v||'没有额外介绍').slice(0,180));
const choices=(values,selected)=>values.map(v=>'<option '+(selected===v?'selected':'')+'>'+esc(v)+'</option>').join('');
async function load(){
 L.error='';
 try{
  if(!L.cfg)L.cfg=await api('/lab/config');
  if(L.tab==='albums'){
   if(!logged())L.scope='public';
   L.albums=(await api('/lab/albums?scope='+L.scope)).items;
   if(!L.albums.some(x=>x.id===L.albumId))L.albumId=L.albums[0]?.id||0;
   L.album=L.albumId?await api('/lab/albums/'+L.albumId):null;
  }
  if(L.tab==='capsules')L.capsules=logged()?(await api('/lab/capsules')).items:[];
  if(L.tab==='passport')L.stamps=logged()?(await api('/lab/stamps')).items:[];
 }catch(e){L.error=e.message||'无法读取万物实验室';}
}
function header(){
 return '<div class="wl-hero"><div class="wl-eyebrow">WONDER ATLAS · V20 · THE EVERYTHING LAB</div>'+
 '<h1>世界万象，<br><em>皆可入馆。</em></h1><p>一件化石、一张照片、一段代码、一个奇怪的想法，甚至一整个原创文明。发现、收藏、编排，留下属于你的万物故事。</p>'+
 '<div class="wl-hero-note">✦ REAL DISCOVERY × FICTIONAL WORLDS × PERSONAL ARCHIVES</div></div>';
}
function tabs(){
 return '<div class="wl-tabs" role="tablist" aria-label="万物实验室">'+
 [['surprise','🎁 每日奇遇'],['albums','📚 万物图鉴'],['capsules','⏳ 时光胶囊'],['passport','🏅 奇遇护照']].map(([k,label])=>
 btn('tab',label,'data-tab="'+k+'" role="tab" aria-selected="'+(L.tab===k)+'" class="'+(L.tab===k?'active':'')+'"')).join('')+'</div>';
}
function source(item,extra=''){
 const fictional=!!item.fictional;
 return '<article class="wl-object"><div class="wl-object-top"><span>'+(fictional?'◇ 原创虚构':'◈ 现实／社区投稿')+'</span><small>'+esc(item.category||item.domain||'万物')+'</small></div>'+
 '<div class="wl-glyph" aria-hidden="true">'+(fictional?'✧':'✺')+'</div>'+
 '<h3>'+esc(item.title)+'</h3><p>'+intro(item.description)+'</p><small>'+esc(item.provenance||'来源待核验')+
 ' · '+esc(item.creator||'未知馆长')+'</small><div class="wl-actions">'+extra+
 (item.kind==='exhibit'?btn('exhibit','打开档案 ↗','data-id="'+uid(item.id)+'"'):btn('fantasy','探索原创世界 ↗'))+'</div></article>';
}
function surprise(){
 return '<div class="wl-grid-two"><section class="wl-panel"><div class="wl-eyebrow">01 / WHAT WILL YOU FIND TODAY?</div>'+
 '<h2>🎁 今日万物盲盒</h2><p>从真正公开的藏品与原创世界中选取，所有用户在同一天、同一主题看到同一候选结果。没有真实来源就不编造。</p>'+
 '<div class="wl-form-row"><label>探索领域<select id="wl-domain">'+choices(L.cfg.domains,L.domain)+'</select></label>'+
 '<label>发现类型<select id="wl-kind">'+[['all','万物皆可'],['exhibit','现实藏品／社区发现'],['world','原创虚构世界']].map(([v,t])=>
 '<option value="'+v+'" '+(L.kind===v?'selected':'')+'>'+t+'</option>').join('')+'</select></label></div>'+
 btn('surprise','✦ 打开今日盲盒','class="wl-primary"')+
 '<p class="wl-small">日期采用服务器 UTC。选择其他领域可以探索更多种类；这不是随机编造的内容。</p></section>'+
 '<section class="wl-panel"><div class="wl-eyebrow">OBJECT OF THE DAY</div><h2>今天的发现</h2>'+
 (L.pick===null?'<div class="wl-empty"><b>✧</b><p>世界正在等你打开。</p></div>':
 L.pick.item?source(L.pick.item,(logged()?btn('stamp','🏅 收藏今日奇遇印章'):'<small>登录后可以收藏奇遇印章</small>')):
 '<div class="wl-empty"><b>◇</b><p>这类公开藏品暂时空缺。欢迎成为第一位发现者。</p></div>')+
 '</section></div>';
}
function albums(){
 const a=L.album,owner=!!a?.is_owner;
 return '<section class="wl-panel"><div class="wl-sectionhead"><div><div class="wl-eyebrow">02 / MAKE YOUR OWN ENCYCLOPEDIA</div>'+
 '<h2>📚 万物图鉴</h2><p>让完全不同的发现产生策展关系。现实藏品与虚构设定始终分别标记。</p></div>'+
 '<div class="wl-segments">'+(logged()?btn('scope','我的图鉴','data-scope="mine" class="'+(L.scope==='mine'?'active':'')+'"'):'')+
 btn('scope','公开图鉴','data-scope="public" class="'+(L.scope==='public'?'active':'')+'"')+'</div></div>'+
 (logged()&&L.scope==='mine'?'<form id="wl-album-form" class="wl-create"><label>新图鉴主题<input name="title" maxlength="70" minlength="2" required placeholder="从恐龙到深空探测器"></label>'+
 '<label>风格<select name="style">'+choices(L.cfg.styles,L.cfg.styles[0])+'</select></label>'+
 '<label class="wl-wide">给访客的故事<textarea name="description" maxlength="500" rows="2" placeholder="为什么将这些东西放在一起？"></textarea></label>'+
 '<button class="wl-primary" type="submit" '+(L.albums.length>=12?'disabled':'')+'>＋ 创建图鉴</button></form>':'')+
 '<div class="wl-album-picks">'+(L.albums.length?L.albums.map(x=>btn('album','<b>'+esc(x.title)+'</b><small>'+esc(x.style)+' · '+(x.visibility==='public'?'公开':'私密')+'</small>',
 'data-id="'+x.id+'" class="'+(x.id===L.albumId?'active':'')+'"')).join(''):
 '<div class="wl-empty">还没有真实创建的图鉴，欢迎创建第一册。</div>')+'</div></section>'+
 (a?'<section class="wl-panel"><div class="wl-sectionhead"><div class="wl-eyebrow">'+esc(a.style)+' · '+(a.visibility==='public'?'PUBLIC':'PRIVATE')+'</div>'+
 '<h2>'+esc(a.title)+'</h2><p>'+intro(a.description)+'</p><small>馆长：'+esc(a.creator)+' · 可访问的展品 '+a.items.length+' 件</small></div>'+
 (owner?'<div class="wl-actions">'+btn('publish',a.visibility==='public'?'撤回公开':'✦ 公开图鉴',
 'data-next="'+(a.visibility==='public'?'private':'public')+'"')+btn('delete-album','删除本图鉴')+'</div>':'')+
 '<div class="wl-object-grid">'+(a.items.length?a.items.map(x=>source(x,owner?btn('remove','移出图鉴','data-id="'+x.entry_id+'"'):'')).join(''):
 '<div class="wl-empty">这册图鉴还没有可展示的事物。</div>')+'</div>'+
 (owner?'<div class="wl-search"><h3>🔎 给图鉴增加万物</h3><form id="wl-search-form" class="wl-form-row">'+
 '<label>选择来源<select name="kind"><option value="exhibit">社区藏品</option><option value="world">原创世界</option></select></label>'+
 '<label>按名称搜索<input name="query" maxlength="80" value="'+esc(L.query)+'" placeholder="化石、热梗、机器人……"></label>'+
 '<button type="submit">搜索</button></form><div class="wl-object-grid">'+
 (L.results.length?L.results.map(x=>source(x,btn('add','＋ 加入图鉴','data-id="'+x.id+'" data-kind="'+x.kind+'"'))).join(''):
 '<p class="wl-small">搜索仅返回已有真实来源或由真实用户创建的虚构世界。</p>')+'</div></div>':'')+
 '</section>':'');
}
function capsules(){
 return '<div class="wl-grid-two"><section class="wl-panel"><div class="wl-eyebrow">03 / PRIVATE TIME CAPSULE</div>'+
 '<h2>⏳ 写给未来的自己</h2><p>把今天的故事封进未来。开启日期到来前，接口不会向浏览器返回正文。只允许本人访问。</p>'+
 (logged()?'<form id="wl-capsule-form" class="wl-create"><label>信件标题<input name="title" maxlength="70" minlength="2" required placeholder="给几年后的自己"></label>'+
 '<label>开启日期（UTC）<input name="unlock_date" type="date" required min="'+esc(L.cfg.today_utc)+'"></label>'+
 '<label class="wl-wide">要封存的文字<textarea name="body" minlength="20" maxlength="1800" rows="7" required placeholder="今天，我在世界里发现了……"></textarea></label>'+
 '<button type="submit" class="wl-primary">封存这段时光</button></form>':
 '<div class="wl-empty">登录后可以创建私人时光胶囊。</div>')+
 '<p class="wl-small">最多 30 封，日期需在未来十年内。重要内容建议另存备份。</p></section>'+
 '<section class="wl-panel"><div class="wl-eyebrow">MEMORIES IN TIME</div><h2>📜 私人时间收藏柜</h2>'+
 (!logged()?'<div class="wl-empty">只有本人能够查看。</div>':
 L.capsules.length?'<div class="wl-capsule-list">'+L.capsules.map(x=>
 '<article><div><small>'+esc(x.unlock_date)+'</small><h3>'+(x.sealed?'🔒 ':'✉ ')+esc(x.title)+'</h3>'+
 (x.sealed?'<p>封存中，开启后方能阅读。</p>':'<p class="wl-letter">'+esc(x.body)+'</p>')+'</div>'+
 btn('delete-capsule','删除','data-id="'+x.id+'"')+'</article>').join('')+'</div>':
 '<div class="wl-empty">还没有时光胶囊。</div>')+'</section></div>';
}
function passport(){
 return '<section class="wl-panel"><div class="wl-eyebrow">04 / COLLECTION OF DISCOVERIES</div>'+
 '<h2>🏅 奇遇护照</h2><p>每天只有自己主动点击，才可以记录一枚当天的发现印章。失去公开授权的藏品会被隐藏。</p>'+
 (!logged()?'<div class="wl-empty">登录后，在万物盲盒里收集第一枚印章。</div>':
 L.stamps.length?'<div class="wl-stamp-grid">'+L.stamps.map(x=>
 '<article><b>✺</b><strong>'+esc(x.date_utc)+'</strong><small>'+esc(x.domain)+'</small>'+
 '<p>'+esc(x.item?.title||'该来源已撤回公开')+'</p></article>').join('')+'</div>':
 '<div class="wl-empty">你的护照暂时还是空白。</div>')+
 btn('tab','🎁 去探索今日万物','data-tab="surprise" class="wl-primary"')+'</section>';
}
async function render(){
 await load();
 return '<div class="wl-root">'+header()+tabs()+
 (L.notice?'<div class="wl-notice">'+esc(L.notice)+'</div>':'')+
 (L.error?'<div class="wl-error">'+esc(L.error)+'</div>':'')+
 (L.tab==='surprise'?surprise():L.tab==='albums'?albums():L.tab==='capsules'?capsules():passport())+
 '<footer class="wl-small">真实社区投稿未经独立事实核验 · 虚构作品明确标记 · 撤回后不再公开来源</footer></div>';
}
async function refresh(){if(window.S?.view==='lab'){document.querySelector('#main').innerHTML=await render();}}
async function search(kind){
 const query=L.query.toLowerCase();
 if(kind==='world'){
  const [pub,mine]=await Promise.all([api('/fantasy/worlds'),api('/fantasy/worlds?scope=mine')]);
  const seen=new Set();
  L.results=[...(mine.items||[]),...(pub.items||[])].filter(x=>{if(seen.has(x.id))return false;seen.add(x.id);return !query||x.name.toLowerCase().includes(query);})
   .slice(0,18).map(x=>({id:x.id,kind:'world',title:x.name,description:x.intro,category:x.theme,
    creator:x.creator,provenance:'原创虚构世界',fictional:true}));
 }else{
  const [mine,pub]=await Promise.all([api('/my/exhibits'),api('/feed?q='+encodeURIComponent(L.query)+'&page=1')]);
  const seen=new Set();
  L.results=[...(mine||[]),...(pub.items||[])].filter(x=>{if(seen.has(x.id))return false;seen.add(x.id);
   return !query||(x.title||'').toLowerCase().includes(query)||(x.description||'').toLowerCase().includes(query);})
   .slice(0,18).map(x=>({id:x.id,kind:'exhibit',title:x.title,description:x.description,
   category:x.category,creator:x.owner,fictional:x.category==='世界观设定',
   provenance:x.category==='世界观设定'?'虚构世界奇物':'社区投稿／未独立核验'}));
 }
}
document.addEventListener('click',async e=>{
 const b=e.target.closest('[data-lab]');if(!b)return;
 e.preventDefault();e.stopImmediatePropagation();
 const k=b.dataset.lab,id=uid(b.dataset.id);
 try{
  if(k==='tab'){L.tab=b.dataset.tab;L.notice='';if(L.tab==='albums'&&logged())L.scope='mine';await refresh();}
  else if(k==='scope'){L.scope=b.dataset.scope;L.albumId=0;L.results=[];await refresh();}
  else if(k==='album'){L.albumId=id;L.results=[];await refresh();}
  else if(k==='surprise'){
   L.domain=document.querySelector('#wl-domain')?.value||'全部';
   L.kind=document.querySelector('#wl-kind')?.value||'all';
   L.pick=await api('/lab/surprise?domain='+encodeURIComponent(L.domain)+'&kind='+L.kind);await refresh();
  }
  else if(k==='stamp'){await api('/lab/stamps?domain='+encodeURIComponent(L.domain)+'&kind='+L.kind,{method:'POST'});
   L.notice='🏅 今日奇遇印章已收入护照';L.tab='passport';await refresh();}
  else if(k==='publish'){await api('/lab/albums/'+L.albumId+'/visibility',
    {method:'PATCH',body:{visibility:b.dataset.next}});L.notice='图鉴公开状态已更新';await refresh();}
  else if(k==='delete-album'){if(!confirm('删除这册图鉴？原始藏品不会被删除。'))return;
   await api('/lab/albums/'+L.albumId,{method:'DELETE'});L.albumId=0;L.notice='图鉴已删除';await refresh();}
  else if(k==='remove'){await api('/lab/albums/'+L.albumId+'/entries/'+id,{method:'DELETE'});
   L.notice='已移出图鉴';await refresh();}
  else if(k==='add'){await api('/lab/albums/'+L.albumId+'/entries',
    {method:'POST',body:{kind:b.dataset.kind,source_id:id}});L.notice='已收入图鉴';await refresh();}
  else if(k==='delete-capsule'){if(!confirm('永久删除这枚时光胶囊？'))return;
    await api('/lab/capsules/'+id,{method:'DELETE'});L.notice='已删除';await refresh();}
  else if(k==='exhibit'){if(typeof openDetail==='function')await openDetail(id);}
  else if(k==='fantasy'){await navigate('fantasy');}
 }catch(err){if(typeof toast==='function')toast(err.message||'操作未完成');}
},true);
document.addEventListener('submit',async e=>{
 if(!['wl-album-form','wl-capsule-form','wl-search-form'].includes(e.target.id))return;
 e.preventDefault();e.stopImmediatePropagation();
 const form=e.target,body=Object.fromEntries(new FormData(form));
 try{
  if(form.id==='wl-album-form'){const r=await api('/lab/albums',{method:'POST',body});
   L.albumId=r.id;L.notice='第一册万物图鉴已经诞生';}
  else if(form.id==='wl-capsule-form'){await api('/lab/capsules',{method:'POST',body});
   L.notice='时光已经封存，未来见';}
  else {L.query=(body.query||'').trim();await search(body.kind);}
  await refresh();
 }catch(err){if(typeof toast==='function')toast(err.message||'操作失败');}
},true);
window.WonderLab={render};
})();