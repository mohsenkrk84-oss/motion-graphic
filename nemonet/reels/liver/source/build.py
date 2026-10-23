"""Nemonet fatty-liver reel – full build (scenes 1-4).
python3 -I build.py out.mp4 [--preview start end]
"""
import sys, os, math, subprocess, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../../..") + "/"
IMG = REPO + "reels/liver/"
AUD = IMG + "audio/"
ATT = os.path.dirname(os.path.abspath(__file__)) + "/test/"
FONT = REPO + "IRANYekanWebBlack.woff2"
W, H, FPS = 1080, 1920, 30
OUT = sys.argv[1] if len(sys.argv) > 1 else "liver_full.mp4"
PREVIEW = None
if "--preview" in sys.argv:
    i = sys.argv.index("--preview"); PREVIEW = (float(sys.argv[i + 1]), float(sys.argv[i + 2]))
WORK = os.path.dirname(os.path.abspath(__file__)) + "/"


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


# ---------------------------------------------------------------- images
def load_src(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    th = round(w * 16 / 9)
    top = (h - th) // 2
    return im.crop((0, top, w, top + th)), top


IMS = {}
def img(key):
    if key not in IMS:
        if key.startswith("A:"):
            IMS[key] = load_src(ATT + key[2:] + "-image.jpg")[0]
        else:
            IMS[key] = load_src(IMG + key + ".jpg")[0]
    return IMS[key]


CROP_TOP_NEW = (2752 - round(1536 * 16 / 9)) // 2  # 10 px for 1536x2752 sources

def feather_paste(dst, src, box, blur=14):
    m = Image.new("L", dst.size, 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=30, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    return Image.composite(src, dst, m)


def diff_box(a, b, region, thr=40, pad=18):
    A = np.asarray(a.convert("L")).astype(int); B = np.asarray(b.convert("L")).astype(int)
    x0, y0, x1, y1 = region
    d = np.abs(A[y0:y1, x0:x1] - B[y0:y1, x0:x1]) > thr
    d = np.asarray(Image.fromarray((d * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5))) > 0
    ys, xs = np.nonzero(d)
    if len(xs) == 0: return None
    return (x0 + xs.min() - pad, y0 + ys.min() - pad, x0 + xs.max() + pad, y0 + ys.max() + pad)


def build_composites():
    # scene 4: doctor-closed + man-worried  (4-3 with doctor mouth from 4-4)
    a, b = img("4-3"), img("4-4")
    box = diff_box(a, b, (1060, 820, 1400, 1080))
    IMS["4-W"] = feather_paste(a, b, box, 10) if box else b
    # 4-5 with doctor mouth closed (mouth from 4-1)
    a, b = img("4-5"), img("4-1")
    box = diff_box(a, b, (1100, 880, 1360, 1060))
    IMS["4-5c"] = feather_paste(a, b, box, 10) if box else a
    return
build_composites()

# door signs (on 1536-wide source coords minus crop top)
SIGN1 = [(204, 717), (633, 810), (633, 952), (206, 878)]
SIGN2 = [(1130, 918), (1442, 974), (1442, 1079), (1143, 1031)]
def quad_to_crop(q): return [(x, y - CROP_TOP_NEW) for x, y in q]
SIGN1, SIGN2 = quad_to_crop(SIGN1), quad_to_crop(SIGN2)

def text_layer(text, size, fill="white", stroke=10, stroke_fill="black", pad=40, rtl=True):
    f = ImageFont.truetype(FONT, size)
    tmp = Image.new("RGBA", (10, 10)); d = ImageDraw.Draw(tmp)
    kw = dict(direction="rtl", language="fa") if rtl else {}
    bb = d.textbbox((0, 0), text, font=f, stroke_width=stroke, anchor="lt", **kw)
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((pad - bb[0], pad - bb[1]), text, font=f, fill=fill, stroke_width=stroke,
                             stroke_fill=stroke_fill, anchor="lt", **kw)
    return lay


def warp_into_quad(base, layer, quad):
    """paste RGBA layer into quad (TL,TR,BR,BL) on base."""
    w, h = layer.size
    # solve perspective coeffs mapping output quad -> layer rect
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    A = []; B = []
    for (x, y), (u, v) in zip(quad, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    coeffs = np.linalg.solve(np.array(A, float), np.array(B, float))
    warped = layer.transform(base.size, Image.PERSPECTIVE, tuple(coeffs), Image.BICUBIC)
    out = base.convert("RGBA"); out.alpha_composite(warped); return out.convert("RGB")


def sign_label(text, color=(70, 40, 25), size=110, w=900, h=300):
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    f = ImageFont.truetype(FONT, size)
    ImageDraw.Draw(lay).text((w // 2, h // 2), text, font=f, fill=color, anchor="mm", direction="rtl", language="fa")
    return lay


def stamp_label(name, w=900, h=300):
    """sign after it's full: name small on top, red 'پُره!' stamp below."""
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.text((w // 2, 62), name, font=ImageFont.truetype(FONT, 70), fill=(70, 40, 25), anchor="mm", direction="rtl", language="fa")
    st = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ds = ImageDraw.Draw(st)
    ds.rounded_rectangle((250, 115, 650, 285), radius=30, outline=(220, 30, 40, 255), width=16)
    ds.text((w // 2, 200), "پُره!", font=ImageFont.truetype(FONT, 125), fill=(220, 30, 40, 255), anchor="mm", direction="rtl", language="fa")
    lay.alpha_composite(st.rotate(-6, resample=Image.BICUBIC, center=(w // 2, 200)))
    return lay


def build_signs():
    for k in ["2-1", "2-2", "2-3", "2-4", "2-5"]:
        base = img(k)
        s = warp_into_quad(base, sign_label("انبار چربی ۱"), SIGN1)
        s = warp_into_quad(s, sign_label("انبار چربی ۲"), SIGN2)
        IMS[k + "s"] = s
        full = warp_into_quad(base, stamp_label("انبار چربی ۱"), SIGN1)
        full = warp_into_quad(full, stamp_label("انبار چربی ۲"), SIGN2)
        IMS[k + "f"] = full
build_signs()

# insulin label anchor points (source px, crop-adjusted): top of cap
LABEL_POS = {
    "2-1": {"gold": (965, 1585)}, "2-2": {"gold": (965, 1585)},
    "2-3": {"gold": (890, 1585), "silver": (1140, 1335)}, "2-4": {"gold": (890, 1585), "silver": (1140, 1335)},
    "2-5": {"gold": (850, 1585), "silver": (1150, 1335)},
}


# ---------------------------------------------------------------- timeline
class Seg:
    def __init__(self, **k): self.__dict__.update(k)

segs, clips, sfx = [], [], []   # clips: (t, path, ss, dur, gain) ; caption words in seg.words
t = 0.0

def speech(path, ss=0.0, dur=None):
    d = dur if dur else adur(path) - ss
    return path, ss, d

def add_seg(kind, path, ss, dur, words, lead=0.0, tail=0.15, **kw):
    global t
    start = t
    vstart = start + lead
    clips.append((vstart, path, ss, dur, 1.0))
    a = pcm(path, ss, dur)
    s = Seg(kind=kind, start=start, vstart=vstart, end=vstart + dur + tail, rms=rms_frames(a),
            words=words, **kw)
    segs.append(s); t = s.end
    return s

def add_sfx(at, name, gain=0.6, ss=0.0, dur=None):
    sfx.append((at, AUD + name, ss, dur, gain))

VO_TEST = AUD + "v0.mp3"

# Scene 1 ---------------------------------------------------------------
s = add_seg("curl", VO_TEST, 0.0, 3.80, "باید بزنم... چربیامو آب کنم داداش!", lead=0.05, tail=0.1)
add_sfx(0.42, "s1.mp3", 0.35, 0, 0.9); add_sfx(2.7, "s1.mp3", 0.3, 0, 0.9)
s = add_seg("lip", AUD + "v1.mp3", 0.0, 2.68, "ولی خبر نداره قند و نوشابه...", lead=0.05, tail=0.0,
            closed="1-4", open="1-5", punch=True, cap_y=1330)
add_sfx(s.start, "s5.mp3", 0.45)
s = add_seg("still", AUD + "v1.mp3", 2.68, adur(AUD + "v1.mp3") - 2.68 - 0.05, "همین الان داره می‌رسه!", lead=0.0, tail=0.35,
            image="1-1", punch=True, shake=True, cap_y=1330)
add_sfx(s.start - 0.05, "s2.mp3", 0.55, 0, 4.2)
s = add_seg("lip", AUD + "v2.mp3", 0.0, 3.84, "باز؟! من هنوز دیروزی‌ها رو تموم نکردم!", lead=0.1, tail=0.35,
            closed="1-2", open="1-3", punch=True, cap_y=1330)

# Scene 2 ---------------------------------------------------------------
add_sfx(t - 0.1, "s5.mp3", 0.5)
s2_start = t
s = add_seg("lip", AUD + "v3.mp3", 0.0, 5.31, "بار جدید! قند اضافه، تبدیل شده به چربی. کجا خالی کنم؟", lead=1.35, tail=0.2,
            closed="2-1s", open="2-2s", punch=True, cap_y=430, labels=["gold"], title=True)
add_sfx(s.start + 0.25, "s7.mp3", 0.5)      # label pop
add_sfx(s.start + 0.45, "s3.mp3", 0.7, 0, 1.0)  # knock
s = add_seg("lip", AUD + "v4.mp3", 0.0, adur(AUD + "v4.mp3"), "همه‌ی انبارا پُره داداش.", lead=0.55, tail=0.2,
            closed="2-3s", open="2-4s", full_at=0.25, punch=True, cap_y=430, labels=["gold", "silver"], silver_pop=0.05)
add_sfx(s.start + 0.05, "s7.mp3", 0.5)
add_sfx(s.start + 0.28, "s3.mp3", 0.5, 0, 0.22)  # stamp thud
s = add_seg("still", AUD + "v5.mp3", 0.0, 0.84, "خب...", lead=0.0, tail=0.0,
            image="2-3f", cap_y=430, labels=["gold", "silver"])
s = add_seg("still", AUD + "v5.mp3", 0.84, 4.99 - 0.84, "همین‌جا تو خود کبد خالی کن دیگه!", lead=0.0, tail=0.6,
            image="2-5f", punch=True, talk_bounce=True, cap_y=430, labels=["gold", "silver"])
add_sfx(s.start + 1.3, "s4.mp3", 0.6, 0.6, 3.9)

# Scene 3 ---------------------------------------------------------------
add_sfx(t - 0.1, "s5.mp3", 0.5)
s = add_seg("fade", AUD + "v6.mp3", 0.0, 10.40, "وقتی انبارهای چربی بدن پر می‌شه، چربی اضافه می‌ره جاهایی که نباید بِره: توی کبد، دور اندام‌ها، حتی لای عضله‌ها.",
            lead=0.25, tail=0.5, a="3-1", b="3-2", fade_at=(5.2, 7.2), cap_y=1720)
add_sfx(s.vstart + 6.0, "s4.mp3", 0.25, 0.6, 2.5)

# Scene 4 ---------------------------------------------------------------
add_sfx(t - 0.1, "s5.mp3", 0.5)
s = add_seg("lip", AUD + "v7.mp3", 0.0, 2.61, "دکتر، من که چاق نیستم!", lead=0.8, tail=0.25,
            closed="4-1", open="4-2", punch=True, cap_y=1700)
add_sfx(s.start + 0.1, "s6.mp3", 0.5)
s = add_seg("lip", AUD + "v8.mp3", 0.0, 5.28, "از بیرون نه، ولی کبدت چرب شده. به این می‌گن چاقی از درون.", lead=0.05, tail=0.25,
            closed="4-W", open="4-3", cap_y=1700)
s = add_seg("lip", AUD + "v9.mp3", 0.15, 1.52, "حالا چی‌کار کنم؟", lead=0.05, tail=0.25,
            closed="4-W", open="4-4", cap_y=1700)
s = add_seg("lip", AUD + "v10.mp3", 0.0, 11.93, "قند و نوشابه رو کم کن، هر روز تحرک داشته باش. با کم کردن پنج تا ده درصد وزن، چربی کبد هم کم می‌شه. ولی اول یه آزمایش بده ببینیم اوضاع چطوره.",
            lead=0.05, tail=1.0, closed="4-5c", open="4-5", cap_y=1700)
TOTAL = t
NF = int(round(TOTAL * FPS))

# ---------------------------------------------------------------- per-seg derived data
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
    wts = np.array([len(w.strip(".،!؟:")) + 1.6 for w in words], float)
    cum = np.concatenate([[0], np.cumsum(wts) / wts.sum()])
    s.wt = [(s.vstart + frames[min(int(cum[i] * len(frames)), len(frames) - 1)] / FPS, w) for i, w in enumerate(words)]
    # mouth: 0/1 with chatter
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

ALLWORDS = [w for s in segs for w in s.wt]

# ---------------------------------------------------------------- render helpers
def camera(src, zoom=1.0, fx=0.5, fy=0.5, ox=0.0, oy=0.0):
    sw, sh = src.size
    cw, ch = sw / zoom, sh / zoom
    x0 = min(max(fx * sw - cw * fx - ox * sw, 0), sw - cw)
    y0 = min(max(fy * sh - ch * fy - oy * sh, 0), sh - ch)
    box = (x0, y0, x0 + cw, y0 + ch)
    return src.resize((W, H), Image.BILINEAR if PREVIEW else Image.LANCZOS, box=box), box


def to_out(pt, box, src):
    return ((pt[0] - box[0]) * W / (box[2] - box[0]), (pt[1] - box[1]) * H / (box[3] - box[1]))


CAP_CACHE = {}
def caption_layer(word):
    if word not in CAP_CACHE:
        CAP_CACHE[word] = text_layer(word, 92, stroke=11)
    return CAP_CACHE[word]

LABEL = text_layer("انسولین", 44, fill="white", stroke=0)
def insulin_badge():
    lw, lh = LABEL.size
    bw, bh = lw - 30, lh - 34
    lay = Image.new("RGBA", (bw + 20, bh + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((4, 4, bw + 14, bh + 4), radius=bh // 2, fill=(30, 110, 200, 255), outline=(15, 25, 45, 255), width=5)
    cx = (bw + 18) // 2
    d.polygon([(cx - 14, bh + 2), (cx + 14, bh + 2), (cx, bh + 26)], fill=(30, 110, 200, 255), outline=(15, 25, 45, 255))
    d.rectangle((cx - 11, bh - 2, cx + 11, bh + 3), fill=(30, 110, 200, 255))
    lay.alpha_composite(LABEL, (cx - lw // 2, (bh + 8) // 2 - lh // 2 + 2))
    return lay
BADGE = insulin_badge()

TITLE = None
def title_layer():
    t = text_layer("داخل کبد", 64, fill=(40, 20, 10), stroke=0, pad=30)
    w, h = t.size
    lay = Image.new("RGBA", (w + 60, h + 10), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle((0, 0, w + 59, h + 9), radius=(h + 10) // 2, fill=(255, 244, 225, 245),
                                          outline=(40, 20, 10, 255), width=6)
    lay.alpha_composite(t, (30, 5)); return lay
TITLE = title_layer()

HANDLE = text_layer("@nemonet.ir", 34, fill=(255, 255, 255, 150), stroke=3, stroke_fill=(0, 0, 0, 90), pad=10, rtl=False)

def ease_out(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def pop_scale(dt, dur=0.18):
    if dt < 0: return 0
    k = min(1, dt / dur)
    return ease_out(k) + 0.18 * math.sin(min(1, dt / 0.32) * math.pi)


def render(f):
    tt = f / FPS
    s = next((x for x in segs if x.start <= tt < x.end), segs[-1])
    lt = tt - s.start
    vi = int(round((tt - s.vstart) * FPS))
    mouth = s.mouth[vi] if 0 <= vi < len(s.mouth) else 0
    zoom, fx, fy, ox, oy = 1.0, 0.5, 0.4, 0.0, 0.0
    if getattr(s, "punch", False):
        zoom += 0.06 * math.exp(-lt / 0.13)
    zoom += 0.010 * lt                      # slow push within the segment
    if getattr(s, "shake", False):
        ox = 0.006 * math.sin(lt * 55) * math.exp(-lt / 0.9)
        oy = 0.004 * math.cos(lt * 47) * math.exp(-lt / 0.9)
    labels_pos_key = None
    if s.kind == "curl":
        up = int(lt / 0.38) % 2 == 1
        key = "A:" + {(False, 0): "230980bc", (False, 1): "96650715", (True, 0): "9c5d11f8", (True, 1): "02fda969"}[(up, int(mouth > 0))]
        src = img(key); zoom = 1.012 + (0.012 if up else 0); fx, fy = 0.45, 0.33; oy = -0.002 if up else 0
    elif s.kind == "lip":
        key = s.open if mouth else s.closed
        if getattr(s, "full_at", None) is not None and lt >= s.full_at:
            key = key[:-1] + "f"
        src = img(key); labels_pos_key = key[:3]
        if key.startswith("1-"): fx, fy = 0.45, 0.33
    elif s.kind == "still":
        src = img(s.image); labels_pos_key = s.image[:3]
        if s.image.startswith("1-"): fx, fy = 0.45, 0.33
        if getattr(s, "talk_bounce", False) and mouth:
            zoom += 0.004
    elif s.kind == "fade":
        a0, a1 = s.fade_at
        k = min(max((tt - s.vstart - a0) / (a1 - a0), 0), 1)
        k = k * k * (3 - 2 * k)
        src = Image.blend(img(s.a), img(s.b), k) if 0 < k < 1 else img(s.b if k >= 1 else s.a)
        fx, fy = 0.5, 0.5
    zoom = max(zoom, 1.01)
    frame, box = camera(src, zoom, fx, fy, ox, oy)
    frame = frame.convert("RGBA")

    # scene-2 overlays
    if getattr(s, "labels", None) and labels_pos_key in LABEL_POS:
        for who in s.labels:
            if who not in LABEL_POS[labels_pos_key]: continue
            px, py = to_out(LABEL_POS[labels_pos_key][who], box, src)
            appear = s2_start + 0.25 if who == "gold" else segs[segs.index(s)].start
            if who == "silver":
                first_silver = next(x for x in segs if "silver" in (getattr(x, "labels", None) or []))
                appear = first_silver.start + 0.05
            sc = pop_scale(tt - appear) if tt - appear < 0.5 else 1.0
            if sc <= 0: continue
            bob = 5 * math.sin(tt * 3.2 + (0 if who == "gold" else 1.7))
            b = BADGE.resize((max(1, int(BADGE.width * sc)), max(1, int(BADGE.height * sc))), Image.LANCZOS)
            frame.alpha_composite(b, (int(px - b.width / 2), int(py - b.height - 6 + bob)))
    if getattr(s, "title", False) or (s2_start <= tt < s2_start + 1.6):
        dt = tt - s2_start
        if 0 <= dt < 1.6:
            a = 1.0 if dt < 1.3 else max(0, 1 - (dt - 1.3) / 0.3)
            sc = pop_scale(dt)
            lay = TITLE.resize((max(1, int(TITLE.width * sc)), max(1, int(TITLE.height * sc))), Image.LANCZOS)
            if a < 1:
                al = lay.getchannel("A").point(lambda v: int(v * a)); lay.putalpha(al)
            frame.alpha_composite(lay, (W // 2 - lay.width // 2, 230 - lay.height // 2))

    # handle
    frame.alpha_composite(HANDLE, (36, 150))

    # captions
    cur = [(st, w) for st, w in s.wt if st <= tt]
    if cur:
        st, w = cur[-1]
        nxt = [x for x, _ in s.wt if x > st]
        end = nxt[0] if nxt else s.end
        if tt < end + 0.25:
            lay = caption_layer(w)
            sc = 0.62 + 0.38 * ease_out((tt - st) / 0.12) + 0.07 * math.sin(min(1, (tt - st) / 0.2) * math.pi)
            if sc != 1:
                lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.LANCZOS)
            cy = s.cap_y if hasattr(s, "cap_y") else 1330
            frame.alpha_composite(lay, (W // 2 - lay.width // 2, cy - lay.height // 2))
    # fade in/out
    out = frame.convert("RGB")
    if tt > TOTAL - 0.5:
        out = Image.blend(out, Image.new("RGB", out.size, (0, 0, 0)), min(1, (tt - (TOTAL - 0.5)) / 0.5))
    return out


# ---------------------------------------------------------------- audio mix
def build_audio(path):
    inputs, filters, labels = [], [], []
    def add(p, at, ss, dur, gain, norm=None):
        i = len(inputs) // 2; inputs.extend(["-i", p])
        tr = f"atrim={ss}" + (f":duration={dur}" if dur else "")
        n = f",loudnorm=I={norm}:TP=-2,aresample=48000" if norm else ""
        filters.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,{tr},asetpts=PTS-STARTPTS{n},volume={gain},adelay={int(at*1000)}|{int(at*1000)}[a{i}]")
        labels.append(f"[a{i}]")
    for at, p, ss, dur, g in clips: add(p, at, ss, dur, g, norm=-16)
    for at, p, ss, dur, g in sfx: add(p, max(at, 0), ss, dur, g)
    # music: s8-1 + s8-2 loudness matched, crossfaded, looped to length
    i1 = len(inputs) // 2; inputs += ["-i", AUD + "s8-1.mp3"]; i2 = len(inputs) // 2; inputs += ["-i", AUD + "s8-2.mp3"]
    filters.append(f"[{i1}:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-24:TP=-3,aresample=48000[m1]")
    filters.append(f"[{i2}:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-24:TP=-3,aresample=48000[m2]")
    filters.append(f"[m1][m2]acrossfade=d=1.5[m12]")
    filters.append(f"[m12]aloop=loop=2:size=2880000,atrim=0:{TOTAL:.3f},volume=0.2,afade=t=in:d=0.6,afade=t=out:st={TOTAL-1.2:.3f}:d=1.2[mus]")
    labels.append("[mus]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,atrim=0:{TOTAL:.3f},alimiter=limit=0.95[out]")
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]", "-c:a", "pcm_s16le", path]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    print("total %.2fs, %d frames" % (TOTAL, NF))
    for s in segs: print(f"{s.start:6.2f}-{s.end:6.2f} {s.kind:5s} {s.words[:40]}")
    mix = WORK + "mix.wav"
    build_audio(mix)
    f0, f1 = (0, NF) if not PREVIEW else (int(PREVIEW[0] * FPS), int(PREVIEW[1] * FPS))
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-ss", str(f0 / FPS), "-t", str((f1 - f0) / FPS), "-i", mix,
           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(render(f).tobytes())
    p.stdin.close(); p.wait()
    print("done", OUT)
