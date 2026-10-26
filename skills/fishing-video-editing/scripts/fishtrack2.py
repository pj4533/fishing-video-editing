#!/usr/bin/env python3
"""Bidirectional multi-keyframe NCC fish tracker.

Usage: fishtrack2.py SRC start end keyframes.json out.txt
  keyframes.json: [[t_abs, x, y, w, h], ...]  boxes in 1920x1080 coords,
  t_abs in source seconds, sorted, spanning [start, end] (first kf >= start).

For each inter-keyframe span, tracks forward from the left anchor and backward
from the right anchor (fresh template at each anchor, adaptive 0.85/0.15),
then blends positions linearly by time. Before the first / after the last
keyframe, single-direction tracking. Output: t_rel x y conf per frame @15fps.
"""
import subprocess, sys, json
import numpy as np

SRC, START, END = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
KFS = json.load(open(sys.argv[4]))
OUT = sys.argv[5]

W, H, FPS = 960, 540, 15.0
sc = W / 1920.0
DUR = END - START
cmd = ["ffmpeg", "-ss", str(START), "-i", SRC, "-t", str(DUR),
       "-vf", f"fps={FPS},scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "gray",
       "-loglevel", "error", "-"]
raw = subprocess.run(cmd, capture_output=True).stdout
n = len(raw) // (W * H)
F = np.frombuffer(raw[: n * W * H], dtype=np.uint8).reshape(n, H, W).astype(np.float32)

def clampi(v, lo, hi):
    return max(lo, min(hi, v))

def get_patch(img, cx, cy, tw, th):
    x1 = clampi(cx - tw // 2, 0, W - tw)
    y1 = clampi(cy - th // 2, 0, H - th)
    return img[y1:y1 + th, x1:x1 + tw]

def ncc_step(img, tmpl, cx, cy, tw, th, srx=90, sry=45):
    x1 = clampi(cx - tw // 2 - srx, 0, W - tw)
    x2 = clampi(cx - tw // 2 + srx, 0, W - tw)
    y1 = clampi(cy - th // 2 - sry, 0, H - th)
    y2 = clampi(cy - th // 2 + sry, 0, H - th)
    tz = tmpl - tmpl.mean()
    tn = np.sqrt((tz * tz).sum()) + 1e-6
    best, bx, by = -2.0, cx, cy
    for fine in (False, True):
        if fine:
            xr = range(max(x1, bx - tw // 2 - 4), min(x2, bx - tw // 2 + 4) + 1)
            yr = range(max(y1, by - th // 2 - 4), min(y2, by - th // 2 + 4) + 1)
        else:
            xr = range(x1, x2 + 1, 3)
            yr = range(y1, y2 + 1, 3)
        for yy in yr:
            for xx in xr:
                p = img[yy:yy + th, xx:xx + tw]
                pz = p - p.mean()
                d = np.sqrt((pz * pz).sum()) + 1e-6
                v = float((tz * pz).sum() / (tn * d))
                if v > best:
                    best, bx, by = v, xx + tw // 2, yy + th // 2
    return bx, by, best

def track(idxs, kf):
    """Track over frame indices idxs (in order given) starting at keyframe kf."""
    t_a, x_a, y_a, w_a, h_a = kf
    tw, th = max(8, int(w_a * sc)), max(8, int(h_a * sc))
    cx, cy = int((x_a + w_a / 2) * sc), int((y_a + h_a / 2) * sc)
    i0 = idxs[0]
    tmpl = get_patch(F[i0], cx, cy, tw, th).copy()
    out = {}
    for i in idxs:
        cx, cy, conf = ncc_step(F[i], tmpl, cx, cy, tw, th)
        tmpl = 0.85 * tmpl + 0.15 * get_patch(F[i], cx, cy, tw, th)
        out[i] = (cx / sc, cy / sc, conf)
    return out

def f_idx(t_abs):
    return clampi(int(round((t_abs - START) * FPS)), 0, n - 1)

pos = {}
kf_is = [f_idx(k[0]) for k in KFS]
# head: before first keyframe -> backward from first anchor
if kf_is[0] > 0:
    res = track(list(range(kf_is[0], -1, -1)), KFS[0])
    pos.update(res)
# tail: after last keyframe -> forward from last anchor
if kf_is[-1] < n - 1:
    res = track(list(range(kf_is[-1], n)), KFS[-1])
    pos.update(res)
# spans
for a in range(len(KFS) - 1):
    ia, ib = kf_is[a], kf_is[a + 1]
    if ib <= ia:
        continue
    fwd = track(list(range(ia, ib + 1)), KFS[a])
    bwd = track(list(range(ib, ia - 1, -1)), KFS[a + 1])
    for i in range(ia, ib + 1):
        u = (i - ia) / (ib - ia)
        xf, yf, cf = fwd[i]
        xb, yb, cb = bwd[i]
        pos[i] = ((1 - u) * xf + u * xb, (1 - u) * yf + u * yb, min(cf, cb))

with open(OUT, "w") as f:
    for i in sorted(pos):
        x, y, c = pos[i]
        f.write(f"{i / FPS:.4f} {x:.0f} {y:.0f} {c:.3f}\n")
xs = [pos[i][0] for i in sorted(pos)]
print(f"{OUT}: {len(pos)} frames, x range {min(xs):.0f}-{max(xs):.0f}")
