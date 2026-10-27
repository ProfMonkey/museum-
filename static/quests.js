/* V26: live museum quest bridge from authentic destiny relay results.
   Relevance is explicitly keyword-based and is never presented as AI judgment. */
(() => {
'use strict';
const Q={cardId:0,quest:null,demoResults:{},loading:false,error:''};
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const btn=(k,label,attrs='')=>'<button type="button" data-quest="'+k+'" '+attrs+'>'+label+'</button>';
const logged=()=>Boolean(window.S?.user);
async function load(cardId){
 if(!logged()||!cardId){Q.quest=null;Q.cardId=0;return;}
 try{Q.quest=await api('/adventures/'+cardId+'/quests');Q.cardId=cardId;Q.error='';}
 catch(err){Q.quest=null;Q.cardId=cardId;Q.error=err.message||'无法查看探索任务';}
}
function cards(items,stage,completedId,owner){
 return '<div class="wq-objects">'+items.map(x=>
 '<article class="wq-object"><span class="wq-kind '+x.mode+'">'+
 esc(x.mode==='source'?'🏛 原始来源':x.mode==='match'?'⌕ 文字匹配':'🧭 随意逛逛')+'</span>'+
 '<h4>'+esc(x.title)+'</h4>'+
 '<small>'+esc(x.domain||'其他')+' · '+esc(x.category||'其他')+'</small>'+
 '<p>'+esc(x.reason)+'</p>'+
 '<div class="wq-actions">'+btn('open','查看真实藏品 ↗','data-id="'+x.id+'"')+
 (owner?btn('mark',completedId===x.id?'✓ 已自行标记':'我参观过这件',
   'data-stage="'+stage+'" data-id="'+x.id+'" '+(completedId===x.id?'disabled':'')):'')+
 '</div></article>').join('')+'</div>';
}
function showGuest(stageInfo){
 const completed=stageInfo.filter(x=>x.completed&&!(!x.available&&x.exhibit_id));
 return '<section class="wq-panel"><div class="wq-heading"><div><small>EXPLORE · GUEST DEMO</small>'+
 '<h2>🗺️ 每抽中一件万物，就沿着线索再走一步</h2>'+
 '<p>游客也可以用自己刚抽中的演示词查找真实公开藏品。仅按关键词匹配，不会凭空编造相关藏品。</p></div></div>'+
 (!completed.length?'<div class="wq-empty">先抽取第一站，解锁真实馆藏探索。</div>':
 '<div class="wq-guest">'+completed.map((x,i)=>'<div class="wq-guest-step"><div class="wq-line">'+
 '<b>第 '+x.number+' 站 · '+esc(x.label)+'</b>'+
 btn('guest-search','⌕ 从博物馆寻找线索','data-stage="'+x.number+'" data-label="'+esc(x.label)+'"')+'</div>'+
 (Q.demoResults[x.number]?renderFound(Q.demoResults[x.number],x.number,false):'')+'</div>').join('')+'</div>')+
 '<p class="wq-footnote">游客探索仅用于体验；不保存在线私人任务进度。登录后可用自己的转盘创建可追踪的探索任务。</p></section>';
}
function renderFound(info,n,own,visitedId=null){
 const list=info.suggestions||info.items||[];
 if(!list.length)return '<div class="wq-empty">暂时没有可用的公开藏品，请更换关键词或先在万物博物馆探索、发布真正的发现。</div>';
 const matches=list.filter(x=>x.mode==='match').length;
 const source=list.filter(x=>x.mode==='source').length;
 return '<div class="wq-results"><div class="wq-signal">'+(source?'🏛 原始源藏品可查看 · ':'')+
 (matches?'⌕ '+matches+' 件文本匹配':'🧭 暂无文本匹配，下方仅为随意逛逛')+'</div>'+
 cards(list,n,visitedId,own)+'</div>';
}
function showOwner(stageInfo){
 const p=Q.quest;
 return '<section class="wq-panel"><div class="wq-heading"><div><small>V26 · DISCOVERY QUESTLINE</small>'+
 '<h2>🌌 从抽到的万物，走进另一座展厅</h2>'+
 '<p>命运决定起点，你来选择探索哪一件真正存在的公开藏品。参观进度只属于你。</p></div>'+
 (p?'<span class="wq-progress">已标记 '+p.visited_count+' / '+p.stages.filter(x=>x.ready).length+' 站</span>':'')+
 '</div>'+
 (Q.error?'<p class="wq-error">'+esc(Q.error)+'</p>':'')+
 (!p?'<div class="wq-empty">选择一张属于自己的奇遇卡，才可以开始标记参观。</div>':
 '<div class="wq-stages">'+p.stages.map(x=>'<article class="wq-stage">'+
 '<div class="wq-line"><div><small>QUEST '+String(x.number).padStart(2,'0')+' · '+
 esc(stageInfo.find(a=>a.number===x.number)?.topic_label||'奇遇站点')+'</small>'+
 '<h3>'+esc(!x.ready?'尚未抽取':x.source_unavailable?'源藏品已经撤回':x.label)+'</h3></div>'+
 '<span class="wq-status">'+(x.visited?'✓ 已自行参观':x.ready?'✦ 等待探索':'🔒 尚未解锁')+'</span></div>'+
 (x.visited?'<div class="wq-visited"><span>你标记参观过：'+esc(x.visited_title)+'</span>'+
 btn('undo','↻ 取消标记','data-stage="'+x.number+'"')+'</div>':'')+
 (x.visit_withdrawn?'<p class="wq-footnote">之前标记的藏品已经删除或撤回，标题已隐藏，任务现在不计入完成。</p>':'')+
 (!x.ready?'<p class="wq-footnote">去上方抽取这一站，然后自动解锁探索入口。</p>':
 x.source_unavailable?'<p class="wq-footnote">来源不再公开，不能从私密信息衍生新的推荐。</p>':
 renderFound(x,x.number,true,x.visited_exhibit_id))+
 '</article>').join('')+'</div>')+
 '<p class="wq-footnote">匹配依据：公开藏品标题、简介、标签的文本重合，未使用 AI，也不保证事实准确或内容真实相关；“随意逛逛”仅为拓展，不是相关匹配。参观完成为你自行标记，不代表平台核实了实际到访。</p>')+
 '</section>';
}
async function render(stageInfo,cardId){
 await load(cardId);
 return logged()?showOwner(stageInfo):showGuest(stageInfo);
}
async function rerender(){
 if(window.S?.view!=='adventure')return;
 const main=document.querySelector('#main');
 if(main)main.innerHTML=await window.WonderAdventure.render();
}
document.addEventListener('click',async e=>{
 const b=e.target.closest('[data-quest]');if(!b)return;
 e.preventDefault();e.stopImmediatePropagation();
 const action=b.dataset.quest;
 const id=Number(b.dataset.id||0),number=Number(b.dataset.stage||0);
 try{
  if(action==='open'){
   if(typeof openDetail==='function')await openDetail(id);
   return;
  }
  if(action==='guest-search'){
   if(Q.loading)return;
   Q.loading=true;
   const term=b.dataset.label;
   const info=await api('/discovery/quests/explore?q='+encodeURIComponent(term));
   Q.demoResults[number]=info;
  }else if(action==='mark'){
   if(!window.confirm('标记为“我参观过”：这是你自己的记录，平台不会验证是否真实参观。确认？'))return;
   await api('/adventures/'+Q.cardId+'/quests/'+number+'/visit',
       {method:'POST',body:{exhibit_id:id}});
  }else if(action==='undo'){
   await api('/adventures/'+Q.cardId+'/quests/'+number+'/visit',{method:'DELETE'});
  }
  await rerender();
 }catch(err){
  Q.error=err.message||'无法完成探索';
  if(typeof toast==='function')toast(Q.error);
  await rerender();
 }finally{Q.loading=false;}
},true);
window.WonderQuests={render};
})();
