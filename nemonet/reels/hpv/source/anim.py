"""Nemonet — HPV reel. Every frame drawn in code, animated on twos at 24fps (rendered at 12 drawings/s)."""
import json, math, os, sys
from multiprocessing import Pool
from chars import *

HERE = os.path.dirname(os.path.abspath(__file__))
TIM = json.load(open(os.path.join(HERE, "timing.json")))
_s = TIM["scenes"]; SC = [(_s[i], _s[i + 1]) for i in range(6)]
CROSS = TIM["cross"]; SUBS = TIM["subs"]
OUT = os.environ.get("FRAMES", "/home/claude/hpv_frames")
DUR, DRAW_FPS = 20.0, 12


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eob(x, s=1.9): x = clamp(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def pop(u, start, dur=0.35): return eob((u - start) / dur) if u >= start else 0.0


def scaled(c, x, y, k):
    """Draw following content scaled by k around (x, y)."""
    c.push(x * (1 - k), y * (1 - k), k)


def partial(pts, k):
    if k <= 0: return None
    d = densify(pts, 3); return d[:max(2, int(len(d) * clamp(k)))]


# ---------------------------------------------------------------- shared pieces
def hook_text(c, t):
    c.text((540, 300), "۳ تا چیزی که درباره‌ی", "Bold", 84, "ink")
    k = 1 + 0.04 * math.sin(t * 5)
    c.text_s((540, 435), "HPV", "Bold", 132, "orange", scale=k)
    underline_scribble(c, 540, 515, c.text_w("HPV", "Bold", 132) + 120, "mustard")
    c.text((540, 600), "اشتباه فکر می‌کنی", "Bold", 84, "ink")
    c.text((540, 690), "(ویروس عامل زگیل تناسلی)", "Regular", 54, "purple_d")


def myth_header(c, u, uc, n, myth, truth):
    k = pop(u, 0.0, 0.3)
    if k:
        scaled(c, 540, 290, k)
        c.fill(rrect(400, 250, 680, 330, 40), "purple_d", hatch=0.4, outline=4)
        c.text((540, 290), f"باور غلط {n}", "Bold", 40, "paper"); c.pop()
    w = c.text_w(myth, "Bold", 74)
    c.text_s((540, 440), myth, "Bold", 74, "ink" if u < uc else "grey", scale=pop(u, 0.12, 0.3))
    p = partial([(540 + w / 2 + 20, 438), (540 - w / 2 - 20, 446)], (u - uc) / 0.3)
    if p: c.line(p, 6, "orange", 1.2)
    kx = pop(u, uc + 0.25, 0.25)
    if kx:
        scaled(c, 540 + w / 2 + 70, 442, kx); xmark(c, 540 + w / 2 + 70, 442, 20); c.pop()
    kt = pop(u, uc + 0.1, 0.35)
    c.text_s((540, 590), truth, "Bold", 92, "teal", scale=kt)
    tw = c.text_w(truth, "Bold", 92)
    p = partial([(540 + tw / 2 + 30, 590), (540 + tw / 2 + 51, 611), (540 + tw / 2 + 90, 566)], (u - uc - 0.35) / 0.25)
    if p: c.line(p, 9, "teal", 0.8)


def subtitle(c, t):
    cur = None
    for i, (st, txt) in enumerate(SUBS):
        if t >= st - 0.05: cur = (i, st, txt)
    if not cur: return
    i, st, txt = cur
    size = 48
    lines = [txt]
    if c.text_w(txt, "Bold", size) > 900:
        words = txt.split(); half = len(words) // 2
        lines = [" ".join(words[:half]), " ".join(words[half:])]
    w = max(c.text_w(l, "Bold", size) for l in lines) + 70
    h = 58 * len(lines) + 34
    y0 = 1585 - h
    k = 0.85 + 0.15 * eob((t - st + 0.05) / 0.2)
    scaled(c, 540, y0 + h / 2, k)
    c.fill(rrect(540 - w / 2 + 8, y0 + 8, 540 + w / 2 + 8, y0 + h + 8, 26), "purple_d", hatch=0.3, outline=0)
    c.fill(rrect(540 - w / 2, y0, 540 + w / 2, y0 + h, 26), "paper", hatch=0, outline=4)
    for j, l in enumerate(lines):
        c.text_s((540, y0 + 17 + 29 + j * 58), l, "Bold", size, "ink")
    c.pop()


# ---------------------------------------------------------------- scenes
def s1(c, u, t):
    deco(c, [(140, 760, 60, 50), (960, 1420, 50, 70), (110, 1380, 40, 40)])
    hook_text(c, t)
    cards = [(210, 950, 150, 200, -12, "mustard"), (870, 920, 150, 200, 10, "orange"), (860, 1210, 120, 160, -6, "purple")]
    for i, (x, y, w, h, tl, col) in enumerate(cards):
        k = pop(u, -0.25 + i * 0.12, 0.35)
        if k:
            yy = y + 10 * math.sin(t * 3 + i * 2)
            scaled(c, x, yy, k); qmark_card(c, x, yy, w, h, tl + 4 * math.sin(t * 2.4 + i), col); c.pop()
    man(c, 540, 1100, "confused", tilt=-5 + 2.5 * math.sin(t * 2.6), shirt_bottom=1640)
    for (x, y, sz, col, ph) in ((380, 850, 70, "purple_d", 0), (330, 930, 46, "orange", 1.5)):
        c.text((x, y + 8 * math.sin(t * 4 + ph)), "؟", "Bold", sz, col)


def s2(c, u, t):
    uc = CROSS[0] - SC[1][0]
    myth_header(c, u, uc, "۱", "نادره", "خیلی رایجه!")
    cols = ["purple", "orange", "mustard", "purple_d", "teal", "orange"]
    i = 0
    for r, y in enumerate((800, 1050, 1300)):
        xs = (170, 355, 540, 725, 910) if r % 2 == 0 else (262, 447, 632, 817)
        for x in xs:
            k = pop(u, 0.2 + i * 0.05, 0.3)
            if k:
                yy = y + 6 * math.sin(t * 5 + i)
                scaled(c, x, yy, k)
                mini_person(c, x, yy, 1.55, cols[i % 6], scarf="mustard" if i % 3 == 1 else None)
                c.pop()
            if i % 4 != 3:
                kv = pop(u, uc + 0.25 + i * 0.04, 0.3)
                if kv:
                    vx, vy = x + 53, y - 40 + 6 * math.sin(t * 5 + i)
                    scaled(c, vx, vy, kv); virus(c, vx, vy, 20, "sly", knobs=8, spin=t * 60 + i * 20); c.pop()
            i += 1
    c.plus(80, 760, 40, 40); c.plus(1000, 1300, 40, 60)


def s3(c, u, t):
    uc = CROSS[1] - SC[2][0]
    myth_header(c, u, uc, "۲", "فقط مال خانم‌هاست", "آقایون هم می‌گیرن")
    dl = -650 * (1 - eo(u / 0.45)); dr = 650 * (1 - eo((u - 0.1) / 0.45))
    c.push(dl, 0, 1); woman(c, 320, 1050, "neutral", tilt=-3 + 2 * math.sin(t * 2), shirt_bottom=1640); c.pop()
    c.push(dr, 0, 1); man(c, 770, 1050, "surprised" if u > uc else "neutral", tilt=4 + 2 * math.sin(t * 2 + 1), shirt_bottom=1640); c.pop()
    for i, (x, y) in enumerate(((120, 880), (975, 860))):
        k = pop(u, uc + 0.2 + i * 0.12, 0.35)
        if k:
            yy = y + 8 * math.sin(t * 4 + i)
            scaled(c, x, yy, k); virus(c, x, yy, 48, "sly", spin=t * 40 + i * 30); c.pop()
    c.text_s((540, 820), "=", "Bold", 120, "purple_d", scale=pop(u, uc + 0.45, 0.3))
    deco(c, [(120, 1500, 40, 40), (990, 1520, 40, 50)])


def s4(c, u, t):
    uc = CROSS[2] - SC[3][0]
    myth_header(c, u, uc, "۳", "حتماً علامت داره", "اغلب بی‌علامته")
    vx = 700 + 130 * eo((u - 0.4) / 0.5)
    virus(c, vx + 6 * math.sin(t * 6), 1190 + 8 * math.sin(t * 4), 78, "sly", spin=t * 30)
    man(c, 560, 1080, "happy", tilt=3 + 1.5 * math.sin(t * 2), shirt_bottom=1640)
    sip = 30 * max(0, math.sin(t * 2.2)) ** 3
    limb(c, [(340, 1640), (330, 1520), (400, 1440 - sip)], 50)
    c.fill([(380, 1350 - sip), (480, 1350 - sip), (470, 1460 - sip), (390, 1460 - sip)], "orange", hatch=0.5, outline=4)
    c.line(ellipse(490, 1400 - sip, 22, 26, 30, -90, 90), 4.5, "ink", 0.5)
    c.fill(ellipse(400, 1440 - sip, 34, 28), "skin", hatch=0, outline=4)
    for i in range(2):
        o = 10 * math.sin(t * 3 + i)
        c.line(bez((405 + i * 35 + o, 1330 - sip), (390 + i * 35, 1300 - sip), (415 + i * 35, 1280 - sip), (400 + i * 35 + o, 1255 - sip)), 3, "grey", 0.6)
    c.text_s((870, 1060), "هیس!", "Bold", 48, "purple_d", scale=pop(u, uc + 0.35, 0.3))
    deco(c, [(150, 860, 50, 50), (1000, 1520, 40, 50)])


def s5(c, u, t):
    c.text_s((540, 330), "پس بهترین کار:", "Regular", 60, "purple_d", scale=pop(u, 0.0, 0.3))
    c.text_s((540, 450), "غربالگری = خیال راحت", "Bold", 88, "ink", scale=pop(u, 0.15, 0.35))
    if u > 0.45: underline_scribble(c, 540, 520, 560 * eo((u - 0.45) / 0.3), "teal")
    c.line([(70, 1640), (70, 720), (470, 720), (470, 1640)], 5, "ink", 1)
    c.fill(rrect(90, 740, 450, 1640, 6), "mustard", hatch=0.35, outline=3.5)
    c.fill(ellipse(410, 1200, 14, 14), "ink", hatch=0, outline=0)
    k = pop(u, 0.1, 0.4)
    if k:
        scaled(c, 300, 1640, k)
        woman(c, 300, 1050, "happy", shirt_bottom=1640, scarf="purple_d", coat=True)
        wave = 6 * math.sin(t * 5)
        limb(c, [(500, 1450), (560, 1310), (590 + wave, 1190)], 48, "teal")
        test_tube(c, 600 + wave, 990, h=200, w=54, tilt=10 + 3 * math.sin(t * 5))
        c.fill(ellipse(592 + wave, 1180, 34, 30), "skin", hatch=0, outline=4)
        c.pop()
    dx = 500 * (1 - eo((u - 0.3) / 0.45))
    c.push(dx, 0, 1); man(c, 840, 1100, "happy", tilt=-3 + 2 * math.sin(t * 2.5), shirt_bottom=1640); c.pop()
    km = pop(u, 1.0, 0.35)
    if km:
        my = 800 + 6 * math.sin(t * 4)
        scaled(c, 960, my, km)
        virus(c, 960, my, 40, "caught", spin=12)
        c.line(ellipse(960, my, 66, 66), 6, "ink", 0.6); c.line([(1006, my + 46), (1040, my + 100)], 10, "ink", 0.4)
        c.pop()


def s6(c, u, t):
    deco(c, [(140, 700, 60, 50), (960, 1000, 50, 70)])
    c.text_s((540, 320), "نمونت؛", "Bold", 110, "teal", scale=pop(u, 0.0, 0.35))
    c.text_s((540, 465), "آزمایش در منزل", "Bold", 104, "ink", scale=pop(u, 0.15, 0.35))
    if u > 0.5: underline_scribble(c, 540, 545, 520 * eo((u - 0.5) / 0.3), "mustard")
    for i, (x, y, s) in enumerate(((200, 760, 26), (900, 720, 22), (170, 1060, 18), (930, 1080, 20))):
        ss = s * (0.6 + 0.4 * abs(math.sin(t * 3 + i)))
        c.line([(x - ss, y), (x + ss, y)], 4, "mustard", 0.3); c.line([(x, y - ss), (x, y + ss)], 4, "mustard", 0.3)
    k = pop(u, 0.1, 0.4)
    if k:
        scaled(c, 540, 1180, k); man(c, 540, 840, "happy", tilt=3 + 2 * math.sin(t * 2.5), shirt_bottom=1180); c.pop()
    dy = 450 * (1 - eo((u - 0.3) / 0.45))
    c.push(0, dy, 1)
    card(c, 70, 1150, 1010, 1420)
    logo = Image.open(LOGO).convert("RGBA").resize((130 * S, 130 * S), Image.LANCZOS)
    c.paste(logo, (850, 1172 + dy))
    c.text((830, 1215 + dy), "نمونت", "Bold", 58, "teal", anchor="rm")
    c.d.text((830 * S, (1275 + dy) * S), "nemonet.ir", font=font("Regular", 38), fill=PAL["purple_d"], anchor="rm")
    c.text((330, 1235 + dy), "بیش از ۵۰۰۰ آزمایش", "Bold", 40, "purple_d")
    kb = 1 + 0.04 * math.sin(t * 6)
    scaled(c, 540, 1355, kb)
    c.fill(rrect(130, 1315, 950, 1395, 40), "orange", hatch=0.45, outline=4.5)
    c.text((540, 1355), "همین حالا نوبت بگیر", "Bold", 44, "paper")
    c.pop(); c.pop()


SCENES = [s1, s2, s3, s4, s5, s6]


def frame(i):
    t = i / DRAW_FPS
    c = Canvas(seed=1000 + i)          # new seed each drawing = line boil on twos
    for k, (a, b) in enumerate(SC):
        if a <= t < b or (k == 5 and t >= a):
            SCENES[k](c, t - a, t); break
    subtitle(c, t)
    c.finish(os.path.join(OUT, f"f{i:04d}.png"))
    return i


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if len(sys.argv) > 1:
        for a in sys.argv[1:]:
            frame(int(round(float(a) * DRAW_FPS))); print("t", a)
    else:
        n = int(DUR * DRAW_FPS)
        todo = [i for i in range(n) if not os.path.exists(os.path.join(OUT, f"f{i:04d}.png"))]
        with Pool(2) as p:
            for i in p.imap_unordered(frame, todo): pass
        print("done", n)
