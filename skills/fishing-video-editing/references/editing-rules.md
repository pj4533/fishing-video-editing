# Editing rules

How fishing edits are cut. These are standing defaults: apply them for the chosen mode unless
the angler says otherwise. Each rule carries the reason it exists. Most came from an edit that
was sent back, so the "why" tells you what failure to watch for.

Craft layers sit on top of these rules, and **this file wins on any conflict**:
[youtube-longform.md](youtube-longform.md) (long-form landscape),
[portrait-shortform.md](portrait-shortform.md) (portrait features),
[tiktok-longform.md](tiktok-longform.md) (full-trip recap),
[wildlife-zoom.md](wildlife-zoom.md) (wildlife clips),
[thumbnails-titles.md](thumbnails-titles.md) (packaging). Exact commands are in
[cookbook.md](cookbook.md). The process is in [workflow.md](workflow.md).

## Contents
1. [Picking the mode](#1-picking-the-mode)
2. [Non-negotiables (every mode)](#2-non-negotiables-every-mode)
3. [Shared content rules (every mode)](#3-shared-content-rules-every-mode)
4. [The catch arc and its verification](#4-the-catch-arc-and-its-verification)
5. [Mode A: long-form landscape (YouTube)](#5-mode-a-long-form-landscape-youtube)
6. [Mode B: portrait features (one per catch)](#6-mode-b-portrait-features-one-per-catch)
7. [Mode R: long-form TikTok recap](#7-mode-r-long-form-tiktok-recap)
8. [Mode D: talk / monologue clips](#8-mode-d-talk--monologue-clips)
9. [Mode W: wildlife zoom clips](#9-mode-w-wildlife-zoom-clips)
10. [Mistakes already made](#10-mistakes-already-made)

---

## 1. Picking the mode

| The angler asks for... | Mode | Output |
|---|---|---|
| "the YouTube edit", "edit it together" | **A** | one landscape 16:9 file: intro → every catch in order → outro |
| "highlights", "shorts", "a TikTok of each fish", "features" | **B** | one portrait 9:16 file per catch, 30–60 s |
| "the full-trip TikTok", "a recap" | **R** | one portrait 9:16 file, roughly 3–6 min, all catches plus bridges |
| "the talk clip", a recurring on-camera monologue series | **D** | one portrait clip per topic section |
| "zoom in on the eagle", "wildlife clips" | **W** | one portrait clip per sighting, from 4K source |

Several modes often come from the same footage (A + B + R on a good day, plus D or W when the
transcript shows a monologue or a sighting). Check every trip's transcripts for monologue
sections and animal call-outs even when nobody asked. The angler can't ask for a clip they
forgot they filmed.

---

## 2. Non-negotiables (every mode)

These six rules hold in every mode. Each was learned from a shipped edit that had to be redone.

### 2.1 Hard cuts only
No fades to or from black. No crossfades, dissolves, `xfade`, `acrossfade`, `fade` or `afade`.
*Why:* the first long-form edit used crossfades and was rejected outright. A POV fishing video
reads as honest and immediate, and dissolves make it feel like a slideshow.

### 2.2 Cut only after a finished sentence, in real silence, never inside a word
- An out-point lands after the speaker finishes a sentence or thought. An in-point lands before
  the first word starts. You may drop a whole line, but never chop one.
- **Verify every segment list with `scripts/check_cuts.py` before encoding**, in every mode. It
  runs webrtcvad voice detection on the source audio. It flags any out-point with speech in its
  last 0.30 s and any in-point with speech in its first 0.15 s. `--fix` proposes a corrected
  list (out = 0.35 s after the speech run ends, in = 0.25 s before it starts). Re-run it on the
  fixed list and ship only at zero chops. A cut at a file's very start is fine.
- The checker finishes the *word*. You still have to finish the *thought*. A cut may only land
  at a sentence end or a real pause (≥ ~0.25 s). If the only gap after a clause is a 40–60 ms
  breath before "and..." or "so...", either run on to the end of the whole thought or cut back at
  the previous full stop. Never end a segment on a dangling "and".
- Extensions marked REVIEW (> 1.5 s), or in-points it wants to move far back, are often wind,
  reel or footstep noise read as voice. Transcribe that small window and look at a 20 ms speech
  strip before accepting. Audit any seconds an extension adds against the content rules (§3).
- Trailing tag phrases are part of the line. In "...I made it, I made it. **No problem.**" the
  tag came 1.3 s after the apparent end and the first cut chopped it.

*Why:* a long-form edit once shipped with the ends of words clipped at dozens of cuts. The
out-points sat 0.05–0.15 s after a `silencedetect` island end, which misses quiet word tails. The
boundary check re-transcribed each segment with whisper, and **whisper fills in a clipped word
from context**: a chopped "fis-" still prints "fish", so every chop passed. Voice detection on the
raw audio can't be fooled that way.

### 2.3 Audio is cut with the video: same frame, no J/L cuts, no overlaps
Every cut is a hard cut in picture and sound on the same frame. Assemble with
**`scripts/concat_av.py`** (or `scripts/build_edit.py`, which calls it), and verify every
delivered file with **`scripts/check_av_sync.py`**. Ship only at zero out-of-sync probes. Re-run
it after captions, bleeps, wind filtering or voice isolation, because anything that re-muxes can
shift a track start.

*Why:* never `ffmpeg -f concat ... -c copy` segments that each carry their own AAC audio. Each
AAC stream has encoder priming and ends a few ms off its video, so every join leaves a tiny gap
or overlap. ffmpeg honours the timestamps, so `ffmpeg -ss` spot checks look perfect. QuickTime
and browsers play the samples back to back, though, and the error piles up: an edit with ~95
cuts drifted ~1 s out of sync by 18 minutes. `concat_av.py` stream-copies the video and rebuilds
the whole soundtrack once from the source, sample-exact to each segment's frame count.
`check_av_sync.py` plays the audio the way a real player does, so it catches what ffmpeg hides.

### 2.4 Nothing the angler says to the editor or AI goes in an edit
Anglers who know an AI or editor will process the footage talk to it on camera. Examples: "remind
me to...", "see if you can zoom in on that", "test of the 4K", "use this as the outro", "check all
the frames", "we'll retie next time", a shopping list, anything about "the plan" or the notes, or
a nickname for the assistant. Those lines are **notes for you**. Act on them, but they never
appear in any mode's output.
- Before building any cut list, grep every transcript for the assistant's name or nickname plus
  `remind me|footage|zoom|4k|outro|intro|shopping list|the plan|note to|edit this|cut this`.
  Exclude every hit and its whole sentence.
- Talk the angler aims at themselves or the viewer ("my plan is to work this weed line") is
  content. Talk aimed *at the editor* is not.

*Why:* these lines break the fourth wall for viewers who don't know an AI is involved, and they
read as the angler narrating to an unseen person. "We'll use that as the outro" once sat right
inside the outro window.

### 2.5 Keep the original source audio
No added music, EQ or normalisation. Ambient sound, reel noise and splashes are the atmosphere.
Exceptions, each with its own rule:
- **Wind:** on a windy trip, also make a wind-filtered copy (cookbook: two high-pass 250 Hz
  stages + RNNoise at mix 0.75, video copied). Keep the untouched cut beside it as
  `...__original_audio.mp4` and let the angler pick. In one A/B test the filtered version won for
  portrait features. Re-verify bleeps and sync after filtering.
- **Someone else's music** (a PA across the water, a boat stereo) is a copyright-flag risk on
  YouTube and TikTok. Keep it out. Audit every finished file with `scripts/music_audit.py` and the
  AudioSet music check ([cookbook.md](cookbook.md)). Where music leaks under the angler's voice,
  drop the line (preferred when music sits right under the words) or swap in the demucs voice
  stem for just that range with `scripts/voice_isolate.py`, with range edges on cut frames.
  Never ship a segment that scores as music. A sus-only `music_audit` flag with an empty or
  `[BLANK_AUDIO]` tag is a false positive on calm days, so the AST check decides.
- **Bleeps** in short-form modes (§2.6).

### 2.6 Bleep curses on short-form platforms only
- **Modes B, R, D and W bleep. Mode A (YouTube long-form) doesn't bleep or cut cursing** unless
  the angler asks for it.
- Bleep surgically with a 1 kHz tone at speech loudness, over only the curse syllable, so the
  words around it stay audible ("Let's ⟨bleep⟩ing go"). Never just cut the line, because the
  bleep is part of the fun.
- The default scope is f-words and sh-words. Mild words ("freaking", "damn", "holy crap") stay,
  unless the angler asks for stricter.
- Boundaries come from the **10 ms low-band/high-band energy envelope**, not whisper word times. Whisper `-ml 1` was
  ~130–280 ms off in calm audio and **seconds** off over splashing, and the first bleep ever made
  ate the word before the curse. Verify on the finished clip: the words on either side are still
  intact, and the tone covers the whole syllable. Burn captions *after* bleeping, and censor the
  caption text too (`f***ing`). Recipe in [cookbook.md](cookbook.md).

---

## 3. Shared content rules (every mode)

- **No other people or other boats, ever.** People on shore, swimmers, passing boats: none of it
  goes in. You don't have their permission. Check every selected segment's frames, and don't
  just trust the transcript. Lines *about* other people ("look at all these swimmers, that's
  dangerous") also go.
- **No private phone or assistant audio.** Voice-assistant interactions, messages read aloud,
  and family texts are personal. Cut around them.
- **No hand-held phone use.** Many anglers log the catch on their phone right after the release,
  heads-down with both hands, sometimes typing a passcode on camera. End the catch segment in the
  silence *before* the reach for the pocket (usually 1–3 s after the post-release line). Any line
  spoken while the phone is in hand is lost. Frame-scan the seconds after every catch end for the
  two-hands-on-phone posture. A phone or fish-finder *mounted* on the boat and showing passively
  in frame is fine.
- **Cut bodily noises:** burps, sniffs, snorts, throat-clears. Scan each kept segment's audio
  with small.en for tags like `[sniff]`, `(sniffling)` or `[burp]` and move the boundary to a
  silence. Never break a continuous catch take or chop speech to remove one, because the full
  arc wins.
- **No maintenance or body-maintenance shots:** tying on, re-rigging, untangling, picking weeds
  off the lure, inspecting the lure, hands at the lens, drinking, eating, stretching, adjusting
  clothes, hat or camera, and fiddling with the scale or net. Nobody watches for these.
  The only exception is when the angler says something over it that the edit needs. Then keep
  the minimum speech window. Hands-on-lure frames fail the full-window audit (§5).
- **No paddling, rowing, trolling-motor fiddling or walking the bank to the next spot** on screen
  unless a necessary line is spoken over it (an outro line, a load-bearing story line). Then
  keep the minimum speech window and record the exception in EDIT_NOTES. *Why:* an edit was
  rejected half-way through for paddling shots that slipped through 3–5 s spot checks between
  samples.
- **Set up the callbacks.** When a catch is followed by "so much for my theory", include the
  earlier line where the angler states that theory ("fish never come here, probably a waste").
  The failed prediction and its payoff *is* the story. More pre-catch talk is welcome when it
  seeds a payoff.
- **Wildlife must be visible to stay.** If the animal the angler is talking about isn't
  identifiable in the frame (zoom in and check), leave the moment out. A heron that is a speck,
  or a turtle you can't see, is talk about nothing.
- **Equipment-failure cards.** If the camera dies mid-catch (battery, card full), bridge the gap
  with a deadpan full-screen card: a black background, big white text stating what the viewer
  missed ("SMALL FISH HELD UP HERE"), and a small reason line ("(camera battery ran out)"). Keep
  it ~4 s, silent, with hard cuts on both sides. If the angler gives a setup line right before the
  doomed catch, keep it in front of the card.
- **Timestamps:** never trust whisper timestamps for a boundary. Block times drift 3+ s inside a
  clip, and ~14 s on quiet footage. Use speech islands (`silencedetect`, or
  `scripts/speech_islands.py`) for line edges, `check_cuts.py` for verification, and the
  low/high-band energy envelope (cookbook §16) for syllables.

---

## 4. The catch arc and its verification

A catch is more than the hold-up. It starts before the bite. Every mode that shows a catch
builds it forward from the bite:

1. the cast and/or the retrieve (rod working, line slack or steady)
2. the bite, hookset and rod load
3. the fight and reeling in
4. the landing (net, lip or swing aboard)
5. the hold-up (show the fish)
6. the weigh, if one happens (Mode A keeps a short version; features usually cut it)
7. **the release.** Let the fish go and watch it swim away. **Never cut before the release.**
8. the post-release line ("thank you", "thanks, buddy", "see you later"). End right after it,
   before the phone comes out.

### 4.1 Arc-presence verification (every catch, every mode)
**A catch segment does not ship until you can point to a frame for each stage:** retrieve, rod
loaded, **the fish itself** (on the line, in the net or out of the water), the fish in hand, and
the release. Log each verified timestamp in EDIT_NOTES. If any stage has no frame, the segment is
wrong. Go find the real arc.
- **Never anchor a catch on a "hands down at the lap" frame.** That posture looks the same for
  unhooking, re-rigging, weed-picking and gear fiddling. Anchor only on a loaded rod, a visible
  fish or a deployed net.
- *Why:* on a day with silent catches (no bite reaction, no hold-up talk, no thank-you), a
  post-release lure-cleaning cluster was taken for the catch. The "catch" segment and its feature
  contained no fish at all. The real bite was ~2 minutes earlier. Boundary checks and centering
  checks both pass silently on a fishless segment. Only a presence check catches it.

### 4.2 Gap verification (the seconds between stages)
Arc presence proves each stage exists. It doesn't prove the seconds *between* stages are clean.
Densely sample every second between consecutive stages. If a stretch shows no rod load, no
visible fish and no meaningful hands-on decision, only reaching, fiddling or empty water, hard-cut
from the end of one real stage to the start of the next. A hard cut beats dead air, even inside
an otherwise continuous take. **Landing → hold-up is the highest-risk gap** (unhooking, scale
rigging, net stowing). Reeling → landing is second.
*Why:* a catch shipped with ~40 s of dead water and scale-fumbling between the fight and the
hold-up. Every stage was present and timestamped, so presence verification passed.

### 4.3 The reaction line is not the bite
On a small fish, the first words often come *as* it's swung out ("what kind of fish are you?"),
and the reeling happened silently before them. Start from frames, not words: step back from the
first visible fish in ≤ 2 s steps until the line is slack or the retrieve is steady, and start
there. *Why:* a feature was rejected because it "starts with me pulling the fish out of the
water". It was cut from the reaction line.

---

## 5. Mode A: long-form landscape (YouTube)

- **Format:** landscape 16:9 at the source aspect, 1920×1080 output (from 1080p or 4K source).
  One continuous file.
- **Structure:** intro → each catch, chronological, full arc → outro.
- **Vibe:** by default, a **calm, relaxing hang**: quiet water, casting, unhurried narration, with
  catches inside that calm. It isn't an adrenaline reel. Let scenery breathe. Light
  self-deprecating humor (stuck in a tree, a bad cast) is welcome in small doses. If a funny bit
  doesn't clearly land, leave it out. Confirm the vibe with the angler on a first edit.
- **Target length** comes from the angler (one channel's standing target was ~20 min). When the
  catches don't fill it, **pad only with action and scenery**:
  - quick-cut casts, retrieves, blow-ups and missed strikes, big splashes
  - wildlife that is visible on camera
  - scenic water, pads, reeds and sky
  - travel story beats where no paddling shows
  Never pad with rambling, fiddling or dead time. A rule of thumb: *if the rod is loaded, the lure
  is flying or the water is doing something, it's filler. If the angler is looking down at their
  hands, it isn't.* Never stretch the intro or outro to pad.
- **Don't linger on non-action shots of the angler.** Inside catch arcs too, trim fixing, looking
  down and scale fiddling hard. A few seconds is the most it gets, and only when it's
  story-relevant (putting on the lure that pays off a callback).
- **Casting montages are CAST, CAST, CAST.** Back-to-back shots of only the cast: wind-up or whip,
  lure flying, splashdown, ~2–4 s each, hard-cut into the next cast. No retrieve, waiting or
  drifting inside a montage. A 10–15 s window "with a cast in it somewhere" isn't a casting shot.
  Trim to the cast. *Why:* this was sent back twice before the definition stuck.
- **Action beats are tight: action → reaction line → cut.** Around blow-ups, strikes and misses,
  keep the lead-in, the moment and the reaction line. Then jump straight to the next spoken line,
  dropping the aftermath (re-collecting the lure, line behind the angler, untangling, silent
  scanning). Inside multi-line postmortems, jump-cut silence-to-silence between line clusters.
  *Why:* one edit sat ~30 s on getting a frog back after a missed hookset when it should have cut
  straight to "big swing and a miss, it happens."
- **Intro:** start on the first spoken word of the greeting or place intro, with dead air cut.
  End on a clean phrase. Cut the tackle-talk filler after it.
- **Outro:** the wrap-up line ("...caught three, see you next time") and nothing else. Cut
  wishy-washy deliberation ("should I go back in?", "might be about that time...") from both ends.
- **Catches:** the full arc (§4), mostly continuous footage. Show the retrieve and the reeling.
  More build-up means more excitement, so don't start at the fish already coming out. A topwater
  blow-up gets a long reel-in build. Gap verification still applies.
- **Full-window 1 fps audit:** every filler or b-roll window, and the whole assembled cut, is
  checked at **1 fps across its entire length** on tiles large enough to see a paddle blade
  (≈ 320 px wide, 6 columns, ~48 per sheet). A paddle in hand, hands on the lure, a drink or
  another person in any frame disqualifies the window. *Why:* 3–5 s strip checks and 250 px tiles
  both let paddle strokes through.
- **Monologue sections (Mode D material):** leave them out of Mode A by default. They aren't part
  of any catch arc. Ask if unsure.
- **Cursing stays untouched** in Mode A unless the angler asks otherwise.
- Packaging (thumbnail + titles) for every Mode A delivery:
  [thumbnails-titles.md](thumbnails-titles.md). Pacing and retention craft:
  [youtube-longform.md](youtube-longform.md).

---

## 6. Mode B: portrait features (one per catch)

One separate file per catch. These are tight, but tight comes from removing the boring middle,
not from chopping the action into snippets.

- **Format:** portrait 9:16, 1080×1920. The crop window is 608×1080 of a 1080p frame or
  1215×2160 of a 4K frame (4K gives a sharp crop). Build with `scripts/build_edit.py` in portrait
  mode.
- **Content = the catch only.** No intro, no outro, no fishing padding.
- **Length: 30–60 s.** ~30 s is the ideal, and up to ~60 s is fine when the commentary earns it.
  *Why:* a 1:31 feature that played a long fight whole was rejected on sight ("the features
  should be short").

### 6.1 The shape: the catch, then the fish (2–4 continuous shots)
**Shot 1, the catch (continuous):**
1. Start **≤ 1 s before the rod loads**, found on frames, not the reaction line (§4.3). No 10 s of
   casting or waiting first.
2. **The reeling**, unbroken, through the fight until the fish comes out of the water or into
   the boat. On a short fight (a few seconds), play it all. On a long one (≳ 10–15 s), compress to
   **two beats**: the bite and rod load, then the fish coming up and aboard, ~5–10 s each, with
   one hard cut over the silent middle. It must still read as a fight. When told "too tight",
   restore more *reeling* specifically, not more of everything.
3. End as the fish comes aboard, or after the line the angler says as they look at it. If a
   swing-up drops back into the water, keep the reeling after it. Don't jump from the drop to the
   net.

**The cut(s).** This is where the boring stuff dies: net time (including the fish dangling
over the net), unhooking, scale rigging, and fumbling with rod, net or gear. **All of it goes.**
Weighing isn't needed in a feature unless the number is the payoff line.

**Shot 2, the fish (continuous):**
4. **The hold-up plus all the angler's commentary about the fish**: size, wounds, recognition ("I
   swear I've caught him before"), the weight guess. This narration is the heart of the clip, so
   never cut it.
5. It flows straight into **the release** in the same take, with no cut between holding and
   releasing. Pan to follow the fish down, so the let-go and swim-away are visible and centered.
6. End right after the post-release line.

The simplest feature is two shots with one cut. Most real features need two or three cuts: fight → first hold-up and
reaction lines → (cut the unhooking and scale rigging) → the scale reading, the final hold-up and the release. That's
fine as long as every kept segment is continuous inside, every cut removes dead handling rather than a line, and the
hold-up flows into the release without a cut.

### 6.2 Framing: the fish is centered, and the head beats the tail
- **The action is centered in the portrait frame at all times**: the pull-out, the hold-up and
  the release especially. Fish drift during a hold (one measured hold drifted 350 source px),
  and releases travel far, so a fixed crop never works.
- **Use the fish tracker** (`scripts/fishtrack2.py`, keyframe-anchored bidirectional tracking)
  to drive the crop. Never eyeball crops, use single-init tracks or "pivot" crops. All of those
  shipped off-center fish and were rejected three times. Read anchor boxes off big gridded
  single frames (`scripts/keyframe_grid.sh`), never off montage tiles. Procedure:
  [cookbook.md](cookbook.md) (fish-centering section).
- **If the whole fish won't fit, frame the head, not the tail.** A close hold-up can be wider than
  the crop. The tracker centers the body, so add a head-side `bias`. The head and grip must never
  be cut off by an edge. A clipped tail is acceptable.
- **Hold the crop steady on sustained poses.** Tracking every jitter makes the hold-up "swim",
  and that was rejected. Smooth the track, hold on each pose, and make one deliberate move between
  poses. Keep crop-x continuous across a chapter join inside one take.
- **Verify on the output:** every 0.5 s across all fish-visible time, on ≥ 300 px tiles. Check
  **presence before centering**: a sheet with no fish is an automatic fail, not a pass. 180 px
  tiles hid every failure the angler later caught.
- Topwater blow-ups: find the eruption visually at 4 fps and measure x at that instant. The
  loudest audio spike can sit ~1 s late, and the rings drift as the boat turns, so a crop built
  from them once missed the strike completely.

### 6.3 Text
Bleep curses (§2.6). Hooks, captions and safe zones are in
[portrait-shortform.md](portrait-shortform.md). Captions come from speech-island timing
(`scripts/burn_captions.py` with `manual_chunks`), never from one whisper pass over the whole
video.

---

## 7. Mode R: long-form TikTok recap

One portrait 9:16 file covering the whole trip: every catch plus short bridges. It's often 3–6
min. Craft rules (event density, flash-forward, bridges, `CATCH n/N` cards, map inserts) are in
[tiktok-longform.md](tiktok-longform.md). The editing rules:

- **Each catch is its finished Mode B feature**, reused whole or close to it. The same
  centering, cuts and bleeps apply. Build the features first and the recap from them.
- **Bridges are real lines from the day**: plans, misses, setbacks, stakes ("if I get one more,
  it's my best day here"). Every one gets the full sentence rule (§2.2). No meta-talk (§2.4), no
  other people, no paddling unless the line is necessary (log the exception).
- **Close order:** release → thank-you → tally card → the angler's own sign-off → stop.
- If the angler points at catches in the sign-off ("this one... and this one"), hard-cut a
  full-frame still card of each catch onto the exact word, timed from speech islands.
- Bleep (§2.6). Run the music audit (§2.5) on the recap separately, because it pulls lines from
  more of the day than the features do.

---

## 8. Mode D: talk / monologue clips

Some anglers run a recurring on-camera series, a topic talked through while fishing. Each topic
section becomes its own portrait clip. The monologue is the content, and the fishing is the
backdrop.

- **Format:** portrait 9:16, same crop pipeline as Mode B. Frame the **bow, rod and hands** (the
  chest-mount anchor). A **fixed crop** is usually right: measure a few grid frames across the
  section and pick one x. Pan only if the composition really shifts.
- **Content = the whole section, nothing else.** Start at the first word that opens the topic
  (sections are usually announced: "another topic for the series...") with ~0.5 s of pre-roll.
  End right after the closer (often a question to viewers, like "what do you think?") with
  ~0.5–1 s of tail. Leave out the fishing talk on either side.
- **Never drop or chop a line.** One continuous take is the default.
- **Silence trimming is optional.** 1–3 s thinking pauses while casting are natural pacing, so
  leave them. Jump-cut only genuinely long silences (> ~4 s), silence-to-silence.
- **Length** is whatever the section runs (2–3+ min is normal). It comes from the delivery, not
  the edit.
- Bleep curses. Bodily-noise rule applies.
- **Finding them:** grep every clip's transcript for the series name, topic vocabulary and the
  closer phrase. They can appear on any trip, including catch days. Pin the edges with speech
  islands, because whisper blocks drifted ~14 s on the quiet footage where these first appeared.

---

## 9. Mode W: wildlife zoom clips

One portrait 9:16 clip per sighting, **cropped from 4K source**. Full process, numbers and traps:
[wildlife-zoom.md](wildlife-zoom.md).

- **Zoom as far as possible, by default. Don't ask.** Size the crop so the animal fills about
  **a quarter to a third of the frame width**: crop width ≈ 3–4× the animal's box width, down to a
  **48 px floor**. Pixelation is accepted, because extreme zoom was the reason to shoot 4K. A hard
  punch-in from the wide POV at the moment the animal becomes identifiable is fine. A
  "standard" wide crop is not the main clip. *Why:* the angler's standing instruction after
  reviewing labelled zoom variants was "as much of a zoom as possible... so you don't have to
  ask." The background sets the practical ceiling: a silhouette on clean sky holds up far past
  where an animal against a treeline turns to watercolour.
- **Centered by a verified per-frame track** (`wildlife_scan.py` / `wildlife_motion.py` finders →
  `wildlife_track.py`, or `wildlife_speck.py` / `wildlife_flock.py` for tiny birds and flocks →
  `wildlife_reframe.py --verify`). Eyeballed crops are rejected here exactly as in Mode B. The
  tighter the crop, the denser the track (anchors every ~0.15 s through a head whip).
- **Shape:** one continuous take, hard cuts. Start ~0.3–0.5 s before the animal is first
  identifiable (or before the first word about it). End after the last finished sentence about it
  or when it leaves frame, whichever is later. 7–15 s for a one-beat sighting, up to ~35 s for
  perched → take-off → flight. No fishing padding.
- **Search around the cue:** the animal was often in frame before the angler noticed. Run the
  finders roughly 120 s either side of the transcript cue, not just forward from it.
- **Audio:** keep the live reaction, because it drives shares. Exclude everything said to the
  editor ("zoom in on that", "test of the 4K"). Bleep curses ("holy crap" is not one).
- **Text:** a frame-one hook of 4–8 words in the top third, gone before the action beat.
  Verbatim captions are timed from speech islands, since whisper word times are unreliable on
  1 s lines in a quiet clip. Verify on rendered frames.
- **When it's a speck, say so.** A 12–14 px bird on a wide lens is the honest limit. Deliver the
  best zoom, and flag it in EDIT_NOTES instead of over-promising.

---

## 10. Mistakes already made

Each of these shipped once. Check for them before delivering.

| Mistake | Rule that prevents it |
|---|---|
| Crossfades on a long-form edit | §2.1 hard cuts |
| Word endings clipped at dozens of cuts; whisper re-check said "fine" | §2.2 `check_cuts.py` |
| ~1 s A/V drift by 18 min in QuickTime from `concat -c copy` of per-segment AAC | §2.3 `concat_av.py` + `check_av_sync.py` |
| "Use that as the outro" / "zoom in on that" left in a cut | §2.4 meta-talk grep |
| A feature that opened at the net, skipping the reeling | §4.3, §6.1 start on the rod load |
| 12 s of dead time before the bite | §6.1 ≤ 1 s lead |
| Reeling cut to 1 s | §6.1 two beats, not a snippet |
| Seconds of fish sitting in the net | §6.1 the single cut |
| Hold-up commentary (size, wound, "caught him before") cut | §6.1 the heart of the clip |
| A cut between hold-up and release | §6.1 one take |
| Fixed or eyeballed crops; the fish drifted off-center | §6.2 tracker + output verify |
| Body-centered crop clipped the head | §6.2 head bias |
| A "catch" with no fish in it (lure cleaning taken for a catch) | §4.1 presence check |
| ~40 s of scale fumbling inside a catch | §4.2 gap check |
| Paddling, a drink of water, a 30 s blow-up aftermath | §3, §5 1 fps full-window audit |
| A "casting montage" full of retrieves | §5 CAST-only |
| A 1:31 feature | §6 30–60 s |
| The first bleep ate the word before the curse | §2.6 envelope boundaries |
| A blow-up outside the portrait crop (measured off drifting rings) | §6.2 measure at the eruption |
