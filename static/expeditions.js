/* Wonder Atlas V15: multi-institution expeditions. Search results are always live official records. */
window.WonderExpeditions = (() => {
  'use strict';
  const X={catalog:null,route:'materials',step:0,records:null,busy:false,error:'',saved:new Set()};
  const E=x=>String(x??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
  const providerNames={met:'大都会艺术博物馆',nhm:'伦敦自然历史博物馆',loc:'美国国会图书馆',nasa:'NASA 航天影像库'};
  const route=()=>X.catalog?.routes?.find(r=>r.id===X.route)||X.catalog?.routes?.[0];
  const step=()=>route()?.steps?.[X.step];
  const track=(action='open')=>window.WonderAnalytics?.track('world_museums',action);
  function card(item){
    const safeImage=item.open_access_image && item.image_url;
    return `<article class="ex-card"><div class="ex-art">${safeImage?`<img loading="lazy" referrerpolicy="no-referrer" src="${E(item.image_url)}" alt="${E(item.title)}">`:'<span>✧</span><small>原始图像需核验许可</small>'}</div>
    <div class="ex-cardtext"><small>${E(item.museum)} · ${E(item.category||'馆藏记录')}</small><h4>${E(item.title)}</h4><p>${E(item.description||item.subtitle||'馆方公开档案')}</p><p class="ex-date">${E(item.date_note||'暂无明确年代')}</p><p class="ex-rights">${E(item.license||'图像权利请查询原馆')}</p>
    <div class="ex-actions"><a href="${E(item.source_url)}" target="_blank" rel="noopener noreferrer">查看原始记录 ↗</a><button type="button" data-ex="save" data-id="${E(item.id)}" ${X.saved.has(item.id)?'disabled':''}>${X.saved.has(item.id)?'✓ 已收藏':'＋ 私人收藏'}</button></div></div></article>`;
  }
  function records(){
    if(X.busy)return '<div class="ex-notice">正在查询馆方 API。网络失败时不会生成虚构作品。</div>';
    if(X.error)return `<div class="ex-notice ex-warning">${E(X.error)}<br><a href="${E(step()?.source_url||'https://www.loc.gov/')}" target="_blank" rel="noopener noreferrer">前往该机构继续探索 ↗</a></div>`;
    if(!X.records)return '<div class="ex-notice">选择一个路线站点，点击「查看真实馆藏」开始查询。</div>';
    if(X.records.unavailable)return `<div class="ex-notice ex-warning">${E(X.records.notice)}<br><a href="${E(step()?.source_url)}" target="_blank" rel="noopener noreferrer">馆方官方入口 ↗</a></div>`;
    const items=X.records.items||[];
    return `<div class="ex-count">馆方搜索共匹配 ${Number(X.records.matched_total)||0} 条 · 当前显示 ${items.length} 条${X.records.cached?' · 缓存查询':''}</div>${items.length?`<div class="ex-records">${items.map(card).join('')}</div>`:'<div class="ex-notice">馆方没有返回可用记录。此站仍保留原始馆藏查询入口，不会自动补入演示展品。</div>'}`;
  }
  function panel(){
    const rt=route(),current=step();
    return `<section id="ex-panel" class="ex-panel" aria-label="跨机构真实馆藏探索路线"><header class="ex-header"><small>EXPEDITIONS · REAL MUSEUM DATA</small><h2>从古代文明，走到今天的科技</h2><p>六条跨领域参观路线，每一站都连接可验证的原始馆藏。它们是主题对照路线，不代表馆藏之间存在已证实的发明传承或历史因果。</p></header>
    <div class="ex-routes">${(X.catalog?.routes||[{id:'materials',title:'从盔甲到航天器',subtitle:'古代材料 → 机械时代 → 航天工程',icon:'⚙'}]).map(r=>`<button type="button" class="ex-route ${r.id===X.route?'active':''}" data-ex="route" data-id="${E(r.id)}"><span>${E(r.icon)}</span><strong>${E(r.title)}</strong><small>${E(r.subtitle)}</small></button>`).join('')}</div>
    ${rt?`<div class="ex-timeline">${rt.steps.map((s,i)=>`<button type="button" data-ex="step" data-index="${i}" class="${X.step===i?'active':''}"><i>0${i+1}</i><strong>${E(s.caption)}</strong><small>${E(providerNames[s.provider]||s.provider)}</small></button>`).join('')}</div>
    <div class="ex-searchrow"><div><small>STATION ${String(X.step+1).padStart(2,'0')} / ${rt.steps.length}</small><h3>${E(current.caption)}</h3><p>${E(providerNames[current.provider])} · 检索关键词「${E(current.query)}」</p></div><button class="primary" type="button" data-ex="load" ${X.busy?'disabled':''}>⌕ 查看真实馆藏 ↗</button></div>
    <div class="ex-results" aria-live="polite">${records()}</div>
    <div class="ex-next"><button type="button" data-ex="prev" ${X.step===0?'disabled':''}>← 上一站</button><span>每一条记录都保留原馆链接与媒体权利说明</span><button type="button" data-ex="next" ${X.step>=rt.steps.length-1?'disabled':''}>下一站 →</button></div>`:'<div class="ex-notice">专题路线正在加载…</div>'}
    <footer class="ex-footer"><div><strong>来源与内容声明</strong><p>已接入：大都会艺术博物馆、伦敦自然历史博物馆、美国国会图书馆、NASA 图片影像库。这里展示的是馆方公开记录索引，不自动转载未经核验的媒体，不把资料编目时间写成化石地质年龄。</p></div><div class="ex-shortcuts"><button type="button" data-ex="cosmos">⏳ 回到世界时间长河</button><button type="button" data-ex="museums">♜ 世界名馆精选</button></div></footer></section>`;
  }
  async function ensure(){if(X.catalog)return;try{X.catalog=await api('/expeditions/catalog');X.error='';}catch(e){X.error=e.message||'探索路线暂时无法加载';}}
  function repaint(){const old=document.querySelector('#ex-panel');if(old){const frag=document.createElement('div');frag.innerHTML=panel();old.replaceWith(frag.firstElementChild);}}
  async function load(){const st=step();if(!st)return;X.busy=true;X.records=null;X.error='';repaint();track('search');
    try{const endpoint=(st.provider==='met'||st.provider==='nhm')?'/world-sources/search':'/expeditions/search';X.records=await api(endpoint+'?'+new URLSearchParams({provider:st.provider,q:st.query,limit:'6'}));}
    catch(e){X.error=e.message||'馆方接口暂时不可用';}finally{X.busy=false;repaint();}}
  document.addEventListener('click',async ev=>{const btn=ev.target.closest('[data-ex]');if(!btn)return;ev.preventDefault();const action=btn.dataset.ex;
    try{
      if(action==='route'){X.route=btn.dataset.id;X.step=0;X.records=null;X.error='';repaint();}
      else if(action==='step'||action==='prev'||action==='next'){const count=route()?.steps?.length||0;const n=action==='step'?Number(btn.dataset.index):X.step+(action==='next'?1:-1);if(n>=0&&n<count){X.step=n;X.records=null;X.error='';repaint();}}
      else if(action==='load'){await load();}
      else if(action==='save'){
        if(!window.S?.user){typeof mustLogin==='function'?mustLogin():toast('请先登录');return;}
        const id=btn.dataset.id;
        btn.disabled=true;
        const endpoint=(step()?.provider==='met'||step()?.provider==='nhm')?'/world-sources/save':'/expeditions/save';
        const payload=endpoint==='/world-sources/save'?{object_id:id}:{record_id:id};
        try{const got=await api(endpoint,{method:'POST',body:payload});X.saved.add(id);track('collect');toast(got.already_saved?'此来源已经在你的博物馆中':'已加入你的私人展品');repaint();}
        catch(e){toast(e.message||'保存失败');btn.disabled=false;}
      }
      else if(action==='cosmos')await navigate('cosmos');
      else if(action==='museums')await navigate('world-museums');
    }catch(e){toast(e.message||'操作暂时不可用');}
  },true);
  const renderPanel=()=>{ensure().then(()=>{if(window.S?.view==='world-museums')repaint();});return panel();};
  return {renderPanel};
})();