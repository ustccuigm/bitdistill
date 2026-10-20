(() => {
  'use strict';
  const models = ['Qwen3-8B', 'Qwen3.5-4B', 'Gemma 4 12B-it'];
  const methods = ['BF16', 'GPTQ', 'EfficientQAT', 'BitDistiller', 'On-Policy QAD', 'QeRL', 'Ours'];
  const colors = ['#9da3a6', '#829bab', '#b7a47c', '#a29aa9', '#739c96', '#c0957b', '#a33a31'];
  const metrics = {
    average: ['Average benchmark score (%)', 'Mean score across the five benchmarks in Table 1.', 40, 70],
    bfcl_v4: ['BFCL V4 score (%)', 'BFCL V4 results from Table 1.', 35, 70],
    tau2_bench: ['τ²-Bench score (%)', 'τ²-Bench results from Table 1.', 20, 70],
    webshop: ['WebShop score (%)', 'WebShop results from Table 1.', 55, 80],
    alfworld: ['ALFWorld score (%)', 'ALFWorld results from Table 1.', 65, 90],
    search_qa: ['Search QA score (%)', 'Search QA results from Table 1.', 30, 50],
  };
  const tabs = [...document.querySelectorAll('[data-metric]')];
  const host = document.getElementById('native-chart');
  if (!host) return;
  const tooltip = document.getElementById('chart-tooltip');
  const status = document.getElementById('chart-status');
  let rows;
  let active = 'average';
  function node(tag, attrs = {}, text) {
    const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, value));
    if (text !== undefined) el.textContent = text;
    return el;
  }
  function hideTip() { tooltip.hidden = true; }
  function showTip(bar, model, method, value, event) {
    tooltip.textContent = `${model} · ${method}: ${value.toFixed(2)}%`;
    tooltip.hidden = false;
    const rect = bar.getBoundingClientRect();
    const x = event?.clientX ?? rect.x + rect.width / 2;
    const y = event?.clientY ?? rect.y;
    tooltip.style.left = `${Math.max(8, Math.min(x - tooltip.offsetWidth / 2, innerWidth - tooltip.offsetWidth - 8))}px`;
    tooltip.style.top = `${Math.max(8, y - tooltip.offsetHeight - 12)}px`;
  }
  function render() {
    if (!rows) return;
    hideTip();
    const [label, caption, low, high] = metrics[active];
    document.getElementById('chart-metric').textContent = label;
    document.getElementById('chart-caption').textContent = caption;
    const svg = node('svg', {viewBox: '0 0 1080 342', role: 'group', 'aria-label': `${label}; three models; axis ${low} to ${high}`});
    svg.append(node('title', {}, label));
    const top = 62, bottom = 302, panelWidth = 322, gap = 24, left = 44;
    const y = value => bottom - (value - low) / (high - low) * (bottom - top);
    models.forEach((model, m) => {
      const start = left + m * (panelWidth + gap);
      svg.append(node('text', {x: start + panelWidth / 2, y: 30, 'text-anchor': 'middle', class: 'chart-model'}, model));
      for (let tick = low; tick <= high; tick += 5) {
        svg.append(node('line', {x1: start, x2: start + panelWidth, y1: y(tick), y2: y(tick), class: 'chart-grid'}));
        if (m === 0) svg.append(node('text', {x: start - 12, y: y(tick) + 4, 'text-anchor': 'end', class: 'chart-tick'}, tick));
      }
      svg.append(node('path', {d: `M ${start-10} ${bottom+4} l 4 -8 l 4 8 l 4 -8`, class: 'chart-break'}));
      methods.forEach((method, i) => {
        const value = rows.find(row => row.model === model && row.method === method)[active];
        const x = start + 13 + i * 44;
        const bar = node('rect', {x, y: y(value), width: 29, height: bottom-y(value), fill: colors[i], tabindex: 0,
          role: 'img', 'aria-label': `${model}, ${method}, ${value.toFixed(2)} percent`,
          class: 'chart-bar', 'data-model': model, 'data-method': method, 'data-value': value});
        bar.addEventListener('pointerenter', e => showTip(bar, model, method, value, e));
        bar.addEventListener('pointermove', e => showTip(bar, model, method, value, e));
        bar.addEventListener('pointerleave', hideTip);
        bar.addEventListener('focus', () => showTip(bar, model, method, value));
        bar.addEventListener('blur', hideTip);
        bar.addEventListener('keydown', e => { if (e.key === 'Escape') hideTip(); });
        svg.append(bar);
        svg.append(node('text', {x: x + 14.5, y: y(value)-9, 'text-anchor': 'middle', class: method === 'Ours' ? 'chart-value ours' : 'chart-value'}, value.toFixed(2)));
      });
    });
    host.replaceChildren(svg);
  }
  function select(tab) {
    active = tab.dataset.metric;
    tabs.forEach(button => { button.setAttribute('aria-selected', String(button === tab)); button.tabIndex = button === tab ? 0 : -1; });
    document.getElementById('result-panel').setAttribute('aria-labelledby', tab.id);
    render();
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => select(tab));
    tab.addEventListener('keydown', e => {
      const positions = {ArrowRight: (index+1)%tabs.length, ArrowLeft: (index+tabs.length-1)%tabs.length, Home: 0, End: tabs.length-1};
      if (!(e.key in positions)) return;
      e.preventDefault(); const target = tabs[positions[e.key]]; select(target); target.focus();
    });
  });
  const legend = document.getElementById('chart-legend');
  methods.forEach((method, i) => {
    const item = document.createElement('span');
    if (method === 'Ours') item.className = 'ours';
    const swatch = document.createElement('i'); swatch.style.backgroundColor = colors[i]; swatch.setAttribute('aria-hidden', 'true');
    item.append(swatch, document.createTextNode(method)); legend.append(item);
  });
  document.querySelector('.result-chart').addEventListener('scroll', hideTip);
  window.addEventListener('scroll', hideTip, {passive: true});
  window.addEventListener('resize', hideTip);
  fetch('experiments/data/results-chart.json').then(response => {
    if (!response.ok) throw new Error('Results unavailable');
    return response.json();
  }).then(data => {
    if (!Array.isArray(data) || data.length !== 21) throw new Error('Invalid result rows');
    for (const model of models) for (const method of methods) {
      const matches = data.filter(row => row.model === model && row.method === method);
      if (matches.length !== 1) throw new Error('Missing or duplicate method');
      for (const [metric, [, , low, high]] of Object.entries(metrics)) {
        const value = matches[0][metric];
        if (!Number.isFinite(value) || value < low || value > high) throw new Error('Invalid score');
      }
    }
    rows = data; status.hidden = true; render();
  }).catch(() => { status.textContent = 'Results could not be loaded. View the table data below.'; })
    .finally(() => document.querySelector('.result-chart').setAttribute('aria-busy', 'false'));
})();
