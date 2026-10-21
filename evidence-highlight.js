(() => {
  'use strict';
  const tokens = text => text.match(/[A-Za-z_][\w]*(?:\.[\w]+)*|\d+(?:\.\d+)?|\s+|[^\w\s]/g) || [];
  function difference(value, reference) {
    const a=tokens(value), b=tokens(reference), changed=new Set();
    if(a.length*b.length>600000){
      const known=new Set(b);a.forEach((t,i)=>{if(!known.has(t)&&t.trim())changed.add(i);});
    }else{
      const rows=Array.from({length:a.length+1},()=>new Uint16Array(b.length+1));
      for(let i=a.length-1;i>=0;i--)for(let j=b.length-1;j>=0;j--)
        rows[i][j]=a[i]===b[j]?rows[i+1][j+1]+1:Math.max(rows[i+1][j],rows[i][j+1]);
      let i=0,j=0;
      while(i<a.length&&j<b.length){
        if(a[i]===b[j]){i++;j++;}
        else if(rows[i+1][j]>=rows[i][j+1]){changed.add(i++);}
        else j++;
      }
      while(i<a.length)changed.add(i++);
    }
    const fragment=document.createDocumentFragment();
    a.forEach((t,i)=>{
      if(changed.has(i)&&t.trim()){
        const mark=document.createElement('mark');mark.textContent=t;fragment.append(mark);
      }else fragment.append(document.createTextNode(t));
    });
    return fragment;
  }
  function prose(value) {
    const fragment=document.createDocumentFragment();
    // Highlight concrete names, values and short missing-action clauses.
    const pattern=/["“][^"”\n]{1,70}["”]|\b[A-Za-z_][A-Za-z_0-9]*(?:[.\-][A-Za-z_0-9]+)*(?:\([\w=, ."'-]{0,55}\))?|\b\d+(?:\.\d+)?\b|(?:没有|缺少|省略|遗漏|未执行|未提供|仍为|变为)[^，。；：]{2,18}/g;
    let cursor=0, count=0;
    const contextStart=value.indexOf('本题的关键要求');
    const focus=contextStart<0?value:value.slice(0,contextStart);
    for(const match of focus.matchAll(pattern)){
      if(count===6)break;
      if(['BF16','Ours','CoT','GPTQ'].includes(match[0]))continue;
      fragment.append(document.createTextNode(value.slice(cursor,match.index)));
      const mark=document.createElement('mark');mark.textContent=match[0];fragment.append(mark);
      cursor=match.index+match[0].length;count++;
    }
    fragment.append(document.createTextNode(value.slice(cursor)));return fragment;
  }
  function terms(value, phrases){
    const fragment=document.createDocumentFragment();
    const ranges=[];
    for(const phrase of [...phrases].sort((a,b)=>b.length-a.length)){
      let from=0,at;
      while((at=value.toLowerCase().indexOf(phrase.toLowerCase(),from))>=0){
        const end=at+phrase.length;
        if(!ranges.some(([a,b])=>at<b&&end>a))ranges.push([at,end]);
        from=end;
      }
    }
    let cursor=0;
    ranges.sort((a,b)=>a[0]-b[0]).forEach(([a,b])=>{
      fragment.append(document.createTextNode(value.slice(cursor,a)));
      const mark=document.createElement('mark');mark.textContent=value.slice(a,b);fragment.append(mark);cursor=b;
    });fragment.append(document.createTextNode(value.slice(cursor)));return fragment;
  }
  window.EvidenceHighlight={difference,prose,terms};
})();
