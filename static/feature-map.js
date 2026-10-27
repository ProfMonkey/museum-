/* V38: searchable feature directory. The main nav stays short; this index keeps every route findable. */
(function(){
'use strict';
const ITEMS=[
{group:"核心馆藏",view:"discover",icon:"⌁",title:"发现广场",desc:"浏览真实公开的用户藏品，搜索、筛选并进入藏品档案。",keywords:"首页 推荐 展品 藏品 搜索 最新 分类"},
{group:"核心馆藏",view:"world-museums",icon:"♜",title:"世界名馆",desc:"探索开放馆藏中的真实艺术品与文化遗产。",keywords:"艺术 博物馆 真实馆藏 大都会 芝加哥"},
{group:"核心馆藏",view:"saved",icon:"♡",title:"心动收藏",desc:"找回你收藏过、想继续看的藏品。",keywords:"收藏 书签 喜欢 稍后看"},
{group:"核心馆藏",view:"museum",icon:"▦",title:"我的博物馆",desc:"管理自己的藏品、个人展厅与私藏内容。",keywords:"我的 上传 私密 展厅 馆长 个人主页"},
{group:"探索发现",view:"cosmos",icon:"⏳",title:"万物时光",desc:"按时间线探索藏品与事件。",keywords:"历史 年代 时间线 亿年前"},
{group:"探索发现",view:"wonder-radar",icon:"✧",title:"万物雷达",desc:"探索 AI、机器人、航天、数码等当代新领域。",keywords:"科技 AI 机器人 数码 太空 新技术"},
{group:"探索发现",view:"culture",icon:"♫",title:"当代新奇",desc:"集中浏览热梗、游戏、数码和流行文化。",keywords:"热梗 流行文化 游戏 网络 新奇"},
{group:"探索发现",view:"journey",icon:"↝",title:"随机奇遇",desc:"让一件公开藏品带你继续探索。",keywords:"随机 发现 探索 关联"},
{group:"探索发现",view:"constellation",icon:"✧",title:"万物星图",desc:"把自己探索过的藏品连接成私人关系地图。",keywords:"知识图谱 关系 网络 路线"},
{group:"探索发现",view:"wheels",icon:"🍜",title:"万物转盘 · 八种随机决定",desc:"美食、旅行、影视、阅读、学习、运动、活动与自定义。逛藏品时一键加入对应转盘。",keywords:"美食 食物 米线 菌子 牛排 转盘 随机菜单 出游 旅行 影视 电影 小说 阅读 读书 数学 学习 运动 跑步 健身 活动 自定义"},
{group:"创作与游玩",action:"new",icon:"＋",title:"发布新发现",desc:"上传图片、写下介绍与来源，创建一件新藏品。",keywords:"上传 投稿 新建 藏品 创作"},
{group:"创作与游玩",view:"virtual-gallery",icon:"▧",title:"展厅工坊",desc:"布置自己的展厅，安排藏品并沉浸参观。",keywords:"建造 布展 房间 展示 工坊"},
{group:"创作与游玩",view:"lab",icon:"✶",title:"万物实验室",desc:"通过互动模型与小实验玩转知识。",keywords:"实验 参数 互动 模型 学习"},
{group:"创作与游玩",view:"play",icon:"⚙",title:"互动玩法",desc:"进入可操作的小游戏与藏品互动体验。",keywords:"游戏 小游戏 互动 玩"},
{group:"创作与游玩",view:"adventure",icon:"✨",title:"命运接力",desc:"把一次随机发现串成连续的探索任务。",keywords:"任务 链条 奇遇 接力 探索路线"},
{group:"专题世界与故事",view:"fantasy",icon:"✵",title:"玄幻异界",desc:"创作虚构世界、角色、地点与世界法则。",keywords:"玄幻 世界观 角色 势力 法则"},
{group:"专题世界与故事",view:"parallel",icon:"🌌",title:"平行宇宙",desc:"从真实藏品出发，构建不同的假设世界。",keywords:"假设 分支 平行 世界碰撞"},
{group:"专题世界与故事",view:"coexhibitions",icon:"🏛",title:"联合展厅",desc:"与另一位馆长共同策展，双方确认后公开。",keywords:"合作 展览 联合 双人"},
{group:"专题世界与故事",view:"living",icon:"🌱",title:"活体博物馆",desc:"持续记录藏品的观察、修正与新发现。",keywords:"更新 年轮 变化 观察 记录"},
{group:"专题世界与故事",view:"mysteries",icon:"🗝",title:"谜案馆",desc:"围绕公开藏品设置线索、问题与解谜路线。",keywords:"谜题 线索 推理 案件 解谜"},
{group:"专题世界与故事",view:"collision",icon:"⚗",title:"万物碰撞机",desc:"把两件藏品放进不同的虚构世界规则中。",keywords:"组合 世界法则 假设 蝴蝶效应"},
{group:"文明与合作",view:"civilizations",icon:"🏛",title:"文明演化",desc:"通过历史轮次和选择，创造自己的架空文明。",keywords:"文明 历史 发展 政策 时代"},
{group:"文明与合作",view:"embassies",icon:"🤝",title:"文明大使馆",desc:"邀请另一位创作者共同写作架空外交历史。",keywords:"使馆 外交 邀请 信件 合作"},
{group:"文明与合作",view:"heritage",icon:"🎁",title:"遗产交换站",desc:"共同解释并交换象征性文化遗产，不转移原物所有权。",keywords:"遗产 交换 文化 互赠"},
{group:"文明与合作",view:"archaeology",icon:"⛏",title:"文明考古局",desc:"给真实公开藏品写下三层架空文明解释。",keywords:"考古 三层 解释 虚构 文明 遗物"},
{group:"个人与系统",view:"memories",icon:"♫",title:"回忆剧场",desc:"回看自己的探索足迹与个人记录。",keywords:"回忆 足迹 音乐 历史"},
{group:"个人与系统",view:"insights",icon:"▥",title:"功能热度",desc:"查看真实使用统计，为后续开发排优先级。",keywords:"统计 数据 使用量 热度 分析"},
{group:"个人与系统",view:"notifications",icon:"✉",title:"通知中心",desc:"查看点赞、评论、关注等站内通知。",keywords:"消息 未读 点赞 评论 关注"}
];
function esc(v){return String(v==null?"":v).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})}
const RECENT_KEY='wonder-feature-recent-v39';
function recents(){try{const x=JSON.parse(localStorage.getItem(RECENT_KEY)||'[]');return Array.isArray(x)?x.filter(k=>ITEMS.some(v=>v.view===k)).slice(0,6):[]}catch(e){return []}}
function remember(view){if(view==='catalog'||!ITEMS.some(x=>x.view===view))return;try{const values=[view,...recents().filter(k=>k!==view)].slice(0,6);localStorage.setItem(RECENT_KEY,JSON.stringify(values))}catch(e){}}
function render(){
var groups=[];ITEMS.forEach(function(x){if(groups.indexOf(x.group)<0)groups.push(x.group)});
var html='<div class="feature-map-page"><section class="feature-map-hero"><div class="eyebrow">WONDER ATLAS · FIND YOUR WAY</div><h1>想做什么？<br>从这里开始。</h1><p>功能很多，但你不应该靠记忆找入口。搜一个词，或按用途浏览。核心馆藏放在最前面，专题玩法按类别整理。</p><div class="hero-buttons"><button class="primary" data-action="navigate" data-view="discover">⌁ 逛藏品</button><button class="ghost" data-action="navigate" data-view="wheels">🍜 今天吃什么</button><button class="ghost" data-action="new">＋ 发布新发现</button></div></section>';
const recent=recents();if(recent.length){html+='<section class="feature-map-group feature-map-recents" id="featureRecent"><h2>↶ 最近打开 <small>仅保存在这台设备，不上传浏览记录</small></h2><div class="feature-map-grid">';recent.forEach(function(key){var x=ITEMS.find(item=>item.view===key);if(x)html+='<button class="feature-map-card" data-action="navigate" data-view="'+esc(x.view)+'"><span class="feature-map-icon">'+x.icon+'</span><span class="feature-map-card-copy"><strong>'+esc(x.title)+'</strong><p>'+esc(x.desc)+'</p></span></button>'});html+='</div></section>'}
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
window.WonderFeatureMap={render:render,remember:remember};
})();