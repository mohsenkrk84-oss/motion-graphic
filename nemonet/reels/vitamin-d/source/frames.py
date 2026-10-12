import math
from PIL import Image
from lib import *


def character(c, cx, cy, mood="tired", tilt=0, shirt_bottom=1500):
    # torso (t-shirt) first, then neck, head
    sh_y = cy + 200
    torso = [(cx - 230, shirt_bottom), (cx - 245, sh_y + 120), (cx - 190, sh_y + 20), (cx - 70, sh_y - 15),
             (cx + 70, sh_y - 15), (cx + 190, sh_y + 20), (cx + 245, sh_y + 120), (cx + 230, shirt_bottom)]
    c.fill(torso, "purple", hatch=0.6, angle=70, spacing=5)
    c.line(bez((cx - 245, sh_y + 160), (cx - 230, sh_y + 150), (cx - 175, sh_y + 165)), 3, "paper", 0.6)  # sleeve hems
    c.line(bez((cx + 245, sh_y + 160), (cx + 230, sh_y + 150), (cx + 175, sh_y + 165)), 3, "paper", 0.6)
    tf = lambda pts: rot(pts, tilt, cx, cy + 150)
    neck = tf([(cx - 42, cy + 105), (cx - 46, sh_y + 5), (cx + 46, sh_y + 5), (cx + 42, cy + 105)])
    c.fill(neck, "skin", hatch=0, outline=4)
    c.line(bez((cx - 72, sh_y - 12), (cx, sh_y + 52), (cx + 72, sh_y - 12)), 4, "paper", 0.8)  # collar
    # ears
    for sx in (-1, 1):
        c.fill(tf(ellipse(cx + sx * 122, cy + 10, 24, 34)), "skin", hatch=0, outline=4)
    c.fill(tf(ellipse(cx, cy, 120, 140)), "skin", hatch=0, outline=4.5)
    # hair with quiff
    hair = [(cx - 126, cy + 5), (cx - 132, cy - 60), (cx - 110, cy - 120), (cx - 60, cy - 160), (cx - 10, cy - 172),
            (cx + 30, cy - 192), (cx + 95, cy - 196), (cx + 140, cy - 170), (cx + 118, cy - 150), (cx + 132, cy - 120),
            (cx + 135, cy - 40), (cx + 124, cy + 5), (cx + 104, cy - 52), (cx + 60, cy - 78), (cx + 10, cy - 70),
            (cx - 40, cy - 90), (cx - 92, cy - 70), (cx - 112, cy - 30)]
    c.fill(tf(hair), "hair", hatch=0.35, angle=35, spacing=4, shade=(20, 19, 24))
    c.line(tf(bez((cx - 60, cy - 130), (cx - 10, cy - 160), (cx + 40, cy - 150))), 2.4, "paper", 0.5)
    c.line(tf(bez((cx + 30, cy - 175), (cx + 70, cy - 195), (cx + 100, cy - 170))), 2.4, "paper", 0.5)
    # glasses
    for sx in (-1, 1):
        c.line(tf(ellipse(cx + sx * 54, cy + 12, 40, 38)), 4.5, "orange", 0.6)
    c.line(tf(bez((cx - 14, cy + 6), (cx, cy - 2), (cx + 14, cy + 6))), 4, "orange", 0.4)
    c.line(tf([(cx - 94, cy + 6), (cx - 122, cy - 2)]), 4, "orange", 0.3)
    c.line(tf([(cx + 94, cy + 6), (cx + 122, cy - 2)]), 4, "orange", 0.3)
    # eyes
    for sx in (-1, 1):
        ex = cx + sx * 54
        if mood == "tired":
            c.line(tf([(ex - 18, cy + 12), (ex + 18, cy + 12)]), 4.5, "ink", 0.3)        # heavy lid
            c.line(tf(ellipse(ex, cy + 13, 12, 9, 20, 0, 180)), 4, "ink", 0.2)            # half pupil
            c.line(tf(bez((ex - 16, cy + 36), (ex, cy + 42), (ex + 16, cy + 36))), 2.2, "grey", 0.3)  # eye bag
        else:
            c.line(tf(ellipse(ex, cy + 20, 16, 14, 20, 200, 340)), 5, "ink", 0.3)        # happy ^ ^
    # brows
    for sx in (-1, 1):
        bx = cx + sx * 54
        dy = 8 if mood == "tired" else -6
        c.line(tf([(bx - 22, cy - 40 + (dy if sx < 0 else 0)), (bx + 22, cy - 40 + (dy if sx > 0 else 0))] if mood == "tired"
                  else bez((bx - 22, cy - 38), (bx, cy - 50), (bx + 22, cy - 38))), 4, "ink", 0.3)
    # nose + mouth
    c.line(tf(bez((cx + 4, cy + 34), (cx - 10, cy + 62), (cx + 10, cy + 66))), 3.5, "ink", 0.3)
    if mood == "tired":
        c.line(tf(bez((cx - 22, cy + 98), (cx, cy + 92), (cx + 22, cy + 100))), 4, "ink", 0.6)
    else:
        mouth = bez((cx - 42, cy + 86), (cx, cy + 132), (cx + 42, cy + 86))
        c.fill(tf(mouth), "orange", hatch=0, outline=4)
        c.fill(tf(ellipse(cx - 78, cy + 70, 16, 9)), (247, 196, 176), hatch=0, outline=0)
        c.fill(tf(ellipse(cx + 78, cy + 70, 16, 9)), (247, 196, 176), hatch=0, outline=0)


def limb(c, pts, w=54, col="skin"):
    p = wob(pts, 1.0, 5)
    c.line(p, w + 9, "ink", 0); c.line(p, w, col, 0)


def phone(c, x, y, w=110, h=190, ringing=True, screen_txt="۰۷:۰۵"):
    c.fill(rrect(x, y, x + w, y + h, 18), "ink", hatch=0.2, outline=4)
    c.fill(rrect(x + 10, y + 16, x + w - 10, y + h - 16, 10), "mustard", hatch=0.5, outline=0)
    c.text((x + w / 2, y + 62), screen_txt, "Black", 30, "ink")
    # bell icon
    bx, by = x + w / 2, y + 120
    c.fill(bez((bx - 22, by + 18), (bx - 26, by - 30), (bx, by - 30)) + bez((bx, by - 30), (bx + 26, by - 30), (bx + 22, by + 18)), "paper", hatch=0, outline=3)
    c.fill(ellipse(bx, by + 24, 6, 5), "ink", hatch=0, outline=0)
    if ringing:
        for i, r in enumerate((26, 44)):
            for sx in (-1, 1):
                ax = x + w / 2 + sx * (w / 2 + 6)
                c.line(ellipse(ax, y + h / 2, r, r * 1.4, 14, -40 if sx > 0 else 140, 40 if sx > 0 else 220), 3.5, "orange", 0.3)


def desk(c, top, x0=40, x1=1040):
    c.fill(rrect(x0, top, x1, top + 46, 6), "paper", hatch=0, outline=4.5)
    c.line([(x0 + 10, top + 22), (x1 - 10, top + 22)], 3, "purple", 0.6)
    # shelf / legs perspective lines like the reference
    for a, b in ((200, 120), (520, 470), (820, 830)):
        c.line([(a, top + 46), (b, 1920)], 3.5, "ink", 1)
    c.line([(150, top + 200), (900, top + 200)], 3.5, "ink", 1)
    for (bx, bw, col) in ((250, 150, "orange"), (230, 190, "paper"), (560, 110, "purple"), (530, 120, "mustard"), (650, 110, "ink")):
        pass
    books = [(250, top + 158, 150, 40, "orange"), (226, top + 198 - 2, 0, 0, None)]
    c.fill(rrect(240, top + 160, 400, top + 198, 3), "orange", hatch=0.5, outline=3.5)
    c.fill(rrect(560, top + 158, 660, top + 198, 3), "purple", hatch=0.5, outline=3.5)
    c.fill(rrect(660, top + 168, 800, top + 198, 3), "mustard", hatch=0.5, outline=3.5)


def underline_scribble(c, cx, y, w, col="orange"):
    pts = []
    for i in range(0, 41):
        t = i / 40
        pts.append((cx - w / 2 + w * t, y + 8 * math.sin(t * math.pi * 3) + (6 if i % 2 else 0) * 0))
    c.line(pts, 7, col, 1.5)
    c.line([(cx - w / 2 + 30, y + 18), (cx + w / 2 - 20, y + 14)], 5, col, 2)


def zzz(c, x, y):
    for i, (dx, dy, s) in enumerate(((0, 0, 34), (46, -58, 46), (100, -130, 60))):
        X, Y = x + dx, y + dy
        c.line([(X, Y), (X + s, Y), (X, Y + s), (X + s, Y + s)], 4.5, "purple_d", 0.8)


def scene1():
    c = Canvas(seed=3)
    # deco marks
    c.plus(860, 640, 120, 110); c.plus(220, 1040, 90, 70); c.plus(900, 1120, 60, 60)
    # wall picture frame (like reference)
    c.line([(150, 680), (215, 610), (280, 680)], 3.5, "ink", 0.8)
    c.fill(ellipse(215, 610, 7, 7), "mustard", hatch=0, outline=0)
    c.fill(rrect(110, 680, 320, 840, 14), "paper", hatch=0, outline=4)
    c.fill(rrect(130, 698, 300, 822, 4), "orange", hatch=0.4, outline=3)
    c.fill(rrect(146, 712, 284, 808, 3), "paper", hatch=0, outline=2.5)
    c.line([(170, 780), (190, 735), (205, 785), (225, 735), (240, 785), (260, 740)], 4, "mustard", 1.2)
    # character (tilted, tired)
    character(c, 560, 930, "tired", tilt=-7, shirt_bottom=1362)
    zzz(c, 720, 720)
    # desk + props on top
    desk(c, 1360)
    # forearms resting on desk; left hand on the phone (snooze)
    phone(c, 140, 1170)
    limb(c, [(330, 1300), (300, 1330), (230, 1334)], 50)
    c.fill(ellipse(222, 1318, 34, 26), "skin", hatch=0, outline=4)
    limb(c, [(790, 1300), (820, 1334), (880, 1336)], 50)
    c.fill(ellipse(884, 1322, 30, 26), "skin", hatch=0, outline=4)
    # mug
    c.fill([(880, 1255), (980, 1255), (970, 1360), (890, 1360)], "orange", hatch=0.5, outline=4)
    c.line(ellipse(990, 1300, 22, 26, 30, -90, 90), 4.5, "ink", 0.5)
    for i in range(2):
        c.line(bez((905 + i * 35, 1235), (890 + i * 35, 1205), (915 + i * 35, 1185), (900 + i * 35, 1160)), 3, "grey", 0.6)
    # headline (top safe zone)
    c.text((540, 300), "همیشه خسته‌ای؟", "Black", 118, "ink")
    underline_scribble(c, 540, 385, 520)
    c.text((540, 470), "حتی وقتی کامل خوابیدی!", "Bold", 52, "purple_d")
    return c.finish("/home/claude/reel/out/storyboard_scene1.png")


def battery(c, x, y, w, h, level, col="teal"):
    c.fill(rrect(x + w * 0.32, y - 34, x + w * 0.68, y + 4, 10), "ink", hatch=0.2, outline=4)
    c.fill(rrect(x, y, x + w, y + h, 34), "paper", hatch=0, outline=5.5)
    n = 4; pad = 22; ch = (h - pad * (n + 1)) / n
    for i in range(n):
        yy = y + h - pad - (i + 1) * ch - i * pad
        if i < level:
            c.fill(rrect(x + pad, yy, x + w - pad, yy + ch, 14), col, hatch=0.5, outline=3.5)
        else:
            c.line(rrect(x + pad, yy, x + w - pad, yy + ch, 14), 2.5, "grey", 0.8)
    # big D badge
    c.fill(ellipse(x + w / 2, y + h * 0.12 - 70, 0, 0), "paper", hatch=0, outline=0)


def scene6():
    c = Canvas(seed=11)
    c.plus(140, 640, 90, 90); c.plus(950, 820, 70, 100); c.plus(170, 1180, 60, 60)
    # sparkles
    for (x, y, s) in ((420, 760, 26), (930, 1050, 20), (360, 1250, 18)):
        c.line([(x - s, y), (x + s, y)], 4, "mustard", 0.3); c.line([(x, y - s), (x, y + s)], 4, "mustard", 0.3)
    # battery full, left
    battery(c, 110, 830, 230, 400, 4)
    c.fill(ellipse(225, 720, 64, 64), "mustard", hatch=0.5, outline=4.5)
    c.text((225, 722), "D", "Black", 78, "ink")
    for a in range(0, 360, 45):
        r0, r1 = 80, 108
        c.line([(225 + r0 * math.cos(math.radians(a)), 720 + r0 * math.sin(math.radians(a))),
                (225 + r1 * math.cos(math.radians(a)), 720 + r1 * math.sin(math.radians(a)))], 4.5, "mustard", 0.4)
    c.text((225, 1290), "۱۰۰٪", "Black", 56, "teal")
    # happy character right
    character(c, 700, 900, "happy", tilt=4, shirt_bottom=1460)
    # thumbs-up arm
    limb(c, [(915, 1210), (960, 1150), (990, 1070)], 52)
    c.fill(rrect(984, 960, 1014, 1030, 14), "skin", hatch=0, outline=4)   # thumb
    c.fill(rrect(958, 1012, 1032, 1080, 18), "skin", hatch=0, outline=4)  # fist
    for yy in (1030, 1048, 1064):
        c.line([(966, yy), (990, yy)], 2.5, "ink", 0.2)
    c.fill([(880, 1120), (950, 1170), (920, 1290), (850, 1250)], "purple", hatch=0.6, angle=70, spacing=5)
    # headline
    c.text((540, 290), "آزمایش ویتامین D", "Black", 104, "ink")
    c.text((540, 420), "در خونه‌ی خودت", "Black", 92, "orange")
    underline_scribble(c, 540, 488, 420, "mustard")
    # CTA card
    c.fill(rrect(70, 1430, 1010, 1610, 40), "paper", hatch=0, outline=5)
    logo = Image.open("/home/claude/reel/src_logo/nemonet/app-icon-tide.png").convert("RGBA").resize((132 * S, 132 * S), Image.LANCZOS)
    c.paste(logo, (850, 1454))
    c.text((830, 1490), "نمونت", "Black", 58, "teal", anchor="rm")
    c.d.text((830 * S, 1568 * S), "nemonet.ir", font=font("SemiBold", 38), fill=PAL["purple_d"], anchor="rm")
    # button
    c.fill(rrect(100, 1470, 520, 1570, 50), "orange", hatch=0.45, outline=4.5)
    c.text((330, 1518), "همین حالا نوبت بگیر", "ExtraBold", 40, "paper")
    c.line([(150, 1505), (126, 1520), (150, 1535)], 6, "paper", 0.3)
    return c.finish("/home/claude/reel/out/storyboard_scene6.png")


if __name__ == "__main__":
    import os; os.makedirs("/home/claude/reel/out", exist_ok=True)
    print(scene1()); print(scene6())
