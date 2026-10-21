"""Detect phrase timings in vo.mp3 using pauses; writes timings.json"""
import sys, json, subprocess, re

VO, OUT = sys.argv[1], sys.argv[2]
PHR = ["اگزوزوم و تزریق‌های میلیونی، واقعاً معجزه می‌کنن؟", "یا فقط هدر دادنِ پوله؟",
       "اگه علتِ لک یا آکنه‌ی شما اختلالِ هورمونی باشه،", "ده جلسه اگزوزوم هم موقتیه!",
       "اول باید هورمون‌هات رو بررسی کنی؛", "راحت، تو خونه، با نمونِت.",
       "تو کدوم درمانِ ترندِ پوستی رو امتحان کردی؟", "تو کامنت‌ها برام بنویس!"]

def silences(noise):
    r = subprocess.run(["ffmpeg", "-i", VO, "-af", f"silencedetect=noise={noise}dB:d=0.12", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r)]
    dur = float(re.search(r"Duration: (\d+):(\d+):([\d.]+)", r).group(3)) + 60 * int(re.search(r"Duration: (\d+):(\d+)", r).group(2))
    return list(zip(st, en + [dur] * (len(st) - len(en)))), dur

sil, dur = silences(-35)
if len(sil) < 8:
    sil, dur = silences(-30)
speech_start = sil[0][1] if sil and sil[0][0] < 0.05 else 0.0
speech_end = sil[-1][0] if sil and sil[-1][1] >= dur - 0.05 else dur
gaps = [(a, b) for a, b in sil if a > speech_start + 0.1 and b < speech_end - 0.1]
lens = [len(p) for p in PHR]
tot = sum(lens)
cum, c = [], 0
for l in lens[:-1]:
    c += l; cum.append(speech_start + (speech_end - speech_start) * c / tot)
# choose a gap for each expected boundary, monotonic, prefer long gaps near expectation
chosen, last = [], -1
for k, e in enumerate(cum):
    best, bs = None, 1e9
    for gi, (a, b) in enumerate(gaps):
        if gi <= last: continue
        if len(gaps) - gi < len(cum) - k: break
        score = abs((a + b) / 2 - e) - 0.8 * (b - a)
        if score < bs: best, bs = gi, score
    if best is None:
        chosen.append((e, e)); continue
    chosen.append(gaps[best]); last = best
starts = [speech_start] + [b for a, b in chosen]
ends = [a for a, b in chosen] + [speech_end]
phr = [[round(s, 2), round(e, 2)] for s, e in zip(starts, ends)]
json.dump({"phrases": phr, "end": round(speech_end + 1.6, 2), "vo_dur": dur}, open(OUT, "w"), indent=1)
print("gaps:", [(round(a, 2), round(b, 2)) for a, b in gaps])
print("expected:", [round(x, 2) for x in cum])
for p, t in zip(PHR, phr): print(t, p)
