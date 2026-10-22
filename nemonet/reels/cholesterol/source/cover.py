import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
W, H = 1080, 1920
img = cv2.imread("src/s04.png"); ih, iw = img.shape[:2]
s = max(W / iw, H / ih) * 1.12; cx, cy = 720, 1220
M = np.array([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]], np.float32)
f = cv2.cvtColor(cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT), cv2.COLOR_BGR2RGB)
im = Image.fromarray(f).convert("RGBA")
ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
d.rectangle([0, 1180, W, 1640], fill=(20, 18, 24, 150))
F = lambda s: ImageFont.truetype("/home/claude/motion-graphic/IRANYekanWebBold.ttf", s, layout_engine=ImageFont.Layout.RAQM)
kw = dict(direction="rtl", language="fa", anchor="mm", stroke_width=12, stroke_fill=(20, 18, 24))
d.text((W / 2, 1300), "کلسترول بد", font=F(150), fill=(255, 206, 48), **kw)
d.text((W / 2, 1480), "واقعاً بده؟!", font=F(130), fill="white", **kw)
im = Image.alpha_composite(im, ov).convert("RGB"); im.save("cover.png")
