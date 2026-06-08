/* =========================================================================
   Sally — LLM client (DeepSeek, OpenAI-compatible, direct from the browser)
   Key/model live in localStorage (entered via the settings panel), so the
   app is a pure static site — no backend, hostable on GitHub Pages.
   DeepSeek sends permissive CORS headers, so direct fetch() works.
   ========================================================================= */
window.Sally = window.Sally || {};

Sally.LLM = (function(){
  const LS = "sally-llm";
  const DEFAULTS = { base:"https://api.deepseek.com", model:"deepseek-v4-flash", key:"" };

  function cfg(){
    let c={}; try{ c = JSON.parse(localStorage.getItem(LS)) || {}; }catch(e){}
    return Object.assign({}, DEFAULTS, c);
  }
  function setCfg(patch){
    const c = Object.assign(cfg(), patch);
    localStorage.setItem(LS, JSON.stringify({ base:c.base, model:c.model, key:c.key }));
    return c;
  }
  function configured(){ return !!cfg().key; }

  /* chat(messages, opts)
     opts: { model, temperature, max_tokens, json:true, onToken:(tok,full)=>{}, signal }
     - with onToken → streams (SSE) and resolves to the full string
     - with json:true → asks for a JSON object back                         */
  async function chat(messages, opts={}){
    const c = cfg();
    if(!c.key) throw new Error("No DeepSeek API key set — open Settings (the gear in the dock).");
    const body = {
      model: opts.model || c.model,
      messages,
      temperature: opts.temperature ?? 0.3,
      stream: !!opts.onToken
    };
    if(opts.json) body.response_format = { type:"json_object" };
    if(opts.max_tokens) body.max_tokens = opts.max_tokens;

    const res = await fetch(c.base.replace(/\/+$/,"") + "/chat/completions", {
      method:"POST",
      headers:{ "Content-Type":"application/json", "Authorization":"Bearer "+c.key },
      body: JSON.stringify(body),
      signal: opts.signal
    });
    if(!res.ok){
      let msg=""; try{ const j=await res.json(); msg=j.error?.message||JSON.stringify(j); }catch(e){ msg=await res.text(); }
      throw new Error(`DeepSeek ${res.status}: ${(msg||"request failed").slice(0,300)}`);
    }

    if(opts.onToken){
      const reader = res.body.getReader(), dec = new TextDecoder();
      let buf="", full="";
      while(true){
        const {done, value} = await reader.read();
        if(done) break;
        buf += dec.decode(value, {stream:true});
        let nl;
        while((nl = buf.indexOf("\n")) >= 0){
          const line = buf.slice(0,nl).trim(); buf = buf.slice(nl+1);
          if(!line.startsWith("data:")) continue;
          const data = line.slice(5).trim();
          if(data === "[DONE]") continue;
          try{
            const j = JSON.parse(data);
            const tok = j.choices?.[0]?.delta?.content || "";
            if(tok){ full += tok; opts.onToken(tok, full); }
          }catch(e){}
        }
      }
      return full;
    }

    const j = await res.json();
    return j.choices?.[0]?.message?.content || "";
  }

  /* convenience: ask for and parse a JSON object */
  async function json(messages, opts={}){
    const txt = await chat(messages, Object.assign({json:true, temperature:0.2}, opts));
    // be forgiving: pull the first {...} block if the model wrapped it
    const m = txt.match(/\{[\s\S]*\}/);
    return JSON.parse(m ? m[0] : txt);
  }

  async function test(){
    const out = await chat([{role:"user", content:"Reply with exactly: ok"}], {max_tokens:4, temperature:0});
    return out.trim();
  }

  return { cfg, setCfg, configured, chat, json, test, KEY:LS };
})();
