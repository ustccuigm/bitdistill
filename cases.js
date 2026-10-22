(() => {
  'use strict';
  const root = document.querySelector('.case-deck');
  if (!root) return;
  const baselines = ['GPTQ', 'EfficientQAT', 'BitDistiller', 'On-Policy QAD', 'QeRL'];
  let cases, index = 0, stage = 'compare', good = 'Ours', bad = 'GPTQ';
  const expanded = new Map();
  const el = (tag, cls, value) => {
    const node = document.createElement(tag); if (cls) node.className = cls;
    if (value !== undefined) node.textContent = value; return node;
  };
  function button(label, title, action) {
    const node = el('button','',label); node.type='button'; node.title=title;
    node.setAttribute('aria-label',title); node.onclick=action; return node;
  }
  function highlight(value, cls) {
    const node=el('p', cls);node.append(EvidenceHighlight.prose(value));return node;
  }
  function code(value, reference) {
    const pre=el('pre','case-code'), content=el('code');
    if(typeof reference==='string')content.append(EvidenceHighlight.difference(value,reference));
    else content.textContent=value;
    pre.append(content);return pre;
  }
  function reasoning(value) {
    const quote=el('blockquote');
    const clauses=value.match(/[^.!?\n]+(?:[.!?]+|$)/g)||[];
    const cues=/\b(?:need to|should|must|cannot|can't|shouldn't|missing|didn't specify|did not (?:specify|provide)|not provided|no (?:tool|function)|only available|have to use|pick one|assum\w*|instead|clarif\w*|doesn't|does not|not (?:available|supported|specifically))\b/i;
    const phrases=clauses.map(s=>s.trim()).filter(s=>s.length>15&&s.length<280&&cues.test(s)).slice(0,5);
    quote.append(EvidenceHighlight.terms(value,phrases));return quote;
  }
  function segment(items, selected, onSelect, label) {
    const nav=el('div','case-segments');nav.setAttribute('aria-label',label);
    for(const item of items){
      const title=label+'：'+item;
      const b=button(item,title,()=>{
        onSelect(item);
        [...root.querySelectorAll('.case-segments button')].find(node=>node.getAttribute('aria-label')===title)?.focus({preventScroll:true});
      });
      b.setAttribute('aria-pressed',String(item===selected));nav.append(b);
    }return nav;
  }
  function panel(name, side) {
    const original=cases[index].methods[name];
    const focus=cases[index].methods[bad].focus_turn;
    const data=side==='good'?{...original,...original.by_turn?.[String(focus)]}:original;
    const peer=side==='good'?cases[index].methods[bad]:cases[index].methods[good];
    const peerEvidence=side==='good'?peer:(peer.by_turn?.[String(focus)]||peer);
    const card=el('section','comparison-panel '+side);
    const head=el('div','comparison-head');head.append(el('h4','',name),el('span','outcome',data.passed?'通过':'未通过'));
    const intro=el('div','comparison-intro');
    intro.append(head,el('p','reason-label',data.passed?'为什么做对':'为什么失败'),highlight(data.reason,'reason-summary'));
    card.append(intro);
    const evidence=el('div','case-evidence action-evidence');evidence.tabIndex=0;
    evidence.setAttribute('aria-label',name+'动作与答复');
      evidence.append(el('p','evidence-label',data.location||'关键动作 / 实际答复'));
      if(side==='bad'&&data.state_evidence?.length){
        const outcome=el('div','state-evidence');outcome.append(el('p','evidence-label','评分记录中的具体状态差异'));
        data.state_evidence.slice(0,4).forEach(value=>outcome.append(el('p','',value)));evidence.append(outcome);
      }
      if(data.missing){
        evidence.append(el('p','no-call',data.passed?'未调用任务工具，直接答复用户':'这一轮没有执行任务工具调用'));
        if(data.reference&&!data.passed){evidence.append(el('p','evidence-label','BF16 在这一轮的对照调用'),code(data.reference));}
        evidence.append(el('p','evidence-label','模型实际答复'),el('blockquote','',data.response||'该轮记录中未检出最终文字答复。'));
      }else evidence.append(code(data.code||'该位置没有动作片段。',peerEvidence.missing?'':peerEvidence.code));
    const thought=el('div','case-evidence reasoning-evidence');thought.tabIndex=0;
    thought.setAttribute('aria-label',name+'推理节选');
    const quote=reasoning(data.reasoning||'该位置没有可展示的推理文本。');
    const decisionCue=data.passed
      ? /cannot|can't|unable|no (?:available )?(?:tool|function)|not (?:possible|supported|available)|should (?:explain|ask|inform)|clarification|refrain|shouldn't/ig
      : /have to use|need to (?:pick|choose)|assum\w*|proceed|let(?:'s| me) (?:try|call|use)|generic|default|only (?:available )?tool/ig;
    const candidates=(data.reasoning||'').match(/[^.!?\n]+(?:[.!?]+|$)/g)||[];
    const ranked=candidates.map((text,i)=>({text:text.trim(),i,score:(text.match(decisionCue)||[]).length}))
      .filter(x=>x.score&&x.text.length>15&&x.text.length<360)
      .sort((a,b)=>b.score-a.score||b.i-a.i);
    const focusText=ranked[0]?.text||quote.querySelector('mark')?.textContent;
    if(focusText){
      const focusQuote=el('blockquote','reasoning-focus');
      focusQuote.append(EvidenceHighlight.terms(focusText,[focusText]));
      thought.append(focusQuote);
    }
    const context=el('details','reasoning-context');
    const contextKey=[index,name,focus].join(':');
    const summary=el('summary');
    context.open=expanded.get(contextKey)??!focusText;
    const updateContext=()=>{
      summary.textContent=context.open?'收起推理上下文':(focusText?'查看推理上下文':'查看推理节选');
      expanded.set(contextKey,context.open);
    };
    updateContext();context.addEventListener('toggle',updateContext);
    context.append(summary,quote);
    thought.append(context);
    const actionGroup=el('section','evidence-group action-group');
    const thoughtGroup=el('section','evidence-group thought-group');
    actionGroup.append(el('h5','evidence-heading',name+' · 动作与答复'),evidence);
    thoughtGroup.append(el('h5','evidence-heading',name+' · 推理节选'),thought);
    card.append(actionGroup,thoughtGroup); return card;
  }
  const pager=el('div','case-pager');
  const count=el('span','case-count');count.setAttribute('aria-live','polite');
  const select=el('select','case-select');select.setAttribute('aria-label','选择案例');
  select.onchange=()=>navigate(Number(select.value));
  const prev=button('←','上一个案例',()=>navigate(index-1));
  const next=button('→','下一个案例',()=>navigate(index+1));
  prev.disabled=next.disabled=select.disabled=true;
  pager.append(count,select,prev,next);
  const heading=el('h3','case-title'), id=el('p','case-task-id'), expectation=el('p','case-expectation');
  const stages=el('div','case-stages');
  const body=el('div','case-body');
  const labels={task:'任务',compare:'关键对照',conclusion:'案例结论'};
  Object.entries(labels).forEach(([key,label])=>{const b=button(label,label,()=>{stage=key;renderBody();});b.dataset.stage=key;stages.append(b);});
  root.replaceChildren(pager,heading,id,expectation,stages,body);
  function renderBody(){
    if(!cases)return;
    const c=cases[index]; body.replaceChildren();
    stages.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.stage===stage)));
    if(stage==='task'){
      const tasks=el('div','case-task-reader'); tasks.tabIndex=0;
      c.tasks.forEach(t=>{const item=el('section','task-turn');item.append(el('p','evidence-label',t.label),el('blockquote','',t.text));tasks.append(item);});
      body.append(tasks);return;
    }
    if(stage==='conclusion'){
      const conclusion=el('div','case-conclusion');
      conclusion.append(el('p','evidence-label','关键分歧'),el('h4','',c.conclusion_title),highlight(c.conclusion,'conclusion-copy'),el('p','case-context',c.intro));
      body.append(conclusion);return;
    }
    const method=c.methods[bad], turn=method.focus_turn;
    const task=c.tasks[Math.min(Math.max(turn-1,0),c.tasks.length-1)];
    const taskStrip=el('div','case-task-strip');taskStrip.append(el('span','evidence-label',task.label),el('p','',task.text));
    const compare=el('div','compare-scroll');compare.tabIndex=0;compare.setAttribute('aria-label','正确方法与 baseline 对照');
    const grid=el('div','compare-grid');
    const left=el('div','method-column'),right=el('div','method-column');
    left.append(segment(['Ours','BF16'],good,value=>{good=value;renderBody();},'正确方法'),panel(good,'good'));
    right.append(segment(baselines,bad,value=>{bad=value;renderBody();},'对比方法'),panel(bad,'bad'));
    grid.append(left,right);compare.append(grid);body.append(taskStrip,compare);
  }
  function navigate(value){
    if(!cases)return;
    index=Math.max(0,Math.min(cases.length-1,value));
    const c=cases[index];
    count.textContent=`CASE ${String(index+1).padStart(2,'0')} / ${cases.length}`;
    heading.textContent=c.title;id.textContent=c.task_id;expectation.textContent=c.expectation;
    select.disabled=false;select.value=String(index);prev.disabled=index===0;next.disabled=index===cases.length-1;
    history.replaceState(null,'',`#case-${index+1}`);renderBody();
  }
  root.addEventListener('keydown',e=>{
    if(!cases||!['ArrowLeft','ArrowRight'].includes(e.key)||e.target.matches('select,input,textarea')||e.target.closest('.case-evidence'))return;
    e.preventDefault();navigate(index+(e.key==='ArrowRight'?1:-1));
  });
  let touch;
  heading.addEventListener('touchstart',e=>touch=e.changedTouches[0].clientX,{passive:true});
  heading.addEventListener('touchend',e=>{if(cases&&touch!==undefined){const delta=e.changedTouches[0].clientX-touch;if(Math.abs(delta)>60)navigate(index+(delta<0?1:-1));}touch=undefined;},{passive:true});
  fetch('data/case-slides.json').then(r=>{if(!r.ok)throw Error();return r.json();}).then(data=>{
    if(data.length!==40)throw Error();cases=data;
    cases.forEach((c,i)=>{const option=el('option','',`${String(i+1).padStart(2,'0')} · ${c.title}`);option.value=i;select.append(option);});
    const hash=location.hash.match(/^#case-(\d+)$/);index=hash?Math.max(0,Math.min(cases.length-1,Number(hash[1])-1)):0;
    const previousHash=location.hash;navigate(index);if(!hash)history.replaceState(null,'',previousHash||location.pathname+location.search);
  }).catch(()=>{body.textContent='案例暂时无法加载，请刷新重试。';prev.disabled=next.disabled=true;});
})();
