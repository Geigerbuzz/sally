/* =========================================================================
   Sally — team sessions (group chats around the corpus).
   · Sally.TEAM      — people roster (colour + initials, Discord-style)
   · Sally.SESSIONS  — seeded demo sessions: titles, members, full threads
                       (incl. replies + Sally answers with citations)
   · Sally.Sessions  — helpers: live overlay persistence (Sally.store),
                       custom sessions, avatar rendering
   Load AFTER corpus.js + store.js.
   ========================================================================= */
window.Sally = window.Sally || {};

Sally.TEAM = {
  you:   {id:"you",   name:"You",          role:"Presenter",           color:"#ffd60a", initials:"Y"},
  maya:  {id:"maya",  name:"Maya Chen",    role:"Sustainability Lead", color:"#ff9f0a", initials:"MC"},
  jonas: {id:"jonas", name:"Jonas Weber",  role:"Operations Director", color:"#32d74b", initials:"JW"},
  priya: {id:"priya", name:"Priya Sharma", role:"Compliance Counsel",  color:"#bf5af2", initials:"PS"},
  tom:   {id:"tom",   name:"Tom Okafor",   role:"Head of Procurement", color:"#64d2ff", initials:"TO"},
  elena: {id:"elena", name:"Elena Rossi",  role:"People & Culture",    color:"#ff375f", initials:"ER"},
  sally: {id:"sally", name:"Sally",        role:"AI Analyst",          color:"#0a84ff", initials:"S", ai:true},
};

/* Seeded sessions. Sally message text uses MESSAGE-LOCAL citation markers:
   [1] refers to that message's own sources[0] — the chat page assigns the
   global numbering when it renders, so threads stay portable. */
Sally.SESSIONS = [
  {
    id:"s-emissions", title:"Q3 Emissions Deep-Dive",
    members:["maya","jonas","you","sally"],
    seed:[
      {id:"e1", who:"maya",  time:"Mon 09:14", text:"Morning all — pulling the Q3 emissions narrative together for the exec review. Where did we land against the glide path?"},
      {id:"e2", who:"sally", time:"Mon 09:14", replyTo:"e1",
        text:"Scope 1–2 closed the quarter at **14,200 tCO₂e** — 27% below the 2019 baseline and slightly ahead of the glide path to net-zero 2035 [1]. Renewables covered **61%** of electricity, helped by the 4.1 MWp solar array coming fully online [2].",
        sources:[
          {code:"CRB-2024", name:"Carbon Report 2024", page:4, type:"Report", date:"2024", goals:[13],
           text:"Scope 1–2 emissions fell to 14,200 tCO₂e, 27% below the 2019 baseline, keeping the company ahead of its net-zero 2035 trajectory."},
          {code:"ENT-2024", name:"Energy Transition Report 2024", page:7, type:"Report", date:"2024", goals:[7,13],
           text:"Renewable sources supplied 61% of total electricity demand; the 4.1 MWp rooftop solar programme reduced grid draw by 18%."}]},
      {id:"e3", who:"jonas", time:"Mon 09:21", text:"Nice. The Plant 2 compressor retrofit finished in August — should that show up in the Q4 number?"},
      {id:"e4", who:"sally", time:"Mon 09:21", replyTo:"e3",
        text:"Yes — facilities modelling credits efficiency upgrades with an **18% reduction in grid draw**, and the retrofit is the biggest single contributor still to land [1]. I'd expect roughly a further 2–3% on Scope 2 in Q4.",
        sources:[
          {code:"FAC-2024", name:"Facilities Report", page:11, type:"Report", date:"2024", goals:[7,12],
           text:"Efficiency upgrades, led by the Plant 2 compressor retrofit, are projected to cut grid electricity draw by 18% on completion."}]},
      {id:"e5", who:"maya",  time:"Mon 09:26", replyTo:"e4", text:"Perfect — that's the bridge slide sorted. Jonas, can you own the ops commentary?"},
      {id:"e6", who:"jonas", time:"Mon 09:27", text:"On it. Draft to you Thursday."},
    ]
  },
  {
    id:"s-csrd", title:"CSRD Readiness Review",
    members:["priya","maya","you","sally"],
    seed:[
      {id:"c1", who:"priya", time:"Tue 11:02", text:"Kicking off the CSRD gap analysis. Sally — how much of ESRS E1 can we already evidence from the corpus?"},
      {id:"c2", who:"sally", time:"Tue 11:02", replyTo:"c1",
        text:"Strong starting position: the Carbon Report and Climate Strategy cover most of E1's transition-plan and target disclosures [1][2]. The real gap is **Scope 3 granularity** — we disclose a 71% share of total footprint but not category-level detail [1].",
        sources:[
          {code:"CRB-2024", name:"Carbon Report 2024", page:9, type:"Report", date:"2024", goals:[13],
           text:"Scope 3 emissions are estimated at 71% of the total footprint; category-level reporting is planned for the next cycle."},
          {code:"CLM-STRAT", name:"Climate Strategy", page:3, type:"Strategy", date:"2024", goals:[13,7],
           text:"The strategy sets a net-zero 2035 operations target with interim milestones in 2027 and 2030, governed by quarterly board review."}]},
      {id:"c3", who:"maya",  time:"Tue 11:09", text:"Scope 3 categories are on my Q1 list — supplier data is the blocker, as usual."},
      {id:"c4", who:"priya", time:"Tue 11:11", replyTo:"c3", text:"Then let's flag it as a known gap with a remediation owner in the readiness memo, rather than promising a date we can't hold."},
      {id:"c5", who:"sally", time:"Tue 11:12", replyTo:"c4",
        text:"Noted — I've tagged the supplier-data dependency against SDG 12 and 13 in the Neural Database, so it surfaces on the compliance view until it's closed [1].",
        sources:[
          {code:"SUS-2024", name:"Sustainability Report 2024", page:14, type:"Report", date:"2024", goals:[12,13],
           text:"Supplier engagement on emissions data remains the principal dependency for full value-chain reporting."}]},
    ]
  },
  {
    id:"s-supplier", title:"Supplier Audit Prep — Apex Metals",
    members:["tom","jonas","you","sally"],
    seed:[
      {id:"a1", who:"tom",   time:"Wed 15:40", text:"Apex Metals audit is in two weeks. What do we hold on their conduct and sourcing history?"},
      {id:"a2", who:"sally", time:"Wed 15:40", replyTo:"a1",
        text:"Procurement memo EN-2024-118 covers the responsible-sourcing clauses Apex signed in March [1], and the Compliance Log shows **zero open cases** involving them [2]. One caution: their last self-assessment scored amber on waste handling.",
        sources:[
          {code:"EN-2024-118", name:"Procurement Memo EN-2024-118", page:2, type:"Memo", date:"2024", goals:[12,8],
           text:"Apex Metals executed the responsible-sourcing addendum in March, committing to traceability and third-party audit access."},
          {code:"CPL-2024", name:"Compliance Log 2024", page:6, type:"Register", date:"2024", goals:[16],
           text:"No open compliance cases are recorded against Apex Metals; two historical queries were closed without findings."}]},
      {id:"a3", who:"jonas", time:"Wed 15:47", text:"Amber on waste matches what our site team saw in May. Worth pressing on."},
      {id:"a4", who:"tom",   time:"Wed 15:52", replyTo:"a2", text:"Sally, can you draft the audit question set weighted toward waste and labour standards?"},
      {id:"a5", who:"sally", time:"Wed 15:53", replyTo:"a4",
        text:"Drafted — 18 questions weighted 40% environment, 35% labour, 25% governance, each mapped to SDG 8 and 12 so the findings score straight into the compliance view [1]. It's saved as **APX-AUDIT-Q** in the shared folder.",
        sources:[
          {code:"OPS-2024", name:"Operations Review", page:8, type:"Review", date:"2024", goals:[9,12],
           text:"Supplier audits follow the weighted framework adopted in 2024, mapping findings to SDG-aligned scoring."}]},
      {id:"a6", who:"tom",   time:"Wed 15:55", replyTo:"a5", text:"You're the best. Jonas — can your site lead join day one?"},
    ]
  },
  {
    id:"s-board", title:"Board Pack · SDG Highlights",
    members:["maya","priya","elena","you","sally"],
    seed:[
      {id:"b1", who:"maya",  time:"Thu 10:05", text:"Board pack is due Friday. I want three headline wins and one honest gap."},
      {id:"b2", who:"sally", time:"Thu 10:05", replyTo:"b1",
        text:"Suggested headlines: emissions **27% below baseline** [1], adjusted pay gap down to **1.9%** [2], and the recordable injury rate at **0.42** — a 31% improvement year on year [3]. The honest gap: **SDG 14** — we currently hold no evidence for Life Below Water.",
        sources:[
          {code:"CRB-2024", name:"Carbon Report 2024", page:4, type:"Report", date:"2024", goals:[13],
           text:"Scope 1–2 emissions fell to 14,200 tCO₂e, 27% below the 2019 baseline."},
          {code:"PEA-2024", name:"Pay Equity Audit 2024", page:5, type:"Audit", date:"2024", goals:[5,10],
           text:"The adjusted gender pay gap narrowed to 1.9%, supported by a £1.2m remediation programme."},
          {code:"EHS-2024", name:"EHS Annual Review 2024", page:3, type:"Review", date:"2024", goals:[3,8],
           text:"The recordable injury rate fell 31% year on year to 0.42 per 200,000 hours worked."}]},
      {id:"b3", who:"elena", time:"Thu 10:12", replyTo:"b2", text:"Love that pay equity leads. Can we add the £1.2m remediation spend next to it? Numbers like that buy credibility."},
      {id:"b4", who:"sally", time:"Thu 10:12", replyTo:"b3",
        text:"Added — the Pay Equity Audit documents the **£1.2m remediation programme** alongside the 1.9% adjusted gap, so both figures carry the same citation [1].",
        sources:[
          {code:"PEA-2024", name:"Pay Equity Audit 2024", page:5, type:"Audit", date:"2024", goals:[5,10],
           text:"A £1.2m remediation programme accompanied the audit, adjusting bands in three job families."}]},
      {id:"b5", who:"priya", time:"Thu 10:18", text:"I'll sanity-check the SDG 14 wording so it reads as deliberate scoping, not a miss."},
      {id:"b6", who:"maya",  time:"Thu 10:19", replyTo:"b5", text:"Thanks both — circulating the skeleton this afternoon."},
    ]
  },
  {
    id:"s-payequity", title:"Pay Equity Follow-ups",
    members:["elena","priya","you","sally"],
    seed:[
      {id:"p1", who:"elena", time:"Fri 13:30", text:"Post-audit actions: where are we on the three flagged job families?"},
      {id:"p2", who:"sally", time:"Fri 13:30", replyTo:"p1",
        text:"Two of three are closed — engineering and logistics bands were adjusted in the October cycle; customer-ops remediation is budgeted and lands in January [1]. The adjusted gap now stands at **1.9%**, down from 4.8% in 2020 [1][2].",
        sources:[
          {code:"PEA-2024", name:"Pay Equity Audit 2024", page:7, type:"Audit", date:"2024", goals:[5,10],
           text:"Engineering and logistics band adjustments completed in October; customer operations remediation is funded for January."},
          {code:"COMP-2024", name:"Compensation Policy 2024", page:2, type:"Policy", date:"2024", goals:[8,10],
           text:"Annual equal-pay reviews are mandated across all job families, with adjustments applied in the October cycle."}]},
      {id:"p3", who:"priya", time:"Fri 13:36", text:"January is fine for the regulator, but it's tight for the board narrative."},
      {id:"p4", who:"elena", time:"Fri 13:38", replyTo:"p3", text:"Agreed — I'll frame it as “committed and funded”, with the date stated plainly."},
      {id:"p5", who:"sally", time:"Fri 13:39",
        text:"For the same section: **women in management is at 34%**, up from 28% last year [1] — worth a line while you have the board's attention.",
        sources:[
          {code:"DIV-2024", name:"Diversity Dashboard 2024", page:1, type:"Dashboard", date:"2024", goals:[5,10],
           text:"Women hold 34% of management roles, up from 28% in the prior year; under-represented groups made up 22% of hires."}]},
    ]
  },
  {
    id:"s-personal", title:"You & Sally",
    members:["you","sally"],
    seed:[
      {id:"w1", who:"sally", time:"Today",
        text:"This is your private session — ask me anything about the company and I'll answer with citations you can trace to the source. Nothing here is visible to the team sessions."},
    ]
  },
];

/* ---------------- helpers: overlay persistence + custom sessions ------- */
Sally.Sessions = (function(){
  const CHAT_KEY = id => "sess:"+id;

  function custom(){ return (Sally.store && Sally.store.get("userSessions", [])) || []; }
  function saveCustom(list){ Sally.store && Sally.store.set("userSessions", list); }

  function defs(){
    const c = custom().map(s=>({ id:s.id, title:s.title, members:s.members||["you","sally"], seed:[], custom:true }));
    return [...Sally.SESSIONS, ...c];
  }
  function get(id){ return defs().find(s=>s.id===id) || null; }

  function overlay(id){ return (Sally.store && Sally.store.loadChat(CHAT_KEY(id))) || []; }
  function messages(id){
    const s=get(id); if(!s) return [];
    return [...s.seed, ...overlay(id)];
  }
  function append(id, msg){
    const o=overlay(id); o.push(msg);
    Sally.store && Sally.store.saveChat(CHAT_KEY(id), o);
    return msg;
  }
  function create(title){
    const id="s-c"+Date.now();
    const list=custom(); list.push({id, title, members:["you","sally"], created:Date.now()});
    saveCustom(list);
    append(id, {id:"m"+Date.now(), who:"sally", time:"Now",
      text:`Welcome to **${title}** — I'm in the room. Ask me anything about the company and I'll bring the receipts; invite teammates and we can work the thread together.`});
    return id;
  }
  function rename(id, title){
    const list=custom(); const s=list.find(x=>x.id===id);
    if(s){ s.title=title; saveCustom(list); }
  }

  /* strip **bold** and [n] markers for previews */
  function plain(t){ return String(t||"").replace(/\*\*([^*]+)\*\*/g,"$1").replace(/\s*\[[\d,\s]+\]/g,""); }
  function lastMessage(id){ const m=messages(id); return m[m.length-1]||null; }

  /* shared avatar circle (used by the hub, the chat and dashboard widgets) */
  function avatarHtml(memberId, cls){
    const m = Sally.TEAM[memberId] || {name:memberId, color:"#8e8e93", initials:"?"};
    if(m.ai) return `<span class="pav ai ${cls||""}" title="${m.name} · ${m.role}"><i class="ri-sparkling-2-fill"></i></span>`;
    return `<span class="pav ${cls||""}" style="background:${m.color}" title="${m.name} · ${m.role}">${m.initials}</span>`;
  }
  function stackHtml(memberIds, max){
    const ids = memberIds.slice(0, max||4);
    const extra = memberIds.length - ids.length;
    return `<span class="pstack">${ids.map(id=>avatarHtml(id)).join("")}${extra>0?`<span class="pav more">+${extra}</span>`:""}</span>`;
  }

  return { defs, get, messages, append, create, rename, overlay, plain, lastMessage, avatarHtml, stackHtml };
})();
