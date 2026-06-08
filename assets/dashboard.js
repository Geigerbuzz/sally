/* =========================================================================
   Dashboard — SDG Command Center
   · default widget set built from the Sally corpus + metrics
   · drag-and-drop grid + auto-arrange (ported from Davlon)
   · "add widget" FAB with an offline, SDG-aware prompt → widget generator
   ========================================================================= */
document.addEventListener("DOMContentLoaded", ()=>{
  const grid = document.getElementById("widget-grid");
  if(!grid || !window.Sally || !window.WidgetRenderer) return;

  /* ---- Chart.js global theme ---- */
  if(window.Chart){
    Chart.defaults.font.family = "'Inter',-apple-system,sans-serif";
    Chart.defaults.font.size = 11;
    Chart.defaults.color = getCss("--text-secondary") || "#a1a1a6";
    Chart.defaults.plugins.tooltip.backgroundColor = "rgba(20,20,22,0.92)";
    Chart.defaults.plugins.tooltip.borderColor = "rgba(255,255,255,0.1)";
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    Chart.defaults.plugins.legend.display = false;
    Chart.defaults.maintainAspectRatio = false;
  }

  /* ---- default widget set (the demo's hero content) ---- */
  const ov = Sally.overallScore();
  const m  = Sally.metrics;
  const sdg = n => Sally.sdg(n).color;
  const tg = Sally.topGoals(6);

  const DEFAULT = [
    { id:"w-score", template:"kpi-card", dimension:"1x1", title:"Overall SDG score", clickable:true, href:"sally-sdg-compliance.html",
      data:{ value:ov.pct, unit:"%", icon:"ri-focus-3-line", accent:getCss("--accent"), trend:{dir:"up", val:"+6 YoY"} } },
    { id:"w-covered", template:"kpi-card", dimension:"1x1", title:"Goals with evidence", clickable:true, href:"sally-sdg-compliance.html",
      data:{ value:ov.covered, unit:"/17", icon:"ri-checkbox-circle-line", accent:getCss("--good") } },
    { id:"w-gaps", template:"kpi-card", dimension:"1x1", title:"Coverage gaps", clickable:true, href:"sally-sdg-compliance.html",
      data:{ value:ov.gaps, icon:"ri-error-warning-line", accent:getCss("--bad"), trend:{dir:"down", val:"close these"} } },
    { id:"w-docs", template:"kpi-card", dimension:"1x1", title:"Documents assessed", clickable:true, href:"sally-documents.html",
      data:{ value:Sally.DOCS.length, icon:"ri-file-list-3-line", accent:getCss("--info") } },

    { id:"w-gauge", template:"gauge", dimension:"2x2", title:"SDG compliance", pct:ov.pct, label:"Overall",
      color:getCss("--accent"), clickable:true, href:"sally-sdg-compliance.html", corner:"ri-arrow-right-up-line" },

    { id:"w-sdggrid", template:"sdg-grid", dimension:"2x2", title:"The 17 goals · coverage", corner:"ri-grid-line" },

    { id:"w-emissions", template:"line-chart", dimension:"2x1", title:"Scope 1–2 emissions (tCO₂e)",
      foot:`<i class="ri-arrow-down-line" style="color:var(--good)"></i> 27% below 2019 · target net-zero ${m.emissions.targetYear}`,
      data:{ labels:m.emissions.years, datasets:[{ label:"tCO₂e", values:m.emissions.scope12, color:sdg(13) }] } },

    { id:"w-energy", template:"donut-chart", dimension:"2x1", title:"Electricity mix",
      data:{ labels:["Renewables","Grid"], values:[m.energy.renewables, m.energy.grid], colors:[sdg(7), "rgba(140,140,150,0.45)"] } },

    { id:"w-top", template:"bar-chart", dimension:"2x2", title:"Top SDGs by coverage",
      data:{ horizontal:true, labels:tg.map(x=>x.g.short),
             datasets:[{ label:"Coverage %", values:tg.map(x=>x.sc.pct), colors:tg.map(x=>x.g.color) }] } },

    { id:"w-gaplist", template:"gap-list", dimension:"1x2", title:"Coverage gaps", corner:"ri-alert-line" },
    { id:"w-recent", template:"doc-list", dimension:"1x2", title:"Recent documents", count:6, corner:"ri-time-line" },

    { id:"w-ask", template:"ask-box", dimension:"2x1", title:"Ask Sally", corner:"ri-sparkling-2-line" }
  ];

  function custom(){ try{ return (Sally.store.loadDash()||{}).custom || []; }catch(e){ return []; } }
  function addCustom(p){ try{ const d=Sally.store.loadDash()||{}; d.custom=(d.custom||[]).concat([p]); Sally.store.saveDash(d); }catch(e){} }

  function renderAll(){
    grid.innerHTML = "";
    DEFAULT.forEach(p => grid.appendChild(WidgetRenderer.render(p)));
    custom().forEach(p => grid.appendChild(WidgetRenderer.render(p)));   // AI-added widgets persist across sessions
    WidgetRenderer.flush();
  }
  renderAll();

  /* ============ drag & drop engine (ported from Davlon) ============ */
  const COL=160, GAP=24, CELL=COL+GAP;
  let dragged=null, offX=0, offY=0;

  function spanOf(el){
    if(el.classList.contains("w-2x2")) return [2,2];
    if(el.classList.contains("w-2x3")) return [2,3];
    if(el.classList.contains("w-3x2")) return [3,2];
    if(el.classList.contains("w-1x2")) return [1,2];
    if(el.classList.contains("w-2x1")) return [2,1];
    return [1,1];
  }

  grid.addEventListener("dragstart", e=>{
    const w = e.target.closest(".widget"); if(!w) return;
    dragged = w; const r=w.getBoundingClientRect();
    offX=e.clientX-r.left; offY=e.clientY-r.top;
    w.classList.add("dragging"); e.dataTransfer.effectAllowed="move";
  });
  grid.addEventListener("dragend", e=>{ if(dragged){ dragged.classList.remove("dragging"); dragged=null; } });
  grid.addEventListener("dragover", e=>{ e.preventDefault(); e.dataTransfer.dropEffect="move"; });
  grid.addEventListener("drop", e=>{
    e.preventDefault(); if(!dragged) return;
    const gr=grid.getBoundingClientRect();
    const x=e.clientX-gr.left+grid.scrollLeft-offX, y=e.clientY-gr.top+grid.scrollTop-offY;
    const [sc,sr]=spanOf(dragged);
    let col=Math.max(1, Math.round(x/CELL)+1), row=Math.max(1, Math.round(y/CELL)+1);
    dragged.style.gridColumn=`${col} / span ${sc}`;
    dragged.style.gridRow=`${row} / span ${sr}`;
  });

  /* ============ auto-arrange (dense pack) ============ */
  function autoArrange(){
    const ws=[...grid.querySelectorAll(".widget")];
    ws.sort((a,b)=>{ const [ac,ar]=spanOf(a),[bc,br]=spanOf(b); return (bc*br)-(ac*ar); });
    ws.forEach(w=>{ w.style.gridColumn=""; w.style.gridRow=""; grid.appendChild(w); });
    grid.style.gridAutoFlow="dense";
    setTimeout(()=>{ lock(); grid.style.gridAutoFlow=""; }, 80);
  }
  function lock(){
    const gr=grid.getBoundingClientRect();
    grid.querySelectorAll(".widget").forEach(w=>{
      const r=w.getBoundingClientRect();
      let col=Math.max(1, Math.round((r.left-gr.left+grid.scrollLeft)/CELL)+1);
      let row=Math.max(1, Math.round((r.top-gr.top+grid.scrollTop)/CELL)+1);
      const [sc,sr]=spanOf(w);
      w.style.gridColumn=`${col} / span ${sc}`;
      w.style.gridRow=`${row} / span ${sr}`;
    });
  }
  const arrangeBtn=document.getElementById("auto-arrange");
  if(arrangeBtn) arrangeBtn.addEventListener("click", autoArrange);
  setTimeout(autoArrange, 120);                          // default layout = arranged

  /* ============ add-widget FAB + offline AI modal ============ */
  const fab=document.getElementById("add-widget"), overlay=document.getElementById("ai-overlay");
  if(fab && overlay){
    const input=overlay.querySelector(".ai-input"), genBtn=overlay.querySelector(".ai-generate"),
          closeBtn=overlay.querySelector(".ai-close");
    const openModal=()=>{ overlay.classList.add("active"); fab.style.display="none"; input.value=""; setTimeout(()=>input.focus(),60); };
    const closeModal=()=>{ overlay.classList.remove("active"); fab.style.display="flex"; };
    fab.addEventListener("click", openModal);
    closeBtn.addEventListener("click", closeModal);
    document.addEventListener("keydown", e=>{ if(e.key==="Escape" && overlay.classList.contains("active")) closeModal(); });
    overlay.querySelectorAll(".ai-suggest .chip").forEach(c=> c.addEventListener("click", ()=>{ input.value=c.textContent; }));
    input.addEventListener("keydown", e=>{ if(e.key==="Enter" && !e.shiftKey){ e.preventDefault(); generate(); } });
    genBtn.addEventListener("click", generate);

    async function generate(){
      const prompt=input.value.trim(); if(!prompt) return;
      genBtn.disabled=true; genBtn.innerHTML=`<i class="ri-loader-4-line spin"></i> Generating`;
      let payload=null;
      if(window.Sally.LLM && Sally.LLM.configured()){
        try{ payload = await aiWidget(prompt); }
        catch(e){ console.warn("AI widget generation failed, using offline matcher:", e); }
      } else {
        await new Promise(r=>setTimeout(r,500));         // brief beat for the offline path
      }
      if(!payload) payload = generatePayload(prompt);
      payload.id = payload.id || ("w-gen-"+Date.now());
      const el=WidgetRenderer.render(payload); grid.appendChild(el); WidgetRenderer.flush();
      addCustom(payload);
      genBtn.disabled=false; genBtn.innerHTML=`<i class="ri-sparkling-2-line"></i> Generate`;
      closeModal(); setTimeout(autoArrange, 60);
      el.animate?.([{transform:"scale(.9)",opacity:0},{transform:"scale(1)",opacity:1}],{duration:300,easing:"cubic-bezier(.2,.8,.2,1)"});
    }
  }

  /* ---- DeepSeek-generated widget (grounded in the corpus metrics) ---- */
  async function aiWidget(prompt){
    const ctx = {
      company: Sally.company.name,
      overall: ov,
      metrics: m,
      sdg: Sally.SDG.map(g=>{ const sc=Sally.scoreForGoal(g.n); return {n:g.n, name:g.short, color:g.color, score:sc.pct, status:sc.status}; })
    };
    const sys = `You generate ONE dashboard widget as STRICT JSON for ${Sally.company.name}'s SDG sustainability dashboard. Use ONLY numbers present in DATA — never invent figures. Output a single JSON object and nothing else.
Allowed shapes:
- {"template":"kpi-card","dimension":"1x1","title":str,"data":{"value":num|str,"unit"?:str,"icon"?:"ri-...-line","accent"?:"#hex","trend"?:{"dir":"up|down|flat","val":str}}}
- {"template":"line-chart"|"bar-chart","dimension":"2x1"|"2x2","title":str,"foot"?:str,"data":{"labels":[...],"horizontal"?:bool,"datasets":[{"label":str,"values":[num],"color"?:"#hex","colors"?:["#hex"]}]}}
- {"template":"donut-chart","dimension":"2x1","title":str,"data":{"labels":[...],"values":[num],"colors":["#hex"]}}
- {"template":"gauge","dimension":"2x2","title":str,"pct":num,"label":str,"color"?:"#hex"}
- {"template":"data-table","dimension":"2x2","title":str,"data":{"headers":[...],"rows":[[...]]}}
When showing SDGs, use the matching sdg[].color hex. Choose the shape that best answers the request.`;
    const usr = `DATA:\n${JSON.stringify(ctx)}\n\nREQUEST: ${prompt}\n\nReturn the widget JSON only.`;
    const payload = await Sally.LLM.json([{role:"system",content:sys},{role:"user",content:usr}], {max_tokens:800});
    if(!payload || !payload.template) throw new Error("invalid widget payload");
    return payload;
  }

  /* ---- offline, SDG-aware prompt → widget payload ---- */
  function generatePayload(prompt){
    const p=prompt.toLowerCase();
    const id="w-gen-"+Date.now();
    const has=(...k)=>k.some(w=>p.includes(w));

    if(has("emission","carbon","scope","co2","co₂","footprint"))
      return { id, template:"line-chart", dimension:"2x1", title:"Scope 1–2 emissions (tCO₂e)",
        foot:`<i class="ri-arrow-down-line" style="color:var(--good)"></i> 27% below 2019 baseline`,
        data:{ labels:m.emissions.years, datasets:[{ label:"tCO₂e", values:m.emissions.scope12, color:sdg(13) }] } };

    if(has("energy","renewable","solar","electric"))
      return { id, template:"donut-chart", dimension:"2x1", title:"Electricity mix",
        data:{ labels:["Renewables","Grid"], values:[m.energy.renewables,m.energy.grid], colors:[sdg(7),"rgba(140,140,150,0.45)"] } };

    if(has("safety","injury","incident","ehs"))
      return { id, template:"line-chart", dimension:"2x1", title:"Recordable injury rate /200k hrs",
        foot:`<i class="ri-arrow-down-line" style="color:var(--good)"></i> ${m.safety.dropPct}% lower YoY`,
        data:{ labels:m.safety.years, datasets:[{ label:"Rate", values:m.safety.injuryRate, color:sdg(3) }] } };

    if(has("pay","gender","equity","wage","gap "))
      return { id, template:"line-chart", dimension:"2x1", title:"Adjusted gender pay gap (%)",
        foot:`Narrowed to ${m.payGap.pct.at(-1)}% · ${m.payGap.remediation} remediation`,
        data:{ labels:m.payGap.years, datasets:[{ label:"% gap", values:m.payGap.pct, color:sdg(5) }] } };

    if(has("top","compare","best","ranking","leader"))
      return { id, template:"bar-chart", dimension:"2x2", title:"Top SDGs by coverage",
        data:{ horizontal:true, labels:tg.map(x=>x.g.short),
               datasets:[{ label:"%", values:tg.map(x=>x.sc.pct), colors:tg.map(x=>x.g.color) }] } };

    if(has("gauge","overall","score","compliance"))
      return { id, template:"gauge", dimension:"2x2", title:"SDG compliance", pct:ov.pct, label:"Overall", color:getCss("--accent") };

    if(has("gap","missing","weak","uncovered"))
      return { id, template:"gap-list", dimension:"1x2", title:"Coverage gaps", corner:"ri-alert-line" };

    if(has("recent","latest","new "))
      return { id, template:"doc-list", dimension:"1x2", title:"Recent documents", count:6, corner:"ri-time-line" };

    if(has("table","list","document","file","library","corpus"))
      return { id, template:"data-table", dimension:"2x2", title:"Document corpus",
        data:{ headers:["Document","Type","Goals"],
               rows:Sally.DOCS.slice(0,12).map(d=>[d.name, d.type, d.goals.map(g=>"SDG "+g).join(", ")]) } };

    if(has("diversity","women","management"))
      return { id, template:"kpi-card", dimension:"1x1", title:"Women in management",
        data:{ value:m.people.womenInMgmt, unit:"%", icon:"ri-group-line", accent:sdg(5), trend:{dir:"up", val:`from ${m.people.womenInMgmtPrev}%`} } };

    if(has("partner","collaborat","university"))
      return { id, template:"kpi-card", dimension:"1x1", title:"Active partnerships",
        data:{ value:m.partnerships.active, icon:"ri-links-line", accent:sdg(17) } };

    if(has("waste","circular","recycl"))
      return { id, template:"kpi-card", dimension:"1x1", title:"Waste diverted",
        data:{ value:m.waste.diverted, unit:"%", icon:"ri-recycle-line", accent:sdg(12) } };

    /* match a named SDG → its score gauge */
    const named = Sally.SDG.find(g=> p.includes(g.short.toLowerCase()) || p.includes(("sdg "+g.n)));
    if(named){ const sc=Sally.scoreForGoal(named.n);
      return { id, template:"gauge", dimension:"2x2", title:named.name, pct:sc.pct, label:sc.status, color:named.color }; }

    /* fallback: overall score KPI */
    return { id, template:"kpi-card", dimension:"1x1", title:"Overall SDG score",
      data:{ value:ov.pct, unit:"%", icon:"ri-focus-3-line", accent:getCss("--accent") } };
  }

  function getCss(v){ return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }
});
