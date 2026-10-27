/* V22: Safe no-code creation, hosted inside the existing playable museum view.
   All source text is escaped, and visitors never receive quiz keys via GET. */
(() => {
'use strict';
const G={cfg:null,scope:'public',projects:[],selected:0,detail:null,
  kind:'quiz',draft:null,editing:0,editorOpen:false,answer:null,
  ecology:null,jam:null,note:'',error:'',audio:null,osc:[]};
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"\'":'&#39;'}[c]));
const btn=(mode,text,attr='')=>'<button type="button" data-studio="'+mode+'" '+attr+'>'+text+'</button>';
const user=()=>Boolean(window.S?.user);
const clone=x=>JSON.parse(JSON.stringify(x));
const noteNames=['C4','D4','E4','F4','G4','A4','B4','C5'];
function fresh(kind='quiz'){
 G.kind=kind;
 G.draft={title:'',description:'',config:clone(G.cfg.defaults[kind])};
}
function option(label,value,selected){
 return '<option value="'+value+'" '+(Number(value)===Number(selected)?'selected':'')+'>'+label+'</option>';
}
function notes(values,forEditor){
 const selector=forEditor?'name="note':'data-jam="';
 return '<div class="cs-score">'+values.map((value,i)=>{
   const attr=forEditor?'name="note'+i+'"':'data-jam="'+i+'"';
   return '<label><small>'+String(i+1).padStart(2,'0')+'</small><select '+attr+' aria-label="第 '+(i+1)+' 格音符">'+
     option('休止',-1,value)+noteNames.map((n,j)=>option(n,j,value)).join('')+'</select></label>';
 }).join('')+'</div>';
}
async function load(){
 G.error='';
 try{
  if(!G.cfg)G.cfg=await api('/play/studio/config');
  if(!G.draft)fresh();
  if(G.scope==='mine'&&!user())G.scope='public';
  const r=await api('/play/studio?scope='+G.scope);
  G.projects=r.items||[];
  if(!G.projects.some(x=>x.id===G.selected))G.selected=G.projects[0]?.id||0;
  G.detail=G.selected?await api('/play/studio/'+G.selected):null;
  if(G.detail?.kind==='music'&&!G.jam)G.jam=[...G.detail.config.notes];
  if(G.detail?.kind==='ecology'&&!G.ecology){
   const out=await api('/play/studio/'+G.selected+'/simulate',{method:'POST',body:G.detail.config});
   G.ecology=out.result;
  }
 }catch(err){G.error=err.message||'加载创作工坊失败';}
}
function intro(){
 return '<section class="cs-intro"><div class="cs-eyebrow">CREATOR MODE · WONDER ATLAS V22</div>'+
 '<h2>✦ 每个人，都能成为万物的创造者。</h2>'+
 '<p>不需要写代码。创作一件可以玩的知识问答、生态演化沙盘或 16 格旋律机。作品会存成真正的博物馆藏品，由你决定什么时候公开。</p>'+
 '<div class="cs-benefits"><span>🧩 互动问答</span><span>🌱 生命演化</span><span>🎹 旋律实验</span>'+
 '<span>🔐 默认私人</span><span>🏛 加入个人展馆</span></div></section>';
}
function cards(){
 return '<section class="cs-panel"><div class="cs-row"><div><div class="cs-eyebrow">CURATED BY REAL USERS</div>'+
 '<h3>🌌 交互作品广场</h3><p>全部来自实际注册馆长。公开作品才能被其他参观者游玩。</p></div>'+
 '<div class="cs-switch">'+(user()?btn('scope','我的作品','data-scope="mine" class="'+(G.scope==='mine'?'active':'')+'"'):'')+
 btn('scope','公开作品','data-scope="public" class="'+(G.scope==='public'?'active':'')+'"')+'</div></div>'+
 (G.projects.length?'<div class="cs-project-grid">'+G.projects.map(p=>
 btn('select','<span>'+esc(p.glyph)+' '+esc(p.template)+'</span><b>'+esc(p.title)+'</b>'+
 '<small>'+esc(p.creator)+' · '+(p.public?'公开':'私人 / 未授权')+'</small>',
 'data-id="'+p.id+'" class="cs-project '+(G.selected===p.id?'active':'')+'"')).join('')+'</div>':
 '<div class="cs-empty">目前还没有这一类交互作品。可以亲手造出第一件。</div>')+'</section>';
}
function quizPlay(d){
 const q=d.config;
 return '<div class="cs-quiz"><div class="cs-tag">🧩 QUIZ / 问答挑战</div><h4>'+esc(q.question)+'</h4>'+
 '<div class="cs-answers">'+q.options.map((x,i)=>btn('answer',
 '<span>'+String.fromCharCode(65+i)+'</span>'+esc(x),
 'data-answer="'+i+'" class="'+(G.answer&&G.answer.correct_answer===i?'correct':'')+'"')).join('')+'</div>'+
 (G.answer?'<div class="cs-judgement '+(G.answer.correct?'right':'wrong')+'"><b>'+
 (G.answer.correct?'✓ 回答正确':'✧ 回答不正确')+'</b><p>'+esc(G.answer.explanation)+'</p>'+
 '<small>正确答案：'+esc(q.options[G.answer.correct_answer])+'</small></div>':
 '<p class="cs-hint">答案只在提交后由服务器判定。题目与解析由作者撰写，未经过本站独立事实核验。</p>')+
 '</div>';
}
function ecologyGraph(curve){
 if(!curve||!curve.series?.length)return '<div class="cs-empty">请运行生态模拟。</div>';
 const all=curve.series,max=Math.max(curve.capacity*1.15,...all,1);
 const x=i=>48+i*(620/(all.length-1)), y=v=>235-200*v/max;
 const line=all.map((v,i)=>(i?'L':'M')+x(i).toFixed(1)+','+y(v).toFixed(1)).join(' ');
 const carrying=y(curve.capacity);
 return '<svg class="cs-chart" viewBox="0 0 730 265" role="img" aria-label="模拟的群体数量随时间变化的折线图">'+
 '<rect width="730" height="265" rx="12" fill="#101b2a"/>'+
 '<path d="M48 235 H682 M48 25 V235" stroke="#a1a8b3" stroke-opacity=".45" fill="none"/>'+
 '<path d="M48 '+carrying.toFixed(1)+' H682" stroke="#e7c178" stroke-dasharray="6 5" opacity=".5"/>'+
 '<text x="51" y="20" font-size="12" fill="#ddd2b7">种群数量</text>'+
 '<text x="599" y="256" font-size="11" fill="#9eafbb">模拟步数</text>'+
 '<text x="685" y="'+(carrying-5).toFixed(1)+'" font-size="10" fill="#e7c178" text-anchor="end">环境容纳量</text>'+
 '<path d="'+line+'" fill="none" stroke="#94e0b6" stroke-width="3" stroke-linejoin="round"/>'+
 '<text x="52" y="252" fill="#b9c3cc" font-size="10">0</text>'+
 '<text x="670" y="252" fill="#b9c3cc" font-size="10">'+curve.steps+'</text></svg>'+
 '<div class="cs-result">起始 '+curve.initial+' → 末期约 <b>'+Number(curve.final).toLocaleString('zh-CN')+'</b>'+
 '<small>生态模型仅示意逻辑斯蒂增长与线性损耗，不构成真实生态预测。</small></div>';
}
function ecologyPlay(d){
 const v=d.config;
 return '<section class="cs-eco"><div class="cs-tag">🌱 ECOLOGY / 沙盘推演</div>'+
 '<p>调节物种起始数量、增长率与资源承载能力，看看演化曲线如何变化。所有结果只在浏览器显示，不会改写作者存档。</p>'+
 '<form id="cs-scenario" class="cs-grid"><label>初始种群<input name="population" type="number" min="1" max="1200" value="'+v.population+'" required></label>'+
 '<label>环境容纳量<input name="capacity" type="number" min="40" max="5000" value="'+v.capacity+'" required></label>'+
 '<label>每步增长率<input name="growth" type="number" min="0" max=".6" step=".01" value="'+v.growth+'" required></label>'+
 '<label>每步损耗率<input name="loss" type="number" min="0" max=".35" step=".01" value="'+v.loss+'" required></label>'+
 '<label>模拟步数<input name="steps" type="number" min="10" max="70" value="'+v.steps+'" required></label>'+
 '<button class="cs-primary" type="submit">▶ 重新模拟</button></form>'+
 ecologyGraph(G.ecology)+'</section>';
}
function musicPlay(d){
 const v=d.config;
 return '<div class="cs-music"><div class="cs-tag">🎹 MUSIC / 16 STEP SEQUENCER</div>'+
 '<h4>调节音符，创作一段属于自己的旋律。</h4>'+
 '<p>按「播放」后才会发声。音频在浏览器中生成，不访问服务器音频文件。临时调整不会改变作者原始作品。</p>'+
 '<div class="cs-music-opts"><span>♩ '+v.bpm+' BPM</span>'+btn('music-play','▶ 播放旋律','class="cs-primary"')+
 btn('music-stop','■ 停止')+'</div>'+notes(G.jam||v.notes,false)+
 '<p class="cs-hint">音阶 C 大调 · 单声部 · 每格为十六分音符（休止格不会发声）。</p></div>';
}
function showcase(){
 const d=G.detail;if(!d)return '';
 const owner=!!d.is_owner;
 return '<section class="cs-panel"><div class="cs-row"><div><div class="cs-eyebrow">PLAYABLE EXHIBIT · NO. '+d.id+'</div>'+
 '<h3>'+esc(d.glyph)+' '+esc(d.title)+'</h3><p>'+esc(d.description||'一件原创交互展品。')+'</p>'+
 '<small>馆长：'+esc(d.creator)+' · '+(d.public?'已明确公开':'仅自己可见')+'</small></div>'+
 (owner?'<div class="cs-ops">'+btn('edit','✎ 编辑作品')+
 btn('publish',d.public?'撤回公开':'✦ 主动公开','data-visibility="'+(d.public?'private':'public')+'"')+
 btn('delete','删除创作')+'</div>':'')+'</div>'+
 (d.kind==='quiz'?quizPlay(d):d.kind==='ecology'?ecologyPlay(d):musicPlay(d))+
 '<p class="cs-hint">这是用户自制的交互作品，科学或历史描述不由万物博物馆独立担保。</p>'+
 '</section>';
}
function editControls(){
 const c=G.draft.config;
 if(G.kind==='quiz')return '<div class="cs-fields"><label class="wide">出题内容<textarea name="question" required minlength="8" maxlength="180" rows="3">'+esc(c.question)+'</textarea></label>'+
 c.options.map((x,i)=>'<label>选项 '+String.fromCharCode(65+i)+'<input name="option'+i+'" required maxlength="90" value="'+esc(x)+'"></label>').join('')+
 '<label>正确答案<select name="answer">'+c.options.map((_,i)=>option('选项 '+String.fromCharCode(65+i),i,c.answer)).join('')+'</select></label>'+
 '<label class="wide">解释／思路<textarea name="explanation" required minlength="10" maxlength="500" rows="4">'+esc(c.explanation)+'</textarea></label></div>';
 if(G.kind==='ecology')return '<div class="cs-fields">'+[
 ['population','初始种群',1,1200,1],['capacity','容纳数量',40,5000,1],
 ['growth','增长率',0,.6,.01],['loss','损耗率',0,.35,.01],
 ['steps','推演步数',10,70,1]
 ].map(([k,label,min,max,step])=>'<label>'+label+
 '<input type="number" name="'+k+'" min="'+min+'" max="'+max+'" step="'+step+
 '" required value="'+c[k]+'"></label>').join('')+'</div>';
 return '<div class="cs-fields"><label>音乐速度（50–200 BPM）<input type="number" name="bpm" min="50" max="200" value="'+c.bpm+'" required></label></div>'+
 '<p class="cs-hint">点击每一格的下拉选项，选择休止或 C 大调音符。</p>'+notes(c.notes,true);
}
function editor(){
 if(!user())return '<section class="cs-panel"><div class="cs-empty">登录后可以免费创作交互展品，先由自己预览，再决定是否公开。</div></section>';
 return '<section class="cs-panel"><div class="cs-row"><div><div class="cs-eyebrow">BUILD WITHOUT CODE</div>'+
 '<h3>🛠️ '+(G.editing?'修改互动作品':'创造一件万物互动作品')+'</h3><p>使用经过验证的模板，不运行自定义 JavaScript，不要求编程。</p></div>'+
 btn('editor',G.editorOpen?'收起编辑器':'＋ 开始创作','class="cs-primary"')+'</div>'+
 (!G.editorOpen?'':('<form id="cs-editor"><div class="cs-templates">'+G.cfg.templates.map(t=>btn('kind',esc(t.glyph)+' '+esc(t.title),
 'data-kind="'+t.kind+'" class="'+(G.kind===t.kind?'active':'')+'"'+(G.editing?' disabled':''))).join('')+'</div>'+
 '<div class="cs-fields"><label>作品标题<input name="title" required minlength="2" maxlength="78" value="'+esc(G.draft.title)+'" placeholder="我的第一件互动展品"></label>'+
 '<label class="wide">作品简介<textarea name="description" maxlength="500" rows="2" placeholder="想让参观者学会什么或发现什么？">'+esc(G.draft.description)+'</textarea></label></div>'+
 editControls()+'<div class="cs-ops"><button type="submit" class="cs-primary">'+(G.editing?'✓ 保存修改':'✦ 创建为私人作品')+'</button>'+
 (G.editing?btn('cancel-edit','取消编辑'):'')+'</div><p class="cs-hint">每位馆长最多创作 15 件作品。发布前只保存在本人私人展柜中。</p></form>'))+
 '</section>';
}
async function render(){
 await load();
 return '<section class="cs-root">'+intro()+
 (G.note?'<div class="cs-notice">'+esc(G.note)+'</div>':'')+
 (G.error?'<div class="cs-error">'+esc(G.error)+'</div>':'')+
 cards()+showcase()+editor()+
 '<p class="cs-footer">用户原创内容与经过验证的专业馆藏不同 · 互动实验不是科学实测 · 不上传可执行脚本或音频文件</p></section>';
}
async function redraw(){
 if(window.S?.view!=='play')return;
 stopMusic();
 document.querySelector('#main').innerHTML=await window.WonderPlay.render();
 window.WonderPlay.afterMount();
}
function stopMusic(){
 for(const osc of G.osc){try{osc.stop()}catch(_){}}
 G.osc=[];
 if(G.audio){try{G.audio.close()}catch(_){}G.audio=null;}
}
function playMusic(){
 stopMusic();
 const card=G.detail;if(!card||card.kind!=='music')return;
 const Audio=window.AudioContext||window.webkitAudioContext;
 if(!Audio){if(typeof toast==='function')toast('浏览器不支持 Web Audio');return;}
 const ctx=new Audio();G.audio=ctx;
 const notes=G.jam||card.config.notes;const bpm=card.config.bpm;
 const freq=[261.63,293.66,329.63,349.23,392.00,440.00,493.88,523.25];
 const step=60/bpm/4;
 for(let i=0;i<16;i++){
  const n=Number(notes[i]);if(n<0||n>7)continue;
  const osc=ctx.createOscillator(),gain=ctx.createGain();
  osc.type='triangle';osc.frequency.value=freq[n];
  osc.connect(gain);gain.connect(ctx.destination);
  const t=ctx.currentTime+0.06+step*i;
  gain.gain.setValueAtTime(.0001,t);
  gain.gain.exponentialRampToValueAtTime(.065,t+.012);
  gain.gain.exponentialRampToValueAtTime(.0001,t+step*.89);
  osc.start(t);osc.stop(t+step*.92);G.osc.push(osc);
 }
 // Not autoplay: invoked exclusively from explicit tap or click.
}
document.addEventListener('click',async e=>{
 const b=e.target.closest('[data-studio]');if(!b)return;
 e.preventDefault();e.stopImmediatePropagation();
 const k=b.dataset.studio,id=Number(b.dataset.id||0);
 try{
  if(k==='scope'){G.scope=b.dataset.scope;G.selected=0;G.answer=null;G.ecology=null;G.jam=null;}
  else if(k==='select'){G.selected=id;G.answer=null;G.ecology=null;G.jam=null;}
  else if(k==='editor'){G.editorOpen=!G.editorOpen;if(!G.editorOpen){G.editing=0;fresh();}}
  else if(k==='kind'){if(G.editing)return;fresh(b.dataset.kind);}
  else if(k==='edit'){
   const d=G.detail;if(!d?.is_owner)return;
   G.editorOpen=true;G.editing=d.id;G.kind=d.kind;
   G.draft={title:d.title,description:d.description,config:clone(d.config)};
   G.scope='mine';
  }else if(k==='cancel-edit'){G.editing=0;fresh();G.editorOpen=false;}
  else if(k==='publish'){
   if(b.dataset.visibility==='public'&&!window.confirm('公开后，任何访客都可以游玩本作品。确认公开吗？'))return;
   await api('/play/studio/'+G.selected+'/visibility',{method:'PATCH',body:{visibility:b.dataset.visibility}});
   G.note=b.dataset.visibility==='public'?'✦ 作品已公开，欢迎所有真实参观者体验':'作品已撤回为私人状态';
  }else if(k==='delete'){
   if(!window.confirm('删除此互动作品及由它自动创建的藏品？此操作不可恢复。'))return;
   await api('/play/studio/'+G.selected,{method:'DELETE'});
   G.selected=0;G.answer=null;G.ecology=null;G.jam=null;G.note='作品与附属藏品均已删除';
  }else if(k==='answer'){
   G.answer=await api('/play/studio/'+G.selected+'/answer',{method:'POST',body:{answer:Number(b.dataset.answer)}});
  }else if(k==='music-play'){playMusic();return;}
  else if(k==='music-stop'){stopMusic();return;}
  await redraw();
 }catch(err){if(typeof toast==='function')toast(err.message||'操作未成功');}
},true);
document.addEventListener('submit',async e=>{
 if(!['cs-editor','cs-scenario'].includes(e.target.id))return;
 e.preventDefault();e.stopImmediatePropagation();
 const f=e.target,data=Object.fromEntries(new FormData(f));
 try{
  if(f.id==='cs-scenario'){
   const body={population:Number(data.population),capacity:Number(data.capacity),
       growth:Number(data.growth),loss:Number(data.loss),steps:Number(data.steps)};
   G.ecology=(await api('/play/studio/'+G.selected+'/simulate',{method:'POST',body})).result;
   // Keep the visitor's local what-if inputs instead of resetting to author defaults.
   const graph=ecologyGraph(G.ecology);
   const prev=document.querySelector('#cs-scenario')?.parentNode;
   if(prev){const old=prev.querySelector('.cs-chart')||prev.querySelector('.cs-empty');
    if(old){let div=old.nextElementSibling;if(div?.classList.contains('cs-result'))div.remove();old.outerHTML=graph;}}
   return;
  }
  const draft={kind:G.kind,title:(data.title||'').trim(),description:(data.description||'').trim(),config:{}};
  if(G.kind==='quiz')draft.config={question:data.question,options:[0,1,2,3].map(i=>data['option'+i]),
      answer:Number(data.answer),explanation:data.explanation};
  else if(G.kind==='ecology')draft.config={population:Number(data.population),capacity:Number(data.capacity),
       growth:Number(data.growth),loss:Number(data.loss),steps:Number(data.steps)};
  else draft.config={bpm:Number(data.bpm),notes:[...Array(16)].map((_,i)=>Number(data['note'+i]))};
  const result=await api(G.editing?'/play/studio/'+G.editing:'/play/studio',
         {method:G.editing?'PUT':'POST',body:draft});
  G.note=G.editing?'互动作品已保存修改':'✨ 互动作品已保存在私人展柜中，只有你能查看';
  G.scope='mine';G.selected=result.id;G.editing=0;G.editorOpen=false;G.answer=null;
  G.ecology=null;G.jam=null;fresh();
  await redraw();
 }catch(err){if(typeof toast==='function')toast(err.message||'保存失败');}
},true);
document.addEventListener('change',e=>{
 const el=e.target.closest('[data-jam]');
 if(!el)return;
 const i=Number(el.dataset.jam);
 if(!G.jam)G.jam=[...G.detail.config.notes];
 if(i>=0&&i<16)G.jam[i]=Number(el.value);
},true);
window.WonderStudio={render,stop:stopMusic};
})();
