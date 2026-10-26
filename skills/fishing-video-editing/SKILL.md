---
name: fishing-video-editing
description: Edit raw action-camera fishing footage (GoPro, Insta360, DJI, phone; kayak, boat, shore, ice; any species) into finished clips. Covers long-form landscape YouTube edits, one portrait 9:16 TikTok/Reels/Shorts feature per catch, a 3–6 minute full-trip TikTok recap, talking-head monologue clips, and 4K wildlife zoom clips. Handles transcription with whisper.cpp, finding the catches, cutting only after finished sentences, keeping the fish centered with a tracker, captions, hooks, bleeps, wind and music cleanup, and A/V-sync verification with ffmpeg. Use this skill whenever someone points at a folder of fishing footage or asks to "edit my fishing video", "make highlight clips/shorts/TikToks", "cut the catch", "make a YouTube video from my trip", "zoom in on the eagle", or anything about turning fishing camera files into shareable video, even if they never say "skill" or name a format.
---

# Fishing video editing

This skill turns a folder of raw fishing footage (usually hours of mostly-nothing with a few minutes of action) into
tight, shareable clips. The craft below came from many rounds of real feedback from an angler who posts these edits.
Most rules exist because breaking them once produced a clip that got rejected, so the reasoning is kept alongside
each rule.

Everything here is about editing. Fishing advice, trip planning and catch logging are out of scope.

## 1. Pick the deliverable

Ask which outputs they want if it isn't clear. A single trip often wants several.

| Mode | Shape | Use it when | Reference |
|---|---|---|---|
| **A: Long-form edit** | landscape 16:9, 1920×1080 | YouTube or desktop viewing; "edit it together", "the YouTube video". Intro → every catch's full arc, chronological → outro | `references/youtube-longform.md`, `references/thumbnails-titles.md` |
| **B: Catch features** | portrait 9:16, 1080×1920, 30–60 s each | TikTok, Reels or Shorts; "highlight clips", "shorts". One clip per catch, catch-only | `references/portrait-shortform.md` |
| **R: Full-trip recap** | portrait 9:16, 3–6 min | "TikTok long form", "recap". All catches plus the story beats in one video | `references/tiktok-longform.md` |
| **D: Talk clips** | portrait 9:16 | The angler does an on-camera monologue on a topic (usually opening with the topic and closing with "what do you think?"). Clip the whole section continuously | `references/editing-rules.md` §8 |
| **W: Wildlife zoom** | portrait 9:16 from **4K only** | "Zoom in on that heron/eagle/beaver". A virtual camera that tracks the animal and holds it big in frame | `references/wildlife-zoom.md` |

**Portrait or landscape?**
- Phone-first platforms (TikTok, Reels, Shorts) get portrait 9:16.
- YouTube long-form and anything watched on a TV or desktop gets landscape 16:9.
- A portrait crop of a 16:9 source throws away about 70% of the width, so portrait clips depend on the
  fish-centering tracker (§4).
- 4K source makes portrait crops sharp: a 1215×2160 window scales cleanly to 1080×1920. 1080p source still works
  (a 608×1080 window, upscaled) but looks softer.

Check transcripts for monologue sections (Mode D) and on-camera wildlife callouts (Mode W) on every trip. Anglers
drop them into ordinary fishing days.

## 2. Non-negotiable rules (full list and reasons in `references/editing-rules.md`)

1. **Hard cuts only.** No fades, dissolves or crossfades.
2. **Cut only after a finished sentence, in real silence. Never mid-word.**
   - Pick cut points from speech islands (`scripts/speech_islands.py`), not whisper word times. Whisper word times
     drift by hundreds of ms, and by seconds over splashing.
   - Verify every segment list with `scripts/check_cuts.py` (voice-activity detection). Re-transcribing can't catch a
     chopped word, because whisper reconstructs "fis-" as "fish".
3. **Audio is cut with the video: same frame, no J/L cuts, no overlaps.**
   - Assemble with `scripts/concat_av.py` (`build_edit.py` does this for you).
   - Verify with `scripts/check_av_sync.py`.
   - Concatenating per-segment AAC with `-c copy` drifted about 1 s out of sync in QuickTime while looking fine in
     ffmpeg.
4. **Full catch arc, including the release.** The arc is bite → fight → landing → hold-up → weigh-in (if any) →
   release → the angler's last line about the fish.
   - Long-form keeps the whole arc.
   - Features and recaps compress it but never drop the hold-up or the release.
5. **A visible fish is centered by a verified per-frame track, never an eyeballed crop.** If the whole fish won't
   fit, frame the head and let the tail clip.
6. **Nothing the angler says to the editor goes in an edit.** That means lines like "zoom in on that", "remind
   me…", "use this as the outro" and "test of the 4K" are notes, not content.
7. **No other people** on camera or audio beyond the angler, unless they ask. Drop conversations with
   passers-by.
8. **Keep the original audio.** No added music. Background music that's already in the footage is a copyright risk
   on social platforms: audit it, then remove or replace that audio (§5).
9. **Short-form gets bleeps** for profanity (1 kHz tone, original muted). Long-form follows the angler's preference.
10. **Cut the boring mechanics.** Net fumbling, unhooking struggles, scale rigging, re-tying, weed-cleaning and
    paddling don't belong in features or montages. The exception is when a line that needs to stay is spoken over them.

## 3. Workflow (details and commands: `references/workflow.md`, `references/cookbook.md`)

1. **Inventory.**
   - `ffprobe` resolution, fps and duration for every `GX*.MP4` (or the camera's equivalent).
   - Ignore `.LRV` proxies for editing but use them for fast contact sheets.
   - Note the chaptering: GoPro splits a session into `GX01nnnn`, `GX02nnnn`…
2. **Audio → transcript.**
   - Extract 16 kHz mono WAVs.
   - Run `whisper-cli` with `small.en`, **one job at a time**. Many parallel jobs crashed a 16 GB machine.
   - Look for hallucination loops (one phrase repeated for minutes, "(crickets)", "[Music]") and re-transcribe those
     clips in ~120 s chunks.
   - Save transcripts somewhere durable, not `/tmp`.
3. **Find the catches.**
   - Grep the transcripts for reactions ("fish on", "got one", "there we go", "look at that", weights, "thank you").
   - Confirm on contact sheets: 1 frame per 10 s, then 1 per second around each hit.
   - Quiet catches exist. Scan the visuals even where the transcript is empty.
4. **Map each arc** in source seconds: the bite or reaction line, the visible fight, the net, each hold-up (which way
   the head points), the scale reading, the release splash, the last line. Write it into `EDIT_NOTES.md` as you go.
5. **Choose segments.**
   - Use `scripts/transcribe_islands.py <wav> <start> <end>` for phrase-accurate timing.
   - Hard-cut out the dead middles: unhooking, scale rigging, silence.
   - Run `check_cuts.py` and apply `--fix`. Review any "REVIEW" extension by ear or with islands.
6. **Frame it.** Portrait catch shots use tracked crops (§4). Static S=960 is fine for talking and scenery.
7. **Build.**
   - Write one JSON per deliverable.
   - Run `scripts/build_edit.py edit.json`. It encodes, assembles and runs the sync check.
8. **Verify the picture.**
   - Make a 1 fps contact sheet of the build.
   - Then check full-size frames at every hold-up. 180 px tiles hide a head cut off at the edge.
   - The audit sheet also catches paddling, other people and dead air.
9. **Finish.**
   - Bleeps (short-form).
   - Captions and hook text with `scripts/burn_captions.py` (verbatim, ≤ 26 characters per line, inside the safe
     zones).
   - Re-run `check_av_sync.py` on the captioned file.
   - Run the music audit (§5).
   - Spot-check rendered caption frames.
10. **Deliver.** Final videos plus `EDIT_NOTES.md` go in one output folder:
    - a table of files, with length and what each one is;
    - the arc table with source timestamps;
    - the segment in/out points;
    - the exclusions;
    - a "left out for length" list, so the angler can ask for any of it back.

## 4. Keeping the fish in the middle (full procedure: `references/cookbook.md` §11)

The portrait crop's horizontal position `S` (in 1920-wide coordinates, whatever the source resolution) is driven
three ways in `build_edit.py`:

- **Fight and landing:** a hand-keyed `path` of `[t, S]` points, read every 1–3 s off grid frames
  (`scripts/keyframe_grid.sh`). Aim at the line entry or the splash, and lead the action a little.
- **Hold-ups:** a **fishtrack2 track**.
  - Read 2–4 keyframe boxes `[t, x, y, w, h]` off grid frames (top-left corner, 1920×1080 space). Choose poses where
    the fish is clearly visible.
  - Run `scripts/fishtrack2.py SRC START END kf.json track.txt`. It tracks forward and backward from every keyframe
    and blends the two.
  - Feed the track into the segment with `track_from`/`track_to`, `smooth` 0.3–0.35 and a `ramp`.
- **Head-side bias:** a 2 lb+ fish held sideways is wider than the 608-px (1920-space) window, so the crop can't show
  it whole.
  - Add `bias` (about +100 to +300 toward the head) so the head stays in and the tail clips. Never the other way
    around.
  - Check large frames at the start, middle and end of every hold-up. A head cut off at the edge is the most common
    rejection.

Re-check after every bias change. If the track drifts (a fast swing, the fish dropped into the lap), end `track_to`
earlier and let `path` take over.

## 5. Audio finishing (`references/cookbook.md` §16–18)

- **Bleeps:**
  - Find the word with `transcribe_islands.py`, then confirm its edges on a low-band/high-band envelope. Fricatives
    like f, s and sh show as high-frequency energy.
  - Mix a 1 kHz sine at volume 2.0 over the window and mute the original there.
  - Verify by transcribing the windows just before and just after. Whisper will "hear" a bleeped word from context,
    so don't trust it on the bleep itself.
- **Wind:**
  - On windy trips, run a highpass at 250 Hz twice, then RNNoise (`arnndn` with `scripts/rnnoise_std.rnnn`, a one-time download (see setup.md §6), mix 0.75).
  - Ship the filtered cut as the main file and keep the raw cut as an alternate.
- **Background music (copyright):**
  - Run `scripts/music_audit.py` (demucs stems plus a whisper tag).
  - Then confirm with the AudioSet AST classifier: music above ~0.1 sustained over 2–3 s is real music. Flags based
    only on sustained bass ("sus") with blank tags are usually false positives on calm days.
  - Fix real music with `scripts/voice_isolate.py` (swaps in the demucs voice stem inside the ranges), or drop the
    line.

## 6. Captions, hooks, cards

- Burned captions run the whole runtime on portrait clips.
  - They're verbatim (never paraphrase to fit), 2–5 words and one clause per chunk, at most ~26 characters, timed
    to the speech islands.
  - Caption band at y ≈ 1360 of 1920 (`cap_y`; the script's default is 1230). Keep the top ~150 px, bottom ~484 px, right ~180 px and left ~60 px clear.
- **Hook:** two short lines of on-screen text for the first ~3 s. Use count, novelty or stakes, often in the
  angler's own words.
- **Recap cards:**
  - A `CATCH n/N` counter at each catch.
  - A tally card near the end (≤ 6 words).
  - Optional full-frame stills of catches, cued by the angler's words ("this one… and this one").
- Details are in `references/portrait-shortform.md` and `references/tiktok-longform.md`.

## 7. Tools

Install with `references/setup.md`:
- ffmpeg/ffprobe;
- whisper.cpp (`whisper-cli`) with the `ggml-base.en` and `ggml-small.en` models;
- Python 3 with numpy, webrtcvad, soundfile and Pillow (OpenCV is only needed in the wildlife venv);
- optional: a demucs + transformers venv (music audit), and a wildlife venv with ultralytics/sahi plus tracker
  models (Mode W).

| Script | Does |
|---|---|
| `build_edit.py` | One JSON per edit → encodes the segments (portrait/landscape, tracked crops, punch-ins), assembles them with `concat_av.py`, runs `check_av_sync.py` |
| `check_cuts.py` | Voice-activity check of every in/out point; `--fix` moves chopped cuts |
| `concat_av.py`, `check_av_sync.py` | Sample-exact audio assembly; sync check the way real players play it |
| `fishtrack2.py` | Keyframe-anchored bidirectional fish tracker → `t x y conf` at 15 fps |
| `burn_captions.py` | Captions (`manual_chunks`) and text elements (`texts`) burned in |
| `speech_islands.py`, `transcribe_islands.py` | Real speech boundaries, and per-phrase transcripts for cuts and captions |
| `keyframe_grid.sh` | Grid-overlaid frames for reading tracker boxes and path points |
| `music_audit.py`, `music_ast_check.py`, `voice_isolate.py` | Background-music detection (demucs stems, then the AudioSet "Music" score), and removal |
| `make_thumbnail.py` | YouTube thumbnail recipe (punch-in, grade, two-tier text, proofs) |
| `wildlife_*.py` | Mode W: find, track and reframe animals in 4K |

The scripts honour these environment overrides: `WHISPER_MODEL`, `CAPTION_FONT`, `THUMB_FONT`, `DEMUCS_PY`,
`WILDLIFE_MODELS`, and `FFMPEG_HWACCEL` (defaults to `videotoolbox` on macOS and none elsewhere; set `cuda`/`vaapi` on
Linux GPUs).

## 8. Reference map: read what the task needs

- `references/editing-rules.md`: every rule with its reason, per mode. **Read this before cutting anything.**
- `references/workflow.md`: the step-by-step process and the `EDIT_NOTES.md` template.
- `references/cookbook.md`: exact commands, the `build_edit.py` JSON schema, fish centering, bleeps, wind, cards.
- `references/portrait-shortform.md`: catch features (structure, hooks, captions, safe zones, checklist).
- `references/tiktok-longform.md`: the full-trip recap (cadence, counters, bridges, close, checklist).
- `references/youtube-longform.md`: landscape long-form (story, pacing, punch-ins, paddling audit, checklist).
- `references/thumbnails-titles.md`: YouTube packaging.
- `references/wildlife-zoom.md`: Mode W end to end.
- `references/lessons-learned.md`: the traps that cost real time. Skim it once per job.

## 9. Working habits that matter

- Run heavy steps in the background: audio extraction, transcription and 4K encodes. 4K frames are about 25 MB each
  raw, so pipe them rather than writing frame sequences to disk. Watch free disk space.
- Use a scratch dir for WAVs, frames and segment encodes. Keep proof files in the output folder: edit JSONs, tracker
  keyframes and tracks, caption JSONs, bleep windows, transcripts.
- When you can't find something the angler mentions (a bird, "the second fish"), search around the cue (±2 min)
  first. Then ask them where it was before giving up.
- Finished videos are hundreds of MB to over a GB. Hand back the folder path rather than trying to upload them
  somewhere.
- When you deliver, give the angler the paths, lengths and beat list. Say what's excluded and what was left out for
  length.
