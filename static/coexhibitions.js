/* V30 · Co-curated Museum: bilateral publish, private drafts, real visitor stamps. */
(() => {
'use strict';
const T={selected:0,tourIndex:0,showEdit:false,notice:''};
const safe=s=>String(s??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[ch]));
const b=(act,title,attrs='')=>'<button type="button" data-co="'+act+'" '+attrs+'>'+title+'</button>';
const logged=()=>Boolean(window.S?.user);
const myRole=(d)=>d?.my_role==='a'?'a':'b';
function exhibitTile(item,ownerPanel=false){
 const x=item.exhibit;
 if(item.source_unavailable||!x)return '<article class="ce-artifact ce-missing"><div class="ce-artifact-icon">🔒</div><h4>原始藏品暂不可用</h4>'+
 (ownerPanel&&item.is_mine?b('remove','撤下我贡献的失效藏品','data-id="'+item.id+'" class="ce-danger"'):'')+'</article>';
 return '<article class="ce-artifact"><div class="ce-artifact-image">'+
 (x.image_url?'<img src="'+safe(x.image_url)+'" alt="" loading="lazy">':'<span>✦</span>')+'</div>'+
 '<div class="ce-artifact-copy"><div class="ce-kicker">EXHIBIT / '+x.id+' · @'+safe(x.curator)+'</div>'+
 '<h4>'+safe(x.title)+'</h4><small>'+safe(x.domain||x.category)+'</small>'+
 '<p>'+safe(item.commentary)+'</p>'+
 '<div class="ce-card-actions">'+b('open-exhibit','查看原始展品 ↗','data-id="'+x.id+'"')+
 (ownerPanel&&item.is_mine?b('remove','撤下我的展品','data-id="'+item.id+'" class="ce-danger"'):'')+'</div></div></article>';
}
function banner(d){
 return '<div class="ce-show-header"><div><div class="ce-kicker">JOINT MUSEUM · #'+d.id+'</div>'+
 '<h2>'+safe(d.title)+'</h2><p>'+safe(d.introduction||'两位馆长共同策划的真实公开藏品之旅。')+'</p>'+
 '<div class="ce-curators"><span>✦ '+safe(d.curators[0])+'</span><b>×</b><span>✦ '+safe(d.curators[1])+'</span></div></div>'+
 '<div class="ce-show-status">'+(d.state==='public'&&d.available?'◉ 公开展览':d.state==='closed'?'◌ 展览结束':'◎ 联合策展中')+
 '<small>第 '+d.revision+' 版 · '+d.items.length+' 件藏品</small></div></div>';
}
function approvals(d){
 const a=d.approved?.a,bv=d.approved?.b;
 return '<div class="ce-approvals"><div class="'+(a?'approved':'')+'">'+(a?'✓':'○')+' '+safe(d.curators[0])+' 审批'+(a?'已完成':'待确认')+'</div>'+
 '<div class="'+(bv?'approved':'')+'">'+(bv?'✓':'○')+' '+safe(d.curators[1])+' 审批'+(bv?'已完成':'待确认')+'</div></div>';
}
function tour(d){
 if(!d.available||!d.items.length)return '';
 const available=d.items.filter(x=>!x.source_unavailable);
 if(!available.length)return '';
 T.tourIndex=Math.min(T.tourIndex,available.length-1);
 const current=available[T.tourIndex];
 return '<div class="ce-tour"><div class="ce-tour-label">🐒 双馆故事漫游 · '+(T.tourIndex+1)+' / '+available.length+'</div>'+
 '<div class="ce-tour-body">'+exhibitTile(current)+'</div>'+
 '<div class="ce-tour-steps">'+b('tour-prev','← 上一站',T.tourIndex===0?'disabled':'')+
 '<div class="ce-tour-dots">'+available.map((x,i)=>b('tour-goto',i===T.tourIndex?'●':'○','data-i="'+i+'" aria-label="第'+(i+1)+'站"')).join('')+'</div>'+
 b('tour-next','下一站 →',T.tourIndex===available.length-1?'disabled':'')+'</div>'+
 '<p class="ce-disclaimer">展览顺序仅来自馆长提交展品的先后；说明文字由贡献者自行编写，平台不将其视作已核验知识。</p></div>';
}
function editPanel(d,my){
 if(!d.is_member||d.state==='closed')return '';
 const sourceOptions=(my?.my_public_exhibits||[]).filter(x=>!d.items.some(y=>y.exhibit?.id===x.id));
 return '<div class="ce-editor">'+
 '<div class="ce-editor-head"><h3>🎨 两位馆长的策展工作台</h3><p>每次修改均撤销双方原有批准，只有共同批准同一版本，才能公开。</p></div>'+
 (!d.available?'<p class="ce-alert">一件来源展品已撤回或平行宇宙会合已失效；展览暂不公开。请各自处理源作品，或结束合作。</p>':'')+
 approvals(d)+
 '<div class="ce-actions">'+
 (d.available?b('approve',d.approved[myRole(d)]?'✓ 我已批准当前版本':'✓ 批准当前版本','class="ce-primary" '+(d.approved[myRole(d)]?'disabled':'')):'')+
 b('retract','撤回批准 / 暂停公开','class="ce-muted-btn"')+
 b('toggle-edit',T.showEdit?'收起主题修改':'编辑展厅主题','class="ce-muted-btn"')+
 b('close','结束联合展厅','class="ce-danger"')+'</div>'+
 (T.showEdit?'<form id="ceEditForm" class="ce-edit-form"><label>展览主题<input name="title" maxlength="80" minlength="2" required value="'+safe(d.title)+'"></label>'+
 '<label>联合策展前言<textarea name="introduction" maxlength="480">'+safe(d.introduction)+'</textarea></label>'+
 '<button class="ce-primary">保存修改并重新进入审批</button></form>':'')+
 '<div class="ce-add"><h4>✦ 为展厅贡献我的公开藏品</h4>'+
 (sourceOptions.length?'<form id="ceAddForm"><label>选择本人公开展品<select name="exhibit_id">'+
 sourceOptions.map(x=>'<option value="'+x.id+'">'+safe(x.title)+'</option>').join('')+'</select></label>'+
 '<label>为什么它适合这个展览？<textarea name="commentary" minlength="8" maxlength="300" required placeholder="写下属于你自己的导览理由，不冒充平台事实核验。"></textarea></label>'+
 '<button class="ce-primary" '+(!d.available||d.items.length>=12?'disabled':'')+'>＋ 将这件藏品加入联合展厅</button></form>':
 '<p class="ce-disclaimer">暂无可添加的本人公开展品，或已经全部加入。</p>')+'</div></div>';
}
function showroom(d,my){
 return '<section class="ce-panel ce-show">'+banner(d)+
 (d.available?'<div class="ce-show-items">'+d.items.map((x,i)=>'<div class="ce-order">'+
 '<div class="ce-order-label">第 '+(i+1)+' 站</div>'+exhibitTile(x,d.is_member)+'</div>').join('')+'</div>':
 '<div class="ce-hide">🔒 任一原始藏品、关联世界或跨馆会合已不可用。展品标题与说明已动态遮蔽。</div>')+
 (d.available?tour(d):'')+
 (d.state==='public'&&d.available?'<div class="ce-stamp"><div><b>🏵️ 联合展览纪念章</b><p>目前 '+d.stamps+' 位登录用户自行领取过本版本纪念章。领取不代表经过平台参观认证。</p></div>'+
 (logged()?b('stamp',d.stamped?'撤销我的纪念章':'✦ 领取纪念章','class="ce-primary"'):
 b('login','登录后领取纪念章','class="ce-primary"'))+
 '</div>':'')+
 (d.is_member?editPanel(d,my):'')+'</section>';
}
async function render(){
 let pub;
 try{pub=await api('/coexhibitions/public')}catch(e){return '<section class="ce-root"><h1>联合展厅暂时不可用</h1><p>'+safe(e.message)+'</p></section>'}
 let my=null;
 if(logged()){try{my=await api('/coexhibitions/mine')}catch(e){T.notice=e.message}}
 const mine=my?.items||[],live=pub.items||[];
 const candidates=[...mine,...live];
 if(!candidates.some(x=>x.id===T.selected))T.selected=candidates[0]?.id||0;
 let selected=null;
 if(T.selected){try{selected=await api('/coexhibitions/'+T.selected)}catch(e){
  T.selected=0;T.tourIndex=0;T.notice='原始展览当前不再可用，请选择其他展览。';
 }}
 const opts=my?.bridge_options||[];
 return '<div class="ce-root"><section class="ce-hero"><div class="ce-orbit"></div>'+
 '<div class="ce-kicker">WONDER ATLAS · WORLD 30 · CO-CURATION</div><h1>一座博物馆，<br><em>由两个世界共同建造。</em></h1>'+
 '<p>每件展品都是真实馆长亲自公开、亲自授权参与的收藏。只有两位馆长批准同一版本，联合展厅才会对游客开放。</p>'+
 '<div class="ce-badges"><span>🤝 双人联合策展</span><span>✦ 真实公开藏品</span><span>🏵️ 参观纪念章</span><span>🐒 双馆故事漫游</span></div></section>'+
 (T.notice?'<div class="ce-alert">'+safe(T.notice)+'</div>':'')+
 '<div class="ce-overview"><section class="ce-panel"><div class="ce-kicker">01 / CURATOR STUDIO</div>'+
 '<h2>共同建造新的世界</h2>'+
 (!logged()?'<p>登录后可以从你与另一位馆长共同同意的 V29 跨馆会合开始联合建馆。</p>'+
 b('login','登录 / 注册，成为馆长','class="ce-primary"'):
 (opts.length?'<form id="ceCreateForm"><label>基于哪次双方同意的会合？<select name="bridge_id">'+
 opts.map(x=>'<option value="'+x.id+'">'+safe(x.curators.join(' × '))+' · #'+x.id+'</option>').join('')+'</select></label>'+
 '<label>联合展厅名称<input name="title" minlength="2" maxlength="80" required placeholder="例如：从一碗米线到人类文明"></label>'+
 '<label>一起策展的理由<textarea name="introduction" maxlength="480" placeholder="两位馆长希望向游客展示什么？"></textarea></label>'+
 '<button class="ce-primary">＋ 创建私人联合策展草稿</button></form>':
 '<div class="ce-empty">还没有可以发起展厅的有效双人会合。先在「万物平行宇宙」与另一位真实馆长建立双方同意的连接。</div>')+
 b('navigate-parallel','🌌 前往平行宇宙会合','class="ce-muted-btn"'))+
 '</section><section class="ce-panel"><div class="ce-kicker">02 / THE EXHIBITION REGISTER</div>'+
 '<h2>正在建造的联合展厅 <span class="ce-number">'+mine.length+'</span></h2>'+
 (mine.length?'<div class="ce-directory">'+mine.map(x=>b('select','<b>'+safe(x.title)+'</b><small>'+safe(x.curators.join(' × '))+
 ' · '+(x.state==='public'?'已公开':'待双方审批')+'</small>',
 'class="'+(T.selected===x.id?'active':'')+'" data-id="'+x.id+'"')).join('')+'</div>':
 '<div class="ce-empty">你的私人联合策展还没有开始。</div>')+
 '</section></div>'+
 '<section class="ce-panel"><div class="ce-kicker">03 / WORLD GALLERY</div><h2>🌍 面向所有游客的联合展览 <span class="ce-number">'+live.length+'</span></h2>'+
 '<p>只展示经真实双方审批，且原始来源始终允许公开的展览。没有开放作品时不会编造社区内容。</p>'+
 (live.length?'<div class="ce-public-list">'+live.map(x=>b('select','<b>✧ '+safe(x.title)+'</b><small>'+safe(x.curators.join(' × '))+
 ' · '+x.count+' 站 · '+x.stamps+' 枚自行领取印章</small>',
 'class="'+(T.selected===x.id?'active':'')+'" data-id="'+x.id+'"')).join('')+'</div>':
 '<div class="ce-empty">联合展览尚未开放。第一座展厅可以由两位馆长一起建造。</div>')+
 '</section>'+
 (selected?showroom(selected,my):'<section class="ce-panel ce-empty ce-empty-wide">✧ 选择一座真实联合展览，或者与另一位馆长共同创建第一座展厅。</section>')+
 '<p class="ce-disclaimer">公开展品来源动态授权；联合策展由双方主动审核；用户领取纪念章仅为自我记录，不是平台验证的参观行为。</p></div>';
}
async function refresh(){if(window.S?.view==='coexhibitions'){const main=document.querySelector('#main');if(main)main.innerHTML=await render()}}
document.addEventListener('submit',async e=>{
 const f=e.target;if(!['ceCreateForm','ceEditForm','ceAddForm'].includes(f.id))return;
 e.preventDefault();e.stopImmediatePropagation();
 const d=Object.fromEntries(new FormData(f).entries()),button=f.querySelector('[type=submit],button');
 if(button)button.disabled=true;
 try{
  if(f.id==='ceCreateForm'){
   const r=await api('/coexhibitions',{method:'POST',body:{bridge_id:Number(d.bridge_id),title:d.title,introduction:d.introduction||''}});
   T.selected=r.exhibition.id;T.tourIndex=0;toast('联合展厅草稿已建立');}
  if(f.id==='ceEditForm'){
   await api('/coexhibitions/'+T.selected,{method:'PUT',body:{title:d.title,introduction:d.introduction||''}});
   T.showEdit=false;toast('已保存新版本，需要双方重新审批');}
  if(f.id==='ceAddForm'){
   await api('/coexhibitions/'+T.selected+'/items',{method:'POST',body:{exhibit_id:Number(d.exhibit_id),commentary:d.commentary}});
   toast('已贡献真实藏品，请双方重新确认');}
  T.notice='';await refresh();
 }catch(err){T.notice=err.message||'未能完成';toast(T.notice);await refresh()}
 finally{if(button)button.disabled=false}
},true);
document.addEventListener('click',async e=>{
 const x=e.target.closest('[data-co]');if(!x)return;
 e.preventDefault();e.stopImmediatePropagation();
 const action=x.dataset.co,id=Number(x.dataset.id||0);
 try{
  if(action==='login'){document.querySelector('#loginTop')?.click();return}
  if(action==='navigate-parallel'){await navigate('parallel');return}
  if(action==='select'){T.selected=id;T.tourIndex=0;T.showEdit=false;await refresh();return}
  if(action==='open-exhibit'){await openDetail(id);return}
  if(action==='toggle-edit'){T.showEdit=!T.showEdit;await refresh();return}
  if(action==='tour-prev'||action==='tour-next'||action==='tour-goto'){
   T.tourIndex=action==='tour-goto'?Number(x.dataset.i):Math.max(0,T.tourIndex+(action==='tour-next'?1:-1));
   await refresh();return}
  if(action==='close'&&!confirm('结束这座联合展厅？展览及纪念章将不再公开，原始藏品保留。'))return;
  if(action==='retract'&&!confirm('撤销双方现有批准并暂停公开展示？游客纪念章也会清空。'))return;
  if(action==='remove'&&!confirm('撤下我贡献的这件展品？双方需要重新审批。'))return;
  const route={
   approve:['POST','/coexhibitions/'+T.selected+'/approve'],
   retract:['POST','/coexhibitions/'+T.selected+'/retract'],
   remove:['DELETE','/coexhibitions/'+T.selected+'/items/'+id],
   close:['DELETE','/coexhibitions/'+T.selected],
  };
  if(action==='stamp'){
   const d=await api('/coexhibitions/'+T.selected);await api('/coexhibitions/'+T.selected+'/stamp',
    {method:d.stamped?'DELETE':'POST'});
   toast(d.stamped?'已撤销私人印章':'🏵️ 已自行领取展览纪念章');await refresh();return;
  }
  const call=route[action];if(!call)return;
  await api(call[1],{method:call[0]});
  if(action==='close')T.selected=0;
  T.tourIndex=0;
  toast({approve:'你的审批已记录',retract:'展览已暂停公开',remove:'已撤下你的展品',close:'联合展厅已结束'}[action]);await refresh();
 }catch(err){T.notice=err.message||'未能完成操作';toast(T.notice);await refresh()}
},true);
window.WonderCoExhibitions={render,refresh,open(id){T.selected=Number(id)||0;T.tourIndex=0}};
})();
