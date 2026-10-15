// Pencil stick-figure toolkit (SVG) — poses are plain numbers so GSAP can tween them.
const NS="http://www.w3.org/2000/svg";
const INK="#2A2A2C", GREY="#8C8C8C", LIGHT="#B9B9B6", TEAL="#167A80", ORANGE="#E0663F", MUST="#E3A236", PAPER="#D8D8D4";
function el(tag,a,p){ const e=document.createElementNS(NS,tag); for(const k in a) e.setAttribute(k,a[k]); if(p) p.appendChild(e); return e; }
function g(p,a={}){ return el("g",a,p); }
function line(p,d,w=8,col=INK,extra={}){ return el("path",Object.assign({d,fill:"none",stroke:col,"stroke-width":w,"stroke-linecap":"round","stroke-linejoin":"round"},extra),p); }
function shape(p,d,fill,w=7,extra={}){ return el("path",Object.assign({d,fill,stroke:INK,"stroke-width":w,"stroke-linejoin":"round","stroke-linecap":"round"},extra),p); }
function circ(p,cx,cy,r,fill="none",w=7,extra={}){ return el("circle",Object.assign({cx,cy,r,fill,stroke:INK,"stroke-width":w},extra),p); }
function txt(p,x,y,s,size,fill=INK,font="Hand",weight=700,extra={}){ const t=el("text",Object.assign({x,y,"font-size":size,fill,"font-family":font,"font-weight":weight,"text-anchor":"middle","dominant-baseline":"central",direction:"rtl"},extra),p); t.textContent= font==="Hand" ? handFix(s) : s; return t; }
// Marhey draws medial Persian ی (U+06CC) without dots; Arabic ي (U+064A) is identical except it keeps them
const handFix=s=>String(s).replace(/ی(?=[\u0600-\u06FF])/g,"ي");
const fa=n=>String(n).replace(/[0-9]/g,d=>"۰۱۲۳۴۵۶۷۸۹"[d]);
const rad=d=>d*Math.PI/180;
function pencil(p){ return g(p,{filter:"url(#pencil)"}); }

// hand-written label with a down arrow, anchored at the arrow tip (x,y)
function label(p,x,y,s,{size=50,col=INK,arrow=true}={}){
  const L=g(p,{transform:`translate(${x} ${y})`}); const k=pencil(L);
  txt(k,0,arrow?-92:0,s,size,col,"Hand",700);
  if(arrow){ line(k,"M0 -58 L0 -8",5,col); line(k,"M-12 -22 L0 -6 L12 -22",5,col); }
  return L;
}

// ---- stick figure ----
const FIG = {headR:46, torso:150, uArm:72, fArm:66, uLeg:92, fLeg:92};
function defaultPose(){ return {x:0,y:0,lean:4,headTilt:0,
  aL1:200,aL2:-40, aR1:160,aR2:40,   // shoulder & elbow angles (deg, 0 = pointing down? we use 180=down)
  lL1:-10,lL2:10, lR1:10,lR2:10,     // hip & knee angles (0 = straight down)
  face:"neutral", sweat:0, mouthOpen:0}; }
// angle convention: limbs measured from straight-down, positive = forward (to the right of screen)
function seg(x,y,ang,len){ const a=rad(ang); return [x+Math.sin(a)*len, y+Math.cos(a)*len]; }
class Fig{
  constructor(parent,{scale=1,extra=null}={}){
    this.root=g(parent); this.s=scale; this.p=defaultPose();
    this.k=pencil(this.root);
    this.limbs={}; for(const n of ["legL","legR","body","armL","armR"]) this.limbs[n]=line(this.k,"M0 0",9);
    this.handL=circ(this.k,0,0,10,INK,1); this.handR=circ(this.k,0,0,10,INK,1);
    this.footL=line(this.k,"M0 0",9); this.footR=line(this.k,"M0 0",9);
    this.headG=g(this.k); this.head=circ(this.headG,0,0,FIG.headR,PAPER,8);
    this.faceG=g(this.headG); this.extraG=g(this.headG);
    this.sweatG=g(this.root);
    if(extra) extra(this);
    this.update();
  }
  set(o){ Object.assign(this.p,o); this.update(); return this; }
  update(){
    const p=this.p, s=this.s;
    this.root.setAttribute("transform",`translate(${p.x} ${p.y}) scale(${s})`);
    // hip at (0,0); ground at y = uLeg+fLeg
    const hip=[0,0], lean=rad(p.lean);
    const neck=[Math.sin(lean)*FIG.torso, -Math.cos(lean)*FIG.torso];
    const shoulder=[neck[0]*0.92, neck[1]*0.92];
    this.limbs.body.setAttribute("d",`M${hip[0]} ${hip[1]} L${neck[0]} ${neck[1]}`);
    const limb=(base,a1,a2,l1,l2,el,hand,foot)=>{
      const k1=seg(base[0],base[1],a1,l1), k2=seg(k1[0],k1[1],a1+a2,l2);
      el.setAttribute("d",`M${base[0]} ${base[1]} L${k1[0]} ${k1[1]} L${k2[0]} ${k2[1]}`);
      if(hand){ hand.setAttribute("cx",k2[0]); hand.setAttribute("cy",k2[1]); }
      if(foot){ foot.setAttribute("d",`M${k2[0]-4} ${k2[1]} l26 0`); }
      return k2;
    };
    this.handLpos=limb(shoulder,p.aL1-180,p.aL2,FIG.uArm,FIG.fArm,this.limbs.armL,this.handL);
    this.handRpos=limb(shoulder,p.aR1-180,p.aR2,FIG.uArm,FIG.fArm,this.limbs.armR,this.handR);
    this.footLpos=limb(hip,p.lL1,p.lL2,FIG.uLeg,FIG.fLeg,this.limbs.legL,null,this.footL);
    this.footRpos=limb(hip,p.lR1,p.lR2,FIG.uLeg,FIG.fLeg,this.limbs.legR,null,this.footR);
    const hc=[neck[0]+Math.sin(lean)*(FIG.headR-4), neck[1]-Math.cos(lean)*(FIG.headR-4)-FIG.headR+6];
    this.headPos=hc;
    this.headG.setAttribute("transform",`translate(${hc[0]} ${hc[1]}) rotate(${p.headTilt})`);
    if(this._face!==p.face+p.mouthOpen){ this._face=p.face+p.mouthOpen; this.drawFace(); }
    this.sweatG.style.opacity=p.sweat;
  }
  drawFace(){
    const f=this.faceG; f.innerHTML=""; const p=this.p;
    const eye=(x,y,r=5.5)=>el("circle",{cx:x,cy:y,r,fill:INK},f);
    if(p.face==="happy"){ line(f,"M4 -10 q8 -9 16 0",5); line(f,"M26 -10 q8 -9 16 0",5); line(f,"M8 12 q16 18 32 0",5.5); }
    else if(p.face==="tired"){ line(f,"M4 -6 q8 5 16 0",5); line(f,"M26 -6 q8 5 16 0",5); line(f,"M12 18 q12 -8 24 0",5); line(f,"M2 -20 l14 6 M42 -20 l-14 6",4); }
    else if(p.face==="sad"){ eye(12,-6); eye(34,-6); line(f,"M12 22 q12 -12 24 0",5); }
    else if(p.face==="shock"){ eye(12,-6,7); eye(34,-6,7); circ(f,23,18,8,INK,3); }
    else if(p.face==="grin"){ eye(12,-8); eye(34,-8); shape(f,"M6 8 Q23 34 40 8 Z",INK,4); }
    else { eye(12,-6); eye(34,-6); line(f,"M14 16 q10 6 20 0",5); }
  }
  W(pt){ return [this.p.x+pt[0]*this.s, this.p.y+pt[1]*this.s]; }
  addSweat(){ const k=pencil(this.sweatG); const hp=this.headPos;
    for(const [dx,dy] of [[-58,-30],[-70,0]]) shape(k,`M${hp[0]+dx} ${hp[1]+dy-14} q10 14 0 22 q-10 -8 0 -22Z`,"#9DB7C9",3);
    line(k,`M${hp[0]+40} ${hp[1]-60} l10 -16 M${hp[0]+56} ${hp[1]-46} l16 -10`,4); }
}
// run cycle pose for phase ph (0..1) and intensity k (1 = sprint)
function runPose(ph,k=1){
  const a=Math.sin(ph*2*Math.PI), b=Math.cos(ph*2*Math.PI);
  return {lean:10*k, aL1:180+48*a*k, aL2:-70, aR1:180-48*a*k, aR2:-70,
          lL1:38*a*k, lL2:Math.max(0,-55*b*k)+8, lR1:-38*a*k, lR2:Math.max(0,55*b*k)+8};
}
function walkPose(ph,k=1){ const a=Math.sin(ph*2*Math.PI);
  return {lean:3, aL1:180+22*a*k, aL2:-12, aR1:180-22*a*k, aR2:-12, lL1:20*a*k, lL2:6+6*Math.max(0,-a), lR1:-20*a*k, lR2:6+6*Math.max(0,a)}; }
function speedLines(p,x,y,w=260,n=7,col=GREY){ const k=pencil(g(p)); for(let i=0;i<n;i++){ const yy=y-170+i*42+(i%2)*9; const ww=w*(0.45+0.55*((i*37)%10)/10); line(k,`M${x-ww} ${yy} L${x} ${yy}`,4,col,{opacity:.75}); } return k; }
function ground(p,y,x0=-200,x1=1280){ const k=pencil(g(p)); line(k,`M${x0} ${y} C${x0+400} ${y-3} ${x1-400} ${y+3} ${x1} ${y}`,6); return k; }

// captions on a dark rounded background
function caption(str,y=1610,size=58){
  const cap=document.getElementById("captions"); cap.innerHTML="";
  const lines=[].concat(str);
  lines.forEach((ln,i)=>{ const yy=y+(i-(lines.length-1))*size*1.5; const grp=g(cap);
    const bg=el("rect",{fill:"#232325",opacity:.86,rx:size*.55},grp);
    const t=txt(grp,540,yy,ln,size,"#FFFFFF","Yekan",700); const bb=t.getBBox(); const px=size*.6, pv=size*.24;
    Object.entries({x:bb.x-px,y:bb.y-pv,width:bb.width+2*px,height:bb.height+2*pv}).forEach(([k,v])=>bg.setAttribute(k,v)); });
}
