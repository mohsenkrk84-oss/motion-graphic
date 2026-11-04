"""Nemonet blood-sugar reel (stomach / pancreas / brain / Reza & Mina).
python3 -I build.py out.mp4 [--preview start end] [--src DIR]
"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)) + "/"
SRC = os.path.abspath(HERE + "..") + "/"
if "--src" in sys.argv: SRC = os.path.abspath(sys.argv[sys.argv.index("--src") + 1]) + "/"
IMG = SRC
AUD = SRC + ("audio/" if os.path.isdir(SRC + "audio") else "")
FONT = HERE + "IRANYekanWebBlack.woff2"
if not os.path.exists(FONT): FONT = os.path.abspath(HERE + "../../../IRANYekanWebBlack.woff2")
W, H, FPS = 1080, 1920, 30
OUT = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "out.mp4"
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


# ---------------------------------------------------------------- images
IMS = {}
CROP_TOP = 0
def img(key):
    global CROP_TOP
    if key not in IMS:
        im = Image.open(IMG + key + ".jpg").convert("RGB")
        w, h = im.size
        th = round(w * 16 / 9); CROP_TOP = (h - th) // 2
        IMS[key] = im.crop((0, CROP_TOP, w, CROP_TOP + th))
    return IMS[key]
img("1-1")


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


def badge(text, color=(30, 110, 200), size=40, pointer=True):
    lab = text_layer(text, size, fill="white", stroke=0, pad=0)
    lw, lh = lab.size
    bw, bh = lw + 44, lh + 30
    lay = Image.new("RGBA", (bw + 12, bh + 34), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((4, 4, bw + 4, bh + 4), radius=bh // 2, fill=color + (255,), outline=(15, 25, 45, 255), width=5)
    cx = (bw + 8) // 2
    if pointer:
        d.polygon([(cx - 14, bh + 2), (cx + 14, bh + 2), (cx, bh + 26)], fill=color + (255,), outline=(15, 25, 45, 255))
        d.rectangle((cx - 11, bh - 3, cx + 11, bh + 3), fill=color + (255,))
    lay.alpha_composite(lab, (cx - lw // 2, 4 + bh // 2 - lh // 2))
    return lay


def pill(text, size=60, fill=(255, 244, 225), fg=(40, 20, 10), outline=(40, 20, 10)):
    t = text_layer(text, size, fill=fg, stroke=0, pad=26)
    w, h = t.size
    lay = Image.new("RGBA", (w + 50, h + 6), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle((0, 0, w + 49, h + 5), radius=(h + 6) // 2, fill=fill + (245,),
                                          outline=outline + (255,), width=6)
    lay.alpha_composite(t, (25, 3)); return lay


B_STOMACH = badge("معده", (225, 80, 110))
B_PANC = badge("لوزالمعده", (230, 140, 40))
B_INS = badge("انسولین")
TITLE1 = pill("داخل بدن رضا")
TITLE2 = pill("دو ساعت بعد...")
HIGH = pill("قند بالا!", 50, fill=(230, 40, 45), fg=(255, 255, 255), outline=(60, 10, 10))
LOW = pill("افت قند!", 50, fill=(30, 120, 220), fg=(255, 255, 255), outline=(10, 25, 60))
G_LABEL = text_layer("قند خون", 38, stroke=7)
HANDLE = text_layer("@nemonet.ir", 34, fill=(255, 255, 255, 150), stroke=3, stroke_fill=(0, 0, 0, 90), pad=10, rtl=False)


# ---------------------------------------------------------------- timeline
class Seg:
    def __init__(self, **k): self.__dict__.update(k)

segs, clips, sfx = [], [], []
t = 0.0
MARK = {}

def add_seg(kind, path, ss, dur, words, lead=0.0, tail=0.15, **kw):
    global t
    start = t; vstart = start + lead
    if path:
        clips.append((vstart, path, ss, dur, 1.0))
        r = rms_frames(pcm(path, ss, dur))
    else:
        r = np.zeros(int(dur * FPS) + 1)
    s = Seg(kind=kind, start=start, vstart=vstart, end=vstart + dur + tail, rms=r, words=words, **kw)
    segs.append(s); t = s.end
    return s

def add_sfx(at, name, gain=0.6, ss=0.0, dur=None):
    sfx.append((at, AUD + name, ss, dur, gain))

V = lambda n: AUD + f"v{n}.mp3"
CAP1 = 1560   # over the intestines
CAP3 = 962    # on the split line
CAP4 = 1640   # on the rug

# Scene 1 – stuffed stomach -------------------------------------------------
MARK["s1"] = t
s = add_seg("lip", V(1), 0.0, 2.90, "این بشر روزی چقدر می‌خوره؟!", lead=0.35, tail=0.0,
            closed="1-1", open="1-2", punch=True, cap_y=CAP1, sc=1)
add_sfx(0.05, "s1.mp3", 0.55)
s = add_seg("lip", V(1), 2.90, 1.70, "دارم می‌ترکم...", tail=0.0,
            closed="1-1", open="1-2", shake=True, cap_y=CAP1, sc=1)
add_sfx(s.start + 0.05, "s1.mp3", 0.35, 0.3, 1.4)
s = add_seg("lip", V(1), 4.60, 2.45, "حالا حالاها کار دارم تا هضمش کنم!", tail=0.2,
            closed="1-1", open="1-2", cap_y=CAP1, sc=1)
MARK["v2"] = t
s = add_seg("lip", V(2), 0.0, 1.62, "قند داره موشکی می‌ره بالا!", lead=0.05, tail=0.0,
            closed="1-4", open="1-3", punch=True, shake=True, cap_y=CAP1, sc=1)
add_sfx(s.start - 0.05, "s2.mp3", 0.55)
MARK["run"] = t
s = add_seg("run", V(2), 1.62, adur(V(2)) - 1.62, "انسولین‌ها، بدوید بیرون!", tail=1.1,
            frames=["1-5", "1-6"], punch=True, cap_y=CAP1, sc=1)
add_sfx(s.start + 0.1, "s6.mp3", 0.5)
add_sfx(s.start + 0.2, "s3.mp3", 0.6)
MARK["s1end"] = t

# Scene 2 – two hours later ---------------------------------------------------
MARK["s2"] = t
add_sfx(t + 0.1, "s6.mp3", 0.5)
s = add_seg("lip", V(3), 0.0, adur(V(3)), "هوی! من کارم تموم شد. تو چرا هنوز داری انسولین می‌فرستی؟", lead=1.2, tail=0.25,
            closed="2-1", open="2-2", punch=True, cap_y=CAP1, sc=2)
s = add_seg("lip", V(4), 0.0, 4.20, "خیالت تخت... این آقا یه ساعت دیگه باز یه چیزی می‌لمبونه.", lead=0.05, tail=0.0,
            closed="2-1", open="2-3", cap_y=CAP1, sc=2)
s = add_seg("still", None, 0, 1.25, "", tail=0.0, image="2-4", punch=True, sc=2)
add_sfx(s.start + 0.05, "s5.mp3", 0.6)
MARK["drop"] = t
s = add_seg("lip", V(4), 4.20, adur(V(4)) - 4.20, "از الان آماده باشیم بهتره.", lead=0.05, tail=0.0,
            closed="2-1", open="2-3", cap_y=CAP1, sc=2)
add_sfx(s.start + 0.3, "s4.mp3", 0.6)
s = add_seg("still", None, 0, 1.5, "", tail=0.0, image="2-1", sc=2)
MARK["low"] = s.start + 0.15
add_sfx(s.start + 0.15, "s6.mp3", 0.5)

# Scene 3 – brain & stomach ---------------------------------------------------
add_sfx(t, "s9.mp3", 0.0)  # placeholder (silent)
s = add_seg("lip", V(5), 0.0, adur(V(5)), "معده‌جان... ما همین الان یه دیگ غذا نخوردیم؟", lead=0.3, tail=0.2,
            closed="3-1", open="3-2", punch=True, cap_y=CAP3, sc=3)
s = add_seg("lip", V(6), 0.0, 3.30, "والا خوردیم، کمرم شکست!", lead=0.05, tail=0.2,
            closed="3-1", open="3-3", punch=True, cap_y=CAP3, sc=3)
s = add_seg("lip", V(7), 0.0, 3.92, "پس چرا دست و پام می‌لرزه و هوس شیرینی کردم؟", lead=0.1, tail=0.0,
            closed="3-4", open="3-5", punch=True, tremble=True, cap_y=CAP3, sc=3)
add_sfx(s.start + 0.1, "s8.mp3", 0.45)
add_sfx(s.start + 2.0, "s7.mp3", 0.4)
s = add_seg("lip", V(7), 3.92, adur(V(7)) - 3.92, "قند! قند لازم داریم!", tail=0.3,
            closed="3-4", open="3-5", punch=True, shake=True, cap_y=CAP3, sc=3)

# Scene 4 – home ----------------------------------------------------------------
add_sfx(t - 0.05, "s9.mp3", 0.5)
s = add_seg("lip", V(8), 0.0, 3.85, "مینا... تو خونه یه چیز شیرین داریم؟", lead=0.55, tail=0.2,
            closed="4-1", open="4-2", punch=True, cap_y=CAP4, sc=4)
s = add_seg("lip", V(9), 0.0, adur(V(9)), "رضا!! همین الان دو بشقاب پلو خوردی! این شکم ته نداره؟!", lead=0.15, tail=0.0,
            closed="4-4", open="4-3", punch=True, shake=True, cap_y=CAP4, sc=4)
add_sfx(s.start - 0.05, "s10.mp3", 0.6)
s = add_seg("still", None, 0, 1.3, "", tail=0.0, image="4-4", shake=True, sc=4)
add_sfx(s.start + 0.1, "s7.mp3", 0.7)
MARK["card"] = t
s = add_seg("card", None, 0, 3.6, "", tail=0.0, image="4-4", sc=5)
add_sfx(s.start + 0.1, "s6.mp3", 0.45)
TOTAL = t
NF = int(round(TOTAL * FPS))

# blood-sugar level keyframes (0 = very low, 1 = very high)
GKEYS = [(0, 0.50), (MARK["v2"], 0.64), (MARK["v2"] + 1.4, 0.97), (MARK["s1end"], 0.97),
         (MARK["s2"], 0.58), (MARK["drop"] + 0.2, 0.55), (MARK["drop"] + 2.6, 0.10), (TOTAL, 0.10)]
def glevel(tt):
    for (t0, a), (t1, b) in zip(GKEYS, GKEYS[1:]):
        if t0 <= tt <= t1:
            k = (tt - t0) / max(t1 - t0, 1e-6); k = k * k * (3 - 2 * k)
            return a + (b - a) * k
    return GKEYS[-1][1]

# ---------------------------------------------------------------- per-seg data
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
    if words:
        wts = np.array([len(w.strip(".،!؟:")) + 1.6 for w in words], float)
        cum = np.concatenate([[0], np.cumsum(wts) / wts.sum()])
        s.wt = [(s.vstart + frames[min(int(cum[i] * len(frames)), len(frames) - 1)] / FPS, w) for i, w in enumerate(words)]
    else:
        s.wt = []
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


# ---------------------------------------------------------------- render helpers
def camera(src, zoom=1.0, fx=0.5, fy=0.5, ox=0.0, oy=0.0):
    sw, sh = src.size
    cw, ch = sw / zoom, sh / zoom
    x0 = min(max(fx * sw - cw * fx - ox * sw, 0), sw - cw)
    y0 = min(max(fy * sh - ch * fy - oy * sh, 0), sh - ch)
    box = (x0, y0, x0 + cw, y0 + ch)
    return src.resize((W, H), Image.BILINEAR if PREVIEW else Image.LANCZOS, box=box), box


def to_out(pt, box):
    return ((pt[0] - box[0]) * W / (box[2] - box[0]), (pt[1] - CROP_TOP - box[1]) * H / (box[3] - box[1]))


CAP_CACHE = {}
def caption_layer(word):
    if word not in CAP_CACHE: CAP_CACHE[word] = text_layer(word, 92, stroke=11)
    return CAP_CACHE[word]


def ease_out(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def pop_scale(dt, dur=0.18):
    if dt < 0: return 0
    k = min(1, dt / dur)
    return ease_out(k) + 0.18 * math.sin(min(1, dt / 0.32) * math.pi)


def scaled(lay, sc, alpha=1.0):
    l = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.LANCZOS)
    if alpha < 1:
        l.putalpha(l.getchannel("A").point(lambda v: int(v * alpha)))
    return l


def put_badge(frame, lay, src_pt, box, appear, tt, phase=0.0):
    sc = pop_scale(tt - appear) if tt - appear < 0.5 else 1.0
    if sc <= 0: return
    px, py = to_out(src_pt, box)
    bob = 5 * math.sin(tt * 3.2 + phase)
    b = scaled(lay, sc)
    frame.alpha_composite(b, (int(px - b.width / 2), int(py - b.height + bob)))


def lerp(c1, c2, k): return tuple(int(a + (b - a) * k) for a, b in zip(c1, c2))
def gcolor(v):
    low, ok, high = (40, 130, 230), (60, 190, 90), (230, 45, 45)
    if v < 0.3: return lerp(low, ok, max(0, (v - 0.12) / 0.18))
    if v > 0.7: return lerp(ok, high, min(1, (v - 0.7) / 0.2))
    return ok


def draw_gauge(frame, box, tt):
    v = glevel(tt)
    x0, y0 = to_out((58, 380), box); x1, y1 = to_out((104, 655), box)
    jit = 3 * math.sin(tt * 60) if v > 0.9 else 0
    x0 += jit; x1 += jit
    d = ImageDraw.Draw(frame)
    w = x1 - x0; r = w * 0.85
    cx = (x0 + x1) / 2
    # tube + bulb
    d.rounded_rectangle((x0, y0, x1, y1), radius=w / 2, fill=(255, 250, 240, 255), outline=(20, 20, 30, 255), width=7)
    d.ellipse((cx - r, y1 - r * 0.6, cx + r, y1 + r * 1.4), fill=(255, 250, 240, 255), outline=(20, 20, 30, 255), width=7)
    col = gcolor(v) + (255,)
    inner = 10
    top = y1 - (y1 - y0 - inner * 2) * v
    d.rounded_rectangle((x0 + inner, top, x1 - inner, y1 + 4), radius=(w - inner * 2) / 2, fill=col)
    d.ellipse((cx - r + inner, y1 - r * 0.6 + inner, cx + r - inner, y1 + r * 1.4 - inner), fill=col)
    # normal-zone ticks
    for lv in (0.3, 0.7):
        ty = y1 - (y1 - y0 - inner * 2) * lv
        d.line((x1 + 4, ty, x1 + 26, ty), fill=(20, 20, 30, 255), width=6)
    lab = G_LABEL
    frame.alpha_composite(lab, (int(cx - lab.width / 2), int(y0 - lab.height + 22)))
    return (x1, y0, y1)


def render(f):
    tt = f / FPS
    s = next((x for x in segs if x.start <= tt < x.end), segs[-1])
    lt = tt - s.start
    vi = int(round((tt - s.vstart) * FPS))
    mouth = s.mouth[vi] if 0 <= vi < len(s.mouth) else 0
    zoom, fx, fy, ox, oy = 1.0, 0.5, 0.45, 0.0, 0.0
    if getattr(s, "punch", False): zoom += 0.06 * math.exp(-lt / 0.13)
    zoom += 0.010 * lt
    if getattr(s, "shake", False):
        ox = 0.006 * math.sin(lt * 55) * math.exp(-lt / 0.9)
        oy = 0.004 * math.cos(lt * 47) * math.exp(-lt / 0.9)
    if getattr(s, "tremble", False):
        ox += 0.0018 * math.sin(tt * 70); oy += 0.0012 * math.cos(tt * 63)
    if s.kind == "lip":
        key = s.open if mouth else s.closed
    elif s.kind == "run":
        key = s.frames[int(lt / 0.15) % 2]
    else:
        key = s.image
    src = img(key)
    zoom = max(zoom, 1.01)
    frame, box = camera(src, zoom, fx, fy, ox, oy)
    frame = frame.convert("RGBA")

    # overlays
    if s.sc in (1, 2):
        gx1, gy0, gy1 = draw_gauge(frame, box, tt)
        v = glevel(tt)
        if s.sc == 1 and tt >= MARK["v2"] + 1.2:
            lay = scaled(HIGH, pop_scale(tt - MARK["v2"] - 1.2) if tt - MARK["v2"] < 1.7 else 1.0)
            frame.alpha_composite(lay, (int(gx1 + 30), int(gy0 + 10 + 4 * math.sin(tt * 9))))
        if s.sc == 2 and tt >= MARK["low"]:
            lay = scaled(LOW, pop_scale(tt - MARK["low"]) if tt - MARK["low"] < 0.5 else 1.0)
            frame.alpha_composite(lay, (int(gx1 + 30), int(gy1 - lay.height - 10)))
    if s.sc == 1:
        put_badge(frame, B_STOMACH, (600, 305), box, MARK["s1"] + 0.35, tt)
        put_badge(frame, B_PANC, (150, 790), box, MARK["s1"] + 0.85, tt, 1.3)
        if s.kind == "run":
            put_badge(frame, B_INS, (545, 885), box, MARK["run"] + 0.1, tt, 2.1)
    if s.sc == 2:
        put_badge(frame, B_INS, (595, 850), box, MARK["s2"] + 1.4, tt, 2.1)
    # titles
    for lay, t0 in ((TITLE1, MARK["s1"] + 0.05), (TITLE2, MARK["s2"] + 0.05)):
        dt = tt - t0
        if 0 <= dt < 1.7:
            a = 1.0 if dt < 1.4 else max(0, 1 - (dt - 1.4) / 0.3)
            l = scaled(lay, pop_scale(dt), a)
            frame.alpha_composite(l, (W // 2 - l.width // 2, 250 - l.height // 2))
    # end card
    if s.kind == "card":
        k = min(1, lt / 0.4)
        dim = Image.new("RGBA", (W, H), (20, 12, 18, int(170 * k)))
        frame.alpha_composite(dim)
        lines = CARD_LINES
        y = 760
        for i, lay in enumerate(lines):
            dt = lt - 0.15 - i * 0.25
            if dt < 0: continue
            l = scaled(lay, pop_scale(dt))
            frame.alpha_composite(l, (W // 2 - l.width // 2, y - l.height // 2))
            y += 150
    frame.alpha_composite(HANDLE, (36, 150))

    # captions
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
    if tt > TOTAL - 0.5:
        out = Image.blend(out, Image.new("RGB", out.size, (0, 0, 0)), min(1, (tt - (TOTAL - 0.5)) / 0.5))
    return out


CARD_LINES = [text_layer("گشنگیِ زود بعد از غذا", 74, stroke=10),
              text_layer("می‌تونه نشونه‌ی", 74, stroke=10),
              text_layer("مقاومت به انسولین باشه", 74, fill=(255, 210, 60), stroke=10)]


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
    for at, p, ss, dur, g in sfx:
        if g > 0: add(p, max(at, 0), ss, dur, g)
    im = len(inputs) // 2; inputs += ["-i", AUD + "s11-1-2.mp3"]
    filters.append(f"[{im}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{TOTAL:.3f},loudnorm=I=-24:TP=-3,aresample=48000,"
                   f"volume=0.2,afade=t=in:d=0.6,afade=t=out:st={TOTAL-1.5:.3f}:d=1.5[mus]")
    labels.append("[mus]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,atrim=0:{TOTAL:.3f},alimiter=limit=0.95[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]", "-c:a", "pcm_s16le", path], check=True)


if __name__ == "__main__":
    print("total %.2fs, %d frames" % (TOTAL, NF))
    for s in segs: print(f"{s.start:6.2f}-{s.end:6.2f} {s.kind:5s} {s.words[:40]}")
    if "--frames" in sys.argv:   # dump stills at given times for checking
        ts = [float(x) for x in sys.argv[sys.argv.index("--frames") + 1].split(",")]
        for x in ts: render(int(x * FPS)).resize((360, 640)).save(HERE + f"chk_{x:05.1f}.jpg")
        sys.exit()
    mix = HERE + "mix.wav"
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
