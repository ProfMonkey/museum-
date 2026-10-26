/* V11: no extra navigation or duplicate gallery. Access the network from each exhibit. */
(() => {
  'use strict';
  const esc = x => String(x ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','"':'&quot;', "'":'&#39;'}[c]));
  const kinds = [
    ['same_topic','主题相近'],['materials','材料或工艺'],['influence','影响或启发'],
    ['historical','历史脉络'],['contrast','相互对照'],['curiosity','意外关联']
  ];
  let current = null;
  let busy = false;
  let depth = 1;
  function coords(graph) {
    const focusId = graph.focus.id;
    const nodes = graph.nodes;
    const levels = new Map([[focusId, 0]]);
    for (const e of graph.edges) {
      if (e.from === focusId) levels.set(e.to, 1);
      if (e.to === focusId) levels.set(e.from, 1);
    }
    const first = nodes.filter(n => n.id !== focusId && levels.has(n.id));
    const second = nodes.filter(n => n.id !== focusId && !levels.has(n.id));
    const positions = new Map([[focusId, {x:460,y:220,level:0}]]);
    const fillRing = (items, rx, ry, start) => items.forEach((node, idx) => {
      const angle = start + 2 * Math.PI * idx / Math.max(items.length, 1);
      positions.set(node.id, {x:460+Math.cos(angle)*rx,y:220+Math.sin(angle)*ry,level:rx>170?2:1});
    });
    fillRing(first, 170, 122, -Math.PI/2);
    fillRing(second, 370, 186, -Math.PI/2+0.14);
    return positions;
  }
  function network(graph) {
    const positions = coords(graph);
    const edges = graph.edges.map(edge => {
      const from = positions.get(edge.from), to = positions.get(edge.to);
      if (!from || !to) return '';
      const dashed = edge.source === 'suggestion';
      return `<line x1="${from.x.toFixed(1)}" y1="${from.y.toFixed(1)}" x2="${to.x.toFixed(1)}" y2="${to.y.toFixed(1)}" stroke="${dashed?'#698092':'#cfaa69'}" stroke-width="${dashed?1.3:2.5}" ${dashed?'stroke-dasharray="5 6"':''} opacity=".75"/>`;
    }).join('');
    const nodes = graph.nodes.map(n => {
      const p = positions.get(n.id);if (!p) return '';
      const root = n.id === graph.focus.id;
      const short = Array.from(n.title).slice(0,10).join('');
      return `<g class="cx-node ${root?'cx-focus':''}" role="button" tabindex="0" aria-label="探索 ${esc(n.title)}" data-cx="view" data-id="${n.id}" transform="translate(${p.x.toFixed(1)},${p.y.toFixed(1)})">
        <circle r="${root?39:29}" fill="${root?'#5d421e':'#172436'}" stroke="${root?'#ecd091':'#728397'}" stroke-width="${root?2.3:1.3}"/>
        <text class="cx-node-glyph" text-anchor="middle" dy=".34em">${root?'✦':'✧'}</text>
        <text class="cx-node-label" text-anchor="middle" y="${root?58:49}">${esc(short)}${Array.from(n.title).length>10?'…':''}</text>
      </g>`;
    }).join('');
    return `<svg class="cx-map" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 465" role="img" aria-label="展品关联网络，可点击节点切换焦点">
      <defs><radialGradient id="cxBg"><stop stop-color="#1b2b3b"/><stop offset="1" stop-color="#080d18"/></radialGradient></defs>
      <rect width="920" height="465" rx="22" fill="url(#cxBg)"/><g>${edges}</g><g>${nodes}</g>
    </svg>`;
  }
  const crumbs = values => `<div class="cx-crumbs">${values.map((value,i)=>`<span>${esc(value||'时间不详')}</span>${i<values.length-1?'<b>›</b>':''}`).join('')}</div>`;
  function body(graph) {
    const f = graph.focus;
    const notes = graph.path;
    const links = graph.edges.slice(0, 65).map(edge => {
      const other = edge.from===f.id?graph.nodes.find(n=>n.id===edge.to):graph.nodes.find(n=>n.id===edge.from);
      const from = graph.nodes.find(n=>n.id===edge.from), to = graph.nodes.find(n=>n.id===edge.to);
      const name = `${from?.title||edge.from} → ${to?.title||edge.to}`;
      return `<article class="cx-reason"><div><span class="cx-tag ${edge.source==='curator'?'cx-hand':''}">${edge.source==='curator'?'馆长关联':'系统推荐'}</span><strong>${esc(edge.label)}</strong></div><p>${esc(name)}</p><p>${esc(edge.explanation)}</p><div class="cx-reason-actions">${edge.author?`<small>由 ${esc(edge.author)} 提出 · 未核验</small>`:'<small>仅由共同分类或标签计算</small>'}${other?`<button type="button" data-cx="view" data-id="${other.id}">查看 ${esc(other.title)} ↗</button>`:''}${f.is_mine && edge.source==='suggestion' && edge.from===f.id?`<button type="button" data-cx="pick" data-id="${edge.to}">手动补充关联依据 ＋</button>`:''}${edge.editable?`<button type="button" data-cx="remove" data-id="${edge.id}" data-origin="${edge.from}">删除关联</button>`:''}</div></article>`;
    }).join('');
    return `<div class="cx-view"><header class="cx-top"><div><div class="eyebrow">WONDER ATLAS · EXPLAINABLE LINKS</div><h2>${esc(f.title)}</h2><p>不是随意牵线：每条推荐都可以看到它为什么出现。</p></div><div class="cx-actions"><button class="ghost" type="button" data-cx="depth" data-depth="${graph.depth===1?2:1}">${graph.depth===1?'扩展两层':'收起一层'}</button><button class="ghost" type="button" data-cx="detail" data-id="${f.id}">查看原始档案</button><button class="ghost" type="button" data-cx="cosmos" data-id="${f.id}">更深入的证据追溯 ↗</button></div></header>
    <section class="cx-paths"><div><h3>🏛️ 藏品分类路径</h3>${crumbs(notes.collection)}</div><div><h3>⏳ 时间路径</h3>${crumbs(notes.time)}${notes.time_note?`<small>原始年代：${esc(notes.time_note)}</small>`:''}</div><p>${esc(notes.source_status)} · ${esc(notes.notice)}</p></section>
    <section class="cx-visual"><div class="cx-key"><span>● 馆长提出</span><span>╌ 分类推荐</span><small>${graph.nodes.length} 个可见节点 · ${graph.edges.length} 条关联</small></div>${network(graph)}</section>
    <p class="cx-disclaimer">${esc(graph.disclaimer)}</p>
    <section class="cx-links"><h3>关联依据</h3>${links||'<div class="cx-empty">暂无可解释的关联。可以添加自己的关联说明，也可以从其他展品继续探索。</div>'}</section>
    ${f.is_mine?`<section class="cx-add"><h3>＋ 为自己的展品建立关联</h3><form id="cxCreate"><label>目标展品编号<input type="number" name="target_id" min="1" required placeholder="例如 23；仅能关联有权查看的展品"></label><label>关联类型<select name="kind">${kinds.map(([key,label])=>`<option value="${key}">${label}</option>`).join('')}</select></label><label class="cx-full">说明依据（8–280字）<textarea name="explanation" minlength="8" maxlength="280" required placeholder="请解释为什么两个展品有关联；这是一条馆长提交的解释，并非平台背书。"></textarea></label><button class="primary" type="submit">保存关联</button></form></section>`:''}
    </div>`;
  }
  async function show(exhibitId, newDepth=1) {
    if (busy) return;
    busy = true;
    try {
      const result = await api(`/exhibits/${Number(exhibitId)}/connections?depth=${Number(newDepth)===2?2:1}`);
      current = result; depth = result.depth;
      showModal('万物关联 · 分类路径', body(result), true);
      if (window.WonderAnalytics?.track) window.WonderAnalytics.track('atlas_explore','open');
    } catch (error) { toast(error.message||'无法加载关联'); }
    finally { busy = false; }
  }
  document.addEventListener('click', async e => {
    const button = e.target.closest('[data-cx]');
    if (!button) return;
    const action = button.dataset.cx;
    e.preventDefault(); e.stopPropagation();
    try {
      if (action==='open' || action==='view') await show(button.dataset.id, action==='view'?1:depth);
      else if (action==='depth' && current) await show(current.focus.id, button.dataset.depth);
      else if (action==='detail') await openDetail(Number(button.dataset.id));
      else if (action==='cosmos') { close();window.WonderCosmos?.focus(Number(button.dataset.id)); }
      else if (action==='pick') { const field=document.querySelector('#cxCreate [name=target_id]'); if(field){field.value=button.dataset.id;document.querySelector('#cxCreate')?.scrollIntoView({behavior:'smooth',block:'center'});field.focus();} }
      else if (action==='remove' && current) {
        if (!window.confirm('删除你提交的这条关联？')) return;
        await api(`/exhibits/${button.dataset.origin}/connections/${button.dataset.id}`, {method:'DELETE'});
        toast('已删除关联'); await show(current.focus.id,depth);
      }
    } catch(err) { toast(err.message||'操作失败'); }
  }, true);
  document.addEventListener('submit', async e => {
    if (e.target.id!=='cxCreate' || !current) return;
    e.preventDefault(); e.stopImmediatePropagation();
    const form = e.target;
    const data = Object.fromEntries(new FormData(form));
    try {
      await api(`/exhibits/${current.focus.id}/connections`, {method:'POST',body:{target_id:Number(data.target_id),kind:data.kind,explanation:data.explanation}});
      toast('关联已保存；其他人会看到它是馆长提出的解释');
      await show(current.focus.id,depth);
    } catch(err) {toast(err.message||'操作失败');}
  }, true);
  document.addEventListener('keydown',e=>{
    if ((e.key==='Enter'||e.key===' ') && e.target.matches('[data-cx="view"]')){
      e.preventDefault();show(e.target.dataset.id,1);
    }
  });
  window.WonderConnections = {open: show};
})();