(() => {
  'use strict';
  const section = document.querySelector('.comparison-section');
  if (!section) return;
  const tabs = [...section.querySelectorAll('[data-compare-tab]')];
  const pauseAll = () => section.querySelectorAll('video').forEach(video => video.pause());
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
    const switcher=document.createElement('div');switcher.className='comparison-method-tabs';
    switcher.setAttribute('role','group');switcher.setAttribute('aria-label','Comparison model');
    cards.forEach((card,index)=>{
      const button=document.createElement('button');button.type='button';button.textContent=card.querySelector('h4').textContent;
      button.setAttribute('aria-pressed',String(index===1));card.dataset.active=String(index===1);
      button.addEventListener('click',()=>{
        pauseAll();cards.forEach((c,i)=>c.dataset.active=String(i===index));
        [...switcher.children].forEach((b,i)=>b.setAttribute('aria-pressed',String(i===index)));
      });switcher.append(button);
    });panel.querySelector('.comparison-grid').before(switcher);
  });
  section.querySelectorAll('.comparison-film').forEach(film => {
    const video = film.querySelector('video');
    const cover = film.querySelector('.comparison-cover');
    video.controls = false;
    cover.addEventListener('click', async () => {
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
})();
