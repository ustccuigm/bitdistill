(() => {
  'use strict';
  const mounts = [...document.querySelectorAll('[data-trajectory]')];
  if (!mounts.length) return;
  const source = new URL('demos/player/trajectories.json', document.baseURI);
  const asset = value => new URL(value, source).href;
  const node = (tag, cls, text) => {
    const e = document.createElement(tag); e.className = cls || '';
    if (text !== undefined) e.textContent = text;
    return e;
  };
  const button = (text, label, fn) => {
    const b = node('button', '', text); b.type = 'button'; b.title = label;
    b.setAttribute('aria-label', label); b.addEventListener('click', fn); return b;
  };
  fetch(source).then(r => {if (!r.ok) throw Error(); return r.json();}).then(data => {
    mounts.forEach(root => {
      const key = root.dataset.trajectory, demo = data[key];
      let mode = 'before', index = demo.pivot, timer = null, animation = null;
      let playing = false;
      const labels = {before:'原始尝试',repair:'教师纠偏后的重试',independent:'训练后独立执行'};
      const header = node('div', 'trajectory-heading');
      header.append(node('h3', '', demo.title), node('p', '', demo.lead));
      const task = node('p', 'trajectory-task', '任务：'+demo.task);
      const paths = node('div', 'trajectory-paths'); paths.setAttribute('role','group');
      paths.setAttribute('aria-label','选择轨迹');
      const timeline = node('div', 'trajectory-timeline');
      timeline.setAttribute('role','group'); timeline.setAttribute('aria-label','逐步轨迹');
      const controls = node('div', 'trajectory-controls');
      const counter = node('span', 'trajectory-counter'); counter.setAttribute('aria-live','polite');
      const prev = button('←','上一步',()=>go(index-1));
      const next = button('→','下一步',()=>go(index+1));
      const play = button('▶','自动播放轨迹',()=>{playing=!playing; updatePlay(); if(playing) schedule(); else clearTimeout(timer);});
      const replay = button('↻','重放本步动作',()=>animate());
      const first = button('从第 1 步','从第 1 步开始',()=>go(0));
      controls.append(counter,first,prev,play,next,replay);
      const teacher = node('details','trajectory-teacher');
      teacher.append(node('summary','','Teacher steering · 原始指导'));
      Object.entries(demo.teacher).forEach(([name,value])=>{
        const p=node('p','');p.append(node('strong','',name.replaceAll('_',' ')+' — '),document.createTextNode(value));teacher.append(p);
      });
      const content = node('div','trajectory-content');
      const zoom = node('dialog','trajectory-zoom');
      const zoomImage=node('img','');
      zoom.append(button('×','关闭放大截图',()=>zoom.close()),zoomImage);
      zoom.addEventListener('click',e=>{if(e.target===zoom)zoom.close();});
      root.replaceChildren(header,task,paths,timeline,controls,teacher,content,zoom);
      for(const [value,label] of Object.entries(labels)){
        const b=button(label,label,()=>{mode=value;index=value==='before'?demo.pivot:0;stop();render();});
        b.dataset.run=value;paths.append(b);
      }
      function stop(){playing=false;clearTimeout(timer);updatePlay();}
      function updatePlay(){play.textContent=playing?'Ⅱ':'▶';play.setAttribute('aria-label',playing?'暂停播放':'自动播放轨迹');}
      function schedule(){clearTimeout(timer);timer=setTimeout(()=>{
        if(root.closest('[hidden]') || document.hidden){stop();return;}
        if(index>=demo.runs[mode].length-1){stop();return;}index++;render();schedule();
      },4200);}
      function go(value){stop();index=Math.max(0,Math.min(demo.runs[mode].length-1,value));render();}
      function animate(){
        clearTimeout(animation);
        const screen=content.querySelector('.trajectory-input'), dot=content.querySelector('.trajectory-tap');
        if(!screen)return;
        screen.classList.remove('acting');void screen.offsetWidth;screen.classList.add('acting');
        if(dot){
          dot.hidden=false;
          const box=screen.getBoundingClientRect();
          dot.style.setProperty('--travel-x',`${box.width*(.5-parseFloat(dot.style.left)/100)}px`);
          dot.style.setProperty('--travel-y',`${box.height*(.85-parseFloat(dot.style.top)/100)}px`);
        }
        const outcome=content.querySelector('.trajectory-output');
        outcome.classList.remove('revealed');void outcome.offsetWidth;
        animation=setTimeout(()=>outcome.classList.add('revealed'),900);
      }
      function render(){
        clearTimeout(animation);
        const steps=demo.runs[mode], step=steps[index];
        root.dataset.run=mode;
        paths.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.run===mode)));
        timeline.replaceChildren();
        steps.forEach((s,i)=>{
          const b=button(`${String(s.turn).padStart(2,'0')} ${s.label}`,`第 ${s.turn} 步：${s.label}`,()=>go(i));
          b.className=s.divergence?'divergence':'';
          b.setAttribute('aria-current',String(i===index));timeline.append(b);
        });
        const selected=timeline.children[index];
        timeline.scrollLeft=Math.max(0,selected.offsetLeft-timeline.offsetLeft-timeline.clientWidth/2+selected.clientWidth/2);
        counter.textContent=`${labels[mode]} · ${index+1} / ${steps.length}`;
        prev.disabled=index===0;next.disabled=index===steps.length-1;
        teacher.hidden=mode!=='repair';teacher.open=mode==='repair';
        const narrative=node('div','trajectory-reading');
        narrative.append(node('p','trajectory-kicker',`第 ${step.turn} 步 · ${step.label}`));
        const guide=node('p','trajectory-guide');
        const period=step.guide.indexOf('。');
        guide.append(node('mark','',step.guide.slice(0,period+1)),document.createTextNode(step.guide.slice(period+1)));
        const action=node('pre','trajectory-action');
        const argumentStart=step.action.indexOf('(');
        if(argumentStart>=0&&(step.divergence||(mode==='repair'&&index===0))){
          action.append(document.createTextNode(step.action.slice(0,argumentStart)),node('mark','',step.action.slice(argumentStart)));
        }else action.textContent=step.action;
        narrative.append(guide,node('h4','','Thinking · 模型原文'),node('blockquote','trajectory-thought',step.thought),node('h4','','Action · 实际动作'),action);
        const result=step.result.info||{};
        const state=step.result.done?(result.success?'环境确认任务成功': '轨迹结束，任务未通过'):
          mode==='before'&&index===steps.length-1?'原始轨迹止于这一步，没有记录到任务成功。':
          step.after?(step.unchanged?'前后截图相同；没有可见进展。':'动作后截图有变化，仍需查看后续任务结果。'):'未记录下一张截图。';
        narrative.append(node('h4','','观察与结果'),node('p','trajectory-state',state));
        if(result.message)narrative.append(node('p','trajectory-message',result.message));
        const raw=node('details','trajectory-record');raw.append(node('summary','','本步执行记录'),node('pre','',JSON.stringify(step.result,null,2)));narrative.append(raw);
        const phones=node('div','trajectory-phones');
        ['before','after'].forEach((side,i)=>{
          const figure=node('figure','');
          const caption=node('figcaption','',i?'动作之后':step.tap?'动作之前 · 点击位置':'动作之前');
          const shell=node('div','trajectory-device '+(i?'trajectory-output':'trajectory-input'));
          const img=node('img','');img.src=asset(step[side]||step.before);
          img.alt=`${demo.task}，第 ${step.turn} 步，${i?'动作后':'动作前'}的执行截图`;img.width=390;img.height=844;
          shell.append(img);
          if(!i&&step.tap){
            const dot=node('span','trajectory-tap');dot.setAttribute('aria-hidden','true');
            dot.style.left=step.tap[0]+'%';dot.style.top=step.tap[1]+'%';shell.append(dot);
          }
          if(!i){shell.tabIndex=0;shell.setAttribute('role','button');shell.setAttribute('aria-label','重放本步动作');shell.onclick=animate;shell.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();animate();}};}
          else{
            const enlarge=()=>{zoomImage.src=img.src;zoomImage.alt=img.alt;zoom.showModal();};
            shell.tabIndex=0;shell.setAttribute('role','button');shell.setAttribute('aria-label','放大动作后截图');
            shell.title='放大动作后截图';shell.onclick=enlarge;
            shell.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();enlarge();}};
          }
          figure.append(caption,shell);
          if(i)figure.append(node('p','trajectory-frame-note',step.after?(step.unchanged?'画面未改变': '下一步记录的实际画面'):'没有后续截图，保留最后画面；结果见环境记录。'));
          phones.append(figure);
        });
        content.replaceChildren(narrative,phones);
        animate();
      }
      root.addEventListener('keydown',e=>{
        if(e.target.matches('summary')||e.target.closest('pre'))return;
        if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();go(index+(e.key==='ArrowRight'?1:-1));}
      });
      new MutationObserver(()=>{if(root.closest('[hidden]'))stop();else render();}).observe(root.closest('[role="tabpanel"]')||root,{attributes:true,attributeFilter:['hidden']});
      render();
    });
  }).catch(()=>mounts.forEach(root=>root.textContent='轨迹加载失败，请刷新重试。'));
})();
