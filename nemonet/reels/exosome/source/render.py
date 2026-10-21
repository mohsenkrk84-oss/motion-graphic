"""Render the full exosome-vs-reality reel frames + sfx events.
usage: render.py LAYERS_DIR ASSET_DIR TIMINGS_JSON FRAMES_DIR [frame_start frame_end]
"""
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

LAY, ASSET, TJ, OUTD = sys.argv[1:5]
W, H, FPS = 1080, 1920, 30
T = json.load(open(TJ))
P = T["phrases"]          # list of [start, end] for P1..P8
END = T["end"]
BG = np.array([247, 238, 221], np.float32)
CREAM = (247, 238, 221); INK = (42, 38, 46); CORAL = (232, 115, 90)
MUST = (242, 181, 68); SLATE = (110, 106, 154); TEAL = (21, 122, 126); WHITE = (255, 252, 246)

def ps(i): return P[i - 1][0]
def pe(i): return P[i - 1][1]

# scene boundaries
B1 = ps(3) - 0.3
B2 = ps(5) - 0.3
B3 = ps(7) - 0.3
SCENES = [("s1", 0.0, B1), ("s2", B1, B2), ("s3", B2, B3), ("s4", B3, END)]
IRIS = [(B1, CORAL), (B2, MUST), (B3, SLATE)]

fonts = {}
def font(kind, size):
    k = (kind, size)
    if k not in fonts:
        fonts[k] = ImageFont.truetype(os.path.join(ASSET, "IRANYekanWeb%s.woff2" % kind), size)
    return fonts[k]

def ease_back(p, s=1.7):
    p = min(max(p, 0.0), 1.0)
    return 1 + (s + 1) * (p - 1) ** 3 + s * (p - 1) ** 2

def smooth(p):
    p = np.clip(p, 0, 1); return p * p * (3 - 2 * p)

# ---------------- illustration layers ----------------
layers = {}
def layer(name):
    if name not in layers:
        z = np.load(os.path.join(LAY, name + ".npz"))
        d = {k: z[k] for k in z.files}
        d["im"] = d["im"].astype(np.float32)
        d["lineA"] = d["lineA"].astype(np.float32)
        d["tline"] = d["tline"].astype(np.float32)
        d["tfill"] = d["tfill"].astype(np.float32)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d["cdist"] = []
        for cy, cx, r in d["circ_par"]:
            d["cdist"].append(np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2))
        d["cache"] = None
        layers[name] = d
    return layers[name]

def illus(name, tau):
    d = layer(name)
    done = tau > 2.2
    if done and d["cache"] is not None:
        return d["cache"]
    im = d["im"]
    out = np.broadcast_to(BG, (H, W, 3)).copy()
    for k, (cy, cx, r) in enumerate(d["circ_par"]):
        p = ease_back((tau - (0.0 + 0.15 * k)) / 0.5)
        vis = (d["circ_id"] == k) & (d["cdist"][k] <= r * p)
        out[vis] = im[vis]
    a = (smooth((tau - d["tfill"]) / 0.18) * d["fill"])[..., None]
    out = out * (1 - a) + im * a
    la = (d["lineA"] * (tau >= d["tline"]))[..., None]
    out = out * (1 - la) + im * la
    img = Image.fromarray(out.clip(0, 255).astype(np.uint8))
    if done:
        d["cache"] = img
    return img

# ---------------- text helpers ----------------
def word_img(txt, col, size, kind="Black"):
    f = font(kind, size)
    bb = f.getbbox(txt, direction="rtl", language="fa")
    w = bb[2] - bb[0] + 20
    h = int(size * 1.9)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - bb[0], int(size * 0.28)), txt, font=f, fill=col + (255,),
                            direction="rtl", language="fa")
    return im

class Caption:
    """Lines of (word, colour) popping word by word, RTL."""
    def __init__(self, lines, y, size, t_in, t_out, span=None, line_starts=None, gap=None):
        self.items = []
        self.t_out = t_out
        lh = int(size * 1.48)
        gap = gap if gap is not None else int(size * 0.26)
        nwords = sum(len(l) for l in lines)
        span = span if span is not None else 0.9
        step = min(0.18, max(0.07, span / max(1, nwords)))
        k = 0
        for li, ln in enumerate(lines):
            imgs = [word_img(t, c, size) for t, c in ln]
            total = sum(i.width for i in imgs) + gap * (len(imgs) - 1)
            x = (W + total) // 2
            base_t = line_starts[li] if line_starts else None
            for wi, wim in enumerate(imgs):
                x -= wim.width
                at = (base_t + wi * step) if base_t is not None else (t_in + k * step)
                self.items.append(dict(img=wim, x=x, y=y + li * lh, t=at, word=ln[wi][0], line=li))
                x -= gap
                k += 1
        self.t_in = min(i["t"] for i in self.items)

    def bbox(self, words):
        its = [i for i in self.items if i["word"] in words]
        return (min(i["x"] for i in its), its[0]["y"], max(i["x"] + i["img"].width for i in its))

    def draw(self, frame, t):
        if t < self.t_in or t > self.t_out + 0.35:
            return
        fo = 1 - smooth((t - self.t_out) / 0.3)
        dy = int(-30 * (1 - fo))
        for it in self.items:
            p = (t - it["t"]) / 0.28
            if p <= 0:
                continue
            s = 0.65 + 0.35 * ease_back(p) if p < 1 else 1.0
            al = float(smooth(p / 0.6)) * fo
            wim = it["img"]
            ww, hh = max(1, int(wim.width * s)), max(1, int(wim.height * s))
            im2 = wim.resize((ww, hh), Image.LANCZOS) if s != 1.0 else wim.copy()
            if al < 1:
                im2.putalpha(im2.getchannel("A").point(lambda v: int(v * al)))
            frame.paste(im2, (it["x"] + (wim.width - ww) // 2, it["y"] + dy + (wim.height - hh) // 2), im2)

def pill(frame, text, t, t_in, t_out, y, bg, fg=CREAM, size=44):
    pt = float(smooth((t - t_in) / 0.3)) * (1 - float(smooth((t - t_out) / 0.3)))
    if pt <= 0:
        return
    tim = word_img(text, fg, size, "Regular")
    tb = tim.getchannel("A").getbbox()
    pw, ph = (tb[2] - tb[0]) + 56, int(size * 1.75)
    im = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, pw - 1, ph - 1), ph // 2, fill=bg + (255,))
    im.alpha_composite(tim, (28 - tb[0], (ph - (tb[3] - tb[1])) // 2 - tb[1]))
    im.putalpha(im.getchannel("A").point(lambda v: int(v * pt)))
    frame.paste(im, ((W - pw) // 2, int(y + 18 * (1 - pt))), im)

def marker(frame, x0, x1, y, t, t_in, col=MUST, h=40, alpha=205):
    mp = float(smooth((t - t_in) / 0.4))
    if mp <= 0:
        return
    xl = x1 - (x1 - x0) * mp
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle((xl, y, x1, y + h), 12, fill=col + (alpha,))
    frame.alpha_composite(ov)

def scribble_ellipse(frame, cx, cy, rx, ry, t, t_in, dur=0.5, col=CORAL, width=7):
    p = float(smooth((t - t_in) / dur))
    if p <= 0:
        return
    n = int(120 * 1.15 * p) + 2
    ang = np.linspace(0.3, 0.3 + 2 * np.pi * 1.15 * p, n)
    wob = 1 + 0.04 * np.sin(ang * 3)
    pts = [(cx + rx * wob[i] * np.cos(a), cy + ry * wob[i] * np.sin(a) - 8 * a / (2 * np.pi)) for i, a in enumerate(ang)]
    d = ImageDraw.Draw(frame)
    d.line(pts, fill=col + (255,), width=width, joint="curve")

def sparkle(d, cx, cy, s, col):
    if s <= 0.02:
        return
    a = 26 * s; b = 5 * s
    d.polygon([(cx, cy - a), (cx + b, cy - b), (cx + a, cy), (cx + b, cy + b),
               (cx, cy + a), (cx - b, cy + b), (cx - a, cy), (cx - b, cy - b)], fill=col + (255,))

LOGO = Image.open(os.path.join(ASSET, "app-icon-tide.png")).convert("RGBA")

def shadow_card(w, h, r, fill):
    pad = 30
    im = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 8, pad + w, pad + h + 8), r, fill=(60, 40, 30, 60))
    sh = sh.filter(ImageFilter.GaussianBlur(12))
    im.alpha_composite(sh)
    ImageDraw.Draw(im).rounded_rectangle((pad, pad, pad + w, pad + h), r, fill=fill + (255,))
    return im, pad

def paste_pop(frame, im, cx, cy, t, t_in, t_out=1e9):
    p = (t - t_in) / 0.35
    if p <= 0 or t > t_out + 0.3:
        return
    s = ease_back(p) if p < 1 else 1.0
    al = float(smooth(p / 0.5)) * (1 - float(smooth((t - t_out) / 0.3)))
    w, h = max(1, int(im.width * s)), max(1, int(im.height * s))
    im2 = im.resize((w, h), Image.LANCZOS)
    if al < 1:
        im2.putalpha(im2.getchannel("A").point(lambda v: int(v * al)))
    frame.alpha_composite(im2, (int(cx - w / 2), int(cy - h / 2)))

# ---------------- build overlays ----------------
SFX = []
def ev(kind, t, **kw):
    SFX.append(dict(kind=kind, t=round(float(t), 3), **kw))

# Scene 1
cap1 = Caption([[("اگزوزوم", INK), ("و", INK), ("تزریق‌های", INK), ("میلیونی", INK)],
                [("واقعاً", INK), ("معجزه", CORAL), ("می‌کنن؟", INK)],
                [("یا", INK), ("فقط", INK), ("هدر", INK), ("دادن", INK), ("پوله؟", INK)]],
               y=330, size=72, t_in=ps(1), t_out=B1 - 0.25,
               line_starts=[ps(1), ps(1) + (pe(1) - ps(1)) * 0.5, ps(2)], gap=18)
# Scene 2
cap2a = Caption([[("اگه", INK), ("علت", INK), ("لک", CORAL), ("یا", INK), ("آکنه", CORAL), ("شما", INK)],
                 [("اختلال", INK), ("هورمونی", SLATE), ("باشه...", INK)]],
                y=300, size=72, t_in=ps(3), t_out=ps(4) - 0.1,
                line_starts=[ps(3), ps(3) + (pe(3) - ps(3)) * 0.5], gap=18)
cap2b = Caption([[("۱۰", CORAL), ("جلسه", INK), ("اگزوزوم", INK)],
                 [("هم", INK), ("موقتیه!", CORAL)]],
                y=290, size=92, t_in=ps(4), t_out=B2 - 0.25,
                line_starts=[ps(4), ps(4) + 0.55], gap=24)
# Scene 3
cap3 = Caption([[("اول", INK), ("باید", INK)],
                [("هورمون‌هات", CORAL), ("رو", INK), ("بررسی", INK), ("کنی", INK)]],
               y=250, size=74, t_in=ps(5), t_out=B3 - 0.25,
               line_starts=[ps(5), ps(5) + 0.3], gap=18)
# Scene 4
cap4 = Caption([[("کدام", INK), ("درمان", INK), ("ترند", CORAL), ("پوستی", INK)],
                [("رو", INK), ("امتحان", INK), ("کردی؟", INK)]],
               y=260, size=76, t_in=ps(7), t_out=END + 5,
               line_starts=[ps(7), ps(7) + (pe(7) - ps(7)) * 0.5], gap=18)
CAPS = [cap1, cap2a, cap2b, cap3, cap4]

# hormone chips (2x2)
CHIP_DEF = [("LH", CORAL), ("FSH", MUST), ("تستوسترون", SLATE), ("DHEA-S", TEAL)]
chips = []
for i, (txt, col) in enumerate(CHIP_DEF):
    kind = "Black"
    tim = word_img(txt, INK, 44, kind)
    tb = tim.getchannel("A").getbbox()
    tw = tb[2] - tb[0]
    w, h = max(270, tw + 130), 92
    card, pad = shadow_card(w, h, 46, WHITE)
    d = ImageDraw.Draw(card)
    # colour dot with check
    cx, cy = pad + w - 46, pad + h // 2
    d.ellipse((cx - 24, cy - 24, cx + 24, cy + 24), fill=col + (255,))
    d.line([(cx - 11, cy + 1), (cx - 3, cy + 9), (cx + 12, cy - 9)], fill=WHITE + (255,), width=6, joint="curve")
    tx = pad + (w - 70 - tw) // 2 - tb[0] + 4
    card.alpha_composite(tim, (tx, pad + (h - (tb[3] - tb[1])) // 2 - tb[1]))
    col_i, row_i = i % 2, i // 2
    ccx = W // 2 + (185 if col_i == 0 else -185)   # RTL: first chip on the right
    ccy = 560 + row_i * 120
    chips.append((card, ccx, ccy, ps(5) + 0.75 + 0.28 * i))

# nemonet badge
def make_badge():
    w, h = 720, 150
    card, pad = shadow_card(w, h, 40, WHITE)
    logo = LOGO.resize((106, 106), Image.LANCZOS)
    card.alpha_composite(logo, (pad + w - 106 - 22, pad + 22))
    t1 = word_img("آزمایش هورمونی در خانه", INK, 44, "Black")
    t2 = word_img("نمونت  |  nemonet.ir", TEAL, 34, "Regular")
    b1 = t1.getchannel("A").getbbox(); b2 = t2.getchannel("A").getbbox()
    right = pad + w - 106 - 50
    card.alpha_composite(t1, (right - b1[2], pad + 22 - b1[1]))
    card.alpha_composite(t2, (right - b2[2], pad + 92 - b2[1]))
    return card
BADGE = make_badge()
BADGE_T = ps(6)

def make_bubble():
    txt = word_img("تو کامنت‌ها برام بنویس!", CREAM, 54, "Black")
    tb = txt.getchannel("A").getbbox()
    w, h = (tb[2] - tb[0]) + 90, 120
    im = Image.new("RGBA", (w + 60, h + 70), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((30, 20, 30 + w, 20 + h), 50, fill=SLATE + (255,))
    d.polygon([(30 + w - 120, 20 + h - 2), (30 + w - 70, 20 + h - 2), (30 + w - 60, 20 + h + 42)], fill=SLATE + (255,))
    im_txt = im.copy()
    im_txt.alpha_composite(txt, (30 + 45 - tb[0], 20 + (h - (tb[3] - tb[1])) // 2 - tb[1]))
    return im, im_txt, (30 + w // 2, 20 + h // 2)
BUB_EMPTY, BUB_FULL, BUB_C = make_bubble()
BUB_T = ps(8)

SMALL_LOGO_T = pe(8) + 0.2

SPARKS = {
    "s1": [(1060, 720, CORAL, 1.6), (980, 860, MUST, 1.9), (1180, 640, SLATE, 2.2)],
    "s2": [(980, 1240, CORAL, 1.6), (900, 1080, MUST, 1.9)],
    "s3": [(1010, 1180, MUST, 1.6), (960, 1310, CORAL, 1.9)],
    "s4": [(1000, 1180, CORAL, 1.6), (930, 1330, MUST, 1.9), (1020, 1460, SLATE, 2.2)],
}
# shift sparkle coords for s1 that were set in 1080 space (already fine)
for k in SPARKS:
    SPARKS[k] = [(min(x, 1040), y, c, st) for x, y, c, st in SPARKS[k]]

# ---------- sfx events ----------
for name, s0, s1 in SCENES:
    ev("draw", s0 + 0.05, dur=1.1)
    d_par = np.load(os.path.join(LAY, name + ".npz"))["circ_par"]
    for k in range(len(d_par)):
        ev("pop", s0 + 0.15 * k + 0.05, gain=0.35)
for b, _ in IRIS:
    ev("whoosh", b - 0.28)
ev("ding", ps(2) + 0.45)              # marker on "هدر دادن پوله"
ev("stamp", ps(4) + 0.55)             # موقتیه!
for c in chips:
    ev("pop", c[3], gain=0.7)
ev("ding", BADGE_T)
ev("pop", BUB_T, gain=0.8)

# ---------------- frame render ----------------
def scene_at(t):
    for name, s0, s1 in SCENES:
        if t < s1 or name == "s4":
            return name, s0
    return SCENES[-1][0], SCENES[-1][1]

def render(f):
    t = f / FPS
    name, s0 = scene_at(t)
    tau = t - s0
    img = illus(name, tau)
    z = 1.0 + 0.04 * float(smooth(tau / 6.0))
    if z > 1.0001:
        cw, ch = W / z, H / z
        x0 = 540 - cw / 2; y0 = 1300 - ch * (1300 / H)
        img = img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
    frame = img.convert("RGBA")
    d = ImageDraw.Draw(frame)
    for sx, sy, col, st in SPARKS[name]:
        if tau > st:
            ph = (tau - st) / 0.9
            sparkle(d, sx, sy, float(np.sin(np.pi * (ph % 1.0))), col)

    # scene specific overlays
    if name == "s1":
        pill(frame, "ترند در برابر واقعیت", t, 0.0, B1 - 0.3, 210, SLATE)
        x0, y0, x1 = cap1.bbox({"هدر", "دادن", "پوله؟"})
        marker(frame, x0 + 4, x1 - 4, y0 + 66, t, ps(2) + 0.45)
    elif name == "s2":
        pill(frame, "واقعیت", t, s0 + 0.1, B2 - 0.3, 190, CORAL)
        if t >= ps(4):
            x0, y0, x1 = cap2b.bbox({"موقتیه!"})
            scribble_ellipse(frame, (x0 + x1) / 2, y0 + 92, (x1 - x0) / 2 + 30, 70, t, ps(4) + 0.6)
    elif name == "s3":
        pill(frame, "پنل هورمونی", t, s0 + 0.1, B3 - 0.3, 150, SLATE)
        for card, cx, cy, ct in chips:
            paste_pop(frame, card, cx, cy, t, ct, B3 - 0.3)
        paste_pop(frame, BADGE, W // 2, 1760, t, BADGE_T, B3 - 0.3)
    elif name == "s4":
        p = (t - BUB_T)
        if p > 0:
            bub = BUB_EMPTY.copy() if p < 0.45 else BUB_FULL
            if p < 0.45:
                dd = ImageDraw.Draw(bub)
                for k in range(3):
                    ph = (p * 6 - k * 0.6)
                    yo = -10 * max(0.0, np.sin(ph)) if ph > 0 else 0
                    cx = BUB_C[0] + (k - 1) * 36
                    dd.ellipse((cx - 10, BUB_C[1] - 10 + yo, cx + 10, BUB_C[1] + 10 + yo), fill=CREAM + (255,))
            paste_pop(frame, bub, W // 2, 630, t, BUB_T)
        if t > SMALL_LOGO_T:
            paste_pop(frame, BADGE, W // 2, 1760, t, SMALL_LOGO_T)

    for c in CAPS:
        c.draw(frame, t)

    # iris transitions
    for b, col in IRIS:
        if b - 0.28 <= t <= b + 0.3:
            if t < b:
                r = 1300 * float(smooth((t - (b - 0.28)) / 0.28))
            else:
                r = 1300 * (1 - float(smooth((t - b) / 0.3)))
            if r > 1:
                ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(ov).ellipse((540 - r, 1100 - r, 540 + r, 1100 + r), fill=col + (255,))
                frame.alpha_composite(ov)
    frame.convert("RGB").save(os.path.join(OUTD, "%04d.png" % f))

if __name__ == "__main__":
    os.makedirs(OUTD, exist_ok=True)
    N = int(round(END * FPS))
    a = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    b = int(sys.argv[6]) if len(sys.argv) > 6 else N
    if a == 0:
        json.dump(dict(events=SFX, frames=N, scenes=SCENES), open(os.path.join(OUTD, "..", "events.json"), "w"), ensure_ascii=False, indent=1)
    for f in range(a, min(b, N)):
        render(f)
    print("rendered", a, min(b, N))
