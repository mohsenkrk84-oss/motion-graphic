"""Nemonet men-vs-women reel – full build.
python3 -I source/sfx.py audio            # synthesise SFX + music once
python3 -I source/build.py out.mp4 [--preview start end] [--sheet sheet.jpg]
"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)) + "/"
D = os.path.abspath(HERE + "..") + "/"                 # nemonet/reels/men-vs-women/
AUD = D + "audio/"
FONT = os.path.abspath(D + "../../../IRANYekanWebBold.ttf")
W, H, FPS = 1080, 1920, 30
OUT = sys.argv[1] if len(sys.argv) > 1 else "out.mp4"
PREVIEW = None
if "--preview" in sys.argv:
    i = sys.argv.index("--preview"); PREVIEW = (float(sys.argv[i + 1]), float(sys.argv[i + 2]))
SHEET = sys.argv[sys.argv.index("--sheet") + 1] if "--sheet" in sys.argv else None

PLUM = (96, 28, 78)
TEAL_D = (34, 78, 80)
CREAM = (246, 241, 228)


# ---------------------------------------------------------------- audio utils
def pcm(path, start=0.0, dur=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(start)]
    if dur: cmd += ["-t", str(dur)]
    cmd += ["-i", path, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.int16).astype(np.float32) / 32768


def rms_frames(a):
    hop = 16000 // FPS
    n = int(math.ceil(len(a) / hop))
    r = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    return r / (np.percentile(r, 97) + 1e-9)


# ---------------------------------------------------------------- images
IMS = {}
def img(key):
    if key not in IMS:
        im = Image.open(HERE + key + ".jpg").convert("RGB")
        w, h = im.size
        th = round(w * 16 / 9); top = (h - th) // 2
        IMS[key] = im.crop((0, top, w, top + th))
    return IMS[key]


def shrunk(key, k=0.82):
    """Scale an image down, bottom-aligned, on its own paper colour (for frames whose action reaches the text area)."""
    src = img(key); w, h = src.size
    bg = tuple(int(v) for v in np.median(np.asarray(src)[5:60, 5:60].reshape(-1, 3), 0))
    out = Image.new("RGB", (w, h), bg)
    sm = src.resize((int(w * k), int(h * k)), Image.LANCZOS)
    out.paste(sm, ((w - sm.width) // 2, h - sm.height))
    return out



# ---------------------------------------------------------------- text
def text_layer(text, size, fill, stroke=7, stroke_fill=CREAM, pad=24, rtl=True):
    f = ImageFont.truetype(FONT, size)
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    kw = dict(direction="rtl", language="fa") if rtl else {}
    bb = d.textbbox((0, 0), text, font=f, stroke_width=stroke, anchor="lt", **kw)
    lay = Image.new("RGBA", (bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((pad - bb[0], pad - bb[1]), text, font=f, fill=fill, stroke_width=stroke,
                             stroke_fill=stroke_fill, anchor="lt", **kw)
    return lay


TXT = {}
def header(t):
    k = ("h", t)
    if k not in TXT: TXT[k] = text_layer(t, 60, PLUM)
    return TXT[k]


def sub(t):
    k = ("s", t)
    if k not in TXT:
        size = 54
        lay = text_layer(t, size, TEAL_D)
        while lay.width > W - 80: size -= 3; lay = text_layer(t, size, TEAL_D)
        TXT[k] = lay
    return TXT[k]


HANDLE = text_layer("@nemonet.ir", 34, (120, 112, 118, 210), stroke=0, rtl=False, pad=8)


# ---------------------------------------------------------------- timeline
class Seg:
    def __init__(self, **k): self.__dict__.update(k)

segs, clips, sfx = [], [], []
t = 0.0
V = lambda n: D + f"v{n}.mp3"


def add(kind, sub_text="", clip=None, dur=None, lead=0.05, tail=0.15, **kw):
    """kind: still (image=), lip (closed=, open=), alt (a=, b=, period=)."""
    global t
    start = t
    if clip:
        n, ss, cd = clip
        clips.append((start + lead, V(n), ss, cd))
        rms = rms_frames(pcm(V(n), ss, cd))
        total = lead + cd + tail
    else:
        rms = np.zeros(1); total = dur
    s = Seg(kind=kind, start=start, end=start + total, vstart=start + lead, rms=rms, sub=sub_text, **kw)
    s.hdr = kw.get("hdr", segs[-1].hdr if segs else "")
    # mouth open/closed from loudness (with chatter + flicker removal)
    m = np.zeros(len(rms), int); run = 0
    for i, v in enumerate(rms):
        o = v > 0.16
        if o:
            run += 1
            if run % 5 == 0: o = False
        else: run = 0
        m[i] = o
    for i in range(1, len(m) - 1):
        if m[i - 1] == m[i + 1] != m[i] and m[i]: m[i] = m[i - 1]
    s.mouth = m
    segs.append(s); t = s.end
    return s


def fx(at, name, gain=0.6):
    sfx.append((at, AUD + name, gain))


W_ = "نمونه‌گیری از خانم‌ها"
M_ = "نمونه‌گیری از آقایون"

# ----- women -----
s = add("lip", "سلام!", (1, 0.17, 0.78), closed="1-1", open="1-1", punch=True, hdr=W_, lead=0.25, tail=0.15, bounce=True)
s = add("still", "باید ۸ تا لوله خون بگیرم", (2, 0.10, 2.00), image="1-2", punch=True, push=(0.10, 0.5, 0.45), tail=0.2)
fx(s.start, "s10.wav", 0.35)
s = add("still", "رگت هم خیلی باریکه...", (3, 0.0, 2.10), image="2-1", punch=True, push=(0.14, 0.62, 0.30), tail=0.1)
fx(s.start + 0.3, "s4.wav", 0.35)
s = add("still", "پس سوزن...", (4, 0.14, 1.18), image="3-1", punch=True, push=(0.08, 0.6, 0.4), tail=0.2)
fx(s.start, "s5.wav", 0.35)
s = add("still", "یه کم درد داره", (4, 1.70, 1.40), image="4-1", punch=True, tremble=True, tail=0.45)
fx(s.end - 0.4, "s4.wav", 0.7)
s = add("lip", "اشکال نداره", (5, 0.13, 0.97), closed="4-2", open="4-3", punch=True, tail=0.3)
s = add("still", "درک می‌کنم", (6, 0.18, 1.16), image="4-4", push=(0.06, 0.5, 0.4), tail=0.3)
s = add("still", "آروم باش...", (7, 0.13, 1.17), image="5-1", sneak=True, tail=0.65)
fx(s.start, "s1.wav", 0.55)
s = add("still", "", None, 0.85, image="5-2", punch=True, shake=0.006)
fx(s.start, "s2.wav", 0.7)
s = add("still", "", None, 1.35, image="6-1", tremble=True, push=(0.08, 0.5, 0.6), panel=True)
fx(s.start, "s3.wav", 0.55)
s = add("still", "تموم شد!", (8, 0.10, 0.92), image="7-1", punch=True, tail=0.25)
fx(s.start, "s5.wav", 0.4)
s = add("lip", "عه، زدی؟", (9, 0.0, 1.40), closed="7-3", open="7-2", punch=True, tail=0.05)
s = add("lip", "اصلاً حس نکردم!", (9, 1.55, 1.82), closed="7-3", open="7-2", lead=0.0, tail=0.25, push=(0.06, 0.3, 0.6))
s = add("lip", "آره دیگه...", (10, 0.0, 1.27), closed="7-5", open="7-4", punch=True, tail=0.05)
s = add("lip", "دستت خیلی سبکه", (10, 1.44, 1.71), closed="7-5", open="7-4", lead=0.0, tail=0.25, push=(0.05, 0.3, 0.6))
s = add("swap", "مرسییی!", (11, 0.12, 1.28), a="8-1", b="8-2", swap_at=0.55, punch=True, bounce=True, tail=0.6, panel=True)
fx(s.start, "s6.wav", 0.6); fx(s.start + 0.55, "s5.wav", 0.4)

# ----- men -----
s = add("still", "فقط یه پنبه‌ست...", (12, 0.0, 1.50), image="9-1", punch=True, hdr=M_, lead=0.3, tail=0.15)
fx(s.start, "s10.wav", 0.5)
s = add("still", "یه ثانیه‌ست", (12, 1.87, 1.06), image="9-2", punch=True, tail=0.35, panel=True)
s = add("lip", "آی", (13, 0.0, 1.85), closed="9-3", open="9-4", punch=True, tremble=True, lead=0.0, tail=0.05, panel=True)
MUSIC_END = s.start
s = add("alt", "آاااای!", (14, 0.0, 1.50), a="10-1", b="10-2", period=0.1, punch=True, shake=0.008, lead=0.0, tail=0.0, grow=True)
fx(s.start, "s7.wav", 0.6)
s = add("still", "آاااااااای!", (14, 1.50, 0.68), image="10-3", punch=True, shake=0.005, lead=0.0, tail=0.25)
fx(s.start, "s8.wav", 0.7)
s = add("still", "", None, 2.4, image="10-4", punch=True, shake=0.010)
fx(s.start, "s9.wav", 0.8)

TOTAL = t
NF = int(round(TOTAL * FPS))


# ---------------------------------------------------------------- render
def camera(src, zoom=1.0, fx_=0.5, fy=0.5, ox=0.0, oy=0.0):
    sw, sh = src.size
    cw, ch = sw / zoom, sh / zoom
    x0 = min(max(fx_ * sw - cw * fx_ - ox * sw, 0), sw - cw)
    y0 = min(max(fy * sh - ch * fy - oy * sh, 0), sh - ch)
    return src.resize((W, H), Image.BILINEAR if PREVIEW else Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))


def ease_out(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3


def pop(dt, dur=0.16):
    if dt < 0: return 0
    return ease_out(dt / dur) + 0.12 * math.sin(min(1, dt / 0.3) * math.pi)


def scaled(lay, sc):
    if abs(sc - 1) < 1e-3: return lay
    return lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.LANCZOS)


def render(f):
    tt = f / FPS
    s = next((x for x in segs if x.start <= tt < x.end), segs[-1])
    lt = tt - s.start
    vi = int(round((tt - s.vstart) * FPS))
    mouth = s.mouth[vi] if 0 <= vi < len(s.mouth) else 0
    zoom, cx, cy, ox, oy = 1.0, 0.5, 0.5, 0.0, 0.0
    if getattr(s, "punch", False):
        zoom += 0.06 * math.exp(-lt / 0.13)
    zoom += 0.008 * lt
    if getattr(s, "push", None):
        amt, cx, cy = s.push
        k = lt / (s.end - s.start)
        zoom += amt * (k * k * (3 - 2 * k))
    if getattr(s, "shake", 0):
        a = s.shake
        ox = a * math.sin(lt * 55) * math.exp(-lt / 0.8)
        oy = a * 0.7 * math.cos(lt * 47) * math.exp(-lt / 0.8)
    if getattr(s, "tremble", False):
        ox = 0.004 * math.sin(lt * 70); oy = 0.003 * math.cos(lt * 63)
    if getattr(s, "sneak", False):
        ox = -0.025 * (lt / (s.end - s.start)); oy = 0.006 * abs(math.sin(lt * 7))
    if getattr(s, "bounce", False):
        zoom += 0.012 * abs(math.sin(lt * 8))
    if getattr(s, "lift", False):
        oy = -0.02 * lt
    if s.kind == "lip":
        src = img(s.open if mouth else s.closed)
    elif s.kind == "alt":
        src = img(s.a if int(lt / s.period) % 2 == 0 else s.b)
    elif s.kind == "swap":
        src = img(s.a if lt < s.swap_at else s.b)
        if lt >= s.swap_at: zoom += 0.05 * math.exp(-(lt - s.swap_at) / 0.13)
    else:
        src = img(s.image)
    zoom = max(zoom, 1.01)
    frame = camera(src, zoom, cx, cy, ox, oy).convert("RGBA")

    # handle (LTR), header, subtitle line – like the reference layout
    if getattr(s, "panel", False):
        pl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(pl).rounded_rectangle((90, 268, W - 90, 478), radius=40, fill=CREAM + (225,))
        frame.alpha_composite(pl)
    frame.alpha_composite(HANDLE, (W - HANDLE.width - 70, 228))
    i = segs.index(s)
    h_start = s.start if (i == 0 or segs[i - 1].hdr != s.hdr) else -99
    hl = scaled(header(s.hdr), pop(tt - h_start) if tt - h_start < 0.5 else 1.0)
    frame.alpha_composite(hl, (W // 2 - hl.width // 2, 330 - hl.height // 2))
    if s.sub:
        prev_same = i > 0 and segs[i - 1].sub == s.sub
        dt = tt - s.vstart + 0.06
        sc = 1.0 if prev_same else (pop(dt) if dt < 0.5 else 1.0)
        if getattr(s, "grow", False): sc *= 1 + 0.25 * min(1, lt / (s.end - s.start))
        if sc > 0:
            sl = scaled(sub(s.sub), sc)
            frame.alpha_composite(sl, (W // 2 - sl.width // 2, 420 - sl.height // 2))
    out = frame.convert("RGB")
    if tt > TOTAL - 0.4:
        out = Image.blend(out, Image.new("RGB", out.size, CREAM), min(1, (tt - (TOTAL - 0.4)) / 0.4))
    return out


# ---------------------------------------------------------------- audio mix
def build_audio(path):
    inputs, filters, labels = [], [], []
    def inp(p):
        inputs.extend(["-i", p]); return len(inputs) // 2 - 1
    for k, (at, p, ss, dur) in enumerate(clips):
        i = inp(p)
        filters.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,atrim={ss}:duration={dur},asetpts=PTS-STARTPTS,"
                       f"afade=t=in:d=0.02,afade=t=out:st={max(dur-0.04,0):.3f}:d=0.04,loudnorm=I=-16:TP=-2,aresample=48000,"
                       f"adelay={int(at*1000)}|{int(at*1000)}[v{k}]")
        labels.append(f"[v{k}]")
    for k, (at, p, g) in enumerate(sfx):
        i = inp(p)
        filters.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,volume={g},adelay={int(at*1000)}|{int(at*1000)}[x{k}]")
        labels.append(f"[x{k}]")
    i = inp(AUD + "music.wav")
    me = MUSIC_END
    filters.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,aloop=loop=-1:size=2000000,atrim=0:{me:.3f},"
                   f"loudnorm=I=-24:TP=-3,aresample=48000,volume=0.55,afade=t=in:d=0.3,afade=t=out:st={me-0.08:.3f}:d=0.08[mus]")
    labels.append("[mus]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,apad=whole_dur={TOTAL+0.5:.3f},"
                   f"atrim=0:{TOTAL:.3f},alimiter=limit=0.93[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]",
                    "-c:a", "pcm_s16le", path], check=True)


if __name__ == "__main__":
    print("total %.2fs, %d frames" % (TOTAL, NF))
    for s in segs: print(f"{s.start:6.2f}-{s.end:6.2f} {s.kind:5s} {s.sub}")
    if SHEET:
        ims = []
        for s in segs:
            ims.append(render(int((s.vstart + 0.35 if s.sub else s.start + 0.3) * FPS)).resize((270, 480)))
        cols = 8; rows = (len(ims) + cols - 1) // cols
        sh = Image.new("RGB", (cols * 270, rows * 480), "white")
        for k, im in enumerate(ims): sh.paste(im, ((k % cols) * 270, (k // cols) * 480))
        sh.save(SHEET); print("sheet", SHEET); sys.exit()
    mix = HERE + "mix.wav"
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
