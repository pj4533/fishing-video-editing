#!/usr/bin/env python3
"""Flag background music (e.g. a wedding PA across the pond) in a finished clip — copyright risk.

Usage: music_audit.py CLIP.mp4 [--work DIR] [--chunk 5]
Runs demucs (htdemucs, ~/.demucs-venv) to split the clip's audio into vocals + accompaniment, then per
chunk reports two signals on the ACCOMPANIMENT stem (bass+drums+other — the angler's voice removed):
  sus  = fraction of 100 ms frames with bass stem > -66 dBFS (sustained low end; music ≈ 1.0,
         quiet pond ≈ 0.0 — but wind on the mic also scores high, so it is never enough alone)
  tag  = what whisper small.en hears on that chunk of the accompaniment stem ("(upbeat music)",
         "♪ lyrics ♪", "[wind howling]", nothing …)
A chunk is MUSIC when the tag says music/♪/lyrics, or when sus >= 0.6 and the tag is not wind/water.
Calibrated on footage with a wedding PA playing across the water: a known song scored sus 1.0 + "(upbeat music)";
pre-wedding pond 0.0; a wind gust scored sus 1.0 + "[wind howling]" (→ not music).
Prints one line per chunk and a summary; exit code 1 if any chunk is MUSIC.
"""
import argparse, os, re, subprocess, sys, tempfile
import numpy as np

DEMUCS_PY = os.path.expanduser(os.environ.get("DEMUCS_PY", "~/.demucs-venv/bin/python"))
WHISPER = os.path.expanduser(os.environ.get("WHISPER_MODEL", "~/.whisper-models/ggml-small.en.bin"))
MUSIC_RE = re.compile(r"music|♪|singing|song|lyrics", re.I)
NOISE_RE = re.compile(r"wind|water|splash|bird|cricket|breath", re.I)  # NOT blank: faint music often transcribes as [BLANK_AUDIO]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip"); ap.add_argument("--work"); ap.add_argument("--chunk", type=float, default=5.0)
    a = ap.parse_args()
    work = a.work or tempfile.mkdtemp(prefix="music_audit_")
    os.makedirs(work, exist_ok=True)
    name = os.path.splitext(os.path.basename(a.clip))[0]
    wav = os.path.join(work, name + ".wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.clip, "-vn", "-ac", "2", "-ar", "44100", wav], check=True)
    subprocess.run([DEMUCS_PY, "-m", "demucs", "-n", "htdemucs", "-o", work, wav], check=True,
                   capture_output=True)
    sep = os.path.join(work, "htdemucs", name)
    import soundfile as sf
    st = {k: sf.read(os.path.join(sep, k + ".wav"))[0].mean(axis=1) for k in ("bass", "drums", "other")}
    sr = 44100
    acc = st["bass"] + st["drums"] + st["other"]
    fr = int(0.1 * sr)
    nb = len(st["bass"]) // fr
    bdb = np.array([20 * np.log10(np.sqrt((st["bass"][i * fr:(i + 1) * fr] ** 2).mean()) + 1e-9) for i in range(nb)])
    step = int(a.chunk * sr); flagged = []
    for c0 in range(0, len(acc), step):
        seg = acc[c0:c0 + step]
        if len(seg) < sr: break
        t0 = c0 / sr
        f0, f1 = int(t0 * 10), int((t0 + len(seg) / sr) * 10)
        sus = float((bdb[f0:f1] > -66).mean()) if f1 > f0 else 0.0
        cw = os.path.join(work, "_c.wav")
        sf.write(cw, seg, sr)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", cw, "-ar", "16000", "-ac", "1", cw + ".16.wav"], check=True)
        out = subprocess.run(["whisper-cli", "-m", WHISPER, "-f", cw + ".16.wav"], capture_output=True, text=True).stdout
        tag = " ".join(l.split("]", 1)[1].strip() for l in out.splitlines() if l.startswith("["))
        music = bool(MUSIC_RE.search(tag)) or (sus >= 0.6 and not NOISE_RE.search(tag))
        if music: flagged.append(t0)
        print(f"{t0:7.1f}-{t0 + len(seg) / sr:7.1f}  sus {sus:.2f}  {'MUSIC' if music else 'ok   '}  {tag[:70]}")
    print(f"{name}: {len(flagged)} music chunk(s)" + (f" at {', '.join(f'{t:.0f}s' for t in flagged)}" if flagged else " — clean"))
    sys.exit(1 if flagged else 0)


if __name__ == "__main__":
    main()
