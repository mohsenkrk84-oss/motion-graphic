"""Nemonet pimple reel ("don't squeeze it") – full build.
python3 -I build.py out.mp4 [--preview start end]

Lip-sync composites ONLY the mouth/face box of the open image onto the closed
pose image, so hands and bodies come from one image per pose and never jitter.
"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__)) + "/"
REPO = os.path.abspath(HERE + "../../..") + "/"          # .../nemonet/
IMG = REPO + "reels/pimple/"
AUD = IMG
FONT = REPO + "IRANYekanWebBlack.woff2"
W, H, FPS = 1080, 1920, 30
OUT = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "pimple_reel.mp4"
PREVIEW = None
if "--preview" in sys.argv:
    i = sys.argv.index("--preview"); PREVIEW = (float(sys.argv[i + 1]), float(sys.argv[i + 2]))


# ---------------------------------------------------------------- audio utils
def pcm(path, start=0.0, dur=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(start)]
    if dur: cmd += ["-t", str(dur)]
    cmd += ["-i", path, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.int16).astype(np.float32) / 32768


def adur(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                capture_output=True, text=True).stdout)


def rms_frames(a):
    hop = 16000 // FPS
    n = int(math.ceil(len(a) / hop))
    r = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    return r / (np.percentile(r, 97) + 1e-9)


def voiced_span(path):
    """(first, last) voiced time in a clip, so trailing silence isn't counted."""
    a = pcm(path); r = rms_frames(a); v = np.nonzero(r > 0.06)[0]
    return max(0.0, v[0] / FPS - 0.05), min(len(a) / 16000, (v[-1] + 1) / FPS + 0.08)


# ---------------------------------------------------------------- images
IMS = {}
def img(key):
    if key not in IMS:
        im = Image.open(IMG + key + ".jpg").convert("RGB")
        w, h = im.size; th = round(w * 16 / 9); top = (h - th) // 2
        IMS[key] = im.crop((0, top, w, top + th))
    return IMS[key]


def mouth_box(a, b, region, thr=40, pad=14):
    A = np.asarray(img(a).convert("L")).astype(int); B = np.asarray(img(b).convert("L")).astype(int)
    x0, y0, x1, y1 = region
    d = np.abs(A[y0:y1, x0:x1] - B[y0:y1, x0:x1]) > thr
    d = ndimage.binary_opening(d, iterations=1)
    ys, xs = np.nonzero(d)
    if len(xs) == 0: return None
    return (x0 + xs.min() - pad, y0 + ys.min() - pad, x0 + xs.max() + pad, y0 + ys.max() + pad)


def feather_paste(dst, src, box, blur=8):
    m = Image.new("L", dst.size, 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=18, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    return Image.composite(src, dst, m)


def face_swap(base, donor, region, name):
    """base pose + only the face region of donor -> new image key."""
    box = mouth_box(base, donor, region)
    IMS[name] = feather_paste(img(base), img(donor), box) if box else img(base)
    return name


# face search regions (768x1365 source coords)
R_PIMPLE = (230, 770, 530, 1100)
R_TWEEZ = (150, 250, 340, 420)
R_NEW = (595, 800, 720, 940)
R_DEEP = (330, 650, 540, 850)
R_PAT = (150, 335, 310, 545)
R_DOC = (480, 335, 635, 505)

# open composites: closed pose + open face only
O = {}
O["1a"] = face_swap("1-1", "1-2", R_PIMPLE, "1-1o")
O["1b"] = face_swap("1-4", "1-3", R_PIMPLE, "1-4o")
O["2a"] = face_swap("2-1", "2-2", R_TWEEZ, "2-1o")
O["2b"] = face_swap("2-4", "2-3", R_PIMPLE, "2-4o")
face_swap("2-5", "2-6", R_NEW, "2-5c")                 # new pimple closed, first pimple frowning
O["2c"] = face_swap("2-5c", "2-5", R_NEW, "2-5o")
O["2d"] = face_swap("2-7", "2-6", R_PIMPLE, "2-7o")
O["3a"] = face_swap("3-2", "3-1", R_DEEP, "3-2o")
O["3b"] = face_swap("3-4", "3-3", R_DEEP, "3-4o")
O["4a"] = face_swap("4-1", "4-2", R_PAT, "4-1o")
O["4b"] = face_swap("4-4", "4-3", R_DOC, "4-4o")
O["4c"] = face_swap("4-5", "4-6", R_PAT, "4-5o")


# ---------------------------------------------------------------- text
def text_layer(text, size, fill="white", stroke=10, stroke_fill="black", pad=40, rtl=True):
    f = ImageFont.truetype(FONT, size)
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    kw = dict(direction="rtl", language="fa") if rtl else {}
    bb = d.textbbox((0, 0), text, font=f, stroke_width=stroke, anchor="lt", **kw)
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((pad - bb[0], pad - bb[1]), text, font=f, fill=fill, stroke_width=stroke,
                             stroke_fill=stroke_fill, anchor="lt", **kw)
    return lay


def pill(text):
    t = text_layer(text, 64, fill=(40, 20, 10), stroke=0, pad=30)
    w, h = t.size
    lay = Image.new("RGBA", (w + 60, h + 10), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle((0, 0, w + 59, h + 9), radius=(h + 10) // 2, fill=(255, 244, 225, 245),
                                          outline=(40, 20, 10, 255), width=6)
    lay.alpha_composite(t, (30, 5)); return lay


HANDLE = text_layer("@nemonet.ir", 34, fill=(255, 255, 255, 170), stroke=3, stroke_fill=(0, 0, 0, 110), pad=10, rtl=False)


# ---------------------------------------------------------------- timeline
class Seg:
    def __init__(self, **k): self.__dict__.update(k)

segs, clips, sfx, titles = [], [], [], []
t = 0.0

def line(v, words, closed, opened, lead=0.1, tail=0.25, **kw):
    global t
    path = AUD + v + ".mp3"
    ss, se = voiced_span(path)
    dur = se - ss
    start = t; vstart = start + lead
    clips.append((vstart, path, ss, dur, 1.0))
    s = Seg(start=start, vstart=vstart, end=vstart + dur + tail, rms=rms_frames(pcm(path, ss, dur)),
            words=words, closed=closed, open=opened, **kw)
    segs.append(s); t = s.end
    return s

def fx(at, name, gain=0.5, ss=0.0, dur=None):
    sfx.append((max(at, 0.0), AUD + name + ".mp3", ss, dur, gain))

CAP_SKIN = 1720     # captions in the empty dermis / floor area
FOC_SKIN = (0.5, 0.62)

# Scene 1: finger ----------------------------------------------------------
s = line("v1", "باز اومدی؟ بزن ببینم چی کار می‌کنی!", "1-1", O["1a"], lead=0.55, tail=0.2,
         punch=True, cap_y=CAP_SKIN, focus=FOC_SKIN)
fx(0.0, "s1", 0.45)
s = line("v2", "قلقلکم اومد!", "1-4", O["1b"], lead=0.25, tail=0.3,
         punch=True, shake=True, cap_y=CAP_SKIN, focus=FOC_SKIN)
fx(s.start, "s2", 0.6)

# Scene 2: tweezers ---------------------------------------------------------
fx(t - 0.2, "s10", 0.4)
s = line("v3", "کنار، کار حرفه‌ایه!", "2-1", O["2a"], lead=0.45, tail=0.2,
         punch=True, cap_y=CAP_SKIN, focus=FOC_SKIN)
fx(s.start + 0.05, "s3", 0.55)
s = line("v4", "آخ آخ! یواش!", "2-4", O["2b"], lead=0.3, tail=0.15,
         punch=True, shake=True, shake_all=True, cap_y=CAP_SKIN, focus=FOC_SKIN)
fx(s.start, "s4", 0.6)
s = line("v5", "سلااام! من تازه رسیدم!", "2-5c", O["2c"], lead=0.45, tail=0.15,
         punch=True, shake=True, cap_y=CAP_SKIN, focus=FOC_SKIN)
fx(s.start, "s5", 0.6); fx(s.start + 0.25, "s6", 0.6)
s = line("v6", "دیدی؟ فشارم بدی، فامیلامو هم دعوت می‌کنم.", "2-7", O["2d"], lead=0.1, tail=0.35,
         cap_y=CAP_SKIN, focus=FOC_SKIN)

# Scene 3: under the skin ---------------------------------------------------
fx(t - 0.15, "s7", 0.5)
s = line("v7", "حالا که اینقدر فشارم دادی، یه کم میرم پایین‌تر... جام راحت‌تره.", "3-2", O["3a"], lead=0.9, tail=0.2,
         punch=True, push=0.02, cap_y=1760, focus=(0.5, 0.5))
titles.append((s.start + 0.1, "زیر پوست"))
s = line("v8", "یه یادگاری هم برات می‌ذارم!", "3-4", O["3b"], lead=0.35, tail=0.5,
         punch=True, cap_y=1760, focus=(0.5, 0.5))
fx(s.start, "s11", 0.55)

# Scene 4: clinic -----------------------------------------------------------
fx(t - 0.2, "s10", 0.4)
CAP_DOC = 1700
s = line("v9", "دکتر، فقط یه دونه بود! فشارش دادم، شد سه تا!", "4-1", O["4a"], lead=0.45, tail=0.2,
         punch=True, cap_y=CAP_DOC, focus=(0.5, 0.45))
s = line("v10", "چون با فشار دادن، چرک و میکروب رو یا به منفذای کناری پخش می‌کنی، یا هلشون میدی زیر پوست.",
         "4-4", O["4b"], lead=0.15, tail=0.2, punch=True, cap_y=CAP_DOC, focus=(0.5, 0.45))
s = line("v11", "نتیجه‌ش التهاب بیشتره، دیرتر خوب شدن، و گاهی جای جوش یا لک.",
         "4-4", O["4b"], lead=0.1, tail=0.2, cap_y=CAP_DOC, focus=(0.5, 0.45))
s = line("v12", "پس چی کار کنم؟", "4-1", O["4a"], lead=0.1, tail=0.2,
         punch=True, cap_y=CAP_DOC, focus=(0.5, 0.45))
s = line("v13", "بذار خودش خوب شه، صورتتو ملایم بشور. اگه جوشات زیاد و همیشگیه، شاید مشکل از هورمون‌هاته؛ هم متخصص پوست، هم یه آزمایش.",
         "4-4", O["4b"], lead=0.1, tail=0.25, punch=True, cap_y=CAP_DOC, focus=(0.5, 0.45))
s = line("v14", "سخت‌ترین کار دنیا...", "4-5", O["4c"], lead=0.25, tail=1.3,
         punch=True, cap_y=CAP_DOC, focus=(0.5, 0.45))
TOTAL = t
NF = int(round(TOTAL * FPS))


# ---------------------------------------------------------------- derived per segment
def regions(mask):
    r, s0 = [], None
    for i, v in enumerate(mask):
        if v and s0 is None: s0 = i
        if not v and s0 is not None:
            if i - s0 >= 2: r.append([s0, i])
            s0 = None
    if s0 is not None: r.append([s0, len(mask)])
    out = []
    for g in r:
        if out and g[0] - out[-1][1] <= 3: out[-1][1] = g[1]
        else: out.append(g)
    return out

for s in segs:
    voiced = s.rms > 0.10
    frames = [f for a, b in regions(voiced) for f in range(a, b)] or list(range(len(s.rms)))
    words = s.words.split()
    wts = np.array([len(w.strip(".،!؟:؛")) + 1.6 for w in words], float)
    cum = np.concatenate([[0], np.cumsum(wts) / wts.sum()])
    s.wt = [(s.vstart + frames[min(int(cum[i] * len(frames)), len(frames) - 1)] / FPS, w) for i, w in enumerate(words)]
    m = np.zeros(len(s.rms), int); run = 0
    for i, v in enumerate(s.rms):
        o = v > 0.16
        if o:
            run += 1
            if run % 5 == 0: o = False
        else: run = 0
        m[i] = o
    for i in range(1, len(m) - 1):
        if m[i - 1] == m[i + 1] != m[i] and m[i]: m[i] = m[i - 1]
    s.mouth = m


# ---------------------------------------------------------------- render
def camera(src, zoom, fx_, fy_, ox=0.0, oy=0.0):
    sw, sh = src.size
    cw, ch = sw / zoom, sh / zoom
    x0 = min(max(fx_ * sw - cw * fx_ - ox * sw, 0), sw - cw)
    y0 = min(max(fy_ * sh - ch * fy_ - oy * sh, 0), sh - ch)
    return src.resize((W, H), Image.BILINEAR if PREVIEW else Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))


CAP_CACHE = {}
def caption_layer(word):
    if word not in CAP_CACHE: CAP_CACHE[word] = text_layer(word, 92, stroke=11)
    return CAP_CACHE[word]

PILLS = {}
def ease_out(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def pop_scale(dt, dur=0.18):
    if dt < 0: return 0
    return ease_out(min(1, dt / dur)) + 0.18 * math.sin(min(1, dt / 0.32) * math.pi)

def scaled(lay, sc):
    return lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.LANCZOS)


def render(f):
    tt = f / FPS
    s = next((x for x in segs if x.start <= tt < x.end), segs[-1])
    lt = tt - s.start
    vi = int(round((tt - s.vstart) * FPS))
    mouth = s.mouth[vi] if 0 <= vi < len(s.mouth) else 0
    zoom = 1.0; ox = oy = 0.0
    if getattr(s, "punch", False): zoom += 0.06 * math.exp(-lt / 0.13)
    zoom += getattr(s, "push", 0.010) * lt
    if getattr(s, "shake", False):
        k = 1.0 if getattr(s, "shake_all", False) and lt < s.end - s.start - 0.2 else math.exp(-lt / 0.6)
        ox = 0.006 * math.sin(lt * 55) * k
        oy = 0.004 * math.cos(lt * 47) * k
    src = img(s.open if mouth else s.closed)
    frame = camera(src, max(zoom, 1.01), *s.focus, ox, oy).convert("RGBA")

    for at, text in titles:
        dt = tt - at
        if 0 <= dt < 1.8:
            if text not in PILLS: PILLS[text] = pill(text)
            lay = scaled(PILLS[text], pop_scale(dt))
            a = 1.0 if dt < 1.5 else max(0, 1 - (dt - 1.5) / 0.3)
            if a < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
            frame.alpha_composite(lay, (W // 2 - lay.width // 2, 240 - lay.height // 2))

    frame.alpha_composite(HANDLE, (36, 150))

    cur = [(st, w) for st, w in s.wt if st <= tt]
    if cur:
        st, w = cur[-1]
        nxt = [x for x, _ in s.wt if x > st]
        end = nxt[0] if nxt else s.end
        if tt < end + 0.25:
            sc = 0.62 + 0.38 * ease_out((tt - st) / 0.12) + 0.07 * math.sin(min(1, (tt - st) / 0.2) * math.pi)
            lay = scaled(caption_layer(w), sc)
            frame.alpha_composite(lay, (W // 2 - lay.width // 2, s.cap_y - lay.height // 2))
    out = frame.convert("RGB")
    if tt < 0.3:
        out = Image.blend(Image.new("RGB", out.size, (0, 0, 0)), out, tt / 0.3)
    if tt > TOTAL - 0.6:
        out = Image.blend(out, Image.new("RGB", out.size, (0, 0, 0)), min(1, (tt - (TOTAL - 0.6)) / 0.6))
    return out


# ---------------------------------------------------------------- audio mix
def build_audio(path):
    inputs, filters, labels = [], [], []
    def add(p, at, ss, dur, gain, norm=None):
        i = len(inputs) // 2; inputs.extend(["-i", p])
        tr = f"atrim={ss:.3f}" + (f":duration={dur:.3f}" if dur else "")
        n = f",loudnorm=I={norm}:TP=-2,aresample=48000" if norm else ""
        filters.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,{tr},asetpts=PTS-STARTPTS{n},volume={gain},adelay={int(at*1000)}|{int(at*1000)}[a{i}]")
        labels.append(f"[a{i}]")
    for at, p, ss, dur, g in clips: add(p, at, ss, dur, g, norm=-16)
    for at, p, ss, dur, g in sfx: add(p, at, ss, dur, g)
    i1 = len(inputs) // 2; inputs += ["-i", AUD + "s8-1.mp3"]
    i2 = len(inputs) // 2; inputs += ["-i", AUD + "s8-2.mp3"]
    filters.append(f"[{i1}:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-24:TP=-3,aresample=48000[m1]")
    filters.append(f"[{i2}:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-24:TP=-3,aresample=48000[m2]")
    filters.append("[m1][m2]acrossfade=d=1.5[m12]")
    filters.append(f"[m12]aloop=loop=2:size=2880000,atrim=0:{TOTAL:.3f},volume=0.2,afade=t=in:d=0.6,afade=t=out:st={TOTAL-1.2:.3f}:d=1.2[mus]")
    labels.append("[mus]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,atrim=0:{TOTAL:.3f},alimiter=limit=0.95[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters),
                    "-map", "[out]", "-c:a", "pcm_s16le", path], check=True)


if __name__ == "__main__":
    print("total %.2fs, %d frames" % (TOTAL, NF))
    for s in segs: print(f"{s.start:6.2f}-{s.end:6.2f} {s.closed:5s} {s.words[:40]}")
    if "--sheet" in sys.argv:
        times = [x.vstart + 0.4 for x in segs]
        tiles = [render(int(tm * FPS)).resize((270, 480)) for tm in times]
        sh = Image.new("RGB", (270 * 7, 480 * 2), "white")
        for i, tl in enumerate(tiles): sh.paste(tl, ((i % 7) * 270, (i // 7) * 480))
        sh.save(sys.argv[sys.argv.index("--sheet") + 1]); sys.exit()
    mix = os.path.splitext(OUT)[0] + "_mix.wav"
    build_audio(mix)
    f0, f1 = (0, NF) if not PREVIEW else (int(PREVIEW[0] * FPS), int(PREVIEW[1] * FPS))
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-ss", str(f0 / FPS), "-t", str((f1 - f0) / FPS), "-i", mix,
           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-af", "apad", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(render(f).tobytes())
    p.stdin.close(); p.wait()
    os.remove(mix)
    print("done", OUT)
