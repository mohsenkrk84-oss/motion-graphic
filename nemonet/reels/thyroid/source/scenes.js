// Nemonet — hypothyroidism reel. Procedural: every frame is a pure function of t (deterministic seek).
const WD=window.WORDS, ws=i=>WD[i][1], we=i=>WD[i][2];
const DUR=25.0, S=1.3, FY=GY-LEGLEN*S;
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const E={ out:gsap.parseEase("power3.out"), inOut:gsap.parseEase("power2.inOut"), back:gsap.parseEase("back.out(2.2)"), in:gsap.parseEase("power2.in"), el:gsap.parseEase("elastic.out(1,0.5)") };
const prog=(t,a,d)=>clamp((t-a)/d);
const tf=(el,x,y,s=1,r=0)=>el.setAttribute("transform",`translate(${x} ${y}) rotate(${r}) scale(${Math.max(s,0.0001)})`);
const vis=(el,on)=>{ el.style.display=on?"":"none"; };
function popS(t,a,d=.4){ return t<a?0:E.back(prog(t,a,d)); }

const scenes=[];
function scene(t0,t1,build){ const root=g(world); const cam=g(root); const s={t0,t1,root,cam}; build(s); scenes.push(s); vis(root,false); return s; }
function wrap(p){ const w=g(p); const i=g(w); return {w,i}; }
function mkFig(p,extra){ return new Fig(p,{scale:S,extra}); }
function lbl(p,s,o={}){ const L=wrap(p); label(L.i,0,0,s,o); return L; }   // anchored at arrow tip
function scrollMarks(p){ const k=pencil(g(p)); const m=[]; for(let i=0;i<14;i++){ const e=line(k,"M0 0 l10 -14 M14 0 l4 -12",4,GREY); m.push(e);} return m; }
function placeMarks(m,off){ m.forEach((e,i)=>{ const x=((i*137-off)%1500+1500)%1500-200; e.setAttribute("transform",`translate(${x} ${GY-2})`); }); }
function speed(p,n=8){ const k=pencil(g(p)); const L=[]; for(let i=0;i<n;i++) L.push(line(k,"M0 0",4,GREY,{opacity:.8})); return {k,L}; }
function setSpeed(sp,x,y,w,t,alpha=1){ sp.L.forEach((e,i)=>{ const yy=y-200+i*44+(i%2)*10; const ww=w*(0.45+0.55*(((i*37)%10)/10))*(0.85+0.15*Math.sin(t*20+i)); e.setAttribute("d",`M${x-ww} ${yy} L${x} ${yy}`); }); sp.k.style.opacity=alpha; }
function headAt(f){ return f.W(f.headPos); }

// ---------- 1. HOOK: race, «تو» falls behind ----------
const A=scene(0,ws(8),s=>{ ground(s.cam,GY); s.marks=scrollMarks(s.cam);
  s.sp1=speed(s.cam); s.sp2=speed(s.cam,5);
  s.other=mkFig(s.cam); s.me=mkFig(s.cam,F=>{}); s.me.addSweat();
  s.lo=lbl(s.cam,"بقیه"); s.lm=lbl(s.cam,"تو");
  s.render=t=>{ placeMarks(s.marks,t*700);
    const ox=560+E.out(prog(t,0,2.8))*260, mx=330-E.inOut(prog(t,.4,2.4))*130;
    s.other.set(Object.assign({x:ox,y:FY,face:"happy"},runPose(t*2.6,1)));
    s.me.set(Object.assign({x:mx,y:FY+Math.abs(Math.sin(t*2*Math.PI*1.8))*-6,face:"tired",headTilt:8},runPose(t*1.8,.6),{lean:16}));
    setSpeed(s.sp1,ox-60,FY+40,420,t); setSpeed(s.sp2,mx-60,FY+40,150,t,.55);
    const ho=headAt(s.other), hm=headAt(s.me); tf(s.lo.w,ho[0],ho[1]-FIG.headR*S-14); tf(s.lm.w,hm[0],hm[1]-FIG.headR*S-14);
  }; });

// ---------- 2. TRIES: diet, gym, sleep — scale won't move ----------
const B=scene(ws(8),ws(14),s=>{ ground(s.cam,GY);
  s.sc=wrap(s.cam); s.needle=null; { const k=pencil(s.sc.i); shape(k,"M-120 0 L120 0 L110 34 L-110 34Z",PAPER,6); el("path",{d:"M-44 22 A44 44 0 0 1 44 22",fill:"none",stroke:INK,"stroke-width":5},k); s.needle=line(s.sc.i,"M0 22 L0 -14",5,ORANGE); }
  tf(s.sc.w,550,GY-6);
  s.me=mkFig(s.cam); s.lm=lbl(s.cam,"تو");
  s.items=[ [wrap(s.cam),"رژیم",180,700,(p)=>plate(p,0,0)], [wrap(s.cam),"باشگاه",540,330,(p)=>dumbbell(p,0,0,-12)], [wrap(s.cam),"خواب بیشتر",900,700,(p)=>pillow(p,0,0)] ];
  s.items.forEach(it=>{ it[4](it[0].i); label(it[0].i,0,it[1]==="خواب بیشتر"?-100:-60,it[1],{size:46}); });
  s.q=wrap(s.cam); txt(pencil(s.q.i),0,0,"؟",140,INK,"Hand");
  const keys=[ws(8),ws(10),ws(12)];
  s.render=t=>{ const T=t;
    // shrug at each try
    let sh=0; keys.forEach(k=>{ const p=prog(T,k+.35,.5); sh=Math.max(sh,Math.sin(p*Math.PI)); });
    s.me.set({x:540,y:FY,face:"sad",lean:0,headTilt:sh*8,aL1:205+sh*55,aL2:-10-sh*70,aR1:155-sh*55,aR2:10+sh*70});
    const h=headAt(s.me); tf(s.lm.w,h[0],h[1]-FIG.headR*S-14);
    s.items.forEach((it,i)=>{ const p=popS(T,keys[i]); tf(it[0].w,it[2],it[3]+Math.sin(T*3+i)*6,p); });
    // needle twitches up then falls back after each try
    let a=-4; keys.forEach(k=>{ const p=prog(T,k+.2,.6); a+=Math.sin(p*Math.PI)*30; });
    s.needle.setAttribute("d",`M0 22 L${Math.sin(rad(a))*36} ${22-Math.cos(rad(a))*36}`);
    tf(s.q.w,720,980,popS(T,ws(13)+.1)*(1+.08*Math.sin(T*8)));
  }; });

// ---------- 3. STILL TIRED: slow heavy run, scale icon ----------
const C3=scene(ws(14),ws(21),s=>{ ground(s.cam,GY); s.marks=scrollMarks(s.cam);
  s.sp=speed(s.cam,6); s.me=mkFig(s.cam); s.me.addSweat(); s.lm=lbl(s.cam,"تو");
  s.ball=wrap(s.cam); ballChain(s.ball.i,0,0,0,0,false); vis(s.ball.w,false);
  s.zz=wrap(s.cam); const k=pencil(s.zz.i); txt(k,0,0,"z",60,INK,"Hand"); txt(k,40,-50,"z",80,INK,"Hand");
  s.sc=wrap(s.cam); scaleObj(s.sc.i,0,0,-4); txt(pencil(s.sc.i),0,-70,"؟",90,ORANGE,"Hand");
  s.render=t=>{ const T=t-s.t0; placeMarks(s.marks,t*260);
    s.me.set(Object.assign({x:480,y:FY,face:"tired",headTilt:12},runPose(T*1.1,.45),{lean:22}));
    setSpeed(s.sp,420,FY+40,120,t,.4);
    const h=headAt(s.me); tf(s.lm.w,h[0],h[1]-FIG.headR*S-14);
    tf(s.zz.w,h[0]+90,h[1]-120,popS(t,ws(16)));
    tf(s.sc.w,800,GY-8,popS(t,ws(18)));
  }; });

// ---------- 4. TWIST: chained to «تیروئید کم‌کار» + magnifier ----------
const D=scene(ws(21),ws(30),s=>{ ground(s.cam,GY);
  s.me=mkFig(s.cam); s.lm=lbl(s.cam,"تو"); s.chain=g(s.cam);
  s.lens=wrap(s.cam); const L=s.lens.i;
  const inner=g(L,{"clip-path":"url(#lensClip)"}); el("rect",{x:-240,y:-240,width:480,height:480,fill:"#E6E6E2"},inner);
  const z=g(inner,{transform:"scale(2.1) translate(-600 -1170)"}); ballChain(z,420,1172,600,1130,true);
  circ(L,0,0,230,"none",12); line(pencil(L),"M165 165 L290 290",30);
  s.dash=line(pencil(s.cam),"M600 1150 L560 990",4,GREY,{"stroke-dasharray":"10 10"});
  s.render=t=>{ const T=t-s.t0;
    const strain=Math.sin(T*9)*3;
    s.me.set(Object.assign({x:300+strain,y:FY,face:t>ws(27)?"shock":"tired",lean:t>ws(27)?-6:18},walkPose(T*.9,.45)));
    const h=headAt(s.me); tf(s.lm.w,h[0],h[1]-FIG.headR*S-14);
    const ft=s.me.W(s.me.footLpos); s.chain.innerHTML=""; ballChain(s.chain,ft[0]+10,GY-8,600,GY-50,false);
    const lp=E.out(prog(t,ws(26)-.1,.55)); tf(s.lens.w,640+(1-lp)*700,760,1);
    const zp=E.back(prog(t,ws(28)-.05,.4)); s.lens.i.setAttribute("transform",`scale(${0.85+0.15*zp})`);
    s.dash.style.opacity=lp;
    s.cam.setAttribute("transform",`translate(540 900) scale(${1+0.06*E.inOut(prog(t,ws(21),2.5))}) translate(-540 -900)`);
  }; });

// ---------- 5. SYMPTOMS ----------
const E5=scene(ws(30),ws(34),s=>{ ground(s.cam,GY);
  s.me=mkFig(s.cam); s.me.addSweat(); s.chain=g(s.cam);
  s.syms=[["خستگی",780,430],["سرمایی بودن",250,250],["ریزش مو",800,700],["بی‌حوصلگی",640,180]].map(([txt_,x,y])=>{ const L=wrap(s.cam); const k=pencil(L.i); shape(k,"M-150 -50 L150 -50 L150 50 L-150 50Z","#EDEDE8",5); txt(k,0,-2,txt_,48,INK,"Hand"); const dl=line(pencil(s.cam),"M0 0",4,GREY,{"stroke-dasharray":"12 10"}); return {L,x,y,dl}; });
  s.snow=wrap(s.cam); { const k=pencil(s.snow.i); for(const a of [0,60,120]) line(k,`M${-26*Math.cos(rad(a))} ${-26*Math.sin(rad(a))} L${26*Math.cos(rad(a))} ${26*Math.sin(rad(a))}`,5,"#6E9CC0"); }
  const keys=[ws(30)+.05,ws(31)-.05,ws(32)-.05,ws(33)];
  s.render=t=>{ const T=t-s.t0;
    s.me.set(Object.assign({x:320,y:FY,face:"tired",headTilt:10+Math.sin(T*2)*3},walkPose(T*.6,.35),{lean:16}));
    const ft=s.me.W(s.me.footLpos); s.chain.innerHTML=""; ballChain(s.chain,ft[0]+8,GY-8,560,GY-50,true);
    const hd=headAt(s.me);
    s.syms.forEach((o,i)=>{ const p=popS(t,keys[i],.35); tf(o.L.w,o.x,o.y,p,(i%2?-3:3)*(1-p));
      o.dl.setAttribute("d",`M${o.x} ${o.y+56} L${o.x+(hd[0]+(o.x>hd[0]?50:-20)-o.x)*clamp((t-keys[i])/0.3)} ${o.y+56+(hd[1]-40-o.y-56)*clamp((t-keys[i])/0.3)}`); o.dl.style.opacity=p>0?1:0; });
    tf(s.snow.w,130,470,popS(t,keys[1]+.1)); s.snow.i.setAttribute("transform",`rotate(${T*60})`);
  }; });

// ---------- 6. SOLUTION: sampler, TSH+T4, chain breaks ----------
const F6=scene(ws(34),ws(44),s=>{ ground(s.cam,GY);
  s.me=mkFig(s.cam); s.lm=lbl(s.cam,"تو"); s.chain=g(s.cam);
  s.sm=new Fig(s.cam,{scale:S,extra:(Fg)=>{ shape(pencil(Fg.extraG),"M-56 -10 Q-60 -62 0 -60 Q58 -62 54 -6 Q60 40 34 60 L-40 60 Q-62 30 -56 -10Z",TEAL,6,{opacity:.9}); }});
  s.sm.extraG.parentNode.insertBefore(s.sm.extraG,s.sm.head); s.ls=lbl(s.cam,"نمونه‌گیر نِمونِت",{size:40});
  s.tubeW=wrap(s.cam); s.kitW=wrap(s.cam); kit(s.kitW.i,0,0);
  s.tsh=wrap(s.cam); { const k=pencil(s.tsh.i); shape(k,"M-150 -48 L150 -48 L150 48 L-150 48Z","#FFFFFF",5); txt(k,0,0,"TSH + T4",58,TEAL,"Hand",800,{direction:"ltr"}); }
  s.dash=line(pencil(s.cam),"M0 0",4,GREY,{"stroke-dasharray":"12 10"});
  s.bits=pencil(g(s.cam)); s.spark=pencil(g(s.cam));
  for(let i=0;i<3;i++) el("ellipse",{rx:16,ry:10,fill:"none",stroke:INK,"stroke-width":5},s.bits);
  for(let i=0;i<4;i++) line(s.spark,"M0 0 l0 -26",6,MUST);
  s.render=t=>{ const T=t-s.t0, brk=ws(42);
    const walkIn=E.out(prog(t,s.t0,.9));
    const sx=1150-(1150-740)*walkIn;
    s.sm.set(Object.assign({x:sx,y:FY,face:"happy"}, walkIn<1?walkPose(T*1.6,1):{lean:-2,aL1:140,aL2:30,aR1:180,aR2:0}));
    const hs=headAt(s.sm); tf(s.ls.w,hs[0],hs[1]-FIG.headR*S-14);
    const freed=t>brk;
    const jump=freed?Math.sin(clamp((t-brk-.2)/.5)*Math.PI)*60:0;
    s.me.set({x:250,y:FY-jump,face:freed?"grin":"tired",lean:freed?0:10,aL1:freed?120:200,aL2:freed?-40:-10,aR1:freed?240:205,aR2:freed?40:-30,lL1:-6,lL2:6,lR1:6,lR2:6});
    const hm=headAt(s.me); tf(s.lm.w,hm[0],hm[1]-FIG.headR*S-14);
    const ft=s.me.W(s.me.footLpos); s.chain.innerHTML=""; if(!freed) ballChain(s.chain,ft[0]+8,GY-8,470,GY-50,true);
    const hp=s.sm.W(s.sm.handLpos), hr=s.sm.W(s.sm.handRpos);
    s.tubeW.i.innerHTML=""; tube(s.tubeW.i,0,0,clamp((t-ws(38))/0.9)*0.85,-8); tf(s.tubeW.w,hp[0]-6,hp[1]-70,walkIn>.9?popS(t,s.t0+.8):0);
    tf(s.kitW.w,hr[0]+10,hr[1]+40);
    const tp=popS(t,ws(38)-.05); tf(s.tsh.w,470,400,tp); s.dash.setAttribute("d",`M500 450 L${hp[0]-6} ${hp[1]-160}`); s.dash.style.opacity=tp>0?1:0;
    // chain pieces fly
    const bp=clamp((t-brk)/0.7); s.bits.style.opacity=freed?1-bp*.6:0; s.spark.style.opacity=freed&&bp<1?1:0;
    [...s.bits.children].forEach((e,i)=>{ const dx=60+i*40+bp*(i-1)*120, dy=-20-bp*(160-i*30)+bp*bp*200; e.setAttribute("cx",ft[0]+dx); e.setAttribute("cy",GY+dy); e.setAttribute("transform",`rotate(${bp*360*(i%2?1:-1)} ${ft[0]+dx} ${GY+dy})`); });
    [...s.spark.children].forEach((e,i)=>{ const a=-60+i*40; e.setAttribute("transform",`translate(${ft[0]+70} ${GY-40}) rotate(${a}) translate(0 ${-30-bp*60})`); });
  }; });

// ---------- 7. OVERTAKE ----------
const G7=scene(ws(44),ws(48),s=>{ ground(s.cam,GY); s.marks=scrollMarks(s.cam);
  s.sp=speed(s.cam,9); s.other=mkFig(s.cam); s.me=mkFig(s.cam); s.lo=lbl(s.cam,"بقیه"); s.lm=lbl(s.cam,"تو");
  s.render=t=>{ const T=t-s.t0; placeMarks(s.marks,t*900);
    const p=E.inOut(prog(T,0,1.2)); const mx=120+p*660, ox=620-p*290;
    s.other.set(Object.assign({x:ox,y:FY,face:p>.45?"shock":"happy"},runPose(T*2.2,.7)));
    s.me.set(Object.assign({x:mx,y:FY,face:"grin"},runPose(T*3,1.15)));
    setSpeed(s.sp,mx-70,FY+40,560,t);
    const ho=headAt(s.other), hm=headAt(s.me); tf(s.lo.w,ho[0],ho[1]-FIG.headR*S-14); tf(s.lm.w,hm[0],hm[1]-FIG.headR*S-14);
  }; });

// ---------- 8. CTA ----------
const H8=scene(ws(48),DUR+1,s=>{ const c=s.cam;
  s.disc=wrap(c); el("circle",{cx:0,cy:0,r:210,fill:"#EDEDE8",stroke:INK,"stroke-width":6,filter:"url(#pencil)"},s.disc.i); el("image",{href:"app-icon-tide.png",x:-120,y:-120,width:240,height:240},s.disc.i);
  s.rays=pencil(g(c,{transform:"translate(540 560)"})); for(let i=0;i<12;i++){ const a=rad(i*30); line(s.rays,`M${Math.sin(a)*240} ${-Math.cos(a)*240} L${Math.sin(a)*300} ${-Math.cos(a)*300}`,7,i%2?MUST:TEAL); }
  s.title=wrap(c); txt(s.title.i,0,0,"تیروئیدت رو چک کن",86,INK,"Hand",800);
  s.l1=wrap(c); txt(s.l1.i,0,0,"پنل تیروئید TSH و T4 در منزل",50,INK,"Yekan",700);
  s.l2=wrap(c); txt(s.l2.i,0,0,"از ۶ صبح - تهران و مشهد",50,"#555","Yekan",700);
  s.btn=wrap(c); el("rect",{x:-330,y:-70,width:660,height:140,rx:70,fill:TEAL,stroke:INK,"stroke-width":6,filter:"url(#pencil)"},s.btn.i); txt(s.btn.i,0,0,"همین الان نوبت بگیر",60,"#FFFFFF","Yekan",700);
  s.url=wrap(c); txt(s.url.i,0,0,"nemonet.ir",56,INK,"Yekan",700,{direction:"ltr"});
  s.arrow=wrap(c); { const k=pencil(s.arrow.i); line(k,"M0 -60 L0 50",9); line(k,"M-36 18 L0 56 L36 18",9); }
  s.render=t=>{ const a=s.t0;
    tf(s.disc.w,540,560,popS(t,a,.55));
    const rp=prog(t,a+.1,.7); s.rays.setAttribute("transform",`translate(540 560) scale(${0.7+rp*.5}) rotate(${rp*20})`); s.rays.style.opacity=rp<1?1-rp:0;
    tf(s.title.w,540,850,popS(t,a+.25)); tf(s.l1.w,540,975,popS(t,ws(49))); tf(s.l2.w,540,1060,popS(t,ws(50)));
    const bp=popS(t,ws(51)); tf(s.btn.w,540,1210,bp*(1+(t>ws(51)+.5?0.04*Math.sin((t-ws(51))*7):0)));
    tf(s.url.w,540,1350,popS(t,ws(52))); tf(s.arrow.w,540,1480+(t>ws(53)+.4?12*Math.sin((t-ws(53))*8):0),popS(t,ws(53)));
  }; });

// ---------- transitions ----------
const fx=document.getElementById("fx");
const flash=el("rect",{width:1080,height:1920,fill:"#FFFFFF",opacity:0},fx);
const wipeL=el("rect",{x:0,y:0,width:1080,height:1920,fill:PAPER,opacity:0},fx);

// ---------- captions ----------
const CH=[[0,3],[4,7],[8,9],[10,11],[12,13],[14,16],[17,20],[21,25],[26,29],[30,33],[34,37],[38,38],[39,43],[44,47],[48,50],[51,54]];
const capL=document.getElementById("captions"); const CAPS=[]; const CY=1640, CS=58;
CH.forEach(([a,b])=>{ const grp=g(capL); const bg=el("rect",{fill:"#232325",opacity:.86,rx:CS*.55},grp);
  const t=el("text",{x:540,y:CY,"font-size":CS,"font-weight":700,"font-family":"Yekan","text-anchor":"middle","dominant-baseline":"central",direction:"rtl",fill:"#fff"},grp);
  const spans=[]; for(let i=a;i<=b;i++){ const sp=el("tspan",{},t); let w=WD[i][0]; if(w==="TSH،") w="TSH"; sp.textContent=(i>a?" ":"")+w; spans.push({sp,s:ws(i),e:we(i)}); }
  const bb=t.getBBox(); const px=CS*.6, pv=CS*.24; Object.entries({x:bb.x-px,y:bb.y-pv,width:bb.width+2*px,height:bb.height+2*pv}).forEach(([k,v])=>bg.setAttribute(k,v));
  grp.style.display="none"; CAPS.push({grp,spans,start:spans[0].s-.05}); });
CAPS.forEach((c,i)=>{ const n=CAPS[i+1]; const last=c.spans[c.spans.length-1].e; c.end=n?Math.min(n.start,last+.6):last+.45; });

function seek(t){
  t=Math.max(t,0.001);
  for(const s of scenes){ const on=t>=s.t0 && t<s.t1; vis(s.root,on); if(on) s.render(t); }
  // whip-ish flash on cuts
  const cuts=[ws(8),ws(14),ws(21),ws(30),ws(34),ws(44),ws(48)]; let f=0;
  for(const c of cuts){ const d=t-c; if(d>=0&&d<.18) f=Math.max(f,(1-d/.18)*.55); }
  flash.setAttribute("opacity",f);
  for(const c of CAPS){ const on=t>=c.start&&t<c.end; c.grp.style.display=on?"":"none"; if(!on) continue;
    const k=clamp((t-c.start)/.14), sc=.86+.14*(1-Math.pow(1-k,3)); c.grp.setAttribute("transform",`translate(540 ${CY}) scale(${sc}) translate(-540 ${-CY})`);
    for(const s of c.spans){ const cur=t>=s.s-.02&&t<s.e+.05, done=t>=s.e+.05; s.sp.setAttribute("fill",cur?"#FFD166":"#fff"); s.sp.setAttribute("fill-opacity",(cur||done)?1:.5); } }
}
window.DUR=DUR; window.seek=seek; window.ready=true;
