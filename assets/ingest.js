/* =========================================================================
   Sally — PDF ingestion. Extracts text client-side with pdf.js, then asks
   DeepSeek (or an offline heuristic) to classify it into a corpus-shaped doc
   (SDG goals, concepts, a verbatim key passage). Persisted via Sally.store.
   ========================================================================= */
window.Sally = window.Sally || {};

Sally.Ingest = (function(){

  function ready(){
    if(window.pdfjsLib && pdfjsLib.GlobalWorkerOptions){
      if(!pdfjsLib.GlobalWorkerOptions.workerSrc) pdfjsLib.GlobalWorkerOptions.workerSrc = "vendor/pdf.worker.min.js";
      return true;
    }
    return false;
  }

  async function extractText(file, onPage){
    if(!ready()) throw new Error("pdf.js not loaded");
    const buf = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({data:buf}).promise;
    const pages = [];
    for(let i=1;i<=pdf.numPages;i++){
      const page = await pdf.getPage(i);
      const tc = await page.getTextContent();
      const text = tc.items.map(it=>it.str).join(" ").replace(/\s+/g," ").trim();
      pages.push({page:i, text});
      onPage && onPage(i, pdf.numPages);
    }
    return { numPages: pdf.numPages, pages };
  }

  /* ---- offline heuristics (no key) ---- */
  function guessFromText(text){
    const t = text.toLowerCase(), goals = new Set(), concepts = [];
    // precise: the full SDG short-name phrase must appear (avoids "water"/"clean"/"life" cross-matches)
    Sally.SDG.forEach(g=>{ if(t.includes(g.short.toLowerCase())) goals.add(g.n); });
    // concept matches only when ALL of its significant words are present
    Object.keys(Sally.CONCEPTS).forEach(c=>{
      const words = c.toLowerCase().split(/[\s/&-]+/).filter(w=>w.length>3);
      if(words.length && words.every(w=>t.includes(w))){ concepts.push(c); (Sally.CONCEPTS[c].goals||[]).forEach(g=>goals.add(g)); }
    });
    const gl = [...goals].slice(0,4);
    // if no corpus concept fit, seed concepts from the matched goals so the node still links richly
    if(!concepts.length && gl.length) concepts.push(...gl.map(n=>(Sally.sdg(n)||{}).short).filter(Boolean).slice(0,2));
    return { goals:gl, concepts:concepts.slice(0,5) };
  }
  function firstSentence(text){
    const m = text.replace(/\s+/g," ").match(/[^.?!]{40,240}[.?!]/);
    return (m ? m[0] : text.slice(0,200)).trim();
  }
  function codeFromName(name){
    const base = name.replace(/\.[^.]+$/,"").replace(/[^a-z0-9]+/ig,"-").replace(/^-|-$/g,"").toUpperCase().slice(0,16);
    return base || ("DOC-" + Math.floor(Date.now()/1000));
  }

  /* ---- AI analysis (DeepSeek) ---- */
  async function analyzeAI(name, pages){
    const joined = pages.map(p=>`[p${p.page}] ${p.text}`).join("\n").slice(0, 12000);
    const sys = `You analyze a corporate document for UN Sustainable Development Goal (SDG) relevance. Return STRICT JSON only, no prose:
{"type": one of "Report|Policy|Audit|Strategy|Memo|Charter|Register|Brief|Record|Dashboard|Review",
 "summary": one sentence (<=22 words),
 "concepts": array of 1-4 short concept tags (prefer ones from CONCEPTS, but you may add a fitting new one),
 "goals": array of 1-4 SDG numbers (1-17) the document advances,
 "keyPassage": {"page": number, "text": a VERBATIM quote (<=240 chars) copied exactly from the document, the strongest single piece of evidence}}`;
    const usr = `CONCEPTS: ${JSON.stringify(Object.keys(Sally.CONCEPTS))}\nSDGs: ${JSON.stringify(Sally.SDG.map(g=>({n:g.n,name:g.short})))}\n\nDOCUMENT "${name}":\n${joined}`;
    return await Sally.LLM.json([{role:"system",content:sys},{role:"user",content:usr}], {max_tokens:600});
  }

  /* ---- main pipeline ---- */
  async function fromPDF(file, opts={}){
    const onp = opts.onProgress || function(){};
    onp({stage:"reading", label:"Reading PDF…"});
    const { numPages, pages } = await extractText(file, (i,n)=> onp({stage:"extract", page:i, total:n, label:`Extracting text · p.${i}/${n}`}));
    const fullText = pages.map(p=>p.text).join(" ");
    const name = file.name.replace(/\.pdf$/i,"");
    const code = codeFromName(file.name);

    let a = null;
    if(Sally.LLM && Sally.LLM.configured()){
      onp({stage:"analyze", label:"Analyzing with DeepSeek…"});
      try{ a = await analyzeAI(name, pages); }catch(e){ console.warn("AI analyze failed, using heuristic:", e); }
    }
    if(!a){
      onp({stage:"analyze", label:"Classifying…"});
      const g = guessFromText(fullText);
      a = { type:"Upload", summary:firstSentence(fullText).slice(0,140),
            concepts:g.concepts.length?g.concepts:["Governance & Ethics"],
            goals:g.goals.length?g.goals:[9],
            keyPassage:{page:1, text:firstSentence(fullText)} };
    }

    const goals = (a.goals||[]).map(Number).filter(n=>n>=1&&n<=17).slice(0,4);
    const concepts = (a.concepts||[]).filter(c=>typeof c==="string" && c.trim()).map(c=>c.trim()).slice(0,5);
    const kp = a.keyPassage || {};
    const doc = {
      name, code, type: a.type || "Upload",
      date: new Date().toISOString().slice(0,7),
      pages: numPages,
      goals: goals.length ? goals : [9],
      concepts: concepts.length ? concepts : ["Governance & Ethics"],
      summary: a.summary || firstSentence(fullText).slice(0,140),
      cite: { p: Math.max(1, Math.min(numPages, kp.page||1)), t: (kp.text || firstSentence(fullText)).slice(0,260) },
      uploaded: true
    };
    Sally.store.addDoc(doc);            // persists + merges into the live corpus
    onp({stage:"done", doc, label:"Done"});
    return doc;
  }

  return { fromPDF, extractText, ready, codeFromName };
})();
