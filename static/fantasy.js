/* Wonder Atlas · The Unwritten Realms. Fantasy fiction is never museum fact. */
(() => {
  'use strict';
  const F = {tab:'forge',config:null,mine:[],public:[],worldId:0,detailId:0,detail:null,
    preview:null,nonce:0,createOpen:false,notice:'',fate:null,selection:{theme:'星河仙庭',law:'灵气必须守恒',ingredient_a:'星尘',ingredient_b:'龙鳞'}};
  const escape = x => String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const opts=(items,selected)=>items.map(x=>`<option value="${escape(x)}" ${x===selected?'selected':''}>${escape(x)}</option>`).join('');
  const list=(objects,key)=>objects.map(x=>x[key]);
  const action=(kind,label,extra='')=>`<button type="button" class="fw-act" data-fantasy="${kind}" ${extra}>${label}</button>`;
  const unlocked=()=>Boolean(window.S?.user);
  const track=(event='open')=>{try{window.WonderAnalytics?.track('fantasy_realms',event);}catch(_){}};
  const fiction=`<span class="fw-fiction">◇ ORIGINAL FICTION · 所有世界与奇物均为虚构创作</span>`;
  async function refresh(){
    if(!F.config)F.config=await api('/fantasy/config');
    if(F.tab==='public')F.public=(await api('/fantasy/worlds')).items;
    if(unlocked())F.mine=(await api('/fantasy/worlds?scope=mine')).items;
    else F.mine=[];
    if(F.tab==='detail'&&F.detailId)F.detail=await api(`/fantasy/worlds/${F.detailId}`);
  }
  function themeText(theme){return F.config.themes.find(x=>x.name===theme)?.region||'';}
  function labelLaw(law){return F.config.laws.find(x=>x.name===law)?.description||'';}
  function opening(){return `<section class="fw-hero"><div class="fw-copy"><div class="fw-english">THE MUSEUM OF UNWRITTEN WORLDS · 异界博物档案</div><h1>现实收藏万物，<br><em>幻想创造万物。</em></h1><p>从一片星尘、一页古画或一颗机械心脏开始，制定一条世界法则，铸造有能力、代价与禁忌的奇物。每个世界都由馆长亲手建造。</p><div class="fw-hero-actions">${action('tab','✧ 万物炼成', 'data-tab="forge"')}${action('tab','♜ 参观异界', 'data-tab="public"')}${action('tab','☯ 万界会盟', 'data-tab="council"')}${action('tab','⏳ 文明演化', 'data-tab="evolution"')}</div></div><div class="fw-orb" aria-hidden="true"><div class="fw-orb-a"></div><div class="fw-orb-b"></div><div class="fw-orb-center">玄</div><span class="fw-planet fw-planet-a"></span><span class="fw-planet fw-planet-b"></span></div></section>`;}
  function toolbar(){return `<div class="fw-tabs" role="tablist" aria-label="异界博物馆功能">${[['forge','✦ 万物炼成台'],['public','♜ 异界藏馆'],['mine','⌘ 我的世界'],['council','☯ 万界会盟'],['evolution','⏳ 文明演化']].map(([k,v])=>`<button data-fantasy="tab" data-tab="${k}" role="tab" aria-selected="${F.tab===k}" class="${F.tab===k?'active':''}">${v}</button>`).join('')}${F.tab==='detail'?'<button class="active" role="tab">▧ 世界档案</button>':''}</div>`;}
  function previewCard(p){if(!p)return `<div class="fw-empty-creation"><span>✧</span><h3>两种材料，一件从未存在过的奇物</h3><p>任选两件材料，再用世界规则进行推演。无需账号即可预览。</p><small>生成过程完全在服务器本地完成，无需外部 AI、无需消耗 Token。</small></div>`;
    return `<article class="fw-treasure" style="--sigil-color:${escape(p.color||'#e9c47f')}"><div class="fw-treasure-top"><span>NO. ${escape(p.sigil)}</span><span>虚构藏品 / ${escape(p.rarity)}</span></div><div class="fw-seal">✧</div><h3>${escape(p.title)}</h3><div class="fw-material-line">${p.ingredients.map(escape).join('　✦　')}</div><div class="fw-treasure-spec"><div><small>神通 · POWER</small><p>${escape(p.ability)}</p></div><div><small>代价 · PRICE</small><p>${escape(p.price)}</p></div><div><small>禁忌 · TABOO</small><p>${escape(p.taboo)}</p></div></div><blockquote>${escape(p.lore)}</blockquote><div class="fw-treasure-note">${escape(p.notice)}</div></article>`;
  }
  function worldSelect(){if(!unlocked())return `<p class="fw-helper">登录并创建世界后，可以把炼成的奇物收入自己的博物馆。</p>`;
    return `<div class="fw-commit"><label>收入我的世界<select id="fw-target">${F.mine.length?F.mine.map(w=>`<option value="${w.id}" ${Number(F.worldId)===w.id?'selected':''}>${escape(w.name)} · ${escape(w.visibility==='public'?'公开世界':'私人世界')}</option>`).join(''):'<option value="">请先创建世界</option>'}</select></label><label>奇物可见性<select id="fw-visibility"><option value="private">私人典藏（默认）</option><option value="public">公开展出（要求世界已公开）</option></select></label><label>真实展品灵感编号（可选）<input id="fw-inspiration" type="number" min="1" placeholder="请输入你有权查看的展品编号"></label><button type="button" class="fw-main" data-fantasy="save" ${!F.mine.length||!F.preview?'disabled':''}>收入奇物展柜 ↗</button><p class="fw-helper">真实展品仅作为创作灵感，不会被误写成虚构奇物的史实来源。公开作品将明确标记“虚构”。</p></div>`;}
  function renderForge(){let theme=F.mine.find(w=>w.id===Number(F.worldId));const v=F.selection;return `<div class="fw-grid"><section class="fw-panel fw-forge"><div class="fw-section-kicker">01 / 造物之始</div><h2>万物炼成台</h2><p class="fw-subtitle">以两种材料相合，受一条天道约束，生成世界观自洽的虚构器物。</p><form id="fw-preview-form"><label>世界气质<select name="theme">${opts(list(F.config.themes,'name'),theme?.theme||v.theme)}</select></label><label>天地法则<select name="law">${opts(list(F.config.laws,'name'),theme?.law||v.law)}</select></label><div class="fw-pair"><label>初始材料<select name="ingredient_a">${opts(F.config.materials,v.ingredient_a)}</select></label><b>✧</b><label>共鸣材料<select name="ingredient_b">${opts(F.config.materials,v.ingredient_b)}</select></label></div><input type="hidden" name="nonce" value="${F.nonce}"><p class="fw-helper">${escape(labelLaw(theme?.law||v.law))}</p><div class="fw-row"><button class="fw-main" type="submit">✧ 推演命运</button>${action('recast','⟳ 另一种命数')}</div></form><div class="fw-world-anchor"><h3>世界先于造物</h3><p>${theme?`正在使用「${escape(theme.name)}」的规则；保存时以世界自己的法则为准。`:'先体验炼成。想保存时，可以在下方创建自己的世界。'}</p>${action('tab','＋ 建造我的世界','data-tab="mine"')}</div></section><div class="fw-forge-right">${previewCard(F.preview)}${worldSelect()}</div></div>`;}
  function listWorlds(items, own=false){if(!items.length)return `<div class="fw-no-world"><span>◌</span><h3>${own?'你的世界尚未诞生':'还没有公开的异界'}</h3><p>${own?'为宇宙写下第一条法则，建造自己的玄幻博物馆。':'这里不会预先伪造馆长或虚构热度。成为第一个开放异界的馆长吧。'}</p></div>`;
    return `<div class="fw-world-grid">${items.map((w,i)=>`<button class="fw-world-card" type="button" data-fantasy="view" data-id="${w.id}" style="--fw-hue:${(i*53+25)%300}deg"><small>${escape(w.theme)} · ${escape(w.visibility==='public'?'公开':'私密')}</small><span class="fw-glyph">${['✵','❖','⌬','✺','◈','✧'][i%6]}</span><h3>${escape(w.name)}</h3><p>${escape(w.intro||themeText(w.theme))}</p><footer><span>法则：${escape(w.law)}</span><b>${w.relic_count||0} 件奇物 →</b></footer></button>`).join('')}</div>`;}
  function createWorld(){if(!unlocked())return `<div class="fw-gate"><h3>建造属于自己的异界</h3><p>游客也可以预览奇物。登录后才能将世界和奇物永久保存。</p><button type="button" class="fw-main" data-fantasy="login">登录 / 注册</button></div>`;
    return `<section class="fw-panel fw-create"><button class="fw-create-head" type="button" data-fantasy="toggle-create"><span><small>WORLD BUILDER</small><strong>＋ 建造一个全新的世界</strong></span><b>${F.createOpen?'收起 −':'展开 ＋'}</b></button>${F.createOpen?`<form id="fw-world-form"><label>世界名称<input name="name" minlength="2" maxlength="50" required placeholder="例如：九霄造物院"></label><label>世界气质<select name="theme">${opts(list(F.config.themes,'name'),'星河仙庭')}</select></label><label>创世法则<select name="law">${opts(list(F.config.laws,'name'),'灵气必须守恒')}</select></label><label>世界介绍<textarea rows="3" name="intro" maxlength="500" placeholder="在这个世界里，什么不可违背？"></textarea></label><label>开放程度<select name="visibility"><option value="private">私人世界（默认）</option><option value="public">允许别人参观</option></select></label><button type="submit" class="fw-main">◇ 开辟世界</button></form>`:''}</section>`;}
  function renderMine(){return `${createWorld()}<section class="fw-panel"><div class="fw-section-kicker">YOUR UNWRITTEN UNIVERSES</div><h2>我创造的世界</h2><p class="fw-subtitle">最多创建 30 个世界，每个世界最多收藏 150 件奇物。默认全部私密。</p>${listWorlds(F.mine,true)}</section>`;}
  function renderPublic(){return `<section class="fw-panel"><div class="fw-section-kicker">UNWRITTEN WORLDS · COMMUNITY</div><h2>异界藏馆</h2><p class="fw-subtitle">只展示真实馆长主动公开的原创玄幻世界和奇物；每一件都属于虚构世界观。</p>${listWorlds(F.public,false)}</section>`;}
  function mapSvg(world,relics){const colors=['#d8b673','#b7b1ff','#7ee6d6','#ed9b7e'];
    if(!relics.length)return `<div class="fw-no-world">这片星空尚无奇物。回到炼成台，为它点亮第一颗星。</div>`;
    const total=Math.min(60,relics.length),items=relics.slice(0,total);
    const lines=items.map((r,i)=>{const angle=i*2.39996;const radius=52+(i%8)*24;const x=450+Math.cos(angle)*radius*1.25,y=220+Math.sin(angle)*radius*.8;return `<path d="M 450 220 L ${x.toFixed(1)} ${y.toFixed(1)}" stroke="#d9bd7f" stroke-width=".7" opacity=".22" />`;}).join('');
    const stars=items.map((r,i)=>{const a=i*2.39996,z=52+(i%8)*24,x=450+Math.cos(a)*z*1.25,y=220+Math.sin(a)*z*.8;return `<g tabindex="0" role="button" data-fantasy="fate" data-id="${r.exhibit_id}" aria-label="命运试炼：${escape(r.title)}"><circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${7+i%4}" fill="${colors[i%4]}" stroke="#fff7d2" stroke-width=".8"/><title>${escape(r.title)}</title></g>`;}).join('');
    return `<svg class="fw-sky" viewBox="0 0 900 440" role="img" aria-label="此虚构世界的奇物星图，点击星点进行命运试炼"><defs><radialGradient id="fwG"><stop stop-color="#263044"/><stop offset="1" stop-color="#0a111b"/></radialGradient></defs><rect width="900" height="440" rx="20" fill="url(#fwG)"/><circle cx="450" cy="220" r="165" fill="none" stroke="#bfa35b30" stroke-dasharray="3 9"/>${lines}<circle cx="450" cy="220" r="22" fill="#d9b875" opacity=".32"/><text x="450" y="226" font-size="13" text-anchor="middle" fill="#ffe8ab">道</text>${stars}</svg>`;}
  function renderDetail(){const d=F.detail;if(!d)return '<div class="fw-panel">这个世界暂时不可访问。</div>';
    const w=d.world;const owner=d.is_owner;
    return `<section class="fw-panel fw-detail"><div class="fw-section-kicker">WORLD ARCHIVE / ${w.id}</div><div class="fw-detail-head"><div><h2>${escape(w.name)}</h2><p>${escape(w.intro||themeText(w.theme))}</p><div class="fw-meta"><span>${escape(w.theme)}</span><span>创造者：${escape(w.creator)}</span><span>${escape(w.visibility==='public'?'公开世界':'私密世界')}</span></div></div>${action('tab','← 返回世界列表',`data-tab="${owner?'mine':'public'}"`)}</div><div class="fw-laws"><small>此界第一天律 · THE FIRST LAW</small><strong>${escape(w.law)}</strong><p>${escape(labelLaw(w.law))}</p></div><h3>异界星图 <small>点亮一颗星，探索其可能的命运</small></h3>${mapSvg(w,d.relics)}${owner?`<div class="fw-row fw-owner-actions">${action('use-world','✧ 前往此界炼物')}${action('council-world','☯ 建造文明 · 万界会盟')}${action('world-visibility',w.visibility==='public'?'关闭世界（奇物同步私密）':'开放世界（奇物仍保持私密）')}${action('delete-world','删除整个世界')}</div>`:''}</section><section class="fw-panel"><div class="fw-section-kicker">FANTASY INVENTORY</div><h2>奇物档案 <small>${d.relics.length} 件</small></h2>${d.relics.length?`<div class="fw-relic-grid">${d.relics.map(r=>`<article class="fw-relic"><header><small>虚构 · ${escape(r.rank)}</small><b>✧</b></header><h3>${escape(r.title)}</h3><p>${escape(r.description||r.ability)}</p><dl><div><dt>炼材</dt><dd>${escape(r.ingredient_a)} ✦ ${escape(r.ingredient_b)}</dd></div><div><dt>神通</dt><dd>${escape(r.ability)}</dd></div><div><dt>代价</dt><dd>${escape(r.price)}</dd></div><div><dt>禁忌</dt><dd>${escape(r.taboo)}</dd></div>${r.inspiration_title?`<div><dt>现实灵感</dt><dd>${escape(r.inspiration_title)}（仅作灵感）</dd></div>`:''}</dl><div class="fw-relic-actions">${['守护','献祭','封印'].map(c=>action('fate','☯ '+c,`data-id="${r.exhibit_id}" data-choice="${c}"`)).join('')}${action('item','展品档案',`data-id="${r.exhibit_id}"`)}${owner?`${action('toggle-relic',r.visibility==='public'?'转为私密':'公开奇物',`data-id="${r.exhibit_id}" data-visibility="${r.visibility}"`)}${action('delete-relic','删除',`data-id="${r.exhibit_id}"`)}`:''}</div></article>`).join('')}</div>`:'<div class="fw-no-world">此世界尚未展出奇物。</div>'}</section>${F.fate?`<section class="fw-panel fw-fate-result"><h2>☯ 三途命运 · ${escape(F.fate.choice)}</h2><p>${escape(F.fate.opening)}</p><blockquote>${escape(F.fate.consequence)}</blockquote><em>${escape(F.fate.echo)}</em><small>纯属交互式虚构结局</small></section>`:''}`;
  }
  async function render(){await refresh();const council=F.tab==='council'?await WonderDiplomacy.render():'';const evolution=F.tab==='evolution'?await WonderEvolution.render():'';return `<div class="fw-root">${opening()}${toolbar()}${F.notice?`<div class="fw-notice">${escape(F.notice)}</div>`:''}${F.tab==='forge'?renderForge():F.tab==='public'?renderPublic():F.tab==='mine'?renderMine():F.tab==='council'?council:F.tab==='evolution'?evolution:renderDetail()}${fiction}</div>`;}
  async function rerender(){if(window.S?.view!=='fantasy')return;document.querySelector('#main').innerHTML=await render();}
  async function runPreview(form){const data=Object.fromEntries(new FormData(form));data.nonce=Number(data.nonce||F.nonce);F.nonce=data.nonce;F.selection={theme:data.theme,law:data.law,ingredient_a:data.ingredient_a,ingredient_b:data.ingredient_b};const bound=F.mine.find(w=>w.id===Number(F.worldId));if(bound){data.theme=bound.theme;data.law=bound.law;F.selection.theme=bound.theme;F.selection.law=bound.law;}F.preview=await api('/fantasy/preview',{method:'POST',body:data});track('play');await rerender();}
  document.addEventListener('click',async e=>{
    const button=e.target.closest('[data-fantasy]');if(!button)return;
    e.preventDefault();e.stopPropagation();const mode=button.dataset.fantasy;
    try{
      if(mode==='tab'){F.tab=button.dataset.tab;F.fate=null;F.notice='';track('open');await rerender();}
      else if(mode==='login')openAuth('login');
      else if(mode==='toggle-create'){F.createOpen=!F.createOpen;await rerender();}
      else if(mode==='view'){F.tab='detail';F.detailId=Number(button.dataset.id);F.fate=null;await rerender();}
      else if(mode==='recast'){F.nonce++;const form=document.querySelector('#fw-preview-form');if(form){form.querySelector('[name=nonce]').value=F.nonce;await runPreview(form);}}
      else if(mode==='save'){
        if(!unlocked()){openAuth('login');return;}
        const worldId=Number(document.querySelector('#fw-target')?.value||0);
        if(!worldId||!F.preview){F.notice='请先创建世界并推演奇物';await rerender();return;}
        const body={ingredient_a:F.preview.ingredients[0],ingredient_b:F.preview.ingredients[1],nonce:F.nonce,
          visibility:document.querySelector('#fw-visibility').value,
          inspiration_id:Number(document.querySelector('#fw-inspiration').value)||null};
        const x=await api(`/fantasy/worlds/${worldId}/forge`,{method:'POST',body});
        F.notice=`「${x.title}」已收入世界；纯虚构藏品。`;
        F.worldId=worldId;F.detailId=worldId;F.tab='detail';F.fate=null;track('create');await rerender();
      }
      else if(mode==='use-world'){F.worldId=F.detailId;F.tab='forge';F.preview=null;await rerender();}
      else if(mode==='council-world'){window.WonderDiplomacy?.selectWorld(F.detailId);F.tab='council';F.fate=null;await rerender();}
      else if(mode==='world-visibility'){
        const next=F.detail.world.visibility==='public'?'private':'public';
        if(next==='private'&&!window.confirm('关闭世界会将所有奇物同时变为私密。继续？'))return;
        await api(`/fantasy/worlds/${F.detailId}/visibility`,{method:'PATCH',body:{visibility:next}});await rerender();
      }
      else if(mode==='delete-world'){
        if(!window.confirm('删除整个世界及其全部奇物（包括通用展品记录）？此操作无法撤销。'))return;
        await api(`/fantasy/worlds/${F.detailId}`,{method:'DELETE'});F.detailId=0;F.tab='mine';F.fate=null;await rerender();
      }
      else if(mode==='toggle-relic'){
        const id=Number(button.dataset.id),visibility=button.dataset.visibility==='public'?'private':'public';
        await api(`/fantasy/relics/${id}/visibility`,{method:'PATCH',body:{visibility}});await rerender();
      }
      else if(mode==='delete-relic'){
        if(!window.confirm('永久删除这件虚构奇物？'))return;
        await api(`/fantasy/relics/${button.dataset.id}`,{method:'DELETE'});F.fate=null;await rerender();
      }
      else if(mode==='item'){await openDetail(Number(button.dataset.id));}
      else if(mode==='fate'){
        const choice=button.dataset.choice||'守护';
        F.fate=await api(`/fantasy/relics/${Number(button.dataset.id)}/fate?choice=${encodeURIComponent(choice)}`);
        const previous=F.tab;await rerender();if(previous==='detail')document.querySelector('.fw-fate-result')?.scrollIntoView({behavior:'smooth',block:'nearest'});
      }
    }catch(err){if(typeof toast==='function')toast(err.message||'异界暂时未能回应');}
  },true);
  document.addEventListener('submit',async e=>{
    if(!['fw-preview-form','fw-world-form'].includes(e.target.id))return;
    e.preventDefault();e.stopImmediatePropagation();
    try{
      if(e.target.id==='fw-preview-form')await runPreview(e.target);
      else{
        if(!unlocked()){openAuth('login');return;}
        const body=Object.fromEntries(new FormData(e.target));
        const world=await api('/fantasy/worlds',{method:'POST',body});
        F.worldId=world.id;F.selection.theme=body.theme;F.selection.law=body.law;F.tab='forge';F.preview=null;F.createOpen=false;
        F.notice=`世界「${world.name}」已经诞生。现在开始炼成第一件奇物！`;
        track('create');await rerender();
      }
    }catch(err){if(typeof toast==='function')toast(err.message||'保存失败');}
  },true);
  document.addEventListener('change',e=>{
    if(e.target.id==='fw-target'){F.worldId=Number(e.target.value||0);const w=F.mine.find(w=>w.id===F.worldId);if(w){F.selection.theme=w.theme;F.selection.law=w.law;F.preview=null;}rerender().catch(()=>{});}
  },true);
  document.addEventListener('keydown',e=>{
    const node=e.target.closest('.fw-sky [data-fantasy]');
    if(node&&(e.key==='Enter'||e.key===' ')){e.preventDefault();node.dispatchEvent(new MouseEvent('click',{bubbles:true}));}
  });
  window.WonderFantasy={render,open:async()=>{F.tab='forge';await navigate('fantasy');}};
})();