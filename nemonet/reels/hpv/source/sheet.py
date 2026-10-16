"""Character sheet for the HPV reel."""
import os
from chars import *

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../storyboard/")


def label(c, x, y, title, sub):
    c.text((x, y), title, "Bold", 44, "ink")
    c.text((x, y + 52), sub, "Regular", 28, "purple_d")


def sheet():
    c = Canvas(seed=21)
    c.text((540, 150), "کاراکترهای ریلز HPV", "Bold", 70, "ink")
    underline_scribble(c, 540, 205, 430)
    # row 1: man / woman
    c.push(20, 260, 0.62); man(c, 400, 500, "confused", tilt=-4, shirt_bottom=1080); c.pop()
    c.push(560, 260, 0.62); woman(c, 400, 500, "neutral", tilt=3, shirt_bottom=1080); c.pop()
    label(c, 270, 960, "آرش", "شخصیت اصلی؛ همون پسر ریلز ویتامین دی")
    label(c, 810, 960, "سارا", "برای صحنه‌ی «آقایون هم می‌گیرن»")
    # row 2: sampler / virus
    c.push(560, 1060, 0.62); woman(c, 400, 500, "happy", shirt_bottom=960, scarf="purple_d", coat=True); c.pop()
    c.push(560, 1060, 0.62); test_tube(c, 640, 720, tilt=12); c.pop()
    virus(c, 270, 1360, 110, "sly")
    virus(c, 130, 1560, 44, "caught", spin=10)
    virus(c, 410, 1580, 40, "sleepy", spin=20)
    label(c, 810, 1700, "نمونه‌گیر نمونت", "روپوش تیل، لوله‌ی آزمایش")
    label(c, 270, 1700, "ویروس HPV", "بامزه، نه ترسناک؛ سه حالت")
    deco(c, [(80, 330, 40, 40), (1000, 600, 50, 40), (530, 1250, 40, 60)])
    return c.finish(OUT + "characters.png")


if __name__ == "__main__":
    print(sheet())
