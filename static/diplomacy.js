/* Wonder Atlas V17: consensual cross-world fiction, civilization archives and lore collaboration. */
(() => {
  'use strict';
  const D={section:'civilizations',config:null,worlds:null,civilizations:null,encounters:null,
    viewWorld:0,encounterId:0,detail:null,notice:'',error:''};
  const e = s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const q=s=>document.querySelector(s);
  const logged=()=>Boolean(window.S?.user);
  const opt=(arr,v)=>arr.map(x=>`<option value="${e(x)}" ${x===v?'selected':''}>${e(x)}</option>`).join('');
  const yes=(status)=>status==='public'?'已开放':'未公开';
  const pill=(status)=>({pending:'等待回应',accepted:'已会盟',declined:'已婉拒',withdrawn:'已撤回'}[status]||status);
  const info='<span class="dc-fic">◇ 纯虚构世界观 · 不与现实历史或交易混淆</span>';
  const minePublic=()=>D.worlds?.mine?.filter(w=>w.visibility==='public')||[];
  const myWorld=(id)=>D.worlds?.mine?.find(w=>w.id===id);
  const getWorld=(id)=>D.worlds?.public?.find(w=>w.id===id);
  async function getData(){
    D.error='';
    try{
      if(!D.config)D.config=await api('/fantasy/council/config');
      const [worlds,publicMeet,privateMeet]=await Promise.all([
        api('/fantasy/council/worlds'),api('/fantasy/council/encounters'),
        logged()?api('/fantasy/council/encounters?scope=mine'):Promise.resolve({items:[]})
      ]);
      D.worlds=worlds;D.encounters={public:publicMeet.items||[],mine:privateMeet.items||[]};
      const access=[...D.worlds.mine,...D.worlds.public].map(x=>x.id);
      if(!access.includes(D.viewWorld))D.viewWorld=(D.worlds.mine?.[0]||D.worlds.public?.[0])?.id||0;
      D.civilizations=D.viewWorld?await api('/fantasy/council/civilizations/'+D.viewWorld):null;
      D.detail=D.encounterId?await api('/fantasy/council/encounters/'+D.encounterId).catch(()=>null):null;
      if(D.encounterId&&!D.detail)D.encounterId=0;
    }catch(err){D.error=err.message||'联动档案暂时无法读取';}
  }
  function tabs(){return `<div class="dc-tabs">${[
    ['civilizations','♜ 文明典藏'],['diplomacy','✧ 万界会盟'],['chronicles','▤ 共创年历']
  ].map(([name,label])=>`<button type="button" data-diplomacy="tab" data-tab="${name}" class="${D.section===name?'active':''}">${label}</button>`).join('')}</div>`;}
  function top(){const publicWorlds=D.worlds?.public?.length||0,accepted=D.encounters?.public?.length||0,pending=D.encounters?.mine?.filter(x=>x.status==='pending').length||0;
    return `<section class="dc-hero"><div class="dc-kicker">THE COUNCIL OF UNWRITTEN WORLDS · 诸界会盟</div><h2>一界有法，<br><em>万界有故事。</em></h2><p>每位馆长都是一个文明的创造者。两界相遇需要双方同意；冲突不是打败对方，而是让两套世界规则碰撞出一段共同写作的传奇。</p><div class="dc-stats"><div><b>${publicWorlds}</b><small>开放异界</small></div><div><b>${accepted}</b><small>双向同意的会盟</small></div><div><b>${pending}</b><small>与我有关的邀请</small></div></div><span class="dc-constellation" aria-hidden="true">✧</span></section>`;}
  function civs(){const d=D.civilizations;
    if(!D.worlds?.mine.length&&!D.worlds?.public.length)return `<section class="dc-box"><h3>万界尚未诞生</h3><p>先去「我的世界」创立一片异界，再让文明在那片星空中成长。这里不会编造用户世界或互动数据。</p></section>`;
    if(!d)return '<section class="dc-box">正在打开文明档案…</section>';
    const w=d.world;
    const all=[...D.worlds.mine,...D.worlds.public.filter(x=>!D.worlds.mine.some(m=>m.id===x.id))];
    return `<section class="dc-box"><div class="dc-heading"><div class="dc-kicker">CIVILIZATION REGISTER</div><h3>万界文明档案</h3><p>文明拥有名称、首都、信条与传说，不会被当成现实民族或历史文献。</p></div><label class="dc-field">探索世界<select id="dc-world-picker" data-diplomacy-change="world">${all.map(x=>`<option value="${x.id}" ${x.id===D.viewWorld?'selected':''}>${e(x.name)} · ${e(x.law)}</option>`).join('')}</select></label><div class="dc-laws"><span>世界天律</span><strong>${e(w.law)}</strong><small>创建者：${e(w.creator)} · ${yes(w.visibility)}</small></div><div class="dc-civ-grid">${d.civilizations.length?d.civilizations.map((c,i)=>`<article class="dc-civ"><span class="dc-civ-icon">${['✧','❖','⌬','♜','☾','✺'][i%6]}</span><small>${e(c.style)} · ${c.visibility==='public'?'公开':'私人档案'}</small><h4>${e(c.name)}</h4><p><b>首都：</b>${e(c.capital)}</p><p><b>文明信条：</b>${e(c.ethos)}</p>${c.lore?`<blockquote>${e(c.lore)}</blockquote>`:''}${d.is_owner?`<div class="dc-actions"><button data-diplomacy="civ-visibility" data-id="${c.id}" data-next="${c.visibility==='public'?'private':'public'}">${c.visibility==='public'?'转为私密':'申请公开'}</button><button data-diplomacy="civ-delete" data-id="${c.id}">删除</button></div>`:''}</article>`).join(''):'<div class="dc-empty">这片世界尚无文明。馆长可以在此写下第一部文明史。</div>'}</div>${d.is_owner?`<form id="dc-civilization-form" class="dc-form"><h4>✦ 新建一座文明</h4><input type="hidden" name="world_id" value="${w.id}"><label>文明名称<input name="name" minlength="2" maxlength="50" placeholder="如：星穹律法城" required></label><label>文明首都<input name="capital" maxlength="60" placeholder="如：九霄石阶" required></label><label>文明类型<select name="style">${opt(D.config.styles,D.config.styles[0])}</select></label><label>文明信条<input name="ethos" minlength="4" maxlength="250" placeholder="如：所有力量都需偿还代价" required></label><label class="dc-wide">文明小传<textarea name="lore" maxlength="600" rows="3" placeholder="写下地理、习俗、历史与生活方式"></textarea></label><label>展示权限<select name="visibility"><option value="private">仅自己可见（默认）</option><option value="public" ${w.visibility!=='public'?'disabled':''}>公开展出</option></select></label><button class="dc-cta" type="submit">+ 录入文明档案</button></form>`:''}</section>`;}
  function invitation(){const owns=minePublic(),publicWorlds=(D.worlds?.public||[]);
    const initial=owns[0];const target=publicWorlds.find(x=>x.creator!==window.S?.user?.username && x.id!==initial?.id);
    const lawA=initial?.law,lawB=target?.law;
    return `<section class="dc-box"><div class="dc-heading"><div class="dc-kicker">THE GATE BETWEEN TWO WORLDS</div><h3>发起两界相遇</h3><p>邀请必须来自自己的公开世界，且受邀世界属于另一位真实馆长；只有对方明确接受，才会诞生公开的共同虚构纪事。</p></div>${!logged()?'<p class="dc-empty">登录后才能邀请其他馆长，共同创造文明史。</p>':!owns.length?'<p class="dc-empty">先在「我的世界」公开一片异界，才能向其他世界递交会盟书。</p>':!publicWorlds.some(x=>x.creator!==window.S?.user?.username)?'<p class="dc-empty">还没有其他馆长开放异界。你可以先录入文明，让第一位来访者看到你的世界。</p>':`<form id="dc-proposal-form" class="dc-form"><label>派出使团的世界<select name="from_world_id" data-diplomacy-change="source">${owns.map(x=>`<option value="${x.id}">${e(x.name)}</option>`).join('')}</select></label><label>邀请到访的世界<select name="to_world_id" data-diplomacy-change="target">${publicWorlds.filter(x=>x.creator!==window.S.user.username).map(x=>`<option value="${x.id}">${e(x.name)} · ${e(x.law)}</option>`).join('')}</select></label><label>会盟仪式<select name="kind">${opt(D.config.kinds,D.config.kinds[0])}</select></label><div class="dc-wide dc-rule-duel"><span>天道交会 · 未发生的虚构设想</span><div><b>${e(lawA||'未知天律')}</b><em>VS</em><b>${e(lawB||'未知天律')}</b></div><small>两界法则各自独立，不涉及真实物品、资产或游戏货币交易。</small></div><label class="dc-wide">写给对方馆长的邀约<textarea name="proposal" required minlength="8" maxlength="450" rows="3" placeholder="我们愿用本界的记忆律法，与你们的时间规则共同写下一个星门故事。"></textarea></label><button class="dc-cta" type="submit">✉ 发送待同意的会盟书</button></form>`}</section>`;}
  function inviteCard(enc,ownerView){const ownProposal=Boolean(logged()&&window.S.user.username===enc.proposer),ownResponse=Boolean(logged()&&window.S.user.username===enc.responder);
    return `<article class="dc-invite"><div><span class="dc-status dc-status-${e(enc.status)}">${pill(enc.status)}</span><span class="dc-sub">${e(enc.kind)}</span></div><h4>${e(enc.from_name)} <span>✧</span> ${e(enc.to_name)}</h4><p>${e(enc.proposal)}</p><small>${e(enc.proposer)} 向 ${e(enc.responder)} 发出邀请 · 原创虚构</small><div class="dc-actions">${enc.status==='accepted'?`<button data-diplomacy="view-encounter" data-id="${enc.id}">阅读共创纪事 ↗</button>`:''}${ownerView&&enc.status==='pending'&&ownResponse?`<button data-diplomacy="reply" data-id="${enc.id}" data-action="accept">✓ 同意并建立故事</button><button data-diplomacy="reply" data-id="${enc.id}" data-action="decline">拒绝</button>`:''}${ownerView&&enc.status==='pending'&&ownProposal?`<button data-diplomacy="reply" data-id="${enc.id}" data-action="withdraw">撤回</button>`:''}</div></article>`;}
  function meeting(){const mine=D.encounters?.mine||[],publicE=D.encounters?.public||[];
    return `${invitation()}<section class="dc-box"><div class="dc-heading"><h3>我的会盟来往</h3><p>接受、拒绝或撤回都有真实的账户记录；不会替其他馆长自动同意。</p></div>${logged()?(mine.length?`<div class="dc-invites">${mine.map(x=>inviteCard(x,true)).join('')}</div>`:'<div class="dc-empty">暂无邀请往来。</div>'):'<div class="dc-empty">登录后才可查看个人邀请。</div>'}</section><section class="dc-box"><h3>已经缔结的公开会盟</h3>${publicE.length?`<div class="dc-invites">${publicE.map(x=>inviteCard(x,false)).join('')}</div>`:'<div class="dc-empty">第一场经双方同意的万界会盟，尚待诞生。</div>'}</section>`;}
  function chronicleDetail(){const data=D.detail;if(!data)return '';
    const enc=data.encounter;
    return `<section class="dc-box dc-chronicle"><div class="dc-heading"><div class="dc-kicker">JOINTLY APPROVED FICTIONAL HISTORY · ${enc.id}</div><h3>《${e(enc.from_name)}》×《${e(enc.to_name)}》</h3><p>${e(enc.kind)} · ${pill(enc.status)}</p></div><blockquote class="dc-opening">${e(enc.chronicle)}</blockquote><h4>共创纪事与待审章节</h4>${data.chapters.length?data.chapters.map((c,i)=>`<article class="dc-chapter"><div><small>第 ${String(i+1).padStart(2,'0')} 卷 · ${e(c.author)}</small><span class="dc-status">${({pending:'等待对方同意',approved:'已共同确认',rejected:'未被接受'}[c.status]||'')}</span></div><h4>${e(c.title)}</h4><p>${e(c.story)}</p>${c.can_respond?`<div class="dc-actions"><button data-diplomacy="review-chapter" data-id="${c.id}" data-action="approve">同意发布</button><button data-diplomacy="review-chapter" data-id="${c.id}" data-action="reject">拒绝公开</button></div>`:''}</article>`).join(''):'<p class="dc-empty">双方尚未提交通用章节。第一卷等待共同写作。</p>'}${data.can_write?`<form id="dc-chapter-form" class="dc-form"><input type="hidden" name="encounter_id" value="${enc.id}"><h4>✍ 续写共同历史</h4><label>章节名称<input name="title" minlength="2" maxlength="75" required placeholder="如：失落的第九次日落"></label><label class="dc-wide">共同纪事（20～1200 字）<textarea name="story" minlength="20" maxlength="1200" rows="5" required placeholder="这场相遇将改变双方的传说，但不会自动改变任何世界的所有权…"></textarea></label><button class="dc-cta" type="submit">提交给另一位馆长审核</button></form>`:''}</section>`;}
  function chronicles(){const pub=D.encounters?.public||[];
    return `${D.detail?chronicleDetail():''}<section class="dc-box"><h3>公开的万界年历</h3><p class="dc-helper">年历只展示双方明确接受的虚构会盟；草稿章节必须通过另一位馆长审核才能公开。</p>${pub.length?`<div class="dc-chronicle-list">${pub.map(x=>`<button type="button" data-diplomacy="view-encounter" data-id="${x.id}"><span>✧</span><div><small>${e(x.kind)} · 共同编写</small><strong>${e(x.from_name)} ↔ ${e(x.to_name)}</strong><p>${e((x.chronicle||'').slice(0,130))}</p></div><b>↗</b></button>`).join('')}</div>`:'<div class="dc-empty">尚无双方同意公开的异界历史。</div>'}</section>`;}
  async function render(){await getData();return `<div class="dc-root">${top()}${tabs()}${info}${D.notice?`<p class="dc-notice">${e(D.notice)}</p>`:''}${D.error?`<div class="dc-error">${e(D.error)}</div>`:''}${!D.config?'':D.section==='civilizations'?civs():D.section==='diplomacy'?meeting():chronicles()}</div>`;}
  async function redraw(){if(window.S?.view==='fantasy')q('#main').innerHTML=await WonderFantasy.render();}
  async function refreshDetail(){if(D.encounterId)D.detail=await api('/fantasy/council/encounters/'+D.encounterId).catch(()=>null);}
  document.addEventListener('click',async ev=>{const button=ev.target.closest('[data-diplomacy]');if(!button)return;
    ev.preventDefault();ev.stopPropagation();const act=button.dataset.diplomacy,id=Number(button.dataset.id||0);
    try{
      if(act==='tab'){D.section=button.dataset.tab;D.notice='';await redraw();}
      else if(act==='view-encounter'){D.encounterId=id;D.section='chronicles';await redraw();}
      else if(act==='civ-visibility'){await api(`/fantasy/council/civilizations/${id}/visibility`,{method:'PATCH',body:{visibility:button.dataset.next}});D.notice='文明档案的展示权限已更新';await redraw();}
      else if(act==='civ-delete'){if(!confirm('确定删除这个原创文明档案？'))return;await api(`/fantasy/council/civilizations/${id}`,{method:'DELETE'});D.notice='文明档案已删除';await redraw();}
      else if(act==='reply'){const action=button.dataset.action;if(action==='accept'&&!confirm('你确认将此世界与对方公开会盟？双方可以继续撰写共同的虚构历史。'))return;
        await api(`/fantasy/council/encounters/${id}`,{method:'PATCH',body:{action}});D.notice=action==='accept'?'会盟已成立，现在双方可以共写年历':'已记录你的回应';await redraw();}
      else if(act==='review-chapter'){await api(`/fantasy/council/chapters/${id}`,{method:'PATCH',body:{action:button.dataset.action}});D.notice='共创章节审核完成';await redraw();}
    }catch(err){if(typeof toast==='function')toast(err.message||'万界档案暂时无法回应');}
  },true);
  document.addEventListener('submit',async ev=>{const f=ev.target;if(!['dc-civilization-form','dc-proposal-form','dc-chapter-form'].includes(f.id))return;
    ev.preventDefault();ev.stopImmediatePropagation();const body=Object.fromEntries(new FormData(f));
    try{
      if(f.id==='dc-civilization-form'){body.world_id=Number(body.world_id);await api('/fantasy/council/civilizations',{method:'POST',body});D.notice='原创文明已录入星图';}
      else if(f.id==='dc-proposal-form'){body.from_world_id=Number(body.from_world_id);body.to_world_id=Number(body.to_world_id);await api('/fantasy/council/encounters',{method:'POST',body});D.notice='会盟书已递出，等待另一位馆长明确同意';}
      else {const id=Number(body.encounter_id);delete body.encounter_id;await api(`/fantasy/council/encounters/${id}/chapters`,{method:'POST',body});D.notice='章节草稿已提交，待对方确认后公开';}
      await redraw();
    }catch(err){if(typeof toast==='function')toast(err.message||'保存失败');}
  },true);
  document.addEventListener('change',ev=>{
    const change=ev.target.dataset.diplomacyChange;
    if(change==='world'){D.viewWorld=Number(ev.target.value);D.civilizations=null;redraw().catch(()=>{});}
    else if(change==='source'||change==='target'){
      const form=ev.target.closest('#dc-proposal-form');if(!form)return;
      const from=Number(form.elements.from_world_id?.value),to=Number(form.elements.to_world_id?.value);
      const labels=form.querySelectorAll('.dc-rule-duel b');
      if(labels[0])labels[0].textContent=myWorld(from)?.law||'未知天律';
      if(labels[1])labels[1].textContent=getWorld(to)?.law||'未知天律';
    }
  },true);
  window.WonderDiplomacy={render,selectWorld(id){D.viewWorld=Number(id);D.section='civilizations';},setSection(s){D.section=s;}};
})();