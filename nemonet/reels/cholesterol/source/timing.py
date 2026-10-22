"""Build timing.json (scene cuts + per-word caption times).
  python3 timing.py vo.mp3   -> tighten pauses into vo_fit.wav and time from it
  python3 timing.py          -> estimated timing (no voiceover yet)"""
import sys, json, re, subprocess
import numpy as np
from scipy.io import wavfile
from lines import LINES, words, wlen

SR = 44100
LINE_GAP = 0.28     # silence kept between lines
INNER_GAP = 0.30    # max silence kept inside a line
TAIL = 0.9


def speech_segments(wav):
    r = subprocess.run(["ffmpeg", "-i", wav, "-af", "silencedetect=n=-30dB:d=0.1", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r)]
    dur = float(re.search(r"time=(\d+):(\d+):([\d.]+)", r.split("silencedetect")[-1]).group(3)) if False else None
    sr, x = wavfile.read(wav)
    total = len(x) / sr
    sil = list(zip(st, en + [total] * (len(st) - len(en))))
    segs, cur = [], 0.0
    for a, b in sil:
        if a > cur + 0.02: segs.append([cur, a])
        cur = b
    if cur < total - 0.02: segs.append([cur, total])
    return segs, x, sr


def from_vo(mp3):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp3, "-ac", "1", "-ar", str(SR), "vo_raw.wav"], check=True)
    segs, x, sr = speech_segments("vo_raw.wav")
    x = x.astype(np.float32)
    n = len(LINES)
    import os
    if os.path.exists("groups.json"):  # manual: number of speech segments per line
        counts = json.load(open("groups.json"))
        assert sum(counts) == len(segs), (sum(counts), len(segs))
        groups, s = [], 0
        for c in counts:
            groups.append(segs[s:s + c]); s += c
    else:
        gaps = [(segs[i + 1][0] - segs[i][1], i) for i in range(len(segs) - 1)]
        cut_after = sorted(i for _, i in sorted(gaps, reverse=True)[: n - 1])
        groups, s = [], 0
        for i in cut_after:
            groups.append(segs[s:i + 1]); s = i + 1
        groups.append(segs[s:])
    assert len(groups) == n, (len(groups), n)
    # rebuild audio with tightened pauses, remember new positions
    out, t, lines = [], 0.0, []
    pad = int(0.04 * sr)
    for gi, g in enumerate(groups):
        lsegs = []
        for k, (a, b) in enumerate(g):
            i0, i1 = max(0, int(a * sr) - pad), min(len(x), int(b * sr) + pad)
            chunk = x[i0:i1]
            lsegs.append([t, t + len(chunk) / sr]); out.append(chunk); t += len(chunk) / sr
            if k < len(g) - 1:
                gap = min(INNER_GAP, g[k + 1][0] - b)
                out.append(np.zeros(int(gap * sr), np.float32)); t += gap
        lines.append(lsegs)
        if gi < n - 1:
            out.append(np.zeros(int(LINE_GAP * sr), np.float32)); t += LINE_GAP
    y = np.concatenate(out)
    wavfile.write("vo_fit.wav", sr, y.astype(np.int16))
    print("vo raw", round(len(x) / sr, 2), "-> fitted", round(t, 2), "s; segs per line", [len(g) for g in groups])
    return lines, t


def estimate():
    t, lines = 0.0, []
    for ln in LINES:
        d = sum(wlen(w) for w in words(ln)) / 13.0
        lines.append([[t, t + d]]); t += d + LINE_GAP
    return lines, t - LINE_GAP


def word_times(ln, lsegs):
    """spread words over the line's speech segments by character weight"""
    chunks = ln[1]
    if len(chunks) == len(lsegs) > 1:  # one speech segment per caption chunk
        out = []
        for ch, sg in zip(chunks, lsegs):
            out += word_times(("", [ch]), [sg])
        return out
    ws = words(ln)
    tot_speech = sum(b - a for a, b in lsegs)
    wts = np.array([wlen(w) for w in ws]); wts = wts / wts.sum() * tot_speech
    times, acc = [], 0.0
    # map cumulative speech time -> absolute time through the segments
    def at(s):
        for a, b in lsegs:
            if s <= b - a + 1e-6: return a + s
            s -= b - a
        return lsegs[-1][1]
    for w in wts:
        times.append(at(acc)); acc += w
    return times


if __name__ == "__main__":
    if len(sys.argv) > 1:
        lines, end = from_vo(sys.argv[1]); mode = "vo"
    else:
        lines, end = estimate(); mode = "estimate"
    scenes = [0.0] + [max(0.0, l[0][0] - 0.08) for l in lines[1:]]
    data = {"mode": mode, "duration": round(end + TAIL, 3), "scenes": scenes,
            "lines": [{"start": l[0][0], "end": l[-1][1], "segs": l, "words": word_times(LINES[i], l)}
                      for i, l in enumerate(lines)]}
    json.dump(data, open("timing.json", "w"), ensure_ascii=False, indent=1)
    print(mode, "duration", data["duration"])
