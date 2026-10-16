"""Trim pauses in the ElevenLabs voiceover to ~0.1s, fit to ~19.4s, write timing.json."""
import json, subprocess, os
A = os.environ.get("AUD", "/home/claude/hpv_audio")
# speech segments from ffmpeg silencedetect (-35dB, 0.12s) on vo.mp3
segs = [(0.0, 3.51), (3.99, 5.23), (5.50, 6.96), (7.34, 8.36), (8.62, 9.06), (9.21, 10.53),
        (10.96, 12.44), (12.74, 14.47), (14.82, 17.48), (17.82, 18.40), (18.67, 21.46)]
pad, gap, target = 0.04, 0.10, 19.4
parts, starts, ends, t = [], [], [], 0.0
for s, e in segs:
    s0, e0 = max(0, s - pad), e + pad
    starts.append(t); ends.append(t + e0 - s0); parts.append((s0, e0)); t += e0 - s0 + gap
total = t - gap; k = max(1.0, total / target)
print("total", round(total, 2), "atempo", round(k, 3))
f, lab = [], ""
for i, (s, e) in enumerate(parts):
    f.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,apad=pad_dur={gap}[p{i}]"); lab += f"[p{i}]"
f.append(lab + f"concat=n={len(parts)}:v=0:a=1,atempo={k:.4f},afade=t=in:d=0.02[out]")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{A}/vo.mp3", "-filter_complex", ";".join(f),
                "-map", "[out]", "-ar", "44100", f"{A}/vo_edit.wav"], check=True)
st = [round(x / k, 3) for x in starts]; en = [round(x / k, 3) for x in ends]
scenes = [0.0, st[1] - 0.15, st[3] - 0.15, st[6] - 0.15, st[8] - 0.15, st[9] - 0.15, 20.0]
subs = [(st[0], "۳ تا چیزی که درباره‌ی HPV اشتباه فکر می‌کنی"), (st[1], "فکر می‌کنی نادره؟"),
        (st[2], "نه، خیلی رایجه"), (st[3], "فقط خانم‌ها؟"), (st[4], "نه، آقایون هم درگیر می‌شن"),
        (st[6], "فکر می‌کنی علامت داره؟"), (st[7], "اغلب هیچ نشونه‌ای نداره"),
        (st[8], "پس بهترین کار، چکاپ و غربالگریه"), (st[9], "نمونت، آزمایش HPV در محیط امن خونه‌ات")]
tim = dict(seg_starts=st, seg_ends=en, scenes=[round(x, 3) for x in scenes], subs=subs,
           cross=[st[2], st[4], st[7]])
json.dump(tim, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "timing.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(tim, ensure_ascii=False))
