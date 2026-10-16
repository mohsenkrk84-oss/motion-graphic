"""Characters and props for the Nemonet HPV reel (same hand-drawn style as the vitamin-D reel)."""
import math, os
from PIL import Image
from lib import *

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../")
LOGO = os.path.join(ROOT, "nemonet/app-icon-tide.png")
BLUSH = (247, 196, 176)


# ---------------------------------------------------------------- faces
def eyes_brows_mouth(c, tf, cx, cy, mood, lashes=False, glasses=True):
    for sx in (-1, 1):
        ex = cx + sx * 54
        if mood == "happy":
            c.line(tf(ellipse(ex, cy + 20, 16, 14, 20, 200, 340)), 5, "ink", 0.3)
        elif mood == "surprised":
            c.fill(tf(ellipse(ex, cy + 14, 10, 12)), "ink", hatch=0, outline=0)
        elif mood == "worried":
            c.fill(tf(ellipse(ex, cy + 16, 8, 9)), "ink", hatch=0, outline=0)
        else:  # confused / neutral
            c.fill(tf(ellipse(ex + (6 if mood == "confused" else 0), cy + 14, 8, 9)), "ink", hatch=0, outline=0)
        if lashes and mood != "happy":
            c.line(tf([(ex + sx * 9, cy + 8), (ex + sx * 19, cy + 5)]), 3, "ink", 0.2)
    # brows
    for sx in (-1, 1):
        bx = cx + sx * 54
        if mood == "confused":
            if sx < 0:
                c.line(tf(bez((bx - 22, cy - 50), (bx, cy - 66), (bx + 22, cy - 52))), 4, "ink", 0.3)
            else:
                c.line(tf([(bx - 22, cy - 34), (bx + 22, cy - 38)]), 4, "ink", 0.3)
        elif mood == "surprised":
            c.line(tf(bez((bx - 22, cy - 50), (bx, cy - 64), (bx + 22, cy - 50))), 4, "ink", 0.3)
        elif mood == "worried":
            c.line(tf([(bx - 20, cy - 34 - (8 if sx > 0 else -2)), (bx + 20, cy - 34 - (8 if sx < 0 else -2))]), 4, "ink", 0.3)
        else:
            c.line(tf(bez((bx - 22, cy - 38), (bx, cy - 50), (bx + 22, cy - 38))), 4, "ink", 0.3)
    if glasses:
        for sx in (-1, 1):
            c.line(tf(ellipse(cx + sx * 54, cy + 12, 40, 38)), 4.5, "orange", 0.6)
        c.line(tf(bez((cx - 14, cy + 6), (cx, cy - 2), (cx + 14, cy + 6))), 4, "orange", 0.4)
        c.line(tf([(cx - 94, cy + 6), (cx - 122, cy - 2)]), 4, "orange", 0.3)
        c.line(tf([(cx + 94, cy + 6), (cx + 122, cy - 2)]), 4, "orange", 0.3)
    # nose
    c.line(tf(bez((cx + 4, cy + 34), (cx - 10, cy + 62), (cx + 10, cy + 66))), 3.5, "ink", 0.3)
    # mouth
    if mood == "happy":
        c.fill(tf(bez((cx - 42, cy + 86), (cx, cy + 132), (cx + 42, cy + 86))), "orange", hatch=0, outline=4)
    elif mood == "surprised":
        c.fill(tf(ellipse(cx, cy + 100, 16, 20)), "orange", hatch=0, outline=4)
    elif mood == "confused":
        c.line(tf([(cx - 26, cy + 100), (cx - 10, cy + 92), (cx + 6, cy + 102), (cx + 24, cy + 94)]), 4, "ink", 0.4)
    elif mood == "worried":
        c.line(tf(bez((cx - 24, cy + 104), (cx, cy + 92), (cx + 24, cy + 104))), 4, "ink", 0.4)
    else:
        c.line(tf(bez((cx - 26, cy + 92), (cx, cy + 106), (cx + 26, cy + 92))), 4, "ink", 0.4)
    if mood in ("happy", "neutral"):
        for sx in (-1, 1):
            c.fill(tf(ellipse(cx + sx * 80, cy + 70, 16, 9)), BLUSH, hatch=0, outline=0)


def torso(c, cx, sh_y, bottom, col, width=245):
    w = width
    pts = [(cx - w + 15, bottom), (cx - w, sh_y + 120), (cx - w + 55, sh_y + 20), (cx - 70, sh_y - 15),
           (cx + 70, sh_y - 15), (cx + w - 55, sh_y + 20), (cx + w, sh_y + 120), (cx + w - 15, bottom)]
    c.fill(pts, col, hatch=0.6, angle=70, spacing=5)
    return pts


# ---------------------------------------------------------------- man (recurring character)
def man(c, cx, cy, mood="neutral", tilt=0, shirt_bottom=1500):
    sh_y = cy + 200
    torso(c, cx, sh_y, shirt_bottom, "purple")
    c.line(bez((cx - 245, sh_y + 160), (cx - 230, sh_y + 150), (cx - 175, sh_y + 165)), 3, "paper", 0.6)
    c.line(bez((cx + 245, sh_y + 160), (cx + 230, sh_y + 150), (cx + 175, sh_y + 165)), 3, "paper", 0.6)
    tf = lambda pts: rot(pts, tilt, cx, cy + 150)
    c.fill(tf([(cx - 42, cy + 105), (cx - 46, sh_y + 5), (cx + 46, sh_y + 5), (cx + 42, cy + 105)]), "skin", hatch=0, outline=4)
    c.line(bez((cx - 72, sh_y - 12), (cx, sh_y + 52), (cx + 72, sh_y - 12)), 4, "paper", 0.8)
    for sx in (-1, 1):
        c.fill(tf(ellipse(cx + sx * 122, cy + 10, 24, 34)), "skin", hatch=0, outline=4)
    c.fill(tf(ellipse(cx, cy, 120, 140)), "skin", hatch=0, outline=4.5)
    hair = [(cx - 126, cy + 5), (cx - 132, cy - 60), (cx - 110, cy - 120), (cx - 60, cy - 160), (cx - 10, cy - 172),
            (cx + 30, cy - 192), (cx + 95, cy - 196), (cx + 140, cy - 170), (cx + 118, cy - 150), (cx + 132, cy - 120),
            (cx + 135, cy - 40), (cx + 124, cy + 5), (cx + 104, cy - 52), (cx + 60, cy - 78), (cx + 10, cy - 70),
            (cx - 40, cy - 90), (cx - 92, cy - 70), (cx - 112, cy - 30)]
    c.fill(tf(hair), "hair", hatch=0.35, angle=35, spacing=4, shade=(20, 19, 24))
    c.line(tf(bez((cx - 60, cy - 130), (cx - 10, cy - 160), (cx + 40, cy - 150))), 2.4, "paper", 0.5)
    c.line(tf(bez((cx + 30, cy - 175), (cx + 70, cy - 195), (cx + 100, cy - 170))), 2.4, "paper", 0.5)
    eyes_brows_mouth(c, tf, cx, cy, mood)


# ---------------------------------------------------------------- woman (new, for the "men get it too" scene)
def woman(c, cx, cy, mood="neutral", tilt=0, shirt_bottom=1500, scarf="mustard", top="orange", coat=False):
    sh_y = cy + 200
    tf = lambda pts: rot(pts, tilt, cx, cy + 150)
    torso(c, cx, sh_y, shirt_bottom, "teal" if coat else top, width=230)
    if coat:  # lab-coat lapels and pocket
        c.line([(cx - 40, sh_y + 10), (cx - 10, sh_y + 160), (cx - 6, shirt_bottom)], 3.5, "paper", 0.6)
        c.line([(cx + 40, sh_y + 10), (cx + 10, sh_y + 160)], 3.5, "paper", 0.6)
        c.line(rrect(cx + 90, sh_y + 190, cx + 170, sh_y + 260, 8), 3, "paper", 0.6)
    else:
        c.line(bez((cx - 230, sh_y + 160), (cx - 215, sh_y + 150), (cx - 160, sh_y + 165)), 3, "paper", 0.6)
        c.line(bez((cx + 230, sh_y + 160), (cx + 215, sh_y + 150), (cx + 160, sh_y + 165)), 3, "paper", 0.6)
    # scarf: outer shape around the face, draped onto the shoulders
    outer = ellipse(cx, cy - 18, 158, 178, 60, 160, 380)
    drape = [(cx + 150, cy + 40), (cx + 170, cy + 150), (cx + 150, sh_y + 60), (cx + 60, sh_y + 80),
             (cx, sh_y + 40), (cx - 60, sh_y + 80), (cx - 150, sh_y + 60), (cx - 170, cy + 150), (cx - 150, cy + 40)]
    c.fill(tf(outer + drape), scarf, hatch=0.5, angle=50, spacing=6)
    # face
    c.fill(tf(ellipse(cx, cy + 4, 116, 136)), "skin", hatch=0, outline=4.5)
    # a sliver of dark hair under the scarf edge
    fringe = bez((cx - 104, cy - 50), (cx - 40, cy - 150), (cx + 40, cy - 128)) + \
        bez((cx + 40, cy - 128), (cx - 10, cy - 100), (cx - 60, cy - 90)) + [(cx - 98, cy - 34)]
    c.fill(tf(fringe), "hair", hatch=0.35, angle=35, spacing=4, shade=(20, 19, 24))
    # scarf inner rim line over the forehead
    c.line(tf(ellipse(cx, cy + 4, 128, 150, 40, 195, 345)), 4, "ink", 0.6)
    # knot / fold under the chin
    c.line(tf(bez((cx - 60, cy + 150), (cx, cy + 176), (cx + 70, cy + 140))), 3.5, "ink", 0.5)
    eyes_brows_mouth(c, tf, cx, cy + 4, mood, lashes=True, glasses=False)


# ---------------------------------------------------------------- HPV virus mascot
def virus(c, cx, cy, r=70, mood="sly", col="orange", knobs=12, spin=0):
    for i in range(knobs):
        a = math.radians(spin + 360 * i / knobs)
        x0, y0 = cx + r * 0.92 * math.cos(a), cy + r * 0.92 * math.sin(a)
        x1, y1 = cx + r * 1.32 * math.cos(a), cy + r * 1.32 * math.sin(a)
        c.line([(x0, y0), (x1, y1)], max(3, r * 0.06), "ink", 0.3)
        c.fill(ellipse(x1, y1, r * 0.14, r * 0.14, 24), "mustard", hatch=0, outline=max(2.5, r * 0.045))
    c.fill(ellipse(cx, cy, r, r * 0.96), col, hatch=0.5, angle=40, spacing=6, outline=max(3, r * 0.065))
    # a few spots
    for (dx, dy, s) in ((-0.45, -0.4, 0.12), (0.5, -0.25, 0.09), (0.35, 0.5, 0.1)):
        c.fill(ellipse(cx + dx * r, cy + dy * r, s * r, s * r, 20), "purple_d", hatch=0, outline=0)
    e = r * 0.28
    if mood == "sly":
        for sx in (-1, 1):
            c.line(ellipse(cx + sx * e, cy - r * 0.05, r * 0.11, r * 0.07, 16, 0, 180), max(3, r * 0.06), "ink", 0.2)
            c.line([(cx + sx * e - r * 0.13, cy - r * 0.12), (cx + sx * e + r * 0.13, cy - r * 0.2 + (0 if sx > 0 else r * 0.08))], max(2.5, r * 0.05), "ink", 0.2)
        c.line(bez((cx - r * 0.25, cy + r * 0.28), (cx + r * 0.05, cy + r * 0.45), (cx + r * 0.3, cy + r * 0.2)), max(3, r * 0.06), "ink", 0.3)
    elif mood == "caught":
        for sx in (-1, 1):
            c.fill(ellipse(cx + sx * e, cy - r * 0.05, r * 0.1, r * 0.13, 20), "paper", hatch=0, outline=max(2.5, r * 0.045))
            c.fill(ellipse(cx + sx * e, cy - r * 0.02, r * 0.05, r * 0.06, 16), "ink", hatch=0, outline=0)
        c.fill(ellipse(cx, cy + r * 0.38, r * 0.12, r * 0.15, 20), "ink", hatch=0, outline=0)
    else:  # sleepy / hidden
        for sx in (-1, 1):
            c.line([(cx + sx * e - r * 0.1, cy), (cx + sx * e + r * 0.1, cy)], max(3, r * 0.06), "ink", 0.2)
        c.line(bez((cx - r * 0.15, cy + r * 0.32), (cx, cy + r * 0.4), (cx + r * 0.15, cy + r * 0.32)), max(3, r * 0.06), "ink", 0.2)


# ---------------------------------------------------------------- props
def limb(c, pts, w=54, col="skin"):
    p = wob(pts, 1.0, 5)
    c.line(p, w + 9, "ink", 0); c.line(p, w, col, 0)


def test_tube(c, x, y, h=210, w=56, tilt=0):
    body = rrect(x - w / 2, y, x + w / 2, y + h, w / 2 - 2)
    liquid = rrect(x - w / 2 + 8, y + h * 0.45, x + w / 2 - 8, y + h - 8, w / 2 - 10)
    cap = rrect(x - w / 2 - 8, y - 40, x + w / 2 + 8, y + 6, 8)
    R = lambda p: rot(p, tilt, x, y + h / 2)
    c.fill(R(body), "paper", hatch=0, outline=4.5)
    c.fill(R(liquid), "orange", hatch=0.5, outline=0)
    c.fill(R(cap), "mustard", hatch=0.5, outline=4.5)
    c.line(R([(x - w / 2 + 14, y + 30), (x - w / 2 + 14, y + h * 0.4)]), 4, "paper", 0.2)


def card(c, x0, y0, x1, y1, col="paper", r=34, outline=5):
    c.fill(rrect(x0, y0, x1, y1, r), col, hatch=0 if col == "paper" else 0.45, outline=outline)


def cross_out(c, x0, y, x1, col="orange", w=10, k=1.0):
    """Red pencil scribble over text; k is draw-on progress (0..1)."""
    if k <= 0: return
    xe = x0 + (x1 - x0) * k
    c.line([(x0, y + 6), ((x0 + xe) / 2, y - 6), (xe, y + 4)], w, col, 2.2)
    if k > 0.6:
        c.line([(x0 + 10, y + 22), (x0 + (x1 - x0) * (k - 0.2), y + 14)], w * 0.6, col, 2.2)


def check(c, x, y, s=34, col="teal", w=9):
    c.line([(x - s, y), (x - s * 0.3, y + s * 0.7), (x + s, y - s * 0.8)], w, col, 0.8)


def xmark(c, x, y, s=26, col="orange", w=9):
    c.line([(x - s, y - s), (x + s, y + s)], w, col, 0.8); c.line([(x + s, y - s), (x - s, y + s)], w, col, 0.8)


def qmark_card(c, x, y, w=150, h=200, tilt=0, col="mustard", label="؟"):
    R = lambda p: rot(p, tilt, x, y)
    c.fill(R(rrect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, 22)), col, hatch=0.5, outline=4.5)
    c.text_s((x, y), label, "Black", h * 0.6, "ink")


def underline_scribble(c, cx, y, w, col="orange"):
    pts = [(cx - w / 2 + w * i / 40, y + 8 * math.sin(i / 40 * math.pi * 3)) for i in range(41)]
    c.line(pts, 7, col, 1.5)
    c.line([(cx - w / 2 + 30, y + 18), (cx + w / 2 - 20, y + 14)], 5, col, 2)


def mini_person(c, x, y, s=1.0, col="purple", scarf=None, infected=False):
    c.fill(bez((x - 34 * s, y + 90 * s), (x - 36 * s, y + 20 * s), (x, y + 20 * s)) +
           bez((x, y + 20 * s), (x + 36 * s, y + 20 * s), (x + 34 * s, y + 90 * s)), col, hatch=0.55, spacing=5, outline=3.5)
    if scarf:
        c.fill(ellipse(x, y - 4 * s, 30 * s, 32 * s), scarf, hatch=0.5, outline=3.5)
    c.fill(ellipse(x, y, 22 * s, 24 * s), "skin", hatch=0, outline=3.5)
    if infected:
        virus(c, x + 34 * s, y - 26 * s, 13 * s, mood="sleepy", knobs=8)


def deco(c, marks):
    for m in marks:
        c.plus(*m)
