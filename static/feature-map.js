/* V40: task-first directory, controlled taxonomy browser, and a shared feature-relationship graph. */
(function(){
'use strict';
const ITEMS=[
{group:"发现与检索",view:"discover",icon:"⌁",title:"发现广场",desc:"浏览真实公开的用户藏品，搜索、筛选并进入藏品档案。",keywords:"首页 推荐 展品 藏品 搜索 最新 分类"},
{group:"发现与检索",view:"world-museums",icon:"♜",title:"世界名馆",desc:"探索开放馆藏中的真实艺术品与文化遗产。",keywords:"艺术 博物馆 真实馆藏 大都会 芝加哥"},
{group:"收藏与创作",view:"saved",icon:"♡",title:"心动收藏",desc:"找回你收藏过、想继续看的藏品。",keywords:"收藏 书签 喜欢 稍后看"},
{group:"收藏与创作",view:"museum",icon:"▦",title:"我的博物馆",desc:"管理自己的藏品、个人展厅与私藏内容。",keywords:"我的 上传 私密 展厅 馆长 个人主页"},
{group:"分类与关联探索",view:"cosmos",icon:"⏳",title:"万物时光",desc:"按时间线探索藏品与事件。",keywords:"历史 年代 时间线 亿年前"},
{group:"发现与检索",view:"wonder-radar",icon:"✧",title:"万物雷达",desc:"探索 AI、机器人、航天、数码等当代新领域。",keywords:"科技 AI 机器人 数码 太空 新技术"},
{group:"发现与检索",view:"culture",icon:"♫",title:"当代新奇",desc:"集中浏览热梗、游戏、数码和流行文化。",keywords:"热梗 流行文化 游戏 网络 新奇"},
{group:"分类与关联探索",view:"journey",icon:"↝",title:"随机奇遇",desc:"让一件公开藏品带你继续探索。",keywords:"随机 发现 探索 关联"},
{group:"分类与关联探索",view:"constellation",icon:"✧",title:"万物星图",desc:"把自己探索过的藏品连接成私人关系地图。",keywords:"知识图谱 关系 网络 路线"},
{group:"互动与体验",view:"wheels",icon:"🍜",title:"万物转盘 · 八种随机决定",desc:"美食、旅行、影视、阅读、学习、运动、活动与自定义。逛藏品时一键加入对应转盘。",keywords:"美食 食物 米线 菌子 牛排 转盘 随机菜单 出游 旅行 影视 电影 小说 阅读 读书 数学 学习 运动 跑步 健身 活动 自定义"},
{group:"收藏与创作",action:"new",icon:"＋",title:"发布新发现",desc:"上传图片、写下介绍与来源，创建一件新藏品。",keywords:"上传 投稿 新建 藏品 创作"},
{group:"收藏与创作",view:"virtual-gallery",icon:"▧",title:"展厅工坊",desc:"布置自己的展厅，安排藏品并沉浸参观。",keywords:"建造 布展 房间 展示 工坊"},
{group:"互动与体验",view:"lab",icon:"✶",title:"万物实验室",desc:"通过互动模型与小实验玩转知识。",keywords:"实验 参数 互动 模型 学习"},
{group:"互动与体验",view:"play",icon:"⚙",title:"互动玩法",desc:"进入可操作的小游戏与藏品互动体验。",keywords:"游戏 小游戏 互动 玩"},
{group:"互动与体验",view:"adventure",icon:"✨",title:"命运接力",desc:"把一次随机发现串成连续的探索任务。",keywords:"任务 链条 奇遇 接力 探索路线"},
{group:"世界与故事",view:"fantasy",icon:"✵",title:"玄幻异界",desc:"创作虚构世界、角色、地点与世界法则。",keywords:"玄幻 世界观 角色 势力 法则"},
{group:"世界与故事",view:"parallel",icon:"🌌",title:"平行宇宙",desc:"从真实藏品出发，构建不同的假设世界。",keywords:"假设 分支 平行 世界碰撞"},
{group:"合作与交流",view:"coexhibitions",icon:"🏛",title:"联合展厅",desc:"与另一位馆长共同策展，双方确认后公开。",keywords:"合作 展览 联合 双人"},
{group:"世界与故事",view:"living",icon:"🌱",title:"活体博物馆",desc:"持续记录藏品的观察、修正与新发现。",keywords:"更新 年轮 变化 观察 记录"},
{group:"世界与故事",view:"mysteries",icon:"🗝",title:"谜案馆",desc:"围绕公开藏品设置线索、问题与解谜路线。",keywords:"谜题 线索 推理 案件 解谜"},
{group:"世界与故事",view:"collision",icon:"⚗",title:"万物碰撞机",desc:"把两件藏品放进不同的虚构世界规则中。",keywords:"组合 世界法则 假设 蝴蝶效应"},
{group:"世界与故事",view:"civilizations",icon:"🏛",title:"文明演化",desc:"通过历史轮次和选择，创造自己的架空文明。",keywords:"文明 历史 发展 政策 时代"},
{group:"合作与交流",view:"embassies",icon:"🤝",title:"文明大使馆",desc:"邀请另一位创作者共同写作架空外交历史。",keywords:"使馆 外交 邀请 信件 合作"},
{group:"合作与交流",view:"heritage",icon:"🎁",title:"遗产交换站",desc:"共同解释并交换象征性文化遗产，不转移原物所有权。",keywords:"遗产 交换 文化 互赠"},
{group:"世界与故事",view:"archaeology",icon:"⛏",title:"文明考古局",desc:"给真实公开藏品写下三层架空文明解释。",keywords:"考古 三层 解释 虚构 文明 遗物"},
{group:"个人与系统",view:"memories",icon:"♫",title:"回忆剧场",desc:"回看自己的探索足迹与个人记录。",keywords:"回忆 足迹 音乐 历史"},
{group:"个人与系统",view:"insights",icon:"▥",title:"功能热度",desc:"查看真实使用统计，为后续开发排优先级。",keywords:"统计 数据 使用量 热度 分析"},
{group:"个人与系统",view:"notifications",icon:"✉",title:"通知中心",desc:"查看点赞、评论、关注等站内通知。",keywords:"消息 未读 点赞 评论 关注"},
{group:"个人与系统",view:"profile",icon:"♙",title:"馆长主页",desc:"查看一位馆长公开的个人介绍、藏品与展厅。",keywords:"用户 主页 馆长 作者 个人资料 关注"}
];
function esc(v){return String(v==null?"":v).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})}
const RECENT_KEY='wonder-feature-recent-v40',LEGACY_RECENT_KEY='wonder-feature-recent-v39';
function recents(){try{let raw=localStorage.getItem(RECENT_KEY);if(!raw){raw=localStorage.getItem(LEGACY_RECENT_KEY);if(raw)localStorage.setItem(RECENT_KEY,raw)}const x=JSON.parse(raw||'[]');return Array.isArray(x)?x.filter(k=>ITEMS.some(v=>v.view===k)).slice(0,6):[]}catch(e){return []}}
function remember(view){if(view==='catalog'||!ITEMS.some(x=>x.view===view))return;try{const values=[view,...recents().filter(k=>k!==view)].slice(0,6);localStorage.setItem(RECENT_KEY,JSON.stringify(values))}catch(e){}}
const INTENTS=[
{view:"discover",icon:"⌕",title:"找一件藏品",desc:"按关键词、领域、类别和年代筛选真实展品"},
{view:"cosmos",icon:"⏳",title:"按时间探索",desc:"从远古、历史到此刻，沿时间线查找"},
{view:"wonder-radar",icon:"✧",title:"发现新奇事物",desc:"科技、太空、数码与互联网奇物"},
{view:"museum",icon:"▦",title:"整理我的收藏",desc:"管理藏品、个人展厅和私藏内容"},
{view:"virtual-gallery",icon:"▧",title:"建造个人展厅",desc:"把收藏整理成自己的空间"},
{view:"play",icon:"⚙",title:"体验互动玩法",desc:"从实验、小游戏和随机转盘开始"},
{view:"coexhibitions",icon:"🤝",title:"与别人合作",desc:"共同策展、交换故事、建立联系"}
];
const RELATIONSHIPS={
 discover:[["world-museums","看真实开放馆藏"],["cosmos","按年代继续探索"],["wonder-radar","发现当代新领域"]],
 "world-museums":[["discover","回到社区藏品"],["cosmos","按时间寻找关联"],["saved","收入心动收藏"]],
 saved:[["constellation","整理收藏之间的关系"],["museum","管理自己的馆藏"],["discover","继续发现新内容"]],
 museum:[["virtual-gallery","把藏品布置成展厅"],["coexhibitions","邀请别人共同策展"],["discover","发现更多可收藏内容"]],
 cosmos:[["discover","打开某个年代的藏品"],["archaeology","比较不同解释"],["constellation","查看关联网络"]],
 "wonder-radar":[["culture","继续探索热梗与流行文化"],["lab","把好奇变成互动实验"],["discover","查看相关藏品"]],
 culture:[["wonder-radar","继续发现科技与互联网新事物"],["play","进入互动体验"],["journey","随机展开新线索"]],
 journey:[["constellation","把奇遇串成关系网络"],["adventure","把探索变成连续任务"],["discover","回到真实藏品"]],
 constellation:[["cosmos","从时间线理解关联"],["parallel","探索假设世界"],["collision","组合藏品生成新故事"]],
 wheels:[["discover","从真实藏品补充候选"],["journey","让随机选择带来新发现"],["saved","收藏想继续看的内容"]],
 "virtual-gallery":[["museum","整理自己的藏品"],["coexhibitions","与其他馆长共同策展"],["discover","发现展厅新藏品"]],
 lab:[["wonder-radar","从科技奇物寻找灵感"],["play","体验互动玩法"],["discover","把有趣的发现收藏起来"]],
 play:[["lab","继续互动实验"],["adventure","进入连续探索任务"],["wheels","随机决定下一步"]],
 adventure:[["journey","寻找下一次奇遇"],["constellation","串联探索路径"],["play","体验其他互动玩法"]],
 fantasy:[["parallel","构建另一种可能世界"],["collision","让两件藏品发生碰撞"],["civilizations","发展架空文明"]],
 parallel:[["fantasy","扩展世界法则"],["collision","组合不同的假设"],["constellation","回到真实藏品关系"]],
 coexhibitions:[["museum","管理自己的展厅"],["heritage","继续文化互赠故事"],["embassies","开展文明合作"]],
 living:[["discover","发现更多可持续观察的藏品"],["cosmos","把变化放进时间线"],["constellation","连接相关记录"]],
 mysteries:[["journey","从线索继续奇遇"],["archaeology","比较不同解释"],["discover","寻找可用的真实藏品"]],
 collision:[["parallel","延伸平行世界设定"],["fantasy","补充世界法则"],["civilizations","让设定发展成文明"]],
 civilizations:[["embassies","与其他文明建立联系"],["heritage","交换象征性文化故事"],["archaeology","为原始藏品写下架空解释"]],
 embassies:[["civilizations","回到文明档案"],["heritage","继续文化互赠"],["coexhibitions","创建联合展厅"]],
 heritage:[["embassies","继续文明交流"],["world-museums","发现真实文化遗产"],["civilizations","查看相关架空文明"]],
 archaeology:[["mysteries","从新线索继续调查"],["cosmos","核对原始藏品年代"],["civilizations","查看相关文明档案"]],
 memories:[["discover","重新打开曾经发现的藏品"],["saved","查看心动收藏"],["constellation","整理探索关系"]],
 insights:[["catalog","从功能地图寻找功能"],["discover","回到真实内容"],["wheels","体验转盘互动"]],
 notifications:[["profile","查看馆长主页"],["museum","管理自己的博物馆"],["discover","继续探索"]],
 profile:[["museum","管理自己的馆藏"],["saved","查看心动收藏"],["discover","浏览公开藏品"]],
 catalog:[["discover","查找真实藏品"],["wheels","使用万物转盘"],["museum","管理个人展馆"]]
};
function taskShortcuts(){
 return '<section class="feature-intents"><div class="feature-intents-heading"><h2>先说你想做什么</h2><p>不用记住功能名，直接按目的进入。</p></div><div class="feature-intents-grid">'+INTENTS.map(x=>
 '<button class="feature-intent" data-action="navigate" data-view="'+esc(x.view)+'"><span>'+x.icon+'</span><b>'+esc(x.title)+'</b><small>'+esc(x.desc)+'</small><i>进入 ↗</i></button>'
 ).join('')+'</div></section>';
}
function taxonomyBrowser(){
 const T=window.WonderTaxonomy;if(!T)return '';
 const series=['藏品系列','民间奇趣'];
 const time=(T.timeBuckets||[]).map(x=>'<button class="taxonomy-chip" data-action="taxonomyTime" data-value="'+esc(x)+'" title="'+esc(T.timeDescriptions?.[x]||'')+'">'+esc(x)+'</button>').join('');
 const groupedCats=new Set(Object.values(T.groups||{}).flat());
 const legacyCats=(T.allCategories||[]).filter(cat=>!groupedCats.has(cat));
 const domains=Object.entries(T.groups||{}).map(([domain,cats])=>
 '<details class="taxonomy-domain"><summary><span>'+esc(domain)+'</span><small>'+cats.length+' 个细类</small></summary><div class="taxonomy-domain-actions"><button class="taxonomy-chip taxonomy-domain-main" data-action="taxonomyDomain" data-value="'+esc(domain)+'">查看整个领域 ↗</button>'+cats.map(cat=>
 '<button class="taxonomy-chip" data-action="taxonomyCategory" data-value="'+esc(cat)+'" data-domain="'+esc(domain)+'">'+esc(cat)+'</button>'
 ).join('')+'</div></details>').join('')+(legacyCats.length?'<details class="taxonomy-domain taxonomy-legacy"><summary><span>历史兼容分类</span><small>'+legacyCats.length+' 个旧标签</small></summary><p class="taxonomy-footnote">这些名称来自旧版本，暂未归入新的标准领域；仍可用于检索历史藏品。</p><div class="taxonomy-domain-actions">'+legacyCats.map(cat=>'<button class="taxonomy-chip" data-action="taxonomyCategory" data-value="'+esc(cat)+'" data-domain="">'+esc(cat)+'</button>').join('')+'</div></details>':'');
 return '<section class="feature-taxonomy"><div class="feature-taxonomy-heading"><div><div class="eyebrow">COLLECTION TAXONOMY</div><h2>按分类找藏品</h2><p>系列、领域、细类和年代是不同的筛选维度。点击任意项，就会带着筛选条件打开发现广场。</p></div><button class="ghost" data-action="taxonomyClear">清除筛选</button></div>'+
 '<div class="taxonomy-dimension"><h3>① 内容系列</h3><div class="taxonomy-chip-row"><button class="taxonomy-chip" data-action="taxonomySeries" data-value="全部">全部系列</button>'+series.map(x=>'<button class="taxonomy-chip" data-action="taxonomySeries" data-value="'+x+'">'+x+'</button>').join('')+'</div></div>'+
 '<div class="taxonomy-dimension"><h3>② 按年代</h3><div class="taxonomy-chip-row">'+time+'</div></div>'+
 '<details class="taxonomy-domain-browser"><summary>③ 按领域与细分类别浏览 <span>'+(T.domains||[]).length+' 个领域 · '+(T.allCategories||[]).length+' 个分类标签</span></summary><div class="taxonomy-domain-list">'+domains+'</div></details>'+
 '<p class="taxonomy-footnote">同一件藏品可以同时属于一个领域、一个细类、一个宽泛年代和一个系列。虚构故事与真实藏品会在各自页面中明确区分。</p></section>';
}
function groupFor(view){return ITEMS.find(x=>x.view===view)?.group|| (view==='catalog'?'功能地图':'其他功能')}
function nextSteps(view){
 return (RELATIONSHIPS[view]||RELATIONSHIPS.discover).map(([to,reason])=>{
 const item=ITEMS.find(x=>x.view===to);return item?{view:to,title:item.title,icon:item.icon,reason}:null;
 }).filter(Boolean);
}
function render(){
var GROUP_ORDER=["发现与检索","分类与关联探索","收藏与创作","互动与体验","世界与故事","合作与交流","个人与系统"];var groups=GROUP_ORDER.filter(function(g){return ITEMS.some(function(x){return x.group===g})});
var html='<div class="feature-map-page"><section class="feature-map-hero"><div class="eyebrow">WONDER ATLAS · FIND YOUR WAY</div><h1>想做什么？<br>从这里开始。</h1><p>功能很多，但你不应该靠记忆找入口。搜一个词，或按用途浏览。先按目标进入，再按分类筛选真实藏品；功能目录与藏品分类各有职责。</p><div class="hero-buttons"><button class="primary" data-action="navigate" data-view="discover">⌁ 逛藏品</button><button class="ghost" data-action="navigate" data-view="wheels">🎡 万物转盘</button><button class="ghost" data-action="new">＋ 发布新发现</button></div></section>';
const recent=recents();if(recent.length){html+='<section class="feature-map-group feature-map-recents" id="featureRecent"><h2>↶ 最近打开 <small>仅保存在这台设备，不上传浏览记录</small></h2><div class="feature-map-grid">';recent.forEach(function(key){var x=ITEMS.find(item=>item.view===key);if(x)html+='<button class="feature-map-card" data-action="navigate" data-view="'+esc(x.view)+'"><span class="feature-map-icon">'+x.icon+'</span><span class="feature-map-card-copy"><strong>'+esc(x.title)+'</strong><p>'+esc(x.desc)+'</p></span></button>'});html+='</div></section>'}
html+=taskShortcuts()+taxonomyBrowser();
html+='<label class="feature-map-search"><span>⌕</span><input id="featureSearch" placeholder="搜功能：美食、上传、文明、谜题、时间线……" autocomplete="off" aria-label="搜索功能入口"><small>支持功能名与用途</small></label><div id="featureMapResults">';
groups.forEach(function(group){
var items=ITEMS.filter(function(x){return x.group===group});
html+='<section class="feature-map-group" data-feature-group="'+esc(group)+'"><h2>'+esc(group)+' <small>'+items.length+' 个入口</small></h2><div class="feature-map-grid">';
items.forEach(function(x){
var action=x.action||"navigate",view=x.view?' data-view="'+esc(x.view)+'"':"";
html+='<button class="feature-map-card" data-feature-card data-feature-search="'+esc([x.group,x.title,x.desc,x.keywords].join(" "))+'" data-action="'+action+'"'+view+'><span class="feature-map-icon">'+x.icon+'</span><span class="feature-map-card-copy"><strong>'+esc(x.title)+'</strong><p>'+esc(x.desc)+'</p></span></button>';
});
html+='</div></section>';
});
html+='</div><div class="feature-map-empty" id="featureNoResults" hidden>没有找到匹配的功能。试试“藏品”“美食”“创作”或“文明”。</div><p class="muted" style="margin-top:20px;font-size:11px">提示：找具体藏品，请回到「发现广场」使用藏品搜索；这里搜索的是功能入口。</p></div>';
return html;
}
document.addEventListener("input",function(e){
if(!e.target||e.target.id!=="featureSearch")return;
var q=e.target.value.trim().toLocaleLowerCase(),count=0;
document.querySelectorAll("[data-feature-card]").forEach(function(card){
var match=!q||(card.getAttribute("data-feature-search")||"").toLocaleLowerCase().indexOf(q)>=0;
card.hidden=!match;if(match)count++;
});
document.querySelectorAll("[data-feature-group]").forEach(function(group){group.hidden=!group.querySelector("[data-feature-card]:not([hidden])")});
var empty=document.getElementById("featureNoResults");if(empty)empty.hidden=count>0;var recent=document.getElementById('featureRecent');if(recent)recent.hidden=Boolean(q);
});
window.WonderFeatureMap={render:render,remember:remember,groupFor:groupFor,nextSteps:nextSteps,getItems:function(){return ITEMS.slice()}};
})();