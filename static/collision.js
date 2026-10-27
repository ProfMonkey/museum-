/* V33 · 万物碰撞机 — honest, user-authored, two-source parallel universes. */
(() => {
'use strict';
const C={focus:0,edit:0,remix:0,left:0,right:0,law:'world_merge',search:'',
 preview:null,echoes:null,picked:'',message:''};
const h=x=>String(x??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const act=(name,label,attrs='')=>'<button type="button" data-collision="'+name+'" '+attrs+'>'+label+'</button>';
const yes=()=>Boolean(window.S?.user);
const source=(x,side='')=>x?'<div class="cx-source">'+(x.image_url?'<img alt="" loading="lazy" src="'+h(x.image_url)+'">':'<span class="cx-source-symbol">✦</span>')+
 '<div><strong>'+h(x.title)+'</strong><small>◉ @'+h(x.curator)+' · '+h(x.domain)+'</small></div>'+
 (side?act('pick','选择','data-side="'+side+'" data-id="'+x.id+'"'):'')+'</div>':
 '<div class="cx-source cx-unknown">✧ 还未选中真实藏品</div>';
const galleryCard=w=>'<article class="cx-world-card"><div class="cx-eyebrow">PARALLEL #'+w.id+' · '+h(w.law_title)+'</div>'+
 '<div class="cx-world-pair"><span>'+h(w.left.title)+'</span><b>×</b><span>'+h(w.right.title)+'</span></div>'+
 '<h3>'+h(w.title)+'</h3><div class="cx-world-footer"><span>原创馆长 @'+h(w.author)+'</span>'+
 act('view','◈ 进入这个世界','data-id="'+w.id+'" class="cx-primary"')+'</div></article>';
function chooser(d){
 const left=C.left||0,right=C.right||0;
 return '<section class="cx-panel" id="cxMaker"><div class="cx-eyebrow">02 / IMPOSSIBLE COLLISION ENGINE</div>'+
 '<h2>⚗️ 将两件真实藏品投入碰撞机</h2><p>不同领域的两件物品，碰撞出全新的创作实验。它们不需要在现实世界存在因果关系。</p>'+
 '<form id="cxSearch" class="cx-search"><input name="search" value="'+h(C.search)+'" maxlength="60" placeholder="搜索当前真正公开的藏品、标签、类别">'+
 '<button type="submit">搜索万物</button></form>'+
 '<div class="cx-found">'+(d.picker?.items||[]).map(x=>'<article>'+source(x)+
 '<div class="cx-inline">'+act('pick','放入 A','data-side="left" data-id="'+x.id+'"')+
 act('pick','放入 B','data-side="right" data-id="'+x.id+'"')+'</div></article>').join('')+
 (!d.picker?.items?.length?'<div class="cx-empty">还没有找到符合条件的公开真实藏品。</div>':'')+'</div>'+
 '<div class="cx-reactor"><div><div class="cx-slot-name">OBJECT A</div>'+source(C.preview?.left||d.a)+'</div>'+
 '<div class="cx-core"><strong>✧</strong><small>碰撞反应堆</small></div>'+
 '<div><div class="cx-slot-name">OBJECT B</div>'+source(C.preview?.right||d.b)+'</div></div>'+
 '<div class="cx-law-picker"><label>为平行宇宙设定一条不可能的法则<select id="cxLaw">'+
 (d.laws?.items||[]).map(x=>'<option value="'+h(x.id)+'" '+(C.law===x.id?'selected':'')+'>'+h(x.title)+'</option>').join('')+'</select></label>'+
 act('preview','⚡ 点燃碰撞','class="cx-primary" '+(!left||!right||left===right?'disabled':''))+'</div>'+
 (C.preview?'<div class="cx-result"><div class="cx-eyebrow">DETERMINISTIC FICTION PROMPT / #'+h(C.preview.seed)+'</div>'+
 '<h3>✨ 创意火花</h3><p>'+h(C.preview.prompt)+'</p>'+
 '<small>'+h(C.preview.notice)+'</small></div>':'')+
 (yes()?creator(d):'<div class="cx-need-login">登录后可以为这场碰撞编写两条平行结局、公开作品或改写其他人的世界。'+
 act('login','登录 / 注册','class="cx-outline"')+'</div>')+'</section>';
}
function creator(d){
 const e=d.editWorld;
 const ready=C.left&&C.right&&C.left!==C.right;
 return '<div class="cx-editor"><div class="cx-eyebrow">03 / YOUR WORLD, YOUR RULES</div>'+
 '<h3>✍️ 写下属于你的不可能实验</h3>'+
 (C.remix?'<div class="cx-banner">你正在改写公开世界 #'+C.remix+'。须保留两件真实来源，并重新写出属于自己的完整故事。</div>':'')+
 (e?'<div class="cx-banner">编辑个人世界 #'+e.id+'：任何修改均会自动变为私密草稿并清空旧投票。</div>':'')+
 '<form id="cxForm"><label>新世界名称<input name="title" required minlength="3" maxlength="80" value="'+h(e?.title||'')+'" placeholder="例如：当米线能够抵押记忆"></label>'+
 '<label>世界碰撞假设（至少20字）<textarea name="premise" required minlength="20" maxlength="480" placeholder="在一个时间倒流的世界里，米线与钟表的命运忽然交错……">'+h(e?.premise||'')+'</textarea></label>'+
 '<div class="cx-branch-editor"><div><div class="cx-eyebrow">FUTURE A</div>'+
 '<label>第一个选择<input name="choice_a" required minlength="2" maxlength="60" value="'+h(e?.choice_a||'')+'" placeholder="例如：保留记忆"></label>'+
 '<label>这条路线的结局<textarea name="ending_a" required minlength="15" maxlength="900" placeholder="走向A之后，世界会出现怎样的荒诞变化？">'+h(e?.ending_a||'')+'</textarea></label></div>'+
 '<div><div class="cx-eyebrow">FUTURE B</div>'+
 '<label>第二个选择<input name="choice_b" required minlength="2" maxlength="60" value="'+h(e?.choice_b||'')+'" placeholder="例如：交换灵魂"></label>'+
 '<label>另一条路线的结局<textarea name="ending_b" required minlength="15" maxlength="900" placeholder="走向B之后，会出现完全不同的未来吗？">'+h(e?.ending_b||'')+'</textarea></label></div></div>'+
 '<div class="cx-creator-actions"><button class="cx-primary" type="submit" '+(!ready?'disabled':'')+'>'+
 (C.remix?'✧ 创造独立改写草稿':e?'✓ 保存新版本（回到私密）':'＋ 保存私人平行世界草稿')+'</button>'+
 (e||C.remix?act('reset-edit','清空编辑 / 改写状态','class="cx-outline"'):'')+'</div></form></div>';
}
function outcome(w){
 if(!w.available)return '<section class="cx-panel"><div class="cx-empty">🔒 任一原始作品已撤回。为尊重原作者，已隐藏双方作品标题与所有对应假设文案。</div></section>';
 const pair=[w.left,w.right];
 return '<section class="cx-panel cx-show"><div class="cx-eyebrow">04 / CREATED UNIVERSE · #'+w.id+' / '+h(w.law_title)+'</div>'+
 '<div class="cx-show-head"><div><h2>'+h(w.title)+'</h2><p>✍️ @'+h(w.author)+' · '+(w.status==='public'?'◉ 公开思想实验':'○ 个人私密草稿')+'</p></div>'+
 (w.is_owner?'<div class="cx-tools">'+act('edit','✎ 编辑','data-id="'+w.id+'" class="cx-outline"')+
 (w.status==='public'?act('unpublish','撤回公开','data-id="'+w.id+'" class="cx-outline"'):
 act('publish','发布这个世界','data-id="'+w.id+'" class="cx-primary"'))+
 act('delete','删除','data-id="'+w.id+'" class="cx-danger"')+'</div>':'')+'</div>'+
 '<div class="cx-pair">'+source(pair[0])+'<span class="cx-between">✧</span>'+source(pair[1])+'</div>'+
 '<div class="cx-premise"><span>WORLD LAW : '+h(w.law_title)+'</span><blockquote>'+h(w.premise)+'</blockquote></div>'+
 '<div class="cx-choice-head"><div class="cx-eyebrow">FORKED FUTURE / 选择一条平行命运</div>'+
 '<p>你要让哪个未来发生在这个虚构世界中？选择后才能揭开对应的原创结局。</p></div>'+
 '<div class="cx-futures">'+["a","b"].map(key=>'<article class="'+(C.picked===key?'active':'')+'">'+
 '<div class="cx-future-number">FUTURE '+key.toUpperCase()+'</div><h3>'+h(w["choice_"+key])+'</h3>'+
 (C.picked===key?'<p>'+h(w["ending_"+key])+'</p>':'<p class="cx-locked">？ 结局尚未揭晓</p>')+
 act('choose',C.picked===key?'✓ 已选择这个世界':'✧ 解锁这个未来',
 'data-branch="'+key+'" data-id="'+w.id+'" class="cx-primary"')+
 (w.status==='public'?'<small>真实登录用户选择：'+(w.votes?.[key]||0)+'</small>':'')+'</article>').join('')+'</div>'+
 (w.status==='public'?
 '<div class="cx-actions">'+act('remix','🪐 改写这段平行历史','data-id="'+w.id+'" class="cx-primary"')+
 act('echoes','🌌 查看同源世界谱系','class="cx-outline"')+
 (w.parent_id?act('view','← 查看灵感来源 #'+w.parent_id,'data-id="'+w.parent_id+'" class="cx-outline"'):'')+
 '</div>':'')+
 '<div class="cx-honesty">⚖️ 这是馆长自行创作的架空世界与分支故事。与真实物品有关的名称仅作为创作素材，不代表事实或真实因果。</div></section>';
}
function echoesPane(d){
 if(!d)return '';
 return '<section class="cx-panel"><div class="cx-eyebrow">05 / MULTIVERSE FAMILY TREE</div>'+
 '<h2>🌌 一对藏品，多少个不同的世界？</h2>'+
 '<p>同一对真实物品可以成为不同馆长的共同创作起点。这里仅展示各作者主动公开、来源仍合法的平行宇宙。</p>'+
 '<div class="cx-echo-list">'+(d.items?.length?d.items.map(w=>'<div>'+act('view',h(w.title)+' · '+h(w.law_title)+' · @'+h(w.author),
 'data-id="'+w.id+'" class="cx-outline"')+'</div>').join(''):'<div class="cx-empty">还没有由真实馆长公开的其他平行世界。</div>')+'</div></section>';
}
async function render(){
 let gallery,laws,picker,mine={items:[]};
 try{
  [gallery,laws,picker]=await Promise.all([api('/collisions'),api('/collisions/laws'),
   api('/collisions/sources?q='+encodeURIComponent(C.search))]);
  if(yes())mine=await api('/collisions/mine');
 }catch(e){return '<div class="cx-root"><h2>碰撞机暂时无法连接</h2><p>'+h(e.message)+'</p></div>'}
 let picked=null,editWorld=null,preview=null;
 if(C.focus){try{picked=await api('/collisions/'+C.focus)}catch(e){C.focus=0;C.picked='';C.echoes=null;C.message='旧世界当前已经不再公开或原始来源已经撤回。';}}
 if(C.edit){editWorld=(mine.items||[]).find(x=>x.id===C.edit)||null;
  if(!editWorld||!editWorld.available){C.edit=0;editWorld=null;}
 }
 if(C.left&&C.right&&C.left!==C.right){
  try{preview=await api('/collisions/preview?left_id='+C.left+'&right_id='+C.right+'&law='+encodeURIComponent(C.law))}
  catch(e){C.preview=null;C.echoes=null;C.message='选定的原始物件已经撤回公开；请重新选择。';C.left=0;C.right=0;}
 }
 C.preview=preview;
 if(C.echoes && C.left && C.right){
  try{C.echoes=await api('/collisions/echoes?left_id='+C.left+'&right_id='+C.right)}
  catch(e){C.echoes=null;}
 }
 const start=gallery.items||[];
 return '<div class="cx-root"><section class="cx-hero"><div class="cx-orbit"></div>'+
 '<div class="cx-eyebrow">WONDER ATLAS / WORLD 33 / IMPOSSIBLE EXPERIMENTS</div>'+
 '<h1>让两件万物碰撞，<br><em>诞生一整个不可能的世界。</em></h1>'+
 '<p>现实藏品 × 虚构法则 × 真实馆长的原创故事。选择一个未来，观察故事如何分岔；同一对物件，还能拥有无数个平行宇宙。</p>'+
 '<div class="cx-tags"><span>⚗️ 万物碰撞机</span><span>⚖️ 架空世界法则</span><span>🔀 蝴蝶效应</span><span>🪐 改写历史</span><span>🌌 世界谱系</span></div></section>'+
 (C.message?'<div class="cx-notice">'+h(C.message)+'</div>':'')+
 '<section class="cx-panel"><div class="cx-heading"><div><div class="cx-eyebrow">01 / DISCOVER IMPOSSIBLE UNIVERSES</div>'+
 '<h2>已经诞生的平行世界</h2><p>仅有真实馆长自愿公开、全部来源仍公开的原创实验才出现在这里。</p></div>'+
 act('random','🎲 随机进入真实世界','class="cx-outline"')+'</div>'+
 (start.length?'<div class="cx-gallery">'+start.map(galleryCard).join('')+'</div>':
 '<div class="cx-empty">目前还没有公开的碰撞世界。成为第一位宇宙建造者，用两件真实藏品创造不可能实验！</div>')+'</section>'+
 (picked?outcome(picked):'')+
 chooser({laws,picker,a:preview?.left,b:preview?.right,editWorld})+
 (yes()?'<section class="cx-panel"><div class="cx-eyebrow">MY PRIVATE WORKSHOP</div><h2>🪐 我的原创世界</h2>'+
 ((mine.items||[]).length?'<div class="cx-mine">'+mine.items.map(w=>'<div>'+
 act('view',h(w.title)+' · '+(w.available?(w.status==='public'?'已公开':'私密草稿'):'🔒 来源失效'),
 'data-id="'+w.id+'" class="cx-outline"')+'</div>').join('')+'</div>':
 '<div class="cx-empty">你还没有创建自己的平行世界。所有新作品默认保持私密。</div>')+'</section>':'')+
 echoesPane(C.echoes)+
 '<p class="cx-footnote">所有碰撞故事均属于虚构创作。两件真实藏品标题会在每次公开访问时重新核验；作者可以撤回作品。投票只是登录用户在虚构分支间的个人选择，不是科学预测。</p></div>';
}
async function refresh(){if(window.S?.view==='collision'){const main=document.querySelector('#main');if(main)main.innerHTML=await render();}}
document.addEventListener('change',e=>{
 if(e.target.id==='cxLaw'){C.law=e.target.value;C.preview=null;C.echoes=null;}
},true);
document.addEventListener('submit',async e=>{
 const form=e.target;if(!['cxSearch','cxForm'].includes(form.id))return;
 e.preventDefault();e.stopImmediatePropagation();
 const d=Object.fromEntries(new FormData(form).entries());
 const b=form.querySelector('button[type=submit]');if(b)b.disabled=true;
 try{
  if(form.id==='cxSearch'){C.search=(d.search||'').trim();await refresh();return;}
  if(!C.left||!C.right||C.left===C.right)throw Error('请先选两件不同的真实公开藏品');
  const body={left_id:C.left,right_id:C.right,law:C.law,
   title:d.title,premise:d.premise,choice_a:d.choice_a,choice_b:d.choice_b,
   ending_a:d.ending_a,ending_b:d.ending_b};
  let url='/collisions',method='POST';
  if(C.remix){url='/collisions/'+C.remix+'/remix';}
  else if(C.edit){url='/collisions/'+C.edit;method='PUT';}
  const r=await api(url,{method,body});
  C.focus=r.id||r.world.id;C.edit=0;C.remix=0;C.picked='';C.message='原创平行世界已存为私密草稿，可以在上方查看并主动公开。';
  await refresh();
 }catch(err){C.message=err.message||'无法保存';toast(C.message);await refresh()}
 finally{if(b)b.disabled=false;}
},true);
document.addEventListener('click',async e=>{
 const el=e.target.closest('[data-collision]');if(!el)return;
 e.preventDefault();e.stopImmediatePropagation();
 const op=el.dataset.collision,id=Number(el.dataset.id||0);
 try{
  if(op==='login'){document.querySelector('#loginTop')?.click();return;}
  if(op==='pick'){if(el.dataset.side==='left')C.left=id;else C.right=id;
   C.preview=null;C.echoes=null;C.edit=0;C.remix=0;await refresh();return;}
  if(op==='preview'){C.law=document.querySelector('#cxLaw')?.value||C.law;await refresh();return;}
  if(op==='view'){C.focus=id;C.picked='';C.message='';C.echoes=null;await refresh();
   document.querySelector('.cx-show')?.scrollIntoView({behavior:'smooth',block:'start'});return;}
  if(op==='random'){const d=await api('/collisions');
   const rows=d.items||[];if(!rows.length){C.message='目前没有真正公开的平行宇宙，不会随机制造虚构馆长。';await refresh();return;}
   C.focus=rows[Math.floor(Math.random()*rows.length)].id;C.picked='';await refresh();return;}
  if(op==='choose'){
   C.picked=el.dataset.branch||'';
   if(yes()){const w=await api('/collisions/'+id);if(w.status==='public')await api('/collisions/'+id+'/choose/'+C.picked,{method:'POST'});}
   await refresh();return;
  }
  if(op==='echoes'){const w=await api('/collisions/'+C.focus);C.left=w.left.id;C.right=w.right.id;
   C.echoes=await api('/collisions/echoes?left_id='+C.left+'&right_id='+C.right);await refresh();
   document.querySelector('.cx-echo-list')?.scrollIntoView({behavior:'smooth',block:'center'});return;}
  if(op==='edit'){const w=await api('/collisions/'+id);
   C.edit=id;C.remix=0;C.left=w.left.id;C.right=w.right.id;C.law=w.law;
   C.message='正在编辑你自己的平行宇宙；保存会撤回原版公开和投票。';await refresh();
   document.querySelector('#cxMaker')?.scrollIntoView({behavior:'smooth',block:'start'});return;}
  if(op==='remix'){if(!yes()){document.querySelector('#loginTop')?.click();return;}
   const w=await api('/collisions/'+id);C.remix=id;C.edit=0;
   C.left=w.left.id;C.right=w.right.id;C.law=w.law;C.message='已取用两个原始物件；请独立创造你自己的全新假设与两个结局。';
   await refresh();document.querySelector('#cxMaker')?.scrollIntoView({behavior:'smooth',block:'start'});return;}
  if(op==='reset-edit'){C.edit=0;C.remix=0;C.message='已退出修改模式。';await refresh();return;}
  if(op==='delete'&&!confirm('确认永久删除你创作的平行世界及其分支投票吗？'))return;
  if(op==='unpublish'&&!confirm('将这个世界恢复为私密草稿并清空旧投票？'))return;
  const routes={publish:['POST','/collisions/'+id+'/publish'],
                unpublish:['POST','/collisions/'+id+'/unpublish'],
                delete:['DELETE','/collisions/'+id]};
  const route=routes[op];if(!route)return;
  await api(route[1],{method:route[0]});if(op==='delete')C.focus=0;
  C.message={publish:'✨ 你的原创平行宇宙已经公开！',
    unpublish:'世界已恢复私密，原有投票已清除。',
    delete:'原创平行世界已删除，原始两件藏品不受影响。'}[op];
  await refresh();
 }catch(err){C.message=err.message||'无法完成';toast(C.message);await refresh();}
},true);
window.WonderCollision={render,refresh,open(id){C.focus=Number(id)||0}};
})();