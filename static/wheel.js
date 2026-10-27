/* V24 — Wonder Wheel. Real cryptographic server draws; local ephemeral guest decisions.
   Colorful SVG segments animate AFTER receiving the backend's winning index.
   Community choices are only real, currently public exhibits. */
(() => {
'use strict';
const W={config:null,wheels:[],wheelId:0,detail:null,guest:null,pending:null,
 search:'',sources:[],notice:'',error:'',busy:false,rotation:0,animation:0,
 result:null,guestIndex:null,history:[],spinTimer:0,guestByTopic:{},sourceWarning:''};
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"\'":'&#39;'}[c]));
const logged=()=>Boolean(window.S?.user);
const button=(action,text,attr='')=>'<button type="button" data-wheel="'+action+'" '+attr+'>'+text+'</button>';
const SCENES={
 food:{label:'🍜 吃什么',title:'今天吃什么？',samples:['米线','菌子火锅','牛排','烤鱼','小锅米线','烧烤'],search:['米线','菌子','牛排','烧烤','甜品','水果']},
 travel:{label:'🧭 去哪玩',title:'周末去哪玩？',samples:['公园散步','逛博物馆','看展览','郊外徒步','去湖边','城市漫游'],search:['旅行','景点','公园','建筑','山川','城市']},
 watch:{label:'🎬 看什么',title:'今晚看什么？',samples:['科幻电影','悬疑片','纪录片','动画电影','经典老片','短片'],search:['电影','动画','纪录片','影视','动漫','剧集']},
 read:{label:'📚 读什么',title:'下一本读什么？',samples:['科普读物','短篇小说','人物传记','自然图鉴','历史故事','文学作品'],search:['书籍','小说','文学','古籍','诗歌','漫画']},
 study:{label:'🧠 学什么',title:'今晚学什么？',samples:['数学','编程','英语','算法','摄影','天文'],search:['数学','编程','物理','人工智能','计算机','语言']},
 exercise:{label:'🏃 怎么运动',title:'今天做什么运动？',samples:['散步','慢跑','拉伸','篮球','骑行','跳绳'],search:['运动','跑步','篮球','健身','骑行','舞蹈']},
 activity:{label:'🎲 做什么',title:'无聊时做什么？',samples:['去逛展','听音乐','动手做实验','整理收藏','画一张画','拍一张照片'],search:['手工','摄影','实验','游戏','艺术','音乐']},
 custom:{label:'✦ 自定义',title:'让万物决定',samples:['探索新领域','随机看件藏品','研究一个问题','画画','体验一个实验','学习新技能'],search:['自然','科技','艺术','生活','故事','历史']}
};
const PALETTE={
 amber:['#f2b766','#e99174','#d6aa7b','#d7c389','#f29b70','#d89ba1'],
 nebula:['#6778d1','#a480c8','#628dae','#9c77aa','#6280ca','#c1a5dd'],
 mint:['#4aa9a1','#83c9aa','#7dbbb9','#90d5ce','#77a592','#a4d1b2'],
 rose:['#de8399','#b87fbc','#e6b3a7','#b58ab3','#d19aa3','#f3ae90']
};
function freshGuest(topic){
 const def=SCENES[topic]||SCENES.food;
 return {labels:[...def.samples],sourceIds:{},title:def.title,topic:def.topic||topic,
  theme:'amber',no_repeat:true,last:null,history:[]};
}
function normalizeGuest(raw,topic){
 const d=freshGuest(topic);
 if(!raw||!Array.isArray(raw.labels))return d;
 const labels=[...new Set(raw.labels.filter(x=>typeof x==='string'&&x.trim().length>0&&x.length<=75).map(x=>x.trim()))].slice(0,24);
 return {labels,sourceIds:raw.sourceIds&&typeof raw.sourceIds==='object'?raw.sourceIds:{},
  title:String(raw.title||d.title).slice(0,60),topic,theme:PALETTE[raw.theme]?raw.theme:'amber',
  no_repeat:raw.no_repeat!==false,last:Number.isInteger(raw.last)?raw.last:null,
  history:Array.isArray(raw.history)?raw.history.slice(0,20):[]};
}
function localLoad(){
 if(W.guest)return;
 let saved=null,legacy=null;
 try{saved=JSON.parse(localStorage.getItem('wonder-wheel-v39')||'null');
  legacy=JSON.parse(localStorage.getItem('wonder-wheel-v24')||'null')}catch(_){}
 W.guestByTopic={};
 if(saved&&saved.byTopic&&typeof saved.byTopic==='object'){
  for(const key of Object.keys(SCENES)){
   if(saved.byTopic[key])W.guestByTopic[key]=normalizeGuest(saved.byTopic[key],key);
  }
 }
 if(legacy&&Array.isArray(legacy.labels)){
  const key=SCENES[legacy.topic]?legacy.topic:'food';
  if(!W.guestByTopic[key])W.guestByTopic[key]=normalizeGuest(legacy,key);
 }
 const current=SCENES[saved?.current]?saved.current:SCENES[legacy?.topic]?legacy.topic:'food';
 W.guest=W.guestByTopic[current]||freshGuest(current);W.guestByTopic[current]=W.guest;
}
function localSave(){
 try{if(!W.guest)return;W.guestByTopic[W.guest.topic]=W.guest;
  localStorage.setItem('wonder-wheel-v39',
    JSON.stringify({current:W.guest.topic,byTopic:W.guestByTopic}))}catch(_){}
}
function setGuestTopic(topic){
 localLoad();
 if(!SCENES[topic])return;
 W.guestByTopic[W.guest.topic]=W.guest;
 W.guest=W.guestByTopic[topic]||freshGuest(topic);
 W.guestByTopic[topic]=W.guest;
 W.search='';W.sources=[];W.sourceWarning='';resetAnimation();localSave();
}
async function verifyGuestSources(){
 if(logged()||!W.guest)return;
 const oldSources=W.guest.sourceIds||{};
 const sourceIds=[...new Set(Object.values(oldSources).map(Number).filter(Number.isSafeInteger))].slice(0,24);
 if(!sourceIds.length)return;
 const valid=(await api('/wheels/resolve?ids='+sourceIds.join(','))).items||[];
 const known=new Map(valid.map(x=>[x.id,x.title]));
 const revised=[],seen=new Set(),newIds={};
 let hidden=0;
 for(const name of W.guest.labels){
  const id=Number(oldSources[name]||0);
  if(id&&!known.has(id)){hidden++;continue}
  const label=id?known.get(id):name;
  if(!label||seen.has(label.toLocaleLowerCase()))continue;
  seen.add(label.toLocaleLowerCase());revised.push(label);
  if(id)newIds[label]=id;
 }
 if(hidden||revised.join('\n')!==W.guest.labels.join('\n')){
  W.guest.labels=revised;W.guest.sourceIds=newIds;W.guest.last=null;
  W.guest.history=[];W.sourceWarning=hidden?'有 '+hidden+' 件原始馆藏已撤回或不再公开，已移除其缓存标题及抽取记录。':'已同步最新的公开馆藏名称。';
  localSave();
 }
}
function selectedItems(){return logged()?W.detail?.items||[]:(W.guest?.labels||[]).map((label,i)=>({id:i+1,kind:W.guest.sourceIds?.[label]?'exhibit':'manual',label,exhibit_id:W.guest.sourceIds?.[label]||null}));}
function current(){return logged()?W.detail:{title:W.guest.title,topic:W.guest.topic,theme:W.guest.theme,
 no_repeat:W.guest.no_repeat,items:selectedItems(),history:W.guest.history,
 unavailable_count:0};}
function resetAnimation(){clearTimeout(W.spinTimer);W.busy=false;W.animation++;W.rotation=0;W.result=null;W.guestIndex=null;}
async function ensureWheel(topic){
 if(!SCENES[topic])topic='custom';
 let target=W.wheels.find(x=>x.topic===topic);
 if(!target){const d=SCENES[topic];const created=await api('/wheels',{method:'POST',body:{title:d.title,topic,theme:W.detail?.theme||'amber',no_repeat:true}});
   W.wheels=(await api('/wheels')).items||[];target=W.wheels.find(x=>x.id===created.id);
 }
 W.wheelId=target?.id||W.wheelId;W.detail=await api('/wheels/'+W.wheelId);
}

async function load(){
 W.error='';localLoad();
 try{
  if(!W.config)W.config=await api('/wheels/config');
  if(logged()){
   W.wheels=(await api('/wheels')).items||[];
   if(W.pending?.topic&&SCENES[W.pending.topic]){
    await ensureWheel(W.pending.topic);
   }else{
    if(!W.wheels.some(x=>x.id===W.wheelId))W.wheelId=W.wheels[0]?.id||0;
    W.detail=W.wheelId?await api('/wheels/'+W.wheelId):null;
   }
  }else{
   W.wheels=[];W.wheelId=0;W.detail=null;
   if(W.pending?.topic&&W.guest.topic!==W.pending.topic)setGuestTopic(W.pending.topic);
  }
  if(W.pending?.auto){
   // The exhibit click is explicit; no need to make the visitor click twice.
   const queued=W.pending;W.pending=null;
   try{
    if(logged()){
     if(!W.wheelId)await ensureWheel(queued.topic||'custom');
     await api('/wheels/'+W.wheelId+'/items',{method:'POST',
       body:{kind:'exhibit',exhibit_id:queued.id}});
    }else guestAdd(queued.title,queued.id);
    W.notice='✓ 已放入'+(SCENES[queued.topic]?.label||'万物')+'转盘：'+queued.title+'。添加至少两个选项即可抽取。';
   }catch(err){
    if(/重复|已经在|已添加/.test(err.message)){
     W.notice='这件藏品已在当前转盘中，不必重复添加。';
    }else{
     W.pending={...queued,auto:false};W.error=err.message||'加入转盘失败，可以在下面重试。';
    }
   }
   if(logged()&&W.wheelId)W.detail=await api('/wheels/'+W.wheelId);
  }
  if(!logged())await verifyGuestSources();
  if(W.search)W.sources=(await api('/wheels/sources?q='+encodeURIComponent(W.search))).items||[];
 }catch(err){W.error=err.message||'无法连接万物转盘';}
}
function svgWheel(items,theme){
 const n=items.length;
 if(!n)return '<div class="ww-dial-empty">转盘尚未放入选项</div>';
 const colors=PALETTE[theme]||PALETTE.amber;
 const center=180,r=164,deg=360/n;
 const sectors=items.map((item,i)=>{
  const start=(-90+i*deg)*Math.PI/180,end=(-90+(i+1)*deg)*Math.PI/180;
  const large=deg>180?1:0;
  const startX=center+r*Math.cos(start),startY=center+r*Math.sin(start);
  const endX=center+r*Math.cos(end),endY=center+r*Math.sin(end);
  const path='M180 180 L'+startX.toFixed(2)+' '+startY.toFixed(2)+
    ' A164 164 0 '+large+' 1 '+endX.toFixed(2)+' '+endY.toFixed(2)+' Z';
  const mid=(start+end)/2,tx=center+102*Math.cos(mid),ty=center+102*Math.sin(mid);
  const label=String(item.label||'未命名');
  const text=label.length>(n>12?5:8)?label.slice(0,n>12?4:7)+'…':label;
  return '<path d="'+path+'" fill="'+colors[i%colors.length]+'" stroke="#201f36" stroke-width="2"/>'+
    '<text x="'+tx.toFixed(1)+'" y="'+ty.toFixed(1)+'" text-anchor="middle" dominant-baseline="middle" font-size="'+(n>16?'9':n>10?'11':'13')+'" fill="#292238" font-weight="700">'+esc(text)+'</text>';
 }).join('');
 return '<svg id="ww-rotor" width="360" height="360" viewBox="0 0 360 360" role="img" aria-label="包含'+n+'个选项的可旋转抽取转盘">'+
 '<circle cx="180" cy="180" r="175" fill="#121e31" stroke="#d4b880" stroke-width="5"/>'+
 sectors+'<circle cx="180" cy="180" r="30" fill="#24354a" stroke="#f0d8a4" stroke-width="6"/>'+
 '<text x="180" y="185" fill="#f1d8aa" text-anchor="middle" font-size="22">✦</text></svg>';
}
function hero(){
 return '<section class="ww-hero"><div class="ww-kicker">WONDER ATLAS · V39 · EIGHT DECISION WORLDS</div>'+
 '<h1>🎡 不止今天吃什么。<br><em>你收藏的万物，都可以成为下一次选择。</em></h1>'+
 '<p>美食 · 旅行 · 影视 · 阅读 · 学习 · 运动 · 日常活动 · 自定义。八种场景各有自己的候选选项和历史，从展品一键加入，抽中后可回到原始馆藏。</p>'+
 '<div class="ww-labels">♡ 无付费 · ◌ 随机抽取 · ✦ 真正馆藏或自己的选项</div>'+button('destiny','✨ 不只抽一次：开启万物命运接力 ↗','class="ww-destiny-link"')+'</section>';
}
function sceneButtons(){
 return '<div class="ww-scenes" role="group" aria-label="选择专属决策转盘">'+Object.entries(SCENES).map(([key,x])=>
 button('scene',x.label,'data-topic="'+key+'" aria-pressed="'+((current()?.topic||'food')===key?'true':'false')+'" class="'+((current()?.topic||'food')===key?'active':'')+'"')).join('')+'</div>';
}
function showSpinner(){
 const d=current();
 if(!d)return '<section class="ww-panel"><h2>✦ 先选一个决策主题</h2><p>点击上方八种场景，即可创建对应的独立私人转盘。</p></section>';
 const items=selectedItems(),available=items.length;
 return '<section class="ww-play-panel"><div class="ww-pane-title"><span class="ww-kicker">DECIDE BY DISCOVERY</span>'+
 '<h2>'+esc(d.title)+'</h2><p>有效选项 '+available+' / 24 · '+(d.no_repeat?'开启连续防重复':'允许连续重复')+
 (d.unavailable_count?' · '+d.unavailable_count+' 件来源已撤回，自动停止参与':'')+'</p></div>'+
 '<div class="ww-two"><div class="ww-dial"><div class="ww-arrow" aria-hidden="true">▼</div>'+
 svgWheel(items,d.theme)+'<button id="ww-trigger" data-wheel="spin" type="button" '+
 (available<2||W.busy?'disabled':'')+'>🎲 '+(W.busy?'抽取中…':'开始抽取')+'</button></div>'+
 '<div class="ww-rhs">'+(W.result?'<div id="ww-result" class="ww-winner" role="status"><span>THE UNEXPECTED PICK</span>'+
 '<h3>'+esc(W.result.label)+'</h3><p>这次命运指向了它 ✨</p>'+
 (W.result.exhibit_id?button('look','查看抽中的馆藏','data-id="'+W.result.exhibit_id+'"'):'')+
 '</div>':'<div id="ww-result" class="ww-winner ww-winner-wait" role="status"><span>ONE RANDOM CHOICE</span><h3>今天让万物替你选一次。</h3>'+
 '<p>每个有效选项机会相同，连续防重复时会排除上次结果。</p></div>')+
 '<div class="ww-entries-title">◈ 当前选项 <span>'+available+' 件</span></div>'+
 '<div class="ww-entry-list">'+(items.length?items.map(e=>
 '<div class="ww-entry"><span>'+esc(e.kind==='exhibit'?'🏛':'✦')+' '+esc(e.label)+'</span>'+
 button('remove','×','data-id="'+e.id+'" aria-label="移除'+esc(e.label)+'"')+'</div>').join(''):
 '<p>还没有候选项，先在下面加入至少两项。</p>')+'</div>'+
 '<p class="ww-small">抽取只帮助决定，结果不代表推荐、消费建议或现实环境真实性。</p>'+
 '</div></div></section>';
}
function wheelControls(){
 if(!logged())return '<section class="ww-panel"><h2>🎁 游客体验：免登录也能抽</h2>'+
 '<p>上方是<b>仅供演示的预设候选</b>，不是社区用户投稿。八种场景互不混合；游客的自定义内容只保存在当前浏览器。</p>'+
 '<form id="ww-guest-config" class="ww-controls"><label>转盘名字<input name="title" value="'+esc(W.guest.title)+'" minlength="2" maxlength="60" required></label>'+
 '<label>颜色风格<select name="theme">'+options('theme',W.guest.theme)+'</select></label>'+
 '<label class="ww-tick"><input name="no_repeat" type="checkbox" '+(W.guest.no_repeat?'checked':'')+'>不连续抽中同一项</label>'+
 '<button class="ww-primary" type="submit">保存转盘设置</button></form></section>';
 return '<section class="ww-panel"><div class="ww-header-row"><div><span class="ww-kicker">MY PRIVATE DECISION WHEELS</span>'+
 '<h2>♡ 私人万物转盘</h2><p>最多 12 个转盘，每个容纳 24 项。不会公开你的选项或抽取历史。</p></div>'+
 '</div>'+
 '<div class="ww-wheel-tabs">'+W.wheels.map(x=>button('choose','◉ '+esc(x.title),
 'data-id="'+x.id+'" class="'+(W.wheelId===x.id?'active':'')+'"')).join('')+
 button('new-form','＋ 创建新转盘','class="ww-new"')+'</div>'+
 '<div id="ww-form-slot">'+(W.detail?'<form id="ww-edit-wheel" class="ww-controls">'+
 '<label>转盘名称<input name="title" value="'+esc(W.detail.title)+'" maxlength="60" minlength="2" required></label>'+
 '<label>场景<select name="topic">'+options('topic',W.detail.topic)+'</select></label>'+
 '<label>配色<select name="theme">'+options('theme',W.detail.theme)+'</select></label>'+
 '<label class="ww-tick"><input name="no_repeat" type="checkbox" '+(W.detail.no_repeat?'checked':'')+'>避免连续抽到相同选项</label>'+
 '<button class="ww-primary" type="submit">保存设置</button>'+button('delete-wheel','删除转盘')+'</form>':
 '<p class="ww-small">还没有长期转盘。点击「＋ 创建新转盘」开始。</p>')+'</div></section>';
}
function options(field,value){
 const opts=field==='theme'?[['amber','琥珀金'],['nebula','星云紫'],['mint','生命绿'],['rose','玫瑰粉']]:
   Object.entries(SCENES).map(([key,x])=>[key,x.label]);
 return opts.map(([id,label])=>'<option value="'+id+'" '+(value===id?'selected':'')+'>'+label+'</option>').join('');
}
function addControls(){
 const d=current();
 return '<section class="ww-panel"><div class="ww-header-row"><div><span class="ww-kicker">COLLECT FIRST · DRAW LATER</span>'+
 '<h2>✦ 放进'+esc((SCENES[d?.topic]||SCENES.custom).label)+'转盘</h2><p>① 选择场景 → ② 放入真实公开藏品或自定义选项 → ③ 至少两项，开始抽取。</p></div></div>'+
 '<div class="ww-food-picks"><b>⌕ '+esc((SCENES[d?.topic]||SCENES.custom).label)+' · 发现相关馆藏</b><p>从本站当前公开的真实藏品中选择；没有找到时，可以手动添加。</p><div>'+((SCENES[d?.topic]||SCENES.custom).search).map(q=>button('scene-search',esc(q),'data-query="'+esc(q)+'"')).join('')+'</div></div>'+
 (W.pending?'<div class="ww-pending"><b>🏛 刚刚在展厅逛到：</b><span>'+esc(W.pending.title)+'</span>'+
 button('add-pending',logged()?'放入当前私人转盘':'加入临时转盘','class="ww-primary"')+
 button('dismiss','取消')+'</div>':'')+
 '<form id="ww-add-manual" class="ww-search"><label>自定义选项<input name="label" maxlength="75" placeholder="例如：米线、读书、郊游、写代码……" required></label>'+
 '<button class="ww-primary" type="submit" '+(logged()&&!W.wheelId?'disabled':'')+'>＋ 加入转盘</button></form>'+
 '<div class="ww-suggestions"><b>⚡ 想不到候选项？用当前场景的示例开始</b><div>'+button('template','✨ 装填 '+esc((SCENES[d?.topic]||SCENES.custom).label)+'示例','data-topic="'+esc(d?.topic||'custom')+'"')+'</div></div>'+
 '<form id="ww-search-museum" class="ww-search"><label>🔎 搜索真实公开馆藏<input name="q" value="'+esc(W.search)+'" maxlength="70" placeholder="搜索公开馆藏，也可点上方快捷搜索"></label>'+
 '<button type="submit">查找馆藏</button></form>'+
 (W.search?'<div class="ww-source-list">'+(W.sources.length?W.sources.map(x=>
 '<div><span>🏛 '+esc(x.title)+'<small>'+esc(x.domain)+' · '+esc(x.category)+'</small></span>'+
 button('add-source','加入转盘','data-id="'+x.id+'" data-title="'+esc(x.title)+'"')+'</div>').join(''):
 '<p class="ww-small">暂时没有找到仍公开且匹配的用户馆藏，可以先手动输入一个选项。</p>')+'</div>':
 '<p class="ww-small">搜索结果只来自目前真正公开的馆藏，不会生成虚构的馆长投稿。</p>')+
 '</section>';
}
function history(){
 const h=current()?.history||[];
 return '<section class="ww-panel"><div class="ww-header-row"><div><span class="ww-kicker">LET CHANCE REMEMBER</span>'+
 '<h2>⏳ 最近抽中了什么</h2><p>'+ (logged()?'仅自己可见，自动保留最近 20 次抽取。':'游客历史仅存在当前浏览器中。')+'</p></div></div>'+
 (h.length?'<div class="ww-history">'+h.map((x,i)=>'<div><span>NO. '+(h.length-i).toString().padStart(2,'0')+
 '</span><b>'+esc(x.label)+'</b><small>'+esc(x.drawn_at||'本地抽取')+'</small></div>').join('')+'</div>':
 '<div class="ww-empty">转盘还没有记录，试试第一次抽取吧 ✨</div>')+'</section>';
}
async function render(){
 await load();return '<div class="ww-root">'+hero()+sceneButtons()+
 (W.notice?'<div class="ww-notice">'+esc(W.notice)+'</div>':'')+
 (W.error?'<div class="ww-error">'+esc(W.error)+'</div>':'')+
 (W.sourceWarning?'<div class="ww-notice" role="status">'+esc(W.sourceWarning)+'</div>':'')+
 '<div class="ww-layout"><div>'+showSpinner()+wheelControls()+'</div>'+
 '<div>'+addControls()+history()+'</div></div>'+
 '<footer class="ww-small">这是私人随机决策工具，不涉及付费、彩票、赌注或中奖金钱。手动模板不是平台真实馆藏。</footer></div>';
}
async function redraw(){
 if(window.S?.view!=='wheels')return;
 const main=document.querySelector('#main');
 if(!main)return;
 main.innerHTML=await render();
}
function queueExhibit(id,title,topic){
 localLoad();
 W.pending={id:Number(id),title:String(title||'这件藏品'),topic:SCENES[topic]?topic:'custom',auto:true};
 if(!logged()&&W.pending.topic!==W.guest.topic)setGuestTopic(W.pending.topic);
 W.notice='正在把这件原始藏品加入「'+SCENES[W.pending.topic].label+'」转盘。';
}
function guestAdd(label,exhibitId){
 label=String(label||'').trim();
 if(!label||label.length>75)throw Error('选项长度需要在 1–75 字内');
 if(W.guest.labels.some(x=>x.toLocaleLowerCase()===label.toLocaleLowerCase()))throw Error('该选项已经在转盘里');
 if(W.guest.labels.length>=24)throw Error('转盘最多可放 24 个选项');
 W.guest.labels.push(label);if(exhibitId)W.guest.sourceIds[label]=Number(exhibitId);W.guest.last=null;W.notice='已加入临时转盘：'+label;localSave();
}
function formValues(f){
 const o=Object.fromEntries(new FormData(f));
 return {title:String(o.title||'').trim(),topic:o.topic||'food',theme:o.theme||'amber',
         no_repeat:!!f.elements.no_repeat?.checked};
}
function showFinal(pick){
 const panel=document.querySelector('#ww-result');
 if(!panel)return;
 W.result=pick;
 panel.className='ww-winner';panel.innerHTML='<span>THE UNEXPECTED PICK</span><h3>'+esc(pick.label)+'</h3>'+
 '<p>万物指向了这个答案 ✨</p>'+
 (pick.exhibit_id?button('look','🏛 查看抽中的原始馆藏','data-id="'+pick.exhibit_id+'"'):'');
}
async function spin(){
 if(W.busy)return;
 const entries=selectedItems();
 if(entries.length<2)throw Error('至少需要两个有效选项');
 W.busy=true;const startAnimation=++W.animation;
 document.querySelector('#ww-trigger')?.setAttribute('disabled','');
 let response;
 try{
  if(logged())response=await api('/wheels/'+W.wheelId+'/spin',{method:'POST'});
  else response=await api('/wheels/preview',{method:'POST',body:{options:W.guest.labels,
    last_index:W.guest.last,no_repeat:W.guest.no_repeat}});
 }catch(e){W.busy=false;document.querySelector('#ww-trigger')?.removeAttribute('disabled');throw e;}
 const index=logged()?response.winner_index:response.index;
 const item=logged()?response.winner:{label:response.label,exhibit_id:W.guest.sourceIds?.[response.label]||null};
 if(startAnimation!==W.animation)return;
 const rotor=document.getElementById('ww-rotor');
 const deg=360/entries.length;
 const target=-(index+.5)*deg;
 const currentMod=((W.rotation%360)+360)%360;
 const advance=((target-currentMod)%360+360)%360;
 W.rotation+=360*5+advance;
 if(rotor){
  rotor.style.transition='transform 3.4s cubic-bezier(.14,.76,.11,1)';
  rotor.style.transform='rotate('+W.rotation+'deg)';
 }
 W.spinTimer=setTimeout(async()=>{
  if(startAnimation!==W.animation||window.S?.view!=='wheels')return;
  W.busy=false;
  if(!logged()){
   W.guest.last=index;
   W.guest.history.unshift({label:item.label,drawn_at:new Date().toLocaleString('zh-CN')});
   W.guest.history=W.guest.history.slice(0,20);localSave();
  }
  showFinal(item);
  const trigger=document.querySelector('#ww-trigger');
  if(trigger){trigger.removeAttribute('disabled');trigger.textContent='再抽一次 ↻';}
  // The next full refresh will reconcile server-side history & revoked source links.
 },3600);
}
document.addEventListener('click',async ev=>{
 const b=ev.target.closest('[data-wheel]');if(!b)return;
 ev.preventDefault();ev.stopImmediatePropagation();
 const act=b.dataset.wheel,id=Number(b.dataset.id||0);
 try{
  if(act==='spin'){await spin();return;}
  if(act==='destiny'){await navigate('adventure');return;}
  if(W.busy)return;
  if(act==='choose'){W.wheelId=id;resetAnimation();}
  else if(act==='scene'){
   const k=b.dataset.topic;
   if(logged()){
    let target=W.wheels.find(x=>x.topic===k);
    if(!target){const title=k==='food'?'今天吃什么？':SCENES[k].label+'？';const created=await api('/wheels',{method:'POST',body:{title,topic:k,theme:W.detail?.theme||'amber',no_repeat:true}});W.wheelId=created.id;W.notice='已创建'+SCENES[k].label+'专属转盘。';}
    else{W.wheelId=target.id;W.notice='已切换到'+SCENES[k].label+'专属转盘。';}
   }else {W.guest.topic=k;W.guest.title=k==='food'?'今天吃什么？':SCENES[k].label+'？';localSave();W.notice='已切换场景；现有选项保留，可点击灵感模板替换。';resetAnimation();}
  }else if(act==='food-search'){
   W.search=String(b.dataset.query||'').trim();W.sources=(await api('/wheels/sources?q='+encodeURIComponent(W.search))).items||[];
   W.notice=W.sources.length?'找到 '+W.sources.length+' 件当前公开的相关馆藏。':'暂时没有匹配的公开馆藏，可以手动加入这个食物。';
  }else if(act==='template'){
   const x=SCENES[b.dataset.topic];if(!x)return;
   if(logged()){
    if(!W.wheelId)throw Error('请先创建一个私人转盘');
    let added=0;
    for(const label of x.samples){
     try{await api('/wheels/'+W.wheelId+'/items',{method:'POST',body:{kind:'manual',label}});added++;}catch(e){
      if(!/(已经在|最多放入)/.test(e.message))throw e;
     }
    }
    W.notice='已添加 '+added+' 个演示灵感选项。它们不是馆长的真实投稿。';
   }else{
    W.guest.labels=[...x.samples];W.guest.sourceIds={};W.guest.topic=b.dataset.topic;W.guest.title=b.dataset.topic==='food'?'今天吃什么？':x.label+'？';
    W.guest.last=null;W.guest.history=[];localSave();W.notice='已装填演示灵感选项。';
   }
   resetAnimation();
  }else if(act==='new-form'){
   document.getElementById('ww-form-slot').innerHTML='<form id="ww-create" class="ww-controls">'+
    '<label>新的转盘名称<input name="title" maxlength="60" minlength="2" value="今天吃什么？" required></label>'+
    '<label>决定哪类事情<select name="topic">'+options('topic','food')+'</select></label>'+
    '<label>配色<select name="theme">'+options('theme','amber')+'</select></label>'+
    '<label class="ww-tick"><input type="checkbox" name="no_repeat" checked>不连续抽中同一项</label>'+
    '<button class="ww-primary" type="submit">创建我的私人转盘</button></form>';return;
  }else if(act==='delete-wheel'){
   if(!window.confirm('删除这个转盘和它的选项、历史记录？不会删除原始馆藏。'))return;
   await api('/wheels/'+W.wheelId,{method:'DELETE'});W.wheelId=0;W.notice='已删除转盘';resetAnimation();
  }else if(act==='remove'){
   if(logged())await api('/wheels/'+W.wheelId+'/items/'+id,{method:'DELETE'});
   else {const removed=W.guest.labels.splice(id-1,1)[0];if(removed&&W.guest.sourceIds)delete W.guest.sourceIds[removed];W.guest.last=null;localSave();}
   resetAnimation();W.notice='已移除该选项';
  }else if(act==='add-pending'){
   if(!W.pending)return;
   if(logged()){
    if(!W.wheelId)throw Error('请先创建一个私人转盘');
    await api('/wheels/'+W.wheelId+'/items',{method:'POST',
      body:{kind:'exhibit',exhibit_id:W.pending.id}});
   }else guestAdd(W.pending.title,W.pending.id);
   W.notice='🏛 已加入刚刚发现的馆藏：'+W.pending.title;W.pending=null;resetAnimation();
  }else if(act==='dismiss'){W.pending=null;}
  else if(act==='add-source'){
   if(logged()){
    if(!W.wheelId)throw Error('请先创建一个私人转盘');
    await api('/wheels/'+W.wheelId+'/items',{method:'POST',body:{kind:'exhibit',exhibit_id:id}});
    W.notice='已经把真实馆藏加入私人转盘！';
   }else guestAdd(b.dataset.title,id);
   resetAnimation();
  }else if(act==='look'){
   if(typeof openDetail==='function')await openDetail(id);
   return;
  }
  await redraw();
 }catch(e){W.error=e.message;if(typeof toast==='function')toast(e.message);}
},true);
document.addEventListener('submit',async ev=>{
 const form=ev.target;
 if(!['ww-guest-config','ww-create','ww-edit-wheel','ww-add-manual','ww-search-museum'].includes(form.id))return;
 ev.preventDefault();ev.stopImmediatePropagation();
 try{
  if(form.id==='ww-search-museum'){
   W.search=new FormData(form).get('q').trim();W.sources=[];
  }else if(form.id==='ww-add-manual'){
   const label=String(new FormData(form).get('label')||'').trim();
   if(logged()){
    if(!W.wheelId)throw Error('请先创建一个转盘');
    await api('/wheels/'+W.wheelId+'/items',{method:'POST',body:{kind:'manual',label}});
    W.notice='✦ 已加入：'+label;
   }else guestAdd(label);
   resetAnimation();
  }else{
   const body=formValues(form);
   if(form.id==='ww-guest-config'){
    Object.assign(W.guest,body);localSave();W.notice='临时转盘设置已保存。';
   }else if(form.id==='ww-create'){
    const r=await api('/wheels',{method:'POST',body});W.wheelId=r.id;W.notice='✦ 私人转盘创建成功，请添加至少两个选项。';
   }else if(form.id==='ww-edit-wheel'){
    await api('/wheels/'+W.wheelId,{method:'PATCH',body});W.notice='转盘设置已更新';
   }
   resetAnimation();
  }
  await redraw();
 }catch(e){if(typeof toast==='function')toast(e.message);}
},true);
window.WonderWheel={render,queueExhibit,stop:resetAnimation};
})();
