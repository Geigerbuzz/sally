/* =========================================================================
   WidgetRenderer — turns a widget payload into a themed dashboard widget.
   Templates: kpi-card · line-chart · bar-chart · donut-chart · gauge ·
              sdg-grid · gap-list · doc-list · ask-box · data-table
   Depends on: window.Chart (vendored), window.Sally (corpus.js)
   ========================================================================= */
(function(){
  const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  const pending = [];                                   // chart init callbacks (run after DOM insert)

  const WidgetRenderer = {

    render(p){
      if(!p || !p.template){ return this.error("Invalid widget"); }
      switch(p.template){
        case "kpi-card":   return this.kpi(p);
        case "line-chart":
        case "bar-chart":
        case "donut-chart":return this.chart(p);
        case "gauge":      return this.gauge(p);
        case "sdg-grid":   return this.sdgGrid(p);
        case "gap-list":   return this.gapList(p);
        case "doc-list":   return this.docList(p);
        case "ask-box":    return this.askBox(p);
        case "data-table": return this.table(p);
        default:           return this.error("Unknown widget");
      }
    },

    /* run any deferred chart initializers once widgets are in the DOM */
    flush(){ while(pending.length){ try{ pending.shift()(); }catch(e){ console.warn(e); } } },

    base(p, extra=[]){
      const el = document.createElement("div");
      const dim = p.dimension || "1x1";
      el.className = ["widget", "w-"+dim, ...extra].join(" ");
      el.id = p.id || ("w-"+Math.random().toString(36).slice(2,9));
      el.setAttribute("draggable","true");
      return el;
    },

    head(p){
      return `<div class="w-head"><span class="w-title" title="${esc(p.title||"")}">${esc(p.title||"")}</span>${
        p.corner ? `<i class="${safeIcon(p.corner)} w-corner"></i>` : ""}</div>`;
    },

    /* ---- KPI ---- */
    kpi(p){
      const el = this.base(p, ["kpi", p.clickable?"clickable":""]);
      const d = p.data||{};
      const ac = safeColor(d.accent);
      const icon = d.icon ? `<div class="kpi-icon" style="${ac?`background:${hexSoft(d.accent)};color:${ac}`:""}"><i class="${safeIcon(d.icon)}"></i></div>` : "";
      let trend = "";
      if(d.trend){
        const dir = ({up:"up",down:"down",flat:"flat"})[d.trend.dir] || "flat";
        const ic = dir==="up"?"ri-arrow-up-line":dir==="down"?"ri-arrow-down-line":"ri-subtract-line";
        trend = `<span class="kpi-trend ${dir}"><i class="${ic}"></i>${esc(d.trend.val||"")}</span>`;
      }
      el.innerHTML = `${icon}
        <div class="kpi-value">${esc(d.value)}${d.unit?`<small>${esc(d.unit)}</small>`:""}</div>
        <div class="kpi-label">${esc(p.title||"")}</div>${trend}`;
      if(p.clickable && p.href) el.onclick = ()=> location.href = p.href;
      return el;
    },

    /* ---- charts (line / bar / donut) ---- */
    chart(p){
      const el = this.base(p);
      const cid = "cv-"+Math.random().toString(36).slice(2,9);
      el.innerHTML = `${this.head(p)}<div class="w-canvas"><canvas id="${cid}"></canvas></div>${
        p.foot?`<div class="w-foot">${(p.footIcon||p.footColor)?`<i class="${safeIcon(p.footIcon)}" style="color:${safeColor(p.footColor)||'currentColor'}"></i> `:""}${esc(p.foot)}</div>`:""}`;
      pending.push(()=>{ const cv=document.getElementById(cid); if(cv) this.buildChart(cv, p); });
      return el;
    },

    buildChart(canvas, p){
      const ctx = canvas.getContext("2d");
      const grid = css("--hairline") || "rgba(255,255,255,0.06)";
      const tick = css("--text-tertiary") || "#6e6e73";
      const c = p.data||{};

      if(p.template==="donut-chart"){
        new Chart(ctx,{ type:"doughnut",
          data:{ labels:c.labels, datasets:[{ data:c.values, backgroundColor:c.colors,
            borderColor:css("--bg-surface"), borderWidth:3, hoverOffset:6 }] },
          options:{ responsive:true, maintainAspectRatio:false, cutout:"68%",
            plugins:{ legend:{ display:true, position:"bottom",
              labels:{ boxWidth:8, boxHeight:8, usePointStyle:true, pointStyle:"circle", padding:12,
                color:css("--text-secondary"), font:{family:"'Inter',sans-serif", size:11} } } } } });
        return;
      }

      const isBar = p.template==="bar-chart";
      const horizontal = !!c.horizontal;
      const datasets = (c.datasets||[]).map(ds=>{
        const color = ds.color || css("--accent") || "#0a84ff";
        if(isBar){
          return { label:ds.label, data:ds.values,
            backgroundColor: Array.isArray(ds.colors)? ds.colors : hexSoft(color,0.85),
            borderRadius:6, borderSkipped:false, maxBarThickness:34 };
        }
        // line: gradient fill
        const g = ctx.createLinearGradient(0,0,0,180);
        g.addColorStop(0, hexSoft(color,0.32)); g.addColorStop(1, hexSoft(color,0));
        return { label:ds.label, data:ds.values, borderColor:color, backgroundColor:g,
          borderWidth:2.5, fill:true, tension:0.4, pointRadius:0, pointHoverRadius:5,
          pointBackgroundColor:color };
      });

      new Chart(ctx,{ type:"bar"===p.template.split("-")[0]?"bar":"line",
        data:{ labels:c.labels, datasets },
        options:{ responsive:true, maintainAspectRatio:false,
          indexAxis: horizontal?"y":"x",
          plugins:{ legend:{ display:(datasets.length>1) } },
          scales:{
            x:{ grid:{ display:horizontal, color:grid }, border:{display:false}, ticks:{ color:tick, font:{size:10} } },
            y:{ grid:{ display:!horizontal, color:grid }, border:{display:false}, ticks:{ color:tick, font:{size:10} },
                beginAtZero:!horizontal } } } });
    },

    /* ---- gauge (reused on the Compliance page too) ---- */
    gauge(p){
      const el = this.base(p, [p.clickable?"clickable":""]);
      const pct = Math.max(0, Math.min(100, p.pct||0));
      const r=64, circ=2*Math.PI*r, off=circ*(1-pct/100);
      const gid = "gg-"+Math.random().toString(36).slice(2,8);
      const col = p.color || css("--accent");
      el.innerHTML = `${this.head(p)}
        <div class="gauge-wrap"><div class="gauge">
          <svg width="150" height="150" viewBox="0 0 150 150">
            <circle cx="75" cy="75" r="${r}" fill="none" stroke="rgba(128,128,128,.18)" stroke-width="11"/>
            <circle cx="75" cy="75" r="${r}" fill="none" stroke="url(#${gid})" stroke-width="11" stroke-linecap="round"
              stroke-dasharray="${circ}" stroke-dashoffset="${circ}" transform="rotate(-90 75 75)" class="gring"/>
            <defs><linearGradient id="${gid}" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stop-color="${lighten(col)}"/><stop offset="1" stop-color="${col}"/></linearGradient></defs>
          </svg>
          <div class="pct"><b>${pct}<small>%</small></b><span>${p.label||"Overall"}</span></div>
        </div></div>`;
      pending.push(()=>{ const ring=el.querySelector(".gring"); if(ring){
        requestAnimationFrame(()=>{ ring.style.transition="stroke-dashoffset 1.1s cubic-bezier(.22,.61,.36,1)"; ring.style.strokeDashoffset=off; }); } });
      if(p.clickable && p.href) el.onclick = ()=> location.href = p.href;
      return el;
    },

    /* ---- 17-goal mini grid ---- */
    sdgGrid(p){
      const el = this.base(p, ["clickable"]);
      const tiles = Sally.SDG.map(g=>{
        const gap = Sally.docsForGoal(g.n).length===0;
        return `<div class="g ${gap?"gap":""}" style="background:${g.color}" title="SDG ${g.n}: ${g.name}" data-n="${g.n}">${g.n}</div>`;
      }).join("");
      el.innerHTML = `${this.head(p)}<div class="sdg-mini">${tiles}</div>`;
      el.querySelectorAll(".sdg-mini .g").forEach(t=> t.addEventListener("click",e=>{
        e.stopPropagation(); location.href="sally-sdg-compliance.html?goal="+t.dataset.n; }));
      return el;
    },

    /* ---- coverage gaps ---- */
    gapList(p){
      const el = this.base(p);
      const gaps = Sally.gapGoals();
      const rows = gaps.map(g=>`
        <div class="wrow" data-n="${g.n}">
          <span class="dot" style="background:${css('--bad')}"></span>
          <div class="wr-main"><div class="wr-title">${g.short}</div><div class="wr-sub">SDG ${g.n} · no evidence</div></div>
        </div>`).join("") || `<div class="wr-sub" style="padding:8px">No gaps — every goal has evidence.</div>`;
      el.innerHTML = `${this.head(p)}<div class="wlist">${rows}</div>`;
      el.querySelectorAll(".wrow").forEach(r=> r.addEventListener("click",e=>{
        e.stopPropagation(); location.href="sally-sdg-compliance.html?goal="+r.dataset.n; }));
      return el;
    },

    /* ---- recent documents ---- */
    docList(p){
      const el = this.base(p);
      const docs = Sally.recentDocs(p.count||5);
      const rows = docs.map(d=>`
        <div class="wrow" data-code="${esc(d.code)}">
          <span class="dot" style="background:${(Sally.sdg(d.goals&&d.goals[0])||{}).color||'#888'}"></span>
          <div class="wr-main"><div class="wr-title">${esc(d.name)}</div><div class="wr-sub">${esc(d.type)} · ${esc(d.date)}</div></div>
        </div>`).join("");
      el.innerHTML = `${this.head(p)}<div class="wlist">${rows}</div>`;
      el.querySelectorAll(".wrow").forEach(r=> r.addEventListener("click",e=>{
        e.stopPropagation(); location.href="sally-documents.html#"+r.dataset.code; }));
      return el;
    },

    /* ---- inline Ask Sally ---- */
    askBox(p){
      const el = this.base(p);
      const sg = ["Carbon emissions?","Pay equity?","Workplace safety?"];
      el.innerHTML = `${this.head(p)}
        <div class="askbox">
          <div class="a-row">
            <input type="text" placeholder="Ask about ${Sally.company.name}…" />
            <button class="a-send" title="Ask"><i class="ri-arrow-right-line"></i></button>
          </div>
          <div class="a-suggest">${sg.map(s=>`<span class="chip">${s}</span>`).join("")}</div>
        </div>`;
      const input = el.querySelector("input"), go = ()=>{
        const q = input.value.trim(); location.href="sally-ask.html"+(q?("?q="+encodeURIComponent(q)):""); };
      el.querySelector(".a-send").addEventListener("click", e=>{ e.stopPropagation(); go(); });
      input.addEventListener("keydown", e=>{ if(e.key==="Enter") go(); });
      input.addEventListener("mousedown", e=>e.stopPropagation());
      el.querySelectorAll(".a-suggest .chip").forEach(c=> c.addEventListener("click", e=>{
        e.stopPropagation(); location.href="sally-ask.html?q="+encodeURIComponent(c.textContent.replace("?","")); }));
      return el;
    },

    /* ---- table ---- */
    table(p){
      const el = this.base(p);
      const d = p.data||{};
      el.innerHTML = `${this.head(p)}
        <div class="table-wrap"><table>
          <thead><tr>${(d.headers||[]).map(h=>`<th>${esc(h)}</th>`).join("")}</tr></thead>
          <tbody>${(d.rows||[]).map(r=>`<tr>${(Array.isArray(r)?r:[r]).map(c=>`<td>${esc(c)}</td>`).join("")}</tr>`).join("")}</tbody>
        </table></div>`;
      return el;
    },

    error(msg){
      const el = document.createElement("div");
      el.className="widget w-1x1 kpi"; el.setAttribute("draggable","true");
      el.innerHTML=`<i class="ri-error-warning-line" style="font-size:24px;color:var(--bad)"></i><div class="kpi-label">${msg}</div>`;
      return el;
    }
  };

  /* helpers */
  function esc(s){ return String(s==null?"":s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  function safeIcon(s){ return /^ri-[a-z0-9-]+$/.test(s||"") ? s : "ri-bar-chart-2-line"; }
  function safeColor(s){ return /^(#[0-9a-fA-F]{3,8}|rgba?\([\d.,\s%]+\)|var\(--[a-z0-9-]+\))$/.test(String(s||"").trim()) ? String(s).trim() : ""; }
  function hexSoft(hex, a=0.14){
    if(!hex) return `rgba(10,132,255,${a})`;
    if(hex.startsWith("rgb")) return hex;
    const h=hex.replace("#",""); const n=parseInt(h.length===3?h.split("").map(x=>x+x).join(""):h,16);
    return `rgba(${(n>>16)&255},${(n>>8)&255},${n&255},${a})`;
  }
  function lighten(hex){
    if(!hex||!hex.startsWith("#")) return hex||"#4aa3ff";
    const h=hex.replace("#",""); const n=parseInt(h.length===3?h.split("").map(x=>x+x).join(""):h,16);
    const r=Math.min(255,((n>>16)&255)+40), g=Math.min(255,((n>>8)&255)+40), b=Math.min(255,(n&255)+40);
    return `rgb(${r},${g},${b})`;
  }

  window.WidgetRenderer = WidgetRenderer;
})();
