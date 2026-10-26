#!/usr/bin/env python3
"""Replace the soundtrack inside given time ranges with the demucs VOICE stem (music removed).

For background music bleeding into a clip (e.g. a wedding PA across the water) — copyright
risk on TikTok/YouTube. Run scripts/music_audit.py first to find the ranges; put range edges on the
edit's cut frames so the change of audio texture lands on a hard cut, never mid-shot.

Usage: voice_isolate.py IN.mp4 OUT.mp4 --ranges "209.776:233.934[,a:b...]" [--work DIR]
- Video is stream-copied; audio is decoded once at 48 kHz, each range is separated by demucs
  (htdemucs, ~/.demucs-venv, 1 s margin either side so the model has context), the vocals stem is
  resampled to 48 kHz and written over exactly [a, b) sample-for-sample, AAC re-encoded once.
- Sung vocals in the music survive in the voice stem — listen/inspect (music_audit.py on OUT).
"""
import argparse, os, subprocess, tempfile
import numpy as np, soundfile as sf

DEMUCS_PY = os.path.expanduser(os.environ.get("DEMUCS_PY", "~/.demucs-venv/bin/python"))
SR = 48000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("out"); ap.add_argument("--ranges", required=True)
    ap.add_argument("--work")
    a = ap.parse_args()
    work = a.work or tempfile.mkdtemp(prefix="voice_iso_")
    os.makedirs(work, exist_ok=True)
    full = os.path.join(work, "full.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.inp, "-vn", "-ar", str(SR), "-ac", "2", full], check=True)
    audio, _ = sf.read(full, always_2d=True)
    for k, r in enumerate(a.ranges.split(",")):
        t0, t1 = map(float, r.split(":"))
        m0, m1 = max(0.0, t0 - 1.0), min(len(audio) / SR, t1 + 1.0)
        piece = os.path.join(work, f"piece{k}.wav")
        sf.write(piece, audio[int(round(m0 * SR)):int(round(m1 * SR))], SR)
        subprocess.run([DEMUCS_PY, "-m", "demucs", "-n", "htdemucs", "--two-stems", "vocals", "-o", work, piece],
                       check=True, capture_output=True)
        voc = os.path.join(work, "htdemucs", f"piece{k}", "vocals.wav")
        voc48 = voc.replace(".wav", "_48k.wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", voc, "-ar", str(SR), "-ac", "2", voc48], check=True)
        v, _ = sf.read(voc48, always_2d=True)
        s0, s1 = int(round(t0 * SR)), int(round(t1 * SR))
        o0 = s0 - int(round(m0 * SR))
        seg = v[o0:o0 + (s1 - s0)]
        audio[s0:s0 + len(seg)] = seg
        print(f"range {t0:.3f}-{t1:.3f}: replaced {len(seg)} samples with the voice stem")
    fixed = os.path.join(work, "fixed.wav")
    sf.write(fixed, audio, SR)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.inp, "-i", fixed, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", a.out], check=True)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
