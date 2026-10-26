#!/usr/bin/env python3
"""Print speech "islands" (non-silent runs) in a window of a WAV, in source seconds.

Usage: speech_islands.py WAV START END [THRESH_DB=-35]

Why: whisper word times drift (100 ms to SECONDS over splashing), so cut points and caption
timing come from the audio itself. A highpass at 150 Hz keeps reel/hull rumble out; silencedetect
finds the gaps; everything between gaps longer than 0.3 s is an island. Splashes also make
islands, so pair this with transcribe_islands.py to see which islands are words.
Lower THRESH_DB (e.g. -40) on quiet audio, raise it (-30) in wind.
"""
import re, subprocess, sys

def islands(wav, a, b, th="-35", min_sil=0.3):
    o = subprocess.run(["ffmpeg", "-ss", str(a), "-t", str(b - a), "-i", wav, "-af",
                        f"highpass=f=150,silencedetect=n={th}dB:d={min_sil}", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    ev = [(m.group(1), float(m.group(2)) + a) for m in re.finditer(r"silence_(start|end): ([0-9.]+)", o)]
    out, cur, in_speech = [], a, True
    for k, t in ev:
        if k == "start":
            if t - cur > 0.12:
                out.append((cur, t))
            in_speech = False
        else:
            cur, in_speech = t, True
    if in_speech and b - cur > 0.12:
        out.append((cur, b))
    return out

if __name__ == "__main__":
    wav, a, b = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    th = sys.argv[4] if len(sys.argv) > 4 else "-35"
    for s, e in islands(wav, a, b, th):
        print(f"speech {s:8.2f} - {e:8.2f}  ({e - s:.2f})")
