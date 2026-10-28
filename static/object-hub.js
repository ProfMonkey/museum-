/* V41: each real exhibit is a navigable center, not another disconnected page. */
(() => {
 'use strict';
 const trail=[];
 const esc = value => String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const GROUPS=[
  ['curator','✍️ 馆长主动关联','作者亲自提交的联系及说明，未经平台核实。'],
  ['metadata','🔎 有依据的相似藏品','仅根据共同标签、类别或领域计算，理由逐条展示。'],
  ['time','⏳ 相同年代的另一种发现','仅按宽泛年代分类对照，不暗示历史因果。']
 ];
 function reset(){trail.length=0}
 function push(id,title){
  if(!Number.isSafeInteger(Number(id))||Number(id)<1)return;
  if(trail[trail.length-1]?.id===Number(id))return;
  trail.push({id:Number(id),title:String(title||'上一件藏品').slice(0,120)});
  if(trail.length>35)trail.shift();
 }
 function pop(){return trail.pop()||null}
 function breadcrumbs(root){
  if(!trail.length)return '<span class="oh-trip-hint">从这件藏品开始自由探索</span>';
  const previous=trail[trail.length-1];
  return '<button class="oh-back" data-action="hubBack">← 返回「'+esc(previous.title)+'」</button>'+
   '<span class="oh-stops">已走过 '+trail.length+' 站 · 当前：'+esc(root.title)+'</span>';
 }
 function peer(item){
  return '<article class="oh-peer"><div class="oh-peer-top"><span class="oh-peer-kind">'+esc(item.kind)+'</span>'+
   '<small>来自馆长 '+esc(item.owner)+'</small></div>'+
   '<button class="oh-peer-title" data-action="hubDetail" data-id="'+item.id+'">'+esc(item.title)+' <span>↗</span></button>'+
   '<p class="oh-peer-reason">'+esc(item.reason)+'</p>'+
   '<div class="oh-peer-bottom"><span>'+esc(item.category||'其他')+' · '+esc(item.time_bucket||'时间不详')+'</span>'+
   (item.source==='curator'?'<em>由 '+esc(item.author||'馆长')+' 提出 · 未核实</em>':'<em>按公开分类匹配</em>')+
   '</div></article>';
 }
 function section(key,title,subtitle,items,expanded){
  const rows=items||[];
  return '<details class="oh-section" '+(expanded?'open':'')+'><summary><span>'+title+'</span><small>'+
   rows.length+' 件</small></summary><p class="oh-help">'+subtitle+'</p>'+
   (rows.length?'<div class="oh-peer-grid">'+rows.map(peer).join('')+'</div>':
   '<p class="oh-no-results">尚无符合条件且当前可访问的真实藏品。</p>')+
   '</details>';
 }
 function render(hub){
  if(!hub||!hub.focus)return '';
  const r=hub.focus,groups=hub.groups||{};
  const all=(groups.curator?.length||0)+(groups.metadata?.length||0)+(groups.time?.length||0);
  return '<section class="oh-root" aria-label="以这件藏品为中心继续探索">'+
   '<div class="oh-heading"><div><span class="eyebrow">OBJECT-CENTERED EXPLORATION · V41</span>'+
   '<h2>🌌 以这件藏品为中心</h2><p>先看它属于哪里，再看它与什么有关。每条关联都说明为什么出现。</p></div>'+
   '<span class="oh-count">'+all+' 条当前可见线索</span></div>'+
   '<div class="oh-trail" role="group" aria-label="藏品探索路径">'+breadcrumbs(r)+(r.is_public?'<button class="oh-copy" data-action="copyExhibit" data-id="'+r.id+'" title="复制可打开的原始藏品链接">🔗 复制这件藏品的链接</button>':'')+'</div>'+
   '<div class="oh-paths"><button data-action="filterDomain" data-value="'+esc(r.domain||'其他')+'"><span>所属领域</span><b>'+esc(r.domain||'其他')+'</b><i>查看同领域 ↗</i></button>'+
   '<button data-action="filterCategory" data-value="'+esc(r.category||'其他')+'" data-domain="'+esc(r.domain||'其他')+'"><span>细分类别</span><b>'+esc(r.category||'其他')+'</b><i>查看同细类 ↗</i></button>'+
   '<button data-action="filterTime" data-value="'+esc(r.time_bucket||'时间不详')+'"><span>时间范围</span><b>'+esc(r.time_bucket||'时间不详')+'</b><i>按年代继续 ↗</i></button></div>'+
   '<div class="oh-channels">'+GROUPS.map(([key,title,subtitle],idx)=>section(key,title,subtitle,groups[key],idx===0||idx===1)).join('')+'</div>'+
   '<div class="oh-next"><h3>或者，换一种探索方式</h3><div class="oh-next-actions">'+
   '<button data-action="cosmosFocus" data-id="'+r.id+'">⏳ 沿时间线看</button>'+
   '<button data-cx="open" data-id="'+r.id+'">⌁ 打开关联网络</button>'+
   '<button data-action="atlasFrom" data-id="'+r.id+'">✧ 从这里随机探索</button>'+
   '<button data-action="constellationAdd" data-id="'+r.id+'">✦ 加入我的星图</button></div></div>'+
   '<p class="oh-warning">真实性说明：'+esc(hub.notice||'关联依据来自真实分类及作者声明，未经平台事实核验。')+'</p>'+
   '</section>';
 }
 window.WonderObjectHub={render,push,pop,reset,trail:()=>trail.slice()};
})();
