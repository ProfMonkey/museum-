/* V27 · Personal Constellation. Private nodes, explicit links, live source checks. */
(() => {
'use strict';
const C={graph:null,selected:0,query:'',results:[],busy:false,error:''};
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const btn=(action,label,attrs='')=>'<button type="button" data-ct="'+action+'" '+attrs+'>'+label+'</button>';
const edgeKinds=[['personal','个人联想'],['same_topic','主题相近'],['historical','历史脉络'],['influence','影响或启发'],['contrast','相互对照'],['materials','材料或工艺'],['curiosity','意外关联']];
const logged=()=>Boolean(window.S?.user);
async function load(){
 if(!logged()){C.graph=null;return}
 C.error='';
 try{C.graph=await api('/constellation');if(!C.graph.nodes.some(x=>x.id===C.selected))C.selected=C.graph.nodes[0]?.id||0;}
 catch(e){C.error=e.message||'无法打开个人星图';C.graph=null}
}
function hero(){
 const g=C.graph,n=g?.nodes||[],e=g?.edges||[];
 return '<section class="ct-hero"><div class="ct-orbit ct-orbit-one"></div><div class="ct-orbit ct-orbit-two"></div>'+
 '<div class="ct-eyebrow">WONDER ATLAS · V27 PERSONAL CONSTELLATION</div>'+
 '<h1>万物之间，<em>自有你的星图。</em></h1>'+
 '<p>一件收藏是一颗星，一个想法是另一颗星。你决定它们如何相连，系统只提供可解释的线索，不替你定义真相。</p>'+
 '<div class="ct-stats"><span><b>'+n.length+'</b> 颗星点</span><span><b>'+e.length+'</b> 条个人连线</span>'+
 '<span>🔒 默认仅自己可见</span></div></section>';
}
function graphMarkup(){
 const g=C.graph,nodes=g?.nodes||[],edges=g?.edges||[];
 if(!nodes.length)return '<div class="ct-empty"><div class="ct-empty-star">✧</div><h3>你的星图正在等待第一颗星</h3>'+
 '<p>可以先导入自己的藏品和收藏，也可以加入一个奇怪的想法，或者从博物馆找一件真正公开的展品。</p>'+
 '<div class="ct-actions">'+btn('import','✦ 导入我的藏品与收藏')+btn('idea-focus','＋ 创建第一颗想法星')+'</div></div>';
 const shown=nodes.slice(0,24);
 const coords={};
 const n=shown.length;
 shown.forEach((x,i)=>{
  if(i===0){coords[x.id]={x:500,y:300};return}
  const index=i-1,ring=Math.floor(index/9)+1,slots=Math.min(9,Math.max(1,n-1));
  const slot=index%9,angle=2*Math.PI*slot/Math.min(9,Math.max(1,n-1))+ring*.24;
  coords[x.id]={x:500+Math.min(380,ring*145)*Math.cos(angle),y:300+Math.min(220,ring*86)*Math.sin(angle)};
 });
 const lines=edges.filter(e=>coords[e.from_node_id]&&coords[e.to_node_id]).map(e=>{
  const a=coords[e.from_node_id],b=coords[e.to_node_id];
  return '<line x1="'+a.x+'" y1="'+a.y+'" x2="'+b.x+'" y2="'+b.y+'" class="ct-line" data-edge="'+e.id+'"/>';
 }).join('');
 const points=shown.map(x=>{
  const p=coords[x.id],selected=C.selected===x.id;
  return '<button type="button" class="ct-point '+(selected?'selected':'')+' '+(x.kind==='idea'?'idea':'exhibit')+'" '+
   'style="left:'+(p.x/10)+'%;top:'+(p.y/6)+'%" data-ct="select-node" data-id="'+x.id+'" title="'+esc(x.title)+'">'+
   '<span class="ct-point-star">'+(x.kind==='idea'?'✧':x.image_url?'◉':'✦')+'</span><span class="ct-point-title">'+esc(x.title)+'</span></button>';
 }).join('');
 return '<div class="ct-graph-head"><span>✧ YOUR PRIVATE UNIVERSE</span><small>金色实线 = 你主动保存的关联</small></div>'+
 '<div class="ct-graph-stage"><svg class="ct-lines" viewBox="0 0 1000 600" preserveAspectRatio="none" aria-hidden="true">'+lines+'</svg>'+points+
 '<div class="ct-graph-core">WONDER<br>ATLAS</div></div>'+
 (nodes.length>shown.length?'<p class="ct-muted">图中展示前 '+shown.length+' 个节点；完整节点列表在下方。</p>':'')+
 '<div class="ct-node-list">'+nodes.map(x=>btn('select-node','<span class="ct-list-symbol">'+(x.kind==='idea'?'✧':'✦')+'</span><span><b>'+esc(x.title)+'</b><small>'+esc(x.kind==='idea'?'原创想法':x.category||'万物藏品')+' · '+esc(x.origin_label)+'</small></span>', 'data-id="'+x.id+'" class="'+(C.selected===x.id?'active':'')+'"')).join('')+'</div>';
}
function selectedPanel(){
 const g=C.graph,nodes=g?.nodes||[],edges=g?.edges||[];
 const x=nodes.find(n=>n.id===C.selected);
 if(!x)return '<section class="ct-panel"><h2>节点档案</h2><p class="ct-muted">选择一颗星，查看它的档案并建立关联。</p></section>';
 const related=edges.filter(e=>e.from_node_id===x.id||e.to_node_id===x.id);
 const targets=nodes.filter(n=>n.id!==x.id);
 return '<section class="ct-panel ct-detail"><div class="ct-eyebrow">STAR FILE · #'+String(x.id).padStart(4,'0')+'</div>'+
 '<div class="ct-detail-top"><div><span class="ct-kind">'+esc(x.kind==='idea'?'原创想法':'博物馆藏品')+'</span>'+
 '<h2>'+esc(x.title)+'</h2></div>'+btn('delete-node','删除星点','data-id="'+x.id+'" class="ct-danger"')+'</div>'+
 '<p class="ct-note">'+esc(x.note||x.description||'还没有添加个人注记。')+'</p>'+
 '<div class="ct-meta"><span>'+esc(x.category||'个人想法')+'</span><span>'+esc(x.origin_label)+'</span>'+
 (x.visibility==='private'?'<span>仅自己可见</span>':'')+'</div>'+
 (x.tags?.length?'<div class="ct-tags">'+x.tags.map(t=>'<span># '+esc(t)+'</span>').join('')+'</div>':'')+
 (x.kind==='exhibit'&&x.exhibit_id?btn('open-exhibit','打开原始馆藏 ↗','data-id="'+x.exhibit_id+'" class="ct-secondary"'):'')+(x.source_unavailable?'<p class="ct-muted">原始藏品已删除、设为私密或撤回公开；你可以删除这颗失效的星点，但系统不会保留原始标题。</p>':'')+
 (x.source_unavailable?'':'<div class="ct-divider"></div><h3>编辑个人档案</h3><form id="ctEditNodeForm">'+
 (x.kind==='idea'?'<label>想法名称<input name="title" maxlength="100" required value="'+esc(x.title)+'"></label>':'<p class="ct-muted">展品标题来自原始馆藏；这里仅编辑你的私人注记。</p>')+
 '<label>个人注记<textarea name="note" maxlength="280" placeholder="写下你自己的观察、问题或联想。">'+esc(x.note||'')+'</textarea></label>'+
 '<button class="ct-secondary" type="submit">保存档案</button></form>')+
 (x.source_unavailable?'<div class="ct-divider"></div><p class="ct-muted">原始藏品已不可见，不能再从它建立新关联。你仍可删除这个占位星点和旧连线。</p>':
 '<div class="ct-divider"></div><h3>把它连接到另一颗星</h3>'+
 (!targets.filter(t=>!t.source_unavailable).length?'<p class="ct-muted">再加入至少一颗可用星点，才能建立连线。</p>':
 '<form id="ctEdgeForm"><label>连接到<select name="target_id" required>'+targets.filter(t=>!t.source_unavailable).map(t=>'<option value="'+t.id+'">'+esc(t.title)+'</option>').join('')+'</select></label>'+
 '<label>关联类型<select name="kind">'+edgeKinds.map(([k,v])=>'<option value="'+k+'">'+v+'</option>').join('')+'</select></label>'+
 '<label>为什么有关联？<textarea name="note" maxlength="280" minlength="8" required placeholder="写下你自己的理由，而不只是它们看起来相似。"></textarea></label>'+
 '<button class="ct-primary" type="submit">✧ 保存个人连线</button></form>'))+
 '<div class="ct-divider"></div><h3>与这颗星相连的路径 <span>'+related.length+'</span></h3>'+
 (related.length?'<div class="ct-edge-list">'+related.map(e=>{
  const other=nodes.find(n=>n.id===(e.from_node_id===x.id?e.to_node_id:e.from_node_id));
  return '<div class="ct-edge-row"><div><b>'+esc(other?.title||'未知节点')+'</b><small>'+esc(e.label)+' · '+esc(e.note)+'</small></div>'+
   btn('delete-edge','×','data-id="'+e.id+'" aria-label="删除这条个人关联"')+'</div>';
 }).join('')+'</div>':'<p class="ct-muted">还没有连线。你可以先建立个人判断，也可以看看下方的分类线索。</p>')+
 '</section>';
}
function suggestions(){
 const rows=C.graph?.suggestions||[];
 return '<section class="ct-panel"><div class="ct-section-head"><div><div class="ct-eyebrow">PATTERN CLUES</div>'+
 '<h2>系统发现的潜在线索</h2></div><span class="ct-count">'+rows.length+'</span></div>'+
 '<p class="ct-muted">这里只检查你星图内的公开或本人可访问藏品，按共同标签、细分类别和领域给出可解释的提示。你确认后才会变成自己的连线。</p>'+
 (rows.length?'<div class="ct-suggestions">'+rows.map(x=>{
  const a=C.graph.nodes.find(n=>n.id===x.from_node_id),b=C.graph.nodes.find(n=>n.id===x.to_node_id);
  return '<article><div class="ct-suggestion-nodes"><b>'+esc(a?.title||'')+'</b><span>↔</span><b>'+esc(b?.title||'')+'</b></div>'+
   '<p>'+esc(x.reason)+'</p><small>这是分类线索，不是因果证明。</small>'+
   btn('accept-suggestion','把它记为我的关联','data-a="'+x.from_node_id+'" data-b="'+x.to_node_id+'" data-reason="'+esc(x.reason)+'"')+'</article>';
 }).join('')+'</div>':'<div class="ct-empty-small">暂时没有新线索。加入更多不同的藏品，或手动连接两个想法。</div>')+
 '</section>';
}
function toolsPanel(){
 return '<section class="ct-panel"><div class="ct-eyebrow">GROW YOUR UNIVERSE</div><h2>增加新的星点</h2>'+
 '<div class="ct-tool-grid"><form id="ctIdeaForm"><h3>✧ 写下一个想法</h3>'+
 '<label>想法名称<input name="title" maxlength="100" required placeholder="例如：为什么人会迷恋无限？"></label>'+
 '<label>你的注记<textarea name="note" maxlength="280" placeholder="先记下来，暂时不必证明它。"></textarea></label>'+
 '<button class="ct-primary">＋ 放入星图</button></form>'+
 '<form id="ctSearchForm"><h3>⌕ 从博物馆寻找藏品</h3>'+
 '<label>搜索真实公开展品<input name="q" maxlength="60" minlength="2" required value="'+esc(C.query)+'" placeholder="恐龙、古画、黑洞、网络热梗…"></label>'+
 '<button class="ct-secondary">搜索馆藏</button>'+
 (C.results.length?'<div class="ct-search-results">'+C.results.map(x=>{
  const exists=(C.graph?.nodes||[]).some(n=>n.kind==='exhibit'&&n.exhibit_id===x.id);
  return '<article><b>'+esc(x.title)+'</b><small>'+esc(x.domain||x.category||'其他')+' · '+esc(x.owner||'')+'</small>'+
   '<div>'+btn('open-exhibit','查看','data-id="'+x.id+'"')+
   btn('add-exhibit',exists?'已在星图中':'＋ 加入星图','data-id="'+x.id+'" '+(exists?'disabled':''))+'</div></article>';
 }).join('')+'</div>':'')+'</form></div>'+
 '<div class="ct-import"><div><b>✦ 把已有的收藏带进来</b><p>仅导入你的藏品、心动收藏、自己标记参观的展品，以及已经主动启用的浏览历史。</p></div>'+
 btn('import','导入我的世界')+'</div></section>';
}
async function render(){
 if(!logged())return '<section class="ct-hero"><div class="ct-eyebrow">WONDER ATLAS · V27</div><h1>建立你的第一张<em>万物星图。</em></h1>'+
 '<p>个人星图用于保存你自己的想法与关联。登录后可以开始构建，所有节点和连线默认仅你可见。</p>'+
 '<button class="ct-primary" data-action="login">登录 / 注册，开始建造</button></section>';
 await load();
 if(!C.graph)return '<section class="ct-hero"><h1>万物星图</h1><p>'+esc(C.error)+'</p><button class="ct-secondary" data-ct="reload">重新加载</button></section>';
 return '<div class="ct-root">'+hero()+
 (C.error?'<p class="ct-error">'+esc(C.error)+'</p>':'')+
 '<div class="ct-layout"><div>'+graphMarkup()+suggestions()+'</div><div>'+selectedPanel()+toolsPanel()+'</div></div>'+
 '<p class="ct-footnote">'+esc(C.graph.notice)+'</p></div>';
}
async function refresh(){if(window.S?.view==='constellation'){const main=document.querySelector('#main');if(main)main.innerHTML=await render();}}
document.addEventListener('click',async e=>{
 const b=e.target.closest('[data-ct]');if(!b)return;
 const act=b.dataset.ct,id=Number(b.dataset.id||0);e.preventDefault();e.stopImmediatePropagation();
 try{
  if(act==='reload'){await refresh();return}
  if(act==='idea-focus'){document.querySelector('#ctIdeaForm [name=title]')?.focus();return}
  if(act==='select-node'){C.selected=id;await refresh();return}
  if(act==='import'){
   b.disabled=true;const r=await api('/constellation/import',{method:'POST'});
   toast('已导入 '+r.added+' 颗星点'+(r.skipped?'，跳过 '+r.skipped+' 件':''));
   await load();await refresh();return;
  }
  if(act==='add-exhibit'){
   await api('/constellation/nodes',{method:'POST',body:{kind:'exhibit',exhibit_id:id}});
   C.selected=(await api('/constellation')).nodes.find(x=>x.exhibit_id===id)?.id||0;
   toast('已加入你的私人星图');await refresh();return;
  }
  if(act==='open-exhibit'){if(typeof openDetail==='function')await openDetail(id);return}
  if(act==='delete-node'){
   if(!confirm('删除这颗星及其个人连线？原始藏品不会被删除。'))return;
   await api('/constellation/nodes/'+id,{method:'DELETE'});C.selected=0;toast('星点已删除');await load();await refresh();return;
  }
  if(act==='delete-edge'){
   if(!confirm('删除这条个人连线？'))return;
   await api('/constellation/edges/'+id,{method:'DELETE'});toast('个人连线已删除');await load();await refresh();return;
  }
  if(act==='accept-suggestion'){
   const note=prompt('确认把这条线索保存为你的个人关联吗？可修改理由。',b.dataset.reason+'；这是我确认保存的个人联想，尚未经过事实核验。');
   if(!note||note.trim().length<8)return;
   await api('/constellation/edges',{method:'POST',body:{from_node_id:Number(b.dataset.a),to_node_id:Number(b.dataset.b),kind:'same_topic',note:note.trim()}});
   toast('已把线索保存为你的个人关联');await load();await refresh();return;
  }
 }catch(err){toast(err.message||'操作未完成');await refresh()}
},true);
document.addEventListener('submit',async e=>{
 const form=e.target;if(!['ctIdeaForm','ctSearchForm','ctEdgeForm','ctEditNodeForm'].includes(form.id))return;
 e.preventDefault();e.stopImmediatePropagation();
 const submit=form.querySelector('[type=submit],button');if(submit)submit.disabled=true;
 const data=Object.fromEntries(new FormData(form).entries());
 try{
  if(form.id==='ctIdeaForm'){
   const r=await api('/constellation/nodes',{method:'POST',body:{kind:'idea',title:data.title,note:data.note||''}});
   C.selected=r.node.id;toast('新的想法星已加入');await load();await refresh();
  }else if(form.id==='ctSearchForm'){
   C.query=String(data.q||'').trim();
   const r=await api('/feed?q='+encodeURIComponent(C.query)+'&page=1');
   C.results=r.items||[];await refresh();
  }else if(form.id==='ctEdgeForm'){
   await api('/constellation/edges',{method:'POST',body:{from_node_id:C.selected,to_node_id:Number(data.target_id),kind:data.kind,note:data.note}});
   toast('个人连线已保存');await load();await refresh();
  }else if(form.id==='ctEditNodeForm'){
   const body={note:data.note||''};if(data.title!==undefined)body.title=data.title;
   await api('/constellation/nodes/'+C.selected,{method:'PATCH',body});
   toast('个人星图档案已更新');await load();await refresh();
  }
 }catch(err){toast(err.message||'操作未完成')}
 finally{if(submit)submit.disabled=false}
});
window.WonderConstellation={render,refresh};
})();
