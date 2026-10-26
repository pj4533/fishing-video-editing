#!/usr/bin/env python3
"""Assemble a hard-cut edit so the audio is cut EXACTLY where the video is cut.

Why: a long-form edit once drifted up to ~1 s out of sync in real
players. Each segment had been encoded with its own AAC audio and then joined with
`ffmpeg -f concat -c copy`. Every AAC stream carries encoder priming/padding and ends a few ms off
its own video, so the joined file had a tiny gap or overlap at every cut. ffmpeg honours the
timestamps (so ffmpeg-based checks looked fine), but QuickTime/browsers play the samples back to
back, and 95 cuts' worth of error piled up into visible lip-sync drift.

This script never reuses per-segment audio. For each segment it counts the video frames that were
actually encoded, takes the SOURCE audio for exactly that span (sample positions computed
cumulatively, so rounding never accumulates), joins the PCM, and encodes the audio ONCE. Video is
stream-copied untouched. Audio and picture share every cut point by construction — no J/L cuts,
no overlaps, no crossfades.

Usage:
  concat_av.py SEGMENTS.json OUT.mp4
    SEGMENTS.json: [[encoded_segment.mp4, source_media, source_in_seconds], ...] in play order.
    source_in_seconds must be the same -ss value the segment was encoded with.
Then verify with scripts/check_av_sync.py.
"""
import hashlib, json, os, subprocess, sys, wave
from fractions import Fraction

SR = 48000


def probe_video(p):
    o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
                        "-show_entries", "stream=nb_read_packets,r_frame_rate", "-of", "json", p],
                       capture_output=True, text=True, check=True).stdout
    s = json.loads(o)["streams"][0]
    return int(s["nb_read_packets"]), Fraction(s["r_frame_rate"])


def main():
    segs = json.load(open(sys.argv[1])); out = sys.argv[2]
    work = os.path.abspath(out) + ".audio"; os.makedirs(work, exist_ok=True)
    cum, fps0, wavs = 0, None, []
    for i, (vid, src, t_in) in enumerate(segs):
        n, fps = probe_video(vid)
        if fps0 is None:
            fps0 = fps
        elif fps != fps0:
            sys.exit(f"frame-rate mismatch: {vid} is {fps}, first segment was {fps0}")
        a = round(cum * SR / fps); cum += n; b = round(cum * SR / fps); ns = b - a
        key = hashlib.md5(json.dumps([os.path.abspath(src), round(float(t_in), 4), ns]).encode()).hexdigest()[:10]
        wav = f"{work}/{i:03d}_{key}.wav"
        if not os.path.exists(wav):
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{float(t_in):.3f}", "-i", src, "-vn",
                            "-t", f"{ns / SR + 0.25:.4f}", "-af", f"aresample={SR},apad,atrim=end_sample={ns}",
                            "-ac", "2", "-ar", str(SR), "-c:a", "pcm_s16le", wav], check=True)
        with wave.open(wav) as w:
            if w.getnframes() != ns:
                sys.exit(f"{wav}: {w.getnframes()} samples, expected {ns}")
        wavs.append(wav)
    full = f"{work}/full.wav"
    with wave.open(full, "wb") as W:
        W.setnchannels(2); W.setsampwidth(2); W.setframerate(SR)
        for p in wavs:
            with wave.open(p) as w:
                W.writeframes(w.readframes(w.getnframes()))
    # Join VIDEO ONLY. Given whole segments, the concat demuxer also sees each segment's AAC track
    # (with its encoder priming) and starts the joined video ~21 ms late. Stripping each segment to
    # its video stream first (lossless stream copy) keeps the first frame at exactly t = 0, where
    # the first audio sample is.
    vonly = []
    for i, (v, _, _) in enumerate(segs):
        st = os.stat(v)
        key = hashlib.md5(json.dumps([os.path.abspath(v), st.st_size, st.st_mtime]).encode()).hexdigest()[:10]
        vo = f"{work}/v{i:03d}_{key}.mp4"
        if not os.path.exists(vo):
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", v, "-map", "0:v:0", "-c", "copy", vo], check=True)
        vonly.append(vo)
    vlist = f"{work}/video.txt"
    # absolute paths: the concat demuxer resolves relative entries against the list file's folder
    open(vlist, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in vonly))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", vlist, "-i", full,
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-ar", str(SR), "-movflags", "+faststart", out], check=True)
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,start_time", "-of", "json", out],
                       capture_output=True, text=True).stdout
    st = {x["codec_type"]: float(x.get("start_time", 0) or 0) for x in json.loads(o)["streams"]}
    skew = (st.get("audio", 0) - st.get("video", 0)) * 1000
    print(f"track starts: video {st.get('video', 0) * 1000:.1f} ms, audio {st.get('audio', 0) * 1000:.1f} ms (skew {skew:+.1f} ms)")
    if abs(skew) > 1.0:
        sys.exit(f"{out}: audio and video tracks start {skew:+.1f} ms apart")
    vd = float(cum / fps0)
    print(f"{out}: {len(segs)} segments, {cum} frames = {vd:.3f} s video, "
          f"{round(cum * SR / fps0) / SR:.3f} s audio (sample-exact to the frame count)")


if __name__ == "__main__":
    main()
