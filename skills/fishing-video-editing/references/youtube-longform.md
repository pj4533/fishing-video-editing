# YouTube long-form edit (landscape 16:9)

One continuous landscape video of the whole trip: **intro → every catch in chronological
order, each with its full arc → outro.** This file covers the shape of the edit and the
retention craft that sits on top of it. The cross-mode hard rules (hard cuts only, cuts in
silence after a finished sentence, audio cut with the video, no other people, nothing said
to the editor) live in [editing-rules.md](editing-rules.md) and always win over anything
here. Exact commands are in [cookbook.md](cookbook.md); the step-by-step process (find
footage, transcribe, locate catches) is in [workflow.md](workflow.md). Packaging is in
[thumbnails-titles.md](thumbnails-titles.md).

Items marked **EXPERIMENT** are promising but change the basic shape. Try one at a time,
flag it in `EDIT_NOTES.md`, and ask the angler before it becomes standard. Everything else
is default practice.

## Contents

1. [Format and skeleton](#1-format-and-skeleton)
2. [The catch arc](#2-the-catch-arc)
3. [Vibe: calm and relaxing](#3-vibe-calm-and-relaxing)
4. [Length, filler and "no lingering"](#4-length-filler-and-no-lingering)
5. [Zero paddling, no maintenance, cast-only montages](#5-zero-paddling-no-maintenance-cast-only-montages)
6. [The 1 fps paddle/maintenance audit](#6-the-1-fps-paddlemaintenance-audit)
7. [Retention craft](#7-retention-craft)
8. [Dialogue selection](#8-dialogue-selection)
9. [Pacing numbers](#9-pacing-numbers)
10. [Punch-ins (fake second camera) with build_edit "zoom"](#10-punch-ins-fake-second-camera-with-build_edit-zoom)
11. [Cards, text and graphics](#11-cards-text-and-graphics)
12. [4K source handling](#12-4k-source-handling)
13. [Pre-delivery checklist](#13-pre-delivery-checklist)

---

## 1. Format and skeleton

- **Landscape 1920×1080**, the camera's own aspect ratio, one continuous file, original
  source audio only (no music beds, no added SFX, no voice-over).
- Lock the same shape every episode. Sameness across episodes is itself a retention tool
  for returning viewers, and the post-release thank-you line (if the angler has one) becomes
  a series signature.

```
[COLD OPEN — EXPERIMENT, §7.4]               0:00–0:12
INTRO (greeting / place / plan, tight)       ~0:10–1:00   must state the day's question
COMPRESSED LAUNCH → first spot               under 60 s of screen time
CATCH 1 — full arc                           reach it by ~2:30–3:00 of runtime
  └─ post-catch "why that worked" line if they say one
VALLEY: close catch → next tease → compressed move → arrive
CATCH 2 … N — full arc each, chronological
BACK-HALF LULLS: longer scenery holds, visible wildlife, technique talk
LAST CATCH — full arc, thank-you line
OUTRO: the wrap-up line → hard cut out
```

- **Intro:** start exactly on the angler's first spoken word (no dead air before it). Open
  on the first *specific* sentence: where they are, what they're throwing, the plan. Never open on
  greeting filler, "in this video…", or slow context.
- **Intro and outro are TIGHT.** Cut all wishy-washy deliberation ("should I head in?",
  "might be about that time…", "well, I think I might…"). Close on the wrap-up line ("…five
  catches, see you next time") and nothing after it. Never stretch either end to pad
  runtime; pad with fishing shots instead (§4). Viewers leave the instant they smell an
  outro, so summaries and thank-you-for-watching chains are exit signals.
- **First catch by ~3:00 of runtime.** If the first fish came 90 minutes into the day,
  compress the whole pre-catch stretch to launch beats + one location-reasoning line + one
  scenic beat.
- **Catches are chronological; filler is not.** The best non-catch moment (a big blow-up,
  an eagle flyover) may move later in the video as a re-engagement beat.

## 2. The catch arc

Every catch keeps **all seven stages, in order, as mostly continuous footage**:

1. the cast
2. the retrieve / reeling (show it; buildup is excitement; never start a catch at the fish
   already coming out of the water)
3. the bite / hookset / fight
4. the landing (net or hand)
5. the hold-up (show the fish)
6. the release: let it go and swim away; **never cut before the release**
7. end right **after the post-release line** ("thank you, I appreciate it", "thanks,
   buddy", or whatever the angler says to the fish). If they have no such line, end on the
   swim-away plus the quiet exhale beat.

Then cut before they reach for a phone to log the catch (see
[editing-rules.md](editing-rules.md)).

- **Arc-presence check:** before shipping, point at a verified frame for each stage
  (rod working, rod loaded, fish visible, fish in hand, fish going back) and log the
  timestamps in `EDIT_NOTES.md`. A "hands down at the lap" frame is not evidence of a catch;
  it looks the same as re-rigging or picking weeds.
- **Gap check:** densely sample the seconds *between* stages. Landing → hold-up is where
  scale fiddling and unhooking hide; reeling → landing is second. Hard-cut over any stretch
  with no rod load, no visible fish and no decision being made, even inside an otherwise
  continuous take.
- **Density contrast:** compress buildup, hold the payoff. The hookset, the hold-up and
  the release each play inside one uninterrupted take; the drop in cut density is what
  tells the viewer this is the climax.
- **Later-catch compression:** on a many-small-fish day, catch 1 gets the most generous
  cut. Later near-identical catches keep every stage but compress harder *inside* stages
  (jump cuts within the reel-in, between sentences). Every stage survives, not every second.
- **Long reel-in on blow-ups/big fish:** a good surface strike or a heavy fish earns a longer
  buildup; the anticipation is the content.
- **Camera died mid-catch?** Bridge the gap with a placeholder card (§11) rather than
  dropping the catch.

## 3. Vibe: calm and relaxing

A fishing long-form is a companionship product, a peaceful hang on the water with catches
inside it, not a hype reel. This is the default unless the angler asks for something else.

- Let ambient and scenery beats breathe. Don't over-compress into a breathless pace;
  over-editing (stacked zooms, relentless jump cuts) fatigues a patient fishing audience.
- **Two-speed strategy:** the portrait short-form clips ([portrait-shortform.md](portrait-shortform.md))
  carry the high-density editing. The long-form cuts dead time and redundancy but never adds
  artificial energy.
- **Light self-deprecating humor in small doses** (stuck in a tree, a bad cast, a backlash
  line) is welcome seasoning, at most a couple of short beats. If a funny bit doesn't
  clearly land, leave it out. The bulk is always fishing: casting, retrieves, catches,
  scenery.
- Authenticity is the moat: real audio, whole sentences, small fish shown honestly. The
  edit's job is density and story, never gloss.

## 4. Length, filler and "no lingering"

- **Agree a target length with the angler** (a ~20 min target worked for a calm-hang
  channel). Genre guidance says 8–15 min out-retains a padded 20 on a small-catch day, so
  resolve the tension this way: pad **only** with genuine fishing action and scenery, and
  tell the angler plainly when the day honestly supports 12–14 minutes. Never hit a number
  by loosening the rules below.
- **Good filler is ACTION:** quick cuts of casts, retrieves, blow-ups/strikes/missed
  bites, big splashes, wildlife **that is identifiable on camera** (zoom in and check;
  unseen-animal talk stays out), pretty water/pad/reed scenery holds. Test: if the rod is
  loaded, the lure is flying, or the water is doing something, it's filler. If they're looking
  down at their hands, it isn't.
- **Filler is NEVER:** tying on or re-rigging, untangling, scale fiddling, paddling,
  rambling, dead time. These aren't "trim hard" candidates; they don't qualify at all.
- **Do not linger on non-action shots of the angler.** Fixing something, looking down,
  fumbling: cut it, or keep a few seconds at most when it's story-relevant (tying on the
  lure that pays off a later callback).
- **Action beats are tight: action → reaction line → CUT.** Around a blow-up, strike or
  miss keep the lead-in, the moment, and the angler's reaction line, then cut straight to their next
  spoken line. Drop the aftermath (retrieving the lure, line wrapped behind them, silent
  scanning). Inside a multi-line postmortem, jump-cut silence-to-silence between line
  clusters instead of playing long quiet gaps.

## 5. Zero paddling, no maintenance, cast-only montages

These are the rules that most often get a long-form sent back. They exist because the
footage is full of these shots and they all read as "nothing is happening".

- **Zero paddling on screen.** No shot may contain the angler paddling (or working a
  pedal drive / trolling motor with hands on it): not as filler, not as a beat tail, not
  "just a stroke or two." Only exception: the angler is saying something *necessary* to the edit
  while paddling (the outro line, a load-bearing story line). Keep the minimum speech
  window and nothing more. Cut the paddle between spots and let a sentence boundary carry
  the location jump.
- **No body-maintenance shots, ever.** Drinking, eating, stretching, adjusting clothes,
  hat or camera. They are lingering-on-the-angler shots even when brief.
- **Never show weed/junk cleaning off the lure**, lure inspection, or hands-at-lens
  fiddling, unless they're saying something over it the edit needs (missed-bite talk while
  picking a weed). Then keep the minimum talking window.
- **A casting montage is CAST… CAST… CAST.** Back-to-back shots of only the cast itself:
  wind-up/whip → lure flying → splashdown, ~2–4 s per shot (~3.5 s typical), hard cut
  straight into the next cast. No reeling, no waiting, no drifting inside a montage. A
  10–15 s window "containing a cast somewhere" is not a casting shot; trim to the cast.
  Montages play as dedicated action beats, and only montage casts that look good (no
  backlash fumbling, no tree snag unless that's the joke).
- When you cut paddling or maintenance out, replace it with more cast-only montage shots or
  a pure scenery hold, never with nothing.
- Pure scenery holds with no angler action remain a separate, allowed filler type.

## 6. The 1 fps paddle/maintenance audit

Sparse strip checks (a frame every 3–5 s) let paddle strokes through between samples, and
small contact-sheet tiles make a raised paddle blade look like sunlit lily pads. Run this on
the **assembled cut** (same number of frames as checking each source window, and it's what
actually ships):

```bash
mkdir -p audit
ffmpeg -v error -i edit.mp4 -vf "fps=1,scale=320:-2,tile=6x8" -q:v 3 audit/sheet_%03d.jpg
```

- **1 fps over the whole video, 320 px tiles, 6 columns × 8 rows = 48 s per sheet**
  (~1920 px wide, readable at about 1:1). 250 px tiles were tried and missed real
  violations, including long continuous paddling runs.
- Sheet *n*, tile *k* (1-based, row-major) = output second `(n−1)·48 + (k−1)`.
- **The discriminator:** a *stowed* paddle lies flat on the deck (fine, it's in half the
  footage). A paddle *in use* shows the blade raised with the shaft crossing the frame
  diagonally, usually with a hand on it.
- In the same pass reject: hands on the lure, drinking/eating/adjusting, other people or
  boats, hand-held phone.
- Color-based automatic paddle detection does not work (sunlit vegetation floods it). Look
  at the sheets.
- **Budget for a re-cut.** After fixing, re-run [check_cuts.py](cookbook.md) on the new
  segment list (recut boundaries commonly clip a word) and re-audit any seconds a boundary
  extension added.

## 7. Retention craft

### 7.1 Minute one decides the video
Roughly half of viewers leave within the first minute; the steepest drop is seconds 10–20.
Videos holding ≥65% at 1:00 see much higher overall average view duration. Spend
disproportionate effort on 0:00–1:00.

### 7.2 State the day's question
Every video needs a stated goal or question in the first minute that the day answers:
"trying to get three today", "can the new lure beat the old one", "before the storm hits".
Small fish then become progress markers instead of underwhelming payoffs. Anglers usually
say one unprompted; find it in the transcript and keep it in the intro. Losing the goal is a
valid ending, and answer it in the outro either way.

### 7.3 Causality beats chronology ("but / therefore")
Consecutive beats should connect with "but" or "therefore", never "and then". A fishing day
is naturally an "and then" list; the edit converts it by selecting dialogue that creates
causal links: theories, lure changes, doubts, setbacks. **Set up the callbacks:** if a catch
is followed by "so much for my theory", the earlier line stating that theory must be in the
cut. Failed prediction → payoff is the story.

### 7.4 Open loops, and the cold open (EXPERIMENT)
Keep at least one unresolved question alive at all times, and never resolve a tease until
the next one is planted. The angler's narration supplies loops for free ("if there's a fish
anywhere it's under that dock", "I'll hit that on the way back"). Keep those lines, ideally
as the last thing before a cut. Every planted tease must pay off; a loop that never closes
is the cardinal sin.

**Cold open (EXPERIMENT):** open on the best 8–15 s of the best catch (rod doubled, drag,
one complete exclamation) and cut away *before* the fish is visible, then hard cut to the
normal intro. Complete sentences only, resolve nothing, and the full arc still plays intact
in its chronological place.

### 7.5 Structure the attention curve
- Minutes 0–1 win or lose the video; 1–3 need fast progression (many beats); 3–6 the most
  exciting simple content. After ~6 minutes invested viewers tolerate and benefit from
  slower, longer takes. **Front-load:** long scenery holds, technique talk and wildlife belong
  in the back two-thirds, not before the first catch.
- **A re-engagement beat every ~2–3 minutes.** Catches are the natural spikes; when they're
  far apart, fill the gap with a missed strike, a blow-up, visible wildlife or a spoken tease,
  never a flat block of filler.
- **Valley sequencing:** thank-you line → *immediately* the angler's next spoken intention or tease
  (never silence after a release) → compressed move → arrival at the new spot. Cut to the
  arrival, not the trip there.
- **Build a beat sheet before cutting:** tag every candidate moment from transcript + visual
  scan as `catch / decision / setback / theory / joke / scenery / wildlife / callback-seed /
  tease`, then answer "what was this day actually about?" That theme decides which non-catch
  dialogue survives.
- **One B-story per video (EXPERIMENT):** on small-fish days, cut back 2–3 times to one
  secondary thread (the heron that keeps showing up, the new lure test) so filler has its own
  mini-arc.

### 7.6 Shot selection extras
- **Keep:** missed strikes and blow-ups (one per valley rather than folding all action into
  catch segments); scenery chosen for its *audio* (drips, birds, water on the hull); shots
  where the waterline stays in frame (it's the stabilizing reference that prevents POV
  motion sickness); the quiet exhale beat after a release.
- **Kill:** whip-pans and the jerkiest stretches. If a segment is continuously jerky for
  more than ~10 s, break it with a punch-in (§10); the scale change resets the viewer.
- **Horizon:** don't globally de-fish the lens (costs resolution; the barrel look is part of
  POV). Level only *held* shots (hold-ups, long scenery) where a canted waterline is
  obvious, by 2–5° with a ~5% crop. Leave fight tilt alone; it reads as energy.

## 8. Dialogue selection

Priority order when choosing which lines survive (highest first):

1. **Theory / decision / reasoning** ("they should be on that windblown bank", "switching
   baits"): the but/therefore connective tissue and the "what's working and why" fishing
   viewers want.
2. **Forward-looking teases**: free open loops; place them at the end of a segment.
3. **Doubt and frustration** ("maybe they're just not here"): editors instinctively cut
   self-doubt, but it's the most valuable retention dialogue because it turns the next catch
   into a reversal. At least one honest "nothing's biting" line per lull.
4. **Callback seeds and payoffs**: predictions right or wrong (wrong is funnier), repeated
   phrases, named spots/lures. If a gag lands twice, the third use should escalate or
   subvert, then retire.
5. **Post-catch "why that worked"**: converts a repetitive catch into new information.
6. **Fourth-wall lines** ("did you see that?"): keep every one.
7. **Exclamations during fights**: a chest/head cam can't see the face, so the voice is the
   reaction shot. When compressing a fight, keep beats with a vocal reaction over similar
   silent ones.
8. **Clock / weather / stakes lines** ("last spot of the day"): free ticking-clock tension.

**Cut:** greeting filler, wishy-washy deliberation, transit chatter with no decision or tease,
repeated observations that don't build, mid-video like/subscribe asks (one short natural
mention max, late), and anything said to the editor/assistant (see editing-rules.md).

**Never** chop inside a sentence or drop a trailing tag phrase ("…no problem."). Use
speech islands (`scripts/speech_islands.py`) for true line ends, not whisper word times, and
verify with `check_cuts.py`.

**Preserve at least one 30–90 s uncut "thinking out loud" stretch per video.** A couple of
unhurried musing passages are what make it a hang rather than a reel.

## 9. Pacing numbers

| Thing | Number |
|---|---|
| Base pacing between catches | ~15–25 s per cut |
| Burst sequences (catches, montages) | 5–10 quick cuts |
| Visual change in talky stretches | every ~30–45 s; every ~10–15 s in the first 3 min |
| First deliberate pattern interrupt | ~0:25–0:35 (first punch-in or overlay) |
| Dead-air threshold between sentences (non-catch) | ~1.5–2 s |
| Long ambient hold, back half | one 10–15 s untouched hold every ~4–6 min |
| Montage beat length | 1–3 s (moves), ~2–4 s (casts), 4–6 shots |
| Re-engagement beat | at least every ~3 min |
| First catch | by ~3:00 runtime |
| Tail after the wrap-up line | hard cut ≤10 s after its last word; ≤20 s total after the final release |

- **Never trim:** the 2–4 s of quiet right before a bite (cheapest tension there is), the
  post-release exhale, pauses inside a musing stretch.
- **Cut off obvious outcomes** mid-*action* (never mid-sentence): cast flies out → cut before
  splashdown to the line already tight.
- **Continuous-thought bridge:** if the angler starts a thought at spot A and finishes at spot B, cut
  the move and let the sentence boundary carry the location jump.
- **Audition every splice eyes-closed for audio continuity.** Match ambient beds
  (water-lap → water-lap); never splice into a wind gust or a paddle bang. This is the most
  transferable rule for a hard-cuts-only, real-audio edit.
- **Signature sounds are protected like sentences:** drag clicker, topwater pop, release
  splash. Never cut during them, never land an overlay on them.

## 10. Punch-ins (fake second camera) with build_edit "zoom"

The axial cut (full frame → tighter crop of the same shot) reads as a second camera angle,
refocuses attention, and center crops dodge the fisheye edges.

- **Cap:** ~1.4× on a 1080p source (softer than that on a TV). On 4K source you can go to
  ~2.0× with zero upscaling (§12).
- **Hard punch in and out.** No drifting zooms, no whip-zooms, no keyframed Ken Burns.
- **Motivated beats only:** the hookset, "there he is!", the first surface flash, the lip
  grab, the lure in the fish's mouth at hold-up. A punch-in *inside* a continuous take is
  not an audio cut, so it may fall mid-sentence, but prefer sentence boundaries and **cut on
  movement** (the hookset swing, the lift) to hide the scale jump.
- **Fight template:** WIDE cast → TIGHT rod tip on hookset → WIDE if the fish runs or jumps
  → TIGHT boatside → WIDE landing → TIGHT hold-up → WIDE release. Wide = geography,
  tight = intensity. Never open a catch already punched in; never punch → same punch (go
  punch → wide → different punch).

**Mechanics.** In a landscape `build_edit.py` JSON, add `"zoom"` to a segment. Each entry is
a piecewise-constant window `[t0, t1, factor, S, Y]`: from source time `t0` to `t1` (absolute
seconds in that GX file, same clock as the segment's `in`/`out`), crop by `factor` centered
on `(S, Y)` in **1920×1080 coordinates** (the script rescales to the real source size and
clamps the window inside the frame). Outside every window the full frame plays.

```json
{"name": "yt", "mode": "landscape", "srcdir": "<footage_dir>",
 "work": "<scratch>/build", "out": "<scratch>/yt_base.mp4",
 "segs": [
   {"tag": "C1", "src": "GX010042", "in": 512.0, "out": 641.5,
    "zoom": [[548.2, 553.0, 1.35, 1100, 420],
             [601.4, 612.0, 1.40,  900, 560]]}
 ]}
```

Always pass all five values `[t0, t1, factor, S, Y]`. Read `S`/`Y` off a 1920-wide
frame grab of the moment, and check the punched frame for softness and for the subject
staying inside the crop for the whole window.

## 11. Cards, text and graphics

Style law: plain white type, no boxes, no animation, hard cut on and off. Static and sparse
reads authentic; animated templates, logo bugs and HUDs read overproduced.

**Standing:**
- **Equipment-failure placeholder card.** If the camera dies or the clip ends mid-catch
  (battery, card full, overheating), bridge the gap with a deadpan full-screen card: black
  background, big white text stating what the viewer missed ("SMALL FISH HELD UP HERE"),
  a small parenthetical with the reason ("(camera battery ran out)"), ~4 s, silent, hard cuts
  both sides. If the angler says a setup line right before the doomed footage, keep it
  before the card. The deadpan honesty plays as a small joke and keeps the catch count true.
- **Closed captions:** upload the transcript as CCs. Do NOT burn full-time captions into the
  long-form (it reads as repurposed short-form). Burn text only for a line genuinely
  unintelligible over wind ([burn_captions.py](cookbook.md) if needed).
- **Description chapters** on every upload. Title them as teases, not labels ("The dock
  finally pays off", not "Catch #2"), and start each catch chapter at the bite *build-up* so a
  skipper lands in tension, not payoff.

**EXPERIMENT (one at a time, flag in EDIT_NOTES):**
- Conditions/location card at the first scenery shot (`PLACE — 6:40 AM`).
- Technique card once per catch, during the reeling, never over the hold-up (the fish owns
  that frame). Get the rig exactly right from the angler's own words, or ask.
- Fish counter at each landing (`FISH #3`), resolved in the outro. Turns a small-fish day
  into a score with stakes.
- Time-of-day stamps at spot changes (camera metadata makes them accurate).
- Text tease where narration lacks one ("the biggest one hits in 6 minutes").
- One informational freeze-frame max, best hold-up, 1.5–2 s.

**Never:** music beds, added SFX/whooshes, animated lower-thirds, subscribe bugs, persistent
HUDs, slow-motion hero shots, dissolves, timelapse/speed ramps of anything with original
audio, J/L audio leads (audio is cut on the same frame as picture), and bleeping in the
long-form (cursing stays as spoken unless the angler asks otherwise).

## 12. 4K source handling

Check every trip with `ffprobe`; cameras get switched between 1080p and 4K
(3840×2160, ~50 Mbps HEVC).

- `build_edit.py` takes either. Landscape mode scales the full frame to 1920×1080 with
  lanczos and decodes with hardware acceleration where available. Deliver 1080p unless the
  angler asks for a 4K master.
- **Punch-ins get much better:** a 2.0× crop of 4K is a native 1920×1080 window, so
  1.4–2.0× punch-ins cost no sharpness. Keep the same restraint rules (§10); more headroom is
  not a reason for more zooms. 4K also makes "is that animal identifiable?" checks
  answerable (and is what portrait wildlife zooms need, see [wildlife-zoom.md](wildlife-zoom.md)).
- **Frames are huge** (~25 MB raw). Pipe frames, use contact sheets (§6) scaled down at
  extraction time, and never write thousands of raw 4K frames to disk.
- Encodes are slower and segment caches bigger; run them as background jobs and keep the
  scratch dir outside the output folder.
- Thumbnails: grab the hero frame from the 4K source for a sharper punch-in crop, but still
  export 1920×1080 (see [thumbnails-titles.md](thumbnails-titles.md)).

## 13. Pre-delivery checklist

**Story**
- [ ] Beat sheet written before cutting; the day's theme and question identified.
- [ ] Intro opens on the angler's first specific sentence, contains the day's question, zero
      deliberation. (Cold open, if used: complete sentences, unresolved, arc intact later.)
- [ ] But/therefore between consecutive segments; no pure "and then" joins.
- [ ] An open loop live at all times; every planted tease pays off; every payoff line has its
      setup line earlier in the cut.
- [ ] The question is answered in the outro, win or lose.

**Structure & pacing**
- [ ] First catch by ~3:00; re-engagement beat at least every ~3 min; no valley starts with
      post-release silence.
- [ ] Burst vs base rhythm; visual change every ~30–45 s in talky stretches; first interrupt
      by ~0:35.
- [ ] At least one 30–90 s uncut musing stretch; one 10–15 s ambient hold per ~4–6 min of
      back half.
- [ ] Pre-bite quiet and post-release exhale not trimmed; signature sounds uncut.
- [ ] Every splice auditioned eyes-closed for ambient continuity.
- [ ] Calm vibe intact; humor beats few, short, and actually funny.
- [ ] Length honest: padded only with action/scenery; told the angler if the day supports
      less than the target.
- [ ] Outro: hard cut ≤10 s after the wrap-up line.

**Catch arcs**
- [ ] All 7 stages present, in order, with a verified frame timestamp each in EDIT_NOTES.
- [ ] Gaps between stages densely sampled; dead time and fumbling hard-cut out.
- [ ] Punch-ins ≤1.4× (1080p) / ≤2.0× (4K), motivated, cut on movement, wide established
      first.
- [ ] Later catches compressed within stages, never across stages.
- [ ] Each catch ends before any phone-logging reach.

**The zero lists**
- [ ] 1 fps / 320 px / 6×8 audit of the assembled cut: zero paddling, zero body maintenance,
      zero lure/weed cleaning, zero hands-at-lens (unless necessary speech overlaps).
- [ ] Casting montages are cast-only (whip → flight → splash, ~2–4 s each).
- [ ] Action beats are action → reaction → cut; no aftermath dead time.
- [ ] No other people/boats, no private phone/assistant audio, no lines addressed to the
      editor, bodily noises cut around.
- [ ] Wildlife shown is identifiable on screen.

**Technical**
- [ ] `check_cuts.py` at zero chops on the final segment list; no sentence or tag phrase cut.
- [ ] Assembled with `concat_av.py` (build_edit does this); `check_av_sync.py` at zero
      out-of-sync probes.
- [ ] Hard cuts only; original audio only; no music beds; third-party music audited out (see
      [cookbook.md](cookbook.md)).

**Packaging**
- [ ] Thumbnail + A/B variants and a `PACKAGING.md` (titles, description, chapters,
      hashtags) per [thumbnails-titles.md](thumbnails-titles.md).
- [ ] `EDIT_NOTES.md`: exact source in/out points, verified arc timestamps, which
      EXPERIMENT items were used, and what to ask the angler about.
