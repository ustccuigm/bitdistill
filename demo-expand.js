(() => {
 const root=document.querySelector('#demo');if(!root)return;
 const dialog=document.createElement('dialog');dialog.className='demo-expanded';
 const bar=document.createElement('div');bar.className='demo-expanded-bar';
 const title=document.createElement('strong');const close=document.createElement('button');close.type='button';close.textContent='Close ×';close.setAttribute('aria-label','Close enlarged recording');
 const video=document.createElement('video');video.controls=true;video.playsInline=true;video.preload='metadata';
 bar.append(title,close);dialog.append(bar,video);document.body.append(dialog);
 let original=null;
 close.onclick=()=>dialog.close();dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close();});
 dialog.addEventListener('close',()=>{video.pause();if(original)original.currentTime=Math.min(video.currentTime,original.duration||video.currentTime);video.removeAttribute('src');video.load();});
 root.querySelectorAll('.comparison-card').forEach(card=>{
  const source=card.querySelector('video');const link=card.querySelector('.comparison-open');
  const button=document.createElement('button');button.type='button';button.className='demo-enlarge';button.textContent='Enlarge screen & model output';
  button.onclick=()=>{
   root.querySelectorAll('video').forEach(v=>v.pause());original=source;title.textContent=source.getAttribute('aria-label');video.src=source.currentSrc||source.src;video.currentTime=source.currentTime;dialog.showModal();video.play().catch(()=>{});
  };link.before(button);
 });
})();
