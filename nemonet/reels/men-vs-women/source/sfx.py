"""Synthesised SFX + music for the men-vs-women reel (no samples, no copyright).
python3 -I sfx.py <out_dir>
"""
import sys, os, wave
import numpy as np

SR = 44100
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(11)


def t_(d): return np.arange(int(SR * d)) / SR


def save(name, x, gain=0.9):
    x = np.asarray(x, float)
    if x.ndim == 1: x = np.stack([x, x], 1)
    x = x / (np.abs(x).max() + 1e-9) * gain
    with wave.open(os.path.join(OUT, name), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def env(n, a=0.005, r=0.1, shape=4.0):
    e = np.ones(n)
    na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
    tt = np.arange(n) / SR
    return e * np.exp(-tt / max(r, 1e-4) * (shape / 4))


def lp(x, a):  # one-pole low-pass, a in (0,1): smaller = darker
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc); y[i] = acc
    return y


def hp(x, a): return x - lp(x, a)


def pluck(f, d, bright=0.5, decay=0.996):
    """Karplus–Strong plucked string."""
    n = int(SR * d); p = max(2, int(SR / f))
    buf = rng.uniform(-1, 1, p) * bright + rng.uniform(-1, 1, p) * (1 - bright) * 0.3
    out = np.empty(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = decay * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    return out * np.linspace(1, 0.0, n) ** 0.3


def bell(f, d, r=0.35):
    tt = t_(d)
    x = (np.sin(2 * np.pi * f * tt) + 0.45 * np.sin(2 * np.pi * f * 2.76 * tt) * np.exp(-tt / (r * 0.4))
         + 0.25 * np.sin(2 * np.pi * f * 5.4 * tt) * np.exp(-tt / (r * 0.2)))
    return x * env(len(tt), 0.002, r)


def sweep(f0, f1, d, kind="sin", curve=1.0):
    tt = t_(d); k = (tt / d) ** curve
    f = f0 * (f1 / f0) ** k
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) if kind == "sin" else (2 * (ph / (2 * np.pi) % 1) - 1)


def place(dst, src, at):
    i = int(at * SR); j = min(len(dst), i + len(src))
    dst[i:j] += src[:j - i]


def noise(d): return rng.uniform(-1, 1, int(SR * d))


# s1 sneaky tiptoe pizzicato -------------------------------------------------
x = np.zeros(int(SR * 2.1))
notes = [196, 233, 196, 262, 196, 233, 294, 262]
for k, f in enumerate(notes):
    place(x, pluck(f, 0.25, 0.7, 0.990) * (0.8 if k % 2 else 1), k * 0.25)
save("s1.wav", lp(x, 0.35))

# s2 wind-up (slide whistle up) then whoosh strike ---------------------------
tt = t_(0.75)
up = sweep(380, 1500, 0.75, curve=1.6) * (1 + 0.15 * np.sin(2 * np.pi * 7 * tt)) * np.linspace(0.3, 1, len(tt))
wh = hp(noise(0.35), 0.25) * np.sin(np.linspace(0, np.pi, int(SR * 0.35))) ** 2
x = np.zeros(int(SR * 1.3)); place(x, up * 0.6, 0); place(x, lp(wh, 0.5), 0.78)
place(x, sweep(900, 120, 0.12) * env(int(SR * 0.12), 0.001, 0.05) * 0.8, 1.08)
save("s2.wav", x)

# s3 comic suspense tremolo --------------------------------------------------
tt = t_(1.6)
st = sum(sweep(f, f * 1.03, 1.6, "saw") for f in (110, 165, 220.5))
trem = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 14 * tt))
x = lp(st * trem, 0.12) * np.linspace(0.2, 1, len(tt)) ** 1.5
x[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
save("s3.wav", x, 0.8)

# s4 nervous gulp ------------------------------------------------------------
tt = t_(0.32)
g = sweep(520, 140, 0.32, curve=0.6) * np.sin(np.linspace(0, np.pi, len(tt))) ** 0.7
g2 = sweep(300, 90, 0.12) * env(int(SR * 0.12), 0.002, 0.04)
x = np.zeros(int(SR * 0.5)); place(x, lp(g, 0.3), 0); place(x, g2 * 0.6, 0.26)
save("s4.wav", x)

# s5 magical sparkle ---------------------------------------------------------
x = np.zeros(int(SR * 1.3))
for k, f in enumerate([1568, 2093, 2637, 3136, 2637, 3520, 4186]):
    place(x, bell(f, 0.6, 0.25) * (1 - k * 0.06), k * 0.07 + rng.uniform(0, 0.02))
save("s5.wav", x, 0.7)

# s6 lovestruck heart pop + boing -------------------------------------------
tt = t_(0.9)
boing = np.sin(2 * np.pi * np.cumsum(330 * (1 + 0.25 * np.sin(2 * np.pi * 9 * tt) * np.exp(-tt / 0.4))) / SR)
x = np.zeros(int(SR * 1.0))
place(x, sweep(300, 1200, 0.06) * env(int(SR * 0.06), 0.001, 0.03), 0)
place(x, boing * env(len(tt), 0.005, 0.35) * 0.8, 0.05)
place(x, bell(1760, 0.5, 0.2) * 0.3, 0.08); place(x, bell(2217, 0.5, 0.2) * 0.25, 0.16)
save("s6.wav", x)

# s7 cartoon scuffle ---------------------------------------------------------
x = np.zeros(int(SR * 2.2))
at = 0.0
while at < 2.0:
    d = rng.uniform(0.05, 0.14)
    place(x, lp(noise(d), rng.uniform(0.15, 0.5)) * env(int(SR * d), 0.003, d / 2) * rng.uniform(0.4, 1), at)
    if rng.random() < 0.45:
        place(x, sweep(rng.uniform(120, 200), 60, 0.1) * env(int(SR * 0.1), 0.001, 0.04) * 0.9, at)
    if rng.random() < 0.25:
        place(x, sweep(rng.uniform(600, 900), rng.uniform(1200, 1800), 0.08) * env(int(SR * 0.08), 0.002, 0.04) * 0.25, at)
    at += rng.uniform(0.06, 0.16)
x *= np.minimum(1, np.linspace(3, 0, len(x)))
save("s7.wav", x, 0.8)

# s8 rocket launch + boing ---------------------------------------------------
tt = t_(1.3)
rk = lp(noise(1.3), 0.1) * np.linspace(1, 0.2, len(tt))
rk += 0.5 * sweep(200, 1800, 1.3, curve=0.7) * np.linspace(1, 0, len(tt))
x = np.zeros(int(SR * 1.5))
place(x, sweep(160, 520, 0.4) * env(int(SR * 0.4), 0.002, 0.25), 0)  # spring boing
place(x, rk * 0.7, 0.05)
save("s8.wav", x)

# s9 crash into the wall, frame falls, dizzy tweets --------------------------
x = np.zeros(int(SR * 2.6))
place(x, sweep(110, 40, 0.35) * env(int(SR * 0.35), 0.001, 0.12) * 1.0, 0)       # thud
place(x, lp(noise(0.4), 0.4) * env(int(SR * 0.4), 0.001, 0.08) * 0.8, 0)          # crash body
for k in range(6):                                                                 # frame clatter
    place(x, bell(rng.uniform(900, 1800), 0.25, 0.06) * 0.35, 0.35 + k * rng.uniform(0.05, 0.09))
place(x, lp(noise(0.12), 0.5) * env(int(SR * 0.12), 0.001, 0.04) * 0.6, 0.72)
for k in range(7):                                                                 # tweets
    c = sweep(2600, 3600, 0.07) * np.sin(np.linspace(0, np.pi, int(SR * 0.07)))
    place(x, c * 0.35, 1.0 + k * 0.2 + (0.07 if k % 2 else 0))
save("s9.wav", x)

# s10 quick whoosh for cuts --------------------------------------------------
w = lp(hp(noise(0.4), 0.3), 0.6) * np.sin(np.linspace(0, np.pi, int(SR * 0.4))) ** 3
save("s10.wav", w, 0.7)

# music: playful pizzicato + glockenspiel, 104 BPM, C major ------------------
BPM = 104; beat = 60 / BPM; bars = 16
L = bars * 4 * beat
m = np.zeros(int(SR * (L + 1)))
prog = [("C", 130.81), ("A", 110.0), ("F", 87.31), ("G", 98.0)]
triads = {"C": [261.6, 329.6, 392.0], "A": [220.0, 261.6, 329.6], "F": [174.6, 220.0, 261.6], "G": [196.0, 246.9, 293.7]}
mel = [784, 659, 784, 880, 784, 659, 587, 523,  659, 587, 523, 587, 659, 0, 523, 0,
       698, 659, 587, 523, 587, 659, 698, 784,  784, 698, 659, 587, 523, 0, 0, 0]
for b in range(bars):
    name, root = prog[b % 4]
    t0 = b * 4 * beat
    # walking pizzicato bass: root, fifth, octave, fifth
    for k, mult in enumerate([1, 1.5, 2, 1.5]):
        place(m, pluck(root * mult, beat * 0.9, 0.6, 0.992) * 0.9, t0 + k * beat)
    # off-beat chord plucks
    for k in range(4):
        for f in triads[name]:
            place(m, pluck(f, beat * 0.4, 0.5, 0.985) * 0.22, t0 + k * beat + beat / 2)
    # glockenspiel melody (eighth notes) on the second half of each 8-bar phrase and every bar after bar 4
    if b >= 2:
        for k in range(8):
            f = mel[((b - 2) % 4) * 8 + k]
            if f: place(m, bell(f * 2, beat * 1.2, 0.3) * 0.28, t0 + k * beat / 2)
# light shaker
for k in range(int(L / (beat / 2))):
    place(m, hp(noise(0.05), 0.5) * env(int(SR * 0.05), 0.001, 0.015) * (0.12 if k % 2 else 0.07), k * beat / 2)
m = lp(m, 0.6)
save("music.wav", m[:int(SR * L)], 0.8)
print("ok", OUT, "music %.1fs" % L)
