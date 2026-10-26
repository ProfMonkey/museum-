/* Wonder Atlas V8. Growth History lives inside the existing Memory Cinema.
   Derived on demand from real account records; not a second tracking system. */
(() => {
'use strict';
const G={year:new Date().getUTCFullYear(),data:null,filter:'all'};
const safe=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&quot;'}[c]));
const typeNames={joined:'建馆',exhibit:'收藏',hall:'展厅',visit:'初次遇见',film:'影片',route:'路线'};
const icons={joined:'✦',exhibit:'♜',hall:'▦',visit:'✧',film:'♫',route:'⌁'};
const fmt=d=>String(d||'').slice(0,10);
const escDate=d=>safe(fmt(d));
function row(x){return `<article class="grow-event"><div class="grow-event-pin">${icons[x.type]||'✧'}</div><div><div class="grow-event-time">${escDate(x.at)} · ${safe(typeNames[x.type]||'足迹')}</div><strong>${safe(x.title)}</strong><p>${safe(x.detail||'')}</p></div>${x.exhibit_id?`<button class="ghost grow-open" data-growth="detail" data-id="${x.exhibit_id}">查看 ↗</button>`:''}</article>`;}
const stat=(key,label,info)=>`<div class="grow-stat"><span>${label}</span><strong>${G.data.stats[key]}</strong><small>${info}</small></div>`;
const musicSelect=()=>`<select id="grow-music" aria-label="年度影片音乐"><option value="piano">♫ 夜航钢琴</option><option value="starlight">✧ 星际漫游</option><option value="journey">◈ 金色旅途</option><option value="silent">无声胶片</option></select>`;
async function render(){
 G.data=await api('/growth/overview?year='+encodeURIComponent(G.year));
 const d=G.data;const hasEvents=d.milestones.length>0;
 const max=Math.max(1,...d.monthly.map(m=>m.exhibits+m.halls+m.first_views+m.films+m.routes));
 const metrics=Object.entries(typeNames).filter(([t])=>t!=='joined').map(([t,n])=>`<button data-growth="filter" data-value="${t}" class="${G.filter===t?'active':''}">${n}</button>`).join('');
 const events=d.milestones.filter(x=>G.filter==='all'||G.filter===x.type);
 return `<div class="grow-hero"><span class="eyebrow">THE WORLD YOU HAVE BUILT · V8</span><div class="grow-hero-grid"><div><h1>${safe(d.year)}，<br><em>你的世界生长了多少？</em></h1><p>不凭想象生成成就。只回顾你真实保存的展品、开设的展厅、主动记录的初遇，以及剪辑的回忆。</p><div class="grow-years"><label for="grow-year">回顾年份</label><select id="grow-year">${d.available_years.map(y=>`<option value="${y}" ${y===d.year?'selected':''}>${y} 年</option>`).join('')}</select><button class="ghost" data-growth="export">↓ 导出私人年度报告</button></div></div><div class="grow-orb">✧<span>${d.stats.active_months}<small>个月留下了可追溯的成长记录</small></span></div></div></div>
 <div class="grow-stats">${stat('exhibits','新增私人藏品','按创建时间计')}${stat('halls','新建展厅','每间展厅都是一个世界')}${stat('first_views','首次观看的奇物','仅主动开启的足迹')}${stat('routes','收藏的探索路线','跨越知识边界')}${stat('films','制作回忆影片','旧时光的剧场')}</div>
 <div class="grow-two"><section class="grow-panel"><header><small>ANNUAL RHYTHM</small><h2>这一年，世界如何慢慢丰富</h2><p>每月计数：建展品 + 建展厅 + 首次观看 + 路线 + 回忆影片。不会把重复浏览虚构成多天活跃。</p></header><div class="grow-months" aria-label="12个月的成长记录">${d.monthly.map(m=>{const sum=m.exhibits+m.halls+m.first_views+m.routes+m.films;return `<div class="grow-month" title="${m.month}月：${sum}项成长事件"><strong>${sum||''}</strong><div class="grow-bar-wrap"><i style="height:${sum?Math.max(8,100*sum/max):3}%"></i></div><small>${m.month}月</small></div>`;}).join('')}</div></section><section class="grow-panel grow-cats"><header><small>YOUR COLLECTION DNA</small><h2>你收藏了什么样的世界</h2><p>只分析你在本年自己创建的馆藏类别，不推断人格或隐私兴趣。</p></header>${d.categories.length?d.categories.map(x=>`<div class="grow-cat"><span>${safe(x.name)}</span><div><i style="width:${Math.min(100,100*x.count/(d.stats.exhibits||1))}%"></i></div><b>${x.count}</b></div>`).join(''):'<p class="grow-empty">这一年还没有新增藏品。收藏第一件奇物，世界就开始生长。</p>'}</section></div>
 <section class="grow-cinema"><div><span class="eyebrow">ANNUAL MEMORY FILM</span><h2>把 ${d.year} 年剪成一部电影</h2><p>从你当年创建或首次主动观看、且现在仍可访问的展品中挑选，最多 40 幕；配乐仅在本地播放。</p><span class="grow-footnote">目前有 ${d.film_items.length} 幕可用 · 无数据时不生成虚构回忆</span></div><div class="grow-film-actions">${musicSelect()}<button class="ghost" data-growth="preview" ${d.film_items.length?'':'disabled'}>▶ 直接预览</button><button class="primary" data-growth="save" ${d.film_items.length?'':'disabled'}>✧ 收藏年度影片</button></div></section>
 <section class="grow-timeline"><header><div class="eyebrow">MILESTONES FROM REAL RECORDS</div><h2>走过的每一步，都值得记住</h2><p>实际记录 ${d.milestone_total} 条；最多展示最近 80 条。删除的数据不恢复，未记录的经历不编造。</p></header><div class="grow-filters"><button data-growth="filter" data-value="all" class="${G.filter==='all'?'active':''}">全部</button>${metrics}</div><div class="grow-events">${events.length?events.map(row).join(''):'<div class="grow-empty">当前筛选下还没有成长记录。换个年份或开始收藏万物吧。</div>'}</div></section>
 <p class="grow-privacy">🔒 仅当前登录者可以查看本报告。${safe(d.methodology.views)} ${safe(d.methodology.private)} 年度影片利用已有私人片库，不新增一套重复数据库。</p>`;
}
async function refresh(){if(S.view==='memories' && window.WonderMemories?.isGrowth?.()){$('#main').innerHTML=await window.WonderMemories.render();}}
function downloadJSON(){const data={...G.data, film_items:G.data.film_items.map(x=>({id:x.id,title:x.title,memory_date:x.memory_date}))};
 const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json;charset=utf-8'}));
 const a=document.createElement('a');a.href=url;a.download=`万物博物馆_我的世界成长史_${G.year}.json`;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
document.addEventListener('change',async event=>{if(event.target.id!=='grow-year')return;
 G.year=Number(event.target.value);G.filter='all';try{await refresh()}catch(err){toast(err.message||'无法读取年度记录');}});
document.addEventListener('click',async event=>{
 const el=event.target.closest('[data-growth]');if(!el)return;event.preventDefault();
 if(!G.data || S.view!=='memories')return;
 const action=el.dataset.growth;
 try {
  if(action==='filter'){G.filter=el.dataset.value;await refresh();}
  else if(action==='detail'){await openDetail(Number(el.dataset.id));}
  else if(action==='export'){downloadJSON();toast('年度报告已下载到本机');}
  else if(action==='preview'){
   if(!G.data.film_items.length)return;
   window.WonderMemories.playFilm(G.data.film_items,`${G.year} · 我的世界回忆`,document.getElementById('grow-music')?.value||'piano');
   window.WonderAnalytics?.track('memories','play');
  }else if(action==='save'){
   const items=G.data.film_items;if(!items.length)return;
   const music=document.getElementById('grow-music')?.value||'piano';
   await api('/memories/reels',{method:'POST',body:{title:`${G.year} · 我的世界回忆`,music,exhibit_ids:items.map(x=>x.id)}});
   window.WonderAnalytics?.track('memories','complete');
   toast('年度影片已存入「回忆剧场」的私人片库');
   await window.WonderMemories.switchTab('cinema');
  }
 }catch(err){toast(err.message||'操作失败')}
});
window.WonderGrowth={render};
})();