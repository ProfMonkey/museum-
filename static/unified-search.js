/* V42 · Unified community exhibit search (not an external search engine).
   All cards are backed by /api/search and obey the server's current PUBLIC_SCOPE. */
window.WonderSearch=(()=>{
 const state={q:'',domain:'全部',category:'全部',series:'全部',time_bucket:'全部',sort:'relevance',page:1};
 function setQuery(q){state.q=String(q||'').slice(0,80);state.domain='全部';state.category='全部';state.series='全部';state.time_bucket='全部';state.sort='relevance';state.page=1}
 function fromForm(form){
  const f=new FormData(form);
  const next=String(f.get('q')||'').slice(0,80);
  if(next!==state.q){state.page=1}
  for(const key of ['domain','category','series','time_bucket','sort'])state[key]=String(f.get(key)|| (key==='sort'?'relevance':'全部'));
  state.q=next;state.page=1;
 }
 function nextPage(page){const p=Number(page);if(Number.isSafeInteger(p)&&p>0)state.page=p}
 function reset(){setQuery(state.q)}
 function select(name,value){if(name==='q'){setQuery(value);return}if(['domain','category','series','time_bucket'].includes(name)){state[name]=value||'全部';state.page=1}}
 function selectOptions(name,facets,label){
  const rows=facets[name]||[];
  const choices=rows.map(x=>x.value).filter(Boolean);
  if(state[name]!=='全部'&&!choices.includes(state[name]))choices.unshift(state[name]);
  return '<label class="us-field"><span>'+label+'</span><select name="'+name+'"><option value="全部">全部'+label+'</option>'+
   choices.map(v=>{const match=rows.find(x=>x.value===v);return '<option value="'+E(v)+'" '+(state[name]===v?'selected':'')+'>'+E(v)+' · '+(match?.count??0)+'</option>'}).join('')+
   '</select></label>';
 }
 function activeChips(){
  return [['domain','领域'],['category','类别'],['series','系列'],['time_bucket','年代']]
   .filter(([k])=>state[k]!=='全部')
   .map(([k,label])=>'<button class="us-active-chip" data-action="searchClearFacet" data-name="'+k+'">✕ '+label+'：'+E(state[k])+'</button>').join('');
 }
 async function render(){
  const params=new URLSearchParams();
  for(const key of ['q','domain','category','series','time_bucket','sort','page'])params.set(key,state[key]);
  const data=await api('/search?'+params.toString());
  const currentStart=data.total?(data.page-1)*data.per_page+1:0;
  const filters=activeChips();
  return '<section class="us-hero"><div class="eyebrow">WONDER ATLAS · SEARCH V42</div>'+
    '<h1>不必知道分类，<br><span>也能找到万物。</span></h1>'+
    '<p>一次搜索，跨领域查找真实的社区藏品。标题、标签、领域、类别、简介、正文及馆长均可匹配；多个空格分隔的词需同时出现。</p></section>'+
    '<form id="unifiedSearchForm" class="us-form" role="search">'+
    '<div class="us-main-input"><input name="q" type="search" value="'+E(state.q)+'" maxlength="80" placeholder="试试：猴子、米线、化石、游戏…" aria-label="搜索所有公开社区藏品">'+
    '<button class="primary" type="submit">⌕ 搜索万物</button></div>'+
    '<div class="us-filters">'+selectOptions('domain',data.facets,'领域')+
    selectOptions('category',data.facets,'类别')+selectOptions('time_bucket',data.facets,'年代')+
    selectOptions('series',data.facets,'系列')+
    '<label class="us-field"><span>排序方式</span><select name="sort">'+
    [['relevance','最相关'],['latest','最新发布'],['popular','最受欢迎']].map(([v,t])=>'<option value="'+v+'" '+(state.sort===v?'selected':'')+'>'+t+'</option>').join('')+'</select></label>'+
    '<button type="submit" class="ghost us-apply">应用筛选</button></div></form>'+
    '<div class="us-quick"><span>试着探索</span>'+
    ['猴子','米线','化石','游戏'].map(v=>'<button data-action="searchPreset" data-value="'+v+'">'+v+'</button>').join('')+
    (filters?'<button data-action="searchReset" class="us-reset">清除全部筛选</button>':'')+'</div>'+
    (filters?'<div class="us-active-filters">'+filters+'</div>':'')+
    '<div class="us-status" role="status"><div><b>'+data.total+'</b> 件符合当前条件的公开社区藏品'+
    (state.q?' · 查询「'+E(data.query)+'」':' · 浏览全部')+
    '</div><small>仅搜索当前服务器的公开社区藏品，不含世界名馆外部数据库 · 分类/年代计数基于关键词匹配结果</small></div>'+
    (data.items.length?'<div class="us-results">'+data.items.map(x=>
      '<div class="us-result">'+card(x)+'<p class="us-match">'+(x.matched_in.length?'匹配位置：'+E(x.matched_in.join('、')):'公开藏品 · '+E(x.domain||'尚未分类'))+'</p></div>'
     ).join('')+'</div>':
     '<div class="us-empty"><h2>目前没有找到符合条件的藏品</h2><p>可以减少关键词、清除筛选或试试其他叫法。这里只展示真实且当前公开的内容，不会虚构搜索结果。</p>'+
     '<button class="ghost" data-action="searchReset">清除筛选</button> <button class="ghost" data-action="navigate" data-view="discover">逛发现广场</button></div>')+
    '<div class="us-pages">'+(data.page>1?'<button class="ghost" data-action="searchPage" data-page="'+(data.page-1)+'">← 上一页</button>':'')+
    (data.total?'<span>第 '+data.page+' 页 · 当前 '+currentStart+'–'+Math.min(data.page*data.per_page,data.total)+' 件</span>':'')+
    (data.has_more?'<button class="ghost" data-action="searchPage" data-page="'+(data.page+1)+'">下一页 →</button>':'')+'</div>'+
    '<section class="us-help"><h2>想继续深入探索？</h2><p>打开任意结果即可进入藏品档案，顺着相似藏品、同年代或馆长关联继续寻找。也可以浏览世界名馆的独立开放馆藏目录。</p>'+
    '<button class="ghost" data-action="navigate" data-view="world-museums">世界名馆 ↗</button>'+
    '<button class="ghost" data-action="navigate" data-view="catalog">全部功能 ↗</button></section>';
 }
 return {render,setQuery,fromForm,nextPage,reset,select};
})();
