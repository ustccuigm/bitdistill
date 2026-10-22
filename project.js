(() => {
  const root=document.documentElement;
  const buttons=[...document.querySelectorAll('.theme-toggle')];
  const updateTheme=()=>{
    buttons.forEach(button=>{
      button.setAttribute('aria-pressed',String(root.dataset.theme==='dark'));
      button.setAttribute('aria-label',root.dataset.theme==='dark'?'Switch to light theme':'Switch to dark theme');
    });
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content',root.dataset.theme==='dark'?'#1b1c1c':'#fffefa');
  };
  updateTheme();
  buttons.forEach(button=>button.addEventListener('click',()=>{
    root.dataset.theme=root.dataset.theme==='dark'?'light':'dark';
    try{localStorage.setItem('steer-theme',root.dataset.theme);}catch{}
    updateTheme();
  }));
  const tabs=[...document.querySelectorAll('[data-demo]')];
  const select=button=>{
    tabs.forEach(tab=>{tab.setAttribute('aria-selected',String(tab===button));tab.tabIndex=tab===button?0:-1;});
    document.querySelectorAll('[data-panel]').forEach(panel=>{
      panel.hidden=panel.dataset.panel!==button.dataset.demo;
      panel.querySelectorAll('video').forEach(video=>video.pause());
    });
  };
  tabs.forEach((button,index)=>{
    button.addEventListener('click',()=>select(button));
    button.addEventListener('keydown',event=>{
      let next;
      if(event.key==='ArrowRight')next=(index+1)%tabs.length;
      else if(event.key==='ArrowLeft')next=(index+tabs.length-1)%tabs.length;
      else if(event.key==='Home')next=0;
      else if(event.key==='End')next=tabs.length-1;
      else return;
      event.preventDefault();select(tabs[next]);tabs[next].focus();
    });
  });
  document.querySelectorAll('video').forEach(video=>video.addEventListener('play',()=>{
    const group=video.closest('[data-compare-panel][data-group-playback="true"]');
    document.querySelectorAll('video').forEach(other=>{
      if(other!==video&&!(group&&group.contains(other)))other.pause();
    });
  }));
})();
