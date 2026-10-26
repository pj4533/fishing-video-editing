#!/usr/bin/env python3
"""Make a YouTube thumbnail from a video frame — a reproducible recipe.

Process (rationale in references/thumbnails-titles.md):
  1. Grab a frame from the source video at a given time (or start from an image).
  2. Punch-in crop (16:9) so the fish/subject fills 40-60% of the frame.
  3. Grade via ffmpeg: contrast + VIBRANCE (not raw saturation — plastic-look
     tell), slight green pull-down (deepens foliage, lifts the fish), unsharp.
     Target the "bright + colorful" quadrant — mid-brightness/mid-sat loses.
  4. Two-tier text: small white KICKER (location/series — branding scale) above
     a big accent-color HEADLINE (the payoff — a number when one exists).
     Cap-height ratio ~2:1, per-line stroke ~9.5% of cap height, shared left
     edge. Auto dark scrim behind the block when measured WCAG contrast fails
     the gates (headline 3:1, kicker 4.5:1). Never bottom-right (duration
     badge ~290x130) or bottom 60 px (progress bar).
  5. Export 1920x1080 JPEG <2 MB + proof sheet: 320/120 px on white & dark,
     plus 120 px GRAYSCALE (luminance-separation gate — if the subject melts
     into the background in grey, the design fails in the feed).

Headline text must NOT repeat the video title (a title word may appear in the
kicker, at branding scale). Total words across both lines <= 4.

Examples:
  python3 scripts/make_thumbnail.py \
      --video <footage_dir>/GX010078.MP4 --time 669.1 --crop 700,360,1220 \
      --headline "5 BASS" --kicker "NEW POND" \
      --out <output_dir>/thumbnail.jpg

  # textless variant / from a still image
  python3 scripts/make_thumbnail.py --image frame.jpg --out thumb.jpg
"""

import argparse
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT_W, OUT_H = 1920, 1080

FONT_CANDIDATES = [
    *([os.environ["THUMB_FONT"]] if os.environ.get("THUMB_FONT") else []),
    "/System/Library/Fonts/Supplemental/Impact.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux fallback
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]

# --- encodable spec (research round 2, part 4) --------------------------------
HEADLINE_SIZE = 260          # font px -> cap height ~185 (15-20% of frame)
KICKER_SIZE = 130            # ~2:1 cap-height ratio; below 1.8 hierarchy collapses
LEADING_RATIO = 0.30         # gap between lines, x headline cap height
STROKE_CAP_RATIO = 0.095     # stroke = 9.5% of the line's cap height
ACCENT = "#FFD400"           # yellow: rare in pond footage, never collides
NEUTRAL = "#FFFFFF"
PAD = 70                     # keeps text inside center ~87% safe area
MIN_CONTRAST_HEADLINE = 3.0  # WCAG large-text gate
MIN_CONTRAST_KICKER = 4.5    # WCAG normal-text gate
# grade: bright+colorful quadrant (Koh & Cui — never land in the middle)
GRADE_VF = ("eq=contrast=1.20:brightness=0.03:gamma=1.02,"
            "vibrance=intensity=0.45,eq=saturation=1.12,"
            "selectivecolor=greens=0 0 -0.15 0.05,"
            "unsharp=luma_msize_x=5:luma_msize_y=5:luma_amount=1.0")


def run_ffmpeg(args):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *args], check=True)


def grab_frame(video: str, t: float) -> Image.Image:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp = f.name
    try:
        run_ffmpeg(["-ss", str(t), "-i", os.path.expanduser(video),
                    "-frames:v", "1", tmp])
        with Image.open(tmp) as img:
            return img.convert("RGB")
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def parse_crop(spec: str, src_w: int, src_h: int):
    """"x,y,w" -> 16:9 box (h derived). "auto" -> full frame."""
    if spec == "auto":
        return (0, 0, src_w, src_h)
    x, y, w = (int(v) for v in spec.split(","))
    h = round(w * 9 / 16)
    if x + w > src_w or y + h > src_h:
        sys.exit(f"crop {x},{y},{w}x{h} exceeds source {src_w}x{src_h}")
    return (x, y, x + w, y + h)


def grade(im: Image.Image) -> Image.Image:
    """Round-2 grade, via ffmpeg (vibrance/selectivecolor aren't in PIL)."""
    src = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    dst = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    try:
        im.save(src)
        run_ffmpeg(["-i", src, "-vf", GRADE_VF, dst])
        with Image.open(dst) as out:
            return out.convert("RGB")
    finally:
        for p in (src, dst):
            if os.path.exists(p):
                os.unlink(p)


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    sys.exit("no usable font found; edit FONT_CANDIDATES")


def rel_luminance(rgb):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(l1, l2):
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def region_mean_luminance(im, box):
    box = (max(box[0], 0), max(box[1], 0),
           min(box[2], im.width), min(box[3], im.height))
    stat = im.crop(box).resize((32, 32)).getdata()
    return sum(rel_luminance(p) for p in stat) / len(list(stat))


def draw_text(im: Image.Image, headline: str, kicker: str | None, pos: str):
    """Kicker (small, white) above headline (big, accent). Shared left edge.
    Both tiers shrink together if the widest line would leave the safe area."""
    draw = ImageDraw.Draw(im)
    h_size, k_size = HEADLINE_SIZE, KICKER_SIZE
    while h_size > 120:
        f = load_font(h_size)
        w = draw.textbbox((0, 0), headline, font=f,
                          stroke_width=round(h_size * 0.07))[2]
        if w <= OUT_W - 2 * PAD:
            break
        h_size = round(h_size * 0.93)
        k_size = round(k_size * 0.93)
    h_font, k_font = load_font(h_size), load_font(k_size)
    lines = []  # (text, font, fill, stroke_w, w, h, ox, oy, min_contrast)
    if kicker:
        s = max(6, round(k_size * 0.72 * STROKE_CAP_RATIO))
        b = draw.textbbox((0, 0), kicker, font=k_font, stroke_width=s)
        lines.append([kicker, k_font, NEUTRAL, s, b[2] - b[0], b[3] - b[1],
                      b[0], b[1], MIN_CONTRAST_KICKER])
    s = max(10, round(h_size * 0.72 * STROKE_CAP_RATIO))
    b = draw.textbbox((0, 0), headline, font=h_font, stroke_width=s)
    lines.append([headline, h_font, ACCENT, s, b[2] - b[0], b[3] - b[1],
                  b[0], b[1], MIN_CONTRAST_HEADLINE])

    gap = round(h_size * 0.72 * LEADING_RATIO)
    block_w = max(l[4] for l in lines)
    block_h = sum(l[5] for l in lines) + gap * (len(lines) - 1)
    x0 = PAD if pos.endswith("l") else OUT_W - PAD - block_w
    y0 = PAD if pos.startswith("t") else OUT_H - PAD - block_h - 60

    # contrast gates: measure what's behind the block; scrim if any line fails
    pad = 30
    block_box = (x0 - pad, y0 - pad, x0 + block_w + pad, y0 + block_h + pad)
    bg_lum = region_mean_luminance(im, block_box)
    worst = min(contrast_ratio(rel_luminance(
        tuple(int(l[2].lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
        if l[2].startswith('#') else (255, 255, 255)), bg_lum) - l[8]
        for l in lines)
    if worst < 0:
        scrim = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(scrim)
        sd.rounded_rectangle(block_box, radius=40, fill=(0, 0, 0, 110))
        scrim = scrim.filter(ImageFilter.GaussianBlur(25))
        im.paste(Image.alpha_composite(im.convert("RGBA"), scrim)
                 .convert("RGB"), (0, 0))
        draw = ImageDraw.Draw(im)
        print(f"contrast gate failed by {-worst:.2f} vs bg L={bg_lum:.3f} "
              f"-> applied scrim")
    else:
        print(f"contrast gates passed (margin {worst:.2f}, bg L={bg_lum:.3f})")

    y = y0
    for text, font, fill, stroke_w, w, h, ox, oy, _ in lines:
        # soft drop shadow for separation on busy water
        shadow = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(shadow).text((x0 - ox + 6, y - oy + 6), text, font=font,
                                    fill=(0, 0, 0, 140), stroke_width=stroke_w,
                                    stroke_fill=(0, 0, 0, 140))
        shadow = shadow.filter(ImageFilter.GaussianBlur(8))
        im.paste(Image.alpha_composite(im.convert("RGBA"), shadow)
                 .convert("RGB"), (0, 0))
        draw = ImageDraw.Draw(im)
        draw.text((x0 - ox, y - oy), text, font=font, fill=fill,
                  stroke_width=stroke_w, stroke_fill="black")
        y += h + gap
    return im


def save_proof(im: Image.Image, out: str):
    """320/120px on white & dark + 120px grayscale (luminance gate)."""
    sheet = Image.new("RGB", (740, 420))
    d = ImageDraw.Draw(sheet)
    d.rectangle((0, 0, 369, 420), fill="white")
    d.rectangle((370, 0, 740, 420), fill="#0f0f0f")
    for x0 in (10, 390):
        sheet.paste(im.resize((320, 180), Image.LANCZOS), (x0, 20))
        sheet.paste(im.resize((120, 68), Image.LANCZOS), (x0, 220))
        grey = im.convert("L").convert("RGB").resize((120, 68), Image.LANCZOS)
        sheet.paste(grey, (x0, 310))
    proof = os.path.splitext(out)[0] + "_proof.png"
    sheet.save(proof)
    print(f"proof sheet (320/120px on white+dark, 120px grayscale): {proof}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--video", help="source video (used with --time)")
    src.add_argument("--image", help="start from an image instead")
    ap.add_argument("--time", type=float, help="timestamp in seconds (with --video)")
    ap.add_argument("--crop", default="auto",
                    help='"x,y,w" 16:9 punch-in window in source pixels, or "auto"')
    ap.add_argument("--headline", help="the payoff — big accent line, "
                    "a NUMBER when one exists; must not repeat the title")
    ap.add_argument("--kicker", help="small white context line above the "
                    "headline (location/series — branding scale)")
    ap.add_argument("--pos", default="tr", choices=["tl", "tr", "bl"],
                    help="text corner; br is forbidden (duration badge)")
    ap.add_argument("--no-grade", action="store_true")
    ap.add_argument("--no-proof", action="store_true")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    if args.video:
        if args.time is None:
            sys.exit("--video requires --time")
        im = grab_frame(args.video, args.time)
    else:
        im = Image.open(os.path.expanduser(args.image)).convert("RGB")

    im = im.crop(parse_crop(args.crop, *im.size)).resize((OUT_W, OUT_H),
                                                         Image.LANCZOS)
    if not args.no_grade:
        im = grade(im)

    if args.headline:
        total_words = len(args.headline.split()) + \
            len(args.kicker.split() if args.kicker else [])
        if total_words > 4:
            sys.exit(f"{total_words} words across both lines — hard cap is 4")
        im = draw_text(im, args.headline.upper(),
                       args.kicker.upper() if args.kicker else None, args.pos)
    elif args.kicker:
        sys.exit("--kicker requires --headline")

    out = os.path.expanduser(args.out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    q = 92
    while True:
        im.save(out, quality=q)
        if os.path.getsize(out) <= 2 * 1024 * 1024 or q <= 70:
            break
        q -= 5
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB, q={q})")

    if not args.no_proof:
        save_proof(im, out)


if __name__ == "__main__":
    main()
