(() => {
  'use strict';
  const section = document.querySelector('.comparison-section');
  if (!section) return;
  const tabs = [...section.querySelectorAll('[data-compare-tab]')];
  async function playVideo(video){
    let timeout;
    try{
      await Promise.race([video.play(),new Promise((_,reject)=>{timeout=setTimeout(()=>{video.pause();reject(Error('Playback timeout'));},15000);})]);
    }finally{clearTimeout(timeout);}
  }
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
    let busy=false,seeking=false;
    const status=document.createElement('span');status.setAttribute('role','status');
    const scrub=document.createElement('div');scrub.className='comparison-scrubber';
    const range=document.createElement('input');range.type='range';range.min=0;range.max=0;range.step=.05;range.value=0;range.disabled=true;
    range.setAttribute('aria-label','Seek all recordings (seconds)');
    const clock=document.createElement('output');clock.textContent='0:00 / 0:00';
    scrub.append(range,clock);
    const format=seconds=>{
      const tenths=Math.round(seconds*10);
      return `${Math.floor(tenths/600)}:${(tenths%600/10).toFixed(1).padStart(4,'0')}`;
    };
    const total=()=>Math.max(0,...videos.map(v=>Number.isFinite(v.duration)?v.duration:0));
    const showTime=time=>{clock.textContent=`${format(time)} / ${format(total())}`;range.setAttribute('aria-valuetext',`${time.toFixed(1)} seconds of ${total().toFixed(1)}`);};
    videos.forEach(video=>{
      video.preload='metadata';
      video.addEventListener('loadedmetadata',()=>{range.max=total();range.disabled=!videos.every(v=>Number.isFinite(v.duration));showTime(Number(range.value));});
      video.addEventListener('timeupdate',()=>{
        if(seeking)return;
        const time=panel.dataset.groupPlayback==='true'?Math.max(...videos.map(v=>v.currentTime)):video.currentTime;
        range.value=time;showTime(time);
      });
    });
    range.addEventListener('input',()=>{
      seeking=true;videos.forEach(video=>video.pause());started=true;
      panel.dataset.groupPlayback='true';
      const time=Number(range.value);
      videos.forEach(video=>{
        video.currentTime=Math.min(time,video.duration);
        video.closest('.comparison-film').querySelector('.comparison-cover').hidden=true;
      });showTime(time);update();
    });
    range.addEventListener('change',()=>{seeking=false;});
    const loading=value=>{
      busy=value;start.disabled=value;pause.disabled=value;range.disabled=value||!videos.every(v=>Number.isFinite(v.duration));
      controls.setAttribute('aria-busy',String(value));start.textContent=value?'Loading…':'▶ Play all from start';
      if(!value)update();
    };
    start.addEventListener('click',async()=>{
      if(busy)return;
      pauseAll();loading(true);status.textContent='';
      started=true;
      panel.dataset.groupPlayback='true';
      videos.forEach(video=>video.currentTime=0);
      const results=await Promise.allSettled(videos.map(playVideo));
      if(panel.hidden){videos.forEach(video=>video.pause());}
      else if(results.some(result=>result.status==='rejected'))status.textContent='Some videos could not start. Use their play buttons to retry.';
      loading(false);
    });
    pause.addEventListener('click',async()=>{
      if(busy)return;
      if(videos.some(video=>!video.paused&&!video.ended)){
        videos.forEach(video=>video.pause());return;
      }
      panel.dataset.groupPlayback='true';status.textContent='';
      loading(true);
      const results=await Promise.allSettled(videos.filter(video=>video.currentTime<video.duration-.05).map(playVideo));
      if(panel.hidden)videos.forEach(video=>video.pause());
      else if(results.some(result=>result.status==='rejected'))status.textContent='Some videos could not resume. Use their play buttons to retry.';
      loading(false);
    });
    const update=()=>{
      if(videos.some(video=>!video.paused))started=true;
      const running=videos.some(video=>!video.paused&&!video.ended);
      pause.textContent=running?'Ⅱ Pause all':'▶ Resume all';
      pause.disabled=busy||!started||videos.every(video=>video.ended||video.currentTime>=video.duration-.05);
    };
    videos.forEach(video=>['play','pause','ended','seeked'].forEach(event=>video.addEventListener(event,update)));
    controls.append(start,pause,status);panel.querySelector('.comparison-grid').before(controls,scrub);
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
      const label=cover.querySelector('span:last-child');label.textContent='Loading…';
      try {
        if(video.ended)video.currentTime=0;
        await playVideo(video);
        cover.hidden = true;
      } catch (_) {
        cover.hidden = false;
        label.textContent='Retry playback';
      } finally {
        cover.disabled = false;
        if(cover.hidden)label.textContent='Watch recorded run';
      }
    });
    video.addEventListener('play', () => { cover.hidden = true; video.controls = true; });
    video.addEventListener('ended', () => { cover.hidden = true; video.controls = true; });
  });
  document.addEventListener('visibilitychange',()=>{if(document.hidden)pauseAll();});
})();
