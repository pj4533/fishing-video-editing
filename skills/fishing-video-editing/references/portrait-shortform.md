# Portrait short-form — one 9:16 "feature" per catch (TikTok / Reels / Shorts)

A **feature** is one portrait 1080×1920 clip per landed fish, 30–60 s, catch-only. It is the
discovery product: it has to stop the scroll on frame 1 and get finished. This file covers how
to cut it. Everything here sits on top of [editing-rules.md](editing-rules.md), which wins any
conflict (hard cuts only, never cut mid-word, original audio cut on the same frame as the
picture, nothing the angler says *to the editor* goes in).

For the 3–6 min full-trip portrait recap see [tiktok-longform.md](tiktok-longform.md). For the
landscape long-form edit see [youtube-longform.md](youtube-longform.md).

Tags: **RULE** = converging evidence or a lesson that was already paid for in rejected cuts;
**EXPERIMENT** = directional, try it and watch the analytics / the angler's reaction.

## Contents

1. [Portrait or landscape?](#1-portrait-or-landscape)
2. [Length band](#2-length-band)
3. [Structure of a feature](#3-structure-of-a-feature)
4. [What to cut, what to keep](#4-what-to-cut-what-to-keep)
5. [Entry-point variety](#5-entry-point-variety)
6. [The hook (0–3 s on-screen text)](#6-the-hook-03-s-on-screen-text)
7. [Burned captions](#7-burned-captions)
8. [Safe zones and layout](#8-safe-zones-and-layout)
9. [Loops](#9-loops)
10. [Pacing numbers](#10-pacing-numbers)
11. [Bleeps](#11-bleeps)
12. [Centering the fish](#12-centering-the-fish)
13. [Example caption/hook JSON](#13-example-captionhook-json)
14. [Per-clip pre-delivery checklist](#14-per-clip-pre-delivery-checklist)

---

## 1. Portrait or landscape?

| Product | Format | When |
|---|---|---|
| Feature (this file) | portrait 9:16, 1080×1920 | every landed fish — always make one |
| Full-trip recap | portrait 9:16, 3–6 min | a day with 2+ catches, or a story worth telling ([tiktok-longform.md](tiktok-longform.md)) |
| Long-form edit | landscape 16:9, source aspect | the whole trip for YouTube ([youtube-longform.md](youtube-longform.md)) |

- **RULE — portrait for anything that lives in a vertical feed.** TikTok, Reels and Shorts all
  play 9:16 full-screen; a letterboxed 16:9 clip looks like a repost and wastes ~2/3 of the
  screen.
- **RULE — one render ships everywhere** if it obeys TikTok's safe zones (the strictest, §8).
- **RULE — portrait is a crop, so the subject must be tracked.** A 9:16 window out of a 16:9
  frame is ~32% of the width (608 px of 1920 at 1080p; ~1215 px of 3840 at 4K). The fish moves;
  a fixed crop loses it (§12).
- 4K sources give a much sharper portrait crop than 1080p — prefer them when available.

## 2. Length band

- **RULE — 30–60 s.** Features are short. A cut that runs past ~60 s is a long-form clip in a
  portrait frame and will be rejected; trim it, don't defend it.
- **RULE — a long fight is two beats, never played whole.** "Keep all the reeling" is sized for
  a fight of a few seconds. When reeling runs past ~10–15 s, keep **two beats** of ~5–10 s each —
  (1) the bite / rod loading / first reaction, (2) the fish coming up and aboard — joined by one
  hard cut over the silent middle. Why: a 28 s unbroken fight blew a feature out to 1:31 and it
  was rejected on sight; the recut at 44 s was approved.
- **RULE — but never compress the fight to one flash.** A single <10 s burst of bent rod reads
  as a still photo, not a fight, and comes back as "you cut too much, show more of the reeling."
  If two beats still feel thin, lengthen a beat or add one — don't pad other sections.
- **EXPERIMENT —** avoid the ~45 s dead middle: short-video performance is bimodal (very short or
  near 60 s). Land a small fish at ~30–40 s; let a big fish with good commentary run to ~55–60 s.
- Completion benchmarks to judge against: 30 s clip → 35%+ healthy; 60 s → ~20% is where the
  algorithm starts favouring you.

## 3. Structure of a feature

Catch only — no intro, no outro, no setup. The arc never loses a stage; tightening happens
*inside* stages.

| Beat | Typical time | Content |
|---|---|---|
| Hook + bite | 0:00–0:05 | Open ≤1 s before the bite / rod load (or a 1–2 s non-speech flash-forward, §5). Hook text on screen from frame 1. The angler's first reaction line ("fish? fish!") lands here. |
| Fight | 0:05–0:20 | All of a short fight, or two beats of a long one. Cut on rod-load peaks, jumps, surface flashes. |
| Quick pull-in | 0:20–0:25 | Fish comes out of the water / into the boat or hand. End the shot as it comes aboard — the net time is cut. |
| — the cut — | | Net-sitting, unhooking, gear juggling all die here. |
| Hold-up | 0:25–0:40 | The fish shown to camera, centered, head kept in frame. **The angler's commentary about the fish is the heart of the clip** — size, colour, wounds, "I think I've caught you before." Longest continuous shot. |
| Weigh/scale line | (optional) | Cut scale *rigging*; keep the line where they read the number ("three oh three!") and their reaction to it. Hard cut from hold-up straight to the reading. |
| Release | 0:40–0:50 | The let-go and swim-away, visible and centered. Ride the crop down to the waterline. Never cut while the fish is still mid-frame. |
| Last line | end | The angler's post-release line ("thank you, buddy"). End ≤1 s after its last word. |

- **RULE — the approved shape is very few, long takes.** Typically shot 1 = bite → fight →
  aboard; one cut; shot 2 = hold-up → (scale line) → release → last line. More cuts only where a
  long fight or a fumbling gap forces them. Tight comes from removing the boring middle, not from
  chopping action into snippets.
- **RULE — the reaction line is not the bite.** On a small fish the angler's first words often come *as*
  it swings out of the water; the reeling happened silently before. Find the rod loading on the
  frames: step back from the first visible fish in ≤2 s steps until the line is slack or the
  retrieve is steady, and start there. Why: a clip that opened on the fish leaving the water was
  sent back for "cutting too much."
- **RULE — keep the reeling after a swing-up that drops back in.** Don't cut from the drop
  straight to the boat.
- **RULE — end the instant the payoff lands.** Trailing seconds after the last line are pure
  completion loss. The angler's line is the outro.
- **RULE — protect the post-release quiet beat** (1–2 s of water and exhale before the closing
  line) — it is the payoff landing, not dead air.

## 4. What to cut, what to keep

**Always keep**
- The bite / hookset with its live sound — the genre's money shot.
- The angler's reaction lines during the fight. When compressing, keep beats that carry a vocal reaction
  over visually similar silent beats; their voice is the reaction shot a chest/head cam can't film.
- Rod-load peaks, drag runs, jumps, surface thrashes.
- The hold-up and all their commentary about the fish.
- The scale *reading* line (number + reaction), when they weigh it.
- The full release through the swim-away, and the post-release line.
- Signature sounds — drag, topwater blow-up, release splash. No cut and no text landing on them.

**Always cut**
- Casting, waiting, pre-bite setup, any intro talk.
- **Net fumbling** and any fish sitting in the net.
- **Unhooking** — hands at the lap, pliers, untangling.
- **Scale rigging** — clipping the fish on, waiting for it to settle, reading it off silently.
  Landing → hold-up and hold-up → scale are the highest-risk gaps for this; sample them densely
  before shipping.
- Two adjacent shots that look the same.
- Whip-pans and spins (motion sickness on first-person footage).
- Anything after the last line.
- Anything said to the editor ("zoom in on that", "remind me…"), and other people.

## 5. Entry-point variety

When one trip yields several features (and they'll be posted near each other), don't open all of
them the same way. Rotate among:
- **Rod loading** — open on the rod bending, reaction line arrives a beat later.
- **The angler's reaction line** — open on a complete short exclamation ("oh! there he is!").
- **Flash-forward** — 1–2 s of the best jump or the hold-up, **non-speech**, then hard cut back to
  the bite. Use it when the fight runs long and the payoff needs teasing; skip it when the bite is
  fast and visual. The full arc still follows in order.
- **A stakes line** just before the bite, if they said one ("last cast here…"), complete.

Never open on a sentence fragment, a cast, or scenery. Adjust the *opening*, never the arc.

## 6. The hook (0–3 s on-screen text)

- **RULE — present from frame 1, never fading in;** held ~3 s; passes the mute test.
- **Two lines, ≤ ~14 characters per line,** all caps, heavy sans, centered in the top third
  (e.g. size ~88 at y ≈ 220 and ≈ 330). A small kicker line over a payoff line reads best.
- **Content: count / novelty / stakes.** "TIP FROM A / COMMENTER", "BIGGEST ONE / HERE YET?",
  "THIRD FISH / OF THE DAY", self-aware "IT'S A DINK / BUT LISTEN".
- **Often the angler's own line.** The best hooks are lifted from their audio ("NOT CATCHING / DINKS TODAY").
  A hook must never contradict what they say on camera.
- **Avoid "wait for it"** and other delay phrasing — platforms penalise it and it signals a slow
  build.
- EXPERIMENT — draft three (curiosity / stakes / counterintuitive) and pick one.

## 7. Burned captions

~80% of feed video is watched muted; captions are the highest-evidence tactic. Every feature gets
them for the whole runtime.

- **Verbatim.** The angler's real words, never paraphrased or "fixed". Never caption ambient or annotations
  ("[wind]", "(beep)", "[Music]"). Bleeped words show as `f***`.
- **2–5 words per chunk, ≤ 26 characters, clause-chunked** — break at natural phrase boundaries
  ("Is this gonna be" / "my biggest here?"), never mid-phrase.
- **Timed to speech islands.** Take chunk windows from `silencedetect` speech islands (or per-
  segment word timing), not one whisper pass over the whole clip — whisper drift reaches seconds
  and goes worse over splash and wind.
- **Band at y ≈ 1360 of 1920** — below a low-held fish, above the bottom UI.
- One chunk on screen at a time; heavy sans, white with a black outline.
- Use `scripts/burn_captions.py` (it merges whisper sub-word tokens so no word is split on screen,
  and accepts hand-timed `manual_chunks` plus extra text elements). After burning, print every
  chunk with its window and spot-check rendered frames at several caption midpoints. **A clip
  with a split word or a mistimed caption does not ship.**
- Captions and hook text go on last, over the finished picture (after any overlays and bleeps).

## 8. Safe zones and layout

Canvas 1080×1920. Keep all text, and the fish's head, out of:

| Edge | Clear | Why |
|---|---|---|
| Top | ~150 px | status bar / tabs |
| Bottom | ~484 px | caption, username, nav bar |
| Right | ~180 px | like / comment / share rail |
| Left | ~60 px | edge cropping |

- Hook in the top third (y ≈ 150–400), captions at y ≈ 1360, nothing over the fish during the
  hold-up.
- **RULE — after centering, check the fish's head is not in the right ~180 px column** — the like
  rail will sit on it.
- When no fish is visible, keep a piece of the angler (hands, rod butt, bow) in frame as the POV
  anchor.

## 9. Loops

- **EXPERIMENT — loop engineering for sub-~35 s features only** (loop value concentrates under
  ~30 s). Pick the opening so the end cuts cleanly back into it: water-to-water (release splash →
  strike splash), or narrative bookends (opens on the angler talking to the fish, ends on "thank you,
  buddy"). Test: play the last 3 s into the first 3 s; if it feels continuous, it loops.
- Longer features end on the angler's closing line; don't contort the arc for a loop.

## 10. Pacing numbers

- Remove between-sentence gaps longer than ~0.5–0.75 s (always at sentence boundaries, verified
  with `scripts/check_cuts.py`).
- Visible change every **2–4 s** during the fight; slower in the hold-up and release, where the
  fish is the interest.
- First cut or visible change within 3 s.
- **Density contrast marks the payoff:** fast through the fight, then hold uncut through the
  hold-up and release.
- Audition every cut for ambient continuity (calm → wind gust reads as a mistake).
- Never: music beds, whooshes, speed ramps, dissolves, freeze-frames, animated templates. Raw
  first-person footage with real reactions is the winning style in this genre.

## 11. Bleeps

- **RULE — short-form platforms get hard curses bleeped**, surgically: a 1 kHz tone over only the
  curse syllable, neighbours audible ("let's ⟨bleep⟩-ing go"). Never cut the line instead — the
  bleep is part of the fun. Mild exclamations ("holy crap", "freaking") stay. The landscape long-
  form edit keeps cursing untouched.
- Time the bleep from the **low/high-band energy envelope** (10 ms windows), not whisper word times (they're ~100+ ms off,
  and seconds off over splash). Verify on the final audio by re-transcribing only the bleep window.
- Time captions from the clean, pre-bleep audio, then apply the bleep. Recipe:
  [cookbook.md](cookbook.md).

## 12. Centering the fish

A visible fish must be **centered by a verified per-frame track** — never an eyeballed crop.
Run `scripts/fishtrack2.py` (keyframe-anchored, bidirectional), feed its track (plus a head-side
bias) to `scripts/build_edit.py`, and verify on large output frames. **If the whole fish won't
fit, frame the head, not the tail.** Before judging centering, confirm the verify frames actually
*contain a fish* at the bite, hold-up and release — centering checks pass silently on empty
water. Full procedure: [cookbook.md](cookbook.md) (fish-centering section).

## 13. Example caption/hook JSON

The extra-text / manual-chunk input `scripts/burn_captions.py` accepts (times in output-clip
seconds):

```json
{
  "cap_y": 1360,
  "texts": [
    {"text": "TIP FROM A", "t0": 0, "t1": 3.0, "size": 88, "y": 220},
    {"text": "COMMENTER",  "t0": 0, "t1": 3.0, "size": 88, "y": 330}
  ],
  "manual_chunks": [
    [0.45, 2.8,  "Fish? Fish."],
    [16.3, 17.6, "Whoo!"],
    [18.1, 19.6, "That's a big boy."],
    [23.05, 24.1, "Is this gonna be"],
    [24.1, 25.6, "my biggest here?"],
    [40.8, 43.2, "3.03"],
    [44.4, 45.9, "That is the biggest"],
    [45.9, 47.4, "I've caught here."],
    [56.9, 59.4, "Thank you very much."]
  ]
}
```

Note the two-line hook, clause-chunked captions, the scale reading as its own chunk, and the
clip ending on the thank-you line.

## 14. Per-clip pre-delivery checklist

**Opening**
- [ ] Frame 1 is a bent rod, a splash, or a fish — never a cast or scenery
- [ ] Opens ≤1 s before the bite/rod load (checked on frames, not on the first reaction line), or
      on a non-speech flash-forward
- [ ] Hook on screen from frame 1: two lines, ≤ ~14 chars each, top third
- [ ] Entry type differs from the trip's other features where possible

**Arc**
- [ ] A frame exists for each stage: rod loaded, fish visible, hold-up, release
- [ ] Fight is the whole short fight, or two beats of ~5–10 s for a long one — not one flash
- [ ] Net fumbling, unhooking and scale rigging cut; gaps between stages sampled densely
- [ ] Hold-up commentary intact; scale reading line kept if weighed
- [ ] Full release visible; ends ≤1 s after the last line

**Sound and cuts**
- [ ] `scripts/check_cuts.py` passes — no cut mid-word, all at sentence boundaries
- [ ] Assembled with `scripts/build_edit.py`; `scripts/check_av_sync.py` passes
- [ ] Original audio only; `scripts/music_audit.py` clean (or flagged music handled)
- [ ] Curses bleeped surgically and verified on the final audio
- [ ] Nothing said to the editor, no other people

**Picture and text**
- [ ] Fish centered by a verified track on every fish-visible shot; head kept over tail
- [ ] Fish head clear of the right ~180 px; all text inside the safe zones
- [ ] Captions verbatim, 2–5 words, ≤26 chars, one at a time, at y ≈ 1360, no split words, no
      annotation leakage; rendered frames spot-checked

**Length and delivery**
- [ ] 30–60 s
- [ ] Sub-35 s: loop test done (or deliberately skipped)
- [ ] Edit notes record source in/out points, every cut, and the hook text
