#!/usr/bin/env python3
"""Per-frame wildlife tracker at NATIVE 4K: keyframe-anchored, bidirectional VitTrack.

Same discipline as fishtrack2.py — human keyframe anchors, track
each inter-anchor span forward from the left anchor AND backward from the right anchor,
blend linearly by time — but with OpenCV's VitTrack (a transformer tracker, ~5 ms/update,
searches only a window around the box so 4K costs nothing extra) instead of NCC on a
960x540 proxy, which is too coarse for a 30-80 px bird. VitTrack reports a tracking score:
< --min-score in BOTH directions marks the frame LOST and the position is interpolated
between the nearest confident frames (or held at the edge of a span).

Usage:
  wildlife_track.py SRC.MP4 START END keyframes.json track.txt [--verify sheet.jpg] [--min-score 0.3]
    keyframes.json: [[t_abs, x, y, w, h], ...] boxes in 3840x2160 px (x,y = top-left),
                    sorted by time, all inside [START, END]. One anchor every ~2-3 s of
                    visible time; more where the animal changes shape (take-off) or the head
                    pans fast. Read boxes off big single frames (crop + scale + drawgrid).
    track.txt: one line per frame  t_abs cx cy w h score flag   (flag: ok | lost)
    --verify: 480 px crops around the tracked box every 0.35 s with the box drawn —
              LOOK at every tile before reframing (a box off the bird = fix the anchor).
Model: $WILDLIFE_MODELS/object_tracking_vittrack_2023sep.onnx (default ~/.wildlife-models;
references/setup.md). Needs opencv-contrib-python (cv2.TrackerVit). Decode uses
-hwaccel videotoolbox on macOS (override with $FFMPEG_HWACCEL, e.g. "cuda" or "none").
"""
import argparse, json, os, subprocess, sys
import numpy as np
import cv2
# hardware decode: VideoToolbox on macOS, none elsewhere; override with $FFMPEG_HWACCEL ("cuda", "vaapi", "none")
_hw = os.environ.get("FFMPEG_HWACCEL", "videotoolbox" if sys.platform == "darwin" else "none")
HWACCEL = [] if _hw == "none" else ["-hwaccel", _hw]

MODELS = os.environ.get("WILDLIFE_MODELS", os.path.expanduser("~/.wildlife-models"))
FPS = 30000 / 1001
W, H = 3840, 2160


def decode_jpegs(src, start, end):
    """All frames of [start,end) as in-memory JPEGs (≈1 MB each) so we can walk them both ways."""
    cmd = ["ffmpeg", "-loglevel", "error", *HWACCEL, "-ss", f"{start:.3f}", "-i", src,
           "-t", f"{end - start:.3f}", "-pix_fmt", "bgr24", "-f", "rawvideo", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 3 * 2)
    n = W * H * 3; out = []
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        f = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        out.append(cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 92])[1])
        if len(out) % 100 == 0:
            print(f"  decoded {len(out)} frames", file=sys.stderr)
    p.stdout.close(); p.wait()
    return out


def new_tracker():
    prm = cv2.TrackerVit_Params()
    prm.net = os.path.join(MODELS, "object_tracking_vittrack_2023sep.onnx")
    # never let the tracker give up internally (it would return (0,0,0,0) forever after one
    # low-score frame in a whip pan); we gate on the score ourselves with --min-score
    prm.tracking_score_threshold = 0.0
    return cv2.TrackerVit_create(prm)


def run(jpegs, idxs, box):
    """Track over frame indices idxs (in the order given), initialised with box on idxs[0]."""
    tr = new_tracker()
    f0 = cv2.imdecode(jpegs[idxs[0]], cv2.IMREAD_COLOR)
    x, y, w, h = [int(round(v)) for v in box]
    tr.init(f0, (x, y, w, h))
    out = {idxs[0]: (x + w / 2, y + h / 2, w, h, 1.0)}
    for i in idxs[1:]:
        f = cv2.imdecode(jpegs[i], cv2.IMREAD_COLOR)
        ok, bb = tr.update(f)
        sc = float(tr.getTrackingScore())
        bx, by, bw, bh = bb
        # a box that balloons past 3x the anchor is the tracker latching onto background
        if not ok or bw > 3 * max(w, 20) or bh > 3 * max(h, 20):
            sc = 0.0
        out[i] = (bx + bw / 2, by + bh / 2, bw, bh, sc)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src"); ap.add_argument("start", type=float); ap.add_argument("end", type=float)
    ap.add_argument("keyframes"); ap.add_argument("out")
    ap.add_argument("--verify"); ap.add_argument("--min-score", type=float, default=0.3)
    a = ap.parse_args()
    kfs = json.load(open(a.keyframes))
    assert kfs == sorted(kfs, key=lambda k: k[0]), "keyframes must be sorted by time"
    jpegs = decode_jpegs(a.src, a.start, a.end)
    n = len(jpegs)
    fi = lambda t: int(np.clip(round((t - a.start) * FPS), 0, n - 1))
    kf_i = [fi(k[0]) for k in kfs]
    pos = {}
    if kf_i[0] > 0:                                   # head: backward from the first anchor
        pos.update(run(jpegs, list(range(kf_i[0], -1, -1)), kfs[0][1:5]))
    if kf_i[-1] < n - 1:                              # tail: forward from the last anchor
        pos.update(run(jpegs, list(range(kf_i[-1], n)), kfs[-1][1:5]))
    for k in range(len(kfs) - 1):
        ia, ib = kf_i[k], kf_i[k + 1]
        if ib <= ia:
            continue
        fwd = run(jpegs, list(range(ia, ib + 1)), kfs[k][1:5])
        bwd = run(jpegs, list(range(ib, ia - 1, -1)), kfs[k + 1][1:5])
        for i in range(ia, ib + 1):
            u = (i - ia) / (ib - ia)
            xf, yf, wf, hf, sf = fwd[i]; xb, yb, wb, hb, sb = bwd[i]
            if sf < a.min_score and sb >= a.min_score:
                pos[i] = (xb, yb, wb, hb, sb)
            elif sb < a.min_score and sf >= a.min_score:
                pos[i] = (xf, yf, wf, hf, sf)
            else:
                pos[i] = ((1 - u) * xf + u * xb, (1 - u) * yf + u * yb, (1 - u) * wf + u * wb, (1 - u) * hf + u * hb, min(sf, sb))
    # anchors themselves are ground truth
    for k, i in zip(kfs, kf_i):
        x, y, w, h = k[1:5]; pos[i] = (x + w / 2, y + h / 2, w, h, 1.0)
    # lost frames -> interpolate between confident neighbours
    idx = np.arange(n)
    good = np.array([pos[i][4] >= a.min_score for i in idx])
    arr = np.array([pos[i][:4] for i in idx], dtype=float)
    if good.sum() >= 2 and not good.all():
        for c in range(4):
            arr[~good, c] = np.interp(idx[~good], idx[good], arr[good, c])
    lost = int((~good).sum())
    with open(a.out, "w") as f:
        for i in idx:
            cx, cy, w, h = arr[i]
            f.write(f"{a.start + i / FPS:.4f} {cx:.1f} {cy:.1f} {w:.0f} {h:.0f} {pos[i][4]:.3f} {'ok' if good[i] else 'lost'}\n")
    print(f"{a.out}: {n} frames, {lost} lost/interpolated, x {arr[:,0].min():.0f}-{arr[:,0].max():.0f}, "
          f"y {arr[:,1].min():.0f}-{arr[:,1].max():.0f}, bird w {arr[:,2].min():.0f}-{arr[:,2].max():.0f}")
    if a.verify:
        step = max(1, int(round(0.35 * FPS))); tiles = []
        for i in range(0, n, step):
            f = cv2.imdecode(jpegs[i], cv2.IMREAD_COLOR)
            cx, cy, w, h = arr[i]; r = 240
            x0, y0 = int(np.clip(cx - r, 0, W - 2 * r)), int(np.clip(cy - r, 0, H - 2 * r))
            crop = f[y0:y0 + 2 * r, x0:x0 + 2 * r].copy()
            col = (0, 255, 0) if good[i] else (0, 0, 255)
            cv2.rectangle(crop, (int(cx - w / 2 - x0), int(cy - h / 2 - y0)), (int(cx + w / 2 - x0), int(cy + h / 2 - y0)), col, 2)
            cv2.putText(crop, f"{a.start + i / FPS:.2f}s {pos[i][4]:.2f}", (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            tiles.append(crop)
        cols = 6
        while len(tiles) % cols:
            tiles.append(np.zeros_like(tiles[0]))
        cv2.imwrite(a.verify, np.vstack([np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]),
                    [cv2.IMWRITE_JPEG_QUALITY, 85])
        print("verify sheet:", a.verify)


if __name__ == "__main__":
    main()
