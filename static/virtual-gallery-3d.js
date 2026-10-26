/* Optional real WebGL gallery scene powered by Three.js (MIT). If the CDN is unavailable, the CSS gallery remains usable. */
(() => {
 'use strict';
 let renderer=null, scene=null, camera=null, frameId=0, observer=null, stage=null, frames=[], raycaster=null, pointer=null;
 let theta=0, phi=1.24, radius=8.2, dragging=false, startX=0, startY=0, moved=false, lastX=0, lastY=0, onSelect=null;
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function available(){return !!window.THREE;}
 function makeLabelTexture(item,index){
  const canvas=document.createElement('canvas');canvas.width=512;canvas.height=384;const ctx=canvas.getContext('2d');
  const grad=ctx.createLinearGradient(0,0,512,384);grad.addColorStop(0,'#282316');grad.addColorStop(.5,'#111722');grad.addColorStop(1,'#090c12');ctx.fillStyle=grad;ctx.fillRect(0,0,512,384);
  ctx.strokeStyle='#c9a74d';ctx.lineWidth=8;ctx.strokeRect(18,18,476,348);ctx.strokeStyle='#c9a74d66';ctx.lineWidth=2;ctx.strokeRect(34,34,444,316);
  ctx.fillStyle='#e7ca77';ctx.textAlign='center';ctx.font='22px Georgia,serif';ctx.fillText('WONDER ATLAS · EXHIBIT '+String(index+1).padStart(2,'0'),256,78);
  const title=String(item.title||'无题展品');ctx.fillStyle='#f5edda';ctx.font='bold 30px "Microsoft YaHei",sans-serif';wrapText(ctx,title,256,145,400,42,3);
  ctx.fillStyle='#b6ad96';ctx.font='20px "Microsoft YaHei",sans-serif';ctx.fillText(String(item.category||'万物展品').slice(0,24),256,285);
  ctx.fillStyle='#b99b4d';ctx.font='16px Georgia,serif';ctx.fillText('A WORLD OF CURIOSITY',256,324);
  const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;return texture;
 }
 function wrapText(ctx,text,x,y,maxWidth,lineHeight,maxLines){let line='',lines=[];for(const char of text){const test=line+char;if(ctx.measureText(test).width>maxWidth&&line){lines.push(line);line=char;}else line=test;}if(line)lines.push(line);if(lines.length>maxLines){lines=lines.slice(0,maxLines);lines[maxLines-1]=lines[maxLines-1].slice(0,Math.max(1,lines[maxLines-1].length-2))+'…';}lines.forEach((l,i)=>ctx.fillText(l,x,y+i*lineHeight));}
 function addMesh(geometry,material,x,y,z,group=scene){const mesh=new THREE.Mesh(geometry,material);mesh.position.set(x,y,z);mesh.castShadow=true;mesh.receiveShadow=true;group.add(mesh);return mesh;}
 function updateCamera(){if(!camera)return;phi=Math.max(.55,Math.min(1.48,phi));radius=Math.max(5.2,Math.min(12,radius));camera.position.set(radius*Math.sin(phi)*Math.sin(theta),radius*Math.cos(phi)+1.15,radius*Math.sin(phi)*Math.cos(theta));camera.lookAt(0,1.5,-.4);}
 function dispose(){if(frameId)cancelAnimationFrame(frameId);frameId=0;if(observer){observer.disconnect();observer=null;}if(renderer){renderer.dispose();renderer.domElement?.remove();}if(scene){scene.traverse(o=>{if(o.geometry)o.geometry.dispose();if(o.material){const mats=Array.isArray(o.material)?o.material:[o.material];mats.forEach(m=>{if(m.map)m.map.dispose();m.dispose();});}});}renderer=scene=camera=stage=null;frames=[];}
 function mount(target,items=[],selected=0,selectCallback){
  dispose();if(!window.THREE||!target)return false;stage=target;onSelect=selectCallback;const w=Math.max(320,target.clientWidth||720),h=Math.max(300,target.clientHeight||460);
  try{scene=new THREE.Scene();scene.background=new THREE.Color('#080b12');scene.fog=new THREE.Fog('#080b12',11,23);camera=new THREE.PerspectiveCamera(52,w/h,.1,100);renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,1.8));renderer.setSize(w,h);renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.outputColorSpace=THREE.SRGBColorSpace;target.innerHTML='';target.appendChild(renderer.domElement);renderer.domElement.setAttribute('aria-label','可拖动旋转视角的三维博物馆');
   scene.add(new THREE.HemisphereLight(0xc9d5ee,0x251d10,2.0));const key=new THREE.DirectionalLight(0xffe4a3,3.2);key.position.set(1,7,4);key.castShadow=true;scene.add(key);const warm=new THREE.PointLight(0xd8b45e,18,12);warm.position.set(-3,4,-1);scene.add(warm);const cool=new THREE.PointLight(0x9bbbe8,8,10);cool.position.set(4,3,1);scene.add(cool);
   const floorMat=new THREE.MeshStandardMaterial({color:'#17130d',roughness:.78,metalness:.12});const floor=addMesh(new THREE.PlaneGeometry(16,14),floorMat,0,0,-.2);floor.rotation.x=-Math.PI/2;floor.position.y=0;floor.receiveShadow=true;
   const wallMat=new THREE.MeshStandardMaterial({color:'#20232b',roughness:.86});const sideMat=new THREE.MeshStandardMaterial({color:'#151923',roughness:.9});
   addMesh(new THREE.BoxGeometry(16,5.5,.25),wallMat,0,2.75,-7.0);addMesh(new THREE.BoxGeometry(.25,5.5,14),sideMat,-8,2.75,0);addMesh(new THREE.BoxGeometry(.25,5.5,14),sideMat,8,2.75,0);
   const trimMat=new THREE.MeshStandardMaterial({color:'#8f6e2e',metalness:.72,roughness:.32});for(const y of [.18,5.25])addMesh(new THREE.BoxGeometry(15.8,.07,.28),trimMat,0,y,-6.82);for(const x of [-7.82,7.82])addMesh(new THREE.BoxGeometry(.28,.07,13.8),trimMat,x,.18,0);
   const grid=new THREE.GridHelper(16,16,'#6d5529','#332a19');grid.position.y=.012;scene.add(grid);
   const max=items.length||6, show=Math.min(max,7), start=Math.max(0,Math.min(max-show,selected-Math.floor(show/2))), spacing=Math.min(2.25,12.8/Math.max(1,show));
   for(let i=0;i<show;i++){
    const absoluteIndex=items.length?start+i:i;const item=items[absoluteIndex]||{title:['古画','古董','科学装置','游戏','奇物'][i%5],category:'精选展品'};const x=(i-(show-1)/2)*spacing;const group=new THREE.Group();group.position.set(x,2.55,-6.7);scene.add(group);
    const frameMat=new THREE.MeshStandardMaterial({color:'#8b682d',metalness:.76,roughness:.28});const panelMat=new THREE.MeshStandardMaterial({map:makeLabelTexture(item,i),roughness:.55,metalness:.08});
    addMesh(new THREE.BoxGeometry(1.85,1.55,.13),frameMat,0,0,0,group);const panel=addMesh(new THREE.PlaneGeometry(1.58,1.28),panelMat,0,0,.075,group);panel.userData.index=absoluteIndex;frames.push(panel);
    if(item.image_url&&/^https:\/\//.test(item.image_url)){try{const loader=new THREE.TextureLoader();loader.setCrossOrigin('anonymous');loader.load(item.image_url,tex=>{if(!renderer||!panel.material)return;tex.colorSpace=THREE.SRGBColorSpace;panel.material.map=tex;panel.material.needsUpdate=true;},undefined,()=>{});}catch(_){/* retain the generated title plate when remote images cannot be loaded */}}
    const plaqueMat=new THREE.MeshStandardMaterial({color:'#15120b',metalness:.5,roughness:.5});addMesh(new THREE.BoxGeometry(1.2,.22,.05),plaqueMat,0,-.98,.02,group);
    const plaque=addMesh(new THREE.BoxGeometry(.018,.018,.018),new THREE.MeshStandardMaterial({color:'#e6c878',emissive:'#9b7829'}),0,-.98,.06,group);plaque.userData.index=absoluteIndex;
   }
   const pedestalMat=new THREE.MeshStandardMaterial({color:'#3a2c17',metalness:.58,roughness:.42});addMesh(new THREE.CylinderGeometry(.72,.88,.55,32),pedestalMat,0,.28,-1.2);addMesh(new THREE.CylinderGeometry(.56,.56,.08,32),trimMat,0,.6,-1.2);const orb=addMesh(new THREE.IcosahedronGeometry(.42,1),new THREE.MeshStandardMaterial({color:'#c8a44f',metalness:.72,roughness:.22,wireframe:false}),0,1.1,-1.2);orb.userData.rotate=true;
   raycaster=new THREE.Raycaster();pointer=new THREE.Vector2();updateCamera();
   let downX=0,downY=0;
   const onDown=e=>{dragging=true;moved=false;startX=lastX=e.clientX;startY=lastY=e.clientY;downX=e.clientX;downY=e.clientY;renderer.domElement.setPointerCapture?.(e.pointerId);};
   const onMove=e=>{if(!dragging)return;const dx=e.clientX-lastX,dy=e.clientY-lastY;if(Math.abs(e.clientX-downX)+Math.abs(e.clientY-downY)>4)moved=true;lastX=e.clientX;lastY=e.clientY;theta-=dx*.006;phi+=dy*.004;updateCamera();};
   const onUp=e=>{if(!dragging)return;dragging=false;if(!moved){const r=renderer.domElement.getBoundingClientRect();pointer.x=((e.clientX-r.left)/r.width)*2-1;pointer.y=-((e.clientY-r.top)/r.height)*2+1;raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObjects(frames,false)[0];if(hit&&onSelect)onSelect(hit.object.userData.index);}};
   const onWheel=e=>{e.preventDefault();radius+=e.deltaY*.006;updateCamera();};
   renderer.domElement.addEventListener('pointerdown',onDown);renderer.domElement.addEventListener('pointermove',onMove);renderer.domElement.addEventListener('pointerup',onUp);renderer.domElement.addEventListener('pointercancel',onUp);renderer.domElement.addEventListener('wheel',onWheel,{passive:false});
   observer=new ResizeObserver(()=>{if(!renderer||!camera||!stage)return;const nw=Math.max(320,stage.clientWidth),nh=Math.max(300,stage.clientHeight);camera.aspect=nw/nh;camera.updateProjectionMatrix();renderer.setSize(nw,nh);});observer.observe(target);
   const clock=new THREE.Clock();const animate=()=>{frameId=requestAnimationFrame(animate);const t=clock.getElapsedTime();scene.traverse(o=>{if(o.userData.rotate)o.rotation.y=t*.42;});renderer.render(scene,camera);};animate();
   target.insertAdjacentHTML('beforeend','<div class="vg-3d-hint">拖动旋转视角 · 滚轮缩放 · 点击墙上的展品可切换档案</div>');
   const selectedFrame=frames.find(f=>f.userData.index===selected);if(selectedFrame){selectedFrame.material.emissive=new THREE.Color('#4b3510');selectedFrame.material.emissiveIntensity=.25;}
   return true;
  }catch(err){console.warn('3D gallery unavailable; CSS tour remains available.',err);dispose();return false;}
 }
 window.WonderGallery3D={available, mount, dispose};
})();