#!/usr/bin/env python3
"""Check every audio cut point against detected SPEECH, not a transcript.

Why this exists: cuts were landing in the middle of words.
The old boundary check re-transcribed each segment with whisper and read its first and last
words — but whisper *reconstructs* a clipped word from context ("fis-" still prints "fish"),
so every chop passed. A raw loudness check fails the other way: pond ambient, reel noise and
splashes read as speech and everything gets flagged. This uses a voice-activity detector
(webrtcvad, aggressiveness 3) on speech-band audio, which fires on voiced speech and mostly
ignores water and gear noise.

Usage:
  check_cuts.py SEGMENTS.json [--fix FIXED.json] [--pad-out 0.35] [--pad-in 0.25]
    SEGMENTS.json: [[tag, source_audio_or_video, in_s, out_s], ...] in play order.
    A join where the next segment continues the same source at the same time (punch-in inside
    one take) is not an audio cut and is skipped.

Rules it enforces:
  OUT — no speech in the last 0.30 s before the cut. If there is, the cut is moved to
        --pad-out seconds after the end of that speech run (a run ends at >= 0.30 s of
        non-speech). That finishes the word AND the sentence it belongs to — never chop.
        Extensions > 1.5 s are marked REVIEW: they may pull in the start of the next line.
  IN  — no speech in the first 0.15 s after the cut. If there is, the cut is moved back to
        --pad-in seconds before the start of that speech run.
Prints one CHOP line per bad cut and a total ("0 chopped cut(s)" = clean; the exit code is 0
either way); --fix writes the corrected segment list.
"""
import json, subprocess, sys
import numpy as np
import webrtcvad

SR = 16000
FR = 0.030                      # webrtcvad frame length
N = int(SR * FR)


def speech_mask(src, t0, t1):
    # snap to an absolute 30 ms grid so every call frames the audio identically; otherwise a
    # noise blip can clear one check and fail the next depending on where the window started
    t0 = max(0.0, round(t0 / FR) * FR)
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", src, "-vn",
           "-ac", "1", "-ar", str(SR), "-af", "highpass=f=120,lowpass=f=3800", "-f", "s16le", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    v = webrtcvad.Vad(3)
    n = len(raw) // (2 * N)
    m = np.array([v.is_speech(raw[i * 2 * N:(i + 1) * 2 * N], SR) for i in range(n)], dtype=bool)
    # drop isolated blips (< 3 frames = 90 ms) so a reel click isn't a "word"
    out = m.copy()
    i = 0
    while i < len(m):
        if m[i]:
            j = i
            while j < len(m) and m[j]:
                j += 1
            if j - i < 3:
                out[i:j] = False
            i = j
        else:
            i += 1
    return t0, out


def fix_out(src, t, pad):
    w0, m = speech_mask(src, t - 6, t + 8)
    ix = lambda tt: int(round((tt - w0) / FR))
    a, b = ix(t - 0.30), ix(t)
    if not m[max(0, a):max(0, b)].any():
        return True, t
    need = int(0.30 / FR)
    i = max(b, 0)
    while i < len(m) - need:
        if not m[i:i + need].any():
            return False, round(w0 + i * FR + pad, 2)
        i += 1
    return False, None


def fix_in(src, t, pad):
    w0, m = speech_mask(src, t - 8, t + 6)
    ix = lambda tt: int(round((tt - w0) / FR))
    a, b = ix(t), ix(t + 0.15)
    if not m[max(0, a):b].any():
        return True, t
    need = int(0.30 / FR)
    i = a
    while i > need:
        if not m[i - need:i].any():
            return False, round(max(0.0, w0 + i * FR - pad), 2)
        i -= 1
    return False, None


def main():
    segs = json.load(open(sys.argv[1]))
    arg = lambda k, d: float(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
    pad_out, pad_in = arg("--pad-out", 0.35), arg("--pad-in", 0.25)
    fix = sys.argv[sys.argv.index("--fix") + 1] if "--fix" in sys.argv else None
    out, chops = [], 0
    for k, (tag, src, a, b) in enumerate(segs):
        prev = segs[k - 1] if k else None
        nxt = segs[k + 1] if k + 1 < len(segs) else None
        na, nb = a, b
        if not (prev and prev[1] == src and abs(prev[3] - a) < 0.02):
            ok, s = fix_in(src, a, pad_in)
            if not ok:
                chops += 1
                print(f"CHOP in  {tag:10s} {a:9.2f} -> {s}  ({(a - s) if s is not None else 0:+.2f}s earlier)")
                if s is not None:
                    na = s
        if not (nxt and nxt[1] == src and abs(nxt[2] - b) < 0.02):
            ok, s = fix_out(src, b, pad_out)
            if not ok:
                chops += 1
                if s is None:
                    print(f"CHOP out {tag:10s} {b:9.2f} -> speech runs on > 8 s, cut by hand")
                else:
                    flag = "  <-- REVIEW" if s - b > 1.5 else ""
                    print(f"CHOP out {tag:10s} {b:9.2f} -> {s}  (+{s - b:.2f}s){flag}")
                    nb = s
        out.append([tag, src, round(na, 2), round(nb, 2)])
    print(f"{chops} chopped cut(s) across {len(segs)} segments")
    if fix:
        json.dump(out, open(fix, "w"), indent=1)


if __name__ == "__main__":
    main()
