/* Wonder Atlas V6: broad collection discovery, official museum directory, live tech radar, transparent product feedback. */
(() => {
  const RD = { tab:'radar', topic:'tech', group:'全部', directoryQ:'', collectionQ:'', collectionSource:'all', directory:[], radar:null, searchResults:null, days:30, summary:null, loading:false };
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const topicLabels = [['tech','科技热榜'],['ai','AI 与智能体'],['robotics','机器人'],['chips','芯片与硬件'],['quantum','量子与前沿科学'],['biotech','生命科学'],['odd','互联网奇物'],['space','航天与宇宙']];
  const categoryTopics = ['古董与珠宝','绘画与书画','古币与钱币','陶瓷与器物','历史文物','古籍与手稿','自然与化石','矿物与宝石','科技与发明','AI与机器人','航天与宇宙','互联网奇物'];
  const track = (feature, action='complete') => { try { window.WonderAnalytics?.track(feature, action); } catch (_) {} };
  const groupGlyph = g => ({'绘画、古董与珠宝':'♜','现代艺术与设计':'✳','亚洲艺术与历史':'山','自然、矿物与化石':'✺','科技、工程与未来':'⌘','摄影、电影与影像':'▧','书籍、手稿与档案':'▤','博物馆导航与地图':'⌖','当代流行与新奇':'↗'}[g] || '✦');
  async function safeApi(path) { try { return await api(path); } catch (e) { return {items:[],error:e.message}; } }
  function topTabs() { return `<div class="wd-tabs" role="tablist"><button data-wonder="tab" data-value="radar" class="${RD.tab==='radar'?'active':''}">✧ 当代新奇</button><button data-wonder="tab" data-value="collections" class="${RD.tab==='collections'?'active':''}">♜ 开放馆藏搜索</button><button data-wonder="tab" data-value="museums" class="${RD.tab==='museums'?'active':''}">⌖ 世界博物馆导航</button></div>`; }
  function hero() { return `<section class="wd-hero"><div><div class="eyebrow">WONDER RADAR · V6</div><h1>从古代珍宝，<br><span>一路探索到未来。</span></h1><p>古董珠宝、千年绘画、自然标本、芯片与机器人、最新 AI 工具、奇怪网站——万物博物馆不只收藏过去，也收集正在发生的世界。</p><div class="wd-hero-tags"><span>古物与珠宝</span><span>艺术与文明</span><span>AI 与科技</span><span>互联网奇物</span><span>自然与宇宙</span></div></div><div class="wd-orbit" aria-hidden="true"><i>✳</i><b>PAST</b><em>NOW</em><strong>FUTURE</strong></div></section>`; }
  function renderRadarContent(data) {
    const items=data?.items||[];
    return `${hero()}${topTabs()}<div class="wd-section-head"><div><div class="eyebrow">LIVE CURIOSITY FEED</div><h2>当代新奇 · 科技雷达</h2><p>科技热榜来自 Hacker News 官方公开 API；航天图像来自 NASA Image and Video Library。数据受外部服务与网络影响。</p></div><span class="wd-live">● ${data?.error?'外部数据暂不可用':'尝试读取实时数据'}</span></div><div class="wd-topic-row">${topicLabels.map(([key,label])=>`<button data-wonder="topic" data-value="${key}" class="${RD.topic===key?'active':''}">${label}</button>`).join('')}</div>
    ${data?.error?`<div class="wd-notice">${esc(data.error)} 如果你所在网络无法连接外部 API，可以通过下面的官方趋势入口继续浏览。</div>`:''}
    ${items.length?`<div class="wd-radar-grid">${items.map(x=>x.kind==='space'?`<article class="wd-live-card">${x.image_url?`<img class="wd-live-image" src="${esc(x.image_url)}" loading="lazy" alt="${esc(x.title)}" referrerpolicy="no-referrer">`:`<div class="wd-live-image wd-live-placeholder">✧ NASA</div>`}<div class="wd-live-body"><span class="wd-source">${esc(x.source)} · ${esc(x.date||'')}</span><h3>${esc(x.title)}</h3><p>${esc(x.description||'打开原始资料，继续探索。')}</p><div class="wd-actions"><a class="ghost" href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">原始资料 ↗</a><button class="primary" data-wonder="collectLink" data-title="${esc(x.title)}" data-description="${esc(x.description||'来自 NASA 的航天与科学图像。')}" data-url="${esc(x.url)}" data-image="${esc(x.image_url||'')}" data-category="航天与宇宙">＋ 收入我的博物馆</button></div></div></article>`:`<article class="wd-live-card wd-tech-card"><div class="wd-live-tech-icon">⌘</div><div class="wd-live-body"><span class="wd-source">${esc(x.source)} · ${esc(x.time||'')}</span><h3>${esc(x.title)}</h3><p>当前热榜分数 ${Number(x.score)||0} · ${Number(x.comments)||0} 条讨论。热度会随时间变化，不代表内容已经核实。</p><div class="wd-actions"><a class="ghost" href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">打开原文 ↗</a><button class="primary" data-wonder="collectLink" data-title="${esc(x.title)}" data-description="来自 Hacker News 实时热榜。热度和内容会变化，请查看原始文章。" data-url="${esc(x.url)}" data-category="科技与发明">＋ 收入我的博物馆</button></div></div></article>`).join('')}</div>`:`<div class="wd-empty"><b>现在没有拿到实时条目</b><p>不用担心，下面的官方入口仍然可用。我们不会用虚构的“热榜”填充页面。</p></div>`}
    <section class="wd-explore-links"><div class="wd-section-head"><div><div class="eyebrow">OPEN THE FRONTIER</div><h2>继续发现新东西</h2><p>这些是官方趋势页、研究入口或交互演示；点击后由原网站提供内容。</p></div></div><div class="wd-link-grid">${(data?.links||[]).map(x=>`<a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer"><span>↗</span><b>${esc(x.name)}</b><small>${esc(x.note)}</small></a>`).join('')}</div></section>`;
  }
  async function renderRadar() {
    const data=await safeApi('/wonder/radar?topic='+encodeURIComponent(RD.topic));
    RD.radar=data;
    return renderRadarContent(data);
  }
  function renderDirectory(data) {
    const items=data?.items||[];const groups=['全部',...(data?.groups||[])];
    
    return `${hero()}${topTabs()}<div class="wd-section-head"><div><div class="eyebrow">MUSEUMS & COLLECTIONS DIRECTORY</div><h2>世界博物馆导航</h2><p>把世界各地的官方馆藏入口集中在一个地方。每个链接都指向来源机构；并非所有机构都开放图像下载或提供 API。</p></div><strong class="wd-count">${data?.total||0} 个入口</strong></div><form id="wdDirectoryForm" class="wd-search-row"><input name="q" value="${esc(RD.directoryQ)}" placeholder="搜索珠宝、绘画、计算机、矿物、博物馆…"><select name="group">${groups.map(g=>`<option value="${esc(g)}" ${RD.group===g?'selected':''}>${esc(g)}</option>`).join('')}</select><button class="primary">搜索目录</button><button class="ghost" type="button" data-wonder="clearDirectory">重置</button></form><div class="wd-group-chips">${groups.map(g=>`<button data-wonder="group" data-value="${esc(g)}" class="${RD.group===g?'active':''}">${esc(g)}</button>`).join('')}</div><div class="wd-directory-grid">${items.map(x=>`<article class="wd-museum-card"><div class="wd-museum-icon">${groupGlyph(x.group)}</div><div class="wd-museum-group">${esc(x.group)}</div><h3>${esc(x.name)}</h3><div class="wd-museum-en">${esc(x.en)}</div><p>${esc(x.note)}</p><div class="wd-museum-meta"><span>${esc(x.kind)}</span><a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">进入官网 ↗</a></div></article>`).join('')||`<div class="wd-empty"><b>没有匹配的入口</b><p>试试更短的关键词，或切换“全部”。</p></div>`}</div><p class="wd-disclaimer">导航说明：这是经过整理的官方入口目录，不代表本站与这些机构存在合作。部分站点可能要求账号、API Key 或遵守单独的图片许可。</p>`;
  }
  async function renderMuseums() {
    const p=new URLSearchParams({q:RD.directoryQ,group:RD.group});const data=await safeApi('/wonder/museums?'+p.toString());RD.directory=data.items||[];
    return renderDirectory(data);
  }
  function renderCollectionSearch(data) {
    const items=data?.items||[];
    return `${hero()}${topTabs()}<div class="wd-section-head"><div><div class="eyebrow">SEARCH OPEN COLLECTIONS</div><h2>跨馆开放馆藏搜索</h2><p>不只看内置精选。输入英文或中文关键词，尝试搜索大都会、芝加哥与克利夫兰的官方开放馆藏；珠宝、古画、项链、戒指、古币、瓷器、盔甲、化石都可以试。</p></div></div><form id="wdCollectionForm" class="wd-search-row"><input name="q" minlength="2" maxlength="100" required value="${esc(RD.collectionQ)}" placeholder="例如 jewelry / necklace / ancient coin / 古画 / 珠宝"><select name="source"><option value="all" ${RD.collectionSource==='all'?'selected':''}>全部已接入馆藏</option><option value="met" ${RD.collectionSource==='met'?'selected':''}>大都会艺术博物馆</option><option value="aic" ${RD.collectionSource==='aic'?'selected':''}>芝加哥艺术博物馆</option><option value="cma" ${RD.collectionSource==='cma'?'selected':''}>克利夫兰艺术博物馆</option></select><button class="primary">搜索真实馆藏</button></form><div class="wd-query-chips">${['jewelry','necklace','ancient coin','oil painting','jade','porcelain','armor','fossil','珠宝','古画'].map(q=>`<button data-wonder="query" data-value="${esc(q)}">${esc(q)}</button>`).join('')}</div>
    ${data?.sources_failed?.length?`<div class="wd-notice">部分馆方接口暂不可用：${esc(data.sources_failed.join('、'))}。可以更换来源或稍后重试。</div>`:''}
    ${data?.error?`<div class="wd-notice">${esc(data.error)}</div>`:''}
    ${RD.collectionQ&&!data?`<div class="wd-empty"><b>正在搜索官方目录…</b><p>稍等片刻。</p></div>`:''}
    ${data?`<div class="wd-search-summary">关键词“${esc(data.query||RD.collectionQ)}” · 找到 ${data.total||0} 件作品。${esc(data.notice||'')}</div>`:''}
    ${items.length?`<div class="wd-open-art-grid">${items.map(x=>`<article class="wd-open-art-card">${x.image_url?`<img src="${esc(x.image_url)}" loading="lazy" alt="${esc(x.title)}" referrerpolicy="no-referrer">`:`<div class="wd-open-art-placeholder">${groupGlyph(x.category)}</div>`}<div class="wd-open-art-body"><span class="wd-source">${esc(x.museum)} · ${esc(x.license||'许可待核')}</span><h3>${esc(x.title)}</h3><div class="wd-museum-en">${esc(x.title_en||'')}</div><p>${esc(x.artist||'创作者未提供')} · ${esc(x.date||'年代未提供')}</p><p class="wd-medium">${esc(x.medium||x.category||'馆藏作品')}</p><div class="wd-actions"><a class="ghost" href="${esc(x.source_url)}" target="_blank" rel="noopener noreferrer">原馆档案 ↗</a><button class="primary" data-wonder="collectLink" data-title="${esc(x.title)}" data-description="${esc([x.artist,x.date,x.medium,x.museum].filter(Boolean).join(' · '))}" data-url="${esc(x.source_url)}" data-image="${esc(x.open_access?x.image_url:'')}" data-category="${esc(x.category||'古董与珠宝')}" data-license="${esc(x.license||'馆方许可需进一步核验')}">＋ 私藏这件作品</button></div></div></article>`).join('')}</div>`:data?`<div class="wd-empty"><b>没有找到结果</b><p>建议用英文关键词，或尝试 necklace、jewelry、painting、coin、jade、porcelain 等词。搜索依赖外部馆方 API，网络限制也可能导致无结果。</p></div>`:`<div class="wd-empty"><b>从一件古董开始</b><p>输入关键词，就能尝试检索官方馆藏，而不必只浏览预先挑选的作品。</p></div>`}
    <p class="wd-disclaimer">版权提醒：搜索结果中的“开放图像”状态来自馆方 API。收藏记录默认为私密；转载、公开发布或商业使用前，仍应查看作品原始档案与最新许可。</p>`;
  }
  async function renderCollections() {
    if(!RD.collectionQ) return renderCollectionSearch(null);
    const p=new URLSearchParams({q:RD.collectionQ,source:RD.collectionSource});
    const data=await safeApi('/wonder/collection-search?'+p.toString());
    RD.searchResults=data;
    return renderCollectionSearch(data);
  }
  async function render() {
    if(RD.tab==='museums') return renderMuseums();
    if(RD.tab==='collections') return renderCollections();
    return renderRadar();
  }
  async function renderInsights() {
    let data; try { data=await api('/insights/summary?days='+RD.days); } catch(err) { return `<div class="wd-empty"><b>功能热度暂时不可用</b><p>${esc(err.message)}</p></div>`; }
    RD.summary=data;const items=data.items||[];const max=Math.max(1,...items.map(x=>x.opens+x.actions));
    return `<section class="wd-hero wd-insight-hero"><div><div class="eyebrow">PRODUCT INSIGHTS · COMMUNITY VOTE</div><h1>把时间花在<br><span>大家真正喜欢的功能上。</span></h1><p>这不是凭感觉排开发计划。我们同时看功能访问、真实操作和用户明确投票，帮助决定下一版优先做什么。</p><div class="wd-hero-tags"><span>实际使用</span><span>用户投票</span><span>透明聚合</span></div></div><div class="wd-orbit" aria-hidden="true"><i>♡</i><b>DATA</b><em>IDEAS</em><strong>BETTER</strong></div></section>
    <div class="wd-insight-toolbar"><div><div class="eyebrow">FEATURE PRIORITY BOARD</div><h2>功能热度与投票</h2><p>访问和操作按周期统计；喜欢票与改进票为累计投票。</p></div><select id="wdInsightDays"><option value="7" ${RD.days===7?'selected':''}>最近 7 天</option><option value="30" ${RD.days===30?'selected':''}>最近 30 天</option><option value="90" ${RD.days===90?'selected':''}>最近 90 天</option></select></div>
    <div class="wd-insight-summary"><div><strong>${data.total_events||0}</strong><span>近 ${data.days} 天功能使用记录</span></div><div><strong>${data.total_votes||0}</strong><span>累计功能偏好票</span></div><div><strong>${items.filter(x=>x.love_votes>0).length}</strong><span>获得喜欢票的功能</span></div></div>
    <div class="wd-vote-callout"><b>馆长投票</b><span>每个账号对每项功能保留一票，可以随时改票。还没多少数据时，不会把“零票”伪装成热门。</span></div>
    <div class="wd-feature-rank">${items.map((x,i)=>`<article class="wd-feature-row"><div class="wd-rank">${String(i+1).padStart(2,'0')}</div><div class="wd-feature-info"><h3>${esc(x.name)}</h3><p>${esc(x.description)}</p><div class="wd-meter"><i style="width:${Math.max(0,Math.min(100,(x.opens+x.actions)/max*100))}%"></i></div><div class="wd-feature-stats"><span>打开 ${x.opens}</span><span>操作 ${x.actions}</span><span>活跃用户 ${x.active_users}</span><span>喜欢 ${x.love_votes}</span><span>想改进 ${x.improve_votes}</span></div></div><div class="wd-vote-buttons"><button data-wonder="vote" data-feature="${esc(x.key)}" data-value="love" class="${x.my_vote==='love'?'selected':''}">♥ 喜欢</button><button data-wonder="vote" data-feature="${esc(x.key)}" data-value="neutral" class="${x.my_vote==='neutral'?'selected':''}">一般</button><button data-wonder="vote" data-feature="${esc(x.key)}" data-value="improve" class="${x.my_vote==='improve'?'selected':''}">需改进</button></div></article>`).join('')}</div>
    <p class="wd-disclaimer">统计原则：仅登录用户的功能名和操作类型会被记录；不记录搜索词、展品 ID、私人展品内容、完整访问网址或 IP。只展示汇总值，不提供个人行为排行榜。首次启用后数据才会逐渐累积；喜欢票、使用量和改进票分别展示，不混成一个无法解释的分数。</p>`;
  }
  document.addEventListener('submit', async ev => {
    const form=ev.target;
    if(form.id==='wdDirectoryForm') { ev.preventDefault();const fd=new FormData(form);RD.directoryQ=String(fd.get('q')||'').trim();RD.group=String(fd.get('group')||'全部');await updateRadarPage(); }
    if(form.id==='wdCollectionForm') { ev.preventDefault();const fd=new FormData(form);RD.collectionQ=String(fd.get('q')||'').trim();RD.collectionSource=String(fd.get('source')||'all');RD.searchResults=null;RD.tab='collections';track('museum_directory','search');await updateRadarPage(); }
  });
  async function updateRadarPage() { if(window.S?.view!=='wonder-radar')return;const main=document.querySelector('#main');if(main)main.innerHTML='<div class="loading">正在整理万物档案…</div>';const html=await render();if(main&&window.S?.view==='wonder-radar')main.innerHTML=html; }
  document.addEventListener('click', async ev => {
    const b=ev.target.closest('[data-wonder]');if(!b)return;const action=b.dataset.wonder;ev.preventDefault();
    try {
      if(action==='tab'){RD.tab=b.dataset.value;track(RD.tab==='museums'?'museum_directory':RD.tab==='collections'?'museum_directory':'tech_radar','open');await updateRadarPage();}
      else if(action==='topic'){RD.topic=b.dataset.value;track('tech_radar','search');await updateRadarPage();}
      else if(action==='group'){RD.group=b.dataset.value;RD.directoryQ='';await updateRadarPage();}
      else if(action==='clearDirectory'){RD.group='全部';RD.directoryQ='';await updateRadarPage();}
      else if(action==='query'){RD.collectionQ=b.dataset.value;RD.collectionSource='all';RD.tab='collections';RD.searchResults=null;track('museum_directory','search');await updateRadarPage();}
      else if(action==='collectLink'){
        if(!window.S?.user){if(typeof mustLogin==='function')mustLogin();else toast('请先登录');return;}
        const title=b.dataset.title||'来自万物雷达的发现';const source_url=b.dataset.url||'';
        if(!source_url)return toast('缺少原始来源链接');b.disabled=true;
        const category=b.dataset.category||'科技与发明';const tags=[category,'万物雷达'];
        const body={title:title.slice(0,100),description:(b.dataset.description||'来自外部开放目录或科技发现。').slice(0,600),source_url,image_url:b.dataset.image||'',category,tags,source_note:(b.dataset.license||'').slice(0,400)};
        const result=await api('/wonder/collect-link',{method:'POST',body});track(category==='科技与发明'||category==='航天与宇宙'?'tech_radar':'museum_directory','collect');toast(result.already_collected?'这件发现已经收藏过了':'已收入你的博物馆，并默认设为私密');b.textContent=result.already_collected?'✓ 已收藏':'✓ 已收入';
      }
      else if(action==='vote'){
        if(!window.S?.user){if(typeof mustLogin==='function')mustLogin();else toast('登录后才能投票');return;}
        await api('/insights/vote',{method:'POST',body:{feature:b.dataset.feature,sentiment:b.dataset.value}});track('insights','vote');toast('收到！功能偏好已更新。');const main=document.querySelector('#main');if(main&&window.S?.view==='insights')main.innerHTML=await renderInsights();
      }
    } catch(err){toast(err.message||'操作失败');b.disabled=false;}
  });
  document.addEventListener('change',async ev=>{if(ev.target.id==='wdInsightDays'){RD.days=Number(ev.target.value)||30;if(window.S?.view==='insights'){const main=document.querySelector('#main');if(main)main.innerHTML=await renderInsights();}}});
  window.WonderDiscovery={render,renderInsights};
})();