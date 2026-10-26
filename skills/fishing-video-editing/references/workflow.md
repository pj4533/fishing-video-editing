# Workflow: raw footage to a finished edit

The end-to-end process for every mode. The rules for *what* to cut are in
[editing-rules.md](editing-rules.md). Exact commands are in [cookbook.md](cookbook.md), and
installs are in [setup.md](setup.md). Mode-specific craft:
[youtube-longform.md](youtube-longform.md), [portrait-shortform.md](portrait-shortform.md),
[tiktok-longform.md](tiktok-longform.md), [wildlife-zoom.md](wildlife-zoom.md),
[thumbnails-titles.md](thumbnails-titles.md). Traps collected along the way:
[lessons-learned.md](lessons-learned.md).

Placeholders: `<footage_dir>` (the camera card or copied folder), `<work_dir>` (scratch:
WAVs, frames, segment encodes), `<output_dir>` (deliverables only). Script paths are relative to
the skill directory (`scripts/<name>`).

## Contents
0. [Workspace and job hygiene](#0-workspace-and-job-hygiene)
1. [Inventory the footage](#1-inventory-the-footage)
2. [Wall-clock time](#2-wall-clock-time)
3. [Extract audio](#3-extract-audio)
4. [Transcribe](#4-transcribe)
5. [Locate the moments](#5-locate-the-moments)
6. [Map each catch's arc](#6-map-each-catchs-arc)
7. [Build the beat sheet / cut list](#7-build-the-beat-sheet--cut-list)
8. [Pick cut points](#8-pick-cut-points)
9. [Build](#9-build)
10. [Audio passes: bleeps, wind, music](#10-audio-passes-bleeps-wind-music)
11. [Captions and text](#11-captions-and-text)
12. [Final QA](#12-final-qa)
13. [Deliver + EDIT_NOTES.md](#13-deliver--edit_notesmd)

---

## 0. Workspace and job hygiene
- Keep everything intermediate in `<work_dir>`. Only the final videos, `EDIT_NOTES.md` and a small
  `proof/` folder go in `<output_dir>`. `proof/` holds the edit JSONs, tracker keyframes and
  tracks, caption JSONs, bleep windows and transcripts.
- **Copy proof files to `<output_dir>/proof/` as you go.** Scratch directories (especially under
  `/tmp`) can be wiped by a crash or reboot, and transcripts take hours to regenerate.
- Run long steps (audio extraction, transcription, encodes, tracking) as background jobs, **one
  whisper job at a time**. ~20 concurrent whisper runs once crashed a 16 GB machine and took the
  scratch dir with it. Encodes and frame pulls can overlap with a single whisper job.
- 4K frames are ~25 MB raw. Pipe them (`-hwaccel videotoolbox` on macOS, `rawvideo` to stdout)
  and never write long 4K frame sequences to disk. Downscale stills you keep.

## 1. Inventory the footage
- **Which files are real.** On GoPro, `GX*.MP4` (HEVC) or `GH*.MP4` (H.264, older bodies) are the
  video. `GL*.LRV` are low-res proxies and `*.THM` are thumbnails: never edit from them. An LRV
  can stand in for a quick triage contact sheet on a slow-to-decode 4K day, but confirm its
  duration matches its `GX` twin, and do every real frame check on the `GX`. Other cameras
  (DJI, Insta360) use their own names, so the idea is the same: find the full-res masters.
- **Chapter naming.** `GXccnnnn.MP4`: `nnnn` = the recording number, `cc` = the chapter. One long
  recording splits into `GX01nnnn, GX02nnnn, ...` at the ~4 GB limit (roughly 10 min per chapter
  at 4K ~50 Mbps, ~20–26 min at 1080p). **Chapters of one recording are gapless.** A catch that
  straddles a split is still one continuous take, so cut it as two segments that join seamlessly.
  The release "thank you" may open the next file. Sort by recording number, then chapter (not by
  plain filename, because `GX020163` sorts after `GX010164`).
- **Probe every file** (`ffprobe`, cookbook): resolution, fps, codec, duration, `creation_time`.
  Footage may be **1080p or 4K (3840×2160)** and can change between trips. 4K enables sharp
  portrait crops (1215×2160 window) and wildlife zooms (Mode W). 1080p portrait uses a 608×1080
  window. Expect 29.97 fps (`30000/1001`) and AAC 48 kHz stereo, but check.
- Write a clip table in `<work_dir>`: file, duration, start wall-clock (§2), one-line content note.
  It becomes the top of EDIT_NOTES.

## 2. Wall-clock time
Transcript and cut timecodes are **per clip** (seconds from that file's start). You'll also want
real time of day for story beats, the recap's arc and the notes.
- **Recording start:** the first chapter's `creation_time` (ffprobe). Many cameras write local
  time but tag it `Z`/UTC, so sanity-check against the light in the frames and the file mtime.
  The mtime is usually the chapter's *end* time.
- **Estimate any moment:** `wall ≈ recording_start + sum(durations of earlier chapters) + t`.
  Chapters are near-constant length, so `(chapter − 1) × typical chapter length + t` is a fine
  quick estimate. Recompute from real durations for anything you write down.
- **Calibrate against an on-screen clock** when one exists: a phone or fish-finder mounted on the
  boat showing the time, a watch in a hold-up shot, or the angler saying the time aloud. Read it
  off a full-res frame and compute the offset. Camera clocks drift, and one was ~2 min ahead of
  the angler's phone.
- Separate recordings (a new `nnnn`) have a real gap between them. Use each one's own
  `creation_time`.

## 3. Extract audio
Per clip, 16 kHz mono PCM WAV, which is what whisper and the cut checker want. It's fast because
only the audio stream is decoded. Keep these WAVs for the whole job. `check_cuts.py`,
`speech_islands.py` and caption timing all read them.

## 4. Transcribe
- **Use whisper.cpp `whisper-cli` with `ggml-small.en.bin`** on every clip. base.en is faster
  but misses speech buried under ambient sound, and on quiet days it's nearly all hallucination.
  **Keep stdout**: it carries the `[hh:mm:ss.mmm --> ...]` timestamps, and `-otxt` alone drops
  them.
- **Detect hallucination loops.** Whisper locks onto a phrase over near-silence, music or water
  noise. One 26-minute clip came back as ~100 repetitions of a single cooking sentence. Watch for
  "(crickets)", "[Music]", "♪" or a run of identical lines. A quick check:
  `grep -E '^\[' clip.stdout.txt | cut -d']' -f2 | sort | uniq -c | sort -rn | head`. Any line
  repeated more than ~3 times is suspect.
- **Break loops by re-transcribing in chunks**: the same WAV in ~120 s windows with 2 s
  overlap, then add each chunk's offset back (cookbook). The loop can't carry across a chunk
  boundary. Filter the ambient tags afterwards. A clip that reduces to one or two real lines really
  was quiet. That's a finding, not a failure.
- **Recover a buried catch.** Cut a short (~50 s) WAV of just the suspected bite window and
  transcribe it alone. Isolation kills the hallucination. Timestamps are relative to the window.
- For tight work, transcribe **speech islands individually** with `scripts/transcribe_islands.py`.
  It finds islands with silencedetect and transcribes each one. You get one line per real
  utterance with trustworthy edges, which is far better than whisper's drifting blocks.
- Whisper timestamps are approximate at every level. Use them to *find* lines, never to *cut*
  on (§8).

## 5. Locate the moments
Use two channels. They cover each other, and on some days only one works.

**Audio (grep the transcripts):**
- **Intro:** the greeting or place intro near the start of the first clip.
- **Catches:** the bite reaction ("is that a fish", "fish on", "there we are", "ooh, okay"), the
  fight and landing ("got him", "come here"), size and weight talk, and the release line ("thank
  you", "thanks, buddy", "see ya").
- **The tally line** ("three fish today") tells you how many catches to find. Use it to confirm
  you found them all.
- **Outro:** the wrap-up near the end of the last clip.
- **Monologue sections (Mode D):** the series name, topic vocabulary, and the closer ("what do you
  think?"). Check every trip.
- **Sightings (Mode W):** "look at that", "oh my gosh", "over there", species names.
- **Meta-talk to exclude:** the assistant's name or nickname,
  `remind me|zoom|4k|footage|outro|shopping list|the plan`. Log each hit in EDIT_NOTES under
  exclusions.
- **Other people:** greetings to shore, "how's it going", boat motors. Flag them for frame checks.

**Visual (contact sheets), required to confirm catches:**
- Sample a frame every 5–10 s per clip and tile ~100 per sheet. Scan for a bent or loaded rod, a
  net coming out, a fish held up to the camera, splashes.
- Densify to ≤ 2 s (then 0.5 s) around anything suspicious. A small fish can be visible for only
  ~2 s of the whole arc.
- Crop-zoom a full-res frame to confirm a fish or animal when a tile is ambiguous.

**Silent catches.** Some catches have no speech at all: no reaction, no hold-up talk, no
thank-you. Then the visual scan is the only channel.
1. Work **backward from proof of a landed fish** (a fish visibly in hand, net or line), stepping
   back ≤ 2 s at a time until the rod loads. That's the bite. The clip starts before it.
2. **Hands down at the lap is not proof.** It looks the same for unhooking, re-rigging and
   weed-picking. When it's your only lead, densify around it and keep scanning *earlier*. The real
   arc is usually 1–3 min before the fiddling.
3. Write each stage's timestamp down before cutting (§6).

**Wildlife (Mode W):** the transcript cue is only a prior. Run `scripts/wildlife_scan.py` (tiled
detector) and `scripts/wildlife_motion.py` (motion finder) roughly 120 s either side of it,
including stretches where the camera faces the cued direction. Then track and reframe per
[wildlife-zoom.md](wildlife-zoom.md). Motion finders raise false birds (a dangling lure, a lens
speck), so confirm on frames.

## 6. Map each catch's arc
For every catch, fill one row with **source file + source seconds** for each stage, each
verified on a frame:

| Stage | What to pin | How |
|---|---|---|
| Retrieve | rod working, line slack or steady, ~1–5 s before the bite | step back from the bite on frames |
| Bite | first frame the rod loads (not the reaction word) | frames at 0.5 s; transcript as the prior |
| Fight / landing | splashes, jumps, net in and out, lift aboard | frames; note net time to cut later |
| Hold-up | each sustained pose, and which side the head is on | big frames (tracking anchors) |
| Weigh | scale on and off, the spoken weight | transcript + frames |
| Release | the let-go and the splash | frames at 0.5 s |
| Last line | the post-release line, and when the phone comes out | speech islands + frames |

Then densely sample the **gaps between stages**. Landing → hold-up is the riskiest. List the
dead stretches to cut ("cuts 312.35 → 339.9: net fumbling, unhooking"). This table goes straight
into EDIT_NOTES and drives every mode, because features, the recap and the long-form all reuse it.

## 7. Build the beat sheet / cut list
- **Long-form (Mode A):** tag every candidate moment from the transcripts and sheets: `catch /
  decision / setback / theory / joke / scenery / wildlife / callback-seed / tease`. Find the day's
  question (the angler's stated goal) and theme. That decides which non-catch lines survive.
  Find the setup lines for every callback. Structure and pacing:
  [youtube-longform.md](youtube-longform.md).
- **Features (Mode B):** two shots per catch from the arc table. Pick the tier (feature vs long
  catch story) per [portrait-shortform.md](portrait-shortform.md).
- **Recap (Mode R):** the features plus bridges. Density and ordering rules are in
  [tiktok-longform.md](tiktok-longform.md).
- Write each edit as **one JSON for `scripts/build_edit.py`**: `mode` (portrait or landscape),
  source dir, WAV dir, work dir, out path, and a `segs` list of `{tag, src, in, out}`, plus framing
  (`S` fixed x, a `path` of `[t, x]` keyframes, or a fishtrack2 `track` with head `bias`, all in
  1920-wide coordinates; landscape punch-ins via `zoom`). Schema and example: cookbook §12.

## 8. Pick cut points
- **Find edges on speech islands, not whisper times.** `scripts/speech_islands.py` (silencedetect
  over a WAV window) lists where speech starts and stops. Its threshold defaults to `-35` dB;
  over paddle or wind ambient pass a higher one (`-30`, or `-23` in strong wind), and on very
  quiet audio a lower one (`-40`). Put out-points in the silence
  after a finished sentence and in-points in the silence before the first word.
- Watch for **trailing tag phrases** a beat after the apparent end ("...no problem.").
- Pull frames around each boundary to pin the visual moment (rod load, net, release splash).
- **Run `scripts/check_cuts.py` on the segment list** (`[[tag, wav, in, out], ...]`, which
  `build_edit.py` also writes as `*.cuts.json`). Apply `--fix`, re-check for the whole thought
  (editing-rules §2.2), review REVIEW-marked extensions, and re-run until zero chops. Do this
  **before encoding**.
- Cross-check every kept segment against the content rules: no meta-talk, no other people, no
  hand-held phone, no bodily noises (small.en tags), no paddling or maintenance unless speech
  needs it.

## 9. Build
- **Portrait features and the recap:** track every fish-visible stretch first with
  `scripts/fishtrack2.py`. Anchors come from big gridded single frames
  (`scripts/keyframe_grid.sh`), and the tracking runs both ways between anchors. Verify the track
  with box overlays, then reference it in the JSON. Procedure: [cookbook.md](cookbook.md).
- **Run `python3 scripts/build_edit.py EDIT.json`.** It encodes each segment to one normalized
  format (cached by content hash, so re-runs only re-encode what changed), assembles with
  `scripts/concat_av.py` (video stream-copied, soundtrack rebuilt once from the source,
  sample-exact) and runs `scripts/check_av_sync.py`. `--only TAG,TAG` rebuilds selected
  segments.
- Building by hand instead: encode every segment with identical params, then `concat_av.py` +
  `check_av_sync.py`. **Never** `ffmpeg -f concat -c copy` segments that carry their own AAC.
- Mode W renders through `scripts/wildlife_reframe.py` instead. Thumbnails come from
  `scripts/make_thumbnail.py` ([thumbnails-titles.md](thumbnails-titles.md)).

## 10. Audio passes: bleeps, wind, music
Order: **build → music audit → voice isolate (if needed) → bleep → captions → audit again →
sync check.**
- **Music audit** every finished file: `scripts/music_audit.py` plus the AudioSet (AST) "Music"
  check (cookbook). Sustained > ~0.1 over 2–3 s is music. Fix it by dropping the line, or with
  `scripts/voice_isolate.py --ranges` with edges on cut frames.
- **Bleeps** (short-form modes only): find the curse in the transcript, then take the boundaries
  from the 10 ms low/high-band energy envelope (cookbook §16). Mute and insert a 1 kHz tone at
  speech loudness. Verify on the finished clip that the words on both sides survive. Record
  each bleep window (final time + source time).
- **Wind:** on a windy day, also make the filtered variant (two 250 Hz high-pass stages +
  RNNoise mix 0.75, video copied) and keep `__original_audio` beside it. Re-check bleeps after.
- Re-run `check_av_sync.py` on every file any of these passes touched.

## 11. Captions and text
- Portrait modes get verbatim, clause-chunked captions plus a frame-one hook. Use
  `scripts/burn_captions.py` with **`manual_chunks`** timed from speech islands (source-time
  chunks mapped into final time). One whisper pass over a finished video drifts by seconds and
  splits words. Set `cap_y` for the safe zone (≈ y 1230–1360 on 1080×1920, above the platform's
  bottom UI and under a low-held fish).
- Hooks, counters (`CATCH n/N`), tally cards and still cards are drawtext or overlay elements.
  Placement, dwell and limits are in [portrait-shortform.md](portrait-shortform.md) and
  [tiktok-longform.md](tiktok-longform.md).
- Burn captions after bleeping, and censor curse text in the captions.
- Spot-check rendered frames at several caption midpoints: no split words, no overlap, no
  annotation leakage ("[Music]"), inside safe zones.

## 12. Final QA
Run this on the **final files**, not the segments:
1. `check_cuts.py` passes (zero chops) on the shipped segment list.
2. `check_av_sync.py` passes on every final file, after all audio and caption passes.
3. **Arc presence:** a frame for retrieve, rod load, fish, hold-up and release in every catch,
   with timestamps logged.
4. **1 fps contact sheets of the whole assembled cut** on ≈ 320 px tiles (6 columns, ~48 per
   sheet). Look for paddling, hands on the lure, drinking, a hand-held phone, other people or
   boats, and dead water inside catches. At 250 px tiles, paddle strokes got missed.
5. **Portrait framing:** every 0.5 s across fish-visible time on ≥ 300 px tiles, plus full-size
   frames at each hold-up pose. The fish must be present (no fish = fail), centered, and
   head-in-frame.
6. **Beat check:** frames at the expected beats (intro, cast, fight, net, hold-up, release, next
   catch, outro) all landed.
7. **Listen to every cut boundary and bleep** in the final audio, or transcribe a 3 s window
   around each one.
8. Music audit clean. Durations are in band (features 30–60 s).

## 13. Deliver + EDIT_NOTES.md
- Put the final videos in `<output_dir>` with descriptive names:
  `catch1_<weight-or-tag>_highlight_portrait.mp4`, `<trip>_full_trip_tiktok.mp4`,
  `<trip>_youtube.mp4`, `wildlife_<animal>_portrait.mp4`, plus any `__windfilter` or
  `__original_audio` variants. Mode A also gets `thumbnail.jpg` and title suggestions
  ([thumbnails-titles.md](thumbnails-titles.md)).
- Finished videos run to hundreds of MB and won't fit a chat upload. Give the path. Don't
  re-encode a smaller copy unless asked.
- **Write `EDIT_NOTES.md`** beside them. It's the record that lets anyone rebuild, tweak or
  re-cut the edit without re-watching hours of footage:

```markdown
# EDIT_NOTES: <trip title> (<day>, ~<start>–<end> wall clock)

**Source:** <footage_dir>, <camera>, <resolution> <codec> <fps>, ~<total hours>.
- GX01–12 nnnn: <wall start>–<wall end>.      # one line per recording

**The ask:** <which modes; anything they said to include or skip>.

| File | Length | What |
|---|---|---|
| `catch1_..._highlight_portrait.mp4` | 0:58 | <fish, bait if said, the key lines in quotes> |
| `..._full_trip_tiktok.mp4` | 5:38 | full-trip recap (below) |
| `proof/` | | edit JSONs, tracker keyframes + tracks, caption JSONs, bleep windows, transcripts |

**Build and checks:** build_edit.py (<crop>); check_cuts passes on all; check_av_sync worst
case <n> ms after captions; hard cuts + original audio; wind filter yes/no.

## Arc presence (source seconds)
| Catch | Source | Bite | Fight / landing | Hold-up | Scale | Release | Last line |
|---|---|---|---|---|---|---|---|
| 1 · <wt> | GX060163 | 286.9 "Fish? Fish." | rod loads 290, net 302–321 | 340–351 (head left) | 368–378 | 389.5 | "thank you" 390.2 |

**What the features cut:** per catch, the source ranges removed and why
(e.g. 312.35 → 339.9 net fumbling + unhooking).

**Tracking:** track names per catch, head-bias values, where the tail clips, how output was verified.

**Hooks / captions:** hook text per file, caption y, timing source.

## <Mode> segment list
| Final | Source | In → Out | Beat |       # every segment, in play order, with its key line
|---|---|---|---|

**Bleeps:** final time, source time, word (censored), how verified.
**Music audit:** result per file, any flags and why they're false positives.

**Excluded everywhere:** meta-talk lines (with source time), other people, private audio.
**Rule exceptions:** e.g. paddling visible under a necessary line, with the time.

**Left out for length (each easy to add back):** line or moment + source file/time, one per bullet.
```

- Keep the "left out for length" list honest and specific. It's the menu the angler picks from
  when they ask for a longer cut or a different story.
- After the angler reviews, record what they approved or rejected and why in EDIT_NOTES (and in
  [lessons-learned.md](lessons-learned.md) if it generalizes). Most rules in
  [editing-rules.md](editing-rules.md) started as one of those notes.
