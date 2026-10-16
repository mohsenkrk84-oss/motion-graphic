"""Cover + six key frames for the HPV reel storyboard."""
import os
from chars import *

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../storyboard/")


def hook_text(c, y=330, sub=None):
    c.text((540, y), "۳ تا چیزی که درباره‌ی", "Bold", 84, "ink")
    w = c.text_w("HPV", "Bold", 132)
    c.text((540, y + 135), "HPV", "Bold", 132, "orange")
    underline_scribble(c, 540, y + 215, w + 120, "mustard")
    c.text((540, y + 300), "اشتباه فکر می‌کنی", "Bold", 84, "ink")
    if sub:
        c.text((540, y + 390), sub, "Regular", 54, "purple_d")


def man_with_cards(c, mood="confused", labels=("؟", "؟", "؟")):
    qmark_card(c, 210, 930, 150, 200, tilt=-12, col="mustard", label=labels[0])
    qmark_card(c, 870, 900, 150, 200, tilt=10, col="orange", label=labels[1])
    qmark_card(c, 860, 1200, 120, 160, tilt=-6, col="purple", label=labels[2])
    man(c, 540, 1080, mood, tilt=-5 if mood == "confused" else 3, shirt_bottom=1640)
    # hand scratching head
    if mood == "confused":
        for (x, y, sz, col) in ((380, 820, 70, "purple_d"), (330, 900, 46, "orange")):
            c.text((x, y), "؟", "Bold", sz, col)


def cover():
    c = Canvas(seed=31)
    deco(c, [(140, 700, 60, 50), (960, 1420, 50, 70), (110, 1380, 40, 40)])
    c.text((540, 400), "سه تا چیزی که", "Bold", 104, "ink")
    c.text((540, 540), "درباره‌اش", "Bold", 128, "orange")
    underline_scribble(c, 540, 625, c.text_w("درباره‌اش", "Bold", 128) + 100, "mustard")
    c.text((540, 720), "اشتباه فکر می‌کنی", "Bold", 96, "ink")
    man_with_cards(c)
    return c.finish(OUT + "cover.png")


def f1():
    c = Canvas(seed=41)
    deco(c, [(140, 700, 60, 50), (960, 1420, 50, 70), (110, 1380, 40, 40)])
    hook_text(c, 300, sub="(ویروس عامل زگیل تناسلی)")
    man_with_cards(c)
    return c.finish(OUT + "f1_hook.png")


def myth_header(c, n, myth, truth, k=1.0):
    c.fill(rrect(400, 250, 680, 330, 40), "purple_d", hatch=0.4, outline=4)
    c.text((540, 290), f"باور غلط {n}", "Bold", 40, "paper")
    c.text((540, 440), myth, "Bold", 74, "grey")
    w = c.text_w(myth, "Bold", 74)
    c.line([(540 - w / 2 - 20, 446), (540 + w / 2 + 20, 438)], 6, "orange", 1.2)
    xmark(c, 540 + w / 2 + 70, 442, 20)
    c.text((540, 590), truth, "Bold", 92, "teal")
    tw = c.text_w(truth, "Bold", 92)
    check(c, 540 + tw / 2 + 60, 590, 30)


def f2():
    c = Canvas(seed=42)
    myth_header(c, "۱", "نادره", "خیلی رایجه!")
    cols = ["purple", "orange", "mustard", "purple_d", "teal", "orange"]
    i = 0
    for r, y in enumerate((790, 1040, 1290)):
        xs = (170, 355, 540, 725, 910) if r % 2 == 0 else (262, 447, 632, 817)
        for x in xs:
            scarf = "mustard" if (i % 3 == 1) else None
            mini_person(c, x, y, 1.55, cols[i % len(cols)], scarf=scarf, infected=(i % 4 != 3))
            i += 1
    c.plus(80, 760, 40, 40); c.plus(1000, 1300, 40, 60)
    return c.finish(OUT + "f2_myth1.png")


def f3():
    c = Canvas(seed=43)
    myth_header(c, "۲", "فقط مال خانم‌هاست", "آقایون هم می‌گیرن")
    woman(c, 320, 1030, "neutral", tilt=-3, shirt_bottom=1640)
    man(c, 770, 1030, "surprised", tilt=4, shirt_bottom=1640)
    virus(c, 120, 860, 48, "sly", spin=5)
    virus(c, 975, 840, 48, "sly", spin=15)
    c.text((540, 800), "=", "Bold", 120, "purple_d")
    deco(c, [(120, 1500, 40, 40), (990, 1520, 40, 50)])
    return c.finish(OUT + "f3_myth2.png")


def f4():
    c = Canvas(seed=44)
    myth_header(c, "۳", "حتماً علامت داره", "اغلب بی‌علامته")
    virus(c, 830, 1170, 78, "sly", spin=8)
    man(c, 560, 1060, "happy", tilt=3, shirt_bottom=1640)
    # mug in hand
    limb(c, [(340, 1640), (330, 1500), (400, 1420)], 50)
    c.fill([(380, 1330), (480, 1330), (470, 1440), (390, 1440)], "orange", hatch=0.5, outline=4)
    c.line(ellipse(490, 1380, 22, 26, 30, -90, 90), 4.5, "ink", 0.5)
    c.fill(ellipse(400, 1420, 34, 28), "skin", hatch=0, outline=4)
    for i in range(2):
        c.line(bez((405 + i * 35, 1310), (390 + i * 35, 1280), (415 + i * 35, 1260), (400 + i * 35, 1235)), 3, "grey", 0.6)
    c.text((870, 1040), "هیس!", "Bold", 44, "purple_d")
    deco(c, [(150, 860, 50, 50), (1000, 1520, 40, 50)])
    return c.finish(OUT + "f4_myth3.png")


def f5():
    c = Canvas(seed=45)
    c.text((540, 330), "پس بهترین کار:", "Regular", 60, "purple_d")
    c.text((540, 450), "غربالگری = خیال راحت", "Bold", 88, "ink")
    underline_scribble(c, 540, 520, 560, "teal")
    # door frame
    c.line([(70, 1640), (70, 720), (470, 720), (470, 1640)], 5, "ink", 1)
    c.fill(rrect(90, 740, 450, 1640, 6), "mustard", hatch=0.35, outline=3.5)
    c.fill(ellipse(410, 1200, 14, 14), "ink", hatch=0, outline=0)
    woman(c, 300, 1030, "happy", shirt_bottom=1640, scarf="purple_d", coat=True)
    limb(c, [(500, 1450), (560, 1300), (590, 1180)], 48, "teal")
    test_tube(c, 600, 980, h=200, w=54, tilt=10)
    c.fill(ellipse(592, 1170, 34, 30), "skin", hatch=0, outline=4)
    man(c, 840, 1080, "happy", tilt=-3, shirt_bottom=1640)
    virus(c, 960, 800, 40, "caught", spin=12)
    c.line(ellipse(960, 800, 66, 66), 6, "ink", 0.6)
    c.line([(1006, 846), (1040, 900)], 10, "ink", 0.4)
    return c.finish(OUT + "f5_screening.png")


def f6():
    c = Canvas(seed=46)
    deco(c, [(140, 700, 60, 50), (960, 1420, 50, 70)])
    c.text((540, 330), "نمونت؛", "Bold", 110, "teal")
    c.text((540, 480), "آزمایش در منزل", "Bold", 104, "ink")
    underline_scribble(c, 540, 560, 520, "mustard")
    for (x, y, s) in ((200, 820, 26), (900, 760, 22), (160, 1180, 18)):
        c.line([(x - s, y), (x + s, y)], 4, "mustard", 0.3); c.line([(x, y - s), (x, y + s)], 4, "mustard", 0.3)
    man(c, 540, 900, "happy", tilt=3, shirt_bottom=1300)
    card(c, 70, 1300, 1010, 1600)
    logo = Image.open(LOGO).convert("RGBA").resize((140 * S, 140 * S), Image.LANCZOS)
    c.paste(logo, (840, 1330))
    c.text((815, 1375), "نمونت", "Bold", 60, "teal", anchor="rm")
    c.d.text((815 * S, 1440 * S), "nemonet.ir", font=font("Regular", 40), fill=PAL["purple_d"], anchor="rm")
    c.fill(rrect(130, 1490, 950, 1575, 44), "orange", hatch=0.45, outline=4.5)
    c.text((540, 1532), "همین حالا نوبت بگیر", "Bold", 44, "paper")
    c.text((310, 1400), "بیش از ۵۰۰۰ آزمایش", "Bold", 40, "purple_d")
    return c.finish(OUT + "f6_cta.png")


if __name__ == "__main__":
    import sys
    fns = dict(cover=cover, f1=f1, f2=f2, f3=f3, f4=f4, f5=f5, f6=f6)
    for k in (sys.argv[1:] or fns):
        fns[k](); print(k)
