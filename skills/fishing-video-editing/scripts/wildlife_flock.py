#!/usr/bin/env python3
"""Turn a wildlife_scan.py scan.json of a FLOCK (many small detections per frame) into a
track.txt for wildlife_reframe.py that follows the flock as a whole.

A flock is not one target: birds drop in and out of detection, the count per frame jumps
(1..19 per frame on one tested goose V), and the median of a few birds is not the flock's centre.
So per sample: the flock box is the min/max of all detection centres; the subject is the
box midpoint; the "bird size" written to the track is the flock's extent (so the
reframer's auto-width = k × size holds the whole V). Samples with fewer than --min-n
detections contribute a centre only if it lies within --jump px of the previous flock
centre (a lone far bird or junk should not yank the camera). Gaps are linearly
interpolated; the reframer then smooths.

Usage:
  wildlife_flock.py scan.json track.txt [--start S --end E] [--min-n 2] [--jump 700] [--pad 200]
    track.txt lines: t_abs cx cy w h score flag   (w,h = flock extent + pad)
"""
import argparse, json
import numpy as np

FPS = 30000 / 1001


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scan"); ap.add_argument("out")
    ap.add_argument("--start", type=float); ap.add_argument("--end", type=float)
    ap.add_argument("--min-n", type=int, default=2); ap.add_argument("--jump", type=float, default=700)
    ap.add_argument("--pad", type=float, default=200)
    a = ap.parse_args()
    d = json.load(open(a.scan))
    pts = []                                    # (t, cx, cy, w, h, n)
    last = None
    for s in d["samples"]:
        t = s["t"]
        if (a.start is not None and t < a.start) or (a.end is not None and t > a.end) or not s["dets"]:
            continue
        b = np.array([x["box"] for x in s["dets"]], dtype=float)
        cx = (b[:, 0] + b[:, 2]) / 2; cy = (b[:, 1] + b[:, 3]) / 2
        mx, my = (cx.min() + cx.max()) / 2, (cy.min() + cy.max()) / 2
        if len(b) >= a.min_n:
            w, h = cx.max() - cx.min() + a.pad, cy.max() - cy.min() + a.pad
            pts.append((t, mx, my, w, h, len(b))); last = (mx, my, w, h)
        elif last is not None and np.hypot(mx - last[0], my - last[1]) <= a.jump:
            pts.append((t, mx, my, last[2], last[3], len(b)))
    if len(pts) < 2:
        raise SystemExit("not enough flock samples")
    P = np.array(pts)
    start = a.start if a.start is not None else P[0, 0]
    end = a.end if a.end is not None else P[-1, 0]
    n = int(round((end - start) * FPS)); t = start + np.arange(n) / FPS
    with open(a.out, "w") as f:
        for i in range(n):
            cx = np.interp(t[i], P[:, 0], P[:, 1]); cy = np.interp(t[i], P[:, 0], P[:, 2])
            w = np.interp(t[i], P[:, 0], P[:, 3]); h = np.interp(t[i], P[:, 0], P[:, 4])
            ok = P[:, 0].min() - 0.6 <= t[i] <= P[:, 0].max() + 0.6
            f.write(f"{t[i]:.4f} {cx:.1f} {cy:.1f} {w:.0f} {h:.0f} {1.0 if ok else 0.0:.3f} {'ok' if ok else 'lost'}\n")
    print(f"{a.out}: {n} frames from {len(pts)} flock samples ({P[0,0]:.2f}-{P[-1,0]:.2f}s), "
          f"extent {P[:,3].min():.0f}-{P[:,3].max():.0f} px wide, birds/sample max {int(P[:,5].max())}")


if __name__ == "__main__":
    main()
