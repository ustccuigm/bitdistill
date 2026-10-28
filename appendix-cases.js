(() => {
  'use strict';
  const nodes = [...document.querySelectorAll('[data-appendix-deck]')];
  if (!nodes.length) return;
  const el = (tag, cls, text) => { const n=document.createElement(tag); if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n; };
  const highlighted=(tag,cls,text)=>{const n=el(tag,cls);n.append(EvidenceHighlight.prose(text));return n;};
  function button(text,label,fn){const b=el('button','',text);b.type='button';b.setAttribute('aria-label',label);b.onclick=fn;return b;}
  function init(root,cases){
    let index=0,step=0,choices={};
    const key=root.dataset.appendixDeck;
    const pager=el('div','case-pager'),count=el('span','case-count'),select=el('select','case-select');
    count.setAttribute('aria-live','polite');select.setAttribute('aria-label',root.dataset.label+'：选择案例');
    cases.forEach((c,i)=>{const o=el('option','',`${String(i+1).padStart(2,'0')} · ${c.title}`);o.value=i;select.append(o);});
    const prev=button('←','上一个'+root.dataset.label,()=>navigate(index-1)),next=button('→','下一个'+root.dataset.label,()=>navigate(index+1));
    select.onchange=()=>navigate(Number(select.value));pager.append(count,select,prev,next);
    const title=el('h3','case-title'),id=el('p','case-task-id'),lede=el('p','case-expectation');
    const task=el('details','appendix-task'),taskSummary=el('summary','','查看任务与展示范围'),taskText=el('blockquote');task.append(taskSummary,taskText);
    const nav=el('div','case-stages appendix-stages'),body=el('div','appendix-body'),conclusion=el('p','appendix-conclusion'),source=el('a','appendix-source','案例数据 ↗');
    const download=el('a','appendix-source','下载案例数据 ↓'),dataLinks=el('div','appendix-data-links');download.setAttribute('download','');dataLinks.append(source,download);
    root.replaceChildren(pager,title,id,lede,task,nav,body,conclusion,dataLinks);
    function render(){
      const c=cases[index],s=c.stages[step];nav.replaceChildren();
      c.stages.forEach((v,i)=>{const b=button(`${String(i+1).padStart(2,'0')}  ${v.label}`,v.label,()=>{step=i;choices={};render();nav.children[i].focus({preventScroll:true});});b.setAttribute('aria-pressed',String(i===step));nav.append(b);});
      body.replaceChildren();body.classList.toggle('single-panel',s.groups.length===1);
      s.groups.forEach((g,gi)=>{
        const n=choices[gi]||0,p=g.options[n],column=el('div','appendix-column');
        const tabs=el('div','case-segments');tabs.setAttribute('aria-label',`选择${gi?'对照':'参考'}方法`);
        if(g.options.length>1)g.options.forEach((v,i)=>{const b=button(v.name,v.name,()=>{choices[gi]=i;render();body.children[gi].querySelectorAll('.case-segments button')[i].focus({preventScroll:true});});b.setAttribute('aria-pressed',String(i===n));tabs.append(b);});
        const card=el('article','appendix-panel '+p.tone),head=el('div','comparison-head');head.append(el('h4','',p.name),el('span','outcome',p.status));
        card.append(head,highlighted('p','reason-summary',p.summary));
        const codeLabel=key==='training'&&step===1?'实际 steering prompt':key==='recovery'&&gi===1?(p.fullCode?'关键工具返回（节选）':'工具返回'):'关键动作与状态';
        const pre=el('pre','case-code'),content=el('code');
        const ref=s.groups.length===2?s.groups[1-gi].options[choices[1-gi]||0].code:null;
        if(key==='inference'&&ref)content.append(EvidenceHighlight.difference(p.code,ref));else content.append(EvidenceHighlight.terms(p.code,[...(p.codeHighlights||[]),...(p.code.match(/\b[A-Za-z_]\w*(?=\()|\b\d{4}-\d{2}-\d{2}\b|menu_version_id|is_published|discount_percent|fuelAmount|fuelLevel|HTTP 500|unknown_tool|complete/g)||[])]));
        pre.append(content);card.append(el('h5','appendix-evidence-label',codeLabel),pre);
        if(p.fullCode){const detail=el('details','reasoning-context'),full=el('pre','case-code',p.fullCode);detail.append(el('summary','','展开完整工具返回'),full);card.append(detail);}
        if(p.quote){
          const q=el('blockquote','appendix-quote');q.textContent=p.quote;
          card.append(el('h5','appendix-evidence-label',key==='ablation'?'实际指导 prompt':'推理节选'));
          if(p.quote.length>1000){
            let focus='';try{focus=JSON.parse(p.quote.replace(/^```json\s*|\s*```$/g,'')).decision_rule||'';}catch{}
            if(!focus)focus=p.quote.split(/(?<=[.!?])\s+/).find(t=>t.length>40&&t.length<450)||'';
            if(focus){const f=el('blockquote','appendix-quote appendix-focus');f.append(EvidenceHighlight.terms(focus,[focus]));card.append(f);}
            const d=el('details','reasoning-context');d.append(el('summary','','展开推理 / 指导上下文'),q);card.append(d);
          }else{q.replaceChildren(EvidenceHighlight.terms(p.quote,[...(p.quoteHighlights||[]),...(p.quote.match(/\b\d{4}-\d{2}-\d{2}\b|\b(?:cannot|must|missing|instead|capacity|discount|order_id|menu_version_id|35|50|15)\b/g)||[])]));card.append(q);}
        }
        if(p.source){const a=el('a','appendix-source','查看对应记录 ↗');a.href=p.source;card.append(a);}
        column.append(tabs,card);body.append(column);
      });
      conclusion.replaceChildren(EvidenceHighlight.prose(c.conclusion));
    }
    function navigate(i){index=Math.max(0,Math.min(cases.length-1,i));step=0;choices={};const c=cases[index];select.value=index;count.textContent=`CASE ${String(index+1).padStart(2,'0')} / ${cases.length}`;prev.disabled=index===0;next.disabled=index===cases.length-1;title.textContent=c.title;id.textContent=c.id;lede.textContent=c.lede;taskText.textContent=c.task;source.href=c.source;download.hidden=!c.download;if(c.download)download.href=c.download;else download.removeAttribute('href');task.open=false;render();}
    root.addEventListener('keydown',e=>{
      if(!['ArrowLeft','ArrowRight'].includes(e.key)||e.target.closest('select,pre,blockquote,details'))return;
      const delta=e.key==='ArrowRight'?1:-1;
      if(e.target.closest('.appendix-stages')){
        e.preventDefault();step=Math.max(0,Math.min(cases[index].stages.length-1,step+delta));choices={};render();nav.children[step].focus({preventScroll:true});
      }else if(e.target.closest('.case-segments')){
        e.preventDefault();const gi=[...body.children].indexOf(e.target.closest('.appendix-column')),g=cases[index].stages[step].groups[gi];
        choices[gi]=Math.max(0,Math.min(g.options.length-1,(choices[gi]||0)+delta));render();body.children[gi].querySelectorAll('.case-segments button')[choices[gi]].focus({preventScroll:true});
      }else if(e.target.closest('.case-pager')){
        e.preventDefault();navigate(index+delta);(delta>0?next:prev).disabled?select.focus({preventScroll:true}):(delta>0?next:prev).focus({preventScroll:true});
      }
    });
    navigate(0);
  }
  fetch('data/appendix-showcase.json?v=20261028-workspace').then(r=>{if(!r.ok)throw Error();return r.json();}).then(data=>nodes.forEach(root=>init(root,data[root.dataset.appendixDeck]))).catch(()=>nodes.forEach(root=>{root.replaceChildren(el('p','','案例暂时无法加载。'));const b=button('重新加载','重新加载案例',()=>location.reload());root.append(b);}));
})();
