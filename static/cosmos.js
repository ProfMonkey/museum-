/* V12 Cosmos: one exploratory page, three coordinated views, no external rendering dependencies. */
(() => {
  'use strict';
  const C = {tab:'river', era:'亿年前', series:'全部', domain:'全部', scope:'public', river:null,
    focusId:0, relations:null, world:null, worldFilter:'全部', loading:false, message:''};
  const esc = x => String(x ?? '').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const intro = `<div class="cs-hero"><div class="cs-eyebrow">WONDER ATLAS · FROM DEEP TIME TO NOW</div><h1>万物有来处，<br><em>世界有回响。</em></h1><p>横跨亿万年的时间长河，追溯每条关联的依据；再看看你亲手建立的收藏世界。</p><div class="cs-orbit" aria-hidden="true"><span>✧</span></div></div>`;
  const options = (values,current) => values.map(x=>`<option value="${esc(x)}" ${x===current?'selected':''}>${esc(x)}</option>`).join('');
  const numeral = n => String(n).padStart(2,'0');
  const featureKeys={river:'world_time',links:'evidence_explore',world:'personal_world_map'};
  const track=(type='open')=>{try{window.WonderAnalytics?.track(featureKeys[C.tab],type);}catch(_){}};
  const itemCard = n => `<button type="button" class="cs-item" data-cosmos="detail" data-id="${n.id}"><div class="cs-thumb">${n.image_url?`<img src="${esc(n.image_url)}" alt="" loading="lazy" onerror="this.remove()">`:'✦'}</div><div class="cs-copy"><small>${esc(n.series||'民间奇趣')} · ${esc(n.domain||'其他')}</small><strong>${esc(n.title)}</strong><span>${esc(n.time_basis||'不详')}${n.time_note?' · '+esc(n.time_note):''}</span></div><b>↗</b></button>`;
  const tabs=()=>`<div class="cs-tabs" role="tablist" aria-label="探索模式">${[['river','⏳ 世界时间长河'],['links','⌁ 证据关联探索'],['world','✦ 我的世界星图']].map(([id,label])=>`<button type="button" data-cosmos="tab" data-tab="${id}" class="${C.tab===id?'current':''}" role="tab" aria-selected="${C.tab===id}">${label}</button>`).join('')}</div>`;
  const miniNotice = str => `<p class="cs-notice">${esc(str)}</p>`;
  async function loadRiver(){
    const p=new URLSearchParams({series:C.series,domain:C.domain,scope:C.scope});
    C.river=await api('/cosmos/eras?'+p.toString());
    if(window.WonderCurator)await WonderCurator.loadMuseum();
    if(!C.river.eras.some(x=>x.id===C.era))C.era='亿年前';
  }
  async function loadRelations(){
    if(!C.focusId){
      const publicItems=await api('/feed?page=1');
      C.focusId=publicItems.items?.[0]?.id||0;
    }
    C.relations=C.focusId?await api('/cosmos/relations/'+C.focusId):null;
  }
  async function loadWorld(){C.world = window.S?.user?await api('/cosmos/me/map'):null;
    if(window.S?.user&&window.WonderCurator)await WonderCurator.loadQuality();}
  async function refresh(){
    C.loading=true;C.message='';
    try{
      if(C.tab==='river')await loadRiver();
      else if(C.tab==='links')await loadRelations();
      else await loadWorld();
    }catch(e){C.message=e.message||'数据暂时无法获取';}
    finally{C.loading=false;}
  }
  function renderRiver(){
    const data=C.river;
    if(!data)return `<section class="cs-panel">${C.message?miniNotice(C.message):'<p>载入世界的时间轴…</p>'}</section>`;
    const eras=data.eras||[];
    const active=eras.find(x=>x.id===C.era)||eras[0];
    const dims = Object.keys(window.WonderTaxonomy?.groups||{});
    return `<section class="cs-control"><div class="cs-control-title"><b>从过去到现在</b><small>按领域与年代交叉探索 · ${data.total} 件符合条件的实际展品</small></div><div class="cs-selectrow"><label>馆藏系列<select data-cosmos-filter="series">${options(['全部','藏品系列','民间奇趣'],C.series)}</select></label><label>主要领域<select data-cosmos-filter="domain">${options(['全部',...dims],C.domain)}</select></label><label>查看范围<select data-cosmos-filter="scope">${options(['public','mine'],C.scope)}</select></label></div></section>
      <div class="cs-river-view"><aside class="cs-era-rail" aria-label="世界年代导航">${eras.map((e,i)=>`<button type="button" class="cs-era ${active.id===e.id?'selected':''}" data-cosmos="era" data-era="${esc(e.id)}"><span>${numeral(i+1)}</span><div><b>${esc(e.id)}</b><small>${esc(e.title)}</small></div><em>${e.count}</em></button>`).join('')}</aside><section class="cs-era-content"><header><div class="cs-eyebrow">TIME STATION / ${numeral(eras.indexOf(active)+1)}</div><h2>${esc(active.id)}</h2><p>${esc(active.intro)}</p></header><div class="cs-era-stats"><div><b>${active.count}</b><small>这个时间段的可见展品</small></div><div><b>${active.items.length}</b><small>本页展示</small></div></div>${active.items.length?`<div class="cs-item-list">${active.items.map(itemCard).join('')}</div>`:`<div class="cs-empty"><span>◌</span><strong>这一段时间还没有符合条件的展品</strong><p>这里不会凭空制造古董或历史事件。可以从世界名馆寻找作品收藏，或上传自己的发现。</p><button type="button" class="ghost" data-cosmos="museums">去世界名馆探索 ↗</button></div>`}</section></div>
      ${window.WonderCurator?.renderEra(active.id)||''}${miniNotice(data.notice)}<small class="cs-footnote">公共时间长河只展示用户公开的实际展品；选择“mine”只展示自己的展品，不会公开私人记录。每个时代最多展示 20 件最近上传的匹配样本，统计数量来自数据库全部匹配记录。</small>`;
  }
  function evidenceScore(n){return `<span class="cs-score">匹配 ${n.score} 分</span>`;}
  function renderLinks(){
    const r=C.relations;
    return `<section class="cs-control"><div><b>比关键词更清楚的关联</b><small>按共同标签、领域、时间和来源网站解释；不是自动核实的历史因果。</small></div><form id="cs-find"><label class="cs-inline">展品编号<input type="number" min="1" name="id" value="${C.focusId||''}" placeholder="输入展品编号" required></label><button type="submit" class="primary">追溯关联 ↗</button></form></section>
      ${r?`<section class="cs-focus"><div class="cs-eyebrow">FOCAL OBJECT / ${numeral(r.focus.id)}</div><h2>${esc(r.focus.title)}</h2><p>${esc(r.focus.domain)} · ${esc(r.focus.category)} · ${esc(r.focus.time_bucket)}</p><div class="cs-focus-actions"><button class="ghost" type="button" data-cosmos="detail" data-id="${r.focus.id}">查看作品原档 ↗</button><button class="ghost" type="button" data-cosmos="v11" data-id="${r.focus.id}">打开原有关系图 ⌁</button></div></section>
      <div class="cs-grid-columns"><section class="cs-panel"><div class="cs-eyebrow">METADATA EVIDENCE</div><h3>系统发现的相似线索 <span>${r.recommendations.length}</span></h3><p class="cs-muted">匹配分数衡量元数据重合，不表示真伪、因果强弱或可信度。</p>${r.recommendations.length?r.recommendations.map(n=>`<article class="cs-relation"><div class="cs-relhead"><strong>${esc(n.target.title)}</strong>${evidenceScore(n)}</div><div class="cs-evidence">${n.evidence.map(e=>`<span>${esc(e.label)}</span>`).join('')}</div><button type="button" data-cosmos="focus" data-id="${n.target.id}">从这件展品继续探索 ↗</button></article>`).join(''):'<div class="cs-empty">暂无足以解释的推荐；这比编造联系更可靠。</div>'}</section>
      <section class="cs-panel"><div class="cs-eyebrow">CURATOR CLAIMS</div><h3>馆长手动关联 <span>${r.manual.length}</span></h3><p class="cs-muted">由投稿馆长提出，仍需要独立证据核实。</p>${r.manual.length?r.manual.map(n=>`<article class="cs-relation"><div class="cs-relhead"><strong>${esc(n.title)}</strong><small>用户：${esc(n.author)}</small></div><p>「${esc(n.explanation)}」</p><button type="button" data-cosmos="focus" data-id="${n.target_id}">查看关联目标 ↗</button></article>`).join(''):'<div class="cs-empty">暂无馆长添加的关联。</div>'}</section></div>${miniNotice(r.notice)}`:`<section class="cs-empty"><span>⌁</span><b>还没有可以探索的起点</b><p>先公开一件藏品，或在发现广场打开任意展品，从它出发探索。</p></section>`}`;
  }
  function worldSvg(w){
    const groups=w.domains||[], shownGroups=C.worldFilter==='全部'?groups:groups.filter(x=>x.id===C.worldFilter);
    const ids=new Set(shownGroups.map(x=>x.id));
    const nodes=(w.nodes||[]).filter(n=>ids.has(n.domain));
    const centers = new Map(shownGroups.map((g,i)=>{const angle=i*Math.PI*2/Math.max(shownGroups.length,1)-Math.PI/2;
      return [g.id,{x:510+315*Math.cos(angle),y:295+188*Math.sin(angle),angle}];}));
    const coords=new Map();
    for(const g of shownGroups){const subset=nodes.filter(n=>n.domain===g.id);const c=centers.get(g.id);
      subset.forEach((n,i)=>{const rad=45+Math.floor(i/8)*26, angle=i*Math.PI*2/Math.min(subset.length,8);
        coords.set(n.id,{x:c.x+Math.cos(angle)*rad,y:c.y+Math.sin(angle)*Math.min(rad,70)});});}
    const edges=(w.edges||[]).filter(e=>coords.has(e.from)&&coords.has(e.to)).map(e=>{const a=coords.get(e.from),b=coords.get(e.to);return `<path d="M ${a.x.toFixed(1)} ${a.y.toFixed(1)} Q 510 295 ${b.x.toFixed(1)} ${b.y.toFixed(1)}" fill="none" stroke="#e4bd69" opacity=".5" stroke-width="1.7"/>`;}).join('');
    const halos=shownGroups.map(g=>{const c=centers.get(g.id);return `<g><circle cx="${c.x}" cy="${c.y}" r="${Math.max(48,Math.min(90,38+g.count*3))}" fill="#bc964411" stroke="#bc96444e"/><text x="${c.x}" y="${c.y-30}" class="cs-svg-domain" text-anchor="middle">${esc(g.id)}</text><text x="${c.x}" y="${c.y-16}" text-anchor="middle" class="cs-svg-count">${g.count} 件</text></g>`;}).join('');
    const star=nodes.map(n=>{const c=coords.get(n.id);return `<g role="button" tabindex="0" aria-label="查看 ${esc(n.title)}" data-cosmos="detail" data-id="${n.id}"><circle cx="${c.x.toFixed(2)}" cy="${c.y.toFixed(2)}" r="6" fill="#f2cf88" stroke="#fff2c5" stroke-width=".8"/><title>${esc(n.title)}</title></g>`;}).join('');
    return `<svg viewBox="0 0 1020 580" class="cs-star-map" role="img" aria-label="私人藏品按领域分布的星图，点按星点查看原展品"><defs><radialGradient id="csNebula"><stop stop-color="#20304b"/><stop offset="1" stop-color="#090d16"/></radialGradient></defs><rect width="1020" height="580" rx="18" fill="url(#csNebula)"/><circle cx="510" cy="295" r="250" fill="none" stroke="#c9b17a2e" stroke-dasharray="5 7"/>${halos}${edges}${star}<circle cx="510" cy="295" r="9" fill="#c5a466"/></svg>`;
  }
  function renderWorld(){const w=C.world;
    if(!window.S?.user)return `<div class="cs-empty"><span>✦</span><h2>你的世界，还在等待创建</h2><p>登录后可查看个人收藏的领域星图，数据不会自动公开。</p><button data-cosmos="login" type="button" class="primary">登录 / 注册</button></div>`;
    if(!w)return `<div class="cs-empty">${esc(C.message||'正在读取个人收藏世界…')}</div>`;
    const groups=w.domains||[];
    return `<section class="cs-world-summary"><div><div class="cs-eyebrow">PRIVATE COLLECTION CONSTELLATION</div><h2>你的世界星图</h2><p>每一颗星代表你真正收藏的一件展品。线条仅表示你本人建立的关联，不会因为属于同一领域就虚构历史联系。</p></div><div class="cs-world-stat"><b>${w.total}</b><span>总藏品</span></div><div class="cs-world-stat"><b>${groups.length}</b><span>探索领域</span></div><div class="cs-world-stat"><b>${w.edges.length}</b><span>手动关联</span></div></section>
      <section class="cs-panel"><header class="cs-map-toolbar"><label>突出领域<select data-cosmos-filter="worldFilter">${options(['全部',...groups.map(g=>g.id)],C.worldFilter)}</select></label><small>点击星点查看藏品 · 放大后更加清晰</small></header>${w.nodes.length?worldSvg(w):`<div class="cs-empty"><span>✦</span><b>还没有藏品星星</b><p>从世界名馆收藏一件作品，或上传第一件私人展品。</p></div>`}</section><section class="cs-panel"><h3>探索轨迹：兴趣领域排行</h3><div class="cs-domain-bars">${groups.length?groups.map(g=>`<button type="button" data-cosmos="worldDomain" data-domain="${esc(g.id)}"><span>${esc(g.id)}</span><b style="width:${Math.max(8,g.count/Math.max(groups[0].count,1)*100).toFixed(1)}%"></b><small>${g.count} 件</small></button>`).join(''):'<p>尚无可分析的数据。</p>'}</div></section>${w.total>w.visible_count?miniNotice(`目前仅展示最近 ${w.visible_count} 件，全部收藏数 ${w.total} 件，避免星图在普通设备上卡顿。`):''}${miniNotice(w.notice)}${window.WonderCurator?.renderQuality()||''}`;
  }
  async function render(){await refresh();return `<div class="cs-root">${intro}${tabs()}${C.message?miniNotice(C.message):''}${C.tab==='river'?renderRiver():C.tab==='links'?renderLinks():renderWorld()}</div>`;}
  async function rerender(){if(window.S?.view!=='cosmos')return;document.querySelector('#main').innerHTML=await render();}
  function focus(id){const n=Number(id);if(!Number.isInteger(n)||n<1)return;C.tab='links';C.focusId=n;C.relations=null;track('open');navigate('cosmos');}
  document.addEventListener('click',async e=>{
    const el=e.target.closest('[data-cosmos]');if(!el)return;
    const op=el.dataset.cosmos;
    e.preventDefault();e.stopPropagation();
    try{
      if(op==='tab'){C.tab=el.dataset.tab;track('open');await rerender();}
      else if(op==='era'){C.era=el.dataset.era;const main=document.querySelector('#main');if(main&&C.river)main.innerHTML=`<div class="cs-root">${intro}${tabs()}${renderRiver()}</div>`;}
      else if(op==='focus'){C.focusId=Number(el.dataset.id);track('search');await rerender();}
      else if(op==='worldDomain'){C.worldFilter=el.dataset.domain;await rerender();}
      else if(op==='detail')await openDetail(Number(el.dataset.id));
      else if(op==='v11')await window.WonderConnections?.open(Number(el.dataset.id));
      else if(op==='museums')await navigate('world-museums');
      else if(op==='login'){if(typeof openAuth==='function')openAuth('login');}
    }catch(err){toast(err.message||'操作失败');}
  },true);
  document.addEventListener('change',async e=>{
    const f=e.target.dataset.cosmosFilter;
    if(!f)return;
    if(f==='series')C.series=e.target.value;
    else if(f==='domain')C.domain=e.target.value;
    else if(f==='scope')C.scope=e.target.value;
    else if(f==='worldFilter')C.worldFilter=e.target.value;
    await rerender();
  },true);
  document.addEventListener('submit',async e=>{
    if(e.target.id!=='cs-find')return;
    e.preventDefault();e.stopImmediatePropagation();
    C.focusId=Number(new FormData(e.target).get('id'));track('search');await rerender();
  },true);
  document.addEventListener('keydown',e=>{
    const btn=e.target.closest('.cs-star-map [data-cosmos="detail"]');
    if(btn && (e.key==='Enter'||e.key===' ')){e.preventDefault();btn.dispatchEvent(new MouseEvent('click',{bubbles:true}));}
  });
  window.WonderCosmos={render,focus,setTab(tab){C.tab=tab;}};
})();