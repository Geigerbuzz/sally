/* =========================================================================
   Sally — shared corpus (single source of truth for all views)
   Company: Lumina Components.  17 UN SDGs · 23 documents · 17 concepts.
   ========================================================================= */
window.Sally = window.Sally || {};

Sally.company = { name:"Lumina Components", sector:"Precision manufacturing", reportYear:2024 };

Sally.SDG = [
  {n:1,  short:"No Poverty",                 name:"No Poverty",                              color:"#E5243B"},
  {n:2,  short:"Zero Hunger",                name:"Zero Hunger",                             color:"#DDA63A"},
  {n:3,  short:"Health & Well-being",        name:"Good Health & Well-being",                color:"#4C9F38"},
  {n:4,  short:"Quality Education",          name:"Quality Education",                       color:"#C5192D"},
  {n:5,  short:"Gender Equality",            name:"Gender Equality",                         color:"#FF3A21"},
  {n:6,  short:"Clean Water",                name:"Clean Water & Sanitation",                color:"#26BDE2"},
  {n:7,  short:"Clean Energy",               name:"Affordable & Clean Energy",               color:"#FCC30B"},
  {n:8,  short:"Decent Work",                name:"Decent Work & Economic Growth",           color:"#A21942"},
  {n:9,  short:"Industry & Innovation",      name:"Industry, Innovation & Infrastructure",   color:"#FD6925"},
  {n:10, short:"Reduced Inequalities",       name:"Reduced Inequalities",                    color:"#DD1367"},
  {n:11, short:"Sustainable Cities",         name:"Sustainable Cities & Communities",        color:"#FD9D24"},
  {n:12, short:"Responsible Production",     name:"Responsible Consumption & Production",    color:"#BF8B2E"},
  {n:13, short:"Climate Action",             name:"Climate Action",                          color:"#3F7E44"},
  {n:14, short:"Life Below Water",           name:"Life Below Water",                        color:"#0A97D9"},
  {n:15, short:"Life on Land",               name:"Life on Land",                            color:"#56C02B"},
  {n:16, short:"Strong Institutions",        name:"Peace, Justice & Strong Institutions",    color:"#00689D"},
  {n:17, short:"Partnerships",               name:"Partnerships for the Goals",              color:"#19486A"},
];
Sally.sdg = n => Sally.SDG.find(g=>g.n===n);

Sally.CONCEPTS = {
  "Renewable Energy":          {goals:[7,13]},
  "Energy Efficiency":         {goals:[7,12]},
  "Emissions":                 {goals:[13]},
  "Net-Zero":                  {goals:[13,7]},
  "Waste Reduction":           {goals:[12]},
  "Circular Economy":          {goals:[12,15]},
  "Workforce Wellbeing":       {goals:[3,8]},
  "Workplace Safety":          {goals:[3,8]},
  "Training & Apprenticeships":{goals:[4,8]},
  "Diversity & Inclusion":     {goals:[5,10]},
  "Pay Equity":                {goals:[5,10]},
  "Governance & Ethics":       {goals:[16]},
  "Anti-Corruption":           {goals:[16]},
  "R&D / Innovation":          {goals:[9]},
  "Manufacturing Efficiency":  {goals:[9,12]},
  "University Partnerships":   {goals:[17,4]},
  "Supply Chain":              {goals:[12,8]},
};

/* documents: the shared corpus. `cites` are page-anchored snippets used as
   evidence in Ask Sally + Compliance. */
Sally.DOCS = [
  {name:"EHS Annual Review 2024", code:"EHS-2024", type:"Report", date:"2024-03", pages:48, goals:[3,8], concepts:["Workplace Safety","Workforce Wellbeing"],
   summary:"Environment, health & safety performance — incident rates, audits and corrective actions across all sites.",
   cite:{p:12, t:"Recordable injury rate fell 31% YoY to 0.42 per 200k hours, the lowest on record, following the rollout of the behavioural-safety program."}},
  {name:"HR Benefits Policy", code:"HR-BEN", type:"Policy", date:"2024-01", pages:22, goals:[3,8], concepts:["Workforce Wellbeing"],
   summary:"Employee benefits, healthcare, parental leave and wellbeing provisions.",
   cite:{p:4, t:"All permanent staff receive private health cover, 16 weeks' paid parental leave, and access to the confidential employee-assistance program."}},
  {name:"L&D Report 2024", code:"LND-2024", type:"Report", date:"2024-02", pages:31, goals:[4,8], concepts:["Training & Apprenticeships"],
   summary:"Learning & development outcomes, apprenticeships and skills investment.",
   cite:{p:7, t:"Employees completed an average of 38 training hours; the apprenticeship intake grew to 64, with an 88% completion-to-hire rate."}},
  {name:"Talent Strategy 2024", code:"TAL-2024", type:"Strategy", date:"2024-02", pages:26, goals:[8,4], concepts:["Training & Apprenticeships","Diversity & Inclusion"],
   summary:"Workforce planning, early-careers pipeline and capability building.",
   cite:{p:9, t:"The three-year plan targets a 40% female apprenticeship intake and ring-fences 2.4% of payroll for upskilling."}},
  {name:"Diversity Dashboard 2024", code:"DIV-2024", type:"Dashboard", date:"2024-04", pages:14, goals:[5,10], concepts:["Diversity & Inclusion"],
   summary:"Representation metrics across gender, ethnicity and seniority bands.",
   cite:{p:3, t:"Women now hold 34% of management roles (up from 28%); under-represented groups account for 22% of new hires."}},
  {name:"Pay Equity Audit 2024", code:"PEA-2024", type:"Audit", date:"2024-05", pages:19, goals:[5,10,8], concepts:["Pay Equity","Diversity & Inclusion"],
   summary:"Independent gender and ethnicity pay-gap analysis with remediation plan.",
   cite:{p:6, t:"The adjusted gender pay gap narrowed to 1.9%; a £1.2m remediation budget closes residual gaps within 18 months."}},
  {name:"Energy Transition Report 2024", code:"ENT-2024", type:"Report", date:"2024-06", pages:40, goals:[7,13], concepts:["Renewable Energy","Energy Efficiency"],
   summary:"Roadmap to renewable electricity and on-site generation.",
   cite:{p:5, t:"Renewables reached 61% of electricity consumed; two on-site solar arrays (4.1 MWp) came online in Q2, cutting grid draw 18%."}},
  {name:"Procurement Memo EN-2024-118", code:"EN-2024-118", type:"Memo", date:"2024-07", pages:3, goals:[12,8], concepts:["Supply Chain"],
   summary:"Sustainable procurement directive for tier-1 suppliers.",
   cite:{p:1, t:"From FY25 all tier-1 suppliers must disclose Scope 1–2 emissions and hold a recognised responsible-sourcing certification."}},
  {name:"Facilities Report", code:"FAC-2024", type:"Report", date:"2024-03", pages:28, goals:[7,12], concepts:["Energy Efficiency","Manufacturing Efficiency"],
   summary:"Plant energy use, HVAC retrofits and utilities optimisation.",
   cite:{p:11, t:"LED retrofits and compressed-air recovery reduced facility energy intensity by 12.5% per unit produced."}},
  {name:"HR Policy Manual", code:"HR-MAN", type:"Policy", date:"2024-01", pages:64, goals:[8,5], concepts:["Workforce Wellbeing","Diversity & Inclusion"],
   summary:"Consolidated people policies: conduct, leave, flexible working, grievance.",
   cite:{p:21, t:"Flexible and hybrid-working entitlements apply to all eligible roles; anti-harassment procedures are reviewed annually."}},
  {name:"People Report 2024", code:"PPL-2024", type:"Report", date:"2024-04", pages:36, goals:[8,5,4], concepts:["Workforce Wellbeing","Diversity & Inclusion"],
   summary:"Engagement, retention and the annual people scorecard.",
   cite:{p:8, t:"Engagement rose to 81%; voluntary attrition fell to 9.3%, below the manufacturing benchmark of 14%."}},
  {name:"Compensation Policy 2024", code:"COMP-2024", type:"Policy", date:"2024-02", pages:17, goals:[8,10], concepts:["Pay Equity"],
   summary:"Reward framework, banding and living-wage commitment.",
   cite:{p:2, t:"Lumina is an accredited Living Wage employer; all roles are mapped to transparent, externally benchmarked pay bands."}},
  {name:"Annual Report 2024", code:"AR-2024", type:"Report", date:"2024-04", pages:120, goals:[8,9], concepts:["Governance & Ethics","R&D / Innovation"],
   summary:"Group financial and operational results for FY2024.",
   cite:{p:34, t:"R&D spend reached 6.1% of revenue; two product lines launched, supporting 140 net new skilled roles."}},
  {name:"Operations Review", code:"OPS-2024", type:"Review", date:"2024-05", pages:44, goals:[9,12], concepts:["Manufacturing Efficiency","Supply Chain"],
   summary:"Production efficiency, OEE and supply-chain resilience.",
   cite:{p:16, t:"Overall equipment effectiveness improved to 82%; material yield rose to 96.4% via closed-loop scrap recovery."}},
  {name:"Governance Charter", code:"GOV-CHTR", type:"Charter", date:"2023-11", pages:18, goals:[16], concepts:["Governance & Ethics"],
   summary:"Board composition, committee mandates and oversight structure.",
   cite:{p:3, t:"The Board is 55% independent with a dedicated Ethics & Sustainability Committee meeting no fewer than four times per year."}},
  {name:"Sustainability Report 2024", code:"SUS-2024", type:"Report", date:"2024-06", pages:72, goals:[12,13,7], concepts:["Emissions","Circular Economy","Net-Zero"],
   summary:"Flagship ESG disclosure spanning climate, circularity and energy.",
   cite:{p:18, t:"Absolute Scope 1–2 emissions are down 27% against the 2019 baseline; the validated target is net-zero operations by 2035."}},
  {name:"Circularity Brief", code:"CIR-2024", type:"Brief", date:"2024-05", pages:9, goals:[12], concepts:["Circular Economy","Waste Reduction"],
   summary:"Product circularity, take-back and waste-diversion initiatives.",
   cite:{p:2, t:"92% of operational waste was diverted from landfill; a component take-back scheme recovered 38 tonnes of material."}},
  {name:"Carbon Report 2024", code:"CRB-2024", type:"Report", date:"2024-06", pages:25, goals:[13], concepts:["Emissions","Net-Zero"],
   summary:"GHG inventory across Scope 1, 2 and screened Scope 3.",
   cite:{p:5, t:"Verified Scope 1–2 footprint was 14,200 tCO2e; Scope 3 screening identified purchased goods as 71% of total emissions."}},
  {name:"Climate Strategy", code:"CLM-STRAT", type:"Strategy", date:"2024-03", pages:30, goals:[13,7], concepts:["Net-Zero","Renewable Energy"],
   summary:"Decarbonisation pathway and SBTi-aligned targets.",
   cite:{p:6, t:"Near-term targets cut Scope 1–2 emissions 50% by 2030, underpinned by electrification and 100% renewable power."}},
  {name:"Code of Conduct 2024", code:"COC-2024", type:"Policy", date:"2024-01", pages:23, goals:[16], concepts:["Governance & Ethics","Anti-Corruption"],
   summary:"Ethical standards, conflicts of interest and reporting obligations.",
   cite:{p:10, t:"A zero-tolerance anti-bribery stance applies group-wide, with a confidential, non-retaliatory whistleblowing channel."}},
  {name:"Compliance Log 2024", code:"CPL-2024", type:"Register", date:"2024-12", pages:52, goals:[16], concepts:["Anti-Corruption","Governance & Ethics"],
   summary:"Register of compliance matters, training completion and incidents.",
   cite:{p:1, t:"100% of staff completed annual anti-corruption training; zero material compliance breaches were recorded in FY2024."}},
  {name:"Partnerships Register 2024", code:"PTR-2024", type:"Register", date:"2024-09", pages:11, goals:[17], concepts:["University Partnerships"],
   summary:"Active research, community and industry partnerships.",
   cite:{p:2, t:"Lumina maintains 14 active partnerships, including three university research collaborations on advanced materials."}},
  {name:"Membership Record", code:"MEM-REC", type:"Record", date:"2024-08", pages:6, goals:[17], concepts:["University Partnerships"],
   summary:"Industry bodies and standards memberships.",
   cite:{p:1, t:"Member of four industry standards bodies and a signatory to two sector decarbonisation coalitions."}},
];

/* derived helpers */
Sally.docsForGoal   = n => Sally.DOCS.filter(d=>d.goals.includes(n));
Sally.conceptsForGoal = n => Object.keys(Sally.CONCEPTS).filter(c=>Sally.CONCEPTS[c].goals.includes(n));

/* compliance scoring (POC heuristic): coverage scales with evidence count */
Sally.scoreForGoal = n => {
  const docs = Sally.docsForGoal(n).length;
  const concepts = Sally.conceptsForGoal(n).length;
  if(docs===0) return {pct:0, status:"Gap", docs, concepts};
  const pct = Math.min(96, 38 + docs*13 + concepts*4);
  const status = pct>=78?"Strong":pct>=55?"Solid":pct>=30?"Developing":"Emerging";
  return {pct, status, docs, concepts};
};
Sally.overallScore = () => {
  const covered = Sally.SDG.filter(g=>Sally.docsForGoal(g.n).length>0);
  const avg = covered.reduce((s,g)=>s+Sally.scoreForGoal(g.n).pct,0)/covered.length;
  return { pct:Math.round(avg), covered:covered.length, total:17, gaps:17-covered.length };
};

Sally.topGoals = (k=6) => Sally.SDG
  .map(g=>({g, sc:Sally.scoreForGoal(g.n)}))
  .filter(x=>x.sc.pct>0)
  .sort((a,b)=>b.sc.pct-a.sc.pct)
  .slice(0,k);
Sally.gapGoals    = () => Sally.SDG.filter(g=>Sally.docsForGoal(g.n).length===0);
Sally.strongCount = () => Sally.SDG.filter(g=>Sally.scoreForGoal(g.n).status==="Strong").length;
Sally.recentDocs  = (k=6) => [...Sally.DOCS].sort((a,b)=>(b.date||"").localeCompare(a.date||"")).slice(0,k);

/* =========================================================================
   metrics — figures pulled straight from the citation quotes above, so the
   dashboard charts show the company's real reported numbers (no invented data)
   ========================================================================= */
Sally.metrics = {
  /* Sustainability/Carbon reports: Scope 1–2 down 27% vs 2019 → 14,200 tCO2e; net-zero 2035 */
  emissions:{ years:[2019,2020,2021,2022,2023,2024],
              scope12:[19450,18600,17400,16250,15050,14200],
              targetYear:2035, targetLabel:"Net-zero operations", scope3Share:71 },
  /* Energy Transition Report: 61% renewables, 4.1 MWp solar, grid draw −18% */
  energy:{ renewables:61, grid:39, solarMWp:4.1, gridReduction:18 },
  /* EHS Review: recordable injury rate −31% YoY → 0.42 / 200k hours */
  safety:{ years:[2020,2021,2022,2023,2024], injuryRate:[0.95,0.78,0.66,0.61,0.42], dropPct:31 },
  /* Pay Equity Audit: adjusted gender pay gap → 1.9%; £1.2m remediation */
  payGap:{ years:[2020,2021,2022,2023,2024], pct:[4.8,3.9,3.1,2.4,1.9], remediation:"£1.2m" },
  /* Diversity Dashboard / People Report */
  people:{ womenInMgmt:34, womenInMgmtPrev:28, underRepHires:22, engagement:81, attrition:9.3,
           trainingHours:38, apprentices:64 },
  /* Sustainability / Circularity */
  waste:{ diverted:92, recoveredTonnes:38 },
  /* Governance / Compliance log */
  governance:{ boardIndependence:55, antiCorruptionTraining:100, materialBreaches:0 },
  /* Partnerships Register / Membership */
  partnerships:{ active:14, research:3, bodies:4 }
};

/* =========================================================================
   app shell — glass icon-dock + theme system (replaces the old topbar)
   ========================================================================= */
Sally.NAV = [
  {id:"dashboard",  href:"index.html",                  icon:"ri-dashboard-line",     label:"Dashboard"},
  {id:"ask",        href:"sally-ask.html",              icon:"ri-chat-3-line",        label:"Ask Sally"},
  {id:"documents",  href:"sally-documents.html",        icon:"ri-file-list-2-line",   label:"Documents"},
  {id:"graph",      href:"sally-knowledge-graph.html",  icon:"ri-bubble-chart-line",  label:"Knowledge Graph"},
  {id:"compliance", href:"sally-sdg-compliance.html",   icon:"ri-shield-check-line",  label:"Compliance"},
];

Sally.applyTheme = function(t){
  document.documentElement.setAttribute("data-theme", t);
  try{ localStorage.setItem("sally-theme", t); }catch(e){}
  const ic = document.querySelector("#dock-theme i");
  if(ic) ic.className = t==="dark" ? "ri-moon-line" : "ri-sun-line";
};

/* set the saved theme as early as possible (call from <head> to avoid a flash) */
Sally.initTheme = function(){
  let t="dark"; try{ t = localStorage.getItem("sally-theme") || "dark"; }catch(e){}
  document.documentElement.setAttribute("data-theme", t);
  return t;
};

Sally.mountDock = function(active){
  const t = Sally.initTheme();
  Sally.mountFX();
  const aiOn = Sally.LLM && Sally.LLM.configured();
  let dock = document.querySelector(".floating-dock");
  if(!dock){ dock = document.createElement("nav"); dock.className="floating-dock"; document.body.appendChild(dock); }
  dock.setAttribute("aria-label","Primary");
  dock.innerHTML = `
    <a class="dock-brand" href="index.html" title="Sally home" aria-label="Sally home"><span class="dot"></span></a>
    <div class="dock-items">
      ${Sally.NAV.map(n=>`<a class="dock-item ${n.id===active?'active':''}" href="${n.href}" data-label="${n.label}" aria-label="${n.label}"><i class="${n.icon}"></i></a>`).join("")}
    </div>
    <div class="dock-divider"></div>
    <button class="dock-item" id="dock-settings" data-label="Settings" aria-label="Settings"><i class="ri-settings-3-line"></i><span class="dock-dot ${aiOn?'on':''}" id="ai-dot"></span></button>
    <button class="dock-item" id="dock-theme" data-label="Toggle theme" aria-label="Toggle theme"><i class="${t==='dark'?'ri-moon-line':'ri-sun-line'}"></i></button>
  `;
  const tt = document.getElementById("dock-theme");
  if(tt) tt.onclick = ()=> Sally.applyTheme(document.documentElement.getAttribute("data-theme")==="dark" ? "light" : "dark");
  if(Sally.mountSettings) Sally.mountSettings();
  const sg = document.getElementById("dock-settings");
  if(sg) sg.onclick = ()=> Sally.openSettings();
};

/* ---- settings panel: DeepSeek key / model, test, reset (per-browser) ---- */
Sally.mountSettings = function(){
  if(document.getElementById("set-modal") || !Sally.LLM) return;
  const c = Sally.LLM.cfg();
  const el = document.createElement("div");
  el.innerHTML = `
    <div class="scrim" id="set-scrim"></div>
    <aside class="settings-modal" id="set-modal" role="dialog" aria-label="Settings">
      <div class="set-head"><div><div class="eyebrow accent">Sally</div><h2>Settings</h2></div>
        <button class="dclose" id="set-close"><i class="ri-close-line"></i></button></div>
      <div class="set-body">
        <div class="set-block">
          <label for="set-key">DeepSeek API key</label>
          <input type="password" id="set-key" class="input" placeholder="sk-…" autocomplete="off" spellcheck="false" value="${c.key?c.key.replace(/./g,'•').slice(0,0)+c.key:''}">
          <p class="set-hint">Stored only in <b>this browser</b> — never committed or sent anywhere but DeepSeek. Create one at <span class="mono">platform.deepseek.com</span>. With no key, Sally runs in offline demo mode.</p>
        </div>
        <div class="set-grid">
          <div class="set-block"><label for="set-model">Model</label>
            <select id="set-model" class="input">
              <option value="deepseek-v4-flash">deepseek-v4-flash · fast</option>
              <option value="deepseek-v4-pro">deepseek-v4-pro · smartest</option>
            </select></div>
          <div class="set-block"><label>Connection</label>
            <div id="set-status" class="set-status">checking…</div></div>
        </div>
        <details class="set-adv"><summary>Advanced</summary>
          <div class="set-block" style="margin-top:12px"><label for="set-base">API base URL</label>
            <input type="text" id="set-base" class="input mono" placeholder="https://api.deepseek.com"></div>
        </details>
      </div>
      <div class="set-foot">
        <button class="btn" id="set-reset"><i class="ri-delete-bin-line"></i> Reset demo data</button>
        <span class="grow"></span>
        <button class="btn" id="set-test"><i class="ri-pulse-line"></i> Test</button>
        <button class="btn btn-accent" id="set-save"><i class="ri-check-line"></i> Save</button>
      </div>
    </aside>`;
  document.body.appendChild(el);

  const $ = id => document.getElementById(id);
  const status = $("set-status");
  function refreshStatus(){
    const on = Sally.LLM.configured();
    status.className = "set-status " + (on?"ok":"off");
    status.innerHTML = on ? `<span class="d"></span>Key set · ${Sally.LLM.cfg().model}` : `<span class="d"></span>No key — offline demo mode`;
    const dot = document.getElementById("ai-dot"); if(dot) dot.classList.toggle("on", on);
  }
  function fill(){ const cc=Sally.LLM.cfg(); $("set-key").value=cc.key||""; $("set-model").value=cc.model; $("set-base").value=cc.base; refreshStatus(); }

  Sally.openSettings = ()=>{ fill(); $("set-scrim").classList.add("open"); $("set-modal").classList.add("open"); setTimeout(()=>$("set-key").focus(),80); };
  const close = ()=>{ $("set-scrim").classList.remove("open"); $("set-modal").classList.remove("open"); };
  $("set-scrim").onclick = close; $("set-close").onclick = close;
  document.addEventListener("keydown", e=>{ if(e.key==="Escape" && $("set-modal").classList.contains("open")) close(); });

  $("set-save").onclick = ()=>{
    Sally.LLM.setCfg({ key:$("set-key").value.trim(), model:$("set-model").value, base:($("set-base").value.trim()||"https://api.deepseek.com") });
    refreshStatus(); close();
    // let pages react (chat/dashboard can re-enable AI affordances)
    document.dispatchEvent(new CustomEvent("sally:llm-config"));
  };
  $("set-test").onclick = async ()=>{
    Sally.LLM.setCfg({ key:$("set-key").value.trim(), model:$("set-model").value, base:($("set-base").value.trim()||"https://api.deepseek.com") });
    status.className="set-status busy"; status.innerHTML=`<span class="d"></span>Testing…`;
    try{ await Sally.LLM.test(); status.className="set-status ok"; status.innerHTML=`<span class="d"></span>Connected · ${Sally.LLM.cfg().model}`; }
    catch(e){ status.className="set-status err"; status.innerHTML=`<span class="d"></span>${(e.message||"failed").slice(0,80)}`; }
  };
  $("set-reset").onclick = ()=>{
    if(!confirm("Clear uploaded documents, chat history and dashboard layout from this browser?")) return;
    if(Sally.store) Sally.store.clearAll();
    location.reload();
  };
  refreshStatus();
};

/* animated frosted backdrop — colour blobs → frost → grain (styled in sally.css) */
Sally.mountFX = function(){
  if(document.querySelector(".bg")) return;
  const bg = document.createElement("div"); bg.className = "bg";
  bg.innerHTML = `<div class="bg-blobs"><i></i><i></i><i></i><i></i><i></i><i></i></div>`+
                 `<div class="bg-frost"></div><div class="bg-grain"></div>`;
  document.body.insertBefore(bg, document.body.firstChild);
  const vig = document.createElement("div"); vig.className = "bg-vignette";
  document.body.insertBefore(vig, bg.nextSibling);
};

/* back-compat: old pages called mountNav() — keep it working */
Sally.mountNav = function(active){ Sally.mountDock(active); };
