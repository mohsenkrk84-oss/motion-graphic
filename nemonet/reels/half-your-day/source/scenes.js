// Nemonet reel A — "نصف روزت یا ۱۰ دقیقه؟"  — GSAP timeline, 30fps, synced to VO word timestamps
// pointing hand: fingertip at (0,0), hand extends downward in local space
function pointer(p,x,y,rot,sleeve){
  const h=g(p,{transform:`translate(${x} ${y}) rotate(${rot})`});
  arm(h,"M36 320 L90 1500",sleeve,120); L(h,"M-20 330 Q36 350 96 330",C.ink,6);
  P(h,"M-58 170 C-66 120 -40 96 -12 100 L92 100 C120 100 132 130 128 170 L120 280 C116 320 80 340 40 336 L-20 330 C-56 326 -64 300 -62 260Z",C.skin,{"stroke-width":5}); // palm
  L(h,"M8 152 Q40 140 72 150 M8 196 Q40 184 76 194 M10 240 Q40 230 74 238",C.ink,4.5,{opacity:.75}); // curled fingers
  P(h,"M-58 190 C-96 170 -112 130 -96 110 C-82 94 -60 108 -44 140Z",C.skin,{"stroke-width":5}); // thumb
  P(h,"M-24 0 C-24 -18 24 -18 24 0 L26 150 L-26 150Z",C.skin,{"stroke-width":5}); // index finger
  L(h,"M-12 10 Q0 2 12 10",C.ink,3.5,{opacity:.6}); L(h,"M-16 70 Q0 76 16 70",C.ink,3,{opacity:.5}); // nail + knuckle
  return h;
}
// left hand holding the phone's left edge (thumb on the bezel)
function gripLeft(p,x,y,sleeve){
  const h=g(p,{transform:`translate(${x} ${y})`});
  arm(h,"M-60 120 L-110 1700",sleeve,120);
  P(h,"M-110 -60 C-120 -110 -60 -130 -20 -110 L20 -90 L24 130 C-10 160 -90 150 -110 100Z",C.skin,{"stroke-width":5});
  P(h,"M-6 -40 C10 -86 46 -100 60 -80 C72 -62 50 -30 20 10Z",C.skin,{"stroke-width":5}); // thumb over bezel
  L(h,"M-100 -20 Q-70 -28 -40 -18 M-104 30 Q-72 22 -40 32",C.ink,4,{opacity:.6});
  return h;
}


const WORDS = window.WORDS;               // [text,start,end] injected before this script
const ws = i => WORDS[i][1], we = i => WORDS[i][2];
const DUR = 29.4;
const world = document.getElementById("world"), fx = document.getElementById("fx");
const tl = gsap.timeline({paused:true, defaults:{ease:"power2.out"}});
const H = {};                               // handles per scene

function scene(name){ const wrap=g(world,{id:"sc_"+name}); const cam=g(wrap,{class:"cam"}); gsap.set(wrap,{autoAlpha:0}); return {wrap,cam}; }
function pop(el,t,{from=0,dur=.45,ease="back.out(2.2)"}={}){ tl.fromTo(el,{scale:from,autoAlpha:0,transformOrigin:"50% 50%"},{scale:1,autoAlpha:1,duration:dur,ease},t); }
function show(sc,t){ tl.set(sc.wrap,{autoAlpha:1},t); }
function hide(sc,t){ tl.set(sc.wrap,{autoAlpha:0},t); }
const arcPath=(r,deg)=>{ const a=Math.min(deg,359.9)*Math.PI/180; return `M0 0 L0 ${-r} A${r} ${r} 0 ${deg>180?1:0} 1 ${r*Math.sin(a)} ${-r*Math.cos(a)} Z`; };

// =============== 1. ALARM (hook) ===============
function buildAlarm(name, mood){
  const sc=scene(name), W=sc.cam, h={};
  R(W,-200,-200,1480,2320,0,C.wallWarm,{stroke:"none"});
  R(W,640,230,330,420,18,C.cream); R(tex(W),664,254,282,372,8,C.sky);
  el("circle",{cx:880,cy:330,r:36,fill:"#F3E7C6"},W); el("circle",{cx:896,cy:318,r:32,fill:C.sky},W);
  h.stars=g(W); for(const [x,y] of [[710,310],[740,450],[820,560],[900,480]]) el("circle",{cx:x,cy:y,r:5,fill:"#F3E7C6"},h.stars);
  L(W,"M805 254 V626 M664 440 H946",C.ink,8);
  R(tex(W),60,820,960,560,46,C.woodD); R(tex(W),130,1000,300,150,60,C.cream);
  const m=g(W,{transform:"translate(560 960) scale(1.45)"}); torso(m,"pajama",165);
  h.head=g(m); const hd=g(h.head,{transform:"translate(0 -64) rotate(-7)"}); head(hd,mood);
  L(hd,"M-30 -122 C-44 -160 -10 -170 -8 -140",C.ink,6); L(hd,"M24 -122 C30 -160 60 -150 48 -124",C.ink,6);
  if(mood==="sleepy"){ h.hand=g(m); arm(h.hand,"M150 250 C200 150 150 40 72 -30",C.pjB); hand(h.hand,62,-50,1.1,-30); }
  else { arm(m,"M150 250 C200 190 210 120 190 40",C.pjB); hand(m,186,20,1.1,0); }
  P(tex(W),"M-200 1250 C300 1200 780 1200 1280 1250 V2200 H-200Z",C.mustard);
  for(let i=0;i<8;i++) L(W,`M${-100+i*180} 1290 l70 520`,"#D59A38",8,{opacity:.6});
  if(mood==="sleepy"){ h.growl=g(W); L(h.growl,"M470 1300 q14 -18 28 0 t28 0 t28 0",C.ink,6); L(h.growl,"M600 1340 q14 -18 28 0 t28 0",C.ink,6); }
  R(tex(W),-200,1120,490,1000,20,C.wood);
  h.clock=g(W,{transform:"translate(175 1000) rotate(-8) scale(.74)"}); const ck=g(h.clock);
  h.ckInner=ck;
  for(const sx of [-1,1]){ L(ck,`M${sx*95} -130 L${sx*120} -170`,C.ink,10); O(tex(ck),sx*130,-182,48,30,C.red); }
  L(ck,"M-100 108 l-20 40 M100 108 l20 40",C.ink,12);
  R(tex(ck),-170,-140,340,250,60,C.red); R(ck,-130,-100,260,160,24,"#1E2430");
  h.digits=T(ck,0,-22,"۰۶:۰۰",100,"#7FE3B0",700,{direction:"ltr","letter-spacing":"4"});
  if(mood==="sleepy"){ h.ring=g(W); for(const sx of [-1,1]) for(const r of [1,2]) L(h.ring,`M${140+sx*(170+r*34)} ${930-r*16} q${sx*22} 60 0 120`,C.red,8); }
  if(mood!=="sleepy"){ // idea bulb
    h.bulb=g(W,{transform:"translate(380 520)"}); const b=g(h.bulb);
    h.rays=g(b); for(let i=0;i<8;i++){ const a=i*Math.PI/4; L(h.rays,`M${Math.sin(a)*120} ${-Math.cos(a)*120} L${Math.sin(a)*165} ${-Math.cos(a)*165}`,C.mustard,12); }
    O(tex(b),0,-10,82,86,"#FFE07A"); R(b,-40,64,80,52,12,C.grey); L(b,"M-24 -10 q24 40 48 0",C.ink,5);
  }
  sc.h=h; return sc;
}
const s1=buildAlarm("alarm","sleepy");
const s4=buildAlarm("idea","open");

// =============== 2. TRAFFIC ===============
function car(p,x,y,col,s=1,driver=false){
  const c=g(p,{transform:`translate(${x} ${y}) scale(${s})`}); const b=g(c);
  P(tex(b),"M-200 40 L-180 -20 C-170 -50 -150 -60 -120 -64 L-80 -130 C-70 -144 -50 -150 -30 -150 L70 -150 C96 -150 112 -140 124 -120 L160 -64 C188 -60 200 -40 204 -10 L210 40 C210 60 196 70 180 70 L-180 70 C-196 70 -204 58 -200 40Z",col);
  P(b,"M-66 -70 L-40 -126 L40 -126 L40 -70Z","#CFE6F0",{"stroke-width":5}); P(b,"M56 -70 L56 -126 L84 -126 C96 -126 104 -120 110 -110 L134 -70Z","#CFE6F0",{"stroke-width":5});
  if(driver){ const hh=g(b,{transform:"translate(-2 -96) scale(.32)"}); head(hh,"sleepy"); }
  for(const wx of [-120,120]){ O(c,wx,70,44,44,"#2E2E36"); O(c,wx,70,18,18,C.grey,{"stroke-width":4}); }
  el("circle",{cx:196,cy:0,r:12,fill:"#FFE07A",stroke:C.ink,"stroke-width":4},b);
  return {c,b};
}
const s2=(()=>{ const sc=scene("traffic"), W=sc.cam, h={};
  R(W,-200,-200,1480,2320,0,"#F2C7A6",{stroke:"none"});           // dawn sky
  el("circle",{cx:780,cy:560,r:120,fill:"#F7E3B4"},W);
  for(const [x,w,hh,col] of [[-40,220,700,"#9FB0C9"],[200,180,520,"#B8C3D6"],[400,240,820,"#8EA0BD"],[660,200,600,"#AAB8CE"],[880,260,760,"#93A4C0"]]){
    R(tex(W),x,1100-hh,w,hh+40,8,col); for(let yy=1100-hh+50; yy<1060; yy+=90) for(let xx=x+30; xx<x+w-40; xx+=60) R(W,xx,yy,30,44,4,"#F6E6C8",{"stroke-width":3});
  }
  R(W,-200,1100,1480,1100,0,"#6E6A72",{stroke:"none"}); L(W,"M-200 1100 H1280",C.ink,6);
  for(const y of [1380,1660]) for(let x=-200;x<1300;x+=200) R(W,x,y,110,16,8,"#F2EAD8",{stroke:"none"});
  h.laneA=g(W); h.laneB=g(W);
  [[ -60,"#5F9AD0"],[420,"#8FB86B"],[900,"#C98BC1"],[1380,"#E6B655"]].forEach(([x,col])=>car(h.laneA,x,1260,col,.9));
  [[ -300,"#E6B655"],[200,"#7FB0B4"],[700,"#C77B5E"],[1200,"#5F9AD0"]].forEach(([x,col])=>car(h.laneB,x,1830,col,1.05));
  h.me=car(W,540,1560,C.sweater,1.35,true);
  h.honk1=g(W,{transform:"translate(840 1350)"}); for(const r of [0,1,2]) L(h.honk1,`M${r*30} ${-60-r*16} q30 ${60+r*16} 0 ${120+r*32}`,C.red,9);
  h.bubble=g(W,{transform:"translate(840 1220)"}); R(tex(h.bubble),-110,-60,220,110,50,C.white); T(h.bubble,0,-6,"بوق!",54,C.red,700);
  h.puffs=g(W); for(const [x,y,r] of [[230,1610,26],[180,1580,34],[120,1550,42]]) O(h.puffs,x,y,r,r,"#D9D4CE",{"stroke-width":4});
  sc.h=h; return sc; })();

// =============== 3. QUEUE ===============
const s3=(()=>{ const sc=scene("queue"), W=sc.cam, h={};
  el("rect",{x:-200,y:-200,width:1480,height:2320,fill:"url(#tiles)"},W);
  R(W,-200,1180,1480,1000,0,C.floor,{stroke:"none"}); L(W,"M-200 1180 H1280",C.ink,6);
  R(W,560,200,400,190,22,"#1E2430"); T(W,760,250,"نوبت فعلی",44,"#F6E6C8",400);
  h.n12=T(W,760,330,fa(12),92,"#FF7A5C",700); h.n13=T(W,760,330,fa(13),92,"#FF7A5C",700,{opacity:0});
  const ck=g(W,{transform:"translate(260 330)"}); O(tex(ck),0,0,120,120,C.cream);
  for(let i=0;i<12;i++){ const a=i*Math.PI/6; L(ck,`M${Math.sin(a)*96} ${-Math.cos(a)*96} L${Math.sin(a)*108} ${-Math.cos(a)*108}`,C.ink,5); }
  h.hr=L(ck,"M0 0 L0 -70",C.ink,9); h.mn=L(ck,"M0 0 L0 -96",C.red,6); el("circle",{r:9,fill:C.ink},ck);
  h.ckLines=g(ck); for(const r of [140,160]) L(h.ckLines,`M${-r*0.6} ${-r*0.8} A${r} ${r} 0 0 1 ${r*0.6} ${-r*0.8}`,C.ink,4,{opacity:.5});
  h.heads=[];
  const people=[[200,"#7C9C6B","sleepy","old"],[480,"#8E6FA8","open","scarf"],[770,"#C9A04A","sleepy","man"]];
  for(const [x,col,md,kind] of people){ const pp=g(W,{transform:`translate(${x} 880) scale(.9)`}); P(tex(pp),"M-130 300 C-130 140 -100 70 -50 50 L50 50 C100 70 130 140 130 300Z",col);
    const hw=g(pp); h.heads.push(hw); const hh=g(hw,{transform:"translate(0 -60)"});
    if(kind==="scarf") P(tex(hh),"M-118 120 C-140 -40 -100 -136 0 -140 C100 -136 140 -40 118 120 C80 90 -80 90 -118 120Z","#C8644A");
    head(hh,md);
    if(kind==="scarf") P(tex(hh),"M-96 -6 C-98 -90 -50 -120 0 -120 C50 -120 98 -90 96 -6 C80 -60 -80 -60 -96 -6Z","#C8644A");
    if(kind==="old"){ P(hh,"M-96 -6 C-104 -80 -60 -122 0 -124 C62 -126 104 -88 98 -8 C86 -40 70 -56 40 -60 C30 -44 -6 -40 -30 -52 C-50 -40 -78 -34 -96 -6Z","#C9C6C2"); P(hh,"M-40 70 Q0 40 40 70 Q0 96 -40 70Z","#C9C6C2",{"stroke-width":4}); }
  }
  R(tex(W),60,1150,940,70,20,C.woodD); for(const x of [120,940]) R(W,x-12,1210,24,170,8,C.ink);
  h.ticketArm=g(W,{transform:"translate(560 1260) rotate(-6) scale(1.05)"}); const tk=h.ticketArm;
  arm(tk,"M260 700 C220 300 120 170 40 120",C.sweater);
  h.ticket=g(tk); P(tex(h.ticket),"M-170 -170 H170 V170 l-20 -14 l-20 14 l-20 -14 l-20 14 l-20 -14 l-20 14 l-20 -14 l-20 14 l-20 -14 l-20 14 l-20 -14 l-20 14 l-20 -14 l-20 14 l-20 -14 l-20 14 l-10 -14 Z",C.cream);
  T(h.ticket,0,-110,"نوبت شما",44,C.ink,400); h.n87=T(h.ticket,0,20,fa(87),190,C.red,700);
  h.ball=g(tk); O(tex(h.ball),0,0,90,80,C.cream); L(h.ball,"M-50 -20 l30 20 l-10 30 M20 -50 l10 30 l30 0 M-20 40 l30 -10",C.ink,5);
  gsap.set(h.ball,{autoAlpha:0});
  hand(tk,40,130,1.4,-20);
  h.growl=g(W,{transform:"translate(300 1520)"}); L(h.growl,"M0 0 q16 -20 32 0 t32 0 t32 0 t32 0",C.ink,7); L(h.growl,"M40 50 q16 -20 32 0 t32 0 t32 0",C.ink,7);
  R(tex(h.growl),-40,-170,300,100,50,C.white); T(h.growl,110,-122,"قار و قور",46,C.ink,700);
  sc.h=h; return sc; })();

// =============== 5. PHONE ===============
const s5=(()=>{ const sc=scene("phone"), W=sc.cam, h={};
  R(W,-200,-200,1480,2320,0,C.mustard,{stroke:"none"});
  for(let i=0;i<11;i++) L(W,`M${-300+i*160} -200 l300 2300`,"#D59A38",14,{opacity:.55});
  const sw=560, sh=Math.round(560*1845/1079), px=540-sw/2, py=150;
  h.ph=g(W); const ph=h.ph;
  gripLeft(ph,px-6,py+sh*0.62,C.pjB);
  R(ph,px-26,py-30,sw+52,sh+60,70,"#22252C");
  el("clipPath",{id:"scr2"},ph).appendChild(el("rect",{x:px,y:py,width:sw,height:sh,rx:46}));
  el("image",{href:"site_home.jpg",x:px,y:py,width:sw,height:sh,"clip-path":"url(#scr2)",preserveAspectRatio:"none"},ph);
  O(ph,540,py-6,40,9,"#22252C",{stroke:"none"});
  const tx=px+sw*0.5, ty=py+sh*0.881; h.tap=[tx,ty];
  h.ripples=[]; for(const r of [52,80,108]) h.ripples.push(el("circle",{cx:tx,cy:ty,r,fill:"none",stroke:C.white,"stroke-width":7},ph));
  h.ptr=g(ph); pointer(h.ptr,tx+6,ty+4,-22,C.pjB);
  h.ok=g(W,{transform:"translate(900 170)"}); const ok=g(h.ok); O(ok,0,0,72,72,C.green); L(ok,"M-30 2 L-8 26 L34 -24",C.white,15);
  sc.h=h; return sc; })();

// =============== 6. DOOR ===============
const s6=(()=>{ const sc=scene("door"), W0=sc.cam, h={};
  R(W0,-200,-200,1480,2320,0,C.wallWarm,{stroke:"none"}); R(W0,-200,1440,1480,800,0,C.floor,{stroke:"none"});
  const W=g(W0,{transform:"translate(0 -120)"});
  L(W,"M-200 1560 H1280",C.ink,6);
  R(W,520,420,460,1150,10,"#F7EFE0"); R(W,545,445,410,1120,6,"#BFD3D6");
  h.samp=g(W); sampler(h.samp,{x:760,y:990,s:1.05}); kitCase(h.samp,620,1360,1.0);
  h.doorOpen=g(W); P(tex(h.doorOpen),"M955 445 L1060 400 L1060 1610 L955 1565Z",C.woodD); el("circle",{cx:1040,cy:1010,r:12,fill:C.mustard,stroke:C.ink,"stroke-width":4},h.doorOpen);
  h.doorClosed=g(W); R(tex(h.doorClosed),545,445,410,1120,6,C.woodD); el("circle",{cx:600,cy:1010,r:14,fill:C.mustard,stroke:C.ink,"stroke-width":4},h.doorClosed);
  R(h.doorClosed,610,560,280,360,10,"none",{stroke:"#7A5236","stroke-width":6}); R(h.doorClosed,610,1000,280,420,10,"none",{stroke:"#7A5236","stroke-width":6});
  P(tex(W),"M560 1600 H960 L990 1680 H530Z",C.sweater);
  const m=man(W,{x:250,y:1140,s:1.15,mood:"happy",outfit:"pajama"});
  h.wave=g(m); arm(h.wave,"M130 120 C220 60 230 -60 210 -150",C.pjB); hand(h.wave,206,-176,1.1,10);
  const lg=tex(m); R(lg,-110,250,90,300,20,C.pjB); R(lg,20,250,90,300,20,C.pjB);
  P(m,"M-120 540 h110 v34 h-120Z","#E7C9A0"); P(m,"M10 540 h110 v34 h-110Z","#E7C9A0");
  h.bell=g(W); for(const r of [1,2,3]) L(h.bell,`M${500-r*26} ${880-r*30} q-30 ${40+r*20} 0 ${80+r*40}`,C.mustard,8);
  h.chip=g(W0,{transform:"translate(540 300)"}); R(tex(h.chip),-230,-75,460,150,75,C.white);
  const sun=g(h.chip,{transform:"translate(140 0)"}); O(sun,0,0,34,34,C.mustard); for(let i=0;i<8;i++){const a=i*Math.PI/4; L(sun,`M${Math.sin(a)*46} ${-Math.cos(a)*46} L${Math.sin(a)*60} ${-Math.cos(a)*60}`,C.mustard,7);}
  T(h.chip,-40,4,"از ۶ صبح",62,C.ink,700);
  sc.h=h; return sc; })();

// =============== 7. TEA ===============
const s7=(()=>{ const sc=scene("tea"), W0=sc.cam, h={};
  R(W0,-200,-200,1480,2320,0,"#DCE9DF",{stroke:"none"}); R(W0,-200,1300,1480,900,0,C.floor,{stroke:"none"});
  const W=g(W0,{transform:"translate(0 -200)"}); L(W,"M-200 1500 H1280",C.ink,6);
  const ck=g(W,{transform:"translate(780 380)"}); O(tex(ck),0,0,150,150,C.cream);
  h.arc=el("path",{d:arcPath(132,0),fill:C.tealL,opacity:.85},ck);
  for(let i=0;i<12;i++){ const a=i*Math.PI/6; L(ck,`M${Math.sin(a)*120} ${-Math.cos(a)*120} L${Math.sin(a)*136} ${-Math.cos(a)*136}`,C.ink,6); }
  h.mn=L(ck,"M0 0 L0 -100",C.ink,10); L(ck,`M0 0 L${-70} ${-24}`,C.ink,12); el("circle",{r:11,fill:C.ink},ck);
  h.badge=g(W,{transform:"translate(330 380) rotate(-8)"}); const bd=g(h.badge); R(tex(bd),-200,-80,400,160,80,C.teal); T(bd,0,4,"فقط ۱۰ دقیقه",64,C.white,700);
  R(tex(W),60,1020,960,360,80,"#8FB7A8"); R(tex(W),30,1240,1020,320,60,"#7FA898");
  const m=man(W,{x:540,y:1080,s:1.15,mood:"happy",outfit:"pajama"});
  arm(m,"M-140 120 C-180 220 -120 300 -20 290",C.pjB);
  const gl=g(m,{transform:"translate(10 230)"}); P(gl,"M-40 -60 L40 -60 L30 40 L-30 40Z","#C0552F",{opacity:.9}); P(gl,"M-50 40 H50 L44 56 H-44Z",C.mustard);
  h.steam=[]; for(const dx of [-14,14]) h.steam.push(L(gl,`M${dx} -80 q-14 -30 0 -60 t0 -60`,C.white,6,{opacity:.9}));
  hand(m,-20,280,1.1,0);
  function nochip(y,label,icon){ const o=g(W0,{transform:`translate(540 ${y})`}); const c=g(o); R(tex(c),-300,-62,600,124,62,C.white);
    T(c,30,2,label,54,C.ink,700); const x=g(c,{transform:"translate(-230 0)"}); O(x,0,0,40,40,C.red); L(x,"M-16 -16 L16 16 M16 -16 L-16 16",C.white,9); return c; }
  h.chipQ=nochip(1260,"بدون صف"); h.chipT=nochip(1410,"بدون ترافیک");
  sc.h=h; return sc; })();

// =============== 8. RESULT + AI ===============
const s8=(()=>{ const sc=scene("result"), W=sc.cam, h={};
  R(W,-200,-200,1480,2320,0,"#E2F0EE",{stroke:"none"});
  for(const [x,y,r] of [[150,300,60],[930,520,40],[120,1250,46],[960,1150,70]]) el("circle",{cx:x,cy:y,r,fill:"#CFE6E2"},W);
  const ph=g(W); R(ph,240,170,600,1180,70,"#22252C"); R(ph,268,200,544,1120,46,C.cream,{stroke:"none"});
  R(ph,268,200,544,130,0,C.teal,{stroke:"none"}); el("image",{href:"app-icon-tide.png",x:700,y:228,width:76,height:76},ph);
  T(ph,520,266,"جواب آزمایش شما",42,C.white,700);
  h.bars=[]; const labels=["ویتامین D","قند خون","کلسترول","آهن"];
  labels.forEach((lb,i)=>{ const y=410+i*120; T(ph,770,y-8,lb,34,C.ink,700,{"text-anchor":"start"}); R(ph,310,y+24,460,26,13,"#E3DED3",{stroke:"none"});
    const b=el("rect",{x:310,y:y+24,width:460,height:26,rx:13,fill:i===0?C.mustard:C.tealL},ph); h.bars.push(b);
    const ck=g(ph,{transform:`translate(330 ${y})`}); O(ck,0,0,22,22,C.green,{"stroke-width":4}); L(ck,"M-9 0 L-2 8 L10 -8",C.white,5); h.bars.push(ck); });
  h.ai=g(W,{transform:"translate(540 960)"}); const ai=g(h.ai);
  R(tex(ai),-250,-60,500,120,60,C.sweater); T(ai,20,2,"تفسیر آنلاین هوشمند",44,C.white,700);
  const sp=g(ai,{transform:"translate(-200 0)"}); P(sp,"M0 -30 L8 -8 L30 0 L8 8 L0 30 L-8 8 L-30 0 L-8 -8Z","#FFE07A",{"stroke-width":4});
  h.bub=g(W); R(tex(h.bub),300,1060,480,210,40,C.white); P(h.bub,"M700 1268 L740 1310 L660 1268Z",C.white,{"stroke-width":5});
  h.dots=g(h.bub); for(const x of [500,540,580]) el("circle",{cx:x,cy:1165,r:14,fill:C.grey},h.dots);
  h.lines=[]; [[340,1110,400],[340,1160,360],[340,1210,280]].forEach(([x,y,w])=>h.lines.push(el("rect",{x:780-40-w,y,width:w,height:22,rx:11,fill:"#BFB8AC"},h.bub)));
  h.spark=g(W); for(const [x,y,s] of [[230,860,1],[860,820,.8],[880,1080,.6]]){ const st=g(h.spark,{transform:`translate(${x} ${y}) scale(${s})`}); P(st,"M0 -40 L10 -10 L40 0 L10 10 L0 40 L-10 10 L-40 0 L-10 -10Z","#FFE07A",{"stroke-width":4}); }
  sc.h=h; return sc; })();

// =============== 9. CTA ===============
const s9=(()=>{ const sc=scene("cta"), W=sc.cam, h={};
  R(W,-200,-200,1480,2320,0,C.cream,{stroke:"none"});
  h.burst=g(W,{transform:"translate(540 560)"}); for(let i=0;i<16;i++){ const a=i*Math.PI/8; L(h.burst,`M${Math.sin(a)*250} ${-Math.cos(a)*250} L${Math.sin(a)*330} ${-Math.cos(a)*330}`,i%2?C.mustard:C.tealL,12); }
  h.disc=el("circle",{cx:540,cy:560,r:230,fill:"#E2F0EE"},W);
  h.logo=g(W); el("image",{href:"app-icon-tide.png",x:410,y:430,width:260,height:260},h.logo);
  h.name=T(W,540,790,"نِمونِت",110,C.teal,700);
  h.countG=g(W); h.count=T(h.countG,540,935,"+۰",120,C.sweater,700,{direction:"ltr"});
  h.sub=T(W,540,1050,"آزمایش در خانه · از ۶ صبح",50,C.ink,700);
  h.chips=[]; [["تهران",680],["مشهد",400]].forEach(([c,x])=>{ const cg=g(W,{transform:`translate(${x} 1170)`}); R(tex(cg),-120,-52,240,104,52,C.white); T(cg,18,2,c,50,C.ink,700); el("circle",{cx:-62,cy:0,r:13,fill:C.sweater,stroke:C.ink,"stroke-width":4},cg); h.chips.push(cg); });
  h.btn=g(W,{transform:"translate(540 1330)"}); const bt=g(h.btn); R(tex(bt),-350,-72,700,144,72,C.sweater); T(bt,0,0,"همین الان نوبت بگیر",62,C.white,700);
  h.url=T(W,540,1460,"nemonet.ir",56,C.navy,700,{direction:"ltr"});
  h.arrow=g(W,{transform:"translate(540 1600)"}); P(h.arrow,"M-46 -64 H46 V0 H92 L0 100 L-92 0 H-46Z",C.green);
  sc.h=h; return sc; })();

// ---------------- transition overlays ----------------
const flash=el("rect",{x:0,y:0,width:1080,height:1920,fill:"#FFFFFF",opacity:0},fx);
const rw=g(fx); gsap.set(rw,{autoAlpha:0});
for(let i=0;i<14;i++) el("rect",{x:0,y:i*140+30,width:1080,height:10,fill:"#FFFFFF",opacity:.35},rw);
const rwIcon=g(rw,{transform:"translate(540 860)"}); R(rwIcon,-170,-110,340,220,60,"#2B2730",{opacity:.85,stroke:"none"});
P(rwIcon,"M-10 -60 L-110 0 L-10 60Z",C.white,{stroke:"none"}); P(rwIcon,"M100 -60 L0 0 L100 60Z",C.white,{stroke:"none"});
const wipe=el("circle",{cx:540,cy:1100,r:0,fill:"#E2F0EE"},fx);

// =============== TIMELINE ===============
const T1=3.45, T2=5.05, T3=9.0, T4=11.05, T5=13.1, T6=15.65, T7=19.3, T8=22.1;
const hh1=s1.h;
// --- scene 1: hook
show(s1,0);
tl.fromTo(s1.cam,{scale:2.7,svgOrigin:"175 1000"},{scale:1,svgOrigin:"175 1000",duration:1.25,ease:"power3.inOut"},0);
tl.fromTo(hh1.ckInner,{rotation:-7,transformOrigin:"50% 60%"},{rotation:7,duration:.06,repeat:27,yoyo:true,ease:"none"},0);
tl.to(hh1.ring,{autoAlpha:0,duration:.06,repeat:27,yoyo:true,ease:"none"},0);
tl.set(hh1.ring,{autoAlpha:0},1.75);
tl.fromTo(hh1.hand,{rotation:-4,transformOrigin:"50% 50%"},{rotation:5,duration:.25,repeat:7,yoyo:true,ease:"sine.inOut"},.4);
tl.fromTo(hh1.head,{y:0},{y:8,duration:.5,repeat:5,yoyo:true,ease:"sine.inOut"},0);
pop(hh1.growl,2.3,{dur:.3}); tl.to(hh1.growl,{x:6,duration:.08,repeat:7,yoyo:true},2.6);
tl.to(s1.cam,{scale:1.12,svgOrigin:"540 1000",duration:2.0,ease:"sine.inOut"},1.3);
// zoom into the window → traffic
tl.to(s1.cam,{scale:5,svgOrigin:"805 440",duration:.42,ease:"power3.in"},T1-.38);
hide(s1,T1);
// --- scene 2: traffic
show(s2,T1);
tl.fromTo(s2.cam,{scale:1.35,svgOrigin:"540 1400"},{scale:1,duration:.5,ease:"power3.out"},T1);
tl.fromTo(s2.h.laneA,{x:0},{x:-520,duration:T2-T1,ease:"none"},T1);
tl.fromTo(s2.h.laneB,{x:0},{x:420,duration:T2-T1,ease:"none"},T1);
tl.fromTo(s2.h.me.b,{y:0},{y:-6,duration:.1,repeat:15,yoyo:true,ease:"none"},T1);
tl.fromTo(s2.h.puffs,{x:0,autoAlpha:1},{x:-120,autoAlpha:0,duration:.5,repeat:2},T1);
pop(s2.h.honk1,3.7,{dur:.25}); pop(s2.h.bubble,3.72,{dur:.35});
tl.to([s2.h.honk1,s2.h.bubble],{scale:1.12,duration:.1,repeat:5,yoyo:true},4.0);
// whip to queue
tl.to(s2.cam,{x:-1080,duration:.36,ease:"power2.inOut"},T2-.2);
hide(s2,T2+.17);
// --- scene 3: queue
show(s3,T2-.2);
tl.fromTo(s3.cam,{x:1080},{x:0,duration:.36,ease:"power2.inOut"},T2-.2);
tl.fromTo(s3.h.mn,{rotation:0,transformOrigin:"50% 100%"},{rotation:360*5,duration:T3-T2,ease:"none"},T2);
tl.fromTo(s3.h.hr,{rotation:0,transformOrigin:"50% 100%"},{rotation:150,duration:T3-T2,ease:"none"},T2);
s3.h.heads.forEach((hd,i)=>tl.fromTo(hd,{rotation:-4,transformOrigin:"50% 100%"},{rotation:4,duration:.7+i*.15,repeat:5,yoyo:true,ease:"sine.inOut"},T2));
tl.set(s3.h.n12,{autoAlpha:0},6.4); tl.set(s3.h.n13,{autoAlpha:1},6.4);
tl.fromTo(s3.h.n13,{scale:1.4,transformOrigin:"50% 50%"},{scale:1,duration:.3},6.4);
gsap.set(s3.h.growl,{autoAlpha:0}); pop(s3.h.growl,ws(7),{dur:.3}); tl.to(s3.h.growl,{autoAlpha:0,duration:.2},ws(8)-.1);
tl.to(s3.cam,{scale:1.75,svgOrigin:"560 1180",duration:.7,ease:"power3.inOut"},ws(8)-.1);
tl.fromTo(s3.h.n87,{scale:1,transformOrigin:"50% 50%"},{scale:1.25,duration:.18,repeat:1,yoyo:true},ws(11));
// crumple
tl.to(s3.h.ticket,{scale:.15,rotation:-200,transformOrigin:"50% 50%",duration:.32,ease:"power3.in"},8.6);
tl.fromTo(s3.h.ball,{autoAlpha:0,scale:.3,transformOrigin:"50% 50%"},{autoAlpha:1,scale:1,duration:.2,ease:"back.out(3)"},8.86);
hide(s3,T3);
// --- rewind flashes 9.0–9.5 (traffic → alarm), then idea scene
tl.set(rw,{autoAlpha:1},T3); tl.set(rw,{autoAlpha:0},9.52);
tl.set(s2.wrap,{autoAlpha:1},T3); tl.set(s2.cam,{x:0,scale:1},T3); tl.set(s2.h.laneA,{x:-300},T3); tl.to(s2.h.laneA,{x:0,duration:.25,ease:"none"},T3); tl.set(s2.wrap,{autoAlpha:0},9.25);
tl.set(s1.wrap,{autoAlpha:1},9.25); tl.set(s1.cam,{scale:1.1,svgOrigin:"540 1000"},9.25); tl.set(s1.wrap,{autoAlpha:0},9.52);
tl.fromTo(rwIcon,{scale:.9,transformOrigin:"50% 50%"},{scale:1.1,duration:.12,repeat:3,yoyo:true},T3);
show(s4,9.52);
tl.fromTo(s4.cam,{scale:1.15,svgOrigin:"540 1000"},{scale:1,duration:.5,ease:"power3.out"},9.52);
pop(s4.h.bulb,9.68,{dur:.45});
tl.fromTo(s4.h.rays,{rotation:0,transformOrigin:"50% 50%"},{rotation:45,duration:1.3,ease:"none"},9.7);
tl.fromTo(s4.h.head,{y:0},{y:-10,duration:.3,repeat:3,yoyo:true,ease:"sine.inOut"},9.7);
// phone rises
hide(s4,T4+.35);
show(s5,T4);
tl.fromTo(s5.cam,{y:1900},{y:0,duration:.45,ease:"power3.out"},T4);
tl.fromTo(s5.h.ptr,{x:180,y:420},{x:0,y:0,duration:.55,ease:"power2.inOut"},11.6);
tl.to(s5.h.ptr,{scale:.94,transformOrigin:"50% 0%",duration:.08,repeat:1,yoyo:true},ws(23));
s5.h.ripples.forEach((r,i)=>{ gsap.set(r,{autoAlpha:0}); tl.fromTo(r,{autoAlpha:1,scale:.4,transformOrigin:"50% 50%"},{autoAlpha:0,scale:1.3,duration:.6},ws(23)+i*.08); });
gsap.set(s5.h.ok,{autoAlpha:0}); pop(s5.h.ok,ws(23)+.15,{dur:.4});
// zoom through the phone screen → door
tl.to(s5.cam,{scale:4.5,svgOrigin:"540 760",duration:.4,ease:"power3.in"},T5-.36);
tl.to(flash,{opacity:.9,duration:.12},T5-.12); tl.to(flash,{opacity:0,duration:.25},T5);
hide(s5,T5);
// --- door
show(s6,T5);
tl.fromTo(s6.cam,{scale:1.2,svgOrigin:"540 900"},{scale:1,duration:.6,ease:"power3.out"},T5);
gsap.set([s6.h.samp,s6.h.doorOpen,s6.h.bell],{autoAlpha:0});
pop(s6.h.chip,ws(25)-.05,{dur:.45});
pop(s6.h.bell,13.95,{dur:.2}); tl.to(s6.h.bell,{x:-10,duration:.07,repeat:5,yoyo:true},14.0); tl.to(s6.h.bell,{autoAlpha:0,duration:.2},14.6);
tl.to(s6.h.doorClosed,{scaleX:0,transformOrigin:"100% 50%",duration:.35,ease:"power2.in"},ws(27));
tl.set(s6.h.doorOpen,{autoAlpha:1},ws(27)+.33);
tl.fromTo(s6.h.samp,{autoAlpha:0,x:120},{autoAlpha:1,x:0,duration:.5,ease:"power2.out"},ws(27)+.2);
tl.fromTo(s6.h.wave,{rotation:-8,transformOrigin:"0% 100%"},{rotation:8,duration:.22,repeat:6,yoyo:true,ease:"sine.inOut"},ws(28));
// whip down to tea
tl.to(s6.cam,{y:-1920,duration:.38,ease:"power2.inOut"},T6-.22);
hide(s6,T6+.17);
// --- tea
show(s7,T6-.22);
tl.fromTo(s7.cam,{y:1920},{y:0,duration:.38,ease:"power2.inOut"},T6-.22);
const arcObj={d:0}; tl.to(arcObj,{d:60,duration:1.3,ease:"power1.inOut",onUpdate:()=>s7.h.arc.setAttribute("d",arcPath(132,arcObj.d))},ws(30));
tl.fromTo(s7.h.mn,{rotation:0,transformOrigin:"50% 100%"},{rotation:60,duration:1.3,ease:"power1.inOut"},ws(30));
gsap.set(s7.h.badge,{autoAlpha:0}); pop(s7.h.badge,ws(31)-.05,{dur:.45});
s7.h.steam.forEach((st,i)=>tl.fromTo(st,{y:0,autoAlpha:.9},{y:-40,autoAlpha:0,duration:.9,repeat:3,ease:"none"},T6+i*.4));
gsap.set([s7.h.chipQ,s7.h.chipT],{autoAlpha:0});
tl.fromTo(s7.h.chipQ,{x:-700,autoAlpha:0},{x:0,autoAlpha:1,duration:.4,ease:"back.out(1.6)"},ws(33)-.05);
tl.fromTo(s7.h.chipT,{x:700,autoAlpha:0},{x:0,autoAlpha:1,duration:.4,ease:"back.out(1.6)"},ws(35)-.05);
// circle wipe → result
tl.set(wipe,{attr:{r:0}},T7-.4); tl.to(wipe,{attr:{r:2300},duration:.42,ease:"power2.in"},T7-.4);
hide(s7,T7); show(s8,T7); tl.set(wipe,{attr:{r:0}},T7+.02);
// --- result + AI
tl.fromTo(s8.cam,{scale:1.1,svgOrigin:"540 760"},{scale:1,duration:.6},T7);
s8.h.bars.forEach((b,i)=>{ if(i%2===0) tl.fromTo(b,{attr:{width:0}},{attr:{width:[300,380,340,260][i/2]},duration:.45,ease:"power2.out"},19.4+i*.12); else pop(b,19.7+i*.12,{dur:.3}); });
gsap.set([s8.h.ai,s8.h.bub,s8.h.spark],{autoAlpha:0});
pop(s8.h.ai,ws(40)-.05,{dur:.5});
pop(s8.h.spark,ws(40)+.1,{dur:.5}); tl.to(s8.h.spark,{rotation:8,transformOrigin:"50% 50%",duration:1.5,ease:"none"},ws(40)+.1);
pop(s8.h.bub,20.7,{dur:.35});
tl.fromTo(s8.h.dots.children,{y:0},{y:-14,duration:.16,repeat:3,yoyo:true,stagger:.08},20.8);
tl.set(s8.h.dots,{autoAlpha:0},ws(42)-.05);
s8.h.lines.forEach((l,i)=>{ const w=+l.getAttribute("width"), x=+l.getAttribute("x"); tl.fromTo(l,{attr:{width:0,x:x+w}},{attr:{width:w,x},duration:.3,ease:"none"},ws(42)-.05+i*.22); });
// zoom-through → CTA
tl.to(s8.cam,{scale:3.5,svgOrigin:"540 960",duration:.38,ease:"power3.in"},T8-.36);
tl.to(flash,{opacity:.9,duration:.1},T8-.1); tl.to(flash,{opacity:0,duration:.3},T8);
hide(s8,T8);
// --- CTA
show(s9,T8);
const H9=s9.h;
gsap.set([H9.logo,H9.disc,H9.name,H9.countG,H9.sub,H9.btn,H9.url,H9.arrow,H9.burst,...H9.chips],{autoAlpha:0});
pop(H9.disc,T8,{dur:.4}); pop(H9.logo,T8+.05,{dur:.6,ease:"back.out(2.6)"});
tl.fromTo(H9.burst,{autoAlpha:1,scale:.6,transformOrigin:"50% 50%"},{scale:1.35,autoAlpha:0,duration:.7},T8+.15);
pop(H9.name,T8+.3,{dur:.4});
const cnt={v:0}; tl.set(H9.countG,{autoAlpha:1},ws(44)-.05);
tl.fromTo(cnt,{v:0},{v:5000,duration:1.2,ease:"power2.out",onUpdate:()=>{ H9.count.textContent="+"+fa(Math.round(cnt.v/10)*10); }},ws(46)-.3);
tl.fromTo(H9.countG,{scale:1,transformOrigin:"50% 50%"},{scale:1.18,duration:.16,repeat:1,yoyo:true},ws(48));
pop(H9.sub,ws(48),{dur:.35});
pop(H9.chips[0],ws(51)-.05,{dur:.4}); pop(H9.chips[1],ws(53)-.05,{dur:.4});
pop(H9.btn,ws(54)-.05,{dur:.45});
tl.to(H9.btn,{scale:1.06,transformOrigin:"50% 50%",duration:.3,repeat:3,yoyo:true,ease:"sine.inOut"},ws(54)+.45);
pop(H9.url,ws(55),{dur:.3}); pop(H9.arrow,ws(56),{dur:.35});
tl.to(H9.arrow,{y:"+=24",duration:.28,repeat:3,yoyo:true,ease:"sine.inOut"},ws(56)+.35);
tl.to(s9.cam,{scale:1.04,svgOrigin:"540 900",duration:DUR-T8,ease:"none"},T8);
tl.set({}, {}, DUR);

// ---------------- captions (word-by-word, RTL) ----------------
// [display tokens, word index ranges] — digits shown as Persian numerals
const CH = [
 [["آزمایش",[0]],["خون",[1]],["یعنی…",[2]]], [["نصف",[3]],["روزت؟",[4]]],
 [["ترافیک…",[5]]], [["صف…",[6]]], [["گرسنگی…",[7]]], [["نوبت",[8]],["۸۷!",[9,10,11]]],
 [["یه",[12]],["لحظه!",[13]]], [["یه",[14]],["راه",[15]],["دیگه",[16]],["هم",[17]],["هست.",[18]]],
 [["از",[19]],["سایت",[20]],["نِمونِت",[21]]], [["نوبت",[22]],["بگیر",[23]]],
 [["از",[24]],["۶",[25]],["صبح،",[26]]], [["نمونه‌گیر",[27]],["میاد",[28]],["خونه‌ت!",[29]]],
 [["فقط",[30]],["۱۰",[31]],["دقیقه",[32]]], [["بدون",[33]],["صف،",[34]]], [["بدون",[35]],["ترافیک",[36]]],
 [["جوابت",[37]],["هم",[38]],["با",[39]]], [["تفسیر",[40]],["آنلاین",[41]],["هوشمند",[42]]],
];
const capLayer=document.getElementById("captions"); const CAPS=[];
const CY=1610, CS=62;
CH.forEach((chunk,ci)=>{
  const grp=g(capLayer); const bg=el("rect",{fill:"#2B2730",opacity:.85,rx:CS*.55},grp);
  const t=el("text",{x:540,y:CY,"font-size":CS,"font-weight":700,"text-anchor":"middle","dominant-baseline":"central",direction:"rtl",fill:C.white},grp);
  const spans=chunk.map(([txt,idx],k)=>{ const sp=el("tspan",{},t); sp.textContent=(k?" ":"")+txt; return {sp,s:ws(idx[0]),e:we(idx[idx.length-1])}; });
  const bb=t.getBBox(); const px=CS*.6, pv=CS*.24;
  Object.entries({x:bb.x-px,y:bb.y-pv,width:bb.width+2*px,height:bb.height+2*pv}).forEach(([k,v])=>bg.setAttribute(k,v));
  grp.style.visibility="hidden";
  CAPS.push({grp,spans,start:spans[0].s-0.06});
});
CAPS.forEach((c,i)=>{ const next=CAPS[i+1]; c.end = next ? Math.min(next.start, c.spans[c.spans.length-1].e+0.6) : c.spans[c.spans.length-1].e+0.3; });
function updateCaptions(t){
  for(const c of CAPS){
    const on = t>=c.start && t<c.end && t<T8;
    c.grp.style.visibility = on?"visible":"hidden";
    if(!on) continue;
    const k=Math.min(1,(t-c.start)/0.14), sc=0.86+0.14*(1-Math.pow(1-k,3));
    c.grp.setAttribute("transform",`translate(540 ${CY}) scale(${sc}) translate(-540 ${-CY})`);
    for(const s of c.spans){ const cur=t>=s.s-0.02 && t<s.e+0.05, done=t>=s.e+0.05;
      s.sp.setAttribute("fill", cur? "#FFD166" : C.white); s.sp.setAttribute("fill-opacity", (cur||done)?1:0.5); }
  }
}

window.DUR=DUR;
window.seek=(t)=>{ t=Math.max(t,0.001); tl.seek(t,false); updateCaptions(t); };
window.ready=true;
