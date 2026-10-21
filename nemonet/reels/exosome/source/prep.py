"""Precompute per-scene animation layers (line draw order, fills, circles) -> npz."""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage.graph import MCP_Geometric

W, H = 1080, 1920
BG = np.array([247, 238, 221], np.float32)


def fit_circle(ys, xs):
    A = np.c_[xs, ys, np.ones_like(xs)]
    b = -(xs ** 2 + ys ** 2)
    (D, E, F), *_ = np.linalg.lstsq(A, b, rcond=None)
    cx, cy = -D / 2, -E / 2
    r = np.sqrt(max(cx ** 2 + cy ** 2 - F, 1))
    return cy, cx, r


def prep(src, points, out):
    img = Image.open(src).convert("RGB").resize((1080, 1935), Image.LANCZOS)
    im = np.array(img).astype(np.float32)[8:8 + H]
    L = im.mean(2)
    core = L < 100
    lineA = np.clip((165 - L) / 95, 0, 1)
    halo = ndi.binary_dilation(core, iterations=2)
    lineA[~halo] = 0

    conn = ndi.binary_dilation(core, iterations=1)
    lab, n = ndi.label(conn, structure=np.ones((3, 3)))
    objs = ndi.find_objects(lab)
    sizes = ndi.sum(conn, lab, range(1, n + 1))
    # big strokes first, then by vertical position
    order = sorted(range(1, n + 1), key=lambda i: (sizes[i - 1] < 1500, objs[i - 1][0].start))
    starts = []
    for i in order:
        sl = objs[i - 1]
        ys, xs = np.nonzero(lab[sl] == i)
        k = np.argmin(ys * 10000 + xs)
        starts.append((ys[k] + sl[0].start, xs[k] + sl[1].start))
    dist, _ = MCP_Geometric(np.where(conn, 1.0, np.inf)).find_costs(starts)
    dist[~conn] = 0
    start_t = np.zeros(n + 1, np.float32)
    for rank, i in enumerate(order):
        start_t[i] = 0.05 + 0.5 * (rank / max(1, n - 1))
    speed = max(float(dist[conn].max()) / 1.0, 1.0)
    tline = (start_t[lab] + dist / speed).astype(np.float32)
    tline[~conn] = 99
    _, (iy, ix) = ndi.distance_transform_edt(~conn, return_indices=True)
    tline = tline[iy, ix]

    diff = np.abs(im - BG).sum(2)
    colored = (diff > 20) & ~halo
    bgmask = (diff <= 20) & ~halo
    circ_masks, circ_par = [], []
    for (sx, sy) in points:
        c = im[sy - 3:sy + 4, sx - 3:sx + 4].reshape(-1, 3).mean(0)
        m = colored & (np.abs(im - c).sum(2) < 34)
        lb, _ = ndi.label(m)
        k = lb[sy, sx]
        if k == 0:
            print("  miss circle at", sx, sy)
            continue
        m = ndi.binary_closing(lb == k, iterations=3)
        edge = m & ndi.binary_dilation(bgmask, iterations=2)
        ys, xs = np.nonzero(edge)
        cy, cx, r = fit_circle(ys.astype(float), xs.astype(float))
        ys2, xs2 = np.nonzero(m)
        rmax = np.sqrt(((ys2 - cy) ** 2 + (xs2 - cx) ** 2).max())
        if not (50 < r < 900) or rmax > r * 1.4:
            cy, cx = ys2.mean(), xs2.mean()
            r = np.sqrt(((ys2 - cy) ** 2 + (xs2 - cx) ** 2).max())
        else:
            r = max(r, rmax)
        circ_masks.append(m)
        circ_par.append((cy, cx, r))
        print(f"  circle at ({cx:.0f},{cy:.0f}) r={r:.0f}")
    circ_any = np.zeros_like(colored)
    for m in circ_masks:
        circ_any |= m
    fill = colored & ~circ_any

    rng = np.random.default_rng(3)
    nz = ndi.gaussian_filter(rng.random((H, W)), (1.5, 9))
    nz = ndi.rotate(nz, 35, reshape=False, mode="reflect")
    nz = (nz - nz.min()) / (nz.max() - nz.min())
    yy = np.mgrid[0:H, 0:W][0]
    tfill = (1.05 + 0.75 * (0.55 * np.clip((yy - 650) / 1250, 0, 1) + 0.45 * nz)).astype(np.float32)

    circ_id = np.full((H, W), -1, np.int8)
    for k, m in enumerate(circ_masks):
        circ_id[m] = k
    np.savez_compressed(out, im=im.astype(np.uint8), lineA=lineA.astype(np.float16),
                        tline=tline.astype(np.float16), fill=fill, tfill=tfill.astype(np.float16),
                        circ_id=circ_id, circ_par=np.array(circ_par, np.float32).reshape(-1, 3))
    print(out, n, "strokes")


if __name__ == "__main__":
    R, OUTD = sys.argv[1], sys.argv[2]
    scenes = {
        "s1": ("Gemini_Generated_Image_2ga6jg2ga6jg2ga6.jpg", [(150, 915), (930, 930), (990, 1440), (70, 1620)]),
        "s2": ("Gemini_Generated_Image_c2mjyrc2mjyrc2mj.jpg", [(800, 1100), (900, 860)]),
        "s3": ("Gemini_Generated_Image_rbwgzmrbwgzmrbwg.jpg", [(720, 1100), (900, 880)]),
        "s4": ("Gemini_Generated_Image_kfg970kfg970kfg9.jpg", [(120, 800), (760, 1150), (900, 900), (160, 1250)]),
    }
    for k in sys.argv[3:] or scenes:
        f, pts = scenes[k]
        print(k)
        prep(os.path.join(R, f), pts, os.path.join(OUTD, k + ".npz"))
