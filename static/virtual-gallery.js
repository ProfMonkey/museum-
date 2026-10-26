/* Wonder Atlas V9 — original SVG floor plans, saved hall layouts, immersive 2.5D tour and interactive exhibit lab. */
(() => {
 'use strict';
 const G={tab:'design',template:'classic',halls:[],mine:[],selectedHall:'',hallData:null,tourIndex:0,flipped:false,loading:false,use3D:false};
 const $=s=>document.querySelector(s);
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const templates=[
  {id:'classic',name:'古典长廊',type:'经典',desc:'对称陈列、中央通道，适合古画、珠宝与历史文物。',rooms:5},
  {id:'courtyard',name:'中央庭院',type:'庭院',desc:'中庭作为视觉中心，四周分区，适合混合主题收藏。',rooms:6},
  {id:'ring',name:'环形展厅',type:'环廊',desc:'围绕中心连续参观，适合做时间线或系列展。',rooms:4},
  {id:'star',name:'星芒展馆',type:'探索',desc:'多个分区从中心发散，适合跨领域关联探索。',rooms:7},
  {id:'corridor',name:'沉浸长廊',type:'叙事',desc:'沿一条路线逐步揭示内容，适合回忆剧场与故事展。',rooms:3},
  {id:'science',name:'科技实验室',type:'实验',desc:'分成实验台、演示区和资料墙，适合数码与科学展品。',rooms:5},
  {id:'arcade',name:'游戏街机馆',type:'互动',desc:'小型展柜均匀排列，适合游戏、梗图和互动作品。',rooms:8},
  {id:'garden',name:'自然花园馆',type:'自然',desc:'展柜沿花园式空间展开，适合植物、矿物、动物与摄影。',rooms:6},
  {id:'blackbox',name:'黑盒实验空间',type:'自由',desc:'极简空白空间，适合现代艺术、装置和实验性作品。',rooms:1}
 ];
 function blueprint(t,large=false){
  const stroke='#d9b967', soft='#8b7744', bg='#0a0d13'; let shapes='';
  const line=(x1,y1,x2,y2,w=2,c=stroke)=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-width="${w}"/>`;
  const rect=(x,y,w,h,fill='none',sw=2)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" rx="2"/>`;
  shapes+=rect(10,10,280,160,'none',3);
  if(t.id==='classic') { shapes+=rect(112,48,76,84,'#d9b96712'); shapes+=line(150,10,150,48)+line(150,132,150,170); [35,75,115].forEach(y=>{shapes+=rect(24,y,58,22,'#d9b9670b',1.5)+rect(218,y,58,22,'#d9b9670b',1.5)}); shapes+=line(82,10,82,170,1,soft)+line(218,10,218,170,1,soft); }
  if(t.id==='courtyard') { shapes+=rect(92,46,116,88,'#d9b96713',2.5); shapes+=rect(24,26,52,28,'#d9b96708',1.5)+rect(224,26,52,28,'#d9b96708',1.5)+rect(24,126,52,28,'#d9b96708',1.5)+rect(224,126,52,28,'#d9b96708',1.5); shapes+=line(76,40,92,56)+line(208,56,224,40)+line(76,140,92,124)+line(208,124,224,140); }
  if(t.id==='ring') { shapes+=rect(68,35,164,110,'#d9b96708',2); shapes+=rect(108,59,84,62,bg,2); shapes+=line(150,10,150,35)+line(150,145,150,170)+line(10,90,68,90)+line(232,90,290,90); }
  if(t.id==='star') { shapes+=rect(117,63,66,54,'#d9b96715',2.5); shapes+=rect(24,24,56,32,'#d9b96708',1.5)+rect(220,24,56,32,'#d9b96708',1.5)+rect(24,124,56,28,'#d9b96708',1.5)+rect(220,124,56,28,'#d9b96708',1.5); shapes+=line(80,40,117,73)+line(220,40,183,73)+line(80,138,117,107)+line(220,138,183,107)+line(150,10,150,63)+line(150,117,150,170); }
  if(t.id==='corridor') { shapes+=rect(20,66,260,48,'#d9b96708',2); [50,100,150,200,250].forEach(x=>{shapes+=line(x,66,x,114,1.4,soft)}); shapes+=rect(24,24,52,26,'#d9b9670a',1.5)+rect(224,24,52,26,'#d9b9670a',1.5)+rect(24,130,52,26,'#d9b9670a',1.5)+rect(224,130,52,26,'#d9b9670a',1.5); }
  if(t.id==='science') { shapes+=rect(22,28,78,116,'#d9b96708',1.5)+rect(112,28,78,116,'#d9b96708',1.5)+rect(202,28,66,116,'#d9b96708',1.5); [40,70,100].forEach(y=>{shapes+=line(30,y,92,y,1,soft)+line(120,y,182,y,1,soft)+line(210,y,260,y,1,soft)}); }
  if(t.id==='arcade') { [0,1,2,3].forEach(i=>{shapes+=rect(20+i*67,26,52,48,'#d9b9670a',1.5)+rect(20+i*67,94,52,48,'#d9b9670a',1.5)}); }
  if(t.id==='garden') { shapes+=rect(96,48,108,84,'#7f9b5a14',1.5); shapes+=`<circle cx="150" cy="90" r="27" fill="none" stroke="#7f9b5a" stroke-width="2"/><circle cx="150" cy="90" r="11" fill="#7f9b5a20" stroke="#7f9b5a"/>`; [[28,28],[240,28],[28,132],[240,132]].forEach(([x,y])=>{shapes+=`<circle cx="${x+12}" cy="${y+6}" r="9" fill="#7f9b5a16" stroke="#7f9b5a"/>`}); }
  if(t.id==='blackbox') { shapes+=rect(36,32,228,116,'#d9b96705',1.5)+`<circle cx="150" cy="90" r="36" fill="none" stroke="${soft}" stroke-dasharray="4 5"/>`+line(150,52,150,128,1,soft)+line(112,90,188,90,1,soft); }
  return `<svg viewBox="0 0 300 180" role="img" aria-label="${esc(t.name)}平面图" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="180" fill="${bg}"/>${shapes}<text x="150" y="178" text-anchor="middle" font-size="7" fill="#a79a70" letter-spacing="2">WONDER ATLAS · PLAN</text></svg>`;
 }
 function layoutFor(template, items){
  const positions=[]; const classic=[[20,25,165],[225,25,165],[430,25,165],[635,25,165],[20,190,165],[225,190,165],[430,190,165],[635,190,165],[20,355,165],[225,355,165],[430,355,165],[635,355,165]];
  const patterns={
   classic:classic,
   courtyard:[[20,25,150],[220,25,150],[420,25,150],[635,25,150],[20,350,150],[220,350,150],[420,350,150],[635,350,150],[20,180,150],[635,180,150]],
   ring:[[20,25,150],[220,15,150],[430,25,150],[650,115,150],[650,310,150],[430,365,150],[220,365,150],[20,310,150],[20,115,150],[325,180,150]],
   star:[[30,25,150],[350,10,150],[670,25,150],[30,180,150],[350,170,150],[670,180,150],[30,345,150],[350,350,150],[670,345,150]],
   corridor:[[25,25,145],[205,25,145],[385,25,145],[565,25,145],[25,250,145],[205,250,145],[385,250,145],[565,250,145]],
   science:[[20,25,210],[320,25,210],[620,25,210],[20,195,210],[320,195,210],[620,195,210],[20,365,210],[320,365,210],[620,365,210]],
   arcade:[[20,25,155],[225,25,155],[430,25,155],[635,25,155],[20,195,155],[225,195,155],[430,195,155],[635,195,155],[20,365,155],[225,365,155],[430,365,155],[635,365,155]],
   garden:[[20,25,160],[225,25,160],[430,25,160],[635,25,160],[20,190,160],[635,190,160],[20,355,160],[225,355,160],[430,355,160],[635,355,160]],
   blackbox:[[90,50,220],[355,50,220],[620,50,220],[90,250,220],[355,250,220],[620,250,220]]
  };
  const pat=patterns[template]||classic;
  items.forEach((item,i)=>{const p=pat[i%pat.length];let row=Math.floor(i/pat.length);positions.push({exhibit_id:item.id,x:Math.min(850,p[0]+(row%2)*12),y:Math.min(480,p[1]+Math.floor(row/2)*8),width:p[2]});});
  return positions;
 }
 async function loadData(){
  if(!S.user){G.halls=[];G.mine=[];G.hallData=null;return;}
  try{G.halls=await api('/my/halls');G.mine=await api('/my/exhibits');if(!G.selectedHall&&G.halls.length)G.selectedHall=String(G.halls[0].id);if(G.selectedHall&&G.halls.some(h=>String(h.id)===String(G.selectedHall)))G.hallData=await api('/halls/'+G.selectedHall);else G.hallData=null;}catch(e){G.error=e.message;}
 }
 function assetsPanel(){
  const sources=[
   {name:'Poly Haven',desc:'CC0 环境、材质与 3D 模型，可用于空间装饰。',url:'https://polyhaven.com/models',license:'CC0 · 公有领域'},
   {name:'Smithsonian Open Access',desc:'历史器物与部分 3D 扫描；只使用明确标记为 CC0 的项目。',url:'https://www.si.edu/openaccess',license:'逐件确认 CC0'},
   {name:'Sketchfab 可下载模型',desc:'雕塑、器物、家具和建筑模型很多；每个模型的许可可能不同。',url:'https://sketchfab.com/features/gltf',license:'逐件检查 CC BY / CC0 等'},
   {name:'PlayCanvas Model Viewer',desc:'免费开源的浏览器 3D 模型查看器，支持 glTF / GLB。',url:'https://dev.playcanvas.com/products/viewer',license:'MIT · 查看器代码'},
   {name:'Kenney 游戏素材',desc:'大量低多边形道具、家具和游戏资产；按资源页标注使用。',url:'https://kenney.nl/assets',license:'多数素材 CC0，逐包确认'},
   {name:'Wikimedia Commons',desc:'建筑、艺术与历史图片资料库；图片授权因文件而异。',url:'https://commons.wikimedia.org/',license:'逐件检查文件页'}
  ];
  return `<div class="vg-section-head"><div><div class="eyebrow">OPEN ASSET LIBRARY</div><h2>免费展厅图纸与模型素材</h2><p>本站内置的 9 套平面图由项目原创绘制，可以直接套用与导出 SVG；外部库用于补充家具、材质、3D 藏品和参考资料。</p></div></div><div class="vg-asset-grid">${sources.map(x=>`<article class="vg-asset-card"><div class="vg-asset-icon">${x.name.includes('Smithsonian')?'🏺':x.name.includes('PlayCanvas')?'🧊':x.name.includes('Kenney')?'🪑':x.name.includes('Wikimedia')?'📚':x.name.includes('Sketchfab')?'🗿':'🧱'}</div><h3>${esc(x.name)}</h3><p>${esc(x.desc)}</p><span>${esc(x.license)}</span><a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">打开资源库 ↗</a></article>`).join('')}</div><div class="vg-license-note"><b>版权规则</b><p>“免费查看”不等于“可以随便转载”。保存或公开 3D 模型前，必须记录原始链接与具体许可；本馆不批量复制外部模型文件。上方的原创 SVG 平面图可直接在本项目内使用。</p></div>`;
 }
 function designPanel(){
  const current=templates.find(t=>t.id===G.template)||templates[0];
  return `<div class="vg-section-head"><div><div class="eyebrow">BLUEPRINT STUDIO · 原创免费图纸</div><h2>先选一张平面图，再建造你的展厅</h2><p>选中的图纸可以应用到自己的真实展厅。系统会根据藏品数量自动排列卡片，并保存到数据库；原有藏品不会被删除。</p></div><button class="ghost" data-action="vg-download">下载当前 SVG 图纸 ↧</button></div>
  <div class="vg-blueprint-layout"><div class="vg-template-grid">${templates.map(t=>`<button class="vg-template-card ${G.template===t.id?'active':''}" data-action="vg-template" data-template="${t.id}"><div class="vg-template-thumb">${blueprint(t)}</div><div class="vg-template-info"><span>${esc(t.type)} · ${t.rooms} 区参考</span><b>${esc(t.name)}</b><small>${esc(t.desc)}</small></div></button>`).join('')}</div><aside class="vg-blueprint-preview"><div class="eyebrow">SELECTED BLUEPRINT</div><h3>${esc(current.name)}</h3><p>${esc(current.desc)}</p><div class="vg-large-blueprint">${blueprint(current,true)}</div><div class="vg-blueprint-meta"><span>原创 SVG 图纸</span><span>适配 0–150 件展品</span><span>黑金配色</span></div><label class="vg-field">选择要应用的展厅<select id="vgHallSelect" ${!S.user?'disabled':''}>${G.halls.length?G.halls.map(h=>`<option value="${h.id}" ${String(h.id)===String(G.selectedHall)?'selected':''}>${esc(h.name)} · ${h.visibility==='public'?'公开':'私密'}</option>`).join(''):'<option value="">尚未创建展厅</option>'}</select></label><div class="vg-actions"><button class="primary" data-action="vg-apply" ${!S.user||!G.halls.length?'disabled':''}>应用图纸并保存</button><button class="ghost" data-action="vg-create" ${!S.user?'disabled':''}>＋ 新建展厅</button></div>${!S.user?'<p class="vg-hint">登录后即可保存图纸布局。游客仍然可以预览和下载原创 SVG。</p>':!G.halls.length?'<p class="vg-hint">先创建展厅，再把自己的藏品放进来。</p>':'<p class="vg-hint">应用图纸会重排当前展厅里的藏品，不会删除展品或更改公开/私密权限。</p>'}</aside></div>`;
 }
 function tourPanel(){
  const items=G.hallData?.items||[]; const current=items[G.tourIndex]||null;
  if(!S.user)return `<div class="vg-empty"><h2>进入自己的虚拟展厅</h2><p>登录后可以从个人展厅加载藏品，在空间中逐件参观。</p><button class="primary" data-action="login">登录 / 注册</button></div>`;
  if(!G.halls.length)return `<div class="vg-empty"><h2>还没有展厅</h2><p>先去展厅设计选择一张图纸并创建展厅。</p><button class="primary" data-action="vg-tab" data-tab="design">去选图纸</button></div>`;
  if(!items.length)return `<div class="vg-empty"><h2>这个展厅还没有藏品</h2><p>创建展品后，返回图纸设计页可以把个人藏品加入展厅。</p><button class="primary" data-action="vg-tab" data-tab="design">回到展厅设计</button></div>`;
  return `<div class="vg-section-head"><div><div class="eyebrow">IMMERSIVE TOUR · 交互式参观</div><h2>${esc(G.hallData.hall.name)} · 沉浸漫游</h2><p>${G.use3D?'真实 WebGL 三维空间：拖动旋转视角、滚轮缩放，点击墙上的展品切换档案。':'在轻量空间中逐件浏览展品，卡片可翻看背面，图片可放大。'}</p></div><div class="vg-tour-actions"><div class="vg-tour-counter">${G.tourIndex+1} / ${items.length}</div><button class="ghost" data-action="vg-3d-toggle">${G.use3D?'切回轻量展厅':'开启真实 3D 漫游'}</button></div></div>
  ${G.use3D?'<div id="vg3dStage" class="vg-3d-stage"></div>':`<div class="vg-room-scene"><div class="vg-room-backwall"><div class="vg-room-light"></div><div class="vg-room-title">${esc(G.hallData.hall.name)}</div><div class="vg-room-subtitle">WONDER ATLAS · PRIVATE COLLECTION</div><div class="vg-gallery-object ${G.flipped?'flipped':''}" data-action="vg-flip"><div class="vg-object-front">${current.image_url?`<img src="${esc(current.image_url)}" alt="${esc(current.title)}" class="vg-art-img" data-action="vg-zoom">`:`<div class="vg-object-symbol">${esc((current.category||'✦').slice(0,2))}</div>`}<b>${esc(current.title)}</b><small>${esc(current.category||'万物展品')}</small></div><div class="vg-object-back"><span>展品档案</span><b>${esc(current.title)}</b><p>${esc(current.description||current.story||'馆长尚未添加说明。')}</p><small>点击卡片翻回正面</small></div></div><div class="vg-side-frame left"></div><div class="vg-side-frame right"></div></div><div class="vg-room-floor"></div><div class="vg-room-caption"><span>来自馆长 ${esc(G.hallData.hall.owner||S.user.username)}</span><span>使用 ← → 键或下方按钮漫游</span></div></div>`}
  <div class="vg-tour-controls"><button class="ghost" data-action="vg-prev" ${items.length<2?'disabled':''}>← 上一件</button><div><b>${esc(current.title)}</b><small>${esc(current.description||'')}</small></div><button class="primary" data-action="vg-next" ${items.length<2?'disabled':''}>下一件 →</button></div>
  <div class="vg-tour-thumbs">${items.map((x,i)=>`<button class="vg-tour-thumb ${i===G.tourIndex?'active':''}" data-action="vg-goto" data-index="${i}">${x.image_url?`<img src="${esc(x.image_url)}" alt="">`:'<span>✳</span>'}<small>${esc(x.title)}</small></button>`).join('')}</div>`;
 }
 function labPanel(){
  return `<div class="vg-section-head"><div><div class="eyebrow">INTERACTIVE EXHIBIT LAB</div><h2>互动展品实验台</h2><p>这是一个本地运行的简化摆锤实验：改变摆长与初始角度，观察摆动幅度与节奏。它是演示模型，不是精密物理仿真。</p></div></div>
  <div class="vg-lab-layout"><div class="vg-pendulum-stage"><div class="vg-pendulum-ceiling"></div><div class="vg-pendulum" id="vgPendulum" style="--pendulum-angle:25deg;--pendulum-length:180px"><div class="vg-pendulum-string"></div><div class="vg-pendulum-bob"></div></div><div class="vg-stage-floor"></div><div class="vg-stage-label">PENDULUM LAB · DEMO</div></div><div class="vg-lab-controls"><label>摆长 <strong id="vgLengthLabel">180 cm</strong><input type="range" id="vgLength" min="100" max="260" value="180"></label><label>初始角度 <strong id="vgAngleLabel">25°</strong><input type="range" id="vgAngle" min="5" max="55" value="25"></label><label>动画速度 <strong id="vgSpeedLabel">1.0×</strong><input type="range" id="vgSpeed" min="5" max="20" value="10"></label><button class="primary" data-action="vg-lab-reset">重置实验</button><p class="vg-hint">原理提示：在小角度近似下，摆长越长，周期通常越大；真实结果还会受到阻尼、摆球形状和测量误差影响。</p></div></div>
  <div class="vg-lab-next"><b>还可以加入的互动展品</b><span>光学混色 · 行星轨道 · 分形生成 · 机械结构拆解</span><p>后续可以把这些实验作为可独立保存的“互动展品”，放进用户自己的展厅。</p></div>`;
 }
 function render(){
  const tabs=[['design','展厅图纸'],['tour','沉浸漫游'],['lab','互动实验'],['assets','免费素材库']];
  return `<section class="vg-hero"><div class="eyebrow">VIRTUAL MUSEUM STUDIO · V9</div><h1>建造一个可以走进去的世界。</h1><p>选择原创免费图纸，保存自己的展厅布局；沿着藏品逐件漫游，翻看作品背面，或进入互动实验台。外部免费 3D 素材也整理在这里。</p><div class="vg-hero-stats"><span><b>9</b> 套原创平面图</span><span><b>4</b> 个交互模块</span><span><b>0</b> 图纸授权费用</span></div></section><nav class="vg-tabs">${tabs.map(([k,v])=>`<button data-action="vg-tab" data-tab="${k}" class="${G.tab===k?'active':''}">${v}</button>`).join('')}</nav><section id="vgPanel" class="vg-panel">${G.tab==='design'?designPanel():G.tab==='tour'?tourPanel():G.tab==='lab'?labPanel():assetsPanel()}</section>`;
 }
 async function refreshPage(){if(typeof window.render==='function')await window.render();else {const m=$('#main');if(m)m.innerHTML=render();}}
 async function applyBlueprint(){
  if(!S.user){mustLogin();return;}
  if(!G.selectedHall){toast('请先选择或创建展厅');return;}
  let hall=await api('/halls/'+G.selectedHall); let items=hall.items||[];
  if(!items.length){
   const mine=await api('/my/exhibits');
   if(!mine.length){toast('先创建至少一件自己的展品，再把它放进展厅');return;}
   for(const item of mine.slice(0,12)){try{await api('/halls/'+G.selectedHall+'/items',{method:'POST',body:{exhibit_id:item.id}})}catch(e){/* already in this hall */}}
   hall=await api('/halls/'+G.selectedHall);items=hall.items||[];
  }
  if(!items.length){toast('这个展厅还没有可布置的藏品');return;}
  await api('/halls/'+G.selectedHall+'/layout',{method:'PATCH',body:{positions:layoutFor(G.template,items)}});
  G.hallData=await api('/halls/'+G.selectedHall); G.tab='tour'; G.tourIndex=0; G.flipped=false;
  if(window.WonderAnalytics)WonderAnalytics.track('virtual_gallery','apply_blueprint');
  toast('图纸已应用，展品位置已保存'); await refreshPage();
 }
 async function createHall(){
  if(!S.user){mustLogin();return;}
  const name=prompt('给新展厅起个名字：','我的黑金展厅');if(!name||!name.trim())return;
  const desc=prompt('简单介绍一下这个展厅（可留空）：','用自己的收藏建造一座小小博物馆。')||'';
  const result=await api('/halls',{method:'POST',body:{name:name.trim().slice(0,50),description:desc.slice(0,300),theme:'gallery',visibility:'private'}});
  G.selectedHall=String(result.id); G.tab='design'; await refreshPage(); toast('展厅已创建，默认设为私密');
 }
 function downloadSvg(){const t=templates.find(x=>x.id===G.template)||templates[0];const svg=blueprint(t,true).replace(/^<svg[^>]*>/,'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 180" width="1500" height="900">');const blob=new Blob([svg],{type:'image/svg+xml;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`WonderAtlas_${t.id}_floorplan.svg`;document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);toast('原创 SVG 图纸已下载');}
 async function goTour(delta){const items=G.hallData?.items||[];if(!items.length)return;G.tourIndex=(G.tourIndex+delta+items.length)%items.length;G.flipped=false;await refreshPage();}
 document.addEventListener('click',async e=>{
  const b=e.target.closest('[data-action^="vg-"]');if(!b)return;const a=b.dataset.action;
  try{
   if(a==='vg-tab'){G.tab=b.dataset.tab;G.flipped=false;await refreshPage();if(window.WonderAnalytics)WonderAnalytics.track('virtual_gallery','tab_'+G.tab);}
   else if(a==='vg-template'){G.template=b.dataset.template;await refreshPage();}
   else if(a==='vg-download')downloadSvg();
   else if(a==='vg-3d-toggle'){if(!window.WonderGallery3D?.available()){toast('3D 引擎没有加载成功，仍可使用轻量沉浸展厅。请检查网络后重试。');return;}G.use3D=!G.use3D;G.flipped=false;await refreshPage();if(window.WonderAnalytics)WonderAnalytics.track('virtual_gallery',G.use3D?'open_3d':'close_3d');}
   else if(a==='vg-create')await createHall();
   else if(a==='vg-apply')await applyBlueprint();
   else if(a==='vg-prev')await goTour(-1);
   else if(a==='vg-next')await goTour(1);
   else if(a==='vg-goto'){G.tourIndex=Number(b.dataset.index)||0;G.flipped=false;await refreshPage();}
   else if(a==='vg-flip'){G.flipped=!G.flipped;const obj=$('.vg-gallery-object');if(obj)obj.classList.toggle('flipped',G.flipped);}
   else if(a==='vg-zoom'){const item=(G.hallData?.items||[])[G.tourIndex];if(item?.image_url&&typeof window.showModal==='function')showModal(item.title,`<div class="vg-zoom-view"><img src="${esc(item.image_url)}" alt="${esc(item.title)}"><p>${esc(item.description||'')}</p><small>点击图片外部区域关闭 · 图片来源与授权以原始展品记录为准</small></div>`,true);}
   else if(a==='vg-lab-reset'){const l=$('#vgLength'),ang=$('#vgAngle'),sp=$('#vgSpeed');if(l)l.value=180;if(ang)ang.value=25;if(sp)sp.value=10;updateLab();}
  }catch(err){toast(err.message||'操作失败');}
 });
 document.addEventListener('change',e=>{if(e.target.id==='vgHallSelect'){G.selectedHall=e.target.value;G.hallData=null;}});
 document.addEventListener('input',e=>{if(['vgLength','vgAngle','vgSpeed'].includes(e.target.id))updateLab();});
 function updateLab(){const l=Number($('#vgLength')?.value||180),a=Number($('#vgAngle')?.value||25),s=Number($('#vgSpeed')?.value||10);const p=$('#vgPendulum');if(p){p.style.setProperty('--pendulum-angle',a+'deg');p.style.setProperty('--pendulum-negative',(-a)+'deg');p.style.setProperty('--pendulum-length',l+'px');p.style.setProperty('--pendulum-duration',(2.4*(l/180)**.5/(s/10))+'s');}if($('#vgLengthLabel'))$('#vgLengthLabel').textContent=l+' cm';if($('#vgAngleLabel'))$('#vgAngleLabel').textContent=a+'°';if($('#vgSpeedLabel'))$('#vgSpeedLabel').textContent=(s/10).toFixed(1)+'×';}
 document.addEventListener('keydown',e=>{if(window.S?.view==='virtual-gallery'&&G.tab==='tour'&&e.key==='ArrowRight')goTour(1);if(window.S?.view==='virtual-gallery'&&G.tab==='tour'&&e.key==='ArrowLeft')goTour(-1);});
 async function renderPage(){await loadData();const html=render();if(G.tab==='tour'&&G.use3D){setTimeout(()=>{const stage=$('#vg3dStage');if(stage&&window.WonderGallery3D){const ok=WonderGallery3D.mount(stage,G.hallData?.items||[],G.tourIndex,i=>{G.tourIndex=i;G.flipped=false;refreshPage();});if(!ok)toast('3D 引擎未能启动，已保留轻量展厅模式。');}},80);}else{window.WonderGallery3D?.dispose();}return html;}
 window.WonderGallery={render:renderPage};
})();