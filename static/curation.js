/* V13: embeds institutional catalogue and private curation audit into the existing time/constellation views. */
(() => {
  'use strict';
  const M = {museum:null,quality:null,loadingMuseum:false,loadingQuality:false,showQuality:false,error:'',museumAt:0};
  const esc = x => String(x ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const urls = value => {
    try{const url = new URL(String(value ?? ''), location.origin);return ['https:','http:'].includes(url.protocol)?url.href:'#';}
    catch(_){return '#';}
  };
  async function loadMuseum(){
    // Initial catalogue can be offline seed metadata while official APIs load asynchronously.
    // Poll infrequently until at least one item has a verified open-access image.
    const ttl = M.museum?.eras?.some(g=>g.items?.some(i=>i.open_access)) ? 15*60*1000 : 45*1000;
    if(M.museum && Date.now()-M.museumAt < ttl)return;
    if(M.loadingMuseum)return;
    M.loadingMuseum=true;
    try{M.museum=await api('/curation/museum-eras');M.museumAt=Date.now();M.error='';}
    catch(e){M.error=e.message||'暂时无法读取来源目录';}
    finally{M.loadingMuseum=false;}
  }
  async function loadQuality(){
    if(!window.S?.user){M.quality=null;return;}
    try{M.quality=await api('/curation/me/quality');}
    catch(e){M.quality=null;M.error=e.message||'暂时无法读取体检信息';}
  }
  function count(era){return M.museum?.eras?.find(x=>x.id===era)?.count||0;}
  function renderEra(era){
    if(!M.museum){
      return `<section class="curation-rail"><div class="curation-head"><span class="curation-mark">▣</span><div><small>WORLD MUSEUM ARCHIVE</small><h3>名馆时代档案</h3><p>${esc(M.error||'正在读取真实馆方来源…')}</p></div></div></section>`;
    }
    const group=M.museum.eras.find(x=>x.id===era), items=group?.items||[];
    return `<section class="curation-rail" aria-label="来自世界名馆的时代档案"><div class="curation-head"><span class="curation-mark">▣</span><div><small>INSTITUTIONAL CATALOGUE · 来源已标注</small><h3>这个时代，世界名馆留下了什么？</h3><p>这里是 ${M.museum.total} 件精选机构目录中的 ${items.length} 件，与上面的用户展品<strong>分开计数</strong>。</p></div></div>
      ${items.length?`<div class="curation-works">${items.map(work=>`<article class="curation-work">
        <div class="curation-cover">${work.open_access&&work.image_url?`<img src="${esc(work.image_url)}" alt="${esc(work.title)}" loading="lazy" referrerpolicy="no-referrer" onerror="this.replaceWith(document.createTextNode('▣'))">`:'<span>▣<small>图片尚未核验开放许可</small></span>'}</div>
        <div class="curation-workbody"><div class="curation-kicker">${esc(work.museum)} · ${esc(work.category)}</div><h4>${esc(work.title)}</h4><p>${esc(work.date||'年代未确定')} · ${esc(work.artist||'作者资料待查')}</p><p>${esc(work.medium||'查看馆方原始记录了解材质')}</p><div class="curation-actions"><a href="${esc(urls(work.source_url))}" target="_blank" rel="noopener noreferrer">查看馆方原档 ↗</a><button type="button" data-curation="collect" data-id="${esc(work.id)}">＋ 私藏这件作品</button></div></div>
      </article>`).join('')}</div>`:
       `<p class="curation-empty">这个年代暂无已筛选的名馆作品。17 件精选档案主要集中于古代艺术至二十世纪初；不会虚构缺失的远古与当代馆藏。</p>`}
      <footer class="curation-footer">${esc(M.museum.notice)} <button type="button" data-curation="openMuseums">浏览全部世界名馆 ↗</button></footer></section>`;
  }
  function renderQuality(){
    if(!window.S?.user)return '';
    const q=M.quality;
    if(!q)return `<section class="curation-audit"><h3>✦ 馆藏体检</h3><p>${esc(M.error||'正在读取个人馆藏质量…')}</p></section>`;
    const issues=q.items.filter(x=>x.missing>0);
    return `<section class="curation-audit"><div class="curation-head"><span class="curation-mark">✦</span><div><small>PRIVATE COLLECTION CHECKUP</small><h3>我的馆藏体检</h3><p>只检查你自己上传的展品，提醒缺失的来源、年代和介绍，不判断藏品真伪。</p></div></div>
      <div class="curation-metrics"><div><b>${q.total}</b><span>私人馆藏总数</span></div><div><b>${q.checked}</b><span>本次抽查</span></div><div><b>${q.fully_described}</b><span>元数据较完整</span></div></div>
      <button type="button" class="curation-toggle" data-curation="toggleQuality">${M.showQuality?'收起详细建议 −':'查看改进建议 +'} ${issues.length?`（${issues.length} 件待补充）`:''}</button>
      ${M.showQuality?`<div class="curation-review">${issues.length?issues.slice(0,30).map(x=>`<article class="curation-reviewcard"><div><strong>${esc(x.title)}</strong><span>元数据建议 ${x.issues.length} 项</span></div><ul>${x.issues.slice(0,3).map(issue=>`<li><b>${esc(issue.label)}</b> · ${esc(issue.tip)}</li>`).join('')}</ul><button type="button" data-curation="edit" data-id="${x.id}">完善这件藏品 ↗</button></article>`).join(''):'<p class="curation-empty">本次抽查的馆藏暂无需要提醒的缺失项。</p>'}</div>`:''}
      <p class="curation-footer">${esc(q.notice)}${q.total>q.checked?` 当前最多抽查 ${q.checked} 件，统计并非全库审核。`:''}</p></section>`;
  }
  async function rerender(){if(window.S?.view==='cosmos')document.querySelector('#main').innerHTML=await window.WonderCosmos.render();}
  document.addEventListener('click',async e=>{
    const b=e.target.closest('[data-curation]');if(!b)return;
    e.preventDefault();e.stopPropagation();
    const action=b.dataset.curation;
    try{
      if(action==='toggleQuality'){M.showQuality=!M.showQuality;await rerender();}
      else if(action==='edit'){await openEditor(Number(b.dataset.id));}
      else if(action==='openMuseums'){await navigate('world-museums');}
      else if(action==='collect'){
        if(!window.S?.user){if(typeof mustLogin==='function')mustLogin();return;}
        b.disabled=true;
        const id=b.dataset.id;
        const data=await api('/world-museums/'+encodeURIComponent(id)+'/collect',{method:'POST'});
        toast(data.already_collected?'你已经收藏过这件作品':'已收入你的私人博物馆');
        b.textContent='✓ 已私藏';
        // Private audit is lazily refreshed when the user next opens their map.
        M.quality=null;
      }
    }catch(err){toast(err.message||'操作失败');b.disabled=false;}
  },true);
  window.WonderCurator={loadMuseum,loadQuality,count,renderEra,renderQuality};
})();