"""Synthesize SFX track from events.json -> sfx.wav"""
import sys, json, wave
import numpy as np
from scipy import signal

EV, OUT, DUR = sys.argv[1], sys.argv[2], float(sys.argv[3])
SR = 48000
rng = np.random.default_rng(7)
track = np.zeros(int(SR * (DUR + 1)), np.float32)

def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(t / a, 1.0) * np.exp(-t / d)

def pop(gain=0.6):
    n = int(SR * 0.16); t = np.arange(n) / SR
    f = 900 * np.exp(-t * 18) + 380
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * env(n, 0.002, 0.035) * gain).astype(np.float32)

def ding(gain=0.35):
    n = int(SR * 0.9); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t) * a for f, a in [(1318, 1), (2637, .35), (1975, .25)])
    return (s * env(n, 0.003, 0.28) * gain).astype(np.float32)

def whoosh(gain=0.45):
    n = int(SR * 0.5); x = rng.standard_normal(n)
    out = np.zeros(n)
    for i in range(0, n, 512):
        fc = 400 + 3500 * (i / n) ** 1.5
        b, a = signal.butter(2, [fc * 0.7 / (SR / 2), min(fc * 1.4 / (SR / 2), 0.99)], "band")
        out[i:i + 512] = signal.lfilter(b, a, x[i:i + 512])
    e = np.sin(np.pi * np.arange(n) / n) ** 2
    return (out * e / np.abs(out).max() * gain).astype(np.float32)

def draw(dur, gain=0.10):
    n = int(SR * dur); x = rng.standard_normal(n)
    b, a = signal.butter(2, [2500 / (SR / 2), 7000 / (SR / 2)], "band")
    y = signal.lfilter(b, a, x)
    t = np.arange(n) / SR
    strokes = 0.5 + 0.5 * np.sin(2 * np.pi * 5.5 * t + 2 * np.sin(2 * np.pi * 1.3 * t))
    fade = np.minimum(1, t / 0.08) * np.minimum(1, (dur - t) / 0.25)
    return (y / np.abs(y).max() * strokes * fade * gain).astype(np.float32)

def stamp(gain=0.7):
    n = int(SR * 0.25); t = np.arange(n) / SR
    thump = np.sin(2 * np.pi * (120 * np.exp(-t * 10) + 50) * t) * env(n, 0.001, 0.06)
    click = rng.standard_normal(n) * env(n, 0.0005, 0.008)
    return ((thump + 0.4 * click) * gain).astype(np.float32)

for e in json.load(open(EV))["events"]:
    k = e["kind"]
    s = {"pop": lambda: pop(e.get("gain", 0.6)), "ding": ding, "whoosh": whoosh,
         "draw": lambda: draw(e.get("dur", 1.0)), "stamp": stamp}[k]()
    i = int(e["t"] * SR)
    if i < 0: s = s[-i:]; i = 0
    track[i:i + len(s)] += s[:len(track) - i]

track = np.clip(track, -1, 1)
with wave.open(OUT, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((track * 32767).astype(np.int16).tobytes())
print("sfx ok")
