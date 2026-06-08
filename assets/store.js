/* =========================================================================
   Sally — persistence (localStorage). Survives reloads & sessions so the POC
   doesn't feel built on stilts: uploaded docs, chat history, dashboard layout.
   Load AFTER corpus.js — it merges uploaded docs/concepts into the live corpus.
   ========================================================================= */
window.Sally = window.Sally || {};

Sally.store = (function(){
  const K = "sally-store-v1";
  let s;
  try{ s = JSON.parse(localStorage.getItem(K)) || {}; }catch(e){ s = {}; }
  s.docs     = s.docs     || [];     // uploaded documents (corpus-shaped)
  s.concepts = s.concepts || {};     // {name: {goals:[]}}  from uploads
  s.chat     = s.chat     || {};     // {ask: [{role,content,sources?}]}
  s.dash     = s.dash     || null;   // {order:[ids], custom:[payloads], pos:{id:{c,r}}}
  s.seen     = s.seen     || false;

  function save(){ try{ localStorage.setItem(K, JSON.stringify(s)); }catch(e){ console.warn("store full?",e); } }

  function get(k, def){ return (k in s) ? s[k] : def; }
  function set(k, v){ s[k]=v; save(); return v; }

  /* ---- uploaded documents ---- */
  function addDoc(doc){
    if(!doc || !doc.code) return doc;
    if(!s.docs.find(d=>d.code===doc.code)){
      s.docs.push(doc);
      (doc.concepts||[]).forEach(c=>{ if(!s.concepts[c]) s.concepts[c] = {goals: doc.goals||[]}; });
      save();
      mergeOne(doc);                 // reflect into the live corpus immediately
    }
    return doc;
  }
  function docs(){ return s.docs.slice(); }
  function removeDoc(code){
    s.docs = s.docs.filter(d=>d.code!==code); save();
    if(window.Sally && Array.isArray(Sally.DOCS)) Sally.DOCS = Sally.DOCS.filter(d=>d.code!==code);
  }

  /* ---- chat history ---- */
  function saveChat(page, messages){ s.chat[page]=messages; save(); }
  function loadChat(page){ return s.chat[page] || []; }
  function clearChat(page){ delete s.chat[page]; save(); }

  /* ---- dashboard layout / custom widgets ---- */
  function saveDash(d){ s.dash = d; save(); }
  function loadDash(){ return s.dash; }

  /* ---- merge uploads into the live corpus (idempotent) ---- */
  const merged = new Set();
  function mergeOne(d){
    if(merged.has(d.code)) return;
    merged.add(d.code);
    if(window.Sally && Array.isArray(Sally.DOCS) && !Sally.DOCS.find(x=>x.code===d.code)) Sally.DOCS.push(d);
    if(window.Sally && Sally.CONCEPTS) (d.concepts||[]).forEach(c=>{ if(!Sally.CONCEPTS[c]) Sally.CONCEPTS[c]={goals:d.goals||[]}; });
  }
  function mergeIntoCorpus(){ s.docs.forEach(mergeOne); }

  function clearAll(){ s={docs:[],concepts:{},chat:{},dash:null,seen:false}; save(); }
  function markSeen(){ s.seen=true; save(); }

  // merge any previously-uploaded docs now (corpus.js has already run)
  mergeIntoCorpus();

  return { get,set, addDoc,docs,removeDoc, saveChat,loadChat,clearChat,
           saveDash,loadDash, mergeIntoCorpus, clearAll, markSeen,
           get seen(){return s.seen;}, KEY:K };
})();
