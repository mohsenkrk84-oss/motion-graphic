"""Turn a tinted face region white: flood-fill from seed points (LAB tolerance),
then shift the region's colour so its median becomes near-white, keeping shading."""
import sys, cv2, numpy as np

src, dst = sys.argv[1], sys.argv[2]
args = sys.argv[3:]
box = None
if args and args[0].startswith('box='):
    box = tuple(map(int, args[0][4:].split(','))); args = args[1:]
tol = (14, 7, 9)
if args and args[0].startswith('tol='):
    t = int(args[0][4:]); tol = (t, max(3, t // 2), max(4, t * 2 // 3)); args = args[1:]
seeds = [tuple(map(int, a.split(','))) for a in args]
img = cv2.imread(src)
h, w = img.shape[:2]
lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
mask = np.zeros((h + 2, w + 2), np.uint8)
for (x, y) in seeds:
    cv2.floodFill(lab.copy(), mask, (x, y), 0, tol, tol,
                  cv2.FLOODFILL_MASK_ONLY | (255 << 8) | 8)
m = mask[1:-1, 1:-1] > 0
if box:
    bm = np.zeros_like(m); x0,y0,x1,y1 = box; bm[y0:y1, x0:x1] = True; m &= bm
# close small holes (shading speckles) but don't cross black lines
m8 = cv2.morphologyEx(m.astype(np.uint8) * 255, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
dark = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) < 70
m8 &= ~dark
f = img.astype(np.float32)
base = np.median(f[m8], axis=0)
target = np.array([246, 249, 250], np.float32)  # BGR near-white, tiny cool
out = f.copy()
out[m8] = np.clip(f[m8] + (target - base), 0, 255)
# soften the edge of the mask
soft = cv2.GaussianBlur(m8.astype(np.float32), (5, 5), 0)[..., None]
res = f * (1 - soft) + out * soft
cv2.imwrite(dst, res.astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95])
print(src, 'region px', int(m8.sum()), 'base BGR', base.round())
