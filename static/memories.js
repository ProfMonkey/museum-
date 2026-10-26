/* Wonder Atlas V4 · Memories. Real private server history; sound generated locally.
   No third-party music URL, no microphone access, no passive analytics. */
(() => {
'use strict';
const M={items:[],reels:[],selected:new Set(),filter:'all',film:[],index:0,playing:false,
       timer:null,soundTimer:null,audioCtx:null,audioNodes:[],music:'piano',customAudio:null,customURL:null,
       sourceName:'',caption:true,interval:6200};
const e=E;
const musicOptions=[['piano','夜航钢琴'],['starlight','星际漫游'],['journey','金色旅途'],['silent','无声胶片']];
const label=k=>(musicOptions.find(x=>x[0]===k)||musicOptions[0])[1];
const key=()=>`wonder_memory_enabled_user_${S?.user?.id||'guest'}`;
const enabled=()=>!!S?.user&&localStorage.getItem(key())==='1';
const choose=(items)=>items.map(x=>`<option value="${e(x[0])}" ${M.music===x[0]?'selected':''}>${e(x[1])}</option>`).join('');
const art=x=>x.image_url?`<img loading="lazy" src="${e(x.image_url)}" alt="">`:`<span class="mem-symbol">${e(icons[x.category]||'✦')}</span>`;
const day=x=>String(x||'').slice(0,10);
const genre=x=>String(x?.category||'其他');
function stamp(x){return `<div class="mem-tile-picture">${art(x)}</div><div class="mem-tile-info"><span>${e(day(x.last_seen_at||x.created_at))} · ${e(genre(x))}</span><strong>${e(x.title)}</strong><small>${e(x.owner||'未知馆长')}</small></div>`}
function escapeFilm(){const x=document.getElementById('memoryCinema');if(x)x.remove()}
function stopMusic(){clearInterval(M.soundTimer);M.soundTimer=null;for(const n of M.audioNodes){try{n.stop()}catch(_){}}M.audioNodes=[];
  if(M.customAudio){M.customAudio.pause();M.customAudio.currentTime=0;}
  if(M.audioCtx){M.audioCtx.close().catch(()=>{});M.audioCtx=null;}}
function stop(){clearTimeout(M.timer);M.timer=null;M.playing=false;stopMusic();escapeFilm();}
function oscillate(freq,t,duration,type='sine',volume=.025){if(!M.audioCtx)return;
  const ctx=M.audioCtx,n=ctx.createOscillator(),gain=ctx.createGain();n.type=type;n.frequency.setValueAtTime(freq,t);
  gain.gain.setValueAtTime(0,t);gain.gain.linearRampToValueAtTime(volume,t+.05);
  gain.gain.exponentialRampToValueAtTime(.0001,t+duration);
  n.connect(gain);gain.connect(ctx.destination);n.start(t);n.stop(t+duration+.01);}
function playMusic(){stopMusic();if(M.music==='silent')return;if(M.music==='custom'){
    if(M.customAudio){M.customAudio.loop=true;M.customAudio.volume=.38;M.customAudio.play().catch(()=>toast('浏览器未能播放该音乐文件'));}return;}
  try{M.audioCtx=new (window.AudioContext||window.webkitAudioContext)()}catch(_){toast('浏览器不支持合成背景音乐');return}
  const patterns={piano:[261.63,329.63,392,523.25,440,392,329.63,293.66],
    starlight:[220,330,440,659.25,587.33,440,330,261.63],
    journey:[196,246.94,293.66,392,440,493.88,392,293.66]};
  let n=0;const seq=patterns[M.music]||patterns.piano;
  const tick=()=>{if(!M.audioCtx)return;const t=M.audioCtx.currentTime+.03;
    oscillate(seq[n%seq.length],t,.55,M.music==='starlight'?'sine':'triangle',.020);
    if(n%4===0)oscillate(seq[(n+4)%seq.length]/2,t,1.7,'sine',.010);
    n++;};tick();M.soundTimer=setInterval(tick,620);
}
function saveUserSetting(flag){if(!S.user)return;localStorage.setItem(key(),flag?'1':'0');}
function selected(){return M.items.filter(x=>M.selected.has(x.id));}
async function render(){if(!S.user)return guest('你的回忆，等你点亮','登录后可以主动开启浏览足迹，再从看过的展品中剪辑回忆影片。');
  const [hist,reels]=await Promise.all([api('/memories/history'),api('/memories/reels')]);M.items=hist.items;M.reels=reels;
  // Filter out previously selected items no longer visible.
  const possible=new Set(M.items.map(x=>x.id));M.selected=new Set([...M.selected].filter(id=>possible.has(id)));
  const dates=new Set(M.items.map(x=>day(x.last_seen_at)));const cats=new Set(M.items.map(x=>genre(x)));
  const visible=M.items.filter(x=>M.filter==='all'||genre(x)===M.filter);
  return `<section class="memory-hero"><span class="eyebrow">WONDER ATLAS · PRIVATE MEMORIES</span><h1>回忆，是时间留下的展品。</h1><p>把你曾经看过的奇物，重新编排成一场属于自己的电影。<br>选择配乐，进入剧场，让每一段好奇心再次闪光。</p>
  <div class="mem-hero-actions"><button class="primary" data-memory="make" ${M.items.length?'':'disabled'}>▶ 从我的足迹放映</button><button class="ghost" data-memory="playAll" ${M.items.length?'':'disabled'}>✦ 播放全部回忆</button><button class="ghost" data-memory="revisit" ${M.items.length?'':'disabled'}>↻ 偶遇旧日奇物</button></div>
  <div class="mem-orbit">✧<i>✶</i><b>◌</b></div></section>
  <div class="memory-controls"><div><b>🔒 浏览足迹记录</b><p>默认关闭。开启之后，只有你点击进入展品详情时才会记录；别人看不到你的足迹。</p></div>
  <button class="mem-switch ${enabled()?'on':''}" data-memory="toggle" role="switch" aria-checked="${enabled()}">${enabled()?'● 正在记录 · 点击暂停':'○ 已关闭 · 点击开启'}</button></div>
  <div class="mem-stats"><div><strong>${M.items.length}</strong><span>遇见过的展品</span></div><div><strong>${dates.size}</strong><span>留下足迹的日子</span></div><div><strong>${M.reels.length}</strong><span>珍藏的回忆影片</span></div><div><strong>${cats.size}</strong><span>走过的不同领域</span></div></div>
  ${heading('PERSONAL ARCHIVE','我的观看足迹','勾选想重温的展品，编排自己的回忆胶片；同一展品重复看只算一件。')}
  <div class="memory-toolbar"><select id="mem-category"><option value="all">全部领域</option>${[...cats].sort().map(c=>`<option value="${e(c)}" ${M.filter===c?'selected':''}>${e(c)}</option>`).join('')}</select>
  <button class="ghost" data-memory="selectAll">全选当前分类</button><button class="ghost" data-memory="selectNone">取消选择</button><span class="mem-count" id="memCount">已选 ${M.selected.size} 件</span>
  <button class="ghost danger" data-memory="clearHistory" ${M.items.length?'':'disabled'}>清空全部观看足迹</button></div>
  ${visible.length?`<div class="mem-grid">${visible.map(x=>`<div class="mem-tile ${M.selected.has(x.id)?'chosen':''}"><label class="mem-checkbox"><input type="checkbox" data-memory-check="${x.id}" ${M.selected.has(x.id)?'checked':''} aria-label="选择 ${e(x.title)}"> ✓</label>${stamp(x)}<div class="mem-tile-actions"><button class="ghost" data-memory="detail" data-id="${x.id}">查看档案</button><button class="ghost" data-memory="forget" data-id="${x.id}" aria-label="移除这条观看足迹">移除</button></div></div>`).join('')}</div>`:empty(enabled()?'还没有留下足迹':'先开启足迹记录',enabled()?'点击一件展品，回忆就从那里开始。':'记录默认关闭，点击上面的按钮开启后再去探索。','<button class="primary" data-action="navigate" data-view="discover">去探索万物</button>')}
  <section class="memory-editor"><div><div class="eyebrow">MEMORY FILM STUDIO</div><h2>剪一部关于你的电影</h2><p>已选 ${M.selected.size} 件展品。影片保存在账号中；音乐由当前浏览器播放，不会被上传到服务器。</p></div>
  <label>影片名称<input id="mem-title" maxlength="60" value="我的万物回忆" placeholder="给这段回忆起个名字"></label>
  <label>配乐选择<select id="mem-music">${choose(musicOptions)}</select></label><div class="mem-editor-buttons"><button class="primary" data-memory="make" ${M.items.length?'':'disabled'}>▶ 预览影片</button><button class="ghost" data-memory="saveReel" ${M.items.length?'':'disabled'}>✧ 保存我的影片</button></div></section>
  ${heading('YOUR PRIVATE CINEMA','回忆影片库','以后回来，还能继续播放你保存的电影。')}
  ${M.reels.length?`<div class="mem-reels">${M.reels.map(r=>`<article class="mem-reel"><span class="eyebrow">FILM • ${e(day(r.created_at))}</span><h3>${e(r.title)}</h3><p>${r.items.length} 幕画面 · ${e(label(r.music))}</p><div class="mem-reel-actions"><button class="primary" data-memory="reel" data-id="${r.id}" ${r.items.length?'':'disabled'}>▶ 放映</button><button class="ghost danger" data-memory="deleteReel" data-id="${r.id}">删除</button></div></article>`).join('')}</div>`:empty('还没有保存的回忆影片','选择观看足迹，再点击“保存我的影片”。')}
  <p class="mem-disclaimer">隐私说明：足迹属于当前登录账号，记录开关仅对当前浏览器生效。若展品被删除或设为私密，保存的影片会自动跳过无权限画面。选择“本地音乐”不会将音频上传到服务器。</p>`;
}
function prepareEditor(){const chosen=selected();return chosen.length?chosen:M.items.slice(0,40);}
function filmMarkup(x){return `<div class="mem-film-art ${x.image_url?'has-photo':''}">${x.image_url?`<img src="${e(x.image_url)}" alt="${e(x.title)}">`:`<div class="mem-film-glyph">${e(icons[x.category]||'✧')}</div>`}</div><div class="mem-film-shade"></div>
  <div class="mem-film-copy"><span class="mem-scene">WONDER ATLAS · ${String(M.index+1).padStart(2,'0')} / ${String(M.film.length).padStart(2,'0')}</span>
  <h2>${e(x.title)}</h2><p>${e(x.description||x.story||'那天，你在浩瀚的世界里遇见了它。')}</p><small>收藏时光 · ${e(day(x.last_seen_at||x.created_at))}　/　来自 ${e(x.owner||'未知馆长')}</small></div>`}
function updateFilm(){if(!M.film.length){stop();return}const card=document.getElementById('mem-screen');if(!card)return;
  card.classList.remove('mem-enter');void card.offsetWidth;card.innerHTML=filmMarkup(M.film[M.index]);card.classList.add('mem-enter');
  document.getElementById('mem-counter').textContent=`${M.index+1} / ${M.film.length}`;
  document.getElementById('mem-progress').style.width=`${((M.index+1)/M.film.length)*100}%`;
  document.getElementById('mem-current').textContent=M.film[M.index].title;
}
function schedule(){clearTimeout(M.timer);if(!M.playing)return;M.timer=setTimeout(()=>{if(M.index===M.film.length-1){pause();return;}step(1);},M.interval)}
function step(d){if(!M.film.length)return;M.index=(M.index+d+M.film.length)%M.film.length;updateFilm();schedule()}
function pause(){M.playing=false;clearTimeout(M.timer);document.getElementById('mem-play')?.setAttribute('aria-label','播放');const b=document.getElementById('mem-play');if(b)b.textContent='▶ 播放';stopMusic()}
function togglePlay(){M.playing=!M.playing;const b=document.getElementById('mem-play');if(b){b.textContent=M.playing?'Ⅱ 暂停':'▶ 播放';b.setAttribute('aria-label',M.playing?'暂停':'播放')}
  if(M.playing){playMusic();schedule()}else {clearTimeout(M.timer);stopMusic();}}
function openFilm(items,title,music='piano'){if(!items.length)return toast('没有可播放的画面');stop();M.film=items;M.index=0;M.music=music;M.playing=false;
  const root=document.createElement('div');root.id='memoryCinema';root.className='memory-cinema';root.setAttribute('role','dialog');root.setAttribute('aria-modal','true');root.setAttribute('aria-label','回忆剧场');
  root.innerHTML=`<div class="mem-cinema-top"><div class="mem-film-brand">✳ 万物博物馆 <span>MEMORY CINEMA</span></div><div class="mem-film-title">${e(title)}</div><button data-memory="exit" class="mem-exit" aria-label="关闭剧场">× 退出剧场</button></div>
    <div id="mem-screen" class="mem-film-stage" aria-live="polite"></div>
    <div class="mem-cinema-controls"><div class="mem-film-progress"><i id="mem-progress"></i></div><div class="mem-button-row"><button data-memory="prev" aria-label="上一幕">⟵ 上一幕</button><button data-memory="play" id="mem-play">▶ 播放</button><button data-memory="next" aria-label="下一幕">下一幕 ⟶</button><span id="mem-counter"></span></div>
    <div class="mem-audio-row"><span class="mem-playing-title" id="mem-current"></span><label>♫ 背景音乐 <select id="mem-film-music">${choose([...musicOptions,['custom','本地音乐文件']])}</select></label><label class="mem-local-file">＋ 选择本地音频<input id="mem-audio-file" type="file" accept="audio/*"></label><label>换幕间隔 <select id="mem-interval"><option value="4200">4秒</option><option value="6200" selected>6秒</option><option value="9000">9秒</option></select></label><button data-memory="fullscreen">⛶ 全屏</button></div></div>`;
  document.body.appendChild(root);updateFilm(); // User clicks Play: audio is started from a gesture.
}
async function track(x){if(!enabled()||!x?.id)return;try{await api('/memories/seen/'+x.id,{method:'POST'})}catch(_){/* Viewing a public exhibit remains possible if history fails */}}
async function refresh(){if(S.view==='memories')await renderToDom()}
async function renderToDom(){$('#main').innerHTML=await render()}
function userOptions(){return {title:(document.getElementById('mem-title')?.value||'我的万物回忆').trim().slice(0,60),music:document.getElementById('mem-music')?.value||'piano'}}
document.addEventListener('click',async event=>{const b=event.target.closest('[data-memory]');if(!b)return;
  const act=b.dataset.memory,id=Number(b.dataset.id);event.preventDefault();try{
    if(act==='toggle'){saveUserSetting(!enabled());toast(enabled()?'现在开始记录你主动打开的展品':'浏览足迹记录已暂停');await refresh()}
    else if(act==='selectAll'){M.items.filter(x=>M.filter==='all'||genre(x)===M.filter).forEach(x=>M.selected.add(x.id));await refresh()}
    else if(act==='selectNone'){M.selected.clear();await refresh()}
    else if(act==='forget'){await api('/memories/history/'+id,{method:'DELETE'});M.selected.delete(id);await refresh()}
    else if(act==='clearHistory'){if(confirm('永久删除自己账号里的全部观看足迹？已保存的影片不会受影响。')){await api('/memories/history',{method:'DELETE'});M.selected.clear();await refresh()}}
    else if(act==='detail')await openDetail(id);
    else if(act==='make'){const opt=userOptions(),items=prepareEditor();window.WonderAnalytics?.track('memories','play');openFilm(items,opt.title,opt.music)}
    else if(act==='playAll'){window.WonderAnalytics?.track('memories','play');openFilm(M.items.slice(0,40),'走过的万物 · 全部回忆','piano');}
    else if(act==='revisit'){const x=M.items[Math.floor(Math.random()*M.items.length)];if(x){window.WonderAnalytics?.track('memories','revisit');await openDetail(x.id);}}
    else if(act==='saveReel'){const chosen=prepareEditor();if(!chosen.length)return toast('请先收集一些足迹');const opt=userOptions();const r=await api('/memories/reels',{method:'POST',body:{title:opt.title||'我的万物回忆',music:opt.music,exhibit_ids:chosen.map(x=>x.id)}});window.WonderAnalytics?.track('memories','complete');toast('影片已保存到你的私人片库');await refresh()}
    else if(act==='reel'){const r=M.reels.find(x=>x.id===id);if(r)openFilm(r.items,r.title,r.music)}
    else if(act==='deleteReel'){if(confirm('删除这部回忆影片？不会删除观看足迹。')){await api('/memories/reels/'+id,{method:'DELETE'});await refresh()}}
    else if(act==='exit'){stop();if(document.fullscreenElement)document.exitFullscreen().catch(()=>{})}
    else if(act==='prev')step(-1);
    else if(act==='next')step(1);
    else if(act==='play')togglePlay();
    else if(act==='fullscreen'){const el=document.getElementById('memoryCinema');if(!document.fullscreenElement)await el.requestFullscreen?.();else await document.exitFullscreen()}
  }catch(err){toast(err.message||'操作失败')}});
document.addEventListener('change',ev=>{const x=ev.target;
  if(x.matches('[data-memory-check]')){const id=Number(x.dataset.memoryCheck);x.checked?M.selected.add(id):M.selected.delete(id);x.closest('.mem-tile').classList.toggle('chosen',x.checked);const c=$('#memCount');if(c)c.textContent=`已选 ${M.selected.size} 件`;}
  else if(x.id==='mem-category'){M.filter=x.value;refresh()}
  else if(x.id==='mem-music'){M.music=x.value}
  else if(x.id==='mem-film-music'){M.music=x.value;if(M.playing)playMusic()}
  else if(x.id==='mem-interval'){M.interval=Number(x.value)||6200;schedule()}
  else if(x.id==='mem-audio-file'){const file=x.files?.[0];if(!file)return;if(!file.type.startsWith('audio/')||file.size>30*1024*1024)return toast('请选择不超过30MB的音频文件');if(M.customURL)URL.revokeObjectURL(M.customURL);M.customURL=URL.createObjectURL(file);M.customAudio=new Audio(M.customURL);M.music='custom';const selector=$('#mem-film-music');if(selector)selector.value='custom';if(M.playing)playMusic();toast('本地音乐已载入，只在你的浏览器播放')}
});
document.addEventListener('keydown',ev=>{if(!document.getElementById('memoryCinema'))return;
  if(ev.target.matches('input,textarea,select'))return;
  if(ev.key==='Escape'){stop();return}
  if(ev.key==='ArrowRight'){ev.preventDefault();step(1)}
  if(ev.key==='ArrowLeft'){ev.preventDefault();step(-1)}
  if(ev.key===' '){ev.preventDefault();togglePlay()}
});
window.WonderMemories={render,track,stop};
})();