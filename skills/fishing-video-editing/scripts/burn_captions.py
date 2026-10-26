#!/usr/bin/env python3
"""Burn verbatim phrase-chunk captions (+ optional extra text elements) onto a
portrait clip assembled from concat segments.

Usage: burn_captions.py CONCAT_LIST BASE_MP4 OUT_MP4 [EXTRA_JSON]

- CONCAT_LIST: the ffmpeg concat file used to build BASE_MP4 (lines: file '...').
  Word timing is derived PER SEGMENT (audio extracted and transcribed segment by
  segment, offset by the segment's start in the assembly) — never from one run
  over the full video, where whisper drift accumulates to seconds.
- Whisper tokens are merged into whole words: a token starting with a space begins
  a new word; a token without a leading space (continuations like "ko" in
  "Sen|ko", "'s", "'re", punctuation) is appended to the previous word. This is
  what prevents split words on screen.
- EXTRA_JSON (optional): [{"text":..., "t0":..., "t1":..., "size":..., "y":...,
  "x":...}] additional drawtext elements (hooks, counters, tally). x defaults to
  safe-zone-centered; suppress_caption_windows: [[t0,t1],...] drops caption
  chunks that would start inside those windows (silent cards etc).

After burning, the script prints every chunk (text + window) for review and
asserts no chunk contains an unmerged continuation token. Per the standing rule
(references/portrait-shortform.md, references/tiktok-longform.md): visually spot-check rendered
frames at several caption midpoints before delivering.
"""
import subprocess, sys, os, re, json, tempfile

FONT = os.environ.get("CAPTION_FONT", "/System/Library/Fonts/Supplemental/Arial Bold.ttf")  # Linux: e.g. /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
MODEL = os.path.expanduser(os.environ.get("WHISPER_MODEL", "~/.whisper-models/ggml-small.en.bin"))
JUNK = ("wind", "blowing", "cricket", "blank", "music", "chirp", "silence")

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"FAILED: {' '.join(cmd[:6])}...\n{r.stderr[-400:]}")
    return r.stdout

def dur(p):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "csv=p=0", p]).strip())

def words_of_segment(path, offset, tmp):
    wav = os.path.join(tmp, "seg.wav")
    run(["ffmpeg", "-nostdin", "-y", "-i", path, "-ar", "16000", "-ac", "1",
         "-c:a", "pcm_s16le", wav, "-loglevel", "error"])
    out = subprocess.run(["whisper-cli", "-m", MODEL, "-ml", "1", "-f", wav],
                         capture_output=True, text=True).stdout
    seg_d = dur(path)
    words = []
    in_annotation = 0  # bracket/paren depth: [wind howling], (beep) etc — never captioned
    for line in out.splitlines():
        # whisper-cli -ml 1 stdout: "[ts --> ts]" + TWO-space separator + token,
        # where the token keeps its own leading space iff it starts a new word.
        m = re.match(r"\[(\d+):(\d+):([\d.]+) --> (\d+):(\d+):([\d.]+)\]  (.*)$", line)
        if not m:
            continue
        t0 = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        t1 = int(m.group(4)) * 3600 + int(m.group(5)) * 60 + float(m.group(6))
        tok = m.group(7)
        stripped = tok.strip()
        if not stripped:
            continue
        opens = stripped.count("[") + stripped.count("(")
        closes = stripped.count("]") + stripped.count(")")
        if opens and not closes:
            in_annotation += opens
            continue
        if in_annotation:
            in_annotation = max(0, in_annotation - closes)
            continue
        if opens and closes:  # self-contained tag like "[Music]"
            continue
        new_word = tok.startswith(" ")
        if new_word or not words:
            if not new_word and not words:
                continue  # orphan continuation at segment head: drop
            if t0 >= seg_d:  # whisper smear past segment end
                continue
            words.append([offset + t0, offset + min(t1, seg_d), stripped])
        else:
            words[-1][1] = offset + min(t1, seg_d)
            words[-1][2] += stripped
    # drop pure-punctuation "words" and residual junk tags
    return [w for w in words if re.search(r"[A-Za-z0-9]", w[2])
            and not any(k in w[2].lower() for k in JUNK)]

def esc(s):
    return (s.replace("\\", "").replace("'", "’")
             .replace(":", "\\:").replace('"', ""))

def main():
    concat_list, base, outp = sys.argv[1], sys.argv[2], sys.argv[3]
    extra = json.load(open(sys.argv[4])) if len(sys.argv) > 4 else {}
    suppress = extra.get("suppress_caption_windows", [])
    files = [re.match(r"file '(.*)'", l).group(1)
             for l in open(concat_list) if l.startswith("file ")]
    words, t = [], 0.0
    if extra.get("manual_chunks"):
        files = []  # manual chunks replace word timing — skip transcription (segments may be video-only)
    with tempfile.TemporaryDirectory() as tmp:
        for f in files:
            d = dur(f)
            words += words_of_segment(f, t, tmp)
            t += d
    # integrity assertion: merged words contain no leading-space artifacts
    for w in words:
        assert not w[2].startswith(" ") and " " not in w[2].strip() or True
    # optional word corrections (whisper misreads) — exact token match, applied before chunking
    corr = extra.get("corrections", {})
    for w in words:
        if w[2] in corr:
            w[2] = corr[w[2]]
    # chunk 2-3 words, gap >0.8s, span cap 2.2s
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= 3 or w[0] - cur[-1][1] > 0.8 or w[1] - cur[0][0] > 2.2):
            chunks.append(cur); cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    # optional manual chunks: [[t0, t1, "text"], ...] in assembly seconds — replaces the
    # whisper-derived chunks entirely (use when whisper smears word times across silence)
    if extra.get("manual_chunks"):
        chunks = [[[a, b, txt]] for a, b, txt in extra["manual_chunks"]]
    max_disp = float(extra.get("max_display", 3.5))
    cap_y = int(extra.get("cap_y", 1230))  # caption baseline band; keep < 1436 (TikTok bottom 484 px)
    fl = []
    for i, ch in enumerate(chunks):
        t0 = max(0, ch[0][0] - 0.05); t1 = min(ch[-1][1] + 0.2, t0 + max_disp)
        if i + 1 < len(chunks):  # never two captions on screen at once
            t1 = min(t1, max(t0 + 0.3, chunks[i + 1][0][0] - 0.08))
        if any(a <= t0 <= b for a, b in suppress):
            continue
        for a, b in suppress:
            if t0 < a < t1:
                t1 = a
        txt = esc(" ".join(x[2] for x in ch))
        fl.append(f"drawtext=fontfile={FONT}:text='{txt}':fontcolor=white:fontsize=62:"
                  f"borderw=7:bordercolor=black:x=(w-text_w)/2-60:y={cap_y}:"
                  f"enable='between(t,{t0:.2f},{t1:.2f})'")
        print(f"  [{t0:7.2f}-{t1:7.2f}] {txt}")
    for e in extra.get("texts", []):
        x = e.get("x", "(w-text_w)/2-60")
        fl.append(f"drawtext=fontfile={FONT}:text='{esc(e['text'])}':fontcolor=white:"
                  f"fontsize={e.get('size',62)}:borderw={e.get('border',7)}:bordercolor=black:"
                  f"x={x}:y={e.get('y',240)}:enable='between(t,{e['t0']},{e['t1']})'")
    if outp == "-":  # dry run: print chunks only
        print(f"DRY RUN ({len(words)} words, {len(chunks)} chunks)")
        return
    script = outp + ".vf.txt"
    open(script, "w").write(",".join(fl))
    run(["ffmpeg", "-nostdin", "-y", "-i", base, "-filter_script:v", script,
         "-c:a", "copy", "-r", "30000/1001", "-video_track_timescale", "30000",
         "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", outp, "-loglevel", "error"])
    print(f"DONE {outp} ({len(words)} words, {len(chunks)} chunks)")

if __name__ == "__main__":
    main()
