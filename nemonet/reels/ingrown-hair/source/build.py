"""Nemonet ingrown-hair reel – full build.
python3 -I build.py out.mp4 [--preview start end]
"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)) + "/"
IMG = os.path.abspath(HERE + "..") + "/"          # nemonet/reels/ingrown-hair/
AUD = IMG
FONT = os.path.abspath(IMG + "../../IRANYekanWebBlack.woff2")
W, H, FPS = 1080, 1920, 30
OUT = sys.argv[1] if len(sys.argv) > 1 else "ingrown_full.mp4"
PREVIEW = None
if "--preview" in sys.argv:
    i = sys.argv.index("--preview"); PREVIEW = (float(sys.argv[i + 1]), float(sys.argv[i + 2]))
WORK = HERE


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
        IMS[key] = load_src(IMG + key + ".jpg")[0]
    return IMS[key]

CT = 5  # crop top for 768x1376 sources (y coords below are crop-adjusted)


def feather_paste(dst, src, box, blur=6):
    m = Image.new("L", dst.size, 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=16, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    return Image.composite(src, dst, m)


def build_composites():
    # hair offended (hands on hips) with closed mouth: mouth from 1-1
    IMS["1-3c"] = feather_paste(img("1-3"), img("1-1"), (262, 945 - CT, 348, 1030 - CT))
    # hair finger raised, closed smile: mouth from 2-1
    IMS["2-3c"] = feather_paste(img("2-3"), img("2-1"), (268, 940 - CT, 352, 1020 - CT))
    # razor shrugging, closed mouth: mouth from 2-7
    IMS["2-6c"] = feather_paste(img("2-6"), img("2-7"), (525, 225 - CT, 600, 295 - CT))
build_composites()


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


def badge(text, color=(30, 110, 200)):
    lab = text_layer(text, 46, fill="white", stroke=0)
    lw, lh = lab.size
    bw, bh = lw - 30, lh - 34
    lay = Image.new("RGBA", (bw + 20, bh + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((4, 4, bw + 14, bh + 4), radius=bh // 2, fill=color + (255,), outline=(15, 25, 45, 255), width=5)
    cx = (bw + 18) // 2
    d.polygon([(cx - 14, bh + 2), (cx + 14, bh + 2), (cx, bh + 26)], fill=color + (255,), outline=(15, 25, 45, 255))
    d.rectangle((cx - 11, bh - 2, cx + 11, bh + 3), fill=color + (255,))
    lay.alpha_composite(lab, (cx - lw // 2, (bh + 8) // 2 - lh // 2 + 2))
    return lay


def pill(text, bg=(255, 244, 225), fg=(40, 20, 10), size=60):
    t = text_layer(text, size, fill=fg, stroke=0, pad=30)
    w, h = t.size
    lay = Image.new("RGBA", (w + 60, h + 10), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle((0, 0, w + 59, h + 9), radius=(h + 10) // 2, fill=bg + (245,),
                                          outline=(40, 20, 10, 255), width=6)
    lay.alpha_composite(t, (30, 5)); return lay


BADGES = {"hair": badge("مو"), "razor": badge("تیغ", (220, 70, 140))}
BADGE_POS = {"hair": (300, 880 - CT), "razor": (468, 150 - CT)}   # source px (crop-adjusted)
PILLS = {
    "later": pill("چند هفته بعد..."),
    "wrong": pill("خلاف جهت رشد مو", bg=(225, 45, 50), fg=(255, 255, 255)),
    "ingrown": pill("موی زیرپوستی", bg=(225, 45, 50), fg=(255, 255, 255)),
    "right": pill("هم‌جهت رشد مو", bg=(40, 170, 90), fg=(255, 255, 255)),
}


# ---------------------------------------------------------------- timeline
class Seg:
    def __init__(self, **k): self.__dict__.update(k)

segs, clips, sfx = [], [], []
t = 0.0

def add_seg(kind, path, ss, dur, words, lead=0.0, tail=0.15, **kw):
    global t
    start = t
    vstart = start + lead
    if path:
        clips.append((vstart, path, ss, dur, 1.0))
        r = rms_frames(pcm(path, ss, dur))
    else:
        r = np.zeros(int(round(dur * FPS)))
    s = Seg(kind=kind, start=start, vstart=vstart, end=vstart + dur + tail, rms=r, words=words, **kw)
    segs.append(s); t = s.end
    return s

def add_sfx(at, name, gain=0.6, ss=0.0, dur=None):
    sfx.append((at, AUD + name, ss, dur, gain))

V = lambda n: AUD + f"v{n}.mp3"
SKIN = 1720   # caption y in skin scenes
OFFICE = 330  # caption y in office

# Scene 1: inside the skin ---------------------------------------------------
s = add_seg("lip", V(1), 0.0, 5.13, "باز من؟ آخه موی زیر بغل، کی قراره تو رو ببینه؟", lead=0.7, tail=0.15,
            closed="1-1", open="1-2", cap_y=SKIN, badges=True)
add_sfx(0.05, "s1.mp3", 0.5)
add_sfx(0.25, "s6.mp3", 0.5); add_sfx(0.45, "s6.mp3", 0.5)
s = add_seg("lip", V(2), 0.0, 5.20, "خودم می‌بینم! منم آبرو دارم، یه اصلاح درست‌وحسابی حقمه!", lead=0.05, tail=0.2,
            closed="1-3c", open="1-3", punch=True, cap_y=SKIN, badges=True)
s = add_seg("still", None, 0, 0.9, "", image="1-4", punch=True, shake=True, cap_y=SKIN)
add_sfx(s.start, "s2.mp3", 0.7)

# Scene 2: weeks later, wrong direction --------------------------------------
s = add_seg("fade", None, 0, 0.8, "", a="1-4", b="2-1", cap_y=SKIN, pill="later", pill_at=s.end, pill_xy=(300, 280))
add_sfx(s.start, "s3.mp3", 0.55)
P_LATER = s.start
s = add_seg("lip", V(3), 0.0, 3.08, "هنوز سه هفته نشده، باز سبز شدی؟", lead=0.0, tail=0.15,
            closed="2-1", open="2-2", cap_y=SKIN, pill="later", pill_at=P_LATER, pill_xy=(300, 280))
s = add_seg("lip", V(4), 0.0, 3.73, "کارمه دیگه! فقط این دفعه از اون‌ور نزنی‌ها...", lead=0.05, tail=0.25,
            closed="2-3c", open="2-3", punch=True, cap_y=SKIN)
s = add_seg("still", None, 0, 0.9, "", image="2-4", punch=True, shake=True, cap_y=SKIN)
add_sfx(s.start, "s4.mp3", 0.7)
s = add_seg("lip", V(5), 0.0, 3.86, "باز برعکس زدی؟! صد دفعه گفتم خلاف جهت نه!", lead=0.0, tail=0.15,
            closed="2-4", open="2-5", shake=True, cap_y=SKIN)
s = add_seg("lip", V(6), 0.0, 2.97, "حالا چه فرقی می‌کنه؟ کوتاه شدی دیگه.", lead=0.05, tail=0.2,
            closed="2-6c", open="2-6", punch=True, cap_y=SKIN)
s = add_seg("lip", V(7), 0.0, 4.69, "باشه... حالا که این‌طوره، دیگه بیرون نمیام. می‌رم تو!", lead=0.05, tail=0.2,
            closed="2-8", open="2-7", punch=True, cap_y=SKIN, slow=True)

# Scene 3: revenge -> ingrown hair -------------------------------------------
s = add_seg("fade", None, 0, 1.0, "", a="2-8", b="3-1", cap_y=SKIN)
add_sfx(s.start, "s5.mp3", 0.6)
P_ING = s.end
s = add_seg("still", V(8), 0.0, 4.60, "و این‌جوری، یه موی زیرپوستی به دنیا اومد.", lead=0.0, tail=0.1,
            image="3-1", cap_y=SKIN, pill="ingrown", pill_at=P_ING, pill_xy=(540, 230))
add_sfx(P_ING, "s6.mp3", 0.5)
s = add_seg("still", None, 0, 0.8, "", image="3-2", punch=True, bounce=True, cap_y=SKIN,
            pill="ingrown", pill_at=P_ING, pill_xy=(540, 230))

# Scene 4: doctor ------------------------------------------------------------
s = add_seg("lip", V(9), 0.18, 5.46 - 0.18 + 0.0, "دکتر، زیر بغلم پر از این جوش‌های دردناک شده. مگه چیکار کردم؟",
            lead=0.35, tail=0.2, closed="4-1", open="4-2", punch=True, cap_y=OFFICE)
add_sfx(s.start, "s1.mp3", 0.35)
s = add_seg("lip", V(10), 0.22, 1.85 - 0.22, "این موی زیرپوستیه.", lead=0.05, tail=0.0,
            closed="4-3", open="4-4", cap_y=OFFICE)
s = add_seg("still", V(10), 1.85, 4.55, "وقتی خیلی از ته یا خلاف جهت رشد مو اصلاح می‌کنی،", lead=0.0, tail=0.0,
            image="2-4", punch=True, cap_y=SKIN, pill="wrong", pill_at=None, pill_xy=(760, 280))
add_sfx(s.start + 0.05, "s4.mp3", 0.35)
s = add_seg("still", V(10), 6.40, 10.9975 - 6.40, "نوک تیز مو برمی‌گرده توی پوست و التهاب و جوش درست می‌کنه.", lead=0.0, tail=0.25,
            image="3-1", punch=True, cap_y=SKIN, pill="ingrown", pill_at=None, pill_xy=(540, 230))
s = add_seg("still", V(11), 0.0, 2.06, "هم‌جهت رشد مو اصلاح کن،", lead=0.1, tail=0.0,
            image="5-1", punch=True, cap_y=SKIN, pill="right", pill_at=None, pill_xy=(300, 280))
add_sfx(s.start + 0.05, "s7.mp3", 0.4)
s = add_seg("lip", V(11), 2.06, 9.08 - 2.06, "و قبلش پوست رو با آب گرم نرم کن. اگه جوش‌ها زیاد یا چرکی شدن، حتماً به پزشک سر بزن.",
            lead=0.0, tail=0.3, closed="4-3", open="4-4", punch=True, cap_y=OFFICE)

# Scene 5: make up -----------------------------------------------------------
s = add_seg("still", None, 0, 0.7, "", image="5-2", punch=True, bounce=True, cap_y=SKIN)
add_sfx(s.start + 0.05, "s7.mp3", 0.6)
s = add_seg("lip", V(12), 0.0, 3.03, "دیدی؟ از اولش هم همینو می‌خواستم!", lead=0.0, tail=1.2,
            closed="5-2", open="5-3", cap_y=SKIN)

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
    words = s.words.split()
    if words:
        voiced = s.rms > 0.10
        frames = [f for a, b in regions(voiced) for f in range(a, b)] or list(range(len(s.rms)))
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
    if getattr(s, "pill", None) and getattr(s, "pill_at", "x") is None:
        s.pill_at = s.start

BADGE_T0 = segs[0].start
BADGE_T1 = segs[1].end


# ---------------------------------------------------------------- render helpers
def camera(src, zoom=1.0, fx=0.5, fy=0.5, ox=0.0, oy=0.0):
    sw, sh = src.size
    cw, ch = sw / zoom, sh / zoom
    x0 = min(max(fx * sw - cw * fx - ox * sw, 0), sw - cw)
    y0 = min(max(fy * sh - ch * fy - oy * sh, 0), sh - ch)
    box = (x0, y0, x0 + cw, y0 + ch)
    return src.resize((W, H), Image.BILINEAR if PREVIEW else Image.LANCZOS, box=box), box


def to_out(pt, box):
    return ((pt[0] - box[0]) * W / (box[2] - box[0]), (pt[1] - box[1]) * H / (box[3] - box[1]))


CAP_CACHE = {}
def caption_layer(word):
    if word not in CAP_CACHE:
        CAP_CACHE[word] = text_layer(word, 92, stroke=11)
    return CAP_CACHE[word]

HANDLE = text_layer("@nemonet.ir", 34, fill=(255, 255, 255, 170), stroke=3, stroke_fill=(0, 0, 0, 110), pad=10, rtl=False)

def ease_out(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def pop_scale(dt, dur=0.18):
    if dt < 0: return 0
    k = min(1, dt / dur)
    return ease_out(k) + 0.18 * math.sin(min(1, dt / 0.32) * math.pi)

def scaled(lay, sc, alpha=1.0):
    l = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.LANCZOS) if sc != 1 else lay.copy()
    if alpha < 1:
        l.putalpha(l.getchannel("A").point(lambda v: int(v * alpha)))
    return l


def render(f):
    tt = f / FPS
    s = next((x for x in segs if x.start <= tt < x.end), segs[-1])
    lt = tt - s.start
    vi = int(round((tt - s.vstart) * FPS))
    mouth = s.mouth[vi] if 0 <= vi < len(s.mouth) else 0
    zoom, fx, fy, ox, oy = 1.0, 0.5, 0.45, 0.0, 0.0
    if getattr(s, "punch", False):
        zoom += 0.06 * math.exp(-lt / 0.13)
    zoom += (0.006 if getattr(s, "slow", False) else 0.010) * lt
    if getattr(s, "slow", False):
        zoom += 0.012 * lt; fx, fy = 0.35, 0.65     # creeping push on the scheming hair
    if getattr(s, "shake", False):
        ox = 0.006 * math.sin(lt * 55) * math.exp(-lt / 0.6)
        oy = 0.004 * math.cos(lt * 47) * math.exp(-lt / 0.6)
    if s.kind == "lip":
        src = img(s.open if mouth else s.closed)
    elif s.kind == "still":
        src = img(s.image)
        if getattr(s, "bounce", False):
            zoom += 0.012 * abs(math.sin(lt * 9))
    elif s.kind == "fade":
        k = min(max(lt / (s.end - s.start), 0), 1)
        k = k * k * (3 - 2 * k)
        src = Image.blend(img(s.a), img(s.b), k)
    zoom = max(zoom, 1.01)
    frame, box = camera(src, zoom, fx, fy, ox, oy)
    frame = frame.convert("RGBA")

    # character name badges (scene 1)
    if BADGE_T0 <= tt < BADGE_T1 + 0.3:
        for who, delay in (("hair", 0.25), ("razor", 0.45)):
            dt = tt - (BADGE_T0 + delay)
            sc = pop_scale(dt) if dt < 0.5 else 1.0
            if sc <= 0: continue
            a = 1.0 if tt < BADGE_T1 else max(0, 1 - (tt - BADGE_T1) / 0.3)
            px, py = to_out(BADGE_POS[who], box)
            bob = 5 * math.sin(tt * 3.2 + (0 if who == "hair" else 1.7))
            b = scaled(BADGES[who], sc, a)
            frame.alpha_composite(b, (int(px - b.width / 2), int(py - b.height - 6 + bob)))

    # info pills
    if getattr(s, "pill", None):
        dt = tt - s.pill_at
        if dt >= 0:
            sc = pop_scale(dt) if dt < 0.5 else 1.0
            nxt = segs[segs.index(s) + 1] if s is not segs[-1] else None
            a = 1.0
            if not (nxt and getattr(nxt, "pill", None) == s.pill) and tt > s.end - 0.2:
                a = max(0, (s.end - tt) / 0.2)
            lay = scaled(PILLS[s.pill], sc, a)
            x, y = s.pill_xy
            frame.alpha_composite(lay, (int(x - lay.width / 2), int(y - lay.height / 2)))

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
    # music: one 67.8 s track, crossfaded into a second copy if the reel is longer
    i1 = len(inputs) // 2; inputs += ["-i", AUD + "s8.mp3"]
    i2 = len(inputs) // 2; inputs += ["-i", AUD + "s8.mp3"]
    for k, i in (("m1", i1), ("m2", i2)):
        filters.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-24:TP=-3,aresample=48000[{k}]")
    filters.append(f"[m1][m2]acrossfade=d=3[m12]")
    filters.append(f"[m12]atrim=0:{TOTAL:.3f},volume=0.2,afade=t=in:d=0.4,afade=t=out:st={TOTAL-1.5:.3f}:d=1.5[mus]")
    labels.append("[mus]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,apad,atrim=0:{TOTAL:.3f},alimiter=limit=0.95[out]")
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]", "-c:a", "pcm_s16le", path]
    subprocess.run(cmd, check=True)
    # make sure the mix covers the whole timeline (ffmpeg stops at -shortest)
    tmp = path + ".pad.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-af", f"apad=whole_dur={TOTAL + 0.5:.3f}",
                    "-c:a", "pcm_s16le", tmp], check=True)
    os.replace(tmp, path)


if __name__ == "__main__":
    print("total %.2fs, %d frames" % (TOTAL, NF))
    for s in segs: print(f"{s.start:6.2f}-{s.end:6.2f} {s.kind:5s} {s.words[:40]}")
    mix = WORK + "mix.wav"
    build_audio(mix)
    f0, f1 = (0, NF) if not PREVIEW else (int(PREVIEW[0] * FPS), int(PREVIEW[1] * FPS))
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-ss", str(f0 / FPS), "-t", str((f1 - f0) / FPS), "-i", mix,
           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(render(f).tobytes())
    p.stdin.close(); p.wait()
    print("done", OUT)
