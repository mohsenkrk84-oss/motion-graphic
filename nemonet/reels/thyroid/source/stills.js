const world=document.getElementById("world");
const GY=1180; // ground line
const LEGLEN=FIG.uLeg+FIG.fLeg;
function fig(p,x,pose,opts={}){ const f=new Fig(p,opts); f.set(Object.assign({x,y:GY-LEGLEN*(opts.scale||1)},pose)); return f; }

function plate(p,x,y){ const k=pencil(g(p,{transform:`translate(${x} ${y})`})); el("ellipse",{cx:0,cy:0,rx:70,ry:20,fill:PAPER,stroke:INK,"stroke-width":6},k); el("ellipse",{cx:0,cy:-4,rx:18,ry:7,fill:"#7FAF6A",stroke:INK,"stroke-width":4},k); return k; }
function dumbbell(p,x,y,r=0){ const k=pencil(g(p,{transform:`translate(${x} ${y}) rotate(${r})`})); line(k,"M-46 0 L46 0",9); for(const s of [-1,1]) el("rect",{x:s*46-12,y:-30,width:24,height:60,rx:6,fill:INK},k); return k; }
function pillow(p,x,y){ const k=pencil(g(p,{transform:`translate(${x} ${y})`})); shape(k,"M-80 -36 Q0 -54 80 -36 Q92 0 80 36 Q0 54 -80 36 Q-92 0 -80 -36Z",PAPER,6); txt(k,40,-80,"z",44,INK,"Hand"); txt(k,70,-120,"z",56,INK,"Hand"); return k; }
function scaleObj(p,x,y,deg=0){ const k=pencil(g(p,{transform:`translate(${x} ${y})`})); shape(k,"M-120 0 L120 0 L110 34 L-110 34Z",PAPER,6);
  el("path",{d:"M-44 22 A44 44 0 0 1 44 22",fill:"none",stroke:INK,"stroke-width":5},k); line(k,`M0 22 L${Math.sin(rad(deg))*36} ${22-Math.cos(rad(deg))*36}`,5,ORANGE); return k; }
function ballChain(p,ax,ay,bx,by,lab=true){ const k=pencil(g(p)); const n=7;
  for(let i=0;i<n;i++){ const t=(i+0.5)/n, x=ax+(bx-ax)*t, y=ay+(by-ay)*t+Math.sin(t*Math.PI)*30; el("ellipse",{cx:x,cy:y,rx:16,ry:10,fill:"none",stroke:INK,"stroke-width":5,transform:`rotate(${i%2?70:0} ${x} ${y})`},k); }
  circ(k,bx,by+40,86,"#4A4A4D",7); line(k,`M${bx-30} ${by+20} q12 -18 30 -20`,5,"#9A9A9A");
  if(lab){ const t=g(p,{transform:`translate(${bx} ${by+40})`}); txt(t,0,-18,"تیروئید",36,"#FFFFFF","Hand"); txt(t,0,24,"کم‌کار",36,"#FFFFFF","Hand"); }
  return k; }
function sampler(p,x,pose){ const f=new Fig(p,{extra:(F)=>{ shape(pencil(F.extraG),"M-56 -10 Q-60 -62 0 -60 Q58 -62 54 -6 Q60 40 34 60 L-40 60 Q-62 30 -56 -10Z",TEAL,6,{opacity:.9}); }});
  f.set(Object.assign({x,y:GY-LEGLEN},pose)); f.extraG.parentNode.insertBefore(f.extraG,f.head); return f; }
function tube(p,x,y,fill=1,rot=0){ const k=g(p,{transform:`translate(${x} ${y}) rotate(${rot})`}); const kk=pencil(k);
  shape(kk,"M-20 -90 L20 -90 L20 70 Q20 92 0 92 Q-20 92 -20 70Z",PAPER,6); if(fill>0.05) el("rect",{x:-14,y:92-150*fill,width:28,height:150*fill-6,rx:12,fill:"#B5413B"},kk);
  el("rect",{x:-26,y:-110,width:52,height:26,rx:6,fill:TEAL,stroke:INK,"stroke-width":5},kk); return k; }
function kit(p,x,y){ const k=g(p,{transform:`translate(${x} ${y})`}); const kk=pencil(k); line(kk,"M-26 -40 Q0 -70 26 -40",8); el("rect",{x:-70,y:-44,width:140,height:96,rx:14,fill:"#EDEDE8",stroke:INK,"stroke-width":6},kk);
  el("image",{href:"app-icon-tide.png",x:-24,y:-20,width:48,height:48},k); return k; }

const STILL={};
const SC=1.3;
const F=(x,pose,face)=>fig(world,x,Object.assign({},pose,face?{face}:{}),{scale:SC});
const lab=(f,s,o)=>{ const h=f.W(f.headPos); return label(world,h[0],h[1]-FIG.headR*SC-14,s,o); };
STILL.hook=()=>{ ground(world,GY);
  speedLines(world,560,GY-260,460,8); const o=F(720,runPose(.3,1),"happy"); lab(o,"بقیه");
  speedLines(world,180,GY-250,150,5,LIGHT); const m=F(280,Object.assign(runPose(.75,.5),{lean:18,headTilt:8}),"tired"); m.addSweat(); lab(m,"تو");
  caption(["همه‌چی رو امتحان کردی","و باز هم نشد؟"]); };
STILL.tries=()=>{ ground(world,GY);
  const m=F(540,{lean:0,aL1:205,aL2:-10,aR1:155,aR2:10},"sad"); lab(m,"تو");
  scaleObj(world,550,GY-6,-5);
  plate(world,180,700); label(world,180,640,"رژیم",{size:46});
  dumbbell(world,540,330,-12); label(world,540,250,"باشگاه",{size:46});
  pillow(world,900,700); label(world,900,600,"خواب بیشتر",{size:46});
  caption(["رژیم گرفتی، باشگاه رفتی،","بیشتر خوابیدی…"]); };
STILL.twist=()=>{ ground(world,GY);
  const m=F(300,Object.assign(walkPose(.2,.5),{lean:-6}),"shock"); lab(m,"تو");
  const ft=m.W(m.footLpos); ballChain(world,ft[0]+10,GY-8,600,GY-50,false);
  // magnifier over the ball with enlarged view
  const L=g(world,{transform:"translate(640 760)"});
  const inner=g(L,{"clip-path":"url(#lensClip)"}); el("rect",{x:-240,y:-240,width:480,height:480,fill:"#E6E6E2"},inner);
  const z=g(inner,{transform:"scale(2.1) translate(-600 -1170)"}); ballChain(z,420,1172,600,1130,true);
  circ(L,0,0,230,"none",12); line(pencil(L),"M165 165 L290 290",30);
  line(pencil(world),"M600 1150 L560 990",4,GREY,{"stroke-dasharray":"10 10"});
  caption(["شاید مشکل از تو نیست؛","شاید تیروئیدت کم‌کار شده!"]); };
STILL.symptoms=()=>{ ground(world,GY);
  const m=F(320,Object.assign(walkPose(.6,.35),{lean:16,headTilt:10}),"tired"); m.addSweat();
  const ft=m.W(m.footLpos); ballChain(world,ft[0]+8,GY-8,560,GY-50,true);
  const hd=m.W(m.headPos);
  const syms=[["خستگی",780,430],["سرمایی بودن",250,250],["ریزش مو",800,700],["بی‌حوصلگی",640,180]];
  for(const [s,x,y] of syms){ line(pencil(world),`M${x} ${y+56} L${hd[0]+(x>hd[0]?50:-20)} ${hd[1]-40}`,4,GREY,{"stroke-dasharray":"12 10"});
    const t=g(world,{transform:`translate(${x} ${y})`}); const k=pencil(t); shape(k,"M-150 -50 L150 -50 L150 50 L-150 50Z","#EDEDE8",5); txt(k,0,-2,s,48,INK,"Hand"); }
  caption("کم‌کاری تیروئید خیلی شایعه!"); };
STILL.solution=()=>{ ground(world,GY);
  const m=F(250,{lean:0,aL1:200,aL2:-10,aR1:205,aR2:-30},"happy"); lab(m,"تو");
  const s=new Fig(world,{scale:SC,extra:(Fg)=>{ shape(pencil(Fg.extraG),"M-56 -10 Q-60 -62 0 -60 Q58 -62 54 -6 Q60 40 34 60 L-40 60 Q-62 30 -56 -10Z",TEAL,6,{opacity:.9}); }});
  s.set({x:740,y:GY-LEGLEN*SC,face:"happy",lean:-2,aL1:140,aL2:30,aR1:180,aR2:0}); s.extraG.parentNode.insertBefore(s.extraG,s.head); lab(s,"نمونه‌گیر نِمونِت",{size:40});
  const hp=s.W(s.handLpos); tube(world,hp[0]-6,hp[1]-70,.85,-8);
  const hr=s.W(s.handRpos); kit(world,hr[0]+10,hr[1]+40);
  const lb=g(world,{transform:"translate(470 400)"}); const kk=pencil(lb); shape(kk,"M-150 -48 L150 -48 L150 48 L-150 48Z","#FFFFFF",5); txt(kk,0,0,"TSH + T4",58,TEAL,"Hand",800,{direction:"ltr"});
  line(pencil(world),`M500 450 L${hp[0]-6} ${hp[1]-160}`,4,GREY,{"stroke-dasharray":"12 10"});
  const br=pencil(g(world)); const ft=m.W(m.footLpos);
  for(const [dx,dy,r] of [[60,-20,20],[100,-50,-30],[140,-14,40]]) el("ellipse",{cx:ft[0]+dx,cy:GY+dy,rx:16,ry:10,fill:"none",stroke:INK,"stroke-width":5,transform:`rotate(${r} ${ft[0]+dx} ${GY+dy})`},br);
  for(const dx of [80,130]) line(br,`M${ft[0]+dx} ${GY-90} l-14 -22 M${ft[0]+dx+16} ${GY-90} l10 -24`,5,MUST);
  caption(["با یک آزمایش ساده TSH،","سلامت تیروئیدت رو بررسی کن"]); };
STILL.overtake=()=>{ ground(world,GY);
  speedLines(world,640,GY-270,560,9); const m=F(780,runPose(.3,1.15),"grin"); lab(m,"تو");
  const o=F(300,runPose(.7,.55),"shock"); lab(o,"بقیه");
  caption("قبل از رژیم بعدی…"); };
STILL.cta=()=>{
  const c=g(world);
  el("circle",{cx:540,cy:560,r:210,fill:"#EDEDE8",stroke:INK,"stroke-width":6,filter:"url(#pencil)"},c);
  el("image",{href:"app-icon-tide.png",x:420,y:440,width:240,height:240},c);
  txt(c,540,850,"تیروئیدت رو چک کن",86,INK,"Hand",800);
  txt(c,540,975,"پنل تیروئید TSH و T4 در منزل",50,INK,"Yekan",700);
  txt(c,540,1060,"از ۶ صبح - تهران و مشهد",50,"#555","Yekan",700);
  const b=g(c,{transform:"translate(540 1210)"}); el("rect",{x:-330,y:-70,width:660,height:140,rx:70,fill:TEAL,stroke:INK,"stroke-width":6,filter:"url(#pencil)"},b); txt(b,0,0,"همین الان نوبت بگیر",60,"#FFFFFF","Yekan",700);
  txt(c,540,1350,"nemonet.ir",56,INK,"Yekan",700,{direction:"ltr"});
  const ar=pencil(g(c,{transform:"translate(540 1480)"})); line(ar,"M0 -60 L0 50",9); line(ar,"M-36 18 L0 56 L36 18",9);
  caption("نِمونِت میاد خونه‌ت؛ همین الان نوبت بگیر",1640,50); };

window.showStill=(n)=>{ world.innerHTML=""; document.getElementById("captions").innerHTML=""; STILL[n](); };
window.ready=true;
STILL.cover=()=>{ ground(world,GY+120);
  const CS2=1.1, G=GY+120, FY2=G-LEGLEN*CS2;
  speedLines(world,600,G-230,420,8);
  const o=new Fig(world,{scale:CS2}); o.set(Object.assign({x:740,y:FY2,face:"happy"},runPose(.3,1))); const ho=o.W(o.headPos); label(world,ho[0],ho[1]-FIG.headR*CS2-14,"بقیه");
  const m=new Fig(world,{scale:CS2}); m.set(Object.assign({x:300,y:FY2,face:"tired",headTilt:8},runPose(.75,.5),{lean:18})); m.addSweat(); const hm=m.W(m.headPos); label(world,hm[0],hm[1]-FIG.headR*CS2-14,"تو");
  const ft=m.W(m.footLpos); ballChain(world,ft[0]+8,G-8,120,G-50,false);
  const t=g(world); const k=pencil(t);
  txt(k,540,330,"همه کار کردی",104,INK,"Hand",800); txt(k,540,470,"ولی باز هم نشد؟",104,ORANGE,"Hand",800);
  line(k,"M280 560 Q540 540 800 560",8,MUST);
  const b=g(world,{transform:"translate(540 1530)"}); el("rect",{x:-200,y:-48,width:400,height:96,rx:48,fill:"#EDEDE8",stroke:INK,"stroke-width":5,filter:"url(#pencil)"},b);
  el("image",{href:"app-icon-tide.png",x:70,y:-34,width:68,height:68},b); txt(b,-40,2,"نِمونِت",48,TEAL,"Hand",800);
};
