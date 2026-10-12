"""Hand-drawn pencil-style drawing helpers (PIL), rendered at 2x then downsampled."""
import math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

S = 2  # supersample
W, H = 1080 * S, 1920 * S

PAL = dict(
    paper=(249, 243, 230), ink=(38, 36, 44), purple=(103, 100, 140), purple_d=(78, 75, 112),
    orange=(238, 117, 92), mustard=(244, 182, 76), skin=(250, 242, 228), grey=(150, 146, 150),
    teal=(22, 122, 128), hair=(40, 38, 46),
)
FONT_DIR = "/home/claude/reel/vazir/fonts/ttf/"


def font(weight, size):
    return ImageFont.truetype(FONT_DIR + f"Vazirmatn-{weight}.ttf", int(size * S),
                              layout_engine=ImageFont.Layout.RAQM)


def P(pts):
    return [(x * S, y * S) for x, y in pts]


def rot(pts, ang, cx, cy):
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def densify(pts, step=6):
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        for i in range(n):
            t = i / n; out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    out.append(pts[-1]); return out


def wob(pts, amp=1.6, seed=0, freq=0.05):
    """Low-frequency jitter so lines feel hand-drawn (coords in 1x units)."""
    r = random.Random(seed); ph1, ph2 = r.random() * 9, r.random() * 9
    d = densify(pts); out = []; acc = 0
    for i, (x, y) in enumerate(d):
        if i: acc += math.hypot(x - d[i - 1][0], y - d[i - 1][1])
        out.append((x + amp * math.sin(acc * freq + ph1), y + amp * math.sin(acc * freq * 1.3 + ph2)))
    return out


def ellipse(cx, cy, rx, ry, n=90, a0=0, a1=360):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def rrect(x0, y0, x1, y1, r, n=10):
    pts = []
    for cx, cy, a in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        pts += [(cx + r * math.cos(math.radians(a + 90 * i / n)), cy + r * math.sin(math.radians(a + 90 * i / n))) for i in range(n + 1)]
    return pts + [pts[0]]


def bez(p0, p1, p2, p3=None, n=30):
    out = []
    for i in range(n + 1):
        t = i / n
        if p3 is None:
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        else:
            x = (1-t)**3*p0[0] + 3*(1-t)**2*t*p1[0] + 3*(1-t)*t*t*p2[0] + t**3*p3[0]
            y = (1-t)**3*p0[1] + 3*(1-t)**2*t*p1[1] + 3*(1-t)*t*t*p2[1] + t**3*p3[1]
        out.append((x, y))
    return out


class Canvas:
    def __init__(self, seed=1):
        self.img = Image.new("RGB", (W, H), PAL["paper"]); self.d = ImageDraw.Draw(self.img)
        self.seed = seed; self.r = random.Random(seed); self.xf = (0, 0, 1)

    def T(self, pts):
        ox, oy, k = self.xf
        return [(ox + x * k, oy + y * k) for x, y in pts]

    def push(self, ox, oy, k):
        """Place following drawing: (x,y) -> (ox + x*k, oy + y*k), composed with current."""
        self.stack = getattr(self, "stack", []); self.stack.append(self.xf)
        a, b, s = self.xf; self.xf = (a + ox * s, b + oy * s, s * k)

    def pop(self):
        st = getattr(self, "stack", [])
        self.xf = st.pop() if st else (0, 0, 1)

    def line(self, pts, w=4, col="ink", amp=1.4, closed=False):
        if closed: pts = pts + [pts[0]]
        w = w * self.xf[2]
        p = P(self.T(wob(pts, amp, self.r.randint(0, 9999))))
        c = PAL.get(col, col) if isinstance(col, str) else col
        self.d.line(p, fill=c, width=int(w * S), joint="curve")
        for x, y in (p[0], p[-1]):
            rr = w * S / 2; self.d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=c)

    def fill(self, pts, col, hatch=0.55, angle=62, spacing=7, outline=4, amp=1.4, shade=None):
        c = PAL.get(col, col) if isinstance(col, str) else col
        mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).polygon(P(self.T(wob(pts + [pts[0]], amp * 0.6, 7))), fill=255)
        layer = Image.new("RGB", (W, H), c)
        if hatch:
            ld = ImageDraw.Draw(layer)
            dk = shade or tuple(max(0, int(v * 0.8)) for v in c)
            lt = tuple(min(255, int(v + (255 - v) * 0.35)) for v in c)
            bb = mask.getbbox()
            if bb:
                x0, y0, x1, y1 = bb; a = math.radians(angle); L = (x1 - x0) + (y1 - y0)
                k = -L
                while k < L:
                    k += spacing * S * (0.6 + self.r.random() * 0.8)
                    cx, cy = (x0 + x1) / 2 + k * math.cos(a + math.pi / 2), (y0 + y1) / 2 + k * math.sin(a + math.pi / 2)
                    ln = L * (0.3 + self.r.random() * 0.7); off = self.r.uniform(-L / 3, L / 3)
                    p0 = (cx + (off - ln / 2) * math.cos(a), cy + (off - ln / 2) * math.sin(a))
                    p1 = (cx + (off + ln / 2) * math.cos(a), cy + (off + ln / 2) * math.sin(a))
                    colr = dk if self.r.random() < hatch else lt
                    ld.line([p0, p1], fill=colr, width=max(1, int(S * self.r.uniform(0.8, 1.8))))
            layer = layer.filter(ImageFilter.GaussianBlur(0.6 * S))
        self.img.paste(layer, (0, 0), mask)
        if outline: self.line(pts, outline, "ink", amp, closed=True)

    def text_s(self, xy, s, weight, size, col, anchor="mm", scale=1.0, rtl=True):
        if scale <= 0.02: return
        c = PAL.get(col, col) if isinstance(col, str) else col
        (x, y), = self.T([xy]); sz = max(1, size * scale * self.xf[2])
        kw = dict(direction="rtl", language="fa") if rtl else {}
        self.d.text((x * S, y * S), s, font=font(weight, sz), fill=c, anchor=anchor, **kw)

    def text(self, xy, s, weight="ExtraBold", size=100, col="ink", anchor="mm"):
        c = PAL.get(col, col) if isinstance(col, str) else col
        self.d.text((xy[0] * S, xy[1] * S), s, font=font(weight, size), fill=c, anchor=anchor,
                    direction="rtl", language="fa")

    def text_w(self, s, weight, size):
        return font(weight, size).getlength(s, direction="rtl", language="fa") / S

    def plus(self, x, y, h, v, col="grey", w=2):
        self.line([(x - h, y), (x + h, y)], w, col, 0.5); self.line([(x, y - v), (x, y + v)], w, col, 0.5)

    def paste(self, im, xy):
        self.img.paste(im, (int(xy[0] * S), int(xy[1] * S)), im if im.mode == "RGBA" else None)

    def finish(self, path=None):
        out = self.img.resize((1080, 1920), Image.LANCZOS)
        noise = Image.effect_noise((1080, 1920), 18).convert("RGB")
        out = ImageChops.blend(out, ImageChops.multiply(out, noise.point(lambda v: 200 + v // 5)), 0.35)
        if path: out.save(path)
        return out
