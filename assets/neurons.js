/* =========================================================================
   Sally — neural field  (adapted from Davlon's neurons.js)
   Drifting "nodes" linked by proximity lines. Refined, on-brand palette.
   Behaviour change: instead of only free-drifting, particles are gently
   pulled toward the cursor on hover — the web "contains" into the pointer,
   then releases back to a slow drift when the mouse leaves.
   ========================================================================= */
window.SallyNeurons = function(canvas, opts){
  const o = Object.assign({
    density:14000, min:46, max:130,   // particle count scales with area
    linkDist:132,                     // px to draw a connecting line
    drift:0.32,                       // base wander speed
    friction:0.965,                   // settles pulled particles
    jitter:0.05,                      // keeps drift alive
    maxSpeed:2.6,
    pull:0.16, pullRadius:210,        // hover-contain strength + reach
    dot:[1.1, 2.7],                   // particle radius range
    linkAlpha:0.5,                    // proximity-line opacity (dial down for busy pages)
    dotAlpha:0.92,                    // particle opacity
    hub:true                          // draw the cursor "containment" web on hover
  }, opts||{});

  const ctx = canvas.getContext("2d");
  const reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  let W=0, H=0, dpr=1, ps=[], raf=null;
  const mouse = { x:null, y:null, on:false };

  // weighted palette: mostly cool blue/teal, a few SDG-flavoured pops
  const PALETTE = [
    {c:"#0a84ff", w:34}, {c:"#64d2ff", w:24}, {c:"#5ac8a8", w:14},
    {c:"#e6edf5", w:14}, {c:"#bf5af2", w:7}, {c:"#ffd60a", w:4}, {c:"#ff7a59", w:3}
  ];
  const WSUM = PALETTE.reduce((s,p)=>s+p.w,0);
  function pickColor(){ let r=Math.random()*WSUM; for(const p of PALETTE){ if((r-=p.w)<0) return p.c; } return "#0a84ff"; }
  const rnd = (a,b)=> a + Math.random()*(b-a);

  function isDark(){ return (document.documentElement.getAttribute("data-theme")||"dark")!=="light"; }

  function size(){
    dpr = Math.min(2, window.devicePixelRatio||1);
    // these fields are always full-viewport; use the viewport directly
    // (a fixed <canvas> with inset:0 keeps its 300x150 intrinsic size otherwise)
    W = window.innerWidth; H = window.innerHeight;
    canvas.style.width = W+"px"; canvas.style.height = H+"px";
    canvas.width = W*dpr; canvas.height = H*dpr;
    ctx.setTransform(dpr,0,0,dpr,0,0);
    const n = Math.max(o.min, Math.min(o.max, Math.floor((W*H)/o.density)));
    seed(n);
  }

  function seed(n){
    ps = [];
    for(let i=0;i<n;i++) ps.push({
      x:rnd(0,W), y:rnd(0,H),
      vx:rnd(-o.drift,o.drift), vy:rnd(-o.drift,o.drift),
      r:rnd(o.dot[0],o.dot[1]), c:pickColor()
    });
  }

  function step(){
    for(const p of ps){
      // hover-contain: pull toward the cursor when near
      if(mouse.on){
        const dx=mouse.x-p.x, dy=mouse.y-p.y, d=Math.hypot(dx,dy);
        if(d<o.pullRadius && d>0.6){
          const f=o.pull*(1-d/o.pullRadius);
          p.vx += (dx/d)*f; p.vy += (dy/d)*f;
        }
      }
      p.x+=p.vx; p.y+=p.vy;
      p.vx=p.vx*o.friction + (Math.random()-0.5)*o.jitter;
      p.vy=p.vy*o.friction + (Math.random()-0.5)*o.jitter;
      const sp=Math.hypot(p.vx,p.vy);
      if(sp>o.maxSpeed){ p.vx*=o.maxSpeed/sp; p.vy*=o.maxSpeed/sp; }
      if(p.x<0){p.x=0;p.vx*=-1;} else if(p.x>W){p.x=W;p.vx*=-1;}
      if(p.y<0){p.y=0;p.vy*=-1;} else if(p.y>H){p.y=H;p.vy*=-1;}
    }
  }

  function draw(){
    ctx.clearRect(0,0,W,H);
    const dark = isDark();
    const line = dark ? "150,178,214" : "40,70,120";
    const linkA = o.linkAlpha * (dark ? 1 : 0.9);

    // proximity links
    ctx.lineWidth = 1;
    for(let i=0;i<ps.length;i++){
      for(let j=i+1;j<ps.length;j++){
        const a=ps[i], b=ps[j];
        const dx=a.x-b.x, dy=a.y-b.y, d=dx*dx+dy*dy;
        if(d < o.linkDist*o.linkDist){
          const dist=Math.sqrt(d);
          ctx.strokeStyle = `rgba(${line},${(1-dist/o.linkDist)*linkA})`;
          ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y); ctx.stroke();
        }
      }
    }

    // the cursor "hub": tie nearby particles to the pointer while hovering
    if(mouse.on && o.hub){
      for(const p of ps){
        const dx=mouse.x-p.x, dy=mouse.y-p.y, d=Math.hypot(dx,dy);
        if(d<o.pullRadius){
          ctx.strokeStyle = `rgba(10,132,255,${(1-d/o.pullRadius)*0.55})`;
          ctx.lineWidth = 1;
          ctx.beginPath(); ctx.moveTo(mouse.x,mouse.y); ctx.lineTo(p.x,p.y); ctx.stroke();
        }
      }
      ctx.beginPath(); ctx.arc(mouse.x,mouse.y,2.5,0,6.283);
      ctx.fillStyle="rgba(10,132,255,0.9)"; ctx.fill();
    }

    // particles
    for(const p of ps){
      ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,6.283);
      ctx.fillStyle=p.c; ctx.globalAlpha = o.dotAlpha*(dark?1:0.87); ctx.fill(); ctx.globalAlpha=1;
    }
  }

  function loop(){ step(); draw(); raf=requestAnimationFrame(loop); }

  // pointer is tracked on the window so it works even though the canvas is
  // behind the content (pointer-events:none) — hover-contain follows the mouse anywhere
  function onMove(e){ mouse.x=e.clientX; mouse.y=e.clientY; mouse.on=true; }
  function onLeave(){ mouse.on=false; }
  window.addEventListener("mousemove", onMove, {passive:true});
  window.addEventListener("mouseout", e=>{ if(!e.relatedTarget) onLeave(); });
  window.addEventListener("blur", onLeave);
  window.addEventListener("resize", size);

  size();
  if(reduce){ draw(); }      // static field, no motion
  else loop();

  return { stop(){ if(raf) cancelAnimationFrame(raf); } };
};
