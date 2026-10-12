"""Synthesized music bed + SFX for the Nemonet vitamin-D reel (no samples, all generated)."""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

SR = 44100
DUR = 20.0
N = int(SR * DUR)
rng = np.random.default_rng(7)


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
    if i >= len(buf): return
    j = min(len(buf), i + len(x)); buf[i:j] += g * x[: j - i]
def hz(n): return 440 * 2 ** ((n - 69) / 12)


def pluck(f, d=1.2, bright=0.5):
    n = int(SR * d); p = max(2, int(SR / f)); buf = rng.uniform(-1, 1, p); buf = lp(buf, 2000 + 6000 * bright, 1)
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]; buf[i % p] = 0.996 * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    return out * env(n, 0.002, d)


# ---------------- music: 100 BPM, C - Am - F - G ----------------
music = np.zeros(N)
bpm = 100; beat = 60 / bpm; bar = 4 * beat
chords = [[60, 64, 67, 72], [57, 60, 64, 69], [53, 57, 60, 65], [55, 59, 62, 67]]
roots = [36, 33, 29, 31]
pl_cache = {}
def pl(n, d=0.9):
    if (n, d) not in pl_cache: pl_cache[(n, d)] = pluck(hz(n), d)
    return pl_cache[(n, d)]
strum = [0, 1.5, 2, 3, 3.5]  # beats with strums (syncopated)
nb = int(DUR / bar) + 1
for b in range(nb):
    ch = chords[b % 4]; t0 = b * bar
    for k, sb in enumerate(strum):
        down = k % 2 == 0
        notes = ch if down else ch[::-1]
        for j, n in enumerate(notes):
            put(music, pl(n), t0 + sb * beat + j * 0.012, 0.16 if down else 0.11)
    # bass
    for sb in (0, 2.5):
        tb = t_(beat * 1.4); x = np.sin(2 * np.pi * hz(roots[b % 4] + 12) * tb) * env(len(tb), 0.01, beat * 1.4)
        put(music, x, t0 + sb * beat, 0.30)
    for q in range(4):  # kick on 1,3 ; snap on 2,4 ; shaker 8ths
        tq = t0 + q * beat
        if q % 2 == 0:
            tk = t_(0.25); f = 120 * np.exp(-tk * 18) + 45
            put(music, np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tk), 0.001, 0.25), tq, 0.55)
        else:
            sn = bp(rng.standard_normal(int(SR * 0.12)), 1500, 6000) * env(int(SR * 0.12), 0.001, 0.12)
            put(music, sn, tq, 0.35)
        for e in (0, 0.5):
            sh = bp(rng.standard_normal(int(SR * 0.05)), 6000, 12000) * env(int(SR * 0.05), 0.002, 0.05)
            put(music, sh, tq + e * beat, 0.10 if e else 0.06)
music = lp(music, 9000)
fade = np.ones(N); fi = int(SR * 0.25); fo = int(SR * 0.6)
fade[:fi] = np.linspace(0.2, 1, fi); fade[-fo:] = np.linspace(1, 0, fo)
music *= fade

# ---------------- SFX ----------------
sfx = np.zeros(N)

def whoosh(d=0.35, up=True):
    n = int(SR * d); x = rng.standard_normal(n); out = np.zeros(n); seg = 256
    for i in range(0, n, seg):
        k = i / n; fc = 400 + 3500 * (k if up else 1 - k)
        out[i:i + seg] = bp(x[i:i + seg + 0], max(100, fc * 0.6), min(16000, fc * 1.6), 1)[: len(out[i:i + seg])]
    return out * np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5

def popsnd(f0=600, f1=180, d=0.12):
    tt = t_(d); f = f1 + (f0 - f1) * np.exp(-tt * 40)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.001, d)

def bell(f, d=1.2):
    tt = t_(d); x = sum(a * np.sin(2 * np.pi * f * m * tt) for m, a in ((1, 1), (2.76, 0.35), (5.4, 0.15), (8.9, 0.06)))
    return x * np.exp(-tt * 3.2) * env(len(tt), 0.002, d)

def beep(f, d=0.14):
    tt = t_(d); return np.sign(np.sin(2 * np.pi * f * tt)) * 0.35 * env(len(tt), 0.003, 0.05)

def scribble(d=0.35):
    n = int(SR * d); x = bp(rng.standard_normal(n), 2500, 7000)
    am = 0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 9 * t_(d)))
    return x * am * np.sin(np.pi * np.linspace(0, 1, n))

def buzz(d=0.4):
    tt = t_(d); x = np.sign(np.sin(2 * np.pi * 165 * tt)) * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * tt))
    return lp(x, 900) * env(len(tt), 0.01, 0.05)

def click():
    return bp(rng.standard_normal(int(SR * 0.02)), 2000, 8000) * env(int(SR * 0.02), 0.0005, 0.02)

def riser(d=1.2):
    tt = t_(d); f = 220 * 2 ** (tt / d * 2)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(2 * np.pi * np.cumsum(f * 2) / SR)
    return x * np.linspace(0.2, 1, len(tt)) * env(len(tt), 0.05, 0.08)

import json
TIM = json.load(open("/home/claude/reel/timing.json")); SCS = TIM["scenes"]
def A(i, off): return max(0.0, SCS[i] + off)
# scene 1 — phone vibrates, Zs, snooze tap
for t in (0.0, 0.6, 1.2): put(sfx, buzz(0.42), A(0, t), 0.30)
for t, f in ((0.5, 520), (0.9, 470), (1.3, 420)): put(sfx, popsnd(f, f * 0.5, 0.14), A(0, t), 0.22)
put(sfx, click(), A(0, 1.62), 0.6)
# scene 2 — battery whoosh + low battery beeps
put(sfx, whoosh(0.35), A(1, -0.05), 0.45); put(sfx, popsnd(300, 90, 0.2), A(1, 0.3), 0.45)
for t in (0.75, 1.9):
    put(sfx, beep(880), A(1, t), 0.18); put(sfx, beep(660), A(1, t + 0.17), 0.18)
# scene 3 — cards + pencil ticks (synced to each spoken symptom)
put(sfx, whoosh(0.3), A(2, -0.05), 0.4)
for t0 in TIM["s3_cards"]:
    t = A(2, t0 - 0.25)
    put(sfx, whoosh(0.22), t, 0.28); put(sfx, popsnd(700, 250, 0.1), t + 0.3, 0.28)
    put(sfx, scribble(0.32), t + 0.45, 0.32)
# scene 4 — sunlight 'ting' on glass
put(sfx, whoosh(0.3), A(3, -0.05), 0.4)
for t in (0.55, 1.3, 2.1): put(sfx, bell(2400, 0.6), A(3, t), 0.10)
# scene 5 — tap, success, doorbell, sampler enters
sp = TIM["s5_split"]
put(sfx, whoosh(0.3), A(4, -0.05), 0.4)
put(sfx, click(), A(4, 0.84), 0.8); put(sfx, bell(1320, 0.5), A(4, 0.9), 0.16); put(sfx, bell(1760, 0.6), A(4, 1.0), 0.16)
put(sfx, bell(659, 1.3), A(4, sp), 0.28); put(sfx, bell(523, 1.6), A(4, sp + 0.45), 0.28)
put(sfx, whoosh(0.4), A(4, sp + 0.2), 0.32)
# scene 6 — charge up + final chime
put(sfx, whoosh(0.3), A(5, -0.05), 0.4)
put(sfx, riser(1.2), A(5, 0.15), 0.16)
put(sfx, popsnd(500, 200, 0.12), A(5, 0.6), 0.28)
for i, n in enumerate((72, 76, 79, 84)): put(sfx, bell(hz(n), 1.4), A(5, 1.35) + i * 0.09, 0.2)

def save(name, x, peak=0.9):
    x = x / (np.max(np.abs(x)) + 1e-9) * peak
    wavfile.write(name, SR, (x * 32767).astype(np.int16))

save("/home/claude/reel/music.wav", music, 0.9)
save("/home/claude/reel/sfx.wav", sfx, 0.9)
print("ok")
