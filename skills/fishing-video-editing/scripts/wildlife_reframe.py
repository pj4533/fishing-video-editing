#!/usr/bin/env python3
"""Virtual camera: render a 9:16 portrait clip from 4K that keeps a tracked animal centered.

Reads a wildlife_track.py track, smooths it (zero-phase gaussian, --sigma seconds — offline,
so no lag), picks a crop width per frame, and renders 1080x1920 by cropping the native 4K
frame and resizing (lanczos up / area down), then CAS sharpening in ffmpeg. Audio is the
source audio for exactly the same span, cut on the same frame (editing-rules: audio always
cut with the video; for multi-segment clips still assemble with concat_av.py).

Crop-width quality ladder (references/wildlife-zoom.md): full-height 9:16 from 2160 px is
1215 px wide (downsample, best quality); 1080 = 1:1; 800 = 1.35x up (fine); 600 = 1.8x up
(soft but OK on a phone). Below that it depends on the background: clean sky holds up to
~8x, treelines smear past ~6x. Auto mode sets width = --k × the animal's box size, clamped
to [--min-w, --max-w] and smoothed — the animal ends up ~1/k of the frame width. The
argparse defaults (--k 9 --min-w 600) are the CONSERVATIVE cut; for the recommended extreme
zoom (animal ~1/4-1/3 of the frame) pass e.g. --k 3.5 --min-w 48 --sigma 0.06, or --width
keyframes. The hard clamp is [48, 1215].

Usage:
  wildlife_reframe.py SRC.MP4 track.txt OUT.mp4 [--start S --end E]
      [--width "t:w,t:w,..." | --k 9 --min-w 600 --max-w 1215] [--sigma 0.4] [--sigma-w 0.8]
      [--subject-y 0.5] [--cas 0.4] [--crf 18] [--verify sheet.jpg]
      [--mark "t0:t1[:label]" ...] [--mark-style circle|arrow|both]
    --width: crop-width keyframes (t_abs:px), piecewise-linear; two keyframes 0.03 s apart
             make a hard punch-in. Overrides auto mode.
    --start/--end default to the track's span. Frames outside the track hold its ends.
    --subject-y: where the animal sits vertically in the output (0.5 = center; 0.45 gives a
             little headroom under a caption).
    --verify: output frame every 0.5 s with a centerline, 360 px tiles — the animal must
             sit on the line in every tile.
    --mark:  draw a marker ON the tracked animal between source times t0 and t1 (absolute
             seconds), e.g. --mark "300.0:302.9:bald eagle" for a perched bird nobody would
             spot. The marker follows the track in output space (circle sized from the
             animal's box, arrow from lower-right, optional label in the caption font),
             pops in/out over ~0.2 s. Repeatable. Only for moments where the animal is
             genuinely hard to see — never on a bird already filling the frame.
"""
import argparse, os, subprocess, sys
import numpy as np
import cv2
# hardware decode: VideoToolbox on macOS, none elsewhere; override with $FFMPEG_HWACCEL ("cuda", "vaapi", "none")
_hw = os.environ.get("FFMPEG_HWACCEL", "videotoolbox" if sys.platform == "darwin" else "none")
HWACCEL = [] if _hw == "none" else ["-hwaccel", _hw]
from scipy.ndimage import gaussian_filter1d
from PIL import Image, ImageDraw, ImageFont

FPS = 30000 / 1001
FONT = os.environ.get("CAPTION_FONT", "/System/Library/Fonts/Supplemental/Arial Bold.ttf")   # macOS default; set $CAPTION_FONT elsewhere
W, H = 3840, 2160
OW, OH = 1080, 1920


def draw_marker(frame, ox, oy, size_px, alpha, label, style):
    """Circle + arrow (+ label) on the output frame at (ox, oy); size_px = animal size on screen."""
    if alpha <= 0:
        return frame
    ov = frame.copy()
    r = int(max(60, min(220, size_px * 1.1)))
    ox, oy = int(ox), int(oy)
    white, black = (255, 255, 255), (0, 0, 0)
    if style in ("circle", "both"):
        cv2.circle(ov, (ox, oy), r, black, 12, cv2.LINE_AA); cv2.circle(ov, (ox, oy), r, white, 6, cv2.LINE_AA)
    if style in ("arrow", "both"):
        # arrow from lower-right, pointing at the circle edge; flip to lower-left near the right edge
        dx = -1 if ox > 1080 - 320 else 1
        tip = (ox + dx * int(r * 0.75), oy + int(r * 0.75))
        tail = (ox + dx * (r + 260), oy + r + 260)
        cv2.arrowedLine(ov, tail, tip, black, 16, cv2.LINE_AA, tipLength=0.22)
        cv2.arrowedLine(ov, tail, tip, white, 8, cv2.LINE_AA, tipLength=0.22)
        if label:
            im = Image.fromarray(ov[:, :, ::-1]); d = ImageDraw.Draw(im)
            f = ImageFont.truetype(FONT, 58)
            tw = d.textlength(label, font=f)
            lx = int(np.clip(tail[0] - (tw if dx < 0 else 0) - (0 if dx < 0 else -10), 44, 1080 - 140 - tw))
            ly = int(np.clip(tail[1] + 10, 130, 1920 - 484 - 70))
            d.text((lx, ly), label, font=f, fill="white", stroke_width=6, stroke_fill="black")
            ov = np.ascontiguousarray(np.array(im)[:, :, ::-1])
    return cv2.addWeighted(ov, alpha, frame, 1 - alpha, 0)


def load_track(p):
    rows = [l.split() for l in open(p) if l.strip()]
    t = np.array([float(r[0]) for r in rows]); cx = np.array([float(r[1]) for r in rows])
    cy = np.array([float(r[2]) for r in rows]); bw = np.array([float(r[3]) for r in rows]); bh = np.array([float(r[4]) for r in rows])
    return t, cx, cy, bw, bh


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src"); ap.add_argument("track"); ap.add_argument("out")
    ap.add_argument("--start", type=float); ap.add_argument("--end", type=float)
    ap.add_argument("--width"); ap.add_argument("--k", type=float, default=9.0)
    ap.add_argument("--min-w", type=int, default=600); ap.add_argument("--max-w", type=int, default=1215)
    ap.add_argument("--sigma", type=float, default=0.4); ap.add_argument("--sigma-w", type=float, default=0.8)
    ap.add_argument("--subject-y", type=float, default=0.5)
    ap.add_argument("--cas", type=float, default=0.4); ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--verify")
    ap.add_argument("--mark", action="append", default=[], help='"t0:t1[:label]" marker window(s), absolute source seconds')
    ap.add_argument("--mark-style", default="both", choices=["circle", "arrow", "both"])
    a = ap.parse_args()
    marks = []
    for m in a.mark:
        parts = m.split(":", 2)
        marks.append((float(parts[0]), float(parts[1]), parts[2] if len(parts) > 2 else ""))
    tt, cx, cy, bw, bh = load_track(a.track)
    start = a.start if a.start is not None else tt[0]
    end = a.end if a.end is not None else tt[-1] + 1 / FPS
    n = int(round((end - start) * FPS))
    t = start + np.arange(n) / FPS
    # smooth the subject path (zero-phase), then resample onto the output frame grid
    sig = max(1e-3, a.sigma * FPS)
    sx = gaussian_filter1d(cx, sig, mode="nearest"); sy = gaussian_filter1d(cy, sig, mode="nearest")
    X = np.interp(t, tt, sx); Y = np.interp(t, tt, sy)
    if a.width:
        kf = sorted((float(p.split(":")[0]), float(p.split(":")[1])) for p in a.width.split(","))
        CW = np.interp(t, [k[0] for k in kf], [k[1] for k in kf])
    else:
        size = np.maximum(bw, bh)
        raw = np.clip(a.k * size, a.min_w, a.max_w)
        CW = np.interp(t, tt, gaussian_filter1d(raw, max(1e-3, a.sigma_w * FPS), mode="nearest"))
    CW = np.clip(CW, 48, 1215)  # 48 px floor so extreme zoom (animal ~1/4-1/3 of the frame) is possible
    CH = CW * 16 / 9
    x0 = np.clip(X - CW / 2, 0, W - CW); y0 = np.clip(Y - CH * a.subject_y, 0, H - CH)
    SZ = np.interp(t, tt, gaussian_filter1d(np.maximum(bw, bh), sig, mode="nearest"))   # animal size, source px
    RX, RY = np.interp(t, tt, cx), np.interp(t, tt, cy)   # RAW track for the marker: the camera lags, the marker must not
    print(f"{n} frames, crop width {CW.min():.0f}-{CW.max():.0f} px (upscale {OW / CW.max():.2f}x-{OW / CW.min():.2f}x)")
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", *HWACCEL, "-ss", f"{start:.3f}", "-i", a.src,
                            "-t", f"{end - start:.3f}", "-frames:v", str(n), "-pix_fmt", "bgr24", "-f", "rawvideo", "-"],
                           stdout=subprocess.PIPE, bufsize=W * H * 3 * 2)
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error",
                            "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{OW}x{OH}", "-r", "30000/1001", "-i", "-",
                            "-ss", f"{start:.3f}", "-t", f"{n / FPS:.4f}", "-i", a.src,
                            "-map", "0:v", "-map", "1:a", "-vf", f"cas={a.cas},format=yuv420p",
                            "-c:v", "libx264", "-crf", str(a.crf), "-preset", "medium", "-pix_fmt", "yuv420p",
                            "-r", "30000/1001", "-video_track_timescale", "30000",
                            "-af", "aresample=async=1:first_pts=0", "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k",
                            "-shortest", a.out], stdin=subprocess.PIPE)
    nb = W * H * 3; i = 0
    while i < n:
        buf = dec.stdout.read(nb)
        if len(buf) < nb:
            break
        f = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        cw, ch = int(round(CW[i])), int(round(CW[i] * 16 / 9))
        xx, yy = int(round(x0[i])), int(round(y0[i]))
        xx = min(max(xx, 0), W - cw); yy = min(max(yy, 0), H - ch)
        crop = f[yy:yy + ch, xx:xx + cw]
        interp = cv2.INTER_AREA if cw >= OW else cv2.INTER_LANCZOS4
        out = cv2.resize(crop, (OW, OH), interpolation=interp)
        for t0, t1, label in marks:
            if t0 <= t[i] <= t1:
                ramp = min(1.0, (t[i] - t0) / 0.2, (t1 - t[i]) / 0.2)          # 0.2 s pop in / out
                sc = OW / cw
                out = draw_marker(out, (RX[i] - xx) * sc, (RY[i] - yy) * sc, SZ[i] * sc, max(0.0, ramp), label, a.mark_style)
        enc.stdin.write(out.tobytes())
        i += 1
        if i % 100 == 0:
            print(f"  {i}/{n}", file=sys.stderr)
    dec.stdout.close(); enc.stdin.close(); enc.wait(); dec.wait()
    print(f"wrote {a.out}: {i} frames ({i / FPS:.2f} s)")
    if a.verify:
        tiles = []
        for ts in np.arange(0, (i - 1) / FPS, 0.5):
            r = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{ts:.3f}", "-i", a.out, "-frames:v", "1",
                                "-vf", f"drawbox=x={OW // 2 - 2}:y=0:w=4:h={OH}:color=red@0.85:t=fill,"
                                       f"drawbox=x=0:y={int(OH * a.subject_y) - 2}:w={OW}:h=4:color=red@0.5:t=fill,"
                                       f"drawtext=text='{ts:.1f}s':x=10:y=10:fontsize=48:fontcolor=yellow:box=1:boxcolor=black@0.5,"
                                       f"scale=360:-1", "-f", "image2pipe", "-vcodec", "mjpeg", "-"], capture_output=True)
            im = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR) if r.stdout else None
            if im is not None:
                tiles.append(im)
        cols = 8
        while len(tiles) % cols:
            tiles.append(np.zeros_like(tiles[0]))
        cv2.imwrite(a.verify, np.vstack([np.hstack(tiles[k:k + cols]) for k in range(0, len(tiles), cols)]),
                    [cv2.IMWRITE_JPEG_QUALITY, 85])
        print("verify sheet:", a.verify)


if __name__ == "__main__":
    main()
