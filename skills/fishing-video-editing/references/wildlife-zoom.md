# Wildlife zoom clips (portrait 9:16 from 4K)

One portrait 1080x1920 clip per wildlife sighting: an eagle, heron, osprey, kingfisher,
hawk, beaver, otter, deer, turtle, a flock of geese. You find the animal in the 4K frame,
track it frame by frame, and render a smooth "virtual camera" crop that keeps it centred
and zoomed in hard. There's no fish and no catch arc.

The shared rules still apply ([editing-rules.md](editing-rules.md)): hard cuts only,
original audio, cuts only after finished sentences, audio cut with the video, and nothing
the angler says to the editor goes in the clip. For caption styling and safe zones, see
[portrait-shortform.md](portrait-shortform.md). For the generic ffmpeg recipes
(silencedetect, single-frame grabs, contact sheets, concat), see
[cookbook.md](cookbook.md).

---

## When it applies

- **4K source only.** A distant bird is 15–80 px wide in a 3840x2160 frame. At 1080p it
  is a smudge, and no crop or upscaler can recover it. Check with
  `ffprobe -v error -select_streams v:0 -show_entries stream=width,height SRC.MP4`. If the
  footage is 1080p, say so and don't try.
- **Daylight only.** At dusk, a dark animal on dark water shows up only as a wake. Every
  finder fails and so does the eye at native resolution with a gamma lift. Don't spend an
  hour on a last-light sighting. Write it up in the notes as unrecoverable.
- **The lens sets the limit.** A wide action cam gives about 32 px per degree at 4K, so a
  2 m wingspan is ~75 px at 50 m and ~25 px at 150 m. Past ~80 m, an action cam is the
  wrong lens and no process fixes that. Sky specks can still make a short "look how far"
  clip.
- Corners of a wide action-cam frame are 5–20x softer than the centre. An animal near
  the edge will look worse at the same crop.

**The angler's camera-directed lines are notes, not content.** Lines like "you've got to
zoom in on that", "such a good test of the 4K" or "that's another zoom shot" are requests
to the editor. They go in the notes, never in the clip. If the angler's reaction line runs straight
into one ("Look at that bird, yep, that's another zoom-in shot"), the cut checker will find
no clean gap between them. Drop the whole line and let the hook caption carry the clip.
Never keep the meta line.

---

## Python environment

Use a dedicated venv with the detector dependencies (e.g. `~/.wildlife-venv`). Install
`torch`, `ultralytics`, `sahi`, `opencv-contrib-python` (VitTrack lives in contrib),
`scipy`, `numpy` and `pillow`. **System Python usually lacks `sahi` and
`opencv-contrib`**, and the scan and track scripts fail on import without them. Full
install steps are in [setup.md](setup.md).

```bash
V=~/.wildlife-venv/bin/python        # or wherever your detector venv lives
S=path/to/skill/scripts
W=$(mktemp -d)                       # scratch: crops, sheets, tracks
```

**Models** are read from `$WILDLIFE_MODELS`, which defaults to `~/.wildlife-models`.
Override it per run with `WILDLIFE_MODELS=/some/dir $V $S/wildlife_scan.py ...`.

| File | Used by |
|---|---|
| `yolo11s.pt` | `wildlife_scan.py` (default COCO "bird" mode) |
| `yoloe-11s-seg.pt` + `mobileclip_blt.ts` (~600 MB text encoder) | `wildlife_scan.py --prompt` (non-bird animals) |
| `object_tracking_vittrack_2023sep.onnx` (OpenCV zoo) | `wildlife_track.py` |

**Platform notes.** The scripts decode with `-hwaccel videotoolbox` on macOS (none
elsewhere; override with `FFMPEG_HWACCEL=cuda|vaapi|none`) and the scan defaults to
`--device mps` (Apple silicon). On Linux or Windows, pass `--device cpu`/`cuda:0`. The
`--mark` label font in `wildlife_reframe.py` defaults to a macOS path; set `$CAPTION_FONT`
elsewhere. Run detector passes **one at a time**: several MPS/GPU models at once on
a 16 GB machine will swap and hang.

---

## 1. Find the cue, then search AROUND it

Transcribe with a model that doesn't hallucinate on quiet audio (see
[cookbook.md](cookbook.md)). Quiet wildlife stretches are where small whisper models
invent text. Grep for reactions:

```
eagle|bird|hawk|heron|osprey|kingfisher|vulture|beaver|otter|deer|turtle|geese|dog|whoa|holy|look at|wow|is that
```

**A cue is a prior, not the answer.** The animal is usually in frame **before** the angler says
anything and often stays after. A typical sighting: the eagle sits in frame for ~10 s, the angler
looks up, it flies, and *then* they say "whoa". By the time they speak they may be looking at
the pads, paddling or turning back. The animal is on camera during the seconds they
*watch* it, which can be a minute before or after the line. Whisper timestamps on quiet
clips also drift 1–4 s early. Pin the real speech onset with `silencedetect` before
cutting.

**Search window: −120 s to +120 s around the FIRST cue line**, extended to the angler's last line
about the animal. A long sighting ("is that a dog?… is that a dog?… big ears… is it a
deer?") spans the whole run.

Three passes:

1. **Headings.** Make a 1 fps contact sheet of the window (proxy/low-res file is fine).
   Mark every stretch where the camera **faces** the water, shore or sky the animal is
   in. Those stretches are the search space, not the cue seconds. Use any geography they
   give you ("across the neck, toward the point with the house").
2. **Finders on the facing stretches.** Run the motion finder and the tiled detector
   (below) at 1–2 fps with `--conf 0.15`.
3. **Eyes on 4K.** For each facing stretch, take native-resolution crops along the far
   shoreline and open water every 2–3 s. A swimmer's V-wake stays visible long after the
   head doesn't. For a heron, scan the reed and shore edges: a standing heron doesn't
   move, so the motion finder can't see it.

**A detector miss means look harder, not "not in frame".** A 15–25 px swimming head or a
heron standing in reeds is missed by both COCO "bird" and text-prompted detectors.

**Before giving up, ask the angler for geography.** Ask which shore, which direction, and
what they were doing. Then report what was searched and why it wasn't found. Never just say
"not in frame". Keep the source footage until the clips are signed off, because a
re-search needs it.

**They may only have heard it.** An angler can call out a bird three times when it's on
camera once, for 0.4 s (a ~40 px fly-by across the far bank). The other callouts were the
bird's call. To actually film a kingfisher-type bird, point the camera at a known perch
and let it roll. Note that as a shooting tip.

---

## 2. The finders

Each finder covers the other's blind spot. Run both on the facing stretches, then **look
at the sheets**. The scores only rank candidates. Your eyes decide.

| Finder | Sees | Blind to | Cost (Apple silicon) |
|---|---|---|---|
| `wildlife_scan.py`: yolo11s COCO "bird" on 960 px native tiles (SAHI) | perched AND flying birds down to ~60 px; zero false positives on bird-free 4K sky at conf 0.2 | 15 px specks against a dark hillside; non-birds need `--prompt` | ~1–2 s / 4K frame, so run at 1–2 fps, never 30 |
| `wildlife_motion.py`: homography-compensated dual-interval (Δ1∩Δ5) differencing + sky mask + tracklets, no models | anything that MOVES against sky or a bright treeline, down to ~15 px | a perched or motionless animal; dark bird on dark trees; whip pans (skipped frames) | ~0.1 s / 4K frame |
| `wildlife_speck.py`: black-hat blob chaining on bright sky | a soaring bird of 6–20 px, too small for VitTrack | anything not against bright sky | fast; it's a tracker, needs anchors |
| `wildlife_flock.py`: turns a scan into a flock-centre track | a V of geese with many tiny detections per frame | single animals | instant |

### wildlife_scan.py (tiled detector)

```bash
$V $S/wildlife_scan.py SRC.MP4 $W/scan --start S --end E [--fps 1] [--conf 0.2] \
    [--tile 960] [--overlap 0.2] [--max-box 600] [--device mps] [--prompt "beaver,otter"]
```

- Writes `scan/scan.json` (`{samples:[{t, dets:[{conf, box:[x1,y1,x2,y2], name}]}]}` in
  4K px), `scan/timeline.txt` (one line per sample), and `scan/hits_sheet.jpg` (a 400x400
  crop around the best box of every hit frame). It prints contiguous hit runs as
  `candidate window A-Bs`.
- `--conf 0.15` for a thorough search pass, `0.2` for clean runs.
- `--max-box` drops whole-tree hallucinations.
- `--prompt "deer,dog"` / `"beaver,otter"` / `"turtle"` switches to YOLOE-11s
  open-vocabulary prompts. Confidence runs lower and there's more junk on pads and
  reflections, so the hits sheet is the judge. Untested on most mammals in daylight.
  Expect it to work like the bird scan for anything ≥60 px.

### wildlife_motion.py (motion finder)

```bash
$V $S/wildlife_motion.py SRC.MP4 $W/motion --start S --dur D \
    [--proc-w 1920] [--top 6] [--no-sky-mask] [--sky-max-frac 0.55]
```

- Writes `motion/tracks.json` (all kept tracklets, best first, points
  `(t_abs, cx, cy, w, h)` in **source 4K px**) and `motion/trackN_crops.jpg` (8 crops
  along each top track). It prints `trackN: t0-t1s n= speed= area= contrast= score=
  first=(x,y)`.
- The **default mask is sky-only**: bright upper part of the frame, rows below
  `--sky-max-frac` of the height ignored. That mask suits flying birds.
- **Bird against a dark hillside:** `--no-sky-mask` (searches everything above
  `--sky-max-frac`).
- **Animal in or on the water** (swimming deer, beaver, otter, dog):
  `--no-sky-mask --sky-max-frac 0.8`. Expect ripple junk in the crops.
- A chosen track's points make good anchors for the tracker as-is.

### wildlife_speck.py (tiny sky birds)

```bash
$V $S/wildlife_speck.py SRC.MP4 START END anchors.json $W/track.txt
```

Positional args only. `anchors.json` uses the same format as the tracker's keyframes
(`[[t_abs, x, y, w, h], ...]`, top-left boxes in 4K px). It chains black-hat blobs on
bright sky in both directions from each anchor and writes the tracker's `track.txt`
format, so the output goes straight to the reframer. **Run a rolling-median outlier pass
on the track first**: a lost frame can extrapolate far off.

### wildlife_flock.py (flocks)

```bash
$V $S/wildlife_flock.py $W/scan/scan.json $W/track.txt [--start S --end E] \
    [--min-n 2] [--jump 700] [--pad 200]
```

Per sample, the flock box is the min/max of all detection centres. The subject is its
midpoint and the "size" is the flock extent plus `--pad`, so the reframer's auto width
holds the whole V. Samples with fewer than `--min-n` birds only count within `--jump` px
of the last centre. Run a scan at 2+ fps over the flock window first. Reframe with
`--k 1.3 --min-w 700`. **Physical limit:** a flock along the top edge of the 4K frame
can't be centred in 9:16, because the crop clamps at y=0. It rides the top tenth of the
portrait frame.

### False positives to reject on sight

- **A dangling lure.** The motion finder's top water track can be the angler's lure swinging from
  the rod tip: an upright 40x70 px figure with "legs" (a jig skirt), swinging across the
  far bank. Before trusting any upright track, check the full frame for the line running
  into it.
- **Fixed lens specks.** Sky hits at the **same frame position on every sample** are a
  water drop, speck or flare on the lens, not a bird.
- **Pad and water debris.** At conf 0.15, the tiled detector calls leaves, debris and
  pad flowers on the water "bird". The motion finder's crops identify the real one.
- **Rod tip, line, stumps, a turtle on the pads.** These all score. A real bird is
  obvious on the crops.

---

## 3. Track: one box per frame at native 4K

`wildlife_track.py` uses keyframe-anchored, bidirectional VitTrack. Each span between two
anchors is tracked forward from the left one and backward from the right one, then
blended by time. Frames scoring below `--min-score` in both directions are marked `lost`
and interpolated between confident neighbours. Anchors are ground truth.

```bash
$V $S/wildlife_track.py SRC.MP4 START END keyframes.json $W/track.txt \
    --verify $W/track_verify.jpg --min-score 0.15
```

- `keyframes.json`: `[[t_abs, x, y, w, h], ...]`, 3840x2160 px, **x,y = top-left**,
  sorted, all inside `[START, END]`. Boxes can be tiny (16x12 for a far speck). VitTrack
  still holds them at score 0.2–0.4, which is why `--min-score 0.15` (default 0.3) suits
  small animals.
- Output `track.txt`: one line per frame, `t_abs cx cy w h score flag` (flag `ok|lost`).
- **VitTrack's internal score threshold must be 0.** The script sets
  `tracking_score_threshold = 0` and gates on the score itself. With the default
  threshold, VitTrack returns (0,0,0,0) forever after one low-score frame in a whip pan.
  Keep it that way if you modify the script.
- Needs `opencv-contrib-python` (`cv2.TrackerVit`).

**Reading anchors.** Read boxes off big single frames, never off small montage tiles.
Crop ~500x500 around the expected spot, scale 2x and add `drawgrid=w=100:h=100`, so each
grid line is 50 source px. Read the box in source px. Scan boxes and motion-track points
are good anchors as-is.

**Anchor density:**
- Every ~2 s while the animal moves slowly and the head is steady.
- **Every 0.15–0.3 s through a head whip, a take-off, or a shape change.** A startled
  look-up moves the image 200–250 px per frame at 4K, more than any tracker's search
  window, so dense anchors carry it. One clean eagle take-off needed 16 anchors.
- Linear interpolation across a lost span of a fast take-off doesn't work, because the
  true path is curved. Add anchors instead.
- Dark bird against a dark hillside with no finder hits: hand-anchor along a straight
  line so the crop at least looks at the right place, or skip that section.

**Verify every tile** of `track_verify.jpg` (480 px crops every 0.35 s, box drawn, green
= ok, red = interpolated). A box off the animal means you add an anchor there. Never nudge
the crop to compensate. Red boxes that sit on the animal are fine (low score in motion
blur).

---

## 4. Reframe: the virtual camera

```bash
$V $S/wildlife_reframe.py SRC.MP4 $W/track.txt seg.mp4 [--start S --end E] \
    [--width "t:w,t:w,..." | --k 9 --min-w 600 --max-w 1215] \
    [--sigma 0.4] [--sigma-w 0.8] [--subject-y 0.5] [--cas 0.4] [--crf 18] \
    [--verify $W/reframe_verify.jpg] [--mark "t0:t1[:label]" ...] [--mark-style circle|arrow|both]
```

How it works: the subject path is smoothed with a zero-phase gaussian (`--sigma` s;
offline, so no lag). Crop width per frame is either `--k` x the animal's box size clamped
to `[--min-w, --max-w]` and smoothed by `--sigma-w`, or piecewise-linear `--width`
keyframes (`t_abs:px`). The crop is lanczos-resized to 1080x1920 (area when downsampling)
and sharpened with ffmpeg CAS. Audio is the source audio for exactly the same span. A hard
clamp keeps every crop within **[48, 1215] px** wide. `--start/--end` default to the
track span.

### Zoom: extreme by default

Zoom factor = **1215 / crop width** (1215 px is a full-height 9:16 slice of 4K, i.e. 1.0x).

**Default: extreme zoom. Crop width ≈ 3–4x the animal's box width**, so it fills
~25–33% of the frame width. That can mean a crop as small as ~48 px of source (25x). The
point of shooting 4K for wildlife is a big animal on screen. A pixelated, frame-filling
bird beats a clean speck, which is how a 12 px kingfisher ends up shipped. A 12–14 px
kingfisher at a 48 px crop against grey sky still reads as a flapping kingfisher
silhouette. Don't ask whether to zoom. Just zoom.

```bash
# auto extreme zoom: animal ~1/3.5 of frame width; tight path smoothing
$V $S/wildlife_reframe.py SRC.MP4 track.txt seg.mp4 --k 3.5 --min-w 48 --sigma 0.06 \
    --verify $W/reframe_verify.jpg

# punch-in: wide POV while the angler reacts, snap in hard when the animal is identifiable
# (two keyframes ~0.03-0.12 s apart = a hard punch-in)
$V $S/wildlife_reframe.py SRC.MP4 track.txt seg.mp4 \
    --width "458.90:800,459.02:120,459.70:120,460.10:400,462.26:400" --sigma 0.06
```

- **The script's argparse defaults (`--k 9 --min-w 600`) are the conservative cut**, not
  the recommended one. Always pass the extreme-zoom flags or `--width` keyframes.
- Use **tight path smoothing (`--sigma ~0.06`)** at extreme zoom. A 48–150 px crop can't
  absorb a lagging path, so the animal drifts out of frame.
- Force a fixed crop with `--min-w W --max-w W`.
- A punch-in is the most watchable form for a speck: open wide, snap in for the action
  beat, pull back for the angler's line.
- A conservative 600 px cut can ride along as an extra in a subfolder. Never ship it as
  the main clip.

### The tradeoff: what the background does to a tight crop

The background sets how mushy a crop looks, more than the animal does. Smooth backgrounds
survive upscaling. Textured ones smear into "watercolour" while the animal stays readable.

| Background | Holds up to | Why |
|---|---|---|
| Clean sky (silhouette) | ~140 px (8.7x) clean; far tighter still reads | smooth gradient, nothing to smear; fingered wingtips survive at 8.7x |
| Open water | ~200 px (6x) | ripple texture softens but still reads as water |
| Treeline / bank / weeds | ~400–600 px | leaves and branches are high-frequency detail and go watercolour past ~6x |

The older conservative ladder used **600 px (1.8x up) as the floor, 480 px (2.25x) for a
"look how far" speck**, with <450 called unusable. It optimised image cleanliness. On a
phone, viewers care more about seeing the animal, so extreme zoom is the default now.
Mention the softness honestly in the notes. No upscaler recovers a 15 px bird, and GAN
super-resolution flickers frame to frame. Lanczos + CAS is the pipeline. Pick moments
where the animal is biggest.

### Other reframe notes

- **Near the top edge** the crop clamps and the animal rides above centre. That's a
  physical limit, so accept it.
- `--subject-y 0.45` leaves a little headroom under a caption.
- **Marker for a hard-to-see animal:** `--mark "300.0:302.9:bald eagle"` draws a white
  circle + arrow + label on the tracked animal for that source-time window, popping in and
  out over 0.2 s. It follows the raw track, not the smoothed camera. Use it for a perched
  or motionless animal before the action beat and end it before the animal moves. Deliver
  it as a `_marked` variant next to the clean cut, never instead of it, and never on an
  animal that already fills the frame.
- **Verify the output** (`--verify`): a tile every 0.5 s with red centrelines (360 px
  tiles). The animal must sit on or near the line in every tile where it's visible. If it
  doesn't, fix the track, not the crop.
- The reframer muxes source audio for the same span. For multi-segment clips, still
  assemble with `concat_av.py` and verify with `check_av_sync.py` ([cookbook.md](cookbook.md)).

---

## 5. Cut points, length, captions, delivery

**In/out:**
- **Start** ~0.3–0.5 s before the animal is first identifiable, or before the angler's first word
  about it if that comes first.
- **End** after the angler's last finished sentence about the animal, or when the animal leaves
  the frame, whichever is later.
- Run `check_cuts.py SEGMENTS.json --fix FIXED.json` on the segment list. Everything they say *to the editor* after
  the sighting is out.

**Length is content-limited:** one-beat sighting (a flyover) 7–15 s; two-beat story
(perched → take-off → flight) 20–35 s with the payoff by ~8–10 s. A take-off clip can be
12 s because the bird leaves the frame when the angler turns their head. **Never pad with fishing.**

**Captions:** whisper word timing is unusable on short, quiet reaction lines. It drifts
1–2 s early and hallucinates, e.g. "I pulled you. Fine." for "There's a bald eagle…
flying". **Time caption chunks from `silencedetect` speech bursts** and pass them as
manual chunks to `burn_captions.py`. Hook: 4–8 words in the top third (y≈200–300), on
frame one, ending before the action beat. Spoken-line captions sit low (y≈1230) so they
stay under the centred animal. Safe zones and styling are in
[portrait-shortform.md](portrait-shortform.md). Check captions on rendered frames.

**Deliver** per sighting: the clip, an `EDIT_NOTES.md` (source file, in/out, crop
widths, zoom factor, an honest quality verdict), and a `proof/` folder (track + reframe
verify sheets, `keyframes.json`, caption JSON) so the clip can be re-cut later.

---

## Shooting tips to pass on to the angler

- Shoot 4K. A 4:3 4K mode, if the camera has one, gives more vertical pixels for 9:16.
- Keep the animal in the centre third of the frame (sharpest part of the lens).
- Hold the head still on it for 2–3 s, because a whip pan kills tracking.
- Don't export through the camera vendor's phone app. Work from the original files.
- For perch birds (kingfishers), point the camera at the perch and let it roll.

Hard-won failures and their fixes are collected in [lessons-learned.md](lessons-learned.md).
