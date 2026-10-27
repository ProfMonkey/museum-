/* V32 · Mystery Museum — play against genuine, live public exhibits. */
(() => {
'use strict';
const X={selected:0,manage:0,query:'',basket:[],answer:0,alert:'',lastReveal:null};
const esc=s=>String(s??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const btn=(action,label,attr='')=>'<button type="button" data-mystery="'+action+'" '+attr+'>'+label+'</button>';
const log=()=>Boolean(window.S?.user);
function sourceCard(e,opts={}){
 if(!e)return '<div class="mx-source mx-vanished">🔒 原始公开藏品已失效</div>';
 return '<div class="mx-source"><div class="mx-glyph">'+
 (e.image_url?'<img src="'+esc(e.image_url)+'" alt="" loading="lazy">':'✦')+'</div>'+
 '<div class="mx-source-copy"><strong>'+esc(e.title)+'</strong><small>#'+e.id+' · '+esc(e.category)+' · @'+esc(e.curator)+'</small></div>'+
 (opts.action?btn(opts.action,opts.label||'查看','data-id="'+e.id+'" '+(opts.extra||'')):'')+'</div>';
}
function introCard(g){
 return '<article class="mx-trail"><div class="mx-trail-symbol">🗝</div><div class="mx-label">MYSTERY TRAIL · #'+g.id+'</div>'+
 '<h3>'+esc(g.title)+'</h3><p>'+esc(g.premise)+'</p><div class="mx-trail-footer"><span>🏛 @'+esc(g.curator)+'</span>'+
 '<span>◎ '+g.stages+' 道线索</span><span>✦ '+g.completions+' 人自行完成</span></div>'+
 btn('select-play','✧ 进入谜案世界','data-id="'+g.id+'" class="mx-gold"')+'</article>';
}
function stagePane(play){
 if(!play)return '<div class="mx-empty">选择一个真实公开的藏品谜案，或创建自己的谜案。</div>';
 let content='<div class="mx-kicker">CURATOR / '+esc(play.curator)+'</div>'+
 '<h2>🧩 '+esc(play.title)+'</h2><p class="mx-premise">'+esc(play.premise)+'</p>';
 if(play.completed){
  content+='<div class="mx-complete"><div class="mx-complete-star">'+('★'.repeat(play.stars||1))+
  ('☆'.repeat(3-(play.stars||1)))+'</div><h3>恭喜！你解开了全部谜案</h3><p>你的答案匹配了馆长设定的谜题。星星根据你的错误次数计算，不代表历史或科学能力认证。</p>'+
  '<div class="mx-complete-route">'+(play.route||[]).map((r,i)=>'<div class="mx-finish-stop"><b>第 '+(i+1)+' 站</b><p>'+esc(r.clue)+'</p>'+sourceCard(r.exhibit,{action:'open-exhibit',label:'查看原展品'})+'</div>').join('')+'</div>'+
  btn('restart','↻ 再挑战一次','class="mx-outline"')+'</div>';
 }else{
  const st=play.stage||{};
  content+='<div class="mx-progress"><span>第 '+st.index+' 站 / 共 '+play.total+' 站</span>'+
  '<span>'+play.solved+' 个已破解 · '+play.wrong+' 次选错</span></div>'+
  '<div class="mx-progress-track"><i style="width:'+Math.round(100*(play.solved/play.total))+'%"></i></div>'+
  '<div class="mx-scroll">📜 <span>馆长写下的谜案线索</span></div>'+
  '<blockquote>'+esc(st.clue)+'</blockquote>'+
  (st.hint?'<div class="mx-hint">💡 馆长的进一步提示：'+esc(st.hint)+'</div>':
  '<div class="mx-hint-locked">🔒 选择错误一次后显示作者提供的提示</div>')+
  '<p class="mx-quest">下面哪一件真实公开藏品符合这条谜案？</p>'+
  '<div class="mx-options">'+(st.options||[]).map((o,i)=>
    '<button type="button" data-mystery="guess" data-id="'+o.id+'" class="mx-answer">'+
    '<b>'+('ABCD'[i])+'</b>'+sourceCard(o)+'</button>').join('')+'</div>';
 }
 return '<section class="mx-panel mx-play" id="mxPlay"><div class="mx-kicker">02 / LIVE TREASURE QUEST</div>'+
 content+
 '<p class="mx-ethics">选项来自当前真正公开的馆藏；正确答案由作者事先选定。不代表平台核实了线索的真实性。</p></section>';
}
function builder(mine,sources){
 const managed=mine.find(x=>x.id===X.manage);
 return '<section class="mx-panel mx-build" id="mxBuild"><div class="mx-kicker">03 / CURATOR ENGINE</div>'+
 '<h2>🛠 真实藏品谜案工坊</h2><p>用真实藏品编写寻宝关卡，让游客跨领域探索万物。每人最多创建 15 条路线。</p>'+
 (!log()?'<div class="mx-empty">登录后你可以亲手编排谜案。即使没有公开谜案，游客也不会看到虚构内容。</div>':
 '<form id="mxCreateForm"><label>给谜案取名<input name="title" minlength="3" maxlength="80" required placeholder="例如：穿过时间的六道石门"></label>'+
 '<label>谜案开场白（至少15字）<textarea name="premise" minlength="15" maxlength="600" required placeholder="告诉探险者他们将踏上一段怎样的藏品旅程。"></textarea></label>'+
 '<button class="mx-gold" type="submit">＋ 创建私人谜案草稿</button></form>'+
 (mine.length?'<div class="mx-my-list"><h3>我的藏宝卷轴</h3><div>'+mine.map(x=>btn('manage','<strong>'+esc(x.title)+'</strong><small>'+x.stages.length+
 ' / 6 关 · '+(x.status==='published'&&x.available?'已公开':'未公开或原来源失效')+'</small>',
 'data-id="'+x.id+'" class="'+(X.manage===x.id?'active':'')+'"')).join('')+'</div></div>':'')+
 (managed?'<div class="mx-draft"><h3>🗝 正在编辑：《'+esc(managed.title)+'》</h3>'+
 '<p class="mx-draft-note">'+esc(managed.premise)+'</p><p>状态：'+(managed.status==='published'&&managed.available?'◉ 当前公开':'○ 仅馆长可见')+
 ' · 版本 '+managed.revision+'</p>'+
 '<div class="mx-stage-manage">'+managed.stages.map((s,i)=>'<article>'+
 '<b>第 '+(i+1)+' 关 · '+esc(s.clue)+'</b>'+
 '<p>💡 '+esc(s.hint)+'</p>'+
 '<div class="mx-mini-sources">'+s.options.map(o=>'<span>'+(o.available?esc(o.exhibit.title):'🔒 已撤回')+
 (o.is_answer?' ✓ 答案':'')+'</span>').join('')+'</div>'+
 btn('remove-stage','删除这一关','data-id="'+s.id+'" class="mx-danger"')+'</article>').join('')+'</div>'+
 (managed.stages.length>=6?'<div class="mx-empty">路线已满六关，可以发布，或删掉一关后再调整。</div>':
 '<div class="mx-add-stage"><h3>✍️ 撰写第 '+(managed.stages.length+1)+' 关</h3>'+
 '<p>先搜索并挑选三至四件**真实公开藏品**，然后指定唯一正确答案。选项自动排序展示，游客不会看到答案标记。</p>'+
 '<form id="mxSearchForm" class="mx-search-row"><input id="mxSearch" name="query" value="'+esc(X.query)+'" placeholder="搜索藏品标题、类别或标签"><button type="submit">搜索公开馆藏</button></form>'+
 '<div class="mx-source-results">'+sources.map(x=>sourceCard(x,{action:'toggle-option',
 label:X.basket.some(y=>y.id===x.id)?'✓ 已选':'＋ 候选'})).join('')+
 (sources.length?'':'<div class="mx-empty">没有匹配的当前公开藏品。</div>')+'</div>'+
 '<h4>候选选项（已选 '+X.basket.length+' / 4）</h4><div class="mx-basket">'+
 (X.basket.length?X.basket.map(x=>'<label><input type="radio" name="mxRight" value="'+x.id+'" data-mystery-answer="'+x.id+'" '+
 (X.answer===x.id?'checked':'')+'><span>'+esc(x.title)+' · #'+x.id+'</span>'+
 btn('remove-option','×','data-id="'+x.id+'" aria-label="移除该候选"')+'</label>').join(''):
 '<div class="mx-empty">从上面的馆藏搜索结果中选择 3 或 4 个不同选项。</div>')+'</div>'+
 '<form id="mxStageForm"><label>谜案线索<textarea name="clue" minlength="12" maxlength="360" required placeholder="至少12字：用诗意但可推理的语言指向正确藏品。"></textarea></label>'+
 '<label>第一次选错后显示的提示<input name="hint" minlength="6" maxlength="200" required placeholder="至少6字，例如：它与云南的食物有关"></label>'+
 '<button class="mx-gold" type="submit" '+(X.basket.length<3||!X.answer?'disabled':'')+'>＋ 保存当前关卡</button></form></div>')+
 '<div class="mx-build-actions">'+btn('publish','✦ 重新核验并公开谜案','class="mx-gold" '+(managed.stages.length<2?'disabled':''))+
 btn('unpublish','暂停公开 / 重置版本','class="mx-outline"')+
 btn('delete','删除整条谜案','class="mx-danger"')+'</div>'+
 '</div>':''));
}
async function render(){
 let gallery,mine={items:[]},sources={items:[]};
 try{gallery=await api('/mysteries');
 if(log())mine=await api('/mysteries/mine');
 if(log()&&X.manage)sources=await api('/mysteries/sources?q='+encodeURIComponent(X.query));
 }catch(e){return '<section class="mx-root mx-panel"><h2>谜案馆暂时不可用</h2><p>'+esc(e.message)+'</p></section>'}
 const mineItems=mine.items||[];
 if(X.manage&&!mineItems.some(x=>x.id===X.manage)){X.manage=mineItems[0]?.id||0}
 if(!X.manage&&mineItems.length)X.manage=mineItems[0].id;
 const publicItems=gallery.items||[];
 if(!X.selected&&publicItems.length)X.selected=publicItems[0].id;
 let play=null;
 if(log()&&X.selected){
  try{play=await api('/mysteries/'+X.selected+'/play')}
  catch(e){X.alert='原始藏品或谜案已撤回，请选择另一条公开路线。';X.selected=0;}
 }
 return '<div class="mx-root"><section class="mx-hero"><div class="mx-portal"></div>'+
 '<div class="mx-kicker">WONDER ATLAS · WORLD 32 · MYSTERY EXPEDITIONS</div>'+
 '<h1>万物皆有谜，<br><em>每件藏品都能成为一把钥匙。</em></h1>'+
 '<p>跨越真实馆藏的线索游戏：作者亲手布置谜题，玩家用藏品选项破解时空路线。不是虚构投稿，也不是假装机器知道所有答案。</p>'+
 '<div class="mx-hero-badges"><span>🗝️ 跨馆寻宝</span><span>🎭 双人故事与真人策展</span><span>📜 真实来源</span><span>✨ 隐藏结局</span></div></section>'+
 (X.alert?'<p class="mx-alert">'+esc(X.alert)+'</p>':'')+
 '<section class="mx-panel"><div class="mx-top"><div><div class="mx-kicker">01 / THE PORTAL GALLERY</div><h2>🚪 进入万物谜案世界</h2>'+
 '<p>只展示拥有真实公开藏品选项、由真实馆长发布的完整寻宝路线。无内容时展示空状态。</p></div>'+
 btn('random','🎲 随机开启一道真实谜案','class="mx-gold"')+'</div>'+
 (publicItems.length?'<div class="mx-cards">'+publicItems.map(introCard).join('')+'</div>':
 '<div class="mx-empty">目前还没有可用的公开谜案。成为第一位谜案馆长，创作从真实藏品出发的跨时空寻宝之旅。</div>')+'</section>'+
 (X.selected?(log()?stagePane(play):'<section class="mx-panel"><h2>🎮 解开这条真实谜案</h2><p>游客可以浏览谜案，登录后才会开始保存你的专属解谜路线和进度。</p>'+
 btn('login','登录 / 注册，开始探险','class="mx-gold"')+'</section>'):
 '')+
 builder(mineItems,sources.items||[])+
 '<div class="mx-final-notice">⚖️ 谜案由真实馆长撰写。正确答案是作者设定的游戏规则，不代表作品之间存在得到核实的历史、科学或因果关系。原始藏品撤回后，关卡自动退出公开展出。</div></div>';
}
async function refresh(){if(window.S?.view==='mysteries'){const host=document.querySelector('#main');if(host)host.innerHTML=await render()}}
function resetBasket(){X.basket=[];X.answer=0}
document.addEventListener('change',e=>{
 const x=e.target.closest('[data-mystery-answer]');if(!x)return;
 X.answer=Number(x.dataset.mysteryAnswer);
 const submit=document.querySelector('#mxStageForm button[type=submit]');
 if(submit)submit.disabled=X.basket.length<3||!X.answer;
},true);
document.addEventListener('submit',async e=>{
 const f=e.target;if(!['mxCreateForm','mxSearchForm','mxStageForm'].includes(f.id))return;
 e.preventDefault();e.stopImmediatePropagation();
 const data=Object.fromEntries(new FormData(f).entries());
 const button=f.querySelector('[type=submit],button');if(button)button.disabled=true;
 try{
  if(f.id==='mxSearchForm'){X.query=String(data.query||'').trim();await refresh();return}
  if(f.id==='mxCreateForm'){
   const res=await api('/mysteries',{method:'POST',body:{title:data.title,premise:data.premise}});
   X.manage=res.id;resetBasket();X.alert='新谜案的私密草稿已建立。请选择真实馆藏编写至少两关，再手动公开。';
  }
  if(f.id==='mxStageForm'){
   if(X.basket.length<3||!X.basket.some(x=>x.id===X.answer))throw Error('请选择至少三个不同公开候选，并指定正确答案');
   const res=await api('/mysteries/'+X.manage+'/stages',{method:'POST',body:{
    clue:data.clue,hint:data.hint,answer_exhibit_id:X.answer,
    distractor_ids:X.basket.filter(x=>x.id!==X.answer).map(x=>x.id)}});
   resetBasket();X.alert='第 '+res.stage_count+' 关已保存为私密草稿。';
  }
  await refresh();
 }catch(err){X.alert=err.message||'操作失败';toast(X.alert);await refresh()}
 finally{if(button)button.disabled=false}
},true);
document.addEventListener('click',async e=>{
 const hit=e.target.closest('[data-mystery]');if(!hit)return;
 e.preventDefault();e.stopImmediatePropagation();
 const act=hit.dataset.mystery,id=Number(hit.dataset.id||0);
 try{
  if(act==='login'){document.querySelector('#loginTop')?.click();return}
  if(act==='open-exhibit'){await openDetail(id);return}
  if(act==='select-play'){
   X.selected=id;X.alert='';await refresh();
   document.querySelector('#mxPlay')?.scrollIntoView({behavior:'smooth',block:'start'});return;
  }
  if(act==='random'){
   const t=await api('/mysteries/random');
   if(t.id){X.selected=t.id;X.alert='🎲 开启了一个真实存在的馆长谜案！'}
   else X.alert='目前没有可用的真实谜案，不会随机制造假内容。';
   await refresh();return;
  }
  if(act==='manage'){X.manage=id;X.query='';resetBasket();X.alert='';await refresh();
   document.querySelector('#mxBuild')?.scrollIntoView({behavior:'smooth',block:'start'});return}
  if(act==='toggle-option'){
   if(X.basket.some(x=>x.id===id)){
    X.basket=X.basket.filter(x=>x.id!==id);if(X.answer===id)X.answer=0;
   }else{
    if(X.basket.length>=4)throw Error('最多选择四个选项');
    const qs=await api('/mysteries/sources?q='+encodeURIComponent(X.query));
    const item=qs.items.find(x=>x.id===id);if(!item)throw Error('这件来源当前不再公开');
    X.basket.push(item);
    if(!X.answer)X.answer=id;
   }
   await refresh();return;
  }
  if(act==='remove-option'){X.basket=X.basket.filter(x=>x.id!==id);if(X.answer===id)X.answer=X.basket[0]?.id||0;
   await refresh();return}
  if(act==='guess'){
   hit.disabled=true;
   const r=await api('/mysteries/'+X.selected+'/guess',{method:'POST',body:{exhibit_id:id}});
   X.alert=r.correct?
    (r.completed?'🏆 藏品谜案全线解锁！你已完成馆长设计的路线。':'✅ 找到真实藏品！下一站已解锁。'):
    ('🧩 还不正确：'+r.hint);
   await refresh();document.querySelector('#mxPlay')?.scrollIntoView({behavior:'smooth',block:'start'});
   return;
  }
  if(act==='restart'){
   if(!confirm('确认重置当前谜案的私人完成进度并重新挑战？'))return;
   await api('/mysteries/'+X.selected+'/restart',{method:'POST'});X.alert='已重新开始！';await refresh();return;
  }
  if(['remove-stage','unpublish','delete'].includes(act) && !confirm({
   'remove-stage':'删除本关并撤销旧版本发布？玩家进度会在新版本重新开始。',
   unpublish:'暂停公开并重置后续玩家的谜案版本？',
   delete:'永久删除整条谜案及所有玩家的私密进度？'
  }[act]))return;
  if(act==='remove-stage')await api('/mysteries/'+X.manage+'/stages/'+id,{method:'DELETE'});
  else if(act==='publish')await api('/mysteries/'+X.manage+'/publish',{method:'POST'});
  else if(act==='unpublish')await api('/mysteries/'+X.manage+'/unpublish',{method:'POST'});
  else if(act==='delete'){await api('/mysteries/'+X.manage,{method:'DELETE'});X.manage=0}
  else return;
  X.alert={publish:'✦ 谜案已通过当前公开来源检查，并开放给所有游客！',
   unpublish:'谜案已暂停公开。',delete:'谜案已删除。',
   'remove-stage':'关卡已移除，整个谜案再次进入私密草稿。'}[act];
  if(act==='publish')X.selected=X.manage;
  resetBasket();await refresh();
 }catch(err){X.alert=err.message||'操作暂未完成';toast(X.alert);await refresh()}
},true);
window.WonderMysteries={render,refresh,open(id){X.selected=Number(id)||0}};
})();