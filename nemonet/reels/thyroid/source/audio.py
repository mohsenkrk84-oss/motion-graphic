"""Music bed + SFX for Nemonet reel A, synthesized in numpy and timed to the VO word timestamps."""
import json, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

SR = 44100; DUR = 25.0; N = int(SR * DUR)
rng = np.random.default_rng(3)
W = json.load(open("/home/claude/reelT/words.json"))
ws = lambda i: W[i][1]

def t_(d): return np.arange(int(SR * d)) / SR
def env(n, a=0.005, r=0.2):
    e = np.ones(n); ai = max(1, int(SR * a)); ri = min(n, int(SR * r))
    e[:ai] = np.linspace(0, 1, ai); e[-ri:] *= np.exp(-np.linspace(0, 6, ri)); return e
def bp(x, lo, hi, o=2): b, a = butter(o, [lo / (SR / 2), hi / (SR / 2)], "band"); return lfilter(b, a, x)
def lp(x, f, o=2): b, a = butter(o, f / (SR / 2)); return lfilter(b, a, x)
def hp(x, f, o=2): b, a = butter(o, f / (SR / 2), "high"); return lfilter(b, a, x)
def put(buf, x, t, g=1.0):
    i = int(t * SR)
    if i >= len(buf) or i < 0: return
    j = min(len(buf), i + len(x)); buf[i:j] += g * x[: j - i]
hz = lambda n: 440 * 2 ** ((n - 69) / 12)
def sine(f, d): return np.sin(2 * np.pi * f * t_(d))
def sweep(f0, f1, d):
    tt = t_(d); f = f0 * (f1 / f0) ** (tt / d); return np.sin(2 * np.pi * np.cumsum(f) / SR)

def pluck(f, d=0.9):
    n = int(SR * d); p = max(2, int(SR / f)); buf = lp(rng.uniform(-1, 1, p), 5000, 1); out = np.zeros(n)
    for i in range(n): out[i] = buf[i % p]; buf[i % p] = 0.995 * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    return out * env(n, 0.002, d)

def whoosh(d=0.35, up=True, lo=300, hi=4000):
    n = int(SR * d); x = rng.standard_normal(n); out = np.zeros(n); seg = 256
    for i in range(0, n, seg):
        k = i / n; fc = lo + (hi - lo) * (k if up else 1 - k)
        out[i:i + seg] = bp(x[i:i + seg], max(80, fc * .6), min(18000, fc * 1.6), 1)[:len(out[i:i + seg])]
    return out * np.sin(np.pi * np.linspace(0, 1, n)) ** 1.4
def popsnd(f0=650, f1=200, d=0.12):
    tt = t_(d); f = f1 + (f0 - f1) * np.exp(-tt * 40); return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), .001, d)
def bell(f, d=1.0, dec=3.5):
    tt = t_(d); x = sum(a * np.sin(2 * np.pi * f * m * tt) for m, a in ((1, 1), (2.76, .3), (5.4, .12), (8.9, .05)))
    return x * np.exp(-tt * dec) * env(len(tt), .002, d)
def click(): return bp(rng.standard_normal(int(SR * .02)), 2000, 9000) * env(int(SR * .02), .0005, .02)
def beep(f=2100, d=0.09): return np.sign(sine(f, d)) * 0.3 * env(int(SR * d), .002, .02)
def horn(d=0.45):
    x = (np.sign(sine(392, d)) + np.sign(sine(494, d))) * 0.5
    return lp(x, 2200) * env(int(SR * d), .01, .06)
def growl(d=0.7):
    tt = t_(d); f = 70 + 25 * np.sin(2 * np.pi * 6 * tt)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.6 + 0.4 * np.sin(2 * np.pi * 11 * tt)) + 0.4 * lp(rng.standard_normal(len(tt)), 300)
    return x * np.sin(np.pi * np.linspace(0, 1, len(tt)))
def crumple(d=0.4):
    n = int(SR * d); out = np.zeros(n)
    for _ in range(26):
        i = rng.integers(0, n - 800); L_ = rng.integers(200, 800)
        out[i:i + L_] += bp(rng.standard_normal(L_), 1500, 8000) * env(L_, .0005, L_ / SR) * rng.uniform(.3, 1)
    return out
def rewind(d=0.5):
    tt = t_(d); f = 1800 * (0.25) ** (tt / d) * (1 + 0.15 * np.sign(np.sin(2 * np.pi * 24 * tt)))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.6 + 0.4 * bp(rng.standard_normal(len(tt)), 2000, 6000)) * env(len(tt), .01, .08)
def pour(d=0.9):
    n = int(SR * d); x = bp(rng.standard_normal(n), 400, 2500)
    am = 0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 13 * t_(d)))
    return x * am * np.sin(np.pi * np.linspace(0, 1, n))
def shimmer(d=0.9):
    out = np.zeros(int(SR * d))
    for k, n in enumerate([84, 88, 91, 96, 100, 103]): put(out, bell(hz(n), 0.6, 6), k * 0.06, 0.25)
    return out
def thump(d=0.5):
    tt = t_(d); f = 90 * np.exp(-tt * 9) + 38; return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), .001, d)


# ---------------- music ----------------
music=np.zeros(N); bpm=112; beat=60/bpm; bar=4*beat
cache={}
def pl(n,d=0.5):
    if (n,d) not in cache: cache[(n,d)]=pluck(hz(n),d)
    return cache[(n,d)]
def drums(buf,t0,t1,g=1.0,hat=True):
    t=t0
    while t<t1:
        q=round((t-t0)/beat)
        if q%2==0:
            tk=t_(0.22); f=105*np.exp(-tk*22)+45; put(buf,np.sin(2*np.pi*np.cumsum(f)/SR)*env(len(tk),.001,.22),t,.5*g)
        else: put(buf,bp(rng.standard_normal(int(SR*.1)),1800,7000)*env(int(SR*.1),.001,.1),t,.28*g)
        if hat:
            for e in (0,.5): put(buf,bp(rng.standard_normal(int(SR*.035)),7000,14000)*env(int(SR*.035),.001,.035),t+e*beat,.07*g)
        t+=beat
# A: playful staccato (0 → twist)
TW=ws(21); SOL=ws(34); BRK=ws(42)
melA=[72,74,76,79, 77,76,74,72, 69,72,74,76, 74,72,71,67]
bassA=[48,48,45,45,41,41,43,43]
k=0; t=0.0
while t<TW-0.05:
    put(music,pl(melA[k%16],.35),t,.16); 
    if k%2==0: put(music,np.sin(2*np.pi*hz(bassA[(k//2)%8])*t_(beat*.9))*env(int(SR*beat*.9),.01,beat*.9),t,.22)
    k+=1; t+=beat/2
drums(music,0,TW-0.05,.8)
# suspense: low pulse + ticking (twist → solution)
t=TW+0.15
while t<SOL:
    tk=t_(0.35); put(music,np.sin(2*np.pi*55*tk)*env(len(tk),.005,.35),t,.4); put(music,np.sin(2*np.pi*55*tk)*env(len(tk),.005,.25),t+0.28,.25)
    t+=0.8
put(music,lp(rng.standard_normal(int(SR*(SOL-TW))),180)*np.linspace(0.3,1,int(SR*(SOL-TW))),TW,.18)
# B: bright and building (solution → end)
melB=[76,79,81,84, 83,81,79,76, 77,81,84,88, 86,84,83,79]
bassB=[45,45,41,41,48,48,43,43]
k=0; t=SOL
while t<DUR-0.6:
    gB=0.6 if t<BRK else 1.0
    put(music,pl(melB[k%16],.4),t,.15*gB)
    if k%2==0: put(music,np.sin(2*np.pi*hz(bassB[(k//2)%8])*t_(beat*.9))*env(int(SR*beat*.9),.01,beat*.9),t,.24*gB)
    if t>=BRK and k%4==0:
        for j,n in enumerate([64,67,72]): put(music,pl(n,.6),t+j*.01,.08)
    k+=1; t+=beat/2
drums(music,SOL,BRK,.5,False); drums(music,BRK,DUR-0.6,1.0)
fo=int(SR*.7); music[-fo:]*=np.linspace(1,0,fo)
music=lp(music,9500)

# ---------------- SFX ----------------
sfx=np.zeros(N)
def boing(d=.35):
    tt=t_(d); f=220+180*np.sin(2*np.pi*14*tt)*np.exp(-tt*6)+120*np.exp(-tt*8); return np.sin(2*np.pi*np.cumsum(f)/SR)*env(len(tt),.002,d)
def wahwah():
    out=np.zeros(int(SR*1.1))
    for k,(n0,n1) in enumerate([(62,61),(61,60),(60,59),(59,54)]):
        d=.25 if k<3 else .5; tt=t_(d); f=hz(n0)*(hz(n1)/hz(n0))**(tt/d)
        x=np.sign(np.sin(2*np.pi*np.cumsum(f)/SR))*0.5+np.sin(2*np.pi*np.cumsum(f)/SR)*.5
        put(out,lp(x,1400)*env(len(tt),.01,.08)*(0.7+0.3*np.sin(2*np.pi*6*tt)),k*.24,1)
    return out
def step(heavy=False):
    d=.09 if not heavy else .16; tt=t_(d); f=(160 if not heavy else 90)*np.exp(-tt*30)+50
    return (np.sin(2*np.pi*np.cumsum(f)/SR)+0.3*bp(rng.standard_normal(len(tt)),300,2000))*env(len(tt),.001,d)
def puff(d=.25): return bp(rng.standard_normal(int(SR*d)),500,2500)*np.sin(np.pi*np.linspace(0,1,int(SR*d)))**2
def scratch():
    d=.45; tt=t_(d); f=900*np.abs(np.sin(2*np.pi*3.2*tt))+150
    return (bp(rng.standard_normal(len(tt)),800,5000)*0.6+0.4*np.sin(2*np.pi*np.cumsum(f)/SR))*env(len(tt),.005,.06)
def clink(f=2400): return bell(f,.25,14)
def chain_rattle(d=1.0):
    out=np.zeros(int(SR*d))
    for i in range(14): put(out,clink(rng.uniform(1800,3600)),rng.uniform(0,d-.25),rng.uniform(.3,.8))
    return out
def boom(d=1.2):
    tt=t_(d); f=60*np.exp(-tt*3)+32; return (np.sin(2*np.pi*np.cumsum(f)/SR)+0.4*lp(rng.standard_normal(len(tt)),150))*env(len(tt),.002,d)
def scribble(d=.3):
    n=int(SR*d); x=bp(rng.standard_normal(n),2500,7000); return x*(0.5+0.5*np.abs(np.sin(2*np.pi*9*t_(d))))*np.sin(np.pi*np.linspace(0,1,n))
def fill(d=.9):
    out=np.zeros(int(SR*d))
    for i in range(10): put(out,popsnd(300+i*60,250+i*50,.06),i*d/10,.35)
    return out
def snap():
    return bp(rng.standard_normal(int(SR*.08)),1500,9000)*env(int(SR*.08),.0005,.08)

# 1 hook — fast feet for «بقیه», heavy feet + panting for «تو»
t=0.05
while t<ws(8)-.1: put(sfx,step(),t,.32); t+=0.19
t=0.1
while t<ws(8)-.1: put(sfx,step(True),t,.3); t+=0.28
for t in (0.5,1.3,2.1): put(sfx,puff(),t,.35)
# 2 tries — pop + boing per item, sad trombone on "?"
for i in (8,10,12): put(sfx,popsnd(620,220,.12),ws(i),.45); put(sfx,boing(),ws(i)+.25,.3)
put(sfx,wahwah(),ws(13),.32)
# 3 still tired — slow heavy steps, zz, scale
t=ws(14)
while t<ws(21)-.1: put(sfx,step(True),t,.28); t+=0.45
put(sfx,popsnd(400,150,.14),ws(16),.35); put(sfx,popsnd(700,260,.12),ws(18),.4); put(sfx,boing(.3),ws(18)+.2,.25)
# 4 twist — record scratch, chain, lens, boom
put(sfx,scratch(),ws(21)-.05,.55)
put(sfx,chain_rattle(1.4),ws(21)+.2,.45)
put(sfx,whoosh(.45,True,300,5000),ws(26)-.15,.45)
put(sfx,boom(1.2),ws(28)-.05,.75); put(sfx,bell(hz(55),1.2,2.5),ws(28),.25)
# 5 symptoms — pencil ticks, shiver
for i in (30,31,32,33): put(sfx,scribble(),ws(i)-.05,.4); put(sfx,popsnd(560,220,.1),ws(i),.25)
put(sfx,bell(hz(96),.8,5),ws(31)+.1,.18)
# 6 solution — footsteps in, tube fill, TSH pop, chain snap + sparkle
t=ws(34)
while t<ws(34)+.9: put(sfx,step(),t,.3); t+=0.22
put(sfx,popsnd(700,260,.12),ws(38)-.05,.45)
put(sfx,fill(.9),ws(38),.4)
BR=ws(42); put(sfx,snap(),BR,.7); put(sfx,chain_rattle(.6),BR,.5); put(sfx,shimmer(1.0),BR+.05,.6); put(sfx,boing(.4),BR+.25,.3)
# 7 overtake — big whoosh, fast steps
put(sfx,whoosh(.6,True,200,8000),ws(44)-.1,.6)
t=ws(44)
while t<ws(48)-.05: put(sfx,step(),t,.3); t+=0.15
# 8 CTA
put(sfx,thump(.6),ws(48),.65); put(sfx,shimmer(1.2),ws(48)+.05,.5)
for i in (49,50): put(sfx,popsnd(560,220,.12),ws(i),.35)
put(sfx,popsnd(480,160,.16),ws(51),.45); put(sfx,click(),ws(52),.4)
for k,n in enumerate([77,81,84,89]): put(sfx,bell(hz(n),1.4,2.4),DUR-1.1+k*.07,.22)

def save(name,x,peak=.9):
    x=x/(np.max(np.abs(x))+1e-9)*peak; wavfile.write(name,SR,(x*32767).astype(np.int16))
save("/home/claude/reelT/music.wav",music); save("/home/claude/reelT/sfx.wav",sfx); print("ok")
