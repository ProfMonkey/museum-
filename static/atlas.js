/* Wonder Atlas V7 — one journey screen, replacing the old separate random page.
   No invented routes: backend explains every edge and only returns public items. */
(()=>{
 'use strict';
 const X={all:[],featured:[],saved:[],current:null,start:'work:met:24671',target:'topic:chips',
     chosen:0,search:'',activeTab:'theatre',loaded:false};
 const e=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const tag={work:'世界名馆',post:'社区藏品',topic:'策展主题'};
 const glyph={work:'♛',post:'✦',topic:'✧'};
 const track=(action)=>{try{window.WonderAnalytics?.track('atlas_explore',action)}catch(_){}};
 const nodeById=id=>X.all.find(x=>x.id===id);
 const opts=(current)=>{
   let list=X.all;
   if(X.search){let q=X.search.toLowerCase();list=list.filter(x=>[x.title,x.category,x.owner,x.description].some(v=>String(v||'').toLowerCase().includes(q))||x.id===current)}
   return ['topic','work','post'].map(kind=>{
     const subset=list.filter(x=>x.kind===kind);
     if(!subset.length)return '';
     return `<optgroup label="${tag[kind]}">${subset.map(x=>`<option value="${e(x.id)}" ${x.id===current?'selected':''}>${e(x.title)} · ${e(x.category)}</option>`).join('')}</optgroup>`
   }).join('')
 };
 const navCard=(x,index)=>`<button type="button" class="ax-stop ${index===X.chosen?'active':''}" data-atlas="focus" data-step="${index}" aria-current="${index===X.chosen?'step':'false'}">
   <span class="ax-stop-icon">${glyph[x.kind]||'✧'}</span><span class="ax-stop-body"><small>${e(tag[x.kind])} · ${e(x.category)}</small><strong>${e(x.title)}</strong></span><span class="ax-stop-num">${String(index+1).padStart(2,'0')}</span></button>`;
 const nodeBlock=(n)=>`<div class="ax-object-view">${n.image_url?`<img src="${e(n.image_url)}" alt="${e(n.title)}" loading="lazy" referrerpolicy="no-referrer">`:`<div class="ax-object-glyph">${glyph[n.kind]||'✧'}</div>`}</div>
 <div class="ax-object-copy"><div class="eyebrow">${e(tag[n.kind])} · ${e(n.category)}</div><h2>${e(n.title)}</h2><p>${e(n.description||'发现一段新的探索方向。')}</p><p class="ax-source">${e(n.owner||'万物策展')}</p><div class="ax-object-actions">${n.kind==='post'?`<button class="primary" data-atlas="post" data-post="${n.post_id}">查看原作者展品 ↗</button>`:
 `<a class="ghost" href="${e(n.source_url)}" target="_blank" rel="noopener noreferrer">${n.kind==='work'?'原馆档案':'官方延伸阅读'} ↗</a>`}</div></div>`;
 const pathHtml=()=>{
    const data=X.current;if(!data)return `<div class="ax-placeholder">从上面的主题路线开始，或者选择任意起点与终点。只有可解释的关联才会成为路线。</div>`;
    if(!data.found)return `<div class="ax-not-found"><span>∅</span><h3>暂时无法连接这两件事物</h3><p>${e(data.message||'没有找到符合条件的关联。')}</p><small>不会为了制造惊喜而编造一条路线。你可以换一个终点或增加允许步数。</small></div>`;
    const step=Math.max(0,Math.min(data.items.length-1,X.chosen));X.chosen=step;
    const n=data.items[step];const prev=data.steps[step-1],next=data.steps[step];
    return `<div class="ax-route-top"><div><div class="eyebrow">DISCOVERED PATH · ${data.hops} HOPS</div><h2>你的万物旅程</h2><p>从 ${e(data.items[0].title)} 到 ${e(data.items.at(-1).title)}，沿真实存在的节点继续探索。</p></div>
     <div class="ax-route-actions"><button class="ghost" data-atlas="share">↗ 分享路线</button><button class="primary" data-atlas="save">☆ 收入路线收藏册</button></div></div>
     <div class="ax-path-rail">${data.items.map(navCard).join('')}</div>
     <div class="ax-stage"><div class="ax-stage-main">${nodeBlock(n)}<div class="ax-stage-footer"><button class="ghost" data-atlas="prev" ${!step?'disabled':''}>← 上一站</button><span>${step+1} / ${data.items.length}</span><button class="primary" data-atlas="next" ${step===data.items.length-1?'disabled':''}>下一站 →</button></div></div>
     <aside class="ax-explain"><small>WHY THIS CONNECTION?</small><h3>为什么会来到这里？</h3>${prev?`<div class="ax-rule"><b>来自上一站</b><span class="ax-relation">${e(prev.kind)}</span><p>${e(prev.reason)}</p></div>`:'<p>这是旅程起点。选择下一站，看看策展主题与真实馆藏如何产生联系。</p>'}
     ${next?`<div class="ax-rule"><b>通往下一站</b><span class="ax-relation">${e(next.kind)}</span><p>${e(next.reason)}</p></div>`:'<p>已抵达本次目的地。你可以收藏这条旅程，或者重新出发。</p>'}
     <p class="ax-caveat">注：策展关联表示主题延伸；关键词建议未经人工核实；仅“人工确认”由展品馆主提交。它们不是因果关系或科学证明。</p></aside></div>`;
 };
 async function load(){
    if(X.loaded)return;
    const [n,f]=await Promise.all([api('/atlas/nodes'),api('/atlas/featured')]);
    X.all=n.items||[];X.featured=f.items||[];X.loaded=true;
    if(!nodeById(X.start))X.start=X.all[0]?.id||'';
    if(!nodeById(X.target))X.target=X.all.find(x=>x.id!==X.start)?.id||'';
    if(X.featured.length){const first=X.featured[0];X.start=first.start;X.target=first.target;X.current={found:true,...first};}
    if(window.S?.user)await refreshSaved();
 }
 async function refreshSaved(){try{X.saved=(await api('/atlas/routes')).items||[]}catch{X.saved=[]}}
 const presets=()=>X.featured.map((r,i)=>`<button type="button" class="ax-preset" data-atlas="preset" data-n="${i}"><small>ROAD ${String(i+1).padStart(2,'0')} · ${r.hops} 次跳转</small><strong>${e(r.title)}</strong><span>${e(r.items[0]?.title)} → ${e(r.items.at(-1)?.title)}　↗</span></button>`).join('');
 const savedHtml=()=>!window.S?.user?'<p class="muted">登录后可以把路线保存到账号，随时重走。</p>':
     X.saved.length?X.saved.map(r=>`<div class="ax-saved-row"><div><strong>${e(r.title)}</strong><small>${r.available?`${r.hops} 次跳转 · ${e(r.created_at?.slice(0,10))}`:'展品已撤回或关联已经失效'}</small></div><div><button class="ghost" data-atlas="replay" data-id="${r.id}" ${!r.available?'disabled':''}>重走</button><button class="ghost" data-atlas="remove" data-id="${r.id}">删除</button></div></div>`).join(''):'<p class="muted">还没有收藏过路线。找到一条旅程后，点击「收入路线收藏册」。</p>';
 async function render(){await load();return `<section class="ax-hero"><div><div class="eyebrow">WONDER ATLAS · EXPLORATION ENGINE V7</div><h1>万物之间，<br><span>皆有奇妙联系。</span></h1><p>从古董珠宝走到半导体，从千年古画走到人工智能。每次转弯，都告诉你为什么有关联。</p><div class="ax-hero-labels"><span>世界名馆</span><span>公开社区</span><span>跨界策展</span><span>有据可查</span></div></div><div class="ax-hero-art"><div class="ax-planet"></div><b>PAST</b><i>→</i><strong>FUTURE</strong></div></section>
   <div class="ax-section-heading"><div class="eyebrow">CURATED CROSS-DOMAIN ROUTES</div><h2>先走一条奇妙的路</h2><p>四条现成主题路线，所有节点都来自实际馆藏或明确标注的策展主题。</p></div><div class="ax-presets">${presets()||'<p>主题路线正在整理中。</p>'}</div>
   <div class="ax-trip-planner"><div><div class="eyebrow">PLAN A JOURNEY</div><h2>自行寻找两件东西之间的路</h2></div>
   <div class="ax-planner-controls"><label>快速筛选路线节点<input id="axFilter" type="search" maxlength="80" value="${e(X.search)}" placeholder="按名称、作者或领域过滤"></label>
   <label>从这里出发<select id="axStart">${opts(X.start)}</select></label><label>想去的地方<select id="axTarget">${opts(X.target)}</select></label>
   <label>最多跳转<select id="axHops"><option value="4">4 站</option><option value="6" selected>6 站</option><option value="8">8 站</option></select></label></div>
   <div class="ax-planner-buttons"><button class="primary" data-atlas="plan">连接这两件事物 ↗</button><button class="ghost" data-atlas="random">✧ 随机起点</button><span>访问权限：只使用公开展品；私密投稿不会进入探索。</span></div></div>
   <section id="axResult" class="ax-result">${pathHtml()}</section>
   <section class="ax-collection"><div><div class="eyebrow">MY SAVED JOURNEYS</div><h2>我的路线收藏册</h2></div><div id="axSaved">${savedHtml()}</div></section>
   <p class="ax-disclaimer">关联说明：本模块不是知识证明引擎。人工策展路径提供跨领域灵感；自动标签匹配仅是推荐候选；跨馆艺术品仍归原机构所有，点击可查看来源。馆藏图片可能受原馆网络限制。</p>`}
 const update=()=>{if(window.S?.view!=='journey')return;const box=document.querySelector('#axResult');if(box)box.innerHTML=pathHtml();const saved=document.querySelector('#axSaved');if(saved)saved.innerHTML=savedHtml()};
 async function plan(){const start=X.start,target=X.target;if(!start||!target)return toast('请选择两个节点');
   X.current=await api('/atlas/path?'+new URLSearchParams({start,target,max_hops:document.querySelector('#axHops')?.value||'6'}).toString());
   X.chosen=0;track('complete');update();document.querySelector('#axResult')?.scrollIntoView({behavior:'smooth',block:'start'});
 }
 document.addEventListener('input',ev=>{if(ev.target.id==='axFilter'){
    X.search=ev.target.value;const a=document.querySelector('#axStart'),b=document.querySelector('#axTarget');
    if(a){a.innerHTML=opts(X.start);a.value=X.start;}if(b){b.innerHTML=opts(X.target);b.value=X.target;}
 }});
 document.addEventListener('change',ev=>{if(ev.target.id==='axStart')X.start=ev.target.value;if(ev.target.id==='axTarget')X.target=ev.target.value});
 document.addEventListener('click',async ev=>{
    const b=ev.target.closest('[data-atlas]');if(!b)return;ev.preventDefault();
    try{
       const action=b.dataset.atlas;
       if(action==='preset'){const r=X.featured[Number(b.dataset.n)];if(!r)return;X.start=r.start;X.target=r.target;X.current={found:true,...r};X.chosen=0;update();const a=document.querySelector('#axStart'),z=document.querySelector('#axTarget');if(a)a.value=X.start;if(z)z.value=X.target;document.querySelector('#axResult')?.scrollIntoView({behavior:'smooth',block:'start'});track('complete')}
       else if(action==='plan')await plan();
       else if(action==='random'){const choices=X.all.filter(x=>x.id!==X.target);if(!choices.length)return;X.start=choices[Math.floor(Math.random()*choices.length)].id;document.querySelector('#axStart').value=X.start;toast('换好了一个随机起点，点击「连接」试试！')}
       else if(action==='focus'){X.chosen=Number(b.dataset.step)||0;update()}
       else if(action==='prev'){X.chosen--;update()}
       else if(action==='next'){X.chosen++;update();track('view')}
       else if(action==='post')await openDetail(Number(b.dataset.post));
       else if(action==='save'){
           if(!window.S?.user){mustLogin();return}
           if(!X.current?.found)return;
           const title=window.prompt('给这段旅程起个名字',`${X.current.items[0].title} → ${X.current.items.at(-1).title}`);
           if(title===null)return;
           if(!title.trim()||title.length>80)return toast('名称应为 1～80 个字符');
           await api('/atlas/routes',{method:'POST',body:{title:title.trim(),node_ids:X.current.node_ids}});await refreshSaved();update();track('save');toast('路线已保存在你的账号里。')
       }
       else if(action==='replay'){const r=X.saved.find(x=>x.id===Number(b.dataset.id));if(!r?.available)return;X.current={found:true,...r};X.chosen=0;update();document.querySelector('#axResult')?.scrollIntoView({behavior:'smooth',block:'start'})}
       else if(action==='remove'){if(!window.confirm('从路线收藏册删除这条旅程？'))return;await api('/atlas/routes/'+b.dataset.id,{method:'DELETE'});await refreshSaved();update()}
       else if(action==='share'){
          if(!X.current?.found)return;const u=new URL(window.location.href);u.searchParams.set('atlas_start',X.current.node_ids[0]);u.searchParams.set('atlas_target',X.current.node_ids.at(-1));
          try{await navigator.clipboard.writeText(u.toString());toast('公开路线链接已复制')}catch{window.prompt('复制此公开路线链接',u.toString())}
       }
    }catch(err){toast(err.message||'操作未完成')}
 });
 // URL with atlas_start, atlas_target is processed only once after user navigates to the journey page.
 async function activateShared(){const query=new URLSearchParams(location.search);const a=query.get('atlas_start'),b=query.get('atlas_target');if(!a||!b||a.length>100||b.length>100)return;
    try{await load();if(!nodeById(a)||!nodeById(b))return;X.start=a;X.target=b;X.current=await api('/atlas/path?'+new URLSearchParams({start:a,target:b,max_hops:'8'}));X.chosen=0;track('complete')}catch{}
 }
 async function startFrom(nodeId){await load();if(!nodeById(nodeId))return false;X.start=nodeId;const hints=await api('/atlas/recommend?node_id='+encodeURIComponent(nodeId));const candidates=(hints.items||[]).map(x=>x.node.id).filter(x=>x!==nodeId);X.target=candidates.find(x=>x.startsWith('topic:'))||candidates[0]||X.target;X.current=null;X.chosen=0;X.search='';return true;}
 window.WonderAtlas={render,activateShared,startFrom};
})();