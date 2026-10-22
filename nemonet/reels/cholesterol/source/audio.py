"""Synthesized music bed + SFX for the cholesterol reel (all generated, no samples)."""
import json
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

SR = 44100
TIM = json.load(open("timing.json"))
DUR = TIM["duration"]
N = int(SR * DUR)
SC = TIM["scenes"]
LW = [l["words"] for l in TIM["lines"]]
rng = np.random.default_rng(11)


def t_(d): return np.arange(int(SR * d)) / SR
def env(n, a=0.005, r=0.2):
    e = np.ones(n); ai = int(SR * a); ri = min(n, int(SR * r))
    if ai: e[:ai] = np.linspace(0, 1, ai)
    e[-ri:] *= np.exp(-np.linspace(0, 6, ri)); return e
def bp(x, lo, hi, o=2):
    b, a = butter(o, [lo / (SR / 2), hi / (SR / 2)], "band"); return lfilter(b, a, x)
def lp(x, f, o=2):
    b, a = butter(o, f / (SR / 2)); return lfilter(b, a, x)
def put(buf, x, t, g=1.0):
    i = int(t * SR)
    if i >= len(buf) or i < 0: return
    j = min(len(buf), i + len(x)); buf[i:j] += g * x[: j - i]
def hz(n): return 440 * 2 ** ((n - 69) / 12)


def pluck(f, d=1.2, bright=0.5):
    n = int(SR * d); p = max(2, int(SR / f)); buf = rng.uniform(-1, 1, p); buf = lp(buf, 2000 + 6000 * bright, 1)
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]; buf[i % p] = 0.996 * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    return out * env(n, 0.002, d)


# ---------------- music: easy, playful 96 BPM, F - Dm - Bb - C ----------------
music = np.zeros(N)
bpm = 96; beat = 60 / bpm; bar = 4 * beat
chords = [[65, 69, 72, 77], [62, 65, 69, 74], [58, 62, 65, 70], [60, 64, 67, 72]]
roots = [41, 38, 34, 36]
cache = {}
def pl(n, d=0.8):
    if (n, d) not in cache: cache[(n, d)] = pluck(hz(n), d, 0.4)
    return cache[(n, d)]
strum = [0, 1.5, 2, 3, 3.5]
for b in range(int(DUR / bar) + 1):
    ch = chords[b % 4]; t0 = b * bar
    for k, sb in enumerate(strum):
        down = k % 2 == 0
        for j, n in enumerate(ch if down else ch[::-1]):
            put(music, pl(n), t0 + sb * beat + j * 0.014, 0.13 if down else 0.08)
    for sb in (0, 2.5):  # round bass
        tb = t_(beat * 1.3)
        put(music, np.sin(2 * np.pi * hz(roots[b % 4] + 12) * tb) * env(len(tb), 0.01, beat * 1.3), t0 + sb * beat, 0.26)
    for q in range(4):
        tq = t0 + q * beat
        if q % 2 == 0:
            tk = t_(0.22); f = 110 * np.exp(-tk * 18) + 45
            put(music, np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tk), 0.001, 0.22), tq, 0.42)
        else:
            sn = bp(rng.standard_normal(int(SR * 0.1)), 1800, 6000) * env(int(SR * 0.1), 0.001, 0.1)
            put(music, sn, tq, 0.22)
        sh = bp(rng.standard_normal(int(SR * 0.04)), 6000, 12000) * env(int(SR * 0.04), 0.002, 0.04)
        put(music, sh, tq + 0.5 * beat, 0.07)
music = lp(music, 8500)
fade = np.ones(N); fi, fo = int(SR * 0.2), int(SR * 0.8)
fade[:fi] = np.linspace(0.3, 1, fi); fade[-fo:] = np.linspace(1, 0, fo)
music *= fade

# ---------------- SFX ----------------
sfx = np.zeros(N)

def whoosh(d=0.3):
    n = int(SR * d); x = rng.standard_normal(n); out = np.zeros(n); seg = 256
    for i in range(0, n, seg):
        fc = 500 + 3000 * (i / n)
        out[i:i + seg] = bp(x[i:i + seg], max(100, fc * 0.6), min(16000, fc * 1.6), 1)[: len(out[i:i + seg])]
    return out * np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5

def popsnd(f0=650, f1=200, d=0.12):
    tt = t_(d); f = f1 + (f0 - f1) * np.exp(-tt * 40)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.001, d)

def bell(f, d=1.0):
    tt = t_(d); x = sum(a * np.sin(2 * np.pi * f * m * tt) for m, a in ((1, 1), (2.76, 0.3), (5.4, 0.12)))
    return x * np.exp(-tt * 3.5) * env(len(tt), 0.002, d)

def tada(t, g=0.22, broken=False):
    notes = (72, 76, 79, 84) if not broken else (72, 71, 68, 63)
    for i, n in enumerate(notes):
        f = hz(n) * (1 + (0.012 * i if broken else 0))
        put(sfx, bell(f, 1.0 if not broken else 0.7), t + i * (0.07 if not broken else 0.13), g)

def scratch(d=0.32):
    tt = t_(d); x = rng.standard_normal(len(tt)); out = np.zeros(len(tt)); seg = 220
    for i in range(0, len(tt), seg):
        fc = 900 + 2600 * abs(np.sin(i / len(tt) * np.pi * 3.2))
        out[i:i + seg] = bp(x[i:i + seg], fc * 0.7, fc * 1.4, 1)[: len(out[i:i + seg])]
    return out * env(len(tt), 0.003, 0.08)

def bubbles(t, k=6, g=0.2):
    for i in range(k):
        put(sfx, popsnd(900 + 500 * rng.random(), 300, 0.07), t + i * 0.09 + 0.03 * rng.random(), g)

def engine(d=2.5):
    tt = t_(d); f = 55 + 6 * np.sin(2 * np.pi * 0.7 * tt)
    saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
    x = lp(saw * (0.7 + 0.3 * np.sin(2 * np.pi * 18 * tt)), 600)
    return x * env(len(tt), 0.3, 0.6)

def beep(f, d=0.16):
    tt = t_(d); return np.sign(np.sin(2 * np.pi * f * tt)) * 0.35 * env(len(tt), 0.004, 0.04)

def horn(d=0.35, f=420):
    tt = t_(d); x = np.sign(np.sin(2 * np.pi * f * tt)) + np.sign(np.sin(2 * np.pi * f * 1.26 * tt))
    return lp(x, 1800) * env(len(tt), 0.01, 0.06)

def splash(d=0.7):
    tt = t_(d); x = lp(rng.standard_normal(len(tt)), 3500) * np.exp(-tt * 5)
    return x * env(len(tt), 0.002, d)

def thump():
    tt = t_(0.3); f = 90 * np.exp(-tt * 12) + 40
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.001, 0.3)

def W(li, wi): return LW[li][wi]

for s in SC[1:]:
    put(sfx, whoosh(0.28), s - 0.12, 0.22)
tada(0.02)                                     # 1 proud
put(sfx, scratch(), W(1, 4) - 0.05, 0.5)       # 2 "مُرده"
put(sfx, popsnd(), SC[2] + 0.15, 0.3)          # 3 cell pop
put(sfx, popsnd(800, 260), W(2, 7) - 0.03, 0.3); put(sfx, popsnd(700, 240), W(2, 8) + 0.1, 0.25)
put(sfx, bell(hz(84), 0.6), W(3, 3), 0.18)     # 4 question ding
bubbles(SC[4] + 0.2)                           # 5 oil bubbles
put(sfx, engine(SC[6] - SC[5]), SC[5], 0.22)   # 6 truck engine
for k in range(3): put(sfx, beep(1050), SC[6] + 0.4 + k * 0.45, 0.14)   # 7 reversing beeps
put(sfx, horn(0.3, 400), SC[7] + 0.35, 0.18); put(sfx, horn(0.45, 360), SC[7] + 0.95, 0.18)  # 8 traffic
put(sfx, splash(), SC[8] + 0.02, 0.5); bubbles(SC[8] + 0.25, 4, 0.12)   # 9 burst pipe
put(sfx, popsnd(500, 250, 0.1), SC[9] + 0.6, 0.2)                        # 10 idea
put(sfx, thump(), SC[10] + 0.02, 0.6)                                     # 11 "نه!"
put(sfx, whoosh(0.25), SC[11] - 0.05, 0.25); put(sfx, bell(hz(88), 0.9), SC[11] + 0.3, 0.2)  # 12 card
put(sfx, bell(hz(91), 0.8), W(11, len(LW[11]) - 1), 0.16)               # brand ting
tada(0.02 + SC[12], 0.18)                                                 # 13 same opening...
tada(W(12, 3) - 0.05, 0.22, broken=True)                                  # ...then the sad version


def save(name, x, peak=0.9):
    x = x / (np.max(np.abs(x)) + 1e-9) * peak
    wavfile.write(name, SR, (x * 32767).astype(np.int16))

save("music.wav", music)
save("sfx.wav", sfx)
print("audio ok", DUR)
