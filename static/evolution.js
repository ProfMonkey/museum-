/* Wonder Atlas V18 — owner-directed fictional civilization simulation. */
(() => {
  'use strict';
  const E={scope:'mine',civilizationId:0,timelineId:0,config:null,civilizations:[],
    timelines:[],detail:null,notice:'',error:'',showAll:false};
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
  const mine=()=>Boolean(window.S?.user);
  const t=(v)=>Number(v||0);
  const statNames={population:'人口',food:'粮储',knowledge:'学识',ecology:'生态',stability:'秩序',culture:'文化',energy:'能量'};
  const statIcon={population:'♟',food:'❋',knowledge:'✦',ecology:'☘',stability:'♜',culture:'♫',energy:'⚡'};
  const statColors={food:'#d9b77e',knowledge:'#a5b9ee',ecology:'#7edac0',stability:'#e99c8d',culture:'#c6a9ef',energy:'#efca82'};
  async function load(){
    E.error='';
    try{
      if(!E.config) E.config=await api('/fantasy/evolution/config');
      if(!mine() && E.scope==='mine')E.scope='public';
      E.civilizations=(await api('/fantasy/evolution/civilizations?scope='+E.scope)).items;
      if(!E.civilizations.some(c=>c.id===E.civilizationId))E.civilizationId=E.civilizations[0]?.id||0;
      E.timelines=E.civilizationId?(await api('/fantasy/evolution/timelines?civilization_id='+E.civilizationId)).items:[];
      if(!E.timelines.some(x=>x.id===E.timelineId))E.timelineId=E.timelines[0]?.id||0;
      E.detail=E.timelineId?await api('/fantasy/evolution/timelines/'+E.timelineId):null;
    }catch(err){E.error=err.message||'无法读取文明年历';E.detail=null;}
  }
  const control=(kind,label,attrs='')=>'<button type="button" data-evolution="'+kind+'" '+attrs+'>'+label+'</button>';
  function policies(){return E.config?.policies||[];}
  function metricCards(stats){
    return '<div class="ev-metrics">'+Object.keys(statNames).map(key=>{
      const value=stats[key];return '<div class="ev-metric"><small>'+statIcon[key]+' '+statNames[key]+'</small>'+
        '<b>'+ (key==='population'?Number(value).toLocaleString('zh-CN'):value)+'</b>'+
        (key==='population'?'':'<div class="ev-meter"><i style="width:'+Number(value)+'%;background:'+(statColors[key]||'#d3b87d')+'"></i></div>')+
      '</div>';}).join('')+'</div>';
  }
  function chart(years){
    if(years.length<2)return '<p class="ev-hint">推进一个纪年后，这里将绘出属于你的文明曲线。</p>';
    const keys=['food','knowledge','ecology','stability','culture','energy'];
    const w=760,h=215,left=40,right=16,top=12,bottom=30,xWidth=w-left-right,hh=h-top-bottom;
    const start=years[0].year,end=years[years.length-1].year,dx=Math.max(1,end-start);
    const ticks=[0,25,50,75,100].map(v=>'<line x1="'+left+'" y1="'+(top+hh*(1-v/100))+'" x2="'+(w-right)+'" y2="'+(top+hh*(1-v/100))+'" stroke="#ddc99a" opacity=".12" /><text x="6" y="'+(top+hh*(1-v/100)+4)+'" fill="#a6abbc" font-size="11">'+v+'</text>').join('');
    const lines=keys.map(key=>{
      const points=years.map(x=>[(left+xWidth*(x.year-start)/dx).toFixed(1),(top+hh*(1-x.stats[key]/100)).toFixed(1)].join(',')).join(' ');
      return '<polyline points="'+points+'" fill="none" stroke="'+statColors[key]+'" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" />';
    }).join('');
    return '<div class="ev-chart-wrap"><svg viewBox="0 0 '+w+' '+h+'" role="img" aria-label="文明发展六项指标随年限变化的折线图">'+ticks+lines+
      '<text x="'+left+'" y="'+(h-8)+'" fill="#a6abbc" font-size="11">第 '+start+' 年</text>'+
      '<text x="'+(w-right)+'" text-anchor="end" y="'+(h-8)+'" fill="#a6abbc" font-size="11">第 '+end+' 年</text></svg>'+
      '<div class="ev-legend">'+keys.map(k=>'<span><i style="background:'+statColors[k]+'"></i>'+statNames[k]+'</span>').join('')+'</div></div>';
  }
  function history(years){
    let list=E.showAll?[...years].reverse():[...years].reverse().slice(0,10);
    return '<div class="ev-history">'+list.map(row=>'<article class="ev-year"><span class="ev-date">'+String(row.year).padStart(3,'0')+' 年</span><div><strong>'+esc(row.event?.name||'平稳纪年')+'</strong><small>施政：'+esc(row.policy)+'</small><p>'+esc(row.event?.description||'文明沿着馆长选择的方向缓慢演化，没有发生特殊事件。')+'</p></div><b>✧</b></article>').join('')+'</div>'+
      (years.length>10?control('toggle-all',E.showAll?'收起部分纪年':'查看全部 '+years.length+' 年档案'):'');
  }
  function detailView(){
    const d=E.detail;if(!d)return '<div class="ev-empty">为文明开启第一条纪元，观察它如何演化。</div>';
    const last=d.current||d.years.at(-1),owner=d.is_owner,canStep=owner&&last.year<100;
    return '<section class="ev-panel"><div class="ev-head"><div><span class="ev-kicker">LIVING CIVILIZATION ARCHIVE · '+d.id+'</span>'+
      '<h3>'+esc(d.name)+'</h3><p>'+esc(d.world)+' · '+esc(d.civilization)+' · 创世律：'+esc(d.law)+'</p></div>'+
      '<span class="ev-pill">'+(d.visibility==='public'?'已授权公开':'仅馆长可见')+'</span></div>'+
      '<div class="ev-year-hero"><span>SIMULATED YEAR</span><strong>'+last.year+'</strong><small>/ 100 虚构年</small><p>每推进一年都会保存独立快照。不同选择可形成不同的文明史。</p></div>'+
      metricCards(last.stats)+'<div class="ev-chart-box"><h4>文明脉搏 · 演化曲线</h4>'+chart(d.years)+'</div>'+
      (canStep?'<div class="ev-decisions"><h4>决定下一个纪元的发展方向</h4><div class="ev-policy-grid">'+
        policies().map(p=>control('advance','<strong>'+esc(p.name)+'</strong><small>'+Object.entries(p.effects).map(([k,v])=>esc(statNames[k])+ (v>0?' +':' ')+v).join(' · ')+'</small>', 'data-policy="'+esc(p.name)+'"')).join('')+'</div></div>':
        (owner?'<p class="ev-hint">这一分支已到达100年上限，可以从过去的一个纪年开启新的分支。</p>':''))+
      (owner?'<div class="ev-owner"><button data-evolution="visibility" data-next="'+(d.visibility==='public'?'private':'public')+'">'+(d.visibility==='public'?'撤回公开授权':'公开这条虚构年历')+'</button>'+
        control('delete','删除这条纪元')+'</div>'+
        '<form id="ev-fork-form" class="ev-form"><h4>⤴ 命运分岔</h4><p>选择曾经发生的纪年，复制当年的状态，另开一条独立支线。最多三条。</p>'+
        '<label>从第几年分岔<select name="year">'+d.years.map(y=>'<option value="'+y.year+'" '+(y.year===last.year?'selected':'')+'>第 '+y.year+' 年 · '+esc(y.policy)+'</option>').join('')+'</select></label>'+
        '<label>新支线的名称<input name="name" maxlength="60" minlength="2" required value="'+esc(d.name+' · 第二命数')+'"></label>'+
        '<button type="submit" '+(E.timelines.length>=3?'disabled':'')+'>开辟另一种命运 ↗</button></form>':'')+
      '<div class="ev-chronicle"><h4>📜 永久虚构年历</h4>'+history(d.years)+'</div></section>';
  }
  function indexView(){
    return '<section class="ev-panel"><div class="ev-head"><div><span class="ev-kicker">CIVILIZATION SELECTOR</span><h3>选择文明 · 打开年历</h3></div>'+
      '<div class="ev-segments">'+(mine()?control('scope','我的文明','data-scope="mine" class="'+(E.scope==='mine'?'active':'')+'"'):'')+
        control('scope','公开纪元','data-scope="public" class="'+(E.scope==='public'?'active':'')+'"')+'</div></div>'+
      (!E.civilizations.length?'<div class="ev-empty">'+(E.scope==='mine'?'还没有自己的文明。先进入「万界会盟」为世界创建文明。':'暂时没有公开文明。这里不会伪造其他用户或文明热度。')+'</div>':
      '<label class="ev-picker">探索的文明<select id="ev-civilization">'+E.civilizations.map(c=>'<option value="'+c.id+'" '+(c.id===E.civilizationId?'selected':'')+'>'+esc(c.name)+' · '+esc(c.world_name)+'</option>').join('')+'</select></label>'+
      '<div class="ev-timeline-cards">'+E.timelines.map(line=>control('select','<b>'+esc(line.name)+'</b><span>'+esc(line.world)+' · '+esc(line.visibility==='public'?'公开展出':'私人年历')+'</span><strong>进入纪元 ↗</strong>','data-id="'+line.id+'" class="'+(line.id===E.timelineId?'active':'')+'"')).join('')+'</div>'+
      (!E.timelines.length?'<p class="ev-empty">此文明尚未开始演化。第一位馆长还没写下它的第一年。</p>':'')+
      (E.scope==='mine'?'<form id="ev-create-form" class="ev-form ev-inline"><label>创建全新纪元<input name="name" minlength="2" maxlength="60" required value="'+esc((E.civilizations.find(c=>c.id===E.civilizationId)?.name||'新文明')+' · 第一纪元')+'"></label><button type="submit" '+(E.timelines.length>=3?'disabled':'')+'>✦ 开始模拟</button></form>':''))+
      '<p class="ev-hint">每个文明最多三条年历；隐私默认关闭，必须由世界和文明的所有者主动选择公开。</p></section>';
  }
  async function render(){
    await load();
    return '<div class="ev-root"><section class="ev-hero"><span>WONDER ATLAS · V18 · THE AGE OF CIVILIZATIONS</span><h2>文明不是一段简介。<br><em>让它活过一百年。</em></h2><p>每一年由馆长选择方向：开垦、求知、守护或通商。粮储会枯竭，文化会繁荣，天律会带来代价。所有纪事都是原创虚构。</p><div class="ev-hero-sig" aria-hidden="true">纪</div><small>⏳ 手动推进 · 确定性推演 · 多线历史 · 永久档案</small></section>'+
      (E.notice?'<div class="ev-note">'+esc(E.notice)+'</div>':'')+
      (E.error?'<div class="ev-error" role="alert">'+esc(E.error)+'</div>':'')+
      indexView()+detailView()+'<p class="ev-disclaimer">'+esc(E.config?.notice||'纯虚构演化模拟')+' 不涉及真实人口数据、货币、资产交换或替他人修改世界。</p></div>';
  }
  async function refresh(){
    if(window.S?.view!=='fantasy')return;
    const root=document.querySelector('#main');
    if(root)root.innerHTML=await WonderFantasy.render();
  }
  const alertError=err=>{if(typeof toast==='function')toast(err.message||'操作失败');else E.notice=err.message||'操作失败';};
  document.addEventListener('click',async event=>{
    const btn=event.target.closest('[data-evolution]');
    if(!btn)return;
    event.preventDefault();event.stopImmediatePropagation();
    const id=E.timelineId;
    try{
      switch(btn.dataset.evolution){
        case 'scope':E.scope=btn.dataset.scope;E.civilizationId=0;E.timelineId=0;E.showAll=false;break;
        case 'select':E.timelineId=t(btn.dataset.id);E.showAll=false;break;
        case 'advance':{
          const result=await api('/fantasy/evolution/timelines/'+id+'/advance',
            {method:'POST',body:{policy:btn.dataset.policy}});
          E.notice='第 '+result.year+' 年已归档 · '+(result.event?.name||'文明平稳发展');break;
        }
        case 'visibility':{
          const result=await api('/fantasy/evolution/timelines/'+id+'/visibility',
            {method:'PATCH',body:{visibility:btn.dataset.next}});
          E.notice=result.visibility==='public'?'已主动公开这条年历':'已撤回年历公开授权';break;
        }
        case 'delete':{
          if(!window.confirm('确定删除整条文明年历？所有年份快照将无法恢复。'))return;
          await api('/fantasy/evolution/timelines/'+id,{method:'DELETE'});
          E.timelineId=0;E.notice='纪元已删除';break;
        }
        case 'toggle-all':E.showAll=!E.showAll;break;
      }
      await refresh();
    }catch(err){alertError(err);}
  },true);
  document.addEventListener('change',async event=>{
    if(event.target.id!=='ev-civilization')return;
    E.civilizationId=t(event.target.value);E.timelineId=0;E.showAll=false;
    try{await refresh();}catch(err){alertError(err);}
  },true);
  document.addEventListener('submit',async event=>{
    if(!['ev-create-form','ev-fork-form'].includes(event.target.id))return;
    event.preventDefault();event.stopImmediatePropagation();
    const form=event.target,body=Object.fromEntries(new FormData(form));
    try{
      let result;
      if(form.id==='ev-create-form'){
        result=await api('/fantasy/evolution/timelines',{method:'POST',
          body:{civilization_id:E.civilizationId,name:body.name}});
        E.notice='新的文明纪元已经开启。每条历史都默认私密。';
      }else{
        result=await api('/fantasy/evolution/timelines/'+E.timelineId+'/fork',
          {method:'POST',body:{name:body.name,year:t(body.year)}});
        E.notice='已从第 '+body.year+' 年创建独立命运支线，原始历史未修改。';
      }
      E.timelineId=result.id;E.showAll=false;await refresh();
    }catch(err){alertError(err);}
  },true);
  window.WonderEvolution={render};
})();
