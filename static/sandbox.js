/* V23: World Sandbox — interactive resistor blocks and time-ordered curations.
   Names/stories/URLs are escaped. All projects come from real authors and storage.
   Uses only a fixed schema: no injected JS, embeds, or arbitrary custom shaders. */
(() => {
'use strict';
const H={config:null,scope:'public',projects:[],selected:0,detail:null,editor:false,
    editing:0,draft:null,kind:'circuit',response:null,focus:0,notice:'',error:''};
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"\'":'&#39;'}[c]));
const btn=(act,txt,attrs='')=>'<button type="button" data-sbx="'+act+'" '+attrs+'>'+txt+'</button>';
const clone=v=>JSON.parse(JSON.stringify(v));
const login=()=>Boolean(window.S?.user);
const fmt=n=>Number(n).toLocaleString('zh-CN',{maximumFractionDigits:5});
const era=y=>y<0?'公元前 '+fmt(-y)+' 年':'公元 '+fmt(y)+' 年';
function reset(kind='circuit'){
 H.kind=kind;H.editing=0;H.draft={kind,title:'',description:'',config:clone(H.config.defaults[kind])};H.response=null;
}
async function load(){
 H.error='';
 try{
  if(!H.config)H.config=await api('/play/sandbox/config');
  if(!H.draft)reset();
  if(!login())H.scope='public';
  H.projects=(await api('/play/sandbox?scope='+H.scope)).items||[];
  if(!H.projects.some(x=>x.id===H.selected))H.selected=H.projects[0]?.id||0;
  H.detail=H.selected?await api('/play/sandbox/'+H.selected):null;
  if(H.detail?.kind==='circuit'&&!H.response){
   H.response=(await api('/play/sandbox/'+H.selected+'/simulate',
       {method:'POST',body:H.detail.config})).result;
  }
  if(H.detail?.kind==='timeline')H.focus=Math.min(H.focus,H.detail.config.events.length-1);
 }catch(err){H.error=err.message||'万物沙盒暂时无法访问';H.detail=null;}
}
function hero(){
 return '<section class="sb-hero"><span>WONDER ATLAS · V23 · SANDBOX OF EVERYTHING</span>'+
 '<h2>🛠️ 把整个世界，<em>拆成可以玩的积木。</em></h2>'+
 '<p>一边摆放电阻，一边观察电流；穿过亿年前与未来，亲自编排一座万物时间剧场。无需写代码，作品还能收入你的私人博物馆。</p>'+
 '<div class="sb-labels"><b>⚡ 电路实验</b><b>⏳ 时间故事</b><b>🏛 真实私人展品</b><b>🔐 主动授权公开</b></div></section>';
}
function gallery(){
 return '<section class="sb-panel"><div class="sb-head"><div><span class="sb-kicker">A COMMUNITY OF INVENTORS</span>'+
 '<h3>✦ 万物沙盒作品</h3><p>作品均由注册馆长真正创建。未授权的个人作品不会出现在公开广场。</p></div>'+
 '<div class="sb-actions">'+(login()?btn('scope','我的作品','data-scope="mine" class="'+(H.scope==='mine'?'active':'')+'"'):'')+
 btn('scope','公开广场','data-scope="public" class="'+(H.scope==='public'?'active':'')+'"')+'</div></div>'+
 '<div class="sb-cards">'+(H.projects.length?H.projects.map(x=>
 btn('select','<span>'+esc(x.label)+'</span><strong>'+esc(x.title)+'</strong><small>馆长 '+esc(x.creator)+' · '+(x.public?'公开':'私人')+'</small>',
 'data-id="'+x.id+'" class="sb-project '+(H.selected===x.id?'active':'')+'"')).join(''):
 '<div class="sb-empty">这里还没有公开作品。登录后可以建造第一件。</div>')+'</div></section>';
}
function circuitDraw(result){
 if(!result)return '<div class="sb-empty">点击运行模型查看电流与每个电阻的电压。</div>';
 const rs=result.resistors,mode=result.mode;
 const w=650,h=245,cx=325;
 let wires='',boxes='';
 if(mode==='series'){
  const width=470,step=width/rs.length;
  wires='<path d="M90 125 V52 H560 V125 M90 125 V192 H560 V125" />';
  boxes=rs.map((v,i)=>{const x=90+step*(i+.5);return '<g><rect x="'+(x-33).toFixed(1)+'" y="36" width="66" height="32" rx="6"/>'+
   '<text x="'+x.toFixed(1)+'" y="28" text-anchor="middle">R'+(i+1)+'</text>'+
   '<text x="'+x.toFixed(1)+'" y="56" text-anchor="middle">'+fmt(v)+'Ω</text></g>';}).join('');
 }else{
  wires='<path d="M80 130 V42 H560 V130 M80 130 V195 H560 V130" />';
  const step=470/(rs.length+1);
  boxes=rs.map((v,i)=>{const x=80+step*(i+1);wires+='<path d="M'+x+' 42 V195" />';return '<g><rect x="'+(x-37).toFixed(1)+'" y="103" width="74" height="37" rx="5"/>'+
   '<text x="'+x.toFixed(1)+'" y="98" text-anchor="middle">R'+(i+1)+'</text>'+
   '<text x="'+x.toFixed(1)+'" y="126" text-anchor="middle">'+fmt(v)+'Ω</text></g>';}).join('');
 }
 return '<svg class="sb-circuit-draw" viewBox="0 0 '+w+' '+h+'" role="img" aria-label="'+
 (mode==='series'?'电阻串联':'电阻并联')+'的理想直流电路示意图">'+
 '<rect width="'+w+'" height="'+h+'" rx="13" fill="#0c1a2c"/>'+
 '<g stroke="#d9b878" stroke-width="3" fill="none" stroke-linecap="round">'+wires+'</g>'+
 '<g><circle cx="80" cy="165" r="17" fill="#1f3851" stroke="#eccb89" stroke-width="3"/>'+
 '<text x="80" y="169" text-anchor="middle" fill="#ffdfad" font-size="13">＋</text>'+
 '<text x="80" y="225" text-anchor="middle" fill="#e5d1a8" font-size="12">'+fmt(result.voltage)+'V</text></g>'+
 '<g stroke="#e1c58f" fill="#29405a" stroke-width="2" font-family="sans-serif" font-size="12" fill-rule="evenodd">'+boxes+'</g>'+
 '<text x="570" y="225" text-anchor="end" fill="#aebfcf" font-size="12">'+
 (mode==='series'?'串联':'并联')+' · 教育示意</text></svg>';
}
function circuitStats(d){
 if(!d)return '';
 return '<div class="sb-stats"><div><small>总等效电阻</small><strong>'+fmt(d.equivalent_ohms)+' Ω</strong></div>'+
 '<div><small>总电流</small><strong>'+fmt(d.total_amperes)+' A</strong></div>'+
 '<div><small>总功率</small><strong>'+fmt(d.total_watts)+' W</strong></div></div>'+
 '<div class="sb-branch">'+d.branches.map((x,i)=>'<div><b>R'+(i+1)+'</b><span>'+fmt(x.ohms)+'Ω</span>'+
 '<small>'+fmt(x.volts)+'V · '+fmt(x.amperes)+'A · '+fmt(x.watts)+'W</small></div>').join('')+'</div>';
}
function circuitControls(config,inEditor=false){
 const base=inEditor?'sb-edit-circuit':'sb-preview-circuit';
 return '<form id="'+base+'" class="sb-controls"><div class="sb-inputs"><label>连接方式<select name="mode">'+
 ['series','parallel'].map(k=>'<option value="'+k+'" '+(config.mode===k?'selected':'')+'>'+(k==='series'?'串联':'并联')+'</option>').join('')+'</select></label>'+
 '<label>电源电压（0.1–24V）<input name="voltage" type="number" min=".1" max="24" step=".1" value="'+config.voltage+'" required></label>'+
 config.resistors.map((v,i)=>'<label>R'+(i+1)+' 电阻（1–1000Ω）<input name="r'+i+'" type="number" step=".1" min="1" max="1000" value="'+v+'" required></label>').join('')+
 '</div><div class="sb-actions">'+(inEditor?
 btn('add-r','＋ 电阻块',''+(config.resistors.length>=4?'disabled':''))+
 btn('remove-r','− 移除一个',''+(config.resistors.length<=2?'disabled':''))+'<span class="sb-muted">修改并保存后才会影响作品。</span>':
 '<button class="sb-primary" type="submit">⚡ 运行模型</button>')+'</div></form>';
}
function circuitPlay(d){
 return '<div class="sb-sub"><span class="sb-kicker">OHM’S LAW · IDEAL DC CIRCUIT</span>'+
 '<h4>⚡ 把电阻组合成一个可玩电路</h4><p>试试从串联切换成并联，再修改电压和电阻。</p>'+
 circuitControls(d.config)+circuitDraw(H.response)+circuitStats(H.response)+
 '<p class="sb-warning">理想稳态电路，仅用于教学；不考虑温升、电路保护、线材或真实电源限制。请勿按照这个图实际接线。</p></div>';
}
function timelineStory(d){
 const events=d.config.events;
 const ix=Math.max(0,Math.min(H.focus,events.length-1));
 const event=events[ix];
 const natureLabel=(x)=>x==='原创虚构'?'✧ 原创虚构':x==='个人记录'?'◈ 个人回忆':'⌁ 史料待核';
 return '<div class="sb-sub"><span class="sb-kicker">THE HISTORY OF EVERYTHING · FACT & FICTION</span>'+
 '<h4>⏳ 跨越亿年的万物时间剧场</h4>'+
 '<p>从真实历史到个人记忆，再到未来架空文明。每一幕都保留清晰的真实性标签。</p>'+
 '<div class="sb-time-events">'+events.map((x,i)=>
 btn('focus','<small>'+esc(era(x.year))+'</small><b>'+esc(x.title)+'</b><em>'+esc(natureLabel(x.nature))+'</em>',
 'data-index="'+i+'" class="'+(i===ix?'active':'')+'"')).join('')+'</div>'+
 '<article class="sb-spotlight"><div class="sb-kicker">CHAPTER '+(ix+1)+' / '+events.length+'</div>'+
 '<small>'+esc(era(event.year))+' · '+esc(natureLabel(event.nature))+'</small>'+
 '<h3>'+esc(event.title)+'</h3><p>'+esc(event.story)+'</p>'+
 (event.source_url?'<a href="'+esc(event.source_url)+'" target="_blank" rel="noopener noreferrer">投稿者提供的参考资料 ↗（未经独立核实）</a>':'')+
 '</article><div class="sb-actions">'+btn('prev','← 上一幕',''+(ix===0?'disabled':''))+
 btn('next','下一幕 →','class="sb-primary" '+(ix===events.length-1?'disabled':''))+'</div>'+
 '<p class="sb-warning">史料待核 ≠ 已认证事实；个人记录不等于公开史料；原创虚构不应该被当成真实历史。</p></div>';
}
function showcase(){
 const d=H.detail;if(!d)return '';
 return '<section class="sb-panel"><div class="sb-head"><div><span class="sb-kicker">INTERACTIVE ARCHIVE · #'+d.id+'</span>'+
 '<h3>'+esc(d.label)+' · '+esc(d.title)+'</h3><p>'+esc(d.description||'一件由真实馆长创作的互动展品。')+'</p>'+
 '<small>作者 '+esc(d.creator)+' · '+(d.public?'✦ 作品公开':'🔐 私人展品')+'</small></div>'+
 (d.is_owner?'<div class="sb-actions">'+btn('edit','✎ 编辑')+
 btn('publish',d.public?'撤回公开':'✦ 公开发布','data-next="'+(d.public?'private':'public')+'"')+
 btn('delete','删除作品')+'</div>':'')+'</div>'+
 (d.kind==='circuit'?circuitPlay(d):timelineStory(d))+'</section>';
}
function timelineEditor(cfg){
 return '<div class="sb-time-editor"><div class="sb-head"><h4>时间节点积木（3–10 幕）</h4>'+
 '<div class="sb-actions">'+btn('add-event','＋ 增加一幕',''+(cfg.events.length>=10?'disabled':''))+
 btn('remove-event','− 删除末幕',''+(cfg.events.length<=3?'disabled':''))+'</div></div>'+
 cfg.events.map((ev,i)=>'<fieldset><legend>时间积木 '+(i+1)+'</legend>'+
 '<div class="sb-inputs"><label>年份（负数代表公元前）<input name="year'+i+'" type="number" min="-999999999" max="3000" value="'+ev.year+'" required></label>'+
 '<label>真实性标记<select name="nature'+i+'">'+['史料待核','个人记录','原创虚构'].map(x=>
 '<option '+(ev.nature===x?'selected':'')+'>'+x+'</option>').join('')+'</select></label>'+
 '<label class="wide">分镜标题<input name="eventTitle'+i+'" minlength="2" maxlength="74" value="'+esc(ev.title)+'" required></label>'+
 '<label class="wide">事件描述<textarea name="story'+i+'" minlength="6" maxlength="350" rows="2" required>'+esc(ev.story)+'</textarea></label>'+
 '<label class="wide">史料参考网址（仅史料待核可选填 HTTPS）<input name="source'+i+'" maxlength="350" value="'+esc(ev.source_url||'')+'" placeholder="https://..."></label></div></fieldset>').join('')+
 '<p class="sb-warning">顺序须从早到晚，不能使用公元 0 年。现实事件的资料由作者提供，不会自动变成本站核实的历史事实。</p></div>';
}
function editor(){
 if(!login())return '<section class="sb-panel"><div class="sb-empty">登录后可以免费创建自己的电路实验或时间故事。</div></section>';
 return '<section class="sb-panel"><div class="sb-head"><div><span class="sb-kicker">CREATE A PLAYABLE OBJECT</span>'+
 '<h3>🧱 '+(H.editing?'编辑我的万物沙盒':'积木创作台')+'</h3>'+
 '<p>使用预置安全积木，不需要写一行代码，也不会上传脚本。</p></div>'+
 btn('toggle-editor',H.editor?'收起':'＋ 建造新作品','class="sb-primary"')+'</div>'+
 (!H.editor?'':'<div class="sb-workbench"><div class="sb-switch">'+H.config.templates.map(t=>
 btn('kind',esc(t.label),'data-kind="'+t.kind+'" class="'+(H.kind===t.kind?'active':'')+'"'+
 (H.editing?' disabled':''))).join('')+'</div>'+
 '<form id="sb-create"><div class="sb-inputs"><label>作品名称<input name="title" required minlength="2" maxlength="80" value="'+esc(H.draft.title)+'" placeholder="例如：我设计的火星探测器电路"></label>'+
 '<label class="wide">给参观者的介绍<textarea name="description" maxlength="460" rows="2">'+esc(H.draft.description)+'</textarea></label></div>'+
 (H.kind==='circuit'?circuitControls(H.draft.config,true):timelineEditor(H.draft.config))+
 '<button class="sb-primary" type="submit">'+(H.editing?'保存修改':'✨ 创建私人互动藏品')+'</button>'+
 '</form><p class="sb-warning">每位馆长最多 12 件作品。默认私人，需要本人明确公开才会出现在作品广场。</p></div>')+'</section>';
}
async function render(){
 await load();
 return '<div class="sb-root">'+hero()+(H.notice?'<p class="sb-message">'+esc(H.notice)+'</p>':'')+
 (H.error?'<p class="sb-error">'+esc(H.error)+'</p>':'')+
 gallery()+showcase()+editor()+
 '<footer class="sb-warning">现实史料未经本站独立验证 · 虚构内容明确标记 · 所有创作记录均为真实用户提交</footer></div>';
}
async function refresh(){
 if(window.S?.view!=='play')return;
 document.querySelector('#main').innerHTML=await window.WonderPlay.render();
 window.WonderPlay.afterMount();
}
function formConfig(form){
 const data=Object.fromEntries(new FormData(form));return {
  mode:data.mode,voltage:Number(data.voltage),
  resistors:[...Array.from(form.querySelectorAll('[name^="r"]')).filter(x=>/^r\d+$/.test(x.name))].map(x=>Number(x.value))
 };
}
function timelineConfig(form){
 const data=Object.fromEntries(new FormData(form));
 return {events:H.draft.config.events.map((_,i)=>({
  year:Number(data['year'+i]),title:data['eventTitle'+i],
  story:data['story'+i],nature:data['nature'+i],source_url:data['source'+i]?.trim()||''
 }))};
}
function captureEditor(){
 const f=document.getElementById('sb-create');if(!f)return;
 H.draft.title=f.elements.title.value;H.draft.description=f.elements.description.value;
 H.draft.config=H.kind==='circuit'?formConfig(f):timelineConfig(f);
}
document.addEventListener('click',async e=>{
 const b=e.target.closest('[data-sbx]');if(!b)return;
 e.preventDefault();e.stopImmediatePropagation();
 const k=b.dataset.sbx,id=Number(b.dataset.id||0);
 try{
  if(k==='scope'){H.scope=b.dataset.scope;H.selected=0;H.response=null;H.focus=0;}
  else if(k==='select'){H.selected=id;H.response=null;H.focus=0;}
  else if(k==='kind'){if(H.editing)return;reset(b.dataset.kind);}
  else if(k==='toggle-editor'){H.editor=!H.editor;if(!H.editor){H.editing=0;reset();}}
  else if(k==='edit'){if(!H.detail?.is_owner)return;
   H.editor=true;H.editing=H.detail.id;H.kind=H.detail.kind;
   H.draft={kind:H.kind,title:H.detail.title,description:H.detail.description,
    config:clone(H.detail.config)};
   H.scope='mine';
  }else if(k==='add-r'||k==='remove-r'){
   captureEditor();
   const resistors=H.draft.config.resistors;
   if(k==='add-r'&&resistors.length<4)resistors.push(100);
   if(k==='remove-r'&&resistors.length>2)resistors.pop();
  }else if(k==='add-event'||k==='remove-event'){
   captureEditor();const es=H.draft.config.events;
   if(k==='add-event'&&es.length<10){
    es.push({year:Math.max(1,(es.at(-1)?.year||0)+1),title:'下一幕',
      story:'在这里写下这一个时代的背景与发现。',nature:'原创虚构',source_url:''});
   }
   if(k==='remove-event'&&es.length>3)es.pop();
  }else if(k==='prev'){H.focus=Math.max(0,H.focus-1);}
  else if(k==='next'){H.focus=Math.min((H.detail?.config.events.length||1)-1,H.focus+1);}
  else if(k==='focus'){H.focus=Number(b.dataset.index);}
  else if(k==='publish'){
   if(b.dataset.next==='public'&&!window.confirm('所有访客都将能看到本作品的配置和内容。确认公开吗？'))return;
   await api('/play/sandbox/'+H.selected+'/visibility',{method:'PATCH',body:{visibility:b.dataset.next}});
   H.notice=b.dataset.next==='public'?'✦ 已主动公开':'已撤回公开';H.response=null;
  }else if(k==='delete'){
   if(!window.confirm('删除作品及它自动创建的私人藏品？此操作不可恢复。'))return;
   await api('/play/sandbox/'+H.selected,{method:'DELETE'});
   H.selected=0;H.response=null;H.notice='已删除此作品';
  }
  await refresh();
 }catch(err){if(typeof toast==='function')toast(err.message||'无法完成操作');}
},true);
document.addEventListener('submit',async e=>{
 const f=e.target;if(!['sb-create','sb-preview-circuit'].includes(f.id))return;
 e.preventDefault();e.stopImmediatePropagation();
 try{
  if(f.id==='sb-preview-circuit'){
   const body=formConfig(f);
   H.response=(await api('/play/sandbox/'+H.selected+'/simulate',{method:'POST',body})).result;
   // Preserve the visitor's parameters by replacing just the graphic and readings.
   const parent=f.parentElement;
   const old=parent.querySelector('.sb-circuit-draw')||parent.querySelector('.sb-empty');
   if(old){const stats=parent.querySelector('.sb-stats'),branches=parent.querySelector('.sb-branch');
    if(stats)stats.remove();if(branches)branches.remove();old.outerHTML=circuitDraw(H.response)+circuitStats(H.response);}
   return;
  }
  captureEditor();
  const body=clone(H.draft);
  const r=await api(H.editing?'/play/sandbox/'+H.editing:'/play/sandbox',
     {method:H.editing?'PUT':'POST',body});
  H.scope='mine';H.selected=r.id;H.notice=H.editing?'已更新沙盒作品':'✦ 已创建私人万物互动展品';
  H.editing=0;H.editor=false;H.response=null;reset();await refresh();
 }catch(err){if(typeof toast==='function')toast(err.message||'内容格式不符合规则');}
},true);
window.WonderSandbox={render};
})();
