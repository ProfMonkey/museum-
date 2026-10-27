/* V36 · 万界遗产交换站：real dual-curator symbolic gifts, never asset transfers. */
(() => {
'use strict';
const H={focus:0,embassy:0,notice:'',editTopic:false};
const safe=x=>String(x??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const action=(act,text,attr='')=>'<button type="button" data-heritage="'+act+'" '+attr+'>'+text+'</button>';
const signed=()=>Boolean(window.S?.user);
const word={draft:'双人私密草稿',public:'双方批准公开',closed:'已终止'};
function gift(x,caption){
 if(!x)return '<div class="hg-gift hg-missing">🔒 原始藏品已撤回</div>';
 return '<div class="hg-gift"><div class="hg-gift-head">'+safe(caption||'ORIGINAL EXHIBIT')+'</div>'+
 '<div class="hg-gift-content">'+(x.image_url?'<img src="'+safe(x.image_url)+'" alt="" loading="lazy">':'<span class="hg-gift-icon">✧</span>')+
 '<div><strong>'+safe(x.title)+'</strong><small>原始馆长 @'+safe(x.curator)+' · '+safe(x.domain)+'</small></div></div>'+
 action('source','↗ 查看原作','data-id="'+x.id+'" class="hg-outline"')+'</div>';
}
function showcase(d){
 if(!d.available)return '<section class="hg-panel hg-locked"><div class="hg-eyebrow">WITHDRAWN / RECONSENT REQUIRED</div>'+
 '<h2>🔒 原始馆藏或使馆授权已变化</h2><p>隐去双方旧标题、文化意义和图像，不展示任何缓存的原作者内容。</p>'+
 (signed()?'<div class="hg-actions">'+action('rebase','↻ 重新核验使馆与馆藏','data-id="'+d.id+'" class="hg-primary"')+
 action('close','结束这项交换','data-id="'+d.id+'" class="hg-danger"')+'</div>':'')+'</section>';
 return '<section class="hg-panel hg-show"><div class="hg-eyebrow">V36 / CULTURAL EXCHANGE / #'+d.id+' / VERSION '+d.version+'</div>'+
 '<div class="hg-head"><div><h2>✧ '+safe(d.title)+'</h2>'+
 '<p>状态：'+safe(word[d.state]||d.state)+' · 两位真实馆长共同策展</p></div>'+
 (d.my_side?'<div class="hg-actions">'+
 (d.state!=='closed'?action('retract','撤回当前公开','data-id="'+d.id+'" class="hg-outline"'):'')+
 action('close','终止合作','data-id="'+d.id+'" class="hg-danger"')+'</div>':'')+
 '</div><blockquote class="hg-premise">'+safe(d.premise)+'</blockquote>'+
 '<div class="hg-exchange">'+gift(d.a,'CIVILIZATION A · 原始馆长的物件')+
 '<div class="hg-gateway"><span>✧</span><b>文化互赠</b><small>不转移产权</small></div>'+
 gift(d.b,'CIVILIZATION B · 原始馆长的物件')+'</div>'+
 '<div class="hg-interpretations"><article><span>VOICE A · @'+safe(d.a.curator)+'</span>'+
 '<p>'+safe(d.a_note||'第一位馆长还没有写下属于自己的文化解释。')+'</p>'+
 '<div class="hg-sign">'+(d.approved?.a?'✓ 已批准本版':'待馆长 A 批准')+'</div></article>'+
 '<article><span>VOICE B · @'+safe(d.b.curator)+'</span>'+
 '<p>'+safe(d.b_note||'第二位馆长还没有写下属于自己的文化解释。')+'</p>'+
 '<div class="hg-sign">'+(d.approved?.b?'✓ 已批准本版':'待馆长 B 批准')+'</div></article></div>'+
 (d.my_side&&d.state!=='closed'?'<div class="hg-participant"><h3>✍️ 我的馆长席位：'+d.my_side.toUpperCase()+'</h3>'+
 '<p>你只能修改自己原始藏品的文化解读。提交后旧公开立即撤回，双方需要重新批准同一版本。</p>'+
 '<form id="hgNoteForm"><label>只代表我自己的原创讲述（12–680字）<textarea name="text" required minlength="12" maxlength="680" placeholder="这件真实馆藏承载什么文化意义？对另一文明意味着什么？">'+safe(d[d.my_side+'_note']||'')+'</textarea></label>'+
 '<button type="submit" class="hg-primary">✦ 保存我的文化诠释</button></form>'+
 '<div class="hg-actions">'+action('approve','✓ 我同意公开这一版本','data-id="'+d.id+'" class="hg-primary"')+
 action('toggle-topic','✎ 修订联合展题','class="hg-outline"')+'</div>'+
 (H.editTopic?'<form id="hgTopicForm"><label>联合展题<input name="title" required minlength="3" maxlength="90" value="'+safe(d.title)+'"></label>'+
 '<label>联合背景<textarea name="premise" required minlength="20" maxlength="560">'+safe(d.premise)+'</textarea></label>'+
 '<button type="submit" class="hg-outline">保存新私密版本</button></form>':'')+
 '</div>':'')+
 (d.state==='public'?'<div class="hg-passport"><div><div class="hg-eyebrow">VISITORS OF AN IMPOSSIBLE HERITAGE EXHIBITION</div>'+
 '<h3>🛂 文化漫游护照 · '+d.passports+' 枚真实站内印章</h3>'+
 '<p>只记录真实账号主动领取的虚拟访问章，不宣称实际到馆或转移藏品。</p></div>'+
 (signed()?action('passport',d.my_passport?'✓ 已领取护照章':'◈ 领取文化交流纪念章',
 'data-id="'+d.id+'" class="hg-primary"'):'<span class="hg-guest">登录后可领取个人虚拟护照章</span>')+
 '</div>':'')+
 '<div class="hg-notice">'+safe(d.notice||'这仅是虚构世界的文化交流，不涉及实际所有权或历史真实性认证。')+'</div></section>';
}
async function render(){
 let gallery,mine={items:[]},embassies={items:[]},sources={a:[],b:[]};
 try{
  gallery=await api('/heritage/public');
  if(signed()){
   [mine,embassies]=await Promise.all([api('/heritage/mine'),api('/heritage/embassies')]);
   if(!H.embassy)H.embassy=embassies.items[0]?.id||0;
   if(H.embassy)try{sources=await api('/heritage/sources?embassy_id='+H.embassy)}
      catch(e){H.embassy=embassies.items[0]?.id||0;sources={a:[],b:[]}}
  }
 }catch(err){return '<div class="hg-root hg-panel"><h2>遗产交换站暂时无法连接</h2><p>'+safe(err.message)+'</p></div>'}
 const publicItems=gallery.items||[],mineItems=mine.items||[];
 if(!H.focus)H.focus=mineItems[0]?.id||publicItems[0]?.id||0;
 let detail=null;
 if(H.focus)try{detail=await api('/heritage/'+H.focus)}
 catch(err){H.focus=0;H.notice='这项合作已撤回公开、终止或无访问权限。'}
 return '<div class="hg-root"><header class="hg-hero"><div class="hg-orbit"></div>'+
 '<div class="hg-eyebrow">WONDER ATLAS · WORLD 36 · CULTURAL HERITAGE EXCHANGE</div>'+
 '<h1>两位馆长，<br><em>交换的不是物品，而是文明的故事。</em></h1>'+
 '<p>让 V35 两国真实签署的外交使馆进一步成为「共同遗产」：双方分别拿出自己公开收藏中的一件物品，亲自写下文化意义，双方审阅同一版本后，才对游客开放。</p>'+
 '<div class="hg-badges"><span>🎁 双文明互赠展</span><span>✍️ 独立馆长署名</span><span>🤝 双方公开授权</span>'+
 '<span>🛂 虚拟漫游护照</span><span>🔒 原始产权不变</span></div></header>'+
 (H.notice?'<p class="hg-alert">'+safe(H.notice)+'</p>':'')+
 '<section class="hg-panel"><div class="hg-eyebrow">01 / HERITAGES ALREADY SHARED</div><h2>🌍 真实公开的万界文化互赠</h2>'+
 '<p>只有两位真实馆长各自撰文、批准同一版本，且原使馆及两件藏品均仍公开的合作才会出现在这里。</p>'+
 (publicItems.length?'<div class="hg-grid">'+publicItems.map(x=>'<article class="hg-card"><div class="hg-eyebrow">JOINT HERITAGE / #'+x.id+'</div>'+
 '<h3>'+safe(x.title)+'</h3><div class="hg-mini-pair"><span>'+safe(x.a.title)+'</span><b>✧</b><span>'+safe(x.b.title)+'</span></div>'+
 '<small>@'+safe(x.a.curator)+' × @'+safe(x.b.curator)+' · '+x.passports+' 枚真实纪念章</small>'+
 action('view','◈ 进入共建遗产展','data-id="'+x.id+'" class="hg-primary"')+'</article>').join('')+'</div>':
 '<div class="hg-empty">还没有双方批准的公开文化互赠。任何空白数据都不会用虚假馆长或模拟热度填充。</div>')+'</section>'+
 (detail?showcase(detail):'')+
 '<section class="hg-panel" id="hgStudio"><div class="hg-eyebrow">02 / TWO CURATORS · ONE SHARED HERITAGE</div>'+
 '<h2>🎁 双馆长文化礼物工坊</h2>'+
 (!signed()?'<div class="hg-empty">登录后可以在双方已经公开的 V35 使馆中参与创建共同文化遗产。</div>':
 '<p>首先建立 V35 大使馆，双方各写至少一封外交信并各自批准同一版本。然后才能邀请彼此将一件公开原作组合成象征性遗产。</p>'+
 (embassies.items.length?'<form id="hgEmbassySelect"><label>选择我参与的正式公开使馆<select name="embassy_id">'+
 embassies.items.map(e=>'<option value="'+e.id+'" '+(H.embassy===e.id?'selected':'')+'>'+safe(e.title)+' · 我的席位 '+e.side.toUpperCase()+'</option>').join('')+
 '</select></label><button class="hg-outline" type="submit">切换使馆与藏品</button></form>'+
 '<form id="hgCreateForm"><div class="hg-form-pair"><label>馆长 A 的公开原始藏品<select name="a_exhibit_id" required>'+
 (sources.a||[]).map(s=>'<option value="'+s.id+'">'+safe(s.title)+' · @'+safe(s.curator)+'</option>').join('')+
 '</select></label><label>馆长 B 的公开原始藏品<select name="b_exhibit_id" required>'+
 (sources.b||[]).map(s=>'<option value="'+s.id+'">'+safe(s.title)+' · @'+safe(s.curator)+'</option>').join('')+'</select></label></div>'+
 '<label>联合文化遗产展题<input name="title" required minlength="3" maxlength="90" placeholder="例如：一支青铜号角与一张星际地图"></label>'+
 '<label>联合展览背景（20–560字）<textarea name="premise" required minlength="20" maxlength="560" placeholder="在这两个虚构文明之间，为什么决定相互展示这两件真实藏品？"></textarea></label>'+
 '<button class="hg-primary" type="submit" '+(!sources.a?.length||!sources.b?.length?'disabled':'')+'>✦ 创建双方可见的私密文化交流草稿</button></form>':
 '<div class="hg-empty">尚无当前双方均批准公开的 V35 合作使馆。请先在「万界文明大使馆」建立并共同公开外交合作。</div>')+
 action('goto-embassy','🤝 前往万界文明大使馆','class="hg-outline"')+
 '<h3 class="hg-mine-heading">我的文化交流项目</h3>'+
 (mineItems.length?'<div class="hg-mine">'+mineItems.map(x=>'<div>'+
 action('view','#'+x.id+' · '+safe(x.title)+' · '+(x.available?safe(word[x.state]||x.state):'🔒 来源失效'),
 'data-id="'+x.id+'" class="hg-outline"')+'</div>').join('')+'</div>':
 '<div class="hg-empty">还没有与你有关的文化互赠草稿。</div>'))+
 '</section><p class="hg-footer">⚖️ 本站只记录作者主动创作的**虚构世界文化互赠**，不代表真正发生了外交、实物搬迁、藏品产权、经济支付或国家协议。</p></div>';
}
async function refresh(){if(window.S?.view==='heritage'){const target=document.querySelector('#main');if(target)target.innerHTML=await render()}}
document.addEventListener('submit',async e=>{
 const f=e.target;if(!['hgNoteForm','hgTopicForm','hgCreateForm','hgEmbassySelect'].includes(f.id))return;
 e.preventDefault();e.stopImmediatePropagation();
 const data=Object.fromEntries(new FormData(f).entries()),btn=f.querySelector('[type=submit],button');
 if(btn)btn.disabled=true;
 try{
  if(f.id==='hgEmbassySelect'){H.embassy=Number(data.embassy_id);H.notice='切换了当前真实公开的合作使馆。';}
  else if(f.id==='hgCreateForm'){
   const r=await api('/heritage',{method:'POST',body:{
     embassy_id:H.embassy,a_exhibit_id:Number(data.a_exhibit_id),b_exhibit_id:Number(data.b_exhibit_id),
     title:data.title,premise:data.premise}});
   H.focus=r.id;H.notice='已创建私密草稿。请由双方分别为自己的原作撰文，并批准同一版本。';
  }else if(f.id==='hgNoteForm'){
   await api('/heritage/'+H.focus+'/note',{method:'PUT',body:{text:data.text}});
   H.notice='✍️ 你的解读已署名保存；双方旧授权已重置。';
  }else{
   await api('/heritage/'+H.focus+'/topic',{method:'PUT',body:{title:data.title,premise:data.premise}});
   H.editTopic=false;H.notice='联合展题已更新；旧公开授权已失效。';
  }
  await refresh();
 }catch(err){H.notice=err.message||'本次操作失败';toast(H.notice);await refresh()}
 finally{if(btn)btn.disabled=false}
},true);
document.addEventListener('click',async e=>{
 const el=e.target.closest('[data-heritage]');if(!el)return;
 e.preventDefault();e.stopImmediatePropagation();
 const command=el.dataset.heritage,id=Number(el.dataset.id||0);
 try{
  if(command==='goto-embassy'){await navigate('embassies');return}
  if(command==='source'){await openDetail(id);return}
  if(command==='view'){H.focus=id;H.editTopic=false;H.notice='';await refresh();document.querySelector('.hg-show,.hg-locked')?.scrollIntoView({behavior:'smooth',block:'start'});return}
  if(command==='toggle-topic'){H.editTopic=!H.editTopic;await refresh();return}
  if(['close','retract'].includes(command)&&!confirm(command==='close'?'确认永久终止此次文化互赠，不删除任何原始藏品？':'确认撤回本版公开并清除全部旧版双方审批？'))return;
  const path='/heritage/'+id+'/'+command;
  if(!['approve','retract','rebase','close','passport'].includes(command))return;
  const r=await api(path,{method:'POST'});
  H.notice=r.notice||({close:'此次文化互赠已终止。',approve:'已记录独立批准，等待另一位馆长。'}[command]||'操作成功');
  await refresh();
 }catch(err){H.notice=err.message||'本次操作失败';toast(H.notice);await refresh()}
},true);
window.WonderHeritage={render,refresh,open(id){H.focus=Number(id)||0}};
})();