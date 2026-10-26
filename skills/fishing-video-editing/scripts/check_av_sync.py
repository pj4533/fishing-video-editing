#!/usr/bin/env python3
"""Check that a finished edit's audio lines up with its picture THE WAY A REAL PLAYER PLAYS IT.

Decodes the whole audio track sequentially (samples back to back, container timestamp gaps
ignored — what QuickTime and browsers do) and cross-correlates a window from the middle of every
segment against the source audio for the moment that segment's picture shows. Any per-cut gap or
overlap in the audio shows up as a growing offset. ffmpeg `-ss` spot checks CANNOT catch this:
they honour the timestamps and look fine on a file that drifts a full second in QuickTime.

Usage:
  check_av_sync.py SEGMENTS.json FINAL.mp4 [--max-ms 45]
    SEGMENTS.json: the same [[encoded_segment.mp4, source_media, source_in_s], ...] list given to
    concat_av.py (segment video lengths come from their frame counts).
Exit code 1 if any confident probe is off by more than --max-ms (default 45 ms, the ITU-R BT.1359
detectability threshold for audio leading picture).
"""
import json, subprocess, sys
import numpy as np
from fractions import Fraction

SR = 8000


def pcm(src, ss=None, t=None):
    cmd = ["ffmpeg", "-v", "error"]
    if ss is not None:
        cmd += ["-ss", f"{max(0.0, ss):.3f}", "-t", f"{t:.3f}"]
    raw = subprocess.run(cmd + ["-i", src, "-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(float)


def frames(p):
    o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                        "stream=nb_read_packets,r_frame_rate", "-of", "json", p], capture_output=True, text=True).stdout
    s = json.loads(o)["streams"][0]
    return int(s["nb_read_packets"]), Fraction(s["r_frame_rate"])


def starts(p):
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,start_time", "-of", "json", p],
                       capture_output=True, text=True).stdout
    st = {}
    for s in json.loads(o)["streams"]:
        st.setdefault(s["codec_type"], float(s.get("start_time", 0) or 0))
    return st.get("video", 0.0), st.get("audio", 0.0)


def main():
    segs = json.load(open(sys.argv[1])); final = sys.argv[2]
    lim = float(sys.argv[sys.argv.index("--max-ms") + 1]) if "--max-ms" in sys.argv else 45.0
    # players honour each track's START time; what they ignore are gaps inside the audio track
    vst, ast = starts(final)
    print(f"track starts: video {vst * 1000:.1f} ms, audio {ast * 1000:.1f} ms")
    F = pcm(final); t = 0.0; worst = 0.0; bad = 0; W = 3.0
    for vid, src, t_in in segs:
        n, fps = frames(vid); d = float(n / fps)
        L = min(2.0, d - 0.3)
        if L >= 0.8:
            off = (d - L) / 2
            i0 = int(round((vst + t + off - ast) * SR))  # audio sample playing when this picture shows
            e = F[i0:i0 + int(L * SR)]
            s = pcm(src, t_in + off - W, L + 2 * W)
            lead = min(W, t_in + off)  # source window may be clipped at file start
            e = e - e.mean(); s = s - s.mean()
            c = np.correlate(s, e, "valid"); k = int(np.argmax(c))
            norm = np.sqrt(np.sum(e * e) * np.convolve(s * s, np.ones(len(e)), "valid")[k]) + 1e-9
            conf = c[k] / norm
            late = (lead - k / SR) * 1000  # + = audio plays late relative to picture
            tag = vid.split("/")[-1]
            flag = ""
            if conf >= 0.5:
                worst = max(worst, abs(late))
                if abs(late) > lim:
                    bad += 1; flag = "  <-- OUT OF SYNC"
            else:
                flag = "  (weak match, ignored)"
            print(f"{int(t // 60)}:{t % 60:05.2f} {tag:34s} audio {late:+6.0f} ms  conf {conf:.2f}{flag}")
        t += d
    print(f"WORST {worst:.0f} ms over confident probes; {bad} out of sync (limit {lim:.0f} ms)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
