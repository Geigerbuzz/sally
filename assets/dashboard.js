/* =========================================================================
   Dashboard — SDG Command Center
   · multiple widget boards (tabs) — add/rename/delete, persisted
   · iOS-style widgets: drag to reflow (others move aside), edit-mode jiggle,
     delete badges
   · "add widget" FAB → DeepSeek (or offline matcher), grounded in the corpus
   ========================================================================= */
document.addEventListener("DOMContentLoaded", ()=>{
  const grid = document.getElementById("widget-grid");
  if(!grid || !window.Sally || !window.WidgetRenderer) return;

  /* ---- Chart.js global theme ---- */
  if(window.Chart){
    Chart.defaults.font.family = "'Helvetica Neue',Helvetica,Arial,sans-serif";
    Chart.defaults.font.size = 11;
    Chart.defaults.color = getCss("--text-secondary") || "#a1a1a6";
    Chart.defaults.plugins.tooltip.backgroundColor = "rgba(20,20,22,0.92)";
    Chart.defaults.plugins.tooltip.borderColor = "rgba(255,255,255,0.1)";
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    Chart.defaults.plugins.legend.display = false;
    Chart.defaults.maintainAspectRatio = false;
    Chart.defaults.animation.duration = 850;
    Chart.defaults.animation.easing = "easeInOutQuart";
  }

  const ov = Sally.overallScore();
  const m  = Sally.metrics;
  const sdg = n => Sally.sdg(n).color;
  const tg = Sally.topGoals(6);
  const TEMPLATES = new Set(["kpi-card","line-chart","bar-chart","donut-chart","gauge","sdg-grid","gap-list","doc-list","ask-box","data-table"]);

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
      foot:`27% below 2019 · target net-zero ${m.emissions.targetYear}`, footIcon:"ri-arrow-down-line", footColor:"var(--good)",
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

  /* ===================== boards (persisted) ===================== */
  const clone = p => JSON.parse(JSON.stringify(p));
  const esc = s => String(s==null?"":s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function seed(){
    return { boards:[
      { id:"b-overview", name:"Overview", widgets: DEFAULT.map(clone) },
      { id:"b-shared",   name:"Shared",   widgets: ["w-gauge","w-sdggrid","w-top","w-ask"].map(id=>clone(DEFAULT.find(p=>p.id===id))) }
    ], active:"b-overview" };
  }
  function load(){
    let d=null; try{ d=Sally.store.loadDash(); }catch(e){}
    if(d && Array.isArray(d.boards) && d.boards.length){
      if(!d.boards.find(b=>b.id===d.active)) d.active=d.boards[0].id;
      return d;
    }
    return seed();
  }
  let state = load();
  const save  = ()=>{ try{ Sally.store.saveDash(state); }catch(e){} };
  const board = ()=> state.boards.find(b=>b.id===state.active) || state.boards[0];
  let editMode = false;

  /* ===================== render ===================== */
  function renderAll(){ renderTabs(); renderWidgets(); }

  function renderTabs(){
    const nav = document.getElementById("board-tabs");
    if(!nav) return;
    nav.innerHTML = state.boards.map(b=>
      `<button class="tab ${b.id===state.active?'active':''}" data-tab="${esc(b.id)}"><span>${esc(b.name)}</span>${
        editMode && state.boards.length>1 ? `<i class="ri-close-circle-fill bt-del" title="Delete board"></i>` : ""}</button>`).join("");
    Sally.mountTabs(nav, id=> switchBoard(id));
    nav.querySelectorAll(".bt-del").forEach(x=> x.addEventListener("click", e=>{
      e.stopPropagation(); deleteBoard(x.closest(".tab").dataset.tab); }));
    nav.querySelectorAll(".tab").forEach(t=> t.addEventListener("dblclick", ()=> renameBoard(t.dataset.tab)));
  }

  function renderWidgets(){
    grid.innerHTML = "";
    const ws = board().widgets;
    ws.forEach((p,i)=>{
      const el = WidgetRenderer.render(p);
      el.dataset.wid = p.id;
      if(!editMode){ el.classList.add("enter"); el.style.animationDelay = (i*0.025)+"s"; }
      if(editMode) addEditChrome(el, p);
      grid.appendChild(el);
    });
    WidgetRenderer.flush();
    grid.classList.toggle("editing", editMode);
    if(!ws.length) grid.insertAdjacentHTML("beforeend",
      `<div class="board-empty">Nothing here yet — tap <b>+</b> below to add a widget.</div>`);
  }

  function addEditChrome(el, p){
    el.style.setProperty("--jd", (-(Math.random()*0.45)).toFixed(2)+"s");   // desync the jiggle
    const del = document.createElement("button");
    del.className = "w-del"; del.type = "button"; del.title = "Remove widget";
    del.innerHTML = '<i class="ri-subtract-line"></i>';
    del.addEventListener("mousedown", e=> e.stopPropagation());
    del.addEventListener("click", e=>{ e.stopPropagation(); e.preventDefault(); removeWidget(p.id); });
    el.appendChild(del);
  }

  /* ===================== board management ===================== */
  function switchBoard(id){ if(id===state.active) return; state.active=id; save(); renderWidgets(); }
  function addBoard(){
    const name = (prompt("Name this board", "New board")||"").trim(); if(!name) return;
    const b = { id:"b-"+Date.now(), name, widgets:[] };
    state.boards.push(b); state.active=b.id; editMode=true; save(); renderAll();
  }
  function renameBoard(id){
    const b = state.boards.find(x=>x.id===id); if(!b) return;
    const name = (prompt("Rename board", b.name)||"").trim(); if(!name) return;
    b.name=name; save(); renderTabs();
  }
  function deleteBoard(id){
    if(state.boards.length<=1) return;
    const b = state.boards.find(x=>x.id===id); if(!b) return;
    if(!confirm(`Delete the “${b.name}” board?`)) return;
    state.boards = state.boards.filter(x=>x.id!==id);
    if(state.active===id) state.active = state.boards[0].id;
    save(); renderAll();
  }
  function removeWidget(id){
    const ws = board().widgets; const i = ws.findIndex(p=>p.id===id); if(i<0) return;
    const el = grid.querySelector('[data-wid="'+CSS.escape(id)+'"]');
    ws.splice(i,1); save();
    if(el && el.animate){ el.style.pointerEvents="none";
      el.animate([{transform:"scale(1)",opacity:1},{transform:"scale(.6)",opacity:0}],{duration:200,easing:"ease"}).onfinish=renderWidgets; }
    else renderWidgets();
  }
  function arrangeBoard(){
    const area = p=>{ const [c,r]=(p.dimension||"1x1").split("x").map(Number); return (c||1)*(r||1); };
    board().widgets.sort((a,b)=> area(b)-area(a)); save(); renderWidgets();
  }

  /* ===================== iOS-style drag reflow (FLIP) ===================== */
  let dragEl=null, lastSig=null;
  function recordRects(){ const map=new Map(); grid.querySelectorAll(".widget").forEach(w=>map.set(w, w.getBoundingClientRect())); return map; }
  function flip(first){
    grid.querySelectorAll(".widget").forEach(w=>{
      if(w===dragEl) return;
      const a=first.get(w); if(!a) return; const b=w.getBoundingClientRect();
      const dx=a.left-b.left, dy=a.top-b.top; if(!dx && !dy) return;
      w.animate([{transform:`translate(${dx}px,${dy}px)`},{transform:"none"}],{duration:260, easing:"cubic-bezier(.2,.8,.2,1)"});
    });
  }
  grid.addEventListener("dragstart", e=>{
    const w=e.target.closest(".widget"); if(!w) return;
    dragEl=w; lastSig=null; w.classList.add("dragging");
    e.dataTransfer.effectAllowed="move"; try{ e.dataTransfer.setData("text/plain", w.dataset.wid); }catch(_){}
  });
  grid.addEventListener("dragend", ()=>{ if(dragEl) dragEl.classList.remove("dragging"); dragEl=null; lastSig=null; syncOrder(); });
  grid.addEventListener("dragover", e=>{
    e.preventDefault(); if(!dragEl) return;
    const over=e.target.closest(".widget"); if(!over || over===dragEl) return;
    const r=over.getBoundingClientRect();
    const after = e.clientY > r.top + r.height*0.5;
    const ref = after ? over.nextElementSibling : over;
    if(ref===dragEl) return;
    const sig = over.dataset.wid+"|"+after; if(sig===lastSig) return; lastSig=sig;
    const first=recordRects();
    grid.insertBefore(dragEl, ref);
    flip(first);
  });
  function syncOrder(){
    const order=[...grid.querySelectorAll(".widget")].map(w=>w.dataset.wid);
    board().widgets.sort((a,b)=> order.indexOf(a.id) - order.indexOf(b.id));
    save();
  }

  /* ===================== header controls ===================== */
  const editBtn = document.getElementById("edit-toggle");
  function setEdit(on){ editMode=on; if(editBtn){ editBtn.classList.toggle("on",on);
    editBtn.innerHTML = on ? '<i class="ri-check-line"></i> Done' : '<i class="ri-edit-2-line"></i> Edit'; } renderAll(); }
  if(editBtn) editBtn.addEventListener("click", ()=> setEdit(!editMode));
  const arrangeBtn = document.getElementById("auto-arrange"); if(arrangeBtn) arrangeBtn.addEventListener("click", arrangeBoard);
  const addBtn = document.getElementById("board-add"); if(addBtn) addBtn.addEventListener("click", addBoard);

  renderAll();

  /* ===================== add-widget FAB + AI modal ===================== */
  const fab=document.getElementById("add-widget"), overlay=document.getElementById("ai-overlay");
  if(fab && overlay){
    const input=overlay.querySelector(".ai-input"), genBtn=overlay.querySelector(".ai-generate"), closeBtn=overlay.querySelector(".ai-close");
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
        try{ payload = await aiWidget(prompt); }catch(e){ console.warn("AI widget failed, using offline matcher:", e); }
      } else { await new Promise(r=>setTimeout(r,500)); }
      if(!payload) payload = generatePayload(prompt);
      payload.id = "w-gen-"+Date.now();
      try{
        board().widgets.push(payload); save();
        renderWidgets();
        const el = grid.querySelector('[data-wid="'+CSS.escape(payload.id)+'"]');
        el?.scrollIntoView?.({behavior:"smooth", block:"nearest"});
      }catch(e){ console.warn("render failed:", e); }
      genBtn.disabled=false; genBtn.innerHTML=`<i class="ri-sparkling-2-line"></i> Generate`;
      closeModal();
    }
  }

  async function aiWidget(prompt){
    const ctx = { company:Sally.company.name, overall:ov, metrics:m,
      sdg: Sally.SDG.map(g=>{ const sc=Sally.scoreForGoal(g.n); return {n:g.n, name:g.short, color:g.color, score:sc.pct, status:sc.status}; }) };
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
    if(!payload || !TEMPLATES.has(payload.template)) throw new Error("invalid widget payload");
    return payload;
  }

  /* ---- offline, SDG-aware prompt → widget payload ---- */
  function generatePayload(prompt){
    const p=prompt.toLowerCase();
    const id="w-gen-"+Date.now();
    const has=(...k)=>k.some(w=>p.includes(w));
    if(has("emission","carbon","scope","co2","co₂","footprint"))
      return { id, template:"line-chart", dimension:"2x1", title:"Scope 1–2 emissions (tCO₂e)",
        foot:`27% below 2019 baseline`, footIcon:"ri-arrow-down-line", footColor:"var(--good)",
        data:{ labels:m.emissions.years, datasets:[{ label:"tCO₂e", values:m.emissions.scope12, color:sdg(13) }] } };
    if(has("energy","renewable","solar","electric"))
      return { id, template:"donut-chart", dimension:"2x1", title:"Electricity mix",
        data:{ labels:["Renewables","Grid"], values:[m.energy.renewables,m.energy.grid], colors:[sdg(7),"rgba(140,140,150,0.45)"] } };
    if(has("safety","injury","incident","ehs"))
      return { id, template:"line-chart", dimension:"2x1", title:"Recordable injury rate /200k hrs",
        foot:`${m.safety.dropPct}% lower YoY`, footIcon:"ri-arrow-down-line", footColor:"var(--good)",
        data:{ labels:m.safety.years, datasets:[{ label:"Rate", values:m.safety.injuryRate, color:sdg(3) }] } };
    if(has("pay","gender","equity","wage","gap "))
      return { id, template:"line-chart", dimension:"2x1", title:"Adjusted gender pay gap (%)",
        foot:`Narrowed to ${m.payGap.pct.at(-1)}% · ${m.payGap.remediation} remediation`, footIcon:"ri-arrow-down-line", footColor:"var(--good)",
        data:{ labels:m.payGap.years, datasets:[{ label:"% gap", values:m.payGap.pct, color:sdg(5) }] } };
    if(has("top","compare","best","ranking","leader"))
      return { id, template:"bar-chart", dimension:"2x2", title:"Top SDGs by coverage",
        data:{ horizontal:true, labels:tg.map(x=>x.g.short), datasets:[{ label:"%", values:tg.map(x=>x.sc.pct), colors:tg.map(x=>x.g.color) }] } };
    if(has("gauge","overall","score","compliance"))
      return { id, template:"gauge", dimension:"2x2", title:"SDG compliance", pct:ov.pct, label:"Overall", color:getCss("--accent") };
    if(has("gap","missing","weak","uncovered"))
      return { id, template:"gap-list", dimension:"1x2", title:"Coverage gaps", corner:"ri-alert-line" };
    if(has("recent","latest","new "))
      return { id, template:"doc-list", dimension:"1x2", title:"Recent documents", count:6, corner:"ri-time-line" };
    if(has("table","list","document","file","library","corpus"))
      return { id, template:"data-table", dimension:"2x2", title:"Document corpus",
        data:{ headers:["Document","Type","Goals"], rows:Sally.DOCS.slice(0,12).map(d=>[d.name, d.type, d.goals.map(g=>"SDG "+g).join(", ")]) } };
    if(has("diversity","women","management"))
      return { id, template:"kpi-card", dimension:"1x1", title:"Women in management",
        data:{ value:m.people.womenInMgmt, unit:"%", icon:"ri-group-line", accent:sdg(5), trend:{dir:"up", val:`from ${m.people.womenInMgmtPrev}%`} } };
    if(has("partner","collaborat","university"))
      return { id, template:"kpi-card", dimension:"1x1", title:"Active partnerships",
        data:{ value:m.partnerships.active, icon:"ri-links-line", accent:sdg(17) } };
    if(has("waste","circular","recycl"))
      return { id, template:"kpi-card", dimension:"1x1", title:"Waste diverted",
        data:{ value:m.waste.diverted, unit:"%", icon:"ri-recycle-line", accent:sdg(12) } };
    const named = Sally.SDG.find(g=> p.includes(g.short.toLowerCase()) || p.includes(("sdg "+g.n)));
    if(named){ const sc=Sally.scoreForGoal(named.n);
      return { id, template:"gauge", dimension:"2x2", title:named.name, pct:sc.pct, label:sc.status, color:named.color }; }
    return { id, template:"kpi-card", dimension:"1x1", title:"Overall SDG score",
      data:{ value:ov.pct, unit:"%", icon:"ri-focus-3-line", accent:getCss("--accent") } };
  }

  function getCss(v){ return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }
});
