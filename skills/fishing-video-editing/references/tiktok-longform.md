# Long-form TikTok — the 3–6 min full-trip recap (portrait 9:16)

One portrait video covering **every catch of the trip**, with the angler's own narration carrying
it between catches. It is the watch-time product (TikTok scores absolute watch time and shares,
and pays creators only on 60 s+ videos). It layers on [portrait-shortform.md](portrait-shortform.md)
(captions, hooks, safe zones, bleeps, centering all apply unchanged) and on
[editing-rules.md](editing-rules.md), which wins any conflict.

Tags: **RULE** = converging evidence or an already-paid lesson; **EXPERIMENT** = directional.

## Contents

1. [What it is, and what it is not](#1-what-it-is-and-what-it-is-not)
2. [Length band](#2-length-band)
3. [Event density — the three-tier cadence](#3-event-density--the-three-tier-cadence)
4. [Anti-predictability](#4-anti-predictability)
5. [Structure template](#5-structure-template)
6. [Bridges](#6-bridges)
7. [Graphics rules](#7-graphics-rules)
8. [Catch-still comparison cards](#8-catch-still-comparison-cards)
9. [Captions and text-element ceilings](#9-captions-and-text-element-ceilings)
10. [Packaging](#10-packaging)
11. [Pre-delivery checklist](#11-pre-delivery-checklist)

---

## 1. What it is, and what it is not

- **RULE — not a small YouTube edit.** ~4 min of recap ≈ 12–15 min of long-form material,
  compressed. Never port the landscape cut to portrait; rebuild from the beats.
- **Build the features first, then reuse them.** Each catch block in the recap is normally the
  finished feature for that fish (already tracked, cut and verified), so the recap adds the cold
  open, premise, bridges and close around them.

| | Full-trip TikTok | YouTube long-form |
|---|---|---|
| Entry | no click — frame 1 is the "thumbnail" | thumbnail + title earn a click |
| Retention checks | 3 s / 10 s / 20 s, then every 15–30 s | first 30 s, then slow decay |
| Pauses tolerated | ≤ ~0.5–1 s | several seconds (calm vibe allowed) |
| Catch arc length | ~35–60 s each | ~90 s+ each |
| Chapters | burned in (`CATCH n/N`) | chapter UI |
| Close | tally card + the angler's closer line | wrap-up line |
| Search | spoken words + on-screen text + caption field, indexed separately | title / description |

- **RULE — one self-contained video, never Part 1 / Part 2.**

## 2. Length band

- **RULE — 3–6 min, sweet spot ~3:30–5:00.** 2–5 min posts carry the highest median reach in
  large studies; completion falls but total watch time rises.
- **Judge it on average watch duration and shares** — ~30–40% completion at 4:00 is a win
  (≈ 80+ s average watch), not a failure against short-clip benchmarks.
- Length follows the catches and the bridges. Don't stretch three catches to 6:00 or
  cram six into 3:00. A slow day with good narration can carry ~5:30 on three catches if the
  bridges are genuinely eventful.

## 3. Event density — the three-tier cadence

| Tier | Cadence | What counts |
|---|---|---|
| Micro (visible change) | every 3–5 s | cut, punch-in, card appearing |
| Minor (new information) | every ~20 s | a miss, a lure change, new water, a stated question, a stakes line |
| Major (payoff) | every 40–50 s | one complete catch arc |

- **RULE — no gap > ~45 s between catch starts** without a strong minor beat inside it; never
  promise a payoff more than ~20 s away.
- Nothing static > 5 s, graphics included. Kill every pause > ~0.5–1 s (between sentences,
  verified with `scripts/check_cuts.py`).

## 4. Anti-predictability

The #1 structural risk in a multi-catch video is not boredom but predictability: by the third
identical arc viewers can call every beat. The arc stages never change — the **presentation** must.

- **Vary the entry point:** rod loading / the angler's reaction line / their bridge sentence running up to
  the bite (complete sentence, then a hard cut — audio and picture cut together, no J/L cuts).
- **Vary durations deliberately** (e.g. 35 / 32 / 41 / 46 / 54 s), never five ~34 s blocks. No two
  catch blocks within ~3 s of each other.
- **Vary density:** cut one catch to the bone; play the best fight nearly real-time.
- **Vary the cards:** not every catch gets a lure card; a map or stat card appears once.
- **RULE — keep chronological order.** Chronology is the story and the counter implies sequence.
  Cheat with duration, density and level (the best fish gets the most seconds and the loudest
  mix), never with order.

## 5. Structure template

```
0:00  COLD OPEN — ONE flash-forward (best jump or hold-up, mid-motion, NON-SPEECH,
      fish centered). Two-line hook from frame 1: count + novelty + stakes
      ("5 FISH / NEW WATER", "A VIEWER'S TIP / PAID OFF?"). Never a montage of
      all catches — it burns every payoff in 4 s.
0:02  PREMISE — the angler's arrival/plan sentences (1–2, complete). The concrete promise
      lands by 0:15. Speak the keywords (species, "kayak fishing", the kind of
      water) in sentence one. Place/stat graphics live here, once each.
~0:20 CATCH 1/N — full arc, feature-tight. Counter card on the cut in (2.5–3 s).
      BRIDGE — one job: open the next loop (see §6)
      CATCH 2/N … chronological, bridged, counters counting
      … best catch: longest, most real-time, loudest
CLOSE release → protected 1–2 s quiet beat → thank-you line → TALLY card
      (≤6 words, e.g. "3 FISH TODAY / BEST: 3.03") → the angler's closer line →
      hard stop ≤2 s after the last word.
```

- **The tally is the last thing read; the angler's line is the last thing heard.** Never a card after their
  closing line.
- **RULE — close on tally + the angler's line, not a loop.** Loop value concentrates under ~30 s; nobody
  re-enters a 4-min video. Their natural "what do you think?" / "see you next time" is the CTA. No
  sub-begging.
- First payoff as early as the premise allows (~0:20–0:30). If the first fish came late in the
  day, the premise and early bridges must carry real minor beats (sightings, misses, a stakes line).

## 6. Bridges

- **6–9 s typical, ≤ ~15% of runtime in total.** Longer narrated stretches are fine only when
  every ~20 s still delivers a minor beat.
- **One job: open the next loop.** A complete sentence that states a plan ("let's try the far
  bank"), reports a miss ("did that just bite?"), names a change, or raises the stakes ("one more
  and it's my best day here"). Ambient paddling is not a bridge.
- Keep free escalation: missed strikes, follows, a fish that came unbuttoned. Put the best miss
  before the weakest catch.
- Cut on action across the boundary; check ambient continuity.
- Kill list: paddling, re-rigging, tackle rummaging, weed-picking, repeated identical shots,
  whip-pans, anything said to the editor, other people.

## 7. Graphics rules

Map, depth or stat inserts (a lake contour map, a water-temp card):

- **Full-frame, never inset** — a portrait frame inside the safe-zone corset has no readable
  corner. Hard cut in and out, 3–4 s, once per graphic.
- **Always under the angler's own sentence** — a complete line they actually said about that place or number
  ("it only gets about sixteen feet deep"). No narration for it = don't insert it.
- Never inside a catch arc; never over a hold-up or release.
- **Dwell formula: 3 s + ~0.6 s per word.** Counter `n/N` ≈ 2.5–3 s; tally (≤6 words) ≈ 4–5 s.
- Same position, size and style every recurrence — consistency turns cards into a system.
- Public-agency maps: crop clean and keep a small source-credit line.
- Plain bold type, no icons or boxes; it should look like data, not a game HUD.
- EXPERIMENT — a slow push on a static map adds motion without a template-y globe zoom.

## 8. Catch-still comparison cards

When the angler points back at the catches in their sign-off ("this one… and this one… same fish or
not?"), show them:

1. **Find the words on silencedetect speech islands**, not whisper word times (which drift).
2. **Hard-cut a full-frame still card for each catch onto the exact word** ("this one" → fish #1,
   "and this one" → fish #2).
3. **Then a split card** (#1 above #2) under the question that follows.
4. Build each card from the hold-up: pick **matching poses** (same side, head the same way, both
   hands) so the fish genuinely compare. Crop tightly around the fish (e.g. ~2200×1000 from a 4K
   frame), scale to 1080 wide, and lay it over a blurred, darkened copy of the same frame. Label it
   inside the safe zone (`FISH #1 · 2.55`).
5. Overlay with `overlay=enable='between(t,a,b)'` on the base picture **before**
   `scripts/burn_captions.py`, so captions sit on top of the cards. The angler's audio continues
   underneath unchanged.
6. Trim dead pauses inside the comparison so the split card isn't static for more than ~5 s.

Same pattern works for any spoken back-reference ("the first one was bigger than this").

## 9. Captions and text-element ceilings

- **Captions run the whole runtime**, verbatim, clause-chunked (2–5 words, ≤26 chars, one at a
  time, y ≈ 1360), timed to speech islands — rules and tooling in
  [portrait-shortform.md §7](portrait-shortform.md#7-burned-captions). Captions are exempt from the
  ceiling below.
- **Ceiling: ~1 text element per 25–30 s** (≈ 8–10 in 4–5 min): hook + N counters + tally +
  2–3 context cards. More than that reads as clutter.
- Counters identical in position and size every time (e.g. size ~84 at y ≈ 240); hook and tally
  two-line, ≤ ~14 chars per line, top third.
- Suppress captions during silent cards (`suppress_caption_windows`).
- Text integrity: no split words, per-segment timing, no annotation leakage, no overlapping
  captions, rendered frames spot-checked. Bleeps per [portrait-shortform.md §11](portrait-shortform.md#11-bleeps).

## 10. Packaging

- **Frame 1 is the thumbnail** on the feed: fish or bent rod, centered, in motion, hook text on.
- **Cover for profile grid / search:** subject and any cover text inside the **center 1080×1080
  square** (the grid crops ~420 px top and bottom; the caption's first line burns over the bottom
  ~270 px).
- The post caption's first line doubles as cover copy — write it as a hook.
- Keywords triple-hit: spoken in the first sentence, on screen, and in the post caption (speech,
  on-screen text and caption are indexed separately; original-audio videos can't ride trending
  sounds, so this is the discovery lane).

## 11. Pre-delivery checklist

On top of the per-clip checklist in [portrait-shortform.md §14](portrait-shortform.md#14-per-clip-pre-delivery-checklist):

- [ ] ONE flash-forward cold open, non-speech, fish centered; two-line hook at frame 1
- [ ] Concrete promise (spoken or text) by 0:15; keywords spoken in sentence one
- [ ] Catch starts ≤ ~45 s apart, or a real minor beat in every gap ≥ 20 s
- [ ] Catch-block durations vary (no two within ~3 s); ≥ 2 different entry types; chronological
- [ ] Bridges each open a loop (plan / miss / change / stakes); total ≤ ~15% of runtime
- [ ] Graphics full-frame, 3–4 s, under the angler's own sentence, outside every arc, once each
- [ ] `CATCH n/N` identical position/size every time, 2.5–3 s each
- [ ] Text elements ≤ ~1 per 25–30 s (captions exempt); dwell = 3 s + 0.6 s/word
- [ ] Still cards (if used) land on the angler's exact words; split card static ≤ ~5 s; captions on top
- [ ] Captions continuous, verbatim, inside safe zones; no split words; frames spot-checked
- [ ] No pause > ~1 s; nothing static > 5 s
- [ ] Close order: release → quiet beat → thank-you → tally → the angler's line → stop ≤ 2 s
- [ ] `scripts/check_cuts.py`, `scripts/check_av_sync.py` and `scripts/music_audit.py` pass on
      the final file; curses bleeped; nothing said to the editor; no other people
- [ ] Every catch keeps its full arc (bite → fight → aboard → hold-up → release → last line),
      fish centered by a verified track
- [ ] Center-square cover checked; edit notes list every segment's source in/out and every card
