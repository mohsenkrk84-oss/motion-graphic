#!/usr/bin/env python3
"""Diet reel (silent): 1080x1920 30fps, exactly 23.41 s.
usage: python3 -I build.py out.mp4 [--preview start end]"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, '..')                  # nemonet/reels/diet-together/
W, H, FPS = 1080, 1920, 30
TOTAL = 23.41
NF = int(round(TOTAL * FPS))  # 702

def load(name):
    im = Image.open(os.path.join(IMG, name + '.jpg')).convert('RGB')
    w, h = im.size
    ch = round(w * 16 / 9)                  # crop to exact 9:16
    top = (h - ch) // 2
    im = im.crop((0, top, w, top + ch)).resize((W, H), Image.LANCZOS)
    return np.asarray(im).astype(np.float32)

names = ['01', '01-2', '02A', '02B', '03', '03-2', '04A', '04B', '05', '05-2',
         '06', '07', '08', '08-2', '09', '09-2', '09-3']
S = {n: load(n) for n in names}

# ---------- woman cut-out for clip 4 (04A minus clean plate 04B) ----------
d = np.abs(S['04A'] - S['04B']).mean(2)
m = (d > 18).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
n_, lab, stats, _ = cv2.connectedComponentsWithStats(m)
big = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
m = (lab == big).astype(np.uint8)
cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
m = np.zeros_like(m); cv2.drawContours(m, cnts, -1, 1, -1)
m = cv2.dilate(m, np.ones((9, 9), np.uint8))
M4 = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 2.5)[..., None]

# ---------- wide canvas for the pan 06 -> 07 ----------
OFF = W                                    # 07 sits right next to 06 on the canvas
seven = S['07'].copy()
sy = H / 1365.0; sx = W / 768.0            # source px -> output px
bgc = seven[int(150 * sy):int(300 * sy), int(400 * sx):int(700 * sx)].mean((0, 1))
yy, xx = np.mgrid[0:H, 0:W]
ys = yy / sy + 5; xs = xx / sx            # back to source coords (approx, 5px crop)
edge = np.where(ys < 895, 42, np.clip(42 - (ys - 895) * (30 / 115.0), 0, 42)) - 3
hide = (xs < edge) & (ys < 1015)          # the woman's hair sliver at 07's left edge
hide = cv2.GaussianBlur(hide.astype(np.float32), (0, 0), 3)[..., None]
seven = seven * (1 - hide) + bgc * hide
pan = np.concatenate([S['06'], seven], 1)

# ---------- helpers ----------
def smooth(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

def camera(img, zoom=1.0, cx=0.5, cy=0.5, dx=0.0, dy=0.0, rot=0.0):
    """zoom around (cx,cy) in fractions, translate dx,dy px, rotate deg; output W x H."""
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((cx * w, cy * h), rot, zoom)
    M[0, 2] += dx + (W - w) * 0  # img may be wider (pan canvas)
    M[1, 2] += dy
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def punch(t):  # zoom bump right after a cut
    return 0.06 * math.exp(-t / 0.13)

def shake(t, amp=14, dec=0.18, f=31):
    k = amp * math.exp(-t / dec)
    return k * math.sin(t * f * 2 * math.pi / 3), k * math.cos(t * f * 1.7 * math.pi / 3)

# ---------- clips: (start, end) ----------
CL = [(0.00, 1.17), (1.17, 3.87), (3.87, 4.80), (4.80, 7.23), (7.23, 9.93),
      (9.93, 15.27), (15.27, 19.13), (19.13, 23.41)]

def frame(T):
    for i, (s, e) in enumerate(CL):
        if s <= T < e or (i == len(CL) - 1 and T >= s):
            t, D = T - s, e - s; break
    p = punch(t) if i != 0 else 0.0
    if i == 0:   # sneak right: alternate steps, camera trucks right
        img = S['01'] if int(t / 0.2) % 2 == 0 else S['01-2']
        bob = -6 * abs(math.sin(math.pi * t / 0.2))
        return camera(img, 1.10, 0.5, 0.55, dx=-70 * t / D + 30, dy=bob)
    if i == 1:   # door: nervous wait, then bag handed over
        if t < 1.35:
            sx = 2.5 * math.sin(t * 2 * math.pi * 9)
            return camera(S['02A'], 1.02 + 0.02 * t + p, 0.45, 0.55, dx=sx)
        t2 = t - 1.35
        return camera(S['02B'], 1.05 + 0.01 * t2 + punch(t2), 0.45, 0.55)
    if i == 2:   # sneak back left
        img = S['03'] if int(t / 0.2) % 2 == 0 else S['03-2']
        bob = -6 * abs(math.sin(math.pi * t / 0.2))
        return camera(img, 1.10 + p, 0.45, 0.55, dx=60 * t / D - 25, dy=bob)
    if i == 3:   # smug hug, then slips left into the closet
        bg = S['04B']
        if t < 1.1:
            x, al, bob = 0.0, 1.0, -5 * abs(math.sin(math.pi * t / 0.55))
        else:
            u = (t - 1.1) / 0.75
            x = -230 * smooth(u)
            bob = -10 * abs(math.sin(math.pi * (t - 1.1) / 0.2))
            al = 1.0 - smooth((u - 0.45) / 0.55)
        Mt = np.float32([[1, 0, x], [0, 1, bob]])
        fg = cv2.warpAffine(S['04A'], Mt, (W, H), borderMode=cv2.BORDER_REPLICATE)
        mk = cv2.warpAffine(M4, Mt, (W, H))[..., None] * al
        img = bg * (1 - mk) + fg * mk
        dx = dy = 0.0
        if t > 1.9:
            dx, dy = shake(t - 1.9, 10)
        return camera(img, 1.04 + 0.015 * t + p, 0.4, 0.55, dx=dx, dy=dy)
    if i == 4:   # closet: huge open mouth, chomp, chew
        if t < 0.9:
            return camera(S['05-2'], 1.04 + 0.05 * t + p, 0.55, 0.45)
        t2 = t - 0.9
        dx, dy = shake(t2, 12)
        ch = 0.006 * math.sin(2 * math.pi * t2 / 0.32)
        return camera(S['05'], 1.12 + punch(t2) + ch + 0.01 * t2, 0.55, 0.42, dx=dx, dy=dy)
    if i == 5:   # caught: hold on her, whip-pan right, hold on him
        h_end, p_end = 1.67, 2.75
        u = smooth((t - h_end) / (p_end - h_end))
        x0 = OFF * u                           # canvas offset
        z = 1.0 + 0.02 * min(t, h_end) + p
        if t >= p_end:
            t3 = t - p_end
            z = 1.0 + 0.07 * math.exp(-t3 / 0.16) + 0.012 * t3
        Mt = cv2.getRotationMatrix2D((x0 + W / 2, H / 2), 0, z)
        Mt[0, 2] -= x0
        return cv2.warpAffine(pan, Mt, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if i == 6:   # victory dance: swap poses on the beat
        beat = 0.32
        k = int(t / beat)
        img = S['08'] if k % 2 == 0 else S['08-2']
        ph = (t % beat) / beat
        dy = -18 * math.sin(math.pi * ph)
        rot = 1.6 * (1 if k % 2 else -1) * math.sin(math.pi * ph)
        return camera(img, 1.05 + p, 0.5, 0.6, dy=dy, rot=rot)
    # i == 7: sit, giant bite, chew
    if t < 0.55:
        return camera(S['09'], 1.05 + p + 0.02 * t, 0.5, 0.55)
    if t < 1.35:
        t2 = t - 0.55
        return camera(S['09-2'], 1.07 + 0.06 * t2 + punch(t2), 0.5, 0.52)
    t2 = t - 1.35
    dx, dy = shake(t2, 14)
    ch = 0.006 * math.sin(2 * math.pi * t2 / 0.34)
    return camera(S['09-3'], 1.14 + punch(t2) + ch + 0.012 * t2, 0.5, 0.52, dx=dx, dy=dy)

# ---------- overlays ----------
FONT = os.path.join(HERE, '..', '..', '..', 'IRANYekanWebBlack.woff2')  # nemonet/IRANYekanWebBlack.woff2
EMOJI = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'

def make_title():
    f = ImageFont.truetype(FONT, 70)
    txt = 'روز سوم رژیم دونفره‌مون'
    tw = ImageDraw.Draw(Image.new('L', (1, 1))).textbbox((0, 0), txt, font=f, direction='rtl', language='fa')
    ef = ImageFont.truetype(EMOJI, 109)
    em = Image.new('RGBA', (140, 140)); ImageDraw.Draw(em).text((0, 0), '🍔', font=ef, embedded_color=True)
    em = em.crop(em.getbbox()).resize((82, 82), Image.LANCZOS)
    w = tw[2] - tw[0] + 18 + em.width + 40
    hgt = 150
    im = Image.new('RGBA', (w, hgt), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.text((em.width + 18 + 20 - tw[0], 30 - tw[1] + 10), txt, font=f, fill=(110, 28, 34, 255),
            direction='rtl', language='fa', stroke_width=7, stroke_fill=(255, 250, 240, 255))
    im.alpha_composite(em, (20, (hgt - em.height) // 2 + 4))
    return im

def make_handle():
    f = ImageFont.truetype(FONT, 42)
    im = Image.new('RGBA', (480, 80), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4, 8), '@nemonet.ir', font=f, fill=(70, 60, 60, 170))
    return im.crop(im.getbbox())

TITLE, HANDLE = make_title(), make_handle()
TITLE_END = 7.23

def overlay(fr, T):
    im = Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8)).convert('RGBA')
    im.alpha_composite(HANDLE, (60, 70))
    if T < TITLE_END:
        s = 0.6 + 0.4 * smooth(T / 0.25) + 0.08 * math.sin(math.pi * min(T / 0.35, 1)) if T < 0.35 else 1.0
        a = 1.0 - smooth((T - (TITLE_END - 0.2)) / 0.2)
        t = TITLE if s == 1.0 else TITLE.resize((max(1, int(TITLE.width * s)), max(1, int(TITLE.height * s))), Image.LANCZOS)
        if a < 1:
            t = t.copy(); t.putalpha(t.getchannel('A').point(lambda v: int(v * a)))
        im.alpha_composite(t, ((W - t.width) // 2, 330 - t.height // 2))
    return np.asarray(im.convert('RGB'))

def main():
    out = sys.argv[1]
    a, b = 0, NF
    if '--preview' in sys.argv:
        k = sys.argv.index('--preview'); a = int(float(sys.argv[k + 1]) * FPS); b = int(float(sys.argv[k + 2]) * FPS)
    cmd = ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
           '-movflags', '+faststart', '-an', out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(a, b):
        T = n / FPS
        pr.stdin.write(overlay(frame(T), T).tobytes())
    pr.stdin.close(); pr.wait()

if __name__ == '__main__':
    main()
