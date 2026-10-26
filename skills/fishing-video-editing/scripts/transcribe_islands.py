#!/usr/bin/env python3
"""Transcribe each speech island in a window on its own — accurate phrase timing for cuts/captions.

Usage: transcribe_islands.py WAV START END [THRESH_DB=-35] [--merge 0.7]

Islands closer than --merge seconds are joined (one phrase), then each is cut out (±0.1 s, padded
with 1 s of silence) and transcribed alone with whisper-cli small.en. Isolation kills the
hallucination loops whisper falls into over long quiet stretches, and the island edges are real
audio boundaries, so you get "start-end: text" lines you can cut on and caption from.
Islands that print only "(water splashing)" etc. are noise, not speech.
Model: $WHISPER_MODEL or ~/.whisper-models/ggml-small.en.bin.
"""
import argparse, os, subprocess, tempfile, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from speech_islands import islands

ap = argparse.ArgumentParser()
ap.add_argument("wav"); ap.add_argument("start", type=float); ap.add_argument("end", type=float)
ap.add_argument("thresh", nargs="?", default="-35"); ap.add_argument("--merge", type=float, default=0.7)
a = ap.parse_args()
model = os.path.expanduser(os.environ.get("WHISPER_MODEL", "~/.whisper-models/ggml-small.en.bin"))
merged = []
for s, e in islands(a.wav, a.start, a.end, a.thresh):
    if merged and s - merged[-1][1] < a.merge:
        merged[-1][1] = e
    else:
        merged.append([s, e])
tmp = tempfile.mkdtemp()
for s, e in merged:
    if e - s < 0.25:
        continue
    w = os.path.join(tmp, "p.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(max(0, s - 0.1)), "-to", str(e + 0.1),
                    "-i", a.wav, "-af", "apad=pad_dur=1", w])
    t = subprocess.run(["whisper-cli", "-m", model, "-f", w, "-nt"], capture_output=True, text=True).stdout
    print(f"{s:8.2f}-{e:8.2f}: {' '.join(t.split())}", flush=True)
