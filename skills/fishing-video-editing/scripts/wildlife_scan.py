#!/usr/bin/env python3
"""Coarse search for wildlife (perched OR flying) in 4K footage: tiled YOLO 'bird' detector.

Why tiles: a far bird is 30-150 px in a 3840x2160 frame. Any detector that resizes the
whole frame to 640/1280 px turns it into a few pixels and misses it. SAHI slices the frame
into 960x960 native-resolution tiles (20% overlap), runs yolo11s (COCO class 14 'bird') on
each, and merges. Measured on real 4K head-cam footage (Apple silicon, MPS): finds pasted
60 px and 120 px eagles in sky and on the treeline, ZERO false positives on eagle-free 4K frames at
conf 0.2; ~1 s per frame. So run it at 1-2 fps over windows, never over a whole clip at
30 fps. Use the transcript cue as the prior: scan from ~90 s BEFORE the cue (was it
perched before he noticed?) to ~30 s after.

Non-bird animals (beaver, otter, deer…): `--prompt "beaver,otter"` switches the backend to
YOLOE-11s with text prompts (open-vocabulary; needs yoloe-11s-seg.pt + the 600 MB
mobileclip_blt.ts text encoder in the models folder). Expect lower confidence than COCO
"bird" and more junk on lily pads / reflections — the hits sheet is the judge.

Usage:
  wildlife_scan.py SRC.MP4 OUTDIR --start S --end E [--fps 1] [--conf 0.2] [--tile 960] [--prompt "beaver,otter"]
    Writes OUTDIR/scan.json  [{t, dets:[{conf, box:[x1,y1,x2,y2]}]}, ...]  (4K px)
           OUTDIR/hits_sheet.jpg  every frame with a hit: a 400x400 crop around the best box
                                  (LOOK at this — a hit is a bird, or it is a rod tip / stump)
           OUTDIR/timeline.txt    one line per sample: t, n_dets, best conf
Model: $WILDLIFE_MODELS/yolo11s.pt (default ~/.wildlife-models; references/setup.md).
Python deps: ultralytics, sahi (use the detector venv — system Python usually lacks sahi).
--device defaults to mps (Apple silicon); use --device cpu or cuda:0 elsewhere.
Decode uses -hwaccel videotoolbox on macOS (override with $FFMPEG_HWACCEL, e.g. "cuda" or "none").
"""
import argparse, json, os, subprocess, sys, time
import numpy as np
import cv2
# hardware decode: VideoToolbox on macOS, none elsewhere; override with $FFMPEG_HWACCEL ("cuda", "vaapi", "none")
_hw = os.environ.get("FFMPEG_HWACCEL", "videotoolbox" if sys.platform == "darwin" else "none")
HWACCEL = [] if _hw == "none" else ["-hwaccel", _hw]

MODELS = os.environ.get("WILDLIFE_MODELS", os.path.expanduser("~/.wildlife-models"))


def frames(src, start, end, fps):
    cmd = ["ffmpeg", "-loglevel", "error", *HWACCEL, "-ss", f"{start:.3f}", "-i", src,
           "-t", f"{end - start:.3f}", "-vf", f"fps={fps}", "-pix_fmt", "bgr24", "-f", "rawvideo", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=3840 * 2160 * 3 * 2)
    n = 3840 * 2160 * 3; i = 0
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        yield start + i / fps, np.frombuffer(buf, np.uint8).reshape(2160, 3840, 3)
        i += 1
    p.stdout.close(); p.wait()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src"); ap.add_argument("outdir")
    ap.add_argument("--start", type=float, required=True); ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--fps", type=float, default=1.0); ap.add_argument("--conf", type=float, default=0.2)
    ap.add_argument("--tile", type=int, default=960); ap.add_argument("--overlap", type=float, default=0.2)
    ap.add_argument("--max-box", type=int, default=600, help="drop boxes wider/taller than this (whole-tree hallucinations)")
    ap.add_argument("--device", default="mps")
    ap.add_argument("--prompt", help="comma-separated YOLOE text prompts (non-bird animals); default = COCO bird")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    os.environ.setdefault("YOLO_CONFIG_DIR", os.path.join(MODELS, "yolo_config"))
    os.chdir(MODELS)                       # ultralytics drops the CLIP text encoder in the cwd
    from sahi import AutoDetectionModel
    from sahi.predict import get_sliced_prediction
    if a.prompt:
        import torch
        names = [n.strip() for n in a.prompt.split(",") if n.strip()]
        dm = AutoDetectionModel.from_pretrained(model_type="yoloe", model_path=os.path.join(MODELS, "yoloe-11s-seg.pt"),
                                                confidence_threshold=min(a.conf, 0.05), device=a.device, image_size=a.tile)
        m = dm.model                       # text embeddings must be computed on CPU (MPS can't run the TorchScript encoder)
        m.model.to("cpu"); pe = m.get_text_pe(names); m.model.to(a.device)
        m.set_classes(names, pe.to(a.device))
        dm.category_mapping = {str(i): n for i, n in enumerate(names)}
        keep_ids = set(range(len(names)))
    else:
        dm = AutoDetectionModel.from_pretrained(model_type="ultralytics", model_path=os.path.join(MODELS, "yolo11s.pt"),
                                                confidence_threshold=min(a.conf, 0.1), device=a.device, image_size=a.tile)
        keep_ids = {14}                    # COCO 'bird'
    results, tiles, lines = [], [], []
    t0 = time.time(); n = 0
    for t, f in frames(a.src, a.start, a.end, a.fps):
        r = get_sliced_prediction(f[:, :, ::-1], dm, slice_height=a.tile, slice_width=a.tile,
                                  overlap_height_ratio=a.overlap, overlap_width_ratio=a.overlap,
                                  postprocess_type="NMS", postprocess_match_threshold=0.5, verbose=0)
        dets = []
        for p in r.object_prediction_list:
            if int(p.category.id) not in keep_ids:
                continue
            x1, y1, x2, y2 = [int(v) for v in p.bbox.to_xyxy()]
            if x2 - x1 > a.max_box or y2 - y1 > a.max_box or float(p.score.value) < a.conf:
                continue
            dets.append({"conf": round(float(p.score.value), 3), "box": [x1, y1, x2, y2], "name": p.category.name})
        dets.sort(key=lambda d: -d["conf"])
        results.append({"t": round(t, 3), "dets": dets})
        best = dets[0]["conf"] if dets else 0.0
        lines.append(f"{t:8.2f}  n={len(dets)}  best={best:.2f}" + (f"  box={dets[0]['box']}" if dets else ""))
        n += 1
        print(lines[-1], f"({(time.time() - t0) / n:.1f} s/frame)", file=sys.stderr)
        if dets:
            b = dets[0]["box"]; cx, cy = (b[0] + b[2]) // 2, (b[1] + b[3]) // 2
            x0, y0 = int(np.clip(cx - 200, 0, 3440)), int(np.clip(cy - 200, 0, 1760))
            crop = f[y0:y0 + 400, x0:x0 + 400].copy()
            for d in dets:
                bb = d["box"]
                cv2.rectangle(crop, (bb[0] - x0, bb[1] - y0), (bb[2] - x0, bb[3] - y0), (0, 0, 255), 2)
            cv2.putText(crop, f"{t:.1f}s {best:.2f} {dets[0]['name']}", (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            tiles.append(crop)
    json.dump({"src": a.src, "start": a.start, "end": a.end, "fps": a.fps, "conf": a.conf, "tile": a.tile,
               "samples": results}, open(os.path.join(a.outdir, "scan.json"), "w"), indent=1)
    open(os.path.join(a.outdir, "timeline.txt"), "w").write("\n".join(lines) + "\n")
    if tiles:
        cols = 6
        while len(tiles) % cols:
            tiles.append(np.zeros_like(tiles[0]))
        rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
        cv2.imwrite(os.path.join(a.outdir, "hits_sheet.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    hits = [r for r in results if r["dets"]]
    print(f"{n} frames scanned, {len(hits)} with a bird hit; {a.outdir}/hits_sheet.jpg, timeline.txt, scan.json")
    if hits:
        # contiguous runs of hits -> candidate windows
        runs, cur = [], [hits[0]["t"], hits[0]["t"]]
        for h in hits[1:]:
            if h["t"] - cur[1] <= 2.5 / a.fps:
                cur[1] = h["t"]
            else:
                runs.append(cur); cur = [h["t"], h["t"]]
        runs.append(cur)
        for r0, r1 in runs:
            print(f"  candidate window {r0:.1f}-{r1:.1f}s")


if __name__ == "__main__":
    main()
