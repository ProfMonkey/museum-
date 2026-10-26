/* Wonder Atlas V3 | distinctive modules, one shared content system, no fabricated community data. */
const FEATURE_META=[
['关联探索','从一件藏品出发，发现其他相关事物','沿着有理由的联系，走进另一位馆长的世界。','✧'],
['奇物调查','把不认识的东西变成公开调查','收集线索、猜想和来源，逐步接近答案。','⌕'],
['不同角度看','同一件物品，不同的人有不同理解','把不同馆长的观点并排放在一起。','◇'],
['时光记录','记录一件东西在不同时间发生的变化','保存见证，而不只记录上传时间。','◷'],
['互动故事','你的选择会改变故事走向','创建分支，让访客选择自己的结局。','⟡'],
['身边的奇物','把线上发现带回真实世界','记录城市、校园和街区里的有趣事物。','⌖'],
['网页小猴子','让 ProfMonkey 在网页里活动','走动、睡觉、吃香蕉，随时可以关闭。','♙'],
['奇物接龙','大家接着同一条故事继续创作','上一件藏品，是下一段故事的开场白。','↝'],
['小猴导览','让小猴按真实馆藏带你参观','按主题整理展品，不编造没有来源的知识。','♔'],
['动手玩展品','调节参数，观察模型变化','先动手试，再理解背后的概念。','⚗'],
['一起逛博物馆','邀请朋友同时看展品和聊天','共享房间、同步展品、一起讨论。','♧'],
['藏品来源','查看展品的来源、署名和修改记录','让每件公开展品都尽量说清来处。','▤'],
['我的兴趣地图','看看自己的收藏主要集中在哪些领域','只在本地统计你的馆藏，不自动公开。','◈']
];
const FEATURE_GUIDES=[
 {what:'从一件展品出发，沿着有理由的关联走向另一件展品。',steps:['先选一件公开展品作为起点。','点击关联卡片：实线是馆主确认的关联，虚线是系统按标签/分类给出的候选。','如果你是起点展品的馆主，可以写明理由，保存一条跨馆关联。'],twist:'试着把两个看似毫无关系的领域连起来；关联理由越具体，下一位探索者越容易理解。'},
 {what:'把无法解释的东西变成一份可以共同调查的公开案卷。',steps:['选择自己发布的公开展品并写出一个清晰的问题。','其他馆主提交“证据线索”或“个人假设”，两者不会混为一谈。','馆主更新状态时需要说明理由，历史记录会保留。'],twist:'欢迎提交反例和“目前无法确定”；票数高不等于事实已证实。'},
 {what:'让不同的人对同一件东西保留不同的理解，而不是争出唯一答案。',steps:['选择一件公开展品。','写下自己的观察角度，例如设计师、工程师、童年记忆或艺术视角。','其他人的观点会并排展示；同一账号可以更新自己的观点。'],twist:'尽量写出“同一件东西为什么会让不同的人想到不同的事”。'},
 {what:'记录一件事物在不同时间点发生了什么。',steps:['选择公开展品。','添加事件发生日期、见证描述和可选来源链接。','时间轴按事件时间排列，并同时显示投稿时间。'],twist:'可以记录校园角落、旧设备、老店或一项技术的变化；投稿见证不自动等于已核实史料。'},
 {what:'创建一个有选择、有分支、有不同结局的互动小展览。',steps:['给展览起名并写开场白。','设置两个选择，以及各自对应的结局。','发布后，访客可以选择不同分支体验。'],twist:'把知识做成“如果当时选了另一条路会怎样”的小实验。当前版本是简化的双分支编辑器，还不是自由拖拽的节点画布。'},
 {what:'把一件公开展品与城市或街区联系起来，让线上发现通往现实。',steps:['选择公开展品。','填写城市、街区和值得探访的理由。','其他人可从地点卡片进入对应展品。'],twist:'适合做“校园奇物地图”或“城市细节收集”；当前版本不接真实地图、不收 GPS，也不建议公开私人住址。'},
 {what:'让 ProfMonkey 在网页里活动，为浏览过程增加一点调皮的陪伴。',steps:['选择 1–6 只猴子。','切换安静模式、猴山模式或关闭。','可以拖动猴子、点击互动，或触发吃香蕉小剧场。'],twist:'网页猴只在本站活动，不会跑到 Windows 桌面；偏好保存在当前浏览器。'},
 {what:'让不同用户轮流选择展品，把一条故事链共同接下去。',steps:['从一件公开展品发起故事链并写明起因。','下一位用户选择另一件公开展品，解释它如何接上前一段。','链条会展示每一段的展品、理由和接力者。'],twist:'接力不是自动推荐：每个人都要亲自做选择并解释连接；同一个账号不能连续接两次。'},
 {what:'根据真实公开馆藏，快速组成一个专题导览。',steps:['选择科学、自然、技术、故事或艺术主题。','浏览由公开展品标题、分类和简介组成的导览卡。','点击展品继续阅读原始档案。'],twist:'可把导览当作策展草稿；目前使用确定性模板，不调用 AI，也不会把缺少来源的内容说成事实。'},
 {what:'通过可调参数观察一个安全的视觉演示如何变化。',steps:['拖动光照强度滑块。','观察植物模型的亮度变化和文字提示。','点击恢复初始条件，重新开始。'],twist:'后续可以扩展成钟表、齿轮、算法步骤等互动展品；当前是教学视觉模型，不代表真实生物实验数据。'},
 {what:'邀请别人进入同一参观房间，共同看展品并留言。',steps:['选一件公开展品，创建参观房间。','把房间码发给其他已登录用户。','主持人可切换当前展品，所有成员可文字交流。'],twist:'适合宿舍夜聊、读书会或线上小型导览；当前约每 7 秒同步一次，没有音视频。'},
 {what:'给展品建立来源、署名、许可声明和修改轨迹。',steps:['选择公开展品并查看护照。','馆主补充原始来源、原作者/发现者、许可与说明。','后续修改会留下修订记录。'],twist:'来源信息是馆主声明，不代表平台已经独立核验；转载内容请先确认授权。'},
 {what:'把你自己的馆藏主题做成一张兴趣星图。',steps:['登录并积累一些自己的展品。','系统在浏览器里按分类统计馆藏数量。','查看各主题占比，判断自己的收藏世界由什么组成。'],twist:'这不是人格测试；当前只统计分类，不上传额外画像，也不会自动公开。'}
];
const W={active:null,selected:null,room:null,caseId:null,chainId:null,storyId:null,roomCode:'',roomTimer:null,labValue:50,collisionPair:null,collisionReason:'',blindGame:null,memoryGame:{phase:'idle'},memoryTimer:null,pairGame:{phase:'idle'},futureItemId:null,futureDraft:'',futureSaved:JSON.parse(localStorage.getItem('wa-future-notes')||'[]'),collisionNote:'',monkeyMode:localStorage.getItem('wa-monkey-mode')||'quiet',monkeyCount:Math.max(1,Math.min(6,Number(localStorage.getItem('wa-monkey-count'))||1))};
const fe=n=>E(n), fcode=n=>'E'+String(n).padStart(2,'0');
function fimage(n){return `/static/assets/covers/e${String(Math.min(n,12)).padStart(2,'0')}.webp`}
function fbutton(label,action,value='',cls=''){return `<button class="${cls||'feature-btn'}" data-wa="${action}" data-value="${fe(value)}">${label}</button>`}
function featureTitle(n){let f=FEATURE_META[n-1];return `<div class="feature-banner" style="--feature-image:url('${fimage(n)}')"><div class="feature-banner-text"><small>WONDER ATLAS / ${fcode(n)}</small><h1>${fe(f[0])}</h1><p>${fe(f[1])}</p><span>${fe(f[2])}</span><div style="margin-top:20px">${fbutton('← 特色工程总览','home')}</div></div></div>`}
function usageCard(title,desc,action,view,icon){return `<button class="nav-guide-card" data-action="navigate" data-view="${view}"><span>${icon}</span><b>${title}</b><small>${desc}</small><i>${action} →</i></button>`}
function readGameStats(){
 try{return Object.assign({played:0,correct:0,points:0},JSON.parse(localStorage.getItem('wa-minigame-stats')||'{}'))}
 catch{return {played:0,correct:0,points:0}}
}
function recordMiniGame(game,correct){
 const stats=readGameStats();stats.played+=1;if(correct){stats.correct+=1;stats.points+=10}
 stats[game]=(stats[game]||0)+1;localStorage.setItem('wa-minigame-stats',JSON.stringify(stats));
}
function shuffleItems(items){const out=[...items];for(let i=out.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[out[i],out[j]]=[out[j],out[i]]}return out}
function randomItem(items){return items.length?items[Math.floor(Math.random()*items.length)]:null}
function uniqueTitleItems(feed){const seen=new Set();return feed.filter(x=>{const key=String(x.title||'').trim().toLocaleLowerCase();if(!key||seen.has(key))return false;seen.add(key);return true})}
function makeBlindRound(feed){
 const pool=uniqueTitleItems(feed);if(pool.length<4)return null;
 const target=randomItem(pool),decoys=shuffleItems(pool.filter(x=>x.id!==target.id)).slice(0,3);
 return {targetId:target.id,options:shuffleItems([target,...decoys]).map(x=>x.id),answered:false,selected:null,correct:null};
}
function makeMemoryRound(feed){
 const pool=uniqueTitleItems(feed);if(pool.length<4)return null;
 const target=randomItem(pool),others=shuffleItems(pool.filter(x=>x.id!==target.id)).slice(0,3);
 return {phase:'show',targetId:target.id,options:shuffleItems([target,...others]).map(x=>x.id),selectedId:null,correct:null};
}
function makePairRound(feed){
 feed=uniqueTitleItems(feed);
 const groups={};feed.forEach(x=>{const c=x.category||'其他';(groups[c]||(groups[c]=[])).push(x)});
 const possible=Object.values(groups).filter(g=>g.length>=2&&feed.filter(x=>(x.category||'其他')!==(g[0].category||'其他')).length>=2);
 if(!possible.length)return null;
 const group=randomItem(possible),target=randomItem(group),match=randomItem(group.filter(x=>x.id!==target.id));
 const distractors=shuffleItems(feed.filter(x=>x.id!==target.id&&x.id!==match.id&&(x.category||'其他')!==(target.category||'其他'))).slice(0,2);
 if(distractors.length<2)return null;
 return {phase:'playing',targetId:target.id,matchId:match.id,options:shuffleItems([match,...distractors]).map(x=>x.id),selectedId:null,correct:null};
}
function gameArt(item,blur=false){
 if(!item)return '<div class="game-art"><div class="game-art-placeholder">✦</div></div>';
 return `<div class="game-art ${blur?'is-blurred':''}">${item.image_url?`<img src="${E(item.image_url)}" alt="${blur?'待猜测藏品':'藏品预览'}" loading="lazy">`:`<div class="game-art-placeholder">${blur?'？':'✦'}</div>`}<span class="game-art-id">展品 #${String(item.id).padStart(4,'0')}</span></div>`;
}
function gameStatsHtml(){const s=readGameStats(),rate=s.played?Math.round(s.correct/s.played*100):0;return `<div class="game-score"><span><b>${s.played}</b><small>已玩轮次</small></span><span><b>${rate}%</b><small>答对率</small></span><span><b>${s.points}</b><small>本机积分</small></span></div>`}
function blindGameHtml(feed){
 const g=W.blindGame,x=feed.find(i=>i.id===g?.targetId);
 if(!x){return uniqueTitleItems(feed).length<4?`${fempty('猜盲盒至少需要 4 件标题不同的公开藏品')}<button class="feature-btn" data-action="new">发布公开藏品</button>`:fempty('正在准备下一件盲盒');}
 const options=(g.options||[]).map(id=>{const item=feed.find(i=>i.id===Number(id));return item?`<button class="game-option" data-wa="blindbox-answer" data-value="${item.id}" ${g.answered?'disabled':''}>${fe(item.title)}</button>`:''}).join('');
 const clue=!x.image_url?(x.description||x.story||'这件藏品暂时没有图片或文字线索。').slice(0,110):'根据模糊的封面图，猜猜它是哪一件藏品。';
 const result=g.answered?`<div class="game-result ${g.correct?'is-correct':'is-wrong'}"><b>${g.correct?'认出来了！+10 分':'这次没猜中，再来一件。'}</b><p>正确答案：${fe(x.title)} · 分类：${fe(x.category||'其他')}</p><p>${fe(x.description||'馆主还没有补充介绍。')}</p><small>投稿者：${fe(x.owner||'馆长')}</small><div class="row-actions"><button class="feature-btn" data-wa="blindbox-next">再猜一件</button>${fbutton('查看藏品','view-exhibit',x.id)}</div></div>`:'';
 return `<div class="blind-game-stage">${gameArt(x,!g.answered)}<div class="blind-game-copy"><span class="eyebrow">BLIND BOX · 猜藏品</span><h3>${g.answered?fe(x.title):'你认得出这件藏品吗？'}</h3><p>${g.answered?'答案已经揭晓。':fe(clue)}</p>${g.answered?'':`<div class="game-options">${options}</div>`}</div></div>${result}`;
}
function memoryGameHtml(feed){
 const g=W.memoryGame||{phase:'idle'};const x=feed.find(i=>i.id===g.targetId);
 if(g.phase==='idle'||!x)return `<p class="game-description">记住一件真实藏品，等它消失后，从四个标题里找回刚才看到的那件。</p><button class="feature-btn" data-wa="memory-start" ${uniqueTitleItems(feed).length<4?'disabled':''}>开始记忆挑战</button>${uniqueTitleItems(feed).length<4?'<small class="local-note">至少需要 4 件标题不同的公开藏品。</small>':''}`;
 if(g.phase==='show')return `<div class="memory-target">${gameArt(x)}<div><span class="eyebrow">MEMORY FLASH · 记住它</span><h3>${fe(x.title)}</h3><p>${fe(x.description||'观察这件藏品的标题和封面。')}</p><strong>3 秒后隐藏，准备好了吗？</strong></div></div>`;
 if(g.phase==='guess')return `<p class="experiment-question">刚才闪过的是哪一件藏品？</p><div class="memory-options">${g.options.map(id=>{const item=feed.find(i=>i.id===id);return item?fbutton(fe(item.title),'memory-answer',id,'game-option'):''}).join('')}</div>`;
 const chosen=feed.find(i=>i.id===Number(g.selectedId));return `<div class="game-result ${g.correct?'is-correct':'is-wrong'}"><b>${g.correct?'记忆成功！+10 分':'没关系，再试一次。'}</b><p>刚才出现的藏品是「${fe(x.title)}」。${chosen&&chosen.id!==x.id?`你选了「${fe(chosen.title)}」。`:''}</p>${gameArt(x)}<div class="row-actions"><button class="feature-btn" data-wa="memory-next">再玩一轮</button>${fbutton('查看藏品','view-exhibit',x.id)}</div></div>`;
}
function pairGameHtml(feed){
 const g=W.pairGame||{phase:'idle'},target=feed.find(i=>i.id===g.targetId);
 if(g.phase==='idle'||!target)return `<p class="game-description">系统先选一件藏品，再从候选里找出与它属于同一分类的那一件。分类会暂时隐藏。</p><button class="feature-btn" data-wa="pair-start" ${uniqueTitleItems(feed).length<4?'disabled':''}>抽取配对题</button>${uniqueTitleItems(feed).length<4?'<small class="local-note">至少需要 4 件标题不同的公开藏品。</small>':''}`;
 if(g.phase==='playing')return `<div class="pair-target">${gameArt(target)}<div><span class="eyebrow">PAIR FINDER · 找同类</span><h3>${fe(target.title)}</h3><p>请从下面选择一件与它属于同一分类的藏品。</p></div></div><div class="pair-options">${g.options.map(id=>{const item=feed.find(i=>i.id===id);return item?`<button class="pair-option" data-wa="pair-answer" data-value="${item.id}">${gameArt(item)}<b>${fe(item.title)}</b></button>`:''}).join('')}</div>`;
 const selected=feed.find(i=>i.id===Number(g.selectedId)),match=feed.find(i=>i.id===Number(g.matchId));return `<div class="game-result ${g.correct?'is-correct':'is-wrong'}"><b>${g.correct?'配对成功！+10 分':'这次没配上。'}</b><p>「${fe(target.title)}」的分类是「${fe(target.category||'其他')}」；正确配对是「${fe(match?.title||'未知藏品')}」。${selected&&selected.id!==match?.id?`你选了「${fe(selected.title)}」。`:''}</p><div class="row-actions"><button class="feature-btn" data-wa="pair-next">再抽一题</button>${fbutton('查看目标藏品','view-exhibit',target.id)}</div></div>`;
}
function featureCovers(){
 const feedPromise=featuredFeed().catch(()=>[]);
 return feedPromise.then(feed=>{
  if(!W.collisionPair||!feed.some(x=>x.id===W.collisionPair.a.id)||!feed.some(x=>x.id===W.collisionPair.b.id))W.collisionPair=makeCollisionPair(feed);
  if(!W.blindGame||!feed.some(x=>x.id===W.blindGame.targetId))W.blindGame=makeBlindRound(feed);
  if(!W.futureItemId||!feed.some(x=>x.id===W.futureItemId))W.futureItemId=feed.length?randomItem(feed).id:null;
  if(W.memoryGame?.targetId&&!feed.some(x=>x.id===W.memoryGame.targetId))W.memoryGame={phase:'idle'};
  if(W.pairGame?.targetId&&!feed.some(x=>x.id===W.pairGame.targetId))W.pairGame={phase:'idle'};
  const pair=W.collisionPair,future=feed.find(x=>x.id===W.futureItemId),stats=readGameStats();
  const collision=pair?`<div class="collision-pair"><div class="collision-item">${art(pair.a,'collision-art')}<b>${fe(pair.a.title)}</b><small>${fe(pair.a.category)} · ${fe(pair.a.owner||'馆主')}</small></div><span class="collision-mark">×</span><div class="collision-item">${art(pair.b,'collision-art')}<b>${fe(pair.b.title)}</b><small>${fe(pair.b.category)} · ${fe(pair.b.owner||'馆主')}</small></div></div><p class="experiment-question">如果这两件东西在现实中相遇，会产生什么联系？</p><p class="feature-muted">${pair.a.category===pair.b.category?'这次是同领域碰撞，试着找出它们不同的用途。':'刻意跨领域配对：联系不必显而易见，但请给出自己的理由。'}</p><div class="row-actions"><button class="feature-btn" data-wa="collision-reroll">换一组奇物</button>${S.user&&pair.a.user_id===S.user.id?fbutton('把联系保存为关联','collision-save'):fbutton('进入关联探索','collision-open')}</div>`:`${fempty('公开展品不足，暂时无法碰撞')}<button class="feature-btn" data-action="new">发布一件公开展品</button>`;
  const futureHtml=future?`<div class="future-object">${art(future,'future-art')}<div><small>未来考古对象 · ${fe(future.category)}</small><h3>${fe(future.title)}</h3><p>${fe(future.description||'一件被后人重新发现的物品。')}</p></div></div><p class="experiment-question">一千年后，考古学家只找到它，却不知道今天的生活。你会怎样解释它？</p><textarea id="futureNote" class="future-note" maxlength="1000" placeholder="写下你的未来考古假说……">${fe(W.futureDraft)}</textarea><div class="row-actions"><button class="feature-btn" data-wa="future-reroll">换一件考古对象</button><button class="feature-btn" data-wa="future-save">保存我的假说</button></div>${W.futureSaved.length?`<div class="future-saved"><b>本浏览器保存的假说（${W.futureSaved.length}）</b>${W.futureSaved.slice(-3).reverse().map(n=>`<p><strong>${fe(n.title)}</strong>：${fe(n.note)} <small>${fe(n.date)}</small></p>`).join('')}</div>`:''}`:fempty('需要至少一件公开展品');
  return `<section class="feature-intro"><div class="eyebrow">WONDER ATLAS / THE COLLECTION OF WORLDS</div><h1>万物博物馆 · 特色玩法</h1><p>统一的黑金封面负责带你进入功能；这里新增基于真实公开藏品的小游戏。<br>玩完还能查看原始档案，继续探索。</p><div class="feature-tags"><span>12 项统一黑金封面</span><span>13 项特色功能</span><span>小游戏基于真实公开藏品</span></div></section>
  <section class="nav-guide"><div class="nav-guide-head"><div><div class="eyebrow">FIRST VISIT · QUICK GUIDE</div><h2>先认路，再开始收藏</h2><p>主导航各有分工，避免重复入口。</p></div></div><div class="nav-guide-grid">${usageCard('发现广场','浏览、搜索和发布公开展品','去发现','discover','⌁')}${usageCard('随机奇遇','不设关键词，随机遇见公开藏品','开始漫游','journey','✧')}${usageCard('心动收藏','保存别人的公开展品，方便以后回来','查看收藏','saved','♡')}${usageCard('我的博物馆','管理自己的藏品、展厅和隐私','建造世界','museum','▦')}${usageCard('通知中心','查看点赞、评论和关注提醒','查看消息','notifications','✉')}</div></section>
  <div class="features-grid">${FEATURE_META.slice(0,12).map((f,i)=>`<button class="feature-cover" data-wa="module" data-value="${i+1}" style="--cover:url('${fimage(i+1)}')"><span class="feature-cover-number">${fcode(i+1)}</span><span class="feature-cover-glyph">${f[3]}</span><span class="feature-cover-copy"><strong>${fe(f[0])}</strong><small>${fe(f[1])}</small></span><span class="feature-cover-footer"><i>点击进入 · 查看玩法说明</i><b>↗</b></span></button>`).join('')}</div>
  <button class="feature-last" data-wa="module" data-value="13"><span>E13 · MY INTEREST MAP</span><h2>我的兴趣地图</h2><p>看看自己的收藏主要集中在哪些领域。</p><span>进入兴趣地图 →</span></button>
  <section class="game-arcade"><div class="game-heading"><div><div class="eyebrow">EXHIBIT ARCADE · PLAY WITH REAL COLLECTIONS</div><h2>藏品游乐场</h2><p>题目来自服务器中的真实公开藏品；每局结束都可以回到原始档案。</p></div>${gameStatsHtml()}</div><div class="game-grid">
   <article class="game-card blindbox-card"><div class="game-card-head"><span>GAME 01 / OBSERVATION</span><h3>猜盲盒</h3><p>看模糊封面，从四个标题中猜出真实藏品。</p></div>${blindGameHtml(feed)}</article>
   <article class="game-card memory-card"><div class="game-card-head"><span>GAME 02 / MEMORY</span><h3>藏品闪记</h3><p>用几秒记住一件藏品，再从候选中找回它。</p></div>${memoryGameHtml(feed)}</article>
   <article class="game-card pair-card"><div class="game-card-head"><span>GAME 03 / MATCH</span><h3>同类配对</h3><p>从真实馆藏里，找出和目标属于同一分类的藏品。</p></div>${pairGameHtml(feed)}</article>
  </div><p class="game-footnote">战绩与积分保存在当前浏览器，不是全站排行榜；不会影响藏品真实性或用户权限。答对一题得 10 分。</p></section>
  <section class="experiment-lab"><div class="experiment-heading"><div class="eyebrow">IDEA WORKSHOP</div><h2>创意实验室</h2><p>小游戏之外，还有两种没有标准答案的创意玩法。</p></div><div class="experiment-grid creative-grid"><article class="experiment-card collision-card"><div class="experiment-card-head"><span>IDEA 01 / COLLISION</span><h3>奇物碰撞台</h3><p>把看似无关的两件东西放在一起，试着创造一条有理由的联系。</p></div>${collision}</article><article class="experiment-card future-card"><div class="experiment-card-head"><span>IDEA 02 / FUTURE ARCHAEOLOGY</span><h3>未来考古舱</h3><p>把今天的物品交给一千年后的考古学家，写下你的大胆解释。</p></div>${futureHtml}<small class="local-note">假说仅保存于当前浏览器，不会上传到服务器。</small></article></div></section>
  <div class="feature-note">所有工程共用同一套账号、藏品、权限与公开内容。小游戏使用真实公开藏品；游戏得分和未来考古假说目前仅保存在本地浏览器。</div>`;
 });
}
function makeCollisionPair(feed){
 if(!feed||feed.length<2)return null;
 const own=S.user?feed.filter(x=>x.user_id===S.user.id):[];
 const pool=own.length?own:feed;
 const a=pool[Math.floor(Math.random()*pool.length)];
 const candidates=feed.filter(x=>x.id!==a.id && x.category!==a.category);
 const fallback=feed.filter(x=>x.id!==a.id);
 const dest=candidates.length?candidates:fallback;
 const b=dest[Math.floor(Math.random()*dest.length)];
 return a&&b?{a,b}:null;
}
function featureGuide(n){const g=FEATURE_GUIDES[n-1];if(!g)return '';return `<section class="feature-guide"><div class="feature-guide-top"><span class="guide-seal">${fcode(n)}</span><div><div class="eyebrow">HOW TO USE THIS ROOM</div><h2>这里可以做什么？</h2><p>${fe(g.what)}</p></div></div><div class="feature-guide-steps">${g.steps.map((x,i)=>`<div class="feature-guide-step"><b>${i+1}</b><span>${fe(x)}</span></div>`).join('')}</div><div class="feature-guide-twist"><b>✦ 新奇玩法</b><span>${fe(g.twist)}</span></div></section>`}

function fbox(title,body,extra=''){return `<section class="feature-box ${extra}"><h2>${title}</h2>${body}</section>`}
function fempty(msg='还没有真实内容'){return `<div class="f-empty">${fe(msg)}<br><small>登录并发布公开展品后，就能开始收集。</small></div>`}
function fchoose(items, label='选择一件公开展品',selected=W.selected){return `<label class="f-select">${label}<select data-wa-change="selected"><option value="">— 请选择 —</option>${items.map(x=>`<option value="${x.id}" ${String(selected)===String(x.id)?'selected':''}>#${x.id} ${fe(x.title)} / ${fe(x.owner||'我的展品')}</option>`).join('')}</select></label>`}
function fform(fields,submit='保存'){return `<form class="f-form" data-wa-form="1">${fields}<button type="submit" class="primary">${submit}</button></form>`}
function input(n,placeholder,type='text',val=''){return `<input name="${n}" type="${type}" placeholder="${fe(placeholder)}" value="${fe(val)}" required ${type==='text'?'maxlength="300"':''}>`}
function ta(n,p,val=''){return `<textarea name="${n}" placeholder="${fe(p)}" rows="3" maxlength="1500" required>${fe(val)}</textarea>`}
function rowLink(x,action='select',value=x.id){return `<button class="f-row" data-wa="${action}" data-value="${fe(value)}"><span>${fe(x.title||x.question||x.name||'未命名')}</span><span>查看 →</span></button>`}
function fnotice(text){return `<p class="feature-muted">${text}</p>`}
async function featuredFeed(){let data=await api('/feed');return data.items||[]}
const analyticsFeatureKeys=['wormhole','mystery_cases','perspectives','timeline','interactive_exhibits','real_world_museum','living_monkey','collaboration','tour_guide','interactive_lab','shared_visit','provenance_passport','personal_world'];
async function featureModule(n){W.active=n;clearInterval(W.roomTimer);W.roomTimer=null;window.WonderAnalytics?.track(analyticsFeatureKeys[n-1]||'personal_world','open');await navigate('features');}
async function renderFeatures(){let n=W.active;if(!n)return await featureCovers();let area='';try{area=await featureBody(n)}catch(err){area=fbox('暂时无法载入',`<p>${fe(err.message)}</p>`)}return `<div class="feature-page">${featureTitle(n)}${featureGuide(n)}<div class="feature-workspace">${area}</div></div>`}
function ensureSelection(list){if(!list.some(x=>String(x.id)===String(W.selected)))W.selected=list[0]?.id||null}

async function featureBody(n){
const feed=await featuredFeed();ensureSelection(feed);
if(n===1){
 if(!W.selected)return fbox('关联探索',fempty('公开展品出现后，才能建立真实虫洞。'));
 let data=await api('/features/wormhole/'+W.selected),x=data.start;
 let nodes=data.links.map(l=>`<button data-wa="worm-next" data-value="${l.destination_id}" class="worm-node ${l.suggested?'suggested':''}"><b>${fe(l.destination_title)}</b><span>${fe(l.relation)}</span><small>${fe(l.reason)}</small></button>`).join('');
 const isOwner=!!(S.user&&x.user_id===S.user.id);
 return fbox('连接，从一件真实展品开始',`${fchoose(feed)}<div class="worm-map"><div class="worm-center"><small>STARTING POINT</small><strong>${fe(x.title)}</strong><span>◉</span></div><div class="worm-branches">${nodes||fempty('还没有可供探索的关联')}</div></div>${fnotice('虚线候选来自标签或分类相似度，不代表已核验的关联。馆主可提交明确的关联理由。')}`)+(isOwner?fbox('馆主确认一条关联',fform(`${input('destination_id','目标展品编号','number',W.collisionDestination||'')}<select name="relation"><option>同一主题</option><option>历史演化</option><option>相似用途</option><option>观点冲突</option><option>互相引用</option><option>跨界碰撞</option></select>${ta('reason','为什么这两件展品有关联？',W.collisionReason||'')}`,'建立关联')):fbox('如何把关联保存下来',fnotice(S.user?'只有起点展品的馆主可以确认关联。可以先选择自己发布的公开展品，再建立虫洞。':'登录并发布公开展品后，就能把自己的藏品与其他公开展品建立关联。')));
}
if(n===2){let cases=await api('/features/cases');let one=W.caseId?await api('/features/cases/'+W.caseId).catch(()=>null):null;
 return `<div class="feature-columns">${fbox('公开的奇物调查',cases.length?cases.map(q=>`<button class="f-row" data-wa="case" data-value="${q.id}"><b>${fe(q.question)}</b><span>${fe(q.state)} · ${q.clue_count} 条投稿</span></button>`).join(''):fempty('还没有人发起调查'))}${fbox('发起新调查',`<div class="feature-muted">仅展品馆主可以为自己的公开展品发起悬案。</div>${fchoose(feed)}${fform(ta('question','你想调查这件未知物品的什么问题？'),'发起公开调查')}`)}</div>`+(one?fbox(`调查档案 #${one.id} · ${fe(one.state)}`,`<h3>${fe(one.question)}</h3><h4>线索与证据</h4>${one.clues.filter(c=>c.kind==='evidence').map(c=>`<div class="f-dossier">${fe(c.body)} <small>— ${fe(c.author)} / 尚待核验</small></div>`).join('')||fempty('暂无线索')}<h4>待验证的假设</h4>${one.clues.filter(c=>c.kind==='hypothesis').map(c=>`<div class="f-dossier">${fe(c.body)} <small>— ${fe(c.author)} / 不是已证实结论</small></div>`).join('')||fempty('暂无假设')}<h4>追加调查记录</h4>${fform(`<select name="kind"><option value="evidence">证据线索</option><option value="hypothesis">个人假设</option></select>${ta('body','写出线索、依据或反例')}<input name="source_url" placeholder="来源 URL（可选）">`,'提交调查线索')}<h4>悬案处理历史</h4>${one.history.map(h=>`<p class="feature-muted">${fe(h.created_at.slice(0,10))} · ${fe(h.state)} · ${fe(h.reason)}</p>`).join('')}${S.user&&S.user.id===one.owner_id?`<div class="row-actions">${['有线索','待核验','已解决','存争议'].map(s=>fbutton(s,'case-state',s)).join('')}</div>`:''}`):'');
}
if(n===3){if(!W.selected)return fbox('不同角度看',fempty());let x=feed.find(e=>e.id===Number(W.selected)),arr=await api(`/features/exhibits/${W.selected}/perspectives`);
 return `<div class="feature-columns">${fbox('选择共同欣赏的展品',`${fchoose(feed)}${x?`<div class="object-stage">${art(x)}<h3>${fe(x.title)}</h3><p>${fe(x.description)}</p></div>`:''}`)}${fbox('一物 · 多种视角',arr.length?arr.map(p=>`<div class="f-dossier"><b>${fe(p.angle)}</b><p>${fe(p.body)}</p><small>— ${fe(p.author)}</small></div>`).join(''):fempty('还没有其他人的解读'))}</div>${fbox('留下你的观点',fform(`${input('angle','我的观察角度（如工程师 / 童年回忆）')}${ta('text','它在你的眼里是什么？')}`,'保存我的视角'))}`;
}
if(n===4){if(!W.selected)return fbox('时光记录',fempty());let entries=await api(`/features/exhibits/${W.selected}/events`);
 return fbox('物件的时间长廊',`${fchoose(feed)}<div class="timeline">${entries.map(x=>`<article class="time-point"><time>${fe(x.happened_at)}</time><div><p>${fe(x.description)}</p><small>投稿：${fe(x.author)} · 上传 ${fe(x.created_at.slice(0,10))} ${x.source_url?' · 附来源链接':''}</small></div></article>`).join('')||fempty('这件展品还没有历史见证')}</div>`)+fbox('补充一次时间见证',fform(`${input('happened_at','事件发生日期，例如 1998-05-21')}${ta('description','这时发生了什么？你如何知道？')}<input name="source_url" placeholder="资料来源 URL（可选）">`,'记录时刻'));
}
if(n===5){let stories=await api('/features/stories');let one=stories.find(e=>e.id===W.storyId)||stories[0];if(!W.storyId&&one)W.storyId=one.id;
 return fbox('互动叙事工坊',`<div class="feature-introline">这里的分支展览由真实用户发布；选择后会在本站展示对应结局，不调用不可信脚本。</div><div class="f-pills">${stories.map(st=>fbutton(fe(st.title),'story',st.id)).join('')}</div>${one?`<div class="story-stage"><h2>${fe(one.title)}</h2><p>${fe(one.intro)}</p><h3>此刻，你会选择……</h3><div class="story-branches">${one.branches.map((branch,i)=>`<button class="story-choice" data-wa="story-choice" data-value="${i}">${fe(branch)} →</button>`).join('')}</div><div id="story-ending" class="feature-muted">选择一条路，开启不同的结局。</div></div>`:fempty('还没有互动展览')}`)+fbox('创建两条分支的新展览',fform(`${input('title','展览名称')}${ta('intro','开场白')}${input('branch1','选项一')}${input('end1','选项一对应的结局')}${input('branch2','选项二')}${input('end2','选项二对应的结局')}`,'公开互动展览'));
}
if(n===6){let places=await api('/features/places');return fbox('身边的奇物 · 城市与街区',`${fnotice('保护隐私：此版本仅标注城市和街区，不采集 GPS 或公开私人住宅的精确地址。')}<div class="place-list">${places.map(p=>`<button data-action="detail" data-id="${p.exhibit_id}" class="place-card"><span>⌖ ${fe(p.city)}${p.area?' · '+fe(p.area):''}</span><h3>${fe(p.title)}</h3><p>${fe(p.note)}</p><small>发现者：${fe(p.owner)} → 查看展品</small></button>`).join('')||fempty('还没有公开的现实奇物地点')}</div>`)+fbox('将一件公开展品关联到一座城市',`${fchoose(feed)}${fform(`${input('city','城市（例如：昆明）')}${input('area','街区或片区（例如：呈贡区）')}${input('note','为何值得实地探访？')}`,'提交位置介绍')}`);
}
if(n===7){return `<div class="feature-columns">${fbox('网页小猴子的数量和活动模式',`<div class="monkey-preview"><img src="/static/assets/monkey/idle_0.webp"><div><h3>ProfMonkey Colony</h3><p>来源：你上传的 Desktop v0.5 项目素材。网页猴子只活动在浏览器页面里，不读取其他软件或桌面内容。</p></div></div><div class="f-pills">${[1,2,3,4,5,6].map(i=>fbutton(`${i} 只猴子`,'monkey-count',i,W.monkeyCount===i?'feature-btn picked':'feature-btn')).join('')}</div><div class="f-pills">${[['quiet','安静模式'],['wild','猴山模式'],['off','关闭猴子']].map(([k,v])=>fbutton(v,'monkey-mode',k,W.monkeyMode===k?'feature-btn picked':'feature-btn')).join('')}</div>`)}${fbox('活体猴演出说明',`<p>已复用 idle / walk / sleep / eat_banana / slip / wake 等动画帧。网页会根据用户选择创建 1–6 只猴子。</p><p>鼠标可以拖动猴子，点击它会触发动作；页面右下角可随时关停。</p><div class="f-tags"><span>不抢输入焦点</span><span>减少动画设置</span><span>仅本站作用域</span></div>${fbutton('让猴子吃香蕉','monkey-banana')}`)}</div>`}
if(n===8){let chains=await api('/features/chains');let selected= W.chainId?await api('/features/chains/'+W.chainId).catch(()=>null):null;
 const left=fbox('正在进行的奇物接龙',chains.map(c=>`<button data-wa="chain" data-value="${c.id}" class="f-row"><strong>${fe(c.title)}</strong><span>${c.steps} 段 · ${fe(c.creator)}</span></button>`).join('')||fempty('尚无人发起接力'));
 const right=fbox('发起一次接力',fchoose(feed)+fform(input('title','这条故事链叫什么？')+ta('reason','为什么从这件展品出发？'),'开始接力'));
 const detail=selected?fbox(`接力故事 #${selected.chain.id}`,`<div class="relay-chain">${selected.steps.map((step,i)=>`<div class="relay-step"><span>${i+1}</span><b>${fe(step.title)}</b><p>${fe(step.reason)}</p><small>接力者 ${fe(step.author)}</small></div>`).join('')}</div><h3>让故事继续</h3>${fchoose(feed)}${fform(ta('reason','这件新展品如何接上上一段？'),'接力下一段')}`):'';
 return `<div class="feature-columns">${left}${right}</div>${detail}`;
}
if(n===9){return fbox('小猴导览 · 导览台',`<div class="guide-top"><img src="/static/assets/monkey/idle_0.webp"><div><h2>今天想逛些什么？</h2><p>以下介绍仅依据公开展品的标题、分类、简介组成。没有来源的内容，不会写成“已证实”。</p></div></div><div class="f-pills">${['科学','自然','技术','故事','艺术'].map(cat=>fbutton(cat+'导览','guide',cat)).join('')}</div><div id="guide-routes" class="guide-route">${feed.slice(0,4).map(x=>`<div class="f-dossier"><b>${fe(x.title)}</b><p>${fe(x.description||'馆长尚未补充解说。')}</p><small>来自 ${fe(x.owner)} · ${fe(x.category)}</small>${fbutton('查看展品','view-exhibit',x.id)}</div>`).join('')||fempty('没有可导览的真实展品')}</div>`)}
if(n===10){return fbox('动手玩展品 · 光与生长（演示模型）',`<div class="lab-layout"><div class="lab-dome"><div id="glowPlant" class="glow-plant" style="--glow:.5"><span>✦</span><span>❋</span><span>✺</span></div><small>这是教学互动模型，不代表真实植物的定量实验结果。</small></div><div class="lab-controls"><h3>调节环境</h3><label>光照强度：<strong id="lab-value">50%</strong><input id="lab-slider" type="range" min="0" max="100" value="50" data-wa-change="lab"></label><p id="lab-observation">光照处于中等水平，观察视觉效果变化。</p>${fbutton('恢复初始条件','lab-reset')}</div></div>`)}
if(n===11){let room=W.roomCode?await api('/features/rooms/'+W.roomCode).catch(()=>null):null;
 return `${fbox('发起一起逛博物馆',`${fnotice('不同账号打开同一个房间码，自动轮询同步公开展品与文字聊天；不包含音视频。')}${fchoose(feed)}${fform(input('title','房间主题，例如：今晚的奇物漫游'),'创建参观房间')}<div class="room-join"><input id="joinRoomCode" placeholder="输入好友发来的房间码" value="${fe(W.roomCode||'')}">${fbutton('加入房间','room-join')}</div>`)}${room?fbox(`正在一起逛博物馆 · ${fe(room.title)}`,`<div class="room-head"><span>房间码 <code>${fe(room.code)}</code></span><span>主持人 ${fe(room.host)}</span></div><div class="tour-stage"><h3>正在同步的展品：${fe(room.exhibit_title)}</h3>${fbutton('查看这件展品','view-exhibit',room.exhibit_id)}</div><h3>参观成员</h3><div class="f-pills">${room.participants.map(p=>`<span class="tag">${fe(p.username)}</span>`).join('')}</div>${S.user?.id===room.host_id?`<h3>主持人切换展品</h3>${fchoose(feed,'切换到',W.selected)}${fbutton('同步此展品','room-advance')}`:''}<h3>同行留言</h3><div class="tour-chat">${room.messages.map(m=>`<p><b>${fe(m.author)}</b> · ${fe(m.body)}</p>`).join('')}</div>${fform(input('text','与同行者讨论这件展品'),'发送到房间')}${fbutton('刷新房间','room-refresh')}`):''}`}
if(n===12){if(!W.selected)return fbox('藏品来源',fempty());let p=await api(`/features/exhibits/${W.selected}/passport`),x=p.exhibit,r=p.passport||{};
 return fbox('出品人、来源与著作权声明',`${fchoose(feed)}<div class="passport-layout"><div class="passport-cover"><small>WONDER ATLAS</small><span>◈</span><h2>藏品来源卡</h2><b>#${String(x.id).padStart(6,'0')}</b></div><div class="passport-info"><h3>${fe(x.title)}</h3><p>发现者：${fe(x.owner)}</p><p>资料出处：${fe(r.origin||x.source_url||'馆主尚未补充')}</p><p>署名：${fe(r.attribution||'待补充')}</p><p>许可：${fe(r.license||'未说明')}</p><p>备注：${fe(r.note||'无')}</p><small>声明由馆主填写，平台尚未对来源真实性完成独立核验。</small></div></div><h3>资料修订历史</h3>${p.history.map(h=>`<p class="feature-muted">${fe(h.created_at)} · ${fe(h.editor)} 更新了护照</p>`).join('')||fempty('尚无修订记录')}`)+(S.user?.id===x.user_id?fbox('馆主编辑来源',fform(`${input('origin','原始来源', 'text',r.origin||x.source_url||'')}${input('attribution','原作者或发现者', 'text',r.attribution||'')}${input('license','授权形式（仅声明）','text',r.license||'未说明')}${ta('note','补充说明',r.note||'')}`,'保存来源并留下修订记录')):'');
}
if(n===13){let mine=S.user?await api('/my/exhibits'):[],counter={};mine.forEach(x=>counter[x.category]=(counter[x.category]||0)+1);let entries=Object.entries(counter).sort((a,b)=>b[1]-a[1]);let max=Math.max(1,...entries.map(x=>x[1]));return fbox('我的兴趣地图 · 仅本地计算',`${fnotice('只读取你自己的馆藏数据。下面的主题统计不会上传到额外的画像服务，也不会自动公开。')}${!S.user?fempty('登录后查看自己的兴趣星图'):entries.length?`<div class="fingerprint-layout"><div class="fingerprint-orb">${entries.slice(0,5).map((x,i)=>`<span style="--rot:${i*72}deg;--scale:${.65+i*.1}">${fe(x[0])}</span>`).join('')}</div><div class="fingerprint-bars">${entries.map(([cat,c])=>`<div><b>${fe(cat)}</b><span class="fingerprint-track"><i style="width:${(c/max)*100}%"></i></span><small>${c} 件</small></div>`).join('')}</div></div><p class="feature-muted">合计 ${mine.length} 件个人藏品。统计标签不代表性格诊断。</p>`:fempty('先收藏第一件展品，我的兴趣地图就会出现')}`)}
return fbox('工程正在规划','这项工程尚无独立交互。');
}

// Override only the central renderer for a single additional navigation destination.
const renderV2=render;
render=async function(){if(S.view!=='features')return renderV2();try{$('#main').innerHTML=await renderFeatures()}catch(e){$('#main').innerHTML=empty('特色工程读取失败',fe(e.message))}};
titles.features='特色工程';
const navFeature=document.createElement('button');navFeature.dataset.action='navigate';navFeature.dataset.view='features';navFeature.innerHTML='<span>✧</span> 13 项特色工程';
const mainNav=document.querySelector('.sidebar .nav');mainNav.insertBefore(navFeature,mainNav.children[1]||null);
document.addEventListener('click',event=>{const b=event.target.closest('[data-action=\"navigate\"][data-view=\"features\"]');if(b)W.active=null},true);
const mobileNav=document.querySelector('.mobile-nav');if(mobileNav){let n=document.createElement('button');n.dataset.action='navigate';n.dataset.view='features';n.innerHTML='<span>✧</span>工程';mobileNav.insertBefore(n,mobileNav.children[2]||null)}

async function featureAction(action,val){let n=W.active;const id=W.selected;if(n&&['collision-reroll','blindbox-answer','memory-answer','pair-answer','future-save','case-state','room-advance','chain','story-choice'].includes(action))window.WonderAnalytics?.track(analyticsFeatureKeys[n-1]||'personal_world','complete');
if(action==='home'){W.active=null;await render();return}
if(action==='module'){W.selected=null;W.caseId=null;W.chainId=null;W.storyId=null;W.roomCode='';W.collisionDestination=null;await featureModule(Number(val));return}
if(action==='collision-reroll'){const feed=await featuredFeed();W.collisionPair=makeCollisionPair(feed);W.collisionDestination=null;await render();return}
if(action==='collision-open'){if(!W.collisionPair)return;W.selected=W.collisionPair.a.id;W.collisionDestination=W.collisionPair.b.id;W.active=1;await navigate('features');return}
if(action==='collision-save'){if(!S.user){if(typeof openAuth==='function')openAuth('login');return}if(!W.collisionPair||W.collisionPair.a.user_id!==S.user.id){toast('要保存关联，请用自己发布的公开展品作为起点。');return}W.selected=W.collisionPair.a.id;W.collisionDestination=W.collisionPair.b.id;W.active=1;await navigate('features');return}
if(action==='blindbox-answer'){
 if(!W.blindGame||W.blindGame.answered)return;
 const feed=await featuredFeed(),target=feed.find(x=>x.id===W.blindGame.targetId);if(!target)return;
 const correct=Number(target.id)===Number(val);W.blindGame={...W.blindGame,answered:true,selected:Number(val),correct};recordMiniGame('blindbox',correct);await render();return;
}
if(action==='blindbox-next'){const feed=await featuredFeed();W.blindGame=makeBlindRound(feed);await render();return}
if(action==='memory-start'||action==='memory-next'){
 const feed=await featuredFeed(),round=makeMemoryRound(feed);if(!round){toast('至少需要 4 件标题不同的公开藏品才能开始记忆挑战。');return}
 clearTimeout(W.memoryTimer);W.memoryGame=round;await render();
 W.memoryTimer=setTimeout(async()=>{if(W.memoryGame?.phase==='show'){W.memoryGame.phase='guess';if(S.view==='features'&&!W.active)await render()}},3000);return;
}
if(action==='memory-answer'){
 const g=W.memoryGame;if(!g||g.phase!=='guess')return;const correct=Number(val)===Number(g.targetId);W.memoryGame={...g,phase:'result',selectedId:Number(val),correct};recordMiniGame('memory',correct);await render();return;
}
if(action==='pair-start'||action==='pair-next'){
 const feed=await featuredFeed(),round=makePairRound(feed);if(!round){toast('目前公开藏品的分类还不够丰富，先多收藏几件不同类别的东西吧。');return}W.pairGame=round;await render();return;
}
if(action==='pair-answer'){
 const g=W.pairGame;if(!g||g.phase!=='playing')return;const feed=await featuredFeed(),target=feed.find(x=>x.id===g.targetId),selected=feed.find(x=>x.id===Number(val));if(!target||!selected)return;
 const correct=(target.category||'其他')===(selected.category||'其他');W.pairGame={...g,phase:'result',selectedId:selected.id,correct};recordMiniGame('pair',correct);await render();return;
}
if(action==='future-reroll'){const feed=await featuredFeed();const pool=feed.filter(x=>x.id!==W.futureItemId);W.futureItemId=(pool.length?pool:feed)[Math.floor(Math.random()*(pool.length?pool:feed).length)]?.id||null;W.futureDraft='';await render();return}
if(action==='future-save'){const note=$('#futureNote')?.value.trim()||'';if(note.length<4){toast('多写几句你的未来考古假说吧（至少 4 个字）。');return}const feed=await featuredFeed();const x=feed.find(i=>i.id===W.futureItemId);if(!x){toast('这件展品暂时不可用。');return}W.futureSaved=Array.isArray(W.futureSaved)?W.futureSaved:[];W.futureSaved.push({id:x.id,title:x.title,note,date:new Date().toLocaleDateString('zh-CN')});W.futureSaved=W.futureSaved.slice(-30);localStorage.setItem('wa-future-notes',JSON.stringify(W.futureSaved));W.futureDraft='';toast('假说已保存在当前浏览器');await render();return}
if(action==='view-exhibit'){await openDetail(Number(val));return}
if(action==='worm-next'){W.selected=Number(val);await render();return}
if(action==='case'){W.caseId=Number(val);await render();return}
if(action==='chain'){W.chainId=Number(val);await render();return}
if(action==='story'){W.storyId=Number(val);await render();return}
if(action==='story-choice'){let all=await api('/features/stories');let story=all.find(x=>x.id===W.storyId)||all[0];$('#story-ending').innerHTML=`<strong>你到达了结局：</strong><p>${fe(story.endings[Number(val)])}</p>${fbutton('重新选择','story-restart')}`;return}
if(action==='story-restart'){$('#story-ending').textContent='选择一条路，开启不同结局。';return}
if(action==='guide'){let feed=await featuredFeed(),filtered=feed.filter(x=>x.category===val);$('#guide-routes').innerHTML=filtered.length?filtered.slice(0,8).map(x=>`<div class="f-dossier"><b>${fe(x.title)}</b><p>${fe(x.description||'暂无简介')}</p><small>来源：${fe(x.owner)} · 未独立核验</small>${fbutton('查看展品','view-exhibit',x.id)}</div>`).join(''):fempty('此分类目前还没有公开展品');return}
if(action==='lab-reset'){$('#lab-slider').value=50;updateLab(50);return}
if(action==='monkey-count'){W.monkeyCount=Number(val);localStorage.setItem('wa-monkey-count',val);setupMonkeys();await render();return}
if(action==='monkey-mode'){W.monkeyMode=val;localStorage.setItem('wa-monkey-mode',val);setupMonkeys();await render();return}
if(action==='monkey-banana'){playMonkeyBanana();return}
if(action==='case-state'){let reason=prompt(`设置为「${val}」的依据是什么？`);if(!reason||reason.trim().length<3)return;await api(`/features/cases/${W.caseId}/state`,{method:'POST',body:{state:val,reason}});toast('状态和原因已记录');await render();return}
if(action==='room-join'){if(!mustLogin())return;W.roomCode=$('#joinRoomCode').value.trim();if(!W.roomCode)throw Error('请输入房间码');await render();startRoomPoll();return}
if(action==='room-refresh'){await render();return}
if(action==='room-advance'){if(!mustLogin())return;await api(`/features/rooms/${W.roomCode}/advance`,{method:'POST',body:{exhibit_id:Number(W.selected)}});await render();return}
}
function updateLab(v){$('#glowPlant')?.style.setProperty('--glow',v/100);if($('#lab-value'))$('#lab-value').textContent=v+'%';if($('#lab-observation'))$('#lab-observation').textContent=`光照模拟强度为 ${v}%。你可以观察模型的亮度变化，这不等于真实生物学结论。`}
function startRoomPoll(){clearInterval(W.roomTimer);if(W.roomCode&&W.active===11){W.roomTimer=setInterval(()=>{if(S.view==='features'&&W.active===11)render().catch(()=>{})},7000)}}
// Capture phase keeps new widgets independent of V2's one document-wide dispatcher.
document.addEventListener('click',async ev=>{let b=ev.target.closest('[data-wa]');if(!b)return;ev.preventDefault();ev.stopPropagation();try{await featureAction(b.dataset.wa,b.dataset.value||'')}catch(err){toast(err.message)}},true);
document.addEventListener('change',async ev=>{let p=ev.target.dataset.waChange;if(p==='selected'){const next=Number(ev.target.value)||null;if(next!==W.selected)W.collisionDestination=null;W.selected=next;await render()}if(p==='lab'){updateLab(Number(ev.target.value))}});
document.addEventListener('input',ev=>{if(ev.target.id==='lab-slider')updateLab(Number(ev.target.value))});
document.addEventListener('submit',async ev=>{let form=ev.target;if(form.dataset.waForm!=='1')return;ev.preventDefault();ev.stopPropagation();if(!mustLogin())return;let data=Object.fromEntries(new FormData(form));let n=W.active;try{
 if(n===1){await api(`/features/wormhole/${W.selected}/links`,{method:'POST',body:{destination_id:Number(data.destination_id),relation:data.relation,reason:data.reason}})}
 if(n===2){if(W.caseId&&form.closest('.feature-box')?.querySelector('h2')?.textContent.includes('案卷')){await api(`/features/cases/${W.caseId}/clues`,{method:'POST',body:{kind:data.kind,body:data.body,source_url:data.source_url.trim()}})}else{let x=await api('/features/cases',{method:'POST',body:{exhibit_id:Number(W.selected),question:data.question}});W.caseId=x.id}}
 if(n===3){await api(`/features/exhibits/${W.selected}/perspectives`,{method:'POST',body:{angle:data.angle,text:data.text}})}
 if(n===4){await api(`/features/exhibits/${W.selected}/events`,{method:'POST',body:{happened_at:data.happened_at,description:data.description,source_url:data.source_url}})}
 if(n===5){let out=await api('/features/stories',{method:'POST',body:{title:data.title,intro:data.intro,branches:[data.branch1,data.branch2],endings:[data.end1,data.end2]}});W.storyId=out.id}
 if(n===6){await api('/features/places',{method:'POST',body:{exhibit_id:Number(W.selected),city:data.city,area:data.area,note:data.note}})}
 if(n===8){if(W.chainId&&form.closest('.feature-box')?.querySelector('h2')?.textContent.includes('接力故事')){await api(`/features/chains/${W.chainId}/steps`,{method:'POST',body:{exhibit_id:Number(W.selected),reason:data.reason}})}else{let out=await api('/features/chains',{method:'POST',body:{title:data.title,exhibit_id:Number(W.selected),reason:data.reason}});W.chainId=out.id}}
 if(n===11){if(data.text){await api(`/features/rooms/${W.roomCode}/chat`,{method:'POST',body:{text:data.text}})}else{let out=await api('/features/rooms',{method:'POST',body:{exhibit_id:Number(W.selected),title:data.title}});W.roomCode=out.code;startRoomPoll()}}
 if(n===12){await api(`/features/exhibits/${W.selected}/passport`,{method:'PUT',body:data})}
 toast('已保存到服务器');await render();
}catch(err){toast(err.message)}},true);