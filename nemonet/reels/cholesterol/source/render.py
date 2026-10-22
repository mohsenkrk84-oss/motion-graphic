"""Render the silent 1080x1920 reel from src/ images + timing.json.
usage: python3 render.py out.mp4 [--frames t1,t2,...]  (frames mode writes PNG stills)"""
import sys, json, math, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from lines import LINES

W, H, FPS = 1080, 1920, 30
ROOT = "/home/claude/motion-graphic"
BOLD = f"{ROOT}/IRANYekanWebBold.ttf"
TIM = json.load(open("timing.json"))
DUR = TIM["duration"]
SC = TIM["scenes"]


def ease(x): x = min(1, max(0, x)); return 0.5 - 0.5 * math.cos(math.pi * x)
def ease_out(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3
def ease_back(x, s=1.9):
    x = min(1, max(0, x)); x -= 1; return x * x * ((s + 1) * x + s) + 1


# camera plan per scene: zoom start/end, centre start/end (source px), push = fast first part,
# shake = list of (time_after_scene_start, amplitude_px)
CAM = {
    1:  dict(z=(1.0, 1.13), c=((770, 1250), (770, 1080)), push=0.45, shake=[(0.05, 10)]),
    2:  dict(z=(1.06, 1.14), c=((830, 1250), (830, 1150))),
    3:  dict(z=(1.0, 1.06), c=((768, 1520), (768, 1540)), shake=[(0.0, 5)]),
    4:  dict(z=(1.08, 1.28), c=((720, 1250), (700, 1150)), push=0.35),
    5:  dict(z=(1.18, 1.18), c=((768, 1650), (768, 1350))),
    6:  dict(z=(1.55, 1.62), c=((560, 1380), (1000, 1380))),
    7:  dict(z=(1.55, 1.62), c=((1150, 1360), (640, 1360))),
    8:  dict(z=(1.0, 1.18), c=((768, 1400), (770, 1480)), shake=[(0.3, 4), (1.2, 4)]),
    9:  dict(z=(1.06, 1.1), c=((768, 1300), (768, 1300)), shake=[(0.05, 22), (0.6, 10)]),
    10: dict(z=(1.0, 1.07), c=((702, 1200), (702, 1150))),
    11: dict(z=(1.0, 1.2), c=((780, 1300), (780, 1150)), push=0.3, shake=[(0.05, 8)]),
    12: dict(z=(1.0, 1.0), c=((768, 1376), (768, 1376))),
    13: dict(z=(1.0, 1.13), c=((770, 1250), (770, 1080)), push=0.45, shake=[(0.6, 8)]),
}

IMGS = {i: cv2.imread(f"src/s{i:02d}.png") for i in range(1, 14)}
CARD = np.array(Image.open("src/card.png").convert("RGBA"))


def scene_at(t):
    i = 0
    while i + 1 < len(SC) and t >= SC[i + 1]: i += 1
    return i + 1, t - SC[i], (SC[i + 1] if i + 1 < len(SC) else DUR) - SC[i]


def camera(si, lt, ld):
    p = CAM[si]
    img = IMGS[si]; ih, iw = img.shape[:2]
    if "push" in p:  # quick push then slow drift
        k = 0.7 * ease_out(lt / p["push"]) + 0.3 * ease(lt / max(ld, 0.01))
    else:
        k = ease(lt / max(ld, 0.01))
    z = p["z"][0] + (p["z"][1] - p["z"][0]) * k
    cx = p["c"][0][0] + (p["c"][1][0] - p["c"][0][0]) * k
    cy = p["c"][0][1] + (p["c"][1][1] - p["c"][0][1]) * k
    # gentle hand-held drift
    cx += 3.0 * math.sin(lt * 1.3 + si); cy += 2.5 * math.cos(lt * 1.1 + si * 2)
    s = max(W / iw, H / ih) * z
    hw, hh = W / 2 / s, H / 2 / s
    cx = min(max(cx, hw), iw - hw); cy = min(max(cy, hh), ih - hh)
    dx = dy = 0.0
    for t0, a in p.get("shake", []):
        u = lt - t0
        if 0 <= u < 0.35:
            dec = (1 - u / 0.35) ** 2
            dx += a * dec * math.sin(u * 95); dy += a * dec * math.cos(u * 77)
    M = np.array([[s, 0, W / 2 - cx * s + dx], [0, s, H / 2 - cy * s + dy]], np.float32)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


# ---------------- captions ----------------
FONT = ImageFont.truetype(BOLD, 80, layout_engine=ImageFont.Layout.RAQM)
WHITE, YEL, INK = (255, 255, 255), (255, 206, 48), (20, 18, 24)
STROKE = 10
MAXW = 940
CAP_Y = 1500  # vertical centre of the caption block


def word_img(w):
    kw = w.startswith("*")
    txt = w.strip("*")
    bb = FONT.getbbox(txt, direction="rtl", language="fa", stroke_width=STROKE)
    im = Image.new("RGBA", (bb[2] - bb[0] + 8, 140), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - bb[0], 70), txt, font=FONT, fill=YEL if kw else WHITE, anchor="lm",
                            direction="rtl", language="fa", stroke_width=STROKE, stroke_fill=INK)
    return np.array(im)


SPACE = 22
CHUNKS = []  # list of dict(words=[(img, x, y)], times=[...], end)
for li, (spk, chunks) in enumerate(LINES):
    L = TIM["lines"][li]
    wt = L["words"]
    nxt = SC[li + 1] if li + 1 < len(SC) else DUR
    k = 0
    starts = []
    for ch in chunks:
        starts.append(k); k += len(ch)
    for ci, ch in enumerate(chunks):
        imgs = [word_img(w) for w in ch]
        rows, cur, curw = [], [], 0
        for im in imgs:  # wrap right-to-left
            w_ = im.shape[1]
            if cur and curw + SPACE + w_ > MAXW:
                rows.append(cur); cur, curw = [], 0
            cur.append(im); curw += (SPACE if len(cur) > 1 else 0) + w_
        rows.append(cur)
        placed = []
        rh = 104
        y0 = CAP_Y - rh * (len(rows) - 1) / 2
        for r, row in enumerate(rows):
            tw = sum(im.shape[1] for im in row) + SPACE * (len(row) - 1)
            x = W / 2 + tw / 2  # start at right edge
            for im in row:
                x -= im.shape[1]
                placed.append((im, int(x), int(y0 + r * rh - 70)))
                x -= SPACE
        times = wt[starts[ci]:starts[ci] + len(ch)]
        end = (wt[starts[ci + 1]] if ci + 1 < len(chunks) else nxt)
        CHUNKS.append(dict(words=placed, times=times, end=end))


def blend(frame, rgba, x, y, scale=1.0):
    if scale != 1.0:
        h0, w0 = rgba.shape[:2]
        nw, nh = max(1, int(w0 * scale)), max(1, int(h0 * scale))
        rgba = cv2.resize(rgba, (nw, nh), interpolation=cv2.INTER_LINEAR)
        x += (w0 - nw) // 2; y += (h0 - nh) // 2
    h, w = rgba.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1: return
    src = rgba[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32)
    a = src[..., 3:4] / 255.0
    roi = frame[y0:y1, x0:x1].astype(np.float32)
    roi = roi * (1 - a) + src[..., 2::-1] * a  # RGBA -> BGR
    frame[y0:y1, x0:x1] = roi.astype(np.uint8)


def captions(frame, t):
    for ch in CHUNKS:
        if ch["times"][0] - 0.02 <= t < ch["end"]:
            for (im, x, y), wt in zip(ch["words"], ch["times"]):
                u = t - wt
                if u < -0.02: continue
                blend(frame, im, x, y, 0.7 + 0.3 * ease_back(u / 0.14) if u < 0.14 else 1.0)


def card(frame, lt):
    sc = 0.703 * (0.55 + 0.45 * ease_back(lt / 0.45, 2.2))
    if lt < 0: return
    ch, cw = CARD.shape[:2]
    rgba = cv2.resize(CARD, (int(cw * sc), int(ch * sc)), interpolation=cv2.INTER_AREA)
    blend(frame, rgba, W // 2 - rgba.shape[1] // 2, 880 - rgba.shape[0] // 2)


def frame_at(t):
    si, lt, ld = scene_at(t)
    f = camera(si, lt, ld)
    if si == 12: card(f, lt - 0.05)
    captions(f, t)
    return f


if __name__ == "__main__":
    out = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == "--frames":
        for t in map(float, sys.argv[3].split(",")):
            cv2.imwrite(f"{out}_{t:05.2f}.png", frame_at(t))
        sys.exit()
    n = int(round(DUR * FPS))
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                          "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame_at(i / FPS).tobytes())
        if i % 150 == 0: print(f"{i}/{n}", flush=True)
    p.stdin.close(); p.wait()
    print("done", out, n, "frames")
