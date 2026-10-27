/* V28 · 万物星图航线 — live paths over explicitly saved personal links. */
(() => {
'use strict';
const R={start:0,end:0,preview:null,selected:0,error:''};
const escapeHtml=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
const button=(name,text,extra='')=>'<button type="button" data-voyage="'+name+'" '+extra+'>'+text+'</button>';
const safeNodes=g=>(g?.nodes||[]).filter(x=>!x.source_unavailable);
function pathHtml(v){
 if(!v)return '<p class="cv-muted">选择起点与终点，查看是否能沿你亲自保存的关联找到航线。</p>';
 if(!v.connected)return '<div class="cv-unreachable">✧ 目前没有连通航线。<p>'+escapeHtml(v.reason||'你可以先在星图里增加个人连线。')+'</p></div>';
 const saved=!!v.id;
 return '<div class="cv-path" aria-label="个人星图航线">'+v.path.map((n,i)=>{
   const leg=i<v.legs.length?v.legs[i]:null;
   return '<div class="cv-stop"><div class="cv-stop-order">'+(i+1)+'</div><div class="cv-stop-body">'+
     '<div class="cv-stop-name">'+(n.kind==='idea'?'✧':'✦')+' '+escapeHtml(n.title)+'</div>'+
     '<div class="cv-muted">'+escapeHtml(n.domain||'个人想法')+'</div></div>'+
     (saved?button(n.marked?'unmark':'mark',n.marked?'✓ 已自行探索':'标记探索','data-id="'+v.id+'" data-node="'+n.node_id+'" class="'+(n.marked?'cv-done':'')+'"'):'')+
     '</div>'+
     (leg?'<div class="cv-leg"><span>↓ '+escapeHtml(leg.label)+'</span><small>'+escapeHtml(leg.note)+'</small></div>':'');
 }).join('')+'</div>'+
 '<p class="cv-muted cv-notice">'+(saved?'进度：'+v.marked_count+' / '+v.path.length+' 颗星。':'航线预览：'+v.path.length+' 颗星。')+
 '路线仅代表你保存的个人关联，不代表科学因果、可信证据或实际到访。</p>';
}
async function render(graph){
 if(!window.S?.user)return '';
 const nodes=safeNodes(graph);
 if(!nodes.some(x=>x.id===R.start))R.start=nodes[0]?.id||0;
 if(!nodes.some(x=>x.id===R.end))R.end=nodes[nodes.length-1]?.id||0;
 let list={items:[],max_routes:20};
 try{list=await api('/constellation/voyages');R.error='';}
 catch(e){R.error=e.message||'私人航线加载失败';}
 const chosen=list.items.find(x=>x.id===R.selected);
 if(!chosen && list.items.length)R.selected=list.items[0].id;
 if(!list.items.length)R.selected=0;
 const active=R.preview||list.items.find(x=>x.id===R.selected);
 const opts=(selected)=>nodes.map(x=>'<option value="'+x.id+'" '+(x.id===selected?'selected':'')+'>'+escapeHtml(x.title)+'</option>').join('');
 return '<section class="cv-root" aria-label="万物星图航线">'+
 '<div class="cv-heading"><div><div class="ct-eyebrow">WONDER ATLAS · V28 / VOYAGES</div>'+
 '<h2>🌠 万物星图航线</h2><p>从一颗星抵达另一颗星。每一站都来自真实可访问的星点，每一步都必须沿你<strong>已经保存</strong>的连线前进。</p></div>'+
 '<div class="cv-count">'+list.items.length+' / '+list.max_routes+' 条私密航线</div></div>'+
 (R.error?'<p class="cv-error">'+escapeHtml(R.error)+'</p>':'')+
 '<div class="cv-grid"><div class="cv-card"><h3>✦ 规划星际旅途</h3>'+
 (nodes.length<2?'<p class="cv-muted">星图至少需要两颗可用星点。先在上方新增展品或原创想法，再建立一条带理由的个人连线。</p>':
 '<form id="cvPreviewForm"><label>从哪颗星出发？<select name="start_node_id" required>'+opts(R.start)+'</select></label>'+
 '<label>想抵达哪颗星？<select name="end_node_id" required>'+opts(R.end)+'</select></label>'+
 '<button type="submit" class="cv-primary">✧ 计算真实连线路径</button></form>')+
 '<h3>我的私人航线</h3>'+
 (list.items.length?'<div class="cv-saved">'+list.items.map(x=>button('select',
 '<span>✧ '+escapeHtml(x.name)+'</span><small>'+(x.connected?x.path.length+' 站 · 已标记 '+x.marked_count+' 站':'路线暂不可用')+'</small>',
 'data-id="'+x.id+'" class="'+(R.selected===x.id&&!R.preview?'active':'')+'"')).join('')+'</div>':
 '<p class="cv-muted">还没有保存航线，先试着连接两颗星。</p>')+
 (R.selected&&!R.preview?button('delete','删除当前航线','data-id="'+R.selected+'" class="cv-delete"'):'')+'</div>'+
 '<div class="cv-card cv-journey"><div class="cv-journey-head"><h3>'+(R.preview?'新航线预览':active?.connected?escapeHtml(active.name):'航线观测舱')+'</h3>'+
 '<span>'+(!active?'AWAITING START':active.connected?'CONNECTED':'DISCONNECTED')+'</span></div>'+
 pathHtml(active)+
 (R.preview?.connected?'<form id="cvSaveForm" class="cv-save"><label>给航线取名<input name="name" maxlength="60" required placeholder="例如：从米线到古代贸易" /></label>'+
 '<button type="submit" class="cv-primary">✧ 保存为我的私人航线</button></form>':'')+
 '</div></div><p class="cv-footnote">🔒 默认仅本人可见 · 不保存他人馆藏旧标题 · 展品撤回后不展示旧路线 · 每次读取动态重算可达路径 · 自行打卡不等于平台核验</p></section>';
}
async function refresh(){await window.WonderConstellation?.refresh();}
document.addEventListener('submit',async e=>{
 const f=e.target;
 if(f.id!=='cvPreviewForm'&&f.id!=='cvSaveForm')return;
 e.preventDefault();e.stopImmediatePropagation();
 const data=Object.fromEntries(new FormData(f).entries());
 const submit=f.querySelector('[type=submit]');if(submit)submit.disabled=true;
 try{
  if(f.id==='cvPreviewForm'){
   R.start=Number(data.start_node_id);R.end=Number(data.end_node_id);
   R.preview=await api('/constellation/voyages/preview',{method:'POST',body:{start_node_id:R.start,end_node_id:R.end}});
   await refresh();
  }else{
   const r=await api('/constellation/voyages',{method:'POST',body:{start_node_id:R.start,end_node_id:R.end,name:String(data.name||'').trim()}});
   R.preview=null;R.selected=r.voyage.id;toast('星际航线已保存到私人星图');await refresh();
  }
 }catch(err){toast(err.message||'航线操作未完成')}
 finally{if(submit)submit.disabled=false}
},true);
document.addEventListener('click',async e=>{
 const b=e.target.closest('[data-voyage]');if(!b)return;
 e.preventDefault();e.stopImmediatePropagation();
 const act=b.dataset.voyage,id=Number(b.dataset.id||0);
 try{
  if(act==='select'){R.preview=null;R.selected=id;await refresh();return}
  if(act==='delete'){
   if(!confirm('删除这条航线和打卡记录？个人星点及连线会保留。'))return;
   await api('/constellation/voyages/'+id,{method:'DELETE'});
   R.selected=0;toast('航线已删除');await refresh();return;
  }
  if(act==='mark'||act==='unmark'){
   const node=Number(b.dataset.node),method=act==='mark'?'PUT':'DELETE';
   await api('/constellation/voyages/'+id+'/checkpoints/'+node,{method});
   toast(act==='mark'?'已自行标记探索':'已取消标记');await refresh();
  }
 }catch(err){toast(err.message||'航线操作未完成')}
},true);
window.WonderVoyages={render};
})();
