"""Nemonet double-uterus reel ("pregnant, but a period?!") – full build.
python3 -I build.py out.mp4 [--preview start end] [--sheet sheet.jpg]

Lip-sync composites ONLY the mouth box of the open image onto the closed pose,
so bodies never jitter. Captions and mouth movement follow real word timings
(ElevenLabs Scribe, source/words/vN.json); without a json the timing is
estimated from the loudness envelope.
"""
import sys, os, math, json, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__)) + "/"
REEL = os.path.abspath(HERE + "..") + "/"                  # nemonet/reels/double-uterus/
REPO = os.path.abspath(REEL + "../..") + "/"                # nemonet/
FONT = REPO + "IRANYekanWebBlack.woff2"
W, H, FPS = 1080, 1920, 30
OUT = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "double_uterus_reel.mp4"
PREVIEW = None
if "--preview" in sys.argv:
    i = sys.argv.index("--preview"); PREVIEW = (float(sys.argv[i + 1]), float(sys.argv[i + 2]))


# ---------------------------------------------------------------- audio utils
SR = 48000
TMP = os.path.join(os.environ.get("TMPDIR", "/tmp"), "du_build")
os.makedirs(TMP, exist_ok=True)

def pcm(path, start=0.0, dur=None, sr=SR):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(start)]
    if dur: cmd += ["-t", str(dur)]
    cmd += ["-i", path, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.int16).astype(np.float32) / 32768


def rms_frames(a, sr=SR):
    hop = sr // FPS
    n = int(math.ceil(len(a) / hop))
    r = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    return r / (np.percentile(r, 97) + 1e-9)


def voiced_span(a):
    r = rms_frames(a); v = np.nonzero(r > 0.06)[0]
    return max(0.0, v[0] / FPS - 0.06), min(len(a) / SR, (v[-1] + 1) / FPS + 0.1)


def write_wav(path, a):
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())


def word_times(v, words, rms, ss):
    """[(start, end)] per script word, relative to the trimmed clip start (ss)."""
    jp = HERE + "words/" + v + ".json"
    if os.path.exists(jp):
        tw = [x for x in json.load(open(jp)) if x.get("type", "word") == "word"]
        if len(tw) == len(words):
            return [(x["start"] - ss, x["end"] - ss) for x in tw]
        # merge/split by normalised letters (e.g. «آخ‌جون» = «آخ» + «جون»)
        norm = lambda s: "".join(c for c in s if c.isalpha() and c not in "ًٌٍَُِّْ")
        if norm("".join(x["text"] for x in tw)) == norm("".join(words)):
            out, k = [], 0
            for w in words:
                need, got, a = len(norm(w)), 0, tw[k]["start"]
                while got < need: got += len(norm(tw[k]["text"])); b = tw[k]["end"]; k += 1
                out.append((a - ss, b - ss))
            return out
        # different tokenisation: map by cumulative character position
        tl = np.array([len(x["text"]) + 1 for x in tw], float); tc = np.concatenate([[0], np.cumsum(tl)]) / tl.sum()
        def at(p):
            k = min(np.searchsorted(tc, p, side="right") - 1, len(tw) - 1)
            fr = (p - tc[k]) / max(tc[k + 1] - tc[k], 1e-9)
            return tw[k]["start"] + fr * (tw[k]["end"] - tw[k]["start"]) - ss
        sl = np.array([len(w) + 1 for w in words], float); sc = np.concatenate([[0], np.cumsum(sl)]) / sl.sum()
        return [(at(sc[i]), at(sc[i + 1] - 1e-6)) for i in range(len(words))]
    voiced = np.nonzero(rms > 0.10)[0]
    wts = np.array([len(w.strip(".،!؟:؛…")) + 1.6 for w in words], float)
    cum = np.concatenate([[0], np.cumsum(wts) / wts.sum()])
    fr = lambda p: voiced[min(int(p * len(voiced)), len(voiced) - 1)] / FPS
    return [(fr(cum[i]), fr(cum[i + 1])) for i in range(len(words))]


# ---------------------------------------------------------------- images
IMS = {}
def img(key):
    if key not in IMS:
        im = Image.open(REEL + key + ".jpg").convert("RGB")
        w, h = im.size; th = round(w * 16 / 9); top = (h - th) // 2
        IMS[key] = im.crop((0, top, w, top + th))
    return IMS[key]


def diff_box(a, b, region, thr=40, pad=12):
    A = np.asarray(img(a).convert("L")).astype(int); B = np.asarray(img(b).convert("L")).astype(int)
    x0, y0, x1, y1 = region
    d = ndimage.binary_opening(np.abs(A[y0:y1, x0:x1] - B[y0:y1, x0:x1]) > thr, iterations=1)
    ys, xs = np.nonzero(d)
    if len(xs) == 0: return None
    return (x0 + xs.min() - pad, y0 + ys.min() - pad, x0 + xs.max() + pad, y0 + ys.max() + pad)


def feather_paste(dst, src, box, blur=7):
    """paste src's box onto dst; src is colour-matched to dst around the box first."""
    x0, y0, x1, y1 = [int(v) for v in box]
    D = np.asarray(dst, np.float32); S = np.asarray(src, np.float32)
    ring = np.zeros(D.shape[:2], bool); ring[max(y0 - 10, 0):y1 + 10, max(x0 - 10, 0):x1 + 10] = True
    ring[y0:y1, x0:x1] = False
    gain = (D[ring].mean(0) + 1) / (S[ring].mean(0) + 1)
    S = np.clip(S * gain, 0, 255).astype(np.uint8)
    m = Image.new("L", dst.size, 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=14, fill=255)
    return Image.composite(Image.fromarray(S), dst, m.filter(ImageFilter.GaussianBlur(blur)))


def face_swap(base, donor, region, name):
    box = diff_box(base, donor, region)
    IMS[name] = feather_paste(img(base), img(donor), box) if box else img(base)
    return name


# mouth search regions (cropped 768x1365 source coords)
R_SPERM = (330, 750, 440, 915)
R_L = (175, 270, 335, 410)
R_R = (435, 320, 590, 405)
R_RWAIL = (420, 320, 665, 455)
R_PAT = (575, 440, 665, 575)
R_DOC = (125, 490, 255, 590)

O = {}
O["sperm"] = face_swap("1-1", "1-2", R_SPERM, "1-1s")
O["L1"] = face_swap("1-1", "1-3", R_L, "1-1L")
O["R1"] = face_swap("1-1", "1-4", R_R, "1-1R")
O["R2"] = face_swap("2-1", "2-2", R_R, "2-1R")
O["R3a"] = face_swap("3-1", "3-3", R_R, "3-1R")          # panic mouth, thin lining
O["R3b"] = face_swap("3-2", "3-3", R_R, "3-2R")          # panic mouth, thick lining
O["L3"] = face_swap("3-2", "3-4", R_L, "3-2L")
O["L3s"] = face_swap("3-5", "3-4", R_L, "3-5L")          # left talking over the shedding image
O["R3w"] = face_swap("3-5", "3-6", R_RWAIL, "3-5W")
O["pat"] = face_swap("4-1", "4-2", R_PAT, "4-1P")
O["doc1"] = face_swap("4-3", "4-4", R_DOC, "4-3D")
O["doc2"] = face_swap("4-5", "4-6", R_DOC, "4-5D")

# sperm sprite (for the swim-in) and a plate without the sperm
def sperm_sprite():
    A = np.asarray(img("1-1"), np.float32); B = np.asarray(img("2-1"), np.float32)
    x0, y0, x1, y1 = R_SPERM
    m = (np.abs(A - B).mean(2) > 22)
    m[:y0] = False; m[y1:] = False; m[:, :x0] = False; m[:, x1:] = False
    m = ndimage.binary_closing(m, iterations=3); m = ndimage.binary_fill_holes(m)
    m = ndimage.binary_dilation(m, iterations=2)
    ys, xs = np.nonzero(m); bx = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    alpha = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    spr = img("1-1").copy().convert("RGBA"); spr.putalpha(alpha)
    plate = Image.composite(img("2-1"), img("1-1"), alpha)   # canal without sperm, faces of 1-1
    return spr.crop(bx), bx, plate
SPR, SPR_BOX, PLATE = sperm_sprite()
IMS["plate"] = PLATE


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


def pill(text, size=62):
    t = text_layer(text, size, fill=(45, 20, 30), stroke=0, pad=28)
    w, h = t.size
    lay = Image.new("RGBA", (w + 60, h + 10), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle((0, 0, w + 59, h + 9), radius=(h + 10) // 2, fill=(255, 240, 236, 248),
                                          outline=(45, 20, 30, 255), width=6)
    lay.alpha_composite(t, (30, 5)); return lay


def badge(text):
    t = text_layer(text, 46, fill="white", stroke=0, pad=18)
    w, h = t.size; pw = 26
    lay = Image.new("RGBA", (w + 30, h + 34), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((3, 3, w + 26, h + 3), radius=26, fill=(40, 120, 220, 255), outline=(15, 40, 90, 255), width=5)
    cx = (w + 30) // 2
    d.polygon([(cx - pw // 2, h), (cx + pw // 2, h), (cx, h + 28)], fill=(40, 120, 220, 255), outline=(15, 40, 90, 255))
    d.rectangle((cx - pw // 2 + 4, h - 4, cx + pw // 2 - 4, h + 3), fill=(40, 120, 220, 255))
    lay.alpha_composite(t, (15, -6)); return lay


def stamp(text):
    t = text_layer(text, 100, fill=(225, 30, 40), stroke=0, pad=30)
    w, h = t.size
    lay = Image.new("RGBA", (w + 40, h + 20), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle((6, 6, w + 33, h + 13), radius=24, outline=(225, 30, 40, 255), width=12)
    lay.alpha_composite(t, (20, 10))
    return lay.rotate(-12, expand=True, resample=Image.BICUBIC)


HANDLE = text_layer("@nemonet.ir", 34, fill=(255, 255, 255, 170), stroke=3, stroke_fill=(0, 0, 0, 110), pad=10, rtl=False)
BADGE1, BADGE2 = badge("رحم ۱"), badge("رحم ۲")
STAMP = stamp("پریود!")


# ---------------------------------------------------------------- timeline
class Seg:
    def __init__(self, **k): self.__dict__.update(k)

segs, clips, sfx, titles, badges, stamps, events = [], [], [], [], [], [], {}
t = 0.0

def line(v, text, closed, opened, lead=0.1, tail=0.25, maxgap=0.26, **kw):
    """one voice clip on one pose; pauses between words longer than maxgap are shortened to maxgap.
    morph=(time, dur, closedB, openB) blends to a second pose."""
    global t
    path = REEL + v + ".mp3"
    a = pcm(path)
    ss, se = voiced_span(a)
    jp = HERE + "words/" + v + ".json"
    tw = [x for x in json.load(open(jp))] if os.path.exists(jp) else []
    pieces, cur = [], ss
    for w0, w1 in zip(tw, tw[1:]):
        g0, g1 = w0["end"], w1["start"]
        if g1 - g0 > maxgap:
            pieces.append((cur, g0 + maxgap / 2)); cur = g1 - maxgap / 2
    pieces.append((cur, se))
    def m(x):                                 # source time -> time inside the trimmed clip
        o = 0.0
        for p0, p1 in pieces:
            if x <= p1: return o + max(x - p0, 0)
            o += p1 - p0
        return o
    fade = int(0.012 * SR); parts = []
    for p0, p1 in pieces:
        c = a[int(p0 * SR):int(p1 * SR)].copy()
        if len(c) > 2 * fade: c[:fade] *= np.linspace(0, 1, fade); c[-fade:] *= np.linspace(1, 0, fade)
        parts.append(c)
    clip = np.concatenate(parts); wav = os.path.join(TMP, v + ".wav"); write_wav(wav, clip)
    dur = len(clip) / SR
    start = t; vstart = start + lead
    clips.append((vstart, wav, 0.0, None, 1.0))
    rms = rms_frames(clip)
    words = text.split()
    raw = word_times(v, words, rms, 0.0)
    mp = m if tw else (lambda x: x)            # without a transcript, raw times are already clip times
    wt = [(vstart + mp(x0), vstart + mp(x1), w) for (x0, x1), w in zip(raw, words)]
    s = Seg(start=start, vstart=vstart, end=vstart + dur + tail, rms=rms, wt=wt,
            closed=closed, open=opened, **kw)
    segs.append(s); t = s.end
    return s

def wstart(s, i): return s.wt[i][0]
def fx(at, name, gain=0.5, ss=0.0, dur=None):
    sfx.append((max(at, 0.0), REEL + name + ".mp3", ss, dur, gain))
def still(dur, closed, **kw):
    global t
    s = Seg(start=t, vstart=t, end=t + dur, rms=np.zeros(1), wt=[], closed=closed, open=closed, **kw)
    segs.append(s); t = s.end; return s

CAP_U = 1560          # captions in the empty lower background of the uterus scenes
FOC_U = (0.5, 0.36)
CAP_DOC = 1690
FOC_DOC = (0.5, 0.42)

# Scene 1: the traveller --------------------------------------------------
s = still(1.55, "plate", punch=False, swim=(0.15, 1.35), cap_y=CAP_U, focus=FOC_U)
titles.append((0.25, 1.9, "باردار، ولی پریود؟!", 0))
fx(0.15, "s1", 0.5)
s = line("v1", "سلام! ببخشید… کدوم اتاق خالیه؟", "1-1", O["sperm"], lead=0.05, tail=0.15,
         cap_y=CAP_U, focus=FOC_U)
s = line("v2", "بیا تو عزیزم، اتاقت آماده‌ست!", "1-1", O["L1"], lead=0.2, tail=0.15,
         punch=True, cap_y=CAP_U, focus=FOC_U)
badges.append((s.start, 1)); fx(s.start, "s2", 0.55)
s = line("v3", "منو حساب نکن. من بچه‌داری نمی‌کنم.", "1-1", O["R1"], lead=0.2, tail=0.3,
         punch=True, cap_y=CAP_U, focus=FOC_U)
badges.append((s.start, 2)); fx(s.start, "s2", 0.55)

# Scene 2: dream vacation -------------------------------------------------
s = line("v4", "آخ‌جون! بارداری یعنی نُه ماه پریود تعطیل. منم رفتم مرخصی!", "2-1", O["R2"], lead=0.6, tail=0.25,
         punch=True, sparkle=True, cap_y=CAP_U, focus=FOC_U)
fx(s.start, "s3", 0.55)

# Scene 3: hormones arrive ------------------------------------------------
HORM0 = t
fx(t, "s4", 0.5)
s = line("v5", "اِ؟ چرا دیواره‌م داره کلفت می‌شه؟ من که مهمون ندارم!", "3-1", O["R3a"], lead=0.7, tail=0.2,
         punch=True, shake=True, cap_y=CAP_U, focus=FOC_U)
s.morph = (wstart(s, 4) - 0.1, 0.9, "3-2", O["R3b"])
fx(wstart(s, 4) - 0.15, "s5", 0.55)
s = line("v6", "هورمون‌ها به هر دوتامون می‌رسن خواهر. مهمون نداری، پس باید بریزیش.", "3-2", O["L3"], lead=0.15, tail=0.25,
         punch=True, cap_y=CAP_U, focus=FOC_U)
SHED = wstart(s, len(s.wt) - 1)
s.morph = (SHED, 0.45, "3-5", O["L3s"])
stamps.append(SHED + 0.35); fx(SHED + 0.35, "s6", 0.7)
HORM1 = SHED + 0.6
s = line("v7", "یعنی تو مرخصی هم باید کار کنم؟!", "3-5", O["R3w"], lead=0.35, tail=0.2,
         punch=True, shake=True, cap_y=CAP_U, focus=FOC_U)
fx(s.end - 0.6, "s7", 0.45)
still(1.0, "3-5", cap_y=CAP_U, focus=FOC_U)

# Scene 4: clinic ---------------------------------------------------------
fx(t - 0.3, "s9", 0.45)
s = line("v8", "دکتر، من باردارم… ولی پریود شدم!", "4-1", O["pat"], lead=0.45, tail=0.2,
         punch=True, cap_y=CAP_DOC, focus=FOC_DOC)
titles.append((s.start + 0.05, 1.5, "مطب دکتر", 1))
s = line("v9", "شما رحمِ دوقلو دارید؛ دو تا حفره‌ی جدا. یکی جنین داره، اون یکی هنوز به هورمون‌ها جواب می‌ده.",
         "4-3", O["doc1"], lead=0.15, tail=0.25, punch=True, poster=True, cap_y=CAP_DOC, focus=FOC_DOC)
s = line("v10", "این حالت نادره. هر خونریزی تو بارداری رو حتماً به پزشکت بگو.", "4-5", O["doc2"], lead=0.15, tail=1.4,
         punch=True, push=0.014, cap_y=CAP_DOC, focus=(0.3, 0.38))
TOTAL = t
NF = int(round(TOTAL * FPS))


# ---------------------------------------------------------------- mouth per segment
for s in segs:
    m = np.zeros(len(s.rms), int)
    inword = np.zeros(len(s.rms), bool)
    for a, b, _ in s.wt:
        inword[max(int((a - s.vstart) * FPS), 0):int((b - s.vstart) * FPS) + 1] = True
    run = 0
    for i, v in enumerate(s.rms):
        o = v > 0.16 and inword[i]
        if o:
            run += 1
            if run % 5 == 0: o = False
        else: run = 0
        m[i] = o
    for i in range(1, len(m) - 1):
        if m[i - 1] == m[i + 1] != m[i]: m[i] = m[i - 1]
    s.mouth = m


# ---------------------------------------------------------------- render helpers
def ease_out(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def smooth(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def pop_scale(dt, dur=0.18):
    if dt < 0: return 0
    return ease_out(min(1, dt / dur)) + 0.18 * math.sin(min(1, dt / 0.32) * math.pi)
def scaled(lay, sc):
    return lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.LANCZOS)
def with_alpha(lay, a):
    if a >= 1: return lay
    lay = lay.copy(); lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a))); return lay


def camera(src, zoom, fx_, fy_, ox=0.0, oy=0.0):
    sw, sh = src.size
    cw, ch = sw / zoom, sh / zoom
    x0 = min(max(fx_ * sw - cw * fx_ - ox * sw, 0), sw - cw)
    y0 = min(max(fy_ * sh - ch * fy_ - oy * sh, 0), sh - ch)
    out = src.resize((W, H), Image.BILINEAR if PREVIEW else Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
    k = W / cw
    return out, (lambda x, y: ((x - x0) * k, (y - y0) * k)), k


# hormone bubbles: fixed random field drifting upward
rng = random.Random(7)
BUBS = [(rng.uniform(0, 768), rng.uniform(0, 1365), rng.uniform(5, 15), rng.uniform(25, 60), rng.uniform(0, 6.28),
         rng.uniform(0, 1)) for _ in range(70)]

def draw_bubbles(lay, tt, M, k):
    amt = smooth((tt - HORM0) / 1.2) * (1 - smooth((tt - HORM1) / 0.8))
    if amt <= 0: return
    d = ImageDraw.Draw(lay)
    lt = tt - HORM0
    for x, y, r, sp, ph, order in BUBS:
        if order > amt: continue
        yy = (y - sp * lt) % 1365
        xx = x + 10 * math.sin(lt * 1.7 + ph)
        X, Y = M(xx, yy); R = r * k * (0.85 + 0.15 * math.sin(lt * 3 + ph))
        d.ellipse((X - R, Y - R, X + R, Y + R), fill=(255, 236, 120, 215), outline=(200, 160, 40, 230), width=3)
        d.ellipse((X - R * 0.45, Y - R * 0.55, X - R * 0.05, Y - R * 0.2), fill=(255, 255, 230, 220))


def draw_sparkles(lay, dt, M, k):
    if not (0 <= dt < 1.6): return
    d = ImageDraw.Draw(lay)
    for i in range(9):
        a = i / 9 * 6.283 + 0.4
        rr = (60 + 40 * ease_out(dt / 0.8)) * (1 + 0.25 * (i % 2))
        X, Y = M(271 + rr * math.cos(a), 490 + rr * math.sin(a))
        s = k * 11 * max(0, math.sin(min(1, (dt - i * 0.05) / 1.1) * math.pi))
        if s <= 0: continue
        d.polygon([(X, Y - 2 * s), (X + s * 0.45, Y - s * 0.45), (X + 2 * s, Y), (X + s * 0.45, Y + s * 0.45),
                   (X, Y + 2 * s), (X - s * 0.45, Y + s * 0.45), (X - 2 * s, Y), (X - s * 0.45, Y - s * 0.45)],
                  fill=(255, 250, 200, 240))


CAP_CACHE, PILLS = {}, {}
def caption_layer(word):
    if word not in CAP_CACHE: CAP_CACHE[word] = text_layer(word.strip("….،؛"), 92, stroke=11)
    return CAP_CACHE[word]

HEADS = {1: (258, 268), 2: (512, 262)}     # top of each uterus head (source coords)


def render(f):
    tt = f / FPS
    s = next((x for x in segs if x.start <= tt < x.end), segs[-1])
    lt = tt - s.start
    vi = int(round((tt - s.vstart) * FPS))
    mouth = s.mouth[vi] if 0 <= vi < len(s.mouth) else 0
    zoom = 1.0; ox = oy = 0.0; fxy = s.focus
    if getattr(s, "punch", False): zoom += 0.06 * math.exp(-lt / 0.13)
    zoom += getattr(s, "push", 0.008) * lt
    if getattr(s, "poster", False):                     # slow push toward the double-uterus poster
        p = smooth((tt - s.vstart - 0.2) / 2.0) * (1 - smooth((tt - (s.end - 2.3)) / 1.2))
        zoom += 0.16 * p; fxy = (0.5 + 0.0 * p, 0.42 - 0.27 * p)
    if getattr(s, "shake", False):
        kk = math.exp(-lt / 0.6)
        ox = 0.006 * math.sin(lt * 55) * kk; oy = 0.004 * math.cos(lt * 47) * kk

    src = img(s.open if mouth else s.closed)
    mo = getattr(s, "morph", None)
    if mo and tt >= mo[0]:
        a = smooth((tt - mo[0]) / mo[1])
        src2 = img(mo[3] if mouth else mo[2])
        src = Image.blend(src, src2, a) if a < 1 else src2
    if getattr(s, "swim", None):                       # sperm swims up into place
        t0, t1 = s.swim
        p = ease_out((tt - t0) / (t1 - t0))
        dy = (1 - p) * 230; dx = 9 * math.sin(tt * 14) * (1 - p)
        src = src.copy()
        if tt >= t0:
            sp = with_alpha(SPR, min(1, (tt - t0) / 0.25))
            src.paste(sp, (int(SPR_BOX[0] + dx), int(SPR_BOX[1] + dy)), sp)

    frame, M, k = camera(src, max(zoom, 1.005), *fxy, ox, oy)
    frame = frame.convert("RGBA")
    over = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw_bubbles(over, tt, M, k)
    if getattr(s, "sparkle", False): draw_sparkles(over, tt - s.start - 0.05, M, k)
    frame.alpha_composite(over)

    if tt < (segs[8].start if len(segs) > 8 else TOTAL):   # name badges in the uterus scenes
        for at, which in badges:
            dt = tt - at
            if dt < 0: continue
            lay = BADGE1 if which == 1 else BADGE2
            lay = scaled(lay, pop_scale(dt) * k / 1.406)
            X, Y = M(*HEADS[which])
            Y += 4 * math.sin(tt * 3.1 + which)
            frame.alpha_composite(lay, (int(X - lay.width / 2), int(Y - lay.height - 6)))

    for at in stamps:
        dt = tt - at
        if 0 <= dt < 2.6 and tt < TOTAL:
            sc = 1.0 + 0.9 * math.exp(-dt / 0.07) if dt > 0 else 1.9
            lay = with_alpha(scaled(STAMP, sc), min(1, dt / 0.06) * (1 - smooth((dt - 2.2) / 0.4)))
            X, Y = M(600, 790)
            frame.alpha_composite(lay, (int(X - lay.width / 2), int(Y - lay.height / 2)))

    for at, dur, text, kind in titles:
        dt = tt - at
        if 0 <= dt < dur:
            if text not in PILLS: PILLS[text] = pill(text, 66 if kind == 0 else 58)
            lay = with_alpha(scaled(PILLS[text], pop_scale(dt)), 1 - smooth((dt - (dur - 0.3)) / 0.3))
            y = 250 if kind == 0 else 225
            frame.alpha_composite(lay, (W // 2 - lay.width // 2, y - lay.height // 2))

    frame.alpha_composite(HANDLE, (36, 120))

    cur = [(a, b, w) for a, b, w in s.wt if a <= tt]
    if cur:
        a, b, w = cur[-1]
        nxt = [x for x, _, _ in s.wt if x > a]
        end = min(nxt[0], b + 0.45) if nxt else min(s.end, b + 0.45)
        if tt < end:
            sc = 0.62 + 0.38 * ease_out((tt - a) / 0.12) + 0.07 * math.sin(min(1, (tt - a) / 0.2) * math.pi)
            lay = scaled(caption_layer(w), sc)
            frame.alpha_composite(lay, (W // 2 - lay.width // 2, s.cap_y - lay.height // 2))
    out = frame.convert("RGB")
    if tt < 0.25:
        out = Image.blend(Image.new("RGB", out.size, (0, 0, 0)), out, tt / 0.25)
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
        filters.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,{tr},asetpts=PTS-STARTPTS{n},"
                       f"volume={gain},adelay={int(at*1000)}|{int(at*1000)}[a{i}]")
        labels.append(f"[a{i}]")
    for at, p, ss, dur, g in clips: add(p, at, ss, dur, g, norm=-16)
    for at, p, ss, dur, g in sfx: add(p, at, ss, dur, g)
    im = len(inputs) // 2; inputs += ["-i", REEL + "s8.mp3"]
    filters.append(f"[{im}:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-24:TP=-3,aresample=48000,"
                   f"atrim=0:{TOTAL:.3f},volume=0.2,afade=t=in:d=0.6,afade=t=out:st={TOTAL-1.4:.3f}:d=1.4[mus]")
    labels.append("[mus]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,atrim=0:{TOTAL:.3f},"
                   "alimiter=limit=0.95[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters),
                    "-map", "[out]", "-c:a", "pcm_s16le", path], check=True)


if __name__ == "__main__":
    print("total %.2fs, %d frames" % (TOTAL, NF))
    for s in segs: print(f"{s.start:6.2f}-{s.end:6.2f} {s.closed:6s} {' '.join(w for _, _, w in s.wt)[:50]}")
    if "--sheet" in sys.argv:
        times = [0.9] + [x.vstart + 0.5 for x in segs[1:]] + [SHED + 0.6]
        tiles = [render(int(tm * FPS)).resize((270, 480)) for tm in times]
        cols = 7; rows = math.ceil(len(tiles) / cols)
        sh = Image.new("RGB", (270 * cols, 480 * rows), "white")
        for i, tl in enumerate(tiles): sh.paste(tl, ((i % cols) * 270, (i // cols) * 480))
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
