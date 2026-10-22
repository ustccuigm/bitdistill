(() => {
  'use strict';
  const section = document.querySelector('.comparison-section');
  if (!section) return;
  const tabs = [...section.querySelectorAll('[data-compare-tab]')];
  const pauseAll = () => {
    section.querySelectorAll('[data-compare-panel]').forEach(panel=>panel.dataset.groupPlayback='false');
    section.querySelectorAll('video').forEach(video => video.pause());
  };
  const select = tab => {
    pauseAll();
    tabs.forEach(button => {
      button.setAttribute('aria-selected', String(button === tab));
      button.tabIndex = button === tab ? 0 : -1;
    });
    section.querySelectorAll('[data-compare-panel]').forEach(panel => {
      panel.hidden = panel.dataset.comparePanel !== tab.dataset.compareTab;
    });
  };
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => select(tab));
    tab.addEventListener('keydown', event => {
      let target;
      if (event.key === 'ArrowRight') target = (index + 1) % tabs.length;
      else if (event.key === 'ArrowLeft') target = (index - 1 + tabs.length) % tabs.length;
      else if (event.key === 'Home') target = 0;
      else if (event.key === 'End') target = tabs.length - 1;
      else return;
      event.preventDefault();
      select(tabs[target]);
      tabs[target].focus();
    });
  });
  section.querySelectorAll('[data-compare-panel]').forEach(panel=>{
    const cards=[...panel.querySelectorAll('.comparison-card')];
    const videos=cards.map(card=>card.querySelector('video'));
    const controls=document.createElement('div');controls.className='comparison-playback';
    const start=document.createElement('button');start.type='button';start.textContent='▶ Play all from start';
    const pause=document.createElement('button');pause.type='button';pause.textContent='Ⅱ Pause all';pause.disabled=true;
    let started=false;
    const status=document.createElement('span');status.setAttribute('role','status');
    start.addEventListener('click',async()=>{
      pauseAll();start.disabled=true;status.textContent='';
      started=true;
      panel.dataset.groupPlayback='true';
      videos.forEach(video=>video.currentTime=0);
      const results=await Promise.allSettled(videos.map(video=>video.play()));
      if(panel.hidden){videos.forEach(video=>video.pause());}
      else if(results.some(result=>result.status==='rejected'))status.textContent='Some videos could not start. Use their play buttons to retry.';
      start.disabled=false;
    });
    pause.addEventListener('click',async()=>{
      if(videos.some(video=>!video.paused&&!video.ended)){
        videos.forEach(video=>video.pause());return;
      }
      panel.dataset.groupPlayback='true';status.textContent='';
      const results=await Promise.allSettled(videos.filter(video=>!video.ended).map(video=>video.play()));
      if(panel.hidden)videos.forEach(video=>video.pause());
      else if(results.some(result=>result.status==='rejected'))status.textContent='Some videos could not resume. Use their play buttons to retry.';
      update();
    });
    const update=()=>{
      if(videos.some(video=>!video.paused))started=true;
      const running=videos.some(video=>!video.paused&&!video.ended);
      pause.textContent=running?'Ⅱ Pause all':'▶ Resume all';
      pause.disabled=!started||videos.every(video=>video.ended);
    };
    videos.forEach(video=>['play','pause','ended'].forEach(event=>video.addEventListener(event,update)));
    controls.append(start,pause,status);panel.querySelector('.comparison-grid').before(controls);
    const switcher=document.createElement('div');switcher.className='comparison-method-tabs';
    switcher.setAttribute('role','group');switcher.setAttribute('aria-label','Comparison model');
    cards.forEach((card,index)=>{
      const button=document.createElement('button');button.type='button';button.textContent=card.querySelector('h4').textContent;
      button.setAttribute('aria-pressed',String(index===1));card.dataset.active=String(index===1);
      button.addEventListener('click',()=>{
        cards.forEach((c,i)=>c.dataset.active=String(i===index));
        [...switcher.children].forEach((b,i)=>b.setAttribute('aria-pressed',String(i===index)));
      });switcher.append(button);
    });panel.querySelector('.comparison-grid').before(switcher);
  });
  section.querySelectorAll('.comparison-film').forEach(film => {
    const video = film.querySelector('video');
    const cover = film.querySelector('.comparison-cover');
    video.controls = false;
    cover.addEventListener('click', async () => {
      film.closest('[data-compare-panel]').dataset.groupPlayback='false';
      cover.disabled = true;
      try {
        await video.play();
        cover.hidden = true;
      } catch (_) {
        cover.hidden = false;
      } finally {
        cover.disabled = false;
      }
    });
    video.addEventListener('play', () => { cover.hidden = true; video.controls = true; });
    video.addEventListener('ended', () => { cover.hidden = false; video.controls = false; });
  });
  document.addEventListener('visibilitychange',()=>{if(document.hidden)pauseAll();});
})();
