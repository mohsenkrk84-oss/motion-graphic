"""Nemonet — Vitamin D reel. Every frame drawn in code, animated on twos at 24fps."""
import math, os, sys
from multiprocessing import Pool
from PIL import Image
from lib import *
from frames import character, limb, phone, desk, underline_scribble, battery

FPS = 24
DUR = 20.0
import json as _j
TIM = _j.load(open("/home/claude/reel/timing.json"))
_s = TIM["scenes"]
SC = [(_s[i], _s[i + 1]) for i in range(6)]
OUT = "/home/claude/reel/frames_out"


# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eob(x, s=1.9):
    x = clamp(x); x -= 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def pop(u, start, dur=0.35): return eob((u - start) / dur) if u >= start else 0.0


def partial(pts, k):
    """First fraction k of a polyline (for draw-on strokes)."""
    if k <= 0: return None
    d = densify(pts, 3); n = max(2, int(len(d) * clamp(k)))
    return d[:n]


def deco(c, marks):
    for m in marks: c.plus(*m)


def headline(c, lines, u, t0=0.0, base_y=300, gap=125):
    for i, (txt, size, col) in enumerate(lines):
        k = pop(u, t0 + i * 0.18, 0.35)
        c.text_s((540, base_y + i * gap), txt, "Black", size, col, scale=k)


def check_mark(c, x, y, k, col="teal", s=1.0):
    p = partial([(x - 28 * s, y), (x - 8 * s, y + 24 * s), (x + 34 * s, y - 30 * s)], k)
    if p: c.line(p, 9 * s, col, 0.4)


def sun(c, x, y, r, spin, glasses=False):
    for i in range(12):
        a = math.radians(spin + i * 30); r0, r1 = r + 18, r + (48 if i % 2 else 34)
        c.line([(x + r0 * math.cos(a), y + r0 * math.sin(a)), (x + r1 * math.cos(a), y + r1 * math.sin(a))], 5, "mustard", 0.4)
    c.fill(ellipse(x, y, r, r), "mustard", hatch=0.5, outline=4.5)
    if glasses:
        for sx in (-1, 1):
            c.fill(rrect(x + sx * r * 0.42 - 26, y - 14, x + sx * r * 0.42 + 26, y + 20, 12), "ink", hatch=0.2, outline=3)
        c.line([(x - 10, y - 4), (x + 10, y - 4)], 4, "ink", 0.2)
        c.line(bez((x - 26, y + r * 0.45), (x, y + r * 0.62), (x + 26, y + r * 0.45)), 4.5, "ink", 0.3)
    else:
        c.text_s((x, y + 2), "D", "Black", r * 1.2, "ink", rtl=False)


def sampler(c, cx, cy, tube_fill=0.0, arm_up=1.0):
    """Nemonet home-sampling nurse: hijab, teal coat, test tube."""
    c.fill([(cx - 150, cy + 30), (cx - 165, cy - 70), (cx - 120, cy - 150), (cx, cy - 180), (cx + 120, cy - 150),
            (cx + 165, cy - 70), (cx + 150, cy + 30), (cx + 175, cy + 190), (cx - 175, cy + 190)], "purple_d", hatch=0.5, angle=40, spacing=5)
    sh = cy + 190
    coat = [(cx - 230, 1500), (cx - 245, sh + 120), (cx - 190, sh + 20), (cx - 100, sh - 10), (cx + 100, sh - 10),
            (cx + 190, sh + 20), (cx + 245, sh + 120), (cx + 230, 1500)]
    c.fill(coat, "teal", hatch=0.5, angle=70, spacing=5)
    c.fill([(cx - 120, cy + 120), (cx, cy + 230), (cx + 120, cy + 120), (cx + 130, sh + 10), (cx - 130, sh + 10)], "purple_d", hatch=0.5, angle=40, spacing=5)
    c.line([(cx, sh + 40), (cx, 1500)], 3.5, "ink", 0.8)
    c.fill(rrect(cx + 60, sh + 120, cx + 160, sh + 160, 8), "paper", hatch=0, outline=3)  # badge
    c.fill(ellipse(cx, cy + 5, 100, 120), "skin", hatch=0, outline=4.5)
    c.fill([(cx - 112, cy - 10), (cx - 95, cy - 95), (cx, cy - 132), (cx + 95, cy - 95), (cx + 112, cy - 10),
            (cx + 88, cy - 52), (cx, cy - 78), (cx - 88, cy - 52)], "purple_d", hatch=0.5, angle=40, spacing=5)
    for sx in (-1, 1):
        c.fill(ellipse(cx + sx * 40, cy + 10, 9, 12), "ink", hatch=0, outline=0)
        c.line(bez((cx + sx * 40 - 18, cy - 22), (cx + sx * 40, cy - 30), (cx + sx * 40 + 18, cy - 22)), 4, "ink", 0.3)
        c.fill(ellipse(cx + sx * 66, cy + 52, 14, 8), (247, 196, 176), hatch=0, outline=0)
    c.line(bez((cx + 2, cy + 26), (cx - 8, cy + 50), (cx + 8, cy + 54)), 3.5, "ink", 0.3)
    c.line(bez((cx - 30, cy + 74), (cx, cy + 98), (cx + 30, cy + 74)), 4.5, "ink", 0.4)
    # arm holding tube
    hx, hy = cx - 300, cy + 260 - 120 * arm_up
    limb(c, [(cx - 215, sh + 140), (cx - 270, sh + 90), (hx + 10, hy + 40)], 50, "teal")
    tx, ty = hx - 18, hy - 150
    c.fill(rrect(tx, ty + 30, tx + 46, ty + 200, 22), "paper", hatch=0, outline=4)
    if tube_fill > 0:
        top = ty + 200 - 160 * tube_fill
        c.fill(rrect(tx + 8, top, tx + 38, ty + 192, 14), "orange", hatch=0.5, outline=0)
    c.fill(rrect(tx - 6, ty + 6, tx + 52, ty + 40, 8), "purple", hatch=0.5, outline=3.5)
    c.fill(ellipse(hx + 10, hy + 40, 34, 30), "skin", hatch=0, outline=4)


# ---------- scenes ----------
def s1(c, u):
    deco(c, [(860, 640, 120, 110), (220, 1040, 90, 70), (900, 1120, 60, 60)])
    c.line([(150, 680), (215, 610), (280, 680)], 3.5, "ink", 0.8)
    c.fill(ellipse(215, 610, 7, 7), "mustard", hatch=0, outline=0)
    c.fill(rrect(110, 680, 320, 840, 14), "paper", hatch=0, outline=4)
    c.fill(rrect(130, 698, 300, 822, 4), "orange", hatch=0.4, outline=3)
    c.fill(rrect(146, 712, 284, 808, 3), "paper", hatch=0, outline=2.5)
    c.line([(170, 780), (190, 735), (205, 785), (225, 735), (240, 785), (260, 740)], 4, "mustard", 1.2)
    nod = -4 - 5 * eo(u / 1.2) - 2.5 * math.sin(u * 5)
    character(c, 560, 930 + 6 * eo(u / 1.2), "tired", tilt=nod, shirt_bottom=1362)
    # Z's appear one by one
    for i, (dx, dy, s, t0) in enumerate(((0, 0, 34, 0.5), (46, -58, 46, 0.9), (100, -130, 60, 1.3))):
        k = pop(u, t0, 0.3)
        if k > 0:
            X, Y = 720 + dx, 720 + dy - 12 * math.sin(u * 3 + i); S2 = s * k
            c.line([(X, Y), (X + S2, Y), (X, Y + S2), (X + S2, Y + S2)], 4.5, "purple_d", 0.8)
    desk(c, 1360)
    ringing = u < 1.9
    jx = 7 * math.sin(u * 90) if ringing else 0
    phone(c, 140 + jx, 1170, ringing=ringing)
    press = eo((u - 1.5) / 0.35)
    limb(c, [(330, 1300), (300, 1330), (230 + 0 * press, 1334 - 30 * press)], 50)
    c.fill(ellipse(222, 1318 - 40 * press, 34, 26), "skin", hatch=0, outline=4)
    limb(c, [(790, 1300), (820, 1334), (880, 1336)], 50)
    c.fill(ellipse(884, 1322, 30, 26), "skin", hatch=0, outline=4)
    c.fill([(880, 1255), (980, 1255), (970, 1360), (890, 1360)], "orange", hatch=0.5, outline=4)
    c.line(ellipse(990, 1300, 22, 26, 30, -90, 90), 4.5, "ink", 0.5)
    for i in range(2):
        o = 8 * math.sin(u * 4 + i)
        c.line(bez((905 + i * 35 + o, 1235), (890 + i * 35, 1205), (915 + i * 35 + o, 1185), (900 + i * 35, 1160)), 3, "grey", 0.6)
    # headline visible from frame 0 (no empty first frame)
    k = 0.88 + 0.12 * eob(u / 0.3)
    c.text_s((540, 300), "همیشه خسته‌ای؟", "Black", 118, "ink", scale=k)
    p = partial([(540 - 260 + 520 * i / 40, 385 + 8 * math.sin(i / 40 * math.pi * 3)) for i in range(41)], eo(u / 0.5))
    if p: c.line(p, 7, "orange", 1.5)
    c.text_s((540, 470), "حتی وقتی کامل خوابیدی؟", "Bold", 52, "purple_d", scale=pop(u, TIM["s1_sub"]))


def s2(c, u):
    deco(c, [(150, 700, 90, 80), (930, 760, 70, 90), (880, 1380, 60, 60)])
    # tired character, smaller, bottom right
    c.push(413, 473, 0.62); character(c, 560, 930, "tired", tilt=-6 - 2 * math.sin(u * 4), shirt_bottom=1700); c.pop()
    c.fill(rrect(520, 1520, 1060, 1564, 6), "paper", hatch=0, outline=4.5)
    c.line([(540, 1542), (1040, 1542)], 3, "purple", 0.6)
    c.line([(600, 1564), (560, 1920)], 3.5, "ink", 1); c.line([(980, 1564), (1010, 1920)], 3.5, "ink", 1)
    k = eob(u / 0.5)
    by = 820 + 620 * (1 - k)
    blink = (int(u * 4) % 2 == 0)
    c.push(0, by - 820, 1)
    battery(c, 150, 860, 260, 460, 1 if blink else 0, "orange")
    if not blink:
        c.line(rrect(172, 1238, 388, 1298, 14), 3, "orange", 0.5)
    sun(c, 280, 735, 60, 0)
    c.pop()
    # warning sparks
    if u > 0.55:
        for i, (x, y) in enumerate(((450, 980), (470, 1080), (440, 1180))):
            if int(u * 8 + i) % 3: c.line([(x, y), (x + 40, y - 10 + 20 * (i - 1))], 5, "orange", 0.3)
    headline(c, [("شاید باتری", 98, "ink"), ("ویتامین D بدنت خالیه!", 92, "orange")], u, 0.1, 290, 120)


def bone(c, x, y):
    c.fill(rrect(x - 50, y - 13, x + 50, y + 13, 8), "paper", hatch=0, outline=0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            c.fill(ellipse(x + sx * 54, y + sy * 14, 18, 18), "paper", hatch=0, outline=4)
    c.fill(rrect(x - 52, y - 13, x + 52, y + 13, 8), "paper", hatch=0, outline=0)
    c.line([(x - 50, y - 13), (x + 50, y - 13)], 4, "ink", 0.3); c.line([(x - 50, y + 13), (x + 50, y + 13)], 4, "ink", 0.3)


def dumbbell(c, x, y):
    c.fill(rrect(x - 55, y - 8, x + 55, y + 8, 4), "grey", hatch=0.4, outline=3.5)
    for sx in (-1, 1):
        c.fill(rrect(x + sx * 58 - 14, y - 38, x + sx * 58 + 14, y + 38, 8), "purple", hatch=0.5, outline=4)


def mini_batt(c, x, y):
    c.fill(rrect(x - 40, y - 60, x + 40, y + 60, 14), "paper", hatch=0, outline=4)
    c.fill(rrect(x - 16, y - 74, x + 16, y - 60, 4), "ink", hatch=0, outline=0)
    c.fill(rrect(x - 26, y + 18, x + 26, y + 46, 8), "orange", hatch=0.5, outline=3)


def s3(c, u):
    deco(c, [(120, 560, 70, 60), (960, 1470, 80, 70)])
    headline(c, [("نشونه‌های کمبود", 96, "ink")], u, 0.0, 300)
    p = partial([(300 + 480 * i / 40, 385 + 7 * math.sin(i / 40 * math.pi * 3)) for i in range(41)], eo((u - 0.2) / 0.5))
    if p: c.line(p, 7, "mustard", 1.5)
    items = [("خستگی مداوم", mini_batt, "orange", TIM["s3_cards"][0] - 0.25), ("درد استخوان و عضله", bone, "mustard", TIM["s3_cards"][1] - 0.25), ("ضعف عضلانی", dumbbell, "purple", TIM["s3_cards"][2] - 0.25)]
    for i, (txt, icon, col, t0) in enumerate(items):
        if u < t0: continue
        k = eob((u - t0) / 0.45, 1.4); dx = 900 * (1 - k)
        y = 600 + i * 270
        c.push(dx, 0, 1)
        c.fill(rrect(90, y, 990, y + 210, 36), "paper", hatch=0, outline=5)
        c.fill(rrect(840, y + 30, 960, y + 180, 26), col, hatch=0.5, outline=4)
        icon(c, 900, y + 105)
        c.text_s((810, y + 105), txt, "Black", 56, "ink", anchor="rm")
        c.fill(ellipse(175, y + 105, 52, 52), "paper", hatch=0, outline=4)
        check_mark(c, 178, y + 108, eo((u - t0 - 0.45) / 0.35))
        c.pop()


def s4(c, u):
    deco(c, [(140, 1300, 70, 60), (960, 560, 60, 80)])
    # window
    c.fill(rrect(160, 560, 920, 1150, 16), (238, 233, 220), hatch=0.15, outline=5.5)
    sun(c, 540 + 10 * math.sin(u * 2), 760, 95, u * 40, glasses=True)
    c.line([(540, 560), (540, 1150)], 7, "ink", 0.8); c.line([(160, 870), (920, 870)], 7, "ink", 0.8)
    c.fill(rrect(130, 1150, 950, 1185, 6), "paper", hatch=0, outline=4.5)
    # rays hit glass and bounce back
    for i, ox in enumerate((-180, 0, 180)):
        ph = (u * 1.4 + i * 0.33) % 1.0
        if ph < 0.5:
            y0 = 860 + 300 * (ph / 0.5); c.line([(540 + ox, y0 - 60), (540 + ox, y0)], 5, "mustard", 0.3)
        else:
            q = (ph - 0.5) / 0.5; y0 = 1160 - 300 * q
            c.line([(540 + ox + 40 * q, y0), (540 + ox + 60 * q, y0 - 60)], 5, "orange", 0.3)
        if 0.45 < ph < 0.6:
            c.line([(520 + ox, 1140), (560 + ox, 1140)], 4, "orange", 0.2); c.line([(540 + ox, 1120), (540 + ox, 1160)], 4, "orange", 0.2)
    # character inside, below window
    c.push(170, 700, 0.66); character(c, 560, 930, "tired", tilt=-5 - 2 * math.sin(u * 3), shirt_bottom=1430); c.pop()
    c.fill(rrect(40, 1640, 1040, 1684, 6), "paper", hatch=0, outline=4.5)
    c.line([(60, 1662), (1020, 1662)], 3, "purple", 0.6)
    headline(c, [("حتی تو کشور آفتابی هم", 84, "ink"), ("کمبودش خیلی شایعه!", 92, "orange")], u, 0.05, 290, 120)


def s5(c, u):
    deco(c, [(130, 580, 70, 70), (950, 1460, 70, 60)])
    if u < TIM["s5_split"]:
        k = eob(u / 0.4)
        c.push(0, 500 * (1 - k), 1)
        c.fill(rrect(290, 600, 790, 1440, 60), "ink", hatch=0.2, outline=5)
        c.fill(rrect(316, 640, 764, 1400, 40), "paper", hatch=0, outline=0)
        logo = Image.open("/home/claude/reel/src_logo/nemonet/app-icon-tide.png").convert("RGBA")
        lx, ly = c.T([(480, 690)])[0]; ls = int(120 * c.xf[2] * S)
        c.img.paste(logo.resize((ls, ls), Image.LANCZOS), (int(lx * S), int(ly * S)), logo.resize((ls, ls), Image.LANCZOS))
        c.text_s((540, 880), "آزمایش ویتامین D", "Black", 52, "ink")
        c.text_s((540, 950), "نمونه‌گیری در منزل", "Bold", 40, "purple_d")
        tapped = u > 0.85
        bk = 1 - 0.08 * math.sin(clamp((u - 0.8) / 0.15) * math.pi)
        c.push(540 * (1 - bk), 1100 * (1 - bk), bk)
        c.fill(rrect(370, 1040, 710, 1160, 60), "teal" if tapped else "orange", hatch=0.45, outline=4.5)
        c.text_s((540, 1098), "رزرو شد" if tapped else "رزرو نوبت", "ExtraBold", 48, "paper")
        c.pop()
        if tapped: check_mark(c, 540, 1270, eo((u - 0.9) / 0.3), "teal", 1.6)
        fy = 1500 - 360 * eo(u / 0.8) + 40 * eo((u - 0.8) / 0.2)
        limb(c, [(660, 1990), (630, fy + 230)], 96, "purple")
        limb(c, [(630, fy + 240), (600, fy + 60), (585, fy)], 58)
        c.fill(ellipse(583, fy, 30, 34), "skin", hatch=0, outline=4)
        c.pop()
        headline(c, [("با یه آزمایش ساده بفهم", 86, "ink")], u, 0.0, 300)
    else:
        v = u - TIM["s5_split"]
        # door
        c.fill(rrect(70, 640, 440, 1500, 10), "purple_d", hatch=0.3, outline=5)
        dw = 340 * (1 - eo(v / 0.5))
        c.fill(rrect(85, 655, 85 + max(dw, 30), 1500, 6), "mustard", hatch=0.5, outline=4.5)
        if dw > 60: c.fill(ellipse(85 + dw - 30, 1080, 12, 12), "ink", hatch=0, outline=0)
        if v < 0.9:  # doorbell
            k = pop(v, 0.0, 0.3)
            c.text_s((260, 580), "دینگ دانگ!", "Black", 50, "orange", scale=k)
        sk = eob((v - 0.2) / 0.5, 1.3)
        c.push(700 * (1 - sk), 0, 1)
        c.push(240, 280, 0.75); sampler(c, 700, 900, tube_fill=eo((v - 0.9) / 1.0), arm_up=eo((v - 0.5) / 0.4)); c.pop()
        c.pop()
        headline(c, [("نمونت میاد خونه‌ت!", 96, "ink")], v, 0.0, 300)
        p = partial([(330 + 420 * i / 40, 385 + 7 * math.sin(i / 40 * math.pi * 3)) for i in range(41)], eo((v - 0.2) / 0.5))
        if p: c.line(p, 7, "teal", 1.5)


def s6(c, u):
    deco(c, [(140, 640, 90, 90), (950, 820, 70, 100), (170, 1180, 60, 60)])
    for i, (x, y, s) in enumerate(((420, 760, 26), (930, 1050, 20), (360, 1250, 18))):
        k = 0.6 + 0.4 * math.sin(u * 6 + i * 2)
        c.line([(x - s * k, y), (x + s * k, y)], 4, "mustard", 0.3); c.line([(x, y - s * k), (x, y + s * k)], 4, "mustard", 0.3)
    level = int(clamp((u - 0.15) / 1.1) * 4 + 0.001)
    battery(c, 110, 830, 230, 400, level, "teal")
    sun(c, 225, 720, 64, u * 30)
    pct = int(round(clamp((u - 0.15) / 1.1) * 100))
    c.text_s((225, 1290), f"{pct}٪".translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")), "Black", 56, "teal")
    hk = eob(u / 0.45, 1.5)
    c.push(700 * (1 - hk), 900 * (1 - hk), hk)
    character(c, 700, 900, "happy", tilt=4 + 2 * math.sin(u * 4), shirt_bottom=1460)
    up = eob((u - 0.5) / 0.4)
    c.push(0, 160 * (1 - up), 1)
    limb(c, [(915, 1210), (960, 1150), (990, 1070)], 52)
    c.fill(rrect(984, 960, 1014, 1030, 14), "skin", hatch=0, outline=4)
    c.fill(rrect(958, 1012, 1032, 1080, 18), "skin", hatch=0, outline=4)
    for yy in (1030, 1048, 1064): c.line([(966, yy), (990, yy)], 2.5, "ink", 0.2)
    c.pop()
    c.fill([(880, 1120), (950, 1170), (920, 1290), (850, 1250)], "purple", hatch=0.6, angle=70, spacing=5)
    c.pop()
    headline(c, [("آزمایش ویتامین D", 104, "ink"), ("در خونه‌ی خودت", 92, "orange")], u, 0.0, 290, 130)
    p = partial([(330 + 420 * i / 40, 488 + 7 * math.sin(i / 40 * math.pi * 3)) for i in range(41)], eo((u - 0.4) / 0.5))
    if p: c.line(p, 7, "mustard", 1.5)
    ck = eob((u - 0.6) / 0.5, 1.2)
    c.push(0, 500 * (1 - ck), 1)
    c.fill(rrect(70, 1430, 1010, 1610, 40), "paper", hatch=0, outline=5)
    logo = Image.open("/home/claude/reel/src_logo/nemonet/app-icon-tide.png").convert("RGBA").resize((132 * S, 132 * S), Image.LANCZOS)
    lx, ly = c.T([(850, 1454)])[0]
    c.img.paste(logo, (int(lx * S), int(ly * S)), logo)
    c.text_s((830, 1490), "نمونت", "Black", 58, "teal", anchor="rm")
    c.text_s((830, 1568), "nemonet.ir", "SemiBold", 38, "purple_d", anchor="rm", rtl=False)
    pulse = 1 + 0.05 * math.sin(max(0, u - 1.3) * 8)
    c.push(310 * (1 - pulse), 1520 * (1 - pulse), pulse)
    c.fill(rrect(100, 1470, 520, 1570, 50), "orange", hatch=0.45, outline=4.5)
    c.text_s((330, 1518), "همین حالا نوبت بگیر", "ExtraBold", 40, "paper")
    c.line([(150, 1505), (126, 1520), (150, 1535)], 6, "paper", 0.3)
    c.pop()
    c.pop()


SCENES = [s1, s2, s3, s4, s5, s6]


def render(f):
    t = f / FPS
    i = next(k for k, (a, b) in enumerate(SC) if t < b or k == len(SC) - 1)
    u = t - SC[i][0]
    c = Canvas(seed=100 + (f // 2) % 3)
    SCENES[i](c, u)
    c.pop()
    c.finish(f"{OUT}/f{f // 2:04d}.png")
    return f


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if len(sys.argv) > 1:  # test specific frames
        for a in sys.argv[1:]:
            f = int(float(a) * FPS) // 2 * 2; render(f); print(f"{OUT}/f{f // 2:04d}.png")
    else:
        frames = list(range(0, int(DUR * FPS), 2))
        with Pool(2) as p:
            for n, f in enumerate(p.imap_unordered(render, frames)):
                if n % 20 == 0: print(n, "/", len(frames), flush=True)
