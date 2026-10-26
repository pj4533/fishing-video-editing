#!/usr/bin/env python3
"""Build a hard-cut edit (portrait 9:16 or landscape 16:9) from 4K or 1080p GoPro sources.

One JSON describes the whole edit; this script encodes every segment, assembles them with
concat_av.py (audio rebuilt once from the source, never per-segment AAC concatenated) and runs
check_av_sync.py. It also writes the check_cuts.py list so the boundary check uses the exact
same in/out points.

Usage:
  build_edit.py EDIT.json [--only TAG,TAG] [--no-concat]

EDIT.json:
  {"name": "f1", "mode": "portrait" | "landscape",
   "srcdir": "<footage_dir>",                 # GX*.MP4 live here
   "wavdir": "~/fishing_scratch/<trip>/wav",   # 16 kHz WAVs for check_cuts (optional)
   "work":   "~/fishing_scratch/<trip>/build", # per-segment encodes (cached by content hash)
   "out":    "<work_dir>/f1_base.mp4",
   "segs": [
     {"tag": "C1a", "src": "GX020156", "in": 12.3, "out": 40.1,
      # portrait framing, all x values are the SUBJECT's horizontal position in 1920-wide
      # coordinates (what fishtrack2.py emits and what a 960-px grid frame reads ×2):
      "S": 960,                                  # fixed, or
      "path": [[t_abs, S], ...],                 # piecewise-linear keyframes, or both plus
      "track": "proof/catch1_track.txt",         # fishtrack2 output (t_rel x y conf, 15 fps)
      "track_start": 30.0,                       # the START passed to fishtrack2
      "track_from": 31.0, "track_to": 39.0,      # where the track drives the crop
      "smooth": 0.35,                            # gaussian sigma (s) on the track
      "bias": [[t_abs, dx], ...]                 # head-side bias added to the track (1920 px)
     }, ...]}
Portrait: a 1215×2160 window of the 4K frame (608×1080 of a 1080p frame) centred on S,
clamped to the frame, scaled to 1080×1920. Landscape: the full frame scaled to 1920×1080;
an optional "zoom": [[t0_abs, t1_abs, factor, S, Y], ...] holds a constant punch-in (factor ≥ 1,
centred on S, Y in 1920×1080 space) from t0 to t1 — hard in, hard out.
"""
import hashlib, json, os, subprocess, sys
import numpy as np

FPS = 30000 / 1001
# hardware HEVC decode: VideoToolbox on macOS; override with $FFMPEG_HWACCEL (e.g. "cuda", "vaapi", or "none")
_hw = os.environ.get("FFMPEG_HWACCEL", "videotoolbox" if sys.platform == "darwin" else "none")
HWACCEL = [] if _hw == "none" else ["-hwaccel", _hw]
HERE = os.path.dirname(os.path.abspath(__file__))


def ex(p):
    return os.path.abspath(os.path.expanduser(p))


def probe_wh(src):
    o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height", "-of", "csv=p=0", src],
                       capture_output=True, text=True, check=True).stdout.strip()
    w, h = o.split(",")[:2]
    return int(w), int(h)


def interp(keys, t):
    keys = sorted(keys)
    ts = [k[0] for k in keys]; vs = [k[1] for k in keys]
    return float(np.interp(t, ts, vs))


def gauss(v, sigma_frames):
    if sigma_frames <= 0 or len(v) < 3:
        return v
    r = int(3 * sigma_frames) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma_frames) ** 2); k /= k.sum()
    pad = np.pad(v, r, mode="edge")
    return np.convolve(pad, k, mode="valid")


def subject_x(seg, n):
    """Per-output-frame subject x (1920 space) for a portrait segment."""
    t = seg["in"] + np.arange(n) / FPS
    if "path" in seg:
        base = np.array([interp(seg["path"], ti) for ti in t])
    else:
        base = np.full(n, float(seg.get("S", 960)))
    if "track" in seg:
        tr = np.loadtxt(ex(seg["track"]))
        tt = seg["track_start"] + tr[:, 0]
        tx = gauss(tr[:, 1].astype(float), seg.get("smooth", 0.35) * 15)
        if "bias" in seg:
            tx = tx + np.array([interp(seg["bias"], ti) for ti in tt])
        a, b = seg.get("track_from", tt[0]), seg.get("track_to", tt[-1])
        ramp = seg.get("ramp", 0.6)
        trk = np.interp(t, tt, tx)
        w = np.clip(np.minimum((t - a) / ramp + 1, (b - t) / ramp + 1), 0, 1)
        w[(t < a - ramp) | (t > b + ramp)] = 0
        base = base * (1 - w) + trk * w
    return base


def encode(seg, src, out, mode, work):
    W, H = probe_wh(src)
    dur = seg["out"] - seg["in"]
    n = int(round(dur * FPS))
    common = ["-r", "30000/1001", "-video_track_timescale", "30000", "-c:v", "libx264", "-crf", "19",
              "-preset", "medium", "-pix_fmt", "yuv420p", "-an"]
    if mode == "portrait":
        cw = int(round(H * 9 / 16)) // 2 * 2
        xs = subject_x(seg, n) * (W / 1920.0) - cw / 2
        xs = np.clip(xs, 0, W - cw)
        cmd_file = out + ".cmd"
        with open(cmd_file, "w") as f:
            for i, x in enumerate(xs):
                f.write(f"{i / FPS:.4f} crop@c x {int(round(x))};\n")
        vf = (f"sendcmd=f='{cmd_file}',crop@c=w={cw}:h={H}:x={int(round(xs[0]))}:y=0,"
              f"scale=1080:1920:flags=lanczos,setsar=1,fps=30000/1001,format=yuv420p")
    else:
        vf = "scale=1920:1080:flags=lanczos,setsar=1,fps=30000/1001,format=yuv420p"
        if "zoom" in seg:
            # piecewise-constant punch-in windows: [[t0, t1, factor, S, Y], ...] (1920 space).
            # crop's w/h are evaluated once at init (t is NAN there), so a per-frame if(between(t..))
            # size expression never zooms. Instead split the segment into frame-exact pieces, crop
            # each piece with a constant window, and concat them inside the one encode.
            cuts = [(0, n, None)]
            for t0, t1, fac, S, Y in sorted(seg["zoom"]):
                f0 = min(max(int(round((t0 - seg["in"]) * FPS)), 0), n)
                f1 = min(max(int(round((t1 - seg["in"]) * FPS)), 0), n)
                if f1 <= f0:
                    continue
                cw, ch = int(W / fac) // 2 * 2, int(H / fac) // 2 * 2
                x = int(min(max(S * W / 1920 - cw / 2, 0), W - cw))
                y = int(min(max(Y * H / 1080 - ch / 2, 0), H - ch))
                nxt = []
                for a, b, c in cuts:
                    if b <= f0 or a >= f1:
                        nxt.append((a, b, c)); continue
                    if a < f0: nxt.append((a, f0, c))
                    nxt.append((max(a, f0), min(b, f1), (cw, ch, x, y)))
                    if b > f1: nxt.append((f1, b, c))
                cuts = nxt
            k = len(cuts)
            fc = f"[0:v]split={k}" + "".join(f"[s{i}]" for i in range(k)) + ";"
            for i, (a, b, c) in enumerate(cuts):
                crop = f"crop={c[0]}:{c[1]}:{c[2]}:{c[3]}:exact=1," if c else ""
                fc += (f"[s{i}]trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS,{crop}"
                       f"scale=1920:1080:flags=lanczos,setsar=1[v{i}];")
            fc += "".join(f"[v{i}]" for i in range(k)) + f"concat=n={k}:v=1:a=0,fps=30000/1001,format=yuv420p[vout]"
            cmd = ["ffmpeg", "-y", "-v", "error", *HWACCEL, "-ss", f"{seg['in']:.3f}", "-i", src,
                   "-t", f"{dur:.3f}", "-filter_complex", fc, "-map", "[vout]"] + common + [out]
            subprocess.run(cmd, check=True)
            return
    cmd = ["ffmpeg", "-y", "-v", "error", *HWACCEL, "-ss", f"{seg['in']:.3f}", "-i", src,
           "-t", f"{dur:.3f}", "-vf", vf] + common + [out]
    subprocess.run(cmd, check=True)


def main():
    E = json.load(open(sys.argv[1]))
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
    mode = E.get("mode", "portrait")
    srcdir, work = ex(E["srcdir"]), ex(E.get("work", "~/fishing_scratch/build"))
    os.makedirs(work, exist_ok=True)
    segl, cuts = [], []
    for i, s in enumerate(E["segs"]):
        src = os.path.join(srcdir, s["src"] + ".MP4")
        key = hashlib.md5(json.dumps([mode, s, os.path.getmtime(src)], sort_keys=True).encode()).hexdigest()[:10]
        out = s.get("pre") or os.path.join(work, f"{E['name']}_{i:03d}_{key}.mp4")
        if (only is None or s.get("tag") in only) and not os.path.exists(out):
            print(f"[{i}] {s.get('tag','')} {s['src']} {s['in']:.2f}-{s['out']:.2f}", flush=True)
            encode(s, src, out, mode, work)
        segl.append([out, src, s["in"]])
        if E.get("wavdir"):
            cuts.append([s.get("tag", str(i)), os.path.join(ex(E["wavdir"]), s["src"] + ".wav"), s["in"], s["out"]])
    base = os.path.splitext(ex(E["out"]))[0]
    os.makedirs(os.path.dirname(base), exist_ok=True)
    json.dump(segl, open(base + ".segments.json", "w"), indent=0)
    if cuts:
        json.dump(cuts, open(base + ".cuts.json", "w"), indent=0)
    if "--no-concat" in sys.argv:
        return
    subprocess.run([sys.executable, os.path.join(HERE, "concat_av.py"), base + ".segments.json", ex(E["out"])], check=True)
    r = subprocess.run([sys.executable, os.path.join(HERE, "check_av_sync.py"), base + ".segments.json", ex(E["out"])])
    tot = sum(s["out"] - s["in"] for s in E["segs"])
    print(f"built {E['out']}  {len(E['segs'])} segs  {tot:.1f}s  av_sync={'OK' if r.returncode == 0 else 'FAIL'}")


if __name__ == "__main__":
    main()
