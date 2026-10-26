# Cookbook — every command, copy-pasteable

The exact ffmpeg / whisper / script invocations used by the editing pipeline. Install
everything first ([setup.md](setup.md)). The rules these commands serve live in
[editing-rules.md](editing-rules.md); the order you run them in lives in
[workflow.md](workflow.md); the traps are collected in
[lessons-learned.md](lessons-learned.md).

## Contents
0. [Conventions](#0-conventions)
1. [Probe a file](#1-probe-a-file)
2. [Contact sheets with timestamps](#2-contact-sheets-with-timestamps)
3. [Extract audio](#3-extract-audio)
4. [Transcribe](#4-transcribe)
5. [Break a hallucination loop — chunked re-transcription](#5-break-a-hallucination-loop--chunked-re-transcription)
6. [Recover buried catch audio — isolated-window re-transcription](#6-recover-buried-catch-audio--isolated-window-re-transcription)
7. [Speech islands and timing truth](#7-speech-islands-and-timing-truth)
8. [Frames: single, full-res, zoomed, 4K piped](#8-frames-single-full-res-zoomed-4k-piped)
9. [Cut points and check_cuts.py](#9-cut-points-and-check_cutspy)
10. [Framing math: portrait, landscape, punch-in](#10-framing-math-portrait-landscape-punch-in)
11. [Fish centering — the full procedure](#11-fish-centering--the-full-procedure)
12. [build_edit.py — one JSON per edit](#12-build_editpy--one-json-per-edit)
13. [Manual segments + concat_av / check_av_sync](#13-manual-segments--concat_av--check_av_sync)
14. [Burned captions](#14-burned-captions)
15. [Catch-still overlay cards](#15-catch-still-overlay-cards)
16. [Bleeping a curse](#16-bleeping-a-curse)
17. [Wind-noise filter](#17-wind-noise-filter)
18. [Music / copyright audit and voice-stem swap](#18-music--copyright-audit-and-voice-stem-swap)
19. [Output QA sheets](#19-output-qa-sheets)
20. [Thumbnails and wildlife — pointers](#20-thumbnails-and-wildlife--pointers)

---

## 0. Conventions

```bash
SKILL=<path to this skill>            # scripts live in $SKILL/scripts
SRC=<footage_dir>/GX010123.MP4        # one source clip (GoPro naming; any MP4 works)
WORK=<work_dir>                       # scratch: WAVs, frames, per-segment encodes
OUT=<output_dir>                      # deliverables + proof files only
FONT="/System/Library/Fonts/Supplemental/Arial Bold.ttf"   # Linux: DejaVuSans-Bold.ttf
BASE=~/.whisper-models/ggml-base.en.bin
SMALL=~/.whisper-models/ggml-small.en.bin
```

- `python3` below means the interpreter with the core deps ([setup.md §8](setup.md#8-which-interpreter-runs-which-script)).
- GoPro files: `GX*.MP4` is the real video, `GL*.LRV` is a low-res proxy of the same clip
  (same timeline — use it for fast scanning), `*.THM` is a thumbnail (ignore). Long
  recordings are split into chapters (`GX01xxxx`, `GX02xxxx`, …) with **no gap** between them.
- Transcript timecodes are per clip (relative to that file's start).
- Run long steps (audio extraction over a whole trip, transcription, 4K encodes) in the
  background, **one whisper job at a time** (`-t 4`).
- Copy every decision file (edit JSONs, keyframes, caption JSON, verify sheets) into
  `$OUT/proof/` as soon as it is final. Scratch in `/tmp` does not survive a reboot.
- In zsh, `$VAR` does not word-split. Never `ffmpeg $ARGS`; use an array or write the
  flags out.

## 1. Probe a file

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=codec_name,width,height,r_frame_rate -of csv=p=0 "$SRC"
ffprobe -v error -select_streams a:0 \
  -show_entries stream=codec_name,sample_rate,channels -of csv=p=0 "$SRC"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$SRC"        # seconds
```

Typical action-cam output: `hevc,1920,1080,30000/1001` or `hevc,3840,2160,30000/1001`,
audio `aac,48000,2`. Check every trip — resolution decides the portrait crop width (§10)
and whether wildlife zooms are possible at all (4K only).

## 2. Contact sheets with timestamps

Scan a whole clip for catches, wildlife, paddling. Use the LRV proxy when there is one —
it decodes many times faster than 4K HEVC.

```bash
IN=<footage_dir>/GL010123.LRV          # or the GX MP4 if no proxy exists
N=10                                   # one tile every N seconds
mkdir -p "$WORK/sheets"
ffmpeg -v error -y -i "$IN" -vf "setpts=PTS-STARTPTS,\
select='isnan(prev_selected_t)+gte(t-prev_selected_t\,$N)',scale=320:-1,\
drawtext=fontfile='${FONT}':text='%{pts\:hms}':x=6:y=6:fontsize=22:fontcolor=yellow:box=1:boxcolor=black@0.6,\
tile=6x8" -fps_mode vfr "$WORK/sheets/GX010123_%03d.jpg"
```

- Tiles read left→right, top→bottom; the label is the exact source time of that frame.
- Use `select=…`, not `fps=1/N`: the `fps` filter picks a frame up to N/2 seconds away
  from the time its label claims.
- 6 columns × 8 rows at 320 px = 48 frames per ~1920 px sheet, a size you can actually
  read. Smaller tiles hide paddle strokes, fish, and birds.
- Densify to every 2–5 s around a suspected catch. A fish can be landed and released
  between 10 s samples.
- Montage tiles are for **finding** moments, never for **measuring** positions (§11).

## 3. Extract audio

16 kHz mono WAV, one per clip, for whisper, silencedetect, and `check_cuts.py`:

```bash
mkdir -p "$WORK/wav"
for f in <footage_dir>/GX*.MP4; do
  b=$(basename "$f" .MP4)
  ffmpeg -v error -y -i "$f" -ar 16000 -ac 1 -c:a pcm_s16le "$WORK/wav/$b.wav"
done
```

## 4. Transcribe

`whisper-cli` prints `[hh:mm:ss.mmm --> hh:mm:ss.mmm] text` on stdout. `-otxt` writes a
`.txt` **without** timestamps, so always keep stdout.

```bash
mkdir -p "$WORK/tx"
for w in "$WORK"/wav/*.wav; do            # sequential — never fan out with &
  b=$(basename "$w" .wav)
  whisper-cli -m "$SMALL" -t 4 -f "$w" 2>/dev/null > "$WORK/tx/$b.small.txt"
done
# optional fast first pass on clear, talky footage: same loop with "$BASE" → $b.base.txt
```

Search for catch language, then for meta-talk that must never reach an edit (lines the
angler addresses to the camera operator / assistant rather than to viewers):

```bash
grep -n -iE "got (him|one)|fish on|there we go|nice|look at (him|that)|thank you|bye" "$WORK"/tx/*.txt
grep -n -iE "remind me|zoom|4k|footage|shopping list|note to self" "$WORK"/tx/*.txt
```

small.en is the default. base.en is faster, but on quiet days (few catches, little talking) its
output on near-silent audio is mostly hallucination.

## 5. Break a hallucination loop — chunked re-transcription

On a near-silent clip whisper can lock onto one phrase and repeat it for the entire file,
burying the real lines. Deny it the long context: re-run the same WAV in short
overlapping chunks.

```bash
W="$WORK/wav/GX010123.wav"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$W" | cut -d. -f1)
for ((t=0; t<DUR; t+=120)); do
  ffmpeg -v error -y -ss $t -t 122 -i "$W" -c copy "$WORK/_chunk.wav"
  echo "--- offset ${t}s ---"
  whisper-cli -m "$SMALL" -t 4 -f "$WORK/_chunk.wav" 2>/dev/null | grep -E "^\["
done | tee "$WORK/tx/GX010123.chunks.txt"

# drop ambient tags, prefix each line with its chunk offset (add it to the timestamp)
awk '/^--- offset/{o=$3} /^\[/{print o" "$0}' "$WORK/tx/GX010123.chunks.txt" \
  | grep -v -iE "BLANK_AUDIO|silence|\(water|\(bird|cricket|music|wind"
```

`-c copy` is fine here because the input is already 16 kHz PCM. A clip that reduces to one
or two real lines really was quiet — that is a finding.

## 6. Recover buried catch audio — isolated-window re-transcription

The bite is often exactly where whisper wrote "(crickets)", "[Music]", or a looping
phrase. Cut just that window from the source and transcribe it alone:

```bash
T0=812                                     # window start (s), ~10 s before the suspected bite
ffmpeg -v error -y -ss $T0 -t 50 -i "$SRC" -ar 16000 -ac 1 -c:a pcm_s16le "$WORK/iso.wav"
whisper-cli -m "$SMALL" -f "$WORK/iso.wav" 2>/dev/null | grep -E "^\["
# printed times are relative to T0 — add T0 back
```

Still nothing? Shift the window ±10 s, shorten it to 20 s, or run
`transcribe_islands.py` (§7) over it. Always cross-check with frames (§2, §8): audio
alone misses quiet catches.

## 7. Speech islands and timing truth

**Whisper timestamps are approximate at every level.** Segment times drift seconds within
a clip; a word at a window edge gets smeared over leading noise; `-ml 1` word times
drift ~100–300 ms normally and can be off by **whole seconds** over splashing. Use whisper
to know *what* was said, and the audio energy to know *when*.

**silencedetect** — speech islands are the gaps between detected silences:

```bash
# quiet ambient: -30 dB. Over paddle/wind/water noise: -23 dB, d=0.3 (speech ≫ ambient)
ffmpeg -ss 800 -t 40 -i "$WORK/wav/GX010123.wav" \
  -af "silencedetect=noise=-30dB:d=0.4" -f null - 2>&1 | grep -E "silence_(start|end)"
# times are relative to -ss
```

**Helper scripts** (absolute source times, no arithmetic):

```bash
python3 $SKILL/scripts/speech_islands.py "$WORK/wav/GX010123.wav" 800 840 [-30]
#   → one line per speech island: start end duration
python3 $SKILL/scripts/transcribe_islands.py "$WORK/wav/GX010123.wav" 800 840
#   → merged islands, each with its own small.en transcript
```

Island boundaries are where captions start/stop (§14), where catch-still cards land
(§15), and where you begin hunting a curse (§16). Island ends are **not** safe out-points
on their own: -30 dB misses quiet word tails. `check_cuts.py` (§9) decides.

**Trailing tag phrases are part of the line.** "…made it, made it. No problem." — the tag
can come 1+ s after the apparent sentence end. Look at the next island before you cut.

## 8. Frames: single, full-res, zoomed, 4K piped

```bash
# quick look (480 px wide)
ffmpeg -v error -y -ss 812.4 -i "$SRC" -frames:v 1 -vf scale=480:-1 -q:v 3 "$WORK/f.jpg"
# full resolution
ffmpeg -v error -y -ss 812.4 -i "$SRC" -frames:v 1 -q:v 2 "$WORK/f_full.jpg"
# crop-zoom to confirm a fish / turtle / bird (crop=W:H:X:Y in source pixels, then upscale)
ffmpeg -v error -y -ss 812.4 -i "$SRC" -frames:v 1 \
  -vf "crop=560:460:480:600,scale=1400:-1" -q:v 2 "$WORK/zoom.jpg"
# 4K native-res crop with a grid (each grid line = 50 source px after the 2x scale)
ffmpeg -v error -y -ss 812.4 -i "$SRC" -frames:v 1 \
  -vf "crop=500:500:2000:700,scale=1000:1000,drawgrid=w=100:h=100:color=yellow@0.6:t=2" "$WORK/z4k.jpg"
```

**4K frames: pipe, never store.** A raw 3840×2160 BGR frame is ~25 MB; a 10 s window at
30 fps is 7.5 GB. Decode straight into numpy:

```python
import subprocess, numpy as np
W, H = 3840, 2160
p = subprocess.Popen(["ffmpeg", "-v", "error", "-hwaccel", "videotoolbox",   # Linux: drop or "auto"
                      "-ss", "812.0", "-i", SRC, "-t", "10", "-vf", "fps=10",
                      "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
while True:
    buf = p.stdout.read(W * H * 3)
    if len(buf) < W * H * 3:
        break
    frame = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    # ... analyse, keep only small crops / numbers ...
```

## 9. Cut points and check_cuts.py

Pick cuts after a finished sentence or thought, in real silence (§7), never on a dangling
"and/so". Then **verify every segment list with `check_cuts.py`**, which runs webrtcvad
on the source audio:

```bash
# segs.json: [[tag, source_wav_or_video, in_s, out_s], ...] in play order
python3 $SKILL/scripts/check_cuts.py "$WORK/segs.json" --fix "$WORK/segs_fixed.json"
#   optional: --pad-out 0.35 --pad-in 0.25
```

- OUT needs ≥0.30 s of non-speech before the cut; IN needs ≥0.15 s after. A CHOP gets
  moved to finish the word (OUT) or start before it (IN).
- Its fix finishes the **word**; you finish the **thought**. Read the transcript at every
  moved cut.
- Extensions >1.5 s are marked REVIEW: they may pull in the next line (or the VAD mistook
  wind/reel noise for speech). Check with a transcript + the 10 ms envelope (§16).
- Consecutive segments that continue one take (punch-ins) are skipped automatically.
- `build_edit.py` writes this list for you (`*.cuts.json`) when `wavdir` is set.
- Re-run after every recut. Do **not** verify cuts by re-transcribing segments: whisper
  reconstructs a chopped word from context, so chops pass.

## 10. Framing math: portrait, landscape, punch-in

**Portrait 9:16** = a full-height window of the source, scaled to 1080×1920:

| Source | Window | Left edge range | Scale |
|---|---|---|---|
| 1920×1080 | 608×1080 | X = 0…1312 | 1.78× up |
| 3840×2160 | 1215×2160 (1214 after even rounding) | X = 0…2626 | 0.89× down (sharpest) |

All subject positions in this pipeline are written in **1920-wide space** (what
`fishtrack2.py` emits and what a 960-px grid frame reads ×2), whatever the source
resolution. To center a subject at 1920-space x = S:
`X_1080p = S − 304`; `X_4K = 2·S − 607`; clamp to the range. Subject appears left of
center in the output → decrease X; right → increase X. Near the source edge (S < 304 or
S > 1616) it cannot be centered; accept the clamp or choose another instant.

Manual portrait crop (ffmpeg crop options must be **all named** — mixing `x='…'` with a
positional `:0` fails with `No option name near '0'`):

```bash
ffmpeg -v error -y -ss 812 -i "$SRC" -t 6 \
  -vf "crop=w=608:h=1080:x='if(lt(t,3),500+120*t/3,620)':y=0,scale=1080:1920,setsar=1,fps=30000/1001,format=yuv420p" \
  -an -c:v libx264 -crf 19 "$WORK/p.mp4"
# 4K: crop=w=1214:h=2160:x=...  (t starts at 0 because -ss precedes -i)
```

**Landscape 16:9**: `scale=1920:1080:flags=lanczos,setsar=1,fps=30000/1001,format=yuv420p`.
A **punch-in** crops a smaller 16:9 window (W/f × H/f) centered on (S, Y) and scales it
back to 1920×1080. From 4K a 2× punch-in is still native 1080p. In `build_edit.py` it is
the `zoom` key (§12). Hold a punch-in as a fixed window (punch in / hold / punch out) —
don't pan it unless the subject is tracked densely.

## 11. Fish centering — the full procedure

Any portrait shot with a visible fish needs the fish **centered by a verified track**.
Eyeballed crops, one fixed X for a hold-up, "pivot" crops at the average of the angler's
rocking, and single-init trackers with ±px patches have all shipped off-center fish.
This procedure is the one that passes review. Budget for it; it is most of the work of a
highlight.

**Step 1 — anchor frames.** For each fish-visible span (bite splash → reel → aboard →
hold-up → release), pull gridded frames every ~1.5–2 s (every 0.3–0.5 s through fast
swings, hand-offs, a head whip):

```bash
$SKILL/scripts/keyframe_grid.sh "$SRC" "$WORK/kf_c1" 830.0 831.5 833.0 834.5 836.0
#   → 960×540 frames, grid line every 160 px of 1920-space (every 80 px on the image)
```

Small fish or fine detail? Use a bigger single frame:

```bash
ffmpeg -v error -y -ss 833.0 -i "$SRC" -frames:v 1 -vf "scale=1920:1080,\
drawgrid=w=120:h=120:color=yellow@0.5:t=2,drawbox=x=958:y=0:w=4:h=1080:color=red@0.9:t=fill" "$WORK/kf_833.jpg"
```

**Step 2 — read a box per anchor** in 1920×1080 coordinates (top-left x, y, width,
height — double what you read on a 960-px frame). Read BOXES on big single frames, never
positions off montage tiles (misreads of 400+ px happened that way). Re-read any
suspicious anchor from a fresh frame. Write `keyframes.json`, sorted:

```json
[[830.0, 1120, 610, 180, 90],
 [831.5, 1010, 560, 200, 110],
 [833.0,  880, 420, 260, 160],
 [834.5,  930, 380, 300, 170],
 [836.0, 1060, 400, 280, 160]]
```

**Step 3 — track both directions between anchors:**

```bash
python3 $SKILL/scripts/fishtrack2.py "$SRC" 829.5 840.0 "$WORK/kf_c1.json" "$WORK/c1_track.txt"
#   START END = absolute source seconds; first keyframe >= START
#   output: t_rel x y conf per frame at 15 fps; x, y = box CENTER in 1920 space; t_rel = t − START
```

Each span is tracked forward from the left anchor and backward from the right anchor
(fresh template at each), then blended linearly by time, so drift cannot survive between
two human-verified boxes. Before the first / after the last anchor it is one-directional
— keep anchors at both ends of the span.

**Step 4 — verify the TRACK visually** (box overlays every ~0.35 s, tiles ≥480 px).
Confidence numbers lie: a tracker latched onto ripple texture reports high confidence.
Where the box leaves the fish, the **anchor** is wrong or missing — add or fix an anchor
and re-run. Never patch the crop with blind ±offsets.

```python
# draw the tracked box on frames every ~0.35 s → sheet of ≥480 px tiles
import subprocess, numpy as np
SRC, START, TRK = "<footage_dir>/GX010123.MP4", 829.5, "<work_dir>/c1_track.txt"
tr = np.loadtxt(TRK)
for k, (t, x, y, c) in enumerate(tr[::5]):           # 15 fps / 5 = every 0.33 s
    vf = (f"scale=960:540,drawbox=x={x/2-50:.0f}:y={y/2-30:.0f}:w=100:h=60:color=red:t=3,"
          f"drawtext=fontfile='/System/Library/Fonts/Supplemental/Arial Bold.ttf':"
          f"text='{START+t:.2f}':x=8:y=8:fontsize=28:fontcolor=yellow")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{START+t:.3f}", "-i", SRC,
                    "-frames:v", "1", "-vf", vf, f"<work_dir>/trk_{k:03d}.jpg"])
# then tile: ffmpeg -pattern_type glob -i '<work_dir>/trk_*.jpg' -vf tile=4x4 trk_sheet_%02d.jpg
```

(Box size here is nominal; use your anchor sizes if the fish is much bigger.)

**Step 5 — wire the track into the segment** (`build_edit.py`, §12):

- `track` + `track_start` (= the START you gave fishtrack2).
- `smooth`: gaussian sigma in seconds on the track (default 0.35; 0.25 for a fast-moving
  fish, 0.5 for a calm hold).
- `track_from` / `track_to`: the span where the track drives the crop. Outside it the
  crop follows `S` or `path`; `ramp` (default 0.6 s) blends between them. Use a fixed/POV
  crop only while **no fish is identifiable** (the pre-bite retrieve), then ramp into the
  track.
- `path`: `[[t_abs, S], …]` piecewise-linear keyframes for non-tracked spans — the
  retrieve, and the bridge when the fish/net leaves the frame entirely during a netting
  swing (linear between exit and re-entry; the tracker has nothing to follow there).
- **Follow the fish everywhere it is visible.** The crop swaying with the angler's body
  rock reads as handheld follow; that is correct. No pose-locks, no pivots.

**Step 6 — head over tail.** When the held fish is wider than the crop window (common
in close hold-ups from 1080p, where the window is only 608 px), centering the body clips
both ends. Put the **head** (usually the hand-grip end, the lip) at center and let the
tail clip. Don't track the head directly — a hand-sized template over water latches onto
ripples. Instead read the head side from the Step 4 overlay frames every ~0.5 s and add
a `bias` ramp: `[[t_abs, dx], …]` in 1920 px, e.g. ±150–210 px toward the head while the
fish is horizontal, ramping to 0 when it is held vertically. The head must be fully in
frame in every verify tile.

**Step 7 — verify the OUTPUT strictly** (§19): a frame every 0.5 s across **all**
fish-visible time, tiles ≥300 px wide, a drawn center line. Pass = the fish (head, if
it doesn't fit) is on or near the line at every sustained instant; only brief (≲0.7 s)
excursions during fast swings are tolerated. 180-px tiles hide failures that are
obvious on a phone. Produce the sheets and look at every tile; don't assert it.

**Step 8 — chapter joins.** When one continuous take spans a GoPro chapter split, make
it two segments whose crop X agrees within ~50 px at the join, or the picture jolts.

**Common failures and fixes**

| Symptom | Cause | Fix |
|---|---|---|
| Box slides onto water mid-span | missing anchor in a fast move | add anchors every 0.3–0.5 s there |
| Box consistently offset from fish | anchor box misread (often off a small tile) | re-read from a fresh full-size frame |
| Crop snaps at span edges | `track_from/to` with no ramp room | widen `ramp` or move `track_from` earlier |
| Fish centered but head cut off | fish wider than window | `bias` toward the head |
| Crop drifts during the netting swing | tracking empty frames | end the track at exit, `path` bridge to re-entry |
| Crop "swims" back and forth | track too noisy | raise `smooth` slightly; fix the anchor, not the smoothing, if it's one bad patch |
| Topwater strike outside the frame | position read off the rings a second later | measure x at the first frame the water breaks (4 fps scan), verify on the encoded output |

## 12. build_edit.py — one JSON per edit

Encodes every segment (cached by content hash), assembles them with `concat_av.py`,
runs `check_av_sync.py`, and writes the `check_cuts.py` list.

```bash
python3 $SKILL/scripts/build_edit.py "$WORK/c1_edit.json" [--only TAG,TAG] [--no-concat]
python3 $SKILL/scripts/check_cuts.py "$WORK/c1_base.cuts.json" --fix "$WORK/c1_cuts_fixed.json"
```

Top-level keys:

| Key | Meaning |
|---|---|
| `name` | prefix for cached segment files |
| `mode` | `"portrait"` (1080×1920) or `"landscape"` (1920×1080) |
| `srcdir` | folder with the sources; each `src` is a file **stem**, opened as `<stem>.MP4` |
| `wavdir` | optional: folder of `<stem>.wav` (§3) → writes `<out stem>.cuts.json` |
| `work` | per-segment encodes (re-used while the segment's JSON is unchanged) |
| `out` | assembled video; also writes `<out stem>.segments.json` |

Per-segment keys:

| Key | Meaning |
|---|---|
| `tag`, `src`, `in`, `out` | label, source stem, absolute in/out seconds |
| `S` | portrait: fixed subject x (1920 space), default 960 |
| `path` | portrait: `[[t_abs, S], …]` piecewise-linear subject x (held flat beyond the ends) |
| `track`, `track_start` | fishtrack2 output file + the START it was run with |
| `track_from`, `track_to`, `ramp` | span where the track drives the crop; blend length (s, default 0.6) |
| `smooth` | gaussian sigma (s) on the track, default 0.35 |
| `bias` | `[[t_abs, dx], …]` head-side offset added to the track (1920 px) |
| `zoom` | landscape: `[[t0_abs, t1_abs, factor, S, Y], …]` constant punch-in windows (factor ≥ 1; S, Y in 1920×1080 space) |
| `pre` | path to an already-encoded segment to use as-is (must match the encode settings) |

Example — a two-beat portrait highlight from 4K (fight compressed with one hard cut,
then hold-up and release on the track):

```json
{"name": "c1", "mode": "portrait",
 "srcdir": "<footage_dir>",
 "wavdir": "<work_dir>/wav",
 "work":   "<work_dir>/build",
 "out":    "<work_dir>/c1_base.mp4",
 "segs": [
  {"tag": "C1a-bite", "src": "GX020156", "in": 812.4, "out": 820.9,
   "path": [[812.4, 900], [818.0, 1040], [820.9, 1100]]},
  {"tag": "C1b-aboard-hold-release", "src": "GX020156", "in": 829.6, "out": 851.2,
   "S": 1060,
   "track": "<work_dir>/c1_track.txt", "track_start": 829.5,
   "track_from": 830.0, "track_to": 849.5, "ramp": 0.6, "smooth": 0.35,
   "bias": [[836.0, 0], [837.0, 180], [843.0, 180], [844.0, 0]]}
 ]}
```

Notes: encodes are video-only; the soundtrack is rebuilt from the source by
`concat_av.py`. If both `path` and `S` are given, `path` wins (`S` is only the fallback).
The script decodes with `-hwaccel videotoolbox` on macOS and
no hardware decode elsewhere; override with `FFMPEG_HWACCEL=cuda|vaapi|none` (see
[setup.md §10](setup.md#10-linux-notes)).

## 13. Manual segments + concat_av / check_av_sync

When not using `build_edit.py`, encode every segment with identical settings so the video
streams join losslessly:

```bash
ffmpeg -v error -y -ss 812.4 -i "$SRC" -t 8.5 \
  -vf "fps=30000/1001,scale=1920:1080,setsar=1,format=yuv420p" \
  -r 30000/1001 -video_track_timescale 30000 \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p -an "$WORK/seg01.mp4"
```

Then assemble — audio is cut on exactly the same frame as the picture:

```bash
# segments.json: [[encoded_segment.mp4, source_media, source_in_s], ...] in play order
#   source_in_s must equal the -ss used for that segment
python3 $SKILL/scripts/concat_av.py   "$WORK/segments.json" "$WORK/base.mp4"
python3 $SKILL/scripts/check_av_sync.py "$WORK/segments.json" "$WORK/base.mp4"   # must exit 0
#   optional: --max-ms 45
```

- `concat_av.py` stream-copies the video and rebuilds the soundtrack once from the
  source, sample-exact to each segment's frame count. It refuses a file whose tracks
  start >1 ms apart.
- **Never** `ffmpeg -f concat -c copy` segments that each carry their own AAC: priming
  and padding leave a gap/overlap at every cut, and real players (QuickTime, browsers)
  drift — ~1 s after ~95 cuts. ffmpeg-based spot checks look perfect, which is why
  `check_av_sync.py` decodes the way players do.
- No `xfade`, `acrossfade`, `fade`, `afade`, J/L cuts or overlaps — hard cuts only.
- Any later step that touches audio (bleep §16, wind §17, voice swap §18) operates on the
  assembled file with `-c:v copy`, so the cut points don't move.

## 14. Burned captions

```bash
python3 $SKILL/scripts/burn_captions.py CONCAT_LIST BASE.mp4 OUT.mp4 [EXTRA.json]
python3 $SKILL/scripts/burn_captions.py CONCAT_LIST BASE.mp4 - EXTRA.json     # dry run: print chunks only
```

- Without `manual_chunks`, word timing comes from transcribing **each segment's own
  audio** listed in `CONCAT_LIST` (lines `file '…'`), offset by its start. Segments from
  `build_edit.py` are video-only, so with those **always use `manual_chunks`**; then
  `CONCAT_LIST` can be any file (an empty one is fine) because nothing is transcribed.
- Font: `$CAPTION_FONT` (default macOS Arial Bold), size 62, white, 7 px black border,
  centered at x = (w−text_w)/2−60 (nudged left of TikTok's right-hand button rail).

`EXTRA.json`:

```json
{
  "manual_chunks": [
    [0.42, 1.60, "Oh, there he is!"],
    [1.75, 3.10, "Get up here, buddy."],
    [9.80, 11.40, "That's a nice one,"],
    [11.40, 12.90, "look at that belly."]
  ],
  "texts": [
    {"text": "SNUCK HIM OUT OF THE PADS", "t0": 0, "t1": 3.0, "size": 74, "y": 260}
  ],
  "cap_y": 1360,
  "max_display": 3.5,
  "suppress_caption_windows": [[20.0, 24.5]],
  "corrections": {"Sinko": "Senko"}
}
```

| Key | Meaning |
|---|---|
| `manual_chunks` | `[[t0, t1, text], …]` in output-clip seconds; replaces whisper chunking |
| `texts` | extra drawtext elements: `text, t0, t1`, optional `size` (62), `y` (240), `x`, `border` (7) |
| `cap_y` | caption band y (default 1230). Keep < 1436 (TikTok covers the bottom 484 px); 1360 sits under a fish held low |
| `max_display` | longest a chunk stays up (s) |
| `suppress_caption_windows` | `[[t0, t1], …]` where no caption may start (silent cards) |
| `corrections` | exact-token fixes for whisper misreads (whisper-timed mode only) |

Rules:
- **Verbatim.** Captions are the speaker's exact words. Never paraphrase, tidy, or summarize.
- **One line, ~26 characters max** at size 62 (fewer with a wider font). A longer chunk
  runs off the frame edge — drawtext does not wrap. Split a long sentence into
  consecutive verbatim chunks at natural phrase breaks (2–4 words each), dividing the
  island's time between them.
- Time chunks from speech islands (§7), not whisper `-ml` word times, on short or quiet
  lines.
- No two captions on screen at once (the script enforces it); bracketed tags
  ("[wind]", "(beep)") never appear; no caption over a centered fish's body.
- Burn captions **last** — after the bleep and any card overlays — and take chunk timing
  from the clean, pre-bleep audio: a bleep tone confuses whisper's word alignment.
- QA: read the printed chunk list, then render frames at several caption midpoints and
  look at them (§19).

## 15. Catch-still overlay cards

Full-frame still of a catch, hard-cut onto the exact words that point at it ("this one…
and this one") — for recaps that compare fish.

```bash
# 1) grab the hold-up frame from the 4K source (pick matching poses across fish)
ffmpeg -v error -y -ss 845.2 -i "$SRC" -frames:v 1 -q:v 2 "$WORK/hold1.jpg"
# 2) build a 1080x1920 card: crop ~2200x1000 around the fish over a blurred, darkened copy
ffmpeg -v error -y -i "$WORK/hold1.jpg" -filter_complex "[0]split[a][b];\
[a]scale=-2:1920,crop=1080:1920,boxblur=40:2,eq=brightness=-0.25[bg];\
[b]crop=2200:1000:900:700,scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2,\
drawtext=fontfile='${FONT}':text='FISH #1':fontsize=72:fontcolor=white:borderw=6:bordercolor=black:x=(w-text_w)/2:y=420" \
  -frames:v 1 "$WORK/card1.png"
# 3) overlay on the assembled base for a window found on the speech islands (§7)
ffmpeg -v error -y -i "$WORK/base.mp4" -loop 1 -i "$WORK/card1.png" -filter_complex \
  "[0:v][1:v]overlay=0:0:enable='between(t,317.2,319.6)':shortest=1,format=yuv420p[v]" \
  -map "[v]" -map 0:a -c:a copy -r 30000/1001 -video_track_timescale 30000 \
  -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p "$WORK/base_cards.mp4"
```

Chain more cards with more `-loop 1 -i` inputs and overlays. A split comparison card
(#1 above #2) is the same recipe with two `fg` crops stacked. Keep labels inside the safe
zone ([portrait-shortform.md](portrait-shortform.md)). Trim dead pauses so no card is
static for more than ~5 s. Then burn captions on top (§14) with the card windows in
`suppress_caption_windows` if the card should be silent.

## 16. Bleeping a curse

Portrait/short-form clips get curses bleeped; whether long-form does is an editorial call
([editing-rules.md](editing-rules.md)). The bleep must be syllable-surgical: neighbors stay
audible ("Let's ⟨bleep⟩ing go").

**Step 1 — find the neighborhood.** Whisper (isolated window, §6) tells you roughly where.
Never place the bleep from whisper word times — they can be 0.3 s off, and seconds off
over splashing. Tell: after bleeping, an isolated-window transcript still prints the
curse. If so, trim the window start forward until the curse disappears from the
transcript; that brackets the real word.

**Step 2 — measure true boundaries on a low/high-band envelope.** Work on the **assembled
file you will modify** (any filtering upstream shifts timing):

```bash
ffmpeg -v error -y -ss 247.0 -t 4 -i "$WORK/base.mp4" -ar 16000 -ac 1 -c:a pcm_s16le "$WORK/curse.wav"
python3 - "$WORK/curse.wav" <<'EOF'
import sys, wave, numpy as np
w = wave.open(sys.argv[1]); sr = w.getframerate()
a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
win = int(sr * 0.010)                                   # 10 ms windows
f = np.fft.rfftfreq(win, 1 / sr)
lo = (f >= 100) & (f < 1000); hi = (f >= 3000) & (f < 7500)
rows = []
for i in range(0, len(a) - win, win):
    s = np.abs(np.fft.rfft(a[i:i + win] * np.hanning(win))) ** 2
    rows.append((i / sr, 10 * np.log10(s[lo].sum() + 1e-12), 10 * np.log10(s[hi].sum() + 1e-12)))
ml = max(r[1] for r in rows); mh = max(r[2] for r in rows)
for t, dl, dh in rows:                                  # bars: dB below the loudest window
    print(f"{t:5.2f}  lo {dl-ml:6.1f} {'#' * max(0, int((dl - ml + 40) / 1.5)):<27}"
          f"  hi {dh-mh:6.1f} {'+' * max(0, int((dh - mh + 40) / 1.5))}")
EOF
```

- The **low band** (vowels) shows syllable bursts and the dips between words.
- The **high band** shows fricatives. "sh-", "f-", "s-" curses open with a quiet
  /ʃ/ /f/ /s/ 0.1–0.2 s **before** the loud vowel — invisible on a plain RMS envelope.
  Start the mute where the high band first lifts off the floor after the previous word's
  dip, not at the vowel burst.
- End the mute at the dip before the next syllable. Typical window 0.3–0.6 s.

**Step 3 — mute + 1 kHz tone at speech loudness** (T1/T2 in the file's seconds;
BLEEP_DUR = T2−T1; T1_MS = T1×1000):

```bash
ffmpeg -v error -y -i "$WORK/base.mp4" \
  -f lavfi -i "sine=frequency=1000:duration=BLEEP_DUR:sample_rate=48000" \
  -filter_complex "[0:a]volume=enable='between(t,T1,T2)':volume=0[a0];\
[1:a]volume=2.0,pan=stereo|c0=c0|c1=c0,adelay=T1_MS|T1_MS[bp];\
[a0][bp]amix=inputs=2:duration=first:normalize=0[aout]" \
  -map 0:v -map "[aout]" -c:v copy -c:a aac -ar 48000 -ac 2 -b:a 192k "$WORK/base_bleep.mp4"
```

ffmpeg's `sine` source has a fixed amplitude of 1/8 (≈ −18 dBFS) and no amplitude option;
`volume=0.3` buries it, `volume=2.0` lands at shouting level (≈ −15 dB RMS).
Several curses: one `between()` per window joined with `+`, one sine input per tone.

**Step 4 — verify on the finished file.** (1) Envelope again: word burst → flat
constant-level tone → next word burst, neighbors intact. (2) Transcribe an isolated
~0.7 s window of just the bleep: a correct bleep returns `(beep)` or nothing. A
whole-clip transcript that still prints the curse is **not** proof of failure — whisper
reconstructs bleeped words from context. If the preceding word got clipped or the tone is
buried, adjust and redo; a bleep that can't be made clean means dropping the line.

## 17. Wind-noise filter

Action-cam wind rumble sits almost entirely below ~200 Hz, often 25–35 dB above the
speech band. Two steep high-passes remove it; RNNoise cleans the broadband hiss without
eating the voice:

```bash
ffmpeg -v error -y -i "$WORK/clip.mp4" \
  -af "highpass=f=250:p=2,highpass=f=250:p=2,arnndn=m=$SKILL/scripts/rnnoise_std.rnnn:mix=0.75" \
  -c:v copy -c:a aac -ar 48000 -ac 2 -b:a 192k -movflags +faststart "$WORK/clip__windfilter.mp4"
```

- Measured: wind −13 to −27 dB, speech band −2.4 dB, whisper reads it the same, 1 kHz
  bleep tones survive. Re-check bleep windows anyway.
- Tried and rejected: `afftdn` alone (too mild), `arnndn` at `mix=1.0` with a 300 Hz
  high-pass (removed the voice), `arnndn` + `afftdn` stacked (−9 dB off speech).
- On a windy day, ship the filtered version as the main clip and keep the raw-audio cut
  beside it (`__original_audio.mp4`) so the angler can compare. No music, EQ or loudness
  normalization beyond this.
- Judge with a per-second band profile (<200 / 200–500 / 500–3000 Hz) on wind seconds vs
  speech seconds, not by ear alone.

## 18. Music / copyright audit and voice-stem swap

Background music (a PA across the water, a passing boat) can get a clip flagged. Order of
work: **build → audit → isolate → bleep → captions → audit again.**

**Detect:**

```bash
python3 $SKILL/scripts/music_audit.py "$WORK/clip.mp4" [--work DIR] [--chunk 5]
#   per 5 s chunk: sus (sustained bass on the accompaniment stem) + whisper's tag on that stem
#   exit 1 if any chunk reads as MUSIC
```

A real song reads `sus ≈ 1.0` with "(upbeat music)". Wind also scores high `sus` but tags
as wind. **On calm, music-free days the audit still flags a few chunks on `sus ≥ 0.6`
alone with an empty or `[BLANK_AUDIO]` tag — those are false positives. The AST check
decides.**

**AST "Music" check** (AudioSet classifier, bundled; tested on real trip audio). Run with the
demucs venv, which has torch + transformers. The first run downloads the model (~350 MB):

```bash
~/.demucs-venv/bin/python $SKILL/scripts/music_ast_check.py "$WORK/clip.mp4" [2.5]
#   one line per 2.5 s window: start, music=<score>, top-3 AudioSet labels; "<<<" when > 0.1
```

If you copy the script elsewhere, **never name it `ast.py`**. That shadows the stdlib module and
breaks `import torch` with a circular-import error.

Clean outdoor audio scores 0.00–0.05; real songs 0.3–0.7. Treat >~0.1 **sustained over
2–3 consecutive windows** as music. A single window at 0.12–0.14 during emphatic speech is
not music.

**Fix — swap in the demucs voice stem inside the ranges only:**

```bash
python3 $SKILL/scripts/voice_isolate.py "$WORK/clip.mp4" "$WORK/clip_vox.mp4" \
  --ranges "209.776:233.934,301.2:315.0" [--work DIR]
```

- Video is copied; each range is separated with 1 s of context and written back
  sample-exact. Put range edges on the edit's cut frames so the change in audio texture
  lands on a hard cut, never mid-shot.
- Sung vocals survive in the voice stem. When music sits right under the words at > 0.3,
  prefer dropping the line.
- Re-transcribe afterwards (the speech should survive intact) and re-run both detectors.

## 19. Output QA sheets

Every check below runs on the **encoded output**, not the source.

**Centering sheet** (portrait; every 0.5 s across fish-visible time; ≥300 px tiles):

```bash
CLIP="$WORK/c1_base.mp4"; A=0; B=22                       # output-clip seconds
ffmpeg -v error -y -ss $A -t $((B-A)) -i "$CLIP" -vf "fps=2,\
drawbox=x=538:y=0:w=4:h=1920:color=red@0.85:t=fill,scale=300:-1,\
drawtext=fontfile='${FONT}':text='%{pts\:hms}':x=6:y=6:fontsize=20:fontcolor=yellow:box=1:boxcolor=black@0.6,\
tile=6x2" -fps_mode vfr "$WORK/center_%02d.jpg"
```

(The `pts` label here is relative to `-ss $A`; add A. `fps=2` is fine for a QA sheet,
where exact labels matter less than density.)

**Paddle / fiddling audit** (assembled cut, 1 fps, 320 px tiles, 6×8 = 48 per sheet): a
stowed paddle lies flat on the deck; a paddle in use shows a raised blade with the shaft
crossing the frame diagonally. Colour-based detectors don't work; look.

```bash
ffmpeg -v error -y -i "$WORK/final.mp4" -vf "fps=1,scale=320:-1,\
drawtext=fontfile='${FONT}':text='%{pts\:hms}':x=6:y=6:fontsize=20:fontcolor=yellow:box=1:boxcolor=black@0.6,\
tile=6x8" -fps_mode vfr "$WORK/audit_%02d.jpg"
```

**Caption QA:** read `burn_captions.py`'s printed chunk list, then grab a frame at the
midpoint of several chunks and look for overflow, split words, and text over the fish:

```bash
for t in 1.0 4.2 10.6 12.1; do
  ffmpeg -v error -y -ss $t -i "$WORK/final_captioned.mp4" -frames:v 1 -vf scale=540:-1 "$WORK/cap_$t.jpg"
done
```

**Sync:** `check_av_sync.py` must exit 0 on every deliverable (§13).

## 20. Thumbnails and wildlife — pointers

- **Thumbnails:** `python3 $SKILL/scripts/make_thumbnail.py --video SRC.MP4 --time T
  --headline "PAYOFF" [--kicker "context"] [--pos tr|tl|bl] [--crop auto] --out thumb.jpg`
  (or `--image`). It grades, sets the two-tier text, and writes small-size and grayscale
  proofs unless `--no-proof`. Process and text rules:
  [thumbnails-titles.md](thumbnails-titles.md).
- **Wildlife zoom clips (4K):** finders → tracker → virtual camera (`wildlife_scan.py`,
  `wildlife_motion.py`, `wildlife_speck.py`, `wildlife_flock.py`, `wildlife_track.py`,
  `wildlife_reframe.py`), all run with `~/.wildlife-venv/bin/python`. Full recipe:
  [wildlife-zoom.md](wildlife-zoom.md). In zsh, brace the font variable inside filters:
  `drawtext=fontfile=${FONT}:text=…` — `$FONT:text=` is read as the `:t` path modifier and
  silently mangles the filter.
