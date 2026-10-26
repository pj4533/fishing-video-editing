#!/usr/bin/env python3
"""Find FLYING wildlife in head-cam footage by motion (no models, offline).

What it does: for every frame, estimates the camera's own motion (ORB features + RANSAC
homography against the frame 1 back AND 5 back), warps those frames onto the current one,
differences both, and keeps only pixels that differ in BOTH (dual-interval differencing —
kills head-jitter noise, keeps real movers). A sky mask (bright upper part of the frame)
throws away water ripples, the rod and the kayak. Blobs are linked into tracklets by
nearest-neighbour with constant-velocity prediction; tracklets are scored by
length × contrast. In testing on 4K head-cam footage the top-scored track in each
audio-cue window WAS the bird (151 frames through an eagle take-off, 84 frames of a
~20 px far flyover), with 2-4× score margin over rod/line false tracks.

Blind spots (by construction): a PERCHED / motionless animal (use wildlife_scan.py), a
dark bird against dark near-shore trees (no sky behind it), whip pans (skipped frames).

Usage:
  wildlife_motion.py SRC.MP4 OUTDIR --start S --dur D [--proc-w 1920] [--top 6] [--no-sky-mask] [--sky-max-frac 0.55]
    Animal in/on the WATER (swimming deer, beaver): --no-sky-mask --sky-max-frac 0.8
    (expect ripple junk in the crops).
    Writes OUTDIR/tracks.json (all kept tracklets, best first, points in SOURCE 4K px)
    and OUTDIR/trackN_crops.jpg (8 crops along each of the top tracks — LOOK at them:
    the bird is obvious, a rod tip / line is obvious too).
  Cost: ~85 ms per 4K frame on an Apple-silicon laptop (decode via videotoolbox → 1920 gray;
  videotoolbox is macOS-only — elsewhere set $FFMPEG_HWACCEL, e.g. "cuda" or "none").
  Then hand the chosen track's first point to wildlife_track.py as the first keyframe.
"""
import argparse, json, math, os, subprocess, sys, time
import numpy as np
import cv2
# hardware decode: VideoToolbox on macOS, none elsewhere; override with $FFMPEG_HWACCEL ("cuda", "vaapi", "none")
_hw = os.environ.get("FFMPEG_HWACCEL", "videotoolbox" if sys.platform == "darwin" else "none")
HWACCEL = [] if _hw == "none" else ["-hwaccel", _hw]

PARAMS = dict(
    orb_features=3000, ransac_thresh=3.0,
    min_inliers=60,          # below this the frame is a whip pan -> skipped
    max_shift_px=60.0,       # median inlier displacement above this -> skipped
    diff_thresh=25, blur_ksize=5,
    sky_gray_thresh=120, sky_close=25, sky_erode=15,
    sky_max_frac=0.55,       # rows below this fraction of height are never sky
    area_min=6, area_max=2500,
    link_dist=40.0, min_track_len=5, max_vel_std=12.0, max_gap=1,
    merge_dilate=15,         # wing/body fragments closer than this are one blob
)
FPS = 30000 / 1001


def gray_frames(path, start, dur, w, h):
    cmd = ["ffmpeg", "-loglevel", "error", *HWACCEL, "-ss", f"{start:.3f}", "-i", path,
           "-t", f"{dur:.3f}", "-vf", f"scale={w}:{h}", "-pix_fmt", "gray", "-f", "rawvideo", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=w * h * 8)
    n = w * h
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        yield np.frombuffer(buf, np.uint8).reshape(h, w)
    p.stdout.close(); p.wait()


class Compensator:
    def __init__(self, P):
        self.P = P
        self.orb = cv2.ORB_create(P["orb_features"])
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.hist = []

    def push(self, gray):
        kps, desc = self.orb.detectAndCompute(gray, None)
        pts = np.float32([k.pt for k in kps]) if kps else np.zeros((0, 2), np.float32)
        self.hist.append((gray, pts, desc))
        if len(self.hist) > 6:
            self.hist.pop(0)

    def homography(self, back):
        if len(self.hist) <= back:
            return None
        g0, p0, d0 = self.hist[-1 - back]
        g1, p1, d1 = self.hist[-1]
        if d0 is None or d1 is None or len(p0) < 20 or len(p1) < 20:
            return None
        m = self.bf.match(d0, d1)
        if len(m) < 20:
            return None
        a = np.float32([p0[x.queryIdx] for x in m]); b = np.float32([p1[x.trainIdx] for x in m])
        H, inl = cv2.findHomography(a, b, cv2.RANSAC, self.P["ransac_thresh"])
        if H is None:
            return None
        inl = inl.ravel().astype(bool); n_inl = int(inl.sum())
        shift = float(np.median(np.linalg.norm(b[inl] - a[inl], axis=1))) if n_inl else 1e9
        return H, n_inl, shift


def sky_mask(gray, P):
    h = gray.shape[0]
    if P.get("no_sky"):        # --no-sky-mask: everything above sky_max_frac (bird against a hillside)
        m = np.ones(gray.shape, np.uint8); m[int(P["sky_max_frac"] * h):] = 0
        return m
    m = (gray > P["sky_gray_thresh"]).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((P["sky_close"], P["sky_close"]), np.uint8))
    m = cv2.erode(m, np.ones((P["sky_erode"], P["sky_erode"]), np.uint8))
    m[int(P["sky_max_frac"] * h):] = 0
    return m


def detect_frame(comp, cur, P):
    Hh, W = cur.shape
    r1, r5 = comp.homography(1), comp.homography(5)
    if r1 is None or r5 is None:
        return [], "no_homography"
    H1, n1, s1 = r1; H5, n5, s5 = r5
    if n1 < P["min_inliers"] or n5 < P["min_inliers"]:
        return [], "few_inliers"
    if s1 > P["max_shift_px"]:
        return [], "whip_pan"
    k = P["blur_ksize"]
    curb = cv2.GaussianBlur(cur, (k, k), 0)
    w1 = cv2.warpPerspective(comp.hist[-2][0], H1, (W, Hh), borderMode=cv2.BORDER_REPLICATE)
    w5 = cv2.warpPerspective(comp.hist[-6][0], H5, (W, Hh), borderMode=cv2.BORDER_REPLICATE)
    d1 = cv2.absdiff(cv2.GaussianBlur(w1, (k, k), 0), curb)
    d5 = cv2.absdiff(cv2.GaussianBlur(w5, (k, k), 0), curb)
    t = P["diff_thresh"]
    mask = ((d1 > t) & (d5 > t)).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    mask *= sky_mask(cur, P)
    md = P["merge_dilate"]
    grp = cv2.dilate(mask, np.ones((md, md), np.uint8)) if md > 0 else mask
    n, lab, st, _ = cv2.connectedComponentsWithStats(grp, connectivity=8)
    dmin = np.minimum(d1, d5)
    blobs = []
    for i in range(1, n):
        x, y, w, h, _ = st[i]
        cm = (lab[y:y + h, x:x + w] == i) & (mask[y:y + h, x:x + w] > 0)
        area = int(cm.sum())
        if P["area_min"] <= area <= P["area_max"]:
            ys_, xs_ = np.nonzero(cm)
            blobs.append((float(x + xs_.mean()), float(y + ys_.mean()), int(x), int(y), int(w), int(h), area,
                          float(dmin[y:y + h, x:x + w][cm].mean())))
    return blobs, "ok"


def link_tracklets(per_frame, P):
    active, done = [], []
    for fi, blobs in enumerate(per_frame):
        used = set()
        for tr in active:
            lx, ly = tr["pts"][-1][1], tr["pts"][-1][2]
            if len(tr["pts"]) >= 2:
                px, py = tr["pts"][-2][1], tr["pts"][-2][2]
                dt = tr["pts"][-1][0] - tr["pts"][-2][0]; gap = fi - tr["pts"][-1][0]
                lx += (lx - px) / dt * gap; ly += (ly - py) / dt * gap
            best, bd = None, P["link_dist"]
            for bi, b in enumerate(blobs):
                if bi in used:
                    continue
                d = math.hypot(b[0] - lx, b[1] - ly)
                if d < bd:
                    best, bd = bi, d
            if best is not None:
                used.add(best); tr["pts"].append((fi,) + tuple(blobs[best]))
        still = []
        for tr in active:
            (done if fi - tr["pts"][-1][0] > P["max_gap"] else still).append(tr)
        active = still
        for bi, b in enumerate(blobs):
            if bi not in used:
                active.append({"pts": [(fi,) + tuple(b)]})
    done += active
    kept = []
    for tr in done:
        pts = tr["pts"]
        if len(pts) < P["min_track_len"]:
            continue
        v = np.diff(np.array([[p[1], p[2]] for p in pts]), axis=0) / np.diff([p[0] for p in pts])[:, None]
        vstd = float(np.linalg.norm(v.std(axis=0)))
        if vstd > P["max_vel_std"]:
            continue
        tr.update(start=pts[0][0], end=pts[-1][0], n=len(pts), vel_std=vstd,
                  speed=float(np.linalg.norm(v.mean(axis=0))),
                  mean_contrast=float(np.mean([p[8] for p in pts])), mean_area=float(np.mean([p[7] for p in pts])),
                  score=len(pts) * float(np.mean([p[8] for p in pts])))
        kept.append(tr)
    kept.sort(key=lambda t: -t["score"])
    return kept


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src"); ap.add_argument("outdir")
    ap.add_argument("--start", type=float, required=True); ap.add_argument("--dur", type=float, required=True)
    ap.add_argument("--proc-w", type=int, default=1920); ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--no-sky-mask", action="store_true", help="search the whole upper frame (bird against a dark hillside); expect more junk tracklets")
    ap.add_argument("--sky-max-frac", type=float, default=PARAMS["sky_max_frac"], help="rows below this fraction of height are never searched")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    pw = a.proc_w; ph = pw * 9 // 16
    P = dict(PARAMS); P["no_sky"] = a.no_sky_mask; P["sky_max_frac"] = a.sky_max_frac
    comp = Compensator(P); per_frame, statuses, keep = [], {}, []
    t0 = time.time()
    for g in gray_frames(a.src, a.start, a.dur, pw, ph):
        comp.push(g)
        blobs, st = detect_frame(comp, g, P)
        per_frame.append(blobs); statuses[st] = statuses.get(st, 0) + 1; keep.append(g)
        if len(keep) % 100 == 0:
            print(f"  {len(keep)} frames, {(time.time() - t0) / len(keep) * 1000:.0f} ms/frame", file=sys.stderr)
    tracks = link_tracklets(per_frame, P)
    sc = 3840 / pw
    out = dict(src=a.src, start=a.start, dur=a.dur, proc_w=pw, n_frames=len(keep), statuses=statuses, tracks=[])
    for tr in tracks:
        out["tracks"].append(dict(
            t_start=round(a.start + tr["start"] / FPS, 3), t_end=round(a.start + tr["end"] / FPS, 3), n=tr["n"],
            speed_px_per_frame=round(tr["speed"] * sc, 1), mean_area=round(tr["mean_area"] * sc * sc, 0),
            mean_contrast=round(tr["mean_contrast"], 1), score=round(tr["score"], 1),
            # (t_abs, cx, cy, w, h) in SOURCE 4K pixels
            pts=[(round(a.start + p[0] / FPS, 3), round(p[1] * sc, 1), round(p[2] * sc, 1), round(p[5] * sc), round(p[6] * sc))
                 for p in tr["pts"]]))
    json.dump(out, open(os.path.join(a.outdir, "tracks.json"), "w"), indent=1)
    print(f"{len(keep)} frames, statuses={statuses}, {len(tracks)} tracklets kept")
    for ti, tr in enumerate(out["tracks"][:a.top]):
        p0 = tr["pts"][0]
        print(f"track{ti}: {tr['t_start']:.2f}-{tr['t_end']:.2f}s n={tr['n']} speed={tr['speed_px_per_frame']} px/f "
              f"area={tr['mean_area']:.0f} contrast={tr['mean_contrast']} score={tr['score']}  first=({p0[1]:.0f},{p0[2]:.0f})")
        tiles = []
        src_pts = tracks[ti]["pts"]
        for p in src_pts[::max(1, len(src_pts) // 8)][:8]:
            g = keep[p[0]]; x, y = int(p[1]), int(p[2]); r_ = 80
            crop = g[max(0, y - r_):y + r_, max(0, x - r_):x + r_]
            crop = cv2.cvtColor(cv2.resize(crop, (320, 320), interpolation=cv2.INTER_NEAREST), cv2.COLOR_GRAY2BGR)
            cv2.putText(crop, f"{a.start + p[0] / FPS:.2f}s", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
            tiles.append(crop)
        cv2.imwrite(os.path.join(a.outdir, f"track{ti}_crops.jpg"), np.hstack(tiles))


if __name__ == "__main__":
    main()
