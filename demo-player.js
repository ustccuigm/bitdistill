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
      let playing = false, timelineMode = null, frame = 'before';
      let markerTimer = null;
      const labels = {before:'原始尝试',repair:'教师纠偏后的重试',independent:'训练后独立执行'};
      const header = node('div', 'trajectory-heading');
      header.append(node('h3', '', demo.task));
      const paths = node('div', 'trajectory-paths'); paths.setAttribute('role','group');
      paths.setAttribute('aria-label','选择轨迹');
      const timeline = node('div', 'trajectory-timeline');
      timeline.setAttribute('role','group'); timeline.setAttribute('aria-label','逐步轨迹');
      const stepPicker=node('select','trajectory-step-picker');
      stepPicker.setAttribute('aria-label','选择任意轨迹步骤');
      stepPicker.addEventListener('change',()=>go(Number(stepPicker.value)));
      const progress=node('div','trajectory-progress');
      const progressLabel=node('span','trajectory-progress-label');
      progress.append(progressLabel,stepPicker,timeline);
      const controls = node('div', 'trajectory-controls');
      const counter = node('span', 'trajectory-counter'); counter.setAttribute('aria-live','polite');
      const prev = button('←','上一步',()=>go(index-1));
      const next = button('→','下一步',()=>go(index+1));
      const play = button('▶','自动播放轨迹',()=>{playing=!playing; updatePlay(); if(playing) schedule(); else clearTimeout(timer);});
      const replay = button('↻','从第 1 步重播',()=>go(0));
      controls.append(counter,prev,play,next,replay);
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
      root.replaceChildren(header,paths,progress,content,zoom);
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
      function centerStep(){
        const selected=timeline.children[index];if(!selected||!timeline.clientWidth)return;
        const a=selected.getBoundingClientRect(),b=timeline.getBoundingClientRect();
        timeline.scrollLeft+=a.left-b.left-(timeline.clientWidth-a.width)/2;
      }
      function go(value){
        const restore=content.contains(document.activeElement);
        stop();index=Math.max(0,Math.min(demo.runs[mode].length-1,value));render();
        if(restore)timeline.children[index].focus({preventScroll:true});
      }
      function animate(){
        clearTimeout(animation);clearTimeout(markerTimer);
        const screen=content.querySelector('.trajectory-input'), dot=content.querySelector('.trajectory-tap');
        if(!screen)return;
        screen.classList.remove('acting');void screen.offsetWidth;screen.classList.add('acting');
        if(dot){
          dot.hidden=false;
          const box=screen.getBoundingClientRect();
          dot.style.setProperty('--travel-x',`${box.width*(.5-parseFloat(dot.style.left)/100)}px`);
          dot.style.setProperty('--travel-y',`${box.height*(.85-parseFloat(dot.style.top)/100)}px`);
        }
        if(dot)markerTimer=setTimeout(()=>dot.hidden=true,1600);
      }
      function highlightChange(phones,step){
        if(!step.after||step.unchanged)return;
        const images=[...phones.querySelectorAll('img')];
        Promise.all(images.map(img=>img.decode())).then(()=>{
          if(!phones.isConnected)return;
          const canvas=document.createElement('canvas');canvas.width=100;canvas.height=216;
          const ctx=canvas.getContext('2d',{willReadFrequently:true});
          const samples=images.map(img=>{ctx.clearRect(0,0,100,216);ctx.drawImage(img,0,0,100,216);return ctx.getImageData(0,0,100,216).data;});
          let x0=100,y0=216,x1=0,y1=0,count=0;
          for(let y=0;y<216;y++)for(let x=0;x<100;x++){
            const at=(y*100+x)*4;
            if(Math.max(...[0,1,2].map(c=>Math.abs(samples[0][at+c]-samples[1][at+c])))>50){
              x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);count++;
            }
          }
          // Only outline localized image changes; navigation can replace the whole screen.
          if(count<5||(x1-x0)*(y1-y0)>100*216*.45)return;
          const region=node('span','trajectory-change');region.setAttribute('aria-hidden','true');
          Object.assign(region.style,{left:Math.max(0,x0-2)+'%',top:Math.max(0,(y0-2)/216*100)+'%',width:Math.min(100-x0+2,x1-x0+5)+'%',height:Math.min(216-y0+2,y1-y0+5)/216*100+'%'});
          phones.querySelector('.trajectory-output').append(region);
        }).catch(()=>{});
      }
      function render(){
        clearTimeout(animation);
        const steps=demo.runs[mode], step=steps[index];
        root.dataset.run=mode;
        paths.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.run===mode)));
        if(timelineMode!==mode){
          timeline.replaceChildren();stepPicker.replaceChildren();
          steps.forEach((s,i)=>{
            const b=button(`${String(s.turn).padStart(2,'0')} ${s.label}`,`第 ${s.turn} 步：${s.label}`,()=>go(i));
            b.className=s.divergence?'divergence':'';timeline.append(b);
            const option=node('option','',`${String(s.turn).padStart(2,'0')} · ${s.label}`);option.value=i;stepPicker.append(option);
          });
          timelineMode=mode;
        }
        [...timeline.children].forEach((b,i)=>{b.setAttribute('aria-current',String(i===index));b.hidden=Math.abs(i-index)>2;});
        stepPicker.value=String(index);
        let start=index,end=index;
        while(start>0&&steps[start-1].label===step.label)start--;
        while(end<steps.length-1&&steps[end+1].label===step.label)end++;
        progressLabel.textContent=end-start>1?`重复尝试 ${steps[start].turn}–${steps[end].turn}`:'步骤';
        requestAnimationFrame(centerStep);
        counter.textContent=`${labels[mode]} · ${index+1} / ${steps.length}`;
        prev.disabled=index===0;next.disabled=index===steps.length-1;
        const narrative=node('div','trajectory-reading');
        narrative.append(node('p','trajectory-kicker',`第 ${step.turn} 步 · ${step.label}`));
        const guide=node('p','trajectory-guide');
        guide.append(EvidenceHighlight.terms(step.guide,key==='phone'?
          ['550','560','输入焦点','标签和下划线变蓝','Save Changes','输入动作与保存是两步','没有转入输入和保存','输入和保存']:
          ['内容区域','右侧图标','右侧蓝色图标','(480, 220)','(880, 410)','Code copied!','复制图标','没有出现复制成功的确认','真正复制']));
        const action=node('pre','trajectory-action');
        const counterpart=mode==='before'&&step.divergence?demo.runs.repair[0]:mode==='repair'&&index===0?demo.runs.before[demo.pivot]:null;
        if(counterpart){
          action.append(EvidenceHighlight.difference(step.action,counterpart.action));
        }else action.textContent=step.action;
        const thought=node('blockquote','trajectory-thought');
        thought.append(EvidenceHighlight.terms(step.thought,key==='phone'?
          ['appears editable','activate the input field','activate the field','ready for input','save the changes','Save Changes']:
          ['Tap code to reveal','small blue icon','copy icon','copied successfully','successfully copied']));
        narrative.append(guide);
        if(mode==='repair'){
          const guidance=node('aside','trajectory-guidance');
          guidance.append(node('span','trajectory-guidance-label','Teacher steering'),node('p','',demo.teacher.decision_rule||''),teacher);
          narrative.append(guidance);
        }
        const thoughtDetails=node('details','trajectory-thought-details');
        thoughtDetails.append(node('summary','','完整推理'),thought);
        const sentences=step.thought.match(/[^.!?\n]+(?:[.!?]+|$)/g)||[step.thought];
        const excerpt=sentences.find(s=>/need|should|next|click|tap|type|save|copy|editable/i.test(s))||sentences[0]||'';
        const preview=node('blockquote','trajectory-thought-preview');
        preview.append(EvidenceHighlight.terms(excerpt.trim(),[...thought.querySelectorAll('mark')].map(m=>m.textContent)));
        narrative.append(node('h4','','Thinking'),preview,thoughtDetails,node('h4','','Action'),action);
        const result=step.result.info||{};
        const state=step.result.done?(result.success?'环境确认任务成功': '轨迹结束，任务未通过'):
          mode==='before'&&index===steps.length-1?'原始轨迹止于这一步，没有记录到任务成功。':
          step.after?(step.unchanged?'前后截图相同；没有可见进展。':'动作后截图有变化，仍需查看后续任务结果。'):'未记录下一张截图。';
        narrative.append(node('h4','','观察与结果'),node('p','trajectory-state',state));
        if(result.message)narrative.append(node('p','trajectory-message',result.message));
        const raw=node('details','trajectory-record');raw.append(node('summary','','本步执行记录'),node('pre','',JSON.stringify(step.result,null,2)));narrative.append(raw);
        const background=node('details','trajectory-background');background.append(node('summary','','任务背景'),node('p','',demo.lead));narrative.append(background);
        const phones=node('div','trajectory-phones');
        const frameTabs=node('div','trajectory-frame-tabs');frameTabs.setAttribute('role','group');frameTabs.setAttribute('aria-label','截图视图');
        const selectFrame=value=>{
          frame=value;phones.dataset.frame=frame;
          frameTabs.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.frame===frame)));
        };
        for(const [value,label] of [['before','动作之前'],['after','动作之后']]){
          const b=button(label,'截图：'+label,()=>selectFrame(value));b.dataset.frame=value;frameTabs.append(b);
        }
        ['before','after'].forEach((side,i)=>{
          const figure=node('figure','');figure.dataset.frame=side;
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
            const enlarge=()=>{stop();zoomImage.src=img.src;zoomImage.alt=img.alt;zoom.showModal();};
            shell.tabIndex=0;shell.setAttribute('role','button');shell.setAttribute('aria-label','放大动作后截图');
            shell.title='放大动作后截图';shell.onclick=enlarge;
            shell.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();enlarge();}};
          }
          figure.append(caption,shell);
          if(i)figure.append(node('p','trajectory-frame-note',step.after?(step.unchanged?'画面未改变': '下一步记录的实际画面'):'没有后续截图，保留最后画面；结果见环境记录。'));
          phones.append(figure);
        });
        const media=node('div','trajectory-media');media.append(controls,frameTabs,phones);
        selectFrame(frame);content.replaceChildren(narrative,media);
        highlightChange(phones,step);
        animate();
      }
      root.addEventListener('keydown',e=>{
        if(zoom.open||e.target.matches('summary,input,textarea,select')||e.target.closest('pre'))return;
        if(e.key==='ArrowLeft'||e.key==='ArrowRight'){
          e.preventDefault();go(index+(e.key==='ArrowRight'?1:-1));
          timeline.children[index].focus({preventScroll:true});
        }
      });
      new MutationObserver(()=>{if(root.closest('[hidden]'))stop();else render();}).observe(root.closest('[role="tabpanel"]')||root,{attributes:true,attributeFilter:['hidden']});
      new ResizeObserver(()=>requestAnimationFrame(centerStep)).observe(timeline);
      render();
    });
  }).catch(()=>mounts.forEach(root=>root.textContent='轨迹加载失败，请刷新重试。'));
})();
