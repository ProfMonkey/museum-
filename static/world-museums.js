/* World-famous museum starter collection. Uses official museum API metadata and image URLs. */
const WorldMuseums = (() => {
  const W = { q: '', museum: '全部', items: [], loading: false, pollCount: 0, pollScheduled: false, clientAttempted: false, clientEnriching: false };
  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const iconFor = item => ({'绘画':'✧','亚洲艺术':'波','中国艺术':'山','织物与工艺':'❖','历史艺术':'⌘','宗教艺术':'☼'}[item.category] || '✦');
  const cover = item => item.image_url
    ? `<div class="wm-art"><img src="${escapeHtml(item.image_url)}" loading="lazy" alt="${escapeHtml(item.title)}" referrerpolicy="no-referrer"><span class="wm-open-access">${item.open_access ? 'OPEN ACCESS' : '馆方记录'}</span></div>`
    : `<div class="wm-art wm-placeholder"><span class="wm-placeholder-mark">${iconFor(item)}</span><span class="wm-placeholder-title">${escapeHtml(item.museum)}</span><span class="wm-placeholder-note">正在等待馆方图像／当前网络不可用</span></div>`;
  const museumLinks = [
    ['大都会艺术博物馆','The Met','https://www.metmuseum.org/art/collection'],
    ['芝加哥艺术博物馆','Art Institute of Chicago','https://www.artic.edu/collection'],
    ['克利夫兰艺术博物馆','Cleveland Museum of Art','https://www.clevelandart.org/art/collection'],
    ['卢浮宫','Musée du Louvre','https://collections.louvre.fr/'],
    ['大英博物馆','The British Museum','https://www.britishmuseum.org/collection'],
    ['荷兰国立博物馆','Rijksmuseum','https://www.rijksmuseum.nl/en/collection'],
    ['美国国家美术馆','National Gallery of Art','https://www.nga.gov/collection.html']
  ];
  async function jsonFetch(url) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 3200);
    try {
      const response = await fetch(url, { signal: controller.signal, headers: { 'Accept': 'application/json' } });
      if (!response.ok) return null;
      return await response.json();
    } catch (_) { return null; }
    finally { clearTimeout(timer); }
  }
  async function enrichOne(item) {
    if (!item?.provider || !item.external_id) return item;
    try {
      if (item.provider === 'met') {
        const raw = await jsonFetch(`https://collectionapi.metmuseum.org/public/collection/v1/objects/${encodeURIComponent(item.external_id)}`);
        if (!raw) return item;
        const open = raw.isPublicDomain === true && /^https:\/\/images\.metmuseum\.org\//i.test(raw.primaryImageSmall || '');
        return { ...item, title_en: raw.title || item.title_en, artist: raw.artistDisplayName || item.artist,
          date: raw.objectDate || item.date, medium: raw.medium || item.medium, culture: raw.culture || item.culture,
          department: raw.department || item.department, source_url: raw.objectURL || item.source_url,
          image_url: open ? raw.primaryImageSmall : '', open_access: Boolean(open),
          license: open ? 'Public Domain / Open Access' : '馆方未将该图像标记为开放访问' };
      }
      if (item.provider === 'aic') {
        const fields = 'id,title,artist_display,date_display,medium_display,department_title,is_public_domain,image_id,web_url,credit_line';
        const raw = await jsonFetch(`https://api.artic.edu/api/v1/artworks/${encodeURIComponent(item.external_id)}?fields=${encodeURIComponent(fields)}`);
        const d = raw?.data; if (!d) return item;
        const open = d.is_public_domain === true && Boolean(d.image_id);
        return { ...item, title_en: d.title || item.title_en, artist: d.artist_display || item.artist,
          date: d.date_display || item.date, medium: d.medium_display || item.medium, department: d.department_title || item.department,
          source_url: d.web_url || item.source_url,
          image_url: open ? `https://www.artic.edu/iiif/2/${encodeURIComponent(d.image_id)}/full/843,/0/default.jpg` : '',
          open_access: Boolean(open), license: open ? 'Public Domain' : '馆方未将该图像标记为公有领域' };
      }
      if (item.provider === 'cma') {
        const raw = await jsonFetch(`https://openaccess-api.clevelandart.org/api/artworks/${encodeURIComponent(item.external_id)}`);
        const d = raw?.data; if (!d) return item;
        const cc0 = String(d.share_license_status || '').toUpperCase() === 'CC0';
        const images = d.images || {}, image = images.web?.url || images.print?.url || '';
        const safe = /^https:\/\//i.test(image) && /(^|\.)clevelandart\.org$/i.test(new URL(image).hostname);
        const open = cc0 && safe;
        const creators = (d.creators || []).map(x => x.description).filter(Boolean).join(', ');
        return { ...item, title_en: d.title || item.title_en, artist: creators || item.artist,
          date: d.creation_date || item.date, medium: d.technique || item.medium, culture: (d.culture || []).join(', ') || item.culture,
          department: d.department || item.department, source_url: d.url || item.source_url,
          image_url: open ? image : '', open_access: Boolean(open), license: open ? 'CC0 开放访问' : '馆方未将该图像标记为 CC0' };
      }
    } catch (_) {}
    return item;
  }
  async function enrichInBrowser(items) {
    const result = new Array(items.length); let next = 0;
    const worker = async () => { while (next < items.length) { const i = next++; result[i] = await enrichOne(items[i]); } };
    await Promise.all(Array.from({ length: 8 }, worker));
    return result;
  }
  async function load() {
    W.loading = true;
    const params = new URLSearchParams({ q: W.q, museum: W.museum });
    try {
      const result = await api('/world-museums?' + params.toString());
      const previous = new Map(W.items.map(x => [x.id, x]));
      W.items = (result.items || []).map(item => {
        const old = previous.get(item.id);
        return old?.open_access && old.image_url && !item.open_access ? { ...item, ...old, collected: item.collected } : item;
      });
      if (result.network_fallback && !W.clientAttempted && W.items.length) {
        W.clientAttempted = true; W.clientEnriching = true;
        const snapshot = [...W.items];
        enrichInBrowser(snapshot).then(enriched => {
          const map = new Map(enriched.map(x => [x.id, x]));
          W.items = W.items.map(item => map.has(item.id) ? { ...map.get(item.id), collected: item.collected } : item);
          if (W.items.some(x => x.open_access && x.image_url) && window.S?.view === 'world-museums') {
            const main = document.querySelector('#main'); if (main) render().then(html => { if (window.S?.view === 'world-museums') main.innerHTML = html; });
          }
        }).finally(() => { W.clientEnriching = false; });
      }
      return { ...result, error: '' };
    } catch (error) {
      W.items = [];
      return { items: [], total: 0, museums: [], error: error.message };
    } finally { W.loading = false; }
  }
  async function render() {
    const data = await load();
    const noOpenImages = !W.items.some(x => x.open_access && x.image_url);
    if (data.network_fallback && noOpenImages && !W.pollScheduled && W.pollCount < 3) {
      W.pollScheduled = true;
      setTimeout(async () => {
        W.pollScheduled = false; W.pollCount += 1;
        if (window.S?.view !== 'world-museums') return;
        try {
          const params = new URLSearchParams({ q: W.q, museum: W.museum });
          const fresh = await api('/world-museums?' + params.toString());
          if ((fresh.items || []).some(x => x.open_access && x.image_url)) {
            W.items = fresh.items; W.pollCount = 0;
            const main = document.querySelector('#main'); if (main && window.S?.view === 'world-museums') main.innerHTML = await render();
          } else if (W.pollCount < 3) {
            const main = document.querySelector('#main'); if (main && window.S?.view === 'world-museums') main.innerHTML = await render();
          }
        } catch (_) {}
      }, 5000);
    }
    const openCount = W.items.filter(x => x.open_access && x.image_url).length;
    const museums = ['全部', ...(data.museums || [])];
    return `
      <section class="wm-hero">
        <div class="wm-hero-copy">
          <div class="eyebrow">THE WORLD'S COLLECTIONS · OPEN ACCESS</div>
          <h1>先从世界名作开始，<br><span>再慢慢建造自己的世界。</span></h1>
          <p>万物博物馆现在自带一组世界名馆精选。无需等别人上传，你也可以从真实馆藏开始探索。每件作品都保留原馆来源与开放许可信息。</p>
          <div class="wm-hero-tags"><span>✦ 官方馆藏来源</span><span>◈ 开放图像优先</span><span>↗ 一键收入个人馆藏</span></div>
        </div>
        <div class="wm-hero-emblem" aria-hidden="true"><div class="wm-ring wm-ring-one"></div><div class="wm-ring wm-ring-two"></div><span>WORLD<br>ART<br>ARCHIVE</span><i>✳</i></div>
      </section>
      <section class="wm-stats"><div><strong>${W.items.length}</strong><span>当前筛选作品</span></div><div><strong>${openCount}</strong><span>已核验开放图像</span></div><div><strong>${museums.length - 1}</strong><span>馆藏机构</span></div><div class="wm-stat-note">精选典藏会随官方数据更新；图像不复制到本站服务器。</div></section>
      ${data.error ? `<div class="wm-notice">${escapeHtml(data.error)}。当前无法连接馆方数据接口，仍会保留页面；请检查网络后重试。</div>` : ''}
      ${data.network_fallback && noOpenImages ? `<div class="wm-notice">当前尚未取到馆方开放图像。精选作品与来源档案仍可浏览，页面会尝试重新读取；若持续无图，请检查网络。</div>` : ''}
      <section class="wm-controls-wrap">
        <div><div class="eyebrow">STARTER COLLECTION / V1</div><h2>世界名馆 · 初始典藏</h2><p>精选作品来自大都会艺术博物馆、芝加哥艺术博物馆与克利夫兰艺术博物馆。</p></div>
        <form class="wm-controls" id="worldMuseumSearch"><input name="q" value="${escapeHtml(W.q)}" placeholder="搜索作品、艺术家、文化或年代…" aria-label="搜索世界名馆藏品"><select name="museum" aria-label="按博物馆筛选">${museums.map(m=>`<option value="${escapeHtml(m)}" ${W.museum===m?'selected':''}>${escapeHtml(m)}</option>`).join('')}</select><button class="primary" type="submit">⌕ 搜索</button><button class="ghost" type="button" data-world-action="clear">重置</button></form>
      </section>
      <div class="wm-intro-row"><span>✦ 作品详情会保留馆方原始资料</span><span>共 ${data.total || 0} 件 · 收藏后默认设为私密</span></div>
      ${W.items.length ? `<div class="wm-grid">${W.items.map(item=>`
        <article class="wm-card">
          ${cover(item)}
          <div class="wm-card-body">
            <div class="wm-card-top"><span>${escapeHtml(item.museum)}</span><span class="wm-license ${item.open_access?'is-open':''}">${item.open_access?'开放图像':'来源档案'}</span></div>
            <h3>${escapeHtml(item.title)}</h3>
            <p class="wm-original-title">${escapeHtml(item.title_en || '')}</p>
            <div class="wm-maker">${escapeHtml(item.artist || '创作者资料待补充')}</div>
            <div class="wm-meta"><span>${escapeHtml(item.date || '年代待核')}</span><span>${escapeHtml(item.medium || item.category || '馆藏作品')}</span></div>
            <p class="wm-note">${escapeHtml(item.note || '打开原馆资料，了解作品背景。')}</p>
            <div class="wm-card-actions"><button class="ghost" type="button" data-world-action="details" data-id="${escapeHtml(item.id)}">作品档案</button><button class="primary" type="button" data-world-action="collect" data-id="${escapeHtml(item.id)}" ${item.collected?'disabled':''}>${item.collected?'✓ 已收入馆藏':'＋ 收入我的博物馆'}</button></div>
          </div>
        </article>`).join('')}</div>` : `<div class="empty"><b>${data.error?'馆方数据暂时不可用':'没有找到匹配的作品'}</b><p>${data.error?'稍后重试即可。':'试试其他作品名、艺术家或切换到全部馆藏。'}</p><button class="ghost" data-world-action="clear">查看全部典藏</button></div>`}
      <section class="wm-how"><div><div class="eyebrow">HOW TO COLLECT</div><h2>把世界名作，变成你世界的一部分。</h2><p>点击“收入我的博物馆”，作品会作为一条独立的个人展品记录保存。它默认是私密的，不会自动发布到公共广场，也不会把原馆图像复制或重新分发。</p></div><div class="wm-how-steps"><div><b>01</b><span>挑选感兴趣的作品</span></div><div><b>02</b><span>查看来源与开放许可</span></div><div><b>03</b><span>收入个人馆藏，再放进自己的展厅</span></div></div></section>
      <section class="wm-source-directory"><div><div class="eyebrow">GO FURTHER</div><h2>继续逛世界名馆</h2><p>下面是各馆官方馆藏入口。它们是外部官网链接，不代表其作品已经导入本站精选目录。</p></div><div class="wm-source-links">${museumLinks.map(([zh,en,url])=>`<a href="${url}" target="_blank" rel="noopener noreferrer"><span>${escapeHtml(zh)}</span><small>${escapeHtml(en)} ↗</small></a>`).join('')}</div></section>
      <div class="wm-footnote">版权说明：本页优先展示由馆方 API 明确标记为 Public Domain / Open Access 或 CC0 的图像。未核验开放许可的作品只显示元数据和馆方来源链接。作品文字介绍为万物博物馆的简短导览，不替代馆方研究资料。</div>`;
  }
  function detail(item) {
    showModal('世界名馆 · 作品档案', `<div class="wm-detail">${item.image_url?`<img src="${escapeHtml(item.image_url)}" alt="${escapeHtml(item.title)}" referrerpolicy="no-referrer">`:''}<div><div class="eyebrow">${escapeHtml(item.museum)}</div><h2>${escapeHtml(item.title)}</h2><p class="wm-detail-en">${escapeHtml(item.title_en||'')}</p><p>${escapeHtml(item.note||'')}</p><dl><dt>创作者</dt><dd>${escapeHtml(item.artist||'未提供')}</dd><dt>年代</dt><dd>${escapeHtml(item.date||'未提供')}</dd><dt>媒材</dt><dd>${escapeHtml(item.medium||'未提供')}</dd><dt>文化／地区</dt><dd>${escapeHtml(item.culture||'未提供')}</dd><dt>部门</dt><dd>${escapeHtml(item.department||'馆方未提供')}</dd><dt>开放许可</dt><dd>${escapeHtml(item.license||'待核验')}</dd><dt>作品来源</dt><dd><a href="${escapeHtml(item.source_url)}" target="_blank" rel="noopener noreferrer">打开馆方原始档案 ↗</a></dd><dt>许可说明</dt><dd><a href="${escapeHtml(item.license_url)}" target="_blank" rel="noopener noreferrer">查看馆方图像与数据政策 ↗</a></dd></dl><div class="wm-detail-actions"><button class="primary" data-world-action="collect" data-id="${escapeHtml(item.id)}" ${item.collected?'disabled':''}>${item.collected?'✓ 已收入馆藏':'＋ 收入我的博物馆'}</button><button class="ghost" data-action="close">返回典藏</button></div></div></div>`);
  }
  document.addEventListener('submit', e => {
    if (e.target.id !== 'worldMuseumSearch') return;
    e.preventDefault();
    const fd = new FormData(e.target);
    W.q = String(fd.get('q') || '').trim(); W.museum = String(fd.get('museum') || '全部');
    render().then(html => { const main = document.querySelector('#main'); if (main && window.S?.view === 'world-museums') main.innerHTML = html; });
  });
  document.addEventListener('click', async e => {
    const b = e.target.closest('[data-world-action]'); if (!b) return;
    const action = b.dataset.worldAction, id = b.dataset.id;
    try {
      if (action === 'clear') { W.q=''; W.museum='全部'; const html=await render(); const main=document.querySelector('#main'); if(main)main.innerHTML=html; }
      else if (action === 'details') { const item=W.items.find(x=>x.id===id); if(item)detail(item); }
      else if (action === 'collect') {
        if (!window.S?.user) { if (typeof mustLogin === 'function') mustLogin(); else toast('请先登录'); return; }
        b.disabled = true;
        const result = await api(`/world-museums/${encodeURIComponent(id)}/collect`, { method: 'POST' });
        toast(result.already_collected ? '这件作品已经在你的博物馆里了' : '已收入你的博物馆，并默认设为私密');
        const html = await render(); const main = document.querySelector('#main'); if (main && window.S?.view === 'world-museums') main.innerHTML = html;
      }
    } catch (err) { toast(err.message); b.disabled = false; }
  });
  return { render };
})();
window.WorldMuseums = WorldMuseums;