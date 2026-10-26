# Thumbnails and titles (long-form packaging)

Every long-form YouTube delivery ([youtube-longform.md](youtube-longform.md)) ships with a
thumbnail and a set of title suggestions. They are one system: **the thumbnail carries the
hook, the title carries the promise the image can't state**, and neither repeats the other.
Upload and setup are done by hand in YouTube Studio; this skill only produces the files and
the text.

## Contents

1. [The three tests](#1-the-three-tests)
2. [Thumbnail: pick the hero frame](#2-thumbnail-pick-the-hero-frame)
3. [Thumbnail: compose and crop](#3-thumbnail-compose-and-crop)
4. [Thumbnail: two-tier text](#4-thumbnail-two-tier-text)
5. [Thumbnail: grade](#5-thumbnail-grade)
6. [make_thumbnail.py usage](#6-make_thumbnailpy-usage)
7. [Variants, A/B and standing out](#7-variants-ab-and-standing-out)
8. [Titles: rules](#8-titles-rules)
9. [Titles: frames that fit fishing trips](#9-titles-frames-that-fit-fishing-trips)
10. [Title ↔ thumbnail system](#10-title--thumbnail-system)
11. [The PACKAGING.md deliverable](#11-the-packagingmd-deliverable)
12. [Checklists](#12-checklists)

---

## 1. The three tests

1. **120 px test.** Shrink to 120 px wide on white AND on `#0f0f0f` (dark mode). If you
   can't tell what the video is, it fails. Most views come from feeds at 120–360 px.
2. **Grayscale test.** At 120 px in grayscale the fish must still separate from the water.
   Luminance contrast beats hue contrast at small sizes; a green-brown bass on green water
   can look fine in color and dissolve in grey.
3. **Cover test.** Cover the thumbnail: does the title alone motivate a click? Cover the
   title: does the thumbnail alone create curiosity? Each half must work alone.

## 2. Thumbnail: pick the hero frame

- The hero is almost always a **hold-up**: fish big in frame, **head/eye/mouth prominent**,
  never the tail. The alternate concept is **the moment before the payoff** (rod doubled,
  boil, hookset), good as an A/B variant.
- A thumbnail must read as **information, not decoration.** Eye-tracking research shows
  decorative images get skipped outright, so a pretty wide water shot fails no matter how
  nice the light is.
- Find candidates with a contact sheet at 2 fps over the hold-up window, then 10 fps around
  the best second. Rank by (1) eye/mouth in focus, (2) no motion blur, (3) background
  separable. **Sharpness beats moment.**
- An extended-arm hold toward the lens does double duty: forced perspective (bigger fish)
  and a pointing cue. Body pointing directs attention better than gaze, which beats graphic
  arrows, so never add an arrow to a fish that's already the subject.
- Grab from the raw source file (from 4K when available, for a sharper crop). The finished
  edit's mp4 works too, which is how retroactive thumbnails get made.
- The fish shown must be in the video. **No blood** (graphic-imagery policy; matters for
  deep-hooked fish).

## 3. Thumbnail: compose and crop

- **Punch-in crop** so the fish (+ hands) fills **40–60% of the frame.** Below ~30% it
  vanishes at 120 px; above ~70% it feels claustrophobic.
- Head near a **left-third** intersection, open water on the right for text.
- **Dead zones:** bottom-right ~290×130 px at 1920×1080 (duration badge) and the bottom
  60 px (progress bar). Keep everything critical inside the center ~87% (~1680×930).
- **Element budget:** subject + scale reference + text block ≈ 3 element types (a
  peer-reviewed inverted-U on visual complexity). Two-tier text already pushes the ceiling;
  add nothing else.
- POV footage has no face, and that's fine. A face only beats a fish when it's big, lit and
  separated; a small dim face is worth nothing. Fish + the angler's hands/arms is the right
  POV composition: the hands are the scale.

## 4. Thumbnail: two-tier text

```
   HOME POND       ← KICKER: small, white, context/location/series (branding scale)
   5 BASS          ← HEADLINE: big, yellow, the payoff, a NUMBER if one exists
```

- **≤4 words total across both lines.** Text gets ~100–150 ms of read time in a feed.
- **Headline = the hook.** Strongest category: a **specific number** (count, weight, time).
  Others that work: contradiction ("I WAS WRONG"), time constraint ("LAST CAST"), a specific
  question. **The headline must never repeat the title**; it carries information the title
  doesn't.
- **Kicker = context.** Location or series name. A word shared with the title is allowed
  *here* (branding, search anchoring), never in the headline. An unknown place name is inert
  to browse traffic, so it only works at kicker scale. It earns headline scale only when it's
  a famous water or is doing hook work ("NOBODY FISHES HERE").
- **Hierarchy mechanics** (script defaults): headline cap height ≈185 px vs kicker ≈94 px,
  about **2:1** (below 1.8:1 the hierarchy collapses); lines differ in **color** (yellow
  headline, white kicker); stroke ≈ **9.5% of each line's own cap height**; tight leading
  (~0.3× headline cap); shared left edge, never centered.
- **Colors:** yellow `#FFD400` + white with a black stroke, chosen for *luminance*: both
  stay readable over anything once stroked, and yellow rarely occurs in water footage.
  Never red text on dark (its luminance is too low). Cyan `#00C8FF` is the differentiation
  alternative (§7).
- **Contrast gates:** the script measures WCAG contrast behind the text block (headline
  ≥3:1, kicker ≥4.5:1) and auto-applies a soft dark scrim when a gate fails.
- No cursing in thumbnail text, even if the video keeps it in the audio.

## 5. Thumbnail: grade

A 3,745-video peer-reviewed study found winners are **bright + colorful** or **dark +
muted**; the ungraded overcast-water middle loses. Default is bright + colorful (the script
does this with ffmpeg):

- contrast 1.20, brightness +0.03, then **vibrance 0.45 + saturation 1.12.** Vibrance, not raw
  saturation: oversaturation now reads as fake/AI and costs trust, and real footage is the
  credibility.
- **Greens pulled down slightly** (`selectivecolor`): deepens foliage and water and lifts the
  fish and skin relatively. Fish flank and skin are both warm, so cooling the background
  separates both at once.
- Unsharp mask. Export **1920×1080 JPG, <2 MB.** Don't upscale to 4K; sharp 1080p beats mushy
  4K.

## 6. make_thumbnail.py usage

`scripts/make_thumbnail.py` does the whole recipe: frame grab → 16:9 punch-in crop → grade →
two-tier text with contrast gates → 1920×1080 JPG + `_proof.png` (320/120 px on white and
dark, plus 120 px grayscale). `--help` for details.

| Flag | Meaning |
|---|---|
| `--video FILE --time SEC` | grab the frame at SEC from FILE (or `--image FILE` to start from a still) |
| `--crop x,y,w` | 16:9 punch-in window in source pixels (top-left x, y, width), or `auto` |
| `--headline "TEXT"` | the big accent line; the payoff, a number when one exists; never the title |
| `--kicker "TEXT"` | small white context line above the headline |
| `--pos tl\|tr\|bl` | text corner (default `tr`); bottom-right is forbidden (duration badge) |
| `--no-grade` / `--no-proof` | skip the grade / proof sheet |
| `--out FILE` | output JPG (required) |

```bash
# main thumbnail
python3 scripts/make_thumbnail.py \
    --video <footage>/GX010078.MP4 --time 669.1 --crop 700,360,1220 \
    --headline "5 BASS" --kicker "HOME POND" \
    --out <output>/thumbnail.jpg

# textless variant from the same frame / from a still
python3 scripts/make_thumbnail.py --video <footage>/GX010078.MP4 --time 669.1 \
    --crop 700,360,1220 --out <scratch>/thumb_textless.jpg
python3 scripts/make_thumbnail.py --image frame.jpg --out <scratch>/thumb.jpg
```

With a 4K source, `--crop` is in 4K pixels (double the 1080p numbers). Open the `_proof.png`
every time and run the 120 px and grayscale tests by eye; the script prints the contrast
margins.

## 7. Variants, A/B and standing out

- Deliver **one uploadable `thumbnail.jpg`** in the output folder plus **2–3 A/B variants**
  (clearly named, e.g. `thumbnail_B_textless.jpg`). Record source file, timestamp, crop and
  text in the notes. Proofs and rejects stay in scratch.
- **Vary the concept, not the font:** hold-up + text / textless / mid-fight / a different
  headline category. Small channels lack the impressions for single-variable tests.
- YouTube Studio's Test & Compare takes up to 3 variants and picks the winner by **watch-time
  share, not CTR**; let it run days to two weeks.
- Re-thumbnailing an underperforming back-catalog video is often better return than the next
  upload.
- **Standing out:** a thumbnail competes with the 5–20 tiles around it, and in fishing those
  are warm grade, centered fish, yellow text (the reliable baseline). Free differentiators:
  the **dark + muted** quadrant, **textless**, an off-center subject with heavy negative
  space, a consistent **cyan** accent instead of yellow. Pick a treatment and stay consistent
  within it (consistency serves subscribers; the pattern break serves browse). Reality check:
  paste the tile into a screenshot of the actual search results it will sit in.
- **Shoot-day habits worth passing to the angler:** hold a good fish out toward the camera
  for ~2 s (the "thumbnail beat"); wear a saturated hat/shirt/PFD; snap a phone photo of the
  best fish as a sharper backup source.

## 8. Titles: rules

- **50–60 characters**, with the hook complete inside the first **30–40.** Truncation test:
  cut the title at 50 characters; if the hook is gone, rewrite. Mobile feeds and suggested
  rails (where small-channel traffic lives) truncate at ~50–60. Hard cap is 100.
- **One promise per title.** Two hooks each land at half strength. A bracketed suffix may add
  a *second, smaller* idea ("(Did Not Expect This)"), never a restatement.
- Title Case; at most **one** ALL-CAPS word. **No emoji** in long-form (a 128M-video dataset:
  −11% average views; the "+49% with emoji" number is the Shorts figure misapplied). No episode
  numbers; series identity comes from the playlist and a consistent thumbnail treatment, and
  every title must work for a first-time viewer.
- **Keywords:** 1–2 natural topic words ("pond", "bass", "kayak") are enough. Search is
  semantic; stuffing wastes characters. Browse + Suggested usually drive 50–70% of views and
  run on CTR and watch time, not keywords.
- **Characterize the place, don't name it.** An unknown proper noun is inert; the adjective or
  clause does the work ("a pond nobody fishes", "the weediest lake I've tried"). The place name
  and long-tail search terms go in the description's first line.
- **Calibration:** one **concrete anchor + one unresolved element.** Pure mystery ("You Won't
  Believe…") is too vague; pure description ("Fishing Mill Pond, Town, State") leaves
  nothing to resolve. Headline-test research found far more headlines fail by being too
  concrete (~51%) than too vague (~9%). And it's relative: check the real search row; if the
  neighbors are hyper-specific, go vaguer, and vice versa.
- **Register:** mild negative beats cheerful where honest. In 22,743 headline A/B tests each
  negative word lifted clicks ~2.3% and each positive word cost ~1.0%, but the winning register
  is **loss and mistakes, not fear** (fear words measurably *reduced* clicks).
- **Honesty is enforced by retention.** Clickbait is punished first by the recommender via the
  bounce (high CTR + low average view duration). Describe the **filmed event**, don't assert
  what the footage only implies ("something huge splashed" is safe; "a monster lives here" is a
  claim). **Every promise must be in the cut.** Re-titling later is low-risk; underperformers
  are free experiments.

## 9. Titles: frames that fit fishing trips

In rough order of fit:

1. **Discovery + characterized place:** `I Found a Pond Nobody Fishes`. The dominant winner
   in small-water fishing.
2. **First-person story:** personal pronouns correlate with higher CTR.
3. **Negation / things going wrong:** `I Was Wrong About This Pond`, `…I Couldn't Catch`.
4. **Time constraint:** `Last Cast…`, `…in 3 Hours`.

**Avoid:** listicle/how-to grammar on a trip vlog, "versus" with no real matchup,
channel-name-led titles, no-context titles like `Fishing Vlog #82`.

**Process:** write **~10 candidates** before picking (the first one is the obvious one
everyone else in the niche also wrote), spread across frames and registers, then shortlist
3–5. Verify each against the delivered cut, not the memory of the day. Respect the angler's
steer on angles: a moment that is a small part of the video can feel wrong as the whole title
even when it's attention-grabbing. Best case, pick the title before or during the shoot and
shoot to it.

## 10. Title ↔ thumbnail system

Run all four on the final pairing:

- **Cover the title**: the thumbnail alone creates curiosity.
- **Cover the thumbnail**: the title alone motivates the click.
- **Overlap audit**: zero shared information between the headline slots. The thumbnail's
  count/payoff never appears in the title; one shared word at kicker/branding scale is the max.
- **Sum test**: together they produce a third idea neither states alone. Example: thumbnail
  `5 BASS` + title `I Found a Pond Nobody Fishes` → "an overlooked pond that's actually full of
  fish."

## 11. The PACKAGING.md deliverable

Every long-form output folder gets a `PACKAGING.md` with:

1. **5–10 title suggestions** (from the ~10 drafted), each with its frame, character count,
   and an honesty check timestamped to the moment in the delivered cut that backs it. Lead
   with a recommendation; the angler picks.
2. **The thumbnail**: which file is main, what the variants test, source frame/crop/text.
3. **Description text, ready to paste:**
   - **First line = searchable location + hook**: the water's real name and area plus the
     natural topic phrase ("kayak bass fishing"). Search reads first lines hardest and viewers
     see them before "…more". Counts withheld from the title are fine here.
   - 2–4 sentences total **in the angler's own voice.** Draft from their actual on-camera lines in
     the transcripts (their words, their slang, their understatement, no marketing-speak). Then strip
     AI tells: no em dashes, no tidy triads, no colon-hinged copywriting, no
     "elevate/leverage/officially", no inspirational closer. Reread against the transcript and
     rewrite any sentence they couldn't plausibly have said.
   - **Description chapters** (`0:00 …`), titled as teases, catch chapters starting at the bite
     build-up (see [youtube-longform.md](youtube-longform.md) §11).
   - **3–5 hashtags** on their own last line (`#fishing #bassfishing #kayakfishing` plus
     optionally species/region). Up to 3 display by the title; over 60 total and all are
     ignored; `#TwoWords` not `#two words`; nothing misleading.

## 12. Checklists

**Thumbnail**
- [ ] Fish head/eye/mouth framed, in focus, no motion blur; fills 40–60% of the frame
- [ ] Reads as information, not decoration; ≤3 element types including the text block
- [ ] ≤4 words total; headline = payoff/number and carries info the title doesn't;
      location/repeated words only in the kicker
- [ ] ~2:1 cap ratio + color split; strokes scaled per line; shared left edge
- [ ] Grade lands bright + colorful (or deliberate dark + muted), vibrance not saturation
- [ ] Contrast gates passed (scrim applied if the script needed it)
- [ ] `_proof.png` reads at 120 px on white and dark, **and in grayscale**
- [ ] Nothing critical in the bottom-right 290×130 or bottom 60 px
- [ ] Truthful (fish is in the video), no blood, no cursing; 1920×1080 JPG <2 MB
- [ ] One `thumbnail.jpg` + 2–3 concept variants in the output folder

**Title**
- [ ] ~10 candidates written across frames; shortlist with a recommendation
- [ ] 50–60 chars; hook inside the first 30–40; survives the 50-char cut
- [ ] One promise; Title Case, ≤1 caps word, no emoji, no episode number
- [ ] Place characterized, not named; place name + long-tail terms in description line 1
- [ ] One concrete anchor + one open element; checked against the real search row
- [ ] Cover test both ways, overlap audit, sum test against the thumbnail
- [ ] Every promise verified at a timestamp in the delivered cut
- [ ] `PACKAGING.md` written: titles, thumbnail notes, description in the angler's voice,
      chapters, 3–5 hashtags
