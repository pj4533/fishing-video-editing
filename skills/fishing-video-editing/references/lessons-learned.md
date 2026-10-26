# Lessons learned — gotchas that already cost a redo

Each item is a mistake that shipped (or nearly shipped) and the rule that prevents it.
Commands are in [cookbook.md](cookbook.md); editorial rules in
[editing-rules.md](editing-rules.md).

## Contents
1. [Transcription and timing](#1-transcription-and-timing)
2. [Cuts and assembly](#2-cuts-and-assembly)
3. [Framing and fish centering](#3-framing-and-fish-centering)
4. [Captions and on-screen text](#4-captions-and-on-screen-text)
5. [Audio: bleeps, wind, music](#5-audio-bleeps-wind-music)
6. [Wildlife](#6-wildlife)
7. [Shell, Python and machine](#7-shell-python-and-machine)
8. [Editorial traps](#8-editorial-traps)

---

## 1. Transcription and timing

- **Whisper hallucinates over music and near-silence.** It loops one phrase (sometimes for
  an entire 25-minute clip), and labels water/wind ambience as "(crickets)", "[Music]",
  "[BLANK_AUDIO]". "No speech" from base.en is not evidence of no catch. Re-run small.en,
  re-transcribe in 2-minute chunks to break loops, and check frames.
- **The bite hides under the hallucination.** The exact window whisper wrote "(crickets)"
  over is often where the quiet "oh, is that a fish?" is. Isolate a 20–50 s window and
  transcribe it alone.
- **On quiet days base.en output is mostly invented.** Use small.en for every clip.
- **`-otxt` drops timestamps.** Keep whisper's stdout.
- **Whisper reconstructs chopped and bleeped words from context.** A cut through "fis-"
  still prints "fish"; a fully bleeped curse still prints the curse in a whole-clip pass.
  So whisper can never verify a cut or a bleep. Use `check_cuts.py` (VAD) for cuts and the
  envelope + an isolated 0.7 s window for bleeps.
- **Whisper times are approximate at every level.** Segment times drift seconds within a
  clip. Words at a window edge get smeared over leading noise. `-ml 1` word times drift
  ~100–300 ms, and over splashing they can be **seconds** off. Whisper says *what*; speech
  islands and the energy envelope say *when*.
- **Trailing tags belong to the line.** "…made it, made it. No problem." — the tag can land
  1+ s after the apparent end. Check the next speech island before cutting.
- **The loud moment is not the event.** A topwater strike's own splash is often quieter
  than the rod/reaction noise ~1 s later, and the angler's excited line usually comes
  after the hookset. Find bites and eruptions visually, frame by frame.
- **A "hands down at the lap" frame is not a catch.** It looks identical when retying or
  untangling. Anchor a catch on the fish itself (in hand, in the net, held up).

## 2. Cuts and assembly

- **`silencedetect` at -30 dB misses quiet word tails.** Out-points 0.05–0.15 s after an
  island end chopped consonants across an entire edit. Run `check_cuts.py` on every
  segment list, after every recut.
- **`check_cuts.py` finishes the word, not the thought.** Read the transcript around each
  moved cut; REVIEW extensions may be wind or reel noise, or the start of the next line.
- **`ffmpeg -f concat -c copy` of segments with their own AAC drifts.** Encoder priming and
  padding leave a few ms at every cut; QuickTime/browsers play samples back to back, so 95
  cuts drifted ~1 s. ffmpeg `-ss` spot checks look perfect because they honor timestamps.
  Assemble with `concat_av.py` and gate on `check_av_sync.py`.
- **Post-assembly audio work must not re-cut video.** Bleeps, wind filtering and voice
  swaps run on the assembled file with `-c:v copy`.
- **GoPro chapter splits are gapless.** A catch can straddle `GX01…` → `GX02…`; cut it as
  two segments, keep the crop x within ~50 px across the join, and look in the next file
  for the release line.
- **Crop options must all be named.** `crop=w=608:h=1080:x='EXPR':y=0`. Mixing a named
  `x='…'` with a positional `:0` fails with `No option name near '0'`.

## 3. Framing and fish centering

- **Positions read off montage tiles are wrong.** 400+ px misreads happened at 300 px
  tiles, and conflicting reads at 960 px. Read anchor **boxes** on big single gridded
  frames.
- **Tracker confidence lies.** A single-init tracker latched onto water ripples with high
  confidence. Only a box-on-fish visual check counts. Fix anchors, never patch the crop
  with blind offsets.
- **Every shortcut has been rejected.** Eyeballed crops, one fixed crop for a hold-up,
  "pivot" crops at the center of the angler's rocking (fish half off-screen 40% of the
  time), and single-init tracking all shipped off-center fish. Use keyframe-anchored
  bidirectional tracking (`fishtrack2.py`) and follow the fish everywhere it is visible.
- **The verification step is the one that gets skipped.** Having the rule in context was
  not enough; a static crop shipped anyway. Produce the 0.5 s, ≥300 px, center-lined output
  sheets and look at every tile before delivery. When briefing a sub-agent, require the
  sheets as deliverables, not a claim that it checked.
- **Small verify tiles hide failures.** 180 px tiles passed clips that were plainly
  off-center on a phone.
- **Head over tail.** A close hold-up is wider than the 608 px (1080p) window; a
  body-centered crop clipped the head. Bias toward the head; let the tail clip.
- **Don't track the head directly.** A hand-sized template over water latches onto ripples
  instantly. Track the body, add a head-side bias.
- **Every catch and every beat sits somewhere different.** Never reuse a crop x across
  catches; measure.
- **Topwater rings drift.** As the kayak rotates, the ring system moves; a position read
  one second after the eruption put the strike entirely outside the window. Measure x on
  the first frame the water breaks.
- **Landscape punch-ins on animals need dense tracking.** Sparse 1.5–3 s readings pointed a
  punch-in at shadows and wake sparkle. Sample every 0.25 s, ID the animal by texture and
  motion across frames, prefer a fixed window, and require the animal visible in nearly
  every frame of the encoded zoom.
- **Chest/low mounts put close animals at the frame's bottom edge**, beside the hull — not
  mid-frame.

## 4. Captions and on-screen text

- **drawtext does not wrap.** At size 62 Arial Bold, more than ~26 characters runs off the
  1080 px frame. Split long lines into consecutive **verbatim** chunks — never paraphrase
  to make them fit.
- **Sub-word tokens split words on screen** ("Sen" + "ko", "he" + "'s"). `burn_captions.py`
  merges tokens; don't hand-roll whisper word captions.
- **One whisper pass over a whole clip drifts seconds** by the end. Time per segment, or
  use `manual_chunks` from speech islands.
- **`build_edit.py` segments are video-only**, so whisper-timed captions have nothing to
  transcribe. Use `manual_chunks`.
- **A bleep tone wrecks word alignment** (one word stretched over 2 s). Time captions on the
  clean pre-bleep audio; burn captions last.
- **Bracketed tags leak** ("[wind howling]", "(beep)"). Check the printed chunk list.
- **Burned-caption QA is visual.** Render frames at several chunk midpoints and look: overflow,
  split words, two captions at once, text over the centered fish, text in TikTok's bottom
  484 px or right-hand rail.
- **zsh mangles `$FONT:text=`.** `:t` is a zsh path modifier; write `${FONT}` inside filter
  strings.

## 5. Audio: bleeps, wind, music

- **ffmpeg's `sine` is fixed at 1/8 amplitude** (≈ −18 dBFS). At `volume=0.3` the bleep was
  inaudible; use `volume=2.0`.
- **Whisper-placed bleeps miss.** One landed 0.28 s early, on the silence before the word,
  and the curse played in full. Measure boundaries on the envelope.
- **Fricative onsets are quiet.** "sh-", "f-" start 0.1–0.2 s before the loud vowel; a mute
  started at the burst leaks the "sh". Use 10 ms windows and the high band.
- **Measure on the file you will modify.** A `loudnorm` upstream shifted timing ~60 ms.
- **Wind lives below ~200 Hz.** Two 250 Hz high-passes + RNNoise at mix 0.75 won a blind A/B
  over the raw track. `afftdn` alone is too mild; RNNoise at 1.0 with a 300 Hz high-pass
  removed the voice; stacking RNNoise + `afftdn` cost 9 dB of speech.
- **`music_audit.py` sus-only flags on calm days are false positives.** Chunks with
  `sus ≥ 0.6` and an empty/`[BLANK_AUDIO]` tag read ≤ 0.04 on the AST classifier. The AST
  check decides; a lone 0.12–0.14 window during loud speech is not music.
- **The voice stem keeps sung vocals.** When a song sits right under the speech at > 0.3,
  drop the line instead.
- **Edge voice-swap ranges on cut frames**, so the change in audio texture hides in a hard
  cut.

## 6. Wildlife

- **False "birds" to reject on sight:** a lure dangling from the rod tip (an upright figure
  whose skirt reads as legs, swinging across the far bank — check the frame for the line
  running into it); detector sky hits at the same frame position on every sample (a lens
  speck or flare); leaves and debris on the water at low confidence.
- **The animal is usually in frame before the angler notices it.** Search −120 s to +120 s
  around the first cue line, on the stretches where the camera faces the right shore/sky.
- **A detector miss means look harder.** COCO "bird" and open-vocabulary prompts both miss a
  15–25 px swimming head or a heron standing in reeds. The motion finder is sky-only by
  default; turn the sky mask off for anything on the water. Ask the angler where it was
  before burning more passes.
- **Heard ≠ on camera.** A bird called out three times was on screen once, for
  0.4 s. Report what was searched, never just "not in frame".
- **Zoom as far as it goes.** A conservative 600 px crop shipped a bird as a 12 px speck.
  Default to the animal filling ~1/4–1/3 of the frame width (crops down to 48 px of 4K);
  a pixelated big bird beats a clean speck. Sky silhouettes hold up best, treelines worst.
- **Dusk sightings are rarely usable**, and **keep the footage until the clips are signed
  off** — a deleted folder ended a re-search.
- **4K needs piping.** A raw 4K frame is ~25 MB; never write frame sequences to disk.

## 7. Shell, Python and machine

- **zsh doesn't word-split `$VAR`.** `ffmpeg $FLAGS` passes one argument. Use arrays or
  write the flags out.
- **zsh aborts on an empty glob** (`rm dir/*.jpg` with no matches). Use
  `rm -rf dir && mkdir -p dir`.
- **macOS bash is 3.2: no `declare -A`.** The assignment silently becomes an indexed array,
  every lookup returns the last value, and a frame scan truncated every clip at the same
  time. Use `case`, and print per-clip frame counts so truncation is visible.
- **`ffmpeg -pattern_type glob` has no `[0-5]` ranges.** Copy the wanted frames to a temp
  dir and glob `*.jpg`.
- **The `fps` filter mislabels sheets.** `fps=1/10` picks a frame up to 5 s from its label;
  sample with `select='isnan(prev_selected_t)+gte(t-prev_selected_t,10)'`.
- **Never name a Python file after a stdlib module** (`ast.py`, `wave.py`, `select.py`,
  `json.py`, `tokenize.py` …). `ast.py` broke `import torch` with a circular import.
- **Don't fan out whisper jobs.** 22 concurrent small.en runs beside a 4K detection job
  crashed a 16 GB Mac. Run them one at a time (`-t 4`); don't overlap heavy 4K
  renders with detector passes.
- **`/tmp` scratch doesn't survive a reboot.** That crash wiped every intermediate. Copy
  finished deliverables and their decision files (edit JSONs, keyframes, caption JSON,
  verify sheets) to `<output_dir>/proof/` as you go.
- **Finished videos exceed chat upload limits.** Give the output path; don't re-encode a
  smaller copy to fit.

## 8. Editorial traps

- **Lines addressed to the assistant aren't content.** Anglers who know an AI assistant
  edits the footage talk to it on camera ("remind me…", "zoom in on that", "test of the 4K", shopping
  lists, plans). Grep for them before every cut list and drop the whole sentence; route the
  content into notes. If a reaction line runs into a note-to-assistant line, drop both.
- **Short-form features are short.** Applying the "keep all the reeling" rule to a 28 s
  fight produced a 1:31 feature that was rejected on sight. Portrait features land in
  30–60 s; a long fight becomes two beats with one hard cut over the silent middle.
- **The paddle audit needs ≥320 px tiles.** A 250 px pass read clean; the 320 px pass found
  nine paddling violations including 48 s of continuous paddling. Audit the assembled cut
  at 1 fps, 48 tiles per sheet. Colour-based paddle detection flagged sunlit lily pads and
  missed the real paddle.
- **Budget for the recut.** After a paddle/fiddling recut, re-check every boundary — 7 of 44
  boundaries clipped a word on the first pass.
- **No other people, no private phone/assistant audio, no catch-logging on the phone** in
  any edit (see [editing-rules.md](editing-rules.md)).
