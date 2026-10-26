# Setup — tools, models, Python environments

Everything runs locally (no cloud services). Written for macOS with Homebrew; Linux
equivalents are noted inline. `$SKILL` = this skill's directory.

## Contents
1. [Core command-line tools](#1-core-command-line-tools)
2. [Whisper models](#2-whisper-models)
3. [Core Python dependencies](#3-core-python-dependencies)
4. [Music / copyright venv (demucs + AST classifier)](#4-music--copyright-venv-demucs--ast-classifier)
5. [Wildlife venv (detector + tracker)](#5-wildlife-venv-detector--tracker)
6. [RNNoise model (wind filter)](#6-rnnoise-model-wind-filter)
7. [Fonts](#7-fonts)
8. [Which interpreter runs which script](#8-which-interpreter-runs-which-script)
9. [Verify the install](#9-verify-the-install)
10. [Linux notes](#10-linux-notes)

---

## 1. Core command-line tools

| Tool | Why | macOS | Linux (Debian/Ubuntu) |
|---|---|---|---|
| `ffmpeg` + `ffprobe` | every cut, crop, frame grab, filter, encode | `brew install ffmpeg` | `sudo apt install ffmpeg` |
| `whisper-cli` (whisper.cpp) | local speech-to-text with timestamps | `brew install whisper-cpp` | build from source (§10) |
| `python3` (3.10+) | helper scripts | `brew install python` | `sudo apt install python3 python3-venv` |

The ffmpeg build must include these filters (Homebrew's and Debian's do):
`drawtext` (libfreetype), `arnndn`, `silencedetect`, `drawgrid`, `tile`, `sendcmd`.
Check with `ffmpeg -hide_banner -filters | grep -E " (drawtext|arnndn|drawgrid|sendcmd) "`.

ImageMagick is **not** needed — contact sheets are built with ffmpeg's `tile` filter.

## 2. Whisper models

whisper.cpp ships no model files. Put two English models in `~/.whisper-models/`
(the scripts default there; override with `$WHISPER_MODEL`):

```bash
mkdir -p ~/.whisper-models && cd ~/.whisper-models
curl -L -o ggml-base.en.bin  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
curl -L -o ggml-small.en.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin
```

- `ggml-base.en.bin` (~148 MB) — fast first pass on clear speech.
- `ggml-small.en.bin` (~488 MB) — use for anything buried under water/wind/reel noise,
  every quiet clip, and every re-transcription of a short isolated window. The caption and
  music-audit scripts default to it.
- `medium.en` exists and is more accurate again, but base + small have been enough.

## 3. Core Python dependencies

Used by `build_edit.py`, `check_cuts.py`, `check_av_sync.py`, `concat_av.py`,
`fishtrack2.py`, `burn_captions.py`, `make_thumbnail.py`, `voice_isolate.py`,
`music_audit.py` (driver side), `speech_islands.py`, `transcribe_islands.py`.

| Package | Used by |
|---|---|
| `numpy` | almost everything (tracking, envelopes, sync check) |
| `webrtcvad` | `check_cuts.py` (voice-activity detection at every cut) |
| `soundfile` | `voice_isolate.py`, `music_audit.py` |
| `Pillow` | `make_thumbnail.py` (also `wildlife_reframe.py`, in its own venv) |

Homebrew Python refuses global `pip install` (PEP 668), so use a venv:

```bash
python3 -m venv ~/.fishing-video-venv
~/.fishing-video-venv/bin/pip install numpy webrtcvad soundfile Pillow
# activate it before running the scripts, or call ~/.fishing-video-venv/bin/python directly
```

If `webrtcvad` fails to compile (common on Python 3.12+ without build tools), install the
prebuilt fork instead — same import name: `pip install webrtcvad-wheels`.
If `import webrtcvad` fails with `No module named 'pkg_resources'` (venvs on Python 3.12+
ship without setuptools), run `pip install "setuptools<81"` in the venv, or use
`webrtcvad-wheels`.

`opencv-python` is **not** needed for the fishing scripts (`fishtrack2.py` is pure
numpy NCC). OpenCV is only used by the wildlife scripts, which get their own venv (§5).

## 4. Music / copyright venv (demucs + AST classifier)

Needed only when a clip may carry background music (a PA across the water, a passing
boat's radio) — `music_audit.py`, `voice_isolate.py`, and the AST "Music" check.

```bash
python3 -m venv --system-site-packages ~/.demucs-venv
~/.demucs-venv/bin/pip install demucs transformers soundfile
```

- `--system-site-packages` lets the venv reuse an already-installed `torch`; if there is
  none, `pip install demucs` pulls one in (large download).
- demucs downloads the `htdemucs` weights on first run.
- The AST classifier `MIT/ast-finetuned-audioset-10-10-0.4593` downloads from Hugging Face
  on first use of the `transformers` pipeline (~350 MB, cached in `~/.cache/huggingface`).
- The scripts find this interpreter at `~/.demucs-venv/bin/python`; override with
  `$DEMUCS_PY`.

## 5. Wildlife venv (detector + tracker)

Needed only for wildlife zoom clips from 4K footage (see
[wildlife-zoom.md](wildlife-zoom.md)). Imports across `wildlife_*.py`: `cv2` (with the
contrib `TrackerVit`), `numpy`, `scipy`, `PIL`, `ultralytics`, `sahi`, `torch`.

```bash
python3 -m venv --system-site-packages ~/.wildlife-venv
~/.wildlife-venv/bin/pip install ultralytics sahi opencv-contrib-python-headless scipy Pillow
```

- `opencv-contrib-python-headless` is what ships `cv2.TrackerVit`. Don't also install
  plain `opencv-python` in this venv — the two fight over the `cv2` package.
- A numpy-version warning during install is harmless.

Model weights go in `~/.wildlife-models/` (override with `$WILDLIFE_MODELS`):

```bash
mkdir -p ~/.wildlife-models && cd ~/.wildlife-models
curl -L -o yolo11s.pt \
  https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11s.pt
curl -L -o object_tracking_vittrack_2023sep.onnx \
  https://huggingface.co/opencv/object_tracking_vittrack/resolve/main/object_tracking_vittrack_2023sep.onnx
```

Optional open-vocabulary detector for mammals (`wildlife_scan.py --prompt "beaver,otter"`):
YOLOE `yoloe-11s-seg.pt`. It auto-downloads a ~600 MB MobileCLIP text encoder into the
**current directory**, so `cd ~/.wildlife-models` before the first run.

Run detector passes one at a time. Two GPU models plus whisper on a 16 GB machine pushed
it deep into swap.

## 6. RNNoise model (wind filter)

ffmpeg's `arnndn` filter needs a trained model file. Use the "std" model from
[richardpl/arnndn-models](https://github.com/richardpl/arnndn-models). It isn't redistributed here,
so download it once into the skill's `scripts/` folder, where every recipe expects it:

```bash
curl -L -o "$SKILL/scripts/rnnoise_std.rnnn" \
  https://raw.githubusercontent.com/richardpl/arnndn-models/master/std.rnnn
```

ffmpeg loads it by path (`arnndn=m=$SKILL/scripts/rnnoise_std.rnnn`). It's only needed for windy footage. Recipe:
[cookbook.md §17](cookbook.md#17-wind-noise-filter).

## 7. Fonts

| Use | macOS default | Linux alternative |
|---|---|---|
| Burned captions (`burn_captions.py`) | `/System/Library/Fonts/Supplemental/Arial Bold.ttf` | `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf` (`fonts-dejavu-core`) or Liberation Sans Bold (`fonts-liberation`) |
| Thumbnails (`make_thumbnail.py`) | Impact → Arial Black → Arial Bold (first found) | set `$THUMB_FONT` (or edit `FONT_CANDIDATES`) |
| Wildlife `--mark` labels (`wildlife_reframe.py`) | Arial Bold | set `$CAPTION_FONT` |
| Ad-hoc `drawtext` (labels, cards) | same Arial Bold path | same DejaVu path |

`burn_captions.py` reads `$CAPTION_FONT`, so on Linux:
`export CAPTION_FONT=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`.
A wider font fits fewer characters per line — re-check the caption width limit
([cookbook.md §14](cookbook.md#14-burned-captions)).

## 8. Which interpreter runs which script

| Scripts | Interpreter |
|---|---|
| `build_edit.py`, `concat_av.py`, `check_av_sync.py`, `check_cuts.py`, `fishtrack2.py`, `burn_captions.py`, `make_thumbnail.py`, `speech_islands.py`, `transcribe_islands.py` | core venv (§3) |
| `music_audit.py`, `voice_isolate.py` | core venv — they shell out to `~/.demucs-venv/bin/python` for demucs themselves |
| `music_ast_check.py` (AST "Music" check) | `~/.demucs-venv/bin/python` (has torch + transformers) |
| `wildlife_scan.py`, `wildlife_motion.py`, `wildlife_track.py`, `wildlife_reframe.py`, `wildlife_speck.py`, `wildlife_flock.py` | `~/.wildlife-venv/bin/python` — system Python has no `sahi` |
| `keyframe_grid.sh` | any shell (ffmpeg only) |

## 9. Verify the install

```bash
ffmpeg -version | head -1
ffmpeg -hide_banner -filters | grep -cE " (drawtext|arnndn|silencedetect|drawgrid|tile|sendcmd) "   # expect 6
whisper-cli --help >/dev/null 2>&1 && echo "whisper-cli OK"
ls -la ~/.whisper-models/ggml-base.en.bin ~/.whisper-models/ggml-small.en.bin
~/.fishing-video-venv/bin/python -c "import numpy, webrtcvad, soundfile, PIL; print('core OK')"
ls -la "$SKILL/scripts/rnnoise_std.rnnn"
ls -la "/System/Library/Fonts/Supplemental/Arial Bold.ttf"        # or your $CAPTION_FONT

# optional: music/copyright tools
~/.demucs-venv/bin/python -c "import demucs, transformers, soundfile; print('demucs OK')"

# optional: wildlife tools
~/.wildlife-venv/bin/python -c "import cv2, ultralytics, sahi, scipy; cv2.TrackerVit_Params(); print('wildlife OK')"
ls -la ~/.wildlife-models/

# end-to-end whisper smoke test on any clip
ffmpeg -y -t 20 -i <footage_dir>/<clip>.MP4 -ar 16000 -ac 1 -c:a pcm_s16le /tmp/smoke.wav -loglevel error
whisper-cli -m ~/.whisper-models/ggml-base.en.bin -f /tmp/smoke.wav 2>/dev/null | head
```

## 10. Linux notes

- **whisper.cpp:** `git clone https://github.com/ggml-org/whisper.cpp && cd whisper.cpp &&
  cmake -B build && cmake --build build -j --config Release`, then put
  `build/bin/whisper-cli` on your `PATH`. Same model files and flags.
- **Hardware decode:** `build_edit.py` and the `wildlife_*.py` decoders use
  `-hwaccel videotoolbox` on macOS and no hardware decode elsewhere. Override with
  `export FFMPEG_HWACCEL=cuda` (or `vaapi`, or `none`). In any cookbook command that writes
  `-hwaccel videotoolbox`, drop the pair or use `-hwaccel auto` on Linux.
- **torch:** the wildlife and demucs venvs use Apple's MPS GPU on macOS; on Linux they use
  CUDA if available, otherwise CPU (much slower for 4K detection — sample fewer fps).
- **Fonts:** see §7; set `CAPTION_FONT`.
- **Shell:** commands are written for zsh/bash. macOS ships bash 3.2 (no `declare -A`);
  Linux bash 5 does not have that limit, but the commands avoid it anyway.
