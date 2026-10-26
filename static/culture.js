/* Wonder Atlas V9 — contemporary culture, meme discovery, digital products and games.
   Live feeds are explicitly labelled; fallback cards are curated links, never fabricated live rankings. */
(() => {
  'use strict';
  const C = {
    tab: 'memes', q: '', memes: [], memeOffset: 0, memeHasMore: false, memeLoading: false, memeError: '',
    tech: [], techLoading: false, techLoaded: false, techError: '',
    gameDeck: [], gameMoves: 0, gameMatches: 0, gameFirst: null, gameLock: false, gameRound: 0
  };
  const $ = s => document.querySelector(s);
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const categories = {
    digital: [
      {title:'Raspberry Pi · 单板电脑', kind:'开源硬件', desc:'把一台小电脑变成家庭服务器、机器人控制器或创客实验平台。', url:'https://www.raspberrypi.com/products/', tags:'Raspberry Pi,单板电脑,硬件'},
      {title:'Framework · 模块化笔记本', kind:'可维修设计', desc:'关注可维修、可升级的笔记本设计，以及硬件开放程度。', url:'https://frame.work/', tags:'Framework,笔记本,模块化'},
      {title:'Steam Deck · 掌上 PC 游戏设备', kind:'游戏硬件', desc:'掌上设备与 PC 游戏生态的交叉案例。', url:'https://www.steamdeck.com/', tags:'Steam Deck,掌机,游戏硬件'},
      {title:'DJI · 无人机与影像设备', kind:'影像科技', desc:'从航拍、云台到小型影像设备，观察消费级机器人如何进入日常生活。', url:'https://www.dji.com/', tags:'DJI,无人机,影像'},
      {title:'Arduino · 创客电子', kind:'开源生态', desc:'从传感器、微控制器到互动装置，适合把想法变成真实物件。', url:'https://www.arduino.cc/', tags:'Arduino,创客,电子'},
      {title:'Nothing · 透明设计语言', kind:'工业设计', desc:'观察手机与音频产品如何用视觉语言形成品牌辨识度。', url:'https://nothing.tech/', tags:'Nothing,手机,工业设计'}
    ],
    games: [
      {title:'OpenTTD', kind:'运输经营模拟', desc:'从铁路、公路和运输网络开始，慢慢搭建自己的系统。', url:'https://www.openttd.org/', tags:'OpenTTD,模拟,开源游戏'},
      {title:'0 A.D.', kind:'历史即时战略', desc:'以古代文明为主题的开源即时战略游戏项目。', url:'https://play0ad.com/', tags:'0 A.D.,即时战略,历史'},
      {title:'SuperTuxKart', kind:'卡丁车竞速', desc:'一款开源卡丁车竞速游戏，适合短时间体验。', url:'https://supertuxkart.net/', tags:'SuperTuxKart,竞速,开源游戏'},
      {title:'Luanti', kind:'沙盒与模组', desc:'体素沙盒引擎与社区内容，可探索不同世界和玩法。', url:'https://www.luanti.org/', tags:'Luanti,沙盒,模组'},
      {title:'Veloren', kind:'开放世界 RPG', desc:'社区驱动的开源多人角色扮演游戏项目。', url:'https://veloren.net/', tags:'Veloren,RPG,开源游戏'},
      {title:'Endless Sky', kind:'太空探索', desc:'探索星系、贸易、战斗与任务构成的开放式太空游戏。', url:'https://endless-sky.github.io/', tags:'Endless Sky,太空,开源游戏'},
      {title:'itch.io 免费游戏', kind:'独立游戏发现', desc:'从短篇实验游戏到独立作品，适合发现不常见的玩法。', url:'https://itch.io/games/free', tags:'itch.io,独立游戏,免费游戏'},
      {title:'GitHub 开源游戏', kind:'源代码与玩法', desc:'直接探索游戏源码、小游戏引擎和开发者作品。', url:'https://github.com/topics/open-source-game', tags:'GitHub,开源游戏,编程'}
    ]
  };
  const tabLabels = {memes:'热梗档案', digital:'数码产品', games:'游戏专区'};
  function liveBadge(text='外部公开数据') { return `<span class="culture-live-badge"><i></i>${esc(text)}</span>`; }
  function itemCard(item, type) {
    const title = item.title || item.name || '未命名发现';
    const desc = item.summary || item.description || item.desc || '';
    const image = item.cover_url || item.image || '';
    const kind = item.kind || (type === 'meme' ? '公开梗词条' : type === 'tech' ? 'Hacker News' : '精选入口');
    const id = type === 'meme' ? item.slug : type === 'tech' ? item.objectID : item.url;
    const sourceUrl = type === 'meme' ? `https://cnmeme.wiki/api/v1/public/memes/${encodeURIComponent(item.slug)}` : type === 'tech' ? (item.url || `https://news.ycombinator.com/item?id=${item.objectID}`) : item.url;
    const url = type === 'meme' ? 'https://cnmeme.wiki' : sourceUrl;
    const source = type === 'meme' ? '梗Wiki' : type === 'tech' ? 'Hacker News' : '官方入口';
    const tags = type === 'meme' ? (item.tags || []).slice(0,4) : type === 'tech' ? [`${item.points || 0} points`, item.created_at ? item.created_at.slice(0,10) : '科技动态'] : [item.kind || '精选入口'];
    const saveData = {title, description: desc.slice(0,600), story: type === 'meme' ? `公开词条 slug：${item.slug}\n来源：梗Wiki 公开只读 API。\n标签：${(item.tags||[]).join('、')}` : type === 'tech' ? `来源：Hacker News 前台动态。\n分数：${item.points || 0}\n发布日期：${item.created_at || '未知'}` : `万物博物馆精选入口。\n类型：${kind}\n来源为官方/项目网站，详细信息以原站为准。`, category: type === 'meme' ? '流行文化' : type === 'tech' ? '科技与发明' : type === 'game' ? '游戏与交互' : '科技与发明', tags: tags.join(','), image_url: image.startsWith('https://') ? image : '', source_url: sourceUrl, visibility: 'private' };
    return `<article class="culture-card">
      <div class="culture-card-cover ${image ? 'has-image' : ''}">${image ? `<img src="${esc(image)}" loading="lazy" alt="${esc(title)}" onerror="this.remove()">` : `<span>${type==='meme'?'😂':type==='tech'?'⚡':type==='game'?'🎮':'⌘'}</span>`}<small>${esc(kind)}</small></div>
      <div class="culture-card-body"><div class="culture-card-source">${esc(source)}</div><h3>${esc(title)}</h3><p>${esc(desc || '打开原始资料，继续探索这件有趣的发现。')}</p><div class="culture-tags">${tags.map(t=>`<span># ${esc(t)}</span>`).join('')}</div><div class="culture-card-actions"><a href="${esc(url)}" target="_blank" rel="noopener noreferrer">查看来源 ↗</a><button data-action="culture-save" data-item="${encodeURIComponent(JSON.stringify(saveData))}">收入我的博物馆 ＋</button></div></div>
    </article>`;
  }
  function memePanel() {
    return `<div class="culture-panel-head"><div><div class="eyebrow">MEME ARCHIVE · 梗的来历也值得收藏</div><h2>热梗档案</h2><p>读取公开词条，记录梗的含义、来源与变化。热度不等于真相，来源也不代表版权许可。</p></div>${liveBadge('梗Wiki 公开只读 API')}</div>
      <div class="culture-search"><input id="cultureMemeQuery" value="${esc(C.q)}" maxlength="80" placeholder="搜索梗、流行语或关键词…"><button class="primary" data-action="culture-search-meme">搜索</button><button class="ghost" data-action="culture-refresh-meme">查看最新公开词条</button></div>
      <div class="culture-note">内容来自 <a href="https://cnmeme.wiki/developers/api" target="_blank" rel="noopener noreferrer">梗Wiki 开发者 API ↗</a>。外部 API 不可用时会显示错误提示，不会用伪造的“实时热梗”替代。</div>
      <div id="cultureMemeResults" class="culture-grid">${C.memeLoading ? '<div class="culture-state">正在读取公开词条…</div>' : C.memes.length ? C.memes.map(x=>itemCard(x,'meme')).join('') : `<div class="culture-state">${C.memeError ? esc(C.memeError) : '正在连接梗Wiki…'}</div>`}</div>
      ${C.memeHasMore ? '<div class="culture-loadmore"><button class="ghost" data-action="culture-more-memes" '+(C.memeLoading?'disabled':'')+'>加载更多公开词条</button></div>' : ''}`;
  }
  function digitalPanel() {
    return `<div class="culture-panel-head"><div><div class="eyebrow">DIGITAL OBJECTS · 设计、硬件与新技术</div><h2>数码产品与奇特设备</h2><p>从手机、掌机、模块化电脑到创客硬件。下方是精选官方入口，不代表销量排名或实时新品榜。</p></div>${liveBadge('精选官方入口')}</div>
      <div class="culture-subtitle"><h3>产品与设计收藏</h3><span>官方资料 · 可私藏</span></div><div class="culture-grid">${categories.digital.map(x=>itemCard(x,'digital')).join('')}</div>
      <div class="culture-subtitle"><div><h3>正在发生的科技动态</h3><p>来自 Hacker News 前台故事；这不是专门的数码销量榜。</p></div>${liveBadge('尝试实时读取')}</div>
      <div class="culture-grid" id="cultureTechResults">${C.techLoading ? '<div class="culture-state">正在读取科技动态…</div>' : C.tech.length ? C.tech.map(x=>itemCard(x,'tech')).join('') : `<div class="culture-state">${C.techError ? esc(C.techError) : '正在连接公开科技动态…'}</div>`}</div>
      <div class="culture-note">更多发现入口：<a href="https://www.producthunt.com/" target="_blank" rel="noopener noreferrer">Product Hunt</a> · <a href="https://github.com/trending" target="_blank" rel="noopener noreferrer">GitHub Trending</a> · <a href="https://www.theverge.com/tech" target="_blank" rel="noopener noreferrer">The Verge Tech</a> · <a href="https://www.gsmarena.com/" target="_blank" rel="noopener noreferrer">GSMArena</a></div>`;
  }
  function initGame() {
    const symbols = ['💎','🖼️','🛰️','🎮','🐒','🧠'];
    C.gameDeck = [...symbols, ...symbols].map((symbol,i)=>({id:i,symbol,pair:symbol,flipped:false,matched:false})).sort(()=>Math.random()-.5);
    C.gameMoves = 0; C.gameMatches = 0; C.gameFirst = null; C.gameLock = false; C.gameRound++;
  }
  function gamesPanel() {
    if (!C.gameDeck.length) initGame();
    return `<div class="culture-panel-head"><div><div class="eyebrow">PLAYABLE ARCHIVE · 游戏也是展品</div><h2>游戏专区</h2><p>从开源游戏和独立游戏入口出发，也可以直接试玩一个小型馆藏记忆挑战。</p></div>${liveBadge('精选项目入口')}</div>
      <div class="culture-subtitle"><h3>开源与独立游戏</h3><span>链接指向项目官网或官方发现页</span></div><div class="culture-grid">${categories.games.map(x=>itemCard(x,'game')).join('')}</div>
      <section class="culture-mini-game"><div class="culture-mini-game-head"><div><div class="eyebrow">MINI EXHIBIT · MEMORY MATCH</div><h3>馆藏记忆挑战</h3><p>翻开两张卡片，找出相同的藏品符号。每一轮都是本地小游戏，不上传游戏操作。</p></div><div class="culture-game-score"><b>${C.gameMatches}/6</b><small>已配对</small><b>${C.gameMoves}</b><small>翻牌次数</small></div></div>
      <div class="culture-memory-grid">${C.gameDeck.map((x,i)=>`<button class="culture-memory-card ${x.flipped||x.matched?'revealed':''} ${x.matched?'matched':''}" data-action="culture-flip" data-index="${i}" ${x.matched||x.flipped||C.gameLock?'disabled':''} aria-label="记忆卡 ${i+1}"><span>${x.flipped||x.matched?x.symbol:'✳'}</span></button>`).join('')}</div>
      <div class="culture-mini-game-foot"><span>${C.gameMatches===6?'🎉 全部配对成功！再来一局？':'找出 6 组相同符号。慢一点观察，记住它们的位置。'}</span><button class="ghost" data-action="culture-new-game">重新开始 ↻</button></div></section>`;
  }
  function panel() { return C.tab==='memes'?memePanel():C.tab==='digital'?digitalPanel():gamesPanel(); }
  function render() {
    const html = `<section class="culture-hero"><div class="eyebrow">CONTEMPORARY CULTURE · V9</div><h1>正在流行的，<br><span>也值得被收藏。</span></h1><p>热梗、数码产品、游戏和新奇科技都使用同一套展品系统。收藏之后可以放进自己的展厅、加入回忆剧场，或在跨界探索中与其他领域建立联系。</p><div class="culture-hero-pills"><span>😂 网络文化</span><span>💻 数码产品</span><span>🎮 游戏档案</span><span>⚡ 新奇科技</span></div></section>
      <nav class="culture-tabs" aria-label="当代新奇分类">${Object.entries(tabLabels).map(([k,v])=>`<button data-action="culture-tab" data-tab="${k}" class="${C.tab===k?'active':''}">${v}</button>`).join('')}</nav>
      <section id="culturePanel" class="culture-panel">${panel()}</section>
      <div class="culture-footer-note">万物博物馆不把“热门”当成唯一价值：经典、冷门、实验性作品和用户原创也都值得收藏。外部内容的可见性与使用许可以原始来源为准。</div>`;
    setTimeout(()=>{if(C.tab==='memes'&&!C.memes.length&&!C.memeLoading)loadMemes();else if(C.tab==='digital'&&!C.techLoaded&&!C.techLoading)loadTech();},30);
    return html;
  }
  function updatePanel() { const p=$('#culturePanel'); if(p) p.innerHTML=panel(); }
  async function loadMemes({append=false}={}) {
    if(C.memeLoading) return;
    C.memeLoading=true; C.memeError=''; updatePanel();
    try {
      const params=new URLSearchParams({q:C.q,limit:'20',offset:String(append?C.memeOffset:0)});
      const r=await fetch('https://cnmeme.wiki/api/v1/public/memes?'+params.toString(),{credentials:'omit',signal:AbortSignal.timeout(10000)});
      if(!r.ok) throw new Error(`梗Wiki 返回 HTTP ${r.status}。可以稍后重试或直接访问官方词条库。`);
      const data=await r.json();
      C.memes=append?[...C.memes,...(data.items||[])]: (data.items||[]);
      C.memeOffset=(append?C.memeOffset:0)+((data.items||[]).length);
      C.memeHasMore=!!data.has_more; C.memeLoading=false;
      if(!C.memes.length) C.memeError='没有找到匹配的公开词条。试试更短的关键词，或清空搜索查看最新条目。';
    } catch(e) { C.memeLoading=false; C.memeError='暂时无法读取梗Wiki公开数据：'+(e.message||'网络错误')+'。请检查网络，或打开官方 API 文档。'; }
    updatePanel();
  }
  async function loadTech() {
    if(C.techLoading||C.techLoaded)return;
    C.techLoading=true; C.techError=''; updatePanel();
    try {
      const r=await fetch('https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=18',{credentials:'omit',signal:AbortSignal.timeout(10000)});
      if(!r.ok)throw new Error('Hacker News 暂时不可用。');
      const data=await r.json();
      C.tech=(data.hits||[]).filter(x=>x.title||x.story_title).slice(0,12).map(x=>({...x,title:x.title||x.story_title,summary:x.story_text||'来自 Hacker News 前台的公开科技动态。',created_at:x.created_at}));
      C.techLoaded=true;
      if(!C.tech.length)C.techError='当前没有可展示的前台故事。';
    }catch(e){C.techError='暂时无法读取实时科技动态：'+(e.message||'网络错误')+'。可以通过 Hacker News 官方入口继续浏览。';}
    C.techLoading=false; updatePanel();
  }
  async function saveItem(data) {
    if(!mustLogin())return;
    try {
      const payload={title:String(data.title||'未命名展品').slice(0,100),description:String(data.description||'').slice(0,600),story:String(data.story||'').slice(0,5000),category:data.category||'其他',tags:String(data.tags||'').slice(0,200),image_url:String(data.image_url||'').startsWith('https://')?data.image_url:'',source_url:String(data.source_url||'').startsWith('https://')?data.source_url:'',visibility:'private'};
      const saved=await api('/exhibits',{method:'POST',body:payload});
      if(window.WonderAnalytics)WonderAnalytics.track('modern_culture','save');
      toast('已收入你的私人博物馆');
      if(confirm('收藏成功！要现在打开这件展品的档案吗？')) await window.openDetail?.(saved.id);
    } catch(e) { toast(e.message||'保存失败'); }
  }
  document.addEventListener('click', async e=>{
    const b=e.target.closest('[data-action^="culture-"]'); if(!b)return;
    const action=b.dataset.action;
    try {
      if(action==='culture-tab') { C.tab=b.dataset.tab; if(C.tab==='games'&&!C.gameDeck.length)initGame(); updatePanel(); document.querySelectorAll('.culture-tabs button').forEach(x=>x.classList.toggle('active',x.dataset.tab===C.tab)); if(C.tab==='memes'&&!C.memes.length)loadMemes(); if(C.tab==='digital'&&!C.techLoaded)loadTech(); if(window.WonderAnalytics)WonderAnalytics.track('modern_culture','tab_'+C.tab); }
      else if(action==='culture-search-meme') { C.q=$('#cultureMemeQuery')?.value?.trim()||''; C.memeOffset=0; await loadMemes(); }
      else if(action==='culture-refresh-meme') { C.q=''; C.memeOffset=0; if($('#cultureMemeQuery'))$('#cultureMemeQuery').value=''; await loadMemes(); }
      else if(action==='culture-more-memes') { await loadMemes({append:true}); }
      else if(action==='culture-save') { let data; try{data=JSON.parse(decodeURIComponent(b.dataset.item||''))}catch{throw Error('无法读取这条展品信息')} await saveItem(data); }
      else if(action==='culture-new-game') { initGame(); updatePanel(); }
      else if(action==='culture-flip') {
        if(C.gameLock)return; const i=Number(b.dataset.index), card=C.gameDeck[i]; if(!card||card.flipped||card.matched)return;
        card.flipped=true; if(C.gameFirst===null){C.gameFirst=i;updatePanel();return;}
        C.gameMoves++; const first=C.gameDeck[C.gameFirst];
        if(first.pair===card.pair){first.matched=true;card.matched=true;C.gameMatches++;C.gameFirst=null;updatePanel();if(C.gameMatches===6&&window.WonderAnalytics)WonderAnalytics.track('modern_culture','game_complete');}
        else {C.gameLock=true;updatePanel();setTimeout(()=>{first.flipped=false;card.flipped=false;C.gameFirst=null;C.gameLock=false;updatePanel()},720);}
      }
    } catch(err) { toast(err.message||'操作失败'); }
  });
  document.addEventListener('keydown',e=>{if(e.key==='Enter'&&e.target?.id==='cultureMemeQuery'){e.preventDefault();document.querySelector('[data-action="culture-search-meme"]')?.click();}});
  window.WonderCulture={render,refresh:()=>C.tab==='memes'?loadMemes():loadTech()};
})();