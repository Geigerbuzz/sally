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

/* shared top nav */
Sally.mountNav = function(active){
  const links = [
    {id:"documents", href:"sally-documents.html",      label:"Documents"},
    {id:"ask",       href:"sally-ask.html",            label:"Ask Sally"},
    {id:"compliance",href:"sally-sdg-compliance.html", label:"Compliance"},
    {id:"graph",     href:"sally-knowledge-graph.html",label:"Graph"},
  ];
  const host = document.getElementById("topbar");
  if(!host) return;
  host.className = "topbar";
  host.innerHTML = `
    <a class="brand" href="index.html" title="Sally home">
      <span class="mark"></span>
      <span class="logo">Sal<b>ly</b></span>
      <span class="sub">${Sally.company.name}</span>
    </a>
    <nav class="nav">
      ${links.map(l=>`<a href="${l.href}" class="${l.id===active?'active':''}">${l.label}</a>`).join("")}
    </nav>
    <span class="spacer"></span>
    ${host.dataset.actions||""}
  `;
};
