/* V14 Official museum source search: read-only results, explicit rights, private bookmarking. */
window.WonderSources = (() => {
  'use strict';
  const E = x => String(x ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
  const W = {provider:'nhm', q:'fossil', meta:null, results:null, busy:false, errors:'', collected:new Set()};
  const ensure = async () => {
    if(W.meta) return W.meta;
    try { W.meta=await api('/world-sources/providers'); }
    catch(e){ W.errors=e.message||'馆方数据服务不可用'; }
    return W.meta;
  };
  const panel = () => `<section class="ws-panel" id="ws-panel" aria-label="世界自然史与科技馆藏">
    <header class="ws-head"><div><div class="eyebrow">WORLD COLLECTION / LIVE OFFICIAL DATA</div><h2>从亿万年前的标本，走向人类的创造。</h2><p>连接真实的馆方标本数据和艺术古董记录。搜索结果来自官方馆藏接口，不会虚构历史条目。</p></div><div class="ws-mini">古董 · 珠宝 · 自然史 · 科技</div></header>
    <div class="ws-picks">${(W.meta?.suggestions||[
    {name:'远古标本',query:'fossil',provider:'nhm'},{name:'古董珠宝',query:'necklace',provider:'met'},
    {name:'昆虫标本',query:'butterfly',provider:'nhm'},{name:'古老绘画',query:'painting',provider:'met'}
    ]).map(x=>`<button type="button" data-ws="suggest" data-provider="${E(x.provider)}" data-q="${E(x.query)}">${E(x.name)} ↗</button>`).join('')}</div>
    <form id="ws-search" class="ws-form"><label>数据来源<select name="provider" aria-label="官方馆藏数据来源"><option value="nhm" ${W.provider==='nhm'?'selected':''}>伦敦自然历史博物馆</option><option value="met" ${W.provider==='met'?'selected':''}>大都会艺术博物馆</option></select></label>
    <label class="ws-grow">搜索馆藏关键词<input name="q" minlength="2" maxlength="60" required value="${E(W.q)}" placeholder="fossil、necklace、painting、butterfly"></label><button class="primary" type="submit">查找真实馆藏</button></form>
    <div id="ws-results" aria-live="polite">${resultsMarkup()}</div>
    <section class="ws-external"><b>更多真实科技藏品和自然史入口</b><p>下面是官方目录和档案，部分站点的 API 未接入本站，请到原网站继续探索。</p><div class="ws-links">${(W.meta?.directories||[
      {name:'英国科学博物馆集团',url:'https://collection.sciencemuseumgroup.org.uk/search/objects',theme:'科技史'},
      {name:'史密森尼开放访问',url:'https://www.si.edu/openaccess',theme:'综合馆藏'}]).map(x=>`<a href="${E(x.url)}" rel="noopener noreferrer" target="_blank"><b>${E(x.name)}</b><span>${E(x.theme||'官方入口')} ↗</span></a>`).join('')}</div></section>
  </section>`;
  const resultsMarkup = () => {
    if(W.busy) return '<p class="ws-hint">正在向馆方 API 查询，不会用生成内容填充结果…</p>';
    if(W.errors) return `<p class="ws-hint ws-warn">${E(W.errors)}　<a href="${W.provider==='nhm'?'https://data.nhm.ac.uk/dataset/collection-specimens':'https://www.metmuseum.org/art/collection'}" target="_blank" rel="noopener noreferrer">前往馆方继续探索 ↗</a></p>`;
    if(!W.results) return '<p class="ws-hint">请选择一个专题或输入关键词开始探索。英文关键词通常更容易找到准确结果。</p>';
    if(W.results.unavailable) return `<p class="ws-hint ws-warn">${E(W.results.notice)}　<a href="${W.provider==='nhm'?'https://data.nhm.ac.uk/dataset/collection-specimens':'https://www.metmuseum.org/art/collection'}" target="_blank" rel="noopener noreferrer">打开官方数据门户 ↗</a></p>`;
    const items=W.results.items||[];
    return `<div class="ws-summary">馆方匹配 ${Number(W.results.matched_total)||0} 条 · 当前安全展示 ${items.length} 条${W.results.cached?' · 缓存结果':''}</div>${items.length?`<div class="ws-grid">${items.map(x=>`<article class="ws-card">
      <div class="ws-art">${x.image_url&&x.open_access_image?`<img src="${E(x.image_url)}" loading="lazy" alt="${E(x.title)}">`:'<span>✳</span>'}</div>
      <div class="ws-content"><small>${E(x.museum)} · ${E(x.category)}</small><h3>${E(x.title)}</h3><p>${E(x.subtitle||x.description||'馆方记录')}</p><div class="ws-date">${E(x.date_note||'')}</div><div class="ws-rights">${E(x.license||'未核验图像许可')}</div><div class="ws-actions"><a href="${E(x.source_url)}" target="_blank" rel="noopener noreferrer">馆方原档 ↗</a><button class="ghost" type="button" data-ws="save" data-id="${E(x.id)}" ${W.collected.has(x.id)?'disabled':''}>${W.collected.has(x.id)?'✓ 已保存':'＋ 私人收藏'}</button></div></div>
    </article>`).join('')}</div>`:'<p class="ws-hint">这一关键词没有返回可用记录。可以更换英文关键词或直接访问馆方。</p>'}<p class="ws-legal">自然标本档案中的“采集年份”不代表化石形成时间；未核验媒体开放许可时仅显示文字和原馆链接。</p>`;
  };
  const paint = () => {const div=document.querySelector('#ws-results');if(div)div.innerHTML=resultsMarkup();};
  const search = async (provider,q) => {
    W.provider=provider;W.q=q.trim();W.errors='';W.busy=true;W.results=null;paint();
    window.WonderAnalytics?.track('world_museums','search');
    try{ W.results=await api('/world-sources/search?'+new URLSearchParams({provider:W.provider,q:W.q,limit:'8'})); if(W.results?.unavailable)W.errors=''; }
    catch(err){W.errors=err.message||'馆方搜索不可用';}
    finally{W.busy=false;paint();}
  };
  document.addEventListener('click',async e=>{
    const btn=e.target.closest('[data-ws]');if(!btn)return;
    const action=btn.dataset.ws;
    if(action==='suggest') {e.preventDefault();await search(btn.dataset.provider,btn.dataset.q); const f=document.querySelector('#ws-search');if(f){f.elements.provider.value=W.provider;f.elements.q.value=W.q;} }
    else if(action==='save') {
      e.preventDefault();
      if(!window.S?.user){typeof mustLogin==='function'?mustLogin():toast('请先登录');return;}
      btn.disabled=true;
      try{const result=await api('/world-sources/save',{method:'POST',body:{object_id:btn.dataset.id}});
          W.collected.add(btn.dataset.id);window.WonderAnalytics?.track('world_museums','collect');toast(result.already_saved?'这件作品已经在你的博物馆中':'馆方记录已收入私人博物馆');paint();}
      catch(err){toast(err.message||'收藏失败');btn.disabled=false;}
    }
  },true);
  document.addEventListener('submit',e=>{
    if(e.target.id!=='ws-search')return;
    e.preventDefault();e.stopImmediatePropagation();
    const data=Object.fromEntries(new FormData(e.target));search(data.provider,String(data.q||''));
  },true);
  const renderPanel=()=>{ensure().then(()=>{if(window.S?.view==='world-museums'){const target=document.querySelector('#ws-panel');if(target){const fresh=document.createElement('div');fresh.innerHTML=panel();target.replaceWith(fresh.firstElementChild);} } });return panel();};
  return {renderPanel};
})();