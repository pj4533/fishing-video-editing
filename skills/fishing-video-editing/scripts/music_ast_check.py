#!/usr/bin/env python3
"""Second opinion on background music: AudioSet AST classifier score for "Music" per window.

Usage (demucs/transformers venv):  ~/.demucs-venv/bin/python music_ast_check.py CLIP_or_WAV [WINDOW_S=2.5]

Prints one line per window: start time, Music score, top-3 labels; "<<<" marks Music > 0.1.
Read it as: a real song scores 0.3–0.7 sustained; clean outdoor audio 0.00–0.05. Treat > ~0.1
SUSTAINED over 2–3 s (several consecutive windows) as music. Isolated single windows at 0.1–0.15
inside loud speech are the speaker's voice, not music. music_audit.py flags that rest only on
sustained bass ("sus") with an empty/[BLANK_AUDIO] tag are usually false positives — this decides.
Never rename this file ast.py: it shadows the stdlib `ast` module and `import torch` breaks.
First run downloads the model (~350 MB) from Hugging Face.
"""
import sys, subprocess
import numpy as np
from transformers import pipeline

clf = pipeline("audio-classification", model="MIT/ast-finetuned-audioset-10-10-0.4593", top_k=None, device=-1)
f = sys.argv[1]; step = float(sys.argv[2]) if len(sys.argv) > 2 else 2.5
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                     capture_output=True).stdout
x = np.frombuffer(raw, dtype=np.float32); sr = 16000
for i in range(0, max(1, len(x) - sr), int(step * sr)):
    r = clf({"raw": x[i:i + int(step * sr)], "sampling_rate": sr})
    m = {o["label"]: o["score"] for o in r}.get("Music", 0.0)
    top = sorted(r, key=lambda o: -o["score"])[:3]
    print(f"{i / sr:7.1f} music={m:.2f}  " + ", ".join(f"{o['label']}:{o['score']:.2f}" for o in top)
          + ("  <<<" if m > 0.1 else ""), flush=True)
