"""Prepare the 13 scene source images (faces fixed, border cropped, labels baked in)
and the scene-12 card layer. Output: src/sNN.png (+ src/card.png)."""
import os, cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont

R = "/home/claude/motion-graphic/nemonet/reels/cholesterol/refs"
FIX = "/home/claude/work/img"
ROOT = "/home/claude/motion-graphic"
OUT = "/home/claude/work/chol/src"
os.makedirs(OUT, exist_ok=True)
BOLD = f"{ROOT}/IRANYekanWebBold.ttf"
REG = f"{ROOT}/IRANYekanWebRegular.ttf"
INK = (38, 36, 44)
TEAL = (22, 122, 128)
MUSTARD = (244, 182, 76)
PAPER = (250, 244, 232)


def font(p, s): return ImageFont.truetype(p, s, layout_engine=ImageFont.Layout.RAQM)


def fa_text(d, xy, txt, f, fill, anchor="mm", stroke=0, sfill=None):
    d.text(xy, txt, font=f, fill=fill, anchor=anchor, direction="rtl", language="fa",
           stroke_width=stroke, stroke_fill=sfill)


def paper_box(im):
    """largest near-white blob in the upper half = the held-up paper"""
    a = np.array(im.convert("L"))
    h = a.shape[0]
    m = (a[: h // 2] > 236).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    x, y, w, hh = st[i, :4]
    return x, y, w, hh


def write_on_paper(im, txt):
    x, y, w, h = paper_box(im)
    d = ImageDraw.Draw(im)
    size = int(h * (1.25 if len(txt) == 1 else 0.78))
    fa_text(d, (x + w / 2, y + h / 2 + h * 0.04), txt, font(BOLD, size), (214, 52, 52))
    return (x, y, w, h)


def tag(im, cx, cy, txt, col):
    """rounded label with ink outline, slightly tilted, hand-made look"""
    f = font(BOLD, 74)
    tw = f.getbbox(txt)[2] - f.getbbox(txt)[0]
    W, H = tw + 70, 116
    lay = Image.new("RGBA", (W + 20, H + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([10, 10, 10 + W, 10 + H], 30, fill=col, outline=INK, width=8)
    d.text((10 + W / 2, 10 + H / 2 + 2), txt, font=f, fill="white", anchor="mm", stroke_width=5, stroke_fill=INK)
    lay = lay.rotate(-4, resample=Image.BICUBIC, expand=True)
    im.paste(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)), lay)


srcs = {i: f"{R}/{i}.jpg" for i in range(1, 14) if i != 12}
srcs[4] = f"{FIX}/4_fix.jpg"
srcs[11] = f"{FIX}/11_fix.jpg"

for i, p in srcs.items():
    im = Image.open(p).convert("RGB")
    if i == 10:  # drop the white panel border the model added
        im = im.crop((66, 106, 1470, 2640))
    if i == 1:
        print("paper s1", write_on_paper(im, "۰"))
    if i == 13:
        print("paper s13", write_on_paper(im, "۱/۲"))
    if i == 3:  # shrink + lift so the hormone/sun icons sit above the captions
        bgc = im.getpixel((40, 40))
        small = im.resize((int(im.width * 0.78), int(im.height * 0.78)), Image.LANCZOS)
        canvas = Image.new("RGB", im.size, bgc)
        canvas.paste(small, ((im.width - small.width) // 2, 260))
        im = canvas
    if i == 6:
        tag(im, 836, 1180, "LDL", (226, 160, 20))
    if i == 7:
        tag(im, 1092, 1150, "HDL", (88, 150, 70))
    im.save(f"{OUT}/s{i:02d}.png")
    print(i, im.size)

# ---- scene 12: background + card layer (card animates separately) ----
bg = Image.new("RGB", (1536, 2752), PAPER)
d = ImageDraw.Draw(bg)
rng = np.random.default_rng(3)
for _ in range(26):  # faint '+' marks like the infographic refs
    x, y = rng.integers(80, 1456), rng.integers(200, 2000)
    d.line([(x - 14, y), (x + 14, y)], fill=(222, 212, 196), width=4)
    d.line([(x, y - 14), (x, y + 14)], fill=(222, 212, 196), width=4)
bg.save(f"{OUT}/s12.png")

CW, CH = 1180, 1460
card = Image.new("RGBA", (CW + 40, CH + 40), (0, 0, 0, 0))
d = ImageDraw.Draw(card)
d.rounded_rectangle([28, 34, 28 + CW, 34 + CH], 60, fill=(0, 0, 0, 60))  # soft offset shadow
d.rounded_rectangle([12, 12, 12 + CW, 12 + CH], 60, fill="white", outline=INK, width=10)
logo = Image.open(f"{ROOT}/app-icon-tide.png").convert("RGBA").resize((210, 210), Image.LANCZOS)
card.paste(logo, (12 + CW // 2 - 105, 70), logo)
fa_text(d, (12 + CW / 2, 400), "آزمایش چربی خون", font(BOLD, 92), INK)
rows = [("LDL", "کامیون باربر", (226, 160, 20)),
        ("HDL", "ماشین زباله", (88, 150, 70)),
        ("TG", "تری‌گلیسرید", (214, 92, 70))]
y = 520
for code, label, col in rows:
    d.rounded_rectangle([90, y, 12 + CW - 78, y + 190], 40, fill=(248, 243, 234), outline=INK, width=6)
    # code pill on the right (RTL reading order)
    d.rounded_rectangle([12 + CW - 78 - 330, y + 35, 12 + CW - 78 - 40, y + 155], 34, fill=col, outline=INK, width=6)
    d.text((12 + CW - 78 - 185, y + 97), code, font=font(BOLD, 76), fill="white", anchor="mm",
           stroke_width=4, stroke_fill=INK)
    fa_text(d, (12 + CW - 78 - 380, y + 97), label, font(BOLD, 70), INK, anchor="rm")
    # empty check box on the left
    d.rounded_rectangle([140, y + 50, 230, y + 140], 18, outline=INK, width=7)
    y += 230
# teal CTA
d.rounded_rectangle([170, y + 40, 12 + CW - 158, y + 200], 80, fill=TEAL, outline=INK, width=8)
fa_text(d, (12 + CW / 2, y + 122), "نمونه‌گیری در خانه", font(BOLD, 78), "white")
card.save(f"{OUT}/card.png")
print("card", card.size)
