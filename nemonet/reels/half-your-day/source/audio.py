"""Music bed + SFX for Nemonet reel A, synthesized in numpy and timed to the VO word timestamps."""
import json, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

SR = 44100; DUR = 29.4; N = int(SR * DUR)
rng = np.random.default_rng(3)
W = json.load(open("/home/claude/reelA/words.json"))
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

# ---------------- music: 104 BPM, F – Dm – Bb – C, ukulele + bass + light drums ----------------
music = np.zeros(N); bpm = 104; beat = 60 / bpm; bar = 4 * beat
chords = [[65, 69, 72, 77], [62, 65, 69, 74], [58, 62, 65, 70], [60, 64, 67, 72]]; roots = [41, 38, 34, 36]
cache = {}
def pl(n):
    if n not in cache: cache[n] = pluck(hz(n))
    return cache[n]
for b in range(int(DUR / bar) + 1):
    t0 = b * bar; ch = chords[b % 4]
    for k, sb in enumerate([0, 1, 1.5, 2.5, 3, 3.5]):
        notes = ch if k % 2 == 0 else ch[::-1]
        for j, n in enumerate(notes): put(music, pl(n), t0 + sb * beat + j * 0.011, 0.13 if k % 2 == 0 else 0.09)
    for sb in (0, 1.5, 2, 3.5):
        tb = t_(beat * 0.9); put(music, np.sin(2 * np.pi * hz(roots[b % 4] + 12) * tb) * env(len(tb), 0.01, beat * .9), t0 + sb * beat, 0.26)
    for q in range(4):
        tq = t0 + q * beat
        if q % 2 == 0:
            tk = t_(0.25); f = 110 * np.exp(-tk * 20) + 45
            put(music, np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tk), 0.001, 0.25), tq, 0.5)
        else:
            put(music, bp(rng.standard_normal(int(SR * .12)), 1500, 7000) * env(int(SR * .12), 0.001, .12), tq, 0.3)
        for e in (0, .5): put(music, bp(rng.standard_normal(int(SR * .04)), 7000, 14000) * env(int(SR * .04), .001, .04), tq + e * beat, .08)
# arrangement: soft start under the alarm, tape-stop at the rewind, restart brighter, fade out
gain = np.ones(N); tt = np.arange(N) / SR
gain *= np.clip((tt - 0.2) / 1.5, 0.35, 1)
# tape stop 8.6–9.0 then silence until 9.5
ts0, ts1, ts2 = 8.6, 9.0, 9.5
i0, i1, i2 = int(ts0 * SR), int(ts1 * SR), int(ts2 * SR)
seg = music[i0:i1].copy(); n = len(seg); pos = np.cumsum(np.linspace(1, 0.05, n)); pos = pos / pos[-1] * (n * 0.5)
music[i0:i1] = np.interp(pos, np.arange(n), seg) * np.linspace(1, 0, n)
music[i1:i2] = 0
gain[-int(SR * 0.8):] *= np.linspace(1, 0, int(SR * 0.8))
music = lp(music * gain, 9500)

# ---------------- SFX ----------------
sfx = np.zeros(N)
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

# 1 hook — digital alarm, rubbing eyes, stomach rumble
for k in range(4):
    for b2 in range(4): put(sfx, beep(), 0.0 + k * 0.45 + b2 * 0.1, 0.32)
put(sfx, growl(0.6), 2.3, 0.35)
# → traffic
put(sfx, whoosh(0.42, True, 300, 6000), 3.05, 0.5)
put(sfx, lp(rng.standard_normal(int(SR * 1.6)), 220) * env(int(SR * 1.6), .2, .3), 3.45, 0.5)
put(sfx, horn(0.35), 3.7, 0.38); put(sfx, horn(0.25), 4.15, 0.3); put(sfx, horn(0.5), 4.45, 0.25)
# → queue (whip)
put(sfx, whoosh(0.3, True, 800, 7000), 4.8, 0.45)
for k in range(int((8.55 - 5.1) / 0.11)): put(sfx, click(), 5.1 + k * 0.11, 0.18 if k % 2 else 0.28)
put(sfx, growl(0.8), ws(7), 0.45)
put(sfx, bell(880, .7), 6.4, 0.18); put(sfx, bell(698, .9), 6.55, 0.18)        # queue display ding-dong
put(sfx, whoosh(0.6, True, 200, 2500), ws(8) - .1, 0.3)                          # push-in
put(sfx, thump(0.35), ws(11), 0.45)
# crumple → rewind → idea
put(sfx, crumple(0.45), 8.58, 0.55)
put(sfx, rewind(0.52), 9.0, 0.45)
put(sfx, popsnd(500, 160, .14), 9.5, 0.4); put(sfx, shimmer(0.8), 9.7, 0.6)
# phone rises, tap, success
put(sfx, whoosh(0.45, True, 300, 5000), 10.95, 0.45)
put(sfx, click(), ws(23), 0.9); put(sfx, popsnd(900, 400, .08), ws(23), 0.3)
put(sfx, bell(hz(84), .6), ws(23) + .15, 0.28); put(sfx, bell(hz(91), .9), ws(23) + .27, 0.28)
# zoom through screen → door
put(sfx, whoosh(0.45, True, 300, 8000), 12.75, 0.5)
put(sfx, popsnd(700, 250, .12), ws(25) - .05, 0.35)
put(sfx, bell(659, 1.2, 2.5), 13.95, 0.38); put(sfx, bell(523, 1.6, 2.2), 14.3, 0.38)
put(sfx, whoosh(0.35, False, 200, 1500), ws(27), 0.3)                            # door swing
# whip → tea
put(sfx, whoosh(0.3, True, 600, 7000), 15.38, 0.45)
put(sfx, pour(0.8), 15.75, 0.3)
put(sfx, popsnd(650, 220, .14), ws(31) - .05, 0.4); put(sfx, bell(hz(88), .7), ws(31), 0.2)
for t in (ws(33) - .05, ws(35) - .05): put(sfx, whoosh(0.25, True, 1000, 6000), t - .05, 0.3); put(sfx, popsnd(520, 180, .12), t + .3, 0.35)
# circle wipe → result, bars, AI sparkle, typing, ding
put(sfx, whoosh(0.45, True, 200, 5000), 18.88, 0.45)
for k in range(4): put(sfx, popsnd(400 + k * 120, 300 + k * 90, .09), 19.45 + k * .12, 0.22)
put(sfx, shimmer(1.0), ws(40) - .05, 0.7)
for k in range(6): put(sfx, click(), 20.8 + k * 0.09, 0.35)
put(sfx, bell(hz(93), .8, 4), ws(42), 0.25)
# → CTA: impact, counter, chips, button
put(sfx, whoosh(0.4, True, 300, 9000), 21.72, 0.5)
put(sfx, thump(0.6), 22.1, 0.65); put(sfx, shimmer(1.2), 22.15, 0.55)
c0 = ws(46) - .3
for k in range(18): put(sfx, click(), c0 + 1.2 * (1 - (1 - k / 18) ** 2), 0.3)
put(sfx, bell(hz(96), 1.0, 3), ws(48), 0.3)
put(sfx, popsnd(560, 200, .12), ws(51) - .05, 0.38); put(sfx, popsnd(620, 220, .12), ws(53) - .05, 0.38)
put(sfx, popsnd(480, 160, .16), ws(54) - .05, 0.45)
for k, n in enumerate([77, 81, 84, 89]): put(sfx, bell(hz(n), 1.6, 2.2), 28.55 + k * .07, 0.22)

def save(name, x, peak=0.9):
    x = x / (np.max(np.abs(x)) + 1e-9) * peak; wavfile.write(name, SR, (x * 32767).astype(np.int16))
save("/home/claude/reelA/music.wav", music); save("/home/claude/reelA/sfx.wav", sfx); print("ok")
